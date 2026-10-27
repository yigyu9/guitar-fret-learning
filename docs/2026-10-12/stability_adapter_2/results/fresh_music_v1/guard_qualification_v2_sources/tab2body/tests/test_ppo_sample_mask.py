"""CPU regressions for passive preparation phases excluded from PPO."""
from pathlib import Path
import copy
import math
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch

from learning.models import ActorCritic
from learning.ppo import PPOConfig, PPOTrainer, combine_actor_advantages


class PhaseEnv:
    device = "cpu"
    num_envs = 2
    num_obs = 3
    num_actions = 2
    value_dim = 1
    reward_weights = [1.0]
    episode_metric_keys = ("finished",)
    episode_reason_keys = ()
    rollout_diagnostic_keys = ()

    def __init__(self, phases):
        self.phases = torch.tensor(phases, dtype=torch.bool)
        self.active = self.phases[0].clone()
        self.frame = 0

    def reset(self):
        return torch.zeros(self.num_envs, self.num_obs)

    def policy_sample_mask(self):
        return self.active

    def step(self, action):
        self.frame += 1
        self.active.copy_(self.phases[self.frame])
        return (torch.full((2, 3), float(self.frame)),
                torch.ones(2, 1), torch.zeros(2, dtype=torch.bool), {})


def trainer_for(phases):
    env = PhaseEnv(phases)
    model = ActorCritic(3, 2, value_dim=1, actor_hidden=(8,), critic_hidden=(8,))
    return PPOTrainer(env, model, PPOConfig(
        horizon=len(phases) - 1, epochs=1, minibatch_size=100,
        gamma=1.0, gae_lambda=1.0, target_kl=100.0))


class SampleMaskTests(unittest.TestCase):
    def test_collect_snapshots_phase_before_action(self):
        trainer = trainer_for([[False, False], [True, False], [True, True]])
        rollout = trainer.collect()
        self.assertTrue(torch.equal(rollout["sample_masks"], torch.tensor(
            [[False, False], [True, False]])))
        self.assertTrue(rollout["next_sample_mask"].all())
        self.assertEqual(rollout["diagnostics"]["policy_sample_fraction"], 0.25)

    def test_gae_cuts_inactive_and_done_boundaries(self):
        trainer = trainer_for([[True, False]] * 4)
        masks = torch.tensor([[True, False], [False, True], [True, True]])
        rollout = dict(
            rewards=torch.tensor([[[1.], [999.]], [[999.], [2.]], [[3.], [4.]]]),
            values=torch.tensor([[[0.], [999.]], [[999.], [0.]], [[0.], [0.]]]),
            dones=torch.tensor([[False, False], [False, True], [False, False]]),
            next_value=torch.tensor([[1000.], [10.]]),
            sample_masks=masks, next_sample_mask=torch.tensor([False, True]))
        returns, actor = trainer.advantages(rollout)
        active = masks.flatten()
        expected = torch.tensor([[1.], [2.], [3.], [14.]])
        self.assertTrue(torch.equal(returns[active], expected))
        self.assertTrue(torch.allclose(actor[active], combine_actor_advantages(expected, [1.])))
        self.assertTrue((actor[~active] == 0).all())
        # Passive states and passive rewards have no influence on recovery.
        rollout["values"][~masks] = -5000
        rollout["rewards"][~masks] = -6000
        changed_returns, changed_actor = trainer.advantages(rollout)
        self.assertTrue(torch.equal(changed_returns[active], returns[active]))
        self.assertTrue(torch.equal(changed_actor, actor))

    def test_all_inactive_skips_optimizer_and_rms(self):
        trainer = trainer_for([[False, False]] * 3)
        rollout = trainer.collect()
        before = copy.deepcopy(trainer.model.state_dict())
        stats = trainer.update(rollout)
        self.assertEqual(stats["ppo_updates"], 0)
        self.assertTrue(all(math.isfinite(value) for value in stats.values()))
        self.assertFalse(trainer.optimizer.state)
        self.assertTrue(all(torch.equal(value, trainer.model.state_dict()[key])
                            for key, value in before.items()))
        self.assertEqual(trainer.global_step, 4)

    def test_update_ignores_passive_data_and_rms(self):
        trainer = trainer_for([[False, True], [True, True]])
        rollout = trainer.collect()
        twin = trainer_for([[False, True], [True, True]])
        twin.model.load_state_dict(trainer.model.state_dict())
        changed = copy.deepcopy(rollout)
        changed["obs"][0, 0] = 100000
        changed["actions"][0, 0] = -0.9
        changed["logp"][0, 0] = 100000
        changed["values"][0, 0] = 100000
        changed["rewards"][0, 0] = 100000
        torch.manual_seed(10)
        stats = trainer.update(rollout)
        torch.manual_seed(10)
        twin.update(changed)
        self.assertEqual(stats["ppo_updates"], 1)
        self.assertTrue(all(torch.equal(value, twin.model.state_dict()[key])
                            for key, value in trainer.model.state_dict().items()))

    def test_all_active_matches_legacy(self):
        trainer = trainer_for([[True, True]] * 3)
        rollout = trainer.collect()
        masked = trainer.advantages(rollout)
        rollout.pop("sample_masks")
        rollout.pop("next_sample_mask")
        legacy = trainer.advantages(rollout)
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(masked, legacy)))

    def test_frozen_normalization_preserves_statistics_while_learning(self):
        trainer = trainer_for([[True, True]] * 3)
        trainer.cfg.freeze_observation_normalization = True
        trainer.model.obs_rms.update(torch.tensor([[2., 3., 4.], [4., 5., 6.]]))
        before = copy.deepcopy(trainer.model.state_dict())
        stats = trainer.update(trainer.collect())
        after = trainer.model.state_dict()
        self.assertGreater(stats["ppo_updates"], 0)
        self.assertTrue(all(torch.equal(value, after[key]) for key, value in before.items()
                            if key.startswith("obs_rms.")))
        self.assertTrue(any(not torch.equal(value, after[key]) for key, value in before.items()
                            if key.startswith("actor.")))

    def test_default_normalization_keeps_updating_active_observations(self):
        trainer = trainer_for([[True, True]] * 3)
        before = trainer.model.obs_rms.count.clone()
        trainer.update(trainer.collect())
        self.assertEqual(float(trainer.model.obs_rms.count-before), 4.)


if __name__ == "__main__":
    unittest.main()
