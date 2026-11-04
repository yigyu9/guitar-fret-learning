"""Serial fixed-budget H training and strict evaluation; sealed native runtime only."""
if not __debug__:raise RuntimeError('optimized Python forbidden')
from pathlib import Path
import os,sys,json,time,datetime,hashlib,subprocess,signal,fcntl,traceback,importlib.util,copy
import psutil
D=Path(__file__).resolve().parents[1];SNAP=D/'작업자료/source_snapshot';R=D.parents[2];SH=Path('/home/yigyu/cgl-lab/docs/2026-11-09/H실험');WORK=D/'작업자료';TOTAL=16777216;QUARTER=4194304
now=lambda:datetime.datetime.now().astimezone().isoformat()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.pc2tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2));q.replace(p)
def state(**kw):
 x=json.loads((D/'진행상황.json').read_text());x.update(updated_at=now(),supervisor_pid=os.getpid(),**kw)
 if x.get('phase')=='training_running':
  for row in x.get('conditions',[]):
   if row['name']==x.get('current_condition'):row.update(status='running',global_update=x.get('global_update',0),committed_transitions=x.get('committed_transitions',0),pid=x.get('running_pid'))
 write(D/'진행상황.json',x)
 try:write(SH/'진행상황.json',x)
 except OSError as e:
  x['shared_status_sync_error']=repr(e);write(D/'진행상황.json',x)
 return x
def study():
 sp=importlib.util.spec_from_file_location('sealed_study',D/'도구/study.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def check():
 v=study().check(R,D);assert v['snapshot_valid'] and v['design_valid'];return v
def lines(p):
 if not p.exists():return []
 s=p.read_text();s=s[:s.rfind('\n')+1];return [json.loads(x) for x in s.splitlines() if x]
def livejson(p):
 try:return json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError):return {}
def lastline(p):
 if not p.exists():return None
 with p.open('rb') as f:f.seek(max(0,p.stat().st_size-200000));b=f.read()
 end=b.rfind(b'\n')
 if end<0:return None
 z=b[:end].splitlines();return json.loads(z[-1]) if z else None
