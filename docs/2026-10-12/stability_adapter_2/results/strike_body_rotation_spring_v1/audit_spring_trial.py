"""Read-only early-prefix, human torque, and guitar-contact audit of two trials."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path('/home/ajou/yigyu/3')
RESULTS = ROOT / 'docs/2026-10-12/stability_adapter_2/results'


def main():
    inputs = {str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}

    def load(path):
        inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())

    reference = RESULTS / 'strike_timed_wait_rebase_v1/native/data'
    ref_controls = load(reference / 'controls.json')
    ref_trace = load(reference / 'trace.json')
    rows = []
    for label in ('strike_body_rotation_spring_v1',):
        data = RESULTS / label / 'native/data'
        controls = load(data / 'controls.json')
        trace = load(data / 'trace.json')
        initial = load(data / 'initial_values.json')
        torques = load(data / 'human_torque_commands.json')
        groups = load(data / 'human_rotation_spring.json')['groups']
        names = initial['joint_names']
        idx = [i for i, n in enumerate(names) if n.startswith(('R_Shoulder', 'R_Elbow', 'R_Wrist'))]
        props = initial['PD_properties']
        kp = np.array([v['stiffness'] for v in props], dtype=np.float32)
        limit = np.array([v['effort'] for v in props], dtype=np.float32)
        first = next(r for r in controls if r['actor_used'])
        start = first['time_s']
        fields = ('time_s', 'phase', 'actor_used', 'requested_targets_rad', 'final_targets_rad', 'source_history', 'song_time_s', 'readiness')
        prefix = [r for r in controls if r['time_s'] < start]
        assert all({k: r.get(k) for k in fields} == {k: ref_controls[i].get(k) for k in fields} for i, r in enumerate(prefix))
        trace_prefix = [r for r in trace if r['time_s'] <= start]
        assert all(r['native_state'] == ref_trace[i]['native_state'] for i, r in enumerate(trace_prefix))
        ref_first = next(r for r in ref_controls if r['actor_used'])
        assert first['observation'] == ref_first['observation'] and first['action'] == ref_first['action']
        outside = np.setdiff1d(np.arange(81), idx)
        error = 0.
        for r in torques:
            goal = np.array(r['logical_targets_rad'], dtype=np.float32)
            actual = np.array(r['actual_R9_rad'], dtype=np.float32)
            coeff = np.array(r['child_rotation_errors_in_native_axis_order_rad'], dtype=np.float32)
            for j, (group, logged) in enumerate(zip(groups, r['rotation_groups'])):
                basis = np.array(group['basis_columns'])
                rest = Rotation.from_quat(group['calibrated_rest_xyzw'])
                computed_goal = Rotation.from_rotvec(basis @ goal[3*j:3*j+3]) * rest
                saved_goal = Rotation.from_quat(logged['goal_parent_relative_xyzw'])
                assert (computed_goal.inv() * saved_goal).magnitude() < 1e-12
                measured = Rotation.from_quat(logged['actual_parent_relative_xyzw'])
                rotation_error = (measured.inv() * saved_goal).as_rotvec()
                assert np.allclose(rotation_error, logged['error_child_rotvec_rad'], atol=1e-12, rtol=0)
                reconstructed = (basis.T @ rotation_error).astype(np.float32)
                assert np.allclose(reconstructed, coeff[3*j:3*j+3], atol=1e-7, rtol=0)
            expected = np.clip(kp[idx] * coeff, -limit[idx], limit[idx])
            command = np.array(r['requested_human_joint_torque_Nm'], dtype=np.float32)
            assert command.shape == (81,) and np.isfinite(command).all()
            assert np.array_equal(command[idx], expected) and np.all(command[outside] == 0)
            error = max(error, float(np.max(abs(command[idx] - expected))))
        assert [r['before_physics_step'] for r in torques] == list(range(first['before_physics_step'], 1200))
        contact_rows = {}
        for r in controls:
            for c in r['contacts']:
                pair = sorted([c['body0_name'], c['body1_name']])
                if not any(n.startswith('guitar/') for n in pair):
                    continue
                key = '|'.join(pair)
                v = contact_rows.setdefault(key, {'rows': 0, 'positive_lambda_rows': 0, 'max_lambda': 0., 'first_positive_time_s': None})
                v['rows'] += 1
                impulse = float(c['lambda'])
                if impulse > 0:
                    v['positive_lambda_rows'] += 1
                    if v['first_positive_time_s'] is None:
                        v['first_positive_time_s'] = r['time_s']
                v['max_lambda'] = max(v['max_lambda'], impulse)
        rows.append({'trial': label, 'start_s': start, 'exact_prepare_control_rows': len(prefix),
                     'exact_native_trace_prefix_rows': len(trace_prefix), 'first_actor_obs_action_exact': True,
                     'torque_command_rows': len(torques), 'human_R9_only': True, 'formula_max_error_Nm': error,
                     'guitar_contacts': contact_rows})
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in inputs.items())
    output = {'input_sha256': inputs, 'inputs_unchanged': True, 'trials': rows,
              'scope': 'requested torques only, no force sensor measurement; sampled prefix, not every-step state equivalence; contact lambda is native contact output, not isolated cause'}
    (Path(__file__).parent / 'spring_audit.json').write_text(json.dumps(output, indent=2) + '\n')
    print([{k: r[k] for k in r if k != 'guitar_contacts'} for r in rows])


if __name__ == '__main__':
    main()
