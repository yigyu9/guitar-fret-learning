"""v25 control semantics, true joint decisions, wrist exits and legacy isolation."""
import copy
import math
import unittest

import torch

from guitar_learning.tool.experiments.active_press_v25.runtime import (
    ActiveController, ActiveEnvironment, ActivePolicy, WristExitState, SPEC, TIMER_FIELDS, bindings)
from guitar_learning.tool.experiments.active_press_v25.collector import ActiveCollector
from guitar_learning.tests.test_finger_skill_policy import contract, inputs
from guitar_learning.tests.test_finger_decisions import TinyDecisionPolicy, FakeDecisionPool
from guitar_learning.tests.test_gpu_control import fake_scene
from guitar_learning.tests.test_gpu_environment import fixture, SONG, BUNDLE
from guitar_learning.training.finger_decisions import DecisionCollector


class ActivePressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def environment(self, count=2):
        metadata, snapshot = fixture(count)
        env = ActiveEnvironment(metadata, bundle=BUNDLE, song=SONG, device='cpu',
            skill=dict(schema='guitar_learning.finger_skill.v1', phase='J', scope='phrases',
                       hold_ticks=3, exploration='independent'))
        env.reset(list(range(count)), snapshot)
        return env, snapshot

    def policy(self):
        value = contract('J')
        value['observation']['fields'][-5:-5] = list(TIMER_FIELDS)
        value['observation']['scales'][-5:-5] = [.75, 3.]
        value['observation']['dimension'] = 559
        return ActivePolicy(559, size='small', contract=value, phase='J')

    def advance(self, env, snapshot, invalid=None):
        env.begin_control(torch.zeros(env.N, 39))
        if invalid is not None:
            env.invalidate_control(invalid)
        for _ in range(4):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        return env.end_control()

    def test_all_33_axes_are_trainable_and_both_heads_receive_gradients(self):
        model = self.policy()
        self.assertEqual(int(model._active_mask().sum()), 33)
        self.assertTrue(all(p.requires_grad for p in model.support_encoder.parameters()))
        self.assertTrue(all(p.requires_grad for p in model.finger_encoder.parameters()))
        data = list(inputs())
        data[0] = torch.randn(4, 559)
        result = model.act(*data)
        self.assertTrue(bool(result['action'][:, 17:33].abs().sum()))
        self.assertTrue(torch.equal(result['action'][:, 33:], torch.zeros(4, 6)))
        result['action'][:, :33].sum().backward()
        self.assertGreater(float(model.support_head.weight.grad.abs().sum()), 0)
        for head in model.finger_heads.values():
            self.assertGreater(float(head[-1].weight.grad.abs().sum()), 0)
        torch.testing.assert_close(model.support_log_std[:12].exp(), torch.full((12,), .10))
        torch.testing.assert_close(model.support_log_std[12:].exp(), torch.full((5,), math.exp(-3)))

    def test_r_and_old_checkpoint_identity_are_not_silently_reused(self):
        with self.assertRaises(ValueError):
            ActivePolicy(557, size='small', contract=contract('R'), phase='R')
        model = self.policy()
        self.assertEqual(model.architecture['schema'], ActivePolicy.schema)
        self.assertNotEqual(model.architecture['schema'], 'guitar_learning.finger_skill_policy.v1')

    def test_timer_observations_reset_and_enter_support_inputs(self):
        env, snapshot = self.environment()
        obs = env.observation()
        self.assertEqual(obs['state'].shape[-1], 559)
        fields = env.contract['observation']['fields']
        timer = fields.index(TIMER_FIELDS[0])
        grace = fields.index(TIMER_FIELDS[1])
        torch.testing.assert_close(obs['state'][:, grace], torch.ones(2))
        env.wrist_exit.outside_s[1] = .3
        obs = env.observation()
        self.assertAlmostEqual(float(obs['state'][1, timer]), .4, places=6)
        model = self.policy()
        for name in TIMER_FIELDS:
            self.assertIn(name, model.architecture['support_fields'])

    def test_thumb_constant_action_is_position_not_drift_and_fingers_still_integrate(self):
        scene, sample = fake_scene(1)
        control = ActiveController(scene)
        control.reset(torch.tensor([0]), sample)
        action = torch.zeros(1, 39, dtype=torch.float64)
        action[:, 15] = .03  # thumb2, position request
        action[:, 19] = .001  # index2, incremental velocity
        first = control.targets(action, sample).clone()
        last = first.clone()
        for _ in range(59):
            last = control.targets(action, sample).clone()
        thumb = scene.names.index('LH:thumb2')
        finger = scene.names.index('LH:index2')
        self.assertEqual(float(first[0, thumb]), float(last[0, thumb]))
        self.assertAlmostEqual(float(last[0, finger]-first[0, finger]), 59*.001*4/60, places=9)
        action.zero_()
        previous_finger = last[0, finger].clone()
        for _ in range(10):
            last = control.targets(action, sample)
        self.assertEqual(float(last[0, thumb]), float(control.reference[thumb]))
        self.assertEqual(float(last[0, finger]), float(previous_finger))
        self.assertEqual(control.incremental_actions.tolist(), list(range(17, 33)))

    def test_joint_actions_are_held_once_and_raw_ticks_covered_once(self):
        pool, model = FakeDecisionPool(k=3, failure=False), TinyDecisionPolicy('J')
        records = []
        buffer, _ = ActiveCollector(model, pool).collect(8, decision_callback=records.append)
        self.assertEqual(buffer['duration'][:, 0].tolist(), [3, 3, 2])
        for a, b in [(0, 1), (1, 2), (3, 4), (4, 5), (6, 7)]:
            torch.testing.assert_close(pool.actions[a], pool.actions[b], rtol=0, atol=0)
        for env in range(2):
            self.assertEqual([t for row in records if row['env_id'] == env for t in row['raw_control_ticks']], list(range(8)))
        self.assertAlmostEqual(float(buffer['reward'][0, 0]), 1+.99+.99**2, places=6)

    def test_joint_failure_truncation_and_rollout_cut_keep_durations_correct(self):
        for truncate in (False, True):
            pool, model = FakeDecisionPool(k=3, truncate=truncate), TinyDecisionPolicy('J')
            collector = ActiveCollector(model, pool)
            buffer, _ = collector.collect(5)
            self.assertEqual(int(buffer['duration'][0, 0]), 2)
            self.assertEqual(bool(buffer['truncated'][0, 0]), truncate)
            self.assertEqual(bool(buffer['terminated'][0, 0]), not truncate)
            before = len(pool.actions)
            collector.collect(2)
            self.assertEqual(len(pool.actions), before+2)
            self.assertGreater(model.sample_calls, 2)

    def test_wrist_initial_grace_sustained_exit_and_partial_reset(self):
        state = WristExitState(2, 'cpu')
        center = torch.zeros(2, 3)
        state.reset([0, 1], center)
        delta = torch.full((2, 3), .04)
        for _ in range(200):
            self.assertFalse(bool(state.step(delta, center, torch.full((2,), 2.)).any()))
        for i in range(179):
            self.assertFalse(bool(state.step(delta, center, torch.full((2,), 4+i/240.)).any()))
        self.assertTrue(bool(state.step(delta, center, torch.full((2,), 5.)).all()))
        state.reset([0], center)
        self.assertFalse(bool(state.failed[0]))
        self.assertTrue(bool(state.failed[1]))

    def test_wrist_reentry_transition_grace_and_severe_exit(self):
        state = WristExitState(1, 'cpu')
        center = torch.zeros(1, 3)
        state.reset([0], center)
        for _ in range(100):
            state.step(torch.full((1, 3), .04), center, torch.tensor([4.]))
        state.step(torch.zeros(1, 3), center, torch.tensor([4.5]))
        self.assertEqual(float(state.outside_s[0]), 0)
        moved = center+torch.tensor([[0., .02, 0.]])
        state.step(torch.full((1, 3), .04), moved, torch.tensor([5.]))
        self.assertEqual(float(state.outside_s[0]), 0)
        state.step(torch.full((1, 3), .04), moved, torch.tensor([5.3]))
        self.assertEqual(float(state.outside_s[0]), 0)
        self.assertTrue(bool(state.step(torch.full((1, 3), .11), moved, torch.tensor([5.31]))[0]))

    def test_wrist_failure_has_own_reason_cost_and_zero_bootstrap_terminal(self):
        env, sample = self.environment()
        env.wrist_exit.failed[0] = True
        _, reward, cost, terminal, truncated, episodes = self.advance(env, sample)
        self.assertTrue(bool(terminal[0]))
        self.assertFalse(bool(truncated[0]))
        self.assertEqual(episodes[0]['failure_reasons'], ['wrist_region_exit'])
        self.assertGreater(float(cost[0]), 5)
        self.assertFalse(episodes[0]['song']['completed'])
        self.assertEqual(episodes[0]['song']['denominator'], int(env.focus_mask[0].sum()))
        self.assertEqual(episodes[0]['reward_components']['song_wrist_position'], 0.)

    def test_physical_control_failure_is_not_relabelled_wrist_exit(self):
        env, sample = self.environment()
        result = self.advance(env, sample, torch.tensor([True, False]))
        row = result[-1][0]
        self.assertIn('support_control_invalid', row['failure_reasons'])
        self.assertNotIn('wrist_region_exit', row['failure_reasons'])

    def test_h32_scope_timer_and_partial_reset_are_preserved(self):
        env, sample = self.environment()
        env.wrist_exit.outside_s[1] = .4
        mask, offset = env.focus_mask.clone(), env.score_offset.clone()
        env.reset([0], sample)
        self.assertAlmostEqual(float(env.wrist_exit.outside_s[1]), .4)
        self.assertTrue(torch.equal(mask[1], env.focus_mask[1]))
        self.assertEqual(float(offset[1]), float(env.score_offset[1]))
        self.assertLessEqual(int(env.plan_decisions(32).max()), 3)
        self.assertTrue(bool((env.plan_decisions(1) == 1).all()))

    def test_bindings_restore_legacy_module_objects(self):
        from guitar_learning.gpu import control, finger_skill_environment
        from guitar_learning.training import finger_decisions
        original = control.BatchedController, finger_skill_environment.FingerSkillEnvironment, finger_decisions.DecisionCollector
        with bindings():
            self.assertIs(control.BatchedController, ActiveController)
            self.assertIs(finger_decisions.DecisionCollector, ActiveCollector)
        self.assertEqual(original, (control.BatchedController, finger_skill_environment.FingerSkillEnvironment, finger_decisions.DecisionCollector))


if __name__ == '__main__':
    unittest.main()
