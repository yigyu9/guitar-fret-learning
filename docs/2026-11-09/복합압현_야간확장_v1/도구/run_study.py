"""복합 압현의 순차 학습·평가·대표 영상과 분기 판단을 기록한다.

검증된 새 입력/학습기만 별도 프로세스로 실행한다. 실패 원문은 보존하고,
관측/모델 계약을 우회하거나 성능 실패를 실행 오류로 바꾸지 않는다.
"""
import argparse
import bisect
import gzip
from datetime import datetime, timezone, timedelta
import fcntl
import hashlib
import json
import os
import re
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
FIRST_STUDY=ROOT/'docs/2026-11-09/복합압현_단계별실험_v1'
ORDER=('N01','N02','N03','N04','N07','N08','N05','N06','N09','N10','N11','N12')
ARM_CASES=(('A0_arm005',0.049787068367863944),('A0_arm010',.10),('A0_arm015',.15))
DEADLINE=datetime.fromisoformat('2026-11-03T10:00:00+09:00')
TRAIN_CUTOFF=datetime.fromisoformat('2026-11-03T09:30:00+09:00')
REFERENCE_MARKER=STUDY/'검증/기하/참조선택.json'
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
        raise DeadlineReached('오전10시 종료/오전9시30분 신규학습 중단 시간 예산')


def predecessor_ready(document):
    return document.get('completed') is True and document.get('driver_pid') is None


def wait_gpu(state,key,pins):
    while True:
        check_time();verify(pins)
        predecessor=read(FIRST_STUDY/'진행상황.json') if (FIRST_STUDY/'진행상황.json').exists() else {}
        busy=occupied()
        if predecessor_ready(predecessor) and not busy:return
        state.update(status='선행 연구/GPU 대기',current_task=key,updated_at=stamp(),
            predecessor_completed=predecessor.get('completed'),predecessor_status=predecessor.get('status'),gpu_processes=busy)
        save(STATE,state);time.sleep(min(10,max(1,remaining())))


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


def training_args(case,seed,arm_std):
    return ['--inputs',STUDY/'입력'/case,'--updates',100,'--num-envs',64,'--size','large','--horizon',32,
            '--seed',seed,'--checkpoint-every',50,'--arm-std',arm_std]


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


def collect_videos(case,seed,render,update,*,label=None,arm_std=None):
    label=label or case
    """실제 렌더에 과제/목표/시계만 표시한다. 추정 접촉이나 가짜3D영역을 만들지 않는다."""
    video=STUDY/'동영상';video.mkdir(exist_ok=True)
    proof=STUDY/'검증/영상표시'/f'{label}_s{seed}';proof.mkdir(parents=True,exist_ok=True)
    subtitles,offset=phase_subtitles(render,proof)
    row=case_row(case);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    header=proof/'header.txt';header.write_text(f'{label} | 손가락 std0.35 | 팔 std{arm_std} | 학습 {update}회 | seed {seed}')
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


def update_analysis(state):
    """분석 실패는 원문을 보존하되 학습 실행 실패로 바꾸지 않는다."""
    if remaining()<=0:
        state['analysis_deferred']=dict(at=stamp(),reason='시간 마감으로 신규 분석 보류; 기존 산출물 보존');save(STATE,state);return
    script=SELF.parent/'analyze.py'
    if not script.is_file():return
    logdir=STUDY/'분석/작업로그';logdir.mkdir(parents=True,exist_ok=True)
    log=logdir/('분석_'+str(time.time_ns())+'.log')
    try:
        env=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
        with log.open('xb') as stream:
            subprocess.run(['/home/ajou/miniconda3/bin/python','-B',str(script)],cwd=ROOT,env=env,
                stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=max(1,min(120,remaining())))
    except Exception as error:
        state.setdefault('analysis_errors',[]).append(dict(at=stamp(),log=str(log),failure=repr(error)))
        save(STATE,state)


