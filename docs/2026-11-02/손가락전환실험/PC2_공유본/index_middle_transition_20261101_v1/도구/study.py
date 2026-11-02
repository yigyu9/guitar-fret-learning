"""Sequential immutable-source AB20 training/evaluation; no parallel GPU jobs."""
if not __debug__:raise RuntimeError('Scientific checks require Python optimization disabled')

from pathlib import Path
import argparse,json,os,sys,time,hashlib,subprocess,datetime,fcntl,traceback,signal
D=Path(__file__).resolve().parents[1];R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R));sys.path.insert(0,str(D/'도구'))
from analyze import analyze
KST=datetime.timezone(datetime.timedelta(hours=9));now=lambda:datetime.datetime.now(KST).isoformat(timespec='seconds')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 q=p.with_name(p.name+'.tmp');q.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False));q.replace(p)
def paths():
 found={R/'scripts/tab2body.py'}
 for folder in (R/'guitar_learning',R/'isaacgym/python/isaacgym',R/'data/song_bundles',D/'도구',D/'진단/geometry',D/'진단/reference_v1'):
  for p in folder.rglob('*'):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':found.add(p)
 found.update((D/'문서/PLAN.md',D/'진단/native_reference_v2/report.json',D/'진단/reference_initial_clear.json',D/'진단/preflight_passed.json'))
 return sorted(found)
def verify(seal):
 current={str(p.relative_to(R)) for p in paths()};assert current==set(seal),'source/input file set changed'
 bad=[n for n,h in seal.items() if sha(R/n)!=h];assert not bad,'sealed source/input SHA changed: '+str(bad[:8])
def publish(state):
 state['updated_at']=now();write(D/'status.json',state)
 done=sum(x.get('train_updates_in_run',0) for x in state['results'] if x['profile']==state.get('profile'));remaining=max(0,600-done)*state.get('seconds_per_update',6)+max(0,12-sum(x['profile']==state.get('profile') for x in state['results']))*80+300
 eta=(datetime.datetime.now(KST)+datetime.timedelta(seconds=remaining)).isoformat(timespec='minutes')
 (D/'PROGRESS.md').write_text('# 검지→중지 전환 연구 진행\n\n갱신: '+state['updated_at']+'\n현재: '+state.get('stage','')+' / '+state.get('job','')+'\n예상 기준군 종료: '+eta+' (후속조건·검수·영상은별도)\n\nlarge64/H32, 두seed각100→200→300회. 전이수/optimizer횟수·실패를각run에기록. '+state.get('error','')+'\n')
 lines=['# 검지→중지 전환 결과','','평균(mean)과 탐색(sampled)은 분리. 최초32환경별 첫episode, 실패포함. 아래는 새20축 정책의 성과이며 참조각 재생과 구분한다.','','|프로파일|seed|누적update|실행|AB/32|A/B clean초|A/B 달성|정시+이전끝/32|해제/32|실패/32|','|---|---:|---:|---|---:|---|---|---:|---:|---:|']
 for x in state['results']:
  m=x['metrics'];n=m['episodes'];a,b=m['notes'];lines.append(f"|{x['profile']}|{x['seed']}|{x['updates']}|{x['mode']}|{m['AB_achievement_count']}/{n}|{a['mean_clean_s']:.3f}/{b['mean_clean_s']:.3f}|{a['achievement']}/{b['achievement']}|{m['on_time_with_previous_tail_count']}/{n}|{m['release_by_B_onset_count']}/{n}|{m['any_failures']}/{n}|")
 lines+=['','安定성/자연스러움/일반화는 별도 검증 대상. 힘은 제출effort와native합력을구분하고몸체쌍압력으로단정하지않는다. 근접샘플은손가락충돌proxy로만사용.']
 (D/'RESULTS.md').write_text('\n'.join(lines))
 if state['results']:
  import matplotlib
  matplotlib.use('Agg')
  import matplotlib.pyplot as plt
  labels=[f"{x['profile']} s{x['seed']} {x['updates']} {x['mode']}" for x in state['results']];fig,ax=plt.subplots(3,1,figsize=(max(9,len(labels)*.65),8),sharex=True);xx=range(len(labels));ax[0].bar(xx,[x['metrics']['AB_achievement_count']/x['metrics']['episodes'] for x in state['results']]);ax[0].set_ylabel('AB achieved fraction');ax[1].plot(list(xx),[x['metrics']['notes'][0]['mean_clean_s']/1.5 for x in state['results']],label='Index A');ax[1].plot(list(xx),[x['metrics']['notes'][1]['mean_clean_s']/1.5 for x in state['results']],label='Middle B');ax[1].set_ylabel('Mean clean / 1.5s');ax[1].legend();ax[2].bar(xx,[x['metrics']['any_failures'] for x in state['results']]);ax[2].set_ylabel('Early failures');ax[2].set_xticks(list(xx));ax[2].set_xticklabels(labels,rotation=60,ha='right');fig.tight_layout();fig.savefig(D/'진단/comparison.png',dpi=140);plt.close(fig)
def read_complete_rows(path):
 return [json.loads(line) for line in path.read_text().splitlines(keepends=True) if line.endswith('\n') and line.strip()]
