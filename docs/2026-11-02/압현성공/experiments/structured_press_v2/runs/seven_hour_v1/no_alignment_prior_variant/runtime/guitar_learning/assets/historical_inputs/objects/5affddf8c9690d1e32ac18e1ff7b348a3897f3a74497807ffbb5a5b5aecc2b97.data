"""Fit the shoulder-side upper-arm to the guitar's upper rounded outline."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as transform_guitar
A=ROOT/'stability_adapter_2'
D=ROOT/'docs/2026-10-19/stability_adapter_2'
P=D/'results/upper_bout_axilla_v1'
BASE=D/'results/natural_right_arm_v1/native_v2/front160mm/initial_values.json'
CFG=D/'results/body_side_lean_axilla_v1/search_v5/right4_close_support/config.json'
PLAN=A/'UPPER_BOUT_AXILLA_PLAN_V4.md'
FOREARM=D/'results/body_side_lean_axilla_v1/native_v2/right4_close_support_upper_press/media/effort_configuration.json'
def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CFG);base=read(BASE);cfg=read(CFG);seed=read(cfg['initial_candidate']);names=base['joint_names'];bodies=base['human_body_names'];state=base['native_initial_state'];qbase=np.array(base['q_ref_rad']);qs=np.array(seed['joint_angles_rad']);gp=np.array(seed['position_W_m']);gr=Rotation.from_quat(seed['quaternion_xyzw']);fk,parents=calibrated_upper_fk(names,bodies,state,qbase);original=fk(qbase);startposes=fk(qs);geometry=read(A/'assets/om_body_geometry_v3/manifest.json');distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 inputs={str(p):sha(p)for p in [Path(__file__).resolve(),PLAN,BASE,CFG,Path(cfg['initial_candidate']),A/'assets/om_body_geometry_v3/manifest.json',ASSET]};inputs[str(FOREARM)]=sha(FOREARM);inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in A.glob('*.py')});inputs.update({m['path']:m['sha256']for m in geometry['meshes']});inputs[geometry['asset']]=sha(geometry['asset']);out=P/'search_v4';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs)
 body=c.body;head=np.array([i for i,n in enumerate(names)if n.startswith(('Neck_','Head_'))]);right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow'))]);unchanged=np.ones(81,dtype=bool);unchanged[np.r_[body,head,right]]=False
 rightaxis=original['R_Shoulder'][0]-original['L_Shoulder'][0];rightaxis[2]=0;rightaxis/=np.linalg.norm(rightaxis);axis=np.cross([0,0,1],rightaxis);handp,handr=startposes['RH:palm'];ref_local=np.array(read(FOREARM)['motor_reference_local_m']);ref_goal=startposes['R_Elbow'][0]+startposes['R_Elbow'][1].apply(ref_local);forwardaxis=np.cross([0,0,1],gr.apply([0,0,1]));rows=[];selected=[]
 for lean in (4,):
  q=qs.copy();targets={n:Rotation.from_rotvec((axis*np.deg2rad(lean)+forwardaxis*np.deg2rad(6))*f)*original[n][1]for n,f in zip(('Torso','Spine','Chest'),(.25,.625,1.))};lo=np.maximum(c.lower[body]+1e-6,qbase[body]-.12);hi=np.minimum(c.upper[body]-1e-6,qbase[body]+.12)
  def body_res(v):
   z=q.copy();z[body]=v;ps=fk(z);return np.r_[np.concatenate([100*(targets[n].inv()*ps[n][1]).as_rotvec()for n in targets]),.01*(v-qbase[body])]
  fit=least_squares(body_res,np.clip(q[body],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=100);q[body]=fit.x;lo=np.maximum(c.lower[head]+1e-6,qbase[head]-.15);hi=np.minimum(c.upper[head]-1e-6,qbase[head]+.15)
  def head_res(v):
   z=q.copy();z[head]=v;return np.r_[100*(original['Head'][1].inv()*fk(z)['Head'][1]).as_rotvec(),.01*(v-qbase[head])]
  fit=least_squares(head_res,np.clip(q[head],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=100);q[head]=fit.x;lo=c.lower[right]+1e-4;hi=c.upper[right]-1e-4
  for j,i in enumerate(right):
   width=.1 if names[i].startswith('R_Thorax')else .45 if names[i]=='R_Elbow_y'else .35;lo[j]=max(lo[j],qbase[i]-width);hi[j]=min(hi[j],qbase[i]+width)
  def residual(v):
   z=q.copy();z[right]=v;ps=fk(z);full=distance.measure(ps,'R_Shoulder',gp,gr);prox=distance.measure(ps,'R_Shoulder',gp,gr,.35);forearm=distance.measure(ps,'R_Elbow',gp,gr);chest=distance.measure(ps,'Chest',gp,gr);d=ps['R_Elbow'][0]-ps['R_Shoulder'][0];w=ps['R_Elbow'][0]-ps['R_Wrist'][0]
   return np.r_[2000*(prox['gap_m']-.001),20000*min(full['gap_m']-.0002,0),10000*min(forearm['gap_m']-.0001,0),1000*(ps['R_Elbow'][0]+ps['R_Elbow'][1].apply(ref_local)-ref_goal),500*(prox['guitar_surface_G_m'][2]+.067),10000*min(chest['gap_m']-.0001,0),1000*max(.022+d[2],0),1000*max(.19-d@rightaxis,0),1000*max(.035-w@rightaxis,0),100*(ps['RH:palm'][0]-handp),5*(handr.inv()*ps['RH:palm'][1]).as_rotvec(),.8*(v-qs[right])]
  fit=least_squares(residual,np.clip(q[right],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=180,diff_step=1e-4);q[right]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q);caps={n:distance.measure(ps,n,gp,gr)for n in distance.capsules if n in ps};prox=distance.measure(ps,'R_Shoulder',gp,gr,.35);normal=np.array(prox['capsule_axis_G_m'])-prox['guitar_surface_G_m'];normal/=np.linalg.norm(normal);surface=np.array(prox['guitar_surface_G_m']);_,predicted=transform_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents);d=ps['R_Elbow'][0]-ps['R_Shoulder'][0];w=ps['R_Elbow'][0]-ps['R_Wrist'][0];shape={'elbow_outside_shoulder_m':float(d@rightaxis),'elbow_below_shoulder_m':float(-d[2]),'wrist_inward_from_elbow_m':float(w@rightaxis)};bodyerror=max(float(np.rad2deg((targets[n].inv()*ps[n][1]).magnitude()))for n in targets);headerror=float(np.rad2deg((original['Head'][1].inv()*ps['Head'][1]).magnitude()));handerror=float(np.linalg.norm(ps['RH:palm'][0]-handp));forearm_error=float(np.linalg.norm(ps['R_Elbow'][0]+ps['R_Elbow'][1].apply(ref_local)-ref_goal));label='right%d_forward6_upper35'%lean
  accepted=bool(audit['source_clear']and min(v['gap_m']for v in caps.values())>=.00005 and .00005<=prox['gap_m']<.006 and forearm_error<.003 and -.085<=surface[2]<=-.025 and surface[0]<-.17 and -.55<=surface[1]<=-.43 and gr.apply(normal)[2]>.35 and shape['elbow_outside_shoulder_m']>=.18 and shape['elbow_below_shoulder_m']>=.015 and shape['wrist_inward_from_elbow_m']>=.03 and handerror<.04 and bodyerror<.2 and headerror<.5 and np.array_equal(q[unchanged],qs[unchanged])and np.all(q>=c.lower-1e-7)and np.all(q<=c.upper+1e-7))
  row={'label':label,'accepted_for_native':accepted,'requested_chest_player_right_lean_deg':lean,'requested_chest_forward_bend_deg':6,'forearm_original_motor_point_error_m':forearm_error,'forearm_reference_scope':'previous human motor reference retained; current geometric forearm gap is in capsule_body','body_goal_max_error_deg':bodyerror,'head_orientation_error_deg':headerror,'guitar_initial_same_as_previous':True,'unchanged_initial_scalars_exact':bool(np.array_equal(q[unchanged],qs[unchanged])),'proximal_fraction_limit':.35,'proximal_upper_arm35_witness':prox,'proximal_upper_arm65_witness':prox,'legacy_key_note':'65 key retained only for existing runner compatibility; actual source segment0..35%','source_proximal_normal_W':gr.apply(normal).tolist(),'capsule_body':caps,'source_audit':audit,'posture_shape':shape,'hand_position_error_m':handerror,'hand_rotation_change_deg':float(np.rad2deg((handr.inv()*ps['RH:palm'][1]).magnitude())),'right9_q_rad':{names[i]:float(q[i])for i in right},'bounds_rad':{'lower':lo.tolist(),'upper':hi.tolist()},'joint_angles_rad':q.tolist()};rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',accepted,'sourceclear',audit['source_clear'],'prox35/full/forearm mm',[prox['gap_m']*1000,caps['R_Shoulder']['gap_m']*1000,caps['R_Elbow']['gap_m']*1000],'shape',shape,'handerror',handerror,flush=True)
  if accepted:
   folder=out/label;folder.mkdir();candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':seed['no_strap_upper_arm_proposal'],'body_side_lean_axilla':row};save(folder/'candidate.json',candidate);newcfg={**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json')};save(folder/'config.json',newcfg);selected.append({'label':label,'config':str(folder/'config.json')})
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'native_runs':0,'scope':'source fit of shoulder-side35% to upper rounded contour; not cooked clearance/contact/stability certification'})
if __name__=='__main__':main()
