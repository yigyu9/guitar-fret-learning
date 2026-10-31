"""원연구가 정상 종료된 뒤 동일 계산의 CPU 스레드 환경만 비교한다."""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent/'개별비교연구'
REPO = Path('/home/ajou/yigyu/3')


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def state(phase, **extra):
    write(HERE/'status.json', dict(phase=phase, updated_at=datetime.now(timezone.utc).isoformat(), **extra))


def ready(status, alive):
    if status.get('phase') == 'failed':
        raise RuntimeError('원연구 실패: 후속 GPU 실험을 시작하지 않음')
    return status.get('completed') is True and status.get('phase') == 'complete' and not alive


def alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except ProcessLookupError:
        return False


def equivalent(candidate, reference):
    keys = ('count', 'timeline_complete', 'physical_failure', 'wrist_failure',
            'mean_left_success_count', 'mean_reward', 'mean_cost')
    return all(math.isfinite(candidate[k]) and math.isclose(candidate[k], reference[k], rel_tol=1e-6, abs_tol=1e-5) for k in keys)


def main():
    lock = (HERE/'runner.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (HERE/'results.json').exists():
        raise RuntimeError('기존 결과 존재: refuse overwrite')
    while True:
        current = read(STUDY/'status.json')
        if ready(current, alive(current['pid'])):
            break
        state('waiting_for_study', study_phase=current['phase'])
        time.sleep(20)
    # 다른 GPU 계산 작업이 있으면 경쟁시키지 않고 대기한다.
    while True:
        active = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid',
            '--format=csv,noheader,nounits'], text=True).strip()
        if not active:
            break
        state('waiting_for_free_gpu', active_pids=active.splitlines())
        time.sleep(20)
    prefix = read(STUDY/'recovery/bwrap_command_prefix.json')
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', LANG='C.UTF-8', LC_ALL='C.UTF-8',
        CUDA_VISIBLE_DEVICES='0', PYTHONUNBUFFERED='1',
        PYTHONPATH=str(REPO/'isaacgym/python')+':'+str(REPO),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
        TORCH_EXTENSIONS_DIR=str(STUDY/'recovery/runtime_cache/torch'),
        MPLCONFIGDIR=str(STUDY/'recovery/runtime_cache/mpl'),
        CUDA_CACHE_PATH=str(STUDY/'recovery/runtime_cache/cuda'))
    # 원연구 봉인은 유지하며 후속 실험 진입 시 다시 검사한다.
    for manifest in ('tools_sealed.json', 'recovery/recovery_tools_sealed.json'):
        for relative, expected in read(STUDY/manifest).items():
            if hashlib.sha256((STUDY/relative).read_bytes()).hexdigest() != expected:
                raise RuntimeError('sealed tool changed: '+relative)

    def run(name, arguments, threads, cpu=False):
        state(name, threads=threads)
        child = env.copy()
        for variable in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            child[variable] = str(threads)
        if cpu:
            child['CUDA_VISIBLE_DEVICES'] = ''
        with (HERE/(name+'.log')).open('x') as output:
            actual = ([str(HERE/'thread_runtime.py'), str(threads)]+arguments[2:]
                      if arguments[:2] == ['-m', 'guitar_learning.tool.experiments.finger_ablation'] else arguments)
            subprocess.run(prefix+[sys.executable, '-B']+actual, env=child,
                cwd=REPO, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=4*3600)

    run('check_sources', [str(STUDY/'recovery/check_frozen.py')], 1, cpu=True)
    factors = []
    recipe = STUDY/'recommended_recipe.json'
    if recipe.exists():
        selection = read(STUDY/'selection.json')
        if selection.get('confirmed') is True:
            factors = read(recipe)['factors']
    rows = []
    module = ['-m', 'guitar_learning.tool.experiments.finger_ablation']
    tests = ['-m', 'unittest', 'guitar_learning.tests.test_ppo',
        'guitar_learning.tests.test_decision_ppo', 'guitar_learning.tests.test_ppo_logging',
        'guitar_learning.tests.test_ppo_signal_balance', 'guitar_learning.tests.test_finger_ablation_learning',
        'guitar_learning.tests.test_finger_ablation_contact',
        'guitar_learning.tests.test_finger_ablation_runtime', '-v']
    for threads in (1, 2, 4):
        run('cpu_threads'+str(threads), tests, threads, cpu=True)
    for seed, order in ((7, (1, 2, 4)), (17, (4, 2, 1))):
        for threads in order:
            name = 'threads%d_s%d' % (threads, seed)
            folder = HERE/name
            folder.mkdir(exist_ok=False)
            run(name+'_train', module+['train', '--out', str(folder/'train'),
                '--updates', '16', '--num-envs', '1024', '--size', 'large',
                '--seed', str(seed), '--factors']+factors, threads)
            if ('torch_intraop_threads=%d;' % threads) not in (HERE/(name+'_train.log')).read_text():
                raise RuntimeError('missing actual thread verification: '+name)
            report = read(folder/'train/J/report.json')
            if not report['completed'] or report.get('failure') or report['updates_in_run'] != 16:
                raise RuntimeError('training verification failed: '+name)
            metrics = [json.loads(line) for line in (folder/'train/J/learning_metrics.jsonl').read_text().splitlines()]
            times = [x['collection_s']+x['update_s'] for x in metrics[4:]]
            if len(times) != 12 or not all(math.isfinite(t) and t > 0 for t in times):
                raise RuntimeError('incomplete/nonfinite timing: '+name)
            run(name+'_evaluate', module+['evaluate', '--checkpoint', str(folder/'train/J/final.pt'),
                '--out', str(folder/'evaluation'), '--num-envs', '128'], threads)
            evaluation = read(folder/'evaluation/report.json')
            if not evaluation['completed'] or evaluation.get('failure') or evaluation['episodes'] != 128:
                raise RuntimeError('strict evaluation failed: '+name)
            rows.append(dict(seed=seed, threads=threads, factors=factors,
                median_step_s=statistics.median(times), summary=evaluation['summary']))
            write(HERE/'partial_results.json', rows)
    eligible = []
    for threads in (2, 4):
        pairs = [(next(r for r in rows if r['seed']==seed and r['threads']==threads),
                  next(r for r in rows if r['seed']==seed and r['threads']==1)) for seed in (7, 17)]
        if all(equivalent(c['summary'], b['summary']) and c['median_step_s'] <= .95*b['median_step_s'] for c,b in pairs):
            eligible.append(threads)
    selected = min(eligible, key=lambda t: statistics.mean(r['median_step_s'] for r in rows if r['threads']==t)) if eligible else 1
    write(HERE/'results.json', dict(selected_threads=selected, rows=rows,
        scope='CPU thread environment only; 16-update timing and strict evaluation, not convergence proof'))
    settings = ''.join('export %s=%d\n' % (v, selected) for v in
        ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'))
    (HERE/'recommended_environment.sh').write_text('# 후속 연구 전용. 원연구와 기본 실행 설정은 변경하지 않는다.\n'+settings+
        '# Torch 스레드 고정 대체도 필요: 아래 래퍼로 연구 CLI 실행\n'+
        '# python '+str(HERE/'thread_runtime.py')+' '+str(selected)+' train --out NEW ...\n')
    (HERE/'RESULTS.md').write_text('# 연구 환경 효율 검증 결과\n\n선택한 CPU 스레드 수: %d\n\n' % selected+
        ('두 seed 모두 5% 이상 빠르고 평가가 일치하는 후보를 채택했다.' if eligible else '채택 기준을 만족하는 후보가 없어 기존 스레드 1을 유지한다.')+
        '\n\n세부 결과는 results.json, 설정은 recommended_environment.sh를 따른다. 장기 학습 품질을 증명하는 검증은 아니다.\n')
    state('complete', selected_threads=selected)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        state('failed', failure=repr(error))
        raise
