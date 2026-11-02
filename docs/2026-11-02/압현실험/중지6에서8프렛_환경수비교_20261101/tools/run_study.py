"""봉인·참조·환경수 벤치를 확인한 뒤 6→8 새 학습을 균형 예산으로 실행한다."""
import argparse
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE = Path(__file__).resolve().parents[1]
OLD = ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3/tools/study.py'
spec = importlib.util.spec_from_file_location('sealed_transition_study_helpers', OLD)
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
BUDGETS = (622592, 1245184, 2097152)


def verify_gates(benchmark_path, native_path):
    benchmark = json.loads(benchmark_path.read_text())
    count = benchmark.get('selected_envs')
    if benchmark.get('status') != 'complete' or count not in (256, 512, 1024):
        raise ValueError('완료된 환경수 벤치와 선정값 필요')
    selected = [r for r in benchmark['results'] if r['num_envs'] == count]
    if len(selected) != 1 or selected[0].get('eligible') is not True or selected[0].get('completed') is not True:
        raise ValueError('선정 벤치 적격/완료 증거 필요')
    study.check_sources(benchmark)
    native = json.loads(native_path.read_text())
    if (native.get('schema') != 'middle_f6_f8.reference_motion.v1' or native.get('accepted') is not True
            or native.get('completed') is not True or native.get('source_unchanged') is not True
            or native.get('AB_on_time_full_hold_verified') is not True or native.get('scene_destroyed') is not True
            or native.get('cleanup_error') is not None or native.get('finite_trace') is not True
            or native.get('no_intermediate_reset') is not True or native.get('clock_matches_physics') is not True):
        raise ValueError('6→8 native accepted와 정리/물리/봉인 검증 필요')
    settings = native['settings']
    if settings.get('initial_state_matches_training_catalog') is not True or settings.get('gap_s') != .75:
        raise ValueError('동일 초기상태와 휴지 필요')
    catalog = BASE/'geometry/initial_catalog.json'
    if settings.get('initial_catalog_sha256') != study.sha(catalog):
        raise ValueError('native와 학습 초기 catalog SHA 불일치')
    candidate = Path(settings['candidate_path']).resolve()
    if study.sha(candidate) != settings['candidate_sha256']:
        raise ValueError('native 후보 SHA 불일치')
    reference = json.loads(candidate.read_text())
    if reference.get('schema') != native['schema'] or [(reference['candidates'][k]['fret'], reference['candidates'][k]['string'], reference['candidates'][k]['finger']) for k in ('A_press', 'B_press')] != [(6, 2, 2), (8, 2, 2)]:
        raise ValueError('native 후보는 중지3번줄6→8이어야 함')
    study.check_sources(dict(source_seal={str(Path(p).resolve().relative_to(ROOT)): value for p, value in reference['source_sha256'].items()}))
    return count, candidate


def seal(extra):
    paths = {OLD, *extra}
    for folder in (ROOT/'guitar_learning', BASE/'tools', BASE/'geometry', ROOT/'data/song_bundles/virtual_middle_s3_f6_f8_AB_v1'):
        paths.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                     and (folder.name == 'virtual_middle_s3_f6_f8_AB_v1' or p.suffix in ('.py', '.json', '.xml', '.obj', '.stl')))
    provenance = json.loads((BASE/'geometry/initial_provenance.json').read_text())
    paths.update(ROOT/name for name in provenance['active_physical_inputs'])
    return {str(p.resolve().relative_to(ROOT)): study.sha(p) for p in sorted(paths)}


