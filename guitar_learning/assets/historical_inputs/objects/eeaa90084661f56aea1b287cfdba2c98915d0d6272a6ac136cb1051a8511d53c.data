"""CPU contracts for ready, timing and release-aware completion."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.strike_events import (
    strike_clearance_waypoint_state,
    strike_clean_recovery_progress,
    strike_recovery_clearance_target,
    strike_completed_recovery_frames,
    strike_dual_recovery_plan,
    strike_dual_recovery_progress,
    strike_dual_recovery_to_approach,
    strike_directional_strum_outcomes,
    strike_handoff_path_clearance,
    strike_event_outcome_masks,
    strike_early_timing_cost,
    strike_false_positive_count,
    strike_focused_practice_direction,
    strike_physical_target_candidate,
    strike_release_recovery_context,
    strike_recovery_incomplete_timeout,
    strike_ready_episode_resolution,
    strike_ready_latch,
    strike_resolved_episode_done,
    strike_timing_gate,
    strike_timed_approach_open,
    strike_limit_traversal_span,
    strike_next_traversal_string,
    strike_ordered_release_progress,
    strike_strum_terminal_progress,
)


def main():
    approach = strike_timed_approach_open(
        torch.tensor([0.84, 0.85, 0.90]),
        torch.ones(3),
        torch.tensor([-0.01, -0.01, -0.01]),
        0.14)
    assert torch.equal(
        approach["approach_open"], torch.tensor([False, True, True]))
    assert torch.allclose(
        approach["approach_start_s"], torch.full((3,), 0.85))
    early_cost = strike_early_timing_cost(
        torch.tensor([[True, True, True, True, False]]),
        torch.tensor([[-0.075, -0.150, 0.030, -1.0, -1.0]]),
        grace_s=0.075,
        scale_s=0.150)
    assert torch.allclose(
        early_cost,
        torch.tensor([[0.0, 0.25, 0.0, 1.0, 0.0]]))
    early_error = torch.full((1, 6), -0.186)
    early_quality = 1.0 / (1.0 + (early_error / 0.180).square())
    early_center_cost = strike_early_timing_cost(
        torch.ones(1, 6, dtype=torch.bool),
        early_error,
        grace_s=0.075,
        scale_s=0.150).mean(dim=1)
    early_objective = 2.0 * early_quality.mean(dim=1) - early_center_cost
    centered_objective = torch.tensor([2.0])
    assert centered_objective.item() > early_objective.item() + 1.5

    previous = torch.zeros(4, 6, dtype=torch.bool)
    release = torch.zeros_like(previous)
    release[0, [5, 4, 3]] = True
    release[1, [5, 3]] = True
    release[2, [3, 4]] = True
    release[3, [5, 4]] = True
    subframe = torch.zeros(4, 6)
    subframe[0, [5, 4, 3]] = torch.tensor([0.1, 0.2, 0.3])
    subframe[1, [5, 3]] = torch.tensor([0.1, 0.2])
    subframe[2, [3, 4]] = torch.tensor([0.1, 0.2])
    subframe[3, [5, 4]] = torch.tensor([0.1, 0.2])
    directions = torch.ones(4, 6, dtype=torch.int8)
    directions[3, 4] = -1
    traversal = torch.zeros_like(previous)
    traversal[:, 3:6] = True
    ordered = strike_ordered_release_progress(
        previous, release, subframe, directions, traversal,
        torch.ones(4, dtype=torch.int8))
    assert ordered["complete"].tolist() == [True, False, False, False]
    assert ordered["order_violation_count"].tolist() == [0, 1, 2, 0]
    assert ordered["wrong_direction_count"].tolist() == [0, 0, 0, 1]
    assert ordered["accumulated_release"][1, 5]
    assert not ordered["accumulated_release"][1, 3]

    next_string = strike_next_traversal_string(
        traversal,
        ordered["accumulated_release"],
        torch.ones(4, dtype=torch.int8),
        torch.zeros(4, dtype=torch.long),
    )
    assert next_string.tolist() == [0, 4, 5, 4]

    full = torch.ones(2, 6, dtype=torch.bool)
    limited = strike_limit_traversal_span(
        full, torch.tensor([1, -1], dtype=torch.int8), 2)
    assert limited[0].tolist() == [False, False, False, False, True, True]
    assert limited[1].tolist() == [True, True, False, False, False, False]

    focused = strike_focused_practice_direction(
        torch.tensor([1, -1, 1, -1], dtype=torch.int8),
        torch.tensor([0.10, 0.20, 0.60, 0.80]),
        focus_direction=1,
        target_focus_fraction=0.70)
    assert focused["focused_subset"].tolist() == [True, True, False, False]
    assert focused["direction"].tolist() == [1, 1, 1, -1]

    complete_traversal = torch.ones(2, 6, dtype=torch.bool)
    completed = torch.zeros_like(complete_traversal)
    sweep_direction = torch.tensor([1, -1], dtype=torch.int8)
    recovery_start_steps = []
    for step in range(6):
        frame_release = torch.zeros_like(complete_traversal)
        frame_release[0, 5 - step] = True
        frame_release[1, step] = True
        frame_subframe = torch.zeros(2, 6)
        frame_subframe[frame_release] = 0.5
        frame_direction = torch.zeros(2, 6, dtype=torch.int8)
        frame_direction[0, 5 - step] = 1
        frame_direction[1, step] = -1
        sweep = strike_ordered_release_progress(
            completed,
            frame_release,
            frame_subframe,
            frame_direction,
            complete_traversal,
            sweep_direction)
        completion_candidate = strike_physical_target_candidate(
            sweep["complete"] & sweep["accepted_release"].any(dim=1),
            torch.zeros(2, dtype=torch.bool),
            torch.zeros(2, dtype=torch.bool))
        assert completion_candidate.tolist() == (
            [True, True] if step == 5 else [False, False])
        recovery_start_steps.append(completion_candidate)
        completed = sweep["accumulated_release"]
    assert completed.all()
    assert torch.stack(recovery_start_steps).T.tolist() == [
        [False, False, False, False, False, True],
        [False, False, False, False, False, True],
    ]
    repeated_completion = strike_physical_target_candidate(
        torch.ones(2, dtype=torch.bool),
        torch.ones(2, dtype=torch.bool),
        torch.zeros(2, dtype=torch.bool))
    assert not repeated_completion.any()

    final_string_point = torch.zeros(2, 3)
    exit_point = torch.tensor([
        [0.004, 0.0, 0.0],
        [-0.004, 0.0, 0.0],
    ])
    best = torch.zeros(2)
    increments = []
    for fraction in (0.25, 0.10, 0.75, 1.00):
        progress = strike_strum_terminal_progress(
            final_string_point + fraction * exit_point,
            final_string_point,
            exit_point,
            best,
            torch.ones(2, dtype=torch.bool))
        increments.append(progress["increment"])
        best = progress["best"]
    assert torch.allclose(increments[0], torch.full((2,), 0.25))
    assert not increments[1].any()
    assert torch.allclose(increments[2], torch.full((2,), 0.50))
    assert torch.allclose(increments[3], torch.full((2,), 0.25))
    assert torch.allclose(sum(increments), torch.ones(2))
    assert torch.allclose(best, torch.ones(2))

    streak = torch.zeros(1, dtype=torch.long)
    success = torch.zeros(1, dtype=torch.bool)
    pulses = []
    for _ in range(6):
        ready = strike_ready_latch(
            torch.ones(1, dtype=torch.bool),
            torch.ones(1, dtype=torch.bool),
            streak,
            success,
            hold_frames=6,
        )
        streak = ready["ready_streak"]
        success = ready["ready_success"]
        pulses.append(bool(ready["ready_pulse"].item()))
    assert pulses == [False, False, False, False, False, True]
    assert success.item()



    ready = strike_ready_latch(
        torch.zeros(1, dtype=torch.bool),
        torch.ones(1, dtype=torch.bool),
        streak,
        success,
        hold_frames=6,
    )
    streak = ready["ready_streak"]
    for _ in range(6):
        ready = strike_ready_latch(
            torch.ones(1, dtype=torch.bool),
            torch.ones(1, dtype=torch.bool),
            streak,
            success,
            hold_frames=6,
        )
        streak = ready["ready_streak"]
        assert not ready["ready_pulse"].item()

    a1 = strike_ready_episode_resolution(
        torch.tensor([False, True, True]),
        torch.tensor([True, True, False]),
    )
    assert torch.equal(a1["done"], torch.tensor([False, True, True]))
    assert torch.equal(a1["success"], torch.tensor([False, True, False]))
    assert torch.equal(a1["miss"], torch.tensor([False, False, True]))

    physical = torch.tensor([True, True, False])
    timing_ok = torch.tensor([True, False, True])
    timed = strike_timing_gate(
        physical, timing_ok, timing_required=True)
    assert torch.equal(
        timed["timing_sample"], torch.tensor([True, True, False]))
    assert torch.equal(
        timed["success_candidate"], torch.tensor([True, False, False]))
    assert (timed["timing_sample"].data_ptr()
            != timed["success_candidate"].data_ptr())

    outcomes = strike_event_outcome_masks(
        physical,
        timed["success_candidate"],
        torch.tensor([False, True, True]))
    assert torch.equal(
        outcomes["newly_resolved"], torch.tensor([True, True, True]))
    assert torch.equal(
        outcomes["physical_hit"], torch.tensor([True, True, False]))
    assert torch.equal(
        outcomes["physical_miss"], torch.tensor([False, False, True]))

    mixed_song_direction = strike_directional_strum_outcomes(
        torch.tensor([True, True, True, True]),
        torch.tensor([True, True, True, False]),
        torch.tensor([False, False, True, True]),
        torch.tensor([1, -1, 1, -1], dtype=torch.int8))
    assert mixed_song_direction["down_event"].tolist() == [
        False, False, True, False]
    assert mixed_song_direction["up_event"].tolist() == [
        False, False, False, True]
    assert mixed_song_direction["down_completed"].sum().item() == 1
    assert mixed_song_direction["up_completed"].sum().item() == 0
    assert (
        mixed_song_direction["down_event"].sum()
        + mixed_song_direction["up_event"].sum()
    ).item() == 2

    untimed = strike_timing_gate(
        physical, timing_ok, timing_required=False)
    assert not untimed["timing_sample"].any()
    assert torch.equal(untimed["success_candidate"], physical)

    matcher_candidate = strike_physical_target_candidate(
        torch.tensor([True, True, True, True]),
        torch.tensor([False, False, True, False]),
        torch.tensor([False, False, False, True]),
    )
    assert torch.equal(
        matcher_candidate, torch.tensor([True, True, False, False]))

    false_positives = strike_false_positive_count(
        torch.tensor([
            [True, False, False],
            [True, True, False],
            [False, False, False],
        ]),
        torch.tensor([True, True, False]),
        torch.tensor([
            [False, False, False],
            [False, False, True],
            [True, False, True],
        ]),
    )
    assert torch.equal(false_positives, torch.tensor([0.0, 2.0, 2.0]))

    recovery_context = strike_release_recovery_context(
        torch.tensor([
            [True, False, True],
            [False, False, False],
        ]),
        torch.tensor([
            [0.2, 0.0, 0.8],
            [0.0, 0.0, 0.0],
        ]),
        torch.tensor([
            [[0.0, -0.30, 0.0], [0.0, 0.0, 0.0],
             [0.0, -0.35, 0.0]],
            [[0.0, 0.0, 0.0]] * 3,
        ]),
        torch.tensor([
            [1, 0, -1],
            [0, 0, 0],
        ], dtype=torch.int8),
    )
    assert torch.equal(
        recovery_context["released"], torch.tensor([True, False]))
    assert torch.equal(
        recovery_context["release_string"], torch.tensor([2, 0]))
    assert torch.allclose(
        recovery_context["release_lane_y"], torch.tensor([-0.35, 0.0]))
    assert torch.equal(
        recovery_context["release_direction"], torch.tensor([-1, 1]))

    recovery_timeout = strike_recovery_incomplete_timeout(
        torch.tensor([True, True, True, False]),
        torch.tensor([True, True, True, True]),
        torch.tensor([11, 12, 12, 0], dtype=torch.long),
        torch.tensor([True, False, True, False]),
        recovery_frames=12,
    )
    assert torch.equal(
        recovery_timeout, torch.tensor([True, True, False, False]))

    recovery_frames = strike_completed_recovery_frames(
        torch.tensor([2, 2, 1], dtype=torch.long),
        torch.tensor([7, 7, 7], dtype=torch.long),
        release_recover_phase=2,
        disruption=torch.tensor([False, True, False]),
    )
    assert torch.equal(recovery_frames, torch.tensor([8, 0, 0]))

    recovery_progress = strike_clean_recovery_progress(
        torch.tensor([2, 7, 12, 4]),
        torch.tensor([0, 8, 11, 4]),
        torch.tensor([True, True, True, False]),
        torch.tensor([True, True, True, True]),
        torch.tensor([False, False, False, False]),
        recovery_frames=12,
    )
    assert torch.equal(
        recovery_progress["best_count"], torch.tensor([2, 8, 12, 4]))
    assert torch.allclose(
        recovery_progress["progress"],
        torch.tensor([2.0 / 12.0, 0.0, 1.0 / 12.0, 0.0]))
    assert torch.equal(
        recovery_progress["complete_pulse"],
        torch.tensor([False, False, True, False]))
    repeated = strike_clean_recovery_progress(
        torch.tensor([2]), recovery_progress["best_count"][2:3],
        torch.tensor([True]), torch.tensor([True]),
        recovery_progress["completion_recorded"][2:3], recovery_frames=12)
    assert repeated["progress"].item() == 0.0
    assert not repeated["complete_pulse"].item()
    disrupted_after_completion = strike_clean_recovery_progress(
        torch.tensor([12]), torch.tensor([0]),
        torch.tensor([True]), torch.tensor([True]), torch.tensor([True]),
        recovery_frames=12)
    assert not disrupted_after_completion["complete_pulse"].item()

    release_lift = torch.tensor([[1.0, 0.0, 0.1]])
    next_entry_lift = torch.tensor([[2.0, 0.0, 0.1]])
    next_ready = torch.tensor([[2.0, 0.0, 0.02]])
    before_lift = strike_recovery_clearance_target(
        torch.tensor([True]), torch.tensor([True]), torch.tensor([False]),
        torch.tensor([False]), release_lift, next_entry_lift, next_ready)
    assert before_lift["active"].item()
    assert torch.equal(before_lift["target"], release_lift)
    after_lift = strike_recovery_clearance_target(
        torch.tensor([True]), torch.tensor([True]), torch.tensor([True]),
        torch.tensor([False]), release_lift, next_entry_lift, next_ready)
    assert after_lift["active"].item()
    assert torch.equal(after_lift["target"], next_entry_lift)
    after_clearance = strike_recovery_clearance_target(
        torch.tensor([True]), torch.tensor([True]), torch.tensor([True]),
        torch.tensor([True]), release_lift, next_entry_lift, next_ready)
    assert after_clearance["active"].item()
    assert torch.equal(after_clearance["target"], next_ready)

    path_clearance = strike_handoff_path_clearance(
        torch.tensor([True, True, True, False]),
        torch.tensor([0, 0, 0, 0]),
        torch.tensor([1, 1, 1, 1]),
        torch.tensor([1, 0, 5, 5]),
        torch.tensor([-1, -1, 1, 1]),
        num_strings=6)
    assert path_clearance["clearance_required"].tolist() == [
        True, False, True, False]
    assert path_clearance["crossing_mask"][0].tolist() == [
        True, False, False, False, False, False]
    assert path_clearance["crossing_mask"][2].tolist() == [
        True, True, True, True, True, True]
    assert path_clearance["same_string"].tolist() == [
        False, True, False, False]

    waypoint = strike_clearance_waypoint_state(
        torch.tensor([True, True, False]),
        torch.tensor([False, True, False]),
        torch.zeros(3, dtype=torch.bool),
        torch.tensor([0.002, 0.002, 0.002]),
        distance_threshold=0.004)
    assert waypoint["target_changed"].tolist() == [True, False, False]
    assert waypoint["reached_pulse"].tolist() == [False, True, False]
    assert waypoint["lifted"].tolist() == [True, True, False]
    assert waypoint["reached"].tolist() == [False, True, False]
    second_waypoint = strike_clearance_waypoint_state(
        torch.tensor([True]),
        waypoint["lifted"][:1],
        waypoint["reached"][:1],
        torch.tensor([0.003]),
        distance_threshold=0.004)
    assert not second_waypoint["target_changed"].item()
    assert second_waypoint["reached_pulse"].item()

    dual_plan = strike_dual_recovery_plan(
        torch.tensor([1.0, 1.0, 1.0, 1.0]),
        torch.tensor([1.40, 1.22, 1.05, 1.05]),
        torch.tensor([True, True, True, False]),
        torch.tensor([2, 2, 2, 2]),
        torch.tensor([1, -1, 1, 1]),
        torch.tensor([3, 3, 2, 2]),
        torch.tensor([1, -1, -1, -1]),
        num_strings=6,
        sim_hz=60,
        approach_lead_s=0.07,
        full_recovery_frames=12,
        minimum_handoff_frames=1,
    )
    assert dual_plan["available_frames"].tolist() == [19, 9, -2, -2]
    assert dual_plan["required_frames"].tolist() == [12, 9, 1, 12]
    assert dual_plan["handoff"].tolist() == [False, True, True, False]
    assert dual_plan["same_string_handoff"].tolist() == [False, False, True, False]
    assert dual_plan["clearance_required"].tolist() == [True, False, False, False]
    assert dual_plan["rearm_required"].tolist() == [True, False, True, False]

    dual_transition = strike_dual_recovery_to_approach(
        torch.tensor([2, 2, 2, 2]),
        torch.zeros(4, dtype=torch.bool),
        torch.tensor([12, 9, 1, 12]),
        torch.tensor([True, False, False, False]),
        torch.tensor([0.06, 0.06, 0.06, 0.08]),
        dual_plan["required_frames"],
        dual_plan["handoff"],
        dual_plan["same_string_handoff"],
        dual_plan["clearance_required"],
        torch.tensor([True, False, False, False]),
        release_recover_phase=2,
        approach_lead_s=0.07,
    )
    assert dual_transition.tolist() == [True, True, False, False]

    protected_handoff = strike_dual_recovery_to_approach(
        torch.full((3,), 2, dtype=torch.long),
        torch.zeros(3, dtype=torch.bool),
        torch.ones(3, dtype=torch.long),
        torch.tensor([False, True, True]),
        torch.zeros(3),
        torch.ones(3, dtype=torch.long),
        torch.ones(3, dtype=torch.bool),
        torch.zeros(3, dtype=torch.bool),
        torch.ones(3, dtype=torch.bool),
        torch.tensor([True, False, True]),
        release_recover_phase=2,
        approach_lead_s=0.07,
    )
    assert protected_handoff.tolist() == [False, False, True]

    dual_progress = strike_dual_recovery_progress(
        torch.tensor([12, 9, 1, 12]),
        torch.tensor([11, 8, 0, 11]),
        torch.tensor([True, False, False, False]),
        torch.ones(4, dtype=torch.bool),
        dual_plan["required_frames"],
        dual_plan["handoff"],
        dual_transition,
        dual_plan["clearance_required"],
        torch.tensor([True, False, False, False]),
        torch.zeros(4, dtype=torch.bool),
    )
    assert torch.allclose(
        dual_progress["progress"],
        torch.tensor([1.0 / 12.0, 1.0 / 9.0, 1.0, 0.0]))
    assert dual_progress["complete_pulse"].tolist() == [True, True, False, False]
    repeated_dual = strike_dual_recovery_progress(
        torch.tensor([12]),
        dual_progress["best_count"][:1],
        torch.tensor([True]),
        torch.tensor([True]),
        dual_plan["required_frames"][:1],
        dual_plan["handoff"][:1],
        torch.tensor([False]),
        dual_plan["clearance_required"][:1],
        torch.tensor([True]),
        dual_progress["completion_recorded"][:1],
    )
    assert repeated_dual["progress"].item() == 0.0
    assert not repeated_dual["complete_pulse"].item()





    resolved = torch.tensor([True, True, True, False])
    phase = torch.tensor([1, 2, 2, 1], dtype=torch.long)
    recovery = torch.tensor([0, 11, 12, 0], dtype=torch.long)
    timeout = torch.tensor([False, False, False, True])
    result = strike_resolved_episode_done(
        resolved,
        phase,
        recovery,
        torch.tensor([True, True, True, True]),
        timeout,
        release_recover_phase=2,
        recovery_frames=12,
    )
    assert torch.equal(
        result["recovery_finished"],
        torch.tensor([True, False, True, True]))
    assert torch.equal(
        result["done"],
        torch.tensor([True, False, True, True]))
    not_rearmed = strike_resolved_episode_done(
        torch.tensor([True]),
        torch.tensor([2], dtype=torch.long),
        torch.tensor([12], dtype=torch.long),
        torch.tensor([False]),
        torch.tensor([False]),
        release_recover_phase=2,
        recovery_frames=12,
    )
    assert not not_rearmed["recovery_finished"].item()
    assert not not_rearmed["done"].item()

    print("PASS: fixed-horizon ready, uncensored timing and release recovery")


if __name__ == "__main__":
    main()
