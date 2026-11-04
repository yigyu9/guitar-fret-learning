"""C1 후처리를 기다린 뒤 봉인 V5의 B/P 비교를 순차 실행한다."""
import argparse
import copy
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

import psutil

SELF = Path(__file__).resolve()
STUDY = SELF.parents[1]
ROOT = next(p for p in STUDY.parents if (p/'guitar_learning/train.py').is_file())
RUNTIME = STUDY/'작업자료/source_snapshot'
OUTPUT = RUNTIME/'study_outputs'
WORK = STUDY/'작업자료'
OLD = ROOT/'docs/2026-11-09/압현_v5_C1_장기학습_v1'
HSTUDY = ROOT/'docs/2026-11-09/H실험'
KST = timezone(timedelta(hours=9))
DEADLINE = datetime(2026, 11, 5, 8, tzinfo=KST)
TRAIN_END = DEADLINE-timedelta(hours=1)
PROFILES = {'B': 'corrected', 'P': 'preparation'}
TOTAL, BATCH, PERIOD = 16777216, 32768, 128


def now():
    return datetime.now(KST)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    temporary.replace(path)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def htool():
    return load('horizon_read_only', HSTUDY/'도구/study.py')


def prepare():
    """소스/입력 목록으로만 복사하여 다른 실험의 출력·캐시는 가져오지 않는다."""
    helper = htool()
    checked = helper.check(ROOT, HSTUDY)
    payload = read(HSTUDY/'기준봉인.json')
    if RUNTIME.exists() or (STUDY/'입력봉인.json').exists():
        raise ValueError('기존 준비본은 덮어쓰지 않습니다')
    RUNTIME.parent.mkdir(parents=True, exist_ok=True)
    temporary = RUNTIME.with_name('source_snapshot_preparing')
    temporary.mkdir()
    try:
        helper.copy_sources(HSTUDY/'작업자료/source_snapshot', temporary, payload['files'])
        if helper.manifest(temporary) != payload['files']:
            raise ValueError('독립 실행 사본 SHA/파일 집합 불일치')
        helper.check(ROOT, HSTUDY)
        temporary.rename(RUNTIME)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    write(STUDY/'입력봉인.json', dict(schema='press_bp_inputs.v1',
        source_seal_sha256=checked['seal_sha256'], files=payload['files'],
        source_copy='H실험의 검증된 봉인 입력; 출력/캐시 제외'))
    write(STUDY/'실험설정.json', dict(schema='press_bp_study.v1', target='C1', seed=7,
        num_envs=1024, horizon=32, updates=512, checkpoint_every=128,
        planned_transitions=TOTAL, full_song_after=TOTAL//4,
        profiles=PROFILES, train_cutoff=TRAIN_END.isoformat(), deadline=DEADLINE.isoformat(),
        evaluation_num_envs=32, max_wall_policy='train cutoff minus120s; operational limit only'))
    return check_inputs()


def check_inputs():
    payload = read(STUDY/'입력봉인.json')
    if htool().manifest(RUNTIME) != payload['files']:
        raise ValueError('독립 runtime 입력 변경')
    if read(STUDY/'실험설정.json')['planned_transitions'] != TOTAL:
        raise ValueError('원래 경험 예산 불일치')
    return dict(completed=True, files=len(payload['files']),
                source_seal_sha256=payload['source_seal_sha256'])


def control_paths():
    return [SELF, SELF.parent/'inspect_inputs.py', SELF.parent/'analyze.py',
            STUDY/'입력봉인.json', STUDY/'실험설정.json', HSTUDY/'도구/study.py']


def seal_controls():
    path = STUDY/'실행봉인.json'
    if path.exists():
        raise ValueError('감독 도구 봉인은 덮어쓰지 않습니다')
    pins = {str(p): sha(p) for p in control_paths()}
    write(path, dict(created_at=now().isoformat(), files=pins))
    return pins


def check_controls():
    for path, expected in read(STUDY/'실행봉인.json')['files'].items():
        if sha(path) != expected:
            raise ValueError('실행 중 감독/설정 변경: '+path)


def cpu_env():
    return dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1',
                OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')


def inspect_checkpoint(checkpoint, digest, condition):
    result = subprocess.run([sys.executable, str(SELF.parent/'inspect_inputs.py'),
        '--runtime', str(RUNTIME), '--checkpoint', str(checkpoint), '--sha', digest,
        '--profile', PROFILES[condition]], cwd=RUNTIME, env=cpu_env(),
        capture_output=True, text=True, timeout=180, check=True)
    value = json.loads(result.stdout)
    if value.get('completed') is not True:
        raise ValueError('strict checkpoint 검증 실패')
    return value


