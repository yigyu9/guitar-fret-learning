"""승인된 5조건 비교를 한 GPU에서 순차 실행하고 결과·예상 시간을 기록한다.

학습 패키지를 import하거나 수정하지 않는다. 실제 학습·평가·영상은 각각 새
프로세스의 공식 실험 실행기를 사용하며, 실패/입력 변경 시 자료를 보존하고 멈춘다.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
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
import traceback


HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p/'scripts/tab2body.py').is_file())
KST = timezone(timedelta(hours=9))
SONG = 'virtual_finger_v9_middle_s3_f6'
TOTAL_UPDATES = 1400
TOTAL_EVALUATIONS = 28
CHILD = None


def timestamp():
    return datetime.now(KST).isoformat(timespec='seconds')


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def source_paths():
    paths = {ROOT/'scripts/tab2body.py', HERE/'run_study.py', HERE/'analyze_results.py'}
    for current, dirs, files in os.walk(ROOT/'guitar_learning', followlinks=False):
        dirs[:] = [name for name in dirs if name not in ('archive', '__pycache__') and
                   not (Path(current)/name).is_symlink()]
        paths.update(Path(current)/name for name in files if name.endswith('.py'))
    paths.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    paths.update(path for path in (ROOT/'data/song_bundles'/SONG).rglob('*') if path.is_file())
    return paths


def verify_sources(seal):
    bad = [name for name, sha in seal.items() if not (ROOT/name).is_file() or digest(ROOT/name) != sha]
    if bad:
        raise RuntimeError('실험 도중 입력이 바뀌어 조건 비교 중단: '+', '.join(bad[:8]))


def live_updates(out):
    path = Path(out)/'J/learning_metrics.jsonl'
    rows = []
    if path.is_file():
        for line in path.read_text().splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                break  # 마지막 행을 쓰는 중에는 다음 관측에서 다시 읽는다.
    times = [row['collection_s']+row['update_s'] for row in rows[-10:]]
    return len(rows), statistics.mean(times) if times else None


def progress(state):
    current = state.get('current_job') or {}
    current_updates, seconds = live_updates(current['out']) if current.get('operation') == 'train' else (0, None)
    done_train = sum(job.get('updates', 0) for job in state['jobs'].values() if job['status'] == 'complete')
    done_eval = sum(job['operation'] == 'evaluate' and job['status'] == 'complete' for job in state['jobs'].values())
    if seconds is not None:
        state['seconds_per_update_recent'] = seconds
    seconds = state.get('seconds_per_update_recent', 5.04)
    remaining = max(0, TOTAL_UPDATES-done_train-current_updates)*seconds
    remaining += max(0, TOTAL_EVALUATIONS-done_eval)*70+6*75+14*15
    now = datetime.now(KST)
    state.update(updated_at=timestamp(), completed_train_updates=done_train,
        current_block_completed_updates=current_updates, completed_evaluations=done_eval,
        estimated_finish_earliest=(now+timedelta(seconds=remaining*.85)).isoformat(timespec='minutes'),
        estimated_finish_latest=(now+timedelta(seconds=remaining*1.25)).isoformat(timespec='minutes'))
    if state['status'] in ('complete', 'complete_with_artifact_errors'):
        state['estimated_finish_earliest'] = state['estimated_finish_latest'] = state['finished_at']
    elif state['status'] in ('failed', 'interrupted'):
        state['estimated_finish_earliest'] = state['estimated_finish_latest'] = '중단: 원인 확인 필요'
    write(HERE/'progress.json', state)
    name = current.get('label', '없음')
    text = ('# 자연스러운 압현 준비 비교 진행\n\n'
        f"- 갱신: {state['updated_at']}\n- 상태: {state['status']}\n"
        f"- 현재 작업: {name}\n- 완료 학습: {done_train}/{TOTAL_UPDATES}반복"
        f" (현재 블록 추가 {current_updates}반복)\n- 완료 평가: {done_eval}/{TOTAL_EVALUATIONS}\n"
        f"- 예상 종료: {state['estimated_finish_earliest']} ~ {state['estimated_finish_latest']}\n"
        '- 진행·평가는 같은 GPU에서 하나씩 실행한다. 압현 성공·자연스러움 채택 여부는 결과표를 따른다.\n'
        f"- 고정 후보: {', '.join(state.get('selected_conditions', [])) or '1차 비교 후 선정'}\n")
    if state.get('error'):
        text += '\n실행 중단 원인: '+state['error']['message']+'\n'
    (HERE/'진행상황.md').write_text(text)


def run_job(state, label, operation, args, out, *, updates=0, render=False):
    global CHILD
    out = Path(out)
    verify_sources(state['source_seal'])
    if label in state['jobs']:
        saved = state['jobs'][label]
        if (saved['status'] != 'complete' or digest(saved['report']) != saved['report_sha256'] or
                any(not Path(name).is_file() or digest(name) != sha for name, sha in saved['evidence_sha256'].items())):
            raise RuntimeError('부분 실행 또는 변경된 보고서는 덮어쓰지 않음: '+label)
        return json.loads(Path(saved['report']).read_text())
    if out.exists():
        raise FileExistsError('기존 출력 보존: '+str(out))
    if shutil.disk_usage(ROOT).free < 12*1024**3:
        raise RuntimeError('디스크 여유12GiB 미만: 자료 보존 후 중단')
    occupied = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip()
    if occupied:
        raise RuntimeError('다른 GPU 프로세스가 있어 동시 실행 중단: '+occupied)
    command = [sys.executable, '-B', str(ROOT/'scripts/tab2body.py'), '--cache-root',
        '/tmp/tab2body_natural_press_v3', 'run', '-m',
        'guitar_learning.tool.experiments.natural_press', operation, *map(str, args), '--out', str(out)]
    if render:
        command = ['xvfb-run', '-a', '--server-args=-screen 0 1280x720x24', *command]
    environment = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    if render:
        environment['VK_ICD_FILENAMES'] = '/usr/share/vulkan/icd.d/nvidia_icd.json'
    logfile = HERE/'logs'/(label+'.log')
    logfile.parent.mkdir(exist_ok=True)
    job = dict(label=label, operation=operation, command=command, out=str(out), log=str(logfile),
               status='running', started_at=timestamp(), updates=updates)
    state['jobs'][label] = job
    state['current_job'] = job
    started = time.monotonic()
    with logfile.open('x') as stream:
        CHILD = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=stream,
            stderr=subprocess.STDOUT, start_new_session=True)
        job['pid'] = CHILD.pid
        progress(state)
        while CHILD.poll() is None:
            if time.monotonic()-started > (2700 if operation == 'train' else 900):
                os.killpg(CHILD.pid, signal.SIGTERM)
                CHILD.wait(timeout=30)
                raise TimeoutError('작업 제한시간 초과: '+label)
            time.sleep(10)
            progress(state)
        code = CHILD.returncode
        CHILD = None
    if code:
        job.update(status='failed', returncode=code, finished_at=timestamp())
        raise RuntimeError(f'{label} 종료코드{code}; 상세 로그: {logfile}')
    verify_sources(state['source_seal'])
    report_path = out/('evaluation/report.json' if '--free-v9' in args else 'report.json')
    report = json.loads(report_path.read_text())
    if not report.get('completed') or report.get('failure'):
        raise RuntimeError('보고서 미완료: '+str(report_path))
    if operation == 'evaluate' and (report['episodes'] != 32 or not report['failed_episodes_in_denominator']):
        raise RuntimeError('최초32 평가 분모 계약 불일치')
    if operation == 'train':
        phase = json.loads((out/'J/report.json').read_text())
        if phase['updates_in_run'] != updates:
            raise RuntimeError('요청한 추가 학습 반복수 미충족')
    evidence = [report_path]
    if operation == 'train':
        evidence.append(out/'J/final.pt')
    if operation == 'evaluate':
        evidence += [report_path.parent/name for name in
                     ('episodes.jsonl', 'episode_metadata.json', 'finger_control_trace.jsonl.gz')]
        if '--free-v9' in args:
            evidence.append(out/'model_only/J/final.pt')
    job['evidence_sha256'] = {str(path): digest(path) for path in evidence}
    job.update(status='complete', finished_at=timestamp(), wall_s=time.monotonic()-started,
               report=str(report_path), report_sha256=digest(report_path))
    state['current_job'] = None
    progress(state)
    return report


def block(state, condition, seed, total):
    from analyze_results import analyze_evaluation
    label = f'seed{seed}_{condition}_u{total}'
    out = HERE/'blocks'/label
    out.mkdir(parents=True, exist_ok=True)
    args = ['--seed', seed, '--updates', 100]
    if total == 100:
        args += ['--condition', condition, '--song', SONG, '--distribution', 'aligned',
                 '--axes', 'goal4', '--size', 'large', '--num-envs', 64]
    else:
        args += ['--resume', HERE/'blocks'/f'seed{seed}_{condition}_u100/train/J/final.pt']
    run_job(state, label+'_train', 'train', args, out/'train', updates=100)
    checkpoint = out/'train/J/final.pt'
    row = dict(condition=condition, seed=seed, updates=total, checkpoint=str(checkpoint),
               checkpoint_sha256=digest(checkpoint))
    for view in ('aligned', 'free_v9'):
        args = ['--checkpoint', checkpoint, '--num-envs', 32]
        if view == 'free_v9':
            args += ['--free-v9']
        run_job(state, label+'_'+view, 'evaluate', args, out/(view+'_eval'))
        evaluation = out/'free_v9_eval/evaluation' if view == 'free_v9' else out/'aligned_eval'
        metrics = analyze_evaluation(evaluation)
        write(out/(view+'_metrics.json'), metrics)
        row[view] = metrics
    state['results'][label] = row
    write(HERE/'summary.json', state['results'])
    result_table(state)
    return row


def ranking(row):
    metrics = row['free_v9']
    opening = metrics['env0_trace']['max_actual_initial_extension_deg']
    return (metrics['physical_failure_count']+metrics['wrist_failure_count'],
        -metrics['success_count'], -metrics['mean_clean_s'], metrics['mean_wrong_s'],
        metrics['mean_early_candidate_s'], max(opening),
        metrics['mean_unready_slow_wrist_s'], row['condition'])


def result_table(state):
    lines = ['# 중지 S3 F6 자연스러운 압현 준비 비교 결과', '',
        'large/64환경/H32, 동일 정렬 초기 상태/목표4축 학습. 각 열은 실패 포함 최초32환경 평가다.',
        '지원 제거는 추가학습 없이 v9/full33으로 평가한다. 후보 선정은 자동 비교이며 최종 채택이 아니다.', '',
        '| 조건 | seed | 반복 | 정렬 달성 | v9 달성 | v9 clean평균(s) | 물리/손목 실패 | 준비완료0.2s | 초기펴짐 MCP/PIP(°), env0 |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in state['results'].values():
        metrics = row['free_v9']
        opening = metrics['env0_trace']['max_actual_initial_extension_deg']
        lines.append(f"|{row['condition']}|{row['seed']}|{row['updates']}|{row['aligned']['success_count']}/32|"
            f"{metrics['success_count']}/32|{metrics['mean_clean_s']:.3f}|"
            f"{metrics['physical_failure_count']}/{metrics['wrist_failure_count']}|{metrics['ready_02_count']}/32|"
            +'/'.join(f'{value:.2f}' for value in opening)+'|')
    lines += ['', '초기펴짐은 첫 실제 관측 각을 기준으로 한 env0 첫 에피소드의0~3초 native MCP_x/PIP 값이다.',
        '이는 리셋 순간각·기하MCP·32회 평균과 다르다. 자세가 그대로인 채 기다리는 전략도 별도 영상으로 확인해야 한다.',
        '', '보상9항·오압현·누락·준비/정체·요청각 지표는 summary.json과 각 블록의 *_metrics.json에 있다.',
        '학습 상태는 progress.json/진행상황.md를 확인한다.']
    if state.get('selected_conditions'):
        lines += ['', 'seed7에서 고정한 후속 후보: '+', '.join(state['selected_conditions'])]
    if state['status'].startswith('complete'):
        lines += ['', '전체 비교가 끝났다. 숫자와 검토 영상을 함께 읽고 판단해야 하며 기본 학습은 자동 변경하지 않았다.']
        if not any(row['free_v9']['pressure_performance_sufficient'] for row in state['results'].values()):
            lines += ['현재 기록에 안정 압현 성능 기준을 충족한 모델이 없다. 자연스러움 개선이나 채택 성공으로 결론 내리지 않는다.']
    if state.get('artifact_errors'):
        lines += ['', '영상 생성 오류: '+json.dumps(state['artifact_errors'], ensure_ascii=False)]
    (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def publish_video(out, label):
    public = ROOT/'docs/2026-11-02/압현성공/video/natural_press_v3_comparison_v1'
    public.mkdir(parents=True, exist_ok=True)
    rows = []
    for kind in ('hand', 'fullbody'):
        source = out/(kind+'.mp4')
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_format',
            '-of', 'json', str(source)], text=True))
        if float(probe['format']['duration']) <= 0:
            raise ValueError('빈 영상')
        target = public/(label+'_'+kind+'.mp4')
        if target.exists():
            raise FileExistsError(str(target))
        shutil.copyfile(source, target)
        if digest(source) != digest(target):
            raise RuntimeError('영상 복사 SHA 불일치')
        rows.append(dict(path=str(target), sha256=digest(target)))
    write(out/'published_video.json', rows)


def stop(signum, frame):
    if CHILD is not None and CHILD.poll() is None:
        os.killpg(CHILD.pid, signal.SIGTERM)
        CHILD.wait(timeout=30)
    raise KeyboardInterrupt('종료 신호 수신')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    with (HERE/'gpu.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.resume:
            state = json.loads((HERE/'progress.json').read_text())
            verify_sources(state['source_seal'])
            state['status'] = 'running'
            state.pop('error', None)
        else:
            if (HERE/'progress.json').exists():
                raise FileExistsError('기존 연구를 덮어쓰지 않음')
            implementation = HERE.parents[1]/'validation/implementation_sources.json'
            verify_sources(json.loads(implementation.read_text())['files'])
            seal = {str(path.relative_to(ROOT)): digest(path) for path in sorted(source_paths())}
            state = dict(schema='guitar_learning.natural_press_comparison.v1', status='running',
                started_at=timestamp(), driver_pid=os.getpid(), jobs={}, results={}, source_seal=seal)
            write(HERE/'source_seal.json', seal)
        try:
            progress(state)
            for condition in ('E0', 'E1', 'E2', 'E3', 'E4'):
                block(state, condition, 7, 100)
            candidates = [state['results'][f'seed7_{condition}_u100'] for condition in ('E1', 'E2', 'E3', 'E4')]
            selected = [row['condition'] for row in sorted(candidates, key=ranking)[:2]]
            if state.get('selected_conditions', selected) != selected:
                raise RuntimeError('재개 시 고정 후보가 달라짐')
            state['selected_conditions'] = selected
            progress(state)
            for condition in ['E0']+selected:
                block(state, condition, 7, 200)
            for condition in ['E0']+selected:
                block(state, condition, 17, 100)
                block(state, condition, 17, 200)
            # 선별 영상을 성공 영상으로 부르지 않는다. 비교 기준과 두 후보를 모두 남긴다.
            labels = ['seed7_E0_u100']+[f'seed7_{condition}_u{updates}'
                for condition in selected for updates in (100, 200)]+[f'seed17_{selected[0]}_u200']
            state['artifact_errors'] = []
            for label in labels:
                out = HERE/'renders'/label
                try:
                    checkpoint = HERE/'blocks'/label/'free_v9_eval/model_only/J/final.pt'
                    run_job(state, label+'_render', 'render', ['--checkpoint', checkpoint,
                        '--num-envs', 4], out, render=True)
                    publish_video(out, label)
                except Exception as error:
                    state['artifact_errors'].append(dict(label=label, message=str(error)))
                    job = state['jobs'].get(label+'_render')
                    if job and job['status'] == 'running':
                        job.update(status='failed', finished_at=timestamp(), error=str(error))
                    state['current_job'] = None
                    break
            state['status'] = 'complete_with_artifact_errors' if state['artifact_errors'] else 'complete'
            state['finished_at'] = timestamp()
            result_table(state)
            progress(state)
        except BaseException as error:
            if CHILD is not None and CHILD.poll() is None:
                os.killpg(CHILD.pid, signal.SIGTERM)
                CHILD.wait(timeout=30)
            state['status'] = 'interrupted' if isinstance(error, KeyboardInterrupt) else 'failed'
            job = state.get('current_job')
            if job and job['status'] == 'running':
                job.update(status='failed', finished_at=timestamp(), error=str(error))
            state['error'] = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc())
            state['stopped_at'] = timestamp()
            progress(state)
            raise


if __name__ == '__main__':
    main()
