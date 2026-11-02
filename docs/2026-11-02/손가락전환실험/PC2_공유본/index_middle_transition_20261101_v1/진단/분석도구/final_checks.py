if not __debug__:raise RuntimeError('Scientific checks require optimization disabled')
from pathlib import Path
import json,sys,hashlib,shutil,subprocess
D=Path(__file__).resolve().parents[2];R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R));sys.path.insert(0,str(D/'도구'))
import study as st

def main():
 lock=(D/'study.lock').open('a');st.fcntl.flock(lock,st.fcntl.LOCK_EX|st.fcntl.LOCK_NB)
 def interrupted(signum,frame):raise KeyboardInterrupt('post-check interrupted by signal '+str(signum))
 st.signal.signal(st.signal.SIGTERM,interrupted);st.signal.signal(st.signal.SIGINT,interrupted)
 script_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 original_stage=st.stage
 def checked_stage(*args,**kwargs):
  if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=script_sha:raise RuntimeError('post-check source changed')
  result=original_stage(*args,**kwargs)
  if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=script_sha:raise RuntimeError('post-check source changed')
  return result
 st.stage=checked_stage
 st.write(D/'진단/post_checks_source.json',dict(path=str(Path(__file__).resolve()),sha256=script_sha,scope='read-only evaluation/render orchestration; sealed training sources unchanged'))
 state=json.loads((D/'status.json').read_text());seal=json.loads((D/'보존/study_seal.json').read_text())['files'];st.verify(seal);assert state['stage']=='profile_complete' and state['profiles_completed']==['base']
 def rank(x):
  m=x['metrics'];return (m['AB_achievement_count'],-m['any_failures'],min(v['mean_clean_s'] for v in m['notes']),sum(v['mean_clean_s'] for v in m['notes']),sum(v['onset_count'] for v in m['notes']),-x['updates'])
 selected={str(s):max((x for x in state['results'] if x['seed']==s and x['mode']=='mean'),key=rank) for s in (7,17)}
 st.write(D/'진단/model_selection.json',dict(selected=selected,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),adopted=False,reason='best available diagnostic models; primary operational threshold not passed'))
 output={}
 try:
  for seed in (7,17):
   ck=D/f'모델/base_seed{seed}_u300/J/final.pt';label=f'probe_seed{seed}_u300_sampled_std0p5';out=D/'진단'/label
   st.stage(state,seal,label,['evaluate','--checkpoint',str(ck),'--action-mode','sampled','--std-scale','.5','--num-envs','32'],out);output[label]=st.analyze(out);st.write(D/'진단/final_checks.json',output)
  for seed in (7,17):
   ck=selected[str(seed)]['checkpoint']
   for mode in ('mean','sampled'):
    label=f'final128_seed{seed}_{mode}';out=D/'진단'/label
    st.stage(state,seal,label,['evaluate','--checkpoint',str(ck),'--action-mode',mode,'--num-envs','128'],out);output[label]=st.analyze(out);st.write(D/'진단/final_checks.json',output)
  for role,ck in (('선정_실패진단용',selected['7']['checkpoint']),('마지막_300회',str(D/'모델/base_seed7_u300/J/final.pt'))):
   label='render_'+('selected' if role.startswith('선정') else 'last');out=D/'진단'/label
   st.stage(state,seal,label,['render','--checkpoint',str(ck),'--num-envs','1'],out)
   for view,name in (('hand','손확대'),('fullbody','전신')):
    p=out/(view+'.mp4');subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True)
    target=D/'동영상'/f'{role}_seed7_평균정책_{name}.mp4';shutil.copy2(p,target)
   output[label]={'checkpoint':str(ck),'views':['hand','fullbody'],'policy_mode':'mean','representative':'env0 single native episode, not aggregate performance'};st.write(D/'진단/final_checks.json',output)
  st.verify(seal);state.update(stage='awaiting_final_review',job='',post_checks_completed=True);st.publish(state)
 except BaseException as e:
  state.update(stage='stopped_error',error=repr(e));st.publish(state);raise
if __name__=='__main__':main()
