"""Fit a small constant target correction using saved hand/guitar responses."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PREVIOUS=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_coupled_response_v1'
PHASE=PREVIOUS.parent/'palm_coupled_correction_v1'
TRIALS=ROOT/'stability_adapter_2/trials/palm_coupled_correction_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    if PHASE.exists() or TRIALS.exists():raise FileExistsError('preserve existing fit')
    path=PREVIOUS/'analysis.json';hashes={str(path):sha(path)};old=read(path)
    paths=[Path(p) for p in old['input_sha256']]+[Path(__file__).resolve(),PREVIOUS/'artifact_inventory.json',PREVIOUS/'environment.json',
        ROOT/'stability_adapter_2/PALM_COUPLED_CORRECTION_PLAN.md']
    hashes.update({str(p):sha(p) for p in paths})
    if not all(old['checks'].values()) or any(sha(p)!=h for p,h in old['input_sha256'].items()):raise AssertionError('source analysis inputs')
    inventory=read(PREVIOUS/'artifact_inventory.json')
    if not all(sha(p)==v['sha256'] for p,v in inventory.items()):raise AssertionError('previous phase changed')
    import numpy as np
    from scipy.optimize import minimize
    report=read(PREVIOUS/'baseline/report.json');seed=read(PREVIOUS/'baseline/states.json')[0]
    q0=np.array([seed['human_dof_states'][i]['pos'] for i in report['arm_indices']],dtype=np.float32)
    bias=np.array(report['bias_rad']);base_target=np.array(read(PREVIOUS/'baseline/controls.json')[0]['final_target_rad'])
    if not np.array_equal(q0+bias.astype(np.float32),base_target):raise AssertionError('baseline float32 target')
    matrix=np.array(old['matrix_terminal_12x12']);y=np.r_[old['curves']['baseline']['hand_error_m_scaled_rad'][-1],old['curves']['baseline']['guitar_error_W_m_rad'][-1]]
    if matrix.shape!=(12,12) or not np.isfinite(matrix).all():raise AssertionError('response matrix')
    response=matrix*.001;blocks=(slice(0,3),slice(6,9),slice(9,12));scales={b.start:float(y[b]@y[b]) for b in blocks};normal_scale=float(y[3:6]@y[3:6])
    if min(list(scales.values())+[normal_scale])<=0:raise AssertionError('normalization')
    weights=np.zeros(12);weights[6:9]=1/scales[6];weights[9:]=1/scales[9];weights[3:6]=.01/normal_scale
    def objective(s):
        value=y+response@s;return float(value@(weights*value)+.0001*(s@s))
    def gradient(s):return 2*response.T@(weights*(y+response@s))+.0002*s
    constraints=[{'type':'ineq','fun':lambda s,b=b:1-float((y+response@s)[b]@(y+response@s)[b])/scales[b.start],
        'jac':lambda s,b=b:-2*response[b].T@(y+response@s)[b]/scales[b.start]} for b in blocks]
    low=np.maximum(-1,(np.array(report['lower_rad'])-base_target)/.001);high=np.minimum(1,(np.array(report['upper_rad'])-base_target)/.001)
    fit=minimize(objective,np.zeros(12),jac=gradient,bounds=list(zip(low,high)),constraints=constraints,method='SLSQP',options={'ftol':1e-12,'maxiter':300})
    if not fit.success or min(c['fun'](fit.x) for c in constraints)<-1e-9:raise AssertionError(fit.message)
    delta=.001*fit.x;predictions=[];candidates=[]
    for label,alpha in (('quarter',.25),('half',.5),('full',1.)):
        corrected=bias+alpha*delta;target=q0+corrected.astype(np.float32);applied=target.astype(float)-base_target;predicted=y+matrix@applied
        if np.max(np.abs(applied))>.001+2e-7 or not ((target>=np.array(report['lower_rad'])-2e-7)&(target<=np.array(report['upper_rad'])+2e-7)).all():raise AssertionError('float32 correction bounds')
        comparisons={str(b.start):float(np.linalg.norm(predicted[b]))<=float(np.linalg.norm(y[b]))+1e-9 for b in blocks}
        if not all(comparisons.values()):raise AssertionError('quantized predicted norm increased')
        predictions.append({'label':label,'scale':alpha,'actual_float32_target_rad':target.astype(float).tolist(),'applied_delta_rad':applied.tolist(),
            'predicted_terminal':predicted.tolist(),'norms_not_increased':comparisons})
        candidates.append({'label':label,'scale':alpha,'bias_rad':corrected.tolist(),'requested_bias_delta_rad':(alpha*delta).tolist()})
    environment=read(PREVIOUS/'environment.json')
    if any(sha(p)!=h for p,h in hashes.items()):raise AssertionError('inputs changed')
    PHASE.mkdir();TRIALS.mkdir()
    result={'checks':{'previous_phase_preserved':True,'source_inputs_unchanged':True,'fit_converged':True,'quantized_bounds_and_predicted_norms':True},
        'input_sha256':hashes,'objective':{'guitar_position_relative_squared':1,'guitar_rotation_relative_squared':1,'hand_normal_relative_squared':.01,'scaled_delta_squared':.0001},
        'solver':{'method':'SLSQP','message':str(fit.message),'iterations':int(fit.nit),'objective_before':objective(np.zeros(12)),'objective_after':objective(fit.x)},
        'matrix_terminal_12x12':matrix.tolist(),'baseline_terminal':y.tolist(),'bias_delta_rad':delta.tolist(),'baseline_bias_rad':bias.tolist(),
        'normalization_squared':scales,'normal_scale_squared':normal_scale,'predictions':predictions,
        'scope':'bounded constant PD target fit; model predictions only, not success thresholds, feedback Jacobian, or native validation'}
    output=PHASE/'fit.json';output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');records=[]
    for candidate in candidates:
        candidate.update(fit_source=str(output),fit_source_sha256=sha(output));path=TRIALS/(candidate['label']+'.json');path.write_text(json.dumps(candidate,indent=2)+'\n')
        records.append({'label':candidate['label'],'candidate_path':str(path),'sha256':sha(path)})
    manifest={'candidates':records,'fit_path':str(output),'fit_sha256':sha(output),'native_initializations_planned':3,'physics_steps_planned':72}
    (TRIALS/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(PHASE/'candidate_generation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (PHASE/'environment.json').write_text(json.dumps(environment,indent=2)+'\n')
    print(json.dumps({'solver':result['solver'],'delta':delta.tolist(),'predictions':predictions},indent=2))


if __name__=='__main__':main()
