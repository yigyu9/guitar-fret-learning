"""8시간 학습 종료 뒤 고정 평가·영상·분석을 순서대로 실행한다."""
import argparse
import datetime
import json
import math
import os
from pathlib import Path
import subprocess
import statistics
import sys
import time


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    status = dict(schema='guitar_learning.long_run_pipeline.v1', started_at=stamp(),
                  completed=False, phase='preparing', pid=os.getpid())

    def write_status(**fields):
        status.update(fields, updated_at=stamp())
        temporary = root/'pipeline_status.tmp'
        temporary.write_text(json.dumps(status, ensure_ascii=False, indent=2)+'\n')
        temporary.replace(root/'pipeline_status.json')

    def command(label, arguments):
        write_status(phase=label)
        with (root/(label+'.log')).open('x') as stream:
            subprocess.run([sys.executable, '-B']+arguments, check=True, stdout=stream,
                           stderr=subprocess.STDOUT)

    try:
        pilot = json.loads((root/'pilot/J/report.json').read_text())
        if not pilot['completed'] or pilot['failure']:
            raise RuntimeError('pilot did not pass')
        metrics = [json.loads(line) for line in (root/'pilot/J/learning_metrics.jsonl').open()]
        # 첫 업데이트는 컴파일·상세 기록 비용을 포함하므로 뒤쪽 실측 처리시간도 남긴다.
        seconds_per_update = min(pilot['wall_s']/pilot['updates_in_run'],
            statistics.median(row['collection_s']+row['update_s'] for row in metrics[-3:]))
        planned = max(100, int(math.ceil(28800/seconds_per_update*1.35/50))*50)
        interval = max(50, int(math.ceil(planned/16/50))*50)
        config = dict(size='large', num_envs=1024, horizon=32, seed=7,
            max_wall_seconds=28800, planned_updates=planned, checkpoint_every=interval,
            pilot_seconds_per_update=seconds_per_update, pilot_updates=len(metrics),
            expected_training_start=stamp(),
            expected_training_end_utc=datetime.datetime.fromtimestamp(time.time()+28800,
                datetime.timezone.utc).isoformat(),
            note='update ceiling includes35% headroom based on late pilot timings; existing wall budget stops at optimizer boundary; '
                 'initial scheduled phrases then full song after25% planned exposure')
        (root/'run_config.json').write_text(json.dumps(config, indent=2)+'\n')
        command('training', [str(root/'tools/train_timed.py'), '--out', str(root/'train'),
            '--updates', str(planned), '--seconds', '28800', '--checkpoint-every', str(interval)])
        report = json.loads((root/'train/J/report.json').read_text())
        final = root/'train/J/final.pt'
        checkpoints = sorted((root/'train/J').glob('checkpoint_*.pt'))
        candidates = [('initial', root/'train/J/initial.pt')]
        if checkpoints:
            candidates.append(('middle', checkpoints[len(checkpoints)//2]))
        candidates.append(('final', final))
        scored = []
        for name, checkpoint in candidates:
            out = root/'evaluation'/name
            command('evaluation_'+name, ['-m', 'guitar_learning.tool.evaluation.evaluate_finger_skill',
                str(checkpoint), '--out', str(out), '--num-envs', '128', '--scope', 'full_song'])
            evaluation = json.loads((out/'report.json').read_text())
            if not evaluation['completed']:
                raise RuntimeError('evaluation incomplete: '+name)
            scored.append(dict(name=name, checkpoint=str(checkpoint), summary=evaluation['summary']))
        # 동점이면 나중 후보를 선택한다. 평가하지 않은 저장본까지 최고라고 주장하지 않는다.
        best = max(enumerate(scored), key=lambda item:(item[1]['summary']['mean_left_success_count'], item[0]))[1]
        (root/'evaluated_candidates.json').write_text(json.dumps(dict(candidates=scored,
            selected=best, selection='highest deterministic128env full-song mean achieved notes among evaluated candidates; later wins ties'), indent=2)+'\n')
        # 分析は動画出力に依存させず、まず数値結果を保存する。
        command('analysis', [str(root/'tools/analyze.py'), '--root', str(root)])
        video_error = None
        try:
            command('render', ['-m', 'guitar_learning.tool.demonstration.render_finger_skill',
                '--checkpoint', best['checkpoint'], '--out', str(root/'video'),
                '--num-envs', '4', '--scope', 'full_song'])
        except Exception as error:
            video_error = repr(error)
        write_status(phase='complete' if video_error is None else 'complete_video_failed',
            completed=True, finished_at=stamp(), training_updates=report['updates_in_run'],
            training_wall_s=report['wall_s'], selected_checkpoint=best['checkpoint'], video_error=video_error)
    except BaseException as error:
        write_status(phase='failed', failure=repr(error), finished_at=stamp())
        raise


if __name__ == '__main__':
    main()
