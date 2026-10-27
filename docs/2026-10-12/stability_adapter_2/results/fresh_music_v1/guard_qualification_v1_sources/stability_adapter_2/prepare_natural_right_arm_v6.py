"""Preserve V5 and prepare one source-clear candidate for native visual review."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from .upper_arm_static_geometry_v1 import ROOT,calibrated_upper_fk
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1'
A=ROOT/'stability_adapter_2'
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
def main():
 source=P/'search_v5/search.json';data=read(source)
 assert all(sha(p)==h for p,h in data['input_sha256'].items())
 inputs=dict(data['input_sha256']);inputs.update({str(p):sha(p)for p in [source,Path(__file__).resolve(),A/'NATURAL_RIGHT_ARM_REFERENCE_PLAN_V6.md',A/'run_natural_right_arm_v6.py']})
 out=P/'search_v6';out.mkdir(exist_ok=False);save(out/'inputs_before.json',inputs)
 row=next(r for r in data['rows']if r['label']=='front160mm');s=row['posture_shape'];bounds=row['bounds_rad'];base=read(OLD/'native_v10/three_support_relative_effort_microgap/initial_values.json');names=base['joint_names'];q=np.array(base['q_ref_rad']);right=[i for i,n in enumerate(names)if n in row['right_scalar_q_rad']]
 q[right]=[row['right_scalar_q_rad'][names[i]]for i in right]
 assert row['source_audit']['source_clear']and min(m['gap_m']for m in row['capsule_body'].values())>=.0001 and row['support_witness']['gap_m']<.015 and row['source_normal_W'][1]>.55
 assert s['elbow_outside_shoulder_m']>=.08 and s['elbow_below_shoulder_m']>=.06 and s['wrist_inward_from_elbow_m']>=.04 and s['hand_target_error_m']<.05 and row['initial_other69_same']
 assert np.all(q[right]>=np.array(bounds['lower'])-1e-7)and np.all(q[right]<=np.array(bounds['upper'])+1e-7)
 state=base['native_initial_state'];fk,_=calibrated_upper_fk(names,base['human_body_names'],state,np.array(base['q_ref_rad']));gp,gr=pose(state['guitar_body_states'][0]);gp+=row['guitar_initial_delta_W_m'];ps=fk(q)
 row={**row,'accepted_for_native':True,'adoption_scope':'native visual diagnostic only; elbow-down provisional gate 60mm replaces unvalidated 80mm; V5 source and q unchanged'}
 folder=out/'front160mm';folder.mkdir();save(folder/'candidate.json',{'joint_names':names,'joint_angles_rad':q.tolist(),'position_W_m':gp.tolist(),'quaternion_xyzw':gr.as_quat().tolist(),'predicted_human_poses':{n:{'p':p.tolist(),'q':r.as_quat().tolist()}for n,(p,r)in ps.items()},'no_strap_upper_arm_proposal':row['no_strap_upper_arm_proposal'],'natural_right_arm':row})
 cfg=read(OLD/'right_effort_config_v1.json');cfg.update(initial_candidate=str(folder/'candidate.json'),initial_candidate_sha256=sha(folder/'candidate.json'));save(folder/'config.json',cfg)
 assert all(sha(p)==h for p,h in inputs.items());save(out/'search.json',{'input_sha256':inputs,'selected':[{'label':'front160mm','config':str(folder/'config.json')}],'rows':[row],'native_runs':0,'scope':'source unchanged V5 candidate, not native clearance or final naturalness certification'})
if __name__=='__main__':main()
