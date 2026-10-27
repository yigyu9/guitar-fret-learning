"""Prepare a source-clear near-axilla candidate for actual native contact diagnosis."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,calibrated_upper_fk
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1'
A=ROOT/'stability_adapter_2'
PREV=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
def main():
 source=P/'search_v4/search.json';data=read(source);assert all(sha(p)==h for p,h in data['input_sha256'].items());row=data['rows'][0];base=read(PREV/'native_v2/front160mm/initial_values.json');seed=next(r for r in read(P/'search_v1/search.json')['rows']if r['label']=='right4deg');names=base['joint_names'];q=np.array(seed['joint_angles_rad']);right=[i for i,n in enumerate(names)if n in row['right9_q_rad']];q[right]=[row['right9_q_rad'][names[i]]for i in right];shape=row['posture_shape'];bounds=row['bounds_rad']
 assert row['source_audit']['source_clear']and min(m['gap_m']for m in row['capsule_body'].values())>=.00005 and .00005<=row['proximal_upper_arm65_witness']['gap_m']<.005 and .00005<=row['capsule_body']['R_Hip']['gap_m']<.003 and row['source_proximal_normal_W'][2]>.35
 assert shape['elbow_outside_shoulder_m']>=.18 and shape['elbow_below_shoulder_m']>=.03 and shape['wrist_inward_from_elbow_m']>=.03 and row['other72_initial_same_as_right4']and row['hand_position_error_m']<.04 and np.all(q[right]>=np.array(bounds['lower'])-1e-7)and np.all(q[right]<=np.array(bounds['upper'])+1e-7)
 inputs=dict(data['input_sha256']);inputs.update({str(p):sha(p)for p in [Path(__file__).resolve(),source,P/'search_v1/search.json',A/'BODY_SIDE_LEAN_AXILLA_PLAN_V5.md',A/'run_body_side_lean_axilla_v4.py']});out=P/'search_v5';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs)
 state=base['native_initial_state'];fk,_=calibrated_upper_fk(names,base['human_body_names'],state,np.array(base['q_ref_rad']));gp,gr=pose(state['guitar_body_states'][0]);gp+=row['guitar_initial_delta_W_m'];ps=fk(q);row={**row,'accepted_for_native':True,'adoption_scope':'same V4 source pose; proximal0~65% heuristic5mm for native diagnostic only; actual contact and stability unverified'};folder=out/'right4_close_support';folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':row['no_strap_upper_arm_proposal'],'body_side_lean_axilla':row});cfg=read(PREV/'search_v6/front160mm/config.json');cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg)
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':[{'label':'right4_close_support','config':str(folder/'config.json')}],'rows':[row],'native_runs':0,'scope':'native proximity diagnosis seed, not final adoption or contact/clearance certification'})
if __name__=='__main__':main()
