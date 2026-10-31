"""완료 모델 5개의 v9 자유 평가와 A 모델 2개의 잡음 배율 평가를 순서대로 수행한다."""
import os
for name in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[name] = '1'
os.environ.setdefault('MPLCONFIGDIR', '/tmp/structured_press_analysis_mpl')
import json
from pathlib import Path
import subprocess
import sys
import time
import research

ROOT, STUDY, RUNTIME = research.ROOT, research.STUDY, research.RUNTIME
TERMINAL = ('passed', 'max_updates_reached_without_two_passes', 'budget_stopped', 'error')


def selected_source(finger, stage):
    """미완료 블록을 선택하지 않고 완료 평가·체크포인트의 원래 SHA를 검사한다."""
    path = ROOT/(finger+'_'+stage+'_seed7_v1')/'summary.json'
    if not path.is_file():
        return dict(ready=False, reason='stage summary not available')
    summary = research.read(path)
    if summary['status'] not in TERMINAL:
        return dict(ready=False, reason='source stage still '+summary['status'])
    best = summary.get('best')
    if not best:
        return dict(ready=False, reason='source stage has no completed selected evaluation')
    candidates = list(summary['blocks'])
    if summary.get('initial'):
        candidates.append(summary['initial'])
    if not any(row == best for row in candidates):
        raise ValueError('selected source is not a completed recorded checkpoint: '+str(path))
    if summary['finger'] != finger or summary['stage'] != stage:
        raise ValueError('source finger/stage mismatch')
    checkpoint = Path(best['checkpoint'])
    if research.digest(checkpoint) != best['checkpoint_sha256']:
        raise ValueError('selected source checkpoint changed')
    evaluation = Path(best['evaluation'])
    for name, sha in best['evaluation_sha256'].items():
        if research.digest(evaluation/name) != sha:
            raise ValueError('source evaluation changed')
    if not research.read(checkpoint.parent.parent/'report.json')['completed']:
        raise ValueError('source belongs to incomplete training block')
    research.aggregate(evaluation)
    return dict(ready=True, finger=finger, stage=stage, checkpoint=str(checkpoint),
        sha256=best['checkpoint_sha256'], updates=best['updates'], role='initial' if best['updates'] == 0 else 'trained',
        source_stage_status=summary['status'], stage_passed=summary['passed'],
        summary=str(path), summary_sha256=research.digest(path), original_evaluation=str(evaluation))


def sources():
    checkpoint = STUDY/'runs/index_s3_f4_A_v1/train_100/J/final.pt'
    if not research.read(checkpoint.parent.parent/'report.json')['completed']:
        raise ValueError('index A100 reference training incomplete')
    result = {'index_A':dict(ready=True, finger='index', stage='A', updates=100,
        checkpoint=str(checkpoint), sha256=research.digest(checkpoint), role='trained',
        source_stage_status='historical completed A100 reference', stage_passed=None)}
    for finger, stage in (('middle', 'A'), ('ring', 'A'), ('pinky', 'A'), ('index', 'B')):
        result[finger+'_'+stage] = selected_source(finger, stage)
    return result


def plan_jobs(selected):
    jobs = []
    for key in ('index_A', 'middle_A', 'ring_A', 'pinky_A', 'index_B'):
        jobs.append(dict(label='free_'+key, kind='free_v9', source_key=key,
                         source=selected[key], status='pending'))
    for finger in ('index', 'middle'):
        for scale in (0., .25, .5, 1.):
            jobs.append(dict(label='noise_{}_scale{:03d}'.format(finger, round(scale*100)),
                kind='A_supported_noise', scale=scale, source_key=finger+'_A',
                source=selected[finger+'_A'], status='pending'))
    return jobs


def remaining_seconds(now=None):
    return research.deadline_status(research.read(ROOT/'budget.json'), 'evaluate', now)['remaining_seconds']


