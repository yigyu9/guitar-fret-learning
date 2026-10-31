"""Validate small fitted targets against native hand/guitar trajectories."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_correction_v1'
PREVIOUS=PHASE.parent/'palm_coupled_response_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    if (PHASE/'analysis.json').exists():raise FileExistsError('preserve previous analysis')
    path=PHASE/'fit_verified_v2/fit.json';hashes={str(path):sha(path)};fit=read(path)
    paths=[Path(p) for p in fit['input_sha256']]+[Path(__file__).resolve(),PHASE/'fit.json',PHASE/'fit_verification.json',
        PHASE/'fit_attempt_v1/fit_palm_coupled_correction.py',PHASE/'candidate_generation.json',PHASE/'execution.json',PHASE/'environment.json']
    labels=['baseline','quarter','half','full'];folders=[PREVIOUS/'baseline']+[PHASE/n for n in labels[1:]]
    paths += [p/(n+'.json') for p in folders for n in ('report','states','trace','tasks','contacts','controls')]
    paths += [ROOT/'stability_adapter_2/trials/palm_coupled_correction_v1'/(n+'.json') for n in labels[1:]]
    hashes.update({str(p):sha(p) for p in paths})
    original=read(PHASE/'fit.json');verification=read(PHASE/'fit_verification.json')
    if not all(fit['checks'].values()) or any(sha(p)!=h for p,h in fit['input_sha256'].items()):raise AssertionError('fit inputs')
    if any(original[k]!=fit[k] for k in original if k!='input_sha256') or sha(verification['original_fit_producer_snapshot'])!=verification['original_fit_source_sha256']:raise AssertionError('refit identity')
    for p,h in original['input_sha256'].items():
        source=verification['original_fit_producer_snapshot'] if p==str(ROOT/'stability_adapter_2/fit_palm_coupled_correction.py') else p
        if sha(source)!=h:raise AssertionError('original fit version seal')
    from .palm_side_feedback import context,np
    from .palm_normal_task import prepare,error_from_state
    from .build_fixed_lower_asset import pose,LOWER_BODIES
    from scipy.spatial.transform import Rotation
    ctx=prepare(context());boundary=read(PHASE.parent/'palm_contact_boundary_v1/analysis.json');goal_p=np.array(boundary['guitar_goal_position_W_m']);goal_q=np.array(boundary['guitar_goal_quaternion_xyzw']);goal_r=Rotation.from_quat(goal_q)
    response=read(PREVIOUS/'analysis.json');matrices=np.array(response['matrix_by_step_25x12x12']);baseline_y=np.c_[response['curves']['baseline']['hand_error_m_scaled_rad'],response['curves']['baseline']['guitar_error_W_m_rad']]
    base_target=np.array(read(PREVIOUS/'baseline/controls.json')[0]['final_target_rad']);summary=[];curves={};predictions={v['label']:v for v in fit['predictions']}
    for label,folder in zip(labels,folders):
        raw={n:read(folder/(n+'.json')) for n in ('report','states','trace','tasks','contacts','controls')};r=raw['report'];arm=r['arm_indices'];targets=np.array([v['final_target_rad'] for v in raw['controls']])
        if r['failure'] or not all(r['checks'].values()) or r['mode']!='bias' or r['physics_steps']!=24 or r['native_initializations']!=1:raise AssertionError('native contracts')
        if any(sha(p)!=h for p,h in r['source_sha256'].items()) or raw['states'][0]!=ctx['seed']:raise AssertionError('native seal/seed')
        if any(len(raw[n])!=25 for n in ('states','tasks','trace')) or any(len(raw[n])!=24 for n in ('contacts','controls')):raise AssertionError('coverage')
        if label=='baseline':expected=base_target
        else:
            candidate=read(ROOT/'stability_adapter_2/trials/palm_coupled_correction_v1'/(label+'.json'));prediction=predictions[label]
            if candidate['scale']!=prediction['scale'] or candidate['bias_rad']!=r['bias_rad'] or candidate['fit_source_sha256']!=sha(PHASE/'fit.json'):raise AssertionError('candidate identity')
            expected=ctx['q0'][arm].astype(np.float32)+np.array(candidate['bias_rad'],dtype=np.float32)
            if not np.array_equal(expected,prediction['actual_float32_target_rad']) or np.max(abs(expected-base_target))>.001+2e-7:raise AssertionError('fit delivered target')
        if not np.array_equal(targets,np.repeat(expected[None,:],24,axis=0)) or not ((targets>=np.array(r['lower_rad'])-2e-7)&(targets<=np.array(r['upper_rad'])+2e-7)).all():raise AssertionError('constant target bounds')
        outputs=[];gaps=[]
        for i,(state,task,trace) in enumerate(zip(raw['states'],raw['tasks'],raw['trace'])):
            if state['physics_step']!=i or abs(trace['time_s']-i/240)>1e-9 or error_from_state(state,ctx).tolist()!=task:raise AssertionError('task/time')
            if any(state['human_body_states'][r['human_body_names'].index(n)]!=ctx['seed']['human_body_states'][r['human_body_names'].index(n)] for n in ('Pelvis',)+LOWER_BODIES):raise AssertionError('fixed lower')
            gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq);rot=(gr*goal_r.inv()).as_rotvec();angle=float(np.degrees(2*np.arccos(np.clip(abs((gq/np.linalg.norm(gq))@goal_q),0,1))))
            if abs(np.linalg.norm(gp-goal_p)-trace['position_error_m'])>1e-10 or abs(angle-trace['rotation_error_deg'])>1e-12:raise AssertionError('guitar convention')
            outputs.append(np.r_[task,gp-goal_p,rot]);pp,pq=pose(state['human_body_states'][ctx['palm_index']])
            gaps.append(float((pp+Rotation.from_quat(pq).apply(ctx['local_point'])-(gp+gr.apply(ctx['goal_point_G']-ctx['normal_G']*.00005)))@gr.apply(ctx['normal_G']))*1000)
        if any(v['physics_step']!=i+1 for n in ('contacts','controls') for i,v in enumerate(raw[n])):raise AssertionError('sequence')
        y=np.array(outputs);delta=targets[0]-base_target;predicted=baseline_y+np.einsum('tij,j->ti',matrices,delta);difference=y-predicted
        if not np.isfinite(y).all() or r['minimum_source_palm_up_proxy_z']<=0 or r['rest_length_m']!=1.1018469719600776:raise AssertionError('finite/up/rest')
        palm=[(v['physics_step'],c) for v in raw['contacts'] for c in v['contacts'] if {c['body0_name'],c['body1_name']}=={'human/LH:palm','guitar/guitar'}];positive=[(s,c) for s,c in palm if c['lambda']>0]
        summary.append({'label':label,'end_point_error_mm':float(np.linalg.norm(y[-1,:3])*1000),'end_source_normal_gap_mm':gaps[-1],'end_normal_angle_deg':float(np.linalg.norm(y[-1,3:6])/.08*180/np.pi),
            'max_guitar_position_error_mm':max(t['position_error_m'] for t in raw['trace'])*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in raw['trace']),
            'positive_raw_palm_lambda_steps':sorted({s for s,c in positive}),'positive_raw_palm_lambda_rows':len(positive),'palm_contact_steps':sorted({s for s,c in palm}),
            'max_actual_torso_drift_deg':float(np.abs([t['torso_drift_deg'] for t in raw['trace']]).max()),'applied_delta_rad':delta.tolist(),
            'terminal_prediction_difference':{'hand_position_mm':float(np.linalg.norm(difference[-1,:3])*1000),'hand_normal_rotvec_deg':float(np.linalg.norm(difference[-1,3:6])/.08*180/np.pi),'guitar_position_mm':float(np.linalg.norm(difference[-1,6:9])*1000),'guitar_rotvec_deg':float(np.linalg.norm(difference[-1,9:])*180/np.pi)}})
        curves[label]={'time_s':[t['time_s'] for t in raw['trace']],'hand_error_m_scaled_rad':y[:,:6].tolist(),'guitar_error_W_m_rad':y[:,6:].tolist(),'source_normal_gap_mm':gaps,
            'predicted_outputs_12':predicted.tolist(),'step_max_raw_palm_lambda':[max((c['lambda'] for s,c in palm if s==i),default=0) for i in range(1,25)]}
    checks={'four_conditions_native_contracts_and_tasks':True,'fit_original_and_cached_refit_numeric_identity':True,'actual_float32_targets_and_bounds':True,
        'all_three_native_executions_exit_zero':len(read(PHASE/'execution.json'))==3 and all(r['exit_code']==0 for r in read(PHASE/'execution.json')),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    result={'checks':checks,'input_sha256':hashes,'counts':{'native_initializations':3,'physics_steps':72},'summary':summary,'curves':curves,
        'requested_bound_active_axes':[i for i,v in enumerate(fit['bias_delta_rad']) if abs(v)>=.001-1e-12],
        'scope':'three new .1s constant target trials with saved baseline; free guitar and unchanged initial q/strap/PD; transient raw lambda not support success; predicted vs actual not a formal accuracy gate; no feedback or final adoption'}
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'summary':summary},indent=2))


if __name__=='__main__':main()
