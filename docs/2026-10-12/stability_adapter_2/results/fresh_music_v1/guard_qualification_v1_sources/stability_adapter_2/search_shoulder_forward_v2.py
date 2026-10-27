"""Fit only the right shoulder scalars to small forward elbow displacements."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as transform_guitar
A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2';P=D/'results/shoulder_forward_v1'
BASE=D/'results/natural_right_arm_v1/native_v2/front160mm/initial_values.json'
CFG=D/'results/upright_neckward_pose_v1/search_v2/bend-6_neckyaw19/config.json'
PLAN=A/'SHOULDER_FORWARD_PLAN_V2.md'
def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CFG);cfg=read(CFG);seed=read(cfg['initial_candidate']);base=read(BASE);names=base['joint_names'];bodies=base['human_body_names'];state=base['native_initial_state'];q0=np.array(seed['joint_angles_rad']);fk,parents=calibrated_upper_fk(names,bodies,state,np.array(base['q_ref_rad']));start=fk(q0);gp=np.array(seed['position_W_m']);gr=Rotation.from_quat(seed['quaternion_xyzw']);forward=gr.apply([0,0,1]);forward[2]=0;forward/=np.linalg.norm(forward);geometry=read(A/'assets/om_body_geometry_v3/manifest.json');distance=CapsuleBodyDistance(geometry['asset'],ASSET)
 shoulder=np.array([i for i,n in enumerate(names)if n.startswith('R_Shoulder_')]);assert len(shoulder)==3;frozen=np.ones(81,dtype=bool);frozen[shoulder]=False
 lo=np.maximum(c.lower[shoulder]+1e-6,q0[shoulder]-.12);hi=np.minimum(c.upper[shoulder]-1e-6,q0[shoulder]+.12)
 paths=[Path(__file__).resolve(),PLAN,BASE,CFG,Path(cfg['initial_candidate']),ASSET,A/'assets/om_body_geometry_v3/manifest.json',Path(geometry['asset'])]+list(A.glob('*.py'))+[Path(m['path'])for m in geometry['meshes']];inputs={str(p):sha(p)for p in paths};inputs.update(c.inputs);out=P/'search_v2';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs);rows=[];selected=[]
 for mm in (10,20):
  target=start['R_Elbow'][0]+forward*(mm/1000)
  def residual(v):
   q=q0.copy();q[shoulder]=v;ps=fk(q);full=distance.measure(ps,'R_Shoulder',gp,gr);prox=distance.measure(ps,'R_Shoulder',gp,gr,.3);arm=distance.measure(ps,'R_Elbow',gp,gr)
   return np.r_[800*((ps['R_Elbow'][0]-start['R_Elbow'][0])@forward-mm/1000),200*((ps['R_Elbow'][0]-start['R_Elbow'][0])-forward*((ps['R_Elbow'][0]-start['R_Elbow'][0])@forward)),20000*min(full['gap_m']-.00015,0),1000*max(prox['gap_m']-.0028,0),10000*min(arm['gap_m']-.012,0),.2*(v-q0[shoulder])]
  fit=least_squares(residual,np.clip(q0[shoulder],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=100,diff_step=1e-4);q=q0.copy();q[shoulder]=fit.x;q=q.astype(np.float32).astype(float);ps=fk(q);caps={n:distance.measure(ps,n,gp,gr)for n in distance.capsules if n in ps};prox=distance.measure(ps,'R_Shoulder',gp,gr,.3);_,predicted=transform_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents);delta=ps['R_Elbow'][0]-start['R_Elbow'][0];palm_delta=ps['RH:palm'][0]-start['RH:palm'][0];error=float(abs(delta@forward-mm/1000));orthogonal=float(np.linalg.norm(delta-forward*(delta@forward)));accepted=bool(audit['source_clear']and min(v['gap_m']for v in caps.values())>=.00005 and .00005<=prox['gap_m']<.003 and caps['R_Elbow']['gap_m']>=.012 and error<.002 and orthogonal<.012 and delta@forward>0 and np.array_equal(q[frozen],q0[frozen])and np.all(q>=c.lower-1e-7)and np.all(q<=c.upper+1e-7));label='shoulder_forward%dmm'%mm
  row={**{k:v for k,v in seed['body_side_lean_axilla'].items()if k not in ('right12_q_rad','right_bounds_rad','posture_shape','hand_position_error_m')},'label':label,'accepted_for_native':accepted,'capsule_body':caps,'proximal_upper_arm30_witness':prox,'proximal_upper_arm65_witness':prox,'proximal_fraction_limit':.3,'legacy_key_note':'65 compatibility only; source fraction0..30%','source_audit':audit,'joint_angles_rad':q.tolist(),'shoulder_forward':{'requested_elbow_forward_mm':mm,'forward_unit_W':forward.tolist(),'forward_definition':'guitar front normal projected horizontally, world+Y approximately','elbow_delta_W_mm':(delta*1000).tolist(),'elbow_forward_mm':float(delta@forward*1000),'elbow_target_error_mm':error*1000,'error_definition':'absolute forward projection error; not Euclidean3D target error','elbow_orthogonal_displacement_mm':orthogonal*1000,'shoulder_bounds_rad':{'lower':lo.tolist(),'upper':hi.tolist()},'palm_delta_W_mm':(palm_delta*1000).tolist(),'shoulder_origin_delta_W_mm':((ps['R_Shoulder'][0]-start['R_Shoulder'][0])*1000).tolist(),'shoulder_scalar_delta_rad':{names[i]:float(q[i]-q0[i])for i in shoulder},'frozen78_exact':bool(np.array_equal(q[frozen],q0[frozen])),'guitar_initial_pq_unchanged':True}}
  rows.append(row);save(out/(label+'_audit.json'),row);print(label,'accepted',accepted,'elbowforward/error mm',row['shoulder_forward']['elbow_forward_mm'],error*1000,'prox/full/forearm mm',[prox['gap_m']*1000,caps['R_Shoulder']['gap_m']*1000,caps['R_Elbow']['gap_m']*1000],flush=True)
  if accepted:
   folder=out/label;folder.mkdir();candidate={**seed,'joint_angles_rad':q.tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']},'body_side_lean_axilla':row};save(folder/'candidate.json',candidate);save(folder/'config.json',{**cfg,'initial_candidate':str(folder/'candidate.json'),'initial_candidate_sha256':sha(folder/'candidate.json'),'elbow_motion_amplitude_rad':0.0});selected.append({'label':label,'config':str(folder/'config.json')})
 assert all(sha(Path(p))==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'rows':rows,'selected':selected,'scope':'initial source FK/geometry only; only R_Shoulder3 changes, native validation pending','native_runs':0})
if __name__=='__main__':main()
