import isaacgym
from isaacgym import gymapi
import torch,json,time,sys
from pathlib import Path
from unittest.mock import patch
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.gpu.control import BatchedController
from guitar_learning.gpu.geometry import multiply,conjugate,rotvec

n=int(sys.argv[1]);spacing=float(sys.argv[2]);buffers=float(sys.argv[3]) if len(sys.argv)>3 else 5.;max_pairs=int(sys.argv[4]) if len(sys.argv)>4 else None;aggregate=len(sys.argv)>5 and sys.argv[5]=='aggregate';raw=gymapi.acquire_gym()
class LayoutGym:
 def __init__(self):self.assets=[];self.groups=[]
 def __getattr__(self,name):return getattr(raw,name)
 def load_asset(self,*args):
  asset=raw.load_asset(*args);self.assets.append(asset);return asset
 def create_box(self,*args):
  asset=raw.create_box(*args);self.assets.append(asset);return asset
 def create_actor(self,env,asset,pose,label,group,collision_filter):
  if aggregate and label=='human':
   bodies=sum(raw.get_asset_rigid_body_count(a) for a in self.assets)
   shapes=sum(raw.get_asset_rigid_shape_count(a) for a in self.assets)
   raw.begin_aggregate(env,bodies,shapes,True)
  actor=raw.create_actor(env,asset,pose,label,group,collision_filter)
  self.groups.append((group,label))
  if aggregate and label=='chair':raw.end_aggregate(env)
  return actor
 def create_sim(self,compute,graphics,engine,params):
  params.physx.default_buffer_size_multiplier=buffers
  if max_pairs is not None:params.physx.max_gpu_contact_pairs=max_pairs
  return raw.create_sim(compute,graphics,engine,params)
 def create_env(self,sim,lower,upper,per_row):
  return raw.create_env(sim,gymapi.Vec3(-spacing/2,-spacing/2,0),gymapi.Vec3(spacing/2,spacing/2,2.5),per_row)
if torch.cuda.mem_get_info()[0] < 2*1024**3:raise RuntimeError('GPU free memory below2GiB')
proxy=LayoutGym()
with patch.object(gymapi,'acquire_gym',lambda:proxy):s=GpuScene(n,'left','cuda:0')
out=Path('/tmp/guitar_control_layout_n%d_s%g_%d.json'%(n,spacing,time.time_ns()))
try:
 c=BatchedController(s);x=s.snapshot();start=time.monotonic();ids=torch.tensor(sorted(set(i for i in [0,1,63,64,65,68,127,512,n-1] if i<n)),device=s.device)
 initial=x['body_state'].clone();g=len(s.human_bodies);rows=[];invalid=None
 with torch.no_grad():
  for step in range(32):
   if torch.cuda.mem_get_info()[0] < 1024**3:raise RuntimeError('GPU free memory below1GiB')
   if step%4==0:t=c.targets(torch.zeros(n,39,device=s.device),x)
   e=c.efforts(x)
   if not bool(c.diagnostics['valid'].all()):
    invalid=dict(step_before_submission=step+1,nonfinite=(~c.diagnostics['finite']).nonzero().flatten().tolist(),uncertified=(~c.diagnostics['chest_witness_certified']).nonzero().flatten().tolist(),undefined_normal=(~c.diagnostics['chest_normal_defined']).nonzero().flatten().tolist(),fallback=c.diagnostics['chest_exact_fallback_used'].nonzero().flatten().tolist());break
   initial_torque=e.clone() if step==0 else initial_torque
   x=s.step(t,e);body=x['body_state']
   delta=torch.linalg.vector_norm(body[:,g,:3]-initial[:,g,:3],dim=-1)
   angle=torch.linalg.vector_norm(rotvec(multiply(conjugate(initial[:,g,3:7]),body[:,g,3:7])),dim=-1)
   speed=x['qd'].abs().amax(-1)
   safe=(delta<.08)&(angle<.35)&(speed<50)&torch.isfinite(x['q']).all(-1)
   rows.append(dict(step=step+1,envs=ids.tolist(),translation_m=delta[ids].tolist(),angle_rad=angle[ids].tolist(),speed_rad_s=speed[ids].tolist(),safe_count=int(safe.sum()),translation_max_m=float(delta.max()),translation_mean_m=float(delta.mean()),angle_max_rad=float(angle.max()),speed_max_rad_s=float(speed.max()),exact_fallback_count=int(c.diagnostics['chest_exact_fallback_used'].sum()),gpu_free_mib=torch.cuda.mem_get_info()[0]/1024**2))
 result=dict(num_envs=n,spacing_m=spacing,buffer_size_multiplier=buffers,max_gpu_contact_pairs=max_pairs,per_env_aggregate=aggregate,aggregate_self_collision=True,actor_collision_groups=proxy.groups,collision_group_native_getters=[name for name in dir(raw) if 'collision_group' in name],origins_max_m=s.origins.max(0).values.tolist(),first_invalid=invalid,initial_torque_batch_max_diff=float((initial_torque-initial_torque[:1]).abs().amax()),elapsed_s=time.monotonic()-start,rows=rows,diagnostics=s.diagnostics)
 out.write_text(json.dumps(result,indent=2));print('RESULT',str(out));print(json.dumps(result['rows'][-1]))
finally:s.close()
