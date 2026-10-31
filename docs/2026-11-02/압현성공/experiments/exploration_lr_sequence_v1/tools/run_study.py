"""고정된 단독·조합·순차 조건을 직렬 학습하고 후보만 새 seed로 확인한다."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parents[1]
RUNTIME = BASE/'runtime'
ROOT = next(p for p in BASE.parents if (p/'isaacgym/python').is_dir())
MODULE = 'guitar_learning.tool.experiments.press_research'
CONDITIONS = ('baseline', 'exploration', 'lr', 'combined', 'sequential')
SCREEN = ('index_s3_f4', 'middle_s3_f6', 'ring_s2_f7', 'pinky_s3_f9')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    tmp.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--smoke-only', action='store_true')
    args = parser.parse_args()
    with (BASE/'runner.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        study(args)


def study(args):
    seal = read(BASE/'seal.json')
    env = dict(os.environ, PYTHONPATH=str(RUNTIME)+':'+str(ROOT/'isaacgym/python'),
        LD_LIBRARY_PATH=str(Path(sys.executable).parent.parent/'lib'),
        PATH=str(Path(sys.executable).parent)+':/usr/local/cuda/bin:/usr/bin:/bin',
        PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
        LANG='C.UTF-8', LC_ALL='C.UTF-8', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', MUJOCO_GL='osmesa',
        TORCH_EXTENSIONS_DIR=str(BASE.parents[1]/'process/cache/torch'))
    manifest_path = BASE/'run_manifest.json'
    if manifest_path.exists():
        if not args.resume:
            raise FileExistsError('기존 실행은 --resume으로만 이어간다')
        manifest = read(manifest_path)
        if manifest['seal'] != seal:
            raise ValueError('실험 입력 봉인이 달라짐')
    else:
        manifest = dict(seal=seal, stages={}, trials=[], created_at=now())
        write(manifest_path, manifest)
    state = dict(phase='preparing', pid=os.getpid(), completed_trials=sum(r['completed'] for r in manifest['trials']))

    def progress(**changes):
        state.update(changes, updated_at=now())
        write(BASE/'status.json', state)
        text = ['# 압현 개선 비교 연구 진행', '',
                f"- 현재 단계: {state['phase']}",
                f"- 평가까지 완료한 실행: {state['completed_trials']}",
                f"- 조건: {state.get('condition', '-')}, 목표: {state.get('target', '-')}, seed: {state.get('seed', '-')}",
                f"- 현재 단계 경과: {state.get('stage_elapsed_s', 0):.0f}초",
                f"- 갱신 UTC: {state['updated_at']}", '',
                '[수치 계획](PLAN.md) · [누적 결과](analysis/RESULTS.md) · [기계 판독 상태](status.json)', '']
        (BASE/'progress.md').write_text('\n'.join(text))

    def check_seal():
        changed = [rel for rel, digest in seal['files'].items()
                   if not (BASE/rel).is_file() or sha(BASE/rel) != digest]
        if changed:
            raise RuntimeError('연구 입력 변경: '+str(changed[:5]))

    def verify_stage(label):
        stage = manifest['stages'][label]
        for name, digest in stage['proofs'].items():
            if not Path(name).is_file() or sha(Path(name)) != digest:
                raise RuntimeError('완료 산출물 변경: '+name)

    def execute(label, operation, mode, out, arguments):
        check_seal()
        proof = out/'report.json'
        if label in manifest['stages']:
            verify_stage(label)
            return read(proof)
        if out.exists():
            raise FileExistsError('미완료 출력은 보존됨, 조사 후 재개 필요: '+str(out))
        progress(phase=label, stage_elapsed_s=0)
        log = BASE/'logs'/(label+'.log')
        log.parent.mkdir(exist_ok=True)
        command = [sys.executable, '-B', '-X', 'utf8', '-m', MODULE, operation,
                   '--mode', mode, '--out', str(out)]+arguments
        started = time.monotonic()
        with log.open('a') as stream:
            child = subprocess.Popen(command, cwd=RUNTIME, env=env, stdout=stream, stderr=subprocess.STDOUT)
            progress(child_pid=child.pid, log=str(log))
            try:
                while child.poll() is None:
                    try:
                        child.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        progress(stage_elapsed_s=time.monotonic()-started)
            except BaseException:
                child.terminate()
                child.wait()
                raise
        if child.returncode:
            raise RuntimeError(label+' 실패: '+str(log))
        check_seal()
        report = read(proof)
        if not report.get('completed') or report.get('failure'):
            raise RuntimeError('완료되지 않은 단계: '+label)
        evidence = [proof]
        evidence += [out/name for name in ('episodes.jsonl', 'episode_metadata.json',
                     'J/initial.pt', 'J/final.pt', 'episode_env0000.json',
                     'capture_metadata.json', 'press_research_diagnostics.json') if (out/name).is_file()]
        manifest['stages'][label] = dict(proofs={str(p):sha(p) for p in evidence},
                                      wall_s=time.monotonic()-started)
        write(manifest_path, manifest)
        progress(child_pid=None)
        return report

    def trial(mode, target, seed):
        label = f'{mode}_{target}_s{seed}'
        previous = next((r for r in manifest['trials'] if r['id'] == label), None)
        if previous:
            if not previous['completed'] and mode == 'baseline':
                raise RuntimeError('기준군 실패는 자동 건너뛰지 않음: '+label)
            if previous['completed']:
                for suffix in ('train', 'evaluate_initial', 'evaluate_final'):
                    verify_stage(label+'_'+suffix)
                fresh = summarize_trial(BASE/'runs'/label)
                if any(previous[k] != fresh[k] for k in ('initial', 'final')):
                    raise RuntimeError('완료 실행 집계 변경: '+label)
            return previous
        progress(condition=mode, target=target, seed=seed)
        folder = BASE/'runs'/label
        row = dict(id=label, condition=mode, target=target, seed=seed, completed=False)
        try:
            train = folder/'train'
            execute(label+'_train', 'train', mode, train,
                ['--song', 'virtual_finger_v9_'+target, '--updates', '100', '--num-envs', '64',
                 '--horizon', '32', '--size', 'large', '--seed', str(seed)])
            for checkpoint in ('initial', 'final'):
                execute(label+'_evaluate_'+checkpoint, 'evaluate', mode, folder/('evaluate_'+checkpoint),
                    ['--checkpoint', str(train/'J'/(checkpoint+'.pt')), '--num-envs', '32'])
            row.update(summarize_trial(folder), completed=True,
                       checkpoint=str((train/'J/final.pt').resolve()))
        except Exception as error:
            row['error'] = repr(error)
            check_seal()
            if mode == 'baseline':
                raise
        finally:
            manifest['trials'].append(row)
            write(manifest_path, manifest)
            write(folder/'trial.json', row)
            progress(completed_trials=sum(r['completed'] for r in manifest['trials']))
            report_study(manifest)
        return row

    try:
        for mode in CONDITIONS:
            label = 'smoke_'+mode
            progress(condition=mode, target=SCREEN[0], seed=7)
            train = BASE/'smoke'/mode/'train'
            execute(label+'_train', 'train', mode, train,
                ['--song', 'virtual_finger_v9_'+SCREEN[0], '--updates', '2', '--num-envs', '8'])
            execute(label+'_evaluate', 'evaluate', mode, BASE/'smoke'/mode/'evaluation',
                ['--checkpoint', str(train/'J/final.pt'), '--num-envs', '4'])
        execute('smoke_sequential_render', 'render', 'sequential', BASE/'smoke/sequential/render',
                ['--checkpoint', str(BASE/'smoke/sequential/train/J/final.pt'), '--num-envs', '1'])
        if args.smoke_only:
            progress(phase='smoke_complete')
            return
        for mode in CONDITIONS:
            for target in SCREEN:
                trial(mode, target, 7)
        candidates = eligible_groups(manifest, 7)
        selection = dict(screen_candidates=candidates, confirmation_seed=17, confirmed=[],
                         default_changed=False)
        write(BASE/'analysis/selection.json', selection)
        if candidates:
            # 선택한 한 후보만 확인해 선택 이후의 조합 탐색을 추가하지 않는다.
            winner = sorted(candidates, key=lambda x: x['rank'], reverse=True)[0]['condition']
            for mode in ('baseline', winner):
                for target in SCREEN:
                    trial(mode, target, 17)
            confirmed = [g for g in eligible_groups(manifest, 17) if g['condition'] == winner]
            selection['confirmed'] = confirmed
            if confirmed:
                selection['expanded_condition'] = winner
                targets = [g['song_id'].replace('virtual_finger_v9_', '')
                           for g in read(BASE/'targets.json')['targets']]
                for target in targets:
                    if target not in SCREEN:
                        trial(winner, target, 7)
            selection['reason'] = 'new_seed_passed' if confirmed else 'new_seed_did_not_reproduce'
        else:
            selection['reason'] = 'no_condition_cleared_prespecified_screen'
        write(BASE/'analysis/selection.json', selection)
        # 조건마다 한 목표를 촬영하며 실제 영상 에피소드의 달성은 따로 기록한다.
        videos = []
        for mode in CONDITIONS:
            own = [x for x in manifest['trials'] if x['condition'] == mode and x['completed'] and x['seed'] == 7]
            if not own:
                continue
            best = max(own, key=lambda r:(r['final']['success'], r['final']['clean_100ms'], r['final']['mean_best_clean_s'], -r['final']['median_min_distance_mm']))
            render = BASE/'rendering'/best['id']
            try:
                report = execute(best['id']+'_render', 'render', mode, render,
                    ['--checkpoint', best['checkpoint'], '--num-envs', '4'])
                files = {}
                for view in ('hand', 'fullbody'):
                    original, dest = render/(view+'.mp4'), BASE/'video'/best['id']/(view+'.mp4')
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if original.exists():
                        original.replace(dest)
                    subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(dest), '-f', 'null', '-'],
                                   check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    files[view] = str(dest)
                episode = report['episode']
                term = episode['termination']
                success = episode['song']['left_success_count'] > 0 and not (term['physical_failure'] or term['wrist_failure'])
                videos.append(dict(id=best['id'], evaluation=best['final'], rendered_episode_success=success, files=files))
            except Exception as error:
                check_seal()
                videos.append(dict(id=best['id'], render_error=repr(error)))
        write(BASE/'analysis/videos.json', videos)
        report_study(manifest)
        progress(phase='complete', child_pid=None, selection=selection)
    except BaseException as error:
        progress(phase='failed', failure=repr(error))
        raise


def summarize_trial(folder):
    import statistics
    result = {}
    for kind in ('initial', 'final'):
        path = folder/('evaluate_'+kind)
        report = read(path/'report.json')
        episodes = [json.loads(line)['episode'] for line in (path/'episodes.jsonl').open()]
        if len(episodes) != 32 or report['episodes'] != 32:
            raise ValueError('고정32평가가 아님')
        safe = lambda e:not (e['termination']['physical_failure'] or e['termination']['wrist_failure'])
        streak = lambda e:e['left_note_ledger']['values']['best_clean_streak'][0]
        result[kind] = dict(episodes=len(episodes),
            success=sum(safe(e) and e['song']['left_success_count'] > 0 for e in episodes),
            clean_100ms=sum(safe(e) and streak(e) >= .1-1e-9 for e in episodes),
            failures=sum(not safe(e) for e in episodes),
            mean_best_clean_s=statistics.mean(streak(e) for e in episodes),
            max_best_clean_s=max(streak(e) for e in episodes),
            min_distances_mm=[e['left_note_ledger']['values']['surface_min'][0]*1000 for e in episodes],
            median_min_distance_mm=statistics.median(e['left_note_ledger']['values']['surface_min'][0]*1000 for e in episodes))
    return result


def grouped(manifest, seed):
    import statistics
    groups = {}
    for mode in CONDITIONS:
        rows = [r for r in manifest['trials'] if r['condition'] == mode and r['seed'] == seed and r['target'] in SCREEN]
        if len(rows) != 4 or not all(r['completed'] for r in rows):
            continue
        groups[mode] = dict(condition=mode, seed=seed,
            **{key:sum(r['final'][key] for r in rows) for key in ('episodes', 'success', 'clean_100ms', 'failures')},
            mean_best_clean_s=statistics.mean(r['final']['mean_best_clean_s'] for r in rows),
            median_min_distance_mm=statistics.median(d for r in rows for d in r['final']['min_distances_mm']))
    return groups


def eligible_groups(manifest, seed):
    groups = grouped(manifest, seed)
    baseline = groups.get('baseline')
    if baseline is None:
        return []
    candidates = []
    for mode, row in groups.items():
        if mode == 'baseline' or row['failures'] > baseline['failures']+4:
            continue
        achieved = row['success'] >= baseline['success']+8
        contact = (row['clean_100ms'] >= baseline['clean_100ms']+16 and
                   row['median_min_distance_mm'] <= baseline['median_min_distance_mm']-10)
        if achieved or contact:
            candidates.append(dict(row, kind='achievement' if achieved else 'preliminary_contact',
                rank=[row['success'], row['clean_100ms'], row['mean_best_clean_s'], -row['median_min_distance_mm']]))
    return candidates


def report_study(manifest):
    write(BASE/'analysis/results.json', dict(trials=manifest['trials'], grouped={str(seed):grouped(manifest, seed) for seed in (7,17)}))
    text = ['# 압현 개선 비교 연구 결과', '',
            '실행 중에는 완료한 목표만 누적한다. 모든 조건은 fresh large/64/H32/100회이며 각 모델은 초기·최종32환경으로 평가한다.', '',
            '| 조건 | 목표 | seed | 완료 | 달성 /32 | clean≥0.1초 /32 | 실패 /32 | 최소거리 중앙값 mm |',
            '|---|---|---:|---|---:|---:|---:|---:|']
    for row in manifest['trials']:
        if row['completed']:
            r = row['final']
            text.append(f"| {row['condition']} | {row['target']} | {row['seed']} | 예 | {r['success']} | {r['clean_100ms']} | {r['failures']} | {r['median_min_distance_mm']:.2f} |")
        else:
            text.append(f"| {row['condition']} | {row['target']} | {row['seed']} | 실패 | — | — | — | — |")
    text.extend(['', '후보 선택은 사전 고정한 PLAN.md 기준이며 병렬환경32개를 독립 학습seed 반복으로 해석하지 않는다. 생산 기본값은 변경하지 않는다.', ''])
    selection = BASE/'analysis/selection.json'
    if selection.exists():
        text.extend(['선택·재확인 결과:', '', '```json', json.dumps(read(selection), ensure_ascii=False, indent=2), '```', ''])
    videos = BASE/'analysis/videos.json'
    if videos.exists():
        text.extend(['## 실제 정책 영상', ''])
        for row in read(videos):
            text.append(f"- {row['id']}: 촬영 에피소드 달성={row.get('rendered_episode_success', '렌더 실패')}")
            for view, path in row.get('files', {}).items():
                text.append(f'  - [{view}]({path})')
    (BASE/'analysis/RESULTS.md').write_text('\n'.join(text))


if __name__ == '__main__':
    main()
