from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.strike_metrics import StrikeRewardAlignmentMonitor


def _s2_stats(index):
    first_half = index < 10
    return {
        "curriculum_stage": "S2_TIMED_STRUM",
        "curriculum_s2_profile_name": "T0_400MS",
        "reward": 0.0 if first_half else 1.0,
        "strike_strum_completion_rate": 1.0 if first_half else 0.0,
        "strike_worst_direction_completion_rate": (
            1.0 if first_half else 0.0),
        "strike_timing_p95_ms": 10.0 if first_half else 100.0,
        "strike_false_positive_rate": 0.0 if first_half else 0.2,
        "strike_timing_signed_mean_ms": -20.0 if first_half else -80.0,
    }


def _s3_stats(index, reward_drops=False, fallback_wrong_metric=False):
    first_half = index < 10
    stats = {
        "curriculum_stage": "S3_SONG_INTEGRATION",
        "curriculum_s2_profile_name": "ignored_in_s3",
        "reward": (
            1.0 if first_half else (0.0 if reward_drops else 1.1)),
        "strike_episode_f1": 0.99 if first_half else 0.96,
        "strike_blocked_crossing_rate": 0.01 if first_half else 0.04,
    }
    wrong_key = (
        "strike_wrong_crossing_rate_exceeded"
        if fallback_wrong_metric
        else "wrong_crossing_termination")
    stats[wrong_key] = 0.0 if first_half else 0.02
    return stats


def test_s2_reward_alignment_behavior_is_preserved():
    monitor = StrikeRewardAlignmentMonitor(window=20)
    diagnostic = None
    for index in range(20):
        diagnostic = monitor.update(_s2_stats(index))
    assert diagnostic["reward_alignment_warning"]
    assert diagnostic["reward_alignment_samples"] == 20
    assert set(diagnostic["reward_alignment_reasons"].split(",")) == {
        "strum_completion", "worst_direction_completion",
        "timing_p95", "false_positive", "timing_bias"}


def test_s3_detects_reward_objective_divergence_and_reports_causes():
    monitor = StrikeRewardAlignmentMonitor(window=20)
    diagnostic = None
    for index in range(20):
        diagnostic = monitor.update(_s3_stats(index))
    assert diagnostic["reward_alignment_warning"]
    assert set(diagnostic["reward_alignment_reasons"].split(",")) == {
        "song_f1", "blocked_crossing", "wrong_crossing"}
    assert diagnostic["reward_alignment_reward_delta"] > 0.0
    assert diagnostic["reward_alignment_song_f1_delta"] < 0.0
    assert diagnostic["reward_alignment_blocked_crossing_delta"] > 0.0
    assert diagnostic["reward_alignment_wrong_crossing_delta"] > 0.0


def test_s3_warning_requires_reward_to_remain_nondecreasing():
    monitor = StrikeRewardAlignmentMonitor(window=20)
    diagnostic = None
    for index in range(20):
        diagnostic = monitor.update(_s3_stats(index, reward_drops=True))
    assert not diagnostic["reward_alignment_warning"]
    assert diagnostic["reward_alignment_reasons"] == "none"


def test_s3_accepts_episode_wrong_rate_fallback_and_ignores_profile_change():
    monitor = StrikeRewardAlignmentMonitor(window=20)
    diagnostic = None
    for index in range(20):
        stats = _s3_stats(index, fallback_wrong_metric=True)
        stats["curriculum_s2_profile_name"] = f"stale-{index}"
        diagnostic = monitor.update(stats)
    assert diagnostic["reward_alignment_warning"]
    assert diagnostic["reward_alignment_samples"] == 20
    assert "wrong_crossing" in diagnostic["reward_alignment_reasons"]


def test_s3_prefers_uniform_evidence_over_hard_training_mix():
    monitor = StrikeRewardAlignmentMonitor(window=20)
    diagnostic = None
    for index in range(20):
        stats = _s3_stats(index)
        stats.update({
            "uniform_evidence_strike_episode_f1": 0.99,
            "uniform_evidence_strike_blocked_crossing_rate": 0.01,
            "uniform_evidence_wrong_crossing_termination": 0.0,
        })
        diagnostic = monitor.update(stats)
    assert not diagnostic["reward_alignment_warning"]
    assert diagnostic["reward_alignment_reasons"] == "none"


if __name__ == "__main__":
    test_s2_reward_alignment_behavior_is_preserved()
    test_s3_detects_reward_objective_divergence_and_reports_causes()
    test_s3_warning_requires_reward_to_remain_nondecreasing()
    test_s3_accepts_episode_wrong_rate_fallback_and_ignores_profile_change()
    test_s3_prefers_uniform_evidence_over_hard_training_mix()
    print("strike reward alignment monitor tests passed")
