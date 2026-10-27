"""Frozen-context calibration episode 분리 집계 CPU 회귀 검사."""
from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- torch보다 먼저 import해야 한다.
import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.tasks.task_fret import (
    FRET_CONTROL_PREFIXES,
    FRET_POLICY_ACTION_DIM,
    JOINT_LIMIT_GROUP_PREFIXES,
    FretTask,
    fret_episode_target_evidence,
    frozen_context_eval_episode_eligibility,
    frozen_context_teacher_cohort_mask,
    frozen_context_training_cohort_mask,
)
from learning.models import ActorCritic
from learning.ppo import (
    PPOConfig,
    PPOTrainer,
    ROLLOUT_DIAGNOSTIC_KEYS,
    aggregate_episode_rows,
)


METRIC_KEYS = (
    "f1_l", "no_press_correct_count", "no_press_evidence_count",
    "press_finger_1_success", "press_finger_1_count",
    "press_finger_1_target_distance_sum",
    "press_finger_1_target_distance_count",
    "thumb_press_readiness_sum", "thumb_press_readiness_count",
)
REASON_KEYS = ("goal_finished",)


def _row(
        f1, success, count, eligible, goal_finished=1.0, *,
        distance=0.01, distance_count=None,
        thumb_readiness=0.5, thumb_count=None):
    distance_count = count if distance_count is None else distance_count
    thumb_count = count if thumb_count is None else thumb_count
    return {
        "f1_l": float(f1),
        "no_press_correct_count": float(count - success),
        "no_press_evidence_count": float(count),
        "press_finger_1_success": float(success),
        "press_finger_1_count": float(count),
        "press_finger_1_target_distance_sum": float(
            distance * distance_count),
        "press_finger_1_target_distance_count": float(distance_count),
        "thumb_press_readiness_sum": float(
            thumb_readiness * thumb_count),
        "thumb_press_readiness_count": float(thumb_count),
        "goal_finished": float(goal_finished),
        "frozen_context_eval_eligible": float(eligible),
    }


class _TensorMaskGoals:
    def __init__(self):
        self.frozen_context_eval_mask = torch.tensor(
            [True, False, True, False])

    def set_curriculum_stage(self, stage, duration_frames=None):
        self.curriculum_stage = str(stage)
        self.duration_frames = duration_frames


class _CalibrationMaskGoals:
    frozen_context_calibration_mask = torch.tensor(
        [False, True, False, True])


class _SelectedMaskGoals:
    def frozen_context_eval_mask(self, env_ids):
        return env_ids.remainder(2) == 0


class _FullCallableMaskGoals:
    def frozen_context_eval_mask(self):
        return torch.tensor([False, True, False, True])


class _RecoveryControl:
    set_frozen_context_recovery = FretTask.set_frozen_context_recovery


class _EmptyEpisodeHarness:
    _episode_metrics = FretTask._episode_metrics
    device = "cpu"


class _TargetAccumulatorHarness:
    _reset_episode_target_evidence = (
        FretTask._reset_episode_target_evidence)

    def __init__(self):
        self.metric_finger_target_distance_sum = torch.ones(3, 4)
        self.metric_finger_target_distance_count = torch.ones(3, 4)
        self.metric_thumb_press_readiness_sum = torch.ones(3)
        self.metric_thumb_press_readiness_count = torch.ones(3)


class _CachedTeacherCohort:
    set_frozen_context_recovery = FretTask.set_frozen_context_recovery
    set_curriculum_stage = FretTask.set_curriculum_stage
    _frozen_context_training_cohort = (
        FretTask._frozen_context_training_cohort)
    _frozen_context_teacher_cohort = FretTask._frozen_context_teacher_cohort

    def __init__(self):
        self.device = "cpu"
        self.num_envs = 4
        self.goals = _TensorMaskGoals()
        self.curriculum_stage = "static_chord"
        self.frozen_context_recovery_active = False
        self.frozen_context_recovery_teacher_scale = 0.0
        self._frozen_context_teacher_cohort_key = torch.tensor(
            [0.1, 0.2, 0.3, 0.8])
        self._frozen_context_training_cohort_cache = torch.ones(
            4, dtype=torch.bool)
        self._frozen_context_teacher_cohort_cache = torch.zeros(
            4, dtype=torch.bool)
        self.refresh_count = 0

    def _refresh_frozen_context_teacher_cohort(self):
        self.refresh_count += 1
        FretTask._refresh_frozen_context_teacher_cohort(self)