def stopchild(p):
 if p.poll() is None:
  try:os.killpg(p.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:p.wait(timeout=30)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
def verify_manifest(stage,cache=None):
 out=[]
 for row in lines(stage/'checkpoint_manifest.jsonl'):
  path=stage/row['path'];key=(str(path),row['sha256'],path.stat().st_size,path.stat().st_mtime_ns)
  if cache is None or key not in cache:
   assert sha(path)==row['sha256'],'checkpoint SHA mismatch '+str(path)
   if cache is not None:cache.add(key)
  out.append(row)
 return out

def publish_tree(path):
 dest=SH/path.relative_to(D);dest.parent.mkdir(parents=True,exist_ok=True)
 if path.is_dir():
  subprocess.run(['rsync','-rt','--ignore-existing',str(path)+'/',str(dest)+'/'],check=True)
  files=[p for p in path.rglob('*') if p.is_file()]
 else:
  if dest.exists():assert sha(path)==sha(dest),'refuse overwrite of changed shared file '+str(dest)
  else:
   with path.open('rb') as a,dest.open('xb') as b:
    import shutil
    shutil.copyfileobj(a,b,8*1024*1024)
  files=[path]
 entries={}
 for p in files:
  target=SH/p.relative_to(D);h=sha(p);assert h==sha(target),'shared copy SHA mismatch';entries[str(p.relative_to(D))]=h
 receipt=WORK/'공유검증';receipt.mkdir(exist_ok=True);key=hashlib.sha256(str(path).encode()).hexdigest()[:12];write(receipt/(key+'.json'),dict(path=str(path),verified_at=now(),files=entries))

def run_job(argv,name,kind,horizon=None,expected_updates=None,baseline_settings=None):
 check();assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU occupied'
 assert sha(Path(__file__))==CONTROL_SHA,'supervisor source changed'
 out=Path(argv[argv.index('--out')+1]);assert not out.exists(),'output must be new'
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MAX_JOBS='2');env.pop('PYTHONUTF8',None);env.pop('PYTHONOPTIMIZE',None);env.pop('CUDA_VISIBLE_DEVICES',None)
 logpath=WORK/(name+'.log');respath=WORK/(name+'_resources.jsonl');write(WORK/(name+'_command.json'),dict(argv=argv,cwd=str(SNAP),started_at=now(),kind=kind,supervisor_sha256=CONTROL_SHA))
 started=time.monotonic();peakv=peakrss=0;last_state=0;last_new=time.monotonic();last_tick=None;cache=set();settings_checked=False
 with logpath.open('x') as log,respath.open('x') as resources:
  child=subprocess.Popen(argv,cwd=SNAP,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   state(phase=kind+'_running',current_condition=name,running_pid=child.pid,stage_started_at=now(),training_started=True,error=None,next_step='H32→H64→H128학습→동일경험량15평가→분석→대표영상',global_update=0,committed_transitions=0)
   while child.poll() is None:
    used=float(subprocess.check_output(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],text=True).splitlines()[0]);rss=0
    try:
     for p in [psutil.Process(child.pid)]+psutil.Process(child.pid).children(recursive=True):
      try:rss+=p.memory_info().rss
      except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    except psutil.NoSuchProcess:pass
    peakv=max(peakv,used);peakrss=max(peakrss,rss);elapsed=time.monotonic()-started;resources.write(json.dumps(dict(time=now(),elapsed_s=elapsed,gpu_total_used_MiB=used,process_tree_rss_bytes=rss,system_available_bytes=psutil.virtual_memory().available))+'\n');resources.flush()
    stage=out/'J' if kind=='training' else out
    if kind=='training' and (stage/'settings.json').exists() and not settings_checked:
     settings=livejson(stage/'settings.json')
     if settings:
      assert settings['num_envs']==1024 and settings['horizon']==horizon and settings['updates']==expected_updates
      trimmed={k:v for k,v in settings.items() if k not in ('horizon','updates','checkpoint_every')}
      if baseline_settings is not None:assert trimmed==baseline_settings,'unexpected setting difference beyond H/updates/checkpoint_every'
      settings_checked=True
    checkpoints=verify_manifest(stage,cache) if kind=='training' else []
    metric=lastline(stage/'learning_metrics.jsonl') if kind=='training' else None
    monitor=livejson(stage/'status.json')
    tick=(metric.get('optimizer_updates') if metric else None,monitor.get('update_index'),monitor.get('ticks'),logpath.stat().st_size)
    if tick!=last_tick:last_new=time.monotonic();last_tick=tick
    if time.monotonic()-last_new>1200:raise TimeoutError('no new progress or log output for1200s')
    if elapsed>24*3600:raise TimeoutError('single-stage24h timeout')
    if time.monotonic()-last_state>=15:
     committed=metric['curriculum']['committed_transitions'] if metric else 0;rate=committed/elapsed if committed else None;remaining=(TOTAL-committed)/rate if rate and kind=='training' else None
     state(global_update=metric['optimizer_updates'] if metric else 0,committed_transitions=committed,latest_checkpoint_sha256=checkpoints[-1]['sha256'] if checkpoints else None,latest_checkpoint_path=str(stage/checkpoints[-1]['path']) if checkpoints else None,actual_transitions_per_s=rate,collection_transitions_per_s=metric['transitions']/metric['collection_s'] if metric else None,elapsed_s=elapsed,estimated_stage_end=(datetime.datetime.now().astimezone()+datetime.timedelta(seconds=remaining)).isoformat() if remaining else None,peak_gpu_total_used_MiB=peakv,peak_process_tree_rss_bytes=peakrss,native_phase=monitor.get('phase'),native_ticks=monitor.get('ticks'));last_state=time.monotonic()
    time.sleep(2)
   code=child.wait()
  finally:stopchild(child)
 check();assert sha(Path(__file__))==CONTROL_SHA
 report=json.loads((out/'report.json').read_text()) if (out/'report.json').exists() else {}
 if code!=0 or report.get('completed') is not True:
  state(phase='stopped_error',running_pid=None,error=dict(stage=name,returncode=code,report=report,log=str(logpath)),next_step='원시실패분석;NaN·봉인·입력오류반복재시도금지')
  if out.is_dir():publish_tree(out)
  publish_tree(logpath);raise RuntimeError('stage failed '+name)
 if kind=='training':
  stage=out/'J';r=json.loads((stage/'report.json').read_text());assert r['completed'] and r['lifecycle_verified'] and not any(r.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))
  assert r['transitions']==TOTAL and r['optimizer_updates']==expected_updates and r['curriculum']['config']==dict(planned_transitions=TOTAL,full_song_after=QUARTER) and r['curriculum']['committed_transitions']==TOTAL
  cp=verify_manifest(stage);assert len(cp)==5 and {x['optimizer_updates'] for x in cp}=={0,expected_updates//4,expected_updates//2,expected_updates*3//4,expected_updates}
  settings=json.loads((stage/'settings.json').read_text());baseline_settings={k:v for k,v in settings.items() if k not in ('horizon','updates','checkpoint_every')}
 else:
  assert report['episodes']==32 and report['first_episode_per_env_per_batch'] and report['failed_episodes_in_denominator'];assert not any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'));assert report['gpu_scene']['closed']
 elapsed=time.monotonic()-started;receipt=dict(stage=name,kind=kind,completed_at=now(),wall_s=elapsed,report_wall_s=report.get('wall_s'),peak_gpu_total_used_MiB=peakv,peak_process_tree_rss_bytes=peakrss,returncode=code,report=str(out/'report.json'),baseline_settings=baseline_settings if kind=='training' else None)
 write(WORK/(name+'_receipt.json'),receipt);state(phase=kind+'_complete',running_pid=None,last_completed_stage=name)
 publish_tree(out)
 for p in (logpath,respath,WORK/(name+'_command.json'),WORK/(name+'_receipt.json')):publish_tree(p)
 return baseline_settings

def main():
 lock=(WORK/'PC2_실행.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def stop(sig,frame):raise KeyboardInterrupt('supervisor signal '+str(sig))
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 assert json.loads((D/'검증/H128_메모리검사.json').read_text())['passed'] is True
 check();commands=study().commands(R,D);assert commands==json.loads((WORK/'명령목록.json').read_text())
 write(WORK/'본실험_감독계약.json',dict(started_at=now(),source_sha256=CONTROL_SHA,commands_sha256=sha(WORK/'명령목록.json'),design_sha256=sha(D/'설계.json'),seal_sha256=sha(D/'기준봉인.json'),sequence='trainH32,H64,H128 then15full-song evaluations; no auto budget/algorithm changes',automatic_recovery='none for uncertain errors; only explicitly diagnosed transient incident may be resumed once via separate strict attempt'))
 baseline=None;completed=[]
 for c in commands['conditions']:
  updates=TOTAL//c['batch_transitions'];baseline=run_job(c['train'],c['name'],'training',c['horizon'],updates,baseline);completed.append(c['name']);x=state(completed_training_conditions=completed)
  for row in x['conditions']:
   if row['name']==c['name']:row.update(status='training_complete',committed_transitions=TOTAL)
  write(D/'진행상황.json',x);write(SH/'진행상황.json',x)
 for c in commands['conditions']:
  training=Path(c['train'][c['train'].index('--out')+1]);manifest=verify_manifest(training/'J');known={x['path']:x for x in manifest}
  for ev in c['evaluations']:
   cp=Path(ev['checkpoint']);assert cp.name in known and sha(cp)==known[cp.name]['sha256'];assert known[cp.name]['optimizer_updates']*c['batch_transitions']==ev['transitions']
   run_job(ev['argv'],c['name']+'_T%09d'%ev['transitions'],'evaluation')
 state(phase='training_evaluation_complete',running_pid=None,current_condition=None,next_step='사전정의strict/해제집계→모델선정→조건별손확대/전신렌더→보고서')
 print('all three fixed-budget training jobs and15 evaluations completed',flush=True)

CONTROL_SHA=sha(Path(__file__))
if __name__=='__main__':
 try:main()
 except BlockingIOError:traceback.print_exc();raise
 except BaseException as e:traceback.print_exc();state(phase='stopped_error',running_pid=None,error=repr(e));raise
