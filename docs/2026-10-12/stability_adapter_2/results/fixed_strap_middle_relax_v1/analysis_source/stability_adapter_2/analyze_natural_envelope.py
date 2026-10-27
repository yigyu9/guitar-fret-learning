"""Re-evaluate saved free-guitar poses; no simulator or controller invocation."""
from pathlib import Path
import hashlib
import json

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'stability_adapter_2'
B = ROOT / 'docs/2026-10-12/stability_adapter_2/results'
OUT = B / 'natural_envelope_assessment_v1'
RUNS = {
    'original': B / 'small_wrist_motion_v1/native',
    'joint18': B / 'joint_only_fixed_strap_v1/native',
    'shoulder_minus': B / 'fixed_strap_shoulder_response_v1/minus008',
    'shoulder_plus': B / 'fixed_strap_shoulder_response_v1/plus008',
}
LA = 1.1018469719600776


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def angles_deg(q, reference):
    """Shortest relative quaternion angle, stable near zero and sign invariant."""
    q = q / np.linalg.norm(q, axis=-1, keepdims=True)
    reference = reference / np.linalg.norm(reference)
    v = reference[3] * q[:, :3] - q[:, 3, None] * reference[:3] - np.cross(reference[:3], q[:, :3])
    w = q[:, 3] * reference[3] + q[:, :3] @ reference[:3]
    return np.degrees(2 * np.arctan2(np.linalg.norm(v, axis=1), np.abs(w)))


def main():
    assert not any((OUT / name).exists() for name in ['analysis.json', 'windows.jsonl', 'timeline.jsonl'])
    paths = [Path(__file__).resolve(), A / 'NATURAL_PLAYING_ENVELOPE.md', A / 'NATURAL_ENVELOPE_ASSESSMENT_PLAN.md']
    paths += [folder / name for folder in RUNS.values() for name in ['initial_values.json', 'report.json', 'trace.jsonl', 'states.jsonl']]
    before = {str(p): sha(p) for p in paths}
    checks, summaries, windows, timeline = {}, [], [], []
    goals = []
    for label, folder in RUNS.items():
        initial, report = read(folder / 'initial_values.json'), read(folder / 'report.json')
        trace, states = rows(folder / 'trace.jsonl'), rows(folder / 'states.jsonl')
        checks[label + '_complete_ordered'] = report['completed'] and report['physics_steps'] == 1200 and len(trace) == len(states) == 1201 and [s['physics_step'] for s in states] == list(range(1201))
        checks[label + '_same_fixed_LA'] = initial['absolute_strap_rest_length_m'] == LA and all(t['strap_rest_length_m'] == LA for t in trace)
        times = np.array([t['time_s'] for t in trace])
        p = np.array([t['guitar_position_m'] for t in trace])
        q = np.array([t['guitar_quaternion_xyzw'] for t in trace])
        raw_p = np.array([[s['guitar_body_states'][0]['pose']['p'][k] for k in 'xyz'] for s in states])
        raw_q = np.array([[s['guitar_body_states'][0]['pose']['r'][k] for k in 'xyzw'] for s in states])
        checks[label + '_finite_pose_clock'] = bool(np.isfinite(p).all() and np.isfinite(q).all() and np.all(np.linalg.norm(q, axis=1) > .99) and np.allclose(times, np.arange(1201) / 240, rtol=0, atol=1e-14))
        raw_q /= np.linalg.norm(raw_q, axis=1, keepdims=True)
        checks[label + '_raw_pose_matches_trace'] = bool(np.array_equal(p, raw_p) and np.max(np.minimum(np.linalg.norm(q - raw_q, axis=1), np.linalg.norm(q + raw_q, axis=1))) < 1e-12)
        goal_p = np.array(initial['guitar_goal_position_W_m'])
        goal_q = np.array(initial['guitar_goal_quaternion_xyzw'])
        goals.append((goal_p, goal_q))
        dp = np.linalg.norm(p - goal_p, axis=1) * 1000
        dr = angles_deg(q, goal_q)
        independent = np.degrees((Rotation.from_quat(q) * Rotation.from_quat(goal_q).inv()).magnitude())
        checks[label + '_independent_angle_and_trace'] = bool(np.max(np.abs(dr - independent)) < 1e-10 and np.array_equal(angles_deg(-q, goal_q), dr) and np.max(np.abs(dp - np.array([t['position_error_m'] for t in trace]) * 1000)) < 1e-9 and np.max(np.abs(dr - np.array([t['rotation_error_deg'] for t in trace]))) < 1e-5)
        outside = (dp > 30) | (dr > 5)
        local_windows = []
        for start in range(480, 961, 4):
            stop = start + 240
            wp = np.linalg.norm(p[start:stop + 1] - p[start], axis=1) * 1000
            wr = angles_deg(q[start:stop + 1], q[start])
            record = dict(run=label, start_step=start, end_step=stop, start_s=start / 240, end_s=stop / 240, samples=241, max_position_change_mm=float(wp.max()), max_rotation_change_deg=float(wr.max()), position_peak_step=start + int(wp.argmax()), rotation_peak_step=start + int(wr.argmax()), within_provisional_window=bool(wp.max() <= 5 and wr.max() <= 1))
            local_windows.append(record)
        checks[label + '_121_complete_1s_windows'] = len(local_windows) == 121 and local_windows[0]['start_s'] == 2 and local_windows[-1]['end_s'] == 5
        summary = dict(run=label, directory=str(folder), max_initial_position_mm=float(dp.max()), max_initial_rotation_deg=float(dr.max()), outside_samples=int(outside.sum()), observed_samples=1201, inside_sample_fraction=float((~outside).mean()), window_count=121, windows_within_provisional_limits=sum(w['within_provisional_window'] for w in local_windows))
        for key in ['max_position_change_mm', 'max_rotation_change_deg']:
            values = [w[key] for w in local_windows]
            summary[key] = dict(p50=float(np.percentile(values, 50)), p95=float(np.percentile(values, 95)), max=float(max(values)))
        summaries.append(summary)
        windows.extend(local_windows)
        timeline.extend(dict(run=label, physics_step=i, time_s=float(times[i]), initial_position_error_mm=float(dp[i]), initial_rotation_error_deg=float(dr[i]), outside_provisional_envelope=bool(outside[i])) for i in range(1201))
    checks['same_nominal_goal_four_runs'] = all(np.array_equal(p, goals[0][0]) and np.array_equal(q, goals[0][1]) for p, q in goals)
    after = {str(p): sha(p) for p in paths}
    checks['inputs_preserved'] = before == after
    assert all(checks.values()), checks
    result = dict(checks=checks, runs=summaries, input_sha256_before=before, input_sha256_after=after, provisional_limits=dict(initial_position_mm=30, initial_rotation_deg=5, window_position_mm=5, window_rotation_deg=1), window_definition='start at steps480..960 stride4; inclusive241 samples/start relative; max within complete1s window; no mandatory WAIT', native_initializations=0, physics_steps=0, actor_inference_calls=0, training_updates=0, naturalness_or_playing_success_certified=False)
    for name, records in [('windows.jsonl', windows), ('timeline.jsonl', timeline)]:
        (OUT / name).write_text(''.join(json.dumps(r, allow_nan=False) + '\n' for r in records))
    (OUT / 'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(checks=len(checks), runs=summaries), allow_nan=False))


if __name__ == '__main__':
    main()