class _FrozenTeacherHarness:
    _success_pose_policy_teacher = FretTask._success_pose_policy_teacher

    def __init__(self):
        self.device = "cpu"
        self.num_envs = 4
        self.num_actions = 18
        self.curriculum_stage = "frozen_context"
        self.integrated_press_recovery = False
        self.frozen_context_recovery_active = True
        self.frozen_context_recovery_teacher_scale = 0.5
        self.chord_fine_action_teacher_min_pose_quality = 0.2
        self.success_action_teacher_min_pose_quality = 0.7
        self._whole_pose_teacher_active = torch.zeros(
            self.num_envs, dtype=torch.bool)
        self._whole_pose_teacher_weakest_finger = torch.zeros(
            self.num_envs, dtype=torch.long)
        self._finger_pose_action_indices = torch.arange(16).reshape(4, 4)
        self._finger_pose_proximal_action_indices = torch.tensor([16, 17])
        self._success_finger_action = torch.arange(
            16, dtype=torch.float32).reshape(1, 4, 4)
        self._success_finger_action_valid = torch.ones(
            1, 4, dtype=torch.bool)
        self._teacher_cohort = torch.tensor(
            [False, True, False, False])

    def _frozen_context_teacher_cohort(self):
        return self._teacher_cohort


class _SuccessRSIGoals:
    pose_slot_count = 1
    frame_idx = torch.zeros(4, dtype=torch.long)
    frame_pose_slot = torch.zeros(1, dtype=torch.long)
    frozen_context_eval_mask = torch.tensor(
        [True, False, True, False])
    # Episode-local sampling state may already describe the next episode when
    # RSI is applied.  It must not override the persistent cohort assignment.
    frozen_context_calibration_sample = torch.zeros(4, dtype=torch.bool)


class _SuccessRSIHarness:
    _apply_success_rsi = FretTask._apply_success_rsi
    _restore_thorax_hold = FretTask._restore_thorax_hold

    def __init__(self, stage="frozen_context", recovery_active=True,
                 teacher_scale=1.0):
        self.device = "cpu"
        self.num_envs = 4
        self.n_dof = 3
        self._thorax_dof_indices = torch.tensor([0])
        self.init_pose = torch.tensor([0.1, 0.0, 0.0])
        self.curriculum_stage = stage
        self.frozen_context_recovery_active = bool(recovery_active)
        self.frozen_context_recovery_teacher_scale = float(teacher_scale)
        self.integrated_press_recovery = False
        self.goals = _SuccessRSIGoals()
        self.success_rsi_probability = 1.0
        self.success_discovery_rsi_probability = 0.0
        self.success_rsi_reset = torch.zeros(4, dtype=torch.bool)
        self.success_rsi_reset_quality = torch.zeros(4)
        self._success_pose_valid = torch.ones(1, dtype=torch.bool)
        self._discovery_pose_valid = torch.zeros(1, dtype=torch.bool)
        self._success_pose_q = torch.tensor([[0.9, 0.25, 0.75]])
        self._discovery_pose_q = torch.zeros(1, 3)
        self._success_pose_body_obs = torch.tensor([[1.0, 2.0, 3.0]])
        self._discovery_pose_body_obs = torch.zeros(1, 3)
        self._success_pose_thumb_obs = torch.tensor([[4.0, 5.0]])
        self._discovery_pose_thumb_obs = torch.zeros(1, 2)
        self._success_pose_quality = torch.tensor([0.9])
        self._discovery_pose_quality = torch.zeros(1)
        self._reset_body_obs = torch.zeros(4, 3)
        self._reset_thumb_obs = torch.zeros(4, 2)
        self.dof_state = torch.zeros(4 * 3 * 2)
        self.pd_target = torch.zeros(4 * 3)
        self.rng = torch.Generator().manual_seed(7)

    def _frozen_context_teacher_cohort(self):
        training = ~self.goals.frozen_context_eval_mask
        cohort_key = torch.tensor([0.1, 0.2, 0.3, 0.8])
        return training & (
            cohort_key < self.frozen_context_recovery_teacher_scale)


