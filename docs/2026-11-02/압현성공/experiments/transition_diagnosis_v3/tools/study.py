"""승인된 전환 비교를 순차 실행하고 각 평가 직후 결과·예상 시간을 기록한다."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import statistics
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE = Path(__file__).resolve().parents[1]
KST = timezone(timedelta(hours=9))
CHILD = None


def now():
    return datetime.now(KST).isoformat(timespec='seconds')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name+'.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def seal():
    files = []
    for folder in (ROOT/'guitar_learning', BASE/'tools', BASE/'geometry'):
        for current, dirs, names in os.walk(folder, followlinks=False):
            dirs[:] = [d for d in dirs if d not in ('archive', '__pycache__') and not (Path(current)/d).is_symlink()]
            files += [Path(current)/n for n in names if n.endswith(('.py', '.json', '.xml', '.obj', '.stl'))]
    files += list((ROOT/'data/song_bundles/virtual_middle_s3_f6_f7_AB_v2').rglob('*'))
    proof = json.loads((BASE/'geometry/initial_provenance.json').read_text())
    files += [ROOT/name for name in proof['active_physical_inputs']]
    return {str(p.relative_to(ROOT)): sha(p) for p in files if p.is_file()}


def check_sources(state):
    bad = [name for name, value in state['source_seal'].items() if not (ROOT/name).is_file() or sha(ROOT/name) != value]
    if bad:
        raise RuntimeError('봉인 소스/입력 변경: '+str(bad[:8]))


def first_episodes(out, count):
    metadata = json.loads((out/'episode_metadata.json').read_text())
    rows = {}
    for line in (out/'episodes.jsonl').read_text().splitlines():
        row = json.loads(line)['episode']
        for field in metadata['fields']:
            current = row
            for key in field['path'][:-1]:
                current = current.setdefault(key, {})
            key = field['path'][-1]
            if key in current and current[key] != field['value']:
                raise ValueError('공유 episode metadata 충돌')
            current[key] = field['value']
        rows.setdefault(row['env_id'], row)
    if set(rows) != set(range(count)):
        raise ValueError('최초 에피소드 분모 누락')
    return [rows[i] for i in range(count)]


def analyze(out, count):
    report = json.loads((out/'report.json').read_text())
    if (report.get('episodes') != count or not report.get('failed_episodes_in_denominator')
            or not report.get('completed') or not report.get('lifecycle_verified')
            or not report.get('first_episode_per_env_per_batch')):
        raise ValueError('실패 포함 평가 분모 검증 실패')
    rows = first_episodes(out, count)
    result = dict(episodes=count, A=0, B=0, AB=0, full_duration_pair=0,
                  physical=0, wrist=0, clean_s=[0., 0.], wrong_s=[0., 0.],
                  thumb_distance_m=0., thumb_contact_candidate_s=0., reward_terms={})
    ids = [row['finger_control_diagnostics']['episode_id'] for row in rows]
    for row in rows:
        ledger = row['left_note_ledger']['values']
        success = [bool(x) for x in ledger['left']]
        if len(success) != 2:
            raise ValueError('AB 두 음 필요')
        physical = bool(row['termination']['physical_failure'])
        wrist = bool(row['termination']['wrist_failure'])
        result['physical'] += physical
        result['wrist'] += wrist
        result['A'] += success[0]
        result['B'] += success[1]
        result['AB'] += all(success) and row['valid'] and not physical and not wrist
        result['full_duration_pair'] += all(v >= 1.5-1e-8 for v in ledger['clean']) and row['valid'] and not physical and not wrist
        for i in range(2):
            result['clean_s'][i] += ledger['clean'][i]/count
            result['wrong_s'][i] += ledger['wrong'][i]/count
        # 실제 진단 위치는 원장을 그대로 보존하고, 없는 값을 0으로 채우지 않는다.
        for key, value in row['reward_components'].items():
            result['reward_terms'][key] = result['reward_terms'].get(key, 0.)+value/count
        if abs(sum(row['reward_components'].values())-row['reward']) > 1e-4:
            raise ValueError('보상 성분 합계 불일치')
    rejection = dict(position=0, facing=0, load=0, wrong=0, clean=0)
    samples = 0
    tail = [[] for _ in range(count)]
    onset = [None for _ in range(count)]
    with gzip.open(out/'finger_control_trace.jsonl.gz', 'rt') as stream:
        for line in stream:
            extra = json.loads(line)['natural_preparation']['transition']
            for env in range(count):
                if extra['all_env_episode_ids'][env] != ids[env]:
                    continue
                candidate = extra['all_env_candidate'][env]
                if all(candidate):
                    raise ValueError('같은 줄6/7프렛 모순된 동시 성공 후보')
                t = extra['all_env_episode_time_s'][env]
                clean = [c and not w for c, w in zip(candidate, extra['all_env_wrong'][env])]
                if 4.45-1e-8 <= t < 4.5-1e-8:
                    tail[env].append(clean[0])
                if onset[env] is None and t >= 5.25-1e-8:
                    onset[env] = t <= 5.25+1/240+1e-8 and clean[1]
                if not 5.25 <= t < 6.75:
                    continue
                samples += 1
                if not extra['all_env_position_geometry'][env][1]:
                    key = 'position'
                elif not extra['all_env_facing_geometry'][env][1]:
                    key = 'facing'
                elif not extra['all_env_assigned_loaded'][env][1]:
                    key = 'load'
                elif extra['all_env_wrong'][env][1]:
                    key = 'wrong'
                else:
                    key = 'clean'
                rejection[key] += 1
    result.pop('thumb_distance_m')
    result.pop('thumb_contact_candidate_s')
    result['B_endpoint_count'] = samples
    result['B_rejection_partition'] = rejection
    result['on_time_with_previous_tail'] = sum(len(a) >= 11 and all(a) and bool(b) for a, b in zip(tail, onset))
    # 엄지 기존 진단은 원래 위치를 찾은 뒤 수치가 있는 항목만 평균한다.
    def find(value, key):
        if isinstance(value, dict):
            if key in value:
                return value[key]
            for child in value.values():
                found = find(child, key)
                if found is not None:
                    return found
        return None
    thumb = [find(row, 'thumb_support') for row in rows]
    if all(isinstance(x, dict) and 'contact_candidate_s' in x for x in thumb):
        result['thumb_contact_candidate_s'] = statistics.mean(x['contact_candidate_s'] for x in thumb)
        result['thumb_signed_gap_m'] = statistics.mean(x['mean_signed_gap_m'] for x in thumb)
        result['thumb_normal_load_N'] = statistics.mean(x['normal_load_mean_N'] for x in thumb)
    result['evaluation'] = str(out)
    write(out/'analysis.json', result)
    return result


def progress(state, out):
    job = state.get('current_job') or {}
    partial = 0
    metrics = Path(job.get('out', '/nonexistent'))/'J/learning_metrics.jsonl'
    if job.get('operation') == 'train' and metrics.is_file():
        rows = [json.loads(line) for line in metrics.read_text().splitlines() if line.strip()]
        partial = len(rows)
        times = [(r['collection_s']+r['update_s'])/job.get('horizon_ratio', 1) for r in rows[-10:]]
        if times:
            state['seconds_per_H32_update'] = statistics.mean(times)
    done = sum(j.get('updates', 0)*j.get('horizon_ratio', 1) for j in state['jobs'].values()
               if j['status'] == 'complete' and j['operation'] == 'train')
    left = max(0, 2000-done-partial*job.get('horizon_ratio', 1))
    state.update(updated_at=now(), current_partial_updates=partial,
                 estimated_L_finish=state.get('L_finished_at') or (datetime.now(KST)+timedelta(seconds=left*state.get('seconds_per_H32_update', 5.1)+2400)).isoformat(timespec='minutes'))
    write(out/'progress.json', state)
    lines = ['# 목표 전환 v3 실험 진행', '', '- 갱신: '+state['updated_at'], '- 상태: '+state['status'],
             '- 현재: '+job.get('label', '없음'), '- 현재 블록 완료: '+str(partial),
             '- L단계 예상 종료: '+state['estimated_L_finish'],
             '- 구조·엄지 비교는 L 결과와 검증에 따라 이어서 진행한다.', '', '[결과 분석](RESULTS.md)']
    (out/'진행상황.md').write_text('\n'.join(lines)+'\n')
    lines = ['# 목표 전환 v3 누적 결과', '', '새 소스에서 기준 조건부터 다시 학습했다. 최초 평가 에피소드와 실패를 분모에 포함한다.', '',
             '|조건|seed|누적 반복|실행|평가수|A/B/AB|B유지(초)|두음전체유지|물리/손목|',
             '|---|---:|---:|---|---:|---|---:|---:|---|']
    for r in state['results'].values():
        m = r['metrics']
        lines.append(f"|{r['condition']}|{r['seed']}|{r['total']}|{r['mode']}|{m['episodes']}|{m['A']}/{m['B']}/{m['AB']}|{m['clean_s'][1]:.3f}|{m['full_duration_pair']}|{m['physical']}/{m['wrist']}|")
    lines += ['', '## 자동 판독', '']
    if state.get('interpretations'):
        lines += ['- '+s for s in state['interpretations']]
    else:
        lines.append('평가가 쌓이기 전에는 학습 성공이나 원인을 판정하지 않는다.')
    if state.get('error'):
        lines += ['', '중단 사유: '+state['error']]
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def plot(state, out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for condition in ('L_H32', 'H128', 'I_mix', 'T_arm21'):
        for seed in (7, 17):
            for mode in ('mean', 'sampled'):
                rows = [r for r in state['results'].values() if r['condition'] == condition and r['seed'] == seed and r['mode'] == mode]
                if not rows:
                    continue
                rows.sort(key=lambda r: r['total'])
                exposure = [r['total']*64*(128 if condition == 'H128' else 32) for r in rows]
                label = f'{condition} s{seed} {mode}'
                axes[0].plot(exposure, [100*r['metrics']['AB']/r['metrics']['episodes'] for r in rows], marker='.', label=label)
                axes[1].plot(exposure, [r['metrics'].get('thumb_contact_candidate_s', float('nan')) for r in rows], marker='.', label=label)
    axes[0].set_title('AB achievement (failures included)')
    axes[0].set_ylabel('Success (%)')
    axes[0].set_ylim(-3, 103)
    axes[1].set_title('Thumb rear contact candidate (proxy)')
    axes[1].set_ylabel('Mean seconds / episode')
    for axis in axes:
        axis.set_xlabel('Collected transitions')
        axis.grid(alpha=.2)
    axes[0].legend(fontsize=6, loc='best')
    fig.savefig(out/'comparison.png', dpi=150)
    plt.close(fig)


def run(state, root, label, operation, args, updates=0, horizon=32, script='runtime.py'):
    global CHILD
    check_sources(state)
    if label in state['jobs']:
        saved = state['jobs'][label]
        if saved['status'] != 'complete':
            raise RuntimeError('불완전 기존 작업 자동 덮어쓰기 거부: '+label)
        for name, value in saved['evidence'].items():
            if not Path(name).is_file() or sha(name) != value:
                raise RuntimeError('기존 결과 변경: '+name)
        return Path(saved['out'])
    if shutil.disk_usage(ROOT).free < 12*1024**3:
        raise RuntimeError('남은 공간12GiB 미만')
    occupied = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip()
    if occupied:
        raise RuntimeError('다른 GPU 계산 프로세스 사용 중: '+occupied)
    target = root/'jobs'/label
    if target.exists():
        raise FileExistsError(str(target))
    command = [sys.executable, '-B', str(ROOT/'scripts/tab2body.py'), '--cache-root', str(ROOT/'.runtime/cache'),
               'run', str(BASE/'tools'/script), operation, *map(str, args), '--out', str(target)]
    env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MPLCONFIGDIR=str(ROOT/'.runtime/cache/matplotlib'))
    if operation == 'render':
        command = ['xvfb-run', '-a', '--server-args=-screen 0 1280x720x24', *command]
        env['VK_ICD_FILENAMES'] = '/usr/share/vulkan/icd.d/nvidia_icd.json'
    logfile = root/'logs'/(label+'.log')
    logfile.parent.mkdir(exist_ok=True)
    job = dict(label=label, operation=operation, updates=updates, horizon_ratio=horizon/32,
               out=str(target), command=command, status='running', started_at=now())
    state['jobs'][label] = state['current_job'] = job
    start = time.monotonic()
    try:
        with logfile.open('x') as stream:
            CHILD = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            job['pid'] = CHILD.pid
            while CHILD.poll() is None:
                progress(state, root)
                if time.monotonic()-start > (5400 if operation == 'train' else 1800):
                    raise TimeoutError(label+' 시간 상한 초과')
                time.sleep(10)
            code = CHILD.returncode
            CHILD = None
        check_sources(state)
        if code:
            raise RuntimeError(label+' 종료코드 '+str(code)+'; '+str(logfile))
        report = json.loads((target/'report.json').read_text())
        if not report.get('completed') or any(report.get(k) for k in ('failure', 'changed_inputs', 'missing_import_pins', 'cleanup_errors')):
            raise RuntimeError(label+' 실행/입력 검증 실패')
        files = [target/'report.json']
        if operation == 'train':
            phase = json.loads((target/'J/report.json').read_text())
            if phase.get('updates_in_run') != updates:
                raise RuntimeError('블록 반복수 불일치')
            files += [target/'J/final.pt']
        elif operation == 'evaluate':
            files += [target/'episodes.jsonl', target/'episode_metadata.json', target/'finger_control_trace.jsonl.gz', target/'action_mode.json']
        else:
            files += [target/'hand.mp4', target/'fullbody.mp4']
        job.update(status='complete', finished_at=now(), wall_s=time.monotonic()-start,
                   evidence={str(p): sha(p) for p in files})
        return target
    finally:
        if CHILD is not None and CHILD.poll() is None:
            os.killpg(CHILD.pid, signal.SIGTERM)
            try:
                CHILD.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(CHILD.pid, signal.SIGKILL)
                CHILD.wait(timeout=30)
        CHILD = None
        if job['status'] != 'complete':
            job['status'] = 'failed'
        state['current_job'] = None
        progress(state, root)


def evaluate(state, out, condition, seed, total, checkpoint, mode, *, count=32, scale=1., script='runtime.py'):
    label = f'{condition}_s{seed}_u{total}_{mode}_std{scale}_n{count}'
    target = run(state, out, label, 'evaluate', ['--checkpoint', checkpoint, '--num-envs', count, '--action-mode', mode, '--std-scale', scale], script=script)
    metrics = analyze(target, count)
    if script == 'initial_mix.py' and any(row['initial_mix']['started_from_B'] for row in first_episodes(target, count)):
        raise ValueError('I조건 평가에 B 초기상태가 섞임')
    if mode == 'expected-angle':
        action = json.loads((target/'action_mode.json').read_text())
        metrics['quadrature_convergence'] = action['quadrature_convergence']
        metrics['quadrature_within_1mrad'] = action['quadrature_convergence']['max_error_rad'] <= .001
    state['results'][label] = dict(condition=condition, seed=seed, total=total, mode=mode,
                                   scale=scale, checkpoint=str(checkpoint), metrics=metrics)
    progress(state, out)
    plot(state, out)
    return metrics


def train(state, out, condition, seed, total, previous, increment, *, horizon=32, axes='arm16', script='runtime.py'):
    args = ['--updates', increment, '--seed', seed]
    if previous:
        args += ['--resume', previous]
    elif script == 'initial_mix.py':
        args += ['--num-envs', 64, '--horizon', horizon, '--candidate', BASE/'geometry/B_hover_initial_candidate.json',
                 '--native-proof', BASE/'validation/B_reset_native_v2/report.json']
    else:
        args += ['--size', 'large', '--num-envs', 64, '--horizon', horizon, '--axes', axes]
    target = run(state, out, f'{condition}_s{seed}_u{total}_train', 'train', args, increment, horizon, script=script)
    phase = json.loads((target/'J/report.json').read_text())
    if phase.get('optimizer_updates') != total:
        raise RuntimeError('누적 반복수 불일치')
    return target/'J/final.pt'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    def stop(signum, frame):
        raise KeyboardInterrupt('종료 신호 '+str(signum))
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with (out/'study.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if args.resume:
            state = json.loads((out/'progress.json').read_text())
            check_sources(state)
            state.update(status='running', driver_pid=os.getpid())
        else:
            if (out/'progress.json').exists():
                raise FileExistsError('기존 진행 보존')
            state = dict(schema='transition_diagnosis.study.v3', status='running', started_at=now(),
                         driver_pid=os.getpid(), source_seal=seal(), jobs={}, results={}, interpretations=[])
        try:
            # 새 경로의 저장·재개·평가를 검증한 뒤 장기 비교를 시작한다.
            if not state.get('preflight_complete'):
                h = run(state, out, 'validation_H128_train', 'train', ['--updates', 2, '--seed', 7, '--num-envs', 2, '--size', 'small', '--horizon', 128], 2, 128)
                run(state, out, 'validation_H128_resume', 'train', ['--resume', h/'J/final.pt', '--updates', 1, '--seed', 7], 1, 128)
                t = run(state, out, 'validation_T21_train', 'train', ['--updates', 2, '--seed', 7, '--num-envs', 2, '--size', 'small', '--axes', 'arm21'], 2)
                run(state, out, 'validation_T21_resume', 'train', ['--resume', t/'J/final.pt', '--updates', 1, '--seed', 7], 1)
                proof = BASE/'validation/B_reset_native_v2/report.json'
                if proof.is_file() and json.loads(proof.read_text()).get('accepted') is True:
                    i = run(state, out, 'validation_I_train', 'train', ['--candidate', BASE/'geometry/B_hover_initial_candidate.json', '--native-proof', proof,
                             '--updates', 2, '--seed', 7, '--num-envs', 2], 2, script='initial_mix.py')
                    resumed = run(state, out, 'validation_I_resume', 'train', ['--resume', i/'J/final.pt', '--updates', 1, '--seed', 7], 1, script='initial_mix.py')
                    e = run(state, out, 'validation_I_Aonly_evaluation', 'evaluate', ['--checkpoint', resumed/'J/final.pt', '--num-envs', 32, '--action-mode', 'mean'], script='initial_mix.py')
                    analyze(e, 32)
                    if any(row['initial_mix']['started_from_B'] for row in first_episodes(e, 32)):
                        raise ValueError('I검증 평가에 B 초기상태가 남음')
                state['preflight_complete'] = now()
            previous = {7: None, 17: None}
            for total in range(100, 1001, 100):
                for seed in (7, 17):
                    cp = train(state, out, 'L_H32', seed, total, previous[seed], 100)
                    previous[seed] = cp
                    for mode in ('mean', 'sampled'):
                        evaluate(state, out, 'L_H32', seed, total, cp, mode)
                    if total == 300:
                        for scale in (.25, .5):
                            evaluate(state, out, 'D0', seed, total, cp, 'sampled', scale=scale)
                        evaluate(state, out, 'D0', seed, total, cp, 'expected-angle')
            final = {}
            for seed, cp in previous.items():
                final[seed] = evaluate(state, out, 'L_final', seed, 1000, cp, 'mean', count=128)
                evaluate(state, out, 'L_final', seed, 1000, cp, 'sampled', count=128)
            state['L_finished_at'] = now()
            for seed in (7, 17):
                before = next(r['metrics'] for r in state['results'].values() if r['condition'] == 'L_H32' and r['seed'] == seed and r['total'] == 300 and r['mode'] == 'mean')
                after = final[seed]
                state['interpretations'].append(f"L seed{seed}: 평균AB {before['AB']}/32→{after['AB']}/128, B유지 {before['clean_s'][1]:.3f}→{after['clean_s'][1]:.3f}초. 분모와 평가 시점을 구분한다.")
                d0 = [r for r in state['results'].values() if r['condition'] == 'D0' and r['seed'] == seed]
                for r in d0:
                    m = r['metrics']
                    state['interpretations'].append(f"D0 seed{seed} {r['mode']}/std{r['scale']}: AB{m['AB']}/{m['episodes']}, B유지{m['clean_s'][1]:.3f}초. 같은300회모델의 실행방식 비교이며 재학습 성과가 아니다.")
            solved = all(m['AB']/128 >= .9 and min(m['clean_s'])/1.5 >= .9
                         and m['on_time_with_previous_tail']/128 >= .9
                         and (m['physical']+m['wrist'])/128 <= .01 for m in final.values())
            state['interpretations'].append('L: '+('길이 연장에서 두 seed 평균 정책의 AB/유지 기준 통과. 정시 시작과 동작 품질은 별도 점검 필요.' if solved else '1000회에서도 두 seed가 모두 평균AB/유지 기준을 통과하지 못함. 학습 길이만으로 충분하다고 결론낼 수 없음. H 비교 진행.'))
            horizon_final = {}
            if not solved:
                for seed in (7, 17):
                    cp = None
                    last = 0
                    for total in (25, 50, 75, 150, 250):
                        cp = train(state, out, 'H128', seed, total, cp, total-last, horizon=128)
                        last = total
                        for mode in ('mean', 'sampled'):
                            evaluate(state, out, 'H128', seed, total, cp, mode)
                    horizon_final[seed] = evaluate(state, out, 'H128_final', seed, 250, cp, 'mean', count=128)
                state['interpretations'].append('H: H32/H128은 동일 전이 수에서 비교하며 업데이트 횟수·실시간 차이를 별도로 기록한다. 개별 수치표를 확인할 것.')
            proof = BASE/'validation/B_reset_native_v2/report.json'
            horizon_solved = horizon_final and all(m['AB']/128 >= .9 and min(m['clean_s'])/1.5 >= .9
                                                  and m['on_time_with_previous_tail']/128 >= .9
                                                  and (m['physical']+m['wrist'])/128 <= .01 for m in horizon_final.values())
            if not solved and not horizon_solved and proof.is_file() and json.loads(proof.read_text()).get('accepted') is True:
                for seed in (7, 17):
                    cp = None
                    last = 0
                    for total in (100, 300, 600, 1000):
                        cp = train(state, out, 'I_mix', seed, total, cp, total-last, script='initial_mix.py')
                        last = total
                        for mode in ('mean', 'sampled'):
                            evaluate(state, out, 'I_mix', seed, total, cp, mode, script='initial_mix.py')
                    evaluate(state, out, 'I_mix_final', seed, 1000, cp, 'mean', count=128, script='initial_mix.py')
                state['interpretations'].append('I: 검증된 B 초기분포50:50으로 학습하고 평가는 모두 A에서 시작했다. A-only와 비교해 초기 편향을 검토한다.')
            elif not solved and not horizon_solved:
                state['interpretations'].append('I: B reset native 검증이 미통과여서 실행하지 않았다. 미검증 초기상태는 채택하지 않았다.')
            # 엄지 비교는 제어 권한만 바꾸고 동일 보상으로 별도 기록한다.
            for seed in (7, 17):
                cp = None
                for total in (100, 200, 300):
                    cp = train(state, out, 'T_arm21', seed, total, cp, 100, axes='arm21')
                    for mode in ('mean', 'sampled'):
                        evaluate(state, out, 'T_arm21', seed, total, cp, mode)
                thumb = [r for r in state['results'].values() if r['condition'] == 'T_arm21' and r['seed'] == seed and r['total'] == 300 and r['mode'] == 'mean'][0]['metrics']
                state['interpretations'].append(f"T seed{seed}: 엄지 허용 후 평균 접촉후보 {thumb.get('thumb_contact_candidate_s', '미기록')}초, signed gap {thumb.get('thumb_signed_gap_m', '미기록')}m, AB{thumb['AB']}/32. 정확한 접촉쌍·압력 측정과 구분한다.")
            # 평균 실행에서 좋은 모델과 마지막 모델을 선정해 실제 영상만 공개한다.
            candidates = [r for r in state['results'].values() if r['mode'] == 'mean' and r['metrics']['episodes'] == 32]
            best = max(candidates, key=lambda r: (r['metrics']['AB']/r['metrics']['episodes'], sum(r['metrics']['clean_s']), -sum(r['metrics']['wrong_s'])))
            selected = {best['checkpoint']: best, str(previous[17]): dict(condition='L_last', seed=17, total=1000)}
            public = ROOT/'docs/2026-11-02/압현성공/video/transition_diagnosis_v3'
            public.mkdir(parents=True, exist_ok=True)
            for cp, row in selected.items():
                label = f"render_{row['condition']}_s{row['seed']}_u{row['total']}"
                target = run(state, out, label, 'render', ['--checkpoint', cp, '--num-envs', 4], script='initial_mix.py' if row['condition'].startswith('I_mix') else 'runtime.py')
                for kind in ('hand', 'fullbody'):
                    video = target/(kind+'.mp4')
                    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(video)], text=True))
                    if float(probe['format']['duration']) <= 0:
                        raise ValueError('빈 영상')
                    dest = public/(label+'_'+kind+'.mp4')
                    if not dest.exists():
                        os.link(video, dest)
                    elif sha(dest) != sha(video):
                        raise FileExistsError('기존 영상 덮어쓰기 거부')
            state.update(status='complete', finished_at=now())
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error, KeyboardInterrupt) else 'failed', error=str(error), finished_at=now())
            raise
        finally:
            progress(state, out)


if __name__ == '__main__':
    main()
