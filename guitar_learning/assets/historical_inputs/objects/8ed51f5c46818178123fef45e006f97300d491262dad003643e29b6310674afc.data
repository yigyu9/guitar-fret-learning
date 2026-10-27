"""CPU checks that partial or unsafe fret episodes cannot pass evaluation."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from learning.evaluation import evaluation_gate_summary


def metrics():
    return {
        "f1_l": 0.95,
        "no_press_accuracy": 1.0,
        "wrong_press_rate": 0.0,
        "sustain_hold_rate": 0.98,
        "sustain_event_success_rate": 1.0,
        "sustain_max_dropout_frames": 1.0,
    }


def rows():
    return [
        {"goal_finished": True, "failure_termination": False,
         "sustain_event_count": 33.0},
        {"goal_finished": True, "failure_termination": False,
         "sustain_event_count": 33.0},
    ]


def gates(m=None, r=None, penetration=True, fingers=True):
    return evaluation_gate_summary(
        metrics() if m is None else m,
        rows() if r is None else r,
        press_applicable=True, no_press_applicable=True,
        expected_sustain_events=33,
        penetration_proxy_passed=penetration,
        finger_intersection_passed=fingers,
        f1_gate=0.90, no_press_gate=0.99, wrong_press_gate=0.01,
        sustain_hold_gate=0.90, sustain_dropout_gate=3)


def main():
    assert gates()["passed"]

    early = rows()
    early[0] = dict(early[0], goal_finished=False, failure_termination=True)
    result = gates(r=early)
    assert not result["full_song_passed"] and not result["passed"]

    partial = rows()
    partial[1] = dict(partial[1], sustain_event_count=32.0)
    result = gates(r=partial)
    assert not result["sustain_coverage_passed"] and not result["passed"]

    bad_release = dict(metrics(), no_press_accuracy=0.95)
    assert not gates(m=bad_release)["no_press_passed"]
    bad_wrong = dict(metrics(), wrong_press_rate=0.02)
    assert not gates(m=bad_wrong)["wrong_press_passed"]
    assert not gates(penetration=False)["passed"]
    diagnostic_overlap = gates(fingers=False)
    assert diagnostic_overlap["passed"]
    assert not diagnostic_overlap["finger_intersection_passed"]
    assert diagnostic_overlap["finger_intersection_diagnostic_only"]

    bad_thumb = evaluation_gate_summary(
        metrics(), rows(),
        press_applicable=True, no_press_applicable=True,
        expected_sustain_events=33,
        penetration_proxy_passed=True,
        finger_intersection_passed=True,
        f1_gate=0.90, no_press_gate=0.99, wrong_press_gate=0.01,
        sustain_hold_gate=0.90, sustain_dropout_gate=3,
        thumb_support_rate=0.0, thumb_wrong_contact_rate=1.0,
        thumb_contact_gate_enabled=False)
    assert bad_thumb["passed"]
    assert not bad_thumb["thumb_passed"]
    assert bad_thumb["thumb_contact_diagnostic_only"]

    gated_thumb = evaluation_gate_summary(
        metrics(), rows(),
        press_applicable=True, no_press_applicable=True,
        expected_sustain_events=33,
        penetration_proxy_passed=True,
        finger_intersection_passed=True,
        f1_gate=0.90, no_press_gate=0.99, wrong_press_gate=0.01,
        sustain_hold_gate=0.90, sustain_dropout_gate=3,
        thumb_support_rate=0.0, thumb_wrong_contact_rate=1.0,
        thumb_contact_gate_enabled=True)
    assert not gated_thumb["passed"]
    assert gated_thumb["thumb_contact_gate_enabled"]

    gated_geometry = evaluation_gate_summary(
        metrics(), rows(),
        press_applicable=True, no_press_applicable=True,
        expected_sustain_events=33,
        penetration_proxy_passed=True,
        finger_intersection_passed=True,
        f1_gate=0.90, no_press_gate=0.99, wrong_press_gate=0.01,
        sustain_hold_gate=0.90, sustain_dropout_gate=3,
        thumb_press_readiness=0.20,
        thumb_press_readiness_gate=0.35,
        thumb_geometry_gate_enabled=True,
        thumb_contact_gate_enabled=False)
    assert not gated_geometry["passed"]
    assert gated_geometry["thumb_geometry_gate_enabled"]
    assert not gated_geometry["thumb_geometry_passed"]

    print("PASS: completion, release, sustain, and safety proxy evaluation gates")


if __name__ == "__main__":
    main()
