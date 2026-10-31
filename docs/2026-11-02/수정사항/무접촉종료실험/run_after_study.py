"""승인된 원연구와 효율 검증 뒤 무접촉 종료 조건을 독립 비교한다."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent/'개별비교연구'
EFFICIENCY = HERE.parent/'연구환경효율검증'
REPO = Path('/home/ajou/yigyu/3')
STATUS_OWNED = False
_LOCK_HANDLE = None


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temporary.replace(path)


def dependency_ready(study, efficiency):
    for label, status in (('원연구', study), ('효율 검증', efficiency)):
        if status.get('phase') == 'failed':
            raise RuntimeError(label+' 실패: 후속 실험 차단')
    return study.get('completed') is True and study.get('phase') == 'complete' and efficiency.get('phase') == 'complete'


def acceptable(candidate, baseline):
    return (candidate['mean_achieved_notes'] >= baseline['mean_achieved_notes']+.25 and
            candidate['physical_failures']+candidate['wrist_failures'] <=
            baseline['physical_failures']+baseline['wrist_failures']+2)


def training_summary(path):
    episodes = 0
    counts = dict(no_contact=0, physical=0, wrist=0)
    selected = exposed = 0
    with path.open() as stream:
        for line in stream:
            record = json.loads(line)['episode']
            episodes += 1
            termination = record.get('termination', {})
            for key, field in (('no_contact', 'no_contact_failure'), ('physical', 'physical_failure'), ('wrist', 'wrist_failure')):
                counts[key] += bool(termination.get(field, False))
            ledger = record.get('left_note_ledger', {})
            mask = ledger.get('focus_mask', [])
            selected += sum(mask)
            values = ledger.get('values', {})
            exposure = values.get('exposure_time', [])
            exposed += sum(bool(m) and x > 0 for m,x in zip(mask, exposure))
    return dict(episodes=episodes, termination_counts=counts,
        no_contact_fraction=counts['no_contact']/max(episodes, 1),
        mean_selected_targets=selected/max(episodes, 1),
        mean_exposed_targets=exposed/max(episodes, 1))


def main():
    global STATUS_OWNED, _LOCK_HANDLE
    _LOCK_HANDLE = (HERE/'runner.lock').open('w')
    fcntl.flock(_LOCK_HANDLE, fcntl.LOCK_EX | fcntl.LOCK_NB)
    if (HERE/'results.json').exists():
        raise RuntimeError('기존 실험 결과를 덮어쓰지 않음')
    STATUS_OWNED = True
    status = dict(phase='waiting_for_dependencies', pid=os.getpid())

    def refresh(**changes):
        status.update(changes, updated_at=datetime.now(timezone.utc).isoformat())
        write(HERE/'status.json', status)
        lines = ['# 무접촉 종료 실험 진행', '', '확인 시각(UTC): '+status['updated_at'],
                 '', '현재 단계: '+status['phase']]
        if status.get('active_run'):
            lines += ['', '현재 조건: '+status['active_run']]
            current = HERE/'runs'/status['active_run']/'train/J/status.json'
            if current.exists():
                training = read(current)
                lines += ['', '현재 반복: %s / 200' % (training.get('update_index', -1)+1)]
        (HERE/'progress.md').write_text('\n'.join(lines)+'\n')

    while True:
        study = read(STUDY/'status.json')
        efficiency = read(EFFICIENCY/'status.json')
        if dependency_ready(study, efficiency):
            break
        refresh(study_phase=study['phase'], efficiency_phase=efficiency['phase'])
        time.sleep(20)
    while True:
        active = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid',
            '--format=csv,noheader,nounits'], text=True).strip()
        if not active:
            break
        refresh(phase='waiting_for_free_gpu', active_pids=active.splitlines())
        time.sleep(20)
    prefix = read(STUDY/'recovery/bwrap_command_prefix.json')
    threads = read(EFFICIENCY/'results.json')['selected_threads']
    factors = []
    if read(STUDY/'selection.json').get('confirmed') is True:
        factors = read(STUDY/'recommended_recipe.json')['factors']
    seals = read(HERE/'tools_sealed.json')
    env = os.environ.copy()
    env.update(PYTHONUTF8='1', LANG='C.UTF-8', LC_ALL='C.UTF-8', CUDA_VISIBLE_DEVICES='0',
        PYTHONPATH=str(REPO/'isaacgym/python')+':'+str(REPO),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib', PYTHONUNBUFFERED='1',
        TORCH_EXTENSIONS_DIR=str(STUDY/'recovery/runtime_cache/torch'),
        MPLCONFIGDIR=str(STUDY/'recovery/runtime_cache/mpl'),
        CUDA_CACHE_PATH=str(STUDY/'recovery/runtime_cache/cuda'))
    for variable in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[variable] = str(threads)
    rows = []
    write(HERE/'inputs.json', dict(factors=factors, threads=threads,
        efficiency=read(EFFICIENCY/'results.json'),
        selection=read(STUDY/'selection.json'), source_seals=seals))
    result = dict(phase='screening', factors=factors, cpu_threads=threads, results=rows,
        production_default_changed=False, evaluation='new no-contact termination disabled; existing safety retained')

    def report():
        write(HERE/'results.json', result)
        lines = ['# 무접촉 종료 실험 결과', '', '단계: '+result['phase'], '',
            '신규 무접촉 종료를 해제한 전곡128환경 평가. 원래 물리·손목 종료는 유지한다.', '',
            '| 조건 | seed | 달성 음/67 | 물리 종료 | 손목 종료 | 학습 무접촉 종료 비율 |',
            '| --- | ---: | ---: | ---: | ---: | ---: |']
        for row in rows:
            lines.append('| %s | %d | %.3f | %d | %d | %.1f%% |' %
                (row['run_id'], row['seed'], row['mean_achieved_notes'], row['physical_failures'],
                 row['wrist_failures'], 100*row['training']['no_contact_fraction']))
        if 'selection' in result:
            lines += ['', '선별/재현 결과: '+json.dumps(result['selection'],ensure_ascii=False)]
        lines += ['', '기본 학습 설정은 변경하지 않는다. 두 seed의 단기 초기 선별이며 장기 수렴을 보장하지 않는다.']
        (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')

    def check_tools():
        for path, sha in seals.items():
            if hashlib.sha256((HERE/path).read_bytes()).hexdigest() != sha:
                raise RuntimeError('new experiment source changed: '+path)
        for manifest in ('tools_sealed.json', 'recovery/recovery_tools_sealed.json'):
            for relative, sha in read(STUDY/manifest).items():
                if hashlib.sha256((STUDY/relative).read_bytes()).hexdigest() != sha:
                    raise RuntimeError('original study tool changed: '+relative)

    def execute(name, arguments, gpu=True):
        check_tools()
        refresh(phase=name)
        child = env.copy()
        if not gpu:
            child['CUDA_VISIBLE_DEVICES'] = ''
        with (HERE/(name+'.log')).open('x') as stream:
            with subprocess.Popen(prefix+[sys.executable,'-B']+arguments, env=child, cwd=REPO,
                    stdout=stream, stderr=subprocess.STDOUT) as process:
                started = time.monotonic()
                while process.poll() is None:
                    if time.monotonic()-started > 4*3600:
                        process.kill()
                        raise TimeoutError(name)
                    refresh()
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        pass
                if process.returncode:
                    raise RuntimeError('subprocess failed: '+name)
        check_tools()

    execute('check_sources', [str(STUDY/'recovery/check_frozen.py')], gpu=False)
    execute('cpu_tests', ['-m','unittest','discover','-s',str(HERE),'-p','test_*.py','-v'], gpu=False)
    # 큰 비교 예산을 쓰기 전에 각 계약의 실제 GPU 저장/복원을 확인한다.
    for threshold in (0,5,3):
        smoke = HERE/'smoke'/('threshold'+str(threshold))
        wrapper = [str(HERE/'termination_runtime.py'),'--threshold',str(threshold),'--threads',str(threads)]
        execute('smoke%d_train' % threshold, wrapper+['train','--updates','8','--num-envs','4',
            '--size','large','--seed','7','--out',str(smoke/'train'),'--factors']+factors)
        execute('smoke%d_evaluate' % threshold, wrapper+['evaluate','--checkpoint',str(smoke/'train/J/final.pt'),
            '--num-envs','4','--out',str(smoke/'evaluation')])
    def trial(threshold, seed):
        name = 'baseline_s%d' % seed if threshold == 0 else 'no_contact%d_s%d' % (threshold,seed)
        folder = HERE/'runs'/name
        folder.mkdir(parents=True,exist_ok=False)
        refresh(active_run=name)
        wrapper = [str(HERE/'termination_runtime.py'),'--threshold',str(threshold),'--threads',str(threads)]
        execute(name+'_train', wrapper+['train','--updates','200','--num-envs','1024',
            '--size','large','--seed',str(seed),'--out',str(folder/'train'),'--factors']+factors)
        training = read(folder/'train/J/report.json')
        if not training['completed'] or training.get('failure') or training['updates_in_run'] != 200:
            raise RuntimeError('incomplete training: '+name)
        execute(name+'_evaluate', wrapper+['evaluate','--checkpoint',str(folder/'train/J/final.pt'),
            '--num-envs','128','--out',str(folder/'evaluation')])
        evaluation = read(folder/'evaluation/report.json')
        if not evaluation['completed'] or evaluation.get('failure') or evaluation['episodes'] != 128:
            raise RuntimeError('incomplete strict evaluation: '+name)
        summary = evaluation['summary']
        row = dict(run_id=name, threshold=threshold, seed=seed,
            mean_achieved_notes=summary['mean_left_success_count'],
            physical_failures=summary['physical_failure'], wrist_failures=summary['wrist_failure'],
            timeline_complete=summary['timeline_complete'],
            training=training_summary(folder/'train/J/episodes.jsonl'))
        metrics = [json.loads(line) for line in (folder/'train/J/learning_metrics.jsonl').read_text().splitlines()]
        row['last20_reward_component_means'] = {key:sum(m['reward_component_means'][key] for m in metrics[-20:])/len(metrics[-20:])
            for key in metrics[-1]['reward_component_means']}
        rows.append(row)
        report()
        return row
    baseline = trial(0,7)
    candidates = [trial(n,7) for n in (5,3)]
    qualified = [r for r in candidates if acceptable(r,baseline)]
    if qualified:
        selected = max(qualified,key=lambda r:r['mean_achieved_notes'])
        result['phase'] = 'confirming'
        report()
        reference = trial(0,17)
        confirmation = trial(selected['threshold'],17)
        confirmed = acceptable(confirmation,reference)
        result['selection'] = dict(threshold=selected['threshold'],confirmed=confirmed,
            reason='both seeds pass' if confirmed else 'not reproduced on second seed')
        if confirmed:
            write(HERE/'recommended_termination.json', dict(threshold=selected['threshold'],
                factors=factors, threads=threads, implementation_sha256=seals['termination_runtime.py'],
                evaluation='disabled in explicit evaluation view', production_default_changed=False))
    else:
        result['selection'] = dict(confirmed=False,reason='no seed7 candidate passes screening')
    result['phase'] = 'complete'
    report()
    refresh(phase='complete',active_run=None)


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        if STATUS_OWNED:
            write(HERE/'status.json',dict(phase='failed',failure=repr(error),updated_at=datetime.now(timezone.utc).isoformat()))
        raise
