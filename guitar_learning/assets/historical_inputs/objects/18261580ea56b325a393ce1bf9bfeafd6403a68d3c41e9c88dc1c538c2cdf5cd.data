"""Episode-level diagnostics that do not shape the policy reward."""
from __future__ import annotations

import math

import torch


def event_failure_window_scores(event_scores, window_size):
    if event_scores.ndim != 1 or event_scores.numel() < 1:
        raise ValueError("event failure scores must have shape [events]")
    if (isinstance(window_size, bool) or not isinstance(window_size, int)
            or not 1 <= window_size <= event_scores.numel()):
        raise ValueError("failure-mining window size is out of range")
    if event_scores.device.type == "cpu" and (
            not torch.isfinite(event_scores).all()
            or bool((event_scores < 0.0).any())):
        raise ValueError("event failure scores must be finite and non-negative")
    return event_scores.unfold(0, window_size, 1).sum(dim=1)


def event_predecessor_rehearsal_scores(event_scores, window_size):
    """Assign each failed event to a short window containing its predecessor."""
    if event_scores.ndim != 1 or event_scores.numel() < 1:
        raise ValueError("event failure scores must have shape [events]")
    if (isinstance(window_size, bool) or not isinstance(window_size, int)
            or not 1 <= window_size <= event_scores.numel()):
        raise ValueError("failure-rehearsal window size is out of range")
    if event_scores.device.type == "cpu" and (
            not torch.isfinite(event_scores).all()
            or bool((event_scores < 0.0).any())):
        raise ValueError("event failure scores must be finite and non-negative")
    num_windows = event_scores.numel() - window_size + 1
    event_index = torch.arange(
        event_scores.numel(), device=event_scores.device)
    starts = (event_index - 1).clamp(0, num_windows - 1)
    scores = torch.zeros(
        num_windows, dtype=event_scores.dtype, device=event_scores.device)
    scores.scatter_add_(0, starts, event_scores)
    return scores


def event_mask_window_scores(event_mask, window_size):
    """Count selected event attributes in every contiguous training window."""
    if event_mask.ndim != 1 or event_mask.numel() < 1:
        raise ValueError("event mask must have shape [events]")
    if event_mask.dtype != torch.bool:
        raise TypeError("event mask must use torch.bool")
    if (isinstance(window_size, bool) or not isinstance(window_size, int)
            or not 1 <= window_size <= event_mask.numel()):
        raise ValueError("event-mask window size is out of range")
    return event_mask.to(dtype=torch.float32).unfold(
        0, window_size, 1).sum(dim=1)


def update_event_failure_statistics(
        failure_mass, exposure_mass, event_index, exposed, failed, *,
        decay, prior_exposure=0.0):
    if failure_mass.ndim != 1 or exposure_mass.shape != failure_mass.shape:
        raise ValueError("event failure/exposure statistics must have shape [events]")
    vectors = (event_index, exposed, failed)
    if any(value.ndim != 1 for value in vectors):
        raise ValueError("event failure updates must have shape [N]")
    if any(value.shape != event_index.shape for value in vectors[1:]):
        raise ValueError("event failure updates must share shape [N]")
    if exposed.dtype != torch.bool or failed.dtype != torch.bool:
        raise TypeError("event exposure/failure masks must use torch.bool")
    decay = float(decay)
    prior_exposure = float(prior_exposure)
    if (not math.isfinite(decay) or not 0.0 < decay <= 1.0
            or not math.isfinite(prior_exposure) or prior_exposure < 0.0):
        raise ValueError("event failure decay/prior must be finite and valid")
    if failure_mass.device.type == "cpu" and (
            not torch.isfinite(failure_mass).all()
            or not torch.isfinite(exposure_mass).all()
            or bool((failure_mass < 0.0).any())
            or bool((exposure_mass < 0.0).any())
            or bool((failure_mass > exposure_mass + 1e-6).any())):
        raise ValueError("event failure statistics are invalid")
    next_failure = failure_mass * decay
    next_exposure = exposure_mass * decay
    valid = exposed & (event_index >= 0) & (event_index < failure_mass.numel())
    if bool(valid.any()):
        selected = event_index[valid].to(dtype=torch.long)
        exposure_count = torch.bincount(
            selected, minlength=failure_mass.numel()).to(failure_mass.dtype)
        failure_count = torch.bincount(
            selected,
            weights=failed[valid].to(failure_mass.dtype),
            minlength=failure_mass.numel()).to(failure_mass.dtype)
        next_failure = next_failure + failure_count
        next_exposure = next_exposure + exposure_count
    total_exposure = next_exposure.sum()
    global_rate = next_failure.sum() / total_exposure.clamp_min(1.0)
    score = (
        (next_failure + prior_exposure * global_rate)
        / (next_exposure + prior_exposure).clamp_min(1e-8))
    score = torch.where(
        next_exposure > 0.0, score.clamp(0.0, 1.0),
        torch.zeros_like(score))
    return {
        "failure_mass": next_failure,
        "exposure_mass": next_exposure,
        "score": score,
    }


