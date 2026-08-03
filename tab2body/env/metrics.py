"""Episode-level diagnostics that do not shape the policy reward."""
from __future__ import annotations

import torch


def update_live_dropout_streak(previous, dropout, enabled):
    if previous.shape != dropout.shape or enabled.shape != previous.shape[:1]:
        raise ValueError(
            "dropout streak tensors must have shapes [N,S], [N,S], [N]")
    live_dropout = dropout.bool() & enabled.bool()[:, None]
    return torch.where(
        live_dropout, previous + 1, torch.zeros_like(previous))


class PressSustainTracker:
    """R27 per-event PRESS hold ratio and dropout tracker."""

    def __init__(self, num_envs, num_events, device, hold_threshold=0.90,
                 max_dropout_frames=3):
        self.num_envs = int(num_envs)
        self.num_events = int(num_events)
        self.device = torch.device(device)
        self.hold_threshold = float(hold_threshold)
        self.max_dropout_frames = int(max_dropout_frames)
        if not 0.0 <= self.hold_threshold <= 1.0:
            raise ValueError("sustain hold threshold must be in [0, 1]")
        if self.max_dropout_frames < 0:
            raise ValueError("sustain max dropout frames must be non-negative")
        shape = (self.num_envs, self.num_events)
        self.eligible = torch.zeros(shape, dtype=torch.long, device=self.device)
        self.correct = torch.zeros_like(self.eligible)
        self.current_correct = torch.zeros_like(self.eligible)
        self.longest_correct = torch.zeros_like(self.eligible)
        self.current_dropout = torch.zeros_like(self.eligible)
        self.longest_dropout = torch.zeros_like(self.eligible)
        self.interruptions = torch.zeros_like(self.eligible)
        self.ever_correct = torch.zeros(shape, dtype=torch.bool, device=self.device)

    def reset(self, env_ids):
        if env_ids.numel() == 0 or self.num_events == 0:
            return
        for value in (self.eligible, self.correct, self.current_correct,
                      self.longest_correct, self.current_dropout,
                      self.longest_dropout, self.interruptions, self.ever_correct):
            value[env_ids] = 0

    def update(self, event_id, eligible, press_success):
        if self.num_events == 0:
            return
        valid = eligible & (event_id >= 0)
        env_idx, string_idx = torch.nonzero(valid, as_tuple=True)
        if env_idx.numel() == 0:
            return
        event_idx = event_id[env_idx, string_idx]
        success = press_success[env_idx, string_idx].bool()

        old_correct = self.current_correct[env_idx, event_idx]
        old_dropout = self.current_dropout[env_idx, event_idx]
        seen_correct = self.ever_correct[env_idx, event_idx]
        new_correct = torch.where(success, old_correct + 1, torch.zeros_like(old_correct))
        new_dropout = torch.where(
            success | ~seen_correct,
            torch.zeros_like(old_dropout),
            old_dropout + 1)

        self.eligible[env_idx, event_idx] += 1
        self.correct[env_idx, event_idx] += success.long()
        self.current_correct[env_idx, event_idx] = new_correct
        self.longest_correct[env_idx, event_idx] = torch.maximum(
            self.longest_correct[env_idx, event_idx], new_correct)
        self.current_dropout[env_idx, event_idx] = new_dropout
        self.longest_dropout[env_idx, event_idx] = torch.maximum(
            self.longest_dropout[env_idx, event_idx], new_dropout)
        self.interruptions[env_idx, event_idx] += (
            (~success) & seen_correct & (old_dropout == 0)).long()
        self.ever_correct[env_idx, event_idx] |= success

    def episode_metrics(self, done):
        env_ids = torch.nonzero(done).squeeze(-1)
        if env_ids.numel() == 0:
            empty = torch.empty(0, device=self.device)
            return {
                "sustain_hold_rate": empty,
                "sustain_event_success_rate": empty,
                "sustain_min_event_hold_rate": empty,
                "sustain_max_dropout_frames": empty,
                "sustain_interruption_count": empty,
                "sustain_event_count": empty,
            }
        if self.num_events == 0:
            count = torch.zeros(env_ids.numel(), device=self.device)
            one = torch.ones_like(count)
            return {
                "sustain_hold_rate": one,
                "sustain_event_success_rate": one,
                "sustain_min_event_hold_rate": one,
                "sustain_max_dropout_frames": count,
                "sustain_interruption_count": count,
                "sustain_event_count": count,
            }
        eligible = self.eligible[env_ids]
        correct = self.correct[env_ids]
        valid = eligible > 0
        ratios = correct.float() / eligible.clamp_min(1).float()
        valid_count = valid.sum(dim=1)
        total_hold = correct.sum(dim=1).float() / eligible.sum(dim=1).clamp_min(1).float()
        event_success = (valid
                         & (ratios >= self.hold_threshold)
                         & (self.longest_dropout[env_ids] <= self.max_dropout_frames))
        min_ratio = ratios.masked_fill(~valid, 1.0).amin(dim=1)
        max_dropout = self.longest_dropout[env_ids].masked_fill(~valid, 0).amax(dim=1)
        interruptions = self.interruptions[env_ids].masked_fill(~valid, 0).sum(dim=1)
        return {
            "sustain_hold_rate": total_hold,
            "sustain_event_success_rate": (event_success.sum(dim=1).float()
                                           / valid_count.clamp_min(1).float()),
            "sustain_min_event_hold_rate": min_ratio,
            "sustain_max_dropout_frames": max_dropout.float(),
            "sustain_interruption_count": interruptions.float(),
            "sustain_event_count": valid_count.float(),
        }


