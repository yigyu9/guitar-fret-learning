"""Zero-step Isaac Gym cameras of the current guitar, with display-only colors."""
from isaacgym import gymapi

import argparse
import hashlib
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np

ROOT = Path('/home/ajou/yigyu/3')
ASSET = ROOT / 'stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml'
COLORS = [(1., .35, .35), (1., .7, .15), (.95, .9, .2),
          (.2, .9, .6), (.2, .7, 1.), (.75, .5, 1.)]
CAMERAS = {
    'overview': dict(size=[1600, 1800], eye=[.08, -.17, 1.65], target=[0., -.17, 0.], fov=42.),
    'frets': dict(size=[1000, 1700], eye=[.025, -.007, .78], target=[0., -.007, 0.], fov=32.),
    'strike': dict(size=[1300, 1200], eye=[.16, -.31, .49], target=[0., -.32, 0.], fov=39.),
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    tree = ET.parse(ASSET)
    xml = tree.getroot()
    meshdir = (ASSET.parent / xml.find('compiler').get('meshdir', '.')).resolve()
    meshes = [(mesh, (meshdir / mesh.get('file')).resolve()) for mesh in xml.findall('./asset/mesh')]
    inputs = [ASSET, Path(__file__).resolve(), ROOT / 'guitar_learning/strike.py',
              ROOT / 'guitar_learning/geometry_v1.py'] + [path for _, path in meshes]
    pins = {str(path): sha(path) for path in inputs}
    source_bodies = {body.get('name'): body for body in xml.findall('.//body')}
    for mesh, path in meshes:
        mesh.set('file', os.path.relpath(path, args.out))
    xml.find('compiler').set('meshdir', '.')
    source_bodies['G:pluck_range'].find('geom').set('rgba', '0 0 0 0')
    for n in range(1, 23):
        for geom in source_bodies['G:fret%d' % n].findall('geom'):
            geom.set('rgba', '.15 .95 .5 1')
    root_body = source_bodies['guitar']
    strings = sorted([g for g in root_body.findall('geom') if g.get('type') == 'capsule'],
                     key=lambda g: -float(g.get('pos').split()[0]))
    assert len(strings) == 6
    for geom, color in zip(strings, COLORS):
        geom.set('rgba', ' '.join(str(x) for x in (*color, 1.)))
    display = args.out / 'guitar_display.xml'
    tree.write(str(display), encoding='unicode')
    original_elements = list(ET.parse(ASSET).getroot().iter())
    display_elements = list(xml.iter())
    assert len(original_elements) == len(display_elements)
    changes = []
    for old, new in zip(original_elements, display_elements):
        assert old.tag == new.tag
        keys = set(old.attrib) | set(new.attrib)
        for key in keys:
            if old.get(key) != new.get(key):
                assert (old.tag, key) in [('geom', 'rgba'), ('mesh', 'file'), ('compiler', 'meshdir')]
                changes.append(dict(tag=old.tag, name=old.get('name'), field=key,
                                    before=old.get(key), after=new.get(key)))
    save(args.out / 'attempt.json', dict(renderer='Isaac Gym native camera',
         physics_steps_requested=0, human_loaded=False, source_asset=str(ASSET),
         mesh_declarations=len(meshes), input_sha256=pins, cameras=CAMERAS,
         display_changes=changes, gravity_enabled=True, guitar_root_free=True,
         scope='Static geometry inspection; no integration, contact, stability, or performance test.'))
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams()
    params.up_axis = gymapi.UP_AXIS_Z
    params.gravity = gymapi.Vec3(0., 0., -9.81)
    params.dt = 1. / 240.
    params.use_gpu_pipeline = False
    params.physx.use_gpu = False
    params.physx.num_threads = 2
    sim = gym.create_sim(0, 0, gymapi.SIM_PHYSX, params)
    if sim is None:
        raise RuntimeError('Isaac Gym simulation/graphics creation failed')
    try:
        options = gymapi.AssetOptions()
        options.fix_base_link = False
        options.disable_gravity = False
        options.collapse_fixed_joints = False
        asset = gym.load_asset(sim, str(display.parent), display.name, options)
        if asset is None:
            raise RuntimeError('Native asset load failed')
        env = gym.create_env(sim, gymapi.Vec3(-1., -1., -1.), gymapi.Vec3(1., 1., 1.), 1)
        actor = gym.create_actor(env, asset, gymapi.Transform(), 'guitar', 0, 0)
        gym.set_light_parameters(sim, 0, gymapi.Vec3(.85, .85, .85),
                                 gymapi.Vec3(.5, .5, .5), gymapi.Vec3(.4, -.5, -1.))
        gym.set_light_parameters(sim, 1, gymapi.Vec3(.3, .3, .3),
                                 gymapi.Vec3(.15, .15, .15), gymapi.Vec3(-.6, .2, -1.))
        handles = {}
        for name, config in CAMERAS.items():
            props = gymapi.CameraProperties()
            props.width, props.height = config['size']
            props.horizontal_fov = config['fov']
            camera = gym.create_camera_sensor(env, props)
            if camera < 0:
                raise RuntimeError('Native camera creation failed: ' + name)
            gym.set_camera_location(camera, env, gymapi.Vec3(*config['eye']),
                                    gymapi.Vec3(*config['target']))
            handles[name] = camera
        gym.prepare_sim(sim)
        names = list(gym.get_actor_rigid_body_names(env, actor))
        states = gym.get_actor_rigid_body_states(env, actor, gymapi.STATE_ALL).copy()
        positions = {name: [float(states['pose']['p'][i][axis]) for axis in 'xyz']
                     for i, name in enumerate(names)}
        errors = {}
        for name in ['G:nut'] + ['G:fret%d' % n for n in range(1, 23)] + [
                'G:string%d%s' % (n, suffix) for n in range(1, 7) for suffix in ('', '_end')]:
            expected = np.array([float(x) for x in source_bodies[name].get('pos').split()])
            errors[name] = float(np.max(np.abs(np.array(positions[name]) - expected)))
        assert max(errors.values()) < 1e-6, errors
        gym.step_graphics(sim)
        gym.render_all_camera_sensors(sim)
        cameras = {}
        for name, camera in handles.items():
            path = args.out / (name + '_raw.png')
            gym.write_camera_image_to_file(sim, env, camera, gymapi.IMAGE_COLOR, str(path))
            assert path.is_file() and path.stat().st_size
            depth = gym.get_camera_image(sim, env, camera, gymapi.IMAGE_DEPTH)
            np.save(str(args.out / (name + '_depth.npy')), np.asarray(depth))
            cameras[name] = dict(CAMERAS[name],
                view=np.asarray(gym.get_camera_view_matrix(sim, env, camera)).tolist(),
                projection=np.asarray(gym.get_camera_proj_matrix(sim, env, camera)).tolist(),
                raw_image=str(path), sha256=sha(path))
        assert np.array_equal(states, gym.get_actor_rigid_body_states(env, actor, gymapi.STATE_ALL))
        assert all(sha(path) == expected for path, expected in pins.items())
        proxy = source_bodies['G:pluck_range']
        save(args.out / 'capture.json', dict(renderer='Isaac Gym native camera', physics_steps=0,
             cameras=cameras, body_positions_G_m=positions, marker_max_abs_error_m=max(errors.values()),
             marker_error_m=errors, input_sha256=pins, inputs_unchanged=True,
             display_asset_sha256=sha(display), colors_string_1_through_6=COLORS,
             pluck_proxy_center_G_m=[float(x) for x in proxy.get('pos').split()],
             pluck_proxy_half_size_m=[float(x) for x in proxy.find('geom').get('size').split()],
             original_geometry_preserved=True, zero_step_native_state_unchanged=True))
        print('Native camera capture complete; 35 source markers agree within 1 micrometre.', flush=True)
    finally:
        gym.destroy_sim(sim)


if __name__ == '__main__':
    main()
