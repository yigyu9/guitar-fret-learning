"""새 목표 전환의 검증·환경수 벤치·4시간 학습·평가를 순서대로 이어간다.

과거 실행기는 import하지 않는다. 동일한 SHA 검증·프로세스 정리·영상 표시 도우미를
필요한 범위에서 복사했으며 새 source/입력/모델을 엄격하게 구분한다.
"""
import argparse
import bisect
import gzip
from datetime import datetime,timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time

SELF=Path(__file__).resolve()
STUDY=SELF.parents[1]
ROOT=next(p for p in SELF.parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
PYTHON=Path('/home/ajou/miniconda3/envs/rl38/bin/python')
LEARNER=SELF.parent/'learning.py'
STATE=STUDY/'진행상황.json'
SEAL=STUDY/'검증/실행봉인.json'
MARKER=STUDY/'검증/참조/참조선택.json'
MAX_TRAIN_S=14400
MAX_TOTAL_S=25200
BENCH_UPDATES=20
ACTIVE={}
class BudgetReached(RuntimeError):pass
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


def remaining():return MAX_TOTAL_S-max(0.,time.time()-ACTIVE.get('run_started_unix',time.time()))

def check_time():
    if remaining()<=0:raise BudgetReached('전체7시간 안전 제한')

def finite(value):
    if isinstance(value,float) and not math.isfinite(value):raise ValueError('비유한 원문 수치')
    if isinstance(value,dict):
        for v in value.values():finite(v)
    if isinstance(value,list):
        for v in value:finite(v)


def validated_report(out,kind,checkpoint=None,updates=None):
    rp=out/('J/report.json' if kind=='train' else 'report.json');r=read(rp);finite(r)
    if not (r.get('completed') is True and r.get('failure') is None and r.get('lifecycle_verified') is True
            and r.get('changed_inputs')==[] and not r.get('missing_import_pins') and r.get('cleanup_errors')==[]):
        raise RuntimeError('미완료/입력변경/정리 실패: '+str(rp))
    if checkpoint is not None and r.get('checkpoint_sha256')!=sha(checkpoint):raise IntegrityError('checkpoint SHA 불일치')
    if kind=='train':
        outer=read(out/'report.json')
        if not (outer.get('completed') is True and outer.get('failure') is None and outer.get('final_phase')=='J'
                and len(outer.get('stages',[]))==1 and outer['stages'][0].get('report')==r):raise RuntimeError('학습 최상위 보고서 불일치')
        metrics=rows(out/'J/learning_metrics.jsonl');finite(metrics)
        if updates is not None and (len(metrics)!=updates or r['updates_in_run']!=updates):raise RuntimeError('요청 학습 횟수 미달')
        if not (out/'J/final.pt').is_file():raise RuntimeError('최종 모델 누락')
    elif kind=='render':
        if not (r.get('scene_closed') is True and r.get('source_pins_unchanged') is True and
                r.get('source_checkpoint_pins_validated') is True and r.get('encoding_exit_codes')=={'hand':0,'fullbody':0}):raise RuntimeError('영상 봉인/장면/인코딩 실패')
    return r


RESOURCE_WARNING=re.compile(r'PhysX.*(?:warning|error)|(?:buffer|capacity|found.lost|collisionStackSize).*(?:overflow|exceed|insufficient|increase)|(?:overflow|insufficient).*(?:buffer|capacity)|non.?finite|\bnan\b',re.I)

def check_log(path):
    warnings=[line.strip() for line in Path(path).read_text(errors='replace').splitlines() if RESOURCE_WARNING.search(line)]
    if warnings:raise RuntimeError('비유한/물리버퍼 경고: '+' | '.join(warnings[:4]))


def update_analysis(state):
    script=SELF.parent/'analyze.py'
    if not script.is_file():return
    logdir=STUDY/'분석/작업로그';logdir.mkdir(parents=True,exist_ok=True);log=logdir/(str(time.time_ns())+'.log')
    try:
        with log.open('xb') as stream:subprocess.run(['/home/ajou/miniconda3/bin/python','-B',str(script)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=max(1,min(120,remaining())))
    except Exception as error:state.setdefault('analysis_errors',[]).append(dict(log=str(log),failure=repr(error)));save(STATE,state)


def execute(state,key,action,args,pins,*,checkpoint=None,updates=None,main_training=False):
    """완료 원문 재사용은 SHA 확인 후만 허용하고 실행 오류는 새 위치에 한 번 재시도한다."""
    for flag in ('--checkpoint','--resume'):
        if flag in args:
            model=Path(args[args.index(flag)+1]).resolve();model.relative_to(ROOT)
            evidence={t['artifacts'][str(model)] for t in state['tasks'].values() if t.get('completed') and str(model) in t.get('artifacts',{})}
            if len(evidence)!=1:raise IntegrityError('모델의 완료 원문 SHA 근거 누락/충돌')
            expected=next(iter(evidence));verify({str(model):expected});pins=merge_pins(pins,{str(model):expected})
    item=state['tasks'].get(key)
    if item and item.get('completed'):
        verify(item['artifacts']);verify(item['dependency_pins']);out=Path(item['out']);validated_report(out,action,checkpoint,updates);check_log(item['log']);return out
    history=list(item.get('attempt_history',[])) if item else []
    if item and item.get('out') and not any(h.get('out')==item['out'] for h in history):history.append(dict(out=item['out'],failure='이전 프로세스 미완료'))
    while len(history)<2:
        check_time();verify(pins)
        if main_training and shutil.disk_usage(STUDY).free<4*1024**3:raise BudgetReached('학습 전 남은 저장공간4GiB 미달')
        while occupied():
            check_time();state.update(status='GPU 대기',current_task=key,updated_at=stamp());save(STATE,state);time.sleep(max(.1,min(5,remaining())))
        out,attempt=new_output(key);log=STUDY/'실행/작업로그'/(out.name+'.log');log.parent.mkdir(parents=True,exist_ok=True)
        entry=dict(completed=False,out=str(out),log=str(log),action=action,updates=updates,checkpoint=str(checkpoint) if checkpoint else None,
            attempt=attempt,attempt_history=history,dependency_pins={p:h for p,h in pins.items() if state['driver_pins'].get(p)!=h})
        state['tasks'][key]=entry;save(STATE,state);process=None;start=time.monotonic();train_before=state.get('training_wall_s',0.)
        allowance=7200
        try:
            cmd=command(action,out,*args);env=dict(os.environ,PYTHONPATH=str(ROOT),OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
            with log.open('xb') as stream:
                process=subprocess.Popen(cmd,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
                if main_training and not state['training_plan'].get('training_started_at'):
                    state['training_plan'].update(training_started_at=stamp(),actual_training_started_unix=time.time(),estimated_finish_at=datetime.fromtimestamp(time.time()+state['training_plan']['total_updates']*state['training_plan']['step_s'],timezone.utc).isoformat())
                state.update(status='실행 중',current_task=key,child_pid=process.pid,command=cmd,updated_at=stamp());save(STATE,state)
                while process.poll() is None:
                    check_time();elapsed=time.monotonic()-start
                    if main_training:state['training_wall_s']=train_before+elapsed
                    if elapsed>=allowance:raise TimeoutError(key+' 작업당2시간 제한')
                    state['updated_at']=stamp();save(STATE,state);time.sleep(min(5,max(.1,remaining())))
                if process.returncode:raise RuntimeError('종료 코드 '+str(process.returncode)+': '+str(log))
            verify(pins);check_log(log);validated_report(out,action,checkpoint,updates)
            entry.update(completed=True,artifacts=manifest(out),wall_s=time.monotonic()-start,finished_at=stamp());save(STATE,state);return out
        except (BudgetReached,IntegrityError,KeyboardInterrupt):raise
        except Exception as error:
            history.append(dict(out=str(out),log=str(log),failure=repr(error),wall_s=time.monotonic()-start));entry.update(attempt_history=history,failure=repr(error));save(STATE,state)
        finally:
            if process is not None:
                close_group(process)
                if main_training:state['training_wall_s']=train_before+time.monotonic()-start
            state.update(child_pid=None,updated_at=stamp());save(STATE,state);verify(pins)
    raise RuntimeError('실행 오류 두 번: '+key)


def train_args(num_envs,updates):
    return ['--inputs',STUDY/'입력/A0','--arm-std',.15,'--lr-mode','recover_floor','--updates',updates,'--num-envs',num_envs,'--size','large','--horizon',32,'--seed',7,'--checkpoint-every',50]


def smoke(state,pins):
    train=execute(state,'연결_train1','train',train_args(8,1),pins,updates=1)
    resumed=execute(state,'연결_resume1','train',['--resume',train/'J/final.pt','--updates',1],pins,updates=1)
    if read(resumed/'J/report.json')['optimizer_updates']!=2:raise IntegrityError('엄격 재개 누적 횟수 불일치')
    checkpoint=resumed/'J/final.pt';evaluated=execute(state,'연결_eval2','evaluate',['--checkpoint',checkpoint,'--num-envs',2],pins,checkpoint=checkpoint)
    if read(evaluated/'diagnostics.json')['summary']['episodes']!=2:raise IntegrityError('연결 평가 분모 불일치')
    execute(state,'연결_render1','render',['--checkpoint',checkpoint,'--num-envs',1],pins,checkpoint=checkpoint)
    state['smoke_completed']=True;save(STATE,state);update_analysis(state)


def native_result(out):
    r=read(out/'report.json');e=read(out/'episode.json');d=read(out/'diagnostics.json')['summary'];targets=case_row('A0')['compiled_targets']
    fractions=[e['left_note_ledger']['values']['clean'][i]/(t['end_s']-t['onset_s']) for i,t in enumerate(targets)]
    union=sum(t['end_s']-t['onset_s'] for t in targets);wrong=d['wrong_press_active_union_s']/union
    if d['episodes']!=1 or d['exact_hz']!=240 or not 0<=wrong<=1+1e-6:raise IntegrityError('참조 진단 분모/시간 오류')
    passed=bool(r.get('task_success') and r.get('native_reference_pass') and r.get('requested_path_rate_feasible') and safe(e)
        and min(fractions)>=.9 and wrong<=.05 and d['timing_pass_episodes']==1 and d['terminal_release_pass_episodes']==1)
    return dict(out=str(out),passed=passed,clean_fraction_by_target=fractions,wrong_active_union_ratio=wrong,timing=d,requested_path_rate_feasible=r.get('requested_path_rate_feasible'))


def native(state,pins):
    marker=read(MARKER);verify(marker['source_sha256']);item=marker['cases']['A0'];path=Path(item['reference'])
    verify({str(path):item['sha256']});out=execute(state,'참조_native','replay',['--inputs',STUDY/'입력/A0','--reference-json',path],pins)
    result=native_result(out);state['native_validation']=result;save(STATE,state);update_analysis(state)
    if not result['passed']:raise RuntimeError('새 native 참조 기준 미달로 학습 시작하지 않음')


def benchmark_result(out,num_envs):
    r=validated_report(out,'train',updates=BENCH_UPDATES);metrics=rows(out/'J/learning_metrics.jsonl');steady=metrics[3:]
    if len(steady)!=BENCH_UPDATES-3:raise IntegrityError('벤치 안정구간 개수 불일치')
    if any(m['transitions']!=num_envs*32 for m in metrics) or r['transitions']!=BENCH_UPDATES*num_envs*32:raise IntegrityError('벤치 수집량 불일치')
    collection=sum(m['collection_s'] for m in steady)/len(steady);update=sum(m['update_s'] for m in steady)/len(steady);step=collection+update
    if not math.isfinite(step) or step<=0:raise IntegrityError('벤치 시간 오류')
    episodes=[r['episode'] for r in rows(out/'J/episodes.jsonl')];seen={e['env_id'] for e in episodes}
    reset_seen=set(range(num_envs))<=seen;memory=r['min_cuda_free_bytes'];eligible=memory>=1.5*1024**3 and reset_seen
    return dict(out=str(out),eligible=eligible,tps=num_envs*32/step,step_s=step,collection_s=collection,update_s=update,min_cuda_free_bytes=memory,
        measurement_updates=len(steady),warmup_updates=3,total_updates=BENCH_UPDATES,environment_reset_boundary_seen=reset_seen,observed_env_count=len(seen),
        task_success_episodes=sum(safe(e) and e['song']['stage_success'] for e in episodes),completed_episode_count=len(episodes),
        eligibility_scope='자원·유한수치·20회완료·각환경종료경계 검사. 짧은 학습의 성공률은 환경 선택 기준이 아님')


def select_environment(results):
    choices=[(int(n),r) for n,r in results.items() if r.get('eligible')]
    if not choices:raise RuntimeError('안전한 환경수 벤치 결과 없음')
    peak=max(r['tps'] for _,r in choices)
    return max((n,r) for n,r in choices if r['tps']>=.95*peak)[0]


def make_plan(num_envs,step_s):
    total=max(100,min(8000,int(MAX_TRAIN_S/step_s)//50*50));chunk=max(50,int(2100/step_s)//50*50);chunk=min(chunk,total)
    return dict(num_envs=num_envs,total_updates=total,chunk_updates=chunk,step_s=step_s,horizon=32,seed=7,size='large',finger_std=.35,arm_std=.15,lr_mode='recover_floor',
        planned_transitions=total*num_envs*32,training_started_at=None,estimated_finish_at=None,target_training_s=MAX_TRAIN_S,training_budget_scope='4시간 soft 목표; 완료 chunk 경계에서 다음 학습을 결정, 전체7시간 hard 제한')


def benchmarks(state,pins):
    for n in (256,512,1024):
        if str(n) in state['benchmark']:continue
        try:
            out=execute(state,'벤치_'+str(n),'train',train_args(n,BENCH_UPDATES),pins,updates=BENCH_UPDATES);result=benchmark_result(out,n)
        except (BudgetReached,IntegrityError,KeyboardInterrupt):raise
        except Exception as error:result=dict(eligible=False,failure=repr(error),scope='실행/자원 실패. 과제 성공 실패와 구분하며 원문은 tasks에 보존')
        state['benchmark'][str(n)]=result;save(STATE,state);update_analysis(state)
    if not any(r.get('eligible') for r in state['benchmark'].values()):
        n=128
        if str(n) not in state['benchmark']:
            try:
                out=execute(state,'벤치_128_fallback','train',train_args(n,BENCH_UPDATES),pins,updates=BENCH_UPDATES);result=benchmark_result(out,n)
            except (BudgetReached,IntegrityError,KeyboardInterrupt):raise
            except Exception as error:result=dict(eligible=False,failure=repr(error),scope='128 fallback 실행/자원 실패')
            state['benchmark'][str(n)]=result;save(STATE,state);update_analysis(state)
    chosen=select_environment(state['benchmark']);state['training_plan']=make_plan(chosen,state['benchmark'][str(chosen)]['step_s']);save(STATE,state)


def evaluate_model(state,key,checkpoint,update,pins,*,stochastic=False,num_envs=16):
    mode='stochastic' if stochastic else 'mean';args=['--checkpoint',checkpoint,'--num-envs',num_envs,'--evaluation-seed',17]
    if stochastic:args.append('--stochastic')
    out=execute(state,key,'evaluate',args,pins,checkpoint=checkpoint);result=evaluation(out,'A0',num_envs)
    mode_info=read(out/'evaluation_mode.json')
    if mode_info['mode']!=mode or mode_info['seed']!=17 or mode_info['checkpoint_sha256']!=sha(checkpoint):raise IntegrityError('평가 방식/seed/모델 SHA 불일치')
    entry=dict(mode=mode,update=update,checkpoint=str(checkpoint),out=str(out),result=result,num_envs=num_envs,evaluation_seed=17)
    if not any(e['out']==entry['out'] for e in state['evaluations']):state['evaluations'].append(entry)
    save(STATE,state);update_analysis(state);return entry


def learning(state,pins):
    plan=state['training_plan'];committed=sum(s['updates_in_run'] for s in state['training_segments']);checkpoint=Path(state['training_segments'][-1]['checkpoint']) if committed else None
    # 학습 저장 뒤 평가 전에 중단되어도 해당 chunk 평가부터 완료한다.
    for segment in state['training_segments']:
        count=segment['cumulative_updates']
        evaluate_model(state,f'평균_u{count:06d}',Path(segment['checkpoint']),count,pins)
    while committed<plan['total_updates']:
        pending=state.get('pending_chunk')
        already_saved=bool(pending and state['tasks'].get(pending['task'],{}).get('completed'))
        if already_saved:
            updates=pending['updates'];key=pending['task']
            if pending['start_update']!=committed:raise IntegrityError('미반영 완료chunk 시작점 불일치')
        else:
            available=min(MAX_TRAIN_S-state.get('training_wall_s',0.),remaining()-1800)
            fitting=int(max(0.,available)/plan['step_s'])//50*50
            if fitting<50:raise BudgetReached('완료chunk 경계에서 4시간 학습 목표/최종평가 여유를 보존')
            if pending:
                updates=pending['updates'];key=pending['task']
                if pending['start_update']!=committed or updates>fitting:raise BudgetReached('미완료chunk 재시도에 필요한 예산 부족; 이전 완료 모델 보존')
            else:
                updates=min(plan['chunk_updates'],plan['total_updates']-committed,fitting);key=f'학습_u{committed+updates:06d}'
                state['pending_chunk']=dict(task=key,updates=updates,start_update=committed);save(STATE,state)
        args=['--resume',checkpoint,'--updates',updates,'--checkpoint-every',50] if checkpoint else train_args(plan['num_envs'],updates)
        out=execute(state,key,'train',args,pins,updates=updates,main_training=True);r=read(out/'J/report.json');metrics=rows(out/'J/learning_metrics.jsonl')
        expected=(committed+updates)*plan['num_envs']*32
        if r['optimizer_updates']!=committed+updates or r['transitions']!=updates*plan['num_envs']*32 or any(m['transitions']!=plan['num_envs']*32 for m in metrics):raise IntegrityError('주 학습 누적update/수집량 불일치')
        if sum(r['exposure_transitions'].values())!=expected:raise IntegrityError('주 학습 누적노출 수 불일치')
        committed+=updates;checkpoint=out/'J/final.pt'
        state['training_segments'].append(dict(task=key,out=str(out),checkpoint=str(checkpoint),updates_in_run=updates,cumulative_updates=committed,transitions=r['transitions'],cumulative_transitions=expected))
        state.pop('pending_chunk',None)
        plan.update(committed_updates=committed,committed_transitions=expected,estimated_remaining_training_s=(plan['total_updates']-committed)*plan['step_s'])
        save(STATE,state);evaluate_model(state,f'평균_u{committed:06d}',checkpoint,committed,pins)
    state['training_complete']=True;save(STATE,state)


def finalize(state,pins):
    if not state['training_segments']:return
    last=state['training_segments'][-1];checkpoint=Path(last['checkpoint']);update=last['cumulative_updates']
    evaluate_model(state,'최종_mean',checkpoint,update,pins)
    evaluate_model(state,'최종_stochastic',checkpoint,update,pins,stochastic=True,num_envs=64)
    mean=[e for e in state['evaluations'] if e['mode']=='mean'];best=max(mean,key=lambda e:select_score(e['result'],e['update']));state['selected']=best
    # 최선 평균정책과 최종모델이 다를 때만 한 쌍 더 남긴다.
    candidates=[('best',best['checkpoint'],best['update'])]
    if Path(best['checkpoint'])!=checkpoint:candidates.append(('final',str(checkpoint),update))
    for label,path,count in candidates:
        out=execute(state,'영상_'+label,'render',['--checkpoint',path,'--num-envs',1],pins,checkpoint=Path(path))
        state['videos'].update(collect_videos('A0',7,out,count,label=label,arm_std=.15,lr_mode='recover_floor'));save(STATE,state)
    update_analysis(state)


def freeze():
    required=('입력CPU검증.json','학습기CPU검증.json','드라이버CPU검증.json','분석CPU검증.json')
    pins={}
    for name in required:
        p=STUDY/'검증'/name
        if read(p).get('completed') is not True:raise IntegrityError('CPU검증 미완료: '+name)
        pins[str(p)]=sha(p)
    review=STUDY/'검증/독립검수.md';pins[str(review)]=sha(review)
    marker=read(MARKER)
    if not marker['completed']:raise IntegrityError('참조 선택 미완료')
    if read(STUDY/'검증/드라이버CPU검증.json').get('driver_sha256')!=sha(SELF):raise IntegrityError('드라이버CPU검사 이후 source 변경')
    pins=merge_pins(pins,marker['source_sha256'],{str(MARKER):sha(MARKER)})
    for directory in (ROOT/'guitar_learning',ROOT/'scripts',SELF.parent):
        for p in sorted(directory.rglob('*.py')):
            if '__pycache__' not in p.parts:pins=merge_pins(pins,{str(p):sha(p)})
    for p in (STUDY/'입력').rglob('*'):
        if p.is_file():pins=merge_pins(pins,{str(p):sha(p)})
    verify(pins);save(SEAL,dict(completed=True,schema='middle_s3f5_s4f8_driver_seal.v1',pins=pins,target_train_s=MAX_TRAIN_S,train_budget_scope='soft at chunk boundary',max_total_s=MAX_TOTAL_S,created_at=stamp()))
    print('새 연구 source/입력 봉인:',len(pins),'개')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--freeze',action='store_true');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.self_test:return self_test()
    if args.freeze:return freeze()
    seal=read(SEAL)
    if seal.get('completed') is not True:raise IntegrityError('실행 봉인 미완료')
    pins=seal['pins'];verify(pins);lockpath=STUDY/'실행/driver.lock';lockpath.parent.mkdir(parents=True,exist_ok=True);lock=lockpath.open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    state=read(STATE) if STATE.is_file() else dict(tasks={},benchmark={},training_segments=[],evaluations=[],videos={},run_started_unix=time.time(),started_at=stamp())
    if state.get('driver_pins') and state['driver_pins']!=pins:raise IntegrityError('재시작 source 봉인 변경')
    ACTIVE.update(state);ACTIVE['run_started_unix']=state['run_started_unix']
    for task in state['tasks'].values():
        if task.get('completed'):
            verify(task['artifacts']);verify(task['dependency_pins']);validated_report(Path(task['out']),task['action'],Path(task['checkpoint']) if task.get('checkpoint') else None,task.get('updates'));check_log(task['log'])
    state.update(driver_pins=pins,driver_pid=os.getpid(),completed=False,failure=None)
    def interrupt(signum,frame):raise KeyboardInterrupt('중단 신호 '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupt)
    try:
        smoke(state,pins);native(state,pins)
        if 'training_plan' not in state:benchmarks(state,pins)
        learning(state,pins);finalize(state,pins);verify(pins);state.update(completed=True,status='완료',finished_at=stamp())
    except BudgetReached as error:
        plan=state.get('training_plan',{});committed=sum(s['updates_in_run'] for s in state['training_segments'])
        state.update(budget_reason=str(error),status='시간 예산 종료',budget_stop=dict(reason=str(error),planned_updates=plan.get('total_updates'),completed_updates=committed,remaining_planned_updates=max(0,plan.get('total_updates',0)-committed),actual_training_wall_s=state.get('training_wall_s',0.)))
        save(STATE,state)
        try:
            if remaining()>1200:finalize(state,pins)
        except BaseException as final_error:
            state.update(completed=False,failure=repr(final_error),status='예산 종료 후 평가/영상 실패');raise
        else:state.update(completed=True,finished_at=stamp())
    except BaseException as error:state.update(completed=False,status='중단/검증 실패',failure=repr(error));raise
    finally:
        state.update(driver_pid=None,child_pid=None,current_task=None,updated_at=stamp());save(STATE,state);update_analysis(state);lock.close()


def select_score(result,update):
    return (result['passed'],result['safe_success'],min(result['clean_fraction_by_target']),result['timing_pass'],-result['wrong_target_time_ratio'],update)


def self_test():
    from unittest.mock import patch
    checks=[]
    assert make_plan(256,10.)['total_updates']==1400 and make_plan(256,10.)['chunk_updates']==200
    assert make_plan(1024,1.)['total_updates']==8000 and make_plan(128,1000.)['total_updates']==100
    assert select_environment({'256':dict(eligible=True,tps=100),'512':dict(eligible=True,tps=104),'1024':dict(eligible=True,tps=100)})==1024
    assert select_environment({'256':dict(eligible=True,tps=100),'1024':dict(eligible=False,tps=1000)})==256
    checks.append('20회벤치·3회제외·5%처리량 선택·50배수 예산 경계')
    with tempfile.TemporaryDirectory() as name:
        root=Path(name);save(root/'seal.json',dict(x=1));verify({str(root/'seal.json'):sha(root/'seal.json')})
        try:merge_pins({'x':'1'},{'x':'2'})
        except IntegrityError:pass
        else:raise AssertionError('SHA 충돌 허용')
        save(root/'seal.json',dict(x=2))
        try:verify({str(root/'seal.json'):'0'*64})
        except IntegrityError:pass
        else:raise AssertionError('입력 SHA 변경 허용')
        for bad in (float('nan'),float('inf')):
            try:finite(dict(value=[bad]))
            except ValueError:pass
            else:raise AssertionError('비유한 수치 허용')
        for text in ('PhysX warning: contact buffer overflow','found_lost capacity exceeded','non-finite actor'):
            (root/'log').write_text(text)
            try:check_log(root/'log')
            except RuntimeError:pass
            else:raise AssertionError('물리버퍼 경고 누락')
        checks.append('출처/SHA 충돌·변조·비유한·PhysX 버퍼 경고 거부')
        with (root/'lock').open('a') as a,(root/'lock').open('a') as b:
            fcntl.flock(a,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:fcntl.flock(b,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:raise AssertionError('중복 실행 허용')
        process=subprocess.Popen([sys.executable,'-c','import time;time.sleep(10)'],start_new_session=True);close_group(process);assert process.poll() is not None
        with patch.dict(globals(),STATE=root/'state.json',STUDY=root,occupied=lambda:[],check_time=lambda:None):
            state=dict(tasks={},driver_pins={})
            with patch.object(subprocess,'Popen',side_effect=OSError('자체검사 실패')) as popen:
                try:execute(state,'실패','train',[],{},updates=1)
                except RuntimeError:pass
                else:raise AssertionError('실패 성공 처리')
                assert popen.call_count==2 and len(state['tasks']['실패']['attempt_history'])==2
        checks.append('flock·프로세스그룹 정리·실패 원문 분리·한 번 재시도')
        episode=dict(valid=True,song=dict(safety_invalidated=False),termination=dict(physical_failure=False,wrist_failure=False),left_note_ledger=dict(values=dict(clean=[1.5,1.5])))
        diagnostic=dict(episodes=1,exact_hz=240,timing_pass_episodes=1,terminal_release_pass_episodes=1,wrong_press_active_union_s=.15)
        save(root/'episode.json',episode);save(root/'diagnostics.json',dict(summary=diagnostic));save(root/'report.json',dict(task_success=True,native_reference_pass=True,requested_path_rate_feasible=True))
        targets=[dict(finger=2,string=2,fret=5,onset_s=3.,end_s=4.5),dict(finger=2,string=3,fret=8,onset_s=5.5,end_s=7.)]
        with patch.dict(globals(),case_row=lambda *a:dict(compiled_targets=targets)):
            assert native_result(root)['passed'];diagnostic['wrong_press_active_union_s']=.16;save(root/'diagnostics.json',dict(summary=diagnostic));assert not native_result(root)['passed']
            diagnostic['wrong_press_active_union_s']=0.;diagnostic['timing_pass_episodes']=0;save(root/'diagnostics.json',dict(summary=diagnostic));assert not native_result(root)['passed']
        checks.append('native 두음clean90%·wrong5%·전체안전·strict timing·rate gate')
        (root/'J').mkdir();ms=[dict(transitions=256*32,collection_s=2.,update_s=1.) for _ in range(20)]
        (root/'J/learning_metrics.jsonl').write_text(''.join(json.dumps(m)+'\n' for m in ms))
        eps=[dict(episode=dict(env_id=i,valid=True,song=dict(safety_invalidated=False,stage_success=False),termination=dict(physical_failure=False,wrist_failure=False))) for i in range(256)]
        (root/'J/episodes.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in eps))
        with patch.dict(globals(),validated_report=lambda *a,**k:dict(transitions=20*256*32,min_cuda_free_bytes=2*1024**3)):
            result=benchmark_result(root,256);assert result['eligible'] and result['measurement_updates']==17 and result['task_success_episodes']==0
        with patch.dict(globals(),validated_report=lambda *a,**k:dict(transitions=20*256*32,min_cuda_free_bytes=1024**3)):
            assert not benchmark_result(root,256)['eligible']
        checks.append('벤치 수집량·全환경 종료경계·1.5GiB 여유·과제성과와자원 분리')
        with patch.dict(globals(),ACTIVE=dict(run_started_unix=time.time()-MAX_TOTAL_S-1)):
            try:check_time()
            except BudgetReached:pass
            else:raise AssertionError('전체7시간 제한 누락')
        render=root/'render';render.mkdir()
        for name in ('hand.mp4','fullbody.mp4'):(render/name).write_bytes(b'video')
        def encoded(args,**kwargs):Path(args[-1]).write_bytes(b'encoded')
        with patch.dict(globals(),STUDY=root,phase_subtitles=lambda *a:(root/'phases.ass',0.),case_row=lambda *a:dict(compiled_targets=targets),read_probe=lambda *a:dict(width=1280,height=720,nb_frames='225',r_frame_rate='30/1')):
            with patch.object(subprocess,'run',side_effect=encoded):
                videos=collect_videos('A0',7,render,200,label='best',arm_std=.15,lr_mode='recover_floor');assert len(videos)==2
                text=(root/'검증/영상표시/best_s7/header.txt').read_text();assert 'best' in text and 'recover_floor' in text
        checks.append('상대시간7시간cap·대표영상동적label/LR/목표시각 표시')
    with tempfile.TemporaryDirectory() as name:
        root=Path(name);out=root/'saved';(out/'J').mkdir(parents=True)
        save(out/'J/report.json',dict(optimizer_updates=50,transitions=3200,exposure_transitions=dict(full_song=3200)))
        (out/'J/learning_metrics.jsonl').write_text(''.join(json.dumps(dict(transitions=64))+'\n' for _ in range(50)))
        plan=dict(num_envs=2,total_updates=50,chunk_updates=50,step_s=10.)
        state=dict(training_plan=plan,training_segments=[],training_wall_s=MAX_TRAIN_S+1,evaluations=[],pending_chunk=dict(task='학습_u000050',updates=50,start_update=0),tasks={'학습_u000050':dict(completed=True)})
        evaluated=[]
        with patch.dict(globals(),STATE=root/'state.json',execute=lambda *a,**k:out,evaluate_model=lambda *a,**k:evaluated.append(a[3])):
            learning(state,{})
        assert state['training_complete'] and 'pending_chunk' not in state and state['training_segments'][0]['cumulative_updates']==50 and evaluated==[50]
        # 이전 완료 모델의 SHA가 달라지면 현재 파일을 새 기준으로 받아들이지 않는다.
        model=root/'model.pt';model.write_bytes(b'changed')
        state=dict(tasks={'train':dict(completed=True,artifacts={str(model):'0'*64})})
        with patch.dict(globals(),ROOT=root):
            try:execute(state,'resume','train',['--resume',model],{})
            except IntegrityError:pass
            else:raise AssertionError('이전 모델 SHA 변경 허용')
    checks.append('저장직후 중단chunk복구·재개모델 이전완료SHA 검증')
    proof=dict(completed=True,schema='middle_s3f5_s4f8_driver_cpu.v1',checks=checks,driver_sha256=sha(SELF),benchmark_updates=BENCH_UPDATES,warmup_updates=3,max_train_s=MAX_TRAIN_S,max_total_s=MAX_TOTAL_S,gpu_executed=False)
    save(STUDY/'검증/드라이버CPU검증.json',proof);print('CPU 자체검사 통과:',len(checks),'묶음')


if __name__=='__main__':main()
