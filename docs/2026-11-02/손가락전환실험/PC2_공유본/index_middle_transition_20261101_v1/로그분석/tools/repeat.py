if not __debug__:raise RuntimeError('optimization disabled required')
from pathlib import Path
import json,hashlib,subprocess,os,sys,signal,fcntl,datetime,time
L=Path(__file__).resolve().parents[1];D=L.parent;R=next(p for p in L.parents if (p/'scripts/tab2body.py').exists());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(v):
 q=L/'status.tmp';q.write_text(json.dumps(v,indent=2));q.replace(L/'status.json')
def main():
 lock=(D/'study.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 def stop(s,f):raise KeyboardInterrupt('signal '+str(s))
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 ck=D/'모델/base_seed17_u200/J/final.pt';pins=json.loads((D/'보존/study_seal.json').read_text())['files'];own={str(p):sha(p) for p in (L/'tools').glob('*.py')};before=sha(ck);state={'stage':'repeating','checkpoint_sha256':before,'observer_source_sha256':own,'completed':[]}
 def check():
  assert all(sha(R/p)==h for p,h in pins.items()),'original seal changed'
  assert sha(ck)==before and all(sha(Path(p))==h for p,h in own.items()),'checkpoint/observer changed'
 for run in range(1,4):
  for n in (32,128):
   check();assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU occupied'
   name=f's17_u200_mean_N{n}_repeat{run}';out=L/'runs'/name;out.parent.mkdir(exist_ok=True);assert not out.exists();state.update(stage='evaluating',current=name,started_at=datetime.datetime.now().isoformat());write(state)
   cmd=[sys.executable,str(R/'scripts/tab2body.py'),'--cache-root','/home/yigyu/.cache/tab2body','run','-u',str(L/'tools/observe_evaluate.py'),'evaluate','--checkpoint',str(ck),'--action-mode','mean','--num-envs',str(n),'--out',str(out)]
   env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MAX_JOBS='2');env.pop('PYTHONOPTIMIZE',None);env.pop('PYTHONUTF8',None)
   with (L/'logs'/f'{name}.log').open('w') as log:
    child=subprocess.Popen(cmd,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:code=child.wait(timeout=1200)
    finally:
     if child.poll() is None:
      try:os.killpg(child.pid,signal.SIGTERM)
      except ProcessLookupError:pass
      try:child.wait(timeout=10)
      except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
   assert code==0,name+' failed';check();r=json.loads((out/'report.json').read_text());assert r['completed'] and not r.get('failure') and not r.get('changed_inputs') and not r.get('missing_import_pins') and not r.get('cleanup_errors');state['completed'].append(name);write(state)
 state.update(stage='evaluations_complete',current='');write(state)
if __name__=='__main__':
 try:main()
 except BaseException as error:
  v=json.loads((L/'status.json').read_text()) if (L/'status.json').exists() else {}
  v.update(stage='stopped_error',error=repr(error));write(v);raise
