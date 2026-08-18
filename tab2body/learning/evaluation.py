"""Pure learned-song evaluation gates, independent of Isaac Gym."""
from __future__ import annotations


def evaluation_gate_summary(
        metrics, episode_rows, *, press_applicable, no_press_applicable,
        expected_sustain_events, penetration_proxy_passed,
        finger_intersection_passed, f1_gate, no_press_gate,
        wrong_press_gate, sustain_hold_gate, sustain_dropout_gate,
        thumb_support_rate=None, thumb_wrong_contact_rate=None,
        thumb_support_gate=0.80, thumb_wrong_contact_gate=0.05,
        thumb_contact_gate_enabled=True,
        thumb_press_readiness=None, thumb_press_readiness_gate=0.35,
        thumb_geometry_gate_enabled=False):
    """Return explicit, independently auditable learned-song gates."""
    if not episode_rows:
        raise ValueError("evaluation gates require at least one episode")
    f1_gate = float(f1_gate)
    no_press_gate = float(no_press_gate)
    wrong_press_gate = float(wrong_press_gate)
    press_passed = (not press_applicable or metrics["f1_l"] >= f1_gate)
    no_press_passed = (
        not no_press_applicable
        or metrics["no_press_accuracy"] >= no_press_gate)
    wrong_press_passed = metrics["wrong_press_rate"] <= wrong_press_gate
    completion_rate = sum(
        float(row["goal_finished"]) for row in episode_rows) / len(episode_rows)
    failure_rate = sum(
        float(row["failure_termination"]) for row in episode_rows) / len(episode_rows)
    full_song_passed = completion_rate >= 1.0 - 1e-9 and failure_rate <= 1e-9

    expected_sustain_events = int(expected_sustain_events)
    sustain_applicable = expected_sustain_events > 0
    sustain_coverage_passed = all(
        int(round(row["sustain_event_count"])) == expected_sustain_events
        for row in episode_rows)
    sustain_quality_passed = (
        not sustain_applicable
        or (metrics["sustain_hold_rate"] >= float(sustain_hold_gate)
            and metrics["sustain_event_success_rate"] >= 1.0 - 1e-6
            and metrics["sustain_max_dropout_frames"]
            <= int(sustain_dropout_gate)))
    sustain_passed = sustain_coverage_passed and sustain_quality_passed
    # R22 is deliberately diagnostic-only until the capsule proxy has been
    # calibrated against valid multi-finger chord poses.  Treating its current
    # zero-overlap heuristic as a delivery gate would contradict that rule and
    # can reject anatomically valid close fingers.  Penetration is the calibrated
    # safety proxy; named hard termination reasons are covered by full_song_passed.
    safety_proxy_passed = (
        full_song_passed and bool(penetration_proxy_passed))
    thumb_applicable = (
        thumb_support_rate is not None
        and thumb_wrong_contact_rate is not None)
    thumb_passed = (
        not thumb_applicable
        or (float(thumb_support_rate) >= float(thumb_support_gate)
            and float(thumb_wrong_contact_rate)
            <= float(thumb_wrong_contact_gate)))
    thumb_gate_enabled = bool(thumb_contact_gate_enabled and thumb_applicable)
    thumb_geometry_applicable = thumb_press_readiness is not None
    thumb_geometry_passed = (
        not thumb_geometry_applicable
        or float(thumb_press_readiness)
            >= float(thumb_press_readiness_gate))
    thumb_geometry_enabled = bool(
        thumb_geometry_gate_enabled and thumb_geometry_applicable)
    passed = (press_passed and no_press_passed and wrong_press_passed
              and sustain_passed and safety_proxy_passed
              and (thumb_passed or not thumb_gate_enabled)
              and (thumb_geometry_passed or not thumb_geometry_enabled))
    return {
        "gate_f1": f1_gate,
        "gate_no_press_accuracy": no_press_gate,
        "gate_wrong_press_rate": wrong_press_gate,
        "press_applicable": bool(press_applicable),
        "press_passed": bool(press_passed),
        # Compatibility name retained for old result readers.
        "accuracy_passed": bool(press_passed),
        "no_press_applicable": bool(no_press_applicable),
        "no_press_passed": bool(no_press_passed),
        "wrong_press_passed": bool(wrong_press_passed),
        "full_song_completion_rate": completion_rate,
        "failure_termination_rate": failure_rate,
        "full_song_passed": bool(full_song_passed),
        "expected_sustain_event_count": expected_sustain_events,
        "sustain_coverage_passed": bool(sustain_coverage_passed),
        "sustain_quality_passed": bool(sustain_quality_passed),
        "sustain_applicable": bool(sustain_applicable),
        "sustain_passed": bool(sustain_passed),
        "penetration_proxy_passed": bool(penetration_proxy_passed),
        "finger_intersection_passed": bool(finger_intersection_passed),
        "finger_intersection_diagnostic_only": True,
        "safety_proxy_passed": bool(safety_proxy_passed),
        "thumb_applicable": bool(thumb_applicable),
        "thumb_contact_gate_enabled": thumb_gate_enabled,
        "thumb_contact_diagnostic_only": not thumb_gate_enabled,
        "gate_thumb_support_rate": float(thumb_support_gate),
        "gate_thumb_wrong_contact_rate": float(thumb_wrong_contact_gate),
        "thumb_passed": bool(thumb_passed),
        "thumb_geometry_applicable": bool(thumb_geometry_applicable),
        "thumb_geometry_gate_enabled": thumb_geometry_enabled,
        "thumb_geometry_diagnostic_only": not thumb_geometry_enabled,
        "gate_thumb_press_readiness": float(thumb_press_readiness_gate),
        "thumb_geometry_passed": bool(thumb_geometry_passed),
        # This no longer claims exact mesh safety; retained as a deprecated alias.
        "hard_safety_passed": bool(safety_proxy_passed),
        "passed": bool(passed),
    }
