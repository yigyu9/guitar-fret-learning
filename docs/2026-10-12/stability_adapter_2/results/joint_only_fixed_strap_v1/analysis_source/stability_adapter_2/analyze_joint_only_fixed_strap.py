"""Compare joint-only initial-pose changes at one fixed original strap length."""
import json,hashlib
from pathlib import Path
import numpy as np
from .analyze_small_wrist_motion import metrics
from .analyze_body9_strap_minus4mm import strap_metrics,wrist_response
from .warmstart_targets import compose

R=Path(__file__).resolve().parents[1];A=R/'stability_adapter_2';B=R/'docs/2026-10-12/stability_adapter_2/results'
P=B/'joint_only_fixed_strap_v1'; OLD=B/'small_wrist_motion_v1/native'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    out=P/'analysis.json';assert not out.exists();new=P/'native';inputs={}
    for folder in (OLD,new):
        for n in ('initial_values.json','states.jsonl','trace.jsonl','controls.jsonl','contacts.jsonl','capture.json','report.json','videos.json'):
            p=folder/n;inputs[str(p)]=sha(p)
    static=B/'torso_hold_native_collision_v1/native/states.jsonl'
    for p in (Path(__file__).resolve(),A/'analyze_small_wrist_motion.py',A/'analyze_body9_strap_minus4mm.py',A/'strap.py',A/'warmstart_targets.py',A/'JOINT_ONLY_FIXED_STRAP_PLAN.md',A/'analyze_body9_strap_fine.py',P/'preparation.json',P/'proposal.json',P/'native_execution.json',static):inputs[str(p)]=sha(p)
    i0=read(OLD/'initial_values.json');i1=read(new/'initial_values.json');proposal=read(P/'proposal.json');row=proposal['rows'][0];prep=read(P/'preparation.json')
    s0=lines(OLD/'states.jsonl');s1=lines(new/'states.jsonl');c0=lines(OLD/'controls.jsonl');c1=lines(new/'controls.jsonl');cap=read(new/'capture.json');report=read(new/'report.json')
    names=i1['human_joint_names'];indices=[names.index(n) for n in prep['selected_names']];held=[j for j in range(81) if j not in indices];main_indices=[names.index(n) for n in i1['main_control_joint_names']]
    common=('PD_properties','physics_parameters','guitar_goal_position_W_m','guitar_goal_quaternion_xyzw','main_control_joint_names','human_joint_names','human_body_names','strap_law_parameters','absolute_strap_rest_length_m','motion_command')
    same={k:i0[k]==i1[k] for k in common}
    restored=json.loads(json.dumps(i1['input_trial']))
    for n in prep['selected_names']:restored['initial_settings']['joint_angles_rad'][n]=i0['input_trial']['initial_settings']['joint_angles_rad'][n]
    checks=dict(one_complete_actual1200step=report['completed'] and report['failure'] is None and report['native_initializations']==1 and report['physics_steps']==1200 and len(s1)==1201,
                all_native_checks=all(report['checks'].values()),two151frame_strap_videos=len(cap['frames'])==151 and len(report['videos'])==2,
                common10_fields_exact=all(same.values()),only_initial18_trial_changed=restored==i0['input_trial'],
                original_LA_exact=i0['absolute_strap_rest_length_m']==i1['absolute_strap_rest_length_m']==1.1018469719600776,
                initial_q_PD_equal_prepared=i1['initial_PD_target_rad']==row['expected_initial_angles_rad'] and i1['preserved_absolute_targets_rad']==row['expected_absolute_targets_rad'],
                guitar_initial_state_exact=s1[0]['guitar_body_states']==s0[0]['guitar_body_states'],
                initial_other63_q_exact=all(s1[0]['human_dof_states'][j]==s0[0]['human_dof_states'][j] for j in held),
                all1200_other63_targets_exact=len(c1)==len(c0)==1200 and all(all(a['final_target_rad'][j]==b['final_target_rad'][j] for j in held) for a,b in zip(c0,c1)),
                all1200_same_clock_and_waveform=all(all(a[k]==b[k] for k in ('physics_step','updated_before_step','command_time_s','wrist_motion_delta_rad')) for a,b in zip(c0,c1)))
    traces={};contact_rows={}
    for label,folder,states,controls in [('original_LA_baseline',OLD,s0,c0),('joint_only_original_LA',new,s1,c1)]:
        traces[label]=lines(folder/'trace.jsonl');contact_rows[label]=lines(folder/'contacts.jsonl')
        checks[label+'_complete_row_coverage']=len(states)==len(traces[label])==1201 and len(controls)==len(contact_rows[label])==1200 and [s['physics_step'] for s in states]==list(range(1201)) and all(t['time_s']==j/240. for j,t in enumerate(traces[label])) and [r['physics_step'] for r in contact_rows[label]]==list(range(1,1201)) and [r['physics_step'] for r in controls]==list(range(1,1201))
    assert all(checks.values()),checks
    offsets=np.array([i1['input_trial']['main_target_offsets_rad'].get(names[j],0.) for j in main_indices]); wrist=names.index('L_Wrist_x');kw=main_indices.index(wrist)
    q=np.array(i1['initial_PD_target_rad'],dtype=np.float32);lo=np.array(i1['PD_properties']['lower']);hi=np.array(i1['PD_properties']['upper'])
    for r in c1:
        command=offsets.copy();command[kw]+=r['wrist_motion_delta_rad']
        assert np.array_equal(compose(q,main_indices,command,lo,hi),np.array(r['final_target_rad'],dtype=np.float32))
    checks['all1200_targets_reconstructed_no_clipping']=True
    checks['capture_all_steps_and_readonly']=all(f['physics_step']==j*8 and f['time_s']==j/30 and f['render_preserves_states'] for j,f in enumerate(cap['frames']))
    for f in cap['frames']:
        for k in ('image_sha256','raw_image_sha256'):
            assert all(sha(p)==h for p,h in f[k].items())
    checks['all604_PNG_SHA_exact']=True
    static_states=lines(static);summary=[]
    for label,folder,states,initial in [('original_LA_baseline',OLD,s0,i0),('joint_only_original_LA',new,s1,i1)]:
        trace=traces[label];contacts={};self_steps=set()
        for r in contact_rows[label]:
            for c in r['contacts']:
                pair=(c['body0_name'],c['body1_name'])
                if all(n.startswith('human/') for n in pair):self_steps.add(r['physics_step'])
                if c['lambda']>0 and any(n.startswith('guitar/') for n in pair) and any(n.startswith('human/') for n in pair):
                    body=next(n for n in pair if n.startswith('human/'));contacts.setdefault(body,set()).add(r['physics_step'])
        actual=np.array([[d['pos'] for d in s['human_dof_states']] for s in states])
        body9=[names.index(body+'_'+axis) for body in ('Torso','Spine','Chest') for axis in 'xyz']
        actual_excess=np.maximum(np.array(initial['PD_properties']['lower'])-actual,actual-np.array(initial['PD_properties']['upper']))
        summary.append(dict(label=label,guitar=metrics(trace),strap=strap_metrics(trace,initial),wrist=wrist_response(states,static_states,wrist),
                            body9_max_actual_coordinate_departure_deg=float(np.degrees(abs(actual[:,body9]-actual[0,body9]).max())),
                            max_actual_native_bound_excess_rad=float(max(0.,actual_excess.max())),
                            human_self_contact_steps=len(self_steps),human_guitar_positive_raw_lambda_by_body={n:dict(steps=len(v),first_step=min(v),last_step=max(v)) for n,v in sorted(contacts.items())}))
    checks['inputs_preserved']=all(sha(p)==h for p,h in inputs.items());assert all(checks.values()),checks
    out.write_text(json.dumps(dict(checks=checks,input_sha256=inputs,common_initial_exact_fields=same,summary=summary,new_native_initializations=1,new_physics_steps=1200,
                                  scope='initial18 and corresponding PD goals shifted; original passive LA fixed at1.1018469719600776m; body9PD2/root-lower/G initial and wrist waveform preserved; joint-only initial/PD comparison, not runtime correction or playing/grip success'),indent=2)+'\n')
    print(json.dumps(dict(checks=checks,summary=summary),indent=2))
if __name__=='__main__':main()
