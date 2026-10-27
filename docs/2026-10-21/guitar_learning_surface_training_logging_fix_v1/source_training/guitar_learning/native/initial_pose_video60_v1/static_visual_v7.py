"""Flatten original visible source geometry at exact recorded world body poses."""
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from .replay_v6 import pose_difference
from ..paths import resolve_input_path


def asset_paths(xml):
    xml = resolve_input_path(xml)
    tree = ET.parse(xml)
    compiler = tree.find('compiler')
    folder = Path(xml).parent / (compiler.get('meshdir', '') if compiler is not None else '')
    return {Path(xml).resolve()} | {(folder / mesh.attrib['file']).resolve() for mesh in tree.findall('./asset/mesh')}


def pose_values(state):
    pose = state['pose']
    p = [pose['p'][key] for key in 'xyz']
    q = [pose['r'][key] for key in 'wxyz']
    norm = math.sqrt(sum(v * v for v in q))
    if not norm or not all(math.isfinite(v) for v in p + q):
        raise ValueError('finite saved pose and nonzero quaternion required')
    return p, [v / norm for v in q]


def build_model(initial):
    import mujoco
    root = ET.Element('mujoco')
    ET.SubElement(root, 'compiler', angle='degree', fusestatic='false')
    ET.SubElement(root, 'option', gravity='0 0 0')
    visual = ET.SubElement(root, 'visual')
    ET.SubElement(visual, 'global', offwidth='1280', offheight='720')
    assets, world = ET.SubElement(root, 'asset'), ET.SubElement(root, 'worldbody')
    ET.SubElement(world, 'light', pos='0 2 3', dir='0 -1 -2', diffuse='.8 .8 .8')
    ET.SubElement(world, 'geom', name='floor', type='plane', size='3 3 .1', rgba='.8 .83 .85 1')
    # Camera x points screen-right, z points backwards from the target.
    dy, dz = 3.1, .08
    norm = math.hypot(dy, dz)
    fovy = math.degrees(2 * math.atan(math.tan(math.radians(55 / 2)) * 720 / 1280))
    ET.SubElement(world, 'camera', name='front', pos='0 3.1 .8', xyaxes='-1 0 0 0 %s %s' % (-dz / norm, dy / norm), fovy=str(fovy))
    mapping = []
    fields = {'type', 'size', 'pos', 'quat', 'euler', 'axisangle', 'xyaxes', 'zaxis', 'fromto', 'mesh'}
    for actor, names_key, asset in zip(('human', 'guitar'), ('human_body_names', 'guitar_body_names'), initial['loaded_assets']):
        path = resolve_input_path(asset['path'])
        source = ET.parse(path)
        compiler = source.find('compiler')
        meshdir = path.parent / (compiler.get('meshdir', '') if compiler is not None else '')
        for mesh in source.findall('./asset/mesh'):
            attributes = dict(mesh.attrib)
            attributes['name'] = actor + '/' + attributes['name']
            attributes['file'] = str((meshdir / attributes['file']).resolve())
            ET.SubElement(assets, 'mesh', attributes)
        sources = {body.get('name'): body for body in source.findall('./worldbody//body')}
        for index, name in enumerate(initial[names_key]):
            node = ET.SubElement(world, 'body', name=actor + '/' + name)
            mapping.append((actor, index, actor + '/' + name))
            geoms = list(sources[name].findall('geom')) if name in sources else []
            visible = [geom for geom in geoms if float(geom.get('rgba', '.65 .65 .65 1').split()[-1]) > 0]
            grouped = [geom for geom in visible if geom.get('group') == '1']
            # Group-1 explicit visual meshes take precedence over duplicate collision meshes.
            for geom in grouped or visible:
                attributes = {key: value for key, value in geom.attrib.items() if key in fields}
                if 'mesh' in attributes:
                    attributes['mesh'] = actor + '/' + attributes['mesh']
                color = '.12 .65 .3 1' if actor == 'human' and name.startswith('LH:') else '.8 .12 .5 1' if actor == 'human' and name.startswith('RH:') else '.65 .65 .65 1'
                ET.SubElement(node, 'geom', attributes, rgba=color, contype='0', conaffinity='0')
    chair = ET.SubElement(world, 'body', name='chair')
    ET.SubElement(chair, 'geom', type='box', size=' '.join(map(str, initial['chair_initial_placement']['half_m'])), rgba='.38 .4 .42 1', contype='0', conaffinity='0')
    mapping.append(('chair', 0, 'chair'))
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    data = mujoco.MjData(model)
    mapping = [(actor, index, mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, name), name) for actor, index, name in mapping]
    return model, data, mapping, ET.tostring(root, encoding='unicode')


def set_body_poses(model, data, mapping, state):
    import mujoco
    for actor, index, body_id, name in mapping:
        position, quaternion = pose_values(state[actor + '_body_states'][index])
        model.body_pos[body_id] = position
        model.body_quat[body_id] = quaternion
    mujoco.mj_kinematics(model, data)
    mujoco.mj_camlight(model, data)
    worst_position = worst_rotation = 0.
    for actor, index, body_id, name in mapping:
        native = {'p': dict(zip('xyz', data.xpos[body_id])), 'r': dict(zip('wxyz', data.xquat[body_id]))}
        position, rotation = pose_difference(state[actor + '_body_states'][index]['pose'], native)
        worst_position, worst_rotation = max(worst_position, position), max(worst_rotation, rotation)
    if worst_position > 1e-9 or worst_rotation > 1e-9 or data.time != 0:
        raise RuntimeError('Static source body transform readback mismatch')
    return {'max_position_error_m': worst_position, 'max_rotation_error_rad': worst_rotation, 'body_count': len(mapping), 'clock_s': float(data.time)}


def add_strings(scene, endpoints):
    import mujoco
    import numpy as np
    for start, end in endpoints:
        if scene.ngeom >= scene.maxgeom:
            raise RuntimeError('scene geom capacity insufficient')
        geom = scene.geoms[scene.ngeom]
        color = np.array([.92, .92, .92, 1.], dtype=np.float32)
        mujoco.mjv_initGeom(geom, mujoco.mjtGeom.mjGEOM_CAPSULE, np.ones(3), np.zeros(3), np.eye(3).reshape(-1), color)
        mujoco.mjv_connector(geom, mujoco.mjtGeom.mjGEOM_CAPSULE, .00065, start, end)
        scene.ngeom += 1
