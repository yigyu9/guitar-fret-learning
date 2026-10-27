"""Measure 24 one-step native target responses and fit a bounded startup preload."""
import json
from pathlib import Path

from .run_finger_grip_hold import validated_seed
from .finger_grip_probe import PHASE, REFERENCE, SUPPORT_PHASE
from .environment import ROOT, np
from .build_fixed_lower_asset import read, sha
from .self_collision_environment import SelfCollisionEnvironment
from .run_joint_hold import native_state, snapshot
from .native_contacts import body_names, read_contacts
from scipy.optimize import lsq_linear


def main():
    settings=ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/mixed/curl_120_pinky090.json'
    seed=validated_seed(settings)
    previous=PHASE/'short/seed120_hold'
    report=read(previous/'report.json');states=read(previous/'states.json')
    arm=np.array(report['arm_indices']);q0=np.array(report['initial_joint_targets_rad'])[arm]
    q1=np.array([d['pos'] for d in states[1]['human_dof_states']])[arm]
    low,high=np.maximum(report['diagnostic_lower_rad'],q0-.15),np.minimum(report['diagnostic_upper_rad'],q0+.15)
    search_path=SUPPORT_PHASE/'search_near_touch.json';search=read(search_path)
    out=PHASE/'arm_start_calibration';out.mkdir(exist_ok=False)
    inputs=[Path(__file__).resolve(),settings,search_path,previous/'report.json',previous/'states.json',PHASE/'probe_settings_manifest.json']
    inputs += [Path(p) for p in report['source_sha256']]
    hashes={str(p):sha(p) for p in inputs}
    columns=[]
    for j,name in enumerate(report['arm_names']):
        h=.03 if high[j]-q0[j]>=.03 else -.03
        if not low[j]<=q0[j]+h<=high[j]:raise AssertionError('no admissible target probe')
        env=SelfCollisionEnvironment(read(settings),search['guitar_initial_translation_m'])
        try:
            before=native_state(env)
            if before!=seed['initial_state']:raise AssertionError('calibration initial state mismatch')
            target=np.zeros(66,dtype=np.float32);target[list(env.main_indices).index(arm[j])]=h
            env.set_main_offsets(target)
            if native_state(env)!=before:raise AssertionError('calibration target wrote state')
            env.step_physics();after=native_state(env)
            actual=np.array([d['pos'] for d in after['human_dof_states']])[arm]
            row={'name':name,'probe_target_delta_rad':h,'state_after':after,
                'snapshot_after':snapshot(env),'column':((actual-q1)/h).tolist(),
                'contacts':read_contacts(env.gym,env.env,body_names(env.gym,env.env))}
            if not np.isfinite(row['column']).all():raise AssertionError('nonfinite response')
            columns.append(row)
            (out/'columns.json').write_text(json.dumps(columns,indent=2,allow_nan=False)+'\n')
        finally:env.close()
    matrix=np.array([c['column'] for c in columns]).T
    motion=q1-q0
    fit=lsq_linear(np.vstack((matrix,1e-5*np.eye(24))),np.r_[-motion,np.zeros(24)],bounds=(low-q0,high-q0),tol=1e-12,max_iter=500)
    if not fit.success or not np.isfinite(fit.x).all():raise AssertionError(fit.message)
    if not all(sha(Path(p))==h for p,h in hashes.items()):raise AssertionError('calibration inputs changed')
    path=ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/arm_start_bias_seed120.json'
    if path.exists():raise FileExistsError('preserve calibrated target bias')
    result={'arm_target_bias_rad':dict(zip(report['arm_names'],fit.x.tolist())),
        'settings_sha256':sha(settings),'settings_path':str(settings),
        'scope':'bounded linear one-step preload; not a certified gravity torque or stability solution'}
    path.write_text(json.dumps(result,indent=2)+'\n')
    (out/'fit.json').write_text(json.dumps({'bias_settings_path':str(path),'bias_settings_sha256':sha(path),
        'input_sha256':hashes,'input_sha256_after':{p:sha(Path(p)) for p in hashes},
        'native_initializations':24,'physics_steps':24,'matrix':matrix.tolist(),
        'baseline_first_step_delta_rad':motion.tolist(),'predicted_first_step_delta_rad':(motion+matrix@fit.x).tolist(),
        'baseline_norm_rad':float(np.linalg.norm(motion)),'predicted_norm_rad':float(np.linalg.norm(motion+matrix@fit.x)),
        'singular_values':np.linalg.svd(matrix,compute_uv=False).tolist(),'fit_success':bool(fit.success),
        'bias_within_bounds':bool(((q0+fit.x>=low)&(q0+fit.x<=high)).all())},indent=2,allow_nan=False)+'\n')
    print(json.dumps({'baseline_first_step_norm':np.linalg.norm(motion),'predicted_norm':np.linalg.norm(motion+matrix@fit.x),'bias':result['arm_target_bias_rad']},indent=2))


if __name__=='__main__':main()
