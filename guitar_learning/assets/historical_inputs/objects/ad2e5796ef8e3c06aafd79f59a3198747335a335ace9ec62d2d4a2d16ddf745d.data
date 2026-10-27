from pathlib import Path
import json
import tempfile
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.learning.periodic_checkpoint_video import (
    PeriodicCheckpointVideoSchedule,
    STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA,
    build_strike_practice_direction_report,
    completed_strike_rollout_iterations,
    strike_full_song_capture_contract,
    strike_full_song_capture_summary,
    strike_rollout_artifact_paths,
    strike_full_song_rollout_artifact_paths,
    strike_full_song_rollout_is_complete,
    strike_full_song_is_better,
    strike_full_song_quality_key,
    strike_rollout_is_complete,
    strike_paired_rollout_artifact_paths,
    strike_paired_rollout_is_complete,
    strike_periodic_rollout_is_complete,
)
from tab2body.learning.run_layout import layout_for
from tab2body.train_strike import (
    _restore_strike_runtime,
    _strike_runtime_state,
    _update_best_full_song,
)


def _checkpoint(layout, iteration):
    target = layout.checkpoints / f"strike_{iteration:06d}.pt"
    target.write_bytes(b"checkpoint")
    return target


def _complete_rollout(checkpoint):
    for path in strike_rollout_artifact_paths(checkpoint).values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"artifact")


def test_periodic_schedule_selects_next_saved_checkpoint_after_gap():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        schedule = PeriodicCheckpointVideoSchedule.from_layout(layout, 1900)
        selected = []
        for iteration in range(500, 6001, 500):
            checkpoint = _checkpoint(layout, iteration)
            if schedule.is_due(checkpoint):
                selected.append(iteration)
                schedule.mark_completed(iteration)
        assert selected == [2000, 4000, 6000]


def test_periodic_schedule_accepts_curriculum_checkpoint_after_1900():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        schedule = PeriodicCheckpointVideoSchedule.from_layout(layout, 1900)
        assert not schedule.is_due(_checkpoint(layout, 1899))
        assert schedule.is_due(_checkpoint(layout, 1901))


def test_incomplete_pair_does_not_advance_resume_schedule():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        checkpoint = _checkpoint(layout, 2000)
        paths = strike_rollout_artifact_paths(checkpoint)
        paths["remembered"].write_bytes(b"video")
        paths["report"].write_bytes(b"report")
        assert not strike_rollout_is_complete(checkpoint)
        assert completed_strike_rollout_iterations(layout) == ()
        schedule = PeriodicCheckpointVideoSchedule.from_layout(layout, 1900)
        assert schedule.is_due(checkpoint)

        paths["current"].write_bytes(b"video")
        assert strike_rollout_is_complete(checkpoint)
        resumed = PeriodicCheckpointVideoSchedule.from_layout(layout, 1900)
        assert resumed.last_completed_iteration == 2000
        assert resumed.is_due(_checkpoint(layout, 3900))


def test_existing_complete_rollout_is_reused_without_recording():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        checkpoint = _checkpoint(layout, 2000)
        _complete_rollout(checkpoint)
        schedule = PeriodicCheckpointVideoSchedule(1900)
        assert not schedule.is_due(checkpoint)
        assert schedule.last_completed_iteration == 2000


def test_paired_practice_artifacts_require_actual_down_and_up_reports():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        checkpoint = _checkpoint(layout, 3200)
        paths = strike_paired_rollout_artifact_paths(checkpoint)
        assert paths["down"]["remembered"].name == (
            "strike_003200_rollout_down_remembered.mp4")
        assert paths["up"]["current"].name == (
            "strike_003200_rollout_up_current.mp4")
        for direction, artifacts in paths.items():
            artifacts["remembered"].write_bytes(b"video")
            artifacts["current"].write_bytes(b"video")
            report = build_strike_practice_direction_report(
                direction=direction,
                curriculum_stage="S2_TIMED_STRUM",
                capture={
                    "practice_direction": direction,
                    "paired_practice_diagnostic": True,
                    "training_runtime_restored_after_pair": True,
                    "training_rng_restored_before_reset": True,
                    "event_trace_summary": {"traversal_recall": 1.0},
                },
                metadata={"iteration": 3200})
            assert report["schema"] == (
                STRIKE_PRACTICE_DIRECTION_REPORT_SCHEMA)
            artifacts["report"].write_text(
                json.dumps(report), encoding="utf-8")
        assert strike_paired_rollout_is_complete(checkpoint)
        assert strike_periodic_rollout_is_complete(checkpoint)
        assert completed_strike_rollout_iterations(layout) == (3200,)
        resumed = PeriodicCheckpointVideoSchedule.from_layout(layout, 1900)
        assert resumed.last_completed_iteration == 3200
        assert not resumed.is_due(checkpoint)

        invalid = json.loads(paths["down"]["report"].read_text(
            encoding="utf-8"))
        invalid["practice_direction"] = "up"
        paths["down"]["report"].write_text(
            json.dumps(invalid), encoding="utf-8")
        assert not strike_paired_rollout_is_complete(checkpoint)


