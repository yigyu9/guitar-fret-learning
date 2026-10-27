"""CPU checks for appended fret observation warm-start contracts."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.models import ActorCritic
from train_fret import (
    finger_acquisition_schedule,
    finger_exploration_ceiling,
    finger_precision_schedule,
    load_fret_initialization_model,
    summarize_goal_finger_coverage,
    thumb_base_exploration_floor,
)


def expect_value_error(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def main():
    assert thumb_base_exploration_floor(1, 0.05, 0.10, 200, 800) == 0.05
    assert thumb_base_exploration_floor(200, 0.05, 0.10, 200, 800) == 0.05
    assert torch.isclose(torch.tensor(
        thumb_base_exploration_floor(600, 0.05, 0.10, 200, 800)),
        torch.tensor(0.075))
    assert thumb_base_exploration_floor(
        1000, 0.05, 0.10, 200, 800) == 0.10

    assert finger_exploration_ceiling(0, 0.08, 0.025, 25, 300) == 0.08
    assert finger_exploration_ceiling(25, 0.08, 0.025, 25, 300) == 0.08
    assert torch.isclose(torch.tensor(
        finger_exploration_ceiling(175, 0.08, 0.025, 25, 300)),
        torch.tensor(0.0525))
    assert finger_exploration_ceiling(
        325, 0.08, 0.025, 25, 300) == 0.025
    assert finger_exploration_ceiling(
        1000, 0.08, 0.025, 25, 300) == 0.025
    expect_value_error(
        lambda: finger_exploration_ceiling(0, 0.08, 0.09, 25, 300))
    expect_value_error(
        lambda: finger_exploration_ceiling(0, 0.08, 0.025, -1, 300))
    expect_value_error(
        lambda: finger_exploration_ceiling(0, 0.08, 0.025, 25, 0))

    assert finger_precision_schedule({
        "curriculum_stage": "fine_reach",
    }) == (False, 0, ())
    assert finger_precision_schedule({
        "curriculum_stage": "chord_fine_reach",
        "curriculum_chord_focus_total_iteration": 175,
        "curriculum_chord_focus_index": 1,
        "curriculum_chord_available_sets": [[1, 2], [1, 3]],
    }) == (False, 0, ())
    assert finger_acquisition_schedule({
        "curriculum_stage": "chord_fine_reach",
        "curriculum_chord_focus_index": 1,
        "curriculum_chord_available_sets": [[1, 2], [1, 3]],
    }) == (True, (1, 3))
    assert finger_precision_schedule({
        "curriculum_stage": "static_chord",
        "curriculum_chord_focus_total_iteration": 325,
        "curriculum_stage_iteration": 20,
    }) == (False, 0, ())
    assert finger_acquisition_schedule({
        "curriculum_stage": "static_chord",
    }) == (True, ())
    assert finger_acquisition_schedule({
        "curriculum_stage": "isolated_press",
    }) == (True, ())
    assert finger_acquisition_schedule({
        "curriculum_stage": "isolated_press",
        "curriculum_early_recovery": True,
        "curriculum_early_recovery_focus_finger": 4,
    }) == (True, (4,))
    assert finger_precision_schedule({
        "curriculum_stage": "goal_pair",
        "curriculum_chord_focus_total_iteration": 325,
        "curriculum_stage_iteration": 20,
        "curriculum_goal_pair_focus_finger": 4,
    }) == (True, 20, (4,))

    class FakeGoals:
        fret = torch.tensor([
            [3, 0, 0, 0, 0, 0],
            [3, 5, 0, 0, 0, 0],
            [0, 5, 7, 0, 0, 0],
        ])
        finger = torch.tensor([
            [1, 0, 0, 0, 0, 0],
            [1, 2, 0, 0, 0, 0],
            [0, 2, 4, 0, 0, 0],
        ])
        sustain_events = (
            {"finger": 1, "string": 0, "fret": 3},
            {"finger": 2, "string": 1, "fret": 5},
            {"finger": 4, "string": 2, "fret": 7},
        )
        practice_chord_frames_by_finger_set = {
            (1, 2): torch.tensor([1]),
            (2, 4): torch.tensor([2]),
        }

    coverage = summarize_goal_finger_coverage(FakeGoals())
    assert coverage["fingers"]["index"]["active_frames"] == 2
    assert coverage["fingers"]["middle"]["stable_chord_runs"] == 2
    assert coverage["fingers"]["ring"]["active_frames"] == 0
    assert set(coverage["underrepresented_fingers"]) == {
        "index", "middle", "ring", "pinky"}

    torch.manual_seed(17)
    source = ActorCritic(
        347, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    with torch.no_grad():
        source.obs_rms.mean.copy_(torch.linspace(-2.0, 2.0, 347))
        source.obs_rms.var.copy_(torch.linspace(0.5, 1.5, 347))
        source.obs_rms.count.fill_(1234.0)
    source_state = {
        key: value.detach().clone()
        for key, value in source.state_dict().items()
    }

    target = ActorCritic(
        353, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    report = load_fret_initialization_model(target, source_state)
    assert report == {
        "expanded": True,
        "source_obs_dim": 347,
        "target_obs_dim": 353,
    }
    loaded = target.state_dict()
    assert torch.equal(loaded["obs_rms.mean"][:347], source_state["obs_rms.mean"])
    assert torch.equal(loaded["obs_rms.var"][:347], source_state["obs_rms.var"])
    assert torch.equal(
        loaded["obs_rms.mean"][347:], torch.zeros(6))
    assert torch.equal(
        loaded["obs_rms.var"][347:], torch.ones(6))
    assert torch.equal(loaded["obs_rms.count"], source_state["obs_rms.count"])
    for key in ("actor.0.weight", "critic.0.weight"):
        assert torch.equal(loaded[key][:, :347], source_state[key])
        assert torch.equal(
            loaded[key][:, 347:], torch.zeros_like(loaded[key][:, 347:]))
    for key in loaded:
        if key not in (
                "obs_rms.mean", "obs_rms.var",
                "actor.0.weight", "critic.0.weight"):
            assert torch.equal(loaded[key], source_state[key]), key

    prefix = torch.randn(7, 347)
    derived_thumb = torch.randn(7, 6)
    with torch.no_grad():
        source_normalized = source.normalized(prefix)
        target_normalized = target.normalized(
            torch.cat([prefix, derived_thumb], dim=-1))
        assert torch.allclose(
            target.actor(target_normalized),
            source.actor(source_normalized), atol=1e-6, rtol=1e-6)
        assert torch.allclose(
            target.critic(target_normalized),
            source.critic(source_normalized), atol=1e-6, rtol=1e-6)

    calibrated = ActorCritic(
        353, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    calibration = torch.randn(257, 353)
    calibration[:, 347:] = (
        0.25 * calibration[:, 347:]
        + torch.linspace(-0.3, 0.3, 6))
    calibrated_report = load_fret_initialization_model(
        calibrated, source_state,
        calibration_observations=calibration)
    assert calibrated_report == {
        "expanded": True,
        "source_obs_dim": 347,
        "target_obs_dim": 353,
    }
    calibrated_state = calibrated.state_dict()
    suffix = calibration[:, 347:]
    assert torch.equal(
        calibrated_state["obs_rms.mean"][:347],
        source_state["obs_rms.mean"])
    assert torch.equal(
        calibrated_state["obs_rms.var"][:347],
        source_state["obs_rms.var"])
    assert torch.allclose(
        calibrated_state["obs_rms.mean"][347:],
        suffix.mean(dim=0))
    assert torch.allclose(
        calibrated_state["obs_rms.var"][347:],
        suffix.var(dim=0, unbiased=False))
    assert torch.equal(
        calibrated_state["obs_rms.count"],
        source_state["obs_rms.count"])
    normalized_suffix = calibrated.normalized(calibration)[:, 347:]
    assert torch.allclose(
        normalized_suffix.mean(dim=0),
        torch.zeros(6), atol=1e-6, rtol=0.0)
    assert torch.allclose(
        normalized_suffix.var(dim=0, unbiased=False),
        torch.ones(6), atol=1e-5, rtol=0.0)
    with torch.no_grad():
        assert torch.allclose(
            calibrated.actor(calibrated.normalized(calibration)),
            source.actor(source.normalized(calibration[:, :347])),
            atol=1e-6, rtol=1e-6)

    source_341 = ActorCritic(
        341, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    with torch.no_grad():
        source_341.obs_rms.mean.copy_(torch.linspace(-1.0, 1.0, 341))
        source_341.obs_rms.var.copy_(torch.linspace(0.4, 1.4, 341))
        source_341.obs_rms.count.fill_(4321.0)
    source_341_state = {
        key: value.detach().clone()
        for key, value in source_341.state_dict().items()
    }
    target_353 = ActorCritic(
        353, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    calibration_12 = torch.randn(193, 353)
    report_12 = load_fret_initialization_model(
        target_353, source_341_state,
        calibration_observations=calibration_12)
    assert report_12 == {
        "expanded": True,
        "source_obs_dim": 341,
        "target_obs_dim": 353,
    }
    assert torch.equal(
        target_353.actor[0].weight[:, :341],
        source_341.actor[0].weight)
    assert torch.equal(
        target_353.actor[0].weight[:, 341:],
        torch.zeros_like(target_353.actor[0].weight[:, 341:]))
    normalized_12 = target_353.normalized(calibration_12)[:, 341:]
    assert torch.allclose(
        normalized_12.mean(dim=0),
        torch.zeros(12), atol=1e-6, rtol=0.0)
    assert torch.allclose(
        normalized_12.var(dim=0, unbiased=False),
        torch.ones(12), atol=1e-5, rtol=0.0)
    with torch.no_grad():
        assert torch.allclose(
            target_353.actor(target_353.normalized(calibration_12)),
            source_341.actor(source_341.normalized(calibration_12[:, :341])),
            atol=1e-6, rtol=1e-6)

    same_size = ActorCritic(
        353, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    same_report = load_fret_initialization_model(
        same_size, target.state_dict())
    assert same_report == {
        "expanded": False,
        "source_obs_dim": 353,
        "target_obs_dim": 353,
    }
    for key, value in target.state_dict().items():
        assert torch.equal(same_size.state_dict()[key], value), key

    current_prefix = ActorCritic(
        350, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    current_prefix_state = {
        key: value.detach().clone()
        for key, value in current_prefix.state_dict().items()
    }
    future_context_target = ActorCritic(
        425, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    future_context_calibration = torch.randn(128, 425)
    future_report = load_fret_initialization_model(
        future_context_target, current_prefix_state,
        appended_obs_dim=75,
        calibration_observations=future_context_calibration)
    assert future_report == {
        "expanded": True,
        "source_obs_dim": 350,
        "target_obs_dim": 425,
    }
    assert torch.equal(
        future_context_target.actor[0].weight[:, :350],
        current_prefix.actor[0].weight)
    assert torch.equal(
        future_context_target.actor[0].weight[:, 350:],
        torch.zeros_like(
            future_context_target.actor[0].weight[:, 350:]))
    with torch.no_grad():
        assert torch.allclose(
            future_context_target.actor(
                future_context_target.normalized(
                    future_context_calibration)),
            current_prefix.actor(current_prefix.normalized(
                future_context_calibration[:, :350])),
            atol=1e-6, rtol=1e-6)

    wrong_size = ActorCritic(
        354, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    expect_value_error(
        lambda: load_fret_initialization_model(wrong_size, source_state))
    too_many = ActorCritic(
        365, 5, value_dim=2,
        actor_hidden=(16, 8), critic_hidden=(16, 8), init_std=0.2)
    expect_value_error(
        lambda: load_fret_initialization_model(too_many, source_state))
    expect_value_error(
        lambda: load_fret_initialization_model(
            target, source_state, appended_obs_dim=12))
    expect_value_error(
        lambda: load_fret_initialization_model(
            calibrated, source_state,
            calibration_observations=torch.randn(7, 5)))
    nonfinite = calibration.clone()
    nonfinite[0, -1] = float("nan")
    expect_value_error(
        lambda: load_fret_initialization_model(
            calibrated, source_state,
            calibration_observations=nonfinite))
    malformed = dict(source_state)
    malformed["actor.2.bias"] = malformed["actor.2.bias"][:-1]
    expect_value_error(
        lambda: load_fret_initialization_model(target, malformed))
    print("PASS: appended fret observations preserve the old policy")


if __name__ == "__main__":
    main()