def lines(path):
    if not Path(path).exists():
        return []
    with Path(path).open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream if line.endswith('\n') and line.strip()]


def last_metric(stage):
    path = stage/'learning_metrics.jsonl'
    if not path.exists():
        return None
    with path.open('rb') as stream:
        stream.seek(max(0, path.stat().st_size-200000))
        data = stream.read()
    complete = data[:data.rfind(b'\n')+1].splitlines()
    return json.loads(complete[-1]) if complete else None


def manifest(stage):
    result = []
    for row in lines(stage/'checkpoint_manifest.jsonl'):
        path = stage/row['path']
        if path.resolve().parent != stage.resolve() or not path.is_file():
            raise ValueError('저장 manifest 경로 불일치')
        if sha(path) != row['sha256']:
            raise ValueError('저장 모델 SHA 불일치')
        result.append(dict(row, checkpoint=str(path)))
    return result


def command(*args, render=False):
    argv = [sys.executable, str(RUNTIME/'scripts/tab2body.py'), '--cache-root',
            str(RUNTIME/'.runtime/cache'), 'run', '-m',
            'guitar_learning.tool.experiments.press_sequence', *map(str, args)]
    if render and not os.environ.get('DISPLAY'):
        if not shutil.which('xvfb-run'):
            raise ValueError('화면 없는 렌더에 xvfb-run이 필요합니다')
        argv = ['xvfb-run', '-a', *argv]
    return argv


def train_argv(condition, out, *, resume=None, committed=0):
    if committed not in (0, 128, 256, 384):
        raise ValueError('128회 공통 경계에서만 복구합니다')
    wall = int((TRAIN_END-now()).total_seconds())-120
    if wall <= 0:
        raise TimeoutError('새 학습 시작 시각 종료')
    args = ['train', '--updates', 512-committed, '--checkpoint-every', PERIOD,
            '--max-wall-seconds', wall, '--out', out]
    if resume:
        args += ['--resume', resume]
    else:
        args += ['C1', '--size', 'large', '--num-envs', 1024, '--horizon', 32,
                 '--seed', 7, '--no-include-pelvis', '--initial-support-std', .15,
                 '--initial-finger-std', .35, '--improvement-profile', PROFILES[condition]]
    return command(*args)


def status(**changes):
    path = STUDY/'진행상황.json'
    value = read(path) if path.exists() else {}
    value.update(updated_at=now().isoformat(), supervisor_pid=os.getpid(), **changes)
    write(path, value)
    return value


def gpu_jobs():
    result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=15, check=True)
    return result.stdout.strip()


def enough_time(seconds_per_transition, post_seconds, at=None):
    at = at or now()
    train_seconds = 2*TOTAL*seconds_per_transition*1.20
    return (at+timedelta(seconds=train_seconds) <= TRAIN_END and
            at+timedelta(seconds=train_seconds+post_seconds) <= DEADLINE)


def wait_original():
    """GPU 유휴만으로 원래 연구의 후처리 완료를 판단하지 않는다."""
    while True:
        check_controls()
        original = read(OLD/'진행상황.json')
        if original.get('failure'):
            raise RuntimeError('기존 C1 실패: '+str(original['failure']))
        if original.get('completed') is True:
            pid = original.get('supervisor_pid')
            alive = False
            if pid and psutil.pid_exists(pid):
                try:
                    proc = psutil.Process(pid)
                    alive = proc.status() != psutil.STATUS_ZOMBIE and any(
                        'resume_c1_after_reboot.py' in arg for arg in proc.cmdline())
                except psutil.NoSuchProcess:
                    pass
            if not alive:
                if gpu_jobs():
                    raise RuntimeError('C1 완료 뒤 GPU의 다른 작업을 보존하며 새 실험 중단')
                report = read(OLD/'작업자료/runtime/study_outputs/학습/attempt02/J/report.json')
                if not report.get('completed') or report.get('optimizer_updates') != 2000:
                    raise ValueError('기존 C1 2000회 완료 증거 누락')
                for name in ('hand.mp4', 'fullbody.mp4'):
                    if not (OLD/'동영상'/name).is_file():
                        raise ValueError('기존 C1 대표 영상 누락')
                return original
        if now() >= TRAIN_END:
            return None
        task = original.get('tasks', {}).get(original.get('current_task'), {})
        status(phase='waiting_for_original_c1', current_condition=None, running_pid=None,
               original_task=original.get('current_task'), original_updates=task.get('optimizer_updates'),
               original_updated_at=original.get('updated_at'),
               next_step='기존 C1의 학습·평가·분석·영상과 감독 종료 대기')
        time.sleep(20)


