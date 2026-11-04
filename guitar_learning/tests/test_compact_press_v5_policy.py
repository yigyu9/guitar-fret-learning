"""V5 목표 이력·33축 우도·별도 배우/가치망과CPU PPO 저장을 검사한다."""
from pathlib import Path
import tempfile
import math
import unittest

import torch
from torch.distributions import Normal, kl_divergence

from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.training.compact_press_v5 import CompactPressV5Policy
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.training.rollout import DecisionCollector
from guitar_learning.tests.test_finger_decisions import FakeDecisionPool


def contract(pelvis=False):
    dimension = 473 if pelvis else 464
    return dict(schema='guitar_learning.training.v1',
        compact_press=dict(schema='guitar_learning.compact_press_observation.v5', include_pelvis=pelvis),
        observation=dict(dimension=dimension, fields=['state.'+str(i) for i in range(dimension)],
                         scales=[1.]*dimension, event_dim=26, priority_slots=8),
        action=dict(names=list(ACTIVE_NAMES)),
        reward=dict(schema='guitar_learning.compact_press_reward.v5'))


def inputs(count=2, pelvis=False):
    return (torch.randn(count, 473 if pelvis else 464), torch.zeros(count, 0, 26),
            torch.zeros(count, 0, dtype=torch.bool), torch.randn(count, 8, 26),
            torch.ones(count, 8, dtype=torch.bool))


class CompactV5Pool(FakeDecisionPool):
    def _obs(self):
        state, events, mask, goals, valid = inputs()
        state.zero_(); state[:, 0] = self.clock; goals.zero_()
        return dict(state=state, events=events, mask=mask, priority_events=goals, priority_mask=valid)


