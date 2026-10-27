"""CPU fixtures only: first-attempt/failure, bounded capture, point J and output guard."""
import ast
import builtins
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock

import numpy as np
import torch

import probe
from protocol import (HERE, ROOT, BASELINE, ENVIRONMENTS, ENDPOINTS, CONTROLS,
                      BYTE_LIMIT, PHYSICS, CONTROL, Trace, condition, failure_latch)
from guitar_learning.tool.validation.thumb_contact_probe import point_jacobian
from guitar_learning.gpu.fingertip_pad import pad_target_geometry
from guitar_learning.tool.experiments.short_finger_learning import runner


def main():
    assert not torch.cuda.is_initialized()
    checks = {}
    # A physical or wrist failure labels its own endpoint; clears only outside first attempt.
    previous = np.array([False, False, False])
    first = np.array([True, True, True])
    previous = failure_latch(first, previous, np.array([True, False, False]), np.array([False, True, False]))
    np.testing.assert_array_equal(previous, [True, True, False])
    previous = failure_latch(first, previous, np.zeros(3, bool), np.zeros(3, bool))
    np.testing.assert_array_equal(previous, [True, True, False])
    np.testing.assert_array_equal(failure_latch(np.zeros(3, bool), previous, previous, previous), [False]*3)
    checks['failure_endpoint_and_following_latched_first_attempt'] = True
    schema = {'first_attempt': ('?', ()), 'clock': ('i4', ()), 'vector': ('f4', (3,))}
    trace = Trace(schema, 2)
    live = np.ones(ENVIRONMENTS, bool); live[1] = False
    row = dict(first_attempt=live, clock=np.ones(ENVIRONMENTS, int), vector=np.ones((ENVIRONMENTS, 3)))
    trace.append(row)
    assert trace.values()['clock'][0, 1] == 0 and not trace.values()['vector'][0, 1].any()
    trace.append(row)
    try: trace.append(row)
    except ValueError: pass
    else: raise AssertionError('Endpoint cap not enforced')
    try: Trace(schema, 1).append({**row, 'vector': np.full((ENVIRONMENTS, 3), np.nan)})
    except ValueError: pass
    else: raise AssertionError('Nonfinite capture accepted')
    physics, control = Trace(PHYSICS, ENDPOINTS), Trace(CONTROL, CONTROLS)
    assert physics.nbytes+control.nbytes < BYTE_LIMIT-1_000_000
    selected_bytes = physics.nbytes+control.nbytes
    del physics, control
    checks['first_attempt_only_zero_mask_finite_and_endpoint_cap'] = True
    # Independent central finite differences at COM plus rotated body-fixed point.
    linear = np.arange(24, dtype=float).reshape(3, 8)/31-.3
    angular = np.arange(24, 48, dtype=float).reshape(3, 8)/37-.8
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    local, com = np.array([.02, -.03, .01]), np.array([.004, .005, -.002])
    offset = rotation@(local-com)
    native = torch.tensor(np.r_[linear, angular][None], dtype=torch.float64)
    actual = point_jacobian(native, torch.tensor(offset[None], dtype=torch.float64))[0].numpy()
    def point(q):
        omega = angular@q
        angle = np.linalg.norm(omega)
        skew = np.array([[0., -omega[2], omega[1]], [omega[2], 0., -omega[0]], [-omega[1], omega[0], 0.]])
        rotate = np.eye(3)+skew*(np.sin(angle)/angle if angle else 1)+(skew@skew)*((1-np.cos(angle))/angle**2 if angle else .5)
        return linear@q+rotate@offset
    epsilon = 1e-6
    finite = np.column_stack([(point(np.eye(8)[i]*epsilon)-point(-np.eye(8)[i]*epsilon))/(2*epsilon) for i in range(8)])
    np.testing.assert_allclose(actual, finite, rtol=0, atol=1e-10)
    qd = np.arange(8)/13-.2
    measured = linear@qd+np.cross(angular@qd, offset)
    np.testing.assert_allclose(actual@qd, measured, atol=1e-12, rtol=0)
    checks['original_point_J_COM_offset_finite_difference_and_velocity'] = True
    # Closest point faces away; another sample witnesses the original positive gate.
    starts = torch.zeros(1, 6, 3, dtype=torch.float64)
    ends = starts.clone(); ends[:, :, 1] = 1
    points = torch.zeros(1, 4, 2, 3, dtype=torch.float64); points[..., 1] = .5
    points[:, :, 1, 0] = .001
    normals = torch.zeros_like(points); normals[:, :, 0, 2] = 1; normals[:, :, 1, 2] = -1
    plane = torch.tensor([0., 0., 1., 0.], dtype=torch.float64)
    any_point = pad_target_geometry(points, normals, torch.zeros_like(points), torch.ones(4, 2, dtype=torch.bool),
        starts, ends, torch.zeros(1, 1, dtype=torch.float64), torch.ones(1, 1, dtype=torch.float64),
        torch.tensor([0]), torch.tensor([2]), torch.ones(1, 4, dtype=torch.bool), plane)
    env = SimpleNamespace(guitar_q=torch.tensor([[0., 0., 0., 1.]], dtype=torch.float64),
        guitar_body=torch.zeros(1, 13, dtype=torch.float64), starts=starts, ends=ends,
        frets=torch.tensor([[[0., 0., 0.], [0., 1., 0.]]], dtype=torch.float64),
        press_plane=plane, selected_index=0, fret=torch.tensor([1]), string=torch.tensor([0]),
        finger=torch.tensor([2]), loaded=torch.ones(1, 4, dtype=torch.bool), pad_indices=torch.arange(4))
    nearest = probe.nearest_geometry(env, points[:, 1, 0], normals[:, 1, 0])
    assert bool(any_point['positive'][0, 0]) and bool(nearest['position_geometry'][0, 0])
    assert not bool(nearest['facing_geometry'][0, 0]) and not bool(nearest['positive'][0, 0])
    checks['nearest_geometry_distinguished_from_any_sample_positive'] = True
    original_import = builtins.__import__
    def no_native(name, *args, **kwargs):
        if name == 'isaacgym' or name.startswith('isaacgym.'):
            raise AssertionError('Existing out reached native import')
        return original_import(name, *args, **kwargs)
    with tempfile.TemporaryDirectory(dir=str(HERE), prefix='cpu-existing-') as temp:
        out = Path(temp)
        for name in ('report.json', 'evaluation.json', 'physics240.npz', 'load_probe_report.json'):
            (out/name).write_bytes(b'original\x00\xff')
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        with mock.patch.object(sys, 'argv', ['probe', '--checkpoint', str(BASELINE/'train/initial.pt'), '--control', 'zero', '--out', str(out)]), \
                mock.patch.object(builtins, '__import__', side_effect=no_native), mock.patch.object(runner, 'run') as base:
            try: probe.main()
            except FileExistsError: pass
            else: raise AssertionError('Existing out accepted')
            base.assert_not_called()
        assert before == {p.name: p.read_bytes() for p in out.iterdir()}
        identity = (out.stat().st_dev, out.stat().st_ino)
        assert probe.owned(out, identity) and not probe.owned(out, None)
        assert not probe.owned(out, (identity[0], identity[1]+1))
    checks['existing_output_bytes_preserved_before_native_and_base'] = True
    for filename, mode in [('initial.pt', 'zero'), ('initial.pt', 'reference'), ('evaluation_000050.pt', 'policy'), ('final.pt', 'policy')]:
        condition(BASELINE/'train'/filename, mode)
    try: condition(BASELINE/'train/initial.pt', 'policy')
    except ValueError: pass
    else: raise AssertionError('Unassigned condition accepted')
    model = torch.nn.Linear(3, 2)
    before = probe.rng_hash()
    assert probe.model_hash(model) == probe.model_hash(model) and probe.rng_hash() == before
    checks['four_fixed_conditions_and_model_hash_RNG_neutral'] = True
    for name in ('probe.py', 'protocol.py', 'self_test.py', 'prepare.py'):
        ast.parse((HERE/name).read_text())
    source = ast.parse((HERE/'probe.py').read_text())
    # Execute the real nested constructor against a fake parent. Bad task metadata
    # must be rejected before parent/native construction, so there is no scene to leak.
    observed = next(n for n in ast.walk(source) if isinstance(n, ast.ClassDef) and n.name == 'ObservedPool')
    constructed = []
    class Parent:
        def __init__(self, *args):
            constructed.append(True)
            raise AssertionError('Rejected task reached native pool construction')
    namespace = dict(original_pool=Parent, ENVIRONMENTS=ENVIRONMENTS, CONTROLS=CONTROLS)
    exec(compile(ast.Module(body=[observed], type_ignores=[]), str(HERE/'probe.py'), 'exec'), namespace)
    valid = dict(num_envs=128, song=dict(short_learning=dict(view=dict(duration_ticks=218), mode='incremental', finger=2)))
    for bad in ({**valid, 'num_envs': 1}, {**valid, 'song': dict(short_learning={**valid['song']['short_learning'], 'ablation': {}})}):
        try: namespace['ObservedPool'](bad, None)
        except ValueError: pass
        else: raise AssertionError('Rejected metadata accepted')
    assert not constructed
    checks['invalid_task_rejected_before_native_pool_construction'] = True
    forbidden = {'act', 'sample', 'rsample', 'manual_seed', 'load_state_dict', 'targets', 'efforts', 'copy_', 'zero_'}
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in forbidden for n in ast.walk(source))
    assert 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    assert ROOT == Path('/home/ajou/yigyu/3')
    result = dict(completed=True, GPU_used=False, checks=checks, physics_and_control_max_uncompressed_bytes=selected_bytes,
        point_J_max_finite_difference_error=float(np.abs(actual-finite).max()),
        source_syntax_valid=True, scope='Synthetic CPU geometry/velocity fixtures and observation guards, not native load evidence')
    probe.write(HERE/'cpu_verification.json', result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
