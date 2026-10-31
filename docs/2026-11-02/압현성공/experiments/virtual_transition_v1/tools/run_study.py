"""승인된 E0/E4 ABAB 비교를 한 GPU에서 순차 실행하고 실패까지 기록한다."""
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

HERE = Path(__file__).resolve().parent
EXPERIMENT = HERE.parent
ROOT = next(p for p in HERE.parents if (p/'scripts/tab2body.py').is_file())
SONG = 'virtual_middle_s3_f6_f7_ABAB_v1'
KST = timezone(timedelta(hours=9))
CHILD = None


class FatalStudyError(RuntimeError): pass


def timestamp(): return datetime.now(KST).isoformat(timespec='seconds')


def digest(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): value.update(chunk)
    return value.hexdigest()


def write(path, value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def source_paths():
    paths={ROOT/'scripts/tab2body.py'}
    for current,dirs,files in os.walk(ROOT/'guitar_learning',followlinks=False):
        dirs[:]=[d for d in dirs if d not in ('archive','__pycache__') and not (Path(current)/d).is_symlink()]
        paths.update(Path(current)/f for f in files if f.endswith('.py'))
    paths.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    paths.update(p for p in (ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1').rglob('*') if p.is_file())
    paths.add(EXPERIMENT/'validation/preflight.json')
    for folder in (HERE,EXPERIMENT/'geometry',ROOT/'data/song_bundles'/SONG):
        paths.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return sorted(paths)


def verify_sources(seal):
    bad=[name for name,value in seal.items() if not (ROOT/name).is_file() or digest(ROOT/name)!=value]
    if bad: raise FatalStudyError('봉인 입력 변경: '+', '.join(bad[:8]))


def prerequisites():
    preflight=EXPERIMENT/'validation/preflight.json'
    data=json.loads(preflight.read_text())
    if data.get('passed') is not True or not data.get('input_sha256'):
        raise FatalStudyError('B native 검사와 소규모 학습/재개/평가 preflight 통과 필요')
    for name,value in data['input_sha256'].items():
        path=Path(name) if Path(name).is_absolute() else ROOT/name
        if not path.is_file() or digest(path)!=value: raise FatalStudyError('preflight 입력 변경: '+name)
    old=ROOT/'docs/2026-11-02/압현성공/experiments/natural_press_v3/runs/comparison_v1/progress.json'
    if old.exists():
        state=json.loads(old.read_text())
        if state.get('status') in ('running','starting'):
            raise FatalStudyError('선행 비교가 아직 진행 중임')
        pid=state.get('driver_pid')
        if pid and Path('/proc') .joinpath(str(pid)).exists():
            raise FatalStudyError('선행 비교 driver가 아직 살아 있음')
    occupied=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    if occupied: raise FatalStudyError('GPU 사용 중: '+occupied)


def live_updates(out):
    path=Path(out)/'J/learning_metrics.jsonl'; rows=[]
    if path.exists():
        for line in path.read_text().splitlines():
            try: rows.append(json.loads(line))
            except json.JSONDecodeError: break
    durations=[r['collection_s']+r['update_s'] for r in rows[-10:]]
    return len(rows), statistics.mean(durations) if durations else None


def progress(state,out):
    current=state.get('current_job') or {}
    partial,seconds=live_updates(current['out']) if current.get('operation')=='train' else (0,None)
    done=sum(j.get('updates',0) for j in state['jobs'].values() if j['status']=='complete' and j['operation']=='train')
    evaluations=sum(j['status']=='complete' and j['operation']=='evaluate' for j in state['jobs'].values())
    if seconds is not None: state['seconds_per_update_recent']=seconds
    remaining=max(0,1200-done-partial)*state.get('seconds_per_update_recent',5.1)+max(0,12-evaluations)*85+8*85
    state.update(updated_at=timestamp(),completed_train_updates=done,current_block_completed_updates=partial,
                 completed_evaluations=evaluations,estimated_finish=(datetime.now(KST)+timedelta(seconds=remaining)).isoformat(timespec='minutes'))
    if state['status']!='running': state['estimated_finish']=state.get('finished_at','중단됨')
    write(out/'progress.json',state); write(out/'summary.json',state['results'])
    (out/'진행상황.md').write_text('# 두 프렛 전환 실험 진행\n\n- 갱신: '+state['updated_at']+'\n- 상태: '+state['status']+
        '\n- 현재 작업: '+current.get('label','없음')+f'\n- 완료 학습: {done}/1200회 (현재블록 {partial}회)\n- 평가: {evaluations}/12\n- 예상 종료: '+state['estimated_finish']+'\n\n실패 블록과 그 후속 연장은 보존·건너뛰며 다른 조건은 계속한다. 전체 미관측 음도 성공 분모에 포함한다.\n')
    lines=['# 두 프렛 전환 비교 결과','','각 평가 최초32 에피소드×4음, 실패 포함. 대표 궤적은 env0 한 회다.','',
           '|조건|seed|반복|전체 ABAB|음 달성|음별 달성 A/B/A/B|물리/손목 실패|','|---|---:|---:|---:|---:|---|---:|']
    for row in state['results'].values():
        m=row['metrics']; counts='/'.join(str(n['success_count']) for n in m['notes'])
        lines.append(f"|{row['condition']}|{row['seed']}|{row['updates']}|{m['full_sequence_success_count']}/32|{m['note_success_count']}/128|{counts}|{m['physical_failure_count']}/{m['wrist_failure_count']}|")
    lines+=['','각 음별 성공 분모는32이며, 전체 달성은4음 모두와 안전 종료를 요구한다. 같은 초기 분포의 반복 평가이므로 새로운 목표·곡에 대한 일반화를 뜻하지 않는다.', '', '## 관측된 패턴', '']
    for name,row in state['results'].items():
        m=row['metrics']; counts=[n['success_count'] for n in m['notes']]
        lines.append(f"- {name}: 첫음 {counts[0]}/32, 뒤3음 {sum(counts[1:])}/96, A복귀 {counts[2]}/32, 마지막B {counts[3]}/32. clean평균은 "+'/'.join(f"{n['mean_clean_s']:.3f}" for n in m['notes'])+'초다.')
    for seed in (7,17):
        for total in (100,200,300):
            a=state['results'].get(f'seed{seed}_E0_u{total}'); b=state['results'].get(f'seed{seed}_E4_u{total}')
            if a and b:
                am,bm=a['metrics'],b['metrics']
                lines.append(f"- seed{seed}/{total}회 E4−E0: 전체 ABAB {bm['full_sequence_success_count']-am['full_sequence_success_count']:+d}/32, 음 달성 {bm['note_success_count']-am['note_success_count']:+d}/128. 준비 모양 개선만으로 압현 성능 개선을 단정하지 않는다.")
    lines+=['','실패·건너뛴 작업:']+[f"- {name}: {j['status']} {j.get('error','')}" for name,j in state['jobs'].items() if j['status'] in ('failed','skipped')]
    if state.get('artifact_errors'): lines+=['','그림 생성 오류(학습 결과는 보존): '+json.dumps(state['artifact_errors'],ensure_ascii=False)]
    if state.get('error'): lines+=['','중단 원인: '+state['error']]
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def nonfinite_failure(out, log_text):
    """구조화된 실패를 먼저 읽고 보고서가 없을 때만 traceback 문구를 사용한다."""
    markers=('non-finite','nonfinite','non finite','nan detected','finite explicit',
             'finite required','finite state required','native finite','nativefinite')
    reports=[]
    for name in ('report.json','J/report.json'):
        path=Path(out)/name
        if path.is_file():
            try: reports.append(json.loads(path.read_text()))
            except json.JSONDecodeError: pass  # 불완전 보고서는 아래 기존 완료 검사에서도 거부한다.
    def inspect(value):
        if isinstance(value,dict):
            failure=value.get('failure')
            if isinstance(failure,dict):
                kind=str(failure.get('type',''))
                message=str(failure.get('message',''))
                lower=message.lower()
                finite_requirement='finite' in lower and ('required' in lower or 'must be' in lower)
                if kind.rsplit('.',1)[-1]=='FloatingPointError' or finite_requirement or any(token in lower for token in markers):
                    return kind+': '+message
            for child in value.values():
                found=inspect(child)
                if found: return found
        elif isinstance(value,list):
            for child in value:
                found=inspect(child)
                if found: return found
        return None
    for report in reports:
        found=inspect(report)
        if found: return found
    if not reports:
        for line in log_text.splitlines():
            lower=line.lower()
            if ('FloatingPointError:' in line or any(token in lower for token in markers) or
                ('finite' in lower and ('required' in lower or 'must be' in lower))):
                return line.strip()
    return None


def run_job(state,root,label,operation,args,out,updates=0):
    global CHILD
    verify_sources(state['source_seal'])
    saved=state['jobs'].get(label)
    if saved:
        if saved['status']!='complete': return None
        for name,value in saved['evidence_sha256'].items():
            if not Path(name).is_file() or digest(name)!=value: raise FatalStudyError('기존 결과 변경: '+name)
        return json.loads((out/'report.json').read_text())
    if out.exists(): raise FatalStudyError('기존 출력 덮어쓰기 거부: '+str(out))
    occupied=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
    if occupied: raise FatalStudyError('다른 GPU 작업 발견: '+occupied)
    if shutil.disk_usage(ROOT).free < 12*1024**3: raise FatalStudyError('남은 공간12GiB 미만')
    cmd=[sys.executable,'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root','/tmp/tab2body_natural_press_v3','run',str(HERE/'transition_runtime.py'),operation,*map(str,args),'--out',str(out)]
    env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    if operation=='render':
        cmd=['xvfb-run','-a','--server-args=-screen 0 1280x720x24',*cmd]
        env['VK_ICD_FILENAMES']='/usr/share/vulkan/icd.d/nvidia_icd.json'
    logfile=root/'logs'/(label+'.log'); logfile.parent.mkdir(exist_ok=True)
    job=dict(label=label,operation=operation,status='running',out=str(out),updates=updates,started_at=timestamp(),command=cmd,log=str(logfile))
    state['jobs'][label]=job; state['current_job']=job; started=time.monotonic()
    try:
        with logfile.open('x') as stream:
            CHILD=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            job['pid']=CHILD.pid
            while CHILD.poll() is None:
                progress(state,root)
                if time.monotonic()-started > (2700 if operation=='train' else 1200):
                    raise TimeoutError('작업 제한시간 초과')
                time.sleep(10)
            code=CHILD.returncode; CHILD=None
        verify_sources(state['source_seal'])
        text=logfile.read_text(errors='replace')
        nonfinite=nonfinite_failure(out,text)
        if nonfinite:
            raise FatalStudyError('비유한 입력/학습/물리 관측: '+label+'; '+nonfinite)
        if code: raise RuntimeError('종료코드 '+str(code))
        report=json.loads((out/'report.json').read_text())
        if report.get('completed') is not True or any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors')):
            raise FatalStudyError('수명주기/입력 검증 실패: '+label)
        evidence=[out/'report.json']
        if operation=='train':
            phase=json.loads((out/'J/report.json').read_text())
            if phase.get('updates_in_run')!=updates: raise FatalStudyError('추가 반복수 불일치')
            evidence.append(out/'J/final.pt')
        elif operation=='evaluate': evidence.extend(out/name for name in ('episodes.jsonl','episode_metadata.json','finger_control_trace.jsonl.gz'))
        else: evidence.extend(out/name for name in ('hand.mp4','fullbody.mp4'))
        job.update(status='complete',evidence_sha256={str(p):digest(p) for p in evidence},finished_at=timestamp(),wall_s=time.monotonic()-started)
        return report
    except BaseException as error:
        if CHILD is not None and CHILD.poll() is None:
            os.killpg(CHILD.pid,signal.SIGTERM); CHILD.wait(timeout=30)
        CHILD=None; job.update(status='failed',error=str(error),finished_at=timestamp())
        if isinstance(error,(FatalStudyError,KeyboardInterrupt,SystemExit)): raise
        return None
    finally:
        state['current_job']=None; progress(state,root)


def ranking(row):
    m=row['metrics']
    return (m['physical_failure_count']+m['wrist_failure_count'],-m['full_sequence_success_count'],
            -m['note_success_count'],-sum(n['mean_clean_s'] for n in m['notes']),sum(n['mean_wrong_s'] for n in m['notes']),row['updates'])


def block(state,root,condition,seed,total):
    from analyze_results import analyze_evaluation
    label=f'seed{seed}_{condition}_u{total}'; base=root/'blocks'/label
    previous=root/'blocks'/f'seed{seed}_{condition}_u{total-100}'/'train/J/final.pt'
    prior=state['jobs'].get(f'seed{seed}_{condition}_u{total-100}_train',{})
    if total>100 and (not previous.exists() or prior.get('status')!='complete'):
        state['jobs'][label+'_train']=dict(status='skipped',operation='train',error='이전 블록 checkpoint 없음'); progress(state,root); return
    args=['--seed',seed,'--updates',100]
    args+=['--condition',condition,'--size','large','--num-envs',64] if total==100 else ['--resume',previous]
    if run_job(state,root,label+'_train','train',args,base/'train',100) is None: return
    checkpoint=base/'train/J/final.pt'
    phase=json.loads((base/'train/J/report.json').read_text())
    if phase.get('optimizer_updates')!=total or phase.get('transitions')!=100*64*32 or phase.get('curriculum',{}).get('committed_transitions')!=total*64*32:
        raise FatalStudyError('누적 checkpoint 반복/노출 수 불일치: '+label)
    if run_job(state,root,label+'_evaluate','evaluate',['--checkpoint',checkpoint,'--num-envs',32],base/'evaluation') is None: return
    metrics=analyze_evaluation(base/'evaluation'); write(base/'metrics.json',metrics)
    state['results'][label]=dict(condition=condition,seed=seed,updates=total,checkpoint=str(checkpoint),checkpoint_sha256=digest(checkpoint),metrics=metrics)
    progress(state,root)
    plotter=HERE/'plot_results.py'
    if plotter.exists():
        try:
            subprocess.run([sys.executable,'-B',str(plotter),'--run',str(root)],cwd=ROOT,check=True,capture_output=True,text=True)
        except Exception as error:
            state.setdefault('artifact_errors',[]).append(dict(operation='plot',block=label,error=str(error)))
            progress(state,root)


def stop(signum,frame): raise KeyboardInterrupt('종료 신호 '+str(signum))


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--out',type=Path,required=True); parser.add_argument('--resume',action='store_true')
    args=parser.parse_args(); out=args.out.resolve(); out.mkdir(parents=True,exist_ok=True)
    signal.signal(signal.SIGTERM,stop); signal.signal(signal.SIGINT,stop)
    with (out/'gpu.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); prerequisites()
        if args.resume:
            state=json.loads((out/'progress.json').read_text()); verify_sources(state['source_seal']); state.update(status='running',driver_pid=os.getpid()); state.pop('error',None)
        else:
            if (out/'progress.json').exists(): raise FileExistsError('기존 실험 보존')
            seal={str(p.relative_to(ROOT)):digest(p) for p in source_paths()}
            preflight=json.loads((EXPERIMENT/'validation/preflight.json').read_text())
            seal.update(preflight['input_sha256'])
            state=dict(schema='guitar_learning.virtual_transition_study.v1',status='running',started_at=timestamp(),driver_pid=os.getpid(),jobs={},results={},source_seal=seal)
            write(out/'source_seal.json',seal)
        try:
            progress(state,out)
            for seed in (7,17):
                for total in (100,200,300):
                    for condition in ('E0','E4'): block(state,out,condition,seed,total)
            public=ROOT/'docs/2026-11-02/압현성공/video/virtual_transition_v1'; public.mkdir(parents=True,exist_ok=True)
            for condition in ('E0','E4'):
                candidates=[r for r in state['results'].values() if r['condition']==condition]
                if not candidates: continue
                selected={min(candidates,key=ranking)['checkpoint']:min(candidates,key=ranking),candidates[-1]['checkpoint']:candidates[-1]}
                for row in selected.values():
                    label=f"seed{row['seed']}_{condition}_u{row['updates']}"; render=out/'renders'/label
                    if run_job(state,out,label+'_render','render',['--checkpoint',row['checkpoint'],'--num-envs',4],render) is None: continue
                    published=[]
                    for kind in ('hand','fullbody'):
                        source=render/(kind+'.mp4'); target=public/(out.name+'_'+label+'_'+kind+'.mp4')
                        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json',str(source)],text=True))
                        if float(probe['format']['duration'])<=0: raise FatalStudyError('빈 영상')
                        if target.exists() and digest(target)!=digest(source): raise FatalStudyError('공개 영상 덮어쓰기 거부')
                        if not target.exists(): shutil.copyfile(source,target)
                        published.append(dict(path=str(target),sha256=digest(target)))
                    write(render/'published_video.json',published)
            state['status']=('finished_with_failed_blocks' if any(j['status']!='complete' for j in state['jobs'].values()) else
                             'complete_with_artifact_errors' if state.get('artifact_errors') else 'complete')
            state['finished_at']=timestamp(); progress(state,out)
        except BaseException as error:
            state.update(status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',error=str(error),finished_at=timestamp()); progress(state,out); raise


if __name__=='__main__': main()