def valid_report(out, kind, checkpoint=None):
    path = out/'J/report.json' if kind == 'train' else out/'report.json'
    report = read(path)
    if not report.get('completed') or report.get('failure'):
        raise ValueError('native 실행 미완료: '+str(path))
    for key in ('changed_inputs', 'missing_import_pins', 'cleanup_errors'):
        if report.get(key):
            raise ValueError('native 감사 실패: '+key)
    if kind == 'train':
        if not report.get('lifecycle_verified') or not read(out/'report.json').get('completed'):
            raise ValueError('학습 lifecycle 검증 실패')
    elif kind == 'evaluate':
        if not (report.get('episodes') == 32 and report.get('scope') == 'full_song' and
                report.get('failed_episodes_in_denominator') and
                report.get('first_episode_per_env_per_batch') and report.get('gpu_scene', {}).get('closed')):
            raise ValueError('전곡32환경 평가/종료 계약 불일치')
    elif kind == 'render':
        if not (report.get('scene_closed') and report.get('source_checkpoint_pins_validated') and
                report.get('source_pins_unchanged') and
                report.get('encoding_exit_codes') == {'hand': 0, 'fullbody': 0}):
            raise ValueError('영상 source/장면/encoding 검증 실패')
    if checkpoint and report.get('checkpoint_sha256') != sha(checkpoint):
        raise ValueError('실행 결과 checkpoint SHA 불일치')
    return report


