"""구조 v2의 활성 분포·목표 의미·관측된 단계 상태를 CPU에서 검사한다."""
import copy
import json
import math
import tempfile
from dataclasses import asdict
import unittest
from unittest.mock import patch
from pathlib import Path

import torch
from torch.distributions import Normal, kl_divergence
from guitar_learning.tool.experiments.structured_press import (
    StructuredPolicy, StructuredEnvironment, StructuredTrainer, EXTRA_FIELDS, EXTRA_DIM,
    active_axes, load_configuration, normalized_action, digest)
from guitar_learning.tests.test_finger_skill_policy import inputs
from guitar_learning.training.ppo import PPOConfig


class StructuredPressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.catalog = Path(self.directory.name)/'catalog.json'
        reference = [0.]*105
        target = [.2]*12+[0.]*93
        self.catalog.write_text(json.dumps(dict(reference105=reference, action_indices=list(range(39)),
            action_lower=[-1.]*39, action_upper=[1.]*39,
            goals=[dict(song='test', finger='index', candidate_valid=True, native_verified=True,
                hold_target105=target, perturbations=[dict(candidate_valid=True, native_verified=True)])])))

    def model(self, stage='A'):
        config = load_configuration(self.catalog, 'test', stage)
        relative = Path('process/learning/runs/index_s3_f6/train/J/training_contract.json')
        source = next(parent/relative for parent in Path(__file__).resolve().parents if (parent/relative).is_file())
        value = json.loads(source.read_text())
        value['structured_press'] = config
        value['observation']['fields'] += EXTRA_FIELDS
        value['observation']['scales'] += [1.]*EXTRA_DIM
        value['observation']['dimension'] += EXTRA_DIM
        return StructuredPolicy(557+EXTRA_DIM, size='small', contract=value, structured=config)

    def data(self, count=4):
        data = list(inputs(count))
        extra = torch.zeros(count, EXTRA_DIM)
        extra[:, 7:19] = .2  # 관측된 arm hold target이며 v9 행동0과 다르다.
        data[0] = torch.cat((data[0], extra), -1)
        return data

    def test_active_axes_and_target_finger_always_free(self):
        for stage, count in (('A', 4), ('B', 16), ('C50', 33), ('C75', 33), ('C100', 33), ('free_v9', 33)):
            model = self.model(stage)
            self.assertEqual(int(model._active_mask().sum()), count)
            for phase in range(3):
                data = self.data()
                data[0][:, 557:560] = 0
                data[0][:, 557+phase] = 1
                result = model.act(*data)
                self.assertGreater(float(result['action'][:, 17:21].abs().sum()), 0.)
                self.assertTrue(torch.all(result['log_std'][:, 17:21].exp() >= .1))

    def test_a_hold_not_zero_v9_and_only_four_gradients(self):
        model = self.model()
        data = self.data()
        action = model.act(*data)
        torch.testing.assert_close(action['action'][:, :12], torch.full((4, 12), .2))
        action['logp'].sum().backward()
        self.assertIsNone(model.core.support_head.weight.grad)
        self.assertIsNotNone(model.core.finger_heads['index'][-1].weight.grad)
        for name in ('middle', 'ring', 'pinky'):
            self.assertIsNone(model.core.finger_heads[name][-1].weight.grad)

    def test_density_kl_entropy_ignore_inactive_channels(self):
        model = self.model().double()
        data = [x.double() if x.dtype == torch.float32 else x for x in self.data()]
        result = model.act(*data)
        active = model._active_mask()
        changed = result['latent'].clone(); changed[:, ~active] += 100
        torch.testing.assert_close(model.evaluate(*data, changed)['logp'], result['logp'])
        mean = result['mean'].clone(); mean[:, ~active] += 100
        torch.testing.assert_close(model.analytic_kl(result['mean'], result['log_std'],
            mean, result['log_std']), torch.zeros(4, dtype=torch.float64))
        expected = Normal(result['mean'][:, active], result['log_std'][:, active].exp())
        torch.testing.assert_close(model.evaluate(*data, result['latent'])['entropy'], expected.entropy().sum(-1))
        shifted = result['mean']+.01
        updated = Normal(shifted[:, active], result['log_std'][:, active].exp())
        torch.testing.assert_close(model.analytic_kl(result['mean'], result['log_std'],
            shifted, result['log_std']), kl_divergence(expected, updated).sum(-1))

    def test_same_v9_codec_all_stages_and_support_initialization(self):
        for stage in ('A', 'B', 'C50'):
            model = self.model(stage)
            torch.testing.assert_close(model.act(*self.data(), deterministic=True)['action'][:, :12],
                                       torch.full((4, 12), .2))
        target = torch.tensor([-.3, .4])
        self.assertTrue(torch.equal(normalized_action(target, torch.zeros(2),
            torch.tensor([-1., -2.]), torch.tensor([2., 1.])), torch.tensor([-.3, .4])))

    def test_contract_rejects_old_shape_and_changed_geometry(self):
        model = self.model()
        with self.assertRaises(ValueError):
            model(*inputs())
        config = copy.deepcopy(model.structured)
        self.catalog.write_text(self.catalog.read_text()+' ')
        with self.assertRaises(ValueError):
            from guitar_learning.tool.experiments.structured_press import catalog_goal
            catalog_goal(config)

    def test_native_validation_is_required(self):
        data = json.loads(self.catalog.read_text())
        data['goals'][0]['native_verified'] = False
        self.catalog.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            load_configuration(self.catalog, 'test', 'A')
        self.assertTrue(load_configuration(self.catalog, 'test', 'A', allow_unverified=True)['allow_unverified'])

    def test_adjacent_transfer_checks_identity_and_source_bytes(self):
        source = self.model('A')
        checkpoint = Path(self.directory.name)/'source.pt'
        config = PPOConfig()
        torch.save(dict(identity=StructuredTrainer(source, config)._identity(),
            model=source.state_dict(), metadata=dict(settings=dict(ppo=asdict(config)))), checkpoint)
        expected = digest(checkpoint)
        target = self.model('B')
        with patch('guitar_learning.training.finger_skill_runner._validate_pins') as verify:
            target.initialize_from(checkpoint, expected_sha256=expected)
            verify.assert_called_once()
        self.assertEqual(int(target._active_mask().sum()), 16)
        torch.testing.assert_close(target.core.support_head.bias, source.core.support_head.bias)
        checkpoint.write_bytes(checkpoint.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError, 'SHA mismatch'):
            target.initialize_from(checkpoint, expected_sha256=expected)

    def test_transfer_rejects_old_stage_and_frozen_source_failure(self):
        source = self.model('A')
        checkpoint = Path(self.directory.name)/'source.pt'
        config = PPOConfig()
        torch.save(dict(identity=StructuredTrainer(source, config)._identity(),
            model=source.state_dict(), metadata=dict(settings=dict(ppo=asdict(config)))), checkpoint)
        with self.assertRaisesRegex(ValueError, 'adjacent'):
            self.model('C50').initialize_from(checkpoint, expected_sha256=digest(checkpoint))
        with patch('guitar_learning.training.finger_skill_runner._validate_pins',
                   side_effect=ValueError('checkpoint input sources changed')):
            with self.assertRaisesRegex(ValueError, 'sources changed'):
                self.model('B').initialize_from(checkpoint, expected_sha256=digest(checkpoint))
        with patch('guitar_learning.training.finger_skill_runner._validate_pins'):
            target = self.model('free_v9')
            target.initialize_from(checkpoint, expected_sha256=digest(checkpoint))
            self.assertEqual(int(target._active_mask().sum()), 33)

    def test_probe_only_configuration_cannot_start_ppo(self):
        policy = self.model()
        policy.structured['allow_unverified'] = True
        with self.assertRaisesRegex(ValueError, 'PPO requires physically verified'):
            StructuredTrainer(policy, PPOConfig())

    def phase_fixture(self):
        env = object.__new__(StructuredEnvironment)
        env.device = torch.device('cpu')
        env.motion_phase = torch.zeros(2, dtype=torch.long)
        env.phase_elapsed = torch.zeros(2)
        env.ready_timers = torch.zeros(2, 2)
        env.transition_elapsed = torch.ones(2)*.20
        env.hold_action = torch.zeros(2, 39)
        env.last_applied_action = torch.ones(2, 39)*.3
        env.last_phase_time = torch.zeros(2, dtype=torch.float64)
        env.phase_counts = torch.zeros(2, 3)
        env.block_counts = torch.zeros(2, 4)
        env.action_min = torch.zeros(2, 39)
        env.action_max = torch.zeros(2, 39)
        env.surface_delta = torch.zeros(2, 1, 3)
        env.surface_height = torch.ones(2, 1)*.01
        env.surface_alignment = torch.ones(2, 1)
        env.guide = dict(delta=torch.zeros(2, 3))
        env.candidate = torch.zeros(2, 1, dtype=torch.bool)
        env.wrong = env.candidate.clone()
        env.test_time = torch.zeros(2, dtype=torch.float64)
        env._local_time = lambda: env.test_time
        return env

    def test_real_endpoint_timers_latch_and_clean_height_exception(self):
        env = self.phase_fixture()
        for _ in range(5):
            env.test_time += 1/60.
            env._advance_phase()
        self.assertTrue(torch.equal(env.motion_phase, torch.zeros(2, dtype=torch.long)))
        env.test_time += 1/60.; env._advance_phase()
        self.assertEqual(env.motion_phase.tolist(), [2, 2])
        torch.testing.assert_close(env.hold_action[:, :12], torch.ones(2, 12)*.3)
        # 0.1초 연속 정렬을 충족했으면 압현면 높이0에서도 압현 유지.
        env.surface_height.zero_()
        env.test_time += 1/60.; env._advance_phase()
        self.assertEqual(env.motion_phase.tolist(), [2, 2])
        env.guide['delta'][0, 0] = .04
        env.test_time += 1/60.; env._advance_phase()
        self.assertEqual(env.motion_phase.tolist(), [0, 2])
        # clean 접촉은 정렬 타이머 미달이어도 즉시 압현 구간.
        env.candidate[0, 0] = True
        env.guide['delta'][0, 0] = 0.
        env.test_time += 1/60.; env._advance_phase()
        self.assertEqual(env.motion_phase.tolist(), [2, 2])
        self.assertAlmostEqual(float(env.phase_counts.sum()), 2*9/60., places=6)

    def test_partial_reset_does_not_clear_other_phase_history(self):
        env = self.phase_fixture()
        env.motion_phase[:] = 2; env.phase_counts[:] = .7
        env.phase_elapsed[:] = .4; env.ready_timers[:] = .1
        with patch.object(StructuredEnvironment.__mro__[1], '_reset_scope'):
            env._reset_scope(torch.tensor([0]))
        self.assertEqual(int(env.motion_phase[0]), 0)
        self.assertEqual(int(env.motion_phase[1]), 2)
        torch.testing.assert_close(env.phase_counts[1], torch.full((3,), .7))
        self.assertEqual(float(env.phase_counts[0].sum()), 0.)

    def test_finite_real_decision_ppo_update(self):
        model = self.model()
        data = self.data(8)
        with torch.no_grad():
            result = model.act(*data)
        buffer = {name: value[None].repeat(3, *([1]*value.ndim)) for name, value in
            zip(('state', 'events', 'mask', 'priority_events', 'priority_mask'), data)}
        for name, key in (('latent', 'latent'), ('old_mean', 'mean'), ('old_log_std', 'log_std'),
                          ('logp', 'logp'), ('reward_value', 'reward_value'), ('cost_value', 'cost_value')):
            value = result[key]; buffer[name] = value[None].repeat(3, *([1]*value.ndim))
        for name in ('next_reward_value', 'next_cost_value'):
            buffer[name] = torch.zeros(3, 8)
        buffer.update(reward=torch.randn(3, 8)*.01, cost=torch.zeros(3, 8),
            terminated=torch.zeros(3, 8, dtype=torch.bool), truncated=torch.zeros(3, 8, dtype=torch.bool),
            valid=torch.ones(3, 8, dtype=torch.bool), duration=torch.ones(3, 8, dtype=torch.long))
        trainer = StructuredTrainer(model, PPOConfig(epochs=1, minibatch_size=24, retry_lr_factor=.5))
        result = trainer.update(buffer, [])
        self.assertTrue(math.isfinite(result['analytic_kl']))
        self.assertEqual(trainer.updates, 1)


if __name__ == '__main__':
    unittest.main()
