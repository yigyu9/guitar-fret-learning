"""CPU-only arithmetic/hook fixtures; no simulator, policy rollout or GPU."""
import ast
import builtins
from itertools import product
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

import run_probe as driver
from projection import project, rounding_tolerance


def reference(raw, lower, upper, normal, beta):
    """Independent 3^4 active-set enumeration of the Euclidean QP."""
    clipped = np.clip(raw, lower, upper)
    if normal@clipped >= beta-1e-13:
        return clipped
    best, cost = None, float('inf')
    for state in product((-1, 0, 1), repeat=4):
        state = np.array(state)
        free = state == 0
        candidate = np.where(state < 0, lower, upper).copy()
        denominator = normal[free]@normal[free]
        if denominator:
            lam = (beta-normal[~free]@candidate[~free]-normal[free]@raw[free])/denominator
            if lam < -1e-11: continue
            candidate[free] = raw[free]+lam*normal[free]
        elif free.any():
            candidate[free] = raw[free]
        if (candidate < lower-1e-10).any() or (candidate > upper+1e-10).any() or normal@candidate < beta-1e-10:
            continue
        value = np.square(candidate-raw).sum()
        if value < cost: best, cost = candidate, value
    assert best is not None
    return best


class FakeController:
    def __init__(self):
        self.active = torch.arange(39, 78)
        self.target = torch.zeros(128, 105)
        self.lower, self.upper = torch.full((105,), -10.), torch.full((105,), 10.)
        self.action_low, self.action_high = torch.full((39,), -10.), torch.full((39,), 10.)
        self.rate = torch.full((105,), 4.)

    def targets(self, action, snapshot):
        self.target[:, 60:64] = (self.target[:, 60:64]+action[:, 21:25]*4/60).clamp(-10, 10)
        return self.target


class FakeBase:
    def __init__(self, settings, output):
        self.controller = FakeController()
        if settings == 'wrong_rate': self.controller.rate[60] = 3
        self.scene = SimpleNamespace(device=torch.device('cpu'), q=torch.zeros(128, 105),
            target=torch.zeros(128, 105), names=['native'+str(i) for i in range(105)], com=torch.zeros(3, 3))
        self.spec = dict(learned_action_indices=[21, 22, 23, 24],
            learned_action_names=self.scene.names[60:64], finger=2)
        self.environment = SimpleNamespace(clock=torch.zeros(128, dtype=torch.int64),
            failure=torch.zeros(128, 7, dtype=torch.bool), wrist_failure=torch.zeros(128, dtype=torch.bool),
            wrist_severe_failure=torch.zeros(128, dtype=torch.bool), guitar_index=2,
            pad_indices=[0, 1, 0, 0], press_plane=torch.tensor([0., 0., 1., 0.]))
        body = torch.zeros(128, 3, 13); body[:, :, 6] = 1
        force = torch.zeros(128, 3, 3); force[:, 1, 2] = 1
        jacobian = torch.zeros(128, 2, 6, 105); jacobian[:, 0, 2, 60:64] = torch.tensor([1., .5, -.25, .1])
        self.snapshot = dict(body_state=body, contact_force=force, q=self.scene.q,
            qd=torch.zeros_like(self.scene.q), jacobian=jacobian,
            reset_body_snapshot=torch.ones(128, dtype=torch.bool))
        self.last_wrist_feedback = dict(requested_arm_rad=torch.zeros(128, 12), pose_error_world=torch.zeros(128, 6))
        self.closed = 0

    def step(self, action):
        self.last_action = action.clone()
        self.snapshot['reset_body_snapshot'][:] = self.environment.clock == 0
        target = self.controller.targets(action, self.snapshot)
        assert target.data_ptr() == self.controller.target.data_ptr()
        self.scene.target.copy_(target)
        self.environment.clock += 4
        return None, None, None, None, None, []

    def close(self): self.closed += 1


