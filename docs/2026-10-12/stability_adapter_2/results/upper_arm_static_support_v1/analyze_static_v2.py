"""Audit static-hold trials and distinguish initial drift from late settling."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/home/ajou/yigyu/3');P=R/'docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1';RUN=P/'native_v2'
inputs={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):inputs[str(p)]=sha(p);return json.loads(p.read_text())
inputs[str(Path(__file__))]=sha(__file__);batch=read(RUN/'batch_report.json');selected=read(P/'configs_v2/selected.json');checks={'all_four_exit_zero':batch['all_completed'] and len(batch['records'])==4};summaries=[]
for record in batch['records']:
    label=record['label'];out=Path(record['output']);d=read(out/'report.json');initial=read(out/'initial_values.json');ct=read(out/'contacts.json');cap=read(out/'media/capture.json');rows=d['rows'];qref=np.array(initial['q_ref_rad']);s=next(e for e in selected['selected'] if e['label']==label)
    checks[label+'_five_seconds']=d['completed'] and d['physics_steps']==1200 and d['controls']==300 and len(rows)==301 and rows[-1]['time_s']==5
    checks[label+'_no_music_policy_CP_noise']=d['music_actors']==d['policy_calls']==d['checkpoint_loads']==0 and not read(out/'attempt.json')['initial_noise']
    checks[label+'_fixed_PD_target']=all(np.array_equal(np.array(row['submitted_target_rad']),qref) for row in rows)
    checks[label+'_guard_and_strap']=not d['forbidden_calls'] and d['initial_state_write_calls']==['set_actor_rigid_body_states','set_actor_dof_states'] and d['strap_force_calls']==13*1200
    checks[label+'_source_native_FK']=d['source_audit']['source_clear'] and max(v['position_error_m'] for v in initial['native_FK_error'].values())<=1e-5 and max(v['orientation_error_deg'] for v in initial['native_FK_error'].values())<=.01
    checks[label+'_video']=len(cap['frames'])==151 and cap['frames'][0]['time_s']==0 and cap['frames'][-1]['time_s']==5 and all(f['render_preserves_states'] for f in cap['frames']) and all(int(v['stream']['nb_read_frames'])==151 and abs(float(v['stream']['duration'])-151/30)<.002 and sha(v['path'])==v['sha256'] for v in d['videos'].values())
    for v in d['videos'].values():inputs[v['path']]=sha(v['path'])
    checks[label+'_input_SHA']=read(out/'inputs_verified.json')['unchanged'] and all(sha(path)==h for path,h in read(out/'attempt.json')['input_sha256'].items())
    at2=rows[120];last=rows[-1];p2=np.array(at2['position_W_m']);r2=Rotation.from_quat(at2['quaternion_xyzw']);late=rows[120:];latep=[np.linalg.norm(np.array(v['position_W_m'])-p2) for v in late];later=[np.rad2deg((r2.inv()*Rotation.from_quat(v['quaternion_xyzw'])).magnitude()) for v in late]
    contact_summary={}
    for target in ('R_Shoulder','R_Elbow','Chest','Torso','Spine','R_Hip','LH:palm'):
        times=[];positive_times=[];raw=[]
        for frame in ct:
            found=[c for c in frame['contacts'] if any(c[k].endswith('/'+target) for k in ('body0_name','body1_name')) and any(c[k].startswith('guitar/') for k in ('body0_name','body1_name'))]
            if found:
                times.append(frame['physics_step']/240);raw.extend(c['lambda'] for c in found)
                if any(c['lambda']>0 for c in found):positive_times.append(frame['physics_step']/240)
        contact_summary[target]={'contact_samples':len(times),'positive_raw_lambda_samples':len(positive_times),'fraction_of_300_samples':len(times)/300,'first_time_s':min(times) if times else None,'last_time_s':max(times) if times else None,'maximum_raw_lambda':max(raw) if raw else None,'units':'unconverted native raw lambda; not Newton force/pressure'}
    summaries.append({'label':label,'requested_Chest_delta_deg':s['requested_lean_deg'],'predicted_initial_support_gap_mm':s['actual_predicted_gap_m']*1000,'final_position_change_mm':last['position_change_m']*1000,'max_position_change_mm':max(row['position_change_m'] for row in rows)*1000,'final_SO3_change_deg':last['rotation_change_deg'],'max_SO3_change_deg':max(row['rotation_change_deg'] for row in rows),'late_2_to_5_net_position_mm':latep[-1]*1000,'late_2_to_5_max_position_from_2s_mm':max(latep)*1000,'late_2_to_5_net_SO3_deg':later[-1],'late_2_to_5_max_SO3_from_2s_deg':max(later),'max_native_Chest_change_from_own_initial_deg':max(row['Chest_change_deg'] for row in rows),'initial_position_W_m':rows[0]['position_W_m'],'final_position_W_m':last['position_W_m'],'final_below_actor_root_Z_min_by_mm':max(0,.65-last['position_W_m'][2])*1000,'contact_summary':contact_summary,'strap_initial':initial['strap_initial'],'native_videos':d['videos']})
checks['native_sources_pinned']=all(sha(path)==h for path,h in read(P/'source_before_native_v2.json').items())
checks['batch_source_pinned']=all(sha(path)==h for path,h in read(P/'source_addition_batch_v2.json').items())
checks['audit_inputs_unchanged']=all(sha(path)==h for path,h in inputs.items())
result={'passed':all(checks.values()),'checks':checks,'input_sha256':inputs,'summaries':summaries,'contact_scope':'query before60Hz control integration; conditional native contact+raw lambda, not calibrated Newton force','scope':'four source-clear five-second constant-initial-q PD trials, no music/checkpoint/policy/noise; late settling improves but initial pose retention not achieved; forearm contact predominates over transient upper-arm contact'}
with (P/'verification_v2.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps({'passed':result['passed'],'checks':len(checks),'summary':[{k:v for k,v in s.items() if k in ('label','final_position_change_mm','final_SO3_change_deg','late_2_to_5_net_position_mm','late_2_to_5_net_SO3_deg')} for s in summaries]},indent=2));assert result['passed'],checks
