"""Draw a world-space guitar-root position region over a fixed native Isaac Gym pose."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

from . import interactive_guitar_pose_static as app
from .guitar_pose_static import Editor
from .run_physx_contacts import native_state

ROOT = Path(__file__).resolve().parents[1]
PLAN = Path(__file__).with_name('POSITION_REGION_BOX_PLAN.md')
PHASE_NAME = 'position_region_box_v1'
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
WIDTH, HEIGHT = 1280, 720
REFERENCE_POSITION = [-.325, 0., .80]
REFERENCE_EULER_XYZ = [67.5, 75., 157.5]
POSITION_LOW = [-.50, -.15, .65]
POSITION_HIGH_XY = [-.15, .15]
CAMERAS = {
    'whole_body': {'camera_id': 'whole_body'},
    'isometric': {'position_W_m': [1.05, 1.00, 1.32], 'target_W_m': [-.25, -.02, .84]},
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def project(points, view, projection):
    points = app.np.asarray(points, dtype=float)
    camera = app.np.column_stack((points, app.np.ones(len(points)))) @ view
    clip = camera @ projection
    ndc = clip[:, :2] / clip[:, 3, None]
    pixels = app.np.column_stack(((ndc[:, 0]+1)*WIDTH/2, (1-ndc[:, 1])*HEIGHT/2))
    valid = ((camera[:, 2] < -.001) & app.np.isfinite(pixels).all(axis=1)
             & (pixels[:, 0] >= 0) & (pixels[:, 0] < WIDTH)
             & (pixels[:, 1] >= 0) & (pixels[:, 1] < HEIGHT))
    return pixels, camera[:, 2], valid


def draw_segment(draw, a, b, view, projection, depth, color, hidden_color,
                 width=4, tolerance=.002):
    endpoints, _, _ = project(app.np.asarray([a, b]), view, projection)
    count = min(4096, max(3, int(app.np.ceil(app.np.linalg.norm(endpoints[1]-endpoints[0])*2))+1))
    samples = app.np.asarray(a)+(app.np.asarray(b)-app.np.asarray(a))*app.np.linspace(0, 1, count)[:, None]
    pixels, camera_z, valid = project(samples, view, projection)
    visible = app.np.zeros(count, dtype=bool)
    indices = app.np.flatnonzero(valid)
    if len(indices):
        xy = pixels[indices].astype(int)
        scene_depth = depth[xy[:, 1], xy[:, 0]]
        visible[indices] = camera_z[indices] >= scene_depth-tolerance
    for i in range(count-1):
        if not (valid[i] and valid[i+1]):
            continue
        p0, p1 = tuple(pixels[i]), tuple(pixels[i+1])
        if visible[i] and visible[i+1]:
            draw.line((p0, p1), fill=(5, 25, 30, 235), width=width+3)
            draw.line((p0, p1), fill=color, width=width)
        elif i % 5 < 2:
            draw.line((p0, p1), fill=hidden_color, width=max(1, width-1))


def box_corners(z_max):
    return {(ix, iy, iz): [-.50 if ix == 0 else -.15,
                            -.15 if iy == 0 else .15,
                            .65 if iz == 0 else z_max]
            for ix in (0, 1) for iy in (0, 1) for iz in (0, 1)}


def box_edges(corners):
    edges = []
    for key, point in corners.items():
        for axis in range(3):
            other = list(key)
            other[axis] = 1-other[axis]
            other = tuple(other)
            if key[axis] == 0:
                edges.append((point, corners[other], axis, key[2] == 1))
    return edges


def annotate(raw, out, camera_info, box_z_max, guitar_root, chest_root, depth):
    image = Image.open(raw).convert('RGBA')
    overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    view = app.np.asarray(camera_info['view_matrix'])
    projection = app.np.asarray(camera_info['projection_matrix'])
    corners = box_corners(box_z_max)
    for a, b, axis, top in box_edges(corners):
        if top:
            color, hidden = (255, 164, 35, 245), (255, 180, 70, 105)
        elif axis == 2:
            color, hidden = (45, 220, 250, 240), (130, 225, 240, 110)
        else:
            color, hidden = (20, 230, 205, 245), (125, 220, 205, 105)
        draw_segment(draw, a, b, view, projection, depth, color, hidden)

    markers = [('guitar root', guitar_root, (255, 235, 45, 255)),
               ('Chest origin', chest_root, (255, 65, 190, 255))]
    marker_pixels = {}
    for label, point, color in markers:
        pixels, _, valid = project([point], view, projection)
        if not valid[0]:
            continue
        x, y = map(int, pixels[0])
        marker_pixels[label] = [x, y]
        draw.ellipse((x-10, y-10, x+10, y+10), fill=(0, 0, 0, 230), outline=(0, 0, 0, 255), width=3)
        draw.ellipse((x-6, y-6, x+6, y+6), fill=color, outline=(255, 255, 255, 255), width=2)
        draw.line((x-14, y, x+14, y), fill=(0, 0, 0, 230), width=2)
        draw.line((x, y-14, x, y+14), fill=(0, 0, 0, 230), width=2)

    font = ImageFont.truetype(str(FONT), 18)
    small = ImageFont.truetype(str(FONT), 16)
    draw.rounded_rectangle((16, 14, 790, 108), radius=9, fill=(14, 22, 32, 224),
                           outline=(205, 220, 230, 220), width=1)
    draw.text((32, 23), '기타 root 허용 위치 영역 (월드 좌표)', font=font, fill=(255, 255, 255, 255))
    draw.text((32, 50), '박스: X -0.50~-0.15m | Y -0.15~0.15m | Z 0.65~%.3fm (Chest 높이)' % box_z_max,
              font=small, fill=(100, 255, 230, 255))
    draw.text((32, 77), '노랑 ● 기타 root 기준점 (-0.325, 0.000, 0.800)m   분홍 ● Chest 원점',
              font=small, fill=(255, 245, 205, 255))
    Image.alpha_composite(image, overlay).convert('RGB').save(out, format='PNG')
    return {'marker_pixel': marker_pixels, 'box_vertices_W_m': list(corners.values()),
            'box_edges': 12, 'depth_test': True, 'source_image_sha256': sha(raw),
            'output_image_sha256': sha(out)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root', type=Path, default=ROOT/'docs/2026-10-12/stability_adapter_2/results')
    args = parser.parse_args()
    phase = args.out_root.resolve()/PHASE_NAME
    phase.mkdir(parents=True, exist_ok=False)
    native_dir, image_dir = phase/'native', phase/'images'
    native_dir.mkdir()
    image_dir.mkdir()
    inputs = [Path(__file__).resolve(), PLAN, Path(app.__file__).resolve(),
              Path(__file__).with_name('guitar_pose_static.py'),
              Path(__file__).with_name('interactive_guitar_pose_static.py'),
              Path(__file__).with_name('guitar_pose_edit.py'),
              Path(__file__).with_name('capture_isaac_gym_initial.py'),
              Path(__file__).with_name('run_physx_contacts.py'), app.BASELINE, FONT]
    input_hashes = {str(path.resolve()): sha(path) for path in inputs}
    save(phase/'attempt.json', {'reference_position_W_m': REFERENCE_POSITION,
        'reference_euler_xyz_world_deg': REFERENCE_EULER_XYZ,
        'position_region_W_m': {'x': [-.50, -.15], 'y': [-.15, .15], 'z_lower_m': .65},
        'upper_z_semantics': 'read from actual initial Chest rigid-body origin world z during scene initialization; approximate chest level, not surface/collision boundary',
        'position_reference_semantics': 'guitar actor root; box constrains this point, not the full guitar mesh',
        'physics_steps_requested': 0, 'strap_display': False,
        'input_sha256': input_hashes, 'camera_setup': CAMERAS})

    editor = Editor(native_dir/'scene', strap=False, viewer=False)
    try:
        editor.position = app.np.asarray(REFERENCE_POSITION, dtype=float)
        editor.quaternion = Rotation.from_euler('xyz', REFERENCE_EULER_XYZ, degrees=True).as_quat()
        editor.install_pose()
        initial = native_state(editor.env)
        app.save(phase/'initial_state.json', initial)
        if 'Chest' not in editor.env.human_bodies:
            raise AssertionError('Chest rigid body is missing from the native humanoid')
        chest_index = editor.env.human_bodies.index('Chest')
        chest_state = editor.env.bodies(editor.env.human)[chest_index]
        chest_root = app.vector(chest_state['pose']['p']).astype(float)
        chest_height = float(chest_root[2])
        if not .75 < chest_height < 1.10:
            raise AssertionError(f'unexpected Chest height: {chest_height}')
        if not .65 < REFERENCE_POSITION[2] < chest_height:
            raise AssertionError('reference point must lie inside vertical box extent')

        candidate = editor.save_candidate()
        camera_ids = {'whole_body': editor.env.cameras['whole_body']}
        props = app.gymapi.CameraProperties()
        props.width, props.height = WIDTH, HEIGHT
        iso = editor.env.gym.create_camera_sensor(editor.env.env, props)
        if iso < 0:
            raise RuntimeError('isometric camera creation failed')
        editor.env.gym.set_camera_location(iso, editor.env.env,
            app.gymapi.Vec3(*CAMERAS['isometric']['position_W_m']),
            app.gymapi.Vec3(*CAMERAS['isometric']['target_W_m']))
        camera_ids['isometric'] = iso
        before = native_state(editor.env)
        editor.env.gym.step_graphics(editor.env.sim)
        editor.env.gym.render_all_camera_sensors(editor.env.sim)
        output_records = {}
        for name, camera in camera_ids.items():
            if name == 'whole_body':
                raw = candidate/'images/frames/whole_body/00000.png'
            else:
                raw = native_dir/(name+'_raw.png')
                editor.env.gym.write_camera_image_to_file(editor.env.sim, editor.env.env,
                    camera, app.gymapi.IMAGE_COLOR, str(raw))
            color = app.np.asarray(editor.env.gym.get_camera_image(
                editor.env.sim, editor.env.env, camera, app.gymapi.IMAGE_COLOR))
            if color.size != WIDTH*HEIGHT*4:
                raise RuntimeError('native camera returned invalid image: '+name)
            view = app.np.asarray(editor.env.gym.get_camera_view_matrix(editor.env.sim, editor.env.env, camera))
            projection = app.np.asarray(editor.env.gym.get_camera_proj_matrix(editor.env.sim, editor.env.env, camera))
            depth = app.np.asarray(editor.env.gym.get_camera_image(
                editor.env.sim, editor.env.env, camera, app.gymapi.IMAGE_DEPTH)).reshape(HEIGHT, WIDTH)
            final = image_dir/('position_region_'+name+'.png')
            details = annotate(raw, final, {'view_matrix': view.tolist(),
                'projection_matrix': projection.tolist()}, chest_height,
                REFERENCE_POSITION, chest_root.tolist(), depth)
            output_records[name] = {'raw_image': str(raw.resolve()),
                'raw_sha256': sha(raw), 'annotated_image': str(final.resolve()),
                **details, 'view_matrix': view.tolist(), 'projection_matrix': projection.tolist()}
        after = native_state(editor.env)
        checks = {'physics_steps_zero': editor.env.steps == 0,
            'human_body_states_unchanged': after['human_body_states'] == initial['human_body_states'],
            'human_joint_states_unchanged': after['human_dof_states'] == initial['human_dof_states'],
            'fixed_guitar_reference_pose': app.np.allclose(editor.position, REFERENCE_POSITION, atol=1e-9),
            'render_preserves_state': after == before,
            'blocked_physics_calls_zero': editor.env.gym.blocked_physics_calls == 0,
            'both_native_views_saved': len(output_records) == 2}
        if not all(checks.values()):
            raise AssertionError(checks)
    finally:
        editor.close_scene()

    checks['input_sources_unchanged'] = all(sha(path) == digest for path, digest in input_hashes.items())
    if not checks['input_sources_unchanged']:
        raise AssertionError(checks)
    report = {'checks': checks, 'physics_steps': 0, 'reference_position_W_m': REFERENCE_POSITION,
        'reference_euler_xyz_world_deg': REFERENCE_EULER_XYZ,
        'chest_body_name': 'Chest', 'chest_origin_W_m': chest_root.tolist(),
        'z_upper_approx_m': chest_height,
        'position_region_W_m': {'x': [-.50, -.15], 'y': [-.15, .15], 'z': [.65, chest_height]},
        'position_reference_semantics': 'guitar actor root only; not the full guitar mesh',
        'scope': 'fixed pose and native camera renders with depth-tested annotation; zero physics; no contact or stability certification',
        'input_sha256': input_hashes, 'views': output_records}
    save(phase/'report.json', report)
    doc = ['# 기타 위치 허용영역 박스와 기준점', '',
        '기타를 여러 위치로 이동한 비교 이미지가 아니라, 기타 한 대를 기준 포즈에 둔 채 root 위치 허용영역을 박스로 표시했습니다. 박스와 표식은 native Isaac Gym camera view/projection에 맞춰 깊이 검사를 적용해 이미지 위에 그렸습니다.', '',
        f'현재 저장된 사람 자세의 `Chest` rigid-body 원점은 월드 `{chest_root[2]:.3f}m`입니다. 이를 요청하신 “가슴 높이 정도”의 Z 상한으로 사용했습니다. 이는 링크 원점으로 정한 근사 높이이며 가슴 표면이나 충돌 경계가 아닙니다.', '',
        f'허용영역은 X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,{chest_height:.3f}]m`입니다. 기타 actor-root 기준점 `(-0.325,0.000,0.800)m`는 노란 표식입니다. 박스는 root 위치를 제한하는 영역이며 기타 전체 형상이 박스 안에 들어간다는 뜻은 아닙니다. Chest 원점은 분홍 표식입니다.', '',
        '![위치 허용영역 박스와 기타 root 기준점 — isometric]('+str(image_dir/'position_region_isometric.png')+')', '',
        '![위치 허용영역 박스와 기타 root 기준점 — whole body]('+str(image_dir/'position_region_whole_body.png')+')', '',
        '장면 초기화 후 물리 step은 0입니다. 휴머노이드 및 기타 상태가 렌더 전후 동일하고 strap은 표시하지 않았습니다. 이미지는 영역의 공간적 의미를 설명하며 접촉·겹침·안정성을 검증하지 않습니다.']
    (phase/'README.md').write_text('\n'.join(doc)+'\n', encoding='utf-8')
    print(json.dumps({'checks': checks, 'chest_z_m': chest_height,
                      'position_region_z_m': [.65, chest_height]}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
