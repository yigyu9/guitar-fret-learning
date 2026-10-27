"""Wait for the sealed500 run, then evaluate, render and analyze sequentially."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import traceback

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'


def now():
    return datetime.now(timezone.utc).isoformat()


def write(name, value):
    path = PHASE/name
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n')
    temporary.replace(path)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--detach',action='store_true')
    args=parser.parse_args()
    env=dict(os.environ)
    env.update(PATH='/home/ajou/miniconda3/envs/rl38/bin:/usr/local/bin:/usr/bin:/bin',
        PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0',
        PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib',
        OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    if args.detach:
        with (PHASE/'postprocess_supervisor.log').open('x') as log:
            process=subprocess.Popen([PYTHON,'-B',str(Path(__file__).resolve())],cwd=ROOT,env=env,
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write('postprocess_launch.json',dict(pid=process.pid,started_utc=now()))
        print(json.dumps(dict(pid=process.pid,started_utc=now())),flush=True)
        return
    with (PHASE/'postprocess_claim.json').open('x') as stream:
        json.dump(dict(pid=os.getpid(),started_utc=now()),stream)
    state=dict(phase='waiting_for_training',completed=False,pid=os.getpid(),started_utc=now(),steps=[])
    def update(**fields):
        state.update(fields)
        write('postprocessing_status.json',state)
    manifest=json.loads((PHASE/'postprocessing_sources.json').read_text())
    def verify_tools():
        assert all(sha(ROOT/p)==h for p,h in manifest.items()),'Sealed postprocessing tools changed'
    try:
        verify_tools()
        update()
        while True:
            training=json.loads((PHASE/'pipeline_status.json').read_text())
            if training['phase']=='failed':raise RuntimeError('Training failed: '+training.get('error','unknown'))
            if training['phase']=='training_audited':break
            live=PHASE/'train500/status.json'
            if live.is_file():
                progress=json.loads(live.read_text())
                update(training_update=progress.get('update_index'),training_phase=progress.get('phase'),
                    training_tick=progress.get('ticks'),heartbeat_utc=now())
            try:os.kill(training['supervisor_pid'],0)
            except ProcessLookupError:raise RuntimeError('Training supervisor exited before its audited completion record')
            time.sleep(30)
        report=json.loads((PHASE/'train500/report.json').read_text())
        audit=json.loads((PHASE/'log_inspection.json').read_text())
        assert report['completed'] and report['optimizer_updates']==500 and report['failure'] is None
        assert not report['changed_inputs'] and not report['missing_import_pins'] and not report['cleanup_errors']
        assert audit['verified'] and audit['transitions']==16_384_000
        update(training_completed=True,training_audited=True)
        def run(label,arguments):
            verify_tools()
            started=time.monotonic()
            update(phase=label)
            with (PHASE/(label+'_console.log')).open('x') as log:
                process=subprocess.Popen([PYTHON,'-B']+arguments,cwd=ROOT,env=env,
                    stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                update(child_pid=process.pid)
                code=process.wait()
            state['steps'].append(dict(label=label,returncode=code,wall_s=time.monotonic()-started))
            update(child_pid=None)
            if code:raise RuntimeError(label+' exited '+str(code))
            verify_tools()
        for repeat in (1,2,3):
            for name,tool in (('evaluation','evaluate.py'),('baseline','evaluate_baseline.py')):
                run(name+'_repeat'+str(repeat),[str(PHASE/'support'/tool),
                    '--repeat',str(repeat),'--out',str(PHASE/(name+'_repeat'+str(repeat)))])
        media_errors=[]
        for view in ('fullbody','hand'):
            try:
                run('render_'+view,[str(PHASE/'support/render_video.py'),
                    '--evaluation',str(PHASE/'evaluation_repeat1'),'--out',str(PHASE/('video_'+view)),
                    '--view',view])
            except RuntimeError as error:
                media_errors.append(str(error))
        run('analysis',[str(PHASE/'support/analyze.py')])
        with (PHASE/'README.md').open('a') as stream:
            stream.write('\n## 후처리 종료\n\n'+now()+' UTC. 500회 학습·감사·반복 평가·분석을 마쳤습니다. 영상 오류: '+str(media_errors)+'.\n\n[결과 분석]('+str(PHASE/'RESULTS.md')+') · [분석 원자료]('+str(PHASE/'analysis.json')+'). 3,000회 연장 채택은 결과 검토 대상입니다.\n')
        update(phase='complete' if not media_errors else 'complete_with_media_errors',
            completed=not media_errors,analysis_completed=True,media_errors=media_errors,ended_utc=now(),
            scope='500-update learning and comparison only;3000-update extension awaits evidence-based review')
    except BaseException as error:
        update(phase='failed',completed=False,error=repr(error),traceback=traceback.format_exc(),ended_utc=now())
        raise


if __name__=='__main__':main()
