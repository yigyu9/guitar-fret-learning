if not __debug__:raise RuntimeError('Scientific checks require optimization disabled')
from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parents[2];R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R));sys.path.insert(0,str(D/'도구'));import study as st
from guitar_learning.training.training_log_io import iter_episode_rows

def main():
 lock=(D/'study.lock').open('a');st.fcntl.flock(lock,st.fcntl.LOCK_EX|st.fcntl.LOCK_NB)
 def interrupted(signum,frame):raise KeyboardInterrupt('context recheck interrupted')
 st.signal.signal(st.signal.SIGTERM,interrupted);st.signal.signal(st.signal.SIGINT,interrupted)
 state=json.loads((D/'status.json').read_text());seal=json.loads((D/'보존/study_seal.json').read_text())['files'];st.verify(seal);digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();checkpoint=D/'모델/base_seed17_u200/J/final.pt';results={}
 try:
  for n in (32,128):
   if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=digest:raise RuntimeError('observer code changed')
   label='context_repeat_seed17_mean_'+str(n);out=D/'진단'/label
   st.stage(state,seal,label,['evaluate','--checkpoint',str(checkpoint),'--action-mode','mean','--num-envs',str(n)],out);m=st.analyze(out);rows=[x['episode'] for x in iter_episode_rows(out)];results[str(n)]={'metrics':m,'per_env_achieved':{str(x['env_id']):x['left_note_ledger']['values']['left'] for x in rows}};st.write(D/'진단/context_recheck.json',{'source_sha256':digest,'evaluations':results})
  st.verify(seal)
  if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=digest:raise RuntimeError('observer code changed')
  state.update(stage='awaiting_final_review',job='',context_recheck_completed=True);st.publish(state)
 except BaseException as e:state.update(stage='stopped_error',error=repr(e));st.publish(state);raise
if __name__=='__main__':main()
