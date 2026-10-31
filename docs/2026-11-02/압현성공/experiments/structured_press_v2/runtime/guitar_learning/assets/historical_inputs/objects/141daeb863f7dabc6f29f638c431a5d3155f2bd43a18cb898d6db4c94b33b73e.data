"""Prepare shoulder amplitudes and bounded actual-guitar-error feedback."""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/'docs/2026-10-12/stability_adapter_2/results/seed2_guitar_response_v1'
PREVIOUS=OLD.parent/'seed2_response_locality_v1'
PHASE=OLD.parent/'seed2_guitar_feedback_v1'
TRIALS=ROOT/'stability_adapter_2/trials/seed2_guitar_feedback_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    PHASE.mkdir(exist_ok=False);TRIALS.mkdir(exist_ok=False)
    path=PREVIOUS/'analysis.json';hashes={str(path):sha(path)};prior=read(path)
    paths=[Path(p) for p in prior['input_sha256']]+[Path(__file__).resolve(),ROOT/'stability_adapter_2/SEED2_SHOULDER_GUITAR_FEEDBACK_PLAN.md',OLD/'proposal.json',OLD/'heldout_selection.json',OLD/'native/base/initial_values.json',OLD/'native/base/initial_grip_audit.json']
    hashes.update({str(p):sha(p) for p in paths})
    save(PHASE/'attempt.json',{'input_sha256':hashes,'native_initializations':0,'physics_steps':0})
    if not all(prior['checks'].values()) or any(sha(p)!=h for p,h in prior['input_sha256'].items()):raise AssertionError('previous input closure')
    initial=read(OLD/'native/base/initial_values.json');audit=read(OLD/'native/base/initial_grip_audit.json');grip=read(OLD/'proposal.json');selection=read(OLD/'heldout_selection.json')
    if not all(audit['checks'].values()) or not all(selection['checks'].values()):raise AssertionError('saved pose/selection not verified')
    base=initial['input_trial'];bias=base['main_target_offsets_rad'];axes=[f'L_{joint}_{a}' for joint in ('Shoulder','Wrist') for a in 'xyz']
    if grip['probe_axes']!=axes or selection['axes']!=axes or set(bias)!={f'L_{joint}_{a}' for joint in ('Thorax','Shoulder','Elbow','Wrist') for a in 'xyz'}:raise AssertionError('exact ordered probe/support axes')
    rows=[]
    j=prior['locality']['paired_windows']['last1s_mean']['axes']['L_Shoulder_y']['backward_derivative_m_per_rad_rad_per_rad']
    feedback={'axis':'L_Shoulder_y','j_W_m_per_rad_rad_per_rad':j,'rotation_lever_m':.1,'gain_per_s':1.,'rate_limit_rad_per_s':.008,'delta_bounds_rad':[-.016,0.],'control_hz':60,'j_source_path':str(path),'j_source_sha256':sha(path),'j_source_field':'locality.paired_windows.last1s_mean.axes.L_Shoulder_y.backward_derivative_m_per_rad_rad_per_rad'}
    for label,value,enabled in [('constant_0p008',-.008,False),('constant_0p016',-.016,False),('guitar_feedback',0.,True)]:
        residual={'L_Shoulder_y':value}
        trial=copy.deepcopy(base);trial['main_target_offsets_rad']={n:v+residual.get(n,0.) for n,v in bias.items()}
        if any(abs(v)>.3 for v in trial['main_target_offsets_rad'].values()):raise AssertionError('combined offset bound')
        path=TRIALS/(label+'.json');save(path,trial)
        rows.append({'label':label,'target_residual_rad':residual,'trial_path':str(path),'trial_sha256':sha(path),'accepted_for_fresh_native':True,'target_clearance_m':.001,'absolute_strap_rest_length_m':initial['absolute_strap_rest_length_m'],'source_state':initial['native_initial_state'],'feedback_enabled':enabled})
    from .environment import np
    q=np.array(initial['initial_PD_target_rad'],dtype=np.float32);lower=np.array(initial['PD_properties']['lower']);upper=np.array(initial['PD_properties']['upper'])
    targets={}
    for row in rows:
        t=read(row['trial_path']);target=q+np.array([t['main_target_offsets_rad'].get(n,0.) for n in initial['human_joint_names']],dtype=np.float32)
        if not np.all((target>=lower)&(target<=upper)):raise AssertionError('actual float32 target would clip')
        targets[row['label']]=target.astype(float).tolist()
    weighted=np.array(j,dtype=float)*np.array([1,1,1,.1,.1,.1]);denominator=float(weighted@weighted)
    if weighted.shape!=(6,) or not np.isfinite(weighted).all() or not np.isfinite(denominator) or denominator<=0:raise AssertionError('finite nonzero six-vector j')
    for value in feedback['delta_bounds_rad']:
        offset=np.array([bias.get(n,0.)+(value if n=='L_Shoulder_y' else 0.) for n in initial['human_joint_names']],dtype=np.float32);target=q+offset
        if any(abs(v)>.3 for v in offset) or not np.all((target>=lower)&(target<=upper)):raise AssertionError('entire feedback interval unclipped native bounds')
    checks={'saved_seed2_pose_and_selection_admitted':True,'only_declared_residual_changes':all({**read(r['trial_path']),'main_target_offsets_rad':bias}==base and read(r['trial_path'])['main_target_offsets_rad']=={n:v+r['target_residual_rad'].get(n,0.) for n,v in bias.items()} for r in rows),'float32_targets_native_bounds_no_clipping':True,'feedback_j_and_entire_interval_admitted':True,'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    save(PHASE/'proposal.json',{'checks':checks,'input_sha256':hashes,'rows':rows,'facets':grip['facets'],'regions_G_m':grip['regions_G_m'],'front_outer_source_z_G_m':grip['front_outer_source_z_G_m'],'seed2_angles_rad':initial['initial_PD_target_rad'],'support_bias_rad':bias,'probe_axes':axes,'initial_route_length_m':initial['initial_route_length_m'],'expected_float32_targets_rad':targets,'feedback_parameters':feedback,'native_initializations':0,'physics_steps':0,'scope':'shoulder Y constants -.008/-.016 and bounded actual guitar-error feedback; same initial81q/G/LA/PD; fresh native source/FK admission required'})
    print(json.dumps({'checks':checks,'residuals':{r['label']:r['target_residual_rad'] for r in rows}},indent=2))


if __name__=='__main__':main()
