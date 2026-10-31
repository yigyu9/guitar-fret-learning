"""Left-away starts and source capsule upper-arm support, no physics calls."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/native_v1/thigh_gap3mm/initial_values.json'
CONFIG=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/search_v2/thigh_gap3mm/config.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
PLAN=ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V5.md'

def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CONFIG);base=read(BASE);geometry=read(GEOMETRY);state=base['native_initial_state'];q0=np.array(base['q_ref_rad']);names=base['joint_names'];bodies=base['human_body_names'];fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp,gr=pose(state['guitar_body_states'][0]);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 inputs={str(p):sha(p)for p in [BASE,CONFIG,GEOMETRY,PLAN,ASSET,Path(__file__).resolve()]};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in Path(__file__).parent.glob('*.py')});inputs.update(geometry['input_sha256']);inputs[geometry['asset']]=geometry['asset_sha256']
 for m in geometry['meshes']:inputs[m['path']]=m['sha256']
 out=P/'search_v4';out.mkdir(exist_ok=False);save(out/'attempt.json',{'input_sha256':inputs,'native_runs':0})
 left=np.array([i for i,n in enumerate(names)if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]);right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);qleft=q0.copy();targetp=original['LH:palm'][0]+[0,-.30,-.10];targetr=original['LH:palm'][1]
 lo=np.maximum(c.lower[left],q0[left]-.8);hi=np.minimum(c.upper[left],q0[left]+.8)
 def left_res(v):
  z=q0.copy();z[left]=v;p,r=fk(z)['LH:palm'];return np.r_[1000*(p-targetp),100*(targetr.inv()*r).as_rotvec(),.01*(v-q0[left])]
 fit=least_squares(left_res,np.clip(q0[left],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=200);qleft[left]=fit.x;rows=[];selected=[]
 def keep(label,q,needs_support):
  q=q.astype(np.float32).astype(float);poses=fk(q);capsules={n:distance.measure(poses,n,gp,gr)for n in distance.capsules if n in poses};prox=distance.measure(poses,'R_Shoulder',gp,gr,.65);audit=source_audit(source_scene(state_from_fk(state,bodies,q,fk),bodies,geometry['asset']),parents);lp,lr=poses['LH:palm'];point=prox['guitar_surface_G_m']
  row={'label':label,'support_requested':needs_support,'left_palm_target_W_m':targetp.tolist(),'left_palm_position_error_m':float(np.linalg.norm(lp-targetp)),'left_palm_orientation_error_deg':float(np.rad2deg((targetr.inv()*lr).magnitude())),'max_left_arm_delta_rad':float(abs(q[left]-q0[left]).max()),'max_right_arm_delta_rad':float(abs(q[right]-q0[right]).max()),'right_palm_position_change_m':float(np.linalg.norm(poses['RH:palm'][0]-original['RH:palm'][0])),'proximal_support':prox,'capsule_body':capsules,'source_audit':audit}
  row['accepted_for_native']=bool(audit['source_clear'] and min(v['gap_m']for v in capsules.values())>=.0002 and row['left_palm_position_error_m']<.002 and row['left_palm_orientation_error_deg']<1 and (not needs_support or (.0002<=prox['gap_m']<.003 and point[0]<-.1 and -.55<=point[1]<=-.25 and row['right_palm_position_change_m']<.1)))
  rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',row['accepted_for_native'],'prox_gap_mm',prox['gap_m']*1000,'fraction',prox['segment_fraction'],'right_palm_delta_mm',row['right_palm_position_change_m']*1000,flush=True)
  if row['accepted_for_native']:
   folder=out/label;folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in poses.items()},'no_strap_upper_arm_proposal':row});cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'),strap_enabled=False);save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json')})
 keep('left_away_reference',qleft,False)
 lo=np.maximum(c.lower[right],q0[right]-.8);hi=np.minimum(c.upper[right],q0[right]+.8)
 def right_res(v):
  z=qleft.copy();z[right]=v;poses=fk(z);full=distance.measure(poses,'R_Shoulder',gp,gr);prox=distance.measure(poses,'R_Shoulder',gp,gr,.65);point=prox['guitar_surface_G_m'];p,r=poses['RH:palm']
  return np.r_[1000*(prox['gap_m']-.001),500*max(.0005-full['gap_m'],0),200*max(point[0]+.1,0),200*max(-.55-point[1],0),200*max(point[1]+.25,0),20*(p-original['RH:palm'][0]),2*(original['RH:palm'][1].inv()*r).as_rotvec(),.1*(v-q0[right])]
 fit=least_squares(right_res,np.clip(q0[right],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=200,diff_step=1e-4);q=qleft.copy();q[right]=fit.x;keep('upper_arm_close',q,True)
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':selected,'rows':rows,'native_runs':0,'scope':'source geometry, no cooked clearance or physical support certification'})

if __name__=='__main__':main()
