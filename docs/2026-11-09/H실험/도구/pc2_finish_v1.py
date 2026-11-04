"""Wait for fixed experiment, aggregate, render six representative videos, verify/publish."""
if not __debug__:raise RuntimeError('optimized Python forbidden')
from pathlib import Path
import os,sys,json,time,hashlib,subprocess,datetime,signal,fcntl,traceback,importlib.util,shutil
import psutil
D=Path(__file__).resolve().parents[1];W=D/'작업자료';S=W/'source_snapshot';SH=Path('/home/yigyu/cgl-lab/docs/2026-11-09/H실험');A=D/'분석';now=lambda:datetime.datetime.now().astimezone().isoformat()
sp=importlib.util.spec_from_file_location('ops',D/'도구/pc2_train_eval_v1.py');ops=importlib.util.module_from_spec(sp);sp.loader.exec_module(ops)
PINS={str(p):ops.sha(p) for p in [Path(__file__),D/'도구/pc2_train_eval_v1.py',D/'도구/pc2_analyze_v1.py',D/'도구/pc2_report_v1.py',D/'도구/study.py',D/'설계.json',D/'기준봉인.json']}
def checkpins():
 assert all(ops.sha(Path(p))==h for p,h in PINS.items()),'finishing tool/input changed while running';return ops.check()
def status(**kw):ops.state(**kw)
def env():
 x=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MAX_JOBS='2');x.pop('PYTHONOPTIMIZE',None);x.pop('PYTHONUTF8',None);x.pop('CUDA_VISIBLE_DEVICES',None);return x

