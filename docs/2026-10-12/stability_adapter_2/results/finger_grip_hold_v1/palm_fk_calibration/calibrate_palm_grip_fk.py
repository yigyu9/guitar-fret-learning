"""Initial-only native palm pose derivatives for the source-clear grip seed."""
import json
from pathlib import Path

from .run_finger_grip_hold import validated_seed
from .finger_grip_probe import PHASE, SUPPORT_PHASE
from .environment import ROOT, np
from .build_fixed_lower_asset import read, sha
from .self_collision_environment import SelfCollisionEnvironment
from .run_joint_hold import native_state
from .palm_grip_feedback import palm_poses
from scipy.spatial.transform import Rotation


def main():
    settings = ROOT/'stability_adapter_2/trials/finger_grip_hold_v1/mixed/curl_120_pinky090.json'
    seed = validated_seed(settings)
    reference_path = PHASE/'short/seed120_preload050_hold/report.json'
    reference = read(reference_path)
    arm = reference['arm_indices']
    q0 = np.array(reference['initial_joint_targets_rad'])
    names = reference['human_joint_names']
    search_path = SUPPORT_PHASE/'search_near_touch.json'
    search = read(search_path)
    inputs = [Path(__file__).resolve(), Path(__file__).with_name('palm_grip_feedback.py'), settings, reference_path, search_path]
    inputs += [Path(p) for p in reference['source_sha256']]
    hashes = {str(p):sha(p) for p in inputs}
    initial = []
    for name in ('LH:palm','RH:palm'):
        pose = seed['initial_state']['human_body_states'][reference['human_body_names'].index(name)]['pose']
        initial.append((np.array([pose['p'][a] for a in 'xyz']), np.array([pose['r'][a] for a in 'xyzw'])))
    out = PHASE/'palm_fk_calibration'
    out.mkdir(exist_ok=False)
    rows = []
    for i in arm:
        h = .001 if q0[i]+.001<=reference['native_joint_upper_rad'][i] else -.001
        changed = dict(read(settings))
        changed['joint_angles_rad'] = dict(changed['joint_angles_rad'], **{names[i]:float(q0[i]+h)})
        env = SelfCollisionEnvironment(changed, search['guitar_initial_translation_m'])
        try:
            before = native_state(env)
            actual_h = env.initial_q[i]-q0[i]
            column = []
            for (p0,qref), (p,q) in zip(initial, palm_poses(env)):
                dr = (Rotation.from_quat(q)*Rotation.from_quat(qref).inv()).as_rotvec()
                column.extend(np.r_[(p-p0)/actual_h, .08*dr/actual_h])
            unchanged = native_state(env)==before
            if env.steps!=0 or not unchanged or not np.isfinite(column).all():
                raise AssertionError('initial FK query contract')
            rows.append({'joint':names[i], 'actual_delta_rad':float(actual_h), 'column':list(column),
                         'initial_state':before, 'zero_steps':True, 'queries_preserve_states':unchanged,
                         'guitar_exact':before['guitar_body_states']==seed['initial_state']['guitar_body_states']})
            (out/'columns.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')
        finally:
            env.close()
    matrix = np.array([r['column'] for r in rows]).T
    checks = {'all_queries_preserve_states':all(r['queries_preserve_states'] for r in rows),
              'all_guitar_exact':all(r['guitar_exact'] for r in rows),
              'inputs_unchanged':all(sha(Path(p))==v for p,v in hashes.items())}
    result = {'matrix':matrix.tolist(), 'arm_names':[names[i] for i in arm],
              'initial_palm_poses':[{'p':p.tolist(),'q':q.tolist()} for p,q in initial],
              'settings_sha256':sha(settings), 'scope':'initial local pose derivative, not runtime response certification',
              'checks':checks, 'native_initializations':24,'physics_steps':0,
              'position_unit':'m/rad', 'orientation_scale_m_per_rad':.08,
              'singular_values':np.linalg.svd(matrix,compute_uv=False).tolist(), 'input_sha256':hashes}
    (out/'jacobian.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    if not all(checks.values()):raise AssertionError(checks)
    print(json.dumps(checks))


if __name__=='__main__':main()