def write_progress(state, out):
    state['updated_at'] = study.now()
    job = state.get('current_job') or {}
    metrics = Path(job.get('out', '/nonexistent'))/'J/learning_metrics.jsonl'
    partial = 0
    if metrics.is_file():
        for line in metrics.read_text().splitlines():
            try:
                json.loads(line)
                partial += 1
            except json.JSONDecodeError:
                pass  # 마지막 기록 중 한 줄은 다음 갱신 때 재확인한다.
    state['current_partial_updates'] = partial
    study.write(out/'progress.json', state)
    lines = ['# 중지6→8 전환 학습', '', '- 상태: '+state['status'], '- 갱신: '+state['updated_at'],
             '- 선정 환경수: '+str(state['num_envs']), '- 현재: '+job.get('label', '없음'),
             '- 현재 블록 완료: '+str(partial), '',
             '|seed|누적경험|실행|평가수|A/B/AB|전체유지|정시전환|B유지초|물리/손목|',
             '|---:|---:|---|---:|---|---:|---:|---:|---|']
    for row in state['results'].values():
        m = row['metrics']
        lines.append(f"|{row['seed']}|{row['transitions']}|{row['mode']}|{m['episodes']}|{m['A']}/{m['B']}/{m['AB']}|{m['full_duration_pair']}|{m['on_time_with_previous_tail']}|{m['clean_s'][1]:.3f}|{m['physical']}/{m['wrist']}|")
    if state.get('error'):
        lines += ['', '중단 원인: '+state['error']]
    (out/'진행상황.md').write_text('\n'.join(lines)+'\n')


def validate_job(folder, operation, updates=0):
    reports = [folder/'report.json']
    if operation == 'train':
        reports.append(folder/'J/report.json')
    for path in reports:
        report = json.loads(path.read_text())
        if report.get('completed') is not True or (operation != 'train' or path.parent.name == 'J') and report.get('lifecycle_verified') is not True or any(
                report.get(k) for k in ('failure', 'changed_inputs', 'missing_import_pins', 'cleanup_errors')):
            raise ValueError('실행·봉인·종료 검증 실패: '+str(path))
    if operation == 'train' and report.get('updates_in_run') != updates:
        raise ValueError('학습 블록 반복수 불일치')
    if operation == 'render' and report.get('policy_unchanged') is not True:
        raise ValueError('영상 정책 불변 검증 필요')


def run(state, out, label, operation, arguments, updates=0):
    study.check_sources(state)
    folder = study.run(state, out, label, operation, arguments, updates=updates)
    validate_job(folder, operation, updates)
    study.check_sources(state)
    return folder