def process(argv,label,cwd=None):
 log=W/(label+'.log');start=time.monotonic()
 with log.open('x') as f:
  p=subprocess.Popen(argv,cwd=cwd or S,env=env(),stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:
   status(running_pid=p.pid,postprocessing_stage=label,postprocessing_started_at=now())
   last=0
   while p.poll() is None:
    checktime=time.monotonic()
    if checktime-last>15:status(postprocessing_elapsed_s=checktime-start);last=checktime
    if checktime-start>3600:raise TimeoutError(label+' exceeded3600s')
    time.sleep(2)
   code=p.wait()
  finally:ops.stopchild(p)
 assert code==0,label+' failed; see'+str(log);return log

def render(c,chosen):
 checkpins();assert not subprocess.check_output(['nvidia-smi','--query-compute-apps=pid','--format=csv,noheader'],text=True).strip(),'GPU occupied'
 a=list(c['render']);i=a.index('render')+1;a[i]=chosen['checkpoint'];cp=Path(a[i]);assert ops.sha(cp)==chosen['sha256'];out=Path(a[a.index('--out')+1]);assert not out.exists()
 display=os.environ.get('DISPLAY');valid_display=bool(display and subprocess.run(['xdpyinfo','-display',display],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0)
 if not valid_display:
  xvfb=shutil.which('xvfb-run')
  if not xvfb:raise RuntimeError('no valid DISPLAY and xvfb-run unavailable; install local rendering dependency without changing training')
  a=[xvfb,'-a']+a
 ops.write(W/(c['name']+'_render_command.json'),dict(argv=a,cwd=str(S),checkpoint_sha256=chosen['sha256'],display=display,display_valid=valid_display));status(phase='render_running',current_condition=c['name'],next_step='원래env0최초episode손확대/전신영상과실제디코딩검사')
 process(a,c['name']+'_render')
 report=json.loads((out/'report.json').read_text());assert report['completed'] and report['scene_closed'] and report['lifecycle_verified'] and report['source_checkpoint_pins_validated'] and report['source_pins_unchanged'] and report['policy_unchanged'] and not report.get('failure') and not report.get('cleanup_errors') and report['checkpoint_sha256']==chosen['sha256'] and all(v==0 for v in report['encoding_exit_codes'].values())
 meta=json.loads((out/'capture_metadata.json').read_text());assert meta['frames']>0 and meta['checkpoint_sha256']==chosen['sha256'];rows=[]
 for camera,korean in [('hand','손확대'),('fullbody','전신')]:
  source=out/(camera+'.mp4');probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration:stream=width,height,nb_frames','-of','json',str(source)],text=True));duration=float(probe['format']['duration']);assert duration>0 and len(probe['streams'])==1
  subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(source),'-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
  name=f"H{c['horizon']}_seed7_T{chosen['transitions']:09d}_{korean}.mp4";dest=D/'동영상'/name
  with source.open('rb') as src,dest.open('xb') as dst:shutil.copyfileobj(src,dst,8*1024*1024)
  assert ops.sha(source)==ops.sha(dest)
  qa=A/'영상검수';qa.mkdir(exist_ok=True);frame=qa/(name[:-4]+'.png');subprocess.run(['ffmpeg','-nostdin','-v','error','-ss',str(duration/2),'-i',str(source),'-frames:v','1',str(frame)],check=True)
  rows.append(dict(condition=c['name'],file=name,source=str(source),sha256=ops.sha(dest),checkpoint_sha256=chosen['sha256'],duration_s=duration,frame_count=probe['streams'][0].get('nb_frames'),source_frames=meta['frames'],source_selection=meta['selection'],native_report=str(out/'report.json'),decoded=True))
 ops.publish_tree(out);return rows

def main():
 ops.write(W/'PC2_후처리계약.json',dict(started_at=now(),source_pins=PINS,wait_for='all3train and15eval completed',analysis='strict original ledger; no new training',render='selected checkpoint, full_song, env0 first episode,1environment, two original native cameras'))
 while True:
  x=json.loads((D/'진행상황.json').read_text());phase=x.get('phase')
  if phase=='training_evaluation_complete':break
  if phase=='stopped_error':raise RuntimeError('training/evaluation supervisor stopped; keep original failure and do not proceed')
  pid=int((W/'PC2_본실험감독.pid').read_text())
  if not psutil.pid_exists(pid) or psutil.Process(pid).status()==psutil.STATUS_ZOMBIE:raise RuntimeError('training/evaluation supervisor exited before required stage')
  time.sleep(15)
 lock=(W/'PC2_실행.lock').open('a')
 for attempt in range(12):
  try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
  except BlockingIOError:
   if attempt==11:raise
   time.sleep(2)
 def stop(sig,frame):raise KeyboardInterrupt('finisher signal'+str(sig))
 signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
 checkpins();status(phase='analysis_running',running_pid=None,current_condition=None,next_step='strict+release원장집계와모델선정')
 process([sys.executable,'-X','utf8',str(D/'도구/pc2_analyze_v1.py')],'PC2_집계',cwd=D.parents[2]);chosen=json.loads((A/'선정모델.json').read_text());cmd=json.loads((W/'명령목록.json').read_text());videos=[]
 for c in cmd['conditions']:videos+=render(c,chosen[c['name']])
 assert len(videos)==6 and len(list((D/'동영상').iterdir()))==6 and all(p.suffix=='.mp4' for p in (D/'동영상').iterdir());ops.write(A/'영상검증.json',dict(verified_at=now(),videos=videos))
 status(phase='reporting',running_pid=None,next_step='최종봉인·공유SHA확인후완료보고');process([sys.executable,'-X','utf8',str(D/'도구/pc2_report_v1.py')],'PC2_보고서',cwd=D.parents[2]);local=checkpins();remote=ops.study().check(SH.parents[2],SH);assert remote['snapshot_valid'] and remote['design_valid']
 ops.write(D/'검증/PC2_최종봉인검사.json',dict(checked_at=now(),local=local,shared=remote,tools=PINS))
 for p in list((D/'도구').glob('pc2_*.py')):
  ops.publish_tree(p)
 ops.publish_tree(D/'검증');ops.publish_tree(A);ops.publish_tree(D/'동영상')
 for p in W.iterdir():
  if p.is_file() and p.suffix in ('.json','.log','.md') and p.name!='PC2_후처리감독.log':ops.publish_tree(p)
 for p in D.glob('*.log'):ops.publish_tree(p)
 receipts=W/'공유검증';remote_receipts=SH/'작업자료/공유검증';remote_receipts.mkdir(parents=True,exist_ok=True)
 for p in receipts.glob('*.json'):
  dest=remote_receipts/p.name
  if not dest.exists():shutil.copyfile(p,dest)
  assert ops.sha(p)==ops.sha(dest)
 complete_rows=json.loads((D/'진행상황.json').read_text())['conditions']
 for row in complete_rows:row.update(status='complete',pid=None,global_update=row['target_updates'],committed_transitions=16777216,evaluations_completed=5,representative_videos=2)
 status(phase='complete',conditions=complete_rows,running_pid=None,estimated_stage_end=None,current_condition=None,completed_at=now(),next_step='완료보고와seed17후속검증우선순위',report='분석/REPORT.md',representative_video_count=6,source_inputs_unchanged=True,training_parameters_modified=False)
 print('H experiment fully completed, source/share hashes verified',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  traceback.print_exc();ops.write(W/'PC2_후처리오류.json',dict(time=now(),error=repr(e)))
  # Preserve training's original stopped_error record when the wait itself is aborted.
  current=json.loads((D/'진행상황.json').read_text())
  if current.get('phase') not in ('training_running','evaluation_running','stopped_error'):status(phase='postprocessing_stopped',running_pid=None,error=repr(e))
  raise
