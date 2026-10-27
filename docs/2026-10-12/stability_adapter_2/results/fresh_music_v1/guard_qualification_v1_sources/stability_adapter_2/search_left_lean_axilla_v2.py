"""Small coupled initial placement after source-confirmed player-left tilt."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as transform_guitar
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1'
PREV=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
BASE=PREV/'native_v2/front160mm/initial_values.json'
CONFIG=P/'search_v1/left4deg/config.json'
SEED=P/'search_v1/left4deg/candidate.json'
PLAN=ROOT/'stability_adapter_2/LEFT_LEAN_AXILLA_PLAN_V2.md'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CONFIG);base=read(BASE);state=base['native_initial_state'];names=base['joint_names'];bodies=base['human_body_names'];qbase=np.array(base['q_ref_rad']);q0=np.array(read(SEED)['joint_angles_rad']);fk,parents=calibrated_upper_fk(names,bodies,state,qbase);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);geometry=read(GEOMETRY);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 inputs={str(p):sha(p)for p in [Path(__file__).resolve(),BASE,CONFIG,SEED,PLAN,GEOMETRY,ASSET]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs[geometry['asset']]=geometry['asset_sha256'];inputs.update({m['path']:m['sha256']for m in geometry['meshes']})
 out=P/'search_v2';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs);right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow'))]);lo=c.lower[right]+1e-4;hi=c.upper[right]-1e-4
 for j,i in enumerate(right):
  width=.05 if names[i].startswith('R_Thorax')else .2;lo[j]=max(lo[j],qbase[i]-width);hi[j]=min(hi[j],qbase[i]+width)
 right_axis=original['R_Shoulder'][0]-original['L_Shoulder'][0];right_axis[2]=0;right_axis/=np.linalg.norm(right_axis);hand_g=gr.inv().apply(fk(qbase)['RH:palm'][0]-gp);hand_rot=fk(qbase)['RH:palm'][1];rows=[];selected=[]
 def residual(v):
  q=q0.copy();q[right]=v[:9];g=gp+v[9:];ps=fk(q);full=distance.measure(ps,'R_Shoulder',g,gr);prox=distance.measure(ps,'R_Shoulder',g,gr,.65);forearm=distance.measure(ps,'R_Elbow',g,gr);hips=min(distance.measure(ps,n,g,gr)['gap_m']for n in ('R_Hip','L_Hip'));chest=distance.measure(ps,'Chest',g,gr);d=ps['R_Elbow'][0]-ps['R_Shoulder'][0];w=ps['R_Elbow'][0]-ps['R_Wrist'][0]
  return np.r_[1000*(prox['gap_m']-.002),10000*min(full['gap_m']-.0005,0),10000*min(forearm['gap_m']-.0005,0),1000*(forearm['gap_m']-.002),1000*(hips-.002),10000*min(chest['gap_m']-.0005,0),1000*max(.035+d[2],0),1000*max(.19-d@right_axis,0),1000*max(.035-w@right_axis,0),100*(ps['RH:palm'][0]-(g+gr.apply(hand_g))),5*(hand_rot.inv()*ps['RH:palm'][1]).as_rotvec(),.8*(v[:9]-qbase[right]),3*v[9:]]
 lower=np.r_[lo,[-.03,-.08,-.02]];upper=np.r_[hi,[.03,.02,.02]]
 for label,delta in [('left4_nearbody',[0,-.02,0])]:
  fit=least_squares(residual,np.r_[np.clip(q0[right],lo+1e-8,hi-1e-8),delta],bounds=(lower,upper),max_nfev=300,diff_step=1e-4);q=q0.copy();q[right]=fit.x[:9];q=q.astype(np.float32).astype(float);g=gp+fit.x[9:];ps=fk(q);caps={n:distance.measure(ps,n,g,gr)for n in distance.capsules if n in ps};prox=distance.measure(ps,'R_Shoulder',g,gr,.65);normal=np.array(prox['capsule_axis_G_m'])-prox['guitar_surface_G_m'];normal/=np.linalg.norm(normal);_,predicted=transform_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},g,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents);d=ps['R_Elbow'][0]-ps['R_Shoulder'][0];w=ps['R_Elbow'][0]-ps['R_Wrist'][0];shape={'elbow_outside_shoulder_m':float(d@right_axis),'elbow_below_shoulder_m':float(-d[2]),'wrist_inward_from_elbow_m':float(w@right_axis)};unchanged=np.ones(81,dtype=bool);unchanged[right]=False
  row={'label':label,'requested_chest_player_left_lean_deg':4,'guitar_initial_delta_W_m':fit.x[9:].tolist(),'source_audit':audit,'capsule_body':caps,'proximal_upper_arm65_witness':prox,'source_proximal_normal_W':gr.apply(normal).tolist(),'support_witness':caps['R_Elbow'],'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']},'posture_shape':shape,'other72_initial_same_as_left4':bool(np.array_equal(q[unchanged],q0[unchanged])),'right9_q_rad':{names[i]:float(q[i])for i in right},'bounds_rad':{'lower':lo.tolist(),'upper':hi.tolist()},'body_head_same_as_left4':True,'hand_position_error_m':float(np.linalg.norm(ps['RH:palm'][0]-(g+gr.apply(hand_g)))),'hand_rotation_change_deg':float(np.rad2deg((hand_rot.inv()*ps['RH:palm'][1]).magnitude()))}
  row['accepted_for_native']=bool(audit['source_clear']and min(m['gap_m']for m in caps.values())>=.0002 and .0002<prox['gap_m']<.006 and .0002<min(caps[n]['gap_m']for n in ('R_Hip','L_Hip'))<.008 and gr.apply(normal)[2]>.35 and shape['elbow_outside_shoulder_m']>=.18 and shape['elbow_below_shoulder_m']>=.03 and shape['wrist_inward_from_elbow_m']>=.03 and row['other72_initial_same_as_left4']and row['hand_position_error_m']<.04 and np.all(q[right]>=lo-1e-7)and np.all(q[right]<=hi+1e-7));rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',row['accepted_for_native'],'clear',audit['source_clear'],'prox/forearm/hip mm',[prox['gap_m']*1000,caps['R_Elbow']['gap_m']*1000,min(caps[n]['gap_m']for n in ('R_Hip','L_Hip'))*1000],'gdelta',fit.x[9:].tolist(),'shape',shape,'handerror',row['hand_position_error_m'],flush=True)
  if row['accepted_for_native']:
   folder=out/label;folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':g.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':row['no_strap_upper_arm_proposal'],'left_lean_axilla':row});cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json')})
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':rows,'native_runs':0,'scope':'bounded coupled source initial placement; not native clearance/contact/stability'})
if __name__=='__main__':main()
