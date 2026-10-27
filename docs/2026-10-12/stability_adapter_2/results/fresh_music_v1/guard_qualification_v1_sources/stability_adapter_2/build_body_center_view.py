"""Body-center-only display and RFU tables from preserved native t0 frames."""
import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as R
from PIL import Image, ImageDraw, ImageFont

from .body_center_coordinates import body_center_world, actor_root_world, pelvis_rfu
from .render_envelope_native import CASES, LABELS, EDGES, FONT
from .strap_trial_recording import project
from .validate_team_pose_envelope import ROOT, RESULTS, BODY_CENTER_G, read, save, sha


def verify_transforms():
    np.testing.assert_allclose(body_center_world([0, 0, 0], [0, 0, 0, 1]), [0, -.4, -.0217])
    np.testing.assert_allclose(body_center_world([0, 0, 0], R.from_euler('z', 90, degrees=True).as_quat()), [.4, 0, -.0217], atol=1e-15)
    random = np.random.default_rng(42)
    for rotation in R.random(256, random_state=random):
        q = rotation.as_quat(); p = random.normal(size=(8, 3))
        np.testing.assert_allclose(actor_root_world(body_center_world(p, q), q), p, atol=1e-15)
        np.testing.assert_allclose(body_center_world(p, q), body_center_world(p, -q), atol=1e-15)
    return {'analytic_identity_and_z90': True, 'random_rotations': 256, 'roundtrip_and_quaternion_sign': True}


