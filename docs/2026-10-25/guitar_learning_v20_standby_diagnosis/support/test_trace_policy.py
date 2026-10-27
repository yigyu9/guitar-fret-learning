"""CPU checks for observational trace isolation and integral reconciliation."""
import importlib.util
from pathlib import Path
import tempfile
import sys
from types import SimpleNamespace
import unittest

import numpy as np
import torch

SPEC = importlib.util.spec_from_file_location('standby_trace', Path(__file__).with_name('trace_policy.py'))
TRACE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TRACE)
sys.path.insert(0, str(TRACE.ROOT))


def inputs():
    n, m = 2, 2
    env = SimpleNamespace(device='cpu', M=m,
        clock=torch.zeros(n, dtype=torch.long),
        finger_joint_indices=torch.arange(21), finger_action_indices=torch.arange(21),
        finger_segment_indices=torch.arange(12).reshape(4, 3), finger_palm_index=12,
        body=torch.zeros(n, 13, 13), action=torch.ones(n, 21),
        finger_outward=torch.zeros(n, 21, dtype=torch.bool),
        surface_distance=torch.ones(n, m),
        candidate=torch.zeros(n, m, dtype=torch.bool), wrong=torch.zeros(n, m, dtype=torch.bool),
        previous_candidate=torch.zeros(n, m, dtype=torch.bool),
        previous_wrong=torch.zeros(n, m, dtype=torch.bool),
        onset=torch.tensor([1., 2.], dtype=torch.float64),
        press=torch.tensor([.5, 1.5], dtype=torch.float64),
        end=torch.tensor([1.5, 2.5], dtype=torch.float64), finger=torch.tensor([1, 2]),
        tick_failure=torch.zeros(n, 2, dtype=torch.bool),
        _weights=lambda: {'approach': .5})
    env.body[..., 6] = 1.
    env.snapshot = dict(q=torch.zeros(n, 21), target=torch.ones(n, 21),
        contact_force=torch.arange(n*13*3).float().reshape(n, 13, 3))
    posture = {k: torch.ones(n, 4, dtype=torch.float64)
               for k in ('gate', 'quality', 'idle_weight')}
    posture.update(per_finger_rate=torch.full((n, 4), .005, dtype=torch.float64),
        shape_per_finger_rate=torch.zeros(n, 4, dtype=torch.float64),
        angles=torch.zeros(n, 4, 3), valid=torch.ones(n, 4, 3, dtype=torch.bool),
        band_inside=torch.ones(n, 4, dtype=torch.bool))
    for key in ('near_veto', 'contact_veto', 'nonfinite_veto'):
        posture[key] = torch.zeros(n, 4, dtype=torch.bool)
    return env, posture, torch.zeros(n, 4, dtype=torch.bool)


def episode(index, steps, failed_last=False):
    raw = np.full(4, .005*steps/60.)
    weighted = np.full(4, .005*(steps-int(failed_last))/60.*.5)
    return dict(env_id=index, steps=steps,
        left_episode_diagnostics={'standby': dict(raw_standby_reward=raw.tolist(),
            weighted_standby_reward=weighted.tolist())},
        reward_components={'song_finger_standby': float(weighted.sum())})


class TraceTests(unittest.TestCase):
    def test_hook_calls_original_once_and_copies_actual_posture(self):
        env, posture, pressing = inputs()
        calls = []
        def original(p, own, wrist, now=None):
            calls.append((p, own, wrist, now))
            return 'original-result'
        env.episode_diagnostics = SimpleNamespace(physics=original)
        trace = TRACE.PhysicsTrace(env, max_steps=4, count=2)
        TRACE.attach_trace(env, trace)
        self.assertEqual(trace.step, 0)  # Attachment does not re-run reset/physics.
        env.clock += 1
        now = env.clock.double()/240.
        delta = torch.zeros(2, 3)
        before = {k: v.clone() for k, v in posture.items()}
        self.assertEqual(env.episode_diagnostics.physics(posture, pressing, delta, now=now), 'original-result')
        self.assertEqual(len(calls), 1)
        self.assertIs(calls[0][0], posture)
        self.assertIs(calls[0][-1], now)
        for key in posture:
            self.assertTrue(torch.equal(posture[key], before[key]))
        posture['gate'].zero_()
        env.snapshot['q'].fill_(99)
        self.assertTrue(torch.equal(trace.arrays['gate'][0], before['gate']))
        self.assertEqual(float(trace.arrays['q'][0].sum()), 0.)
        self.assertTrue(torch.equal(trace.arrays['segment_contact_force'][0],
            env.snapshot['contact_force'][:, env.finger_segment_indices]))

    def test_first_episode_freeze_clocks_and_failed_tick_integrals(self):
        env, posture, pressing = inputs()
        trace = TRACE.PhysicsTrace(env, max_steps=8, count=2)
        for tick in range(2):
            for substep in range(4):
                env.clock += 1
                trace.record(posture, pressing, env.clock.double()/240.)
            env.tick_failure[1, 0] = tick == 1
            trace.end_control([episode(tick, tick+1, failed_last=tick == 1)])
            if tick == 0:
                # Simulate an earlier completed row reset while another runs.
                env.clock[0] = 0
                env.snapshot['q'][0] = 42
        self.assertEqual(trace.step, 8)
        self.assertFalse(bool(trace.arrays['q'][4:, 0].any()))
        with tempfile.TemporaryDirectory() as folder:
            captures = trace.save(Path(folder)/'physics')
            self.assertEqual([r['frames'] for r in captures], [4, 8])
            second = np.load(Path(folder)/'physics/physics_env0001.npz')
            self.assertTrue(np.array_equal(second['clock'], np.arange(1, 9)))
            self.assertTrue(second['control_failed'][-4:].all())
            self.assertLess(abs(captures[1]['weighted_B_error']), 1e-12)

    def test_rejects_budget_missing_episode_and_bad_integral(self):
        env, posture, pressing = inputs()
        trace = TRACE.PhysicsTrace(env, max_steps=4, count=2)
        for _ in range(4):
            env.clock += 1
            trace.record(posture, pressing, env.clock.double()/240.)
        with self.assertRaisesRegex(ValueError, 'budget'):
            trace.record(posture, pressing, env.clock.double()/240.)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'must end'):
                trace.save(Path(folder)/'missing')
            trace.end_control([episode(0, 1), episode(1, 1)])
            trace.episodes[0]['left_episode_diagnostics']['standby']['raw_standby_reward'][0] += .1
            with self.assertRaisesRegex(ValueError, 'raw B'):
                trace.save(Path(folder)/'wrong')


if __name__ == '__main__':
    unittest.main()
