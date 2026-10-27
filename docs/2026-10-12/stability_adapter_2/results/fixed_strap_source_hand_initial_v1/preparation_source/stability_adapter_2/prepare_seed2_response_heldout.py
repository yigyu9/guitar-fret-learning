"""Select one bounded physical heldout from the sealed saved probe response."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    output=PHASE/'heldout_selection.json'; proposal_path=PHASE/'heldout_proposal.json'
    trial_path=ROOT/'stability_adapter_2/trials/seed2_guitar_response_v1/heldout.json'
    if any(p.exists() for p in (output,proposal_path,trial_path)):raise FileExistsError('preserve heldout inputs')
    path=PHASE/'probe_analysis.json'; hashes={str(path):sha(path)}; analysis=read(path)
    paths=[Path(p) for p in analysis['input_sha256']]+[Path(__file__).resolve(),ROOT/'stability_adapter_2/SEED2_HELDOUT_SELECTION_PLAN.md',PHASE/'proposal.json',PHASE/'native/base/initial_values.json']
    hashes.update({str(p):sha(p) for p in paths})
    if not all(analysis['checks'].values()) or any(sha(p)!=h for p,h in analysis['input_sha256'].items()):raise AssertionError('probe input closure')
    from .environment import np
    from scipy.optimize import lsq_linear
    identification=analysis['response_identification']; axes=identification['axes']; window=identification['windows']['last1s_mean']
    J=np.array(window['jacobian_rows_m_per_rad_rad_per_rad']); e=np.array(window['baseline_error_W_m_rad']); W=np.diag([1,1,1,.1,.1,.1])
    fit=lsq_linear(W@J,-W@e,bounds=(-.001,.001),tol=1e-12,max_iter=1000)
    if not fit.success or not np.isfinite(fit.x).all():raise RuntimeError('bounded fit failed')
    residual={n:float(v) for n,v in zip(axes,fit.x)}
    init=read(PHASE/'native/base/initial_values.json'); proposal=read(PHASE/'proposal.json')
    trial=copy.deepcopy(init['input_trial']); bias=proposal['support_bias_rad']
    trial['main_target_offsets_rad']={n:v+residual.get(n,0.) for n,v in bias.items()}
    if any(abs(v)>.3 for v in trial['main_target_offsets_rad'].values()):raise AssertionError('diagnostic combined offset bound')
    q=np.array(init['initial_PD_target_rad'],dtype=np.float32); names=init['human_joint_names']; lower=np.array(init['PD_properties']['lower']); upper=np.array(init['PD_properties']['upper'])
    fulloffset=np.array([trial['main_target_offsets_rad'].get(n,0.) for n in names],dtype=np.float32)
    target=q+fulloffset
    if not np.all((target>=lower)&(target<=upper)):raise AssertionError('heldout target native bounds, no clipping')
    baseoffset=np.array([bias.get(n,0.) for n in names],dtype=np.float32)
    actual_delta=np.array([float(target[names.index(n)]-(q+baseoffset)[names.index(n)]) for n in axes])
    predictions={name:{'predicted_error_W_m_rad':(np.array(v['baseline_error_W_m_rad'])+np.array(v['jacobian_rows_m_per_rad_rad_per_rad'])@actual_delta).tolist()} for name,v in identification['windows'].items()}
    checks={'probe_contracts_passed':True,'only_declared_sixaxis_residual':set(residual)==set(axes),'bounded_requested_residual':all(abs(v)<=.001 for v in residual.values()),'native_target_not_clipped':True,'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    save(trial_path,trial)
    row={'label':'heldout','target_residual_rad':residual,'trial_path':str(trial_path),'trial_sha256':sha(trial_path),'accepted_for_fresh_native':True,'target_clearance_m':.001,'absolute_strap_rest_length_m':init['absolute_strap_rest_length_m'],'source_state':init['native_initial_state']}
    save(proposal_path,{**proposal,'input_sha256':hashes,'rows':[row],'checks':checks,'scope':'separate bounded heldout proposal; same seed2 initial state; source admission still requires fresh native verification'})
    save(output,{'checks':checks,'input_sha256':hashes,'requested_residual_rad':residual,'actual_float32_submitted_target_difference_rad':actual_delta.tolist(),'axes':axes,'optimizer':{'success':bool(fit.success),'status':int(fit.status),'message':fit.message,'cost':float(fit.cost),'optimality':float(fit.optimality),'active_mask':fit.active_mask.tolist()},'fit_window':'last1s_mean','provisional_rotation_lever_m':.1,'baseline_weighted_error_norm_m':float(np.linalg.norm(W@e)),'predicted_weighted_error_norm_m':float(np.linalg.norm(W@(e+J@actual_delta))),'predictions':predictions,'native_initializations':0,'physics_steps':0,'scope':'saved-data fit only; fresh physical heldout not yet run; not a stability or controller certification'})
    print(json.dumps({'checks':checks,'residual_rad':residual,'weighted_norm_before_after_m':[float(np.linalg.norm(W@e)),float(np.linalg.norm(W@(e+J@actual_delta)))]},indent=2))


if __name__=='__main__':main()
