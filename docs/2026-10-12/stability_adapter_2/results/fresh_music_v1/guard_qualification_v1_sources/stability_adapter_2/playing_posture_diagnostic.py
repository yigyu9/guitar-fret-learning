"""Offline diagnostics on one saved native Fret/strap run; no simulator import."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

from tab2body.fret_v2_contract import FRET_V2_BLOCK_SLICES

ROOT = Path(__file__).resolve().parents[1]
FONT = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FINGERS = ('index', 'middle', 'ring', 'pinky')


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xyz(value):
    return np.array([value[k] for k in ('x', 'y', 'z')], dtype=float)


def body_pose(state):
    pose = state['pose']
    return xyz(pose['p']), Rotation.from_quat([pose['r'][k] for k in ('x', 'y', 'z', 'w')])


def posture(gp, gr, cp, pelvis_rotation):
    # Source anatomy: subject-right=-X, forward=-Y, up=+Z in Pelvis frame.
    basis = pelvis_rotation.apply([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
    neck, front = gr.apply([[0, 1, 0], [0, 0, 1]])
    return {
        'neck_elevation_deg': float(np.degrees(np.arcsin(np.clip(neck[2], -1, 1)))),
        'front_angle_to_root_forward_deg': float(np.degrees(np.arccos(np.clip(front @ basis[1], -1, 1)))),
        'front_normal_world_z': float(front[2]),
        'root_minus_chest_right_forward_up_m': ((gp - cp) @ basis.T).tolist(),
        'neck_direction_W': neck.tolist(), 'front_normal_W': front.tolist(),
    }


def joint_margin(q, lower, upper, names, indices):
    lower, upper = np.asarray(lower)[indices], np.asarray(upper)[indices]
    q = np.asarray(q)[indices]
    if np.any(upper <= lower):
        raise ValueError('Selected diagnostic joints must have nonzero limit width')
    margins = np.minimum(q - lower, upper - q)
    fractions = margins / (upper - lower)
    i = int(np.argmin(margins))
    j = int(np.argmin(fractions))
    return {'min_margin_rad': float(margins[i]), 'joint': names[indices[i]],
            'min_fraction': float(fractions[j]), 'fraction_joint': names[indices[j]],
            'outside_count': int(np.count_nonzero(margins < 0))}


def target_markers(observation):
    obs = np.asarray(observation, dtype=float)
    if obs.shape != (420,) or not np.isfinite(obs).all():
        raise ValueError('Expected one finite saved Fret-v2 420D observation')
    hand = obs[FRET_V2_BLOCK_SLICES['O_hand_geometry']]
    event = obs[FRET_V2_BLOCK_SLICES['O_current_event']]
    target = obs[FRET_V2_BLOCK_SLICES['O_target_geometry']]
    result = []
    for i, finger in enumerate(FINGERS):
        if event[0] > .5 and event[1 + i] > .5:
            tip = hand[30 + 6*i:33 + 6*i]
            vector = target[3*i:3*i+3]
            result.append({'finger': finger, 'tip_G_m': tip.tolist(),
                           'target_G_m': (tip + vector).tolist(),
                           'marker_distance_mm': float(np.linalg.norm(vector)*1000),
                           'signed_press_depth_mm': float(target[12+i]*1000),
                           'string_lateral_error_mm': float(target[16+i]*1000)})
    return result, float(np.linalg.norm(target[20:23])*1000)


def aligned_observations(controls, terminal, last_step):
    result = {}
    for control in controls:
        if control['actor_used']:
            step = round(control['time_s']*240)
            if abs(control['time_s'] - step/240) > 1e-7 or step in result:
                raise ValueError('Control times are not unique physics-step timestamps')
            result[step] = (control['observation'][0], 'pre_integration_observation')
    if not controls[-1]['source_done'][0]:
        raise ValueError('This diagnostic expects a saved source terminal')
    if last_step != round(controls[-1]['time_s']*240) + 4:
        raise ValueError('Terminal evaluation must follow the last control by four steps')
    result[last_step] = (terminal['terminal_observation'][0], 'terminal_observation')
    return result


def project(points, camera, width, height):
    points = np.asarray(points)
    view = np.column_stack((points, np.ones(len(points)))) @ np.asarray(camera['view_matrix'])
    clip = view @ np.asarray(camera['projection_matrix'])
    with np.errstate(divide='ignore', invalid='ignore'):
        ndc = clip[:, :2] / clip[:, 3, None]
    pixels = np.column_stack(((ndc[:, 0]+1)*width/2, (1-ndc[:, 1])*height/2))
    valid = (view[:, 2] < -.001) & np.isfinite(pixels).all(axis=1)
    valid &= (pixels[:, 0] >= 0) & (pixels[:, 0] < width) & (pixels[:, 1] >= 0) & (pixels[:, 1] < height)
    return pixels, valid


def annotate(image_path, camera, row, state, destination):
    image = Image.open(image_path).convert('RGB')
    w, h = image.size
    canvas = Image.new('RGB', (w+430, h), '#151a22')
    canvas.paste(image, (0, 0))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT), 19)
    gp, gr = body_pose(state['guitar_body_states'][0])
    # Lines are unoccluded diagnostic guides. They add no geometry or contact.
    points = [gp, gp+gr.apply([0, .20, 0]), gp+gr.apply([0, 0, .13])]
    markers = row['active_targets'] or []
    for marker in markers:
        points.extend([gp+gr.apply(marker['tip_G_m']), gp+gr.apply(marker['target_G_m'])])
    pixels, valid = project(points, camera, w, h)
    for i, color in ((1, '#ffd166'), (2, '#00d4ff')):
        if valid[0] and valid[i]:
            draw.line([tuple(pixels[0]), tuple(pixels[i])], fill=color, width=4)
            draw.ellipse([*(pixels[i]-5), *(pixels[i]+5)], fill=color)
    for i, marker in enumerate(markers):
        a, b = 3+2*i, 4+2*i
        if valid[a] and valid[b]:
            draw.line([tuple(pixels[a]), tuple(pixels[b])], fill='#ff6ce4', width=3)
        for j, color in ((a, '#ffffff'), (b, '#ff6ce4')):
            if valid[j]:
                draw.ellipse([*(pixels[j]-6), *(pixels[j]+6)], outline=color, width=3)
    text = [f"Native Isaac Gym | t={row['time_s']:.4f}s", f"step {row['physics_step']} | {row['phase']}",
            '', 'GUIDES (not contact / depth proof)', 'Yellow: neck local +Y', 'Cyan: front normal local +Z',
            'White: active fingertip marker', 'Magenta: current assigned target', '',
            f"Neck elevation: {row['neck_elevation_deg']:+.2f} deg",
            f"Front vs body-forward: {row['front_angle_to_root_forward_deg']:.2f} deg",
            f"Front normal world Z: {row['front_normal_world_z']:+.3f}", '',
            'G root minus Chest (root basis), m:']
    rel = row['root_minus_chest_right_forward_up_m']
    text += [f'right {rel[0]:+.3f}, forward {rel[1]:+.3f}', f'up {rel[2]:+.3f}',
             f"Position box: {'inside' if row['position_box_inside'] else 'OUTSIDE'}",
             'Rotation-set membership: not evaluated', '', 'Arm12 min NATIVE joint margin:']
    for side in ('L', 'R'):
        m = row['arm_limits'][side]['native']
        text += [f"{side}: {m['min_margin_rad']:+.4f} rad ({m['joint']})"]
    text += ['', 'Fret targets at this physics state:']
    text += [f"{m['finger']}: {m['marker_distance_mm']:.1f} mm" for m in markers] or ['Not stored (policy not running)']
    text += ['', 'Signed margin is model feasibility,', 'not anatomical naturalness or reach.', 'New soft thresholds: UNSET']
    for i, line in enumerate(text):
        draw.text((w+14, 14+i*22), line, font=font, fill='white')
    canvas.save(destination)


def run(data, out):
    out.mkdir(exist_ok=False)
    inputs = [data/name for name in ('initial_values.json', 'trace.json', 'controls.json', 'terminal_info.json', 'report.json', 'images/capture.json')]
    inputs += [Path(__file__), ROOT/'tab2body/fret_v2_contract.py', FONT,
               ROOT/'tab2body/env/tasks/task_fret.py', ROOT/'tab2body/assets/guitar_asset.xml',
               ROOT/'tab2body/assets/smpl_mpl_hands_body.xml',
               ROOT/'stability_adapter_2/PLAYING_POSTURE_DIAGNOSTIC_PLAN.md',
               ROOT/'stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md']
    initial, trace, controls, terminal, report, capture = [read(p) for p in inputs[:6]]
    chosen = [int(np.argmin([abs(t['time_s']-s) for t in trace])) for s in (0, 2, 3, trace[-1]['time_s'])]
    for index in chosen:
        for view in ('whole_body', 'hands'):
            inputs += [data/f'images/frames/{view}/{index:05d}.png', data/f'images/raw/frames/{view}/{index:05d}.png']
    before = {str(p): sha(p) for p in inputs}
    save(out/'inputs_before.json', before)
    names = initial['human_body_names']
    joints = initial['joint_names']
    obs = aligned_observations(controls, terminal, trace[-1]['physics_step'])
    initial_chest_z = body_pose(trace[0]['native_state']['human_body_states'][names.index('Chest')])[0][2]
    rows = []
    alignment_errors = []
    for index, t in enumerate(trace):
        frame = capture['frames'][index]
        assert frame['physics_step'] == t['physics_step'] and abs(frame['time_s']-t['time_s']) < 1e-9
        state = t['native_state']
        assert state['physics_step'] == t['physics_step']
        gp, gr = body_pose(state['guitar_body_states'][0])
        assert np.allclose(gp, t['position_W_m'], atol=1e-8, rtol=0)
        cp, _ = body_pose(state['human_body_states'][names.index('Chest')])
        _, pr = body_pose(state['human_body_states'][names.index('Pelvis')])
        row = {'frame_index': index, 'physics_step': t['physics_step'], 'time_s': t['time_s'],
               'phase': t['phase'], **posture(gp, gr, cp, pr)}
        lo, hi = np.array([-.50, -.15, .65]), np.array([-.15, .15, initial_chest_z])
        margin = np.minimum(gp-lo, hi-gp)
        row.update(position_box_inside=bool(np.all(margin >= 0)), position_box_margin_xyz_m=margin.tolist())
        q = [v['pos'] for v in state['human_dof_states']]
        row['arm_limits'] = {}
        for side in ('L', 'R'):
            slots = [i for i, name in enumerate(joints) if name.startswith(tuple(f'{side}_{part}_' for part in ('Thorax', 'Shoulder', 'Elbow', 'Wrist')))]
            assert len(slots) == 12
            row['arm_limits'][side] = {kind: joint_margin(q, initial[f'{kind}_lower_rad'], initial[f'{kind}_upper_rad'], joints, slots) for kind in ('native', 'source')}
        row.update(active_targets=None, observation_origin=None, wrist_vector_norm_mm=None)
        if t['physics_step'] in obs:
            observation, origin = obs[t['physics_step']]
            row['active_targets'], row['wrist_vector_norm_mm'] = target_markers(observation)
            row['observation_origin'] = origin
            hand = np.asarray(observation)[FRET_V2_BLOCK_SLICES['O_hand_geometry']]
            for i, finger in enumerate(FINGERS):
                tip, _ = body_pose(state['human_body_states'][names.index(f'LH:{finger}_top')])
                alignment_errors.append(float(np.linalg.norm(gr.inv().apply(tip-gp)-hand[30+6*i:33+6*i])))
        rows.append(row)
    assert max(alignment_errors) < 1e-6
    for index in chosen:
        frame = capture['frames'][index]
        for view in ('whole_body', 'hands'):
            image_path = data/f'images/frames/{view}/{index:05d}.png'
            raw = data/f'images/raw/frames/{view}/{index:05d}.png'
            assert before[str(image_path)] == frame['image_sha256'][str(image_path)]
            assert before[str(raw)] == frame['raw_image_sha256'][str(raw)]
            annotate(image_path, frame['cameras'][view], rows[index], trace[index]['native_state'], out/f'frame_{index:03d}_{view}.png')
    # Compact comparison keeps the native scene untouched; values below each scene.
    font = ImageFont.truetype(str(FONT), 20)
    comparison = Image.new('RGB', (1600, 590), '#151a22')
    draw = ImageDraw.Draw(comparison)
    for column, index in enumerate((chosen[1], chosen[-1])):
        picture = Image.open(out/f'frame_{index:03d}_hands.png').crop((0, 0, 1280, 720)).resize((800, 450))
        comparison.paste(picture, (800*column, 0))
        row = rows[index]
        lines = [f"t={row['time_s']:.4f}s | step {row['physics_step']}",
                 f"Neck {row['neck_elevation_deg']:+.2f} deg | Front/body {row['front_angle_to_root_forward_deg']:.2f} deg"]
        lines += [f"{m['finger']} target error: {m['marker_distance_mm']:.1f} mm" for m in row['active_targets'] or []]
        lines += ['Guides: yellow=neck, cyan=front, magenta=target; not contact proof']
        for k, line in enumerate(lines):
            draw.text((800*column+12, 459+25*k), line, font=font, fill='white')
    comparison.save(out/'comparison.png')
    fig, axes = plt.subplots(4, 1, figsize=(12, 11), sharex=True, constrained_layout=True)
    times = [r['time_s'] for r in rows]
    for key, label in [('neck_elevation_deg', 'Neck elevation'), ('front_angle_to_root_forward_deg', 'Front / body-forward angle')]:
        axes[0].plot(times, [r[key] for r in rows], label=label)
    axes[0].set_ylabel('deg'); axes[0].legend(loc='upper left', bbox_to_anchor=(1, 1))
    for side in ('L', 'R'):
        for kind, style in [('native', '-'), ('source', '--')]:
            axes[1].plot(times, [r['arm_limits'][side][kind]['min_margin_rad'] for r in rows], style, label=f'{side}12 {kind}')
    axes[1].set_ylabel('Signed min margin, rad'); axes[1].legend(loc='upper left', bbox_to_anchor=(1, 1))
    for i, label in enumerate(('right', 'forward', 'up')):
        axes[2].plot(times, [1000*r['root_minus_chest_right_forward_up_m'][i] for r in rows], label=label)
    axes[2].set_ylabel('G root - Chest, mm'); axes[2].legend(loc='upper left', bbox_to_anchor=(1, 1))
    for finger in FINGERS:
        values = [next((m['marker_distance_mm'] for m in r['active_targets'] or [] if m['finger'] == finger), np.nan) for r in rows]
        axes[3].plot(times, values, marker='.', markersize=2, label=finger)
    axes[3].set_ylabel('Active marker error, mm'); axes[3].legend(loc='upper left', bbox_to_anchor=(1, 1)); axes[3].set_xlabel('Native physics time, s')
    for ax in axes:
        ax.axvline(2, color='gray', linestyle=':', linewidth=1)
        ax.grid(alpha=.25)
    fig.suptitle('Saved Isaac Gym run | 2 s handoff | no new naturalness thresholds')
    fig.savefig(out/'trends.png', dpi=150); plt.close(fig)
    summary = {'input_run': str(data), 'new_physics_runs': 0, 'learning_updates': 0,
               'source_episode_music_success': report['music_success'], 'source_stop_reason': report['stop_reason'],
               'physics_duration_s': trace[-1]['time_s'], 'frame_count': len(rows),
               'selected_frame_indices': chosen, 'max_tip_alignment_error_m': max(alignment_errors),
               'observation_aligned_state_count': sum(r['observation_origin'] is not None for r in rows),
               'rotation_set_membership_evaluated': False, 'soft_naturalness_thresholds_set': False,
               'position_box_outside_count': sum(not r['position_box_inside'] for r in rows),
               'wrist_target_presence_certified': False,
               'selected_rows': [rows[i] for i in chosen],
               'versions': {'numpy': np.__version__, 'matplotlib': matplotlib.__version__}}
    save(out/'metrics.json', rows); save(out/'summary.json', summary)
    after = {p: sha(p) for p in before}
    assert before == after
    save(out/'inputs_after.json', after)
    save(out/'checks.json', {'input_hashes_unchanged': before == after, 'tip_alignment_below_1um': max(alignment_errors) < 1e-6,
                             'capture_trace_steps_exact': True, 'selected_image_hashes_match_capture': True,
                             'terminal_observation_at_last_physics_step': True})
    print(json.dumps({k: summary[k] for k in ('frame_count', 'physics_duration_s', 'max_tip_alignment_error_m', 'position_box_outside_count')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.data.resolve(), args.out.resolve())