def run_job(argv, name, kind, condition, checkpoint=None):
    check_controls()
    check_inputs()
    if gpu_jobs():
        raise RuntimeError('다른 GPU 작업이 있어 새 작업을 시작하지 않습니다')
    out = Path(argv[argv.index('--out')+1])
    if out.exists():
        raise ValueError('native 출력은 새 경로여야 합니다')
    log_path = WORK/(name+'.log')
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', MAX_JOBS='2')
    env.pop('CUDA_VISIBLE_DEVICES', None)
    env.pop('PYTHONOPTIMIZE', None)
    write(WORK/(name+'_command.json'), dict(argv=argv, cwd=str(RUNTIME), started_at=now().isoformat()))
    started, last_progress, token = time.monotonic(), time.monotonic(), None
    peak_gpu, peak_rss = 0., 0
    initial_checked = False
    latest_checkpoint = None
    checked_checkpoints = set()
    stage = out/'J' if kind == 'train' else out
    with log_path.open('x', encoding='utf-8') as log, (WORK/(name+'_resources.jsonl')).open('x') as resource:
        child = subprocess.Popen(argv, cwd=RUNTIME, env=env, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while child.poll() is None:
                check_controls()
                metric = last_metric(stage) if kind == 'train' else None
                if kind == 'train':
                    for saved in lines(stage/'checkpoint_manifest.jsonl'):
                        model = stage/saved['path']
                        if model.resolve().parent != stage.resolve():
                            raise ValueError('진행 저장 경로 불일치')
                        key = (str(model), saved['sha256'])
                        if key not in checked_checkpoints:
                            if sha(model) != saved['sha256']:
                                raise ValueError('진행 저장 모델 SHA 불일치')
                            checked_checkpoints.add(key)
                        latest_checkpoint = dict(path=str(model), sha256=saved['sha256'],
                                                 updates=saved['optimizer_updates'])
                    if not initial_checked and (stage/'initial.pt').is_file() and latest_checkpoint:
                        saved_initial = next(r for r in manifest(stage) if r['path'] == 'initial.pt')
                        initial = inspect_checkpoint(stage/'initial.pt', saved_initial['sha256'], condition)
                        if initial['updates'] == 0:
                            digest_path = STUDY/'검증/초기모델.json'
                            digests = read(digest_path) if digest_path.exists() else {}
                            digests[condition] = initial['tensor_sha256']
                            if len(set(digests.values())) != 1:
                                raise ValueError('B/P 초기 정책 tensor 불일치')
                            write(digest_path, digests)
                        write(WORK/(name+'_initial_inspection.json'), initial)
                        initial_checked = True
                try:
                    monitor = read(stage/'status.json')
                except (FileNotFoundError, json.JSONDecodeError):
                    monitor = {}
                current = (metric.get('optimizer_updates') if metric else None,
                           monitor.get('update_index'), monitor.get('ticks'), log_path.stat().st_size)
                if current != token:
                    token, last_progress = current, time.monotonic()
                if time.monotonic()-last_progress > 1200:
                    raise TimeoutError('진행/로그가1200초간 멈춤')
                if shutil.disk_usage(STUDY).free < 8*1024**3:
                    raise OSError('여유 저장공간8GiB 미만')
                info = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=15, check=True)
                used = float(info.stdout.splitlines()[0])
                rss = 0
                try:
                    processes = [psutil.Process(child.pid)]+psutil.Process(child.pid).children(recursive=True)
                    for proc in processes:
                        try:
                            rss += proc.memory_info().rss
                        except psutil.NoSuchProcess:
                            pass
                except psutil.NoSuchProcess:
                    pass
                peak_gpu, peak_rss = max(peak_gpu, used), max(peak_rss, rss)
                resource.write(json.dumps(dict(time=now().isoformat(), gpu_total_used_mib=used,
                                              process_tree_rss_bytes=rss))+'\n')
                resource.flush()
                elapsed = time.monotonic()-started
                update = metric['optimizer_updates'] if metric else 0
                rate = metric['transitions']/(metric['collection_s']+metric['update_s']) if metric else None
                status(phase=kind+'_running', current_condition=condition, running_pid=child.pid,
                    stage=name, global_update=update, committed_transitions=update*BATCH,
                    collection_transitions_per_s=rate, elapsed_s=elapsed,
                    estimated_stage_end=(now()+timedelta(seconds=(512-update)*BATCH/rate)).isoformat()
                        if rate and kind == 'train' else None,
                    native_phase=monitor.get('phase'), native_ticks=monitor.get('ticks'),
                    latest_checkpoint=latest_checkpoint,
                    peak_gpu_used_mib=peak_gpu, peak_process_tree_rss_bytes=peak_rss,
                    next_step='B/P 학습→동일 전이 평가10회→분석→대표 영상')
                time.sleep(10)
            code = child.wait()
        except BaseException:
            # 즉시 kill 대신 native에 중단을 알리고 유효 저장/장면 종료를 기다린다.
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGINT)
                try:
                    child.wait(timeout=180)
                except subprocess.TimeoutExpired:
                    status(phase='child_cleanup_unconfirmed', running_pid=child.pid)
            raise
    check_controls()
    check_inputs()
    write(WORK/(name+'_receipt.json'), dict(returncode=code, elapsed_s=time.monotonic()-started,
        peak_gpu_used_mib=peak_gpu, peak_process_tree_rss_bytes=peak_rss, log=str(log_path)))
    if code:
        raise RuntimeError('native 작업 실패: '+name+'; '+str(log_path))
    return valid_report(out, kind, checkpoint)


def transient(log):
    text = Path(log).read_text(encoding='utf-8', errors='replace').lower()
    if any(x in text for x in ('nan', 'nonfinite', 'sha mismatch', 'identity', 'input changed',
                               'assertion', 'illegal memory', 'out of memory')):
        return False
    return any(x in text for x in ('interrupted system call', 'temporarily unavailable',
                                   'connection reset by peer'))


def train_condition(condition, inputs):
    base = OUTPUT/'학습'/(condition+'_seed7')
    first = base/'attempt01'
    runs = inputs['training_runs'][condition]
    runs.append(str(first/'J'))
    write(STUDY/'analysis_inputs.json', inputs)
    try:
        report = run_job(train_argv(condition, first), condition+'_train01', 'train', condition)
    except (RuntimeError, TimeoutError) as error:
        log = WORK/(condition+'_train01.log')
        if not log.exists() or not transient(log):
            raise
        candidates = [r for r in manifest(first/'J') if int(r['optimizer_updates']) in (0, 128, 256, 384)]
        if not candidates or now() >= TRAIN_END:
            raise
        selected = max(candidates, key=lambda r: r['optimizer_updates'])
        checked = inspect_checkpoint(selected['checkpoint'], selected['sha256'], condition)
        committed = checked['updates']
        inputs['committed_prefix'][str(first/'J')] = committed
        second = base/'attempt02'
        runs.append(str(second/'J'))
        write(STUDY/'analysis_inputs.json', inputs)
        write(WORK/(condition+'_recovery.json'), dict(reason=str(error), checkpoint=selected,
            discarded_tail_after_update=committed, scope='Adam/RNG/sampler/exposure; fresh prepared episodes'))
        report = run_job(train_argv(condition, second, resume=selected['checkpoint'], committed=committed),
                         condition+'_train02', 'train', condition)
    final = Path(runs[-1])/'final.pt'
    records = manifest(Path(runs[-1]))
    row = next(r for r in records if Path(r['checkpoint']) == final)
    checked = inspect_checkpoint(final, row['sha256'], condition)
    inputs['committed_prefix'][runs[-1]] = checked['updates']
    write(STUDY/'analysis_inputs.json', inputs)
    if checked['updates'] != 512 or report['curriculum']['committed_transitions'] != TOTAL:
        raise TimeoutError('벽시계 종료: 전체 예산 미완료')
    return checked


