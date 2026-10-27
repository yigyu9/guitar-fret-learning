"""Offline exact-snapshot predicate audit; no environment imports or physics."""
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path('/home/ajou/yigyu/3')
D = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
OUT = Path(__file__).resolve().parent
TRIALS = ['strike_timed_wait_rebase_v1', 'strike_free_finger_curl_v1',
          'strike_waypoint_velocity_v1', 'strike_ready_incremental_v1']
SOURCE = ROOT / 'stability_adapter_2/prepared_strike_start.py'
CANDIDATE = D / 'guitar_relative_ready_v1/search_v1/data/candidate_1.json'
paths = [SOURCE, ROOT / 'stability_adapter_2/underneck_pose_trial_v5.py', CANDIDATE]
for trial in TRIALS:
    base = D / trial / 'native'
    paths += [base / 'data' / name for name in
              ('initial_values.json', 'controls.json', 'trace.json', 'checkpoint_connection.json')]
    paths += [base / 'source_before/stability_adapter_2' / name for name in
              ('prepared_strike_start.py', 'run_strike_timed_exit.py')]

# Seal every numeric/source input before any decoding/parsing in this run.
sha = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
cache = {str(p): p.read_bytes() for p in paths}
assert all(hashlib.sha256(cache[str(p)]).hexdigest() == sha[str(p)] for p in paths)
read = lambda p: json.loads(cache[str(p)])
tree = ast.parse(cache[str(SOURCE)].decode())
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name == 'guitar_in_playable_region')
namespace = {'np': np, 'Rotation': Rotation}
exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), namespace)
predicate = namespace['guitar_in_playable_region']
for trial in TRIALS:
    frozen = D / trial / 'native/source_before/stability_adapter_2/prepared_strike_start.py'
    f = next(n for n in ast.parse(cache[str(frozen)].decode()).body
             if isinstance(n, ast.FunctionDef) and n.name == function.name)
    assert ast.dump(function, include_attributes=False) == ast.dump(f, include_attributes=False)


def pose(body):
    return (np.array([body['pose']['p'][a] for a in 'xyz']),
            Rotation.from_quat([body['pose']['r'][a] for a in 'xyzw']))


def expanded(p, r, upper):
    low, high = np.array([-.50, -.15, .65]), np.array([-.15, .15, upper])
    pos_fail = [axis + side for i, axis in enumerate('xyz')
                for side, test in (('_lower', p[i] < low[i]), ('_upper', p[i] > high[i])) if test]
    matrix = r.as_matrix()
    cy = float(np.hypot(matrix[0, 0], matrix[1, 0]))
    result = {'position_failed_conditions': pos_fail,
              'position_lower_margin_m': (p-low).tolist(),
              'position_upper_margin_m': (high-p).tolist(), 'cy': cy}
    if cy < 1e-7:
        difference = float(np.degrees(np.arctan2(matrix[0, 1], matrix[0, 2])))
        positive = bool(-matrix[2, 0] >= 0)
        passes = positive and any(-135-1e-6 <= difference+k <= -45+1e-6
                                  for k in (-360, 0, 360))
        result.update(chart='singular', positive_pitch=positive,
                      roll_minus_yaw_deg=difference, orientation_pass=passes)
    else:
        x, y, z = np.degrees([np.arctan2(matrix[2, 1], matrix[2, 2]),
                             np.arctan2(-matrix[2, 0], cy),
                             np.arctan2(matrix[1, 0], matrix[0, 0])])
        branches = []
        for label, raw in [('principal', (x, y, z)), ('alternate', (x+180, 180-y, z+180))]:
            values = np.array([raw[0] % 360, raw[1], raw[2] % 360])
            lows, highs = np.array([45, 50, 135]), np.array([90, 100, 180])
            failed = [axis+side for i, axis in enumerate(('roll', 'pitch', 'yaw'))
                      for side, test in (('_lower', values[i] < lows[i]-1e-6),
                                         ('_upper', values[i] > highs[i]+1e-6)) if test]
            branches.append({'branch': label, 'raw_xyz_deg': list(map(float, raw)),
                             'tested_xyz_deg': values.tolist(), 'failed_conditions': failed,
                             'lower_margin_deg': (values-lows).tolist(),
                             'upper_margin_deg': (highs-values).tolist(),
                             'SO3_equivalence_error_deg': float(np.degrees(
                                 (Rotation.from_euler('xyz', raw, degrees=True)*r.inv()).magnitude()))})
        result.update(chart='regular', branches=branches,
                      orientation_pass=any(not b['failed_conditions'] for b in branches))
    result['expanded_result'] = not pos_fail and result['orientation_pass']
    assert result['expanded_result'] == bool(predicate(p, r.as_quat(), upper))
    return result


