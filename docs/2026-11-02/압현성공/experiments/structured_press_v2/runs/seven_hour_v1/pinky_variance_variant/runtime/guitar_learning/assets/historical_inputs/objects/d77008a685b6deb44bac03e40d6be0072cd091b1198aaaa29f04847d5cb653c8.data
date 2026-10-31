"""Fit a bounded bias correction from saved native 0.1s target responses."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_finite_response_v1'
CALIBRATION=PHASE.parent/'palm_normal_control_v1/cap_0p3/calibration.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    output=PHASE/'calibration.json';candidate_path=ROOT/'stability_adapter_2/trials/palm_finite_response_v1/corrected.json'
    if output.exists() or candidate_path.exists():raise FileExistsError('preserve previous fit')
    hashes={str(CALIBRATION):sha(CALIBRATION)};old=read(CALIBRATION)
    labels=['baseline']+['axis_'+str(i).zfill(2) for i in range(12)]+['heldout']
    paths=[Path(p) for p in old['input_sha256']]+[Path(__file__).resolve(),PHASE/'execution.json',PHASE/'environment.json',PHASE/'candidate_generation.json']
    paths += [ROOT/'stability_adapter_2/trials/palm_finite_response_v1'/(label+'.json') for label in labels]
    paths += [PHASE/'calibration_runs'/label/(name+'.json') for label in labels for name in ('report','states','trace','tasks','contacts','controls')]
    paths += [ROOT/'stability_adapter_2/run_palm_finite_response.py']
    hashes.update({str(p):sha(p) for p in paths})
    if any(hashes[p]!=h for p,h in old['input_sha256'].items()):raise AssertionError('calibration inputs changed')
    from .palm_side_feedback import context,np
    from .palm_normal_task import prepare,error_from_state
    from .build_fixed_lower_asset import LOWER_BODIES
    from scipy.optimize import lsq_linear
    ctx=prepare(context());arm=ctx['indices'];q0=ctx['q0'][arm];runs={}
    for label in labels:
        run={name:read(PHASE/'calibration_runs'/label/(name+'.json')) for name in ('report','states','trace','tasks','contacts','controls')}
        report=run['report'];states=run['states'];controls=run['controls'];trace=run['trace']
        if report['failure'] or not all(report['checks'].values()) or report['physics_steps']!=24 or report['native_initializations']!=1 or report['mode']!='bias':raise AssertionError('native contracts')
        if any(sha(p)!=h for p,h in report['source_sha256'].items()):raise AssertionError('producer sources changed')
        if states[0]!=ctx['seed'] or any(len(run[n])!=25 for n in ('states','trace','tasks')) or any(len(run[n])!=24 for n in ('controls','contacts')):raise AssertionError('coverage')
        if any(error_from_state(s,ctx).tolist()!=t for s,t in zip(states,run['tasks'])):raise AssertionError('measured task')
        if any(s['physics_step']!=i for i,s in enumerate(states)) or any(abs(t['time_s']-i/240)>1e-9 for i,t in enumerate(trace)):raise AssertionError('time/step')
        if any(v['physics_step']!=i+1 for n in ('controls','contacts') for i,v in enumerate(run[n])):raise AssertionError('sequence')
        if any(s['human_body_states'][report['human_body_names'].index(n)]!=states[0]['human_body_states'][report['human_body_names'].index(n)] for s in states for n in ('Pelvis',)+LOWER_BODIES):raise AssertionError('fixed lower')
        targets=np.array([v['final_target_rad'] for v in controls]);bias=np.array(report['bias_rad'])
        if not np.isfinite(targets).all() or not np.array_equal(targets,np.repeat(targets[:1],24,axis=0)) or np.max(abs(targets[0]-(q0+bias)))>2e-7:raise AssertionError('constant applied target')
        if not ((targets>=np.array(old['lower_rad'])-2e-7)&(targets<=np.array(old['upper_rad'])+2e-7)).all():raise AssertionError('bounds')
        if np.any(abs(targets-q0)>.3+2e-7) or any(t['strap_rest_length_m']!=report['rest_length_m'] for t in trace):raise AssertionError('box/rest')
        if not np.isfinite(np.array(run['tasks'])).all():raise AssertionError('finite task')
        runs[label]=run
    baseline=runs['baseline'];base_target=np.array(baseline['controls'][0]['final_target_rad']);error=np.array(baseline['tasks'][-1]);columns=[];applied=[]
    for i in range(12):
        run=runs['axis_'+str(i).zfill(2)];delta=np.array(run['controls'][0]['final_target_rad'])-base_target
        if np.count_nonzero(delta)!=1 or delta[i]==0:raise AssertionError('single applied probe axis')
        columns.append((error-np.array(run['tasks'][-1]))/delta[i]);applied.append(delta[i])
    matrix=np.array(columns).T
    heldout=runs['heldout'];heldout_delta=np.array(heldout['controls'][0]['final_target_rad'])-base_target
    predicted=error-matrix@heldout_delta;actual=np.array(heldout['tasks'][-1]);difference=actual-predicted
    bias=np.array(baseline['report']['bias_rad']);low=np.maximum(-.05,np.array(old['lower_rad'])-q0-bias);high=np.minimum(.05,np.array(old['upper_rad'])-q0-bias)
    fit=lsq_linear(np.vstack((matrix,1e-5*np.eye(12))),np.r_[error,np.zeros(12)],bounds=(low,high),tol=1e-12,max_iter=500)
    if not fit.success:raise AssertionError(fit.message)
    checks={'all_14_native_contracts_and_coverage':True,'same_initial_state_and_constant_targets':True,
        'applied_single_axis_float32_probes':True,'bounded_fit_converged':bool(fit.success),
        'fit_within_0p05_and_original_box':bool(((fit.x>=low)&(fit.x<=high)).all()),
        'all_executions_exit_zero':len(read(PHASE/'execution.json'))==14 and all(r['exit_code']==0 for r in read(PHASE/'execution.json')),
        'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    result={'checks':checks,'input_sha256':hashes,'native_initializations':14,'physics_steps':336,
        'matrix':matrix.tolist(),'singular_values':np.linalg.svd(matrix,compute_uv=False).tolist(),
        'applied_probe_delta_rad':applied,'baseline_end_error_m_scaled_rad':error.tolist(),
        'heldout':{'applied_delta_rad':heldout_delta.tolist(),'predicted_error_m_scaled_rad':predicted.tolist(),
            'actual_error_m_scaled_rad':actual.tolist(),'point_prediction_difference_mm':float(np.linalg.norm(difference[:3])*1000),
            'normal_rotation_vector_prediction_difference_deg':float(np.linalg.norm(difference[3:])/.08*180/np.pi)},
        'bias_delta_rad':fit.x.tolist(),'bias_rad':(bias+fit.x).tolist(),'predicted_corrected_end_error_m_scaled_rad':(error-matrix@fit.x).tolist(),
        'scope':'0.1s constant-target finite response, not FK or feedback Jacobian; extrapolated correction needs native validation; no physical success threshold'}
    if not all(checks.values()):raise AssertionError(checks)
    output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    candidate_path.write_text(json.dumps({'label':'corrected','bias_rad':result['bias_rad'],'requested_bias_delta_rad':result['bias_delta_rad'],
        'fit_source':str(output),'fit_source_sha256':sha(output)},indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('checks','singular_values','heldout','bias_delta_rad','predicted_corrected_end_error_m_scaled_rad')},indent=2))


if __name__=='__main__':main()
