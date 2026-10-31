"""Identify hand and guitar finite responses around a transient contact condition."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1'
PREVIOUS=PHASE.parent/'palm_contact_boundary_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    if (PHASE/'analysis.json').exists():raise FileExistsError('preserve previous analysis')
    path=PHASE/'candidate_generation.json';hashes={str(path):sha(path)};manifest=read(path)
    labels=[r['label'] for r in manifest['candidates']]
    paths=[Path(p) for p in manifest['input_sha256']]+[Path(__file__).resolve(),PHASE/'execution.json',PHASE/'environment.json']
    paths += [Path(r['candidate_path']) for r in manifest['candidates']]
    paths += [PHASE/label/(n+'.json') for label in labels for n in ('report','states','trace','tasks','contacts','controls')]
    paths += [PREVIOUS/'alpha_45'/(n+'.json') for n in ('report','states','trace','tasks','contacts','controls')]
    hashes.update({str(p):sha(p) for p in paths})
    if any(sha(p)!=h for p,h in manifest['input_sha256'].items()):raise AssertionError('generation input seal')
    from .palm_side_feedback import context,np
    from .palm_normal_task import prepare,error_from_state
    from .build_fixed_lower_asset import pose,LOWER_BODIES
    from scipy.spatial.transform import Rotation
    ctx=prepare(context());boundary=read(PREVIOUS/'analysis.json');goal_p=np.array(boundary['guitar_goal_position_W_m']);goal_q=np.array(boundary['guitar_goal_quaternion_xyzw']);goal_r=Rotation.from_quat(goal_q)
    runs={};curves={};summary=[]
    for item in manifest['candidates']:
        label=item['label'];raw={n:read(PHASE/label/(n+'.json')) for n in ('report','states','trace','tasks','contacts','controls')};r=raw['report'];candidate=read(item['candidate_path'])
        if sha(item['candidate_path'])!=item['sha256'] or any(sha(p)!=h for p,h in r['source_sha256'].items()):raise AssertionError('native inputs')
        if r['failure'] or not all(r['checks'].values()) or r['mode']!='bias' or r['physics_steps']!=24 or r['native_initializations']!=1:raise AssertionError('native contracts')
        if any(len(raw[n])!=25 for n in ('states','tasks','trace')) or any(len(raw[n])!=24 for n in ('controls','contacts')) or raw['states'][0]!=ctx['seed']:raise AssertionError('initial coverage')
        arm=r['arm_indices'];targets=np.array([v['final_target_rad'] for v in raw['controls']]);expected=ctx['q0'][arm].astype(np.float32)+np.array(candidate['bias_rad'],dtype=np.float32)
        if candidate['bias_rad']!=r['bias_rad'] or not np.array_equal(targets,np.repeat(expected[None,:],24,axis=0)):raise AssertionError('actual target identity')
        if not ((targets>=np.array(r['lower_rad'])-2e-7)&(targets<=np.array(r['upper_rad'])+2e-7)).all():raise AssertionError('target box')
        outputs=[]
        for i,(state,task,trace) in enumerate(zip(raw['states'],raw['tasks'],raw['trace'])):
            if state['physics_step']!=i or abs(trace['time_s']-i/240)>1e-9 or error_from_state(state,ctx).tolist()!=task:raise AssertionError('task/time')
            if any(state['human_body_states'][r['human_body_names'].index(n)]!=ctx['seed']['human_body_states'][r['human_body_names'].index(n)] for n in ('Pelvis',)+LOWER_BODIES):raise AssertionError('fixed lower')
            gp,gq=pose(state['guitar_body_states'][0]);rot=(Rotation.from_quat(gq)*goal_r.inv()).as_rotvec();angle=float(np.degrees(2*np.arccos(np.clip(abs((gq/np.linalg.norm(gq))@goal_q),0,1))))
            if abs(np.linalg.norm(gp-goal_p)-trace['position_error_m'])>1e-10 or abs(angle-trace['rotation_error_deg'])>1e-12:raise AssertionError('guitar conventions')
            outputs.append(np.r_[task,gp-goal_p,rot])
        if any(v['physics_step']!=i+1 for n in ('controls','contacts') for i,v in enumerate(raw[n])):raise AssertionError('command/contact sequence')
        y=np.array(outputs)
        if not np.isfinite(y).all() or r['minimum_source_palm_up_proxy_z']<=0 or r['rest_length_m']!=1.1018469719600776:raise AssertionError('finite/up/rest')
        palm=[(v['physics_step'],c) for v in raw['contacts'] for c in v['contacts'] if {c['body0_name'],c['body1_name']}=={'human/LH:palm','guitar/guitar'}];positive=[(s,c) for s,c in palm if c['lambda']>0]
        runs[label]={'raw':raw,'target':targets[0],'y':y};curves[label]={'time_s':[t['time_s'] for t in raw['trace']],'hand_error_m_scaled_rad':y[:,:6].tolist(),'guitar_error_W_m_rad':y[:,6:].tolist(),
            'step_max_raw_palm_lambda':[max((c['lambda'] for s,c in palm if s==i),default=0) for i in range(1,25)]}
        summary.append({'label':label,'end_point_error_mm':float(np.linalg.norm(y[-1,:3])*1000),'end_normal_angle_deg':float(np.linalg.norm(y[-1,3:6])/.08*180/np.pi),
            'max_guitar_position_error_mm':max(t['position_error_m'] for t in raw['trace'])*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in raw['trace']),
            'positive_raw_palm_lambda_steps':sorted({s for s,c in positive}),'positive_raw_palm_lambda_rows':len(positive),'palm_contact_steps':sorted({s for s,c in palm}),
            'max_actual_torso_drift_deg':float(np.abs([t['torso_drift_deg'] for t in raw['trace']]).max())})
    baseline=runs['baseline'];columns=[];deltas=[]
    for i in range(12):
        probe=runs['axis_'+str(i).zfill(2)];delta=probe['target']-baseline['target']
        if np.count_nonzero(delta)!=1 or delta[i]==0:raise AssertionError('single applied probe')
        columns.append((probe['y']-baseline['y'])/delta[i]);deltas.append(delta[i])
    matrices=np.stack(columns,axis=2);matrix=matrices[-1];heldout=runs['heldout'];heldout_delta=heldout['target']-baseline['target'];predicted=baseline['y']+np.einsum('tij,j->ti',matrices,heldout_delta);difference=heldout['y']-predicted
    def norms(v):return {'hand_position_mm':float(np.linalg.norm(v[:3])*1000),'hand_normal_rotation_vector_deg':float(np.linalg.norm(v[3:6])/.08*180/np.pi),'guitar_position_mm':float(np.linalg.norm(v[6:9])*1000),'guitar_rotation_vector_deg':float(np.linalg.norm(v[9:])*180/np.pi)}
    exact={n:baseline['raw'][n]==read(PREVIOUS/'alpha_45'/(n+'.json')) for n in ('states','trace','tasks','contacts','controls')}
    checks={'14_native_contracts_and_coverage':True,'same_initial_actual_float32_targets_and_bounds':True,'baseline_5_raw_exact_previous_alpha45':all(exact.values()),
        'actual_single_axis_probe_deltas':True,'all_14_execution_exit_zero':len(read(PHASE/'execution.json'))==14 and all(r['exit_code']==0 for r in read(PHASE/'execution.json')),
        'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    result={'checks':checks,'input_sha256':hashes,'counts':{'native_initializations':14,'physics_steps':336},'summary':summary,'curves':curves,
        'matrix_terminal_12x12':matrix.tolist(),'matrix_by_step_25x12x12':matrices.tolist(),'applied_probe_delta_rad':deltas,'singular_values_unscaled_mixed_units':np.linalg.svd(matrix,compute_uv=False).tolist(),
        'heldout':{'applied_delta_rad':heldout_delta.tolist(),'predicted_terminal':predicted[-1].tolist(),'actual_terminal':heldout['y'][-1].tolist(),'terminal_prediction_difference':norms(difference[-1]),
            'prediction_difference_by_step':[norms(v) for v in difference]},'baseline_repeat_exact':exact,
        'scope':'constant PD targets at identical initial state, .1s response d(output)/d(applied target); rows hand desired-minus-actual position and .08 normal rotvec, then guitar actual-minus-configured-goal WORLD position and SO3 rotvec; mixed units singular values are not conditioning certification; no feedback Jacobian or support success'}
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'summary':summary,'heldout':result['heldout']['terminal_prediction_difference']},indent=2))


if __name__=='__main__':main()
