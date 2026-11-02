"""환경 수만 바꾼 기존6→7 workload의 동일 전이 예산 처리량을 실측한다."""
import fcntl,hashlib,json,os,signal,subprocess,sys,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
import psutil
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE=Path(__file__).resolve().parents[1]
OLD=ROOT/'docs/2026-11-02/압현성공/experiments/transition_diagnosis_v3'
sys.path.insert(0,str(OLD/'tools'))
import study
KST=timezone(timedelta(hours=9))
TOTAL=524288;WARMUP=65536

def now():return datetime.now(KST).isoformat(timespec='seconds')
def write(p,d):study.write(p,d)
def gpu():
 data=subprocess.check_output(['nvidia-smi','--query-gpu=utilization.gpu,memory.used,memory.total','--format=csv,noheader,nounits'],text=True).strip().split(',')
 return dict(utilization_pct=float(data[0]),used_MiB=float(data[1]),total_MiB=float(data[2]),available_ram_bytes=psutil.virtual_memory().available)
def first_summary(folder,n):
 rows={}
 path=folder/'J/episodes.jsonl'
 if path.is_file():
  for line in path.read_text().splitlines():
   ep=json.loads(line)['episode'];rows.setdefault(ep['env_id'],ep)
 physical=sum(ep['termination']['physical_failure'] for ep in rows.values());wrist=sum(ep['termination']['wrist_failure'] for ep in rows.values())
 return dict(first_episodes=len(rows),expected=n,physical=physical,wrist=wrist,failed_envs=sum(ep['termination']['physical_failure'] or ep['termination']['wrist_failure'] for ep in rows.values()))
