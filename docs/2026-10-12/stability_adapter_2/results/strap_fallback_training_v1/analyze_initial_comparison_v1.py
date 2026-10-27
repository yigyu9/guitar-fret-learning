"""Read two completed native evaluations; no simulation or checkpoint mutation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

BASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    paths = [Path(__file__).resolve(), BASE/'initial_policy_ON_OFF_equivalence_v1.json']
    roots = {}
    for mode in ('off', 'on'):
        root = BASE/('smoke_'+mode+'_v1/evaluations/initial_000000')
        roots[mode] = root
        paths += [root/'report.json', root/'evaluation.json', root/'learning_abi.json']
        native = root/'native/episode_0001'
        paths += [native/name for name in ('report.json', 'initial_values.json', 'controls.json',
                                           'trace.json', 'media/capture.json')]
    manifest = {str(p): sha(p) for p in paths}
    results = {}
    for mode, root in roots.items():
        outer = json.loads((root/'report.json').read_text())
        native = root/'native/episode_0001'
        report, initial, controls, trace, capture = [json.loads((native/name).read_text())
            for name in ('report.json', 'initial_values.json', 'controls.json', 'trace.json', 'media/capture.json')]
        assert outer['completed'] and outer['inputs_unchanged']
        assert not report['forbidden_calls'] and report['baseline_weights_unchanged']
        assert report['control_steps'] == len(controls)
        outside = np.array([row['position_outside_m'] for row in controls])
        is_outside = np.any(outside > 0, axis=1)
        longest = current = 0
        for value in is_outside:
            current = current+1 if value else 0
            longest = max(longest, current)
        positions = np.array([row['position_W_m'] for row in trace])
        rotations = Rotation.from_quat([row['quaternion_xyzw'] for row in trace])
        displacement = np.linalg.norm(positions-positions[0], axis=1)
        rotation = (rotations[0].inv()*rotations).magnitude()
        tension = np.array([row['strap']['last_applied_tension_n'] for row in controls])
        geometry_tension = np.array([row['strap']['calculated_tension_n'] for row in controls])
        max_ledger_error = 0.
        for row in controls:
            before = sum(row['raw_component_ledger'].values())
            max_ledger_error = max(max_ledger_error, abs(before-row['unfloored_raw_reward']),
                                   abs(row['reward']-row['raw_reward']*.1))
            if row['safety_violation'] is None:
                assert row['raw_reward'] == max(-2., row['unfloored_raw_reward'])
        assert max_ledger_error < 1e-10
        expected_calls = report['physics_steps']*13 if mode == 'on' else 0
        assert report['strap_force_calls'] == expected_calls
        assert capture['frames'][0]['physics_step'] == 0
        assert capture['frames'][-1]['physics_step'] == report['physics_steps']
        assert all(frame['render_preserves_states'] for frame in capture['frames'])
        results[mode] = {
            'evaluation': str(root), 'full_horizon_completed': report['full_horizon_completed'],
            'stop_reason': report['stop_reason'], 'physics_steps': report['physics_steps'],
            'control_steps': report['control_steps'], 'actual_physics_seconds': report['physics_seconds'],
            'position_outside_percent': float(is_outside.mean()*100),
            'longest_position_outside_s': longest/60,
            'max_position_outside_norm_m': float(np.linalg.norm(outside, axis=1).max()),
            'max_initial_translation_m': float(displacement.max()),
            'max_initial_rotation_deg': float(np.rad2deg(rotation).max()),
            'rotation_envelope_outside_percent': 100*sum(row['rotation']['upper_rad'] > 0 for row in controls)/len(controls),
            'last_applied_tension_positive_percent_control_endpoints': float(np.mean(tension > 0)*100),
            'last_applied_tension_max_n_control_endpoints': float(tension.max()),
            'current_calculated_tension_max_n_control_endpoints': float(geometry_tension.max()),
            'tension_scope': 'last preintegration cable command at 60Hz control endpoints; not measured sensor force or full240Hz extrema',
            'strap_rest_length_m': report['strap_initial']['rest_length_m'],
            'initial_slack_m': report['strap_initial']['slack_m'],
            'strap_force_calls': report['strap_force_calls'], 'zero_force_submissions_counted': True,
            'joint_success_events': report['joint_success_events'], 'settled_events': report['settled_events'],
            'accepted_crossings': report['accepted_crossings'], 'raw_return': report['raw_return'],
            'scaled_return': report['return'], 'reward_ledger_max_error': max_ledger_error,
            'videos': report['videos'], 'native_render_frame_count_per_view': len(capture['frames']),
            'initial_state': initial['native_initial_state']}
    assert results['on'].pop('initial_state') == results['off'].pop('initial_state')
    assert manifest == {str(p): sha(p) for p in paths}
    output = {'same_initial_native_state_exact': True, 'same_model_RMS': json.loads(
              (BASE/'initial_policy_ON_OFF_equivalence_v1.json').read_text()),
              'conditions': results, 'input_sha256': manifest,
              'inputs_unchanged': True, 'position_scope': 'current actor-root position envelope; not body-center/teammate tolerance certification',
              'native_executions_added_by_analysis': 0, 'production_reward_certified': False}
    with (BASE/'initial_comparison_v1.json').open('x') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