def publish(state):
    state['updated_utc'] = research.utcnow().isoformat()
    research.write(ROOT/'diagnostics_progress.json', state)
    research.write(ROOT/'diagnostic_summary.json', dict(state,
        schema='structured_press.diagnostic_batch_summary.v1',
        completed_jobs=sum(job['status'] == 'completed' for job in state['jobs']),
        expected_jobs=13, new_training=False,
        limitations=['free-v9 and A supported noise evaluations have different initial/support distributions',
            'noise jobs use the same checkpoint mean and restored RNG; only active-four sigma changes',
            'no new target/song generalization test; finger targets differ',
            '32 first episodes per job; failures remain in denominator; no multi-seed claim']))
    lines = ['# 고정 모델 자유 평가·잡음 진단', '', '상태: '+state['status'],
        '갱신 UTC: '+state['updated_utc'], '',
        '새 학습이 아니다. A 잡음 평가 8개는 동일 체크포인트의 평균·제어·초기분포·보상·물리를 유지하며, '
        '저장 RNG를 복원하고 활성 손가락4축의 Gaussian 표준편차 배율만 바꾼다. '
        '자유 평가 5개는 모델 가중치·물리·보상을 보존하지만 초기분포를 원래 v9로 바꾸고, '
        '지원을 해제해 33축을 활성화하므로 실행 출력과 제어 조건이 달라진다. '
        'scale0은 평균 행동, scale1은 저장 Gaussian이다. 목표 곡/줄/프렛을 바꾸지 않으므로 새 목표 일반화를 뜻하지 않는다. '
        '손가락마다 목표 줄·프렛이 달라 손가락 자체 난이도로 단정하지 않는다.']
    for kind, title in (('free_v9', '원래 v9 자유 조건'), ('A_supported_noise', 'A 정렬·지원 조건 잡음 진단')):
        lines += ['', '## '+title, '', '|평가|모델 갱신|배율|안전 달성 /32|실패 /32|clean 평균(실패0점,초)|상태|',
                  '|---|--:|--:|--:|--:|--:|---|']
        reasons = []
        for job in state['jobs']:
            if job['kind'] != kind:
                continue
            metrics = job.get('metrics')
            values = (str(metrics['safe_success']), str(metrics['failure_episodes']),
                      '{:.4f}'.format(metrics['mean_safe_clean_s'])) if metrics else ('—', '—', '—')
            lines.append('|{}|{}|{}|{}|{}|{}|{}|'.format(job['label'], job['source'].get('updates', '—'),
                job.get('scale', '—'), *values, job['status']))
            if job.get('reason'):
                reasons.append('`'+job['label']+'`: '+job['reason'])
        for reason in reasons:
            lines += ['', reason]
    lines += ['', '![잡음 민감도](noise_sensitivity.png)', '',
        '자유 v9 성과와 A 지원 조건 성과를 합산하지 않는다. 원본 모델 SHA·선택 출처·종료 상태와 각 평가 보고서 경로는 '
        'diagnostic_summary.json에 기록한다. 실패/시간 초과/보류는 완료 성과에 포함하지 않는다.']
    (ROOT/'DIAGNOSTICS.md').write_text('\n'.join(lines)+'\n')


def graph(state):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    found = False
    for finger in ('index', 'middle'):
        jobs = [job for job in state['jobs'] if job['kind'] == 'A_supported_noise' and
                job['source_key'] == finger+'_A' and job['status'] == 'completed']
        jobs.sort(key=lambda job:job['scale'])
        if not jobs:
            continue
        found = True
        axes[0].plot([job['scale'] for job in jobs], [job['metrics']['safe_success']/32 for job in jobs], 'o-', label=finger)
        axes[1].plot([job['scale'] for job in jobs], [job['metrics']['mean_safe_clean_s'] for job in jobs], 'o-', label=finger)
    for axis, label in zip(axes, ('Safe success / 32', 'Mean clean seconds (failure = 0)')):
        axis.set(xlabel='Active-finger Gaussian sigma multiplier', ylabel=label, title='A supported condition, fixed model')
        axis.grid(alpha=.25)
        if found: axis.legend()
        else: axis.text(.5, .5, 'No completed noise probe yet', transform=axis.transAxes, ha='center')
    axes[0].set_ylim(-.03, 1.03)
    fig.savefig(ROOT/'noise_sensitivity.png', dpi=150)
    plt.close(fig)


