"""Detached H128 memory probe using unmodified sealed CLI; no training-condition fallback."""
if not __debug__:raise RuntimeError('assert checks require non-optimized Python')
from pathlib import Path
import os,sys,json,subprocess,time,datetime,hashlib,traceback,importlib.util,signal
import psutil,fcntl
D=Path(__file__).resolve().parents[1];SNAP=D/'작업자료/source_snapshot';R=D.parents[2];SH=Path('/home/yigyu/cgl-lab/docs/2026-11-09/H실험');now=lambda:datetime.datetime.now().astimezone().isoformat()
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):
 q=p.with_name(p.name+'.pc2tmp');q.write_text(json.dumps(x,ensure_ascii=False,indent=2));q.replace(p)
def update(**kwargs):
 x=json.loads((D/'진행상황.json').read_text());x.update(updated_at=now(),supervisor_pid=os.getpid(),**kwargs);write(D/'진행상황.json',x);write(SH/'진행상황.json',x)
def seal():
 spec=importlib.util.spec_from_file_location('study_pc2',D/'도구/study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);x=m.check(R,D);assert x['snapshot_valid'] and x['design_valid'];return x

def main():
 lock=(D/'작업자료/PC2_실행.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def stop(sig,frame):raise KeyboardInterrupt('supervisor signal '+str(sig))
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 seal();cmds=json.loads((D/'작업자료/명령목록.json').read_text());spec=importlib.util.spec_from_file_location('fresh_study',D/'도구/study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);fresh=m.commands(R,D);assert cmds==fresh,'saved command list changed';a=list(cmds['conditions'][2]['train']);baseline=list(a);out=SNAP/'study_outputs/사전검사/H128_memory'
 for k,v in [('--updates','1'),('--checkpoint-every','1'),('--out',str(out))]:a[a.index(k)+1]=v
 assert [(i,baseline[i],a[i]) for i in range(len(a)) if baseline[i]!=a[i]]==[(baseline.index(k)+1,baseline[baseline.index(k)+1],v) for k,v in [('--updates','1'),('--checkpoint-every','1'),('--out',str(out))]],'only3specified memory flags may differ'
 assert not out.exists();assert a[a.index('--num-envs')+1]=='1024' and a[a.index('--horizon')+1]=='128'
 assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU occupied'
 work=D/'작업자료';write(work/'H128_메모리_명령.json',dict(argv=a,cwd=str(SNAP),started_at=now(),scope='one-update resource test; excluded from scientific comparison',supervisor_source_sha256=sha(Path(__file__))))
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MAX_JOBS='2');env.pop('PYTHONUTF8',None);env.pop('PYTHONOPTIMIZE',None);env.pop('CUDA_VISIBLE_DEVICES',None)
 start=time.monotonic();resources=work/'H128_메모리_자원.jsonl';peakv=peakrss=peakram=0;last=0
 with (work/'H128_메모리_실행.log').open('x') as log,resources.open('x') as res:
  child=subprocess.Popen(a,cwd=SNAP,env=env,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True)
  try:
   update(phase='H128_memory_running',running_pid=child.pid,current_condition='H128_memory',gpu_executed=True,training_started=False,started_at=now(),next_step='메모리검사완료및봉인/저장/정리상태확인후H32')
   while child.poll() is None:
    vals=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,memory.free,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip().splitlines()[0].split(',');v=float(vals[0]);rss=0
    try:
     procs=[psutil.Process(child.pid)]+psutil.Process(child.pid).children(recursive=True)
     for p in procs:
      try:rss+=p.memory_info().rss
      except (psutil.NoSuchProcess,psutil.AccessDenied):pass
    except psutil.NoSuchProcess:pass
    mem=psutil.virtual_memory();peakv=max(peakv,v);peakrss=max(peakrss,rss);peakram=max(peakram,mem.total-mem.available);row=dict(time=now(),elapsed_s=time.monotonic()-start,gpu_used_MiB=v,gpu_free_MiB=float(vals[1]),gpu_util_percent=float(vals[2]),process_tree_rss_bytes=rss,system_used_available_basis_bytes=mem.total-mem.available);res.write(json.dumps(row)+'\n');res.flush()
    if time.monotonic()-last>=10:update(memory_peak_gpu_used_MiB=peakv,memory_peak_process_tree_rss_bytes=peakrss,memory_elapsed_s=row['elapsed_s']);last=time.monotonic()
    if time.monotonic()-start>1800:raise TimeoutError('memory probe exceeded1800s')
    time.sleep(1)
   code=child.wait()
  finally:
   if child.poll() is None:
    try:os.killpg(child.pid,signal.SIGTERM)
    except ProcessLookupError:pass
    try:child.wait(timeout=20)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
 repath=out/'report.json';rep=json.loads(repath.read_text()) if repath.exists() else {};stage=out/'J';stage_report=json.loads((stage/'report.json').read_text()) if (stage/'report.json').exists() else {};manifest=[]
 if (stage/'checkpoint_manifest.jsonl').exists():
  for line in (stage/'checkpoint_manifest.jsonl').read_text().splitlines():
   x=json.loads(line);assert sha(stage/x['path'])==x['sha256'],'checkpoint SHA mismatch';manifest.append(x)
 valid=code==0 and rep.get('completed') is True and stage_report.get('completed') is True and stage_report.get('lifecycle_verified') is True and not stage_report.get('failure') and not stage_report.get('changed_inputs') and not stage_report.get('missing_import_pins') and not stage_report.get('cleanup_errors')
 valid=valid and stage_report.get('updates_in_run')==1 and stage_report.get('transitions')==131072 and {'initial','final'}.issubset({r['kind'] for r in manifest})
 after=seal();elapsed=time.monotonic()-start;x=dict(completed_at=now(),passed=valid,returncode=code,peak_gpu_total_used_MiB=peakv,peak_process_tree_RSS_bytes=peakrss,peak_system_used_available_basis_bytes=peakram,wall_s=elapsed,transitions=stage_report.get('transitions'),end_to_end_transitions_per_s=stage_report.get('transitions',0)/elapsed,report=rep,stage_report=stage_report,checkpoint_manifest=manifest,source_check=after)
 write(D/'검증/H128_메모리검사.json',x)
 # Sync only new output and observational metadata; never touch the sealed source payload.
 (SH/'작업자료/source_snapshot/study_outputs/사전검사').mkdir(parents=True,exist_ok=True)
 if out.is_dir():
  destout=SH/'작업자료/source_snapshot/study_outputs/사전검사/H128_memory'
  subprocess.run(['rsync','-rt','--ignore-existing',str(out)+'/',str(destout)+'/'],check=True)
  for source in out.rglob('*'):
   if source.is_file():assert sha(source)==sha(destout/source.relative_to(out)),'shared output hash mismatch'
 for p in (D/'검증/H128_메모리검사.json',work/'H128_메모리_명령.json',work/'H128_메모리_실행.log',resources):
  dest=SH/p.relative_to(D);dest.parent.mkdir(parents=True,exist_ok=True)
  with p.open('rb') as aa,dest.open('xb') as bb:
   import shutil
   shutil.copyfileobj(aa,bb)
  assert sha(p)==sha(dest),'shared metadata hash mismatch'
 if not valid:
  why='memory_or_native_failure; see original report; do not reduce H128 alone';update(phase='stopped_memory_probe',running_pid=None,error=why,next_step='원인보고; OOM이면공통512환경별도설계필요');raise RuntimeError(why)
 update(phase='H128_memory_passed',running_pid=None,memory_probe_passed=True,next_step='H32→H64→H128순차학습과동일경험평가')
 print('memory passed',peakv,elapsed,flush=True)
if __name__=='__main__':
 try:main()
 except BlockingIOError:
  traceback.print_exc();raise
 except BaseException as e:
  traceback.print_exc();update(phase='stopped_error',running_pid=None,error=repr(e));raise
