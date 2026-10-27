"""Identify native collision-shape order with inspection-only friction tags.

The tagged assets are never prepared or simulated. No production asset changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def tagged_source(source, destination):
    tree = ET.parse(source)
    compiler = tree.find('compiler')
    meshdir = source.parent/compiler.get('meshdir', '')
    for mesh in tree.findall('./asset/mesh'):
        mesh.set('file', os.path.relpath((meshdir/mesh.attrib['file']).resolve(), destination.parent))
    compiler.set('meshdir', '.')
    labels = []
    for body in tree.findall('./worldbody/body')[0].iter('body'):
        for local_index, geom in enumerate(body.findall('geom')):
            ordinal = len(labels)+1
            friction = geom.get('friction', '1 .005 .0001').split()
            friction[0] = format(ordinal*.001, '.17g')
            geom.set('friction', ' '.join(friction))
            labels.append(dict(ordinal=ordinal, tag=ordinal*.001, body=body.attrib['name'],
                local_geom_index=local_index, geom_name=geom.get('name'),
                identifier=body.attrib['name']+'#'+str(local_index)+':'+geom.get('name', ''),
                collision_enabled=geom.get('contype', '1') != '0'))
    tree.write(destination, encoding='utf-8', xml_declaration=True)
    return labels


def native_order(gym, sim, path, labels):
    from isaacgym import gymapi
    options = gymapi.AssetOptions()
    options.fix_base_link = options.disable_gravity = False
    options.override_com = options.override_inertia = True
    options.collapse_fixed_joints = False
    asset = gym.load_asset(sim, str(path.parent), path.name, options)
    if asset is None:
        raise RuntimeError('Tagged inspection asset failed to import: '+str(path))
    names = list(gym.get_asset_rigid_body_names(asset))
    spans = gym.get_asset_rigid_body_shape_indices(asset)
    properties = gym.get_asset_rigid_shape_properties(asset)
    rows = []
    for body, span in zip(names, spans):
        for local_index in range(span.count):
            index = span.start+local_index
            friction = float(properties[index].friction)
            ordinal = round(friction/.001)
            if ordinal < 1 or ordinal > len(labels) or abs(friction-ordinal*.001) > 1e-7:
                raise ValueError('Native importer did not retain unique friction tags: '+str(friction))
            label = labels[ordinal-1]
            rows.append(dict(native_index=index, native_body=body, local_shape_index=local_index,
                friction_readback=friction, source_ordinal=ordinal, identifier=label['identifier']))
    if len(rows) != len(properties) or len({r['native_index'] for r in rows}) != len(properties):
        raise ValueError('Native body spans do not partition the shape buffer')
    return dict(body_count=len(names), shape_count=len(properties), body_names=names,
        rows=rows, identifiers=[row['identifier'] for row in rows])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    import isaacgym  # Must precede modules that can import Torch.
    from isaacgym import gymapi
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.native.paths import resolve_input_path
    from compound_probe import flatten_asset
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    contract = load_prepared_reset_contract()
    source = resolve_input_path(contract['initial']['loaded_assets'][1]['path'])
    original, flat = args.out/'tagged_original.xml', args.out/'tagged_flat.xml'
    labels = tagged_source(source, original)
    geometry = flatten_asset(original, contract, flat)
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams()
    params.use_gpu_pipeline = params.physx.use_gpu = True
    sim = gym.create_sim(0, -1, gymapi.SIM_PHYSX, params)
    if sim is None:
        raise RuntimeError('Shape-inspection simulator creation failed')
    try:
        before = native_order(gym, sim, original, labels)
        after = native_order(gym, sim, flat, labels)
    finally:
        gym.destroy_sim(sim)
    expected = {row['identifier'] for row in labels if row['collision_enabled']}
    matched = (before['identifiers'] == after['identifiers'] and
        set(before['identifiers']) == expected and len(expected) == len(before['identifiers']) and
        before['body_count'] == len(contract['initial']['guitar_body_names']) and after['body_count'] == 1)
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = dict(completed=matched, identical_native_collision_shape_order=matched,
        scope='Unique friction tags identify source geoms through native import; asset inspection only; no actors, prepare_sim, simulate, or production writes',
        source=str(source), source_sha256=sha(source), helper_sha256=sha(Path(__file__)),
        flatten_helper_sha256=sha(Path(__file__).with_name('compound_probe.py')),
        tagged_original_sha256=sha(original), tagged_flat_sha256=sha(flat),
        geometry=geometry, source_geoms=labels, original=before, flat=after)
    write(args.out/'shape_order.json', report)
    print(json.dumps(dict(completed=matched, original_bodies=before['body_count'], flat_bodies=after['body_count'],
        original_shapes=before['shape_count'], flat_shapes=after['shape_count'])), flush=True)
    if not matched:
        raise RuntimeError('Native shape ordering/identity differs; see shape_order.json')


if __name__ == '__main__':
    main()
