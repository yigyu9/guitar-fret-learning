"""Audit actual static trials, including every left-arm guitar contact sample."""
from pathlib import Path
import hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/rounded_spine_no_left_v1'
inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
    p=Path(p);inputs[str(p)]=sha(p);return json.loads(p.read_text())
def music_free(report):return report['music_actors']==report['policy_calls']==report['checkpoint_loads']==0
def main():
    inputs[str(Path(__file__))]=sha(__file__);batch=read(P/'native_v2/batch_report.json');selected=read(P/'search_v2/selected.json');checks={};summaries=[];initials={}
    checks['four_completed_exit_zero']=batch['all_completed'] and len(batch['records'])==4
    for record in batch['records']:
        label=record['label'];out=Path(record['output']);proposal=next(e for e in selected['selected'] if e['label']==label);rp=out/'report.json'
        if not rp.exists():
            summaries.append({'label':label,'completed':False,'failure':read(out/'failure.json') if (out/'failure.json').exists() else record,'scope':'partial diagnostic, not full five-second success'});continue
        report=read(rp);initial=read(out/'initial_values.json');initials[label]=initial;rows=report['rows'];contact=read(out/'contacts.json');cap=read(out/'media/capture.json');qref=np.array(initial['q_ref_rad']);attempt=read(out/'attempt.json')
        checks[label+'_horizon']=report['completed'] and report['physics_steps']==1200 and report['controls']==300 and len(rows)==301 and rows[-1]['time_s']==5
        checks[label+'_no_music_CP_policy_noise']=music_free(report) and not attempt['initial_noise']
        checks[label+'_fixed_qref_and_guard']=all(np.array_equal(np.array(e['submitted_target_rad']),qref) for e in rows) and not report['forbidden_calls'] and report['initial_state_write_calls']==['set_actor_rigid_body_states','set_actor_dof_states']
        checks[label+'_source_FK']=report['source_audit']['source_clear'] and max(e['position_error_m'] for e in initial['native_FK_error'].values())<1e-5 and max(e['orientation_error_deg'] for e in initial['native_FK_error'].values())<.01
        checks[label+'_strap_original']=report['strap_force_calls']==15600 and attempt['strap_enabled']
        checks[label+'_inputs_exact']=read(out/'inputs_verified.json')['unchanged'] and all(sha(p)==h for p,h in attempt['input_sha256'].items())
        checks[label+'_videos_full']=len(cap['frames'])==151 and cap['frames'][0]['time_s']==0 and cap['frames'][-1]['time_s']==5 and all(e['render_preserves_states'] for e in cap['frames']) and all(int(v['stream']['nb_read_frames'])==151 and abs(float(v['stream']['duration'])-151/30)<.002 and sha(v['path'])==v['sha256'] for v in report['videos'].values())
        for v in report['videos'].values():inputs[v['path']]=sha(v['path'])
        contact_summary={};groups={'left_hand':lambda n:n.startswith('LH:') or n=='L_Wrist','all_left_arm_hand':lambda n:n.startswith(('L_','LH:'))}
        for n in ('LH:palm','L_Elbow','L_Shoulder','R_Shoulder','R_Elbow','Chest','Spine','Torso','R_Hip'):groups[n]=lambda other,target=n:other==target
        for name,predicate in groups.items():
            times=[];positive=[];raw=[];observed={}
            for frame in contact:
                found=[]
                for c in frame['contacts']:
                    a,b=c['body0_name'],c['body1_name'];human=b if a.startswith('guitar/') else a if b.startswith('guitar/') else None
                    if human is not None and predicate(human.rsplit('/',1)[-1]):found.append(c);observed[human]=observed.get(human,0)+1
                if found:
                    t=frame['physics_step']/240;times.append(t);raw.extend(c['lambda'] for c in found)
                    if any(c['lambda']>0 for c in found):positive.append(t)
            contact_summary[name]={'sample_count':len(times),'positive_raw_lambda_sample_count':len(positive),'first_time_s':min(times) if times else None,'last_time_s':max(times) if times else None,'maximum_unconverted_raw_lambda':max(raw) if raw else None,'body_contact_record_counts':observed}
        late=rows[120:];p2=np.array(late[0]['position_W_m']);r2=Rotation.from_quat(late[0]['quaternion_xyzw']);dp=[float(np.linalg.norm(np.array(e['position_W_m'])-p2)*1000) for e in late];dr=[float(np.rad2deg((r2.inv()*Rotation.from_quat(e['quaternion_xyzw'])).magnitude())) for e in late]
        summaries.append({'label':label,'completed':True,'requested_Chest_forward_deg':proposal['requested_lean_deg'],'left_absent_initial_goal':proposal['left_absent_initial_goal'],'initial_body_world_deltas_deg':proposal['source_row']['segment_world_delta_deg'],'predicted_upper_arm_source_plane_gap_mm':proposal['source_row']['support_top_plane_signed_gap_m']*1000,'final_position_change_mm':rows[-1]['position_change_m']*1000,'maximum_position_change_mm':max(e['position_change_m'] for e in rows)*1000,'final_SO3_change_deg':rows[-1]['rotation_change_deg'],'maximum_SO3_change_deg':max(e['rotation_change_deg'] for e in rows),'late_net_position_mm':dp[-1],'late_max_position_from_2s_mm':max(dp),'late_net_SO3_deg':dr[-1],'late_max_SO3_from_2s_deg':max(dr),'max_actual_Chest_rotation_from_own_initial_deg':max(e['Chest_change_deg'] for e in rows),'initial_guitar_actor_root_W_m':rows[0]['position_W_m'],'final_guitar_actor_root_W_m':rows[-1]['position_W_m'],'left_hand_no_contact_at_300_queries':contact_summary['left_hand']['sample_count']==0,'all_left_arm_hand_no_contact_at_300_queries':contact_summary['all_left_arm_hand']['sample_count']==0,'contacts':contact_summary,'native_videos':report['videos']})
    if len(initials)==4:
        reference=next(iter(initials.values()));names=reference['joint_names'];finger_head=[i for i,n in enumerate(names) if n.startswith(('LH:','RH:','Head_','Neck_'))]
        checks['same_initial_guitar_PD_finger_head']=all(e['native_initial_state']['guitar_body_states']==reference['native_initial_state']['guitar_body_states'] and e['PD_properties']==reference['PD_properties'] and all(e['q_ref_rad'][i]==reference['q_ref_rad'][i] for i in finger_head) for e in initials.values())
        support=initials['rounded9_left_support'];away=initials['rounded9_left_away'];nonleft=[i for i,n in enumerate(names) if not n.startswith('L_')]
        checks['nine_deg_pair_nonleft_targets_exact']=all(support['q_ref_rad'][i]==away['q_ref_rad'][i] for i in nonleft)
    pins=read(P/'source_before_native_v2.json');checks['native_sources_unchanged']=all(sha(p)==h for p,h in pins.items());checks['analysis_inputs_exact']=all(sha(p)==h for p,h in inputs.items())
    result={'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'summaries':summaries,'contact_scope':'300 queries before60Hz control, not every240Hz physics substep; zero queries is not continuous-time absence certification; raw lambda not Newton force','scope':'initial hand withdrawn, original strapON; no runtime release, music, policy or training; position uses actor-root, not body center natural range'}
    with (P/'verification_v1.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({'passed':result['passed'],'checks':len(checks),'summaries':[{k:e.get(k) for k in ('label','completed','final_position_change_mm','final_SO3_change_deg','late_net_position_mm','late_net_SO3_deg','all_left_arm_hand_no_contact_at_300_queries')} for e in summaries]},ensure_ascii=False,indent=2));assert result['passed'],checks
if __name__=='__main__':main()
