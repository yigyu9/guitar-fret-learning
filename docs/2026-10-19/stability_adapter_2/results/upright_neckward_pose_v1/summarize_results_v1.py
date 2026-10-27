"""Summarize seven native diagnostics without merging source and measured posture."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 files=[Path(__file__).resolve(),P/'torso_posture_v7.json',P/'contact_region_v1.json',P/'elbow_comparison_v1.json',P/'motion_candidate_v1/gate_release.json']+sorted(P.glob('analysis_v*/*/verification.json'));inputs={str(p):sha(p)for p in files};post=read(files[1]);region=read(files[2]);cases={}
 for f in files[5:]:
  v=read(f);assert v['passed']
  for name,s in v['cases'].items():
   d=post['cases'][name]['final_minus_previous_stable_deg'];gate=bool(s['final_body_bbox_centre_change_mm']<10 and s['final_rotation_change_deg']<3 and s['endpoints']['head_presence']==s['endpoints']['left_arm_hand_presence']==s['endpoints']['right_distal_presence']==0 and s['right_upper_last_half_second_presence']>=100 and s['body_centre_2_to_2p5s_mm']<1 and s['rotation_2_to_2p5s_deg']<.5 and d['chest_facing_yaw_from_guitar_front_deg']>=5 and d['chest_to_neck_forward_inclination_deg']<=-5);cases[name]={'native_summary':s,'native_torso_initial':post['cases'][name]['initial'],'native_torso_final':post['cases'][name]['final'],'native_torso_final_delta_vs_previous_12deg':d,'declared_shoulder35_upper_bout_samples':region['cases'][name]['declared_region_contact_samples'],'declared_region_positive_lambda_samples':region['cases'][name]['declared_region_positive_raw_lambda_samples'],'static_metrics_gate_passed':gate,'adoption_scope':'recommended 19-degree diagnostic' if name in ('static_neckyaw19','elbow_neckyaw19') else 'preserved, not adopted'}
 assert len(cases)==7 and cases['static_neckyaw19']['static_metrics_gate_passed'];assert read(P/'elbow_comparison_v1.json')['small_elbow_influence_diagnostic_passed'];assert all(sha(Path(p))==h for p,h in inputs.items())
 result={'input_sha256':inputs,'selected_static':'static_neckyaw19','selected_motion':'elbow_neckyaw19','native_complete_5s':7,'native_aborted':0,'cases':cases,'elbow_comparison':read(P/'elbow_comparison_v1.json'),'limitations':['final static rotation gate margin only0.004602degrees, maximum transient3.313974degrees; not repeatability robustness','source requested additional body19degree yaw is not native heading, guitar quaternion unchanged','63piece source gaps and native contacts do not certify anatomical armpit tissue/force shares','one5s matched pair, no fret/strike or long-duration validation'],'execution_context':'run1 attempt pins PLAN_V1; later static20 follows separate PLAN_V4 and static19/motion19 PLAN_V5, immutable runner unchanged'}
 with (P/'result_summary_v1.json').open('x') as f:json.dump(result,f,indent=2,ensure_ascii=False,allow_nan=False)
 print('summarized',len(cases),'native cases')
if __name__=='__main__':main()
