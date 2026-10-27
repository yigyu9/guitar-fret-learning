"""Fit shoulder/torso/thigh support with a clear, independently moving forearm."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,ASSET,calibrated_upper_fk,state_from_fk
from .realistic_guitar_geometry_v1 import source_scene,source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .underneck_initial_search import source_scene as transform_guitar
A=ROOT/'stability_adapter_2';D=ROOT/'docs/2026-10-19/stability_adapter_2';P=D/'results/axilla_elbow_isolation_v1'
BASE=D/'results/natural_right_arm_v1/native_v2/front160mm/initial_values.json'
CFG=D/'results/upper_bout_axilla_v1/search_v3/right6_upper35/config.json'
PLAN=A/'AXILLA_ELBOW_ISOLATION_PLAN_V2.md'
PRIOR=P/'search_v1/search.json'
def main():
 from .environment_contract_v1 import EnvironmentContract
 c=EnvironmentContract(CFG);base=read(BASE);cfg=read(CFG);seed=read(cfg['initial_candidate']);names=base['joint_names'];bodies=base['human_body_names'];state=base['native_initial_state'];qbase=np.array(base['q_ref_rad']);fk,parents=calibrated_upper_fk(names,bodies,state,qbase)
 prior=P/'search_v2/search.json';row=next(r for r in read(prior)['rows']if r['label']=='bend8_cradle');geometry=read(A/'assets/om_body_geometry_v3/manifest.json');distance=CapsuleBodyDistance(geometry['asset'],ASSET);vertices=np.vstack([v[0]for v in distance.pieces]);centre=(vertices.min(0)+vertices.max(0))/2;gp0=np.array(seed['position_W_m']);gr0=Rotation.from_quat(seed['quaternion_xyzw']);gr=Rotation.from_rotvec(gr0.apply([0,0,1])*np.deg2rad(row['guitar_neck_initial_elevation_deg']))*gr0;gp=gp0+gr0.apply(centre)+np.array(row['guitar_body_bbox_centre_delta_W_m'])-gr.apply(centre);q=np.array(row['joint_angles_rad']);assert np.array_equal(q,q.astype(np.float32).astype(float));ps=fk(q)
 _,predicted=transform_guitar(state_from_fk(state,bodies,q,fk),{'human_body_names':bodies},gp,gr);audit=source_audit(source_scene(predicted,bodies,geometry['asset']),parents);caps={n:distance.measure(ps,n,gp,gr)for n in distance.capsules if n in ps};prox=distance.measure(ps,'R_Shoulder',gp,gr,.3);shape=row['posture_shape'];assert audit['source_clear']and min(v['gap_m']for v in caps.values())>=.00005 and .00005<=prox['gap_m']<.003 and caps['R_Hip']['gap_m']<.004 and caps['R_Elbow']['gap_m']>=.012 and shape['elbow_below_shoulder_m']>=.02 and shape['elbow_outside_shoulder_m']>=.16 and shape['wrist_inward_from_elbow_m']>=.03
 assert np.all(q>=c.lower-1e-7)and np.all(q<=c.upper+1e-7);out=P/'diagnostic_candidate_v1';out.mkdir(exist_ok=False);files=[Path(__file__).resolve(),A/'AXILLA_ELBOW_ISOLATION_PLAN_V3.md',prior,BASE,CFG,Path(cfg['initial_candidate']),ASSET,A/'assets/om_body_geometry_v3/manifest.json'];inputs={str(p):sha(p)for p in files};inputs.update(c.inputs);inputs.update({str(p):sha(p)for p in A.glob('*.py')});save(out/'inputs_before.json',inputs)
 candidate={'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':{'proximal_support':caps['R_Elbow']},'body_side_lean_axilla':row,'diagnostic_only':'source2 rejected torso gate explicitly waived; no claim of torso/axilla contact or stability'};save(out/'candidate.json',candidate);newcfg={**cfg,'initial_candidate':str(out/'candidate.json'),'initial_candidate_sha256':sha(out/'candidate.json'),'elbow_motion_amplitude_rad':0.0};save(out/'config_static.json',newcfg);save(out/'verification.json',{'source_clear':audit['source_clear'],'source_candidate_pinned':sha(prior),'q81_float32_exact':True,'capsule_body':caps,'proximal30':prox,'torso_gap_m':caps['R_Thorax']['gap_m'],'accepted_for_diagnostic_not_success':True});assert all(sha(p)==h for p,h in inputs.items())
if __name__=='__main__':main()
