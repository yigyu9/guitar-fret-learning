"""중지 6→8프렛의 팔 탐색·학습률 2×2 비교를 동일400회로 순차 실행한다.

기존 검증된 실행·영상 도우미를 명시 복사했으며 과거 Python을 import하지 않는다.
실행 실패와 성능 미달을 구분하고 원문·모델·입력 SHA를 보존한다.
"""
import argparse
import bisect
import gzip
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

SELF=Path(__file__).resolve()
STUDY=SELF.parents[1]
ROOT=SELF.parents[4]
PYTHON=Path('/home/ajou/miniconda3/envs/rl38/bin/python')
LEARNER=SELF.parent/'learning.py'
STATE=STUDY/'진행상황.json'
SEAL=STUDY/'검증/실행봉인.json'
PREVIOUS=ROOT/'docs/2026-11-09/복합압현_야간확장_v1'
DEADLINE=datetime.fromisoformat('2026-11-03T14:30:00+09:00')
TRAIN_CUTOFF=datetime.fromisoformat('2026-11-03T13:30:00+09:00')
CONDITIONS=(('C00',.15,'existing'),('C10',.20,'existing'),('C01',.15,'recover_floor'),('C11',.20,'recover_floor'))
CONFIG={label:dict(arm_std=std,lr_mode=mode) for label,std,mode in CONDITIONS}
class DeadlineReached(RuntimeError):pass
class IntegrityError(RuntimeError):pass


def stamp():return datetime.now(timezone.utc).isoformat()

def read(path):return json.loads(Path(path).read_text())

