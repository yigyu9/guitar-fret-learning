"""남은 A200 모델의 B0 평가와 실제 자유 정책 영상을 GPU 하나에서 순서대로 만든다.

기존 검지 영상은 제외한다. 모델 생성·평가·렌더는 검수된 도구를 각각 새 프로세스로
호출하며, 부분 결과가 있는 경로는 덮어쓰지 않는다. 이 파일 자체는 학습하지 않는다.
"""
import os
from pathlib import Path
import subprocess
import sys
import time

import probes
import research

ROOT, RUNTIME = research.ROOT, research.RUNTIME
PUBLIC = ROOT.parents[3]/'video/seven_hour_v1'
PROGRESS = ROOT/'media_progress.json'
FINGERS = ('middle', 'ring', 'pinky')


def exclusive(paths):
    for path in paths:
        if Path(path).exists():
            raise FileExistsError('existing/partial output must not be overwritten: '+str(path))


def completed(report):
    if report.get('completed') is not True:
        raise ValueError('native report is incomplete or failed')
    return report


def remaining(budget, now=None):
    return research.deadline_status(budget, 'render', now)['remaining_seconds']


def plan(sources):
    jobs = []
    prefix = [sys.executable, '-B', '-X', 'utf8']
    for finger, source in sources.items():
        b, free = ROOT/'model_only'/(finger+'_B0'), ROOT/'model_only'/(finger+'_free_v9')
        label = finger+'_A200_free_v9'
        commands = [
            ('export_B0', b, source['checkpoint'], prefix+[str(ROOT/'initialize_stage.py'),
                '--checkpoint', source['checkpoint'], '--stage', 'B', '--out', str(b)]),
            ('evaluate_B0', b.with_name(b.name+'_evaluate'), str(b/'J/final.pt'),
                prefix+['-m', research.MODULE, 'evaluate', '--checkpoint', str(b/'J/final.pt'),
                    '--num-envs', '32', '--out', str(b.with_name(b.name+'_evaluate'))]),
            ('export_free', free, source['checkpoint'], prefix+[str(ROOT/'initialize_stage.py'),
                '--checkpoint', source['checkpoint'], '--stage', 'free_v9',
                '--initial-distribution', 'v9', '--out', str(free)]),
            ('render_free', ROOT/'renders'/label, str(free/'J/final.pt'),
                prefix+[str(ROOT/'render_policy.py'), '--checkpoint', str(free/'J/final.pt'),
                    '--label', label])]
        for kind, out, checkpoint, command in commands:
            jobs.append(dict(finger=finger, kind=kind, out=str(out), checkpoint=checkpoint,
                log=str(out.with_name(out.name+'.console.log')), command=command, status='pending',
                public_videos=[str(PUBLIC/(label+'_'+view+'.mp4')) for view in ('hand', 'fullbody')]
                    if kind == 'render_free' else []))
    return jobs


def validate_job(job, checkpoint_sha):
    out = Path(job['out'])
    report = completed(research.read(out/'report.json'))
    artifacts = [out/'report.json']
    result = dict(completed=True)
    if job['kind'].startswith('export'):
        completed(research.read(out/'J/report.json'))
        if not report.get('no_training') or report['optimizer_updates'] != 0:
            raise ValueError('stage export unexpectedly trained')
        artifacts += [out/'J/report.json']
        for exported in report['exports']:
            path = Path(exported['path'])
            if research.digest(path) != exported['sha256']:
                raise ValueError('export checkpoint SHA mismatch')
            artifacts.append(path)
        if report['source_sha256'] != checkpoint_sha:
            raise ValueError('export source differs from scheduled checkpoint')
    else:
        if report['checkpoint_sha256'] != checkpoint_sha:
            raise ValueError('native report used another checkpoint')
        if job['kind'] == 'evaluate_B0':
            result['summary'] = research.aggregate(out)
            artifacts += [out/'episodes.jsonl', out/'episode_metadata.json']
        else:
            if not all(report.get(key) is True for key in ('native_pixels', 'policy_unchanged',
                    'source_pins_unchanged', 'source_checkpoint_pins_validated', 'lifecycle_verified')):
                raise ValueError('native render contract failed')
            publication = research.read(out/'publication.json')
            if publication['checkpoint_sha256'] != checkpoint_sha or len(publication['videos']) != 2:
                raise ValueError('publication source/video count mismatch')
            for video in publication['videos']:
                path = Path(video['path'])
                if str(path) not in job['public_videos'] or research.digest(path) != video['sha256']:
                    raise ValueError('published video path/SHA mismatch')
                artifacts.append(path)
            artifacts += [out/name for name in ('publication.json', 'capture_metadata.json',
                'episode_env0000.json', 'poses_env0000.npz')]
            result['episode'] = research.read(out/'episode_env0000.json')['song']
    result['artifact_sha256'] = {str(path):research.digest(path) for path in artifacts}
    return result


