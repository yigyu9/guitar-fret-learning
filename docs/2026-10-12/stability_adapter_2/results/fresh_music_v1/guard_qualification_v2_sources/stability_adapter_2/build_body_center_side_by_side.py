"""Same saved native frame, separate body-center boxes in adjacent panels."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .render_envelope_native import EDGES, FONT
from .strap_trial_recording import project
from .validate_team_pose_envelope import ROOT, RESULTS, read, save, sha


def panel(raw, depth, camera, box, center, color, title, bounds, actual, roi):
    im = Image.open(raw).convert('RGB'); w, h = im.size; draw = ImageDraw.Draw(im)
    view, proj = np.asarray(camera['view_matrix']), np.asarray(camera['projection_matrix'])
    px, _, valid = project(np.vstack((box, center)), view, proj, w, h)
    assert valid.all() and np.all(px >= roi[:2]) and np.all(px < roi[2:]), 'range outside comparison crop'
    for i, j in EDGES:
        ends = px[[i, j]]; count = max(2, int(np.linalg.norm(ends[1]-ends[0])*2)+1)
        pixels, z, valid = project(box[i]+(box[j]-box[i])*np.linspace(0, 1, count)[:, None], view, proj, w, h)
        for k in range(count-1):
            if not (valid[k] and valid[k+1]): continue
            xy = pixels[k:k+2].astype(int)
            visible = np.all(z[k:k+2] >= depth[xy[:, 1], xy[:, 0]]-.002)
            if visible: draw.line([tuple(pixels[k]), tuple(pixels[k+1])], fill=color, width=4)
            elif k//12 % 2 == 0: draw.line([tuple(pixels[k]), tuple(pixels[k+1])], fill=tuple(int(c*.55) for c in color), width=2)
    x, y = px[-1]; draw.ellipse((x-6, y-6, x+6, y+6), fill=(255, 100, 200), outline='black')
    crop = im.crop(tuple(roi)); height = round(crop.height*640/crop.width)
    canvas = Image.new('RGB', (640, height+210), '#131a24'); canvas.paste(crop.resize((640, height), Image.Resampling.LANCZOS), (0, 55))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 10), title, font=ImageFont.truetype(str(FONT), 28), fill=color)
    for i, name in enumerate(('오른쪽', '앞', '위')):
        lo, hi = bounds[0][i], bounds[1][i]
        text = f'{name}: {lo:+.2f}~{hi:+.2f} cm  (폭 {hi-lo:.2f} cm)'
        draw.text((16, height+65+i*29), text, font=ImageFont.truetype(str(FONT), 22), fill=color)
    text = '분홍 실제 중심: ('+', '.join(f'{v:.2f}' for v in actual)+') cm'
    draw.text((16, height+155), text, font=ImageFont.truetype(str(FONT), 20), fill=(255, 100, 200))
    return canvas


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--out', type=Path, required=True); args = parser.parse_args()
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=False)
    native = RESULTS/'envelope_native_comparison_v1/native/current_control'
    prior = RESULTS/'body_center_view_v1'; paths = [Path(__file__), FONT, prior/'analysis/summary.json', prior/'artifact_inventory.json',
        ROOT/'stability_adapter_2/BODY_CENTER_SIDE_BY_SIDE_PLAN.md']
    paths += [ROOT/'stability_adapter_2'/n for n in ('render_envelope_native.py', 'strap_trial_recording.py', 'gym_trial_recording.py', 'validate_team_pose_envelope.py')]
    paths += [native/n for n in ('geometry.json', 'report.json', 'front_raw.png', 'side_raw.png', 'front_depth.npy', 'side_depth.npy')]
    hashes = {str(f.resolve()): sha(f) for f in paths}; save(out/'attempt.json', {'input_sha256': hashes})
    summary = read(prior/'analysis/summary.json'); case = summary['cases']['current_control']; g = read(native/'geometry.json'); report = read(native/'report.json')
    assert all(sha(f) == digest for f, digest in summary['input_sha256'].items())
    user = np.asarray(case['user_center_corners_W_m']); team = np.asarray(g['team_body_box_W_m']); center = np.asarray(case['actual_center_W_m'])
    np.testing.assert_allclose(user, g['user_body_box_W_m_fixed_rotation'], atol=1e-12)
    np.testing.assert_allclose(center, g['actual_body_center_W_m'], atol=1e-12)
    bounds = [case['user_min_pelvis_RFU_cm'], case['user_max_pelvis_RFU_cm']]; actual = case['actual_center_pelvis_RFU_cm']
    views = {}
    for view, roi in [('front', (400, 115, 910, 710)), ('side', (400, 115, 830, 710))]:
        raw = native/(view+'_raw.png'); assert sha(raw) == report['cameras'][view]['raw_sha256']
        depth = np.load(native/(view+'_depth.npy')); camera = report['cameras'][view]
        left = panel(raw, depth, camera, user, center, (75, 190, 255), '사용자 범위', bounds, actual, roi)
        right = panel(raw, depth, camera, team, center, (255, 210, 45), '팀원 후보 범위', [[17, 24.5, 8], [23, 34.5, 10]], actual, roi)
        assert left.size == right.size
        canvas = Image.new('RGB', (1296, left.height+80), '#202734'); canvas.paste(left, (0, 45)); canvas.paste(right, (656, 45)); draw = ImageDraw.Draw(canvas)
        draw.text((16, 8), '같은 수평 기타 · 같은 카메라 · 골반 기준 바디 중심 비교', font=ImageFont.truetype(str(FONT), 25), fill='white')
        draw.text((16, canvas.height-30), '저장 Isaac Gym t=0 후처리 | 왼쪽 범위는 이 회전에서 유효 | 점선: 가려진 선 | 접촉 시험 아님', font=ImageFont.truetype(str(FONT), 19), fill='#d0d5df')
        file = out/(view+'.png'); canvas.save(file); views[view] = {'roi_native_pixels': list(roi), 'same_camera_and_raw_frame': True, 'output_sha256': sha(file), 'size': list(canvas.size)}
    assert all(sha(f) == digest for f, digest in hashes.items())
    save(out/'report.json', {'input_sha256': hashes, 'views': views, 'new_native_initializations': 0, 'physics_steps': 0, 'learning_updates': 0,
        'checks': {'same_scene_camera_crop_scale': True, 'saved_center_and_user_corners_match': True, 'prior_input_hashes_match': True, 'inputs_unchanged': True},
        'scope': 'Two position boxes at the same saved horizontal guitar q; display reference point, not mass CoM or safe-volume certification.'})
    print('PASS: front/side adjacent panels with identical scene and separate ranges')


if __name__ == '__main__': main()
