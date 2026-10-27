"""Bounded right-arm posture from a qualitative photographic reference."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
PLAN=ROOT/'stability_adapter_2/NATURAL_RIGHT_ARM_REFERENCE_PLAN_V3.md'
BASE=OLD/'native_v10/three_support_relative_effort_microgap/initial_values.json'
CONFIG=OLD/'right_effort_config_v1.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
PHOTO=Path('/home/ajou/.codex/attachments/6b4c873f-1066-4883-ae58-9a85977bce8f/1.jpeg')
def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CONFIG);base=read(BASE);state=base['native_initial_state'];q0=np.array(base['q_ref_rad']);names=base['joint_names'];bodies=base['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);geometry=read(GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 inputs={str(p):sha(p)for p in [Path(__file__).resolve(),PLAN,BASE,CONFIG,GEOMETRY,ASSET,PHOTO]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs[geometry['asset']]=geometry['asset_sha256'];inputs.update({m['path']:m['sha256']for m in geometry['meshes']})
 out=P/'search_v3';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs);right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);lo=c.lower[right].copy();hi=c.upper[right].copy()
 for j,i in enumerate(right):
  name=names[i];width=.07 if name.startswith('R_Thorax')else .55 if name.startswith('R_Shoulder')else .8 if name=='R_Elbow_y'else .25
  lo[j]=max(lo[j]+1e-4,q0[i]-width);hi[j]=min(hi[j]-1e-4,q0[i]+width)
  if name.startswith('R_Wrist'):lo[j]=max(c.lower[i]+1e-4,-.35);hi[j]=min(c.upper[i]-1e-4,.35)
  if name=='R_Elbow_y':lo[j]=max(lo[j],.5);hi[j]=min(hi[j],2.3)
 right_axis=original['R_Shoulder'][0]-original['L_Shoulder'][0];right_axis[2]=0;right_axis/=np.linalg.norm(right_axis);up=np.array([0.,0,1.]);forward=np.cross(up,right_axis);rows=[];selected=[]
 for normal_offset in (.136,.16):
  hand_target=gp+gr.apply([-.0342,-.3637,normal_offset]);direction=.20*right_axis+.10*forward-.13*up;direction/=np.linalg.norm(direction);length=np.linalg.norm(original['R_Elbow'][0]-original['R_Shoulder'][0]);elbow_target=original['R_Shoulder'][0]+length*direction
  def seed_res(v):
   q=q0.copy();q[right]=v;ps=fk(q);return np.r_[80*(ps['R_Elbow'][0]-elbow_target),120*(ps['RH:palm'][0]-hand_target),.3*(v-q0[right])]
  seed=least_squares(seed_res,np.clip(q0[right],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=100)
  def res(v):
   q=q0.copy();q[right]=v[:12];current_gp=gp+v[12:];ps=fk(q);m=distance.measure(ps,'R_Elbow',current_gp,gr);shoulder=distance.measure(ps,'R_Shoulder',current_gp,gr);hip=min(distance.measure(ps,n,current_gp,gr)['gap_m']for n in ['R_Hip','L_Hip']);surf=np.array(m['guitar_surface_G_m']);normal=np.array(m['capsule_axis_G_m'])-surf;normal/=np.linalg.norm(normal);moving_hand=current_gp+gr.apply([-.0342,-.3637,normal_offset])
   return np.r_[40*(ps['R_Elbow'][0]-elbow_target),140*(ps['RH:palm'][0]-moving_hand),10000*min(shoulder['gap_m']-.0005,0),10000*min(m['gap_m']-.0005,0),1000*(m['gap_m']-.001),1500*(hip-.003),10*(normal-[0,0,1]),.6*(v[:12]-q0[right]),3*v[12:]]
  lo_fit=np.r_[lo,[-.025,0,-.07]];hi_fit=np.r_[hi,[.025,.09,.02]]
  fit=least_squares(res,np.r_[seed.x,[0,.04,-.02]],bounds=(lo_fit,hi_fit),max_nfev=160,diff_step=1e-4);q=q0.copy();q[right]=fit.x[:12];q=q.astype(np.float32).astype(float);current_gp=gp+fit.x[12:];ps=fk(q);caps={n:distance.measure(ps,n,current_gp,gr)for n in distance.capsules if n in ps};witness=caps['R_Elbow'];normal=np.array(witness['capsule_axis_G_m'])-witness['guitar_surface_G_m'];normal/=np.linalg.norm(normal);from .underneck_initial_search import source_scene as move_guitar
  _,predicted=move_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},current_gp,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
  elbow_delta=ps['R_Elbow'][0]-ps['R_Shoulder'][0];wrist_delta=ps['R_Wrist'][0]-ps['R_Elbow'][0];label='front%dmm'%round(normal_offset*1000)
  shape={'elbow_outside_shoulder_m':float(elbow_delta@right_axis),'elbow_below_shoulder_m':float(-elbow_delta@up),'wrist_inward_from_elbow_m':float(-wrist_delta@right_axis),'hand_target_error_m':float(np.linalg.norm(ps['RH:palm'][0]-(current_gp+gr.apply([-.0342,-.3637,normal_offset]))))}
  row={'label':label,'guitar_initial_delta_W_m':fit.x[12:].tolist(),'support_body':'R_Elbow','support_witness':witness,'no_strap_upper_arm_proposal':{'proximal_support':witness},'source_normal_W':gr.apply(normal).tolist(),'capsule_body':caps,'source_audit':audit,'posture_shape':shape,'right_scalar_q_rad':dict(zip([names[i]for i in right],q[right].tolist())),'bounds_rad':{'lower':lo.tolist(),'upper':hi.tolist()},'initial_other69_same':bool(np.array_equal(np.delete(q,right),np.delete(q0,right))),'photo_scope':'qualitative single-view reference; not reconstructed person joint angles'}
  row['accepted_for_native']=bool(audit['source_clear']and min(m['gap_m']for m in caps.values())>=.0001 and witness['gap_m']<.015 and gr.apply(normal)[1]>.55 and shape['elbow_outside_shoulder_m']>=.08 and shape['elbow_below_shoulder_m']>=.08 and shape['wrist_inward_from_elbow_m']>=.04 and shape['hand_target_error_m']<.05 and row['initial_other69_same']and np.all(q[right]>=lo-1e-7)and np.all(q[right]<=hi+1e-7));rows.append(row);save(out/(label+'_audit.json'),row);print(label,row['accepted_for_native'],shape,'gap',witness['gap_m'],'normalW',row['source_normal_W'],flush=True)
  if row['accepted_for_native']:
   folder=out/label;folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':current_gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':{'proximal_support':witness},'natural_right_arm':row});cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json')})
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':rows,'native_runs':0,'scope':'bounded source posture, not native contact/stability or exact photo reconstruction'})
if __name__=='__main__':main()
