import isaacgym
import json, numpy as np, torch
from types import SimpleNamespace
from scipy.spatial.transform import Rotation
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.gpu.control import BatchedController
from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
from guitar_learning.native.seated_foot_support_v1.runtime_v6 import Controller as Foot
scene,snap=fake_scene(1)
gpu=BatchedController(scene)
c=scene.contract; ini=c['initial']; saved=c['state']
s=SimpleNamespace(names=scene.names, q_ref=np.array([r['pos'] for r in ini['native_state']['human_dof_states']]), lower=scene.lower.numpy(), upper=scene.upper.numpy(),target=c['target105'].copy(),steps=5280,cfg=c['config'], native=lambda:saved,lower_indices=np.array([i for i,n in enumerate(scene.names) if n.startswith(tuple(side+'_'+part+'_' for side in ('L','R') for part in ('Hip','Knee','Ankle','Toe')))]),human_bodies=scene.human_bodies)
cpu=Foot.__new__(Foot);cpu.s=s;cpu.leg=gpu.foot_channels.numpy();cpu.fk=full_fk(s,ini['native_state']);cpu.reference=cpu.fk(s.q_ref);cpu.locals={gpu.lower_name_order[fk_id]:local.numpy() for fk_id,body_id,local in gpu.sole_points}
old,d=cpu.apply(dict(zip(scene.names,c['target105'])))
new=gpu.targets(torch.zeros(1,39,dtype=scene.q.dtype),snap)[0].numpy()
# Match CPU final native target rate limiter
raw=np.array([old[n] for n in scene.names]); rates=gpu.rate.numpy(); final=np.clip(raw,c['target105']-rates/60,c['target105']+rates/60)
print(json.dumps({'max_target_diff':float(abs(new-final).max()),'diff':{n:{'cpu':float(final[i]),'gpu':float(new[i]),'diff':float(new[i]-final[i]),'qref':float(s.q_ref[i]),'prepared':float(c['target105'][i])} for i,n in enumerate(scene.names) if abs(new[i]-final[i])>1e-8},'cpu_foot_diag':d},indent=2))
from guitar_learning.native.front_facing_ready_v1.runtime_v12 import Controller as NativeController
from guitar_learning.native.om_axilla_source_geometry_v3 import CapsuleBodyDistance
from guitar_learning.native.lower_body_release_v1.common import HUMAN,A,read
from guitar_learning.native.paths import resolve_input_path
from pathlib import Path
# Original controller effort at the same shared prepared state. No native physics.
# Supply independently constructed COM Jacobians and geometric lower mass to API reads.
gpu.target[:]=torch.tensor(final,dtype=scene.q.dtype)
geff=gpu.efforts(snap)[0].numpy();diag=gpu.diagnostics
jv,jw=gpu._geometry_jacobian(snap['body_state'],gpu.human_ids,gpu.all_joint_ids)
s.jacobian=torch.cat((jv,jw),2)[:,1:]
mass=np.zeros((105,105));mass[np.ix_(gpu.moving_leg.numpy(),gpu.moving_leg.numpy())]=diag['lower_mass'][0].numpy()
# zero-range axes are removed by originalcontroller before solve; full24geometry
# direct tensor geometry for all24 to satisfy exact originalmass audit.
legids=torch.tensor(s.lower_indices);lv,lw=gpu._geometry_jacobian(snap['body_state'],gpu.lower_bodies,legids)
r=snap['body_state'][:,gpu.lower_bodies,3:7]
from guitar_learning.gpu.geometry import apply
mat=apply(r[...,None,:],torch.eye(3,dtype=r.dtype)).transpose(-1,-2);inertia=mat@scene.inertia[gpu.lower_bodies]@mat.transpose(-1,-2)
mass24=(scene.mass[gpu.lower_bodies][None,:,None,None]*(lv.transpose(-1,-2)@lv)+lw.transpose(-1,-2)@inertia@lw).sum(1)[0].numpy()
mass[np.ix_(s.lower_indices,s.lower_indices)]=mass24;s.mass_matrix=torch.tensor(mass[None]);s.sim=None;s.gym=SimpleNamespace(refresh_mass_matrix_tensors=lambda _:None,refresh_jacobian_tensors=lambda _:None)
s.effort_indices=np.array(ini['effort_indices']);s.position_indices=np.array(ini['position_indices']);s.zero_indices=np.array(ini['zero_range_indices']);s.upper_effort_indices=np.array([j for j in s.effort_indices if j not in s.lower_indices]);s.hcom=np.array([r['COM_body_m'] for r in ini['human_properties']]);s.mass=np.array([r['mass_kg'] for r in ini['human_properties']]);s.human_properties=ini['human_properties'];s.jacobian_mode='COM';s.control_kp=np.array(ini['control_K105']);s.control_kd=np.array(ini['control_D105']);s.pd_properties={k:np.array(v) for k,v in ini['native_PD_properties'].items()};s.guitar_bodies=ini['guitar_body_names'];s.com={r['name']:np.array(r['COM_body_m']) for r in ini['human_properties']+ini['guitar_properties']['applied']};s.target=final
ncfg=read(A/'config.json');gains=read(resolve_input_path(ncfg['gain_source']));s.kp=np.array([min(max(gains.get(n,[50,5])[0],100 if 'Neck' in n or 'Head' in n else 30),20 if n.startswith(('LH:','RH:')) else 150 if 'Neck' in n or 'Head' in n else 60 if 'Wrist' in n or 'Elbow_y' in n or 'Elbow_z' in n else 600) for n in s.names]);s.kd=np.array([max(.25*k,gains.get(n,[50,5])[1]) for k,n in zip(s.kp,s.names)])
orig=NativeController.__new__(NativeController);orig.s=s;orig.chest_distance=CapsuleBodyDistance(Path(read(A/'assets/om_body_geometry_v3/manifest.json')['asset']),HUMAN)
# Both original references are established on original pre-preparation constructorstate.
support=read(s.cfg['candidate']);support=read(support['support_candidate'])['right_block_cradle'];state=ini['native_state'];from guitar_learning.native.initial_pose_noise_v1 import pose
gp,gr=pose(state['guitar_body_states'][0]);s.references=[]
for n,witness,depth in [('Chest',support['capsule_body']['Chest'],.003),('R_Shoulder',support['upper_arm_witness'],.004)]:
 i=s.human_bodies.index(n);p,r=pose(state['human_body_states'][i]);surface=np.array(witness['guitar_surface_G_m']);normal=np.array(witness['capsule_axis_G_m'])-surface;normal/=np.linalg.norm(normal);point=gp+gr.apply(surface+normal*witness['gap_m']);ix=np.array([j for j,name in enumerate(s.names) if name.startswith(('Torso_','Spine_','Chest_')) or(n=='R_Shoulder' and name.startswith(('R_Thorax_','R_Shoulder_')))])
 s.references.append(dict(body=n,index=i,local_m=r.inv().apply(point-p).tolist(),goal_G_m=(surface+normal*(witness['gap_m']-depth)).tolist(),indices=ix,cap_N=20))
