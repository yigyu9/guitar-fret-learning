"""CPU regression checks for scalar actor advantage construction."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from learning.models import ActorCritic, RunningMeanStd
from learning.ppo import (PPOConfig, PPOTrainer,
                          aggregate_episode_rows,
                          combine_actor_advantages)


class _GoalStub:
    fret = torch.tensor([[0.0, 1.0, 1.0, 0.0, 0.0, 0.0]])


class _EnvStub:
    def __init__(self, num_envs=4, obs_dim=5, action_dim=3):
        self.device = "cpu"
        self.num_envs = num_envs
        self.num_obs = obs_dim
        self.num_actions = action_dim
        self.value_dim = 6
        self.reward_weights = torch.full((6,), 1.0 / 6.0)
        self.goals = _GoalStub()

    def reset(self):
        return torch.zeros(self.num_envs, self.num_obs)


class _ReusedObservationEnv(_EnvStub):
    """Minimal Isaac Gym-style env that overwrites one observation buffer."""

    def __init__(self):
        super().__init__(num_envs=2, obs_dim=5, action_dim=3)
        self.obs_buf = torch.zeros(self.num_envs, self.num_obs)

    def reset(self):
        self.obs_buf.zero_()
        return self.obs_buf

    def step(self, action):
        self.obs_buf.add_(1.0)
        reward = torch.zeros(self.num_envs, self.value_dim)
        done = torch.zeros(self.num_envs, dtype=torch.bool)
        return self.obs_buf, reward, done, {}


class _MaskedObservationEnv(_ReusedObservationEnv):
    def policy_action_mask(self):
        return torch.tensor(
            [[True, True, False], [True, False, False]])


def main():
    timing = aggregate_episode_rows(
        [
            {
                "strike_timing_mae_ms": 10.0,
                "strike_timing_p95_ms": 10.0,
                "goal_finished": 1.0,
                "_timing_abs_ms": [10.0],
            },
            {
                "strike_timing_mae_ms": 100.0,
                "strike_timing_p95_ms": 100.0,
                "goal_finished": 0.0,
                "_timing_abs_ms": [100.0],
            },
        ],
        ("strike_timing_mae_ms", "strike_timing_p95_ms"),
        ("goal_finished",),
    )
    assert timing["strike_timing_mae_ms"] == 55.0
    assert abs(timing["strike_timing_p95_ms"] - 95.5) < 1e-5
    assert timing["strike_timing_sample_count"] == 2
    assert timing["goal_finished_count"] == 1

    hold = aggregate_episode_rows(
        [
            {
                "sustain_max_dropout_frames": 2.0,
                "press_max_dropout_frames": 1.0,
                "press_finger_1_success": 8.0,
                "press_finger_1_count": 10.0,
            },
            {
                "sustain_max_dropout_frames": 7.0,
                "press_max_dropout_frames": 5.0,
                "press_finger_1_success": 9.0,
                "press_finger_1_count": 10.0,
            },
        ],
        (
            "sustain_max_dropout_frames", "press_max_dropout_frames",
            "press_finger_1_success",
            "press_finger_1_count",
        ),
        (),
    )
    assert hold["sustain_max_dropout_frames"] == 7.0
    assert hold["press_max_dropout_frames"] == 5.0
    assert abs(hold["sustain_p95_dropout_frames"] - 6.75) < 1e-6
    assert abs(hold["press_p95_dropout_frames"] - 4.8) < 1e-6
    assert abs(hold["finger_1_press_success_rate"] - 0.85) < 1e-6

    active = torch.tensor([
        [1.0, 4.0],
        [2.0, 1.0],
        [4.0, 3.0],
        [8.0, 2.0],
    ])
    adv = torch.zeros(4, 6)
    adv[:, 1:3] = active
    weights = torch.tensor([0.0, 1.0, 3.0, 0.0, 0.0, 0.0])

    got = combine_actor_advantages(adv, weights)
    raw = 0.25 * active[:, 0] + 0.75 * active[:, 1]
    expected = (raw - raw.mean()) / raw.std(unbiased=False)
    assert torch.allclose(got, expected, atol=1e-6)

    # Permanently DONT_CARE heads cannot change the actor objective.
    noisy = adv.clone()
    noisy[:, 0] = torch.tensor([1e6, -1e6, 5e5, -5e5])
    noisy[:, 3:] = torch.randn(4, 3) * 1e7
    assert torch.allclose(combine_actor_advantages(noisy, weights), got, atol=1e-6)

    try:
        combine_actor_advantages(adv.fill_(float("nan")), weights)
    except FloatingPointError:
        pass
    else:
        raise AssertionError("non-finite advantages must fail before PPO update")

    rms = RunningMeanStd(2)
    try:
        rms.update(torch.tensor([[0.0, float("inf")]]))
    except FloatingPointError:
        pass
    else:
        raise AssertionError("non-finite observations must not poison running statistics")

    # The actor and the environment must use the same bounded action.  In
    # particular, PPO must recompute the density of the action that PhysX saw,
    # including the tanh change-of-variables Jacobian.
    torch.manual_seed(7)
    init_action = torch.tensor([-0.8, 0.0, 0.75])
    model = ActorCritic(5, 3, value_dim=2, init_std=0.2,
                        init_mean=init_action)
    obs = torch.zeros(32, 5)
    deterministic, det_logp, _ = model.act(obs, deterministic=True)
    assert torch.allclose(deterministic[0], init_action, atol=2e-6)
    assert (deterministic.abs() < 1.0).all()

    sampled, sampled_logp, _ = model.act(obs)
    assert (sampled.abs() < 1.0).all()
    reevaluated_logp, entropy, value = model.evaluate_actions(obs, sampled)
    assert torch.allclose(sampled_logp, reevaluated_logp, atol=2e-5)
    assert torch.isfinite(entropy).all() and torch.isfinite(value).all()

    all_actions = torch.ones_like(sampled, dtype=torch.bool)
    all_logp, _, _ = model.evaluate_actions(
        obs, sampled, action_mask=all_actions)
    assert torch.allclose(all_logp, reevaluated_logp, atol=2e-5)

    two_actions = all_actions.clone()
    two_actions[:, 2] = False
    masked_logp, _, _ = model.evaluate_actions(
        obs, sampled, action_mask=two_actions)
    changed_inactive = sampled.clone()
    changed_inactive[:, 2] = -changed_inactive[:, 2]
    changed_logp, _, _ = model.evaluate_actions(
        obs, changed_inactive, action_mask=two_actions)
    assert torch.allclose(masked_logp, changed_logp, atol=2e-5)

    # Even an exact boundary supplied by an external caller remains numerically
    # finite; policy-generated actions themselves are strictly interior.
    edge = torch.tensor([[1.0, -1.0, 0.0]]).expand(4, -1)
    edge_logp, edge_entropy, _ = model.evaluate_actions(obs[:4], edge)
    assert torch.isfinite(edge_logp).all()
    assert torch.isfinite(edge_entropy).all()

    # The narrow safety-first policy uses an actor learning rate independent of
    # the faster critic, and an already-excessive KL must prevent mutation.
    env = _EnvStub()
    guarded_model = ActorCritic(5, 3, value_dim=6, init_std=0.02,
                                init_mean=torch.zeros(3))
    config = PPOConfig(horizon=1, epochs=1, minibatch_size=4,
                       actor_learning_rate=1e-5, learning_rate=3e-4,
                       target_kl=0.03)
    trainer = PPOTrainer(env, guarded_model, config)
    assert [group["lr"] for group in trainer.optimizer.param_groups] == [1e-5, 3e-4]
    with torch.no_grad():
        action, current_logp, value = guarded_model.act(trainer.obs)
        next_value = guarded_model.value(trainer.obs)
    rollout = {
        "obs": trainer.obs.unsqueeze(0),
        "actions": action.unsqueeze(0),
        # Force the current-policy KL estimate to one, far outside the gate.
        "logp": (current_logp + 1.0).unsqueeze(0),
        "values": value.unsqueeze(0),
        "rewards": torch.zeros(1, env.num_envs, env.value_dim),
        "dones": torch.zeros(1, env.num_envs, dtype=torch.bool),
        "next_value": next_value,
        "episode": [],
    }
    before = [parameter.detach().clone()
              for parameter in guarded_model.parameters()]
    stats = trainer.update(rollout)
    after = list(guarded_model.parameters())
    assert all(torch.equal(old, new) for old, new in zip(before, after))
    assert stats["kl"] == 0.0

    # Rollout observations must be snapshots. Isaac Gym exposes a reusable
    # obs_buf, so storing the raw reference would turn every historical frame
    # into the final observation and make the PPO pre-update KL invalid.
    reused_env = _ReusedObservationEnv()
    reused_model = ActorCritic(5, 3, value_dim=6, init_std=0.2,
                               init_mean=torch.zeros(3))
    reused_trainer = PPOTrainer(
        reused_env, reused_model,
        PPOConfig(horizon=3, epochs=1, minibatch_size=6))
    reused_rollout = reused_trainer.collect()
    expected_frames = torch.tensor([0.0, 1.0, 2.0])
    assert torch.equal(reused_rollout["obs"][:, 0, 0], expected_frames)
    assert reused_rollout["next_value"].shape == (2, 6)

    masked_env = _MaskedObservationEnv()
    masked_model = ActorCritic(5, 3, value_dim=6, init_std=0.2,
                               init_mean=torch.zeros(3))
    masked_trainer = PPOTrainer(
        masked_env, masked_model,
        PPOConfig(horizon=3, epochs=1, minibatch_size=6))
    masked_rollout = masked_trainer.collect()
    expected_mask = masked_env.policy_action_mask()
    assert torch.equal(
        masked_rollout["action_masks"],
        expected_mask.unsqueeze(0).expand(3, -1, -1))
    recomputed, _, _ = masked_model.evaluate_actions(
        masked_rollout["obs"].reshape(-1, 5),
        masked_rollout["actions"].reshape(-1, 3),
        action_mask=masked_rollout["action_masks"].reshape(-1, 3))
    assert torch.allclose(
        recomputed, masked_rollout["logp"].reshape(-1), atol=2e-5)

    print("PASS: actor advantages and finite PPO guards")


if __name__ == "__main__":
    main()
