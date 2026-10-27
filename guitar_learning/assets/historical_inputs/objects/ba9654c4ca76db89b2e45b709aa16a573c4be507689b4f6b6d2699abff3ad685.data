"""Save front, side and top views of the fixed guitar and its position region."""
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from scipy.spatial.transform import Rotation

from . import interactive_guitar_pose_static as app
from . import render_position_region_box as box
from .guitar_pose_static import Editor
from .run_physx_contacts import native_state

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/2026-10-12/기타허용범위'
PLAN = Path(__file__).with_name('POSITION_REGION_VIEWS_PLAN.md')
REFERENCE_POSITION = [-.325, 0., .80]
REFERENCE_EULER_XYZ = [67.5, 75., 157.5]
WIDTH, HEIGHT = 1280, 720
CAMERAS = {
    'front': {'position_W_m': [0., 1.70, .96], 'target_W_m': [-.23, -.015, .86],
              'axes': ('X', 'Z')},
    'side': {'position_W_m': [1.70, 0., .96], 'target_W_m': [-.23, -.015, .86],
             'axes': ('Y', 'Z')},
    'top': {'position_W_m': [.12, 0., 2.20], 'target_W_m': [-.325, 0., .80],
            'axes': ('X', 'Y')},
}
AXIS_COLORS = {'X': (245, 85, 85, 255), 'Y': (80, 220, 125, 255),
               'Z': (80, 155, 255, 255)}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def compass(path, view, projection, axes):
    image = Image.open(path).convert('RGBA')
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(str(box.FONT), 17)
    origin = app.np.array([-.325, 0., .80], dtype=float)
    anchor = (1175, 650)
    for axis in axes:
        vector = app.np.zeros(3)
        vector['XYZ'.index(axis)] = .12
        pixels, _, valid = box.project([origin, origin+vector], view, projection)
        delta = pixels[1]-pixels[0]
        length = float(app.np.linalg.norm(delta))
        if not valid.all() or length < 2:
            continue
        direction = delta/length
        end = (int(anchor[0]+direction[0]*52), int(anchor[1]+direction[1]*52))
        color = AXIS_COLORS[axis]
        draw.line((anchor, end), fill=(0, 0, 0, 230), width=8)
        draw.line((anchor, end), fill=color, width=4)
        draw.ellipse((end[0]-5, end[1]-5, end[0]+5, end[1]+5), fill=color,
                     outline=(15, 25, 35, 255), width=1)
        draw.text((end[0]+7, end[1]-12), axis, font=font, fill=(255, 255, 255, 255),
                  stroke_width=2, stroke_fill=(0, 0, 0, 220))
    image.convert('RGB').save(path, format='PNG')


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    raw_dir = OUT/'native_raw'
    raw_dir.mkdir()
    inputs = [Path(__file__).resolve(), PLAN, Path(box.__file__).resolve(),
              Path(app.__file__).resolve(), Path(__file__).with_name('guitar_pose_static.py'),
              Path(__file__).with_name('interactive_guitar_pose_static.py'),
              Path(__file__).with_name('guitar_pose_edit.py'),
              Path(__file__).with_name('capture_isaac_gym_initial.py'),
              Path(__file__).with_name('run_physx_contacts.py'), app.BASELINE, box.FONT]
    input_hashes = {str(path.resolve()): sha(path) for path in inputs}
    editor = Editor(OUT/'native_scene', strap=False, viewer=False)
    try:
        editor.position = app.np.asarray(REFERENCE_POSITION, dtype=float)
        editor.quaternion = Rotation.from_euler('xyz', REFERENCE_EULER_XYZ,
                                                degrees=True).as_quat()
        editor.install_pose()
        initial = native_state(editor.env)
        chest_i = editor.env.human_bodies.index('Chest')
        chest_state = editor.env.bodies(editor.env.human)[chest_i]
        chest_world = app.vector(chest_state['pose']['p']).astype(float)
        z_upper = float(chest_world[2])
        if not .65 < REFERENCE_POSITION[2] < z_upper:
            raise AssertionError('reference guitar point is outside the vertical region')
        editor.env.gym.step_graphics(editor.env.sim)

        cameras = {}
        for name, config in CAMERAS.items():
            props = app.gymapi.CameraProperties()
            props.width, props.height = WIDTH, HEIGHT
            camera = editor.env.gym.create_camera_sensor(editor.env.env, props)
            if camera < 0:
                raise RuntimeError('native camera creation failed: '+name)
            editor.env.gym.set_camera_location(camera, editor.env.env,
                app.gymapi.Vec3(*config['position_W_m']),
                app.gymapi.Vec3(*config['target_W_m']))
            cameras[name] = camera

        editor.env.gym.render_all_camera_sensors(editor.env.sim)
        before_render = native_state(editor.env)
        views, outputs = {}, {}
        for name, camera in cameras.items():
            raw = raw_dir/(name+'.png')
            ok = editor.env.gym.write_camera_image_to_file(editor.env.sim, editor.env.env,
                camera, app.gymapi.IMAGE_COLOR, str(raw))
            color = app.np.asarray(editor.env.gym.get_camera_image(
                editor.env.sim, editor.env.env, camera, app.gymapi.IMAGE_COLOR))
            if not ok or color.size != WIDTH*HEIGHT*4 or not raw.is_file():
                raise RuntimeError('native camera capture failed: '+name)
            view = app.np.asarray(editor.env.gym.get_camera_view_matrix(editor.env.sim,
                                                                         editor.env.env, camera))
            projection = app.np.asarray(editor.env.gym.get_camera_proj_matrix(editor.env.sim,
                                                                               editor.env.env, camera))
            depth = app.np.asarray(editor.env.gym.get_camera_image(
                editor.env.sim, editor.env.env, camera, app.gymapi.IMAGE_DEPTH)).reshape(HEIGHT, WIDTH)
            output = OUT/(name+'.png')
            detail = box.annotate(raw, output, {'view_matrix': view.tolist(),
                'projection_matrix': projection.tolist()}, z_upper,
                REFERENCE_POSITION, chest_world.tolist(), depth)
            compass(output, view, projection, CAMERAS[name]['axes'])
            detail['output_image_sha256'] = sha(output)
            detail['axis_compass'] = list(CAMERAS[name]['axes'])
            detail['source_image_sha256'] = sha(raw)
            views[name] = {'camera_position_W_m': CAMERAS[name]['position_W_m'],
                'camera_target_W_m': CAMERAS[name]['target_W_m'],
                'view_matrix': view.tolist(), 'projection_matrix': projection.tolist(), **detail}
            outputs[name] = {'raw': str(raw.resolve()), 'image': str(output.resolve()), **detail}

        after_render = native_state(editor.env)
        checks = {'zero_physics_steps': editor.env.steps == 0,
            'human_body_states_unchanged': after_render['human_body_states'] == initial['human_body_states'],
            'human_joint_states_unchanged': after_render['human_dof_states'] == initial['human_dof_states'],
            'guitar_state_unchanged_by_cameras': after_render['guitar_body_states'] == before_render['guitar_body_states'],
            'render_preserves_state': after_render == before_render,
            'blocked_physics_calls_zero': editor.env.gym.blocked_physics_calls == 0,
            'three_views_written': set(outputs) == {'front', 'side', 'top'},
            'all_view_image_hashes_match': all(sha(v['image']) == v['output_image_sha256']
                                              for v in outputs.values())}
        if not all(checks.values()):
            raise AssertionError(checks)
        pose = editor.payload()
        app.save(OUT/'native_scene'/'reference_pose.json', pose)
        app.save(OUT/'native_scene'/'initial_state.json', initial)
    finally:
        editor.close_scene()

    checks['inputs_unchanged'] = all(sha(path) == digest for path, digest in input_hashes.items())
    if not all(checks.values()):
        raise AssertionError(checks)
    report = {'checks': checks, 'physics_steps': 0, 'strap_display': False,
        'reference_position_W_m': REFERENCE_POSITION,
        'reference_euler_xyz_world_deg': REFERENCE_EULER_XYZ,
        'position_region_W_m': {'x': [-.50, -.15], 'y': [-.15, .15], 'z': [.65, z_upper]},
        'position_reference_semantics': 'guitar actor-root point; not the full guitar mesh',
        'chest_body_name': 'Chest', 'chest_origin_W_m': chest_world.tolist(),
        'views': views, 'input_sha256': input_hashes,
        'scope': 'three native Isaac Gym camera views with world-space, depth-tested position-region overlay; no physics/contact/stability test'}
    write_json(OUT/'report.json', report)
    text = ['# 기타 위치 허용영역 — front / side / top', '',
        '기타는 이동 비교용으로 여러 번 배치하지 않았습니다. 세 장 모두 같은 기준 포즈의 기타 한 대를 보여주며, 박스는 기타 actor-root 위치가 이동할 수 있는 월드 좌표 영역입니다.', '',
        f'영역: X `[-0.50,-0.15]m`, Y `[-0.15,0.15]m`, Z `[0.65,{z_upper:.3f}]m`. Z 상한은 현재 초기 자세의 Chest rigid-body 원점 높이 `{z_upper:.6f}m`로 근사했습니다. Chest 원점은 분홍 점, 기타 root 기준점 `(-0.325,0.000,0.800)m`는 노란 점입니다. 기타 전체 mesh가 박스 안에 들어간다는 뜻은 아닙니다.', '',
        '색상: 청록색은 영역 상자 옆면/수직 모서리, 주황색은 Chest 높이의 윗면, 연한 점선은 장면 물체에 가려지는 박스 모서리입니다. 우하단 축 표시는 각 카메라에서 보이는 world axes입니다.', '',
        f'![Front view]({OUT / "front.png"})', '',
        f'![Side view]({OUT / "side.png"})', '',
        f'![Top view]({OUT / "top.png"})', '',
        '모두 Isaac Gym native camera 이미지입니다. 물리 step은 0이며 사람/기타 상태 불변을 확인했습니다. 실제 접촉, 겹침 또는 안정성을 검증한 결과는 아닙니다. 카메라 원본은 `native_raw/`, 초기 pose/state 및 행렬·해시는 `report.json`과 `native_scene/`에 보존했습니다.']
    (OUT/'README.md').write_text('\n'.join(text)+'\n', encoding='utf-8')
    print(json.dumps({'checks': checks, 'chest_z_m': z_upper,
                      'output': str(OUT)}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