def main():
    exclusive([PROGRESS])
    sources = {finger:probes.selected_source(finger, 'A') for finger in FINGERS}
    if any(not source.get('ready') or source['updates'] != 200 for source in sources.values()):
        raise ValueError('all three completed, validated best A200 sources are required')
    jobs = plan(sources)
    exclusive([Path(job[key]) for job in jobs for key in ('out', 'log')]+
              [Path(path) for job in jobs for path in job['public_videos']])
    helper_paths = [Path(__file__), ROOT/'initialize_stage.py', ROOT/'render_policy.py',
                    ROOT/'research.py', ROOT/'probes.py']
    pins = {str(path):research.digest(path) for path in helper_paths}
    state = dict(status='planned', jobs=jobs, sources=sources, tool_sha256=pins,
        source_seal_sha256=research.verify_seal(), child_pid=None,
        skipped=['index: existing native free-v9 videos already completed'], completed_jobs=0)
    # 초기 파일만 배타 생성하며 이후 갱신은 이 실행기의 파일에만 수행한다.
    with PROGRESS.open('x') as stream:
        stream.write('{}\n')
    def publish():
        state['updated_utc'] = research.utcnow().isoformat()
        research.write(PROGRESS, state)
    def verify_sources():
        research.verify_seal()
        for source in sources.values():
            if research.digest(source['checkpoint']) != source['sha256'] or research.digest(source['summary']) != source['summary_sha256']:
                raise ValueError('selected source checkpoint/summary changed')
        if any(research.digest(path) != expected for path, expected in pins.items()):
            raise ValueError('execution helper changed')
    child = None
    try:
        publish()
        for job in jobs:
            state['current'] = job['finger']+':'+job['kind']
            if remaining(research.read(ROOT/'budget.json')) <= 0:
                raise research.BudgetStop('overall media deadline reached before child launch')
            verify_sources()
            checkpoint_sha = research.digest(job['checkpoint'])
            Path(job['log']).parent.mkdir(parents=True, exist_ok=True)
            started = time.monotonic()
            job.update(status='running', started_utc=research.utcnow().isoformat(),
                       input_checkpoint_sha256=checkpoint_sha)
            state.update(current=job['finger']+':'+job['kind'], child_pid=None, command=job['command'])
            publish()
            with Path(job['log']).open('x') as stream:
                child = subprocess.Popen(job['command'], cwd=RUNTIME, env=os.environ.copy(),
                    stdout=stream, stderr=subprocess.STDOUT)
                state.update(status='running', current=job['finger']+':'+job['kind'],
                             child_pid=child.pid, command=job['command'])
                publish()
                while child.poll() is None:
                    deadline = remaining(research.read(ROOT/'budget.json'))
                    timeout = 300-(time.monotonic()-started)
                    if min(deadline, timeout) <= 0:
                        job['interrupt_signals'] = research.interrupt_child(child)
                        if deadline <= 0:
                            raise research.BudgetStop('overall media deadline reached during child')
                        raise TimeoutError('media child exceeded five minutes')
                    try:
                        child.wait(timeout=min(15., deadline, timeout))
                    except subprocess.TimeoutExpired:
                        publish()
                if child.returncode:
                    raise RuntimeError('media child exit {}: {}'.format(child.returncode, job['log']))
            state['child_pid'] = None
            verify_sources()
            if research.digest(job['checkpoint']) != checkpoint_sha:
                raise ValueError('child input checkpoint changed')
            job['result'] = validate_job(job, checkpoint_sha)
            job['result']['log_sha256'] = research.digest(job['log'])
            job.update(status='completed', finished_utc=research.utcnow().isoformat(),
                       wall_seconds=time.monotonic()-started)
            state['completed_jobs'] += 1
            publish()
        state.update(status='completed', current=None)
    except BaseException as error:
        if child is not None and child.poll() is None:
            state['interrupt_signals'] = research.interrupt_child(child)
        state.update(status='budget_stopped' if isinstance(error, research.BudgetStop) else 'failed',
            failure=dict(type=type(error).__name__, message=str(error)))
        if state.get('current'):
            job['status'] = state['status']
        raise
    finally:
        state['child_pid'] = None
        publish()


if __name__ == '__main__':
    main()
