"""Observed native evidence only; sampled unions are not all-step union times."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation as R
P=Path(__file__).resolve().parent
runs=['physics_off','physics_follow','physics_hold','physics_hold_v5']
files=[Path(__file__)]+[P/n/f for n in runs for f in ['report.json','trace.json','contacts.json','initial_values.json','initial_audit.json','attempt.json']]+[P/n/'controls.json' for n in runs if n!='physics_off']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
hashes={str(p):sha(p) for p in files}
result={}
initials={n:read(P/n/'initial_values.json') for n in runs}
for n in runs:
    trace=read(P/n/'trace.json');contacts=read(P/n/'contacts.json');controls=read(P/n/'controls.json') if n!='physics_off' else []
    init=initials[n];chest=init['native_initial_state']['human_body_states'][init['human_body_names'].index('Chest')]['pose']['p']['z']
    pos=np.array([s['position_W_m'] for s in trace]);late=[s for s in trace if s['time_s']>=2]
    q0=np.array(init['actual_initial_angles_rad']);qend=np.array(trace[-1]['human_angles_rad'])
    box=((pos>=np.array([-.5,-.15,.65]))&(pos<=np.array([-.15,.15,chest]))).all(axis=1)
    union={digit:{'contact_row_sample_count':0,'positive_lambda_row_sample_count':0} for digit in ['palm','thumb','index','middle','ring','pinky','right']}
    for sample in contacts['samples']:
        for digit,counts in union.items():
            found=[]
            for c in sample['contacts']:
                a,b=c['body0_name'],c['body1_name']
                if b.startswith('guitar/'):a,b=b,a
                match=(b.startswith('human/RH:') or b=='human/R_Wrist') if digit=='right' else b.startswith('human/LH:'+digit)
                if a.startswith('guitar/') and match:found.append(c)
            counts['contact_row_sample_count']+=bool(found)
            counts['positive_lambda_row_sample_count']+=any(c['lambda']>0 for c in found)
    common=[k for k in init if k!='candidate_path']
    exact=all(init[k]==initials['physics_off'][k] for k in common)
    report=read(P/n/'report.json')
    result[n]={'initial_common_fields_exact_with_OFF':exact,'max_sampled_position_change_mm':report['max_position_change_m']*1000,
        'max_sampled_rotation_change_deg':report['max_rotation_change_deg'],'final_position_change_mm':trace[-1]['position_change_m']*1000,
        'final_rotation_change_deg':trace[-1]['rotation_change_deg'],'final_position_W_m':trace[-1]['position_W_m'],
        'sampled_position_box_outside_count':int((~box).sum()),'position_trace_samples':len(trace),'minimum_sampled_height_m':float(pos[:,2].min()),
        'maximum_sampled_height_deficit_mm':float(max(0,.65-pos[:,2].min())*1000),
        'late_2_to_5s_position_change_from_2s_max_mm':float(max(np.linalg.norm(np.array(s['position_W_m'])-late[0]['position_W_m']) for s in late)*1000),
        'late_2_to_5s_rotation_change_from_2s_max_deg':float(max(np.degrees((R.from_quat(s['quaternion_xyzw'])*R.from_quat(late[0]['quaternion_xyzw']).inv()).magnitude()) for s in late)),
        'L_Shoulder_x_final_error_deg':float(np.degrees(qend[init['joint_names'].index('L_Shoulder_x')]-q0[init['joint_names'].index('L_Shoulder_x')])),
        'control_count':len(controls),'cap_reached_update_count':sum(c['max_target_delta_from_initial_rad']>=.29999 for c in controls),
        'max_float32_target_delta_rad':max((c['max_target_delta_from_initial_rad'] for c in controls),default=0),
        'max_float32_target_step_rad':max((c['max_target_step_rad'] for c in controls),default=0),
        'contact_sample_union':union,'contact_sample_count':len(contacts['samples']),
        'report_checks':report['checks'],'source_clear':report['source_clear']}
result['hold_v4_vs_v5_trace_exact']=read(P/'physics_hold/trace.json')==read(P/'physics_hold_v5/trace.json')
result['hold_v4_vs_v5_controls_exact']=read(P/'physics_hold/controls.json')==read(P/'physics_hold_v5/controls.json')
result['scope']='151 pose samples/150 contact samples at every8 of1200 steps; contact row union sample counts, lambda>0 flag is not measured Newton force; rotation-box containment not evaluated; source proxy clearance not PhysX certification'
result['inputs_sha256']=hashes
result['inputs_unchanged']=all(sha(Path(p))==h for p,h in hashes.items())
assert result['inputs_unchanged']
(P/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({n:{k:v for k,v in result[n].items() if k not in ['contact_sample_union','report_checks']} for n in runs},indent=2))