def rows(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

def verify(pins):
    changed=[p for p,h in pins.items() if not Path(p).is_file() or sha(p)!=h]
    if changed:raise IntegrityError('실행 입력/산출물 SHA 불일치: '+', '.join(changed))

def merge_pins(*sources):
    result={}
    for source in sources:
        for path,digest in source.items():
            if path in result and result[path]!=digest:raise IntegrityError('출처 SHA 중복키 충돌: '+path)
            result[path]=digest
    return result

def manifest(out):return {str(p):sha(p) for p in sorted(Path(out).rglob('*')) if p.is_file()}

def case_row(case):return read(STUDY/'입력'/case/'catalog.json')['goals'][0]

def safe(episode):
    return (episode['valid'] and not episode['song']['safety_invalidated'] and
            not episode['termination']['physical_failure'] and not episode['termination']['wrist_failure'])

def evaluation(out,case,denominator=16):
    """평가 분모를 고정하고 목표별 유지와 시각·동시 구간을 별도로 판정한다."""
    ep=[r['episode'] for r in rows(out/'episodes.jsonl')]
    targets=case_row(case)['compiled_targets'];m=len(targets)
    if len(ep)!=denominator:raise ValueError('평가 에피소드 수 불일치')
    if any(len(e['left_note_ledger']['values']['clean'])!=m for e in ep):raise ValueError('전체 목표 원장 필요')
    fractions=[sum(e['left_note_ledger']['values']['clean'][i] for e in ep)/denominator/(t['end_s']-t['onset_s']) for i,t in enumerate(targets)]
    success=sum(safe(e) and e['song']['stage_success'] and e['song']['left_success_count']==m for e in ep)
    physics=sum(e['termination']['physical_failure'] for e in ep);wrist=sum(e['termination']['wrist_failure'] for e in ep)
    diagnostic=read(out/'diagnostics.json');d=diagnostic['summary']
    if d['episodes']!=denominator or d['exact_hz']!=240:raise ValueError('전체 평가의 정확240Hz 시각 진단 필요')
    timing_key='timing_pass_episodes'
    timing=d[timing_key]
    overlap=d['overlap_pass_episodes']
    wrong=sum(sum(e['left_note_ledger']['values']['wrong']) for e in ep)
    intervals=sorted((t['onset_s'],t['end_s']) for t in targets)
    union=0.;end=-float('inf')
    for start,stop in intervals:
        union+=max(0.,stop-max(start,end));end=max(end,stop)
    budget=denominator*union
    wrong_union=d['wrong_press_active_union_s']
    if not 0.<=wrong_union<=budget+1e-6:raise ValueError('오압현 union 시간 범위 불일치')
    wrong_ratio=wrong_union/budget if budget else 0.
    overlaps=any(a['onset_s']<b['end_s']-1e-9 and b['onset_s']<a['end_s']-1e-9 for i,a in enumerate(targets) for b in targets[i+1:])
    passed=(success>=denominator-1 and min(fractions)>=.9 and physics==0 and wrist==0
            and timing>=denominator-1 and wrong_ratio<=.05 and (not overlaps or overlap>=denominator-1))
    return dict(denominator=denominator,safe_success=success,clean_fraction_by_target=fractions,
        mean_best_streak_by_target_s=[sum(e['left_note_ledger']['values']['best_clean_streak'][i] for e in ep)/denominator for i in range(m)],
        wrong_target_seconds=wrong,wrong_active_union_s=wrong_union,wrong_target_time_ratio=wrong_ratio,wrong_denominator='active target-time interval union over all evaluated episodes; each native tick counted once',
        physical=physics,wrist=wrist,invalid=sum(not safe(e) for e in ep),
        timing_scope=timing_key,timing_pass=timing,strict_timing_pass=d['timing_pass_episodes'],
        terminal_release_pass=d['terminal_release_pass_episodes'],overlap_pass=overlap,passed=passed)

def validated_report(out,kind,checkpoint=None,updates=None):
    rp=out/('J/report.json' if kind=='train' else 'report.json');r=read(rp)
    if not (r.get('completed') is True and r.get('failure') is None and r.get('lifecycle_verified') is True
            and r.get('changed_inputs')==[] and not r.get('missing_import_pins') and r.get('cleanup_errors')==[]):
        raise ValueError('미완료/입력변경/장면 정리 실패: '+str(rp))
    if checkpoint is not None and r.get('checkpoint_sha256')!=sha(checkpoint):raise ValueError('checkpoint SHA 불일치')
    if kind=='train':
        outer=read(out/'report.json')
        if not (outer.get('completed') is True and outer.get('failure') is None and outer.get('final_phase')=='J'
                and len(outer.get('stages',[]))==1 and outer['stages'][0].get('report')==r):
            raise ValueError('학습 최상위 완료 보고서 불일치')
        ms=rows(out/'J/learning_metrics.jsonl')
        if updates is not None and (len(ms)!=updates or r['updates_in_run']!=updates):raise ValueError('요청 학습 횟수 미달')
        if not (out/'J/final.pt').is_file():raise ValueError('최종 모델 누락')
    elif kind=='render':
        if not (r.get('scene_closed') is True and r.get('source_pins_unchanged') is True
                and r.get('source_checkpoint_pins_validated') is True and r.get('encoding_exit_codes')=={'hand':0,'fullbody':0}):
            raise ValueError('영상 장면/인코딩/원본 봉인 검증 실패')
    return r

def close_group(process):
    try:os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=10)
    try:os.killpg(process.pid,signal.SIGKILL)
    except ProcessLookupError:pass

def occupied():
    p=subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=15)
    return [s for s in p.stdout.splitlines() if s.strip()]

def new_output(key):
    n=1;p=STUDY/'실행'/key
    while p.exists() or (STUDY/'실행/작업로그'/(p.name+'.log')).exists():
        n+=1;p=STUDY/'실행'/(key+'_attempt%02d'%n)
    return p,n

def command(action,out,*args):
    return [str(PYTHON),'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root',str(ROOT/'.runtime/cache'),
            'run','-B',str(LEARNER),action,'--out',str(out),*map(str,args)]

def remaining(now=None):
    return (DEADLINE-(now or datetime.now(timezone.utc))).total_seconds()

def check_time(*,training=False,reserve=0,now=None):
    now=now or datetime.now(timezone.utc)
    if now>=DEADLINE or (training and now>=TRAIN_CUTOFF) or (DEADLINE-now).total_seconds()<reserve:
        raise DeadlineReached('14:30 종료/13:30 신규 학습 중단 시간 예산')

