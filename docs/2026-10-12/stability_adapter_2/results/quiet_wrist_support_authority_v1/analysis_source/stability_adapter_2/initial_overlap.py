"""Static source-shape distances at native Gym poses; no PhysX clearance gate."""
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import numpy as np


def build_probe(scene, include_ground=False):
    """Flatten active source geoms at native body poses, preserving geom offsets."""
    root = ET.Element('mujoco')
    ET.SubElement(root, 'compiler', angle='degree')
    assets, world = ET.SubElement(root, 'asset'), ET.SubElement(root, 'worldbody')
    shapes = []
    excluded = {'LH:thumb_pad', 'G:thumb_support_proxy', 'G:pluck_range'}
    geometry_fields = {'type', 'size', 'pos', 'quat', 'euler', 'axisangle', 'xyaxes', 'zaxis', 'fromto', 'mesh'}
    for actor_name, actor, key in [('human', scene.human, 'humanoid_asset'),
                                   ('guitar', scene.guitar, 'guitar_asset')]:
        path = Path(__file__).resolve().parents[1] / scene.config[key]
        source = ET.parse(path).getroot()
        meshdir = path.parent / source.find('compiler').get('meshdir', '')
        for mesh in source.findall('./asset/mesh'):
            fields = dict(mesh.attrib)
            fields['name'] = actor_name + '/' + fields['name']
            fields['file'] = str((meshdir / fields['file']).resolve())
            ET.SubElement(assets, 'mesh', fields)
        names = list(scene.gym.get_actor_rigid_body_names(scene.env, actor))
        states = scene.bodies(actor)
        for body in source.findall('./worldbody//body'):
            name = body.get('name')
            if name in excluded:
                continue
            geoms = [g for g in body.findall('geom') if g.get('contype') != '0' and g.get('conaffinity') != '0']
            if not geoms:
                continue
            state = states[names.index(name)]
            p, q = state['pose']['p'], state['pose']['r']
            node = ET.SubElement(world, 'body', name=actor_name + '/' + name,
                pos=' '.join(str(float(p[a])) for a in ('x', 'y', 'z')),
                quat=' '.join(str(float(q[a])) for a in ('w', 'x', 'y', 'z')))
            for geom in geoms:
                fields = {k:v for k,v in geom.attrib.items() if k in geometry_fields}
                if 'mesh' in fields:
                    fields['mesh'] = actor_name + '/' + fields['mesh']
                geom_name = 'shape_' + str(len(shapes))
                ET.SubElement(node, 'geom', fields, name=geom_name)
                shapes.append({'actor': actor_name, 'body': name, 'geom_name': geom_name})
    if include_ground:
        ET.SubElement(world, 'geom', name='ground_plane', type='plane', size='3 3 .1')
        shapes.append({'actor':'ground', 'body':'ground', 'geom_name':'ground_plane'})
    model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding='unicode'))
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    for shape in shapes:
        shape['geom_id'] = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, shape['geom_name'])
    return model, data, shapes


def query_pairs(model, data, shapes, distance_limit=.02):
    """Backend signed gaps, not penetration depths; farther pairs are truncated."""
    human = [s for s in shapes if s['actor'] == 'human']
    guitar = [s for s in shapes if s['actor'] == 'guitar']
    pairs = []
    for h in human:
        for g in guitar:
            points = np.zeros(6)
            gap = mujoco.mj_geomDistance(model, data, h['geom_id'], g['geom_id'], distance_limit, points)
            if not np.isfinite(gap) or not np.isfinite(points).all():
                raise FloatingPointError('nonfinite source geometry distance')
            if gap < distance_limit:
                pairs.append({'human_body':h['body'], 'guitar_body':g['body'],
                    'human_geom_id':h['geom_id'], 'guitar_geom_id':g['geom_id'],
                    'signed_gap_m':float(gap), 'witness_points_m':points.reshape(2, 3).tolist()})
    pairs.sort(key=lambda p:p['signed_gap_m'])
    return {'shape_count':{'human':len(human), 'guitar':len(guitar)},
        'pair_count':len(human)*len(guitar), 'distance_limit_m':distance_limit,
        'negative_gap_pair_count':sum(p['signed_gap_m'] < -1e-7 for p in pairs),
        'numerical_sign_epsilon_m':1e-7,
        'gap_semantics':'MuJoCo query output; negative magnitude is not calibrated physical penetration depth',
        'pairs_within_limit':pairs}


def query_ground(model, data, shapes, distance_limit=.05):
    """Source human/guitar vs the native scene's z=0 plane; no cooked clearance gate."""
    ground = next(s for s in shapes if s['actor']=='ground')
    pairs, gaps = [], []
    for shape in shapes:
        if shape['actor']=='ground':
            continue
        points = np.zeros(6)
        gap = mujoco.mj_geomDistance(model,data,shape['geom_id'],ground['geom_id'],distance_limit,points)
        if not np.isfinite(gap) or not np.isfinite(points).all():
            raise FloatingPointError('nonfinite source ground distance')
        gaps.append(float(gap))
        if gap < distance_limit:
            pairs.append({'actor':shape['actor'],'body':shape['body'],'geom_id':shape['geom_id'],
                'signed_gap_m':float(gap),'witness_points_m':points.reshape(2,3).tolist()})
    pairs.sort(key=lambda p:p['signed_gap_m'])
    return {'pair_count':len(gaps),'distance_limit_m':distance_limit,
        'minimum_gap_m':min(gaps),'negative_gap_pair_count':sum(g < -1e-7 for g in gaps),
        'gap_semantics':'source geometry vs z=0 plane; gaps >= cutoff are truncated; no native cooked clearance certification',
        'pairs_within_limit':pairs}
