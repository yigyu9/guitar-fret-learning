"""Full-G0 recorder scope must default to the complete song timeline."""
from types import SimpleNamespace

from tab2body.tools.record_full_g0_rollout import (
    _diagnostic_gate_status,
    _diagnostic_label,
    _full_timeline_step_limit,
    _validate_args,
    parser,
)


def test_recorder_defaults_to_automatic_full_timeline():
    args = parser().parse_args([
        "--fret-checkpoint", "fret.pt",
        "--strike-checkpoint", "strike.pt",
    ])
    assert args.max_steps is None
    assert not args.no_watermark

    clean = parser().parse_args([
        "--fret-checkpoint", "fret.pt",
        "--strike-checkpoint", "strike.pt",
        "--no-watermark",
    ])
    assert clean.no_watermark
    assert _diagnostic_label(args.no_watermark) == (
        "DIAGNOSTIC_UNQUALIFIED / NOT G0 VALIDATION")
    assert _diagnostic_label(clean.no_watermark) is None


def test_full_timeline_limit_includes_preroll_deadline_and_drain_reserve():
    events = [
        SimpleNamespace(
            release_decision_deadline_frame=4,
            traversal_end_frame=1,
            effective_delay_cap_frames=3),
        SimpleNamespace(
            release_decision_deadline_frame=851,
            traversal_end_frame=848,
            effective_delay_cap_frames=3),
    ]
    timeline = SimpleNamespace(events=events)
    assert _full_timeline_step_limit(timeline, 60) == 914


def test_explicit_cap_before_completion_is_never_a_pass():
    passed, failures, status = _diagnostic_gate_status(
        timeline_completed=False,
        blocked_count=0,
        hold_saturation_count=0,
        unsafe_state_frame_count=0,
        joint_limit_violation_count=0)
    assert not passed
    assert failures == ["timeline_incomplete"]
    assert status == "diagnostic_incomplete_timeline"


def test_explicit_cap_must_allow_two_video_frames():
    args = parser().parse_args([
        "--fret-checkpoint", "fret.pt",
        "--strike-checkpoint", "strike.pt",
        "--fps", "30",
        "--max-steps", "2",
    ])
    try:
        _validate_args(args)
    except ValueError as exc:
        assert "at least two video frames" in str(exc)
    else:
        raise AssertionError("too-short video cap was accepted")