results = {}
for trial in TRIALS:
    base = D / trial / 'native/data'
    initial, controls, trace, connection = [read(base/name) for name in
        ('initial_values.json', 'controls.json', 'trace.json', 'checkpoint_connection.json')]
    upper = connection['playable_upper_z_m']
    gi = initial['guitar_body_names'].index('guitar')
    p0, r0 = pose(initial['native_initial_state']['guitar_body_states'][gi])
    chest0 = initial['native_initial_state']['human_body_states'][initial['human_body_names'].index('Chest')]
    assert chest0['pose']['p']['z'] == upper
    by_step, duplicates = {}, []
    for index, row in enumerate(trace):
        step = row['physics_step']
        if step in by_step:
            old = by_step[step][1]
            assert old['position_W_m'] == row['position_W_m']
            assert np.linalg.norm((Rotation.from_quat(old['quaternion_xyzw'])*
                                   Rotation.from_quat(row['quaternion_xyzw']).inv()).as_rotvec()) < 1e-10
            duplicates.append({'physics_step': step, 'trace_indices': [by_step[step][0], index]})
        else:
            by_step[step] = (index, row)
    samples, mismatches = [], []
    for index, control in enumerate(controls):
        step = control['before_physics_step']
        if step not in by_step:
            continue
        trace_index, row = by_step[step]
        assert abs(control['time_s']-row['time_s']) < 1e-12
        p, r = pose(row['native_state']['guitar_body_states'][gi])
        assert np.linalg.norm(p-np.array(row['position_W_m'])) < 1e-10
        assert (r*Rotation.from_quat(row['quaternion_xyzw']).inv()).magnitude() < 1e-6
        detail = expanded(p, r, upper)
        recorded = control['guitar_in_playable_region']
        if detail['expanded_result'] != recorded:
            mismatches.append(index)
        sample = {'control_index': index, 'trace_index': trace_index, 'physics_step': step,
                  'time_s': control['time_s'], 'phase': control['phase'],
                  'recorded_result': recorded, 'position_W_m': p.tolist(),
                  'quaternion_xyzw': r.as_quat().tolist(),
                  'SO3_from_initial_deg': float(np.degrees((r*r0.inv()).magnitude())), **detail}
        if samples:
            previous = samples[-1]
            sample['previous_matched_time_s'] = previous['time_s']
            sample['position_delta_from_previous_matched_m'] = float(np.linalg.norm(p-np.array(previous['position_W_m'])))
            sample['SO3_delta_from_previous_matched_deg'] = float(np.degrees(
                (r*Rotation.from_quat(previous['quaternion_xyzw']).inv()).magnitude()))
        samples.append(sample)
    assert not mismatches
    transitions = [{'previous': a, 'current': b} for a, b in zip(samples, samples[1:])
                   if a['recorded_result'] != b['recorded_result']]
    false = [s for s in samples if not s['recorded_result']]
    reasons = Counter()
    for s in false:
        if s['position_failed_conditions']:
            reasons.update(s['position_failed_conditions'])
        if not s['orientation_pass']:
            reasons['orientation_both_branches_fail' if s['chart']=='regular' else 'singular_condition_fail'] += 1
    results[trial] = {'initial': {'position_W_m': p0.tolist(), 'quaternion_xyzw': r0.as_quat().tolist(),
                                  'chest_upper_z_m': upper, **expanded(p0, r0, upper)},
        'control_count': len(controls), 'trace_count': len(trace), 'duplicate_trace_steps': duplicates,
        'exact_matched_count': len(samples), 'unmatched_control_count': len(controls)-len(samples),
        'recorded_result_mismatches': mismatches, 'matched_true': len(samples)-len(false),
        'matched_false': len(false), 'false_predicate_counts': dict(reasons),
        'counts_by_phase': {phase: dict(Counter(str(s['recorded_result']) for s in samples if s['phase']==phase))
                            for phase in sorted({s['phase'] for s in samples})},
        'minimum_SO3_false_sample': min(false, key=lambda s:s['SO3_from_initial_deg']) if false else None,
        'maximum_SO3_sample': max(samples, key=lambda s:s['SO3_from_initial_deg']),
        'transitions': transitions, 'exact_matched_samples': samples}

candidate = read(CANDIDATE)
r_initial = Rotation.from_quat(results[TRIALS[0]]['initial']['quaternion_xyzw'])
witness = [67.5, 90, 157.5]
synthetic = []
for axis in range(3):
    for sign in (-1, 1):
        vector = np.zeros(3); vector[axis] = np.radians(sign*.01)
        r = Rotation.from_rotvec(vector)*r_initial
        synthetic.append({'world_axis': 'xyz'[axis], 'perturbation_deg': sign*.01,
                          **expanded(np.array(results[TRIALS[0]]['initial']['position_W_m']), r,
                                     results[TRIALS[0]]['initial']['chest_upper_z_m'])})
end_sha = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
assert sha == end_sha
summary = {'scope': 'offline saved snapshots and pure rotation math; no physics or A/raw modification',
           'input_SHA256_before_parsing': sha, 'input_SHA256_end': end_sha,
           'inputs_unchanged': True, 'analysis_SHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'first_exploratory_read_scope': 'underneck function-location rg occurred before that exploratory SHA; this analysis run seals all inputs before parsing',
           'candidate_position_W_m': candidate['position_W_m'], 'candidate_quaternion_xyzw': candidate['quaternion_xyzw'],
           'initial_equivalent_xyz_witness_deg': witness,
           'initial_witness_SO3_error_deg': float(np.degrees((Rotation.from_euler('xyz', witness, degrees=True)*r_initial.inv()).magnitude())),
           'synthetic_0_01deg_world_perturbations_not_native': synthetic, 'trials': results}
OUT.mkdir(parents=True, exist_ok=True)
(OUT/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
for trial, result in results.items():
    print(trial, result['exact_matched_count'], result['matched_true'], result['matched_false'], result['false_predicate_counts'])
    print('minimum false', result['minimum_SO3_false_sample'])
