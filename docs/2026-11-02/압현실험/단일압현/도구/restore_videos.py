"""예정 영상 경로를 완료로 오인한 원장은 보존하고 실제 MP4를 별도 원장에서 복구한다."""
import argparse
import copy
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('single18_sealed_supervisor',HERE/'supervisor.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def selection(case):
    choices=[]
    for run in [case]+case.get('replicates',[]):
        result=run.get('confirmation') or run.get('best')
        if result and result.get('checkpoint'):
            choices.append((m.rank(result['metrics']),run.get('seed',7),result['checkpoint']))
    return max(choices,key=lambda r:r[0]) if choices else None


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,default=m.BASE/'로그/study_v1/state.json')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    with (m.ROOT/'.runtime/guitar_gpu_study.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        study=m.Study.__new__(m.Study)
        study.out=args.out.resolve();study.out.mkdir(parents=True,exist_ok=True)
        study.path=study.out/'state.json';study.child=None
        parent_sha=m.sha(args.parent)
        if study.path.exists():
            study.state=json.loads(study.path.read_text())
            if study.state['parent_sha256']!=parent_sha:raise RuntimeError('부모 연구 원장 변경')
        else:
            study.state=copy.deepcopy(json.loads(args.parent.read_text()))
            study.state.update(status='rendering',render_started_at=m.now(),driver_pid=os.getpid(),
                parent_state=str(args.parent.resolve()),parent_sha256=parent_sha,jobs={},current_job=None)
            study.state.pop('finished_at',None)
            study.state['source_seal'][str(Path(__file__).resolve())]=m.sha(__file__)
            for case in study.state['cases'].values():
                case['planned_video']=case.pop('video',None)
        study.check_seal();study.save()
        def stop(sig,frame):raise KeyboardInterrupt('영상 복구 중단 '+str(sig))
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
        try:
            for case in study.state['cases'].values():
                if time.time()+180>=study.state['deadline_epoch']:break
                if case.get('video_status')=='rendered' and Path(case.get('video','')).is_file():
                    if m.sha(case['video'])!=case.get('video_sha256'):raise RuntimeError('GLOBAL_IDENTITY: 복구 영상 변경')
                    continue
                chosen=selection(case)
                original=case.get('selected_checkpoint')
                if chosen:
                    case['selected_checkpoint']=chosen[2]
                    case['video_selection']=dict(seed=chosen[1],checkpoint=chosen[2],
                        rule='highest fixed-policy achievement, clean, wrong/failure rank across recorded seeds; training results unchanged')
                try:study.render(case)
                except (RuntimeError,ValueError,TimeoutError,OSError,subprocess.SubprocessError) as error:
                    if 'GLOBAL_' in str(error):raise
                    case.update(video_status='render_failed',video_error=repr(error))
                finally:
                    if original is None:case.pop('selected_checkpoint',None)
                    else:case['selected_checkpoint']=original
                    study.save()
            count=sum(c.get('video_status')=='rendered' and Path(c.get('video','')).is_file() for c in study.state['cases'].values())
            study.state.update(status='complete' if count==18 else 'render_partial',render_finished_at=m.now(),actual_videos=count)
            study.save()
            m.write(m.BASE/'분석/영상목록.json',[dict(case_id=c['case_id'],path=c.get('video'),kind=c.get('video_kind'),
                status=c.get('video_status','missing'),selection=c.get('video_selection'),
                episode_success=c.get('video_episode_success'),sha256=c.get('video_sha256')) for c in study.state['cases'].values()])
            (m.BASE/'분석/영상복구.md').write_text('# 영상 복구\n\n예정 경로를 저장 완료로 오인한 원본 감독기의 오류를 별도 원장에서 복구했다.\n'
                +'원본 학습 원장·코드·모델·판정은 변경하지 않았다. 실제 영상 '+str(count)+'/18개.\n'
                +'복구 원장: '+str(study.path)+'\n')
        except BaseException as error:
            if study.child is not None:m.terminate(study.child)
            study.state.update(status='render_interrupted',error=repr(error));study.save();raise
        finally:
            if m.sha(args.parent)!=parent_sha:raise RuntimeError('원본 연구 원장 변경')


if __name__=='__main__':
    if '--watch' in sys.argv:
        command=[sys.executable,'-B',str(Path(__file__).resolve())]+[a for a in sys.argv[1:] if a!='--watch']
        for attempt in range(3):
            child=subprocess.Popen(command,start_new_session=True)
            try:code=child.wait()
            except BaseException:
                m.terminate(child);raise
            if code==0:break
        raise SystemExit(code)
    main()