class _RolloutGoals:
    fret = torch.tensor([[1.0, 0.0, 0.0, 0.0, 0.0, 0.0]])


class _TaggedEpisodeEnv:
    device = "cpu"
    num_envs = 2
    num_obs = 3
    num_actions = 2
    value_dim = 6
    reward_weights = torch.full((6,), 1.0 / 6.0)
    goals = _RolloutGoals()
    episode_metric_keys = ("f1_l",)
    episode_reason_keys = ()
    rollout_diagnostic_keys = ()

    def reset(self):
        return torch.zeros(self.num_envs, self.num_obs)

    def step(self, action):
        del action
        return (
            torch.ones(self.num_envs, self.num_obs),
            torch.zeros(self.num_envs, self.value_dim),
            torch.ones(self.num_envs, dtype=torch.bool),
            {
                "f1_l": torch.tensor([0.9, 0.2]),
                "episode_frozen_context_eval_eligible":
                    torch.tensor([True, False]),
            },
        )


def main():
    assert FRET_POLICY_ACTION_DIM == 30
    assert "L_Thorax" not in FRET_CONTROL_PREFIXES
    assert JOINT_LIMIT_GROUP_PREFIXES[0] == ("shoulder", "L_Shoulder")
    assert all(group != "thorax"
               for group, _ in JOINT_LIMIT_GROUP_PREFIXES)

    rows = [
        _row(
            1.0, 8.0, 10.0, True,
            distance=0.02, distance_count=2,
            thumb_readiness=0.2, thumb_count=2),
        _row(
            0.0, 1.0, 10.0, False, goal_finished=0.0,
            distance=0.09, distance_count=10,
            thumb_readiness=0.9, thumb_count=10),
        _row(
            0.5, 3.0, 5.0, True,
            distance=0.04, distance_count=6,
            thumb_readiness=0.6, thumb_count=6),
    ]
    result = aggregate_episode_rows(rows, METRIC_KEYS, REASON_KEYS)
    frozen_eval = result["_frozen_eval"]
    frozen_train = result["_frozen_train"]
    assert result["episodes"] == 3
    assert result["frozen_eval_episodes"] == 2
    assert result["frozen_train_episodes"] == 1
    assert abs(result["frozen_eval_fraction"] - 2.0 / 3.0) < 1e-9
    assert abs(result["frozen_train_fraction"] - 1.0 / 3.0) < 1e-9
    assert frozen_eval["episodes"] == 2
    assert frozen_eval["f1_l"] == 0.75
    assert frozen_eval["finger_1_press_success_frames"] == 11
    assert frozen_eval["finger_1_press_target_frames"] == 15
    assert abs(
        frozen_eval["finger_1_press_success_rate"] - 11.0 / 15.0
    ) < 1e-9
    assert result["frozen_eval_f1_l"] == 0.75
    assert abs(
        result["frozen_eval_finger_1_press_success_rate"] - 11.0 / 15.0
    ) < 1e-9
    assert result["frozen_eval_finger_1_press_target_frames"] == 15
    assert frozen_eval["finger_1_target_distance_active_frames"] == 8
    assert abs(frozen_eval["finger_1_target_distance_sum"] - 0.28) < 1e-9
    assert abs(frozen_eval["finger_1_target_distance_mean"] - 0.035) < 1e-9
    assert abs(
        frozen_eval["curriculum_finger_1_target_distance"] - 0.035
    ) < 1e-9
    assert frozen_train["finger_1_target_distance_active_frames"] == 10
    assert abs(frozen_train["finger_1_target_distance_mean"] - 0.09) < 1e-9
    assert abs(result["frozen_eval_thumb_press_readiness"] - 0.5) < 1e-9
    assert abs(result["frozen_train_thumb_press_readiness"] - 0.9) < 1e-9
    assert frozen_eval["goal_finished_count"] == 2
    assert frozen_train["episodes"] == 1
    assert frozen_train["f1_l"] == 0.0
    assert frozen_train["goal_finished_count"] == 0

    no_eval = aggregate_episode_rows(
        [_row(0.0, 0.0, 1.0, False)], METRIC_KEYS, REASON_KEYS)
    assert no_eval["frozen_eval_episodes"] == 0
    assert no_eval["_frozen_eval"] == {}
    assert no_eval["_frozen_train"]["episodes"] == 1

    untagged = dict(rows[0])
    untagged.pop("frozen_context_eval_eligible")
    plain = aggregate_episode_rows(
        [untagged], METRIC_KEYS, REASON_KEYS)
    assert "_frozen_eval" not in plain
    assert "_frozen_train" not in plain

    metrics = {
        "active": torch.tensor([
            [True, True, False], [True, False, False]]),
        "finger_assignment": torch.tensor([
            [[True, False, False, False],
             [False, True, False, False],
             [False, False, False, False]],
            [[True, False, False, False],
             [False, False, False, False],
             [False, False, False, False]],
        ]),
        "target_distance": torch.tensor([
            [0.01, 0.03, 0.00], [0.50, 0.00, 0.00]]),
        "thumb_press_readiness": torch.tensor([0.75, 0.25]),
    }
    distance_sum, distance_count, thumb_sum, thumb_count = (
        fret_episode_target_evidence(
            metrics, torch.tensor([True, False])))
    assert torch.allclose(
        distance_sum,
        torch.tensor([[0.01, 0.03, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]))
    assert distance_count.tolist() == [
        [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]]
    assert thumb_sum.tolist() == [0.75, 0.0]
    assert thumb_count.tolist() == [1.0, 0.0]
    empty_episode = _EmptyEpisodeHarness()._episode_metrics(
        torch.zeros(2, dtype=torch.bool))
    for finger in range(1, 5):
        assert empty_episode[
            f"press_finger_{finger}_target_distance_sum"].numel() == 0
        assert empty_episode[
            f"press_finger_{finger}_target_distance_count"].numel() == 0
    assert empty_episode["thumb_press_readiness_sum"].numel() == 0
    assert empty_episode["thumb_press_readiness_count"].numel() == 0
    reset_harness = _TargetAccumulatorHarness()
    reset_harness._reset_episode_target_evidence(torch.tensor([1]))
    assert not reset_harness.metric_finger_target_distance_sum[1].any()
    assert not reset_harness.metric_finger_target_distance_count[1].any()
    assert reset_harness.metric_finger_target_distance_sum[[0, 2]].all()
    assert not reset_harness.metric_thumb_press_readiness_sum[1]
    assert not reset_harness.metric_thumb_press_readiness_count[1]
    assert reset_harness.metric_thumb_press_readiness_sum[[0, 2]].all()

    ids = torch.tensor([0, 3])
    tensor_goals = _TensorMaskGoals()
    mask = frozen_context_eval_episode_eligibility(
        tensor_goals, "frozen_context", ids, 4)
    tensor_goals.frozen_context_eval_mask[0] = False
    assert mask.tolist() == [True, False]
    assert frozen_context_eval_episode_eligibility(
        _SelectedMaskGoals(), "frozen_context", ids, 4).tolist() == [
            True, False]
    assert frozen_context_eval_episode_eligibility(
        _FullCallableMaskGoals(), "frozen_context", ids, 4).tolist() == [
            False, True]
    assert frozen_context_eval_episode_eligibility(
        _CalibrationMaskGoals(), "frozen_context", ids, 4).tolist() == [
            False, True]
    assert not frozen_context_eval_episode_eligibility(
        _TensorMaskGoals(), "goal_pair", ids, 4).any()
    assert not frozen_context_eval_episode_eligibility(
        object(), "frozen_context", ids, 4).any()

    training = frozen_context_training_cohort_mask(
        _TensorMaskGoals(), 4, "cpu")
    assert training.tolist() == [False, True, False, True]
    cohort_key = torch.tensor([0.1, 0.2, 0.3, 0.8])
    half = frozen_context_teacher_cohort_mask(
        training, cohort_key, 0.5)
    full = frozen_context_teacher_cohort_mask(
        training, cohort_key, 1.0)
    assert half.tolist() == [False, True, False, False]
    assert full.tolist() == [False, True, False, True]
    assert not frozen_context_teacher_cohort_mask(
        training, cohort_key, 0.0).any()
    assert not (half & ~full).any()

    recovery = _RecoveryControl()
    recovery.set_frozen_context_recovery(True, teacher_scale=0.65)
    assert recovery.frozen_context_recovery_active
    assert recovery.frozen_context_recovery_teacher_scale == 0.65
    recovery.set_frozen_context_recovery(False, teacher_scale=1.0)
    assert not recovery.frozen_context_recovery_active
    assert recovery.frozen_context_recovery_teacher_scale == 0.0
    try:
        recovery.set_frozen_context_recovery(True, teacher_scale=1.1)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid recovery scale must fail")

    cached = _CachedTeacherCohort()
    cached.set_frozen_context_recovery(True, teacher_scale=0.5)
    cached_mask = cached._frozen_context_teacher_cohort()
    assert cached.refresh_count == 1
    assert cached._frozen_context_training_cohort().tolist() == [
        False, True, False, True]
    assert cached_mask.tolist() == [False, True, False, False]
    # curriculum.apply의 실제 순서처럼 recovery가 task stage보다 먼저
    # 설정되어도 첫 frozen-context step 전에 cohort가 준비되어야 한다.
    cached.set_curriculum_stage("frozen_context", reset=False)
    assert cached.refresh_count == 2
    assert cached._frozen_context_teacher_cohort().tolist() == [
        False, True, False, False]
    assert cached._frozen_context_teacher_cohort().data_ptr() == (
        cached_mask.data_ptr())
    cached.set_frozen_context_recovery(True, teacher_scale=0.5)
    assert cached.refresh_count == 2
    cached.set_frozen_context_recovery(True, teacher_scale=0.9)
    assert cached.refresh_count == 3
    assert cached._frozen_context_teacher_cohort().tolist() == [
        False, True, False, True]
    cached.goals.frozen_context_eval_mask = torch.tensor(
        [True, True, False, False])
    assert cached._frozen_context_teacher_cohort().tolist() == [
        False, False, True, True]
    assert cached.refresh_count == 4
    cached.set_frozen_context_recovery(False, teacher_scale=1.0)
    assert cached.refresh_count == 5
    assert not cached._frozen_context_teacher_cohort().any()

    teacher_env = _FrozenTeacherHarness()
    goal = {"finger_pose_slot": torch.zeros(4, 4, dtype=torch.long)}
    metrics = {
        "success_pose_guide_active_per_finger": torch.ones(
            4, 4, dtype=torch.bool),
        "success_pose_guide_per_finger": torch.ones(4, 4),
    }
    teacher, teacher_mask = teacher_env._success_pose_policy_teacher(
        goal, metrics)
    assert teacher_mask[1, :16].all()
    assert not teacher_mask[[0, 2, 3]].any()
    assert not teacher_mask[:, 16:].any()
    assert torch.equal(
        teacher[1, :16],
        teacher_env._success_finger_action.reshape(-1))
    assert not teacher_env._whole_pose_teacher_active.any()

    rsi_env = _SuccessRSIHarness()
    rsi_env._apply_success_rsi(torch.arange(4))
    reset_q = rsi_env.dof_state.view(4, 3, 2)[:, :, 0]
    assert not rsi_env.success_rsi_reset[[0, 2]].any()
    assert rsi_env.success_rsi_reset[[1, 3]].all()
    assert not reset_q[[0, 2]].any()
    assert torch.equal(reset_q[[1, 3], 0], torch.full((2,), 0.1))
    assert torch.equal(
        reset_q[[1, 3], 1:],
        rsi_env._success_pose_q[:, 1:].expand(2, -1))
    assert not rsi_env._reset_body_obs[[0, 2]].any()
    assert not rsi_env._reset_thumb_obs[[0, 2]].any()

    hold_env = _SuccessRSIHarness(stage="static_chord")
    hold_state = hold_env.dof_state.view(4, 3, 2)
    hold_state[:, 0, 0] = 0.8
    hold_state[:, 0, 1] = 1.2
    hold_env.pd_target.view(4, 3)[:, 0] = -0.7
    hold_env._restore_thorax_hold(torch.tensor([1, 3]))
    assert torch.equal(hold_state[[1, 3], 0, 0], torch.full((2,), 0.1))
    assert not hold_state[[1, 3], 0, 1].any()
    assert torch.equal(
        hold_env.pd_target.view(4, 3)[[1, 3], 0],
        torch.full((2,), 0.1))
    assert torch.equal(hold_state[[0, 2], 0, 0], torch.full((2,), 0.8))
    assert torch.equal(
        hold_env.pd_target.view(4, 3)[[0, 2], 0],
        torch.full((2,), -0.7))

    half_scale_rsi = _SuccessRSIHarness(teacher_scale=0.5)
    half_scale_rsi._apply_success_rsi(torch.arange(4))
    assert half_scale_rsi.success_rsi_reset.tolist() == [
        False, True, False, False]

    zero_scale_rsi = _SuccessRSIHarness(teacher_scale=0.0)
    zero_scale_rsi._apply_success_rsi(torch.arange(4))
    assert not zero_scale_rsi.success_rsi_reset.any()
    assert not zero_scale_rsi.success_rsi_reset_quality.any()
    assert not zero_scale_rsi.dof_state.any()
    assert not zero_scale_rsi._reset_body_obs.any()
    assert not zero_scale_rsi._reset_thumb_obs.any()

    post_recovery_rsi = _SuccessRSIHarness(recovery_active=False)
    post_recovery_rsi._apply_success_rsi(torch.arange(4))
    assert not post_recovery_rsi.success_rsi_reset.any()
    assert not post_recovery_rsi.success_rsi_reset_quality.any()
    assert not post_recovery_rsi.dof_state.any()
    assert not post_recovery_rsi._reset_body_obs.any()
    assert not post_recovery_rsi._reset_thumb_obs.any()

    non_frozen_rsi = _SuccessRSIHarness(stage="static_chord")
    non_frozen_rsi._apply_success_rsi(torch.arange(4))
    assert non_frozen_rsi.success_rsi_reset.all()

    model = ActorCritic(
        _TaggedEpisodeEnv.num_obs, _TaggedEpisodeEnv.num_actions,
        value_dim=_TaggedEpisodeEnv.value_dim, init_std=0.2,
        init_mean=torch.zeros(_TaggedEpisodeEnv.num_actions))
    rollout = PPOTrainer(
        _TaggedEpisodeEnv(), model,
        PPOConfig(horizon=1, epochs=1, minibatch_size=2)).collect()
    assert [
        row["frozen_context_eval_eligible"]
        for row in rollout["episode"]
    ] == [1.0, 0.0]

    expected_sampler_keys = {
        "frozen_context_sampler_weighted",
        "frozen_context_sampler_calibration_env_fraction",
        "frozen_context_sampler_calibration_active_fraction",
        "frozen_context_sampler_mix_assignment_total",
    }
    for category in ("singleton", "stable_multi", "coverage"):
        expected_sampler_keys.update({
            f"frozen_context_sampler_mix_{category}_fraction",
            f"frozen_context_sampler_mix_{category}_target_fraction",
        })
    for cohort in ("adaptive", "calibration"):
        expected_sampler_keys.update({
            f"frozen_context_sampler_{cohort}_assignment_total",
            f"frozen_context_sampler_{cohort}_max_quota_error",
            f"frozen_context_sampler_{cohort}_reset_batch_mean",
            f"frozen_context_sampler_{cohort}_reset_batch_max",
            f"frozen_context_sampler_{cohort}_singleton_reset_fraction",
        })
        for finger in range(1, 5):
            expected_sampler_keys.update({
                f"frozen_context_sampler_{cohort}_finger_{finger}_assignments",
                f"frozen_context_sampler_{cohort}_finger_{finger}_fraction",
                f"frozen_context_sampler_{cohort}_finger_{finger}_target_fraction",
            })
    assert expected_sampler_keys <= set(ROLLOUT_DIAGNOSTIC_KEYS)

    try:
        frozen_context_eval_episode_eligibility(
            type("Bad", (), {
                "frozen_context_eval_mask": torch.ones(3)})(),
            "frozen_context", ids, 4)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid frozen evaluation mask was accepted")

    print("PASS: frozen-context evaluation episode aggregation")


if __name__ == "__main__":
    main()
