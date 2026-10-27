"""Static source-mesh hand comparison rendered by native Isaac Gym cameras."""
from pathlib import Path
import importlib.util
import json
import xml.etree.ElementTree as ET

import isaacgym  # Import before NumPy/Torch.
from isaacgym import gymapi
import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
spec = importlib.util.spec_from_file_location('source_figures', HERE.parents[1]/'support/render_comparison.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


def save_obj(path, triangles):
    with path.open('w') as stream:
        for p in triangles.reshape(-1, 3):
            stream.write('v %.10g %.10g %.10g\n' % tuple(p))
        for i in range(len(triangles)):
            stream.write('f %d %d %d\n' % (3*i+1, 3*i+2, 3*i+3))


def save_asset(name, meshes):
    robot = ET.Element('robot', name=name)
    for i, (body, triangles) in enumerate(meshes.items()):
        local_name = body.replace(':', '_')
        filename = name+'_'+local_name+'.obj'
        save_obj(HERE/filename, triangles)
        link = ET.SubElement(robot, 'link', name=local_name)
        inertial = ET.SubElement(link, 'inertial')
        ET.SubElement(inertial, 'mass', value='.01')
        ET.SubElement(inertial, 'inertia', ixx='.00001', iyy='.00001', izz='.00001', ixy='0', ixz='0', iyz='0')
        visual = ET.SubElement(link, 'visual')
        ET.SubElement(ET.SubElement(visual, 'geometry'), 'mesh', filename=filename)
        material = ET.SubElement(visual, 'material', name='neutral')
        ET.SubElement(material, 'color', rgba='.72 .77 .82 1')
        if i:
            joint = ET.SubElement(robot, 'joint', name='fixed_'+local_name, type='fixed')
            ET.SubElement(joint, 'parent', link=next(iter(meshes)).replace(':', '_'))
            ET.SubElement(joint, 'child', link=local_name)
    ET.ElementTree(robot).write(str(HERE/(name+'.urdf')))
    return name+'.urdf'


def main():
    pad = source.load_fingertip_pad()
    meshes, poses, pins = source.read_geometry(pad)
    pins.update(pad['contract']['source_sha256'])
    prepared = source.load_prepared_reset_contract()
    names = prepared['initial']['human_body_names']
    props = prepared['initial']['human_properties']
    centers = np.array([poses['LH:'+f+'3']+props[names.index('LH:'+f+'3')]['COM_body_m']
                        for f in source.FINGERS])
    world_meshes = {name: tri+poses[name] for name, tri in meshes.items()}
    patch_meshes = {}
    for f in source.FINGERS:
        name = 'LH:'+f+'3'
        tri = source.clipped_patch(meshes[name])
        normals = np.cross(tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0])
        normals /= np.linalg.norm(normals, axis=1, keepdims=True)
        patch_meshes[name] = tri+poses[name]+normals[:, None]*.00015
    hand_file = save_asset('hand', world_meshes)
    pad_file = save_asset('pad', patch_meshes)
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams()
    params.up_axis = gymapi.UP_AXIS_Z
    params.gravity = gymapi.Vec3(0, 0, 0)
    params.use_gpu_pipeline = False
    params.physx.use_gpu = False
    params.physx.num_threads = 1
    sim = gym.create_sim(0, 0, gymapi.SIM_PHYSX, params)
    if sim is None:
        raise RuntimeError('Cannot create native Isaac Gym renderer')
    metadata = dict(renderer='Isaac Gym native camera, CPU PhysX scene, zero simulation steps',
                    pose='source-neutral fixed hand, palm-facing and oblique views',
                    source_sha256=pins, surface_offset_m=.00015, cameras={})
    try:
        hand_rotation = Rotation.from_euler('x', -90, degrees=True)
        hand_matrix = hand_rotation.as_matrix()
        hand_quat = gymapi.Quat(*hand_rotation.as_quat())
        options = gymapi.AssetOptions()
        options.fix_base_link = True
        options.disable_gravity = True
        options.collapse_fixed_joints = False
        options.use_mesh_materials = False
        hand = gym.load_asset(sim, str(HERE), hand_file, options)
        patch = gym.load_asset(sim, str(HERE), pad_file, options)
        if hand is None or patch is None:
            raise RuntimeError('Hand mesh asset loading failed')
        env = gym.create_env(sim, gymapi.Vec3(-1, -1, -1), gymapi.Vec3(1, 1, 1), 1)
        actors = []
        for mode in range(3):
            transform = gymapi.Transform(p=gymapi.Vec3(mode*.4, 0, 0), r=hand_quat)
            actor = gym.create_actor(env, hand, transform, 'hand_'+str(mode), 0, 1)
            actors.append(actor)
            for i, name in enumerate(gym.get_actor_rigid_body_names(env, actor)):
                selected = mode == 1 and any(name.startswith('LH_'+f) for f in source.FINGERS) and name[-1] in '23'
                color = (.93, .53, .11) if selected else (.72, .77, .82)
                gym.set_rigid_body_color(env, actor, i, gymapi.MESH_VISUAL, gymapi.Vec3(*color))
            if mode == 2:
                p = gym.create_actor(env, patch, transform, 'selected_pad', 0, 1)
                for i in range(gym.get_actor_rigid_body_count(env, p)):
                    gym.set_rigid_body_color(env, p, i, gymapi.MESH_VISUAL, gymapi.Vec3(.04, .67, .43))
        backdrop = gym.create_box(sim, 20, 20, .001, options)
        wall = gym.create_actor(env, backdrop, gymapi.Transform(p=gymapi.Vec3(.4, 5, .077), r=hand_quat), 'backdrop', 0, 1)
        gym.set_rigid_body_color(env, wall, 0, gymapi.MESH_VISUAL, gymapi.Vec3(1, 1, 1))
        gym.set_light_parameters(sim, 0, gymapi.Vec3(.45, .45, .45), gymapi.Vec3(.8, .8, .8), gymapi.Vec3(-.2, -1, -.4))
        cameras = []
        for view, angles in [('palm', (0, 0, 0)), ('oblique', (0, -24, 0))]:
            base = Rotation.from_euler('y', angles[1], degrees=True).as_matrix()
            for mode in range(3):
                target = np.array([mode*.4, 0, 0])+hand_matrix@np.array([-.025, -.077, -.003])
                position = target+hand_matrix@base@np.array([0, 0, -.39])
                forward = (target-position)/np.linalg.norm(target-position)
                right = np.cross(forward, np.array([0, 0, 1.]))
                right /= np.linalg.norm(right)
                up = np.cross(right, forward)
                rot = np.column_stack((right, up, -forward))
                cp = gymapi.CameraProperties()
                cp.width = cp.height = 1400
                cp.horizontal_fov = 35
                camera = gym.create_camera_sensor(env, cp)
                if camera < 0:
                    raise RuntimeError('Native camera creation failed')
                gym.set_camera_location(camera, env, gymapi.Vec3(*position), gymapi.Vec3(*target))
                cameras.append((view, mode, camera, rot, position))
        gym.prepare_sim(sim)
        gym.step_graphics(sim)
        gym.render_all_camera_sensors(sim)
        outputs = []
        for view, mode, camera, rot, position in cameras:
            rgba = np.asarray(gym.get_camera_image(sim, env, camera, gymapi.IMAGE_COLOR)).reshape(1400, 1400, 4)
            image = Image.fromarray(rgba[:, :, :3].copy())
            raw = HERE/('raw_'+view+'_'+str(mode)+'.png')
            image.save(raw)
            if mode == 0:
                # X-ray markers: exact projected internal COM, not surface points.
                projected = (centers@hand_matrix.T-position)@rot
                focal = 700/np.tan(np.deg2rad(35)/2)
                pixel = np.column_stack([700+focal*projected[:, 0]/(-projected[:, 2]),
                                         700-focal*projected[:, 1]/(-projected[:, 2])])
                draw = ImageDraw.Draw(image)
                for x, y in pixel:
                    draw.ellipse((x-13, y-13, x+13, y+13), fill=(45, 115, 225), outline='white', width=3)
                metadata['center_markers_'+view] = pixel.tolist()
            filename = source.FILES[mode]+'_'+view+'.png'
            image.save(OUT/filename)
            outputs.append(filename)
            metadata['cameras'][view+'_'+str(mode)] = dict(position=position.tolist(), rotation=rot.tolist(), fov=35, size=[1400, 1400])
        for view in ('palm', 'oblique'):
            combined = Image.new('RGB', (4200, 1400), 'white')
            for mode in range(3):
                combined.paste(Image.open(OUT/(source.FILES[mode]+'_'+view+'.png')), (mode*1400, 0))
            combined.save(OUT/('comparison_'+view+'.png'))
        assert all(source.digest(p) == value for p, value in pins.items())
        metadata['outputs'] = outputs
        (HERE/'manifest.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
        print(json.dumps(dict(outputs=outputs, renderer=metadata['renderer'])))
    finally:
        gym.destroy_sim(sim)


if __name__ == '__main__':
    main()