def test_practice_report_rejects_plan_direction_substitution():
    try:
        build_strike_practice_direction_report(
            direction="down",
            curriculum_stage="S2_TIMED_STRUM",
            capture={
                "practice_direction": "up",
                "paired_practice_diagnostic": True,
                "training_runtime_restored_after_pair": True,
                "training_rng_restored_before_reset": True,
            })
    except ValueError as exc:
        assert "capture mismatch" in str(exc)
    else:
        raise AssertionError("paired report accepted the wrong actual direction")


def test_failed_capture_is_retried_at_next_checkpoint():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        schedule = PeriodicCheckpointVideoSchedule(1900)
        assert schedule.is_due(_checkpoint(layout, 2000))
        assert schedule.is_due(_checkpoint(layout, 2500))


def test_periodic_schedule_rejects_invalid_gap():
    for value in (0, -1, True):
        try:
            PeriodicCheckpointVideoSchedule(value)
        except ValueError:
            pass
        else:
            raise AssertionError(f"invalid gap accepted: {value!r}")


def test_full_song_artifacts_use_separate_names_and_semantic_completion():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        checkpoint = _checkpoint(layout, 8000)
        regular = strike_rollout_artifact_paths(checkpoint)
        full_song = strike_full_song_rollout_artifact_paths(checkpoint)
        assert set(regular.values()).isdisjoint(full_song.values())
        assert full_song["remembered"].name == (
            "strike_008000_full_song_remembered.mp4")
        assert full_song["current"].name == (
            "strike_008000_full_song_current.mp4")
        assert full_song["report"].name == "strike_008000_full_song.json"
        full_song["remembered"].write_bytes(b"video")
        full_song["current"].write_bytes(b"video")
        full_song["report"].write_text(
            '{"schema":"tab2body.strike_full_song_rollout.v1",'
            '"evaluation_scope":"full_song_original_tempo",'
            '"captured_original_song_duration":false,'
            '"stitched_after_episode_reset":false}',
            encoding="utf-8")
        assert not strike_full_song_rollout_is_complete(checkpoint)
        full_song["report"].write_text(
            '{"schema":"tab2body.strike_full_song_rollout.v1",'
            '"evaluation_scope":"full_song_original_tempo",'
            '"captured_original_song_duration":true,'
            '"stitched_after_episode_reset":false}',
            encoding="utf-8")
        assert strike_full_song_rollout_is_complete(checkpoint)


def test_full_song_v2_requires_complete_unstitched_original_timeline():
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        checkpoint = _checkpoint(layout, 8500)
        paths = strike_full_song_rollout_artifact_paths(checkpoint)
        paths["remembered"].write_bytes(b"video")
        paths["current"].write_bytes(b"video")
        report = {
            "schema": "tab2body.strike_full_song_rollout.v2",
            "evaluation_scope": "full_song_original_tempo",
            "captured_original_song_duration": True,
            "stitched_after_episode_reset": False,
            "completed_full_timeline": True,
            "ended_before_original_song_end": False,
            "steps_simulated": 2548,
            "minimum_original_song_steps": 2548,
        }

        paths["report"].write_text(json.dumps(report), encoding="utf-8")
        assert strike_full_song_rollout_is_complete(checkpoint)

        invalid_updates = (
            {"schema": "tab2body.strike_full_song_rollout.v3"},
            {"evaluation_scope": "training_phrase_current_tempo"},
            {"captured_original_song_duration": False},
            {"stitched_after_episode_reset": True},
            {"completed_full_timeline": False},
            {"ended_before_original_song_end": True},
            {"steps_simulated": 2547},
            {"minimum_original_song_steps": 0},
        )
        for update in invalid_updates:
            invalid = dict(report)
            invalid.update(update)
            paths["report"].write_text(
                json.dumps(invalid), encoding="utf-8")
            assert not strike_full_song_rollout_is_complete(checkpoint)


