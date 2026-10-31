"""Capture real finger opening/closing and replay the saved source-mesh poses."""
import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def capture(out, profile):
    import isaacgym
    import numpy as np
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.core.control import default_profile
    from guitar_learning.core.measurement import StabilityMonitor
    from guitar_learning.core.training_environment import default_action_ranges
    from guitar_learning.runtime.persistent_environment import PreparedPersistentContactEnvironment as PersistentContactEnvironment
    from guitar_learning.runtime.finger_session import FlexibleLeftFingerSession
    from guitar_learning.runtime.persistent_session import PersistentHeadlessPreparedSession
    from guitar_learning.runtime.prepared_reset_v1 import BASELINE_CONFIG, prepared_input_paths
    from guitar_learning.training.training_log_io import digest, write
    out.mkdir(parents=True, exist_ok=False)
    sources = prepared_input_paths() | {Path(__file__).resolve()}
    sources.update(p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts)
    pins = {str(p): digest(p) for p in sorted(sources)}
    write(out/'inputs_before.json', pins)
    flexible = profile == 'flexible'
    session_type = FlexibleLeftFingerSession if flexible else PersistentHeadlessPreparedSession
    env = PersistentContactEnvironment(BASELINE_CONFIG, out/'environment',
        action_half_range_rad=default_action_ranges(), preparation_seconds=0.,
        session_factory=session_type, finger_profile=default_profile() if flexible else None)
    rows, failures, first_native_delta = [], [], None
    maximum_speed = maximum_guitar_m = maximum_guitar_rad = 0.
    try:
        sample, reset = env.reset()
        scene = env.session.scene
        initial = dict(joint_names=scene.names, human_body_names=scene.human_bodies,
            guitar_body_names=scene.guitar_bodies, loaded_assets=scene.loaded_assets,
            chair_initial_placement=scene.chair_placement)
        write(out/'initial_values.json', initial)
        write(out/'reset_initial.json', reset)
        monitor = StabilityMonitor(scene.human_bodies, scene.guitar_bodies)
        monitor.reset(sample)
        rows.append(dict(tick=0, action=[0.]*39, sample=sample))
        for tick in range(240):
            action = np.zeros(39)
            # Fixed diagnostic gesture, no trained policy or posture injection.
            phase = tick/60.
            amplitude = (-.35 if phase < 1. else .35 if phase < 2. else
                         -.35 if phase < 3. else 0.)
            for index, name in enumerate(ACTIVE_NAMES):
                if name.startswith('LH:') and (name.endswith(('1_x', '2', '3'))):
                    action[index] = amplitude
            if tick == 0:
                action[:] = 0.
                action[ACTIVE_NAMES.index('LH:index1_x')] = 1.
            before = scene.target.copy()
            sample, info = env.step(action)
            if tick == 0:
                index = scene.names.index('LH:index1_x')
                first_native_delta = float(scene.target[index]-before[index])
            for physical in info['physics_samples240']:
                safety = monitor.update(physical)
                maximum_speed = max(maximum_speed, safety['max_joint_speed_rad_s'])
                maximum_guitar_m = max(maximum_guitar_m, float(np.linalg.norm(safety['guitar_delta_m'])))
                maximum_guitar_rad = max(maximum_guitar_rad, float(np.linalg.norm(safety['guitar_rotation_vector_rad'])))
                failures.extend(r for r in safety['failure_reasons'] if r not in failures)
            rows.append(dict(tick=tick+1, action=action.tolist(), sample=sample,
                target105_rad=scene.target.tolist(), command=info['target_submission']))
            if failures:
                break
        expected_delta = (4. if flexible else 1.5)/60.
        if not np.isclose(first_native_delta, expected_delta, atol=1e-6, rtol=0.):
            raise RuntimeError('final native finger target rate mismatch')
        before_reset = sample['native']['physics_step']
        restored, reset_again = env.reset()
        if restored['native']['physics_step'] != 0:
            raise RuntimeError('finger demonstration reset did not restore clock')
        write(out/'reset_again.json', reset_again)
        joint_range = {}
        for index, name in enumerate(scene.names):
            if name.startswith('LH:'):
                values = [row['sample']['native']['human_dof_states'][index]['pos'] for row in rows]
                joint_range[name] = dict(min_rad=min(values), max_rad=max(values),
                    excursion_deg=float(np.rad2deg(max(values)-min(values))))
        write(out/'samples.json.gz', rows, compressed=True)
        changed = [p for p, value in pins.items() if digest(p) != value]
        report = dict(completed=not failures and len(rows)==241 and not changed,
            profile=profile, physics_steps=before_reset, policy_ticks=len(rows)-1,
            training_updates=0, first_index_native_target_delta_rad=first_native_delta,
            max_joint_speed_rad_s=maximum_speed, max_guitar_displacement_m=maximum_guitar_m,
            max_guitar_rotation_rad=maximum_guitar_rad, failure_reasons=failures,
            changed_inputs=changed, finger_joint_ranges=joint_range,
            finger_control=getattr(env.session, 'finger_control_description', None),
            reset_scope='same native scene, prepared state at boundary; no per-step state writes',
            scope='fixed opening/closing diagnostic; not a trained musical performance')
        write(out/'report.json', report)
        if not report['completed']:
            raise RuntimeError('finger motion diagnostic incomplete; see report.json')
    finally:
        env.close()


