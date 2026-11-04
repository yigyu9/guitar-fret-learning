"""부모 비교 종료 후 동일 목표 재현과 새 동시 압현 개선을 제한 시간에 검사한다.

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
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
PYTHON=Path('/home/ajou/miniconda3/envs/rl38/bin/python')
LEARNER=SELF.parent/'learning.py'
STATE=STUDY/'진행상황.json'
SEAL=STUDY/'검증/실행봉인.json'
PARENT=ROOT/'docs/2026-11-09/중지6에서8_탐색학습률비교_v1'
MARKER=STUDY/'검증/참조/참조선택.json'
DEADLINE=datetime.fromisoformat('2026-11-03T14:08:00+09:00')
TRAIN_CUTOFF=datetime.fromisoformat('2026-11-03T13:40:00+09:00')
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
        raise DeadlineReached('14:08 종료/13:40 신규 학습 중단 시간 예산')

def execute(state,key,action,args,pins,*,checkpoint=None,updates=None):
    """완료 근거를 재검증하고 실행오류는 새 원문을 남기며 한 번만 재시도한다."""
    pins=merge_pins(pins,state.get('parent_evidence_pins',{}))
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

def collect_videos(case,seed,render,update,*,label=None,arm_std=None,lr_mode=None):
    label=label or case
    check_time()
    """실제 렌더에 과제/목표/시계만 표시한다. 추정 접촉이나 가짜3D영역을 만들지 않는다."""
    video=STUDY/'동영상';video.mkdir(exist_ok=True)
    proof=STUDY/'검증/영상표시'/f'{label}_s{seed}';proof.mkdir(parents=True,exist_ok=True)
    subtitles,offset=phase_subtitles(render,proof)
    row=case_row(case);font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    header=proof/'header.txt';header.write_text(f'{label} | 손가락 초기std0.35 | 팔 초기std{arm_std} | LR {lr_mode} | 학습 {update}회 | seed {seed}')
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
        check_time()
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


def parent_terminal(document):
    return document.get('driver_pid') is None and (document.get('completed') is True or bool(document.get('failure')))


def wait_gpu(state,key,pins):
    while True:
        check_time();verify(pins)
        parent=read(PARENT/'진행상황.json') if (PARENT/'진행상황.json').is_file() else {}
        busy=occupied()
        if parent_terminal(parent) and not busy:return
        state.update(status='부모 종료/GPU 대기',current_task=key,parent_status=parent.get('status'),gpu_processes=busy,updated_at=stamp())
        save(STATE,state);time.sleep(min(10,max(1,remaining())))


def promising(result):
    return (result.get('denominator')==16 and min(result['clean_fraction_by_target'])>=.8 and
        result['safe_success']>=15 and result['wrong_target_time_ratio']<=.05 and result['physical']==0 and result['wrist']==0)


def select_parent(results):
    """최선 영상 모델이 아니라 네 조건의 같은400회 평가만 비교한다."""
    fallback=dict(label='C00',arm_std=.15,lr_mode='existing',fallback=True,reason='네 조건400회 비교 미완료 또는 유망한 평균 정책 우위 미입증')
    if set(results)!=set(CONFIG):return fallback
    eligible=[label for label,r in results.items() if promising(r)]
    if not eligible:return fallback
    best=max(eligible,key=lambda label:(results[label]['passed'],min(results[label]['clean_fraction_by_target']),
        results[label]['timing_pass'],-results[label]['wrong_target_time_ratio'],-CONFIG[label]['arm_std'],CONFIG[label]['lr_mode']=='existing'))
    return dict(label=best,**CONFIG[best],fallback=False,reason='같은400회 평균정책의 유망 기준 통과 조건 중 엄격통과·유지·시각·오압현·작은std·existing 순 선택')


def parent_checkpoint(path,label,expected_update):
    """과거 도구를 실행하지 않고 공식 입력검증과 원시 identity를 대조한다. 이식하지 않는다."""
    import torch
    from guitar_learning.portability import localize,validate_checkpoint_inputs,portable,PATH_SCHEMA,settings_digest
    torch.set_num_threads(1);payload=torch.load(path,map_location='cpu',weights_only=False)
    identity=payload.get('identity',{});meta=payload.get('metadata',{})
    if (identity.get('schema')!='guitar_learning.a0_exploration_lr_trainer.v1' or
            identity.get('architecture',{}).get('schema')!='guitar_learning.a0_exploration_lr_policy.v1' or
            identity['architecture'].get('state_dim')!=613 or meta.get('schema')!='guitar_learning.a0_exploration_lr_resume.v1' or
            payload.get('updates')!=expected_update):raise IntegrityError('부모 checkpoint schema/횟수 불일치')
    validate_checkpoint_inputs(meta);settings=localize(meta['settings']);config=settings['natural_press']
    ppo_config=dict(settings['ppo'])
    if ppo_config.get('advantage_normalization')=='joint':ppo_config.pop('advantage_normalization')
    contract=read(path.parent/'training_contract.json')
    if (identity.get('path_schema')!=PATH_SCHEMA or meta.get('settings_sha256')!=settings_digest(settings) or
            identity.get('config')!=ppo_config or identity['architecture'].get('complex_press')!=portable(config) or
            identity['architecture'].get('contract')!=portable(contract)):
        raise IntegrityError('부모 checkpoint 설정/architecture/입력 계약 identity 불일치')
    if (config.get('arm_initial_std')!=CONFIG[label]['arm_std'] or config.get('lr_mode')!=CONFIG[label]['lr_mode'] or
            config.get('geometry_sha256')!=sha(PARENT/'입력/A0/catalog.json') or config.get('lr_recovery_floor')!=1.5e-5):raise IntegrityError('부모 checkpoint 조건/입력 불일치')
    return dict(path=str(path),sha256=sha(path),updates=payload['updates'],identity=identity,
        scope='부모 모델은 비교 근거로만 읽고 새 정책에 로드하지 않음')



def validated_parent_evaluation(parent,label,update):
    entry=parent.get('cases',{}).get(label+'_s7',{}).get('evaluations',{}).get(str(update))
    task=parent.get('tasks',{}).get(label+f'_s7_eval{update}',{});training=parent.get('tasks',{}).get(label+'_s7_train400',{})
    if not entry or not task.get('completed') or not training.get('completed'):return None,{}
    for t in (training,task):verify(t['artifacts']);verify(t.get('dependency_pins',{}))
    checkpoint=Path(entry['checkpoint']).resolve();out=Path(entry['out']).resolve()
    checkpoint.relative_to(PARENT);out.relative_to(PARENT)
    if out!=Path(task['out']).resolve():raise IntegrityError('부모 평가 경로 불일치')
    validated_report(Path(training['out']),'train',updates=400);validated_report(out,'evaluate',checkpoint)
    model=parent_checkpoint(checkpoint,label,update);result=evaluation(out,'A0')
    if result!=entry.get('result'):raise IntegrityError('부모 평가 원문과 상태 집계 불일치')
    proof=merge_pins(training['artifacts'],task['artifacts'],{str(checkpoint):sha(checkpoint)})
    return dict(out=str(out),model=model,result=result),proof


def parent_evidence(state,pins):
    source=read(PARENT/'검증/실행봉인.json')
    if source.get('completed') is not True:raise IntegrityError('부모 실행 봉인 미완료')
    verify(source['pins']);parent=read(PARENT/'진행상황.json')
    if not parent_terminal(parent):raise RuntimeError('부모 종료 전 조건 선택 금지')
    results={};records={};proof_pins={str(PARENT/'검증/실행봉인.json'):sha(PARENT/'검증/실행봉인.json')}
    for label in CONFIG:
        record,proof=validated_parent_evaluation(parent,label,400)
        if record is None:continue
        results[label]=record['result'];records[label]=record;proof_pins=merge_pins(proof_pins,proof)
    selection=select_parent(results)
    state['parent_selection']=dict(**selection,comparison_update=400,complete_four_conditions=len(results)==4,
        parent_completed=parent.get('completed'),parent_terminal_failure=parent.get('failure'),evidence=records,
        parent_state_sha256=sha(PARENT/'진행상황.json'),source_pins_verified=True)
    state['parent_evidence_pins']=proof_pins;save(STATE,state)
    return selection,parent


def reference_pins(key,pins):
    marker=read(MARKER)
    if marker.get('schema')!='successor_simultaneous_reference_selection.v1' or marker.get('completed') is not True:
        raise IntegrityError('최종 후보 선택 marker 미완료')
    item=marker['cases'][key]
    if item.get('status')!='candidate_available':return None,dict(pins)
    path=Path(item['reference']).resolve();path.relative_to(STUDY);ref=read(path)
    if (sha(path)!=item['sha256'] or ref.get('case_id')!=item['case_id'] or ref.get('candidate_valid') is not True or
            ref.get('schema')!='guitar_learning.successor_simultaneous_reference.v1' or
            ref.get('catalog_sha256')!=sha(STUDY/'입력'/item['case_id']/'catalog.json')):raise IntegrityError('선택 후보의 SHA/과제 계약 불일치')
    more=merge_pins(pins,{str(MARKER):sha(MARKER),str(path):sha(path)},marker['source_sha256'],ref['source_sha256'])
    verify(more);return path,more


def native_result(out,case):
    report=read(out/'report.json');episode=read(out/'episode.json');d=read(out/'diagnostics.json')['summary']
    if d.get('episodes')!=1 or d.get('exact_hz')!=240:raise IntegrityError('native 평가 분모/240Hz 진단 불일치')
    targets=case_row(case)['compiled_targets'];fractions=[episode['left_note_ledger']['values']['clean'][i]/(t['end_s']-t['onset_s']) for i,t in enumerate(targets)]
    intervals=sorted((t['onset_s'],t['end_s']) for t in targets);end=-float('inf');union=0.
    for lo,hi in intervals:union+=max(0.,hi-max(lo,end));end=max(end,hi)
    if not 0<=d['wrong_press_active_union_s']<=union+1e-6:raise IntegrityError('native wrong union 범위 불일치')
    wrong=d['wrong_press_active_union_s']/union
    overlaps=any(a['onset_s']<b['end_s'] and b['onset_s']<a['end_s'] for i,a in enumerate(targets) for b in targets[i+1:])
    passed=bool(report.get('task_success') is True and report.get('native_reference_pass') is True and report.get('requested_path_rate_feasible') is True and safe(episode) and
        min(fractions)>=.9 and wrong<=.05 and d['timing_pass_episodes']==1 and (not overlaps or d['overlap_pass_episodes']==1))
    return dict(out=str(out),passed=passed,fractions=fractions,wrong_active_union_ratio=wrong,timing=d,
        requested_path_rate_feasible=report.get('requested_path_rate_feasible'),snapshot=str(out/'replay_snapshots.json'),
        scope='실제 원장·시각·rate 검사; 참조 실패를 물리 불가능으로 단정하지 않음')


def run_native(state,key,case,pins):
    reference,dependencies=reference_pins(key,pins)
    if reference is None:return dict(passed=False,status='참조 미확보')
    out=execute(state,key+'_native','replay',['--inputs',STUDY/'입력'/case,'--reference-json',reference],dependencies)
    result=native_result(out,case);result['task_key']=key+'_native';state.setdefault('native_candidates',{})[key]=result;save(STATE,state);write_summary(state)
    return result


def smoke(state,pins):
    if state.get('smoke_completed'):verify(state['smoke_artifacts']);return
    train=execute(state,'검증_train1','train',['--inputs',STUDY/'입력/A0','--arm-std',.20,'--lr-mode','recover_floor',
        '--updates',1,'--num-envs',8,'--size','large','--horizon',32,'--seed',7,'--checkpoint-every',1],pins,updates=1)
    resume=execute(state,'검증_resume1','train',['--resume',train/'J/final.pt','--updates',1,'--checkpoint-every',1],pins,updates=1)
    if read(resume/'J/report.json')['optimizer_updates']!=2:raise IntegrityError('엄격 재개 횟수 불일치')
    checkpoint=resume/'J/final.pt'
    evaluated=execute(state,'검증_eval2','evaluate',['--checkpoint',checkpoint,'--num-envs',2],pins,checkpoint=checkpoint)
    if read(evaluated/'diagnostics.json')['summary']['episodes']!=2:raise IntegrityError('연결검사 평가 분모 불일치')
    rendered=execute(state,'검증_render1','render',['--checkpoint',checkpoint,'--num-envs',1],pins,checkpoint=checkpoint)
    proof=STUDY/'검증/GPU연결검증.json';artifacts={**manifest(train),**manifest(resume),**manifest(evaluated),**manifest(rendered)}
    save(proof,dict(completed=True,artifacts=artifacts,source_pins=pins,scope='새 소스 GPU 연결 검사이며 정책 성능 인증 아님'))
    state.update(smoke_completed=True,smoke_artifacts={str(proof):sha(proof),**artifacts});save(STATE,state)


def budget_updates(seconds):
    return 200 if seconds>=30*60 else 100 if seconds>=18*60 else None


def run_learning(state,key,case,seed,config,updates,pins):
    c=state['cases'].setdefault(key,dict(evaluations={},input_case=case,arm_std=config['arm_std'],lr_mode=config['lr_mode'],seed=seed,planned_updates=updates))
    if c.get('finished'):
        for name,t in state['tasks'].items():
            if name.startswith(key+'_') and t.get('completed'):
                verify(t['artifacts']);verify(t.get('dependency_pins',{}));validated_report(Path(t['out']),t['action'],Path(t['checkpoint']) if t.get('checkpoint') else None,t.get('updates'))
        for p,item in c.get('videos',{}).items():verify({p:item['sha256']})
        return c
    if c['planned_updates']!=updates or c['arm_std']!=config['arm_std'] or c['lr_mode']!=config['lr_mode']:raise IntegrityError('재시작 조건/사전 예산 변경')
    check_time(training=True,reserve=(30 if updates==200 else 18)*60)
    train=execute(state,key+f'_train{updates}','train',['--inputs',STUDY/'입력'/case,'--arm-std',config['arm_std'],'--lr-mode',config['lr_mode'],
        '--updates',updates,'--num-envs',64,'--size','large','--horizon',32,'--seed',seed,'--checkpoint-every',100],pins,updates=updates)
    candidates=[]
    for update in ((100,200) if updates==200 else (100,)):
        checkpoint=train/'J'/('final.pt' if update==updates else 'checkpoint_000100.pt')
        out=execute(state,key+f'_eval{update}','evaluate',['--checkpoint',checkpoint,'--num-envs',16],pins,checkpoint=checkpoint)
        entry=dict(update=update,checkpoint=str(checkpoint),out=str(out),result=evaluation(out,case));c['evaluations'][str(update)]=entry;candidates.append(entry)
        save(STATE,state);write_summary(state)
    best=max(candidates,key=lambda e:select_score(e['result'],e['update']));c.update(selected=best,comparison=c['evaluations'][str(updates)],status='대표 영상 저장')
    rendered=execute(state,key+'_render_best','render',['--checkpoint',best['checkpoint'],'--num-envs',1],pins,checkpoint=Path(best['checkpoint']))
    c['videos']=collect_videos(case,seed,rendered,best['update'],label=key.rsplit('_s',1)[0],arm_std=config['arm_std'],lr_mode=config['lr_mode'])
    c.update(finished=True,status='엄격 통과' if c['comparison']['result']['passed'] else '과제 성능 미달');save(STATE,state);write_summary(state);return c



def confirm_a0(state,config,pins):
    """선택 조건의 재현 실행 실패도 원문을 보존하고 N01 기준 구성으로 분리한다."""
    fallback=dict(arm_std=.15,lr_mode='existing')
    try:
        native=run_native(state,'A0','A0',pins)
        if not native.get('passed'):
            state['reproduction_fallback']='새 source A0 native 기준 미달';return fallback
        reproduced=run_learning(state,'A0_confirm_s17','A0',17,config,200,pins)
        if not promising(reproduced['evaluations']['200']['result']):
            state['reproduction_fallback']='A0 seed17의200회 유망 기준 미달';return fallback
        return config
    except (DeadlineReached,IntegrityError,KeyboardInterrupt):raise
    except Exception as error:
        state['cases'].setdefault('A0_confirm_s17',dict(evaluations={},input_case='A0',seed=17,
            arm_std=config['arm_std'],lr_mode=config['lr_mode'])).update(status='재현 실행 오류로 보류',finished=True,passed=False,failure=repr(error))
        state['reproduction_fallback']='재현 실행 오류 두 attempt: N01은 기준 구성 사용';save(STATE,state);return fallback


def write_summary(state):
    lines=['# 후속 동시 압현 개선 연구','',f'갱신: {stamp()}','','부모는 공통400회로 선택하고 새 정책을 만든다. 대표 영상 best 모델과 비교 모델은 다를 수 있다.','',
        '| 조건 | 상태 | 팔std / LR | 비교 횟수 | 전체 달성 | 엄격 통과 |','|---|---|---|---:|---:|---|']
    for key,c in state.get('cases',{}).items():
        entry=c.get('comparison',{});r=entry.get('result',{})
        lines.append(f"| {key} | {c.get('status','대기')} | {c.get('arm_std','—')} / {c.get('lr_mode','—')} | {entry.get('update','—')} | {r.get('safe_success','—')}/16 | {r.get('passed','—')} |")
    (STUDY/'결과.md').write_text('\n'.join(lines)+'\n')
    if remaining()<=0:state['analysis_deferred']='시간 마감으로 기존 분석 보존';save(STATE,state);return
    script=SELF.parent/'analyze.py'
    if script.is_file():
        logdir=STUDY/'분석/작업로그';logdir.mkdir(parents=True,exist_ok=True);log=logdir/(str(time.time_ns())+'.log')
        try:
            with log.open('xb') as stream:subprocess.run(['/home/ajou/miniconda3/bin/python','-B',str(script)],cwd=ROOT,
                stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=max(1,min(120,remaining())))
        except Exception as error:state.setdefault('analysis_errors',[]).append(dict(log=str(log),failure=repr(error)));save(STATE,state)


def freeze():
    original=PARENT/'검증/실행봉인.json';parent=read(original)
    if parent.get('completed') is not True:raise IntegrityError('부모 source 봉인 없음')
    pins=merge_pins(parent['pins'],{str(original):sha(original)})
    for n in ('learning.py','test_learning.py','inputs.py','run_study.py','analyze.py'):pins=merge_pins(pins,{str(SELF.parent/n):sha(SELF.parent/n)})
    for n in ('학습기CPU검증.json','입력CPU검증.json','드라이버CPU검증.json','분석CPU검증.json','독립검수.md'):
        path=STUDY/'검증'/n
        if path.suffix=='.json' and read(path).get('completed') is not True:raise IntegrityError('CPU 검증 미완료')
        pins=merge_pins(pins,{str(path):sha(path)})
    marker=read(MARKER)
    if marker.get('completed') is not True:raise IntegrityError('참조 marker 미완료')
    pins=merge_pins(pins,{str(MARKER):sha(MARKER)},marker['source_sha256'])
    for folder in (STUDY/'입력',STUDY/'검증/참조'):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:pins=merge_pins(pins,{str(path):sha(path)})
    verify(pins);save(SEAL,dict(completed=True,schema='successor_simultaneous_seal.v1',pins=pins,deadline=DEADLINE.isoformat(),train_cutoff=TRAIN_CUTOFF.isoformat(),created_at=stamp()))
    print('새 후속 연구 봉인:',len(pins),'파일')


def finish_budget(state):
    for c in state['cases'].values():
        if not c.get('finished'):c.update(status='시간 예산 중단: 기존 평가/원문 보존',finished=True,passed=False)
    state['cases'].setdefault('N01_s7',dict(input_case='N01',finished=True,status='시간 예산 보류',passed=False,evaluations={}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:return self_test()
    if args.freeze:return freeze()
    seal=read(SEAL)
    if seal.get('completed') is not True:raise IntegrityError('봉인 미완료')
    pins=seal['pins'];verify(pins);lockpath=STUDY/'실행/driver.lock';lockpath.parent.mkdir(parents=True,exist_ok=True)
    lock=lockpath.open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=read(STATE) if STATE.exists() else dict(tasks={},cases={})
    if state.get('driver_pins') and state['driver_pins']!=pins:raise IntegrityError('기존 실행 source 변경')
    state.update(driver_pid=os.getpid(),driver_pins=pins,completed=False,failure=None,status='부모 종료 대기',currentcase=None)
    def interrupted(signum,frame):raise KeyboardInterrupt('중단 신호 '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
    try:
        wait_gpu(state,'부모 종료 대기',pins)
        if 'parent_selection' not in state:selection,parent=parent_evidence(state,pins)
        else:
            verify(state['parent_evidence_pins']);selection=state['parent_selection'];parent=read(PARENT/'진행상황.json')
        config=dict(arm_std=selection['arm_std'],lr_mode=selection['lr_mode']);smoke(state,pins)
        label=selection['label'];parent200=parent.get('cases',{}).get(label+'_s7',{}).get('evaluations',{}).get('200')
        if remaining()>=65*60 and parent200:
            record,proof=validated_parent_evaluation(parent,label,200)
            if record is None:raise IntegrityError('재현에 사용할 부모200회 검증 근거 누락')
            state['parent200_evidence']=record
            state['parent_evidence_pins']=merge_pins(state['parent_evidence_pins'],proof)
            save(STATE,state);metrics=record['result']
            if promising(metrics):
                state['currentcase']='A0_confirm_s17';save(STATE,state)
                config=confirm_a0(state,config,pins)
            else:state['reproduction_deferred']='선택 조건의 부모200회 평균 정책 유망 기준 미달'
        else:state['reproduction_deferred']='65분 예산 또는 부모200회 평가 근거 부족'
        state['N01_config']=config;state['currentcase']='N01_s7';save(STATE,state)
        improved=None
        for key in ('N01_G0','N01_G1','N01_G2'):
            try:result=run_native(state,key,'N01',pins)
            except (DeadlineReached,IntegrityError,KeyboardInterrupt):raise
            except Exception as error:
                state.setdefault('native_candidate_errors',{})[key]=repr(error);save(STATE,state);continue
            if key!='N01_G0' and result.get('passed'):improved=key;break
        if improved is None:state['cases']['N01_s7']=dict(input_case='N01',finished=True,status='개선 native 후보 미통과로 학습 보류',passed=False,evaluations={},arm_std=config['arm_std'],lr_mode=config['lr_mode'])
        else:
            updates=budget_updates(remaining())
            if updates is None:raise DeadlineReached('N01 학습/평가/영상18분 예산 미달')
            state['selected_native_candidate']=improved
            try:run_learning(state,'N01_s7','N01',7,config,updates,pins)
            except (DeadlineReached,IntegrityError,KeyboardInterrupt):raise
            except Exception as error:
                state['cases'].setdefault('N01_s7',dict(evaluations={},input_case='N01',seed=7,
                    arm_std=config['arm_std'],lr_mode=config['lr_mode'])).update(status='실행 오류 두 attempt로 보류',finished=True,passed=False,failure=repr(error))
                save(STATE,state)
        verify(pins);state.update(completed=True,status='완료',current_task=None,currentcase=None,finished_at=stamp())
    except DeadlineReached as error:
        finish_budget(state);state.update(completed=True,status='시간 예산 종료',failure=None,deadline_reason=str(error),currentcase=None,current_task=None)
    except BaseException as error:state.update(completed=False,status='중단 또는 봉인 오류',failure=repr(error));raise
    finally:
        state.update(driver_pid=None,child_pid=None,updated_at=stamp());save(STATE,state);write_summary(state);lock.close()


def self_test():
    from unittest.mock import patch
    assert budget_updates(30*60)==200 and budget_updates(18*60)==100 and budget_updates(18*60-1) is None
    assert parent_terminal(dict(completed=True,driver_pid=None)) and parent_terminal(dict(completed=False,driver_pid=None,failure='실패'))
    assert not parent_terminal(dict(completed=False,driver_pid=None)) and not parent_terminal(dict(completed=True,driver_pid=1))
    good=dict(denominator=16,safe_success=16,clean_fraction_by_target=[1.,1.],wrong_target_time_ratio=0.,physical=0,wrist=0,passed=True,timing_pass=16)
    bad=dict(good,safe_success=0,passed=False)
    results={label:dict(bad) for label in CONFIG};results['C00']=dict(good,passed=False)
    assert select_parent(results)['label']=='C00'
    results['C10']=dict(good);assert select_parent(results)['label']=='C10'
    del results['C01'];assert select_parent(results)['fallback']
    assert select_parent({})['label']=='C00'
    # best100을 섞지 않고400회 평가 전용 자료만 조건 선택에 전달한다.
    for now,training,reserve in [(TRAIN_CUTOFF,True,0),(DEADLINE,False,0),(DEADLINE,True,18*60)]:
        try:check_time(now=now,training=training,reserve=reserve)
        except DeadlineReached:pass
        else:raise AssertionError('시각 제한이 동작하지 않음')
    with tempfile.TemporaryDirectory() as name:
        p=Path(name)/'seal.json';save(p,dict(x=1));verify({str(p):sha(p)})
        try:merge_pins({'x':'1'},{'x':'2'})
        except IntegrityError:pass
        else:raise AssertionError('SHA 충돌 허용')
        with (Path(name)/'lock').open('a') as a,(Path(name)/'lock').open('a') as b:
            fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:raise AssertionError('중복 실행 허용')
        process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True);close_group(process);assert process.poll() is not None
        with patch.dict(globals(),STATE=Path(name)/'state.json',STUDY=Path(name),wait_gpu=lambda *a:None,check_time=lambda **k:None):
            state=dict(tasks={},driver_pins={})
            with patch.object(subprocess,'Popen',side_effect=OSError('검사 실패')) as popen:
                try:execute(state,'실패','train',[],{},updates=1)
                except RuntimeError:pass
                else:raise AssertionError('실패 성공 처리')
                assert popen.call_count==2 and len(state['tasks']['실패']['attempt_history'])==2
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder);render=root/'render';render.mkdir()
        for name in ('hand.mp4','fullbody.mp4'):(render/name).write_bytes(b'video')
        def encoded(args,**kwargs):Path(args[-1]).write_bytes(b'encoded')
        with patch.dict(globals(),STUDY=root,phase_subtitles=lambda *a:(root/'phases.ass',0.),
            case_row=lambda *a:dict(compiled_targets=[]),read_probe=lambda *a:dict(width=1280,height=720,nb_frames='150',r_frame_rate='30/1')):
            with patch.object(subprocess,'run',side_effect=encoded):
                for label in ('A0_confirm_s17','N01_s7'):
                    result=collect_videos('N01',7,render,100,label=label,arm_std=.2,lr_mode='recover_floor')
                    assert len(result)==2
                    assert 'recover_floor' in (root/'검증/영상표시'/f'{label}_s7/header.txt').read_text()
        state=dict(tasks={},cases={})
        with patch.dict(globals(),STATE=root/'state.json',run_native=lambda *a:dict(passed=True)):
            with patch.dict(globals(),run_learning=lambda *a:(_ for _ in ()).throw(RuntimeError('학습 두 번 실패'))):
                cfg=confirm_a0(state,dict(arm_std=.2,lr_mode='recover_floor'),{})
                assert cfg==dict(arm_std=.15,lr_mode='existing')
                assert state['cases']['A0_confirm_s17']['finished']
            with patch.dict(globals(),run_learning=lambda *a:dict(evaluations={'200':dict(result=bad)})):
                assert confirm_a0(state,dict(arm_std=.2,lr_mode='recover_floor'),{})['arm_std']==.15
        targets=[dict(onset_s=3.,end_s=4.5),dict(onset_s=3.,end_s=4.5)]
        e=dict(valid=True,song=dict(safety_invalidated=False,stage_success=True),termination=dict(physical_failure=False,wrist_failure=False),left_note_ledger=dict(values=dict(clean=[1.5,1.5])))
        d=dict(episodes=1,exact_hz=240,timing_pass_episodes=1,overlap_pass_episodes=1,wrong_press_active_union_s=.075)
        save(root/'episode.json',e);save(root/'report.json',dict(task_success=True,native_reference_pass=True,requested_path_rate_feasible=True));save(root/'diagnostics.json',dict(summary=d))
        with patch.dict(globals(),case_row=lambda *a:dict(compiled_targets=targets)):
            assert native_result(root,'N01')['passed']
            d['wrong_press_active_union_s']=.08;save(root/'diagnostics.json',dict(summary=d));assert not native_result(root,'N01')['passed']
    # 과거 도구 실행 없이 완료 원문 보고서와 현재 부모 checkpoint 입력만 읽어 검증한다.
    old=ROOT/'docs/2026-11-09/복합압현_야간확장_v1/실행/A0_arm015_s7_train100'
    validated_report(old,'train',updates=100)
    validated_report(old.parent/'A0_arm015_s7_eval100','evaluate',old/'J/final.pt')
    parent100=PARENT/'실행/C00_s7_train400/J/checkpoint_000100.pt'
    if parent100.is_file():parent_checkpoint(parent100,'C00',100)
    reference,dependencies=reference_pins('N01_G1',{});assert reference is not None;verify(dependencies)
    print('CPU 자체검사 통과: 부모선택·예산·SHA·잠금·재시도·정리')


if __name__=='__main__':main()
