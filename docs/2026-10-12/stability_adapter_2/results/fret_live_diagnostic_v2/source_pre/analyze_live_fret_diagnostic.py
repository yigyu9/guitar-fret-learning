"""Analyze frozen current-guitar recordings; preserves inputs and former baseline."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .gym_trial_recording import sha
from .live_fret_geometry import actual_guitar_contacts


def read(p): return json.loads(Path(p).read_text())
def save(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, required=True); parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args(); phase = args.phase.resolve(); native = phase/'native/data'; out = phase/'analysis'
    out.mkdir(parents=True, exist_ok=False)
    paths = [Path(__file__), native/'images/capture.json', native/'images/raw/capture.json', native/'initial_values.json',
             native/'controls.json', native/'trace.json', native/'report.json', native/'terminal_info.json',
             native/'images/videos.json', native/'images/raw/videos.json', phase/'native/inputs_before.json', phase/'native/inputs_after.json']
    paths += [args.baseline/n for n in ('controls.json', 'trace.json', 'initial_values.json', 'report.json')]
    inputs = {str(p.resolve()): sha(p) for p in paths}; save(out/'attempt.json', dict(input_sha256=inputs))
    capture = read(native/'images/capture.json'); frames = capture['frames']; report = read(native/'report.json')
    controls = read(native/'controls.json'); trace = read(native/'trace.json'); initial = read(native/'initial_values.json')
    raw = read(native/'images/raw/capture.json')['frames']; old_controls = read(args.baseline/'controls.json'); old_trace = read(args.baseline/'trace.json')
    initial_equal = initial['native_initial_state'] == read(args.baseline/'initial_values.json')['native_initial_state']
    controls_equal = controls == old_controls; trace_equal = trace == old_trace
    image_hashes_valid = all(sha(p) == digest for row in frames for field in ('image_sha256', 'raw_image_sha256') for p, digest in row[field].items())
    raw_equal = len(raw) == len(frames) and all(a['physics_step'] == b['physics_step'] and a['image_sha256'] == b['raw_image_sha256'] for a, b in zip(raw, frames))
    aligned = all(abs(row['time_s']-row['physics_step']/240) < 1e-12 for row in frames)
    control_by_end = {round((r['time_s']+1/60)*240): r for r in controls}
    phase_aligned = all(row['goal_frame_at_capture'] is None or row['measurement_phase'] != 'before source evaluation'
        or row['goal_frame_at_capture'] == int(control_by_end[row['physics_step']]['source_frame_before'][0]) for row in frames)
    csv_rows = []
    for row in frames:
        for target in row['targets']:
            csv_rows.append(dict(time_s=row['time_s'], physics_step=row['physics_step'], goal_frame=row['goal_frame_at_capture'],
                measurement_phase=row['measurement_phase'], string=target['string_index_zero_based']+1, fret=target['fret'],
                finger=target['finger'], tip_marker_distance_mm=target['tip_marker_distance_m']*1000,
                one_sided_pad_approach_mm=target['one_sided_pad_approach_distance_m']*1000,
                wrist_goal_distance_mm=row['wrist_goal_distance_m']*1000 if row['wrist_goal_distance_m'] is not None else None,
                left_actual_contact_pairs=row['left_contact_pair_count'], guitar_rotation_change_deg=row['rotation_change_deg'],
                position_box_excess_mm=row['user_position_box_distance_m']*1000))
    with (out/'active_targets.csv').open('w') as f:
        if csv_rows:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0])); writer.writeheader(); writer.writerows(csv_rows)
    play = [row for row in frames if row['time_s'] >= 2 and row['measurement_phase'] == 'before source evaluation']
    selected = []
    for time in [0, 2, 5, 8, 10, frames[-1]['time_s']]:
        i = min(range(len(frames)), key=lambda j: abs(frames[j]['time_s']-time)); row = frames[i]
        entry = {k: row[k] for k in ('physics_step', 'time_s', 'phase_at_capture', 'measurement_phase', 'body_center_pelvis_RFU_m',
            'rotation_change_deg', 'neck_elevation_deg', 'user_position_box_distance_m', 'wrist_G_m', 'wrist_goal_distance_m', 'goal_frame_at_capture', 'targets', 'left_contact_pair_count')}
        entry['frame_index'] = i; entry['images'] = {}
        for view in ('whole_body', 'hands'):
            source = native/'images/frames'/view/f'{i:05d}.png'; dest = out/f'{view}_step_{row["physics_step"]:05d}.png'
            shutil.copy2(source, dest); entry['images'][view] = str(dest)
        selected.append(entry)
    # Use full 60 Hz contact records for occupancy; raw pairs need not carry positive impulse.
    contact_stats = {}
    for phase_name in ('PREPARE', 'PLAY'):
        rows = [r for r in controls if r['phase'] == phase_name]
        left_samples = positive_samples = 0; body_counts = {}
        for row in rows:
            actual = actual_guitar_contacts(row['native_contacts'])
            left = [r for r in actual if any(n.startswith('human/LH:') or n == 'human/L_Wrist' for n in (r['body0_name'], r['body1_name']))]
            left_samples += bool(left); positive_samples += any(r['lambda'] > 0 for r in left)
            for name in {n for r in left for n in (r['body0_name'], r['body1_name']) if n.startswith('human/')}:
                body_counts[name] = body_counts.get(name, 0)+1
        contact_stats[phase_name] = dict(samples=len(rows), samples_with_left_contact_pair=left_samples,
            samples_with_positive_raw_lambda_left_pair=positive_samples, body_sample_counts=body_counts,
            scope='60 Hz pre-integration native pair samples; raw lambda units not converted; presence is not press/music success')
    t = np.array([r['time_s'] for r in frames])
    fig, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=True, constrained_layout=True)
    c = np.array([r['body_center_pelvis_RFU_m'] for r in frames])*100
    for j, label in enumerate(('Right', 'Forward', 'Up')): axes[0].plot(t, c[:, j], label=label)
    axes[0].set_ylabel('Body-center RFU (cm)'); axes[0].legend(ncol=3); axes[0].set_title('Isaac Gym / unchanged Fret finger control / strap OFF')
    axes[1].plot(t, [r['rotation_change_deg'] for r in frames], label='Rotation from t0')
    axes[1].plot(t, [r['neck_elevation_deg'] for r in frames], label='Neck elevation'); axes[1].set_ylabel('deg'); axes[1].legend()
    wrist = [np.nan if r['wrist_goal_distance_m'] is None else r['wrist_goal_distance_m']*1000 for r in frames]
    axes[2].plot(t, wrist, color='purple', label='Wrist to current guitar goal')
    for finger, color in zip(('index', 'middle', 'ring', 'pinky'), ('orange', 'blue', 'green', 'red')):
        pts = [r for r in csv_rows if r['finger'] == finger]
        axes[2].scatter([r['time_s'] for r in pts], [r['tip_marker_distance_mm'] for r in pts], s=8, label=finger, color=color)
    axes[2].set_ylabel('Marker/goal error (mm)'); axes[2].legend(ncol=3)
    axes[3].step(t, [r['left_contact_pair_count'] for r in frames], label='Left actual contact pairs', where='post')
    axes[3].plot(t, [r['user_position_box_distance_m']*1000 for r in frames], label='Position-box excess (mm)')
    axes[3].set_ylabel('Pairs / mm'); axes[3].set_xlabel('Physical time (s)'); axes[3].legend()
    for ax in axes: ax.axvline(2, color='black', ls='--', lw=1); ax.grid(alpha=.2)
    fig.savefig(out/'timeline.png', dpi=150); plt.close(fig)
    checks = dict(native_run_complete=report['completed_recording'], source_checks_pass=all(report['checks'].values()),
        snapshot_inputs_unchanged=read(phase/'native/inputs_after.json')['inputs_unchanged'],
        diagnostics_native_readonly=all(r['render_preserves_states'] for r in frames),
        diagnostics_source_readonly=all(r['source_readonly'] for r in frames),
        diagnostics_targets_readonly=all(r['submitted_targets_unchanged'] for r in frames),
        frames_raw_aligned=raw_equal, timestamps_physics_aligned=aligned, goal_capture_phase_aligned=phase_aligned,
        image_hashes_valid=image_hashes_valid, baseline_initial_state_exact=initial_equal,
        baseline_controls_exact=controls_equal, baseline_trace_exact=trace_equal,
        complete_t0_to_terminal=frames[0]['physics_step'] == 0 and frames[-1]['physics_step'] == report['physics_steps'],
        no_full_rotation_set_claim=all(not r['rotation_set_evaluated'] for r in frames),
        inputs_unchanged=all(sha(p) == digest for p, digest in inputs.items()))
    summary = dict(checks=checks, report=report, selected_frames=selected, contact_stats=contact_stats,
        frame_count=len(frames), play_capture_count=len(play), user_position_outside_frames=sum(not r['user_position_inside'] for r in frames),
        max_rotation_change_deg=max(r['rotation_change_deg'] for r in frames),
        play_wrist_error_mm_range=[min(r['wrist_goal_distance_m'] for r in play)*1000, max(r['wrist_goal_distance_m'] for r in play)*1000],
        per_finger_target_samples={finger: dict(count=len(rows), min_mm=min([r['tip_marker_distance_mm'] for r in rows], default=None),
            max_mm=max([r['tip_marker_distance_mm'] for r in rows], default=None)) for finger in ('index', 'middle', 'ring', 'pinky')
            for rows in [[r for r in csv_rows if r['finger'] == finger and r['time_s'] >= 2]]},
        wrist_G_displacement_from_handoff_mm=[dict(time_s=r['time_s'], value_mm=float(np.linalg.norm(np.asarray(r['wrist_G_m'])-np.asarray(selected[1]['wrist_G_m']))*1000)) for r in selected[1:]],
        input_sha256=inputs,
        limits='Body reference not mass CoM. Current-frame markers not pad contacts; cached ready is prior tracker. No full rotation set or penetration/safe-volume certification. Different target frames/events must not be compared as one fixed task.')
    save(out/'summary.json', summary)
    print(json.dumps({'checks': checks, 'frame_count': len(frames), 'physics_s': report['recorded_physics_duration_s'],
        'wrist_play_mm': summary['play_wrist_error_mm_range'], 'position_outside_frames': summary['user_position_outside_frames']}, indent=2))
    if not all(checks.values()): raise AssertionError('see summary checks; baseline differences must be reviewed')


if __name__ == '__main__': main()