class PressedDragMonitor:
    """R28 diagnostic-only pressed travel during a MOVE transition.

    ``pressed_cells`` is N x finger x string x fret.  Confirmed distance requires
    at least one identical pressed cell at both control-frame endpoints.  This is
    deliberately conservative: endpoint contact alone is retained as a candidate
    channel but never labelled confirmed dragging.
    """

    def __init__(self, num_envs, device, num_fingers=4, threshold=0.003):
        self.num_envs = int(num_envs)
        self.num_fingers = int(num_fingers)
        self.device = torch.device(device)
        self.threshold = float(threshold)
        if self.threshold < 0.0:
            raise ValueError("pressed-drag threshold must be non-negative")
        shape = (self.num_envs, self.num_fingers)
        self.move_active = torch.zeros(shape, dtype=torch.bool, device=self.device)
        self.cumulative = torch.zeros(shape, device=self.device)
        self.candidate_cumulative = torch.zeros_like(self.cumulative)
        self.drag_frames = torch.zeros(shape, dtype=torch.long, device=self.device)
        self.reported = torch.zeros(shape, dtype=torch.bool, device=self.device)
        self.previous_mask = torch.zeros(
            self.num_envs, self.num_fingers, 6, dtype=torch.bool, device=self.device)
        self.previous_fret = torch.zeros(shape, dtype=torch.long, device=self.device)
        self.previous_relation_move = torch.zeros(
            shape, dtype=torch.bool, device=self.device)
        self.previous_tip_xy = torch.zeros(
            self.num_envs, self.num_fingers, 2, device=self.device)
        self.previous_pressed_cells = torch.zeros(
            self.num_envs, self.num_fingers, 6, 22,
            dtype=torch.bool, device=self.device)
        self.have_previous = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)

    def reset(self, env_ids):
        if env_ids.numel() == 0:
            return
        for value in (self.move_active, self.cumulative,
                      self.candidate_cumulative, self.drag_frames,
                      self.reported, self.previous_mask,
                      self.previous_fret, self.previous_relation_move,
                      self.previous_tip_xy, self.previous_pressed_cells,
                      self.have_previous):
            value[env_ids] = 0

    def update(self, target_mask, target_fret, relation_move, stable_press,
               tip_xy, pressed_cells):
        target_mask = target_mask.bool()
        target_fret = target_fret.long()
        relation_move = relation_move.bool()
        stable_press = stable_press.bool()
        pressed_cells = pressed_cells.bool()
        previous_active = self.previous_fret > 0
        target_changed = ((target_fret != self.previous_fret)
                          | (target_mask != self.previous_mask).any(dim=-1))
        started = (self.have_previous[:, None] & previous_active & target_changed
                   & self.previous_relation_move)
        self.move_active |= started
        self.cumulative = torch.where(started, torch.zeros_like(self.cumulative),
                                      self.cumulative)
        self.candidate_cumulative = torch.where(
            started, torch.zeros_like(self.candidate_cumulative),
            self.candidate_cumulative)
        self.drag_frames = torch.where(
            started, torch.zeros_like(self.drag_frames), self.drag_frames)
        self.reported &= ~started

        step_distance = (tip_xy - self.previous_tip_xy).norm(dim=-1)
        previous_any = self.previous_pressed_cells.flatten(2).any(dim=-1)
        current_any = pressed_cells.flatten(2).any(dim=-1)
        endpoint_candidate = (self.move_active & self.have_previous[:, None]
                              & previous_any & current_any)
        same_cell = (self.previous_pressed_cells & pressed_cells).flatten(2).any(dim=-1)
        confirmed = endpoint_candidate & same_cell
        candidate_step = torch.where(endpoint_candidate, step_distance,
                                     torch.zeros_like(step_distance))
        confirmed_step = torch.where(confirmed, step_distance,
                                     torch.zeros_like(step_distance))
        self.candidate_cumulative += candidate_step
        self.cumulative += confirmed_step
        self.drag_frames += confirmed.long()
        violation_started = ((self.cumulative > self.threshold) & ~self.reported)
        self.reported |= violation_started

        # Arrival ends the MOVE after this frame's conservative drag sample.
        completed = self.move_active & stable_press & (target_fret > 0)
        result = {
            "r28_move_active": self.move_active.clone(),
            "r28_move_started": started,
            "r28_move_completed": completed,
            "r28_pressed_endpoint_candidate": endpoint_candidate,
            "r28_same_cell_drag": confirmed,
            "r28_candidate_step_distance": candidate_step,
            "r28_confirmed_step_distance": confirmed_step,
            "r28_candidate_cumulative_distance": self.candidate_cumulative.clone(),
            "r28_confirmed_cumulative_distance": self.cumulative.clone(),
            "r28_confirmed_drag_frames": self.drag_frames.clone(),
            "r28_drag_violation_started": violation_started,
        }
        self.move_active &= ~completed
        self.previous_mask.copy_(target_mask)
        self.previous_fret.copy_(target_fret)
        self.previous_relation_move.copy_(relation_move)
        self.previous_tip_xy.copy_(tip_xy)
        self.previous_pressed_cells.copy_(pressed_cells)
        self.have_previous.fill_(True)
        return result
