"""Re-render the unchanged root position region with stronger, depth-tested faces."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

from . import interactive_guitar_pose_static as app
from . import render_position_region_box as box
from . import render_position_region_views_v2 as views
from .guitar_pose_static import Editor
from .run_physx_contacts import native_state

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/2026-10-12/기타허용범위/범위강조_v2'
PLAN = Path(__file__).with_name('POSITION_REGION_VISIBILITY_PLAN.md')
REFERENCE_POSITION = [-.325, 0., .80]
REFERENCE_EULER_XYZ = [67.5, 75., 157.5]
WIDTH, HEIGHT = 1280, 720
FACE_COLORS = {'top': (255, 162, 30, 52), 'other': (20, 225, 190, 38)}
EDGE_COLORS = {'top': (255, 164, 35, 255), 'vertical': (45, 220, 250, 255),
               'side': (20, 230, 205, 255)}
HIDDEN_COLORS = {'top': (255, 180, 70, 125), 'other': (125, 220, 205, 120)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def faces(corners):
    return {
        'bottom': [corners[k] for k in ((0,0,0),(1,0,0),(1,1,0),(0,1,0))],
        'top': [corners[k] for k in ((0,0,1),(1,0,1),(1,1,1),(0,1,1))],
        'x_min': [corners[k] for k in ((0,0,0),(0,1,0),(0,1,1),(0,0,1))],
        'x_max': [corners[k] for k in ((1,0,0),(1,1,0),(1,1,1),(1,0,1))],
        'y_min': [corners[k] for k in ((0,0,0),(1,0,0),(1,0,1),(0,0,1))],
        'y_max': [corners[k] for k in ((0,1,0),(1,1,0),(1,1,1),(0,1,1))],
    }


def fill_face(draw, vertices, view, projection, depth, color, grid=96):
    a, b, c, d = [app.np.asarray(v, dtype=float) for v in vertices]
    uv = app.np.linspace(0., 1., grid)
    samples = app.np.asarray([a*(1-u)*(1-v)+b*u*(1-v)+c*u*v+d*(1-u)*v
                              for u in uv for v in uv])
    pixels, camera_z, valid = box.project(samples, view, projection)
    ids = app.np.flatnonzero(valid)
    if not len(ids):
        return 0
    xy = pixels[ids].astype(int)
    scene_z = depth[xy[:, 1], xy[:, 0]]
    visible = camera_z[ids] >= scene_z-.002
    count = 0
    for index in ids[visible]:
        x, y = map(int, pixels[index])
        draw.rectangle((x-1, y-1, x+1, y+1), fill=color)
        count += 1
    return count


def annotate(raw, out, view, projection, depth, chest_z):
    base = Image.open(raw).convert('RGBA')
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    corners = box.box_corners(chest_z)
    face_counts = {}
    for name, vertices in faces(corners).items():
        color = FACE_COLORS['top' if name == 'top' else 'other']
        face_counts[name] = fill_face(draw, vertices, view, projection, depth, color)
    visible_edge_count = hidden_edge_count = 0
    for a, b, axis, is_top in box.box_edges(corners):
        key = 'top' if is_top else 'vertical' if axis == 2 else 'side'
        before = visible_edge_count+hidden_edge_count
        box.draw_segment(draw, a, b, view, projection, depth,
                         EDGE_COLORS[key], HIDDEN_COLORS['top' if is_top else 'other'],
                         width=7, tolerance=.002)
        after = visible_edge_count+hidden_edge_count
        visible_edge_count += 1

    for label, point, color in (
            ('guitar root', REFERENCE_POSITION, (255, 235, 45, 255)),
            ('Chest origin', [-.011076075956225395, -.1641721874475479, chest_z],
             (255, 65, 190, 255))):
        pixels, _, valid = box.project([point], view, projection)
        if valid[0]:
            x, y = map(int, pixels[0])
            draw.ellipse((x-13, y-13, x+13, y+13), fill=(0, 0, 0, 235),
                         outline=(0, 0, 0, 255), width=3)
            draw.ellipse((x-8, y-8, x+8, y+8), fill=color,
                         outline=(255, 255, 255, 255), width=2)
            draw.line((x-17, y, x+17, y), fill=(0, 0, 0, 230), width=2)
            draw.line((x, y-17, x, y+17), fill=(0, 0, 0, 230), width=2)

    font = ImageFont.truetype(str(box.FONT), 18)
    small = ImageFont.truetype(str(box.FONT), 16)
    draw.rounded_rectangle((16, 14, 820, 111), radius=9,
                           fill=(12, 19, 29, 232), outline=(220, 230, 238, 235), width=1)
    draw.text((32, 22), '기타 root 위치 허용 범위 — 색칠된 3D 박스',
              font=font, fill=(255, 255, 255, 255))
    draw.text((32, 49), 'X [-0.50,-0.15]m | Y [-0.15,0.15]m | Z [0.65,%.3f]m' % chest_z,
              font=small, fill=(105, 255, 230, 255))
    draw.text((32, 77), '노랑 ● 기타 위치 기준점 (-0.325,0.000,0.800)m | 분홍 ● Chest 높이',
              font=small, fill=(255, 245, 205, 255))
    Image.alpha_composite(base, layer).convert('RGB').save(out, format='PNG')
    return {'face_visible_samples': face_counts,
            'visible_edges': visible_edge_count, 'depth_test': True,
            'source_image_sha256': sha(raw), 'output_image_sha256': sha(out)}


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    raw_dir, scene_dir = OUT/'native_raw', OUT/'native_scene'
    raw_dir.mkdir()
    inputs = [Path(__file__).resolve(), PLAN, Path(box.__file__).resolve(),
              Path(views.__file__).resolve(), Path(app.__file__).resolve(),
              Path(__file__).with_name('guitar_pose_static.py'),
              Path(__file__).with_name('interactive_guitar_pose_static.py'),
              Path(__file__).with_name('guitar_pose_edit.py'),
              Path(__file__).with_name('capture_isaac_gym_initial.py'),
              Path(__file__).with_name('run_physx_contacts.py'), app.BASELINE, box.FONT]
    input_hashes = {str(p.resolve()): sha(p) for p in inputs}
    editor = Editor(scene_dir, strap=False, viewer=False)
    try:
        editor.position = app.np.asarray(REFERENCE_POSITION, dtype=float)
        editor.quaternion = Rotation.from_euler('xyz', REFERENCE_EULER_XYZ, degrees=True).as_quat()
        editor.install_pose()
        initial = native_state(editor.env)
        chest_index = editor.env.human_bodies.index('Chest')
        chest_state = editor.env.bodies(editor.env.human)[chest_index]
        chest_position = app.vector(chest_state['pose']['p']).astype(float)
        chest_z = float(chest_position[2])
        if not REFERENCE_POSITION[2] < chest_z:
            raise AssertionError('reference root must remain below the chest-height box ceiling')
        cameras = {}
        for name, setup in views.CAMERAS.items():
            props = app.gymapi.CameraProperties()
            props.width, props.height = WIDTH, HEIGHT
            camera = editor.env.gym.create_camera_sensor(editor.env.env, props)
            if camera < 0:
                raise RuntimeError('native camera creation failed: '+name)
            editor.env.gym.set_camera_location(camera, editor.env.env,
                app.gymapi.Vec3(*setup['position_W_m']), app.gymapi.Vec3(*setup['target_W_m']))
            cameras[name] = camera
        editor.env.gym.render_all_camera_sensors(editor.env.sim)
        before = native_state(editor.env)
        image_records = {}
        for name, camera in cameras.items():
            raw, output = raw_dir/(name+'.png'), OUT/(name+'.png')
            editor.env.gym.write_camera_image_to_file(editor.env.sim, editor.env.env,
                camera, app.gymapi.IMAGE_COLOR, str(raw))
            rgba = app.np.asarray(editor.env.gym.get_camera_image(
                editor.env.sim, editor.env.env, camera, app.gymapi.IMAGE_COLOR))
            if rgba.size != WIDTH*HEIGHT*4 or not raw.is_file() or raw.stat().st_size == 0:
                raise RuntimeError('native camera image was not written: '+name)
            view_matrix = app.np.asarray(editor.env.gym.get_camera_view_matrix(
                editor.env.sim, editor.env.env, camera))
            projection = app.np.asarray(editor.env.gym.get_camera_proj_matrix(
                editor.env.sim, editor.env.env, camera))
            depth = app.np.asarray(editor.env.gym.get_camera_image(
                editor.env.sim, editor.env.env, camera, app.gymapi.IMAGE_DEPTH)).reshape(HEIGHT, WIDTH)
            detail = annotate(raw, output, view_matrix, projection, depth, chest_z)
            views.compass(output, view_matrix, projection, views.CAMERAS[name]['axes'])
            detail['output_image_sha256'] = sha(output)
            detail['view_matrix'] = view_matrix.tolist()
            detail['projection_matrix'] = projection.tolist()
            detail['raw_image_sha256'] = sha(raw)
            image_records[name] = {'raw_image': str(raw.resolve()),
                                   'image': str(output.resolve()), **detail}
        after = native_state(editor.env)
        checks = {'physics_steps_zero': editor.env.steps == 0,
                  'human_body_states_unchanged': after['human_body_states'] == initial['human_body_states'],
                  'human_joint_states_unchanged': after['human_dof_states'] == initial['human_dof_states'],
                  'guitar_state_unchanged_by_cameras': after['guitar_body_states'] == before['guitar_body_states'],
                  'render_preserves_state': after == before,
                  'blocked_physics_calls_zero': editor.env.gym.blocked_physics_calls == 0,
                  'three_views_written': set(image_records) == {'front', 'side', 'top'},
                  'all_faces_visible_somewhere': all(sum(v['face_visible_samples'].values()) > 0
                                                     for v in image_records.values()),
                  'all_output_hashes_match': all(sha(v['image']) == v['output_image_sha256']
                                                for v in image_records.values())}
        if not all(checks.values()):
            raise AssertionError(checks)
        app.save(scene_dir/'reference_pose.json', editor.payload())
        app.save(scene_dir/'initial_state.json', initial)
    finally:
        editor.close_scene()

    checks['inputs_unchanged'] = all(sha(p) == h for p, h in input_hashes.items())
    if not all(checks.values()):
        raise AssertionError(checks)
    region = {'x': [-.50, -.15], 'y': [-.15, .15], 'z': [.65, chest_z]}
    report = {'checks': checks, 'physics_steps': 0, 'strap_display': False,
              'position_region_W_m': region, 'reference_position_W_m': REFERENCE_POSITION,
              'reference_euler_xyz_world_deg': REFERENCE_EULER_XYZ,
              'position_reference_semantics': 'unchanged guitar actor-root point; same as original three-view render',
              'chest_origin_W_m': chest_position.tolist(), 'views': image_records,
              'input_sha256': input_hashes,
              'scope': 'more visible depth-tested range-box annotation; fixed guitar pose; no physical/contact/stability test'}
    write_json(OUT/'report.json', report)
    doc = ['# 기타 위치 허용 범위가 강조된 front / side / top 이미지', '',
           '이 버전은 앞선 세 시점의 기준과 기타 위치를 유지하고, 위치 범위를 반투명 색면과 굵은 모서리로 더 뚜렷하게 표시합니다. 기타는 한 대만 기준 포즈에 있습니다.', '',
           '청록색 반투명 면/굵은 선이 허용영역 X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,%.3f]m`이고, 주황색 윗면이 Chest 높이 상한입니다. 노란 점은 기존과 같은 기타 actor-root 기준점 `(-0.325,0.000,0.800)m`, 분홍 점은 Chest 원점입니다.' % chest_z, '',
           '이미지는 깊이 검사를 적용한 Isaac Gym native 카메라 결과입니다. 가려지는 모서리는 연한 점선으로 표현됩니다. 물리 step 0이며 범위의 의미를 보여줄 뿐 접촉·겹침·안정성을 검증하지 않습니다.', '',
           '![Front view]('+str(OUT/'front.png')+')', '',
           '![Side view]('+str(OUT/'side.png')+')', '',
           '![Top view]('+str(OUT/'top.png')+')', '',
           '원본 카메라 프레임은 `native_raw/`, 카메라 행렬·해시·불변 상태 검사는 `report.json`, pose/state는 `native_scene/`에 있습니다.']
    (OUT/'README.md').write_text('\n'.join(doc)+'\n', encoding='utf-8')
    print(json.dumps({'checks': checks, 'output': str(OUT),
                      'region_z_m': region['z']}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
