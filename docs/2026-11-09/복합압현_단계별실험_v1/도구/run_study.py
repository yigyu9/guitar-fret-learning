"""복합 압현의 순차 학습·평가·대표 영상과 분기 판단을 기록한다.

검증된 새 입력/학습기만 별도 프로세스로 실행한다. 실패 원문은 보존하고,
관측/모델 계약을 우회하거나 성능 실패를 실행 오류로 바꾸지 않는다.
"""
import argparse
import bisect
import gzip
from datetime import datetime, timezone
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
ORDER=('B1','B2','S1','T1','S2','T2','S3','T3','O1','C1','C2')
DEPENDENCIES={'B1':(), 'B2':('B1',), 'S1':('B2',), 'T1':('B2','S1'),
 'S2':('B2',), 'T2':('T1','S2'), 'S3':('B2',), 'T3':('T1','S3'),
 'O1':('T3',), 'C1':('B2','S3'), 'C2':('C1','T1'), 'D1':('B2',), 'D2':('D1',)}
SINGLE={'B1','B2','S1','S2','S3','D1','D2'}


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
    if changed:raise RuntimeError('실행 입력/산출물 SHA 불일치: '+', '.join(changed))


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
    timing_key='internal_timing_pass_episodes' if case in SINGLE else 'timing_pass_episodes'
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
    overlaps=case in ('O1','C1','C2')
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


