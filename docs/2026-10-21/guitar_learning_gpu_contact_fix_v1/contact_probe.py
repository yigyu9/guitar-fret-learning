"""Saved-source runtime ablations; never alter production or prior evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
import types

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
p = argparse.ArgumentParser()
p.add_argument('--variant', choices=('baseline', 'no_human_guitar', 'no_human_chair', 'no_guitar_chair', 'no_human_self', 'pgs', 'aggregate', 'spacing_small', 'original_guitar_filter', 'original_guitar_properties', 'substeps4', 'no_hg_exact', 'no_left_hand_hg', 'no_right_hand_hg', 'no_guitar_body_hg', 'no_fret5_hg', 'no_all_frets_hg', 'frictionless_hg', 'friction_correlation_small', 'friction_offset_small', 'articulations'), required=True)
p.add_argument('--envs', type=int, required=True)
p.add_argument('--out', type=Path, required=True)
args = p.parse_args()
import isaacgym

path = ROOT / 'guitar_learning/gpu/scene.py'
original = path.read_text()
source = original
if args.variant == 'articulations':
    source = source.replace('params.physx.solver_type = 1', 'params.physx.solver_type = 1\n            params.physx.always_use_articulations = True')
elif args.variant == 'frictionless_hg':
    before = '                self.actors.append(handles)'
    code = '''                for actor in handles[:2]:
                    shapes = self.gym.get_actor_rigid_shape_properties(env, actor)
                    for prop in shapes:
                        prop.friction = prop.rolling_friction = prop.torsion_friction = 0.
                    assert self.gym.set_actor_rigid_shape_properties(env, actor, shapes) is not False
'''
    source = source.replace(before, code + before)
elif args.variant in ('friction_correlation_small','friction_offset_small'):
    field = 'friction_correlation_distance' if args.variant == 'friction_correlation_small' else 'friction_offset_threshold'
    value = '.001' if args.variant == 'friction_correlation_small' else '.0002'
    source = source.replace('params.physx.solver_type = 1', 'params.physx.solver_type = 1\n            params.physx.'+field+' = '+value)
elif args.variant in ('no_hg_exact','no_guitar_body_hg','no_left_hand_hg','no_right_hand_hg','no_fret5_hg','no_all_frets_hg'):
    before = '                self.actors.append(handles)'
    code = '''                human_shapes = self.gym.get_actor_rigid_shape_properties(env, handles[0])
                guitar_shapes = self.gym.get_actor_rigid_shape_properties(env, handles[1])
                if VARIANT in ('no_hg_exact','no_guitar_body_hg','no_fret5_hg','no_all_frets_hg'):
                    mask = 0
                    for prop in human_shapes:
                        mask |= prop.filter
                    spans = self.gym.get_actor_rigid_body_shape_indices(env, handles[1])
                    names = list(self.gym.get_actor_rigid_body_names(env, handles[1]))
                    for name, span in zip(names, spans):
                        if VARIANT == 'no_hg_exact' or (VARIANT == 'no_guitar_body_hg' and name == 'G:body') or (VARIANT == 'no_fret5_hg' and name == 'G:fret5') or (VARIANT == 'no_all_frets_hg' and name.startswith('G:fret')):
                            for j in range(span.start,span.start+span.count):
                                guitar_shapes[j].filter |= mask
                else:
                    prefix = 'LH:' if VARIANT == 'no_left_hand_hg' else 'RH:'
                    spans = self.gym.get_actor_rigid_body_shape_indices(env, handles[0])
                    names = list(self.gym.get_actor_rigid_body_names(env, handles[0]))
                    for name, span in zip(names, spans):
                        if name.startswith(prefix):
                            for j in range(span.start,span.start+span.count):
                                human_shapes[j].filter |= (1 << 25)
                    for prop in guitar_shapes:
                        prop.filter |= (1 << 25)
                    assert self.gym.set_actor_rigid_shape_properties(env, handles[0], human_shapes) is not False
                assert self.gym.set_actor_rigid_shape_properties(env, handles[1], guitar_shapes) is not False
'''.replace('VARIANT', repr(args.variant))
    assert source.count(before) == 1
    source = source.replace(before, code + before)
elif args.variant == 'original_guitar_filter':
    source = source.replace("-1 if kind == 'human' else 0", "-1 if kind == 'human' else 2 if kind == 'guitar' else 0")
elif args.variant.startswith('no_'):
    pairs = dict(no_human_guitar=(0, 1), no_human_chair=(0, 2), no_guitar_chair=(1, 2), no_human_self=(0,))
    indices = pairs[args.variant]
    before = '                self.actors.append(handles)'
    code = '''                for actor_index in INDICES:
                    actor = handles[actor_index]
                    shapes = self.gym.get_actor_rigid_shape_properties(env, actor)
                    for prop in shapes:
                        prop.filter |= (1 << 25)
                    assert self.gym.set_actor_rigid_shape_properties(env, actor, shapes) is not False
'''.replace('INDICES', repr(indices))
    assert source.count(before) == 1
    source = source.replace(before, code + before)
elif args.variant == 'original_guitar_properties':
    source = source.replace('                        _apply_body_properties(props, rows)', '''                        if kind == 'guitar':
                            for prop, row in zip(props, rows):
                                ratio = row['mass_kg'] / prop.mass
                                prop.mass = row['mass_kg']
                                for axis in 'xyz':
                                    for other in 'xyz':
                                        setattr(getattr(prop.inertia, axis), other, getattr(getattr(prop.inertia, axis), other) * ratio)
                        else:
                            _apply_body_properties(props, rows)''')
elif args.variant == 'substeps4':
    source = source.replace('params.dt, params.substeps = 1 / 240., 1', 'params.dt, params.substeps = 1 / 240., 4')
elif args.variant == 'pgs':
    source = source.replace('params.physx.solver_type = 1', 'params.physx.solver_type = 0')
elif args.variant == 'aggregate':
    source = source.replace('                handles = []', '''                self.gym.begin_aggregate(env, sum(self.gym.get_asset_rigid_body_count(a) for a in assets), sum(self.gym.get_asset_rigid_shape_count(a) for a in assets), True)
                handles = []''')
    source = source.replace('                self.actors.append(handles)', '                self.gym.end_aggregate(env)\n                self.actors.append(handles)')
elif args.variant == 'spacing_small':
    source = source.replace('gymapi.Vec3(-1.5, -1.5, 0)', 'gymapi.Vec3(-.5, -.5, 0)').replace('gymapi.Vec3(1.5, 1.5, 2.5)', 'gymapi.Vec3(.5, .5, 2.5)')
args.out.mkdir(parents=True, exist_ok=False)
(args.out / 'scene_source.py.txt').write_text(source)
module = types.ModuleType('guitar_learning.gpu.scene')
module.__file__, module.__package__ = str(path), 'guitar_learning.gpu'
exec(compile(source, str(args.out / 'scene_source.py.txt'), 'exec'), module.__dict__)
sys.modules[module.__name__] = module
probe = ROOT / 'docs/2026-10-20/guitar_learning_gpu_force_replay_v1/probe.py'
tape = ROOT / 'docs/2026-10-20/guitar_learning_gpu_force_replay_v1/reference_n1/tape.npz'
sys.argv = [str(probe), '--envs', str(args.envs), '--out', str(args.out / 'run'), '--tape', str(tape)]
try:
    runpy.run_path(str(probe), run_name='__main__')
finally:
    (args.out / 'variant.json').write_text(json.dumps(dict(variant=args.variant, num_envs=args.envs,
        production_unchanged=path.read_text() == original, production_sha256=hashlib.sha256(original.encode()).hexdigest(),
        runtime_source_sha256=hashlib.sha256(source.encode()).hexdigest(), helper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()), indent=2) + '\n')