def analyze(folder, count):
    path = BASE/'tools/analyze_results.py'
    spec = importlib.util.spec_from_file_location('middle_f68_result_analysis', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.analyze(folder, count)


def evaluate(state, out, seed, budget, checkpoint, tag, count=32, mode='mean'):
    label = f's{seed}_t{budget}_{tag}_{mode}_n{count}'
    folder = run(state, out, label, 'evaluate', ['--checkpoint', checkpoint, '--num-envs', count, '--action-mode', mode])
    metrics = analyze(folder, count)
    state['results'][label] = dict(seed=seed, transitions=budget, mode=mode, checkpoint=str(checkpoint),
                                    tag=tag, evaluation=str(folder), metrics=metrics)
    write_progress(state, out)
    return metrics


def passed(m):
    n = m['episodes']
    return (m['AB']/n >= .9 and m['full_duration_pair']/n >= .9
            and m['on_time_with_previous_tail']/n >= .9 and min(m['clean_s'])/1.5 >= .9
            and (m['physical']+m['wrist'])/n <= .01)


def train(state, out, seed, total, previous=None, previous_total=0):
    n = state['num_envs']; increment = (total-previous_total)//(n*32)
    if total <= previous_total or (total-previous_total) % (n*32):
        raise ValueError('환경수·H32 배치 정수 경험 예산 필요')
    args = ['--updates', increment, '--seed', seed, '--num-envs', n, '--size', 'large', '--horizon', 32]
    if previous:
        args += ['--resume', previous]
    folder = run(state, out, f's{seed}_t{total}_train', 'train', args, updates=increment)
    phase = json.loads((folder/'J/report.json').read_text())
    if phase['transitions'] != total-previous_total:
        raise ValueError('실제 수집 경험수와 계획 불일치')
    return folder/'J/final.pt'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--native-report', type=Path, required=True)
    parser.add_argument('--benchmark-report', type=Path, default=BASE/'benchmark/progress.json')
    args = parser.parse_args()
    native = args.native_report.resolve(); benchmark = args.benchmark_report.resolve()
    n, candidate = verify_gates(benchmark, native)
    out = args.out.resolve()
    if out.exists():
        raise FileExistsError('기존 실험 출력 보존: '+str(out))
    out.mkdir(parents=True)
    with (BASE/'gpu_study.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        def stop(signum, frame):
            raise KeyboardInterrupt('종료 신호 '+str(signum))
        signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
        state = dict(schema='middle_f68.learning_study.v1', status='running', started_at=study.now(),
                     driver_pid=os.getpid(), num_envs=n, budgets=list(BUDGETS), source_seal=seal((native, benchmark, candidate)),
                     jobs={}, results={}, last={}, videos=[], native_report=str(native), benchmark_report=str(benchmark),
                     scope='fresh models only; reward/control/physics/PPO unchanged; balanced transition budgets')
        study.BASE = BASE; study.progress = write_progress
        try:
            write_progress(state, out)
            smoke = run(state, out, 'smoke_train2', 'train', ['--updates', 2, '--seed', 7, '--num-envs', n, '--size', 'large', '--horizon', 32], updates=2)
            resumed = run(state, out, 'smoke_resume1', 'train', ['--updates', 1, '--seed', 7, '--num-envs', n, '--resume', smoke/'J/final.pt'], updates=1)
            evaluate(state, out, 7, 3*n*32, resumed/'J/final.pt', 'smoke')
            run(state, out, 'smoke_render', 'render', ['--checkpoint', resumed/'J/final.pt', '--num-envs', 4])
            for budget in BUDGETS:
                stage = []
                for seed in (7, 17):
                    prior = state['last'].get(str(seed), {})
                    checkpoint = train(state, out, seed, budget, prior.get('checkpoint'), prior.get('transitions', 0))
                    state['last'][str(seed)] = dict(checkpoint=str(checkpoint), transitions=budget)
                    stage.append(evaluate(state, out, seed, budget, checkpoint, 'development'))
                if all(passed(m) for m in stage):
                    confirm = [evaluate(state, out, seed, budget, state['last'][str(seed)]['checkpoint'], 'early_confirm', 128) for seed in (7, 17)]
                    if all(passed(m) for m in confirm):
                        state['early_stop'] = 'both seeds passed 32 and independent128 criteria'
                        break
            selections = []
            for seed in (7, 17):
                candidates = [r for r in state['results'].values() if r['seed'] == seed and r['tag'] == 'development']
                best = max(candidates, key=lambda r: (r['metrics']['full_duration_pair'], r['metrics']['AB'], r['metrics']['on_time_with_previous_tail'], sum(r['metrics']['clean_s'])))
                last = state['last'][str(seed)]
                selections += [(seed, 'best', best['transitions'], best['checkpoint']), (seed, 'last', last['transitions'], last['checkpoint'])]
            for seed, kind, budget, cp in selections:
                evaluate(state, out, seed, budget, cp, kind+'_final', 128)
                evaluate(state, out, seed, budget, cp, kind+'_repeat', 128)
                evaluate(state, out, seed, budget, cp, kind+'_exploration', 32, 'sampled')
                folder = run(state, out, f's{seed}_t{budget}_{kind}_render', 'render', ['--checkpoint', cp, '--num-envs', 4])
                public = BASE/'동영상'; public.mkdir(exist_ok=True)
                for view, korean in (('hand', '손확대'), ('fullbody', '전신')):
                    source = folder/(view+'.mp4')
                    duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', str(source)], text=True))
                    if duration <= 0:
                        raise ValueError('빈 영상')
                    target = public/f'중지3번줄6에서8프렛_seed{seed}_{kind}_{budget}경험_{korean}.mp4'
                    if target.exists():
                        raise FileExistsError('기존 영상 보존: '+str(target))
                    os.link(source, target)
                    state['videos'].append(dict(path=str(target), checkpoint=cp, sha256=study.sha(target), duration_s=duration))
                study.write(out/'videos.json', state['videos'])
            state.update(status='complete', finished_at=study.now())
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed', error=repr(error), finished_at=study.now())
            raise
        finally:
            write_progress(state, out)
            study.check_sources(state)
            study.write(out/'SOURCE_VERIFICATION.json', dict(unchanged=True, source_count=len(state['source_seal']), checked_at=study.now()))


if __name__ == '__main__':
    main()
