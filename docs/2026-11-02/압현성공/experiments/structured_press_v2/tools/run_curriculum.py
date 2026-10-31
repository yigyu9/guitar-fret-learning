"""승인된 A→B→C 예산과 두 checkpoint 연속 통과 규칙을 순서대로 실행한다.

이 파일은 학습을 자동 시작하지 않는다. 실행하면 목표별 최대 A300+B300+C900회를
사용하며, 막힌 목표는 보류하고 다음 목표를 검사한다. 중간 결과를 지우지 않는다.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

STUDY = Path(__file__).resolve().parents[1]
RUNTIME = STUDY/'runtime'
MODULE = 'guitar_learning.tool.experiments.structured_press'
STAGES = ('A', 'B', 'C50', 'C75', 'C100')


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def execute(arguments, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    with (out.parent/(out.name+'.console.log')).open('x') as stream:
        subprocess.run([sys.executable, '-B', '-X', 'utf8', '-m', MODULE]+arguments,
            cwd=RUNTIME, env=os.environ.copy(), stdout=stream, stderr=subprocess.STDOUT, check=True)


def accepted(stage, report):
    summary = report['summary']
    if not report['completed'] or summary['count'] != 32:
        raise ValueError('a completed fixed 32-episode evaluation is required')
    minimum = 24 if stage == 'A' else 22 if stage == 'B' else 16
    # 강한 실패 두 원인의 동시 발생도 한 에피소드 실패로 세기 위해 raw 요약을 사용한다.
    failures = report.get('failure_episode_count')
    if failures is None:
        # A는 달성24회가 안전 조건을 포함한다. B/C는 실패 합계가≤1이면 중복 여부와 무관하다.
        failures = summary['physical_failure']+summary.get('wrist_failure', 0)
        if stage != 'A' and failures > 1:
            return False
    return summary['stage_success'] >= minimum and (stage == 'A' or failures <= 1)


def verify_block(row, stage):
    if hashlib.sha256(Path(row['checkpoint']).read_bytes()).hexdigest() != row['checkpoint_sha256']:
        raise ValueError('previous checkpoint changed')
    if 'evaluation_sha256' not in row or 'report.json' not in row['evaluation_sha256']:
        raise ValueError('previous evaluation input seal missing')
    for name, expected in row['evaluation_sha256'].items():
        if hashlib.sha256((Path(row['evaluation'])/name).read_bytes()).hexdigest() != expected:
            raise ValueError('previous evaluation changed')
    report = json.loads((Path(row['evaluation'])/'report.json').read_text())
    if accepted(stage, report) != row['accepted']:
        raise ValueError('previous promotion decision changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry', type=Path, default=RUNTIME/'guitar_learning/assets/structured_press_v2/catalog.json')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out, geometry = args.out.resolve(), args.geometry.resolve()
    catalog = json.loads(geometry.read_text())
    geometry_sha = hashlib.sha256(geometry.read_bytes()).hexdigest()
    out.mkdir(parents=True, exist_ok=True)
    state_path = out/'progress.json'
    state = (json.loads(state_path.read_text()) if state_path.exists() else dict(
        schema='structured_press_v2.curriculum.v1', geometry=str(geometry),
        geometry_sha256=geometry_sha, seed=7, size='large', num_envs=64,
        evaluation_envs=32, goals={}, adopted=False,
        limitation='seed17 and matched-budget J33 control remain separate required confirmation'))
    if state['geometry_sha256'] != geometry_sha:
        raise ValueError('cannot continue a study with changed geometry')
    for goal in catalog['goals']:
        song = goal['song']
        history = state['goals'].setdefault(song, dict(stages={}, status='pending'))
        if history['status'] in ('blocked', 'curriculum_complete'):
            for previous_stage, previous_blocks in history['stages'].items():
                for row in previous_blocks:
                    verify_block(row, previous_stage)
            continue
        previous = None
        for stage in STAGES:
            blocks = history['stages'].setdefault(stage, [])
            streak, passed = 0, False
            for block in range(1, 4):
                location = out/song/stage/('%03d' % (block*100))
                train = location/'train'
                checkpoint = train/'J/final.pt'
                evaluation = location/('evaluation_free_v9' if stage.startswith('C') else 'evaluation_supported')
                if len(blocks) < block:
                    history['status'] = 'running:'+stage+':'+str(block*100)
                    write(state_path, state)
                    if not train.exists():
                        command = ['train', '--geometry', str(geometry), '--song', song,
                            '--stage', stage, '--size', 'large', '--num-envs', '64',
                            '--updates', '100', '--seed', '7', '--out', str(train)]
                        if block > 1:
                            command += ['--resume', str(previous)]
                        elif previous is not None:
                            command += ['--initialize-from', str(previous)]
                        execute(command, train)
                    # 이미 존재하는 실패/부분 실행을 자동 덮어쓰지 않는다.
                    train_report = json.loads((train/'report.json').read_text())
                    if not train_report['completed'] or not checkpoint.is_file():
                        raise RuntimeError('incomplete training block; inspect '+str(train))
                    if not evaluation.exists():
                        execute(['evaluate-free-v9' if stage.startswith('C') else 'evaluate',
                            '--checkpoint', str(checkpoint), '--num-envs', '32', '--out', str(evaluation)], evaluation)
                    report = json.loads((evaluation/'report.json').read_text())
                    blocks.append(dict(updates=block*100, checkpoint=str(checkpoint),
                        checkpoint_sha256=hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
                        evaluation=str(evaluation),
                        evaluation_sha256={name:hashlib.sha256((evaluation/name).read_bytes()).hexdigest()
                            for name in ('report.json', 'episodes.jsonl', 'episode_metadata.json')
                            if (evaluation/name).is_file()},
                        summary=report['summary'], accepted=accepted(stage, report)))
                    write(state_path, state)
                row = blocks[block-1]
                verify_block(row, stage)
                previous = Path(row['checkpoint'])
                streak = streak+1 if row['accepted'] else 0
                if streak >= 2:
                    passed = True
                    break
            if not passed:
                history['status'] = 'blocked'
                history['blocked_stage'] = stage
                break
        else:
            history['status'] = 'curriculum_complete'
        write(state_path, state)
    state['completed'] = all(g['status'] in ('blocked', 'curriculum_complete') for g in state['goals'].values())
    write(state_path, state)


if __name__ == '__main__':
    main()