def render(capture_path, out):
    os.environ['MUJOCO_GL'] = 'osmesa'
    os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
    import gzip
    import subprocess
    import mujoco
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from guitar_learning.core.geometry import frame
    from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import (
        build_model, set_body_poses, asset_paths)
    from guitar_learning.training.training_log_io import digest, write
    out.mkdir(parents=True, exist_ok=False)
    initial = json.loads((capture_path/'initial_values.json').read_text())
    report = json.loads((capture_path/'report.json').read_text())
    if not report['completed'] or report['policy_ticks'] != 240:
        raise ValueError('complete fixed motion recording required')
    with gzip.open(capture_path/'samples.json.gz', 'rt') as stream:
        rows = json.load(stream)
    if [r['sample']['native']['physics_step'] for r in rows] != list(range(0, 961, 4)):
        raise ValueError('consecutive recorded 60Hz poses required')
    font_path = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    sources = {Path(__file__).resolve(), font_path, capture_path/'samples.json.gz',
               capture_path/'initial_values.json', capture_path/'report.json'}
    for asset in initial['loaded_assets']:
        sources.update(asset_paths(Path(asset['path'])))
    sources.update(ROOT/p for p in (
        'guitar_learning/native/initial_pose_video60_v1/static_visual_v7.py',
        'guitar_learning/native/initial_pose_video60_v1/replay_v6.py',
        'guitar_learning/native/paths.py', 'guitar_learning/core/geometry.py',
        'guitar_learning/assets/native_provenance.json'))
    pins = {str(p):digest(p) for p in sources}
    model, data, mapping, _ = build_model(initial)
    for geom in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[geom])) or ''
        model.geom_rgba[geom] = ((1., .55, .12, 1.) if name.startswith('human/LH:thumb') else
            (.22, .56, .76, 1.) if name.startswith('human/LH:') or name=='human/L_Wrist' else
            (.62, .65, .69, 1.) if name.startswith('guitar/') else (0., 0., 0., 0.))
    model.vis.headlight.ambient[:] = .55
    model.vis.headlight.diffuse[:] = .7
    model.vis.map.znear = .0001
    renderer = mujoco.Renderer(model, height=640, width=640)
    font = ImageFont.truetype(str(font_path), 25)
    small = ImageFont.truetype(str(font_path), 19)
    camera = mujoco.MjvCamera()
    camera.type = mujoco.mjtCamera.mjCAMERA_FREE
    gp, gr = frame(rows[0]['sample']['native']['guitar_body_states'][initial['guitar_body_names'].index('guitar')])
    process = subprocess.Popen(['ffmpeg','-nostdin','-n','-loglevel','error',
        '-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-',
        '-an','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(out/'finger_motion.mp4')], stdin=subprocess.PIPE)
    frames = 0
    try:
        for row in rows[::2]:
            readback = set_body_poses(model, data, mapping, row['sample']['native'])
            image = Image.new('RGB', (1280,720), (240,244,248))
            for view, offset in enumerate(([.09,.08,.30], [.09,.08,-.30])):
                camera.lookat[:] = gp+gr.apply([.025,.045,-.025])
                direction = -gr.apply(offset)
                camera.distance = float(np.linalg.norm(direction))
                camera.azimuth = float(np.rad2deg(np.arctan2(direction[1],direction[0])))
                camera.elevation = float(np.rad2deg(np.arctan2(direction[2],np.linalg.norm(direction[:2]))))
                renderer.update_scene(data,camera=camera)
                image.paste(Image.fromarray(renderer.render()), (view*640,60))
            draw = ImageDraw.Draw(image)
            draw.text((18,8),'실제 물리 손가락 동작 · '+report['profile']+' · %.2f초'%(row['tick']/60),font=font,fill=(25,38,50))
            draw.text((18,690),'앞쪽 / 뒤쪽 | 원본 메시의 저장 자세 재생 · 학습 0회',font=small,fill=(25,38,50))
            process.stdin.write(np.asarray(image).tobytes())
            if row['tick'] in (0,60,120,180,240):
                image.save(out/('pose_%03d.png'%row['tick']))
            frames += 1
    finally:
        renderer.close()
        process.stdin.close()
        code = process.wait()
    if code or frames != 121 or any(digest(Path(p))!=value for p,value in pins.items()):
        raise RuntimeError('recorded finger video verification failed')
    stream = json.loads(subprocess.run(['ffprobe','-v','error','-count_frames',
        '-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,nb_read_frames,duration',
        '-of','json',str(out/'finger_motion.mp4')],check=True,capture_output=True,text=True).stdout)['streams'][0]
    if (stream['width'],stream['height'],stream['avg_frame_rate'],int(stream['nb_read_frames'])) != (1280,720,'30/1',121):
        raise RuntimeError('video dimensions/rate/coverage mismatch')
    write(out/'report.json', dict(completed=True,frames=frames,source=str(capture_path),
        scope='rendered original meshes at saved native world poses; no new physics',
        inputs_sha256=pins,video_sha256=digest(out/'finger_motion.mp4'),ffprobe=stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    native = commands.add_parser('capture')
    native.add_argument('--profile', choices=('flexible','legacy'), default='flexible')
    native.add_argument('--out', type=Path, required=True)
    video = commands.add_parser('render')
    video.add_argument('--capture', type=Path, required=True)
    video.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'capture':
        capture(args.out.resolve(),args.profile)
    else:
        render(args.capture.resolve(),args.out.resolve())


if __name__ == '__main__':
    main()
