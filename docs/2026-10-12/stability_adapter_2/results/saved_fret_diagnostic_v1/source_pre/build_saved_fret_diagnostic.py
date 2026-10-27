"""Full saved-native episode overlays; no simulator import or new physics."""
import argparse
import csv
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .gym_trial_recording import GymTrialRecording, sha
from .strap_trial_recording import project
from .live_fret_geometry import pose, position_geometry, actual_guitar_contacts, EDGES, FINGERS
from .playing_posture_diagnostic import aligned_observations, target_markers
from tab2body.fret_v2_contract import FRET_V2_BLOCK_SLICES

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT/'docs/2026-10-12/stability_adapter_2/results'
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')

def read(p): return json.loads(Path(p).read_text())
def save(p, value): Path(p).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')

def annotate(raw_path, destination, row, view, projection):
    im = Image.open(raw_path).convert('RGB'); w, h = im.size; draw = ImageDraw.Draw(im)
    stats = dict(xray_segments=0, outside_segments=0)
    def line(a, b, color, width=3):
        a, b = np.asarray(a), np.asarray(b)
        px, z, _ = project(np.array([a, b]), view, projection, w, h)
        if not np.isfinite(px).all() or np.any(z >= -.001):
            stats['outside_segments'] += 1; return
        count = min(4096, max(2, int(np.linalg.norm(px[1]-px[0])*2)+1))
        points = a+(b-a)*np.linspace(0, 1, count)[:, None]
        px, z, valid = project(points, view, projection, w, h)
        for i in range(count-1):
            if not (valid[i] and valid[i+1]): continue
            if i//12 % 2 == 0:
                draw.line([tuple(px[i]), tuple(px[i+1])], fill=color, width=2); stats['xray_segments'] += 1
    def marker(point, color, radius=5):
        px, z, valid = project(np.asarray([point]), view, projection, w, h)
        if valid[0]:
            x, y = px[0]
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), outline=color, width=3)
    box = row['user_body_center_box_W_m']
    for i, j in EDGES: line(box[i], box[j], (75, 190, 255), 2)
    marker(row['body_center_W_m'], (255, 100, 200), 7)
    for target in row['targets']:
        line(target['tip_marker_W_m'], target['target_W_m'], (255, 175, 50))
        marker(target['tip_marker_W_m'], (255, 175, 50))
        marker(target['target_W_m'], (245, 245, 245), 4)
    for point in row['left_contact_body_origins_W_m'].values(): marker(point, (80, 255, 140), 6)
    canvas = Image.new('RGB', (w+480, h), '#131a24'); canvas.paste(im, (0, 0)); draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(str(FONT), 20); small = ImageFont.truetype(str(FONT), 17)
    def text(y, value, color='white', size=font): draw.text((w+15, y), value, font=size, fill=color)
    text(12, '저장 Isaac Gym · 현재 기타 기준 Fret')
    text(45, f"t={row['time_s']:.3f}s  step={row['physics_step']}  {row['phase_at_capture']}")
    c = np.asarray(row['body_center_pelvis_RFU_m'])*100
    text(80, '바디 중심 (골반 오른쪽/앞/위 cm)')
    text(112, ' / '.join(f'{v:+.2f}' for v in c), (255, 100, 200))
    text(146, f"사용자 위치box: {'안' if row['user_position_inside'] else '밖'} / 이탈 {row['user_position_box_distance_m']*1000:.2f} mm")
    text(178, f"초기 대비 회전: {row['rotation_change_deg']:.2f}°")
    text(210, f"넥 고도: {row['neck_elevation_deg']:+.2f}°")
    text(242, f"앞면-골반 전방: {row['front_to_pelvis_forward_deg']:.2f}°")
    text(274, '전체 회전 허용집합 판정: 미적용', '#aeb6c3', small)
    text(304, f"goal frame: {row['goal_frame_at_capture']}")
    if row['wrist_goal_distance_m'] is not None: text(336, f"저장 손목 목표벡터: {row['wrist_goal_distance_m']*1000:.1f} mm")
    else: text(336, '손목 목표: 미초기화/미제공')
    text(370, '활성 손가락 : 손끝목표 거리 mm', size=small)
    for i, target in enumerate(row['targets']):
        text(398+i*24, f"{target['finger']}: {target['tip_marker_distance_m']*1000:.1f}", (255, 175, 50), small)
    text(552, f"실제 기타–왼손 접촉 pair: {row['left_contact_pair_count'] if row['left_contact_pair_count'] is not None else '미측정'}", (80, 255, 140))
    text(582, '초록: 접촉 body 원점 (표면 접촉점 아님)', (80, 255, 140), small)
    text(610, '파랑: 현재 회전의 조건부 위치 범위', (75, 190, 255), small)
    text(637, '주황: 손끝–목표 / 흰 원: 현재 목표', (255, 175, 50), small)
    text(664, '투시 설명선 · 가려짐 미판정 · 스트랩 OFF', '#aeb6c3', small)
    text(690, '저장 기록 후처리 · 새 물리 실행 없음', '#aeb6c3', small)
    canvas.save(destination); return stats


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True); args = parser.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    data = RESULTS/'fret_fingers_arm_hold_v1/native/data'; camera_file = RESULTS/'fret_live_diagnostic_v2/native/data/images/capture.json'
    base_file = RESULTS/'initial_middle3_alignment_v1/native/initial_values.json'
    capture = read(data/'images/capture.json'); trace = read(data/'trace.json'); controls = read(data/'controls.json')
    initial = read(data/'initial_values.json'); report = read(data/'report.json'); terminal = read(data/'terminal_info.json'); camera_rows = read(camera_file)['frames']
    paths = [Path(__file__), FONT, camera_file, base_file, ROOT/'stability_adapter_2/SAVED_FRET_DIAGNOSTIC_PLAN.md']
    paths += [data/n for n in ('images/capture.json', 'trace.json', 'controls.json', 'initial_values.json', 'report.json', 'terminal_info.json')]
    paths += [ROOT/'stability_adapter_2'/n for n in ('gym_trial_recording.py', 'strap_trial_recording.py', 'live_fret_geometry.py',
        'body_center_coordinates.py', 'validate_team_pose_envelope.py', 'playing_posture_diagnostic.py', 'underneck_pose_trial_v5.py', 'capture_isaac_gym_initial.py', 'environment.py')]
    paths += [ROOT/'tab2body/fret_v2_contract.py', data.parent/'inputs_before.json', RESULTS/'fret_live_diagnostic_v2/native/inputs_before.json']
    paths += [Path(p) for frame in capture['frames'] for p in frame['image_sha256']]
    inputs = {str(p.resolve()): sha(p) for p in paths}; save(out/'attempt.json', dict(input_sha256=inputs, new_physics_runs=0))
    assert report['completed_recording'] and report['stop_reason'] == 'source_terminal'
    assert len(trace) == len(capture['frames']) == 389
    assert all(a['physics_step'] == b['physics_step'] for a, b in zip(trace, capture['frames']))
    assert initial['native_initial_state'] == read(RESULTS/'fret_live_diagnostic_v2/native/data/initial_values.json')['native_initial_state']
    cameras = camera_rows[0]['cameras']; camera_constant = all(r['cameras'][v]['view_matrix'] == cameras[v]['view_matrix'] and
        r['cameras'][v]['projection_matrix'] == cameras[v]['projection_matrix'] for r in camera_rows for v in cameras)
    assert camera_constant
    old_hashes = read(data.parent/'inputs_before.json')['sha256']; new_hashes = read(RESULTS/'fret_live_diagnostic_v2/native/inputs_before.json')['sha256']
    camera_source_equal = all(old_hashes[str(ROOT/'stability_adapter_2'/n)] == new_hashes[str(ROOT/'stability_adapter_2'/n)] for n in
        ('underneck_pose_trial_v5.py', 'capture_isaac_gym_initial.py', 'environment.py', 'run_fret_fingers_arm_hold.py'))
    assert camera_source_equal
    prefix_pixels = True
    for i in range(len(camera_rows)):
        for name in cameras:
            a = np.asarray(Image.open(data/'images/frames'/name/f'{i:05d}.png').convert('RGBA'))
            p = RESULTS/'fret_live_diagnostic_v2/native/data/images/raw/frames'/name/f'{i:05d}.png'
            inputs[str(p)] = sha(p)
            b = np.asarray(Image.open(p).convert('RGBA')); prefix_pixels &= np.array_equal(a, b)
    assert prefix_pixels
    save(out/'attempt.json', dict(input_sha256=inputs, new_physics_runs=0))
    names = read(base_file)['human_body_names']; chest_z = initial['native_initial_state']['human_body_states'][names.index('Chest')]['pose']['p']['z']
    initial_rotation = pose(trace[0]['native_state']['guitar_body_states'][0])[1]
    observations = aligned_observations(controls, terminal, trace[-1]['physics_step'])
    by_step = {round(r['time_s']*240): r for r in controls}; rows = []; tip_errors = []
    for name in cameras: (out/'frames'/name).mkdir(parents=True, exist_ok=False)
    for i, frame in enumerate(capture['frames']):
        step = frame['physics_step']; state = trace[i]['native_state']; bodies = dict(zip(names, state['human_body_states']))
        gp, gr = pose(state['guitar_body_states'][0]); wrist = pose(bodies['L_Wrist'])[0]
        row = position_geometry(state['guitar_body_states'][0], bodies['Pelvis'], initial_rotation, chest_z)
        row.update(physics_step=step, time_s=step/240, phase_at_capture=trace[i]['phase'],
            measurement_phase=None, goal_frame_at_capture=None, targets=[], wrist_goal_distance_m=None,
            wrist_G_m=gr.inv().apply(wrist-gp).tolist(), left_contact_pair_count=None, left_contact_body_origins_W_m={})
        if step in observations:
            obs, origin = observations[step]; markers, wrist_error = target_markers(obs)
            row.update(measurement_phase=origin, wrist_goal_distance_m=wrist_error/1000)
            if step in by_step: row['goal_frame_at_capture'] = int(by_step[step]['source_frame_before'][0])
            hand = np.asarray(obs)[FRET_V2_BLOCK_SLICES['O_hand_geometry']]
            for j, finger in enumerate(FINGERS):
                actual_tip = pose(bodies['LH:'+finger+'_top'])[0]
                tip_errors.append(float(np.linalg.norm(gr.inv().apply(actual_tip-gp)-hand[30+6*j:33+6*j])))
            for marker in markers:
                row['targets'].append(dict(finger=marker['finger'], tip_marker_W_m=(gp+gr.apply(marker['tip_G_m'])).tolist(),
                    target_W_m=(gp+gr.apply(marker['target_G_m'])).tolist(), tip_marker_distance_m=marker['marker_distance_mm']/1000,
                    source_signed_press_depth_m=marker['signed_press_depth_mm']/1000))
        else: row['measurement_phase'] = 'preparation: target not recorded'
        if step in by_step:
            contacts = actual_guitar_contacts(by_step[step]['native_contacts'])
            left = [c for c in contacts if any(n.startswith('human/LH:') or n == 'human/L_Wrist' for n in (c['body0_name'], c['body1_name']))]
            human = sorted({n[6:] for c in left for n in (c['body0_name'], c['body1_name']) if n.startswith('human/')})
            row.update(left_contact_pair_count=len(left), native_actual_guitar_contacts=contacts,
                left_contact_body_origins_W_m={n: pose(bodies[n])[0].tolist() for n in human})
        row['raw_image_sha256'] = frame['image_sha256']; row['image_sha256'] = {}; row['cameras'] = cameras
        for name in cameras:
            raw = data/'images/frames'/name/f'{i:05d}.png'; assert sha(raw) == frame['image_sha256'][str(raw)]
            output = out/'frames'/name/raw.name
            annotate(raw, output, row, np.asarray(cameras[name]['view_matrix']), np.asarray(cameras[name]['projection_matrix']))
            row['image_sha256'][str(output)] = sha(output)
        rows.append(row)
    assert max(tip_errors) < 1e-6
    save(out/'capture.json', dict(renderer='saved Isaac Gym native frames + unoccluded explanatory guides', fps=30, frames=rows,
        scope='existing complete run, no new physics; pre-integration/terminal saved goals; preparation targets and final contact not measured; no depth test'))
    recorder = object.__new__(GymTrialRecording); recorder.out = out; recorder.frames = rows; recorder.fps = 30; recorder.views = ('whole_body', 'hands')
    videos = recorder.encode(); selected = []
    for time in (0, 2, 5, 8, 10, rows[-1]['time_s']):
        i = min(range(len(rows)), key=lambda j: abs(rows[j]['time_s']-time)); selected.append(dict(frame_index=i, **rows[i]))
    with (out/'metrics.csv').open('w') as f:
        fields = ['physics_step', 'time_s', 'phase', 'position_excess_mm', 'rotation_deg', 'neck_elevation_deg', 'right_cm', 'forward_cm', 'up_cm', 'wrist_vector_mm', 'left_contact_pairs']
        writer = csv.writer(f); writer.writerow(fields)
        for r in rows: writer.writerow([r['physics_step'], r['time_s'], r['phase_at_capture'], r['user_position_box_distance_m']*1000,
            r['rotation_change_deg'], r['neck_elevation_deg'], *[v*100 for v in r['body_center_pelvis_RFU_m']],
            None if r['wrist_goal_distance_m'] is None else r['wrist_goal_distance_m']*1000, r['left_contact_pair_count']])
    t = [r['time_s'] for r in rows]; fig, axes = plt.subplots(3, 1, figsize=(11, 9), sharex=True, constrained_layout=True)
    for j, label in enumerate(('Right', 'Forward', 'Up')): axes[0].plot(t, [r['body_center_pelvis_RFU_m'][j]*100 for r in rows], label=label)
    axes[0].set_ylabel('Body-center RFU (cm)'); axes[0].legend(ncol=3); axes[0].set_title('Saved Isaac Gym Fret episode / strap OFF / no new physics')
    axes[1].plot(t, [r['rotation_change_deg'] for r in rows], label='Rotation from t0'); axes[1].plot(t, [r['neck_elevation_deg'] for r in rows], label='Neck elevation')
    axes[1].set_ylabel('deg'); axes[1].legend()
    axes[2].plot(t, [np.nan if r['wrist_goal_distance_m'] is None else r['wrist_goal_distance_m']*1000 for r in rows], label='Saved wrist-target vector', color='purple')
    for finger in FINGERS:
        pts = [(r['time_s'], m['tip_marker_distance_m']*1000) for r in rows for m in r['targets'] if m['finger'] == finger]
        if pts: axes[2].scatter(*np.asarray(pts).T, s=8, label=finger)
    axes[2].set_ylabel('Marker/target error (mm)'); axes[2].legend(ncol=3); axes[2].set_xlabel('Physical time (s)')
    for ax in axes: ax.axvline(2, color='black', ls='--', lw=1); ax.grid(alpha=.2)
    fig.savefig(out/'timeline.png', dpi=150); plt.close(fig)
    play = [r for r in rows if r['wrist_goal_distance_m'] is not None]
    checks = dict(source_episode_completed=report['completed_recording'], frame_trace_steps_exact=True, input_hashes_unchanged=all(sha(p) == h for p, h in inputs.items()),
        source_camera_sha_equal=camera_source_equal, camera_matrix_static=camera_constant, common_prefix_rgba_pixels_exact=bool(prefix_pixels),
        observation_tip_alignment_below_1um=max(tip_errors) < 1e-6, full_t0_to_original_done=rows[0]['physics_step'] == 0 and rows[-1]['physics_step'] == report['physics_steps'],
        preparation_target_unmeasured=all(not r['targets'] and r['wrist_goal_distance_m'] is None for r in rows if r['time_s'] < 2),
        terminal_contacts_unmeasured=rows[-1]['left_contact_pair_count'] is None)
    summary = dict(checks=checks, selected_frames=selected, frame_count=len(rows), physics_duration_s=report['recorded_physics_duration_s'],
        new_physics_runs=0, learning_updates=0, saved_run=str(data), music_success=report['music_success'], source_stop_reason=report['stop_reason'],
        terminal_info_path=str(data/'terminal_info.json'), max_tip_alignment_error_m=max(tip_errors),
        user_position_outside_frames=sum(not r['user_position_inside'] for r in rows), max_rotation_change_deg=max(r['rotation_change_deg'] for r in rows),
        wrist_vector_mm_range=[min(r['wrist_goal_distance_m'] for r in play)*1000, max(r['wrist_goal_distance_m'] for r in play)*1000], videos=videos,
        input_sha256=inputs, camera_prefix_verified_frames=len(camera_rows), limits='No new run or live full success. No rotation-set membership/depth/contact-point/penetration certification. Different goals are different tasks; prep goals/final contacts unavailable.')
    save(out/'summary.json', summary)
    print(json.dumps(dict(checks=checks, frames=len(rows), wrist_mm=summary['wrist_vector_mm_range'], position_outside=summary['user_position_outside_frames']), indent=2))
    if not all(checks.values()): raise AssertionError(checks)


if __name__ == '__main__': main()
