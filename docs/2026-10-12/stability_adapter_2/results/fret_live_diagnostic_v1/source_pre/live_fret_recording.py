"""Read-only native recording of current-guitar Fret geometry and raw contacts."""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .gym_trial_recording import GymTrialRecording, sha
from .strap_trial_recording import project
from .live_fret_geometry import pose, position_geometry, assigned_targets, actual_guitar_contacts, EDGES, FINGERS

FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')


def tensors(owners):
    import torch
    return {(i, name): value.clone() for i, owner in enumerate(owners) for name, value in vars(owner).items()
            if isinstance(value, torch.Tensor)}


def unchanged_tensors(owners, saved):
    import torch
    current = {(i, name): value for i, owner in enumerate(owners) for name, value in vars(owner).items()
               if isinstance(value, torch.Tensor)}
    return current.keys() == saved.keys() and all(torch.equal(value, current[key]) for key, value in saved.items())


def annotate(raw_path, destination, row, view, projection, depth):
    im = Image.open(raw_path).convert('RGB'); w, h = im.size; draw = ImageDraw.Draw(im)
    stats = dict(visible_segments=0, hidden_segments=0, outside_segments=0)
    def line(a, b, color, width=3):
        a, b = np.asarray(a), np.asarray(b)
        px, _, valid = project(np.array([a, b]), view, projection, w, h)
        if not valid.all(): stats['outside_segments'] += 1; return
        count = min(4096, max(2, int(np.linalg.norm(px[1]-px[0])*2)+1))
        points = a+(b-a)*np.linspace(0, 1, count)[:, None]
        px, z, valid = project(points, view, projection, w, h)
        for i in range(count-1):
            if not (valid[i] and valid[i+1]): continue
            xy = px[i:i+2].astype(int)
            visible = bool(np.all(z[i:i+2] >= depth[xy[:, 1], xy[:, 0]]-.002))
            if visible:
                draw.line([tuple(px[i]), tuple(px[i+1])], fill=color, width=width); stats['visible_segments'] += 1
            elif i//12 % 2 == 0:
                draw.line([tuple(px[i]), tuple(px[i+1])], fill=tuple(int(c*.55) for c in color), width=1); stats['hidden_segments'] += 1
    def marker(point, color, radius=5):
        px, z, valid = project(np.asarray([point]), view, projection, w, h)
        if valid[0]:
            x, y = px[0]; scene = depth[int(y), int(x)]
            if z[0] < scene-.002: color = tuple(int(c*.55) for c in color)
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
    text(12, 'Isaac Gym · 현재 기타 기준 Fret')
    text(45, f"t={row['time_s']:.3f}s  step={row['physics_step']}  {row['phase_at_capture']}")
    c = np.asarray(row['body_center_pelvis_RFU_m'])*100
    text(80, '바디 중심 (골반 오른쪽/앞/위 cm)')
    text(112, ' / '.join(f'{v:+.2f}' for v in c), (255, 100, 200))
    text(146, f"사용자 위치box: {'안' if row['user_position_inside'] else '밖'} / 이탈 {row['user_position_box_distance_m']*1000:.2f} mm")
    text(178, f"초기 대비 회전: {row['rotation_change_deg']:.2f}°")
    text(210, f"넥 고도: {row['neck_elevation_deg']:+.2f}°")
    text(242, f"앞면-골반 전방: {row['front_to_pelvis_forward_deg']:.2f}°")
    text(274, '전체 회전 허용집합 판정: 미적용', '#aeb6c3', small)
    text(304, f"goal frame: {row['goal_frame_before_evaluation']}")
    if row['wrist_goal_distance_m'] is not None: text(336, f"손목→현재 목표: {row['wrist_goal_distance_m']*1000:.1f} mm")
    else: text(336, '손목 목표: 미초기화/미제공')
    text(370, '활성 弦 / 품 / 손가락 : 손끝거리 mm', size=small)
    for i, target in enumerate(row['targets']):
        text(398+i*24, f"{target['string_index_zero_based']+1} / {target['fret']} / {target['finger']}: {target['tip_marker_distance_m']*1000:.1f}", (255, 175, 50), small)
    text(552, f"실제 기타–왼손 접촉 pair: {row['left_contact_pair_count']}", (80, 255, 140))
    text(582, '초록: 접촉 body 원점 (표면 접촉점 아님)', (80, 255, 140), small)
    text(610, '파랑: 현재 회전의 조건부 위치 범위', (75, 190, 255), small)
    text(637, '주황: 손끝–목표 / 흰 원: 현재 목표', (255, 175, 50), small)
    text(664, '점선/어두운 원: 가려짐 · 스트랩 OFF', '#aeb6c3', small)
    text(690, '표시용 기준점 ≠ 질량중심 / 제어 변경 없음', '#aeb6c3', small)
    canvas.save(destination); return stats