class CompactPressV5PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)

    def test_464_473_state_26goal_768feature_and_fixed_actor_critic_widths(self):
        for pelvis in (False, True):
            model = CompactPressV5Policy(473 if pelvis else 464, contract=contract(pelvis))
            data = inputs(pelvis=pelvis)
            self.assertEqual(model.actor_encoder.features(data[0], data[3], data[4]).shape, (2, 768))
            self.assertEqual(model.actor_encoder.goal[0].weight.shape, (64, 26))
            self.assertEqual(model.actor_encoder.fusion[0].weight.shape, (512, 768))
            self.assertEqual(model.actor_encoder.fusion[2].weight.shape, (256, 512))
            self.assertEqual(model.value_encoder.fusion[0].weight.shape, (256, 768))
            self.assertEqual(model.value_encoder.fusion[2].weight.shape, (256, 256))
            ids = {id(p) for p in model.actor_parameters()}
            self.assertFalse(ids & {id(p) for p in model.value_parameters()})
            self.assertEqual(model.architecture['schema'], 'guitar_learning.compact_press_policy.v5')

    def test_33learned_axes_fixed_right6_and_original_likelihood_entropy_kl(self):
        model = CompactPressV5Policy(464, contract=contract())
        data = inputs(); result = model.act(*data)
        self.assertEqual(result['action'].shape, (2, 39))
        self.assertTrue(bool((result['action'][:, 33:] == 0).all()))
        evaluated = model.evaluate(*data, result['latent'])
        torch.testing.assert_close(result['logp'], evaluated['logp'])
        distribution = Normal(result['mean'][:, :33], result['log_std'][:, :33].exp())
        torch.testing.assert_close(evaluated['entropy'], distribution.entropy().sum(-1))
        shifted = result['mean']+.01
        torch.testing.assert_close(model.analytic_kl(result['mean'], result['log_std'], shifted,
            result['log_std']), kl_divergence(distribution,
                Normal(shifted[:, :33], distribution.scale)).sum(-1))
        latent = result['latent'].clone(); latent[:, 33:] = 999.
        torch.testing.assert_close(result['logp'], model.evaluate(*data, latent)['logp'])
        with torch.no_grad():
            model.support_log_std.add_(.5); model.finger_log_std.add_(.5)
        torch.testing.assert_close(model.log_std, torch.cat((torch.full((17,), math.log(.15)+.5), torch.full((16,), math.log(.35)+.5))))

    def test_invalid26goal_slots_are_zero_even_with_bias_and_nan_payload(self):
        model = CompactPressV5Policy(464, contract=contract())
        data = list(inputs()); data[4][:, 1::2] = False
        feature = model.actor_encoder.features(data[0], data[3], data[4])
        self.assertTrue(bool((feature[:, 256:].reshape(2, 8, 64)[:, 1::2] == 0).all()))
        data[3][~data[4]] = float('nan')
        torch.testing.assert_close(feature, model.actor_encoder.features(data[0], data[3], data[4]), rtol=0, atol=0)
        data[4][:] = False
        self.assertTrue(all(torch.isfinite(v).all() for v in model(*data).values()))
        data[4][:, 0] = True
        data[3][:, 0] = float('nan')
        with self.assertRaises(ValueError):
            model(*data)

    def test_new_goal_history_and_state_fields_reach_all33_outputs(self):
        model = CompactPressV5Policy(464, contract=contract())
        with torch.no_grad():
            model.actor_head.weight.normal_(0, .02)
        data = list(inputs()); before = model(*data)['mean']
        data[3][:, 0, 16:] += 1.
        after_goal = model(*data)['mean']
        self.assertTrue(bool((before[:, :33] != after_goal[:, :33]).all()))
        data[0][:, -9:] += .5
        after_state = model(*data)['mean']
        self.assertTrue(bool((after_goal[:, :33] != after_state[:, :33]).all()))

    def test_old_schema_and_partial_dimensions_are_rejected(self):
        for field, value in (('schema', 'guitar_learning.compact_press_observation.v1'),
                             ('include_pelvis', 1)):
            bad = contract(); bad['compact_press'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                CompactPressV5Policy(464, contract=bad)
        for key, value in (('event_dim', 16), ('priority_slots', 7), ('dimension', 443)):
            bad = contract(); bad['observation'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                CompactPressV5Policy(464, contract=bad)
        bad = contract(); bad['observation']['scales'][0] = float('nan')
        with self.assertRaises(ValueError):
            CompactPressV5Policy(464, contract=bad)
        model = CompactPressV5Policy(464, contract=contract())
        data = list(inputs()); data[3] = data[3][:, :7]
        with self.assertRaises(ValueError):
            model(*data)

    def test_cpu_ppo_update_roundtrip_and_retired_checkpoint_rejection(self):
        model = CompactPressV5Policy(464, contract=contract())
        config = PPOConfig(epochs=1, minibatch_size=8)
        trainer = DecisionPPOTrainer(model, config)
        buffer, episodes = DecisionCollector(model, CompactV5Pool(failure=False)).collect(4)
        before = model.actor_head.weight.detach().clone()
        trainer.update(buffer, episodes)
        self.assertFalse(torch.equal(before, model.actor_head.weight))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'v3.pt'; trainer.save(path, metadata=dict(test=True))
            restored = CompactPressV5Policy(464, contract=contract())
            DecisionPPOTrainer(restored, config).load(path)
            for key, value in model.state_dict().items():
                torch.testing.assert_close(value, restored.state_dict()[key], rtol=0, atol=0)
            payload = torch.load(path, map_location='cpu', weights_only=False)
            payload['identity']['architecture']['schema'] = 'retired-policy'
            old_path = Path(folder)/'retired.pt'
            torch.save(payload, old_path)
            with self.assertRaisesRegex(ValueError, 'architecture'):
                trainer.load(old_path)

    def test_real_environment_policy_four_native_substeps_cpu_integration(self):
        from guitar_learning.gpu.compact_press_v5 import CompactPressV5Environment
        from guitar_learning.tests.test_gpu_environment import fixture, BUNDLE, SONG
        metadata, snapshot = fixture(2)
        env = CompactPressV5Environment(metadata, bundle=BUNDLE, song=SONG, device='cpu',
            skill=dict(schema='guitar_learning.finger_skill.v3', phase='J', scope='scheduled',
                hold_ticks=1, exploration='independent', planned_transitions=128, full_song_after=32))
        observation = env.reset([0, 1], snapshot)
        model = CompactPressV5Policy(464, contract=env.contract)
        action = model.act(**observation)['action']
        env.begin_control(action)
        for _ in range(4):
            env.substep(dict(snapshot, physics_step=env.clock+1))
        after, reward, cost, done, truncated, episodes = env.end_control()
        self.assertEqual(after['state'].shape, (2, 464))
        self.assertEqual(after['priority_events'].shape, (2, 8, 26))
        self.assertTrue(bool(torch.isfinite(reward).all() & torch.isfinite(cost).all()))
        self.assertEqual(env.clock.tolist(), [4, 4])


if __name__ == '__main__':
    unittest.main()