def expected_models(condition, inputs):
    chosen = {}
    for directory in inputs['training_runs'][condition]:
        limit = inputs['committed_prefix'].get(directory, 0)
        for row in manifest(Path(directory)):
            update = int(row['optimizer_updates'])
            if update <= limit and update in (0, 128, 256, 384, 512):
                chosen.setdefault(update, row)
    return chosen


def analyze(inputs):
    write(STUDY/'analysis_inputs.json', inputs)
    result = subprocess.run([sys.executable, str(SELF.parent/'analyze.py'), '--study', str(STUDY)],
        cwd=RUNTIME, env=cpu_env(), capture_output=True, text=True, timeout=1200)
    (WORK/'analysis_stdout.log').write_text(result.stdout, encoding='utf-8')
    (WORK/'analysis_stderr.log').write_text(result.stderr, encoding='utf-8')
    if result.returncode:
        raise RuntimeError('분석 실패: '+result.stderr[-1200:])


def render_results(inputs):
    selected = read(STUDY/'분석/선정모델.json')
    videos = []
    for condition in PROFILES:
        item = selected.get(condition)
        if not item:
            continue
        checkpoint = Path(item['checkpoint'])
        inspect_checkpoint(checkpoint, item['sha256'], condition)
        out = OUTPUT/'영상'/(condition+'_seed7')
        run_job(command('render', checkpoint, '--scope', 'full_song', '--num-envs', 1,
            '--out', out, render=True), condition+'_render', 'render', condition, checkpoint)
        for kind in ('hand', 'fullbody'):
            source = out/(kind+'.mp4')
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-i', str(source), '-f', 'null', '-'],
                           capture_output=True, check=True, timeout=600)
            target = STUDY/'동영상'/(condition+'_'+kind+'.mp4')
            target.parent.mkdir(exist_ok=True)
            with source.open('rb') as src, target.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            if sha(source) != sha(target):
                raise ValueError('대표 영상 복사 SHA 불일치')
            videos.append(dict(condition=condition, file=str(target), sha256=sha(target),
                               checkpoint_sha256=item['sha256']))
    write(STUDY/'분석/영상검증.json', dict(completed=True, videos=videos))


