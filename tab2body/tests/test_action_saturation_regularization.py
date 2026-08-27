"""선택 action의 PPO mean 포화 정규화 회귀 검사."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACKAGE_PARENT = ROOT.parent
if str(PACKAGE_PARENT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_PARENT))

import torch

from cfg import FRET
from learning.models import ActorCritic
from learning.ppo import (
    PPOConfig,
    PPOTrainer,
    action_saturation_regularization,
    masked_action_teacher_loss,
)
from strike_cfg import STRIKE


class _GoalStub:
    fret = torch.tensor([[0.0, 1.0, 1.0, 0.0, 0.0, 0.0]])


class _EnvStub:
    def __init__(self, expose_indices=False):
        self.device = "cpu"
        self.num_envs = 4
        self.num_obs = 5
        self.num_actions = 3
        self.value_dim = 6
        self.reward_weights = torch.full((6,), 1.0 / 6.0)
        self.goals = _GoalStub()
        if expose_indices:
            self.action_saturation_regularization_indices = (0, 2)

    def reset(self):
        return torch.zeros(self.num_envs, self.num_obs)


def _expect(exception, function):
    try:
        function()
    except exception:
        return
    raise AssertionError(f"expected {exception.__name__}")


def _rollout(trainer, action_mask=None):
    with torch.no_grad():
        action, logp, value = trainer.model.act(
            trainer.obs, deterministic=True, action_mask=action_mask)
        next_value = trainer.model.value(trainer.obs)
    rollout = {
        "obs": trainer.obs.unsqueeze(0),
        "actions": action.unsqueeze(0),
        "logp": logp.unsqueeze(0),
        "values": value.unsqueeze(0),
        "rewards": torch.zeros(
            1, trainer.env.num_envs, trainer.env.value_dim),
        "dones": torch.zeros(
            1, trainer.env.num_envs, dtype=torch.bool),
        "next_value": next_value,
        "episode": [],
    }
    if action_mask is not None:
        rollout["action_masks"] = action_mask.unsqueeze(0)
    return rollout


def main():
    mean_action = torch.tensor(
        [[0.95, 0.40, -0.99], [0.89, -0.91, 0.20]],
        requires_grad=True)
    mask = torch.tensor(
        [[True, True, True], [False, True, False]])
    loss = action_saturation_regularization(
        mean_action, (0, 2), 0.90, action_mask=mask)
    assert torch.allclose(loss, torch.tensor(0.53), atol=1e-6)
    loss.backward()
    assert mean_action.grad[0, 0] > 0.0
    assert mean_action.grad[0, 2] < 0.0
    assert mean_action.grad[1].abs().sum() == 0.0

    all_masked = torch.zeros_like(mask)
    masked_action = mean_action.detach().clone().requires_grad_(True)
    masked_loss = action_saturation_regularization(
        masked_action, (0, 2), 0.90, action_mask=all_masked)
    assert masked_loss == 0.0
    masked_loss.backward()
    assert torch.equal(masked_action.grad, torch.zeros_like(masked_action))

    _expect(
        ValueError,
        lambda: action_saturation_regularization(
            torch.zeros(3), (0,), 0.90))
    _expect(
        FloatingPointError,
        lambda: action_saturation_regularization(
            torch.tensor([[float("nan"), 0.0]]), (0,), 0.90))
    _expect(
        ValueError,
        lambda: action_saturation_regularization(
            torch.zeros(2, 3), (0,), 0.90,
            action_mask=torch.ones(2, 2, dtype=torch.bool)))
    _expect(
        IndexError,
        lambda: action_saturation_regularization(
            torch.zeros(2, 3), (3,), 0.90))

    teacher_mean = torch.zeros(2, 3, requires_grad=True)
    teacher_target = torch.tensor(
        [[0.5, -0.5, 0.0], [0.0, 0.0, 0.8]])
    teacher_mask = torch.tensor(
        [[True, False, False], [False, False, True]])
    teacher_loss = masked_action_teacher_loss(
        teacher_mean, teacher_target, teacher_mask)
    assert torch.isclose(teacher_loss, torch.tensor(0.445))
    teacher_loss.backward()
    assert teacher_mean.grad[0, 0] < 0.0
    assert teacher_mean.grad[1, 2] < 0.0
    assert teacher_mean.grad[0, 1] == 0.0

    # 자주 등장하는 action이 희귀 action의 교사 기울기를 희석하지 않는다.
    imbalanced_mean = torch.zeros(4, 2, requires_grad=True)
    imbalanced_target = torch.tensor(
        [[0.1, 1.0], [0.1, 0.0], [0.1, 0.0], [0.1, 0.0]])
    imbalanced_mask = torch.tensor(
        [[True, True], [True, False], [True, False], [True, False]])
    imbalanced_loss = masked_action_teacher_loss(
        imbalanced_mean, imbalanced_target, imbalanced_mask)
    assert torch.isclose(imbalanced_loss, torch.tensor(0.505))
    imbalanced_loss.backward()
    assert imbalanced_mean.grad[0, 1].abs() > (
        imbalanced_mean.grad[:, 0].abs().sum())

    assert PPOConfig().action_saturation_regularization_weight == 0.0
    assert PPOConfig().action_teacher_weight == 0.0
    strike_ppo = PPOConfig(**STRIKE["ppo"])
    assert strike_ppo.action_saturation_regularization_weight == 0.0
    assert FRET["ppo"]["action_saturation_regularization_weight"] == 0.01
    assert FRET["ppo"]["action_saturation_regularization_threshold"] == 0.80
    assert FRET["ppo"]["action_teacher_weight"] == 0.05

    # Weight 0은 환경 index를 요구하거나 actor mean을 추가 평가하지 않는다.
    legacy_env = _EnvStub(expose_indices=False)
    legacy_model = ActorCritic(
        5, 3, value_dim=6, init_std=0.2,
        init_mean=torch.tensor([0.99, 0.0, -0.99]))
    legacy_trainer = PPOTrainer(
        legacy_env, legacy_model,
        PPOConfig(
            horizon=1, epochs=1, minibatch_size=4,
            entropy_coef=0.0,
            action_saturation_regularization_weight=0.0))
    legacy_stats = legacy_trainer.update(_rollout(legacy_trainer))
    assert legacy_stats["action_saturation_loss"] == 0.0

    # 정규화는 hard action을 바꾸지 않고 선택 mean의 경계 초과만 안쪽으로 민다.
    regularized_env = _EnvStub(expose_indices=True)
    regularized_model = ActorCritic(
        5, 3, value_dim=6, init_std=0.2,
        init_mean=torch.tensor([0.99, 0.0, -0.99]))
    regularized_trainer = PPOTrainer(
        regularized_env, regularized_model,
        PPOConfig(
            horizon=1, epochs=1, minibatch_size=4,
            entropy_coef=0.0, actor_learning_rate=1e-2,
            target_kl=1.0,
            action_saturation_regularization_weight=0.002,
            action_saturation_regularization_threshold=0.90))
    before = torch.tanh(
        regularized_model.distribution(regularized_trainer.obs).mean)[0]
    regularized_stats = regularized_trainer.update(
        _rollout(regularized_trainer))
    after = torch.tanh(
        regularized_model.distribution(regularized_trainer.obs).mean)[0]
    assert regularized_stats["action_saturation_loss"] > 0.0
    assert after[0].abs() < before[0].abs()
    assert after[2].abs() < before[2].abs()

    teacher_env = _EnvStub(expose_indices=False)
    teacher_model = ActorCritic(
        5, 3, value_dim=6, init_std=0.2,
        init_mean=torch.zeros(3))
    teacher_trainer = PPOTrainer(
        teacher_env, teacher_model,
        PPOConfig(
            horizon=1, epochs=1, minibatch_size=4,
            entropy_coef=0.0, actor_learning_rate=1e-2,
            target_kl=1.0, action_teacher_weight=0.10))
    teacher_rollout = _rollout(teacher_trainer)
    teacher_rollout["teacher_actions"] = torch.zeros(1, 4, 3)
    teacher_rollout["teacher_actions"][..., 1] = 0.8
    teacher_rollout["teacher_masks"] = torch.zeros(
        1, 4, 3, dtype=torch.bool)
    teacher_rollout["teacher_masks"][..., 1] = True
    before_teacher = torch.tanh(
        teacher_model.distribution(teacher_trainer.obs).mean)[0, 1]
    teacher_stats = teacher_trainer.update(teacher_rollout)
    after_teacher = torch.tanh(
        teacher_model.distribution(teacher_trainer.obs).mean)[0, 1]
    assert teacher_stats["action_teacher_loss"] > 0.0
    assert after_teacher > before_teacher

    print("PASS: PPO action saturation regularization")


if __name__ == "__main__":
    main()