def write_summary(state):
    lines=['# 야간 복합 압현 진행 결과','',f"갱신: {stamp()}",'','각16환경은 같은 준비 입력의 재현이며 독립 학습 시드16개가 아니다. 대표 영상은 동영상/에 모은다.','',
           '| 조건/seed | 상태 | 선택 모델 | 안전 전체달성 | 최소 목표유지율 | 시각 통과 | 엄격 최종해제 포함 | 대표 영상 |',
           '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for key,c in state.get('cases',{}).items():
        e=c.get('selected',{});v=e.get('result',{});vid=next((p for p in c.get('videos',{}) if p.endswith('_hand.mp4')),None)
        lines.append('| '+key+' | '+c['status']+' | '+str(e.get('update','—'))+' | '+str(v.get('safe_success','—'))+'/16 | '+(f"{min(v['clean_fraction_by_target']):.1%}" if v else '—')+' | '+str(v.get('timing_pass','—'))+'/16 | '+str(v.get('strict_timing_pass','—'))+'/16 | '+(f'[손 확대]({vid})' if vid else '—')+' |')
    lines+=['','실행 오류·기하 부적합·과제 성능 미달·선행 조건 보류를 별도로 기록한다. 시간·동시 접촉은240Hz진단에 근거하며 물리 접촉력/음향 품질 검증으로 확대하지 않는다.']
    (STUDY/'결과.md').write_text('\n'.join(lines)+'\n')
    update_analysis(state)


def latest_marker():
    candidates=[]
    for path in REFERENCE_MARKER.parent.glob('참조선택*.json'):
        match=re.fullmatch(r'참조선택(?:_v(\d+))?\.json',path.name)
        if not match:continue
        try:complete=read(path).get('completed') is True
        except json.JSONDecodeError:continue
        if complete:candidates.append((int(match.group(1) or 1),path))
    return max(candidates)[1] if candidates else None


def reference_for(case,pins,marker_path=None):
    marker_path=marker_path or latest_marker()
    if marker_path is None:return None,dict(pins)
    marker=read(marker_path)
    if marker.get('schema')!='complex_press_night_reference_selection.v1' or marker.get('completed') is not True:
        raise ValueError('최종 참조 선택 근거 미완료')
    item=marker['cases'][case]
    if item['status'] in ('reference_unavailable','candidate_unavailable'):return None,dict(pins)
    if item['status']!='candidate_available':raise ValueError('알 수 없는 참조 상태')
    path=Path(item['reference']).resolve();path.relative_to(STUDY)
    if sha(path)!=item['sha256']:raise IntegrityError('선택 참조 SHA 불일치')
    ref=read(path)
    if (ref.get('schema')!='guitar_learning.complex_press_night_reference.v1' or ref.get('case_id')!=case or
            ref.get('catalog_sha256')!=sha(STUDY/'입력'/case/'catalog.json') or ref.get('candidate_valid') is not True):
        raise ValueError('선택 참조의 과제/입력 계약 불일치')
    result=merge_pins(pins,{str(marker_path.resolve()):sha(marker_path)},marker['source_sha256'],{str(path):sha(path)},ref['source_sha256']);verify(result)
    return path,result


def native_check(state,case,pins):
    selections=state.setdefault('native_selections',{})
    selected=selections.get(case)
    if selected:
        verify(selected['dependency_pins']);marker_path=Path(selected['marker'])
    else:
        marker_path=latest_marker()
    reference,dependencies=reference_for(case,pins,marker_path)
    if reference is None and not selected and not state.get('reference_wait_completed'):
        # 전체 연구에서 미확보 참조를 최대10분 한 번만 기다린다. 사용한 참조는 교체하지 않는다.
        until=time.monotonic()+600;original=marker_path
        state['reference_wait_completed']=True;state['reference_wait_started_at']=stamp();save(STATE,state)
        while time.monotonic()<until:
            check_time(training=True,reserve=35*60)
            state.update(status='후속 참조 근거 대기',current_task=case+'_native',updated_at=stamp());save(STATE,state)
            newer=latest_marker()
            if newer is not None and newer!=original:
                marker_path=newer;reference,dependencies=reference_for(case,pins,marker_path);break
            time.sleep(min(10,max(1,remaining())))
    if reference is None:
        marker=read(marker_path) if marker_path is not None else {}
        state.setdefault('unavailable_references',{})[case]=dict(marker=str(marker_path) if marker_path else None,
            marker_sha256=sha(marker_path) if marker_path else None,
            original_reason=marker.get('cases',{}).get(case,{}).get('reason','최종 선택 marker 미확보'),
            original_status=marker.get('cases',{}).get(case,{}).get('status'))
        save(STATE,state);return None
    if not selected:
        selections[case]=dict(marker=str(marker_path),reference=str(reference),dependency_pins={p:h for p,h in dependencies.items() if pins.get(p)!=h})
        save(STATE,state)
    key=case+'_native_'+sha(reference)[:12]
    out=execute(state,key,'replay',['--inputs',STUDY/'입력'/case,'--reference-json',reference],dependencies)
    report=read(out/'report.json');ep=read(out/'episode.json');diag=read(out/'diagnostics.json')['summary']
    targets=case_row(case)['compiled_targets']
    fractions=[ep['left_note_ledger']['values']['clean'][i]/(t['end_s']-t['onset_s']) for i,t in enumerate(targets)]
    overlaps=any(a['onset_s']<b['end_s']-1e-9 and b['onset_s']<a['end_s']-1e-9 for i,a in enumerate(targets) for b in targets[i+1:])
    passed=(report.get('task_success') is True and report.get('requested_path_rate_feasible') is True and
            safe(ep) and min(fractions)>=.9 and diag['timing_pass_episodes']==1 and
            (not overlaps or diag['overlap_pass_episodes']==1))
    return dict(passed=passed,out=str(out),key=key,reference=str(reference),fractions=fractions,
        strict_timing_pass=diag['timing_pass_episodes'],overlap_pass=diag['overlap_pass_episodes'],
        scope='새 실제 재생; 기하 후보 미달은 물리 불가능 증명이 아님')


def run_case(state,label,case,arm_std,pins,seed=7):
    name=f'{label}_s{seed}';state['cases'].setdefault(name,dict(status='대기',evaluations={},input_case=case,arm_std=arm_std))
    item=state['cases'][name]
    if item.get('finished'):
        native_key=(item.get('native_validation') or {}).get('key')
        for key,t in state['tasks'].items():
            if (key.startswith(name+'_') or key==native_key) and t.get('completed'):
                verify(t['artifacts']);verify(t.get('dependency_pins',{}));validated_report(Path(t['out']),t['action'],Path(t['checkpoint']) if t.get('checkpoint') else None,t.get('updates'))
        for path,value in item.get('videos',{}).items():verify({path:value['sha256']})
        return
    check_time(training=True,reserve=35*60)
    native=native_check(state,case,pins);item['native_validation']=native
    if native is None:
        item.update(status='기하 참조 미확보로 보류',finished=True,passed=False,
            unavailable_reference=state.get('unavailable_references',{}).get(case))
        save(STATE,state);write_summary(state);return
    if not native['passed']:
        item.update(status='새 물리 재생 기준 미달로 학습 보류',finished=True,passed=False)
        save(STATE,state);write_summary(state);return
    train=execute(state,name+'_train100','train',training_args(case,seed,arm_std),pins,updates=100)
    candidates=[]
    for update in (50,100):
        checkpoint=train/'J'/('checkpoint_000050.pt' if update==50 else 'final.pt')
        out=execute(state,name+f'_eval{update}','evaluate',['--checkpoint',checkpoint,'--num-envs',16],pins,checkpoint=checkpoint)
        candidate=dict(update=update,checkpoint=str(checkpoint),out=str(out),result=evaluation(out,case))
        item['evaluations'][str(update)]=candidate;candidates.append(candidate);save(STATE,state);write_summary(state)
    opportunity=opportunities(train,case);item['opportunities_100']=opportunity
    if case=='A0' or min(opportunity)<320 or not candidates[-1]['result']['passed']:
        item['extension_reason']='팔 std 비교의 공통200회 예산' if case=='A0' else '노출320회 미만 또는100회 기준 미달'
        # 연장도 새 학습 시작 시간과 평가/영상 마무리 예산을 만족해야 한다.
        try:check_time(training=True,reserve=20*60)
        except DeadlineReached:item['extension_deferred']='오전 종료 시간 예산'
        else:
            resumed=execute(state,name+'_extend100','train',['--resume',train/'J/final.pt','--updates',100,'--checkpoint-every',50],pins,updates=100)
            item['opportunities_total_200']=[a+b for a,b in zip(opportunity,opportunities(resumed,case))]
            checkpoint=resumed/'J/final.pt'
            out=execute(state,name+'_eval200','evaluate',['--checkpoint',checkpoint,'--num-envs',16],pins,checkpoint=checkpoint)
            candidate=dict(update=200,checkpoint=str(checkpoint),out=str(out),result=evaluation(out,case))
            item['evaluations']['200']=candidate;candidates.append(candidate)
    best=max(candidates,key=lambda c:select_score(c['result'],c['update']))
    item.update(selected=best,passed=best['result']['passed'],status='대표 영상 저장');save(STATE,state)
    out=execute(state,name+'_render_best','render',['--checkpoint',best['checkpoint'],'--num-envs',1],pins,checkpoint=Path(best['checkpoint']))
    item['videos']=collect_videos(case,seed,out,best['update'],label=label,arm_std=arm_std)
    item.update(status='엄격 통과' if item['passed'] else '과제 성능 미달',finished=True,finished_at=stamp())
    save(STATE,state);write_summary(state)


def choose_arm(cases):
    """세 std의 최대 공통 평가 횟수로만 선택한다. 영상의 best 모델과 구분한다."""
    baseline=ARM_CASES[0][1];common={50,100,200};comparisons={};opportunity={}
    for label,std in ARM_CASES:
        case=cases.get(label+'_s7',{});evaluated=case.get('evaluations',{})
        common&={int(key) for key,value in evaluated.items() if int(key) in (50,100,200) and value.get('result') is not None}
        opportunity[label]=dict(at100=case.get('opportunities_100'),at200=case.get('opportunities_total_200'))
    if not common:
        return dict(arm_std=baseline,comparison_complete=False,comparison_update=None,opportunities=opportunity,
            reason='세 조건의 공통 평가가 없어 비교 불완전: 기준 팔 std 유지',eligible=[])
    update=max(common);eligible=[];base=None
    for label,std in ARM_CASES:
        entry=cases[label+'_s7']['evaluations'][str(update)];result=entry['result']
        comparisons[label]=entry
        if result.get('passed'):
            eligible.append((label,std,result))
            if std==baseline:base=result
    evidence=dict(comparison_complete=True,comparison_update=update,comparison_entries=comparisons,opportunities=opportunity,
        scope='세 조건의 동일 optimizer 횟수·같은 입력·seed7 평균정책 비교; 영상 best 모델 선택과 별도')
    if not eligible:return dict(arm_std=baseline,reason='동일 횟수 평가에서 안전한 엄격 통과 우위 미입증: 기준값 유지',eligible=[],**evidence)
    if base:
        better=[]
        for label,std,r in eligible:
            nonworse=(r['safe_success']>=base['safe_success'] and r['timing_pass']>=base['timing_pass'] and
                r['wrong_target_time_ratio']<=base['wrong_target_time_ratio']+1e-9 and
                r['clean_fraction_by_target'][-1]>=base['clean_fraction_by_target'][-1]-1e-9)
            meaningful=(r['safe_success']>base['safe_success'] or r['timing_pass']>base['timing_pass'] or
                r['wrong_target_time_ratio']<=base['wrong_target_time_ratio']-.01 or
                r['clean_fraction_by_target'][-1]>=base['clean_fraction_by_target'][-1]+.05)
            if nonworse and meaningful:better.append((label,std,r))
        if not better:return dict(arm_std=baseline,reason='같은 횟수에서 기준도 엄격 통과하며 명확한 비악화 우위 없음: 최소값 유지',eligible=[x[0] for x in eligible],**evidence)
        eligible=better
    best=max(eligible,key=lambda x:(x[2]['safe_success'],x[2]['timing_pass'],
        -x[2]['wrong_target_time_ratio'],x[2]['clean_fraction_by_target'][-1],-x[1]))
    return dict(arm_std=best[1],selected=best[0],eligible=[x[0] for x in eligible],
        reason='동일 횟수의 엄격 통과·안전 유지, 성공/시각1개 또는 wrong1%p/목표B유지5%p 이상 차이; 동률 최소 std',**evidence)


def smoke(state,pins):
    """선행 연구 종료 뒤에만 작은 GPU 연결·동일 모델 엄격 재개를 실제 실행한다."""
    proof=STUDY/'검증/GPU_연결검증.json'
    if state.get('smoke_completed'):
        verify(state['smoke_artifacts']);return
    args=['--inputs',STUDY/'입력/A0','--updates',1,'--num-envs',8,'--size','large','--horizon',32,'--seed',7,'--checkpoint-every',1]
    train=execute(state,'검증_smoke_train1','train',args,pins,updates=1)
    resumed=execute(state,'검증_smoke_resume1','train',['--resume',train/'J/final.pt','--updates',1,'--checkpoint-every',1],pins,updates=1)
    if read(resumed/'J/report.json')['optimizer_updates']!=2:raise ValueError('연결 검사 엄격 재개의 누적 업데이트 불일치')
    checkpoint=resumed/'J/final.pt'
    evaluated=execute(state,'검증_smoke_eval2','evaluate',['--checkpoint',checkpoint,'--num-envs',2],pins,checkpoint=checkpoint)
    if read(evaluated/'diagnostics.json')['summary']['episodes']!=2:raise ValueError('연결 검사 평가 분모 불일치')
    render=execute(state,'검증_smoke_render1','render',['--checkpoint',checkpoint,'--num-envs',1],pins,checkpoint=checkpoint)
    values=dict(schema='complex_press_night_gpu_connection.v1',completed=True,train=str(train),resume=str(resumed),
        evaluate=str(evaluated),render=str(render),scope='실제 연결 검사이며 정책 압현 성공 인증 아님',source_pins=pins,
        artifacts={**manifest(train),**manifest(resumed),**manifest(evaluated),**manifest(render)})
    save(proof,values);state['smoke_completed']=True;state['smoke_artifacts']={str(proof):sha(proof),**values['artifacts']};save(STATE,state)


def freeze():
    original=FIRST_STUDY/'검증/실행봉인.json';source=read(original)
    if source.get('completed') is not True:raise ValueError('선행 연구 봉인 누락')
    pins=dict(source['pins']);verify(pins);pins[str(original)]=sha(original)
    for path in [SELF,LEARNER,SELF.parent/'inputs.py',SELF.parent/'test_learning.py',SELF.parent/'analyze.py',
                 STUDY/'검증/학습기CPU검증.json',STUDY/'검증/드라이버CPU검증.json',
                 STUDY/'검증/입력_CPU검증.json',STUDY/'검증/구현독립검수.md',STUDY/'검증/드라이버_독립검수.md',STUDY/'검증/기하분석_독립검수.md']:
        if not path.is_file():raise ValueError('새 연구 검증 근거 누락: '+str(path))
        if path.suffix=='.json' and read(path).get('completed') is not True:raise ValueError('미완료 검증 근거: '+str(path))
        pins[str(path.resolve())]=sha(path)
    for path in sorted((STUDY/'입력').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:pins[str(path.resolve())]=sha(path)
    verify(pins);save(SEAL,dict(schema='complex_press_night_study_seal.v1',completed=True,created_at=stamp(),pins=pins,
        deadline=DEADLINE.isoformat(),train_cutoff=TRAIN_CUTOFF.isoformat(),order=list(ORDER)))
    print('새 연구 실행 봉인 완료:',len(pins),'파일')


def finish_time_budget_cases(state):
    """진행 중 조건의 기존 평가·원문을 보존하면서 시간 중단을 명확히 표시한다."""
    for key,value in state['cases'].items():
        if value.get('finished'):continue
        evaluated=[name for name,t in state['tasks'].items() if name.startswith(key+'_') and t.get('action')=='evaluate' and t.get('completed')]
        value.update(status='시간 예산 중단: 완료 평가와 원문 보존' if evaluated else '시간 예산 중단: 평가 미완료',
            finished=True,passed=False,preserved_partial_task=True,
            evaluation_completion=dict(any_completed=bool(evaluated),completed_task_keys=evaluated,
                recorded_updates=list(value.get('evaluations',{}))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true');parser.add_argument('--self-test',action='store_true')
    args=parser.parse_args()
    if args.self_test:return self_test()
    if args.freeze:return freeze()
    seal=read(SEAL);pins=seal['pins']
    if seal.get('completed') is not True:raise ValueError('미완료 실행 봉인')
    verify(pins)
    lockpath=STUDY/'실행/driver.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
    lock=lockpath.open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=read(STATE) if STATE.exists() else {};state.setdefault('tasks',{});state.setdefault('cases',{})
    if state.get('driver_pins') and state['driver_pins']!=pins:raise IntegrityError('기존 실행 봉인이 다름')
    state.update(schema='complex_press_night_sequential.v1',driver_pins=pins,driver_pid=os.getpid(),completed=False,failure=None)
    def interrupted(signum,frame):raise KeyboardInterrupt('중단 신호 '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    def condition(label,case,std,seed=7):
        try:run_case(state,label,case,std,pins,seed)
        except (DeadlineReached,IntegrityError,KeyboardInterrupt):raise
        except Exception as error:
            state['cases'].setdefault(f'{label}_s{seed}',{}).update(finished=True,passed=False,status='실행 오류 두 번으로 보류',failure=repr(error),input_case=case,arm_std=std)
            save(STATE,state);write_summary(state)
    try:
        wait_gpu(state,'연결 검사 대기',pins);check_time(training=True,reserve=35*60);smoke(state,pins)
        for label,std in ARM_CASES:condition(label,'A0',std)
        state['arm_selection']=choose_arm(state['cases']);save(STATE,state)
        selected=state['arm_selection']['arm_std']
        for case in ORDER:condition(case,case,selected)
        # 서로 다른 종류의 유망 조건만 최대 두 개, 새 seed로 독립 재학습한다.
        kinds={**{x:'2음 동시' for x in ('N01','N02','N03','N04')},**{x:'3음 동시' for x in ('N05','N06')},
            'N07':'손가락 교대','N08':'손가락 교대','N09':'동일 손가락 왕복','N10':'중첩 유지','N11':'중첩 유지','N12':'2음 조합 전환'}
        promising=[]
        for case in ORDER:
            c=state['cases'].get(case+'_s7',{});r=c.get('selected',{}).get('result',{})
            if r and min(r['clean_fraction_by_target'])>=.8 and r['physical']==0 and r['wrist']==0:
                promising.append((case,r))
        promising.sort(key=lambda x:select_score(x[1],0),reverse=True)
        chosen=[];seen=set()
        for case,result in promising:
            if kinds[case] not in seen:chosen.append(case);seen.add(kinds[case])
            if len(chosen)==2:break
        state['repeat_selection']=dict(cases=chosen,kinds={x:kinds[x] for x in chosen},
            reason='유지80% 이상·평가 물리/손목0, 서로 다른 종류 최대2개' if chosen else '유지80% 이상·안전한 유망 조건이 없어 추가 반복하지 않음',seeds=[17,27])
        save(STATE,state)
        for case in chosen:
            for seed in (17,27):condition(case,case,selected,seed)
        verify(pins);state.update(status='완료',completed=True,current_task=None,finished_at=stamp())
    except DeadlineReached as error:
        state.setdefault('repeat_selection',dict(cases=[],reason='남은 시간 부족으로 후속 독립 seed 반복 보류',seeds=[17,27]))
        finish_time_budget_cases(state)
        for label,case in [(x[0],'A0') for x in ARM_CASES]+[(x,x) for x in ORDER]:
            state['cases'].setdefault(label+'_s7',dict(status='시간 예산 보류',passed=False,finished=True,input_case=case))
        state.update(status='시간 예산 종료',completed=True,current_task=None,failure=None,deadline_reason=str(error),finished_at=stamp())
    except BaseException as error:
        state.update(status='중단 또는 봉인 오류',completed=False,failure=repr(error));raise
    finally:
        state.update(driver_pid=None,child_pid=None,updated_at=stamp());save(STATE,state);write_summary(state);lock.close()


def self_test():
    """GPU 없이 시간 경계·오류 복구·겹침·모델 선택·실제 기존 보고서 호환을 검사한다."""
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as name:
        p=Path(name)/'상태.json';save(p,dict(completed=False));pins={str(p):sha(p)};verify(pins);save(p,dict(completed=True))
        try:verify(pins)
        except IntegrityError:pass
        else:raise AssertionError('변조를 허용함')
        with (Path(name)/'lock').open('a') as a,(Path(name)/'lock').open('a') as b:
            fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:raise AssertionError('중복 잠금 실패')
        child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True);close_group(child);assert child.poll() is not None
        assert predecessor_ready(dict(completed=True,driver_pid=None))
        assert not predecessor_ready(dict(completed=False,driver_pid=None))
        assert not predecessor_ready(dict(completed=True,driver_pid=1))
        for now,training,reserve in [(TRAIN_CUTOFF,True,0),(DEADLINE,False,0),(DEADLINE-timedelta(minutes=34),True,35*60)]:
            try:check_time(now=now,training=training,reserve=reserve)
            except DeadlineReached:pass
            else:raise AssertionError('시간 예산 검사가 실패함')
        assert merge_pins({'a':'x'},{'a':'x'})=={'a':'x'}
        try:merge_pins({'a':'x'},{'a':'y'})
        except IntegrityError:pass
        else:raise AssertionError('출처 SHA 충돌을 허용함')
        budget_state=dict(cases={'x_s7':dict(evaluations={'100':{'out':'보존'}},native_validation={'out':'원문'}),
            'y_s7':dict(evaluations={}), 'z_s7':dict(finished=True,passed=True,status='기존 통과')},
            tasks={'x_s7_eval100':dict(action='evaluate',completed=True)})
        finish_time_budget_cases(budget_state)
        assert budget_state['cases']['x_s7']['evaluations']['100']['out']=='보존'
        assert budget_state['cases']['x_s7']['native_validation']['out']=='원문'
        assert budget_state['cases']['x_s7']['evaluation_completion']['any_completed']
        assert budget_state['cases']['y_s7']['finished'] and not budget_state['cases']['y_s7']['passed']
        assert budget_state['cases']['z_s7']['passed']
        with patch.dict(globals(),STATE=Path(name)/'분석마감.json',remaining=lambda:-1):
            with patch.object(subprocess,'run') as process_run:
                analysis_state={};update_analysis(analysis_state)
                assert 'analysis_deferred' in analysis_state;process_run.assert_not_called()
        assert choose_arm({})['arm_std']==ARM_CASES[0][1]
        good=dict(passed=True,safe_success=16,timing_pass=16,physical=0,wrist=0,wrong_target_time_ratio=0.,clean_fraction_by_target=[1.,1.])
        cases={label+'_s7':dict(evaluations={'100':dict(update=100,result=good)},selected=dict(update=100,result=good)) for label,std in ARM_CASES}
        assert choose_arm(cases)['arm_std']==ARM_CASES[0][1]
        # 영상 best가 서로 달라도 공통100회만 팔 std 선정에 사용한다.
        cases['A0_arm010_s7']['evaluations']['200']=dict(update=200,result=good)
        cases['A0_arm010_s7']['selected']=dict(update=200,result=good)
        assert choose_arm(cases)['comparison_update']==100
        assert choose_arm(cases)['arm_std']==ARM_CASES[0][1]
        del cases['A0_arm005_s7'];assert choose_arm(cases)['arm_std']==ARM_CASES[0][1]
        assert not choose_arm(cases)['comparison_complete']
        # 작성 중이거나 미완료인 후속 marker는 선택하지 않는다.
        with patch.dict(globals(),REFERENCE_MARKER=Path(name)/'참조선택.json'):
            save(Path(name)/'참조선택.json',dict(completed=True))
            save(Path(name)/'참조선택_v2.json',dict(completed=True))
            save(Path(name)/'참조선택_v3.json',dict(completed=False))
            assert latest_marker().name=='참조선택_v2.json'
        # 로그만 남은 실패도 새 attempt를 선택한다.
        old=STUDY
        with patch.dict(globals(),STUDY=Path(name)):
            log=Path(name)/'실행/작업로그/x.log';log.parent.mkdir(parents=True);log.touch()
            out,attempt=new_output('x');assert out.name=='x_attempt02'
    with tempfile.TemporaryDirectory() as name:
        temp=Path(name);out=temp/'평가';out.mkdir()
        goals=[dict(onset_s=1.,end_s=2.),dict(onset_s=1.5,end_s=2.5)]
        episode=dict(valid=True,song=dict(safety_invalidated=False,stage_success=True,left_success_count=2),
            termination=dict(physical_failure=False,wrist_failure=False),
            left_note_ledger=dict(values=dict(clean=[1.,1.],best_clean_streak=[1.,1.],wrong=[0.,0.])))
        (out/'episodes.jsonl').write_text('\n'.join(json.dumps(dict(episode=episode)) for _ in range(16)))
        diagnostic=dict(episodes=16,exact_hz=240,timing_pass_episodes=16,internal_timing_pass_episodes=16,
            overlap_pass_episodes=0,terminal_release_pass_episodes=16,wrong_press_active_union_s=0.)
        save(out/'diagnostics.json',dict(summary=diagnostic))
        with patch.dict(globals(),case_row=lambda _:dict(compiled_targets=goals)):
            assert not evaluation(out,'N11')['passed']  # 이름 목록 대신 실제 시간 교차를 검사한다.
            diagnostic['overlap_pass_episodes']=16;save(out/'diagnostics.json',dict(summary=diagnostic))
            assert evaluation(out,'N11')['passed']
            diagnostic['timing_pass_episodes']=0;save(out/'diagnostics.json',dict(summary=diagnostic))
            assert not evaluation(out,'N11')['passed']  # 내부값만 통과해도 엄격 tail 실패는 탈락한다.
        state=dict(tasks={},driver_pins={})
        with patch.dict(globals(),STUDY=temp,STATE=temp/'진행.json',wait_gpu=lambda *a:None,check_time=lambda **k:None):
            with patch.object(subprocess,'Popen',side_effect=OSError('연결 검사 실패')) as popen:
                try:execute(state,'복구검사','train',[],{},updates=1)
                except RuntimeError:pass
                else:raise AssertionError('두 번 실패를 성공으로 처리함')
                assert popen.call_count==2
                assert len(state['tasks']['복구검사']['attempt_history'])==2
                assert len(list((temp/'실행/작업로그').glob('복구검사*.log')))==2
                try:execute(state,'복구검사','train',[],{},updates=1)
                except RuntimeError:pass
                else:raise AssertionError('실패 원문 없이 성공 재사용함')
                assert popen.call_count==2
    # 동결 기존 원문을 실행하지 않고 JSON 스키마만 대조한다.
    base=FIRST_STUDY/'실행/B1_s7_train100'
    validated_report(base,'train',updates=100)
    validated_report(FIRST_STUDY/'실행/B1_s7_eval100','evaluate',base/'J/final.pt')
    validated_report(FIRST_STUDY/'실행/B1_s7_render_best','render',base/'J/final.pt')
    assert str(ROOT/'scripts/tab2body.py') in command('train',Path('/tmp/out'))
    print('CPU 검사 통과: SHA/잠금/정리/시간/선행대기/선정/실패로그/원문보고서/공식실행접두사')


if __name__=='__main__':main()