def execute(state,key,action,args,pins,*,checkpoint=None,updates=None):
    """완료 근거를 재검증하고 실행오류는 새 원문을 남기며 한 번만 재시도한다."""
    pins=dict(pins)
    for flag in ('--checkpoint','--resume'):
        if flag in args:
            model=Path(args[args.index(flag)+1]).resolve();model.relative_to(ROOT);pins=merge_pins(pins,{str(model):sha(model)})
    item=state['tasks'].get(key)
    if item and item.get('completed'):
        verify(item['artifacts']);verify(item.get('dependency_pins',{}))
        out=Path(item['out']);validated_report(out,action,checkpoint,updates);return out
    history=list(item.get('attempt_history',[])) if item else []
    # 이전 프로세스가 비정상 종료한 미완료 attempt도 재시도 횟수에 포함한다.
    if item and not item.get('completed') and item.get('out') and not any(x.get('out')==item['out'] for x in history):
        history.append(dict(out=item['out'],failure='이전 실행 미완료',completed=False))
    while len(history)<2:
        check_time(training=action=='train');wait_gpu(state,key,pins)
        check_time(training=action=='train');verify(pins)
        out,attempt=new_output(key);log=STUDY/'실행/작업로그'/(out.name+'.log');log.parent.mkdir(parents=True,exist_ok=True)
        entry=dict(completed=False,out=str(out),attempt=attempt,action=action,checkpoint=str(checkpoint) if checkpoint else None,
            updates=updates,attempt_history=history,dependency_pins={p:h for p,h in pins.items() if state['driver_pins'].get(p)!=h})
        state['tasks'][key]=entry;save(STATE,state)
        process=None;start=time.monotonic();cmd=command(action,out,*args)
        try:
            env=dict(os.environ,PYTHONPATH=str(ROOT),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
            with log.open('xb') as stream:
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                state.update(status='실행 중',current_task=key,child_pid=process.pid,log=str(log),command=cmd,started_at=stamp())
                while process.poll() is None:
                    check_time();state['updated_at']=stamp();save(STATE,state)
                    if time.monotonic()-start>(3600 if action=='train' else 1200):raise TimeoutError(key)
                    time.sleep(min(5,max(1,remaining())))
                if process.returncode!=0:raise RuntimeError('종료 코드 '+str(process.returncode)+': '+str(log))
            verify(pins);validated_report(out,action,checkpoint,updates)
            entry.update(completed=True,artifacts=manifest(out),wall_s=time.monotonic()-start,finished_at=stamp())
            return out
        except (DeadlineReached,IntegrityError,KeyboardInterrupt):raise
        except Exception as error:
            history.append(dict(out=str(out),log=str(log),failure=repr(error),completed=False,finished_at=stamp()))
            entry.update(attempt_history=history,failure=repr(error));save(STATE,state)
        finally:
            if process is not None:close_group(process)
            state.update(child_pid=None,updated_at=stamp());save(STATE,state);verify(pins)
    raise RuntimeError('실행오류 두 번으로 조건 보류: '+key)

def select_score(result,update):
    return (result['passed'],result['safe_success'],min(result['clean_fraction_by_target']),result['timing_pass'],
            -result['wrong_target_time_ratio'],update)

def phase_subtitles(render,proof):
    """캡처 원장의 프레임 시각을 실제240Hz의 손가락 상태에 연결한다."""
    frame_times=read(render/'capture_metadata.json')['frame_times_s']
    samples=[];first_generation=None
    trace=render/'scene/diagnostic_trace.jsonl.gz'
    with gzip.open(trace,'rt') as stream:
        for line in stream:
            row=json.loads(line);generation=row['episode_generation'][0]
            if first_generation is None:first_generation=generation
            if generation!=first_generation:continue
            samples.append((row['time_s'][0],row['phase'][0]))
    if not samples:raise ValueError('대표 영상의 실제 단계 진단 누락')
    times=[t for t,_ in samples]
    offset=frame_times[0]
    if any(abs(t-(offset+i/30.))>1e-7 for i,t in enumerate(frame_times)):
        raise ValueError('대표 영상 프레임 시각이 고정30Hz와 불일치')
    names=('검지','중지','약지','소지');phases=('대기','준비','정렬','압현','유지','해제')
    labels=[]
    for t in frame_times:
        i=bisect.bisect_right(times,t+1e-8)-1
        if i<0 or t-times[i]>1/240.+1e-6:raise ValueError('캡처 프레임에 대응하는240Hz단계 없음')
        labels.append(' | '.join(n+' '+phases[k] for n,k in zip(names,samples[i][1])))
    def clock(t):
        c=round(t*100);return f'{c//360000}:{c//6000%60:02d}:{c//100%60:02d}.{c%100:02d}'
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1280\nPlayResY: 720\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Noto Sans CJK KR,21,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,3,1,0,2,15,15,18,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    events=[];start=0
    for i in range(1,len(labels)+1):
        if i==len(labels) or labels[i]!=labels[start]:
            events.append(f'Dialogue: 0,{clock(start/30.)},{clock(i/30.)},Default,,0,0,0,,{labels[start]}')
            start=i
    target=proof/'native_phases.ass';target.write_text(header+'\n'.join(events)+'\n')
    save(proof/'frame_phase_mapping.json',dict(source=str(trace),
        source_sha256=sha(trace),frames=len(labels),frame_times_s=frame_times,
        scope='env0 first episode; nearest preceding native240Hz phase; PTS0 corresponds to first capture endpoint',offset_s=offset))
    return target,offset

def collect_videos(case,seed,render,update,*,label=None,arm_std=None):
    label=label or case
    """실제 렌더에 과제/목표/시계만 표시한다. 추정 접촉이나 가짜3D영역을 만들지 않는다."""
    video=STUDY/'동영상';video.mkdir(exist_ok=True)
    proof=STUDY/'검증/영상표시'/f'{label}_s{seed}';proof.mkdir(parents=True,exist_ok=True)
    subtitles,offset=phase_subtitles(render,proof)
    row=case_row(case);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    header=proof/'header.txt';header.write_text(f'{label} | 손가락 초기std0.35 | 팔 초기std{arm_std} | LR {CONFIG[label]["lr_mode"]} | 학습 {update}회 | seed {seed}')
    filters=[f"drawtext=fontfile='{font}':textfile='{header}':fontsize=21:fontcolor=white:box=1:boxcolor=black@0.65:x=15:y=12",
             "drawtext=fontfile='"+font+"':text='t=%{pts\\:hms\\:"+str(offset)+"}':fontsize=19:fontcolor=white:box=1:boxcolor=black@0.65:x=w-tw-15:y=12"]
    for i,t in enumerate(row['compiled_targets']):
        p=proof/f'target{i}.txt';p.write_text(f"{ {1:'검지',2:'중지',3:'약지',4:'소지'}[t['finger']]} | {t['string']+1}번 줄 {t['fret']}프렛 | {t['onset_s']:.2f} - {t['end_s']:.2f}초")
        common=f"drawtext=fontfile='{font}':textfile='{p}':fontsize=19:box=1:boxcolor=black@0.65:x=15:y={44+25*i}"
        filters.append(common+':fontcolor=white')
        filters.append(common+f":fontcolor=lime:enable='gte(t+{offset},{t['onset_s']})*lt(t+{offset},{t['end_s']})'")
    filters.append(f"ass=filename='{subtitles}'")
    collected=read(proof/'manifest.json') if (proof/'manifest.json').is_file() else {}
    for view in ('hand','fullbody'):
        source=render/(view+'.mp4');target=video/f'{label}_s{seed}_u{update}_{view}.mp4'
        old=collected.get(str(target),{});source_hash=sha(source)
        reusable=(target.is_file() and old.get('sha256')==sha(target) and old.get('source_sha256')==source_hash)
        source_info=read_probe(source)
        if not reusable:
            attempt=1
            temporary=proof/f'{view}_encode_attempt{attempt:02d}.mp4'
            while temporary.exists():
                attempt+=1;temporary=proof/f'{view}_encode_attempt{attempt:02d}.mp4'
            subprocess.run(['ffmpeg','-v','error','-i',str(source),'-vf',','.join(filters),'-an','-c:v','libx264','-crf','19','-preset','fast','-movflags','+faststart',str(temporary)],check=True,timeout=max(1,min(240,remaining())))
            if read_probe(temporary)!=source_info:raise ValueError('표시 영상 프레임/크기/재생률 불일치')
            if target.exists():
                target.rename(proof/f'{view}_unverified_attempt{attempt:02d}.mp4')
            os.replace(temporary,target)
        info=read_probe(target)
        if info!=source_info:raise ValueError('저장 영상의 프레임/크기/재생률 불일치')
        collected[str(target)]=dict(sha256=sha(target),source=str(source),source_sha256=source_hash,**info)
        save(proof/'manifest.json',collected)
    return collected

def read_probe(path):
    r=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate','-of','json',str(path)],capture_output=True,text=True,check=True,timeout=20)
    return json.loads(r.stdout)['streams'][0]


def wait_gpu(state,key,pins):
    while True:
        check_time();verify(pins);busy=occupied()
        if not busy:return
        state.update(status='GPU 대기',current_task=key,gpu_processes=busy,updated_at=stamp());save(STATE,state)
        time.sleep(min(10,max(1,remaining())))


def write_summary(state):
    lines=['# 중지6→8프렛 탐색·학습률 비교','',f'갱신: {stamp()}','',
        '같은400회 평가를 주 비교로 사용한다. 대표 영상은 조건별 최선 모델이므로 비교 모델과 다를 수 있다. 평가16환경은 같은 준비 입력 반복이며 독립16학습시드가 아니다.','',
        '| 조건 | 팔 초기std | LR 정책 | 상태 | 평가100/200/400의 B유지율 | 400회 전체 달성 | 400회 엄격 통과 | 대표 영상 |',
        '| --- | ---: | --- | --- | --- | --- | --- | --- |']
    for label,std,mode in CONDITIONS:
        c=state.get('cases',{}).get(label+'_s7',{});evaluations=c.get('evaluations',{})
        progression='/'.join(f"{evaluations[str(u)]['result']['clean_fraction_by_target'][1]:.1%}" if str(u) in evaluations else '—' for u in (100,200,400))
        end=evaluations.get('400',{}).get('result',{});video=next((p for p in c.get('videos',{}) if p.endswith('_hand.mp4')),None)
        lines.append(f"| {label} | {std} | {mode} | {c.get('status','대기')} | {progression} | {end.get('safe_success','—')}/16 | {end.get('passed','—')} | "+(f'[손 확대]({video})' if video else '—')+' |')
    lines+=['','진행 상태: '+str(state.get('status')),'','실행 오류: '+str(state.get('failure')),
        '', 'recover_floor는 반복 시작에서만 LR을 최소1.5e-5로 복구한다. KL 재시도 중에는 원래 rollback·추가 감소를 허용하며 실제 수용 LR과 시작 LR을 별도로 기록한다.']
    (STUDY/'결과.md').write_text('\n'.join(lines)+'\n')
    script=SELF.parent/'analyze.py'
    if script.is_file() and remaining()>2:
        try:
            result=subprocess.run(['/home/ajou/miniconda3/bin/python','-B',str(script)],cwd=ROOT,capture_output=True,text=True,timeout=min(120,remaining()))
            if result.returncode:raise RuntimeError(result.stderr[-2000:])
        except Exception as error:
            state.setdefault('analysis_errors',[]).append(dict(at=stamp(),failure=repr(error)));save(STATE,state)


def check_native(state,pins):
    reference=STUDY/'검증/참조/A0_reference.json'
    ref=read(reference)
    if ref.get('case_id')!='A0' or ref.get('candidate_valid') is not True or ref.get('catalog_sha256')!=sha(STUDY/'입력/A0/catalog.json'):
        raise IntegrityError('새 참조의 입력/과제 계약 불일치')
    dependencies=merge_pins(pins,ref['source_sha256'],{str(reference):sha(reference)})
    out=execute(state,'A0_native','replay',['--inputs',STUDY/'입력/A0','--reference-json',reference],dependencies)
    report=read(out/'report.json');episode=read(out/'episode.json');diag=read(out/'diagnostics.json')['summary']
    fractions=[episode['left_note_ledger']['values']['clean'][i]/(t['end_s']-t['onset_s']) for i,t in enumerate(case_row('A0')['compiled_targets'])]
    result=dict(out=str(out),clean_fraction_by_target=fractions,timing=diag,
        passed=bool(report.get('native_reference_pass') is True and report.get('requested_path_rate_feasible') is True and safe(episode) and min(fractions)>=.9 and diag['timing_pass_episodes']==1))
    state['native_validation']=result;save(STATE,state)
    if not result['passed']:raise RuntimeError('동일 A0 참조의 새 물리 검증 미달: 학습 시작 보류')


def smoke(state,pins):
    proof=STUDY/'검증/GPU연결검증.json'
    if state.get('smoke_completed'):
        verify(state['smoke_artifacts']);return
    args=['--inputs',STUDY/'입력/A0','--arm-std',.20,'--lr-mode','recover_floor','--updates',2,'--num-envs',8,
          '--size','large','--horizon',32,'--seed',7,'--checkpoint-every',1]
    train=execute(state,'검증_train2','train',args,pins,updates=2)
    resumed=execute(state,'검증_resume2','train',['--resume',train/'J/final.pt','--updates',2,'--checkpoint-every',1],pins,updates=2)
    if read(resumed/'J/report.json')['optimizer_updates']!=4:raise ValueError('엄격 재개 누적 횟수 불일치')
    checkpoint=resumed/'J/final.pt'
    evaluated=execute(state,'검증_eval2','evaluate',['--checkpoint',checkpoint,'--num-envs',2],pins,checkpoint=checkpoint)
    if read(evaluated/'diagnostics.json')['summary']['episodes']!=2:raise ValueError('연결 검사 평가 분모 불일치')
    render=execute(state,'검증_render1','render',['--checkpoint',checkpoint,'--num-envs',1],pins,checkpoint=checkpoint)
    document=dict(completed=True,scope='실제 GPU 연결과 엄격 재개 검사; 압현 성공 인증 아님',
        artifacts={**manifest(train),**manifest(resumed),**manifest(evaluated),**manifest(render)},source_pins=pins)
    save(proof,document);state.update(smoke_completed=True,smoke_artifacts={str(proof):sha(proof),**document['artifacts']});save(STATE,state)


def run_case(state,label,std,mode,pins):
    name=label+'_s7';c=state['cases'].setdefault(name,dict(status='대기',evaluations={},arm_std=std,lr_mode=mode))
    if c.get('finished'):
        for key,item in state['tasks'].items():
            if key.startswith(name+'_') and item.get('completed'):
                verify(item['artifacts']);verify(item.get('dependency_pins',{}))
                validated_report(Path(item['out']),item['action'],Path(item['checkpoint']) if item.get('checkpoint') else None,item.get('updates'))
        for path,value in c.get('videos',{}).items():verify({path:value['sha256']})
        return
    check_time(training=True,reserve=50*60)
    c['status']='400회 학습';save(STATE,state);write_summary(state)
    train=execute(state,name+'_train400','train',['--inputs',STUDY/'입력/A0','--arm-std',std,'--lr-mode',mode,
        '--updates',400,'--num-envs',64,'--size','large','--horizon',32,'--seed',7,'--checkpoint-every',100],pins,updates=400)
    candidates=[]
    for update in (100,200,400):
        checkpoint=train/'J'/('final.pt' if update==400 else f'checkpoint_{update:06d}.pt')
        out=execute(state,name+f'_eval{update}','evaluate',['--checkpoint',checkpoint,'--num-envs',16],pins,checkpoint=checkpoint)
        entry=dict(update=update,checkpoint=str(checkpoint),out=str(out),result=evaluation(out,'A0'))
        c['evaluations'][str(update)]=entry;candidates.append(entry);save(STATE,state);write_summary(state)
    best=max(candidates,key=lambda x:select_score(x['result'],x['update']))
    c.update(selected=best,comparison=c['evaluations']['400'],status='대표 영상 저장')
    out=execute(state,name+'_render_best','render',['--checkpoint',best['checkpoint'],'--num-envs',1],pins,checkpoint=Path(best['checkpoint']))
    c['videos']=collect_videos('A0',7,out,best['update'],label=label,arm_std=std)
    c.update(finished=True,status='엄격 통과' if c['comparison']['result']['passed'] else '과제 성능 미달',finished_at=stamp())
    save(STATE,state);write_summary(state)


def freeze():
    original=PREVIOUS/'검증/실행봉인.json';pins=dict(read(original)['pins']);verify(pins)
    pins[str(original)]=sha(original)
    for filename in ('run_study.py','learning.py','test_learning.py','inputs.py','analyze.py'):
        path=SELF.parent/filename;pins[str(path)]=sha(path)
    for filename in ('입력CPU검증.json','학습기CPU검증.json','드라이버CPU검증.json','독립검수.md'):
        path=STUDY/'검증'/filename
        if path.suffix=='.json' and read(path).get('completed') is not True:raise ValueError('미완료 CPU 검사: '+str(path))
        pins[str(path)]=sha(path)
    for folder in (STUDY/'입력',STUDY/'검증/참조'):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:pins[str(path)]=sha(path)
    verify(pins);save(SEAL,dict(completed=True,schema='a0_exploration_lr_seal.v1',pins=pins,created_at=stamp(),conditions=CONDITIONS,updates=400))
    print('실행 봉인:',len(pins),'파일')


def self_test():
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as folder:
        path=Path(folder)/'p.json';save(path,dict(a=1));verify({str(path):sha(path)})
        try:merge_pins({'a':'1'},{'a':'2'})
        except IntegrityError:pass
        else:raise AssertionError('SHA 충돌 허용')
        with patch.dict(globals(),STATE=Path(folder)/'s.json',STUDY=Path(folder),wait_gpu=lambda *a:None,check_time=lambda **k:None):
            state=dict(tasks={},driver_pins={})
            with patch.object(subprocess,'Popen',side_effect=OSError('test')) as process:
                try:execute(state,'failed','train',[],{},updates=400)
                except RuntimeError:pass
                else:raise AssertionError('실패 허용')
                assert process.call_count==2 and len(state['tasks']['failed']['attempt_history'])==2
    assert len(CONDITIONS)==4 and len({(s,m) for _,s,m in CONDITIONS})==4
    assert {s for _,s,_ in CONDITIONS}=={.15,.20}
    assert {m for _,_,m in CONDITIONS}=={'existing','recover_floor'}
    assert str(ROOT/'scripts/tab2body.py') in command('train',Path('/tmp/x'))
    # 최선 영상이100회여도 공통400회 비교 결과를 바꾸지 않는다.
    with tempfile.TemporaryDirectory() as folder:
        calls=[]
        def fake_execute(state,key,action,args,pins,**kwargs):
            calls.append((key,action,args,kwargs));return Path(folder)/key
        good=dict(passed=True,safe_success=16,clean_fraction_by_target=[1.,1.],timing_pass=16,wrong_target_time_ratio=0.)
        bad=dict(good,passed=False,safe_success=0,clean_fraction_by_target=[1.,0.],timing_pass=0)
        state=dict(cases={},tasks={})
        with patch.dict(globals(),STUDY=Path(folder),STATE=Path(folder)/'state.json',execute=fake_execute,
            check_time=lambda **k:None,write_summary=lambda s:None,collect_videos=lambda *a,**k:{},
            evaluation=lambda out,case:good if str(out).endswith('eval100') else bad):
            run_case(state,'C00',.15,'existing',{})
        case=state['cases']['C00_s7']
        assert case['selected']['update']==100 and case['comparison']['update']==400
        assert case['status']=='과제 성능 미달'
        assert calls[0][2][calls[0][2].index('--updates')+1]==400
        assert [c[0] for c in calls if c[1]=='evaluate']==['C00_s7_eval100','C00_s7_eval200','C00_s7_eval400']
    print('CPU 검사 통과: 네 조건·SHA·제한 재시도·공식 실행 접두사')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true');parser.add_argument('--self-test',action='store_true');parser.add_argument('--smoke-only',action='store_true')
    args=parser.parse_args()
    if args.self_test:return self_test()
    if args.freeze:return freeze()
    pins=read(SEAL)['pins'];verify(pins)
    lockpath=STUDY/'실행/driver.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
    lock=lockpath.open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=read(STATE) if STATE.exists() else dict(tasks={},cases={})
    if state.get('driver_pins') and state['driver_pins']!=pins:raise IntegrityError('실행 봉인 변경')
    state.update(driver_pins=pins,driver_pid=os.getpid(),completed=False,failure=None,status='연결 검사',updated_at=stamp())
    state.setdefault('started_at',stamp())
    def interrupted(signum,frame):raise KeyboardInterrupt('중단 신호 '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        smoke(state,pins);check_native(state,pins)
        if args.smoke_only:
            state.update(status='연결 검사 완료',current_task=None);return
        for label,std,mode in CONDITIONS:
            try:run_case(state,label,std,mode,pins)
            except (DeadlineReached,IntegrityError,KeyboardInterrupt):raise
            except Exception as error:
                state['cases'].setdefault(label+'_s7',dict(evaluations={})).update(finished=True,status='실행 오류로 보류',failure=repr(error))
                save(STATE,state);write_summary(state)
        verify(pins);state.update(completed=True,status='완료',current_task=None,finished_at=stamp())
    except BaseException as error:
        state.update(status='중단 또는 검증 오류',failure=repr(error),updated_at=stamp());raise
    finally:
        state.update(driver_pid=None,child_pid=None,updated_at=stamp());save(STATE,state);write_summary(state);lock.close()


if __name__=='__main__':main()