def overlay(raw, destination, boxes, center, neck, camera, depth, title, rfu, bounds):
    im = Image.open(raw).convert('RGB'); w, h = im.size; draw = ImageDraw.Draw(im)
    view = np.asarray(camera['view_matrix']); proj = np.asarray(camera['projection_matrix'])
    def line(a, b, color, width):
        ends, _, _ = project(np.array([a, b]), view, proj, w, h)
        count = min(4096, max(2, int(np.linalg.norm(ends[1]-ends[0])*2)+1))
        pixels, z, valid = project(a+(b-a)*np.linspace(0, 1, count)[:, None], view, proj, w, h)
        for i in range(count-1):
            if not (valid[i] and valid[i+1]): continue
            xy = pixels[i:i+2].astype(int)
            visible = np.all(z[i:i+2] >= depth[xy[:, 1], xy[:, 0]]-.002)
            if visible: draw.line([tuple(pixels[i]), tuple(pixels[i+1])], fill=color, width=width)
            elif i//12 % 2 == 0: draw.line([tuple(pixels[i]), tuple(pixels[i+1])], fill=tuple(int(c*.55) for c in color), width=2)
    for box, color in zip(boxes, ((75, 190, 255), (255, 210, 45))):
        for i, j in EDGES: line(box[i], box[j], color, 4)
    line(center, center+neck*.15, (75, 255, 130), 4)
    pixels, _, valid = project(np.array([center]), view, proj, w, h)
    assert valid[0], 'body center outside camera frame'
    x, y = pixels[0]; draw.ellipse((x-6, y-6, x+6, y+6), fill=(255, 100, 200), outline='black')
    draw.text((x+10, y+7), '바디 중심', font=ImageFont.truetype(str(FONT), 20), fill=(255, 100, 200), stroke_width=2, stroke_fill='black')
    canvas = Image.new('RGB', (w, h+190), '#131a24'); canvas.paste(im, (0, 0)); draw = ImageDraw.Draw(canvas)
    actual = ' / '.join(f'{name} {v:+.2f}' for name, v in zip(('오른쪽', '앞', '위'), rfu))
    ranges = ' / '.join(f'{name} {lo:+.2f}~{hi:+.2f}' for name, lo, hi in zip(('오른쪽', '앞', '위'), bounds[0], bounds[1]))
    texts = [(title+' | 골반 기준 바디 중심 (cm)', 'white'),
             ('분홍: 실제 중심 | '+actual, (255, 100, 200)),
             ('하늘색 사용자 범위: '+ranges, (75, 190, 255)),
             ('노랑 팀원 후보: 오른쪽 +17~+23 / 앞 +24.5~+34.5 / 위 +8~+10', (255, 210, 45)),
             ('저장된 Isaac Gym t=0 후처리 | 위치범위는 이 회전에서만 유효 | 초록: 넥 방향 | 접촉 시험 아님', '#d0d5df')]
    for i, (text, color) in enumerate(texts):
        font = ImageFont.truetype(str(FONT), 21 if i < 4 else 18)
        assert draw.textbbox((0, 0), text, font=font)[2] < w-32, 'caption too wide'
        draw.text((16, h+8+i*35), text, fill=color, font=font)
    canvas.save(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True); args = parser.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    previous = RESULTS/'envelope_native_comparison_v1'
    paths = [Path(__file__), ROOT/'stability_adapter_2/body_center_coordinates.py',
             ROOT/'stability_adapter_2/BODY_CENTER_VIEW_PLAN.md', FONT,
             previous/'artifact_inventory.json']
    paths += [ROOT/'stability_adapter_2'/n for n in ('render_envelope_native.py', 'strap_trial_recording.py', 'gym_trial_recording.py', 'validate_team_pose_envelope.py')]
    paths += [previous/'native'/c/n for c in CASES for n in ('geometry.json', 'report.json', 'front_raw.png', 'side_raw.png', 'front_depth.npy', 'side_depth.npy')]
    paths += [RESULTS/'team_pose_envelope_validation_v1/native'/c/'initial_values.json' for c in CASES]
    hashes = {str(p.resolve()): sha(p) for p in paths}
    save(out/'attempt.json', {'input_sha256': hashes, 'new_native_initializations': 0, 'physics_steps': 0})
    checks = verify_transforms(); rows = []; cases = {}
    inventory = read(previous/'artifact_inventory.json')['sha256']
    for c, title in zip(CASES, LABELS):
        source = previous/'native'/c; geometry = read(source/'geometry.json'); report = read(source/'report.json')
        assert all(report['checks'].values()) and report['physics_steps'] == 0
        assert all(sha(source/n) == inventory[str(source/n)] for n in ('geometry.json', 'report.json', 'front_raw.png', 'side_raw.png', 'front_depth.npy', 'side_depth.npy'))
        state = geometry['initial_state']
        reference = read(RESULTS/'team_pose_envelope_validation_v1/native'/c/'initial_values.json')
        assert state['human_body_states'] == reference['actual_initial_state']['human_body_states']
        pelvis = state['human_body_states'][reference['body_names'].index('Pelvis')]['pose']
        pp = [pelvis['p'][k] for k in 'xyz']; pq = [pelvis['r'][k] for k in 'xyzw']
        pose = state['guitar_body_states'][0]['pose']; gp = [pose['p'][k] for k in 'xyz']; q = [pose['r'][k] for k in 'xyzw']
        center = body_center_world(gp, q); box = body_center_world(geometry['user_root_box_W_m'], q)
        np.testing.assert_allclose(center, geometry['actual_body_center_W_m'], atol=1e-12)
        np.testing.assert_allclose(box, geometry['user_body_box_W_m_fixed_rotation'], atol=1e-12)
        np.testing.assert_allclose(actor_root_world(box, q), geometry['user_root_box_W_m'], atol=1e-12)
        rfu = pelvis_rfu(center, pp, pq)*100; rfu_box = pelvis_rfu(box, pp, pq)*100
        bounds = [rfu_box.min(axis=0), rfu_box.max(axis=0)]
        team = np.asarray(geometry['team_body_box_W_m']); team_rfu = pelvis_rfu(team, pp, pq)*100
        np.testing.assert_allclose(team_rfu.min(axis=0), [17, 24.5, 8], atol=1e-12)
        np.testing.assert_allclose(team_rfu.max(axis=0), [23, 34.5, 10], atol=1e-12)
        neck = np.asarray(geometry['neck_direction_W'])
        case_out = out/c; case_out.mkdir()
        for view in ('front', 'side'):
            raw = source/(view+'_raw.png'); assert sha(raw) == report['cameras'][view]['raw_sha256']
            overlay(raw, case_out/(view+'.png'), [box, team], center, neck, report['cameras'][view], np.load(source/(view+'_depth.npy')), title, rfu, bounds)
        row = {'case': c, 'neck_elevation_deg': float(np.degrees(np.arcsin(neck[2])))}
        for i, name in enumerate(('right', 'forward', 'up')):
            row.update({f'actual_{name}_cm': float(rfu[i]), f'user_{name}_min_cm': float(bounds[0][i]), f'user_{name}_max_cm': float(bounds[1][i]), f'user_{name}_width_cm': float(bounds[1][i]-bounds[0][i])})
        rows.append(row)
        cases[c] = {'actual_center_W_m': center.tolist(), 'actual_center_pelvis_RFU_cm': rfu.tolist(), 'user_center_corners_W_m': box.tolist(), 'user_center_corners_pelvis_RFU_cm': rfu_box.tolist(), 'user_min_pelvis_RFU_cm': bounds[0].tolist(), 'user_max_pelvis_RFU_cm': bounds[1].tolist(), 'rotation_membership_from_previous_diagnostic': geometry['rotation_membership']}
    with (out/'body_center_ranges.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    checks.update(saved_native_center_and_corners_match=True, inputs_unchanged=all(sha(p) == h for p, h in hashes.items()))
    assert all(v for k, v in checks.items() if k != 'random_rotations')
    save(out/'summary.json', {'checks': checks, 'body_center_local_m': BODY_CENTER_G.tolist(), 'new_native_initializations': 0, 'physics_steps': 0, 'learning_updates': 0, 'rows': rows, 'cases': cases, 'input_sha256': hashes, 'scope': 'Display reference point, not mass CoM. Position boxes at three fixed native rotations; existing controller is unchanged; new helper not wired to runner.'})
    print('PASS: body-center RFU table and six saved-native overlays; no new physics')


if __name__ == '__main__': main()
