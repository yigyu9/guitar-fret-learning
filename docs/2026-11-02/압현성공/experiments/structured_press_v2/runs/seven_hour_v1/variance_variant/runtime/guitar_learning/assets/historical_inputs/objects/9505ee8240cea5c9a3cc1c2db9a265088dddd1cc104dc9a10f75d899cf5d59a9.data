"""Release same-initial elbow motion after actual guitar and torso direction gates."""
from pathlib import Path
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';P=R/'docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
 with p.open('x')as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False)
def main():
 vp=P/'analysis_v1/static_neckyaw12/verification.json';posture=P/'torso_posture_v1.json';cp=P/'search_v1/bend2_neckyaw12/config.json';v=read(vp);s=v['cases']['static_neckyaw12'];delta=read(posture)['cases']['static_neckyaw12']['final_minus_previous_stable_deg'];gate=bool(v['passed']and s['final_body_bbox_centre_change_mm']<10 and s['final_rotation_change_deg']<3 and s['endpoints']['head_presence']==s['endpoints']['left_arm_hand_presence']==s['endpoints']['right_distal_presence']==0 and s['right_upper_last_half_second_presence']>=100 and s['body_centre_2_to_2p5s_mm']<1 and s['rotation_2_to_2p5s_deg']<.5 and delta['chest_facing_yaw_from_guitar_front_deg']>=5 and delta['chest_to_neck_forward_inclination_deg']<=-3);assert gate;cfg=read(cp);candidate=Path(cfg['initial_candidate']);assert sha(candidate)==cfg['initial_candidate_sha256'];out=P/'motion_candidate_v1';out.mkdir(exist_ok=False);paths=[Path(__file__).resolve(),A/'NECKWARD_TORSO_TURN_PLAN_V2.md',vp,posture,cp,candidate,P/'native_v1/static_neckyaw12/initial_values.json'];inputs={str(p):sha(p)for p in paths};save(out/'inputs_before.json',inputs);save(out/'config_motion.json',{**cfg,'elbow_motion_amplitude_rad':float(np.deg2rad(5)),'static_gate_input':str(vp),'static_gate_input_sha256':sha(vp),'torso_posture_input':str(posture),'torso_posture_input_sha256':sha(posture)})
 save(out/'gate_release.json',{'input_sha256':inputs,'passed':gate,'same_candidate':str(candidate),'same_candidate_sha256':sha(candidate),'only_actuator_change':'R_Elbow_y target5degree one cycle','body_final_mm':s['final_body_bbox_centre_change_mm'],'rotation_final_deg':s['final_rotation_change_deg'],'actual_torso_direction_delta_deg':delta});assert all(sha(Path(p))==h for p,h in inputs.items())
if __name__=='__main__':main()