def bounded_failure_sampling_probabilities(scores, max_probability):
    if scores.ndim != 1 or scores.numel() < 1:
        raise ValueError("failure sampling scores must have shape [windows]")
    max_probability = float(max_probability)
    uniform_probability = 1.0 / scores.numel()
    if (not math.isfinite(max_probability)
            or not uniform_probability <= max_probability <= 1.0):
        raise ValueError(
            "failure sampling probability cap must be in [1/windows, 1]")
    if scores.device.type == "cpu" and (
            not torch.isfinite(scores).all()
            or bool((scores < 0.0).any())):
        raise ValueError("failure sampling scores must be finite and non-negative")
    total = scores.sum()
    if not bool(total > 0.0):
        return torch.zeros_like(scores)
    weighted = scores / total
    peak = weighted.max()
    if bool(peak <= max_probability):
        return weighted
    uniform = torch.full_like(weighted, uniform_probability)
    denominator = (peak - uniform_probability).clamp_min(1e-8)
    mixture = max(
        0.0, min(1.0,
                 (max_probability - uniform_probability)
                 / float(denominator)))
    probabilities = mixture * weighted + (1.0 - mixture) * uniform
    return probabilities / probabilities.sum().clamp_min(1e-8)


def normalized_joint_limit_usage(position, lower, upper):
    """관절 중앙은 0, hard limit은 1이 되는 사용률을 반환한다."""
    if lower.shape != upper.shape or position.shape[-lower.ndim:] != lower.shape:
        raise ValueError("joint limits must match the trailing position shape")
    half = 0.5 * (upper - lower)
    if half.device.type == "cpu" and (
            not torch.isfinite(half).all() or (half <= 0.0).any()):
        raise ValueError("joint limits must be finite and increasing")
    center = 0.5 * (lower + upper)
    return ((position - center) / half.clamp_min(1e-8)).abs()


def update_wrong_press_termination(
        previous, wrong_press, enabled, *, stage, frames, stages):
    """후기 단계에서만 지속 오압현 streak과 종료 여부를 계산한다."""
    if (previous.ndim != 1 or wrong_press.shape != previous.shape
            or enabled.shape != previous.shape):
        raise ValueError("wrong-press termination tensors must share shape [N]")
    if isinstance(frames, bool) or int(frames) < 0:
        raise ValueError("wrong-press termination frames must be non-negative")
    frames = int(frames)
    active = bool(stage in tuple(stages)) and frames > 0
    violation = wrong_press.bool() & enabled.bool() if active else torch.zeros_like(
        wrong_press, dtype=torch.bool)
    streak = torch.where(
        violation, previous + 1, torch.zeros_like(previous))
    termination = (
        streak >= frames if active
        else torch.zeros_like(streak, dtype=torch.bool))
    return streak, termination