orig.right_reference=s.references[1];p,r=pose(state['human_body_states'][orig.right_reference['index']]);orig.material_W=p+r.apply(orig.right_reference['local_m']);orig.task_goal_W=gp+gr.apply(orig.right_reference['goal_G_m']);spec=read(s.cfg['finite_right_goal_spec']);corr=Rotation.from_quat(spec['R_delta_xyzw']);orig.material_W=corr.apply(orig.material_W)+spec['translation_W_m'];orig.task_goal_W=corr.apply(orig.task_goal_W)+spec['translation_W_m'];orig.palm_W,orig.palm_rotation_W=pose(state['human_body_states'][s.human_bodies.index('RH:palm')]);orig.palm_W=corr.apply(orig.palm_W)+spec['translation_W_m'];orig.palm_rotation_W=corr*orig.palm_rotation_W
orig.load_spec=read(s.cfg['hip_load_bias_spec']);orig.load_bias3=np.array(orig.load_spec['bias_Nm']);orig.rotational_groups=[]
for body,parent in [('R_Elbow','R_Shoulder'),('R_Wrist','R_Elbow')]:
 ix,basis=gpu.groups[body];orig.rotational_groups.append((body,parent,ix.numpy(),basis.numpy()))
orig.goal_correction={'spec_sha256':s.cfg['finite_right_goal_spec_sha256']};ceff,cdiag=orig.effort();print(json.dumps({'max_effort_diff':float(abs(ceff-geff).max()),'diff':{n:dict(cpu=float(ceff[i]),gpu=float(geff[i]),diff=float(geff[i]-ceff[i])) for i,n in enumerate(scene.names) if abs(ceff[i]-geff[i])>1e-5},'right_local_diff':float(abs(np.array(orig.right_reference['local_m'])-gpu.right_local.numpy()).max()),'right_goal_diff':float(abs(orig.task_goal_W-gpu.right_goal.numpy()).max()),'lower_mass_error':cdiag['lower_stable_pd']['mass_matrix_max_error_kg_m2'],'chest_CPU':next(p for p in cdiag['support_points'] if p['body']=='Chest'),'chest_GPU_force':diag['chest_force'][0].tolist()},indent=2))