class LiveFretRecording:
    def __init__(self, env, out):
        from .run_joint_hold import native_state
        from .native_contacts import body_names
        self.env = env; self.out = Path(out); self.raw = GymTrialRecording(env, self.out/'raw')
        self.views = self.raw.views; self.fps = self.raw.fps; self.interval = self.raw.interval; self.frames = []
        initial = native_state(env)
        self.initial_rotation = pose(initial['guitar_body_states'][0])[1]
        self.initial_chest_z = initial['human_body_states'][env.human_bodies.index('Chest')]['pose']['p']['z']
        self.contact_names = body_names(env.gym, env.env)
        for name in self.views: (self.out/'frames'/name).mkdir(parents=True, exist_ok=False)

    def capture(self):
        import torch
        from .environment import gymapi
        from .run_joint_hold import native_state
        from .native_contacts import read_contacts
        from .strike_native_view import refresh_native
        from .run_fret_fingers_arm_hold import json_plain
        env = self.env; before = native_state(env); submitted = env.target.copy()
        self.raw.capture()
        bodies = dict(zip(env.human_bodies, before['human_body_states']))
        gp, gr = pose(before['guitar_body_states'][0]); wrist = pose(bodies['L_Wrist'])[0]
        row = position_geometry(before['guitar_body_states'][0], bodies['Pelvis'], self.initial_rotation, self.initial_chest_z)
        row.update(physics_step=env.steps, time_s=env.steps/env.config['physics_hz'],
            phase_at_capture='PREPARE' if env.steps < 480 else 'HANDOFF/PLAY',
            measurement_phase='capture before source evaluation; final extra capture may be after terminal evaluation',
            goal_frame_before_evaluation=None, targets=[], wrist_goal_distance_m=None,
            wrist_G_m=gr.inv().apply(wrist-gp).tolist(), source_readonly=True, goal=None, source_measurement=None)
        view = getattr(env, 'live_diagnostic_view', None)
        if view is not None:
            refresh_native(view, env)
            owners = (view, view.goals, view.reward_fn); snapshot = tensors(owners)
            with torch.no_grad():
                goal = view.goals.current(); measurement = view.reward_fn.observe_fret_v2_state(goal)
            row['source_readonly'] = unchanged_tensors(owners, snapshot)
            row['goal_frame_before_evaluation'] = int(view.goals.frame_idx[0])
            row['goal'] = json_plain({k: goal[k] for k in ('fret', 'finger', 'barre', 'wrist', 'wrist_radius') if k in goal})
            row['source_measurement'] = json_plain(measurement)
            tips = [pose(bodies['LH:'+finger+'_top'])[0] for finger in FINGERS]
            row['targets'] = assigned_targets(row['goal'], row['source_measurement'], tips)
            if getattr(view.goals, 'has_wrist_target', False):
                target = gp+gr.apply(np.asarray(row['goal']['wrist'][0]))
                row.update(wrist_target_W_m=target.tolist(), wrist_goal_distance_m=float(np.linalg.norm(target-wrist)))
        contacts = read_contacts(env.gym, env.env, self.contact_names)
        actual = actual_guitar_contacts(contacts)
        left = [r for r in actual if any(n.startswith('human/LH:') or n == 'human/L_Wrist' for n in (r['body0_name'], r['body1_name']))]
        left_names = sorted({n[6:] for r in left for n in (r['body0_name'], r['body1_name']) if n.startswith('human/')})
        row.update(native_contacts=contacts, actual_guitar_contacts=actual, left_contact_pair_count=len(left),
            left_contact_body_origins_W_m={name: pose(bodies[name])[0].tolist() for name in left_names})
        cameras = {}; images = {}
        for name in self.views:
            camera = env.cameras[name]
            view_matrix = np.asarray(env.gym.get_camera_view_matrix(env.sim, env.env, camera))
            projection = np.asarray(env.gym.get_camera_proj_matrix(env.sim, env.env, camera))
            depth = np.asarray(env.gym.get_camera_image(env.sim, env.env, camera, gymapi.IMAGE_DEPTH)).reshape(720, 1280)
            raw = self.out/'raw/frames'/name/('%05d.png'%len(self.frames)); output = self.out/'frames'/name/raw.name
            stats = annotate(raw, output, row, view_matrix, projection, depth)
            images[str(output)] = sha(output)
            cameras[name] = dict(view_matrix=view_matrix.tolist(), projection_matrix=projection.tolist(), overlay_stats=stats)
        row.update(render_preserves_states=native_state(env) == before, submitted_targets_unchanged=bool(np.array_equal(env.target, submitted)),
            cameras=cameras, image_sha256=images, raw_image_sha256=self.raw.frames[-1]['image_sha256'])
        self.frames.append(row)
        temp = self.out/'capture.tmp'
        temp.write_text(json.dumps(dict(renderer='Isaac Gym native camera + read-only geometry overlay', fps=self.fps,
            font_path=str(FONT), font_sha256=sha(FONT), frames=self.frames), indent=2, allow_nan=False)+'\n')
        temp.replace(self.out/'capture.json')
        if not all(row[k] for k in ('source_readonly', 'render_preserves_states', 'submitted_targets_unchanged')):
            raise AssertionError('diagnostic mutated source/native/control state')

    def encode(self):
        self.raw.encode()
        return GymTrialRecording.encode(self)
