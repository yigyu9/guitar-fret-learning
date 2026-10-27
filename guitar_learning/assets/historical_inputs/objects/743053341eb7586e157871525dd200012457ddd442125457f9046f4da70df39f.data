"""Decision diagnostics must expose weak fingers without changing gates."""
import json
from unittest.mock import patch

from test_goal_pair_curriculum_phases import (
    _config, _stats, FingertipApproachCurriculum,
)


def main():
    curriculum = FingertipApproachCurriculum(
        _config(), forced_stage="goal_pair")
    curriculum.required_song_fingers = (1, 2, 3, 4)
    curriculum.goal_pair_phase = "mixed"
    curriculum.goal_pair_mixed_level = 2
    stats = _stats()
    # Legacy rows retain the existing aggregate-only compatibility behavior.
    assert curriculum._goal_pair_sequence_finger_sample(stats) is True
    for finger in range(1, 5):
        prefix = f"curriculum_goal_pair_sequence_finger_{finger}"
        stats.update({
            f"{prefix}_target_active_count": 100,
            f"{prefix}_press_success": 0.99 if finger != 4 else 0.10,
            f"{prefix}_target_distance": 0.005,
            f"{prefix}_hold_quality": 0.99,
            f"{prefix}_dropout_rate": 0.01,
            f"{prefix}_wrong_press": 0.0,
        })
    before = curriculum.state()
    report = curriculum.goal_pair_gate_diagnostics(stats)
    assert curriculum.state() == before, "diagnosis must not mutate curriculum"
    assert "sequence_finger_4_success" in report["failures"]
    check = report["checks"]["sequence_finger_4_success"]
    assert check["value"] == 0.10 and check["threshold"] > 0.10
    assert curriculum._goal_pair_sequence_finger_sample(stats) is False
    stats["curriculum_goal_pair_sequence_finger_4_target_active_count"] = 1
    report = curriculum.goal_pair_gate_diagnostics(stats)
    assert "sequence_finger_4_evidence" in report["evidence_shortages"]
    assert curriculum._goal_pair_sequence_finger_sample(stats) is None
    curriculum._sync_goal_pair_phase(stats)
    state = curriculum.state()
    logged = json.loads(state["curriculum_goal_pair_gate_report"])
    assert logged["phase"] == "mixed"
    assert "sequence_finger_4_evidence" in logged["evidence_shortages"]
    assert "insufficient_evidence" in state["curriculum_last_gate_failures"]
    # Preserve original ordered short-circuit: first finger failure precedes
    # missing evidence in a later finger.
    stats["curriculum_goal_pair_sequence_finger_1_press_success"] = 0.0
    assert curriculum._goal_pair_sequence_finger_sample(stats) is False
    curriculum.goal_pair_recovery_active = True
    report = curriculum.goal_pair_gate_diagnostics(stats)
    assert "recovery_age" in report["failures"]
    assert "phase_age" not in report["checks"]
    assert report["checks"]["recovery_song_ready"]["passed"] == (
        curriculum._goal_pair_recovery_song_ready(stats))
    full = FingertipApproachCurriculum(_config(), forced_stage="goal_pair")
    full.goal_pair_phase = "full"
    full.required_song_fingers = (1, 2, 3, 4)
    # A bridge window completing this iteration must appear in the report
    # used for this iteration, not only in the next iteration's snapshot.
    evidence = {"ready": False}
    def accumulate(_stats):
        evidence["ready"] = True
    with patch.object(full, "_accumulate_bridge_stats", accumulate), \
            patch.object(full, "_bridge_windows_pass",
                         lambda: evidence["ready"]):
        assert not full.goal_pair_gate_diagnostics(_stats())["checks"][
            "bridge_windows"]["passed"]
        full._sync_goal_pair_phase(_stats())
        state = full._after_bridge_iteration(_stats(), allow_promotion=False)
    report = json.loads(state["curriculum_goal_pair_gate_report"])
    assert report["checks"]["bridge_windows"]["passed"] is True
    assert report["scope"] == "normal_stage_promotion_conditions"
    full.goal_pair_recovery_active = True
    report = full.goal_pair_gate_diagnostics(_stats())
    assert report["scope"] == "recovery_exit_conditions"
    assert "recovery_good_windows" in report["checks"]
    assert "bridge_windows" not in report["checks"]
    retained = FingertipApproachCurriculum(
        _config(), forced_stage="goal_pair")
    retained.required_song_fingers = (1, 2, 3, 4)
    retained.goal_pair_mastered_fingers = [True] * 4
    retained.goal_pair_phase_iteration = 10
    report = retained.goal_pair_gate_diagnostics(_stats(rehearsal_pass=False))
    assert report["checks"]["finger_4_post_update_quality"]["passed"] is False
    assert report["checks"]["finger_4_streak"]["passed"] is False
    assert not report["failures"], "mastery latch tolerates transient retention loss"
    print("PASS: goal-pair gate diagnostics and decision parity")


if __name__ == "__main__":
    main()
