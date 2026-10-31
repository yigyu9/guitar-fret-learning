"""Single score clock and event cursor for the fixed-guitar G0 runtime."""
from __future__ import annotations

from dataclasses import dataclass

import torch

from .events import CanonicalEventTimeline


SCORE_CLOCK_SCHEMA = "tab2body.canonical_score_clock.v1"
N_GUITAR_STRINGS = 6
STRIKE_DIRECTION_UP = -1
STRIKE_DIRECTION_DOWN = 1


@dataclass(frozen=True)
class CanonicalEventBatch:
    """Tensor projection of each environment's current canonical event."""

    event_index: torch.Tensor
    score_frame: torch.Tensor
    score_time_s: torch.Tensor
    event_center_frame: torch.Tensor
    release_boundary_frame: torch.Tensor
    traversal_end_frame: torch.Tensor
    delay_budget_frames: torch.Tensor
    target_frets: torch.Tensor
    audible_mask: torch.Tensor
    traversal_mask: torch.Tensor
    traversal_order: torch.Tensor
    traversal_offsets_s: torch.Tensor
    strike_direction: torch.Tensor


class CanonicalScoreClock:
    """Own the only mutable song cursor used by both frozen source skills.

    The score frame advances once after every physical control step and never
    pauses for a late hand.  The event cursor advances only after the
    Synchronizer emits an exactly-once resolution pulse.  Negative frames form
    a common pre-roll; they do not alter any authored event time.
    """

    def __init__(self, timeline: CanonicalEventTimeline, *, num_envs: int,
                 device="cpu", preroll_frames: int = 60):
        if not isinstance(timeline, CanonicalEventTimeline):
            raise TypeError("timeline must be a CanonicalEventTimeline")
        if not timeline.events:
            raise ValueError("canonical timeline must contain an event")
        if any(not event.supported for event in timeline.events):
            raise ValueError(
                "unsupported canonical events cannot enter a G0 runtime")
        self.timeline = timeline
        self.num_envs = int(num_envs)
        self.device = torch.device(device)
        self.preroll_frames = int(preroll_frames)
        if self.num_envs < 1:
            raise ValueError("num_envs must be positive")
        if self.preroll_frames < 0:
            raise ValueError("preroll_frames must be non-negative")
        self.event_index = torch.zeros(
            self.num_envs, dtype=torch.long, device=self.device)
        self.score_frame = torch.full(
            (self.num_envs,), -self.preroll_frames,
            dtype=torch.long, device=self.device)
        self.finished = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)

    def reset(self, env_ids=None):
        if env_ids is None:
            ids = torch.arange(
                self.num_envs, dtype=torch.long, device=self.device)
        else:
            ids = torch.as_tensor(
                env_ids, dtype=torch.long, device=self.device).reshape(-1)
            if ids.numel() and (
                    (ids < 0).any() or (ids >= self.num_envs).any()):
                raise IndexError("score-clock env_ids are outside the batch")
        self.event_index[ids] = 0
        self.score_frame[ids] = -self.preroll_frames
        self.finished[ids] = False

    def current(self) -> CanonicalEventBatch:
        if bool(self.finished.any().item()):
            rows = torch.nonzero(self.finished).flatten().tolist()
            raise RuntimeError(
                "reset finished G0 environments before requesting events: "
                f"{rows}")
        events = self.timeline.events
        indices = self.event_index.detach().cpu().tolist()
        target_frets = torch.full(
            (self.num_envs, N_GUITAR_STRINGS), -1,
            dtype=torch.long, device=self.device)
        audible = torch.zeros(
            self.num_envs, N_GUITAR_STRINGS,
            dtype=torch.bool, device=self.device)
        traversal = torch.zeros_like(audible)
        traversal_order = torch.full(
            (self.num_envs, N_GUITAR_STRINGS), -1,
            dtype=torch.long, device=self.device)
        traversal_offsets_s = torch.zeros(
            self.num_envs, N_GUITAR_STRINGS,
            dtype=torch.float32, device=self.device)
        strike_direction = torch.empty(
            self.num_envs, dtype=torch.int8, device=self.device)
        centers = torch.empty(
            self.num_envs, dtype=torch.long, device=self.device)
        boundaries = torch.empty_like(centers)
        traversal_ends = torch.empty_like(centers)
        budgets = torch.empty_like(centers)
        for row, index in enumerate(indices):
            event = events[index]
            centers[row] = event.score_frame
            boundaries[row] = event.release_boundary_frame
            traversal_ends[row] = event.traversal_end_frame
            budgets[row] = event.effective_delay_cap_frames
            for target in event.string_targets:
                target_frets[row, target.string] = target.fret
                audible[row, target.string] = True
            ordered_strings = event.strike.traversal_strings
            traversal[row, list(ordered_strings)] = True
            traversal_order[row, :len(ordered_strings)] = torch.tensor(
                ordered_strings, dtype=torch.long, device=self.device)
            traversal_offsets_s[row, :len(ordered_strings)] = torch.tensor(
                event.strike.traversal_offsets_s,
                dtype=torch.float32, device=self.device)
            strike_direction[row] = (
                STRIKE_DIRECTION_DOWN
                if event.strike.direction == "down"
                else STRIKE_DIRECTION_UP)
        return CanonicalEventBatch(
            event_index=self.event_index.clone(),
            score_frame=self.score_frame.clone(),
            score_time_s=(
                self.score_frame.to(torch.float32) / float(self.timeline.fps)),
            event_center_frame=centers,
            release_boundary_frame=boundaries,
            traversal_end_frame=traversal_ends,
            delay_budget_frames=budgets,
            target_frets=target_frets,
            audible_mask=audible,
            traversal_mask=traversal,
            traversal_order=traversal_order,
            traversal_offsets_s=traversal_offsets_s,
            strike_direction=strike_direction,
        )

    def consume_resolution(self, event_index, resolved_pulse):
        supplied = torch.as_tensor(
            event_index, dtype=torch.long, device=self.device)
        pulse = torch.as_tensor(
            resolved_pulse, dtype=torch.bool, device=self.device)
        expected = (self.num_envs,)
        if supplied.shape != expected or pulse.shape != expected:
            raise ValueError("score-clock resolution tensors must have shape [N]")
        if bool((supplied != self.event_index).any().item()):
            raise RuntimeError("Synchronizer resolved a non-current event")
        if bool((pulse & self.finished).any().item()):
            raise RuntimeError("finished event was resolved more than once")
        rows = torch.nonzero(pulse).flatten()
        if rows.numel():
            next_index = self.event_index[rows] + 1
            now_finished = next_index >= len(self.timeline.events)
            continuing = rows[~now_finished]
            self.event_index[continuing] = next_index[~now_finished]
            self.finished[rows[now_finished]] = True

    def advance_physics(self):
        """Advance the immutable score by exactly one 60 Hz control step."""
        self.score_frame += 1

    def state_dict(self):
        return {
            "schema": SCORE_CLOCK_SCHEMA,
            "timeline_sha256": self.timeline.content_sha256,
            "fps": self.timeline.fps,
            "preroll_frames": self.preroll_frames,
            "event_index": self.event_index.clone(),
            "score_frame": self.score_frame.clone(),
            "finished": self.finished.clone(),
        }

    def load_state_dict(self, state):
        expected_keys = {
            "schema", "timeline_sha256", "fps", "preroll_frames",
            "event_index", "score_frame", "finished",
        }
        if (not isinstance(state, dict)
                or set(state) != expected_keys
                or state.get("schema") != SCORE_CLOCK_SCHEMA):
            raise ValueError("invalid score-clock state schema")
        expected = (
            self.timeline.content_sha256, self.timeline.fps,
            self.preroll_frames)
        actual = (
            state.get("timeline_sha256"), state.get("fps"),
            state.get("preroll_frames"))
        if actual != expected:
            raise ValueError("score-clock state contract mismatch")
        validated = {}
        for name, reference in (
                ("event_index", self.event_index),
                ("score_frame", self.score_frame),
                ("finished", self.finished)):
            value = torch.as_tensor(state.get(name), device=self.device)
            if value.shape != reference.shape or value.dtype != reference.dtype:
                raise ValueError(f"score-clock state tensor mismatch: {name}")
            validated[name] = value.clone()
        event_index = validated["event_index"]
        score_frame = validated["score_frame"]
        finished = validated["finished"]
        if bool((event_index < 0).any().item()) or bool(
                (event_index >= len(self.timeline.events)).any().item()):
            raise ValueError("score-clock event index is outside the timeline")
        if bool((score_frame < -self.preroll_frames).any().item()):
            raise ValueError("score-clock frame precedes the configured pre-roll")
        if bool((finished & (event_index != len(self.timeline.events) - 1)).any(
                ).item()):
            raise ValueError("only the final event may mark a score clock finished")
        self.event_index.copy_(event_index)
        self.score_frame.copy_(score_frame)
        self.finished.copy_(finished)


__all__ = [
    "CanonicalEventBatch",
    "CanonicalScoreClock",
    "SCORE_CLOCK_SCHEMA",
    "STRIKE_DIRECTION_DOWN",
    "STRIKE_DIRECTION_UP",
]
