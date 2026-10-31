"""Recorded native guitar contacts, frame semantics and source surface distances."""
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from ..initial_pose_video60_v1.replay_v6 import rows, sha, save, original_expected_inputs
from ..initial_pose_video60_v1.static_visual_v7 import asset_paths


def transform(pose, vector):
    import numpy as np
    from scipy.spatial.transform import Rotation
    return np.array([pose['p'][key] for key in 'xyz']) + Rotation.from_quat([pose['r'][key] for key in 'xyzw']).apply(vector)


def selected(path, steps):
    wanted = set(steps)
    result = {}
    for row in rows(path):
        if row['physics_step'] in wanted:
            result[row['physics_step']] = row
        if len(result) == len(wanted):
            return result
    raise ValueError('missing requested saved sample')


def source_meshes(xml):
    import trimesh
    import numpy as np
    tree = ET.parse(xml)
    folder = xml.parent / tree.find('compiler').get('meshdir', '')
    assets = {mesh.get('name'): mesh for mesh in tree.findall('./asset/mesh')}
    body = tree.find(".//body[@name='G:body']")
    result = {'visual': [], 'collision': []}
    for geom in body.findall('geom'):
        mesh = assets[geom.get('mesh')]
        shape = trimesh.load(folder / mesh.get('file'), force='mesh', process=False)
        shape.vertices *= np.fromstring(mesh.get('scale', '1 1 1'), sep=' ')
        # Current G:body source mesh geoms have no local transform; fail on future changes.
        assert not any(key in geom.attrib for key in ('pos', 'quat', 'euler', 'axisangle', 'fromto'))
        kind = 'visual' if geom.get('contype') == '0' else 'collision'
        result[kind].append(shape)
    return result


def nearest_distance(meshes, point):
    import numpy as np
    import trimesh
    # Exact triangle closest points, not a vertex-distance or convex-cooking proxy.
    return min(float(trimesh.proximity.closest_point_naive(mesh, np.asarray(point)[None])[1][0]) for mesh in meshes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import numpy as np
    run, out = args.run.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    initial = json.loads((run / 'initial_values.json').read_text())
    inputs = {Path(__file__).resolve(), Path(__file__).resolve().parents[1] / 'initial_pose_video60_v1/replay_v6.py', Path(__file__).resolve().parents[1] / 'initial_pose_video60_v1/static_visual_v7.py'}
    inputs.update(run / name for name in ('initial_values.json', 'native_properties.json', 'states240.json', 'contacts240.json', 'attempt.json', 'support_wrapper.json'))
    root = Path(__file__).resolve().parents[2]
    inputs.add(root / 'isaacgym/docs/api/python/struct_py.html')
    assets = set()
    for asset in initial['loaded_assets']:
        assets.update(asset_paths(Path(asset['path'])))
    inputs.update(assets)
    pins = {str(path): sha(path) for path in inputs}
    save(out / 'inputs_before.json', pins)
    expected = original_expected_inputs(run)
    assert all(expected[str(path.resolve())] == sha(path) for path in assets)
    props = json.loads((run / 'native_properties.json').read_text())
    com = {actor + '/' + row['name']: row['COM_body_m'] for actor, values in (('human', props['human']), ('guitar', props['guitar']['applied'])) for row in values}
    states = selected(run / 'states240.json', (4080, 6960))
    contacts = selected(run / 'contacts240.json', (4080, 6960))
    meshes = source_meshes(Path(initial['loaded_assets'][1]['path']))
    frames = []
    for step in (4080, 6960):
        state = states[step]['state']
        bodies = {actor + '/' + name: body for actor in ('human', 'guitar') for name, body in zip(initial[actor + '_body_names'], state[actor + '_body_states'])}
        evidence = []
        for raw in contacts[step]['contacts']:
            names = [raw['body0_name'], raw['body1_name']]
            if not any(name.startswith('guitar/') for name in names) or not any(name.startswith('human/') for name in names):
                continue
            world, com_world = [], []
            for i, name in enumerate(names):
                local = np.array([raw['localPos%d' % i][axis] for axis in 'xyz'])
                world.append(transform(bodies[name]['pose'], local))
                com_world.append(transform(bodies[name]['pose'], local + com[name]))
            gi = 0 if names[0].startswith('guitar/') else 1
            human, guitar = names[1 - gi], names[gi]
            item = {'human_body': human, 'guitar_body': guitar, 'guitar_point_W_m': world[gi].tolist(), 'human_point_W_m': world[1 - gi].tolist(), 'body_origin_witness_gap_m': float(np.linalg.norm(world[0] - world[1])), 'COM_hypothesis_witness_gap_m': float(np.linalg.norm(com_world[0] - com_world[1])), 'positive_lambda': raw['lambda'] > 0, 'raw_lambda': raw['lambda'], 'raw_contact': raw}
            if guitar == 'guitar/G:body':
                point = [raw['localPos%d' % gi][axis] for axis in 'xyz']
                item['source_visual_triangle_distance_m'] = nearest_distance(meshes['visual'], point)
                item['source_collision_triangle_distance_m'] = nearest_distance(meshes['collision'], point)
            evidence.append(item)
        frames.append({'physics_step': step, 'time_s': step / 240, 'raw_guitar_human_contact_count': len(evidence), 'positive_lambda_count': sum(item['positive_lambda'] for item in evidence), 'positive_lambda_human_bodies': sorted({item['human_body'] for item in evidence if item['positive_lambda']}), 'contacts': evidence})
    result = {'scope': 'Actual saved native contact feature points, excluding thickness; raw lambda positive is distinguished from zero candidates, never calibrated N. Source triangle distances are unsigned and do not certify PhysX cooked surface distance.', 'local_coordinate_conclusion': 'Body-origin frame: independently transformed pair features coincide; adding COM offsets creates centimetre-scale inconsistency.', 'source_geometry': {'G_body_visual_meshes': len(meshes['visual']), 'G_body_collision_meshes': len(meshes['collision']), 'invisible_proxy_policy': 'G:thumb_support_proxy and G:pluck_range are excluded from native active human-guitar policy; invisible source geometry is not an active contact proof'}, 'frames': frames, 'new_physics_steps': 0, 'inputs_unchanged': all(sha(path) == digest for path, digest in pins.items())}
    save(out / 'analysis.json', result)
    assert result['inputs_unchanged']
    print(json.dumps([{key: frame[key] for key in ('time_s', 'raw_guitar_human_contact_count', 'positive_lambda_count', 'positive_lambda_human_bodies')} for frame in frames], indent=2))


if __name__ == '__main__':
    main()