def refresh(out,state):
 state['updated_at']=now();write(out/'progress.json',state)
 lines=['# 환경 수 처리량 비교','','- 상태: '+state['status'],'- 갱신: '+state['updated_at'],'- 현재: '+str(state.get('current_envs')),
 '- 동일6→7 workload이며6→8성공률비교가아님. 총524288전이,앞65536전이warmup제외.','',
 '|환경수|반복|완료|초당전이(정상상태)|최저VRAM여유GiB|GPU평균%|최초episode 물리/손목|적격|','|---|---:|---|---:|---:|---:|---|---|']
 for row in state['results']:
  s=row.get('episode_summary',{});lines.append(f"|{row['num_envs']}|{row['updates']}|{row.get('completed')}|{row.get('transitions_per_second',0):.1f}|{row.get('min_cuda_free_GiB',0):.2f}|{row.get('mean_gpu_utilization_pct',0):.1f}|{s.get('physical')}/{s.get('wrist')}|{row.get('eligible')}|")
 if state.get('selected_envs'):lines+=['','선정환경수: '+str(state['selected_envs'])]
 if state.get('error'):lines+=['','오류: '+state['error']]
 (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
def clean_kl_failure(report,outer):
 return ((report.get('failure') or {}).get('type')=='KLGuardError'
  and (outer.get('failure') or {}).get('type')=='KLGuardError'
  and report.get('lifecycle_verified') is True
  and all(report.get(k)==[] for k in ('changed_inputs','missing_import_pins','cleanup_errors'))
  and not any(outer.get(k) for k in ('changed_inputs','missing_import_pins','cleanup_errors')))
def run_candidate(out,state,n):
 assert TOTAL%(n*32)==0 and WARMUP%(n*32)==0
 updates=TOTAL//(n*32);warmup=WARMUP//(n*32);folder=out/f'N{n}';log=out/f'N{n}.log'
 command=[sys.executable,'-B',str(ROOT/'scripts/tab2body.py'),'--cache-root',str(ROOT/'.runtime/cache'),'run',str(OLD/'tools/runtime.py'),'train','--updates',str(updates),'--seed','7','--size','large','--num-envs',str(n),'--horizon','32','--out',str(folder)]
 occupied=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip()
 if occupied:raise RuntimeError('다른GPU계산사용중: '+occupied)
 study.check_sources(state)
 state['current_envs']=n;state['command']=command;refresh(out,state)
 environment=dict(os.environ,OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR=str(ROOT/'.runtime/cache/matplotlib'))
 samples=[];start=time.monotonic();child=None
 try:
  with log.open('x') as stream:
   child=subprocess.Popen(command,cwd=ROOT,env=environment,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
   state['child_pid']=child.pid
   while child.poll() is None:
    samples.append(dict(time=now(),**gpu()));write(out/f'N{n}_resources.json',samples)
    metrics=folder/'J/learning_metrics.jsonl';count=0
    if metrics.exists():
     for line in metrics.read_text().splitlines():
      try:json.loads(line);count+=1
      except json.JSONDecodeError:pass
    state['current_completed_updates']=count;refresh(out,state)
    if time.monotonic()-start>1800:raise TimeoutError('벤치단일조건30분초과')
    time.sleep(5)
   code=child.returncode
 finally:
  if child is not None and child.poll() is None:
   os.killpg(child.pid,signal.SIGTERM)
   try:child.wait(timeout=30)
   except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=30)
 study.check_sources(state)
 report_path=folder/'J/report.json';report=json.loads(report_path.read_text()) if report_path.exists() else {}
 rows=[];metrics=folder/'J/learning_metrics.jsonl'
 if metrics.exists():rows=[json.loads(line) for line in metrics.read_text().splitlines() if line.strip()]
 row=dict(num_envs=n,updates=updates,warmup_updates=warmup,physical_transition_budget=TOTAL,wall_s=time.monotonic()-start,exit_code=code,
  completed=code==0 and report.get('completed') is True,report=str(report_path),failure=report.get('failure'),committed_updates=len(rows),
  mean_gpu_utilization_pct=sum(x['utilization_pct'] for x in samples)/len(samples) if samples else 0,
  peak_gpu_memory_MiB=max(x['used_MiB'] for x in samples) if samples else None,
  minimum_available_ram_GiB=min(x['available_ram_bytes'] for x in samples)/1024**3 if samples else 0)
 if any(report.get(k) for k in ('changed_inputs','missing_import_pins','cleanup_errors')):raise RuntimeError('벤치입력/종료검증이상: '+str(n))
 if row['completed']:
  assert report['lifecycle_verified'] and report['updates_in_run']==updates and report['transitions']==TOTAL
  timed=rows[warmup:];timed_s=sum(x['collection_s']+x['update_s'] for x in timed)
  assert sum(x['transitions'] for x in timed)==TOTAL-WARMUP
  row.update(transitions_per_second=(TOTAL-WARMUP)/timed_s,steady_collection_s=sum(x['collection_s'] for x in timed),steady_update_s=sum(x['update_s'] for x in timed),
   full_wall_transitions_per_second=TOTAL/row['wall_s'],min_cuda_free_GiB=report['min_cuda_free_bytes']/1024**3,
   episode_summary=first_summary(folder,n),checkpoint=str(folder/'J/final.pt'),checkpoint_sha256=study.sha(folder/'J/final.pt'),
   accepted_actor_steps=sum(x['diagnostics']['minibatches']['actor_accepted']['steps'] for x in rows),kl_retries=sum(x['kl_retries'] for x in rows))
  ep=row['episode_summary'];row['eligible']=row['min_cuda_free_GiB']>=1 and row['minimum_available_ram_GiB']>=4 and ep['first_episodes']==n and ep['failed_envs']/n<=.01
 else:
  text=log.read_text();row['out_of_memory']='out of memory' in text.lower();row['eligible']=False
  outer_path=folder/'report.json';outer=json.loads(outer_path.read_text()) if outer_path.exists() else {}
  if not row['out_of_memory'] and not clean_kl_failure(report,outer):raise RuntimeError('환경수벤치예상외실패 '+str(n)+' '+text[-1000:])
 return row

def main():
 out=BASE/'benchmark'
 if out.exists():raise FileExistsError(out)
 out.mkdir()
 with (out/'benchmark.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  def stop(signum,frame):raise KeyboardInterrupt('종료신호 '+str(signum))
  signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
  pins=study.seal();pins[str(Path(__file__).resolve().relative_to(ROOT))]=study.sha(__file__)
  state=dict(schema='middle68.env_benchmark.v1',status='running',started_at=now(),driver_pid=os.getpid(),source_seal=pins,results=[],scope='same original6to7 workload; environmental throughput not6to8 success')
  try:
   for n in (256,512,1024):
    row=run_candidate(out,state,n);state['results'].append(row);refresh(out,state);print(json.dumps({k:v for k,v in row.items() if k not in ('failure',)},ensure_ascii=False),flush=True)
   eligible=[r for r in state['results'] if r['eligible']]
   if not eligible:raise RuntimeError('속도/메모리/물리안정성적격조건없음; 장기학습선정금지')
   best=max(eligible,key=lambda r:r['transitions_per_second']);state.update(status='complete',finished_at=now(),selected_envs=best['num_envs'])
  except BaseException as error:
   state.update(status='interrupted' if isinstance(error,KeyboardInterrupt) else 'failed',finished_at=now(),error=repr(error));raise
  finally:
   refresh(out,state);study.check_sources(state)
   write(out/'SOURCE_VERIFICATION.json',dict(unchanged=True,source_count=len(state['source_seal']),checked_at=now()))
if __name__=='__main__':main()