def stage(state,seal,label,args,out):
 verify(seal);assert not out.exists(),'output exists: '+str(out);state.update(stage='running',job=label,stage_started_at=now(),out=str(out));publish(state)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MAX_JOBS='2',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');env.pop('PYTHONUTF8',None);env.pop('PYTHONOPTIMIZE',None)
 cmd=[sys.executable,str(R/'scripts/tab2body.py'),'--cache-root','/home/yigyu/.cache/tab2body','run','-u',str(D/'도구/runtime.py')]+args+['--out',str(out)]
 with (D/'로그'/f'{label}.log').open('w') as log:
  child=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);start=time.monotonic()
  try:
   while child.poll() is None:
    if time.monotonic()-start>7200:raise RuntimeError('stage timeout '+label)
    state.update(elapsed_stage_s=time.monotonic()-start)
    metrics=out/'J/learning_metrics.jsonl'
    if metrics.exists():
     rows=read_complete_rows(metrics);state['current_updates']=len(rows)
     if rows:state['seconds_per_update']=sum(x['collection_s']+x['update_s'] for x in rows[-10:])/len(rows[-10:])
    publish(state);time.sleep(15)
  finally:
   if child.poll() is None:
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:child.wait(timeout=10)
    except subprocess.TimeoutExpired:
     try:os.killpg(child.pid,signal.SIGKILL)
     except ProcessLookupError:pass
     child.wait(timeout=10)
   else:child.wait()
  assert child.returncode==0,'child failed '+label+'; see log'
 verify(seal);report=json.loads((out/'report.json').read_text());assert report['completed'] and not report.get('failure'),label+' incomplete'
 return report

def prerequisites():
 proof=json.loads((D/'진단/preflight_passed.json').read_text())
 if proof.get('passed') is not True or not all(proof.get('exact_restore',{}).values()):raise RuntimeError('preflight required')
 for folder,h in proof['reports'].items():
  if sha(D/'진단'/folder/'report.json')!=h:raise RuntimeError('preflight report changed: '+folder)
 if json.loads((D/'진단/native_reference_v2/report.json').read_text()).get('passed') is not True:raise RuntimeError('strict feasibility required')
def main():
 def interrupted(signum,frame):raise KeyboardInterrupt('study interrupted by signal '+str(signum))
 signal.signal(signal.SIGTERM,interrupted);signal.signal(signal.SIGINT,interrupted)
 p=argparse.ArgumentParser();p.add_argument('--profile',choices=('base','narrow','broad'),required=True);p.add_argument('--seal',action='store_true');a=p.parse_args();lock=(D/'study.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 prerequisites()
 manifest=D/'보존/study_seal.json'
 if a.seal:
  assert not manifest.exists();pins={str(p.relative_to(R)):sha(p) for p in paths()};write(manifest,dict(created_at=now(),files=pins,sha256=hashlib.sha256(json.dumps(pins,sort_keys=True).encode()).hexdigest()));print('sealed',len(pins));return
 seal=json.loads(manifest.read_text())['files'];verify(seal)
 state=json.loads((D/'status.json').read_text()) if (D/'status.json').exists() else dict(started_at=now(),results=[],profiles_completed=[],default_changed=False)
 assert a.profile not in state['profiles_completed']
 if a.profile!='base':
  assert 'base' in state['profiles_completed'],'baseline must complete first'
  assert not any(x!='base' for x in state['profiles_completed']), 'at most one follow-up profile'
  assert not any(x['profile']!='base' for x in state['results']), 'follow-up already started'
  final={}
  for seed in (7,17):
   final[seed]={x['mode']:x['metrics'] for x in state['results'] if x['profile']=='base' and x['seed']==seed and x['updates']==300}
   assert set(final[seed])=={'mean','sampled'},'both seed final evaluations required'
  narrow=all(final[z]['sampled']['AB_achievement_count']>=final[z]['mean']['AB_achievement_count']+4 for z in (7,17))
  broad=all(final[z]['sampled']['AB_achievement_count']<4 and final[z]['sampled']['notes'][1]['contact']<16 for z in (7,17))
  assert (a.profile=='narrow' and narrow) or (a.profile=='broad' and broad),'predeclared follow-up predicate not met'
  state['selected_followup']=a.profile
 state.update(completed=False,profile=a.profile,stage='starting');publish(state)
 try:
  for seed in (7,17):
   checkpoint=None
   for updates in (100,200,300):
    name=f'{a.profile}_seed{seed}_u{updates}';out=D/'모델'/name
    args=['train','--updates','100','--seed',str(seed),'--num-envs','64','--size','large','--noise-profile',a.profile]
    if checkpoint:args+=['--resume',str(checkpoint)]
    r=stage(state,seal,name,args,out);jr=json.loads((out/'J/report.json').read_text());assert jr['updates_in_run']==100 and jr['transitions']==204800
    checkpoint=out/'J/final.pt';lr=[json.loads(x) for x in (out/'J/learning_metrics.jsonl').read_text().splitlines()];assert len(lr)==100
    for mode in ('mean','sampled'):
     label=name+'_'+mode;ev=D/'진단'/label
     stage(state,seal,label,['evaluate','--checkpoint',str(checkpoint),'--action-mode',mode,'--num-envs','32'],ev)
     m=analyze(ev);state['results'].append(dict(profile=a.profile,seed=seed,updates=updates,mode=mode,checkpoint=str(checkpoint),evaluation=str(ev),train_updates_in_run=100 if mode=='mean' else 0,train_transitions_in_run=204800 if mode=='mean' else 0,train_wall_s=jr['wall_s'],optimizer_accepted_steps=sum(v['diagnostics']['minibatches']['actor_accepted']['steps'] for v in lr),optimizer_value_steps=sum(v['diagnostics']['minibatches']['value']['steps'] for v in lr),metrics=m));publish(state)
  verify(seal);state['profiles_completed'].append(a.profile);state.update(stage='profile_complete',job='',execution_completed_at=now());publish(state)
 except BaseException as error:
  state.update(stage='stopped_error',error=repr(error),traceback=traceback.format_exc(),stopped_at=now());publish(state);raise
if __name__=='__main__':main()
