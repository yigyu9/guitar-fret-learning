"""Measure coupled palm/guitar response across a saved scalar bias sweep."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_contact_boundary_v1'
PREVIOUS=PHASE.parent/'palm_finite_response_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    if (PHASE/'analysis.json').exists():raise FileExistsError('preserve existing analysis')
    calibration_path=PREVIOUS/'calibration.json';hashes={str(calibration_path):sha(calibration_path)};calibration=read(calibration_path)
    folders=[PREVIOUS/'validation/corrected_quarter']+[PHASE/('alpha_'+str(i)) for i in (30,35,40,45)]+[PREVIOUS/'validation/corrected_half']
    alphas=(.25,.30,.35,.40,.45,.50)
    paths=[Path(p) for p in calibration['input_sha256']]+[Path(__file__).resolve(),PREVIOUS/'artifact_inventory.json',
        PHASE/'execution.json',PHASE/'environment.json',PHASE/'candidate_generation.json']
    paths += [folder/(n+'.json') for folder in folders for n in ('report','states','trace','tasks','contacts','controls')]
    paths += list((ROOT/'stability_adapter_2/trials/palm_contact_boundary_v1').glob('*.json'))
    hashes.update({str(p):sha(p) for p in paths})
    from .palm_side_feedback import context,np
    from .palm_normal_task import prepare,error_from_state
    from .build_fixed_lower_asset import pose,LOWER_BODIES
    from scipy.spatial.transform import Rotation
    ctx=prepare(context());goal_p,goal_q=pose(ctx['seed']['guitar_body_states'][0]);goal_r=Rotation.from_quat(goal_q)
    rows=[];curves={};counts={'native_initializations':0,'physics_steps':0}
    for alpha,folder in zip(alphas,folders):
        raw={n:read(folder/(n+'.json')) for n in ('report','states','trace','tasks','contacts','controls')};r=raw['report']
        if r['failure'] or not all(r['checks'].values()) or r['mode']!='bias' or r['physics_steps']!=24 or r['native_initializations']!=1:raise AssertionError('run contracts')
        if any(sha(p)!=h for p,h in r['source_sha256'].items()):raise AssertionError('native input seal')
        if raw['states'][0]!=ctx['seed'] or any(len(raw[n])!=25 for n in ('states','trace','tasks')) or any(len(raw[n])!=24 for n in ('contacts','controls')):raise AssertionError('initial/coverage')
        targets=np.array([v['final_target_rad'] for v in raw['controls']]);arm=r['arm_indices']
        if not np.array_equal(targets,np.repeat(targets[:1],24,axis=0)) or not ((targets>=np.array(r['lower_rad'])-2e-7)&(targets<=np.array(r['upper_rad'])+2e-7)).all():raise AssertionError('constant bounded target')
        errors=[];gap=[]
        for i,state in enumerate(raw['states']):
            if state['physics_step']!=i or abs(raw['trace'][i]['time_s']-i/240)>1e-9:raise AssertionError('step/time')
            if error_from_state(state,ctx).tolist()!=raw['tasks'][i]:raise AssertionError('measured palm task')
            if any(state['human_body_states'][r['human_body_names'].index(n)]!=raw['states'][0]['human_body_states'][r['human_body_names'].index(n)] for n in ('Pelvis',)+LOWER_BODIES):raise AssertionError('fixed lower')
            gp,gq=pose(state['guitar_body_states'][0]);gr=Rotation.from_quat(gq);rotation=(gr*goal_r.inv()).as_rotvec();errors.append(np.r_[gp-goal_p,rotation].tolist())
            if abs(np.linalg.norm(gp-goal_p)-raw['trace'][i]['position_error_m'])>1e-10 or abs(np.linalg.norm(rotation)*180/np.pi-raw['trace'][i]['rotation_error_deg'])>1e-8:raise AssertionError('guitar error convention')
            pp,pq=pose(state['human_body_states'][ctx['palm_index']]);delta=pp+Rotation.from_quat(pq).apply(ctx['local_point'])-(gp+gr.apply(ctx['goal_point_G']-ctx['normal_G']*.00005));gap.append(float(delta@gr.apply(ctx['normal_G']))*1000)
        pairs=[(v['physics_step'],c) for v in raw['contacts'] for c in v['contacts'] if {c['body0_name'],c['body1_name']}=={'human/LH:palm','guitar/guitar'}]
        positive=[(s,c) for s,c in pairs if c['lambda']>0];task=np.array(raw['tasks']);trace=raw['trace'];error=np.array(errors)
        if not np.isfinite(error).all() or r['minimum_source_palm_up_proxy_z']<=0 or r['rest_length_m']!=1.1018469719600776:raise AssertionError('finite/palm-up/rest')
        rows.append({'alpha':alpha,'label':folder.name,'run_path':str(folder),'end_point_error_mm':float(np.linalg.norm(task[-1,:3])*1000),
            'end_source_normal_gap_mm':gap[-1],'end_normal_angle_deg':float(np.linalg.norm(task[-1,3:])/.08*180/np.pi),
            'max_guitar_position_error_mm':max(t['position_error_m'] for t in trace)*1000,'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in trace),
            'end_guitar_error_W_m_rad':errors[-1],'palm_contact_steps':sorted({s for s,c in pairs}),
            'positive_raw_palm_lambda_steps':sorted({s for s,c in positive}),'positive_raw_palm_lambda_rows':len(positive),'max_raw_palm_lambda':max((c['lambda'] for s,c in pairs),default=0),
            'minimum_source_palm_up_proxy_z':r['minimum_source_palm_up_proxy_z'],'max_actual_torso_drift_deg':float(np.abs([t['torso_drift_deg'] for t in trace]).max())})
        curves[str(alpha)]={'time_s':[t['time_s'] for t in trace],'guitar_error_W_m_rad':errors,'source_normal_gap_mm':gap,
            'point_error_mm':(np.linalg.norm(task[:,:3],axis=1)*1000).tolist(),'step_max_raw_palm_lambda':[max((c['lambda'] for s,c in pairs if s==i),default=0) for i in range(1,25)]}
        if folder.parent==PHASE:counts['native_initializations']+=1;counts['physics_steps']+=24
    secants=[{'alpha_interval':[a['alpha'],b['alpha']],
        'guitar_terminal_secant_W_m_rad_per_alpha':((np.array(b['end_guitar_error_W_m_rad'])-a['end_guitar_error_W_m_rad'])/(b['alpha']-a['alpha'])).tolist()} for a,b in zip(rows,rows[1:])]
    checks={'six_constant_trials_initial_tasks_guitar_conventions_verified':True,'new_counts_4_init_96_steps':counts=={'native_initializations':4,'physics_steps':96},
        'all_four_native_executions_exit_zero':len(read(PHASE/'execution.json'))==4 and all(r['exit_code']==0 for r in read(PHASE/'execution.json')),
        'previous_phase_preserved':all(sha(p)==v['sha256'] for p,v in read(PREVIOUS/'artifact_inventory.json').items()),
        'fit_inputs_unchanged':all(sha(p)==h for p,h in calibration['input_sha256'].items()),'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    result={'checks':checks,'input_sha256':hashes,'counts':counts,'summary':rows,'curves':curves,'secants':secants,
        'scope':'six scalar alpha samples, four new native trials; WORLD guitar actual-minus-initial position and SO3 rotvec, not Euler/DOF coordinate differences; contact rows/raw lambda not loaded-support certification'}
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'counts':counts,'summary':rows},indent=2))


if __name__=='__main__':main()
