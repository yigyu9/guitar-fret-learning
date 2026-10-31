"""Find lower starts from analytic thigh clearance and guitar-relative palm IK."""
from pathlib import Path
import numpy as np
from scipy.optimize import brentq,least_squares
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance

P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1'
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/native_v1/lean18_back30/initial_values.json'
CONFIG=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/search_v4/lean18_back30/config.json'
GEOMETRY=ROOT/'stability_adapter_2/assets/om_body_geometry_v3/manifest.json'
PLAN=ROOT/'stability_adapter_2/OM_THIGH_HEIGHT_INITIAL_PLAN_V2.md'

def main():
 from .environment_contract_v1 import EnvironmentContract
 from .underneck_initial_search import source_scene as transformed_scene
 c=EnvironmentContract(CONFIG);base=read(BASE);geometry=read(GEOMETRY);state=base['native_initial_state'];names=base['joint_names'];bodies=base['human_body_names'];q0=np.array(base['q_ref_rad'])
 fk,parents=calibrated_upper_fk(names,bodies,state,q0);original=fk(q0);gp0,gr=pose(state['guitar_body_states'][0]);distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 inputs={str(p):sha(p) for p in [BASE,CONFIG,GEOMETRY,ASSET,PLAN,Path(__file__).resolve()]};inputs.update(c.inputs);inputs.update({str(p):sha(p) for p in Path(__file__).parent.glob('*.py')});inputs.update(geometry['input_sha256']);inputs[geometry['asset']]=geometry['asset_sha256']
 for m in geometry['meshes']:inputs[m['path']]=m['sha256']
 out=P/'search_v2';out.mkdir(exist_ok=False);save(out/'attempt.json',{'input_sha256':inputs,'source_only':True,'native_runs':0,'height_targets_source_gap_m':[.008,.003]})
 before=distance.measure(original,'R_Hip',gp0,gr);rows=[];selected=[]
 print('original_R_Hip_gap_mm',before['gap_m']*1000,flush=True)
 for gap in [.008,.003]:
  def height_error(down):return min(distance.measure(original,n,gp0+[0,0,-down],gr)['gap_m'] for n in ['L_Hip','R_Hip'])-gap
  down=brentq(height_error,0.,.18,xtol=1e-9);delta=np.array([0,0,-down]);gp=gp0+delta;q=q0.copy();fits={}
  for side in ['L','R']:
   idx=np.array([i for i,n in enumerate(names) if n.startswith(tuple(side+'_'+part for part in ['Thorax','Shoulder','Elbow','Wrist']))]);palm=side+'H:palm';targetp=original[palm][0]+delta;targetr=original[palm][1]
   lo=np.maximum(c.lower[idx],q0[idx]-.6);hi=np.minimum(c.upper[idx],q0[idx]+.6)
   def residual(v):
    z=q.copy();z[idx]=v;p,r=fk(z)[palm]
    return np.r_[1000*(p-targetp),100*(targetr.inv()*r).as_rotvec(),.01*(v-q0[idx])]
   fit=least_squares(residual,np.clip(q0[idx],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=200);q[idx]=fit.x
  q=q.astype(np.float32).astype(float);poses=fk(q)
  for side in ['L','R']:
   palm=side+'H:palm';p,r=poses[palm];fits[palm]={'position_error_m':float(np.linalg.norm(p-(original[palm][0]+delta))),'orientation_error_deg':float(np.rad2deg((original[palm][1].inv()*r).magnitude()))}
  capsules={n:distance.measure(poses,n,gp,gr) for n in distance.capsules if n in poses}
  _,predicted=transformed_scene(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents)
  label='thigh_gap%dmm'%round(gap*1000);row={'label':label,'target_min_Hip_gap_m':gap,'guitar_delta_W_m':delta.tolist(),'palm_fit':fits,'capsule_body_gaps':capsules,'source_audit':audit,'max_arm_scalar_delta_rad':float(abs(q-q0).max())}
  row['accepted_for_native']=bool(audit['source_clear'] and min(x['gap_m'] for x in capsules.values())>=.0002 and abs(min(capsules[n]['gap_m'] for n in ['L_Hip','R_Hip'])-gap)<.0002 and all(x['position_error_m']<.002 and x['orientation_error_deg']<1 for x in fits.values()))
  rows.append(row);save(out/(label+'_audit.json'),row);print(label,'down_mm',down*1000,'accepted',row['accepted_for_native'],'min_capsule_gap_mm',min(x['gap_m'] for x in capsules.values())*1000,flush=True)
  if row['accepted_for_native']:
   folder=out/label;folder.mkdir();candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()} for n,(p,r) in poses.items()},'om_thigh_height_proposal':row}
   save(folder/'candidate.json',candidate);cfg=read(CONFIG);cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg);selected.append({'label':label,'config':str(folder/'config.json')})
 assert all(sha(p)==h for p,h in inputs.items())
 save(out/'search.json',{'input_sha256':inputs,'before_R_Hip':before,'height_rule':'minimum left/right Hip capsule–OM source gap','rows':rows,'selected':selected,'native_runs':0,'scope':'source geometry and initial IK, not cooked PhysX clearance'})

if __name__=='__main__':main()
