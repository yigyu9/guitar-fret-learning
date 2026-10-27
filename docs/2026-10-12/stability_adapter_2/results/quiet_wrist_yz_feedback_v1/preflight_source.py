"""Check feedback geometry and full command sequences without initializing Gym."""
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation
from .wrist_yz_guitar_feedback import update, JOINTS, SCALE, KAPPA, CONTROL_DT

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
B = R / 'docs/2026-10-12/stability_adapter_2/results'
P = B / 'quiet_wrist_yz_feedback_v1'
Z = B / 'quiet_wrist_z_support_authority_v1'
BASE = B / 'initial_middle3_alignment_v1/native'


def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    output = P / 'preflight.json'
    assert not output.exists() and not (P / 'preflight_source.py').exists()
    inputs = [Path(__file__).resolve(), A / 'wrist_yz_guitar_feedback.py',
              A / 'run_quiet_wrist_yz_feedback.py', A / 'run_quiet_wrist_yz_feedback_phase.py',
              A / 'QUIET_WRIST_YZ_FEEDBACK_PLAN.md', A / 'QUIET_WRIST_YZ_FEEDBACK_EXECUTION.md',
              Z / 'comparison_v2.json', Z / 'series.json', Z / 'artifact_inventory.json',
              BASE / 'initial_values.json', BASE / 'controls.jsonl', BASE.parent / 'artifact_inventory.json']
    before = {str(p): sha(p) for p in inputs}
    (P / 'preflight_source.py').write_bytes(Path(__file__).read_bytes())
    initial = read(BASE / 'initial_values.json'); series = read(Z / 'series.json')['baseline']
    comparison = read(Z / 'comparison_v2.json'); inventory = read(Z / 'artifact_inventory.json')
    baseline_inventory = read(BASE.parent / 'artifact_inventory.json')
    checks = {'sealed_inputs_exact': all(sha(p) == inventory[str(p)]['sha256'] for p in
              [Z / 'comparison_v2.json', Z / 'series.json', A / 'QUIET_WRIST_YZ_FEEDBACK_PLAN.md'])
              and all(sha(p) == baseline_inventory[str(p)]['sha256'] for p in
                      [BASE / 'initial_values.json', BASE / 'controls.jsonl'])}
    response = np.array(comparison['response_matrix_world_6x2'])
    gp = np.array(initial['guitar_goal_position_W_m']); gq = np.array(initial['guitar_goal_quaternion_xyzw'])
    def call(p, q, delta=None, enabled=True, time=3., j=response):
        return update(j, gp, gq, p, q, np.zeros(2) if delta is None else delta, enabled, time)
    d, rec = call(gp, gq)
    checks['zero_error_no_correction'] = bool(np.max(abs(d)) < 1e-15 and np.max(abs(np.array(rec['guitar_error_at_update_world_m_rad']))) < 1e-15)
    current_r = Rotation.from_euler('xyz', [.4, -.2, .3]); world_vector = np.array([.02, -.01, .005])
    goal_r = Rotation.from_rotvec(world_vector) * current_r
    _, test = update(response, gp, goal_r.as_quat(), gp, current_r.as_quat(), np.zeros(2), True, 3.)
    checks['world_left_rotation_error_sign'] = bool(np.allclose(test['guitar_error_at_update_world_m_rad'][3:], world_vector, rtol=0, atol=1e-15))
    p2 = np.array(series['position_W_m'][480]); q2 = np.array(series['quaternion_xyzw'][480])
    d2, rec2 = call(p2, q2); dn, rn = call(p2, -q2)
    checks['quaternion_sign_invariance'] = bool(np.array_equal(d2, dn) and np.allclose(rec2['gradient_per_rad'], rn['gradient_per_rad'], rtol=0, atol=1e-14))
    gref = np.array(rec2['gradient_per_rad'])
    checks['fixed_gain_matches_baseline_t2'] = bool(np.allclose(gref, [-.8247321000112535, .4581455826792709], rtol=0, atol=1e-14) and abs(KAPPA - .002 / np.max(abs(gref))) < 1e-16)
    fake = np.zeros((6, 2)); fake[0, 0] = fake[1, 1] = 1.
    saturated, first = call(gp - [.03, 0, 0], gq, np.array([.005, 0]), j=fake)
    reversed_delta, reverse = call(gp + [.03, 0, 0], gq, saturated, j=fake)
    checks['bounded_state_no_hidden_windup_and_reversal'] = bool(saturated[0] == .005 and first['effective_rate_rad_s'][0] == 0 and reversed_delta[0] < .005 and reverse['requested_rate_rad_s'][0] < 0)
    checks['gradient_model_descent_direction'] = bool(np.dot(gref, rec2['requested_rate_rad_s']) > 0)
    names = initial['human_joint_names']; main = [names.index(n) for n in initial['main_control_joint_names']]
    support = [names.index(n) for n in JOINTS]; others = np.setdiff1d(np.arange(81), support)
    fingers = [i for i, n in enumerate(names) if n.startswith(('LH:', 'RH:'))]
    q0 = np.array([initial['actual_initial_angles_rad'][n] for n in names])
    base_offsets = np.array([initial['input_trial']['main_target_offsets_rad'].get(names[i], 0.) for i in main])
    lower = np.array(initial['PD_properties']['lower']); upper = np.array(initial['PD_properties']['upper'])
    controls = [json.loads(line) for line in (BASE / 'controls.jsonl').read_text().splitlines()]
    assert len(controls) == 1200 and len(names) == 81 and len(main) == 66
    off = []; on = []; corrections = np.zeros(2); max_rate = 0.; max_angle = 0.
    for step, old in enumerate(controls):
        if step % 4 == 0:
            t = step / 240.; offsets = base_offsets.copy()
            offsets[main.index(names.index('L_Wrist_x'))] += .005 * np.sin(2 * np.pi * t)
            target0 = q0.copy(); target0[main] += offsets; target0 = target0.astype(np.float32)
            prior = corrections.copy()
            corrections, rec = call(np.array(series['position_W_m'][step]), np.array(series['quaternion_xyzw'][step]), corrections, time=t)
            e = np.r_[gp - series['position_W_m'][step], (Rotation.from_quat(gq) * Rotation.from_quat(series['quaternion_xyzw'][step]).inv()).as_rotvec()]
            expected = np.clip(prior + np.clip(KAPPA * ((response / SCALE[:, None]).T @ (e / SCALE)), -.002, .002) / 60., -.005, .005) if t > 2. else np.zeros(2)
            assert np.allclose(corrections, expected, rtol=0, atol=1e-18)
            max_rate = max(max_rate, float(np.max(abs((corrections - prior) / CONTROL_DT))))
            max_angle = max(max_angle, float(np.max(abs(corrections))))
            offsets[[main.index(i) for i in support]] += corrections
            target1 = q0.copy(); target1[main] += offsets; target1 = target1.astype(np.float32)
            assert np.all(abs(offsets) <= .3) and np.all(target1 >= lower) and np.all(target1 <= upper)
        off.append(target0); on.append(target1)
    off = np.array(off); on = np.array(on); old = np.array([v['final_target_rad'] for v in controls], dtype=np.float32)
    checks.update(off_all1200x81_targets_exact=bool(np.array_equal(off, old)),
                  on_first484_targets_exact=bool(np.array_equal(on[:484], old[:484])),
                  on_other79_and_all_fingers_exact=bool(np.array_equal(on[:, others], old[:, others]) and np.array_equal(on[:, fingers], old[:, fingers])),
                  on_recorded_baseline_error_replay_bounded=bool(max_angle <= .005 and max_rate <= .002 + 1e-15))
    after = {p: sha(p) for p in before}; checks['inputs_unchanged'] = before == after
    assert all(checks.values()), checks
    output.write_text(json.dumps(dict(checks=checks, input_sha256_before=before, input_sha256_after=after,
        reference_gradient_per_rad=gref.tolist(), reference_requested_rate_rad_s=rec2['requested_rate_rad_s'],
        replay_final_delta_rad=corrections.tolist(), replay_max_angle_rad=max_angle, replay_max_effective_rate_rad_s=max_rate,
        native_initializations=0, physics_steps=0, scope='Pure geometry and saved-baseline command replay only; no feedback native result'), indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(checks=len(checks), native_initializations=0, replay_final_delta_rad=corrections.tolist())))


if __name__ == '__main__': main()
