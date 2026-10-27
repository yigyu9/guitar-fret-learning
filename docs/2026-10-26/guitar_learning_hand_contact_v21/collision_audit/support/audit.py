"""Finite source-convex audit; this does not simulate or certify cooked contacts."""
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

os.environ['MUJOCO_GL'] = 'osmesa'
os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
import numpy as np
from guitar_learning.gpu.hand_collision import (
    SEGMENT_FINGER, left_hand_collision_properties, verify_external_filter_preservation)
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.initial_pose_video60_v1.static_visual_v7 import build_model, set_body_poses

OUT = Path(__file__).resolve().parents[1]
HELPER = ROOT/'docs/2026-10-26/시각화/생성자료/render_finger_preparation_candidates_v1.py'
OLD = ROOT/'docs/2026-10-25/guitar_learning_v20_A500/evaluation_repeat1'
B = ROOT/'docs/2026-10-26/시각화/standby_B_native_v1/native_run'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pose_state(rows, names):
    state = {actor+'_body_states': [] for actor in ('human', 'guitar', 'chair')}
    for name, row in zip(names, rows):
        state[name.split('/')[0]+'_body_states'].append(dict(pose=dict(
            p=dict(zip('xyz', row[:3].tolist())), r=dict(zip('xyzw', row[3:7].tolist())))))
    return state


def main():
    prepared = load_prepared_reset_contract()
    initial = prepared['initial']
    before = initial['actual_shape_properties']['human']
    after, contract = left_hand_collision_properties(before)
    manifest = ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json'
    guitar = json.loads(manifest.read_text())['shape_properties']
    verify_external_filter_preservation(before, after, [0]+[r['filter'] for r in guitar])
    pairs = []
    shapes = [(n, i, r) for n, rs in before.items() for i, r in enumerate(rs)]
    for (a, ai, av), (b, bi, bv) in itertools.combinations(shapes, 2):
        pairs.append(dict(body_a=a, shape_a=ai, body_b=b, shape_b=bi,
            before_enabled=(av['filter'] & bv['filter']) == 0,
            after_enabled=(after[a][ai]['filter'] & after[b][bi]['filter']) == 0))
    (OUT/'filter_matrix.json').write_text(json.dumps(dict(contract=contract,
        before=before, after=after, human_pairs=pairs,
        actual_external_filters=sorted(set([0]+[r['filter'] for r in guitar]))), indent=2)+'\n')
    spec = importlib.util.spec_from_file_location('frozen_static_helper', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    bodies = {b.get('name'): b for b in ET.parse(initial['loaded_assets'][0]['path']).findall('.//body')}
    model, data, mapping, _ = build_model(initial)
    names = (['human/'+n for n in initial['human_body_names']] +
             ['guitar/'+n for n in initial['guitar_body_names']] + ['chair/box'])
    old = np.load(OLD/'poses_env0000.npz')
    native_b = np.load(B/'physics.npz')
    b_state, _, _ = helper.changed_state(prepared, bodies, helper.CANDIDATES['B'])
    states = dict(prepared035=prepared['state'], static_B=b_state,
                  native_B_final=pose_state(native_b['body_state'][-1], names),
                  A500_original_final=pose_state(old['body_state'][-1], names))
    geometry = {}
    for label, state in states.items():
        readback = set_body_poses(model, data, mapping, state)
        rows = helper.separation_check(model, data)
        physical = [row for row in rows if all(
            name.split('/', 1)[-1] in SEGMENT_FINGER for name in row['bodies'])]
        assert len(physical) == 90
        geometry[label] = dict(static_pose_readback=readback, pairs=physical,
            source_convex_intersections_over_1um=[r for r in physical if r['overlap_over_1um']])
    pins = [Path(__file__).resolve(), HELPER, manifest, OLD/'poses_env0000.npz',
            B/'physics.npz', ROOT/'guitar_learning/gpu/hand_collision.py']
    result = dict(schema='guitar_learning.hand_collision_source_geometry.v1',
        contract=contract, geometry=geometry,
        limitations=['Source convex intersection inradius is not PhysX cooked penetration depth.',
            'Static source geometry is not native body-pair force evidence.',
            'B native final is an existing collision-disabled direct-target test, not this new physics.'],
        fingerprints={str(p): sha(p) for p in pins})
    (OUT/'geometry.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key: value['source_convex_intersections_over_1um']
                      for key, value in geometry.items()}, indent=2))


if __name__ == '__main__':
    main()
