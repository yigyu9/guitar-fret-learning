"""Deterministic timing supervisor for fixed-guitar two-hand play.

The Synchronizer deliberately owns no humanoid joint.  It consumes the
canonical event, physical Fret readiness and Strike readiness, then opens a
short, bounded physical-release window.  Source actors remain frozen and see
their native observation contract; the decision returned here is enforced by
the Full runtime outside those actors.

The implementation is batched and Isaac-free so the exact event/deadline
semantics can be tested on CPU before a combined physics task exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional

import torch


SYNCHRONIZER_SCHEMA = "tab2body.rule_synchronizer.v2"
N_GUITAR_STRINGS = 6


class DeadlineAction(IntEnum):
    """Command issued before the next physics step."""

    PREPARE = 0
    WAIT = 1
    EXECUTE = 2
    SKIP = 3
    RESOLVED = 4


class EventOutcome(IntEnum):
    """Exactly-once terminal result for one canonical event."""

    ACTIVE = 0
    FULL = 1
    PARTIAL = 2
    MISSED_FRET = 3
    MISSED_STRIKE = 4
    MISSED_BOTH = 5
    MISSED_STABILITY = 6


class DelayCause(IntEnum):
    """Hand-side cause accumulated while the event was delayed."""

    NONE = 0
    FRET = 1
    STRIKE = 2
    BOTH = 3


@dataclass(frozen=True)
class SynchronizerDecision:
    """Batched command produced immediately before one physics step."""

    event_id: torch.Tensor
    score_frame: torch.Tensor
    action: torch.Tensor
    strike_permission: torch.Tensor
    traversal_permission_mask: torch.Tensor
    scorable_target_mask: torch.Tensor
    hold_strike_action: torch.Tensor
    hold_fret_action: torch.Tensor
    release_decision_deadline_frame: torch.Tensor
    completion_deadline_frame: torch.Tensor
    timing_shift_frames: torch.Tensor
    timing_shift_s: torch.Tensor
    delay_cause: torch.Tensor
    resolved: torch.Tensor
    outcome: torch.Tensor


@dataclass(frozen=True)
class SynchronizerResult:
    """Post-physics event result and detector audit signals."""

    event_id: torch.Tensor
    resolved_pulse: torch.Tensor
    resolved: torch.Tensor
    outcome: torch.Tensor
    accepted_crossing_mask: torch.Tensor
    ordered_crossing_mask: torch.Tensor
    planned_crossing_mask: torch.Tensor
    protected_crossing_mask: torch.Tensor
    failed_target_crossing_mask: torch.Tensor
    blocked_crossing_mask: torch.Tensor
    unplanned_crossing_mask: torch.Tensor
    wrong_direction_crossing_mask: torch.Tensor
    order_violation_crossing_mask: torch.Tensor
    crossing_contract_violated: torch.Tensor
    accumulated_crossing_mask: torch.Tensor
    target_success_mask: torch.Tensor
    traversal_complete: torch.Tensor
    delay_frames: torch.Tensor
    delay_cause: torch.Tensor


def _as_tensor(value, *, device, dtype, shape, name):
    result = torch.as_tensor(value, device=device, dtype=dtype)
    if tuple(result.shape) != tuple(shape):
        raise ValueError(
            f"{name} must have shape {tuple(shape)}, got {tuple(result.shape)}")
    if result.is_floating_point() and not torch.isfinite(result).all():
        raise ValueError(f"{name} must be finite")
    return result


class RuleBasedSynchronizer:
    """One-cursor, bounded-delay rule supervisor.

    Call :meth:`before_step` once, apply its physical permission and action
    holds, simulate exactly once, and then call :meth:`after_step` with the
    detector crossings from that same step.  An event may be replaced only
    after it has resolved.  This fail-closed ordering prevents Fret and Strike
    from silently advancing separate cursors.

    ``readiness_dwell_frames=1`` means that a target must be correct at two
    consecutive frame boundaries: the first observation starts the dwell and
    the second proves one complete intervening control frame.  Dwell carries
    across a repeated strike only for an unchanged ``(string, fret)`` target.
    """

    def __init__(
            self, num_envs: int, *, device="cpu", fps: int = 60,
            configured_max_delay_frames: int = 3,
            readiness_dwell_frames: int = 1):
        self.num_envs = int(num_envs)
        self.device = torch.device(device)
        self.fps = int(fps)
        self.configured_max_delay_frames = int(
            configured_max_delay_frames)
        self.readiness_dwell_frames = int(readiness_dwell_frames)
        if self.num_envs < 1:
            raise ValueError("num_envs must be positive")
        if self.fps < 1:
            raise ValueError("fps must be positive")
        if self.configured_max_delay_frames < 0:
            raise ValueError("configured_max_delay_frames must be non-negative")
        if self.readiness_dwell_frames < 0:
            raise ValueError("readiness_dwell_frames must be non-negative")

        n, d = self.num_envs, self.device
        self.event_id = torch.full((n,), -1, dtype=torch.long, device=d)
        self.target_frets = torch.full(
            (n, N_GUITAR_STRINGS), -1, dtype=torch.long, device=d)
        self.audible_mask = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.bool, device=d)
        self.traversal_mask = torch.zeros_like(self.audible_mask)
        self.traversal_order = torch.full(
            (n, N_GUITAR_STRINGS), -1, dtype=torch.long, device=d)
        self.traversal_offsets_s = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.float32, device=d)
        self.strike_direction = torch.zeros(n, dtype=torch.int8, device=d)
        self.release_boundary_frame = torch.zeros(
            n, dtype=torch.long, device=d)
        self.traversal_end_frame = torch.zeros(
            n, dtype=torch.long, device=d)
        self.delay_budget_frames = torch.zeros(
            n, dtype=torch.long, device=d)
        self.ready_streak = torch.zeros(
            n, N_GUITAR_STRINGS, dtype=torch.long, device=d)
        self.permission_open = torch.zeros(n, dtype=torch.bool, device=d)
        self.scorable_target_mask = torch.zeros_like(self.audible_mask)
        self.completion_deadline_frame = torch.full(
            (n,), -1, dtype=torch.long, device=d)
        self.accumulated_crossing_mask = torch.zeros_like(self.audible_mask)
        self.target_success_mask = torch.zeros_like(self.audible_mask)
        self.failed_target_crossing_mask = torch.zeros_like(
            self.audible_mask)
        self.crossing_contract_violated = torch.zeros(
            n, dtype=torch.bool, device=d)
        self.resolved = torch.ones(n, dtype=torch.bool, device=d)
        self._resolution_pending = torch.zeros(
            n, dtype=torch.bool, device=d)
        self.outcome = torch.full(
            (n,), int(EventOutcome.ACTIVE), dtype=torch.long, device=d)
        self.selected_delay_frames = torch.zeros(
            n, dtype=torch.long, device=d)
        self.fret_blocked_during_window = torch.zeros(
            n, dtype=torch.bool, device=d)
        self.strike_blocked_during_window = torch.zeros(
            n, dtype=torch.bool, device=d)
        self.stability_blocked_during_window = torch.zeros(
            n, dtype=torch.bool, device=d)
        self.strike_entry_hold_latched = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._last_score_frame = torch.full(
            (n,), -1, dtype=torch.long, device=d)
        self._clock_initialized = torch.zeros(
            n, dtype=torch.bool, device=d)
        self._before_step_pending = torch.zeros(
            n, dtype=torch.bool, device=d)

    @property
    def release_decision_deadline_frame(self):
        return self.release_boundary_frame + self.delay_budget_frames

    def reset(self, env_ids: Optional[torch.Tensor] = None) -> None:
        if env_ids is None:
            ids = torch.arange(
                self.num_envs, dtype=torch.long, device=self.device)
        else:
            ids = torch.as_tensor(
                env_ids, dtype=torch.long, device=self.device).reshape(-1)
            if ids.numel() and (
                    (ids < 0).any() or (ids >= self.num_envs).any()):
                raise IndexError("reset env_ids are outside the batch")
        self.event_id[ids] = -1
        self.target_frets[ids] = -1
        self.audible_mask[ids] = False
        self.traversal_mask[ids] = False
        self.traversal_order[ids] = -1
        self.traversal_offsets_s[ids] = 0.0
        self.strike_direction[ids] = 0
        self.release_boundary_frame[ids] = 0
        self.traversal_end_frame[ids] = 0
        self.delay_budget_frames[ids] = 0
        self.ready_streak[ids] = 0
        self.permission_open[ids] = False
        self.scorable_target_mask[ids] = False
        self.completion_deadline_frame[ids] = -1
        self.accumulated_crossing_mask[ids] = False
        self.target_success_mask[ids] = False
        self.failed_target_crossing_mask[ids] = False
        self.crossing_contract_violated[ids] = False
        self.resolved[ids] = True
        self._resolution_pending[ids] = False
        self.outcome[ids] = int(EventOutcome.ACTIVE)
        self.selected_delay_frames[ids] = 0
        self.fret_blocked_during_window[ids] = False
        self.strike_blocked_during_window[ids] = False
        self.stability_blocked_during_window[ids] = False
        self.strike_entry_hold_latched[ids] = False
        self._last_score_frame[ids] = -1
        self._clock_initialized[ids] = False
        self._before_step_pending[ids] = False

    def _delay_cause(self):
        fret = self.fret_blocked_during_window
        strike = self.strike_blocked_during_window
        result = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        result = torch.where(
            fret & ~strike,
            torch.full_like(result, int(DelayCause.FRET)), result)
        result = torch.where(
            ~fret & strike,
            torch.full_like(result, int(DelayCause.STRIKE)), result)
        result = torch.where(
            fret & strike,
            torch.full_like(result, int(DelayCause.BOTH)), result)
        return result

    def _activate_changed_events(
            self, changed, event_id, release_boundary_frame,
            traversal_end_frame, delay_budget_frames, target_frets,
            audible_mask, traversal_mask, traversal_order,
            traversal_offsets_s, strike_direction):
        unresolved_change = changed & ~self.resolved
        if bool(unresolved_change.any().item()):
            rows = torch.nonzero(unresolved_change).flatten().tolist()
            raise RuntimeError(
                "canonical event changed before exactly-once resolution for "
                f"environments {rows}")
        noncontiguous = (
            changed & (self.event_id >= 0) & (event_id != self.event_id + 1))
        if bool(noncontiguous.any().item()):
            rows = torch.nonzero(noncontiguous).flatten().tolist()
            raise RuntimeError(
                "canonical event cursor must advance exactly once for "
                f"environments {rows}")

        # Preserve readiness only for a continuously held, identical target.
        same_target = (
            (self.target_frets == target_frets)
            & audible_mask & self.audible_mask)
        self.ready_streak[changed] = torch.where(
            same_target[changed], self.ready_streak[changed],
            torch.zeros_like(self.ready_streak[changed]))
        self.event_id[changed] = event_id[changed]
        self.target_frets[changed] = target_frets[changed]
        self.audible_mask[changed] = audible_mask[changed]
        self.traversal_mask[changed] = traversal_mask[changed]
        self.traversal_order[changed] = traversal_order[changed]
        self.traversal_offsets_s[changed] = traversal_offsets_s[changed]
        self.strike_direction[changed] = strike_direction[changed]
        self.release_boundary_frame[changed] = release_boundary_frame[changed]
        self.traversal_end_frame[changed] = traversal_end_frame[changed]
        self.delay_budget_frames[changed] = delay_budget_frames[changed]
        self.permission_open[changed] = False
        self.scorable_target_mask[changed] = False
        self.completion_deadline_frame[changed] = -1
        self.accumulated_crossing_mask[changed] = False
        self.target_success_mask[changed] = False
        self.failed_target_crossing_mask[changed] = False
        self.crossing_contract_violated[changed] = False
        self.resolved[changed] = False
        self._resolution_pending[changed] = False
        self.outcome[changed] = int(EventOutcome.ACTIVE)
        self.selected_delay_frames[changed] = 0
        self.fret_blocked_during_window[changed] = False
        self.strike_blocked_during_window[changed] = False
        self.stability_blocked_during_window[changed] = False
        self.strike_entry_hold_latched[changed] = False
        self._before_step_pending[changed] = False

    def _resolve_without_crossing(self, rows, fret_ready, strike_ready,
                                  guitar_stable):
        if not rows.any():
            return
        fret_missing = ~fret_ready
        strike_missing = ~strike_ready
        outcome = torch.full_like(self.outcome, int(EventOutcome.MISSED_FRET))
        outcome = torch.where(
            fret_missing & strike_missing,
            torch.full_like(outcome, int(EventOutcome.MISSED_BOTH)), outcome)
        outcome = torch.where(
            ~fret_missing & strike_missing,
            torch.full_like(outcome, int(EventOutcome.MISSED_STRIKE)), outcome)
        outcome = torch.where(
            ~guitar_stable,
            torch.full_like(outcome, int(EventOutcome.MISSED_STABILITY)), outcome)
        self.outcome[rows] = outcome[rows]
        self.resolved[rows] = True
        self._resolution_pending[rows] = True
        self.permission_open[rows] = False
        self.scorable_target_mask[rows] = False

    def before_step(
            self, *, event_id, score_frame, release_boundary_frame,
            traversal_end_frame, delay_budget_frames, target_frets,
            audible_mask, traversal_mask, traversal_order,
            traversal_offsets_s, strike_direction,
            fret_ready_mask, strike_ready, guitar_stable=None
            ) -> SynchronizerDecision:
        """Update readiness and decide whether this physics step may strike.

        ``fret_ready_mask`` is target-specific physical truth, not a policy
        intention.  The caller must derive it from effective sounding fret for
        the canonical audible strings.  Protected traversal strings must be
        absent from ``audible_mask``.
        """
        n, d = self.num_envs, self.device
        event_id = _as_tensor(
            event_id, device=d, dtype=torch.long, shape=(n,), name="event_id")
        score_frame = _as_tensor(
            score_frame, device=d, dtype=torch.long, shape=(n,),
            name="score_frame")
        boundary = _as_tensor(
            release_boundary_frame, device=d, dtype=torch.long, shape=(n,),
            name="release_boundary_frame")
        traversal_end = _as_tensor(
            traversal_end_frame, device=d, dtype=torch.long, shape=(n,),
            name="traversal_end_frame")
        budget = _as_tensor(
            delay_budget_frames, device=d, dtype=torch.long, shape=(n,),
            name="delay_budget_frames")
        targets = _as_tensor(
            target_frets, device=d, dtype=torch.long,
            shape=(n, N_GUITAR_STRINGS), name="target_frets")
        audible = _as_tensor(
            audible_mask, device=d, dtype=torch.bool,
            shape=(n, N_GUITAR_STRINGS), name="audible_mask")
        traversal = _as_tensor(
            traversal_mask, device=d, dtype=torch.bool,
            shape=(n, N_GUITAR_STRINGS), name="traversal_mask")
        order = _as_tensor(
            traversal_order, device=d, dtype=torch.long,
            shape=(n, N_GUITAR_STRINGS), name="traversal_order")
        offsets = _as_tensor(
            traversal_offsets_s, device=d, dtype=torch.float32,
            shape=(n, N_GUITAR_STRINGS), name="traversal_offsets_s")
        direction = _as_tensor(
            strike_direction, device=d, dtype=torch.int8, shape=(n,),
            name="strike_direction")
        ready_now = _as_tensor(
            fret_ready_mask, device=d, dtype=torch.bool,
            shape=(n, N_GUITAR_STRINGS), name="fret_ready_mask")
        strike_ready = _as_tensor(
            strike_ready, device=d, dtype=torch.bool, shape=(n,),
            name="strike_ready")
        if guitar_stable is None:
            guitar_stable = torch.ones(n, dtype=torch.bool, device=d)
        else:
            guitar_stable = _as_tensor(
                guitar_stable, device=d, dtype=torch.bool, shape=(n,),
                name="guitar_stable")

        if bool((event_id < 0).any().item()):
            raise ValueError("event_id must be non-negative")
        if bool((budget < 0).any().item()) or bool(
                (budget > self.configured_max_delay_frames).any().item()):
            raise ValueError(
                "delay_budget_frames exceeds the configured bounded delay")
        if bool((~audible.any(dim=1)).any().item()):
            raise ValueError("every canonical event must have an audible target")
        if bool((~traversal.any(dim=1)).any().item()):
            raise ValueError("every canonical event must traverse a string")
        if bool((audible & ~traversal).any().item()):
            raise ValueError("audible targets must be a subset of traversal")
        traversal_count = traversal.sum(dim=1)
        slots = torch.arange(
            N_GUITAR_STRINGS, dtype=torch.long, device=d)[None]
        active_order_slot = slots < traversal_count[:, None]
        if bool(((order >= 0) != active_order_slot).any().item()) or bool(
                ((order[active_order_slot] < 0)
                 | (order[active_order_slot] >= N_GUITAR_STRINGS)).any().item()):
            raise ValueError(
                "traversal_order must contain active strings then -1 padding")
        ordered_count = torch.zeros_like(traversal, dtype=torch.long)
        ordered_count.scatter_add_(
            1, order.clamp_min(0), active_order_slot.to(torch.long))
        if bool((ordered_count != traversal.to(torch.long)).any().item()):
            raise ValueError(
                "traversal_order must contain every traversal string exactly once")
        if bool(((direction != -1) & (direction != 1)).any().item()):
            raise ValueError("strike_direction must contain only -1 or +1")
        adjacent_slot = slots[:, 1:] < traversal_count[:, None]
        order_delta = order[:, 1:] - order[:, :-1]
        direction_order_bad = adjacent_slot & torch.where(
            (direction == 1)[:, None], order_delta >= 0, order_delta <= 0)
        if bool(direction_order_bad.any().item()):
            raise ValueError(
                "traversal_order is inconsistent with strike_direction")
        offset_delta = offsets[:, 1:] - offsets[:, :-1]
        if bool((adjacent_slot & (offset_delta <= 0.0)).any().item()) or bool(
                ((~active_order_slot) & (offsets != 0.0)).any().item()):
            raise ValueError(
                "traversal_offsets_s must increase in traversal order and use "
                "zero padding")
        if bool((traversal_end < boundary).any().item()):
            raise ValueError("traversal_end_frame precedes release boundary")
        if bool(((targets < 0) & audible).any().item()):
            raise ValueError("audible target frets must be non-negative")
        if bool(((targets >= 0) & ~audible).any().item()):
            raise ValueError("inactive strings must use target_fret=-1")
        if bool(self._before_step_pending.any().item()):
            rows = torch.nonzero(self._before_step_pending).flatten().tolist()
            raise RuntimeError(
                "before_step called twice without after_step for "
                f"environments {rows}")

        backwards = (
            self._clock_initialized
            & (score_frame < self._last_score_frame))
        if bool(backwards.any().item()):
            raise RuntimeError("score clock must be monotonic")
        changed = event_id != self.event_id
        self._activate_changed_events(
            changed, event_id, boundary, traversal_end, budget, targets,
            audible, traversal, order, offsets, direction)
        unchanged = ~changed
        semantic_change = unchanged & (
            (boundary != self.release_boundary_frame)
            | (traversal_end != self.traversal_end_frame)
            | (budget != self.delay_budget_frames)
            | (targets != self.target_frets).any(dim=1)
            | (audible != self.audible_mask).any(dim=1)
            | (traversal != self.traversal_mask).any(dim=1)
            | (order != self.traversal_order).any(dim=1)
            | (offsets != self.traversal_offsets_s).any(dim=1)
            | (direction != self.strike_direction))
        if bool(semantic_change.any().item()):
            raise RuntimeError(
                "canonical event semantics changed while event_id stayed fixed")
        active_target_ready = ready_now & audible
        self.ready_streak = torch.where(
            active_target_ready,
            self.ready_streak + 1,
            torch.zeros_like(self.ready_streak))
        self.ready_streak.masked_fill_(~audible, 0)
        dwell_ready_mask = (
            self.ready_streak > self.readiness_dwell_frames) & audible
        fret_full_ready = (
            dwell_ready_mask | ~audible).all(dim=1)
        partial_ready = dwell_ready_mask & audible
        target_count = audible.sum(dim=1)

        deadline = self.release_decision_deadline_frame
        before_boundary = score_frame < boundary
        # The Strike actor must remain free to approach the entry boundary.
        # Freezing every WAIT command would deadlock a late Strike hand before
        # it ever became ready.  Latch the hold only after physical entry
        # readiness is observed while permission is still closed.  The shared
        # physics backend remains responsible for treating a closed crossing
        # as a premature/blocked crossing; detector masking alone is not a
        # physical barrier.
        permission_closed = ~self.resolved & ~self.permission_open
        self.strike_entry_hold_latched |= (
            permission_closed & strike_ready)
        in_window = (
            ~self.resolved & ~self.permission_open & ~before_boundary
            & (score_frame <= deadline))
        missed_deadline = (
            ~self.resolved & ~self.permission_open & ~before_boundary
            & (score_frame > deadline))

        blockers_active = in_window & ~self.permission_open
        self.fret_blocked_during_window |= blockers_active & ~fret_full_ready
        self.strike_blocked_during_window |= blockers_active & ~strike_ready
        self.stability_blocked_during_window |= blockers_active & ~guitar_stable

        can_execute_full = (
            in_window & ~self.permission_open & fret_full_ready
            & strike_ready & guitar_stable)
        at_deadline = in_window & (score_frame == deadline)
        can_execute_partial = (
            at_deadline & ~self.permission_open & (target_count > 1)
            & partial_ready.any(dim=1) & ~fret_full_ready
            & strike_ready & guitar_stable)
        open_now = can_execute_full | can_execute_partial
        if open_now.any():
            self.permission_open[open_now] = True
            self.scorable_target_mask[can_execute_full] = audible[
                can_execute_full]
            self.scorable_target_mask[can_execute_partial] = partial_ready[
                can_execute_partial]
            delay = (score_frame - boundary).clamp_min(0)
            self.selected_delay_frames[open_now] = delay[open_now]
            self.completion_deadline_frame[open_now] = (
                traversal_end[open_now] + delay[open_now])

        must_skip_at_deadline = (
            at_deadline & ~self.permission_open)
        skipped_or_expired = must_skip_at_deadline | missed_deadline
        skip_delay = (score_frame - boundary).clamp_min(0)
        self.selected_delay_frames[skipped_or_expired] = torch.minimum(
            skip_delay[skipped_or_expired], budget[skipped_or_expired])
        self._resolve_without_crossing(
            skipped_or_expired,
            fret_full_ready, strike_ready, guitar_stable)

        action = torch.full(
            (n,), int(DeadlineAction.PREPARE), dtype=torch.long, device=d)
        action = torch.where(
            in_window & ~self.permission_open & ~self.resolved,
            torch.full_like(action, int(DeadlineAction.WAIT)), action)
        action = torch.where(
            self.permission_open & ~self.resolved,
            torch.full_like(action, int(DeadlineAction.EXECUTE)), action)
        action = torch.where(
            (must_skip_at_deadline | missed_deadline) & self.resolved,
            torch.full_like(action, int(DeadlineAction.SKIP)), action)
        already_resolved = self.resolved & ~(
            must_skip_at_deadline | missed_deadline)
        action = torch.where(
            already_resolved,
            torch.full_like(action, int(DeadlineAction.RESOLVED)), action)

        # A right-side command is frozen only after the hand has actually
        # reached its entry state.  Before that, the frozen Strike prior keeps
        # approaching using the shifted native timing fields.  Fret keeps
        # moving if it is the blocker; once Fret is ready, holding it preserves
        # the press while the right hand finishes its approach.
        waiting = action == int(DeadlineAction.WAIT)
        closed_entry_hold = (
            self.strike_entry_hold_latched & ~self.permission_open
            & ~self.resolved)
        hold_strike = closed_entry_hold | (action == int(DeadlineAction.SKIP))
        hold_fret = waiting & fret_full_ready
        planned_delay = self.selected_delay_frames.clone()
        not_open_wait = waiting & ~self.permission_open
        planned_delay[not_open_wait] = torch.minimum(
            (score_frame[not_open_wait] - boundary[not_open_wait] + 1)
            .clamp_min(0), budget[not_open_wait])

        self._last_score_frame.copy_(score_frame)
        self._clock_initialized.fill_(True)
        # Every live event is expected to receive an after_step, even PREPARE;
        # detector crossings before permission must be audited as blocked.
        self._before_step_pending.copy_(~self.resolved)

        return SynchronizerDecision(
            event_id=self.event_id.clone(),
            score_frame=score_frame.clone(),
            action=action,
            strike_permission=(self.permission_open & ~self.resolved).clone(),
            traversal_permission_mask=(
                self.traversal_mask
                & (self.permission_open & ~self.resolved)[:, None]).clone(),
            scorable_target_mask=self.scorable_target_mask.clone(),
            hold_strike_action=hold_strike,
            hold_fret_action=hold_fret,
            release_decision_deadline_frame=deadline.clone(),
            completion_deadline_frame=self.completion_deadline_frame.clone(),
            timing_shift_frames=planned_delay,
            timing_shift_s=planned_delay.to(torch.float32) / float(self.fps),
            delay_cause=self._delay_cause(),
            resolved=self.resolved.clone(),
            outcome=self.outcome.clone(),
        )

    def after_step(
            self, *, score_frame, crossing_mask, crossing_subframe_t,
            crossing_direction, fret_ready_mask
            ) -> SynchronizerResult:
        """Consume physical detector crossings from the just-finished step.

        A crossing while permission is closed is reported but cannot consume or
        resurrect an event.  At the deadline, a permitted multi-string gesture
        resolves as partial when at least one canonical audible target sounded.
        """
        n, d = self.num_envs, self.device
        score_frame = _as_tensor(
            score_frame, device=d, dtype=torch.long, shape=(n,),
            name="score_frame")
        crossing = _as_tensor(
            crossing_mask, device=d, dtype=torch.bool,
            shape=(n, N_GUITAR_STRINGS), name="crossing_mask")
        subframe_t = _as_tensor(
            crossing_subframe_t, device=d, dtype=torch.float32,
            shape=(n, N_GUITAR_STRINGS), name="crossing_subframe_t")
        release_direction = _as_tensor(
            crossing_direction, device=d, dtype=torch.int8,
            shape=(n, N_GUITAR_STRINGS), name="crossing_direction")
        fret_ready = _as_tensor(
            fret_ready_mask, device=d, dtype=torch.bool,
            shape=(n, N_GUITAR_STRINGS), name="fret_ready_mask")
        if bool((crossing & ((subframe_t < 0.0) | (subframe_t > 1.0))).any(
                ).item()):
            raise ValueError(
                "crossing_subframe_t must be in [0,1] for every crossing")
        if bool((crossing & ((release_direction != -1)
                             & (release_direction != 1))).any().item()):
            raise ValueError(
                "crossing_direction must be -1 or +1 for every crossing")
        if bool(((release_direction < -1) | (release_direction > 1)).any(
                ).item()):
            raise ValueError("crossing_direction entries must be -1, 0, or +1")
        if bool((score_frame != self._last_score_frame).any().item()):
            raise RuntimeError("after_step score_frame does not match before_step")

        pending = self._before_step_pending
        # Rows resolved by an immediate deadline skip have no pending physics
        # ownership.  Their crossings remain blocked and cannot alter outcome.
        permitted = self.permission_open & ~self.resolved & pending
        planned = crossing & permitted[:, None] & self.traversal_mask
        unplanned = crossing & ~self.traversal_mask
        protected = planned & ~self.audible_mask
        blocked = crossing & (
            ~permitted[:, None] | ~self.traversal_mask)

        # Detector releases are ordered by their swept-segment intersection time
        # inside this control frame.  Across frames, accumulated progress already
        # fixes the earlier/later relation.  Only the exact next authored string
        # in the canonical traversal may advance progress.
        observed_time = torch.where(
            crossing & permitted[:, None], subframe_t,
            torch.full_like(subframe_t, float("inf")))
        observed_order = torch.argsort(observed_time, dim=1)
        ordered = torch.zeros_like(crossing)
        wrong_direction = torch.zeros_like(crossing)
        order_violation = torch.zeros_like(crossing)
        rows = torch.arange(n, dtype=torch.long, device=d)
        progress = self.accumulated_crossing_mask.sum(dim=1)
        previous_time = torch.full(
            (n,), float("-inf"), dtype=subframe_t.dtype, device=d)
        for slot in range(N_GUITAR_STRINGS):
            string_index = observed_order[:, slot]
            active = crossing[rows, string_index] & permitted
            target = self.traversal_mask[rows, string_index]
            direction_ok = (
                release_direction[rows, string_index]
                == self.strike_direction)
            already = self.accumulated_crossing_mask[rows, string_index]
            expected_slot = progress.clamp(
                min=0, max=N_GUITAR_STRINGS - 1)
            expected_string = self.traversal_order[
                rows, expected_slot]
            expected_now = string_index == expected_string
            current_time = observed_time[rows, string_index]
            ambiguous_time = active & (current_time == previous_time)
            can_accept = (
                active & target & direction_ok & ~already & expected_now
                & ~ambiguous_time)
            wrong_now = active & target & ~direction_ok
            order_bad_now = (
                active & target & direction_ok
                & (already | ~expected_now | ambiguous_time))
            ordered[rows, string_index] |= can_accept
            wrong_direction[rows, string_index] |= wrong_now
            order_violation[rows, string_index] |= order_bad_now
            self.accumulated_crossing_mask[rows, string_index] |= can_accept
            progress += can_accept.to(progress.dtype)
            previous_time = torch.where(active, current_time, previous_time)

        crossing_contract_violated_now = (
            unplanned | wrong_direction | order_violation).any(dim=1)
        self.crossing_contract_violated |= crossing_contract_violated_now
        accepted = ordered & self.scorable_target_mask & fret_ready
        failed_target = ordered & self.audible_mask & ~accepted
        self.target_success_mask |= accepted
        self.failed_target_crossing_mask |= failed_target

        traversal_complete = (
            self.accumulated_crossing_mask | ~self.traversal_mask).all(dim=1)
        at_completion_deadline = (
            permitted
            & (score_frame >= self.completion_deadline_frame))
        finish = ~self.resolved & (
            traversal_complete | at_completion_deadline)
        any_success = self.target_success_mask.any(dim=1)
        # A full event requires both musical target correctness and completion
        # of the authored motor traversal.  Missing an intervening/protected
        # traversal string must not be hidden merely because every audible
        # target happened to sound correctly.
        full = (
            finish & traversal_complete & ~self.crossing_contract_violated
            & (self.target_success_mask | ~self.audible_mask).all(dim=1))
        partial = finish & ~full & any_success
        no_success = finish & ~any_success
        fret_failed = self.failed_target_crossing_mask.any(dim=1)
        strike_failed = (
            ~traversal_complete | self.crossing_contract_violated)
        missed_both = no_success & fret_failed & strike_failed
        missed_fret = no_success & fret_failed & ~strike_failed
        missed_strike = no_success & ~fret_failed
        resolved_pulse = finish | self._resolution_pending
        self.outcome[full] = int(EventOutcome.FULL)
        self.outcome[partial] = int(EventOutcome.PARTIAL)
        self.outcome[missed_both] = int(EventOutcome.MISSED_BOTH)
        self.outcome[missed_fret] = int(EventOutcome.MISSED_FRET)
        self.outcome[missed_strike] = int(EventOutcome.MISSED_STRIKE)
        self.resolved[finish] = True
        self.permission_open[finish] = False
        self._resolution_pending.zero_()

        self._before_step_pending.zero_()
        return SynchronizerResult(
            event_id=self.event_id.clone(),
            resolved_pulse=resolved_pulse,
            resolved=self.resolved.clone(),
            outcome=self.outcome.clone(),
            accepted_crossing_mask=accepted,
            ordered_crossing_mask=ordered,
            planned_crossing_mask=planned,
            protected_crossing_mask=protected,
            failed_target_crossing_mask=failed_target,
            blocked_crossing_mask=blocked,
            unplanned_crossing_mask=unplanned,
            wrong_direction_crossing_mask=wrong_direction,
            order_violation_crossing_mask=order_violation,
            crossing_contract_violated=(
                self.crossing_contract_violated.clone()),
            accumulated_crossing_mask=self.accumulated_crossing_mask.clone(),
            target_success_mask=self.target_success_mask.clone(),
            traversal_complete=traversal_complete,
            delay_frames=self.selected_delay_frames.clone(),
            delay_cause=self._delay_cause(),
        )

    def state_dict(self):
        """Return the small non-learned runtime state for exact resume."""
        names = (
            "event_id", "target_frets", "audible_mask", "traversal_mask",
            "traversal_order", "traversal_offsets_s", "strike_direction",
            "release_boundary_frame", "traversal_end_frame",
            "delay_budget_frames", "ready_streak", "permission_open",
            "scorable_target_mask", "completion_deadline_frame",
            "accumulated_crossing_mask", "target_success_mask",
            "failed_target_crossing_mask", "crossing_contract_violated",
            "resolved",
            "_resolution_pending",
            "outcome", "selected_delay_frames",
            "fret_blocked_during_window", "strike_blocked_during_window",
            "stability_blocked_during_window", "strike_entry_hold_latched",
            "_last_score_frame",
            "_clock_initialized", "_before_step_pending",
        )
        return {
            "schema": SYNCHRONIZER_SCHEMA,
            "fps": self.fps,
            "configured_max_delay_frames": self.configured_max_delay_frames,
            "readiness_dwell_frames": self.readiness_dwell_frames,
            "tensors": {name: getattr(self, name).clone() for name in names},
        }

    def load_state_dict(self, state, *, max_event_count=None):
        expected_keys = {
            "schema", "fps", "configured_max_delay_frames",
            "readiness_dwell_frames", "tensors",
        }
        if (not isinstance(state, dict)
                or set(state) != expected_keys
                or state.get("schema") != SYNCHRONIZER_SCHEMA):
            raise ValueError("invalid Synchronizer state schema")
        expected = (
            self.fps, self.configured_max_delay_frames,
            self.readiness_dwell_frames)
        actual = (
            state.get("fps"), state.get("configured_max_delay_frames"),
            state.get("readiness_dwell_frames"))
        if actual != expected:
            raise ValueError("Synchronizer state configuration mismatch")
        tensors = state.get("tensors")
        current = self.state_dict()["tensors"]
        if not isinstance(tensors, dict) or set(tensors) != set(current):
            raise ValueError("Synchronizer state tensor set mismatch")
        validated = {}
        for name, reference in current.items():
            value = torch.as_tensor(tensors[name], device=self.device)
            if value.shape != reference.shape or value.dtype != reference.dtype:
                raise ValueError(f"Synchronizer state tensor mismatch: {name}")
            if value.is_floating_point() and not torch.isfinite(value).all():
                raise ValueError(
                    f"Synchronizer state tensor is non-finite: {name}")
            validated[name] = value.clone()

        event_id = validated["event_id"]
        active = event_id >= 0
        if bool((event_id < -1).any().item()):
            raise ValueError("Synchronizer event_id is invalid")
        if max_event_count is not None:
            count = int(max_event_count)
            if count < 1 or bool((active & (event_id >= count)).any().item()):
                raise ValueError("Synchronizer event_id is outside the timeline")
        targets = validated["target_frets"]
        audible = validated["audible_mask"]
        traversal = validated["traversal_mask"]
        order = validated["traversal_order"]
        offsets = validated["traversal_offsets_s"]
        direction = validated["strike_direction"]
        if bool((active & ~audible.any(dim=1)).any().item()) or bool(
                (active & ~traversal.any(dim=1)).any().item()):
            raise ValueError("active Synchronizer event lacks a traversal target")
        if bool((audible & ~traversal).any().item()):
            raise ValueError("Synchronizer audible mask is outside traversal")
        if bool(((targets < 0) & audible).any().item()) or bool(
                ((targets >= 0) & ~audible).any().item()):
            raise ValueError("Synchronizer target frets disagree with audible mask")
        if bool((active & ((direction != -1) & (direction != 1))).any().item(
                )) or bool((~active & (direction != 0)).any().item()):
            raise ValueError("Synchronizer strike direction is invalid")
        traversal_count = traversal.sum(dim=1)
        slots = torch.arange(
            N_GUITAR_STRINGS, dtype=torch.long, device=self.device)[None]
        active_order_slot = slots < traversal_count[:, None]
        if bool(((order >= 0) != active_order_slot).any().item()):
            raise ValueError("Synchronizer traversal order padding is invalid")
        ordered_count = torch.zeros_like(traversal, dtype=torch.long)
        ordered_count.scatter_add_(
            1, order.clamp_min(0), active_order_slot.to(torch.long))
        if bool((ordered_count != traversal.to(torch.long)).any().item()):
            raise ValueError("Synchronizer traversal order is not a partition")
        adjacent = slots[:, 1:] < traversal_count[:, None]
        delta = order[:, 1:] - order[:, :-1]
        bad_direction_order = adjacent & torch.where(
            (direction == 1)[:, None], delta >= 0, delta <= 0)
        if bool(bad_direction_order.any().item()):
            raise ValueError("Synchronizer order disagrees with strike direction")
        if bool((adjacent & ((offsets[:, 1:] - offsets[:, :-1]) <= 0)).any(
                ).item()) or bool(
                ((~active_order_slot) & (offsets != 0)).any().item()):
            raise ValueError("Synchronizer traversal offsets are invalid")
        budget = validated["delay_budget_frames"]
        selected = validated["selected_delay_frames"]
        if bool(((budget < 0) | (budget > self.configured_max_delay_frames)).any(
                ).item()) or bool(((selected < 0) | (selected > budget)).any(
                ).item()):
            raise ValueError("Synchronizer delay state is outside its bounds")
        if bool((validated["ready_streak"] < 0).any().item()):
            raise ValueError("Synchronizer readiness streak is negative")
        resolved = validated["resolved"]
        permission = validated["permission_open"]
        if bool((permission & (~active | resolved)).any().item()):
            raise ValueError("Synchronizer permission/resolution state conflicts")
        if bool((~active & ~resolved).any().item()) or bool(
                (~active & validated["_clock_initialized"]).any().item()):
            raise ValueError("inactive Synchronizer row is not reset")
        if bool((active & ~validated["_clock_initialized"]).any().item()):
            raise ValueError("active Synchronizer row lacks an initialized clock")
        if bool((validated["_resolution_pending"] & ~resolved).any().item()):
            raise ValueError("Synchronizer resolution pulse state is invalid")
        if bool((validated["_before_step_pending"] & resolved).any().item()):
            raise ValueError("resolved Synchronizer event still owns a step")
        if bool((validated["scorable_target_mask"] & ~audible).any().item()):
            raise ValueError("Synchronizer scorable mask is not audible")
        accumulated = validated["accumulated_crossing_mask"]
        if bool((accumulated & ~traversal).any().item()):
            raise ValueError("Synchronizer accumulated an unplanned crossing")
        success = validated["target_success_mask"]
        failed = validated["failed_target_crossing_mask"]
        if bool((success & ~(accumulated & audible)).any().item()) or bool(
                (failed & ~(accumulated & audible)).any().item()):
            raise ValueError("Synchronizer target outcome masks are inconsistent")
        if bool((validated["traversal_end_frame"]
                 < validated["release_boundary_frame"]).any().item()):
            raise ValueError("Synchronizer traversal ends before release")
        outcome = validated["outcome"]
        if bool(((outcome < int(EventOutcome.ACTIVE))
                 | (outcome > int(EventOutcome.MISSED_STABILITY))).any().item()):
            raise ValueError("Synchronizer event outcome is invalid")
        if bool((active & ~resolved & (outcome != int(EventOutcome.ACTIVE))).any(
                ).item()) or bool(
                (active & resolved & (outcome == int(EventOutcome.ACTIVE))).any(
                ).item()):
            raise ValueError("Synchronizer event outcome conflicts with resolution")

        for name, value in validated.items():
            getattr(self, name).copy_(value)


__all__ = [
    "DeadlineAction",
    "DelayCause",
    "EventOutcome",
    "N_GUITAR_STRINGS",
    "RuleBasedSynchronizer",
    "SYNCHRONIZER_SCHEMA",
    "SynchronizerDecision",
    "SynchronizerResult",
]
