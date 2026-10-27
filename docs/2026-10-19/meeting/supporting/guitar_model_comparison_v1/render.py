"""Render two original guitar assets together with an actual Isaac Gym camera."""
from isaacgym import gymapi
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
ROOT = MEETING.parents[2]
OUTPUT = MEETING / 'result/images/00_guitar_initial_and_current_native.png'
REPORT = HERE / 'capture.json'
assert not OUTPUT.exists() and not REPORT.exists(), 'Use a new version for another capture'
ASSETS = [ROOT / 'tab2body/assets/guitar_asset.xml',
          ROOT / 'stability_adapter_2/assets/om_body_geometry_v3/guitar_asset.xml']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

inputs = {Path(__file__).resolve()}
for path in ASSETS:
    xml = ET.parse(path).getroot()
    directory = path.parent / xml.find('compiler').get('meshdir', '.')
    inputs.add(path)
    inputs.update((directory / mesh.attrib['file']).resolve()
                  for mesh in xml.findall('./asset/mesh'))
before = {str(p): digest(p) for p in sorted(inputs)}
(HERE / 'inputs_before.json').write_text(json.dumps(before, indent=2) + '\n')

gym = gymapi.acquire_gym()
params = gymapi.SimParams()
params.up_axis = gymapi.UP_AXIS_Z
params.gravity = gymapi.Vec3(0, 0, -9.81)
params.use_gpu_pipeline = False
params.physx.use_gpu = False
params.physx.num_threads = 1
sim = gym.create_sim(0, 0, gymapi.SIM_PHYSX, params)
assert sim is not None, 'Native simulation/graphics creation failed'
try:
    env = gym.create_env(sim, gymapi.Vec3(-2, -2, 0), gymapi.Vec3(2, 2, 2), 1)
    gym.set_light_parameters(sim, 0, gymapi.Vec3(.85, .85, .85),
                             gymapi.Vec3(.4, .4, .4), gymapi.Vec3(-.3, -.6, -1))
    actors = []
    poses = []
    for i, path in enumerate(ASSETS):
        options = gymapi.AssetOptions()
        options.fix_base_link = True
        options.disable_gravity = True
        options.collapse_fixed_joints = False
        asset = gym.load_asset(sim, str(path.parent), path.name, options)
        assert asset is not None
        pose = gymapi.Transform()
        pose.p = gymapi.Vec3(-.4 if i == 0 else .4, 0, .95)
        pose.r = gymapi.Quat.from_axis_angle(gymapi.Vec3(1, 0, 0), math.pi / 2)
        actor = gym.create_actor(env, asset, pose, ['initial', 'current'][i], 0, 0, i + 1)
        assert actor >= 0
        actors.append(actor)
        poses.append({'side': ['left', 'right'][i], 'asset': str(path),
                      'scale': 1.0, 'position_m': [pose.p.x, pose.p.y, pose.p.z],
                      'quaternion_xyzw': [pose.r.x, pose.r.y, pose.r.z, pose.r.w],
                      'body_count': gym.get_actor_rigid_body_count(env, actor)})
    camera = gymapi.CameraProperties()
    camera.width, camera.height, camera.horizontal_fov = 1920, 1440, 36
    camera.use_collision_geometry = False
    handle = gym.create_camera_sensor(env, camera)
    assert handle >= 0
    eye, target = [0, -2.55, .8], [0, 0, .8]
    gym.set_camera_location(handle, env, gymapi.Vec3(*eye), gymapi.Vec3(*target))
    gym.prepare_sim(sim)
    gym.step_graphics(sim)
    gym.render_all_camera_sensors(sim)
    rgba = np.asarray(gym.get_camera_image(sim, env, handle, gymapi.IMAGE_COLOR))
    rgba = rgba.reshape(camera.height, camera.width, 4)
    segmentation = np.asarray(gym.get_camera_image(sim, env, handle,
                                                   gymapi.IMAGE_SEGMENTATION))
    segmentation = segmentation.reshape(camera.height, camera.width)
    visible = {}
    for i, actor in enumerate(actors):
        yy, xx = np.where(segmentation == i + 1)
        assert len(xx) > 1000, 'Both guitars must be visible in the same image'
        bounds = [int(xx.min()), int(yy.min()), int(xx.max()), int(yy.max())]
        assert bounds[0] > 4 and bounds[1] > 4
        assert bounds[2] < camera.width - 5 and bounds[3] < camera.height - 5
        visible[['left_initial', 'right_current'][i]] = {
            'pixels': int(len(xx)), 'bounds_xyxy': bounds}
    after = {str(p): digest(p) for p in sorted(inputs)}
    assert before == after, 'Source assets changed during rendering'
    Image.fromarray(rgba[:, :, :3], 'RGB').save(OUTPUT)
    with Image.open(OUTPUT) as check:
        check.verify()
    report = {'renderer': 'Isaac Gym native camera', 'physics_steps': 0,
              'environment_count': 1, 'guitar_actor_count': len(actors),
              'display_only_fixed_base': True, 'original_assets_unchanged': before == after,
              'poses': poses, 'camera': {'eye_m': eye, 'target_m': target,
              'width': camera.width, 'height': camera.height,
              'horizontal_fov_deg': camera.horizontal_fov, 'collision_geometry': False},
              'visibility': visible, 'input_sha256': before,
              'output': str(OUTPUT), 'output_sha256': digest(OUTPUT),
              'scope': 'Static shape comparison; no support, playing, or stability test',
              'native_import_warnings': 'See native.log; no substitute geometry or image compositing'}
    REPORT.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'saved': str(OUTPUT), 'visibility': visible}), flush=True)
finally:
    gym.destroy_sim(sim)