def supervise():
    check_controls()
    check_inputs()
    inputs = dict(runtime=str(RUNTIME), training_runs={'B': [], 'P': []},
                  evaluation_runs={'B': [], 'P': []}, committed_prefix={}, status='pending')
    status(phase='waiting_for_original_c1', started_at=now().isoformat(), completed=False,
           deadline=DEADLINE.isoformat(), train_cutoff=TRAIN_END.isoformat(), error=None)
    try:
        original = wait_original()
        if original is None:
            inputs['status'] = 'insufficient_time'
            status(phase='insufficient_time', running_pid=None, reason='C1 후처리가 학습 마감 전 끝나지 않음')
            return
        metrics = lines(OLD/'작업자료/runtime/study_outputs/학습/attempt02/J/learning_metrics.jsonl')[-100:]
        seconds = max(1/2000., sum(r['collection_s']+r['update_s'] for r in metrics)/sum(r['transitions'] for r in metrics))
        eval_times = [t['elapsed_s'] for name, t in original.get('tasks', {}).items()
                      if '평가' in name and t.get('elapsed_s')]
        post = max(3600., 10*max(eval_times or [0])*1.25+600)
        admitted = enough_time(seconds, post)
        write(STUDY/'검증/시간진입판정.json', dict(checked_at=now().isoformat(), admitted=admitted,
            seconds_per_transition=seconds, pair_training_estimate_s=2*TOTAL*seconds*1.2,
            post_reserve_s=post, deadline=DEADLINE.isoformat(), cutoff=TRAIN_END.isoformat()))
        if not admitted:
            inputs['status'] = 'insufficient_time'
            status(phase='insufficient_time', running_pid=None, reason='전체 B/P와 후처리의 마감 여유 부족')
            return
        initial_digests = []
        for condition in PROFILES:
            train_condition(condition, inputs)
            model = expected_models(condition, inputs)[0]
            initial_digests.append(inspect_checkpoint(model['checkpoint'], model['sha256'], condition)['tensor_sha256'])
        if initial_digests[0] != initial_digests[1]:
            raise ValueError('B/P 초기 모델 tensor SHA 불일치')
        models_by_condition = {condition: expected_models(condition, inputs) for condition in PROFILES}
        for condition, models in models_by_condition.items():
            if set(models) != {0, 128, 256, 384, 512}:
                raise ValueError('정확한 공통 평가 모델 누락')
        eval_estimate = max(eval_times or [120.])*1.25
        evaluation_complete = True
        # 마감 지연 때도 양쪽 최종 모델을 먼저 확보하고, 나머지 학습 곡선을 보강한다.
        for update in (512, 0, 128, 256, 384):
            if now()+timedelta(seconds=2*eval_estimate+600) > DEADLINE:
                evaluation_complete = False
                break
            for condition in PROFILES:
                model = models_by_condition[condition][update]
                checkpoint = Path(model['checkpoint'])
                inspect_checkpoint(checkpoint, model['sha256'], condition)
                out = OUTPUT/'평가'/(condition+'_seed7')/('T%09d' % (update*BATCH))
                run_job(command('evaluate', checkpoint, '--scope', 'full_song', '--num-envs', 32,
                    '--out', out), condition+'_eval%03d' % update, 'evaluate', condition, checkpoint)
                inputs['evaluation_runs'][condition].append(str(out))
                write(STUDY/'analysis_inputs.json', inputs)
        inputs['status'] = 'training_evaluation_complete' if evaluation_complete else 'partial_evaluation'
        analyze(inputs)
        render_results(inputs)
        inputs['status'] = 'complete' if evaluation_complete else 'partial_evaluation'
        analyze(inputs)
        status(phase=inputs['status'], completed=evaluation_complete, running_pid=None, finished_at=now().isoformat(),
               report=str(STUDY/'분석/REPORT.md'), next_step='B/P 결과 검토; L/E는 후속 연구')
    except BaseException as error:
        inputs['status'] = 'partial_or_failed'
        status(phase='partial_or_failed', completed=False, running_pid=None,
               error=dict(type=type(error).__name__, message=str(error)))
        try:
            for condition, directories in inputs['training_runs'].items():
                for directory in directories:
                    rows = manifest(Path(directory))
                    if rows:
                        inputs['committed_prefix'].setdefault(directory, max(int(r['optimizer_updates']) for r in rows))
            analyze(inputs)
        except BaseException as analysis_error:
            write(STUDY/'검증/실패보고.json', dict(error=str(error), analysis_error=str(analysis_error)))
        raise
    finally:
        write(STUDY/'analysis_inputs.json', inputs)
        if inputs['status'] == 'insufficient_time':
            report_path = STUDY/'분석/REPORT.md'
            report_path.parent.mkdir(exist_ok=True)
            report_path.write_text('# 야간 B/P 비교 결과\n\n상태: 시간 부족으로 새 비교를 시작하지 않음.\n\n'
                '기존 C1의 학습·평가·영상 완료를 우선 보존했다. 계획한 동일 예산 B/P와 후처리가 '
                '마감 안에 들어갈 시간적 여유가 없어 조건을 임의 축소하지 않았다.\n\n'
                '기존 결과: '+str(OLD)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'seal', 'check', 'start', 'detach'))
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    if args.command == 'prepare':
        print(json.dumps(prepare(), ensure_ascii=False))
    elif args.command == 'seal':
        print(json.dumps(seal_controls(), ensure_ascii=False))
    elif args.command == 'check':
        check_controls()
        print(json.dumps(check_inputs(), ensure_ascii=False))
    elif args.command == 'detach':
        check_controls()
        with (WORK/'supervisor.log').open('x') as log:
            process = subprocess.Popen([sys.executable, '-u', str(SELF), 'start'], cwd=ROOT,
                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
                    OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1'),
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        write(WORK/'supervisor_pid.json', dict(pid=process.pid, started_at=now().isoformat()))
        print(json.dumps(dict(pid=process.pid, log=str(WORK/'supervisor.log'))))
    else:
        with (WORK/'supervisor.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            supervise()


if __name__ == '__main__':
    main()
