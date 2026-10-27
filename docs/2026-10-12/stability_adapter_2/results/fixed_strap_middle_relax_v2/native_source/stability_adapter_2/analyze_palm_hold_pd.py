"""Compare saved native left-arm PD trials, including source gap and guitar drift."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2'
OBSERVATION=PHASE.parent/'palm_hold_observation_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    if (PHASE/'analysis.json').exists():raise FileExistsError('preserve previous analysis')
    labels=('scale_1','scale_1p5','scale_2');hashes={};pd={};first={};first_phase=PHASE.parent/'palm_hold_pd_v1'
    for label in labels:
        p=PHASE/label/'PD.json';hashes[str(p)]=sha(p);pd[label]=read(p)
        p=first_phase/label/'PD.json';hashes[str(p)]=sha(p);first[label]=read(p)
    paths=[Path(p) for a in list(pd.values())+list(first.values()) for p in a['input_sha256']]+[Path(__file__).resolve(),PHASE/'execution.json',PHASE/'environment.json',first_phase/'execution.json',first_phase/'validation_gap.json']
    paths += [PHASE/label/'native'/(n+'.json') for label in labels for n in ('report','states','trace','tasks','contacts','controls')]
    paths += [first_phase/label/'native'/(n+'.json') for label in labels for n in ('report','states','trace','tasks','contacts','controls')]
    hashes.update({str(p):sha(p) for p in paths})
    from .palm_side_feedback import context,np
    from .palm_normal_task import prepare,error_from_state
    from .build_fixed_lower_asset import pose,LOWER_BODIES
    from scipy.spatial.transform import Rotation
    ctx=prepare(context());reference=OBSERVATION/'full/native';baseline_props=read(OBSERVATION/'analysis.json')['properties']['drive_properties']
    initial=read(reference/'states.json')[0];base_controls=read(reference/'controls.json');summary=[];curves={}
    for label in labels:
        a=pd[label];scale=a['trial']['left_arm_PD_scale'];folder=PHASE/label/'native';raw={n:read(folder/(n+'.json')) for n in ('report','states','trace','tasks','contacts','controls')};r=raw['report'];arm=r['arm_indices'];prop=a['properties']
        if not all(a['checks'].values()) or any(sha(p)!=h for p,h in a['input_sha256'].items()):raise AssertionError('PD contracts/seal')
        if not all(first[label]['checks'].values()) or any(sha(p)!=h for p,h in first[label]['input_sha256'].items()):raise AssertionError('first attempt seal')
        if any(raw[n]!=read(first_phase/label/'native'/(n+'.json')) for n in ('states','trace','tasks','contacts','controls')):raise AssertionError('setter check changed physical arrays')
        if r['failure'] or not all(r['checks'].values()) or r['physics_steps']!=24 or r['native_initializations']!=1 or r['mode']!='bias':raise AssertionError('native contracts')
        if any(sha(p)!=h for p,h in r['source_sha256'].items()) or raw['states'][0]!=initial or initial!=ctx['seed']:raise AssertionError('initial/source')
        if any(len(raw[n])!=25 for n in ('states','trace','tasks')) or any(len(raw[n])!=24 for n in ('contacts','controls')):raise AssertionError('coverage')
        if prop['before']!=baseline_props or prop['left_arm_indices']!=arm or len(arm)!=12:raise AssertionError('baseline native properties')
        for field,values in prop['before'].items():
            expected=[v*scale if field in ('stiffness','damping') and i in arm else v for i,v in enumerate(values)]
            if prop['after'][field]!=expected:raise AssertionError('left-arm-only property change')
        if r['pd_kp']!=prop['after']['stiffness'] or r['pd_kd']!=prop['after']['damping']:raise AssertionError('runner PD readback')
        if any(v['final_target_rad']!=base_controls[i]['final_target_rad'] or v['physics_step']!=i+1 for i,v in enumerate(raw['controls'])):raise AssertionError('same commands')
        if scale==1 and any(raw[n]!=read(reference/(n+'.json')) for n in ('states','trace','tasks','contacts','controls')):raise AssertionError('baseline exact')
        gaps=[];joint_errors=[];joint_velocities=[]
        for i,(state,task,trace) in enumerate(zip(raw['states'],raw['tasks'],raw['trace'])):
            if state['physics_step']!=i or abs(trace['time_s']-i/240)>1e-9 or error_from_state(state,ctx).tolist()!=task:raise AssertionError('time/task')
            if any(state['human_body_states'][r['human_body_names'].index(n)]!=initial['human_body_states'][r['human_body_names'].index(n)] for n in ('Pelvis',)+LOWER_BODIES):raise AssertionError('fixed lower')
            gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq);pp,pq=pose(state['human_body_states'][ctx['palm_index']])
            gaps.append(float((pp+Rotation.from_quat(pq).apply(ctx['local_point'])-(gp+gr.apply(ctx['goal_point_G']-ctx['normal_G']*.00005)))@gr.apply(ctx['normal_G']))*1000)
            joint_errors.append([state['human_dof_states'][j]['pos']-base_controls[0]['final_target_rad'][k] for k,j in enumerate(arm)])
            joint_velocities.append([state['human_dof_states'][j]['vel'] for j in arm])
        if r['rest_length_m']!=1.1018469719600776 or r['minimum_source_palm_up_proxy_z']<=0:raise AssertionError('rest/up')
        if any(v['physics_step']!=i+1 for i,v in enumerate(raw['contacts'])):raise AssertionError('contact time')
        palm=[(v['physics_step'],c) for v in raw['contacts'] for c in v['contacts'] if {c['body0_name'],c['body1_name']}=={'human/LH:palm','guitar/guitar'}];positive=[(s,c) for s,c in palm if c['lambda']>0]
        points=[float(np.linalg.norm(t[:3])*1000) for t in raw['tasks']]
        summary.append({'label':label,'PD_scale':scale,'end_point_error_mm':points[-1],'max_point_error_mm':max(points),'end_source_normal_gap_mm':gaps[-1],
            'end_normal_angle_deg':float(np.linalg.norm(raw['tasks'][-1][3:])/.08*180/np.pi),
            'max_guitar_position_error_mm':max(t['position_error_m'] for t in raw['trace'])*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in raw['trace']),
            'end_guitar_position_error_mm':raw['trace'][-1]['position_error_m']*1000,'end_guitar_rotation_error_deg':raw['trace'][-1]['rotation_error_deg'],
            'positive_raw_palm_lambda_steps':sorted({s for s,c in positive}),'positive_raw_palm_lambda_rows':len(positive),'palm_contact_steps':sorted({s for s,c in palm}),
            'max_actual_torso_drift_deg':float(np.abs([t['torso_drift_deg'] for t in raw['trace']]).max()),'terminal_native_coordinate_error_rad':joint_errors[-1]})
        curves[label]={'time_s':[t['time_s'] for t in raw['trace']],'point_error_mm':points,'source_normal_gap_mm':gaps,
            'guitar_position_error_mm':[t['position_error_m']*1000 for t in raw['trace']],'guitar_rotation_error_deg':[t['rotation_error_deg'] for t in raw['trace']],
            'step_max_raw_palm_lambda':[max((c['lambda'] for s,c in palm if s==i),default=0) for i in range(1,25)],
            'native_coordinate_error_rad':joint_errors,'native_velocity_rad_s':joint_velocities}
    execution=read(PHASE/'execution.json')
    checks={'three_native_contracts_and_initial_state':True,'left12_kp_kd_only_and_same_targets':True,'baseline_five_arrays_exact':True,'setter_check_repeats_first_attempt_five_arrays':True,
        'three_executions_exit_zero':len(execution)==3 and [v['label'] for v in execution]==list(labels) and all(v['exit_code']==0 for v in execution),
        'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    result={'checks':checks,'input_sha256':hashes,'counts':{'native_initializations':3,'physics_steps':72},'summary':summary,'curves':curves,
        'earlier_validation_gap_counts':{'native_initializations':3,'physics_steps':72},
        'scope':'same initial pose/strap/targets; left12 kp/kd scale only; source gap is not cooked clearance, raw lambda is not N; 0.1s diagnosis, no feedback or stability success; coordinate components are not whole-joint SO3 errors'}
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'summary':summary},indent=2))


if __name__=='__main__':main()