def run_job(job, state):
    source = job['source']; checkpoint = Path(source['checkpoint'])
    out = ROOT/'probes'/job['label']; log = out.with_suffix('.console.log')
    if out.exists() or log.exists():
        raise FileExistsError('existing/partial probe output will not be overwritten: '+str(out))
    if research.digest(checkpoint) != source['sha256']:
        raise ValueError('source checkpoint changed before probe')
    research.verify_seal()
    if job['kind'] == 'free_v9':
        command = [sys.executable, '-B', '-X', 'utf8', '-m', research.MODULE, 'evaluate-free-v9']
    else:
        command = [sys.executable, '-B', str(ROOT/'noise_probe.py'), '--scale', str(job['scale'])]
    command += ['--checkpoint', str(checkpoint), '--out', str(out)]
    out.parent.mkdir(exist_ok=True)
    started = time.monotonic()
    job.update(status='running', started_utc=research.utcnow().isoformat(), output=str(out), command=command)
    state.update(current=job['label'], child_pid=None)
    publish(state)
    with log.open('x') as stream:
        child = subprocess.Popen(command, cwd=RUNTIME, env=os.environ.copy(), stdout=stream, stderr=subprocess.STDOUT)
        state.update(current=job['label'], child_pid=child.pid)
        publish(state)
        try:
            while True:
                left = min(300-(time.monotonic()-started), remaining_seconds())
                if left <= 0:
                    job.update(status='timeout', reason='300-second or total study deadline reached', partial=True,
                               signals=research.interrupt_child(child))
                    break
                try:
                    code = child.wait(timeout=min(15., left))
                    if code:
                        job.update(status='error', reason='child exit '+str(code), partial=True)
                    break
                except subprocess.TimeoutExpired:
                    publish(state)
        except BaseException:
            research.interrupt_child(child)
            raise
        finally:
            state['child_pid'] = None
            job.update(finished_utc=research.utcnow().isoformat(), wall_seconds=time.monotonic()-started)
    if research.digest(checkpoint) != source['sha256']:
        raise ValueError('source checkpoint changed during probe')
    research.verify_seal()
    if job['status'] == 'running':
        report = research.read(out/'report.json')
        if report['checkpoint_sha256'] != source['sha256']:
            raise ValueError('evaluation source SHA mismatch')
        if job['kind'] == 'A_supported_noise' and (
                report['schema'] != 'diagnostic_sampling_override.v1' or report['scale'] != job['scale']):
            raise ValueError('noise sampling override report mismatch')
        if job['kind'] == 'free_v9' and report.get('evaluation_stage') != 'free_v9':
            raise ValueError('unassisted evaluation contract required')
        job.update(status='completed', metrics=research.aggregate(out),
            report_sha256=research.digest(out/'report.json'),
            episodes_sha256=research.digest(out/'episodes.jsonl'),
            metadata_sha256=research.digest(out/'episode_metadata.json'))


def main():
    research.verify_seal()
    selected = sources()
    jobs = plan_jobs(selected)
    # 어느 한 경로라도 남아 있으면 GPU를 시작하기 전에 전체 배치를 거부한다.
    for job in jobs:
        out = ROOT/'probes'/job['label']
        if out.exists() or out.with_suffix('.console.log').exists():
            raise FileExistsError('probe result already exists: '+str(out))
    state = dict(schema='structured_press.diagnostic_batch_progress.v1', status='running',
        started_utc=research.utcnow().isoformat(), current=None, child_pid=None, jobs=jobs,
        source_seal_sha256=research.digest(STUDY/'source_seal.json'),
        driver_sha256=research.digest(__file__))
    publish(state); graph(state)
    try:
        for job in jobs:
            if not job['source']['ready']:
                job.update(status='deferred_source', reason=job['source']['reason'])
            elif remaining_seconds() < 300:
                job.update(status='deferred_budget', reason='less than five minutes remain')
            else:
                run_job(job, state)
            publish(state); graph(state)
        state['status'] = ('completed' if all(job['status'] == 'completed' for job in jobs) else
                           'partial_with_errors' if any(job['status'] in ('error', 'timeout') for job in jobs) else 'deferred')
    except BaseException as error:
        state.update(status='error', failure=type(error).__name__+': '+str(error))
        if state.get('current'):
            for job in jobs:
                if job['label'] == state['current'] and job['status'] == 'running':
                    job.update(status='error', reason=state['failure'], partial=True)
        raise
    finally:
        state['current'] = None
        publish(state); graph(state)


if __name__ == '__main__':
    main()
