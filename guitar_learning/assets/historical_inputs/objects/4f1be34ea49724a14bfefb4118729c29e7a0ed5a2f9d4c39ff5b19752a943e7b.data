"""Verify actual left-contact/task removal and retained initial support settings."""
from pathlib import Path
import numpy as np
from .initial_pose_noise_v1 import read, save, sha
from .upper_arm_static_geometry_v1 import ROOT


def main():
    a=ROOT/'stability_adapter_2';d=ROOT/'docs/2026-10-19/stability_adapter_2/results'
    p=d/'left_hand_off_current_v1';b=d/'right_arm_wrap_forward_v1/native_elbow10_static';n=p/'native_back100_static'
    paths=[Path(__file__).resolve(),p/'timelines_v1.json']+[f for folder in (n,b) for f in folder.rglob('*.json')]
    inputs={str(f):sha(f) for f in paths};save(p/'left_off_analysis_before_v1.json',inputs)
    old=read(b/'initial_values.json');new=read(n/'initial_values.json');report=read(n/'report.json')
    left=[i for i,name in enumerate(new['joint_names']) if name.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))]
    frozen=[i for i in range(81) if i not in left];assert len(left)==12 and len(frozen)==69
    assert np.array_equal(np.array(old['q_ref_rad'])[frozen],np.array(new['q_ref_rad'])[frozen])
    s0=old['native_initial_state'];s1=new['native_initial_state']
    assert s0['guitar_body_states']==s1['guitar_body_states']
    support=['Torso','Spine','Chest','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','R_Hip']
    assert all(s0['human_body_states'][old['human_body_names'].index(name)]==s1['human_body_states'][new['human_body_names'].index(name)] for name in support)
    assert read(b/'media/two_block_configuration.json')==read(n/'media/two_block_configuration.json')
    track=read(n/'media/left_wrist_tracking_rows.json')['rows'];end=read(n/'media/physics_endpoint_contacts.json')['rows']
    assert len(track)==len(end)==report['physics_steps']
    assert all(not row['enabled'] and np.array_equal(row['virtual_force_request_W_N'],np.zeros(3)) and np.array_equal(row['task_left_Nm'],np.zeros(12)) for row in track)
    assert all(not row['left_arm_hand_guitar_contacts'] for row in end)
    for field in ('right_upper_arm_body_contacts','right_hip_body_contacts'):
        steps=[row['physics_step'] for row in end if row[field]]
        print(field,'last',max(steps) if steps else None)
    timeline=read(p/'timelines_v1.json')['cases'][n.name]
    result={'passed':True,'input_sha256':inputs,'frozen69_initial_q_exact':True,'guitar39_initial_full_state_exact':True,
        'right_trunk_support_initial_full_state_exact':True,'right_two_block_configuration_exact':True,
        'left12_q_delta_rad':{new['joint_names'][i]:new['q_ref_rad'][i]-old['q_ref_rad'][i] for i in left},
        'left_contact_presence_steps':0,'left_tracking_enabled_steps':0,'left_virtual_force_and_task_exact_zero':True,
        'physics_steps':len(end),'physics_seconds':report['physics_seconds'],'maintained_for_5s':report['completed'],
        'failure':report['failure'],'body_centre_final_displacement_mm':timeline['final_body_centre_change_mm'],
        'final_SO3_rotation_deg':timeline['final_rotation_change_deg'],
        'last_contact_physics_steps':{field:max((r['physics_step'] for r in end if r[field]),default=None) for field in ('right_upper_arm_body_contacts','right_hip_body_contacts')},
        'scope':'t=0 left-away initialization; gravity/scalar PD and right/body current-G stabilization remain active. No continuous hand-release transition or passive equilibrium claim. No strap or guitar forces/state writes.'}
    assert all(sha(f)==h for f,h in inputs.items());save(p/'left_off_analysis_v1.json',result)


if __name__=='__main__':main()
