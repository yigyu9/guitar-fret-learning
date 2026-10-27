"""CPU contracts for the 105D G0 arbiter and rule Synchronizer."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.full.action import (  # noqa: E402
    FULL_ACTION_DIM,
    FullActionManifest,
    G0ActionArbiter,
    humanoid_joint_names,
)
from tab2body.full.synchronizer import (  # noqa: E402
    DeadlineAction,
    DelayCause,
    EventOutcome,
    RuleBasedSynchronizer,
)
from tab2body.full.readiness import (  # noqa: E402
    evaluate_sounding_fret_readiness,
    evaluate_strike_readiness,
)
from tab2body.full.clock import CanonicalScoreClock  # noqa: E402
from tab2body.full.events import compile_song_bundle_events  # noqa: E402


def _row(value, dtype=torch.long):
    return torch.tensor([value], dtype=dtype)


def _mask(*indices):
    value = torch.zeros(1, 6, dtype=torch.bool)
    if indices:
        value[0, list(indices)] = True
    return value


def _targets(**values):
    result = torch.full((1, 6), -1, dtype=torch.long)
    for key, value in values.items():
        result[0, int(key)] = int(value)
    return result


def _before(sync, *, event=0, frame, boundary=10, budget=2,
            traversal_end=None, targets=None, traversal=None, ready=None,
            strike=True):
    targets = _targets(**{"2": 4}) if targets is None else targets
    audible = targets >= 0
    traversal = audible.clone() if traversal is None else traversal
    ordered_strings = torch.nonzero(traversal[0]).flatten()
    traversal_order = torch.full((1, 6), -1, dtype=torch.long)
    traversal_order[0, :ordered_strings.numel()] = ordered_strings
    traversal_offsets_s = torch.zeros(1, 6, dtype=torch.float32)
    if ordered_strings.numel() > 1:
        traversal_offsets_s[0, :ordered_strings.numel()] = torch.arange(
            ordered_strings.numel(), dtype=torch.float32) * .005
    traversal_end = boundary if traversal_end is None else traversal_end
    ready = audible.clone() if ready is None else ready
    return sync.before_step(
        event_id=_row(event), score_frame=_row(frame),
        release_boundary_frame=_row(boundary),
        traversal_end_frame=_row(traversal_end),
        delay_budget_frames=_row(budget), target_frets=targets,
        audible_mask=audible, traversal_mask=traversal,
        traversal_order=traversal_order,
        traversal_offsets_s=traversal_offsets_s,
        strike_direction=_row(-1, torch.int8),
        fret_ready_mask=ready,
        strike_ready=_row(strike, torch.bool),
        guitar_stable=_row(True, torch.bool))


def _after(sync, frame, crossing=None, ready=None, *,
           subframe_t=None, direction=None):
    crossing = _mask() if crossing is None else crossing
    ready = _mask(2) if ready is None else ready
    if subframe_t is None:
        subframe_t = torch.zeros(1, 6, dtype=torch.float32)
        indices = torch.nonzero(crossing[0]).flatten()
        if indices.numel():
            subframe_t[0, indices] = torch.arange(
                1, indices.numel() + 1, dtype=torch.float32) / (
                    indices.numel() + 1)
    if direction is None:
        direction = torch.where(
            crossing, torch.full_like(crossing, -1, dtype=torch.int8),
            torch.zeros_like(crossing, dtype=torch.int8))
    return sync.after_step(
        score_frame=_row(frame), crossing_mask=crossing,
        crossing_subframe_t=subframe_t,
        crossing_direction=direction,
        fret_ready_mask=ready)


def test_full_action_manifest_and_named_scatter():
    names = humanoid_joint_names(
        PROJECT_ROOT / "tab2body/assets/smpl_mpl_hands_body.xml")
    assert len(names) == FULL_ACTION_DIM == 105
    fret = tuple(name for name in names if name.startswith((
        "L_Shoulder", "L_Elbow", "L_Wrist", "LH:")))
    strike = tuple(name for name in names if name.startswith((
        "R_Shoulder", "R_Elbow", "R_Wrist", "RH:")))
    manifest = FullActionManifest.from_joint_names(
        names, fret_action_names=fret, strike_action_names=strike)
    assert len(manifest.fret_indices) == 30
    assert len(manifest.strike_indices) == 30
    assert len(manifest.reserved_hold_indices) == 45

    hold = torch.linspace(-0.7, 0.7, 105).repeat(2, 1)
    left = torch.full((2, 30), 0.25)
    right = torch.full((2, 30), -0.5)
    previous_right = torch.full((2, 30), 0.75)
    merged = G0ActionArbiter(manifest).merge(
        left, right, hold, hold_strike=torch.tensor([False, True]),
        previous_strike_action=previous_right)
    assert torch.all(merged.full_action[0, list(manifest.fret_indices)] == .25)
    assert torch.all(merged.full_action[0, list(manifest.strike_indices)] == -.5)
    assert torch.all(merged.full_action[1, list(manifest.strike_indices)] == .75)
    assert torch.equal(
        merged.full_action[:, list(manifest.reserved_hold_indices)],
        hold[:, list(manifest.reserved_hold_indices)])


def test_one_full_frame_dwell_then_on_time_execute():
    sync = RuleBasedSynchronizer(1)
    first = _before(sync, frame=9)
    assert first.action.item() == DeadlineAction.PREPARE
    _after(sync, 9)
    second = _before(sync, frame=10)
    assert second.action.item() == DeadlineAction.EXECUTE
    assert second.strike_permission.item()
    result = _after(sync, 10, crossing=_mask(2))
    assert result.resolved_pulse.item()
    assert result.outcome.item() == EventOutcome.FULL
    assert result.delay_frames.item() == 0


def test_same_target_restrike_carries_dwell_changed_target_resets_it():
    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9)
    _after(sync, 9)
    _before(sync, frame=10)
    _after(sync, 10, crossing=_mask(2))

    # The next event keeps exactly the same sounding fret.  Its dwell is
    # already valid at the first observation after the cursor advances.
    same = _before(sync, event=1, frame=11, boundary=11)
    assert same.action.item() == DeadlineAction.EXECUTE
    _after(sync, 11, crossing=_mask(2))

    changed_targets = _targets(**{"2": 6})
    changed = _before(
        sync, event=2, frame=12, boundary=12,
        targets=changed_targets, ready=_mask(2))
    assert changed.action.item() == DeadlineAction.WAIT
    _after(sync, 12, ready=_mask(2))
    next_frame = _before(
        sync, event=2, frame=13, boundary=12,
        targets=changed_targets, ready=_mask(2))
    assert next_frame.action.item() == DeadlineAction.EXECUTE
    assert next_frame.timing_shift_frames.item() == 1
    _after(sync, 13, crossing=_mask(2), ready=_mask(2))


def test_single_note_delayed_rescue_and_fret_skip():
    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9, ready=_mask())
    _after(sync, 9, ready=_mask())
    at_boundary = _before(sync, frame=10, ready=_mask())
    assert at_boundary.action.item() == DeadlineAction.WAIT
    assert at_boundary.hold_strike_action.item()
    assert at_boundary.timing_shift_frames.item() == 1
    _after(sync, 10, ready=_mask())
    first_ready = _before(sync, frame=11, ready=_mask(2))
    assert first_ready.action.item() == DeadlineAction.WAIT
    _after(sync, 11, ready=_mask(2))
    rescue = _before(sync, frame=12, ready=_mask(2))
    assert rescue.action.item() == DeadlineAction.EXECUTE
    assert rescue.timing_shift_frames.item() == 2
    rescued = _after(sync, 12, crossing=_mask(2), ready=_mask(2))
    assert rescued.outcome.item() == EventOutcome.FULL
    assert rescued.delay_cause.item() == DelayCause.FRET

    sync = RuleBasedSynchronizer(1)
    for frame in (9, 10, 11):
        decision = _before(sync, frame=frame, ready=_mask())
        _after(sync, frame, ready=_mask())
        assert not decision.resolved.item()
    skipped = _before(sync, frame=12, ready=_mask())
    assert skipped.action.item() == DeadlineAction.SKIP
    assert skipped.resolved.item()
    assert skipped.outcome.item() == EventOutcome.MISSED_FRET
    assert skipped.timing_shift_frames.item() == 2
    late = _after(sync, 12, crossing=_mask(2), ready=_mask(2))
    assert late.resolved_pulse.item()
    assert late.blocked_crossing_mask[0, 2]
    assert late.outcome.item() == EventOutcome.MISSED_FRET


def test_multi_string_partial_at_deadline_and_protected_exclusion():
    sync = RuleBasedSynchronizer(1)
    targets = _targets(**{"1": 3, "3": 5})
    traversal = _mask(1, 2, 3)
    for frame in (9, 10, 11):
        _before(
            sync, frame=frame, targets=targets,
            traversal=traversal, traversal_end=12,
            ready=_mask(1), strike=True)
        _after(sync, frame, ready=_mask(1))
    decision = _before(
        sync, frame=12, targets=targets, traversal=traversal,
        traversal_end=12, ready=_mask(1), strike=True)
    assert decision.action.item() == DeadlineAction.EXECUTE
    assert decision.scorable_target_mask[0].tolist() == [
        False, True, False, False, False, False]
    assert decision.traversal_permission_mask[0].tolist() == [
        False, True, True, True, False, False]
    result = _after(sync, 12, crossing=_mask(1, 2, 3), ready=_mask(1))
    assert result.outcome.item() == EventOutcome.PARTIAL
    assert result.accepted_crossing_mask[0, 1]
    # String 2 may be a protected/intervening traversal string, but it is not
    # an audible target and therefore never enters success/readiness.
    assert not result.accepted_crossing_mask[0, 2]
    assert result.protected_crossing_mask[0, 2]
    assert not result.blocked_crossing_mask[0, 2]
    assert result.failed_target_crossing_mask[0, 3]


def test_strum_waits_for_traversal_completion_not_release_deadline():
    sync = RuleBasedSynchronizer(1)
    targets = _targets(**{"1": 3, "3": 5})
    traversal = _mask(1, 2, 3)
    ready = _mask(1, 3)
    _before(
        sync, frame=9, targets=targets, traversal=traversal,
        traversal_end=12, ready=ready)
    _after(sync, 9, ready=ready)
    opened = _before(
        sync, frame=10, targets=targets, traversal=traversal,
        traversal_end=12, ready=ready)
    assert opened.action.item() == DeadlineAction.EXECUTE
    first = _after(sync, 10, crossing=_mask(1), ready=ready)
    assert not first.resolved.item()
    _before(
        sync, frame=11, targets=targets, traversal=traversal,
        traversal_end=12, ready=ready)
    protected = _after(sync, 11, crossing=_mask(2), ready=ready)
    assert protected.protected_crossing_mask[0, 2]
    assert not protected.resolved.item()
    _before(
        sync, frame=12, targets=targets, traversal=traversal,
        traversal_end=12, ready=ready)
    final = _after(sync, 12, crossing=_mask(3), ready=ready)
    assert final.resolved_pulse.item()
    assert final.traversal_complete.item()
    assert final.outcome.item() == EventOutcome.FULL


def test_missing_protected_traversal_cannot_count_as_full_event():
    sync = RuleBasedSynchronizer(1)
    targets = _targets(**{"1": 3, "3": 5})
    traversal = _mask(1, 2, 3)
    ready = _mask(1, 3)
    _before(
        sync, frame=9, targets=targets, traversal=traversal,
        traversal_end=10, ready=ready)
    _after(sync, 9, ready=ready)
    _before(
        sync, frame=10, targets=targets, traversal=traversal,
        traversal_end=10, ready=ready)
    # Both audible targets cross, but protected/intervening string 2 does not.
    result = _after(sync, 10, crossing=_mask(1, 3), ready=ready)
    assert result.resolved_pulse.item()
    assert not result.traversal_complete.item()
    assert result.outcome.item() == EventOutcome.PARTIAL


def test_reverse_wrong_direction_and_unplanned_crossings_never_count_full():
    targets = _targets(**{"1": 3, "3": 5})
    traversal = _mask(1, 2, 3)
    ready = _mask(1, 3)

    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9, targets=targets, traversal=traversal,
            traversal_end=10, ready=ready)
    _after(sync, 9, ready=ready)
    _before(sync, frame=10, targets=targets, traversal=traversal,
            traversal_end=10, ready=ready)
    reverse_time = torch.zeros(1, 6)
    reverse_time[0, 3] = .1
    reverse_time[0, 2] = .2
    reverse_time[0, 1] = .3
    reverse = _after(
        sync, 10, crossing=traversal, ready=ready,
        subframe_t=reverse_time)
    assert reverse.outcome.item() != EventOutcome.FULL
    assert reverse.crossing_contract_violated.item()
    assert reverse.order_violation_crossing_mask.any().item()

    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9, targets=targets, traversal=traversal,
            traversal_end=10, ready=ready)
    _after(sync, 9, ready=ready)
    _before(sync, frame=10, targets=targets, traversal=traversal,
            traversal_end=10, ready=ready)
    wrong_direction = torch.where(
        traversal, torch.ones_like(traversal, dtype=torch.int8),
        torch.zeros_like(traversal, dtype=torch.int8))
    wrong = _after(
        sync, 10, crossing=traversal, ready=ready,
        direction=wrong_direction)
    assert wrong.outcome.item() != EventOutcome.FULL
    assert wrong.wrong_direction_crossing_mask.any().item()

    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9, targets=targets, traversal=traversal,
            traversal_end=10, ready=ready)
    _after(sync, 9, ready=ready)
    _before(sync, frame=10, targets=targets, traversal=traversal,
            traversal_end=10, ready=ready)
    with_extra = _mask(1, 2, 3, 4)
    extra = _after(sync, 10, crossing=with_extra, ready=ready)
    assert extra.outcome.item() != EventOutcome.FULL
    assert extra.unplanned_crossing_mask[0, 4]


def test_closed_gate_crossing_does_not_consume_event():
    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=8, ready=_mask(2))
    blocked = _after(sync, 8, crossing=_mask(2), ready=_mask(2))
    assert blocked.blocked_crossing_mask[0, 2]
    assert not blocked.resolved.item()
    _before(sync, frame=9, ready=_mask(2))
    _after(sync, 9, ready=_mask(2))
    decision = _before(sync, frame=10, ready=_mask(2))
    assert decision.strike_permission.item()
    result = _after(sync, 10, crossing=_mask(2), ready=_mask(2))
    assert result.outcome.item() == EventOutcome.FULL


def test_strike_entry_action_is_held_before_release_boundary():
    sync = RuleBasedSynchronizer(1)
    approaching = _before(sync, frame=8, strike=False)
    assert not approaching.hold_strike_action.item()
    _after(sync, 8)
    at_entry = _before(sync, frame=9, strike=True)
    assert at_entry.action.item() == DeadlineAction.PREPARE
    assert at_entry.hold_strike_action.item()
    _after(sync, 9)
    release = _before(sync, frame=10, strike=True)
    assert release.action.item() == DeadlineAction.EXECUTE
    assert not release.hold_strike_action.item()
    _after(sync, 10, crossing=_mask(2))


def test_strike_delay_cause_and_zero_safe_budget():
    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9, strike=False)
    _after(sync, 9)
    waiting = _before(sync, frame=10, strike=False)
    assert waiting.action.item() == DeadlineAction.WAIT
    # A late right hand must still be allowed to approach the entry state.
    # Only an already-ready hand is held behind the closed release gate.
    assert not waiting.hold_strike_action.item()
    _after(sync, 10)
    execute = _before(sync, frame=11, strike=True)
    assert execute.delay_cause.item() == DelayCause.STRIKE
    _after(sync, 11, crossing=_mask(2))

    # An outgoing transition with no spare edge gap overrides the global +2
    # maximum.  The current event must be skipped at its boundary.
    sync = RuleBasedSynchronizer(1)
    _before(sync, frame=9, budget=0, ready=_mask())
    _after(sync, 9, ready=_mask())
    skipped = _before(sync, frame=10, budget=0, ready=_mask())
    assert skipped.action.item() == DeadlineAction.SKIP
    assert skipped.outcome.item() == EventOutcome.MISSED_FRET


def test_effective_sounding_fret_and_extra_press_semantics():
    cells = torch.zeros(1, 6, 8, dtype=torch.bool)
    targets = _targets(**{"0": 0, "1": 5, "2": 4, "3": 3})
    # Open target remains correct on string 0.  String 1 has the target plus a
    # harmless lower press.  String 2 has a higher press that changes pitch.
    # String 3 lacks its requested press.
    cells[0, 1, 1] = True   # fret 2, harmless
    cells[0, 1, 4] = True   # fret 5, sounding target
    cells[0, 2, 3] = True   # target fret 4
    cells[0, 2, 6] = True   # fret 7 wins and interferes
    state = evaluate_sounding_fret_readiness(cells, targets)
    assert state.effective_sounding_fret[0].tolist() == [0, 5, 7, 0, 0, 0]
    assert state.ready_mask[0].tolist() == [
        True, True, False, False, False, False]
    assert state.harmless_extra_press_mask[0, 1]
    assert state.interfering_mask[0, 2]
    assert state.interfering_mask[0, 3]
    assert not state.target_active_mask[0, 4]


def test_one_score_clock_owns_frame_and_exactly_once_cursor():
    timeline = compile_song_bundle_events(
        PROJECT_ROOT / "data/song_bundles/02_Jazz1-200-B_solo")
    clock = CanonicalScoreClock(
        timeline, num_envs=1, preroll_frames=3)
    first = clock.current()
    assert first.score_frame.item() == -3
    assert first.event_index.item() == 0
    assert first.release_boundary_frame.item() == (
        timeline.events[0].release_boundary_frame)
    clock.consume_resolution(first.event_index, _row(False, torch.bool))
    clock.advance_physics()
    assert clock.current().score_frame.item() == -2
    clock.consume_resolution(first.event_index, _row(True, torch.bool))
    clock.advance_physics()
    second = clock.current()
    assert second.event_index.item() == 1
    assert second.score_frame.item() == -1
    try:
        clock.consume_resolution(first.event_index, _row(True, torch.bool))
    except RuntimeError as exc:
        assert "non-current" in str(exc)
    else:
        raise AssertionError("a resolved event was consumed twice")

    restored = CanonicalScoreClock(
        timeline, num_envs=1, preroll_frames=3)
    restored.load_state_dict(clock.state_dict())
    assert torch.equal(restored.event_index, clock.event_index)
    assert torch.equal(restored.score_frame, clock.score_frame)


def test_strike_readiness_is_physical_conjunction():
    state = evaluate_strike_readiness(
        motor_phase=torch.tensor([1, 0, 1, 1, 1, 1]),
        grip_success=torch.tensor([True, True, False, True, True, True]),
        entry_distance_m=torch.tensor([.002, .002, .002, .020, .002, .002]),
        detector_armed=torch.tensor([True, True, True, True, False, True]),
        approach_direction_ok=torch.tensor(
            [True, True, True, True, True, True]),
        entry_signed_distance_m=torch.tensor(
            [-.002, -.002, -.002, -.002, -.002, .001]),
        approach_phase=1, entry_distance_threshold_m=.005,
        pre_side_epsilon_m=.0005)
    assert state.ready.tolist() == [True, False, False, False, False, False]
    assert not state.phase_ready[1]
    assert not state.grip_ready[2]
    assert not state.entry_ready[3]
    assert not state.detector_ready[4]
    assert not state.entry_side_ready[5]


def main():
    test_full_action_manifest_and_named_scatter()
    test_one_full_frame_dwell_then_on_time_execute()
    test_same_target_restrike_carries_dwell_changed_target_resets_it()
    test_single_note_delayed_rescue_and_fret_skip()
    test_multi_string_partial_at_deadline_and_protected_exclusion()
    test_strum_waits_for_traversal_completion_not_release_deadline()
    test_missing_protected_traversal_cannot_count_as_full_event()
    test_reverse_wrong_direction_and_unplanned_crossings_never_count_full()
    test_closed_gate_crossing_does_not_consume_event()
    test_strike_entry_action_is_held_before_release_boundary()
    test_strike_delay_cause_and_zero_safe_budget()
    test_effective_sounding_fret_and_extra_press_semantics()
    test_one_score_clock_owns_frame_and_exactly_once_cursor()
    test_strike_readiness_is_physical_conjunction()
    print("PASS: Full G0 action and rule Synchronizer contracts")


if __name__ == "__main__":
    main()