def execute(state,key,action,args,pins,*,checkpoint=None,updates=None):
    """완료 재사용은 원문SHA/보고서 재검증 뒤에만 허용한다."""
    item=state['tasks'].get(key)
    if item and item.get('completed'):
        verify(item['artifacts']);verify(item.get('dependency_pins',{}));out=Path(item['out']);validated_report(out,action,checkpoint,updates)
        return out
    out,attempt=new_output(key);log=STUDY/'실행/작업로그'/(out.name+'.log');log.parent.mkdir(parents=True,exist_ok=True)
    state['tasks'][key]=dict(completed=False,out=str(out),attempt=attempt,action=action,
        checkpoint=str(checkpoint) if checkpoint is not None else None,updates=updates,
        dependency_pins={p:h for p,h in pins.items() if state.get('driver_pins',{}).get(p)!=h})
    while True:
        verify(pins);busy=occupied()
        if not busy:break
        state.update(status='GPU 대기',current_task=key,gpu_processes=busy,updated_at=stamp());save(STATE,state);time.sleep(10)
    cmd=command(action,out,*args);process=None;start=time.monotonic()
    try:
        verify(pins)
        env=dict(os.environ,PYTHONPATH=str(ROOT),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        with log.open('xb') as stream:
            process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            state.update(status='실행 중',current_task=key,child_pid=process.pid,log=str(log),command=cmd,started_at=stamp())
            while process.poll() is None:
                state['updated_at']=stamp();save(STATE,state)
                if time.monotonic()-start>(3600 if action=='train' else 1800):raise TimeoutError(key)
                time.sleep(5)
            if process.returncode!=0:raise RuntimeError('실행 종료 코드 '+str(process.returncode)+': '+str(log))
        validated_report(out,action,checkpoint,updates)
        state['tasks'][key].update(completed=True,artifacts=manifest(out),wall_s=time.monotonic()-start,finished_at=stamp())
        return out
    finally:
        if process is not None:close_group(process)
        state.update(child_pid=None,updated_at=stamp());save(STATE,state);verify(pins)


def training_args(case,seed):
    return ['--inputs',STUDY/'입력'/case,'--updates',100,'--num-envs',64,'--size','large','--horizon',32,'--seed',seed,'--checkpoint-every',50]


def opportunities(out,case):
    m=len(case_row(case)['compiled_targets']);counts=[0]*m
    for record in rows(out/'J/episodes.jsonl'):
        e=record['episode'];v=e['left_note_ledger']['values'];focus=e['left_note_ledger']['focus_mask']
        if e['reason']!='timeline_complete':continue
        for i in range(m):counts[i]+=int(focus[i] and v['performance_settled'][i])
    return counts


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


def collect_videos(case,seed,render,update):
    """실제 렌더에 과제/목표/시계만 표시한다. 추정 접촉이나 가짜3D영역을 만들지 않는다."""
    video=STUDY/'동영상';video.mkdir(exist_ok=True)
    proof=STUDY/'검증/영상표시'/f'{case}_s{seed}';proof.mkdir(parents=True,exist_ok=True)
    subtitles,offset=phase_subtitles(render,proof)
    row=case_row(case);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    header=proof/'header.txt';header.write_text(f'{case} | 초기 탐색 0.35 | 학습 {update}회 | seed {seed}')
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
        source=render/(view+'.mp4');target=video/f'{case}_s{seed}_u{update}_{view}.mp4'
        old=collected.get(str(target),{});source_hash=sha(source)
        reusable=(target.is_file() and old.get('sha256')==sha(target) and old.get('source_sha256')==source_hash)
        source_info=read_probe(source)
        if not reusable:
            attempt=1
            temporary=proof/f'{view}_encode_attempt{attempt:02d}.mp4'
            while temporary.exists():
                attempt+=1;temporary=proof/f'{view}_encode_attempt{attempt:02d}.mp4'
            subprocess.run(['ffmpeg','-v','error','-i',str(source),'-vf',','.join(filters),'-an','-c:v','libx264','-crf','19','-preset','fast','-movflags','+faststart',str(temporary)],check=True,timeout=240)
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


def write_summary(state):
    lines=['# 복합 압현 진행 결과','',f"갱신: {stamp()}",'','각16환경은 같은 준비 입력의 재현이며 독립 학습 시드16개가 아니다. 대표 영상은 동영상/에 모은다.','',
           '| 조건/seed | 상태 | 선택 모델 | 안전 전체달성 | 최소 목표유지율 | 시각 통과 | 엄격 최종해제 포함 | 대표 영상 |',
           '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for key,c in state.get('cases',{}).items():
        e=c.get('selected',{});v=e.get('result',{});vid=next((p for p in c.get('videos',{}) if p.endswith('_hand.mp4')),None)
        lines.append('| '+key+' | '+c['status']+' | '+str(e.get('update','—'))+' | '+str(v.get('safe_success','—'))+'/16 | '+(f"{min(v['clean_fraction_by_target']):.1%}" if v else '—')+' | '+str(v.get('timing_pass','—'))+'/16 | '+str(v.get('strict_timing_pass','—'))+'/16 | '+(f'[손 확대]({vid})' if vid else '—')+' |')
    lines+=['','실행 오류·기하 부적합·과제 성능 미달·선행 조건 보류를 별도로 기록한다. 시간·동시 접촉은240Hz진단에 근거하며 물리 접촉력/음향 품질 검증으로 확대하지 않는다.']
    (STUDY/'결과.md').write_text('\n'.join(lines)+'\n')


def run_case(state,case,seed,pins):
    name=f'{case}_s{seed}'
    state['cases'].setdefault(name,dict(status='대기',evaluations={}))
    c=state['cases'][name]
    if c.get('finished'):
        selected_native=c.get('native_task')
        if not selected_native or selected_native not in state['tasks']:raise ValueError('완료 조건의 선택 참조 실행 누락: '+name)
        related=[item for key,item in state['tasks'].items() if key.startswith(name+'_') or key==selected_native]
        if not related:raise ValueError('완료 조건의 실행 원문 누락: '+name)
        for item in related:
            if not item.get('completed'):raise ValueError('완료 조건에 미완료 실행 존재: '+name)
            verify(item['artifacts']);verify(item.get('dependency_pins',{}))
            checkpoint=Path(item['checkpoint']) if item.get('checkpoint') else None
            validated_report(Path(item['out']),item['action'],checkpoint,item.get('updates'))
        for p,item in c.get('videos',{}).items():verify({p:item['sha256']})
        return
    c['status']='물리 재생 검사';write_summary(state)
    native_args=['--inputs',STUDY/'입력'/case]
    reference=STUDY/'검증/복합기하/탐색_v4'/(case+'_reference.json')
    transition=STUDY/'검증/복합기하/전환경로_v1'/(case+'_reference.json')
    if transition.is_file():reference=transition
    refined=STUDY/'검증/복합기하/후보개선_v1'/(case+'_reference.json')
    if refined.is_file() and (refined.parent/'CPU검증.json').is_file():
        if read(refined.parent/'CPU검증.json').get('completed') is True:reference=refined
    native_pins=dict(pins);native_key=f'{case}_native'
    if reference.is_file():
        native_args+=['--reference-json',reference]
        native_pins.update(read(reference)['source_sha256']);native_pins[str(reference)]=sha(reference)
        native_key+='_'+sha(reference)[:12]
    verify(native_pins)
    c['native_task']=native_key
    native=execute(state,native_key,'replay',native_args,native_pins)
    replay=read(native/'report.json')
    if replay.get('task_success') is not True:
        c.update(status=('참조 경로 미확보: 학습 보류' if replay.get('supported') is False else '참조 물리 재생 미달: 학습 보류'),finished=True,passed=False,native=str(native))
        save(STATE,state);write_summary(state);return
    native_episode=read(native/'episode.json')
    target_clock=case_row(case)['compiled_targets']
    native_fractions=[native_episode['left_note_ledger']['values']['clean'][i]/(t['end_s']-t['onset_s']) for i,t in enumerate(target_clock)]
    native_diag=read(native/'diagnostics.json')['summary']
    c['native_validation']=dict(out=str(native),clean_fraction_by_target=native_fractions,
        requested_path_rate_feasible=replay.get('requested_path_rate_feasible'),
        strict_timing_pass=native_diag['timing_pass_episodes'],overlap_pass=native_diag['overlap_pass_episodes'],
        scope='native finite controller replay; a failed reference is not proof of physical impossibility')
    if replay.get('native_reference_pass') is not True or min(native_fractions)<.9 or (case in ('O1','C1','C2') and native_diag['overlap_pass_episodes']<1):
        c.update(status='참조 유지/시각/속도/동시 구간 미달: 학습 보류',finished=True,passed=False)
        save(STATE,state);write_summary(state);return
    train=execute(state,name+'_train100','train',training_args(case,seed),pins,updates=100)
    candidates=[]
    for update in (50,100):
        ckpt=train/'J'/('checkpoint_000050.pt' if update==50 else 'final.pt')
        out=execute(state,name+f'_eval{update}','evaluate',['--checkpoint',ckpt,'--num-envs',16],pins,checkpoint=ckpt)
        result=evaluation(out,case);entry=dict(update=update,checkpoint=str(ckpt),out=str(out),result=result)
        c['evaluations'][str(update)]=entry;candidates.append(entry);save(STATE,state);write_summary(state)
    opportunity=opportunities(train,case)
    c['completed_note_opportunities_100']=opportunity
    if min(opportunity)<320 or not candidates[-1]['result']['passed']:
        c['extension_reason']='목표 노출320회 미만' if min(opportunity)<320 else '100회 과제 기준 미달'
        resumed=execute(state,name+'_extend100','train',['--resume',train/'J/final.pt','--updates',100,'--checkpoint-every',50],pins,updates=100)
        ckpt=resumed/'J/final.pt'
        out=execute(state,name+'_eval200','evaluate',['--checkpoint',ckpt,'--num-envs',16],pins,checkpoint=ckpt)
        result=evaluation(out,case);entry=dict(update=200,checkpoint=str(ckpt),out=str(out),result=result)
        c['evaluations']['200']=entry;candidates.append(entry)
        c['completed_note_opportunities_total']=[a+b for a,b in zip(opportunity,opportunities(resumed,case))]
    best=max(candidates,key=lambda e:select_score(e['result'],e['update']))
    c.update(selected=best,passed=best['result']['passed'],status='대표 영상 저장')
    save(STATE,state);write_summary(state)
    render=execute(state,name+'_render_best','render',['--checkpoint',best['checkpoint'],'--num-envs',1],pins,checkpoint=Path(best['checkpoint']))
    c['videos']=collect_videos(case,seed,render,best['update'])
    c.update(status='통과' if c['passed'] else '과제 성능 미달',finished=True,finished_at=stamp())
    save(STATE,state);write_summary(state)


def freeze():
    """실행 전 독립검수/CPU/GPU 연결 증거와 새 입력을 고정한다."""
    # 참조 입력원장은 현재 실행과 동일한 활성코드/자산인지 전부 대조한다.
    original=ROOT/'docs/2026-11-09/탐색값_035_040_045_비교_v1/실행/std035_s7/J/inputs_before.json'
    pins=read(original);verify(pins)
    pins[str(original)]=sha(original)
    for name in ('learning.py','inputs.py','test_learning.py','run_study.py'):
        p=STUDY/'도구'/name;pins[str(p.resolve())]=sha(p)
    for p in sorted((STUDY/'입력').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:pins[str(p.resolve())]=sha(p)
    # 참조 경로는 학습 입력/정답이 아니다. 선택 시 출처와 함께 별도 봉인한다.
    # 이로써 다른 과제의 CPU 기하 탐색과 현재 과제의 GPU 학습을 병행한다.
    for name in ('입력_CPU검증.json','학습기_CPU검증.json','GPU_연결검증.json','구현독립검수.md'):
        p=STUDY/'검증'/name
        if not p.is_file():raise ValueError('실행 검증 근거 누락: '+str(p))
        if p.suffix=='.json' and read(p).get('completed') is not True:raise ValueError('미완료 검증 근거: '+str(p))
        pins[str(p.resolve())]=sha(p)
    pins[str(ROOT/'scripts/tab2body.py')]=sha(ROOT/'scripts/tab2body.py')
    verify(pins)
    save(SEAL,dict(schema='complex_press_study_seal.v1',completed=True,created_at=stamp(),pins=pins,
        active_default_modified=False,std_initial=.35,order=list(ORDER)))
    print('실행 봉인 저장:',len(pins),'파일')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze',action='store_true');parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--stop-after',choices=ORDER)
    args=parser.parse_args()
    if args.self_test:return self_test()
    if args.freeze:return freeze()
    seal=read(SEAL);pins=seal['pins']
    if not seal.get('completed'):raise ValueError('미완료 봉인')
    verify(pins)
    lockpath=STUDY/'실행/driver.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
    lock=lockpath.open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=read(STATE) if STATE.exists() else {}
    if state.get('driver_pins') and state['driver_pins']!=pins:raise ValueError('기존 실행 봉인이 달라 재사용 불가')
    state.update(schema='complex_press_sequential.v1',driver_pid=os.getpid(),driver_pins=pins,completed=False,failure=None)
    state.setdefault('tasks',{});state.setdefault('cases',{})
    def interrupted(signum,frame):raise KeyboardInterrupt('중단 신호 '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    def passed(case):return state['cases'].get(case+'_s7',{}).get('passed',False)
    try:
        for case in ORDER:
            blocked=[d for d in DEPENDENCIES[case] if not passed(d)]
            if blocked:
                state['cases'][case+'_s7']=dict(status='선행 조건 미달로 보류',blocked_by=blocked,passed=False,finished=True)
                save(STATE,state);write_summary(state)
            else:
                run_case(state,case,7,pins)
                if case in ('T3','O1') and not passed(case):
                    run_case(state,'D1',7,pins)
                    if case=='O1' and passed('D1'):run_case(state,'D2',7,pins)
            if args.stop_after==case:
                state.update(status='지정 단계까지 완료',current_task=None);return
        for case in ('T1','T3','C2'):
            if passed(case):
                for seed in (17,27):run_case(state,case,seed,pins)
        verify(pins)
        state.update(status='완료',completed=True,current_task=None,finished_at=stamp())
    except BaseException as error:
        state.update(status='중단 또는 오류',failure=repr(error),completed=False,updated_at=stamp());raise
    finally:
        state.update(driver_pid=None,child_pid=None,updated_at=stamp());save(STATE,state);write_summary(state);lock.close()


def self_test():
    """GPU 없이 변조·중복실행·프로세스 정리와 분기 의존성을 검사한다."""
    with tempfile.TemporaryDirectory() as name:
        p=Path(name)/'상태.json';save(p,dict(completed=False));pins={str(p):sha(p)};verify(pins)
        save(p,dict(completed=True))
        try:verify(pins)
        except RuntimeError:pass
        else:raise AssertionError('변조를 거부하지 않음')
        with (Path(name)/'lock').open('a') as a,(Path(name)/'lock').open('a') as b:
            fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:raise AssertionError('중복 실행을 거부하지 않음')
        child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True)
        close_group(child);assert child.poll() is not None
    seen=set()
    for case in ORDER:
        assert set(DEPENDENCIES[case])<=seen
        seen.add(case)
    base=dict(passed=False,safe_success=0,clean_fraction_by_target=[0.],timing_pass=0,wrong_target_time_ratio=0.)
    better=dict(base,passed=True,safe_success=16,clean_fraction_by_target=[1.],timing_pass=16)
    assert select_score(better,50)>select_score(base,200)
    print('CPU 검사 통과: 원자 저장·SHA 변조 거부·중복 잠금·프로세스 그룹 정리·분기 의존성·안전 평가 모델선정')


if __name__=='__main__':main()