def hook(mode, settings=None):
    driver.observer()
    from protocol import Trace
    trace = Trace(driver.SCHEMA, 218)
    tree = ast.parse((driver.HERE/'run_probe.py').read_text())
    node = next(n for n in next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main').body
        if isinstance(n, ast.ClassDef) and n.name == 'TapePool')
    scope = dict(original_pool=FakeBase, torch=torch, args=SimpleNamespace(mode=mode), pools=[], trace=trace,
        action_source=np.full((218, 128, 4), -.2, dtype=np.float32), material_source=np.zeros((128, 3), dtype=np.float32),
        measure=driver.measure, project=project, rounding_tolerance=rounding_tolerance,
        sealed={'force_threshold_N': .01}, MODES=driver.MODES)
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'actual_TapePool_fixture', 'exec'), scope)
    return scope['TapePool'](settings, None), trace


class CPUChecks(unittest.TestCase):
    def test_projection_independent_active_sets(self):
        random = np.random.default_rng(7)
        count = 180
        lower = -random.uniform(0, .0666667, (count, 4))
        upper = random.uniform(0, .0666667, (count, 4))
        lower[0] = 0; upper[1] = 0
        raw = random.uniform(lower, upper)
        normal = random.normal(size=(count, 4)); normal[2] = 0; normal[3, 1:] = 0
        error = random.normal(size=(count, 4))
        for relax in (False, True):
            result = project(*map(torch.tensor, (raw, lower, upper, normal, error)), relax=relax)
            for index in range(count):
                expected = reference(raw[index], lower[index], upper[index], result['normal_scaled'][index].numpy(), float(result['beta_scaled'][index]))
                np.testing.assert_allclose(result['delta'][index], expected, atol=2e-10, rtol=2e-10)
            self.assertTrue(bool((result['halfspace_residual_scaled'] >= -1e-12).all()))
            tiny = project(*map(torch.tensor, (raw, lower, upper, normal*1e-200, error)), relax=relax)
            torch.testing.assert_close(tiny['delta'], result['delta'], atol=1e-12, rtol=1e-12)
        raw_bad = torch.tensor(raw); raw_bad[0, 0] = float('nan')
        with self.assertRaises(ValueError): project(raw_bad, *map(torch.tensor, (lower, upper, normal, error)), relax=False)

    def test_float32_rounding(self):
        random = np.random.default_rng(17)
        old = torch.tensor(random.uniform(-3, 3, (100, 4)), dtype=torch.float32)
        raw = old+torch.tensor(random.uniform(-4/60, 4/60, (100, 4)), dtype=torch.float32)
        lower, upper = torch.full_like(old, -4/60).double(), torch.full_like(old, 4/60).double()
        normal = torch.tensor(random.normal(size=(100, 4)))
        result = project(raw.double()-old.double(), lower, upper, normal, old.double(), relax=True)
        final = (old.double()+result['delta']).float()
        coordinates, tol = rounding_tolerance(old, raw, final, result['normal_scaled'], result['beta_scaled'])
        delta = final.double()-old.double()
        self.assertTrue(bool((torch.maximum(lower-delta, delta-upper) <= coordinates).all()))
        self.assertTrue(bool(((result['normal_scaled']*delta).sum(-1)-result['beta_scaled'] >= -tol).all()))

    def test_actual_target_hook_prefix_alias_rate_tape(self):
        prefixes = []
        for mode in driver.MODES:
            pool, trace = hook(mode)
            action = torch.full((128, 39), .9)
            expected = torch.zeros(128, 4)
            for _ in range(120):
                expected = expected+torch.full((128, 4), -.2)*4/60
                pool.step(action)
                torch.testing.assert_close(pool.controller.target[:, 60:64], expected, atol=0, rtol=0)
                torch.testing.assert_close(pool.last_action[:, 21:25], torch.full((128, 4), -.2), atol=0, rtol=0)
                self.assertTrue(bool((pool.last_action[:, :21] == .9).all()))
            prefixes.append(pool.controller.target.clone())
            self.assertFalse(trace.values()['gate'].any())
            pool.step(action)
            a = trace.values()
            np.testing.assert_array_equal(a['old_target4'][120], a['final_target4'][119])
            self.assertFalse(a['memory_submit_error_rad'].any())
            self.assertFalse(a['other_target_change_rad'].any())
            self.assertTrue((a['box_excess_rad'] <= a['coordinate_tolerance_rad']).all())
            if mode == driver.MODES[0]: np.testing.assert_array_equal(a['raw_target4'], a['final_target4'])
            else:
                self.assertTrue(a['gate'][120].all())
                self.assertTrue((a['halfspace_residual_m'][120] >= -a['halfspace_tolerance_m'][120]).all())
                self.assertTrue((a['beta_m'][120] > 0).all() if mode == driver.MODES[2] else (a['beta_m'][120] == 0).all())
            pool.close(); self.assertEqual(pool.closed, 1)
        for prefix in prefixes[1:]: torch.testing.assert_close(prefix, prefixes[0], atol=0, rtol=0)

    def test_invalid_state_stale_J_and_failure_excluded_before_math(self):
        pool, _ = hook(driver.MODES[2]); pool.environment.clock[:] = 480
        snapshot = pool.snapshot
        snapshot['reset_body_snapshot'][:] = False
        snapshot['reset_body_snapshot'][0] = True; snapshot['jacobian'][0] = float('nan')
        snapshot['q'][1, 0] = float('nan'); snapshot['qd'][2, 0] = float('nan')
        snapshot['jacobian'][3] = float('nan')
        pool.environment.failure[4, 0] = True; pool.environment.wrist_failure[5] = True
        m = driver.measure(pool, snapshot, pool.replay_first, pool.material, .01)
        self.assertFalse(bool(m['gate'][:6].any())); self.assertTrue(bool(m['gate'][6:].all()))
        self.assertEqual(m['invalid_state'].nonzero().flatten().tolist(), [1, 2])
        self.assertEqual(m['invalid'].nonzero().flatten().tolist(), [3])
        for name in ('J', 'g', 'measured', 'predicted'): self.assertTrue(bool(torch.isfinite(m[name]).all()))
        # Run actual hook directly: recording sanitizes invalid actual4, never the native q/qd.
        pool.incoming4 = pool.replayed4 = torch.zeros(128, 4)
        pool.controller.targets(torch.zeros(128, 39), snapshot)
        self.assertTrue(bool(torch.isfinite(pool.pending['actual4']).all()))
        self.assertTrue(bool(torch.isfinite(pool.pending['old_normal_error_m']).all()))
        self.assertTrue(bool(torch.isnan(snapshot['q'][1, 0])))
        self.assertTrue(bool(torch.isnan(snapshot['qd'][2, 0])))

    def test_existing_out_rejected_before_observer_or_native_import(self):
        original_import = builtins.__import__
        def guarded(name, *args, **kwargs):
            if name.startswith('isaacgym'): raise AssertionError('Native import attempted')
            return original_import(name, *args, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)/'existing'; out.mkdir(); sentinel = out/'keep'; sentinel.write_bytes(b'preserve\x00')
            before = (out.stat().st_dev, out.stat().st_ino, sentinel.read_bytes())
            with patch.object(sys, 'argv', ['run_probe.py', '--mode', driver.MODES[0], '--out', str(out)]), patch.object(builtins, '__import__', guarded), patch.object(driver, 'observer', side_effect=AssertionError('Observer called')):
                with self.assertRaises(FileExistsError): driver.main()
            self.assertEqual(before, (out.stat().st_dev, out.stat().st_ino, sentinel.read_bytes()))

    def test_budget_syntax_and_no_cuda(self):
        driver.observer()
        from protocol import Trace
        source = json.loads((driver.OBSERVER/'run_final300_policy/load_probe_report.json').read_text())
        own = Trace(driver.SCHEMA, 218)
        self.assertLess(own.nbytes+source['selected_output_uncompressed_bytes'], 100_000_000)
        for path in driver.HERE.glob('*.py'): ast.parse(path.read_text())
        self.assertFalse(torch.cuda.is_initialized())


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CPUChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    driver.write(driver.HERE/'cpu_verification.json', dict(completed=result.wasSuccessful(), CPU_only=True,
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        scope='Independent active-set arithmetic, actual nested target-hook CPU fixture, prefix/tape/alias/rate/invalid-state/stale-J/output protection; native replay not executed'))
    sys.exit(not result.wasSuccessful())
