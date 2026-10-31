"""Small player-right torso lean with the accepted arm scalar posture retained."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1'
PREV=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
PLAN=ROOT/'stability_adapter_2/BODY_SIDE_LEAN_AXILLA_PLAN_V1.md'
BASE=PREV/'native_v2/front160mm/initial_values.json'
CONFIG=PREV/'search_v6/front160mm/config.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CONFIG);base=read(BASE);state=base['native_initial_state'];names=base['joint_names'];bodies=base['human_body_names'];q0=np.array(base['q_ref_rad']);fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);geometry=read(GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 inputs={str(p):sha(p)for p in [Path(__file__).resolve(),PLAN,BASE,CONFIG,GEOMETRY,ASSET]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs[geometry['asset']]=geometry['asset_sha256'];inputs.update({m['path']:m['sha256']for m in geometry['meshes']})
 out=P/'search_v1';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs);body=c.body;head=np.array([i for i,n in enumerate(names)if n.startswith(('Neck_','Head_'))]);other=np.ones(81,dtype=bool);other[np.r_[body,head]]=False
 right_axis=original['R_Shoulder'][0]-original['L_Shoulder'][0];right_axis[2]=0;right_axis/=np.linalg.norm(right_axis);up=np.array([0.,0.,1.]);axis=np.cross(up,right_axis);rows=[];selected=[]
 for lean in (0,4,8):
  q=q0.copy();targets={n:Rotation.from_rotvec(axis*np.deg2rad(lean*f))*original[n][1]for n,f in zip(('Torso','Spine','Chest'),(.25,.625,1.))};lo=np.maximum(c.lower[body]+1e-6,q0[body]-.12);hi=np.minimum(c.upper[body]-1e-6,q0[body]+.12)
  def body_res(v):
   z=q.copy();z[body]=v;ps=fk(z);return np.r_[np.concatenate([100*(targets[n].inv()*ps[n][1]).as_rotvec()for n in targets]),.01*(v-q0[body])]
  fit=least_squares(body_res,np.clip(q[body],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=100);q[body]=fit.x
  lo=np.maximum(c.lower[head]+1e-6,q0[head]-.15);hi=np.minimum(c.upper[head]-1e-6,q0[head]+.15)
  def head_res(v):
   z=q.copy();z[head]=v;return np.r_[100*(original['Head'][1].inv()*fk(z)['Head'][1]).as_rotvec(),.01*(v-q0[head])]
  fit=least_squares(head_res,np.clip(q[head],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=100);q[head]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q);caps={n:distance.measure(ps,n,gp,gr)for n in distance.capsules if n in ps};prox=distance.measure(ps,'R_Shoulder',gp,gr,.65);witness=caps['R_Elbow'];normal=np.array(witness['capsule_axis_G_m'])-witness['guitar_surface_G_m'];normal/=np.linalg.norm(normal)
  audit=source_audit(source_scene(state_from_fk(state,bodies,q,fk),bodies,geometry['asset']),parents);d=ps['R_Elbow'][0]-ps['R_Shoulder'][0];w=ps['R_Elbow'][0]-ps['R_Wrist'][0];rv=(ps['Chest'][1]*original['Chest'][1].inv()).as_rotvec();shape={'elbow_outside_shoulder_m':float(d@right_axis),'elbow_below_shoulder_m':float(-d[2]),'wrist_inward_from_elbow_m':float(w@right_axis)};body_errors={n:float(np.rad2deg((targets[n].inv()*ps[n][1]).magnitude()))for n in targets};label='right%ddeg'%lean
  row={'label':label,'joint_angles_rad':q.tolist(),'requested_chest_player_right_lean_deg':lean,'actual_chest_rotation_vector_W_deg':np.rad2deg(rv).tolist(),'actual_chest_player_right_rotation_projection_deg':float(np.rad2deg(rv@axis)),'right_axis_W':right_axis.tolist(),'right_lean_rotation_axis_W':axis.tolist(),'body_goal_orientation_errors_deg':body_errors,'head_orientation_error_deg':float(np.rad2deg((original['Head'][1].inv()*ps['Head'][1]).magnitude())),'body_max_initial_scalar_change_deg':float(np.rad2deg(abs(q[body]-q0[body])).max()),'head_max_initial_scalar_change_deg':float(np.rad2deg(abs(q[head]-q0[head])).max()),'other66_initial_scalar_same':bool(np.array_equal(q[other],q0[other])),'guitar_initial_same':True,'posture_shape':shape,'capsule_body':caps,'proximal_upper_arm65_witness':prox,'support_witness':witness,'no_strap_upper_arm_proposal':{'proximal_support':witness},'source_normal_W':gr.apply(normal).tolist(),'source_audit':audit,'body_scalar_q_rad':{names[i]:float(q[i])for i in body},'head_scalar_q_rad':{names[i]:float(q[i])for i in head}}
  row['accepted_for_native']=bool(lean>0 and audit['source_clear']and min(m['gap_m']for m in caps.values())>=.0001 and witness['gap_m']<.04 and shape['elbow_outside_shoulder_m']>.08 and shape['wrist_inward_from_elbow_m']>.02 and shape['elbow_below_shoulder_m']>.02 and row['other66_initial_scalar_same']and max(body_errors.values())<.2 and row['head_orientation_error_deg']<.5 and np.all(q>=c.lower-1e-7)and np.all(q<=c.upper+1e-7));rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',row['accepted_for_native'],'sourceclear',audit['source_clear'],'shoulder/prox/forearm mm',[caps['R_Shoulder']['gap_m']*1000,prox['gap_m']*1000,witness['gap_m']*1000],'shape',shape,flush=True)
  if row['accepted_for_native']:
   folder=out/label;folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':row['no_strap_upper_arm_proposal'],'body_side_lean_axilla':row});cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json')})
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'source posture and gap comparison only; not native contact/clearance/stability'})
if __name__=='__main__':main()