def update_wrong_crossing_termination(
        total_wrong, consecutive_wrong_events, event_had_wrong,
        wrong_count, event_resolved, resolved_events, enabled, *,
        minimum_resolved_events, max_count, max_rate,
        consecutive_event_limit, terminate_on_rate=True):
    vectors = (
        total_wrong, consecutive_wrong_events, event_had_wrong,
        wrong_count, event_resolved, resolved_events, enabled)
    if any(value.ndim != 1 for value in vectors):
        raise ValueError("wrong-crossing termination inputs must have shape [N]")
    if any(value.shape != total_wrong.shape for value in vectors[1:]):
        raise ValueError("wrong-crossing termination inputs must share shape [N]")
    if event_had_wrong.dtype != torch.bool or event_resolved.dtype != torch.bool \
            or enabled.dtype != torch.bool:
        raise TypeError("wrong-crossing masks must use torch.bool")
    if minimum_resolved_events < 0 or max_count < 1 \
            or consecutive_event_limit < 1:
        raise ValueError("wrong-crossing termination counts are invalid")
    if not isinstance(terminate_on_rate, bool):
        raise TypeError("terminate_on_rate must be bool")
    max_rate = float(max_rate)
    if not math.isfinite(max_rate) or not 0.0 <= max_rate <= 1.0:
        raise ValueError("wrong-crossing max_rate must be in [0, 1]")
    next_total = total_wrong + wrong_count
    current_had_wrong = event_had_wrong | (wrong_count > 0)
    next_resolved = resolved_events + event_resolved.to(resolved_events.dtype)
    next_consecutive = torch.where(
        event_resolved,
        torch.where(
            current_had_wrong,
            consecutive_wrong_events + 1,
            torch.zeros_like(consecutive_wrong_events)),
        consecutive_wrong_events)
    next_event_had_wrong = current_had_wrong & ~event_resolved
    rate = next_total / next_resolved.clamp_min(1).to(next_total.dtype)
    count_termination = enabled & (next_total >= max_count)
    consecutive_termination = enabled & (
        next_consecutive >= consecutive_event_limit)
    rate_limit_exceeded = (
        enabled
        & event_resolved
        & (next_resolved >= minimum_resolved_events)
        & (rate > max_rate))
    rate_termination = rate_limit_exceeded & terminate_on_rate
    termination = (
        count_termination | consecutive_termination | rate_termination)
    return {
        "total_wrong": next_total,
        "resolved_events": next_resolved,
        "consecutive_wrong_events": next_consecutive,
        "event_had_wrong": next_event_had_wrong,
        "wrong_rate": rate,
        "rate_limit_exceeded": rate_limit_exceeded,
        "count_termination": count_termination,
        "rate_termination": rate_termination,
        "consecutive_termination": consecutive_termination,
        "termination": termination,
    }


def summarize_joint_trajectory(position, lower, upper, names):
    """관절 trajectory의 각도 분위수와 hard-limit 사용률을 요약한다."""
    if position.ndim != 2 or lower.shape != position.shape[1:] \
            or upper.shape != position.shape[1:]:
        raise ValueError("joint trajectory must have shapes [T,D], [D], [D]")
    if len(names) != position.shape[1] or position.shape[0] == 0:
        raise ValueError("joint names and non-empty trajectory are required")
    usage = normalized_joint_limit_usage(position, lower, upper)
    quantiles = torch.quantile(
        position.float(),
        torch.tensor([0.05, 0.50, 0.95], device=position.device), dim=0)
    scale = 180.0 / math.pi
    return {
        str(name): {
            "min_deg": float(position[:, index].min()) * scale,
            "p05_deg": float(quantiles[0, index]) * scale,
            "median_deg": float(quantiles[1, index]) * scale,
            "p95_deg": float(quantiles[2, index]) * scale,
            "max_deg": float(position[:, index].max()) * scale,
            "max_limit_usage": float(usage[:, index].max()),
            "near_limit_rate": float((usage[:, index] >= 0.90).float().mean()),
        }
        for index, name in enumerate(names)
    }


def adjacent_finger_motion_correlations(flexion):
    """[T,4,3] 굽힘 변화량에서 인접 손가락의 Pearson 상관을 구한다."""
    if flexion.ndim != 3 or flexion.shape[1:] != (4, 3):
        raise ValueError("finger flexion must have shape [T,4,3]")
    labels = ("index_middle", "middle_ring", "ring_pinky")
    if flexion.shape[0] < 3:
        return {label: None for label in labels}
    delta = flexion[1:] - flexion[:-1]
    motion = delta.mean(dim=2).float()
    result = {}
    for index, label in enumerate(labels):
        left = motion[:, index] - motion[:, index].mean()
        right = motion[:, index + 1] - motion[:, index + 1].mean()
        denominator = left.square().sum().sqrt() * right.square().sum().sqrt()
        result[label] = (
            float((left * right).sum() / denominator)
            if float(denominator) > 1e-8 else None)
    return result


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
                "sustain_event_success_count": empty,
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
                "sustain_event_success_count": count,
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
            "sustain_event_success_count": event_success.sum(dim=1).float(),
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