def test_full_song_contract_uses_original_timeline_and_detects_early_end():
    class Scalar:
        def __init__(self, value):
            self.value = value

        def item(self):
            return self.value

    class Goals:
        time = [Scalar(0.0), Scalar(41.9439)]
        num_events = 105

    class Env:
        curriculum_stage = "S3_SONG_INTEGRATION"
        goals = Goals()
        full_song_start_time_s = -0.5
        SIM_HZ = 60
        max_episode_length = 2560

    contract = strike_full_song_capture_contract(Env())
    assert contract["minimum_original_song_steps"] == 2548
    assert abs(contract["original_song_duration_s"] - 41.9439) < 1e-9
    early = strike_full_song_capture_summary(contract, {
        "steps_simulated": 100,
        "episode_ended": True,
        "episode_end": {"failure_termination": True},
    })
    assert not early["captured_original_song_duration"]
    assert early["ended_before_original_song_end"]
    complete = strike_full_song_capture_summary(contract, {
        "steps_simulated": 2548,
        "episode_ended": True,
        "episode_end": {"goal_finished": True},
    })
    assert complete["captured_original_song_duration"]
    assert complete["completed_full_timeline"]


def test_training_runtime_is_restored_after_full_song_capture():
    class Env:
        curriculum_stage = "S3_SONG_INTEGRATION"
        timing_tolerance_ms = 50.0
        tempo_lambda = 0.75
        strum_span = 6
        s2_profile_name = "Z2_50MS"
        s2_endpoint_recovery_active = True
        s2_focus_direction = "down"
        s2_focus_fraction = 0.7
        zone_gate_active = True
        timing_reward_core_ms = 20.0
        duration_reward_core_ms = 25.0
        approach_lead_s = 0.07
        timing_early_grace_ms = 8.0
        timing_early_penalty_scale_ms = 30.0
        curriculum_song_f1_gate = 0.975
        curriculum_stalled = True
        evaluation_full_song = False
        _event_failure_mass = torch.tensor([2.0, 0.0])
        _event_failure_exposure = torch.tensor([4.0, 1.0])
        _event_failure_score = torch.tensor([0.5, 0.0])
        _hard_window_probability_max = 0.1

        def __init__(self):
            self.rng = torch.Generator(device="cpu")
            self.rng.manual_seed(1234)
            self._reset_generation = torch.tensor([3, 7])

        def set_evaluation_mode(self, full_song, reset=False):
            self.evaluation_full_song = bool(full_song)
            if full_song:
                self.tempo_lambda = 1.0

        def set_curriculum_stage(
                self, stage, tolerance, tempo_lambda, strum_span,
                s2_profile_name, zone_active, timing_reward_core_ms,
                duration_reward_core_ms, approach_lead_s,
                timing_early_grace_ms, timing_early_penalty_scale_ms,
                s2_endpoint_recovery_active=False,
                s2_focus_direction="balanced", s2_focus_fraction=0.5,
                song_f1_gate=None,
                song_events_per_episode=None,
                stalled=False,
                reset=False):
            self.curriculum_stage = stage
            self.timing_tolerance_ms = tolerance
            self.tempo_lambda = tempo_lambda
            self.strum_span = strum_span
            self.s2_profile_name = s2_profile_name
            self.s2_endpoint_recovery_active = (
                s2_endpoint_recovery_active)
            self.s2_focus_direction = s2_focus_direction
            self.s2_focus_fraction = s2_focus_fraction
            self.zone_gate_active = zone_active
            self.timing_reward_core_ms = timing_reward_core_ms
            self.duration_reward_core_ms = duration_reward_core_ms
            self.approach_lead_s = approach_lead_s
            self.timing_early_grace_ms = timing_early_grace_ms
            self.timing_early_penalty_scale_ms = (
                timing_early_penalty_scale_ms)
            self.curriculum_song_f1_gate = song_f1_gate
            if song_events_per_episode is not None:
                self.song_events_per_episode = song_events_per_episode
            self.curriculum_stalled = stalled

        def reset(self):
            torch.randint(0, 1000, (1,), generator=self.rng)
            self._reset_generation += 1
            return "restored_observation"

    env = Env()
    state = _strike_runtime_state(env)
    assert state["s2_endpoint_recovery_active"] is True
    assert state["s2_focus_direction"] == "down"
    assert state["s2_focus_fraction"] == 0.7
    env.set_evaluation_mode(True)
    env._event_failure_mass.fill_(99.0)
    env._event_failure_exposure.fill_(99.0)
    env._event_failure_score.fill_(1.0)
    env._hard_window_probability_max = 1.0
    env.reset()
    env.reset()
    env._reset_generation.fill_(99)
    expected_rng = torch.Generator(device="cpu")
    expected_rng.set_state(state["rng_state"])
    torch.randint(0, 1000, (1,), generator=expected_rng)
    expected_generation = state["reset_generation"] + 1
    assert env.tempo_lambda == 1.0
    assert _restore_strike_runtime(env, state) == "restored_observation"
    restored = _strike_runtime_state(env)
    for key in (
            "event_failure_mass", "event_failure_exposure",
            "event_failure_score"):
        assert torch.equal(restored.pop(key), state[key])
    restored.pop("rng_state")
    restored.pop("reset_generation")
    assert torch.equal(env.rng.get_state(), expected_rng.get_state())
    assert torch.equal(env._reset_generation, expected_generation)
    assert restored == {
        key: value for key, value in state.items()
        if key not in (
            "event_failure_mass", "event_failure_exposure",
            "event_failure_score", "rng_state", "reset_generation")}


