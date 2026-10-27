import isaacgym
import torch,json,time
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.gpu.control import BatchedController
from guitar_learning.gpu.geometry import multiply,conjugate,rotvec
s=GpuScene(1024,'left','cuda:0')
try:
 c=BatchedController(s);x=s.snapshot();start=time.monotonic();ids=torch.tensor([0,1,63,64,65,68,127,512,1023],device=s.device)
 initial=x['body_state'].clone();g=len(s.human_bodies);rows=[];invalid=None
 with torch.no_grad():
  for step in range(32):
   if step%4==0:t=c.targets(torch.zeros(1024,39,device=s.device),x)
   e=c.efforts(x)
   # Source and bounds are certified before every submission, never relaxed.
   if not bool(c.diagnostics['valid'].all()):
    invalid=dict(step_before_submission=step+1,nonfinite=(~c.diagnostics['finite']).nonzero().flatten().tolist(),uncertified=(~c.diagnostics['chest_witness_certified']).nonzero().flatten().tolist(),undefined_normal=(~c.diagnostics['chest_normal_defined']).nonzero().flatten().tolist(),fallback=c.diagnostics['chest_exact_fallback_used'].nonzero().flatten().tolist())
    break
   jv,jw=c._geometry_jacobian(x['body_state'],c.human_ids,c.all_joint_ids)
   native=x['jacobian']
   jdiff=(native-jv.new_tensor(0)).new_zeros(1024)
   if step>0:
    jdiff=(native[:,:,:3]-jv[:,1:]).abs().flatten(1).amax(-1)
   initial_torque=e.clone() if step==0 else initial_torque
   x=s.step(t,e);body=x['body_state']
   delta=torch.linalg.vector_norm(body[:,g,:3]-initial[:,g,:3],dim=-1)
   angle=torch.linalg.vector_norm(rotvec(multiply(conjugate(initial[:,g,3:7]),body[:,g,3:7])),dim=-1)
   speed=x['qd'].abs().amax(-1)
   safe=(delta<.08)&(angle<.35)&(speed<50)&torch.isfinite(x['q']).all(-1)
   rows.append(dict(step=step+1,envs=ids.tolist(),translation_m=delta[ids].tolist(),angle_rad=angle[ids].tolist(),speed_rad_s=speed[ids].tolist(),effort_peak=e.abs().amax(-1)[ids].tolist(),native_vs_geom_J_max=jdiff[ids].tolist(),safe_count=int(safe.sum()),exact_fallback_count=int(c.diagnostics['chest_exact_fallback_used'].sum()),min_eigen=float(torch.linalg.eigvalsh(c.diagnostics['lower_mass']).amin()),chest_gap_m=c.diagnostics['chest_gap'][ids].tolist()))
 result=dict(first_invalid=invalid,initial_torque_batch_max_diff=float((initial_torque-initial_torque[:1]).abs().amax()),elapsed_s=time.monotonic()-start,rows=rows)
 open('/tmp/guitar_control_batch_debug.json','w').write(json.dumps(result,indent=2));print(json.dumps(result))
finally:s.close()
