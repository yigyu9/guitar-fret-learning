if __name__=='__main__':import isaacgym
import pathlib,sys,json,hashlib,argparse,importlib.util
import numpy as np
import torch
D=pathlib.Path(__file__).resolve().parents[1];R=next(p for p in D.parents if (p/'scripts/tab2body.py').exists());sys.path.insert(0,str(R));sys.path.insert(0,str(D/'도구'))
import runtime as rt
import reference_motion as motion
from reference_motion import trajectory,quintic
from guitar_learning.training.training_log_io import dumps
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--settle',type=float,default=.4);a=p.parse_args();motion.SETTLE_S=a.settle;a.out.mkdir(parents=True,exist_ok=False)
 v=json.loads((D/'진단/reference_v1/reference_candidates.json').read_text());assert all(sha(pathlib.Path(n))==h for n,h in v['source_sha256'].items())
 ts,qs,_=trajectory(v['candidates'],.75);settings=rt.build_settings(num_envs=1,updates=2);pool=None;rows=[];completed=[];pins={str(p):sha(p) for p in (D/'도구').glob('*.py')};initial=0;max_fk_position_error=0.;max_fk_rotation_error=0.
 from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
 from types import SimpleNamespace
 from scipy.spatial.transform import Rotation
 try:
  pool=rt.TransitionPool(settings,a.out);e=pool.environment;c=pool.controller;active=torch.tensor(settings['natural_press']['active_axes'],device=c.device);q0=np.array(v['initial_hold_target105']);qpress=np.array(v['candidates']['A_press']['q105']);qhoverB=np.array(v['candidates']['B_hover']['q105'])
  fk=full_fk(SimpleNamespace(names=pool.scene.names,human_bodies=pool.scene.human_bodies,q_ref=np.array(v['initial_q105'])),v['initial_state'])
  initial=dict(settle_s=a.settle,q_max_error_rad=float((pool.scene.q[0]-torch.tensor(v['initial_q105'],device=c.device)).abs().max()),candidate=e.candidate.tolist(),wrong=e.wrong.tolist(),native_reset_source=pool.scene.metadata['reset_body_source'])
  for tick in range(435):
   t=(tick+1)/60
   if t<=.5:q=q0
   elif t<2.8:q=q0+quintic((t-.5)/2.3)*(qpress-q0)
   elif t<3:q=qpress
   elif t<=6.75:q=qs[min(round((t-3)*60),len(qs)-1)]
   else:q=np.array(v['candidates']['B_press']['q105'])+quintic((t-6.75)/.5)*(qhoverB-np.array(v['candidates']['B_press']['q105']))
   req=torch.tensor(q,device=c.device,dtype=c.reference.dtype)[c.active];action=rt.natural.normalized_action(req,c.reference[c.active],c.action_low,c.action_high)[None]
   obs,reward,cost,term,trunc,eps=pool.step(action);completed.extend(eps)
   rows.append(dict(time_s=t,candidate=e.candidate.tolist(),wrong=e.wrong.tolist(),distance=e.surface_distance.tolist(),height=e.surface_height.tolist(),alignment=e.surface_alignment.tolist(),requested_q105=q.tolist(),applied_q105=c.target[0].tolist(),actual_q105=pool.scene.q[0].tolist(),wrist_delta=e.guide['delta'].tolist()))
   if tick%60==0:
    actual=pool.scene.body_state[0].cpu().numpy();predicted=fk(pool.scene.q[0].cpu().numpy().astype(float))
    for name in ('L_Wrist','LH:index3','LH:middle3'):
     body=actual[pool.scene.body_names.index('human/'+name)];pos,rot=predicted[name]
     max_fk_position_error=max(max_fk_position_error,float(np.linalg.norm(pos-body[:3])))
     max_fk_rotation_error=max(max_fk_rotation_error,float((rot.inv()*Rotation.from_quat(body[3:7])).magnitude()))
   if tick%60==0:print(round(t,3),e.candidate.tolist(),e.wrong.tolist(),flush=True)
   if bool((term|trunc).any()):break
  assert all(sha(pathlib.Path(n))==h for n,h in pins.items()),'source changed'
 finally:
  if pool is not None:pool.close()
 assert completed,'reference did not terminate'
 ep=completed[0];safe=not(ep['termination']['physical_failure'] or ep['termination']['wrist_failure']);ledger=ep['left_note_ledger']['values'];onsets=ep['transition_diagnostics']['first_contact_s'];schedule=settings['transition']['schedule']
 passed=bool(safe and ep['steps']==435 and all(v>=1.5-1e-8 for v in ledger['clean']) and all(t is not None and t-s['onset_s']<=1/240+1e-8 for t,s in zip(onsets,schedule)) and not any(any(x) for row in rows[:30] for x in row['candidate']) and max_fk_position_error<=.002 and max_fk_rotation_error<=.05)
 (a.out/'reference_trace60.json').write_text(dumps(rows,allow_nan=False));(a.out/'episodes.json').write_text(dumps(completed,allow_nan=False));(a.out/'report.json').write_text(dumps(dict(completed=True,passed=passed,max_fk_position_error_m=max_fk_position_error,max_fk_rotation_error_rad=max_fk_rotation_error,initial=initial,source_unchanged=True,scene_closed=pool.closed,episodes=completed,kind='finite controller reference, not learned policy',pins=pins),allow_nan=False,indent=2))
 if not passed:raise RuntimeError('reference strict full-hold/onset/initial/safety gate failed; see report')
if __name__=='__main__':main()