def test_best_full_song_prefers_accuracy_and_flags_regression():
    def report(iteration, f1, timing):
        return {
            "schema": "tab2body.strike_full_song_rollout.v2",
            "iteration": iteration,
            "checkpoint": f"/tmp/strike_{iteration:06d}.pt",
            "episode_end": {"irrecoverable_safety_failure": False},
            "grip_preservation": {"passed": True},
            "event_trace_summary": {
                "traversal_f1": f1,
                "event_completion_rate": 0.99,
                "strum_completion_rate": 0.98,
                "blocked_crossing_count": 1,
                "wrong_crossing_count": 1,
                "timing_abs_p95_ms": timing,
            },
        }

    best = report(8500, 0.997, 15.5)
    regressed = report(10500, 0.964, 13.8)
    no_timing = report(500, 0.0, None)
    assert strike_full_song_quality_key(best) > (
        strike_full_song_quality_key(regressed))
    assert strike_full_song_quality_key(no_timing)
    assert not strike_full_song_is_better(regressed, best)
    with tempfile.TemporaryDirectory() as temporary:
        layout = layout_for(Path(temporary) / "run", create=True)
        checkpoint = layout.checkpoints / "strike_008500.pt"
        checkpoint.write_bytes(b"test policy")
        best["checkpoint"] = str(checkpoint)
        best_report = layout.videos / "strike_008500_full_song.json"
        best_report.write_text(json.dumps(best), encoding="utf-8")
        selected = _update_best_full_song(layout, best, best_report)
        assert selected["selected"]
        record = json.loads((layout.evaluations / "best_video.json").read_text())
        assert record["checkpoint"] == "checkpoints/strike_008500.pt"
        assert record["checkpoint_sha256"]
        later_report = layout.videos / "strike_010500_full_song.json"
        later_report.write_text(json.dumps(regressed), encoding="utf-8")
        later = _update_best_full_song(layout, regressed, later_report)
        assert not later["selected"]
        assert later["best_iteration"] == 8500
        assert later["regression_warning"]


if __name__ == "__main__":
    test_periodic_schedule_selects_next_saved_checkpoint_after_gap()
    test_periodic_schedule_accepts_curriculum_checkpoint_after_1900()
    test_incomplete_pair_does_not_advance_resume_schedule()
    test_existing_complete_rollout_is_reused_without_recording()
    test_paired_practice_artifacts_require_actual_down_and_up_reports()
    test_practice_report_rejects_plan_direction_substitution()
    test_failed_capture_is_retried_at_next_checkpoint()
    test_periodic_schedule_rejects_invalid_gap()
    test_full_song_artifacts_use_separate_names_and_semantic_completion()
    test_full_song_v2_requires_complete_unstitched_original_timeline()
    test_full_song_contract_uses_original_timeline_and_detects_early_end()
    test_training_runtime_is_restored_after_full_song_capture()
    test_best_full_song_prefers_accuracy_and_flags_regression()
    print("strike periodic checkpoint video tests passed")
