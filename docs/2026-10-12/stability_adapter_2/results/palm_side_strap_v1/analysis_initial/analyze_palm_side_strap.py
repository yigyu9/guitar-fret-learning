"""Verify saved fixed-length strap trials and actual support observations."""
import json
from pathlib import Path
from scipy.spatial.transform import Rotation
from .run_palm_side_strap import PHASE,PREVIOUS
from .palm_side_feedback import context,np
from .palm_normal_task import prepare,error_from_state
from .build_fixed_lower_asset import read,sha,pose
from .analyze_palm_side_feedback import finite
from .strap import cable_forces


def main():
    candidate_path=Path(__file__).with_name('trials')/'palm_side_strap_v1/candidates.json'
    candidate_inputs=read(PHASE/'candidate_inputs.json')
    config_path=Path(__file__).with_name('config.json')
    candidates=read(candidate_path);config=read(config_path)['strap']
    paths=[candidate_path,config_path,PHASE/'candidate_inputs.json',Path(__file__).resolve(),Path(__file__).with_name('analyze_palm_side_feedback.py')]
    paths += [Path(p) for p in candidate_inputs['input_sha256']]
    folders=[PHASE/c['label']/stage for c in candidates for stage in ('first_step','short')]+[PHASE/'native_initial_10n']
    paths += [PHASE/name for name in ('execution_first.json','execution_short.json','execution_camera.json','environment.json')]
    for folder in folders:
        paths += [folder/(name+'.json') for name in ('report','states','trace','normal_tasks','tasks','controls','contacts')]
        r=read(folder/'report.json');paths += [Path(p) for p in r['source_sha256']]+[Path(p) for p in r['images']]
    hashes={str(p):sha(p) for p in paths};ctx=prepare(context());checks={};summaries=[];raw_by_folder={};counts={'native_initializations':0,'physics_steps':0}
    if any(sha(Path(p))!=h for p,h in candidate_inputs['input_sha256'].items()):raise AssertionError('candidate source SHA')
    for folder in folders:
        r=read(folder/'report.json');raw={n:read(folder/(n+'.json')) for n in ('states','trace','normal_tasks','tasks','controls','contacts')};steps=r['physics_steps']
        expected=1 if folder.name=='first_step' else 24
        if r['failure'] is not None or not all(r['checks'].values()) or steps!=expected or r['native_initializations']!=1:raise AssertionError('trial identity/contracts')
        if not finite(raw) or not all(len(raw[n])==steps+1 for n in ('states','trace','normal_tasks','tasks')) or not all(len(raw[n])==steps for n in ('controls','contacts')):raise AssertionError('coverage/finite')
        if not all(s['physics_step']==i and error_from_state(s,ctx).tolist()==raw['normal_tasks'][i]==raw['tasks'][i] for i,s in enumerate(raw['states'])):raise AssertionError('state task sequence')
        if not all(v['physics_step']==i+1 for n in ('controls','contacts') for i,v in enumerate(raw[n])) or not all(v['updated_before_step']==(i%4==0) for i,v in enumerate(raw['controls'])):raise AssertionError('step/update schedule')
        if not all(abs(t['time_s']-i/240)<1e-9 for i,t in enumerate(raw['trace'])):raise AssertionError('time coverage')
        if any(sha(Path(p))!=h for p,h in r['source_sha256'].items()):raise AssertionError('production SHA')
        settings=read(Path(r['settings_path']));rest=settings['strap_rest_length_m']
        if r['rest_length_m']!=rest or not all(t['strap_rest_length_m']==rest for t in raw['trace']):raise AssertionError('fixed absolute length')
        initial=raw['trace'][0]
        t0=cable_forces(np.array(initial['route_points_m']),np.array(initial['route_point_velocities_mps']),rest,config['stiffness_n_per_m'],config['damping_n_s_per_m'],config['max_tension_n'])[1]
        if abs(t0-r['initial_law_tension_n'])>1e-9:raise AssertionError('initial passive tension')
        for i,t in enumerate(raw['trace'][:-1]):
            tension=cable_forces(np.array(t['route_points_m']),np.array(t['route_point_velocities_mps']),rest,config['stiffness_n_per_m'],config['damping_n_s_per_m'],config['max_tension_n'])[1]
            if abs(tension-raw['trace'][i+1]['last_applied_tension_n'])>1e-9:raise AssertionError('pre-step passive tension timing')
        counts['native_initializations']+=1;counts['physics_steps']+=steps;raw_by_folder[str(folder)]=raw
    checks['all_nine_contracts_coverage_tasks_inputs']=True
    checks['passive_tension_recomputed_before_each_step']=True
    for c in candidates:
        first=raw_by_folder[str(PHASE/c['label']/'first_step')];raw=raw_by_folder[str(PHASE/c['label']/'short')]
        for n in raw:
            count=2 if n in ('states','trace','normal_tasks','tasks') else 1
            if first[n]!=raw[n][:count]:raise AssertionError('short first-step prefix mismatch')
        r=read(PHASE/c['label']/'short/report.json');normal=np.array(raw['normal_tasks']);trace=raw['trace']
        if abs(c['initial_route_m']-trace[0]['strap_length_m'])>1e-12 or c['rest_length_m']!=r['rest_length_m'] or abs(c['initial_tension_law_n']-r['initial_law_tension_n'])>1e-9:raise AssertionError('candidate identity')
        pairs=[(row['physics_step'],v) for row in raw['contacts'] for v in row['contacts']]
        palms=[(step,v) for step,v in pairs if {v['body0_name'],v['body1_name']}=={'human/LH:palm','guitar/guitar'}]
        hip=[(step,v) for step,v in pairs if {v['body0_name'],v['body1_name']}=={'human/R_Hip','guitar/G:body'}]
        state=raw['states'][-1];pp,pq=pose(state['human_body_states'][ctx['palm_index']]);gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq)
        delta=pp+Rotation.from_quat(pq).apply(ctx['local_point'])-(gp+gr.apply(ctx['goal_point_G']-ctx['normal_G']*.00005));ng=gr.apply(ctx['normal_G']);gap=float(delta@ng)
        summaries.append({'label':c['label'],'rest_length_m':r['rest_length_m'],'initial_tension_law_n':r['initial_law_tension_n'],
            'first_step_guitar_position_error_mm':trace[1]['position_error_m']*1000,'first_step_guitar_rotation_error_deg':trace[1]['rotation_error_deg'],
            'max_guitar_position_error_mm':max(t['position_error_m'] for t in trace)*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in trace),
            'max_applied_tension_n':max(t['last_applied_tension_n'] for t in trace),'end_applied_tension_n':trace[-1]['last_applied_tension_n'],
            'end_linear_speed_mps':trace[-1]['linear_speed_mps'],'end_angular_speed_rad_s':trace[-1]['angular_speed_rad_s'],
            'max_point_error_mm':float(np.linalg.norm(normal[:,:3],axis=1).max()*1000),'max_normal_angle_deg':float(np.linalg.norm(normal[:,3:],axis=1).max()/.08*180/np.pi),
            'end_normal_gap_mm':gap*1000,'end_tangent_distance_mm':float(np.linalg.norm(delta-gap*ng)*1000),
            'palm_contact_steps':sorted({step for step,v in palms}),'palm_contact_rows':len(palms),'positive_raw_palm_lambda_steps':sorted({step for step,v in palms if v['lambda']>0}),
            'positive_raw_palm_lambda_rows':sum(v['lambda']>0 for step,v in palms),'max_raw_palm_lambda':max((v['lambda'] for step,v in palms),default=0),
            'hip_contact_steps':sorted({step for step,v in hip}),'positive_raw_hip_lambda_rows':sum(v['lambda']>0 for step,v in hip),
            'positive_raw_self_lambda_rows':sum(v['lambda']>0 and v['body0_name'].startswith('human/') and v['body1_name'].startswith('human/') for step,v in pairs),
            'max_actual_torso_drift_deg':float(np.abs([t['torso_drift_deg'] for t in trace]).max()),'minimum_source_palm_up_proxy_z':r['minimum_source_palm_up_proxy_z']})
    checks['first_step_prefix_exact_and_candidates_match']=True
    cam=raw_by_folder[str(PHASE/'native_initial_10n')];head=raw_by_folder[str(PHASE/'initial_10n/short')]
    checks['camera_six_raw_exact']=cam==head
    checks['camera_images_sha']=all(sha(Path(p))==v['sha256'] for p,v in read(PHASE/'native_initial_10n/report.json')['images'].items())
    checks['native_counts_9_init_124_steps']=counts=={'native_initializations':9,'physics_steps':124}
    checks['executions_exit_zero']=all(r['exit_code']==0 for name in ('execution_first.json','execution_short.json') for r in read(PHASE/name)) and read(PHASE/'execution_camera.json')['exit_code']==0
    for name in ('palm_normal_control_v1','palm_support_weight_v1'):
        inventory=read(PREVIOUS.parent/name/'artifact_inventory.json');checks[name+'_preserved']=all(sha(Path(p))==v['sha256'] for p,v in inventory.items())
    checks['inputs_unchanged']=all(sha(Path(p))==h for p,h in hashes.items())
    output={'checks':checks,'summary':summaries,'counts':counts,'input_sha256':hashes,'scope':'short actual passive strap comparison; no sustained-support/playing success threshold; postprocessing 0 native/0 physics'}
    (PHASE/'analysis.json').write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    if not all(checks.values()):raise AssertionError(checks)
    print(json.dumps({'checks':checks,'summary':summaries,'counts':counts},indent=2))


if __name__=='__main__':main()
