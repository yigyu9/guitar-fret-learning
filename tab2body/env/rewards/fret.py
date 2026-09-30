"""왼손 프렛 압현 보상."""
from __future__ import annotations

import math

import torch

from ..goals import FINGER_EVENT_TIME_SCALE_S
from ..metrics import PressedDragMonitor
from .common import smoothstep01
from .motion import ProximalMotionReward
from .reference_posture import HumanJointRangePrior, ReferenceHandPosturePrior
from .thumb import (
    ThumbSupportReward,
    thumb_base_action_saturation_penalty,
    thumb_press_readiness,
    thumb_press_reward_factor,
    thumb_support_reward,
)


FINGER_NAMES = ("index", "middle", "ring", "pinky")
PRESS_PRECISION_MIN_POSITION = 0.50
PRESS_PRECISION_MIN_ARCH = 0.65
FRET_VALID_REGION_LOWER = 0.10
FRET_VALID_REGION_UPPER = 0.90

# These stages ask the finger to depress the virtual string.  Their alignment
# target must therefore accept a pad that has moved through the string plane;
# using the hover target here creates a direct reward conflict at contact.
PRESS_COMPATIBLE_ALIGNMENT_STAGES = frozenset({
    "isolated_press", "integrated_press", "chord_fine_reach",
    "static_chord", "frozen_context", "goal_pair", "transition_window",
    "coverage", "integration", "full_song",
})


def uses_press_compatible_alignment(stage):
    return str(stage) in PRESS_COMPATIBLE_ALIGNMENT_STAGES


def soft_interval_quality(angle, lower, upper, softness):
    if not lower < upper or softness <= 0.0:
        raise ValueError("soft interval requires lower < upper and softness > 0")
    rise = smoothstep01((angle - (lower - softness)) / softness)
    fall = smoothstep01(((upper + softness) - angle) / softness)
    return (rise * fall).clamp(0.0, 1.0)


def finger_arch_quality(mcp, pip, dip):
    deg = torch.pi / 180.0
    mcp_q = soft_interval_quality(mcp, 15.0 * deg, 80.0 * deg, 15.0 * deg)
    # 중립 자세에서도 PIP 굽힘 기울기가 생기도록 완화 구간을 넓힌다.
    pip_q = soft_interval_quality(pip, 25.0 * deg, 90.0 * deg, 30.0 * deg)
    dip_q = soft_interval_quality(dip, 5.0 * deg, 70.0 * deg, 15.0 * deg)
    coupling = torch.exp(-(((dip - 0.60 * pip) / (35.0 * deg)) ** 2))
    return (0.35 * mcp_q + 0.40 * pip_q + 0.20 * dip_q
            + 0.05 * coupling).clamp(0.0, 1.0)


def fret_position_inside(
        x, lower=FRET_VALID_REGION_LOWER,
        upper=FRET_VALID_REGION_UPPER):
    """Return the exact, uniform correct-position band inside a fret cell."""
    if not 0.0 < lower < upper < 1.0:
        raise ValueError("fret position region must satisfy 0 < lower < upper < 1")
    return (x >= float(lower)) & (x <= float(upper))


def fret_position_quality(
        x, lower=FRET_VALID_REGION_LOWER, optimal=0.20,
        upper=FRET_VALID_REGION_UPPER):
    """Give every point in the decided 10--90% fret band equal credit.

    ``optimal`` is retained for source compatibility with old analysis tools;
    it no longer creates a privileged point inside the valid interval.
    Outside the interval, a smooth margin still supplies a learning signal.
    """
    if not 0.0 < lower <= optimal <= upper < 1.0:
        raise ValueError(
            "fret position bounds must satisfy 0 < lower <= optimal <= upper < 1")
    rising = smoothstep01(x / float(lower))
    falling = smoothstep01((1.0 - x) / float(1.0 - upper))
    return torch.minimum(rising, falling).clamp(0.0, 1.0)


def dense_fret_position_quality(
        x, optimal=0.20, scale=0.20,
        lower=FRET_VALID_REGION_LOWER,
        upper=FRET_VALID_REGION_UPPER):
    """Keep a dense gradient toward the nearest edge of the valid band."""
    if (not 0.0 < lower <= optimal <= upper < 1.0
            or scale <= 0.0):
        raise ValueError(
            "dense fret position requires a valid region and positive scale")
    distance = torch.maximum(
        (float(lower) - x).clamp_min(0.0),
        (x - float(upper)).clamp_min(0.0))
    return torch.exp(-((distance / scale) ** 2)).clamp(0.0, 1.0)


def press_precision_gate(dense_quality, floor=0.40):
    if not 0.0 <= floor <= 1.0:
        raise ValueError("press precision gate floor must be in [0, 1]")
    return floor + (1.0 - floor) * dense_quality.clamp(0.0, 1.0)


def precise_press_success(press_success, position_quality, arch_quality=None,
                          min_position=PRESS_PRECISION_MIN_POSITION,
                          min_arch=None):
    result = press_success & (position_quality >= float(min_position))
    if min_arch is not None:
        if arch_quality is None:
            raise ValueError("arch quality is required when min_arch is set")
        result &= arch_quality >= float(min_arch)
    return result


def press_precision_components(
        press_success, position_quality, arch_quality,
        min_position=PRESS_PRECISION_MIN_POSITION,
        min_arch=PRESS_PRECISION_MIN_ARCH):
    """엄격 압현 판정의 접촉·위치·아치·결합 통과값을 분리한다."""
    if (press_success.shape != position_quality.shape
            or arch_quality.shape != position_quality.shape):
        raise ValueError("press precision tensors must share shape")
    position_pass = position_quality >= float(min_position)
    arch_pass = arch_quality >= float(min_arch)
    precise_pass = press_success & position_pass & arch_pass
    return press_success, position_pass, arch_pass, precise_pass


def press_arch_shaping_quality(
        arch_quality, threshold=PRESS_PRECISION_MIN_ARCH):
    """연속 아치 품질을 엄격 판정 경계까지 직접 유도한다."""
    threshold = float(threshold)
    if not 0.0 < threshold <= 1.0:
        raise ValueError("press arch threshold must be in (0, 1]")
    gate_margin = smoothstep01(arch_quality / threshold)
    return (0.50 * arch_quality + 0.50 * gate_margin).clamp(0.0, 1.0)


def isolated_press_conjunctive_quality(
        press_acquisition, position_quality, arch_precision_quality):
    """접촉·유효 압점·아치를 동시에 만족한 만큼만 정밀 품질을 준다."""
    tensors = (press_acquisition, position_quality, arch_precision_quality)
    if any(value.shape != press_acquisition.shape for value in tensors):
        raise ValueError("isolated press precision tensors must share shape")
    return (
        press_acquisition.clamp(0.0, 1.0)
        * position_quality.clamp(0.0, 1.0)
        * arch_precision_quality.clamp(0.0, 1.0))


def multi_scale_approach_reward(distance):
    return (0.60 * torch.exp(-((distance / 0.012) ** 2))
            + 0.25 * torch.exp(-((distance / 0.060) ** 2))
            + 0.15 * torch.exp(-((distance / 0.150) ** 2))).clamp(0.0, 1.0)


def linear_approach_reward(distance, far_distance=0.250, near_distance=0.010):
    if not 0.0 <= near_distance < far_distance:
        raise ValueError("approach distances must satisfy 0 <= near < far")
    return ((far_distance - distance) /
            (far_distance - near_distance)).clamp(0.0, 1.0)


def fine_alignment_distance_reward(distance):
    """10 mm 부근에서도 목표 중심을 향하는 정밀 거리 기울기를 유지한다."""
    return (
        0.65 * torch.exp(-((distance / 0.010) ** 2))
        + 0.25 * torch.exp(-((distance / 0.030) ** 2))
        + 0.10 * torch.exp(-((distance / 0.100) ** 2))
    ).clamp(0.0, 1.0)


def integrated_press_core_reward(
        distance_reward, fine_distance_reward, lateral_quality,
        normal_quality, precision_gate, press_acquisition,
        press_hold_quality, press_success, good_position_quality):
    """접촉 전 정렬 기울기를 남기면서 실제 압현과 유지를 우선한다."""
    values = (
        distance_reward, fine_distance_reward, lateral_quality,
        normal_quality, precision_gate, press_acquisition,
        press_hold_quality, press_success, good_position_quality)
    if any(value.shape != distance_reward.shape for value in values):
        raise ValueError("integrated press reward tensors must share shape")
    alignment = (
        0.40 * fine_distance_reward
        + 0.35 * lateral_quality
        + 0.25 * normal_quality)
    return (
        0.25 * distance_reward
        + 0.15 * alignment
        + precision_gate * (
            0.30 * press_acquisition + 0.10 * press_hold_quality)
        + 0.20 * press_success.float() * good_position_quality)


def qualify_curriculum_episode_success(
        streak_success, success_frames, evidence_frames,
        minimum_fraction=0.80):
    minimum_fraction = float(minimum_fraction)
    if not 0.0 < minimum_fraction <= 1.0:
        raise ValueError("curriculum success fraction must be in (0, 1]")
    if (streak_success.shape != success_frames.shape
            or evidence_frames.shape != success_frames.shape):
        raise ValueError("curriculum episode tensors must share shape")
    fraction = success_frames / evidence_frames.clamp_min(1.0)
    qualified = (
        streak_success.bool()
        & (evidence_frames > 0.0)
        & (fraction >= minimum_fraction))
    return qualified, fraction


def chord_aware_target_fraction(
        fret, active, base_target, usable,
        optimal=0.20, lower=FRET_VALID_REGION_LOWER,
        upper=FRET_VALID_REGION_UPPER,
        fingertip_clearance=0.0155):
    """같은 프렛의 손끝 목표를 10--90% correct region 안에서 엇갈린다."""
    if (fret.ndim != 2 or active.shape != fret.shape
            or usable.shape != fret.shape
            or base_target.shape != (*fret.shape, 3)):
        raise ValueError("chord target tensors must have shapes [N,S] and [N,S,3]")
    if not 0.0 <= lower <= optimal <= upper <= 1.0:
        raise ValueError("chord target bounds must contain the optimum")
    if fingertip_clearance <= 0.0:
        raise ValueError("fingertip clearance must be positive")

    result = torch.full_like(
        usable, float(optimal), dtype=base_target.dtype)
    pair_distance = torch.cdist(base_target, base_target)
    upper_triangle = torch.triu(
        torch.ones(
            fret.shape[1], fret.shape[1],
            dtype=torch.bool, device=fret.device),
        diagonal=1)
    for fret_number in range(1, 23):
        group = active & (fret.long() == fret_number)
        count = group.sum(dim=1)
        pair = (
            group[:, :, None] & group[:, None, :]
            & upper_triangle[None])
        minimum_separation = pair_distance.masked_fill(
            ~pair, float("inf")).amin(dim=(1, 2))
        minimum_usable = usable.masked_fill(
            ~group, float("inf")).amin(dim=1)
        step = torch.sqrt(
            (float(fingertip_clearance) ** 2
             - minimum_separation.square()).clamp_min(0.0)
        ) / minimum_usable.clamp_min(1e-6)
        span = (step * (count - 1).clamp_min(0)).clamp(
            max=float(upper - lower))
        start = torch.minimum(
            float(optimal) - 0.5 * span,
            float(upper) - span,
        ).clamp_min(float(lower))
        rank = group.long().cumsum(dim=1) - 1
        fraction = (
            start[:, None]
            + span[:, None] * rank.clamp_min(0)
            / (count - 1).clamp_min(1)[:, None])
        result = torch.where(
            group & (count > 1)[:, None], fraction, result)
    return result


def minimum_active_target_separation(target, active):
    if target.ndim != 3 or target.shape[-1] != 3 \
            or active.shape != target.shape[:2]:
        raise ValueError("target separation tensors must have shapes [N,S,3] and [N,S]")
    pair = (
        active[:, :, None] & active[:, None, :]
        & torch.triu(
            torch.ones(
                active.shape[1], active.shape[1],
                dtype=torch.bool, device=active.device),
            diagonal=1)[None])
    minimum = torch.cdist(target, target).masked_fill(
        ~pair, float("inf")).amin(dim=(1, 2))
    return torch.where(
        active.sum(dim=1) > 1, minimum,
        torch.zeros_like(minimum))


def apply_finger_arch_shaping(base_reward, arch_quality, approach_distance,
                              active, weight=0.10):
    """모든 압현 단계에서 거리로 게이트된 아치 품질을 보상에 섞는다."""
    weight = float(weight)
    if not 0.0 <= weight < 1.0:
        raise ValueError("finger arch reward weight must be in [0, 1)")
    arch_reward = arch_quality * linear_approach_reward(approach_distance)
    shaped = (1.0 - weight) * base_reward + weight * arch_reward
    return torch.where(active, shaped, base_reward)


def approach_progress_reward(previous, current, valid, scale=0.002):
    if scale <= 0.0:
        raise ValueError("approach progress scale must be positive")
    progress = ((previous - current) / scale).clamp(-1.0, 1.0)
    return torch.where(valid, progress, torch.zeros_like(progress))


def press_depth_progress(depth, start_depth=-0.005, success_depth=0.001):
    if not start_depth < success_depth:
        raise ValueError("press depth shaping requires start_depth < success_depth")
    return smoothstep01((depth - start_depth) / (success_depth - start_depth))


def update_press_hold_state(
        previous_streak, previous_acquired, previous_fret, previous_finger,
        current_fret, current_finger, press_success,
        min_frames=6, full_frames=12):
    """같은 목표를 연속 압현한 시간과 획득 뒤 이탈을 갱신한다."""
    min_frames = int(min_frames)
    full_frames = int(full_frames)
    if min_frames < 1 or full_frames < min_frames:
        raise ValueError("press hold frames must satisfy 1 <= min <= full")
    tensors = (
        previous_streak, previous_acquired, previous_fret, previous_finger,
        current_fret, current_finger, press_success)
    if any(value.shape != current_fret.shape for value in tensors):
        raise ValueError("press hold tensors must share shape")

    active = current_fret > 0
    same_target = (
        active & (previous_fret > 0)
        & (current_fret == previous_fret)
        & (current_finger == previous_finger))
    streak = torch.where(
        press_success,
        torch.where(same_target, previous_streak + 1,
                    torch.ones_like(previous_streak)),
        torch.zeros_like(previous_streak))
    acquired_now = streak >= min_frames
    acquired = torch.where(
        same_target, previous_acquired | acquired_now, acquired_now) & active
    dropout = same_target & previous_acquired & ~press_success
    span = full_frames - min_frames + 1
    hold_quality = smoothstep01(
        (streak.float() - float(min_frames) + 1.0) / float(span))
    return streak, acquired, hold_quality, dropout, same_target


def balance_press_no_press_channels(
        channel_reward, press_mask, no_press_mask, press_success,
        press_weight=0.75, no_press_weight=0.25,
        no_press_failure_credit=0.10,
        press_bottleneck_weight=0.0,
        no_press_completion_power=1.0):
    """줄 수와 무관한 PRESS/NO_PRESS 클래스 평균을 reward 벡터로 펼친다."""
    if (channel_reward.ndim != 2
            or press_mask.shape != channel_reward.shape
            or no_press_mask.shape != channel_reward.shape
            or press_success.shape != channel_reward.shape):
        raise ValueError("class-balanced fret tensors must share shape [N,S]")
    press_weight = float(press_weight)
    no_press_weight = float(no_press_weight)
    no_press_failure_credit = float(no_press_failure_credit)
    press_bottleneck_weight = float(press_bottleneck_weight)
    no_press_completion_power = float(no_press_completion_power)
    if (press_weight < 0.0 or no_press_weight < 0.0
            or abs(press_weight + no_press_weight - 1.0) > 1e-6):
        raise ValueError("PRESS/NO_PRESS class weights must be non-negative and sum to 1")
    if not 0.0 <= no_press_failure_credit <= no_press_weight:
        raise ValueError("NO_PRESS failure credit must be in [0, no_press_weight]")
    if not 0.0 <= press_bottleneck_weight <= 1.0:
        raise ValueError("PRESS bottleneck weight must be in [0, 1]")
    if no_press_completion_power <= 0.0:
        raise ValueError("NO_PRESS completion power must be positive")

    press_count = press_mask.sum(dim=-1)
    no_press_count = no_press_mask.sum(dim=-1)
    press_mean = (
        channel_reward.masked_fill(~press_mask, 0.0).sum(dim=-1)
        / press_count.clamp_min(1))
    press_min = channel_reward.masked_fill(
        ~press_mask, float("inf")).amin(dim=-1)
    press_min = torch.where(
        press_count > 0, press_min, torch.zeros_like(press_min))
    press_aggregate = (
        (1.0 - press_bottleneck_weight) * press_mean
        + press_bottleneck_weight * press_min)
    no_press_mean = (
        channel_reward.masked_fill(~no_press_mask, 0.0).sum(dim=-1)
        / no_press_count.clamp_min(1))
    press_completion = (
        (press_success & press_mask).sum(dim=-1).float()
        / press_count.clamp_min(1).float())
    effective_no_press_weight = (
        no_press_failure_credit
        + (no_press_weight - no_press_failure_credit)
        * press_completion.pow(no_press_completion_power))

    has_press = press_count > 0
    has_no_press = no_press_count > 0
    mixed = has_press & has_no_press
    aggregate = torch.where(
        mixed,
        press_weight * press_aggregate
        + effective_no_press_weight * no_press_mean,
        torch.where(
            has_press, press_aggregate,
            torch.where(has_no_press, no_press_mean,
                        torch.zeros_like(press_mean))))
    balanced = aggregate[:, None].expand_as(channel_reward)
    return balanced, {
        "press_class_reward": press_aggregate,
        "press_class_mean_reward": press_mean,
        "press_class_min_reward": press_min,
        "no_press_class_reward": no_press_mean,
        "press_class_completion": press_completion,
        "effective_press_class_weight": torch.where(
            mixed, torch.full_like(press_mean, press_weight),
            has_press.float()),
        "effective_no_press_class_weight": torch.where(
            mixed, effective_no_press_weight, has_no_press.float()),
        "class_balanced_reward": aggregate,
    }


def blend_goal_pair_rehearsal_anchor_reward(
        balanced_reward, channel_reward, anchor_mask, weight=0.20):
    if (balanced_reward.shape != channel_reward.shape
            or anchor_mask.shape != channel_reward.shape):
        raise ValueError(
            "goal-pair anchor tensors must share shape [N,S]")
    weight = float(weight)
    if not 0.0 <= weight < 1.0:
        raise ValueError("goal-pair anchor weight must be in [0, 1)")
    count = anchor_mask.sum(dim=-1)
    anchor_reward = (
        channel_reward.masked_fill(~anchor_mask, 0.0).sum(dim=-1)
        / count.clamp_min(1))
    active = count > 0
    shaped = (
        (1.0 - weight) * balanced_reward
        + weight * anchor_reward[:, None])
    return torch.where(active[:, None], shaped, balanced_reward), anchor_reward, active


def gate_static_chord_auxiliary_reward(
        balanced_reward, press_reward, press_completion, floor=0.15):
    """압현 미완성 상태에서 보조 채널의 양의 이득만 제한한다."""
    floor = float(floor)
    if not 0.0 <= floor <= 1.0:
        raise ValueError("static chord auxiliary gate floor must be in [0, 1]")
    if (balanced_reward.ndim != 2
            or press_reward.shape != balanced_reward.shape[:1]
            or press_completion.shape != balanced_reward.shape[:1]):
        raise ValueError("static chord gate tensors have incompatible shapes")
    delta = balanced_reward - press_reward[:, None]
    gate = floor + (1.0 - floor) * press_completion.clamp(0.0, 1.0)
    gated_delta = delta.clamp_max(0.0) + gate[:, None] * delta.clamp_min(0.0)
    return press_reward[:, None] + gated_delta, gate


def gate_incomplete_static_chord_reward(
        balanced_reward, press_completion, press_count,
        floor=0.15, power=2.0):
    """동시 압현이 덜 완성된 코드의 양의 보상만 강하게 제한한다."""
    if (balanced_reward.ndim != 2
            or press_completion.shape != balanced_reward.shape[:1]
            or press_count.shape != balanced_reward.shape[:1]):
        raise ValueError(
            "static chord completion tensors have incompatible shapes")
    floor = float(floor)
    power = float(power)
    if not 0.0 <= floor <= 1.0 or power <= 0.0:
        raise ValueError(
            "static chord completion gate requires floor in [0,1] "
            "and power > 0")
    multi_press = press_count >= 2
    completion_gate = (
        floor + (1.0 - floor)
        * press_completion.clamp(0.0, 1.0).pow(power))
    gate = torch.where(
        multi_press, completion_gate, torch.ones_like(completion_gate))
    gated = (
        balanced_reward.clamp_max(0.0)
        + gate[:, None] * balanced_reward.clamp_min(0.0))
    return gated, gate


def gate_chord_completion_for_stage(
        stage, balanced_reward, press_completion, press_count,
        floor=0.15, power=2.0):
    """Keep the completion gate active throughout static and frozen stages."""
    if str(stage) not in ("static_chord", "frozen_context"):
        return balanced_reward, torch.ones_like(press_completion)
    return gate_incomplete_static_chord_reward(
        balanced_reward, press_completion, press_count,
        floor=floor, power=power)


def blend_anchor_finger_reward(
        mean_reward, per_finger_reward, active_mask, anchor_finger,
        weight=0.20):
    if (mean_reward.ndim != 1
            or per_finger_reward.shape != (mean_reward.shape[0], 4)
            or active_mask.shape != per_finger_reward.shape
            or anchor_finger.shape != mean_reward.shape):
        raise ValueError(
            "anchor-finger reward tensors must have shapes [N] and [N,4]")
    weight = float(weight)
    if not 0.0 <= weight < 1.0:
        raise ValueError("anchor-finger reward weight must be in [0, 1)")
    index = (anchor_finger.long() - 1).clamp(0, 3)
    selected_reward = per_finger_reward.gather(
        1, index[:, None]).squeeze(1)
    selected_active = active_mask.gather(
        1, index[:, None]).squeeze(1)
    selected_active &= anchor_finger > 0
    shaped = (1.0 - weight) * mean_reward + weight * selected_reward
    return torch.where(selected_active, shaped, mean_reward), (
        selected_reward), selected_active


def cached_finger_pose_guide(
        current_q, target_q, scale, valid, gate):
    """리허설 성공 자세를 실제 곡의 같은 손가락 목표에 전달한다."""
    if (current_q.ndim != 3 or current_q.shape[1] != 4
            or target_q.shape != current_q.shape
            or scale.shape != current_q.shape[1:]
            or valid.shape != current_q.shape[:2]
            or gate.shape != current_q.shape[:2]):
        raise ValueError("finger pose guide tensors have incompatible shapes")
    if (not torch.isfinite(current_q).all()
            or not torch.isfinite(target_q).all()
            or not torch.isfinite(scale).all()
            or (scale <= 0.0).any()):
        raise ValueError("finger pose guide inputs must be finite and scaled")
    active = valid.bool() & gate.bool()
    normalized_error = (current_q - target_q) / scale
    per_finger = torch.exp(
        -0.5 * normalized_error.square().mean(dim=-1))
    per_finger = per_finger.masked_fill(~active, 0.0)
    count = active.sum(dim=-1)
    reward = per_finger.sum(dim=-1) / count.clamp_min(1)
    reward = torch.where(count > 0, reward, torch.zeros_like(reward))
    return reward, per_finger, active


def frozen_context_pose_guide_gate(current_finger_active, training_mask):
    if (current_finger_active.ndim != 2
            or training_mask.shape != current_finger_active.shape[:1]):
        raise ValueError("frozen pose-guide masks must have shape [N,F] and [N]")
    return current_finger_active & training_mask.bool()[:, None]


def cached_finger_action_teacher(
        target_action, valid, guide_active, guide_quality,
        minimum_quality=0.0):
    """유효한 성공 캐시만 손가락별 action teacher로 선택한다."""
    if target_action.ndim != 3:
        raise ValueError("finger action targets must have shape [N,F,A]")
    expected = target_action.shape[:2]
    if (valid.shape != expected or guide_active.shape != expected
            or guide_quality.shape != expected):
        raise ValueError(
            "finger action teacher gates must have shape [N,F]")
    minimum_quality = float(minimum_quality)
    if not 0.0 <= minimum_quality <= 1.0:
        raise ValueError("finger action teacher quality must be in [0, 1]")
    selected = (
        valid.bool() & guide_active.bool()
        & (guide_quality >= minimum_quality))
    mask = selected[..., None].expand_as(target_action)
    teacher = torch.where(mask, target_action, torch.zeros_like(target_action))
    return teacher, mask


def cached_consensus_action_teacher(
        target_action, valid, active, cache_quality,
        max_action_spread=0.35, minimum_sources=2):
    """여러 손가락의 성공 action이 합의하는 proximal 축만 감독한다.

    정규화 action은 관절 범위에 선형 대응하므로 품질 가중 평균을 사용할 수
    있다. 손가락별 목표가 충돌하는 축은 range 검사를 통해 mask에서 제외해
    잘못된 평균 자세를 정책에 강제하지 않는다.
    """
    if target_action.ndim != 3:
        raise ValueError("consensus targets must have shape [N,F,A]")
    expected = target_action.shape[:2]
    if (valid.shape != expected or active.shape != expected
            or cache_quality.shape != expected):
        raise ValueError("consensus teacher gates must have shape [N,F]")
    max_action_spread = float(max_action_spread)
    minimum_sources = int(minimum_sources)
    if not 0.0 < max_action_spread <= 2.0:
        raise ValueError("consensus action spread must be in (0, 2]")
    if minimum_sources < 1:
        raise ValueError("consensus teacher needs at least one source")
    selected = valid.bool() & active.bool()
    source_count = selected.sum(dim=1)
    weights = torch.where(
        selected, cache_quality.clamp_min(1e-4),
        torch.zeros_like(cache_quality))
    weight_sum = weights.sum(dim=1, keepdim=True).clamp_min(1e-6)
    teacher = (
        target_action * weights[..., None]
    ).sum(dim=1) / weight_sum
    low = target_action.masked_fill(
        ~selected[..., None], float("inf")).amin(dim=1)
    high = target_action.masked_fill(
        ~selected[..., None], -float("inf")).amax(dim=1)
    agreed = (
        (source_count >= minimum_sources)[:, None]
        & torch.isfinite(low) & torch.isfinite(high)
        & ((high - low) <= max_action_spread))
    teacher = torch.where(agreed, teacher, torch.zeros_like(teacher))
    return teacher, agreed


def aggregate_active_channel_bottleneck(
        channel_reward, active_mask, bottleneck_weight=0.50):
    if channel_reward.ndim != 2 or active_mask.shape != channel_reward.shape:
        raise ValueError("active-channel tensors must share shape [N,S]")
    bottleneck_weight = float(bottleneck_weight)
    if not 0.0 <= bottleneck_weight <= 1.0:
        raise ValueError("active-channel bottleneck weight must be in [0, 1]")
    count = active_mask.sum(dim=-1)
    mean = (
        channel_reward.masked_fill(~active_mask, 0.0).sum(dim=-1)
        / count.clamp_min(1))
    minimum = channel_reward.masked_fill(
        ~active_mask, float("inf")).amin(dim=-1)
    minimum = torch.where(count > 0, minimum, torch.zeros_like(minimum))
    aggregate = (
        (1.0 - bottleneck_weight) * mean
        + bottleneck_weight * minimum)
    expanded = torch.where(
        active_mask, aggregate[:, None], channel_reward)
    return expanded, aggregate, mean, minimum


def chord_fine_conjunctive_reward(
        fine_distance, longitudinal_quality, lateral_quality,
        normal_quality, broad_depth_progress, press_success, active_mask,
        bottleneck_weight=1.0):
    """넓은 좌표 기울기와 실제 접촉을 최약 압현 기준으로 결합한다."""
    tensors = (
        fine_distance, longitudinal_quality, lateral_quality,
        normal_quality, broad_depth_progress, press_success, active_mask)
    if any(value.shape != fine_distance.shape for value in tensors):
        raise ValueError("chord-fine tensors must share shape [N,S]")
    if fine_distance.ndim != 2:
        raise ValueError("chord-fine tensors must have shape [N,S]")
    broad_axes = torch.stack((
        longitudinal_quality.clamp(0.0, 1.0).pow(0.25),
        lateral_quality.clamp(0.0, 1.0).pow(0.25),
        normal_quality.clamp(0.0, 1.0).pow(0.25),
        broad_depth_progress.clamp(0.0, 1.0),
    ), dim=-1)
    axis_minimum = broad_axes.amin(dim=-1)
    channel = (
        0.35 * fine_distance.clamp(0.0, 1.0)
        + 0.45 * axis_minimum
        + 0.20 * press_success.float())
    expanded, aggregate, mean, minimum = (
        aggregate_active_channel_bottleneck(
            channel, active_mask,
            bottleneck_weight=bottleneck_weight))
    return expanded, aggregate, mean, minimum, axis_minimum


def fret_region_alignment(
        signed_longitudinal, lateral_error, normal_error,
        target_fraction, usable_length,
        lower=FRET_VALID_REGION_LOWER,
        upper=FRET_VALID_REGION_UPPER):
    """목표점이 아니라 허용 압현 구간까지의 오차를 계산한다."""
    if not 0.0 <= lower < upper <= 1.0:
        raise ValueError("fret region must satisfy 0 <= lower < upper <= 1")
    tensors = (
        signed_longitudinal, lateral_error, normal_error,
        target_fraction, usable_length)
    if any(value.shape != signed_longitudinal.shape for value in tensors):
        raise ValueError("fret-region tensors must share shape")
    sample_fraction = (
        target_fraction
        - signed_longitudinal / usable_length.clamp_min(1e-5))
    fraction_error = torch.maximum(
        (float(lower) - sample_fraction).clamp_min(0.0),
        (sample_fraction - float(upper)).clamp_min(0.0))
    longitudinal_error = fraction_error * usable_length
    longitudinal_quality = torch.exp(-((longitudinal_error / 0.008) ** 2))
    lateral_quality = torch.exp(-((lateral_error / 0.004) ** 2))
    normal_quality = torch.exp(-((normal_error / 0.006) ** 2))
    distance = torch.sqrt(
        longitudinal_error.square() + lateral_error.square()
        + normal_error.square() + 1e-12)
    return {
        "sample_fraction": sample_fraction,
        "fraction_error": fraction_error,
        "longitudinal_error": longitudinal_error,
        "longitudinal_quality": longitudinal_quality,
        "lateral_quality": lateral_quality,
        "normal_quality": normal_quality,
        "alignment_quality": (
            longitudinal_quality + lateral_quality + normal_quality) / 3.0,
        "distance": distance,
        "inside": fraction_error <= 1e-6,
    }


def next_goal_approach_reward(
        tips, all_approach, outward, finger_event, current_finger_active,
        pad_radius=0.0063, lookahead_s=0.50,
        current_press_protected=None, release_window_s=0.25,
        prepress_clearance=0.004, time_gate_floor=0.0):
    """MOVE 손가락이 현재 압현을 보존하며 다음 목표에 미리 접근하도록 한다."""
    if tips.ndim != 3 or tips.shape[1:] != (4, 3):
        raise ValueError("fingertips must have shape [N,4,3]")
    if (all_approach.shape != (tips.shape[0], 6, 22, 3)
            or outward.shape != (tips.shape[0], 6, 3)
            or finger_event.shape != (tips.shape[0], 4, 13)
            or current_finger_active.shape != (tips.shape[0], 4)):
        raise ValueError("next-goal tensors have incompatible shapes")
    if (pad_radius < 0.0 or lookahead_s <= 0.0
            or release_window_s <= 0.0 or prepress_clearance < 0.0):
        raise ValueError(
            "next-goal geometry/timing parameters are invalid")
    if current_press_protected is None:
        current_press_protected = torch.zeros_like(current_finger_active)
    elif current_press_protected.shape != current_finger_active.shape:
        raise ValueError(
            "current press protection must match current finger activity")
    else:
        current_press_protected = current_press_protected.bool()

    string_mask = finger_event[..., :6] > 0.5
    next_fret = torch.round(finger_event[..., 6] * 22.0).long()
    next_fret_index = next_fret.clamp(1, 22) - 1
    source = all_approach[:, :, None].expand(-1, -1, 4, -1, -1)
    gather_index = next_fret_index[:, None, :, None, None].expand(
        -1, 6, -1, 1, 3)
    target = torch.gather(source, 3, gather_index).squeeze(3).permute(0, 2, 1, 3)
    hover_center = (
        target
        + (float(pad_radius) + float(prepress_clearance))
        * outward[:, None])
    distance_by_string = (
        tips[:, :, None] - hover_center).norm(dim=-1)
    distance = distance_by_string.masked_fill(
        ~string_mask, float("inf")).amin(dim=-1)

    time_to_next = finger_event[..., 7] * FINGER_EVENT_TIME_SCALE_S
    time_to_change = finger_event[..., 9] * FINGER_EVENT_TIME_SCALE_S
    base_enabled = (
        (finger_event[..., 8] > 0.5)
        & (finger_event[..., 11] > 0.5)
        & string_mask.any(dim=-1)
        & (time_to_next < float(lookahead_s)))
    next_time_gate = smoothstep01(
        (float(lookahead_s) - time_to_next) / float(lookahead_s))
    release_time_gate = smoothstep01(
        (float(release_window_s) - time_to_change)
        / float(release_window_s))
    inactive_enabled = base_enabled & ~current_finger_active
    active_enabled = (
        base_enabled & current_finger_active & current_press_protected
        & (time_to_change < float(release_window_s)))
    enabled = inactive_enabled | active_enabled
    time_gate = next_time_gate * torch.where(
        active_enabled, release_time_gate, torch.ones_like(release_time_gate))
    floor = torch.as_tensor(
        time_gate_floor, dtype=time_gate.dtype, device=time_gate.device)
    if floor.numel() == 1:
        floor = floor.expand(tips.shape[0])
    elif floor.shape != (tips.shape[0],):
        raise ValueError("next-goal time gate floor must be scalar or [N]")
    if not torch.isfinite(floor).all() or (floor < 0.0).any() or (floor > 1.0).any():
        raise ValueError("next-goal time gate floor must be finite in [0, 1]")
    time_gate = floor[:, None] + (1.0 - floor[:, None]) * time_gate
    per_finger = (
        multi_scale_approach_reward(distance) * time_gate
    ).masked_fill(~enabled, 0.0)

    def masked_mean(mask):
        count = mask.sum(dim=-1)
        value = per_finger.masked_fill(~mask, 0.0).sum(dim=-1) \
            / count.clamp_min(1)
        return torch.where(count > 0, value, torch.zeros_like(value))

    count = enabled.sum(dim=-1)
    reward = per_finger.sum(dim=-1) / count.clamp_min(1)
    reward = torch.where(count > 0, reward, torch.zeros_like(reward))
    return reward, {
        "next_goal_approach_per_finger": per_finger,
        "next_goal_approach_distance": torch.where(
            enabled, distance, torch.zeros_like(distance)),
        "next_goal_approach_gate": enabled,
        "next_goal_time_gate": torch.where(
            enabled, time_gate, torch.zeros_like(time_gate)),
        "next_goal_inactive_move_gate": inactive_enabled,
        "next_goal_active_move_gate": active_enabled,
        "next_goal_inactive_move_reward": masked_mean(inactive_enabled),
        "next_goal_active_move_reward": masked_mean(active_enabled),
        "next_goal_release_time_gate": torch.where(
            active_enabled, release_time_gate,
            torch.zeros_like(release_time_gate)),
    }


def next_goal_distance_potential(distance, near=0.010, far=0.350):
    if not 0.0 <= near < far:
        raise ValueError(
            "next-goal potential distances must satisfy 0 <= near < far")
    return 1.0 - ((distance - float(near))
                  / (float(far) - float(near))).clamp(0.0, 1.0)


def next_goal_potential_progress(
        previous_potential, current_distance, previous_valid,
        same_target, enabled, current_press_preserved,
        near=0.010, far=0.350, unprotected_positive_scale=0.0):
    if (previous_potential.shape != current_distance.shape
            or previous_valid.shape != current_distance.shape
            or same_target.shape != current_distance.shape
            or enabled.shape != current_distance.shape):
        raise ValueError("next-goal progress tensors must share shape [N,F]")
    if current_press_preserved.shape != current_distance.shape[:1]:
        raise ValueError("current press preservation must have shape [N]")
    if not 0.0 <= float(unprotected_positive_scale) <= 1.0:
        raise ValueError(
            "unprotected positive progress scale must be in [0, 1]")
    potential = next_goal_distance_potential(
        current_distance, near=near, far=far)
    valid = previous_valid.bool() & same_target.bool() & enabled.bool()
    progress = torch.where(
        valid, potential - previous_potential,
        torch.zeros_like(potential))
    preservation = current_press_preserved.float().clamp(0.0, 1.0)
    positive_scale = (
        float(unprotected_positive_scale)
        + (1.0 - float(unprotected_positive_scale)) * preservation)
    progress = torch.where(
        progress > 0.0,
        progress * positive_scale[:, None],
        progress)
    return progress, potential


def gate_next_goal_positive_progress(
        progress, current_press_preserved, require_preservation=False):
    """Keep signed progress, but optionally require a held current press.

    A transition may still move *away* from the next target when the outgoing
    press is lost; that negative signal is useful for learning.  The opposite
    direction is different: granting positive next-goal credit while the
    current note is not held teaches the policy to release before transferring.
    ``require_preservation`` is opt-in so the historical standalone shaping
    helper remains usable for non-transition ablations.
    """
    if progress.ndim != 2 or current_press_preserved.shape != progress.shape[:1]:
        raise ValueError("next-goal progress gate requires [N,F] and [N]")
    preserved = current_press_preserved.bool()
    if require_preservation:
        progress = torch.where(
            progress > 0.0,
            progress * preserved[:, None].to(progress.dtype),
            progress)
    return progress


def conjunctive_next_goal_quality(next_quality, preservation_quality):
    """다음 접근은 현재 압현을 보존한 만큼만 양의 품질을 인정한다."""
    if next_quality.shape != preservation_quality.shape:
        raise ValueError(
            "next-goal and preservation quality must share shape [N]")
    if (not torch.isfinite(next_quality).all()
            or not torch.isfinite(preservation_quality).all()):
        raise ValueError("next-goal conjunction requires finite qualities")
    return (
        next_quality.clamp(0.0, 1.0)
        * preservation_quality.clamp(0.0, 1.0))


def conjunctive_chord_quality(
        press_completion, hold_quality, no_press_completion,
        thumb_press_factor):
    """압현 결합 점수의 NO_PRESS·엄지 우회 경로를 막는다."""
    tensors = (
        press_completion, hold_quality, no_press_completion,
        thumb_press_factor)
    if any(value.shape != press_completion.shape for value in tensors):
        raise ValueError("chord quality tensors must share shape [N]")
    if any(not torch.isfinite(value).all() for value in tensors):
        raise ValueError("chord quality requires finite inputs")
    press_hold = (
        (2.0 / 3.0) * press_completion.clamp(0.0, 1.0).square()
        + (1.0 / 3.0) * hold_quality.clamp(0.0, 1.0))
    return (
        press_hold
        * no_press_completion.clamp(0.0, 1.0)
        * thumb_press_factor.clamp(0.0, 1.0))


def thumb_goal_proximity_gate(distance, active, full_distance=0.025,
                              zero_distance=0.080):
    if not 0.0 <= full_distance < zero_distance:
        raise ValueError("thumb proximity distances must satisfy 0 <= full < zero")
    nearest = distance.masked_fill(~active, float("inf")).amin(dim=-1)
    gate = smoothstep01(
        (zero_distance - nearest) / (zero_distance - full_distance))
    return torch.where(active.any(dim=-1), gate, torch.zeros_like(gate))


def one_sided_pad_distance(axis_delta, outward, radius):
    outside = (axis_delta * outward).sum(dim=-1)
    tangent = (axis_delta - outside[..., None] * outward).norm(dim=-1)
    tangent_gap = (tangent - radius).clamp_min(0.0)
    outside_gap = (outside - radius).clamp_min(0.0)
    return torch.sqrt(tangent_gap.square() + outside_gap.square() + 1e-12)


def cylindrical_pad_depth(axis_delta, outward, radius):
    outside = (axis_delta * outward).sum(dim=-1)
    lateral2 = ((axis_delta - outside[..., None] * outward) ** 2).sum(dim=-1)
    lateral_ok = lateral2 <= radius ** 2
    inward_extent = (radius ** 2 - lateral2).clamp_min(0.0).sqrt()
    return inward_extent - outside, lateral_ok


def update_press_hysteresis(previous, depth, on_depth=0.0010, off_depth=0.0005):
    return (depth >= on_depth) | (previous & (depth > off_depth))


def fret_requirement_masks(fret_goal, max_fret=22):
    """목표에서 프렛별 압현·금지·무관 마스크를 만든다."""
    fret_numbers = torch.arange(1, max_fret + 1, device=fret_goal.device)
    view_shape = (1,) * fret_goal.ndim + (max_fret,)
    fret_numbers = fret_numbers.view(view_shape)
    goal = fret_goal.long()[..., None]
    positive = goal > 0
    no_press_string = goal < 0
    press_required = positive & (fret_numbers == goal)
    no_press_required = no_press_string | (positive & (fret_numbers > goal))
    dontcare = ~(press_required | no_press_required)
    return press_required, no_press_required, dontcare


def wrong_press_mask(pressed_by_fret, no_press_required):
    return (pressed_by_fret & no_press_required).any(dim=-1)


def wrong_press_finger_mask(pressed_by_finger_fret, no_press_required):
    """금지 프렛을 실제로 누른 손가락을 분리한다."""
    if (pressed_by_finger_fret.ndim != 4
            or no_press_required.shape
                != (pressed_by_finger_fret.shape[0],
                    pressed_by_finger_fret.shape[1],
                    pressed_by_finger_fret.shape[3])):
        raise ValueError(
            "finger wrong-press tensors must be [N,S,Finger,Fret] and "
            "[N,S,Fret]")
    forbidden = (
        pressed_by_finger_fret
        & no_press_required[:, :, None, :])
    return forbidden.any(dim=1).any(dim=-1)


def wrong_press_avoidance_reward(max_forbidden_depth, on_depth=0.0010,
                                 margin=0.0020):
    """금지 프렛 압현 직전의 선택적 회피 점수다."""
    return smoothstep01((on_depth - max_forbidden_depth) / margin)


def blend_wrong_press_avoidance(
        core, avoidance_reward, supervised_mask, wrong_press, weight):
    """감독 줄에만 연속 회피 점수를 섞고 실제 오압현은 0점으로 둔다."""
    if not (
            core.shape == avoidance_reward.shape
            == supervised_mask.shape == wrong_press.shape):
        raise ValueError("wrong-press shaping tensors must share shape")
    weight = float(weight)
    if not 0.0 <= weight < 1.0:
        raise ValueError("wrong-press avoidance weight must be in [0, 1)")
    shaped = torch.lerp(core, avoidance_reward, weight)
    shaped = torch.where(wrong_press, torch.zeros_like(shaped), shaped)
    return torch.where(supervised_mask, shaped, core)


def apply_binary_penalty(value, mask, penalty):
    """불리언 사건에 유한한 비음수 비용을 적용한다."""
    if value.shape != mask.shape:
        raise ValueError("penalty value and mask must share shape")
    penalty = float(penalty)
    if not math.isfinite(penalty) or penalty < 0.0:
        raise ValueError("binary penalty must be finite and non-negative")
    return value - penalty * mask.to(value.dtype)


def press_near_miss_mask(active, success, target_distance, max_distance):
    if not (active.shape == success.shape == target_distance.shape):
        raise ValueError("near-miss tensors must share shape")
    max_distance = float(max_distance)
    if not math.isfinite(max_distance) or max_distance <= 0.0:
        raise ValueError("near-miss distance must be finite and positive")
    return active.bool() & ~success.bool() & (target_distance <= max_distance)


def bound_fret_reward(
        reward, stage, wrong_press_penalty, press_dropout_penalty,
        press_near_miss_penalty=0.0):
    """일반 보상을 유한한 학습 범위에 두되 활성 실패 비용은 보존한다."""
    wrong_press_penalty = float(wrong_press_penalty)
    press_dropout_penalty = float(press_dropout_penalty)
    press_near_miss_penalty = float(press_near_miss_penalty)
    if (not math.isfinite(wrong_press_penalty)
            or not math.isfinite(press_dropout_penalty)
            or wrong_press_penalty < 0.0
            or press_dropout_penalty < 0.0):
        raise ValueError("fret penalties must be finite and non-negative")
    if (not math.isfinite(press_near_miss_penalty)
            or press_near_miss_penalty < 0.0):
        raise ValueError("near-miss penalty must be finite and non-negative")
    early_stage = stage in (
        "coarse_reach", "fine_reach",
        "chord_reach", "chord_fine_reach")
    lower = -1.0 if early_stage else -min(
        wrong_press_penalty + press_dropout_penalty
        + press_near_miss_penalty, 1.0)
    return reward.clamp(lower, 1.0)


def suppress_positive_reward_on_penetration(reward, penetration):
    """관통한 프레임에서는 양의 보상을 제거하고 기존 감점은 유지한다."""
    if reward.ndim != 2 or penetration.shape != reward.shape[:1]:
        raise ValueError(
            "penetration reward gate requires [N,C] reward and [N] mask")
    return torch.where(
        penetration.bool()[:, None], reward.clamp_max(0.0), reward)


def guitar_penetration_soft_cost(
        depth, soft_threshold=0.0025, hard_threshold=0.005,
        max_cost=0.05):
    """심각한 관통 종료 전에 깊이에 비례한 연속 회피 신호를 만든다."""
    if (not math.isfinite(soft_threshold)
            or not math.isfinite(hard_threshold)
            or not math.isfinite(max_cost)
            or soft_threshold < 0.0
            or hard_threshold <= soft_threshold
            or max_cost < 0.0):
        raise ValueError("penetration soft-cost bounds are invalid")
    fraction = (
        (depth - soft_threshold) / (hard_threshold - soft_threshold)
    ).clamp(0.0, 1.0)
    return float(max_cost) * fraction.square()


def released_finger_hover_reward(tips, string_start, string_end, gate,
                                 pad_radius=0.0063, free_gap=0.030,
                                 decay_scale=0.040):
    """해제된 손가락이 허용 간격 밖으로 멀어질 때만 감점한다."""
    if pad_radius < 0 or free_gap < 0 or decay_scale <= 0:
        raise ValueError("hover geometry parameters must be non-negative/positive")
    segment = string_end - string_start
    denom = segment.square().sum(-1).clamp_min(1e-10)
    delta = tips[:, :, None] - string_start[:, None]
    t = (delta * segment[:, None]).sum(-1) / denom[:, None]
    closest = string_start[:, None] + t.clamp(0.0, 1.0)[..., None] * segment[:, None]
    center_distance = (tips[:, :, None] - closest).norm(dim=-1)
    surface_gap = (center_distance - pad_radius).clamp_min(0.0).min(dim=-1).values
    excess = (surface_gap - free_gap).clamp_min(0.0)
    per_finger = torch.exp(-((excess / decay_scale) ** 2))
    gate_f = gate.float()
    count = gate_f.sum(dim=-1)
    reward = (per_finger * gate_f).sum(dim=-1) / count.clamp_min(1.0)
    reward = torch.where(count > 0, reward, torch.ones_like(reward))
    return reward, surface_gap, per_finger


def released_finger_outward_velocity_reward(
        outward_speed, gate, free_speed=0.10, decay_scale=0.25):
    """손끝과 줄 사이 간격이 커지는 속도만 부드럽게 억제한다."""
    if free_speed < 0.0 or decay_scale <= 0.0:
        raise ValueError("hover speed parameters must be non-negative/positive")
    excess = (outward_speed - free_speed).clamp_min(0.0)
    per_finger = torch.exp(-((excess / decay_scale) ** 2))
    gate_f = gate.float()
    count = gate_f.sum(dim=-1)
    reward = (per_finger * gate_f).sum(dim=-1) / count.clamp_min(1.0)
    reward = torch.where(count > 0, reward, torch.ones_like(reward))
    return reward, per_finger


def released_finger_velocity_gate(
        had_successful_press, current_active, previous_valid,
        relation_rest, relation_move, time_to_next_s, move_release_time=0.25):
    if move_release_time < 0.0:
        raise ValueError("hover MOVE release time must be non-negative")
    released = had_successful_press & ~current_active & previous_valid
    waiting_to_move = relation_move & (time_to_next_s > move_release_time)
    return released & (relation_rest | waiting_to_move)


def released_finger_pose_reward(
        current_arch, release_anchor, release_age, gate,
        blend_time=0.30, relaxed_pip_deg=25.0, relaxed_dip_deg=10.0,
        tolerance_deg=(15.0, 20.0, 15.0)):
    """마지막 압현 자세를 짧게 유지한 뒤 완만한 hover 아치로 이완한다."""
    if blend_time <= 0.0:
        raise ValueError("release pose blend time must be positive")
    tolerance = torch.as_tensor(
        tolerance_deg, dtype=current_arch.dtype,
        device=current_arch.device)
    if tolerance.shape != (3,) or (tolerance <= 0.0).any():
        raise ValueError("release pose tolerance must contain 3 positive angles")
    tolerance = torch.deg2rad(tolerance)
    relaxed = release_anchor.clone()
    relaxed[..., 1] = float(relaxed_pip_deg) * torch.pi / 180.0
    relaxed[..., 2] = float(relaxed_dip_deg) * torch.pi / 180.0
    blend = smoothstep01(release_age / float(blend_time))[..., None]
    target = release_anchor + blend * (relaxed - release_anchor)
    normalized_error = (current_arch - target) / tolerance
    per_finger = torch.exp(-normalized_error.square().mean(dim=-1))
    gate_f = gate.float()
    count = gate_f.sum(dim=-1)
    reward = (per_finger * gate_f).sum(dim=-1) / count.clamp_min(1.0)
    reward = torch.where(count > 0, reward, torch.ones_like(reward))
    error_deg = torch.rad2deg((current_arch - target).abs().mean(dim=-1))
    return reward, per_finger, error_deg


def finger_synergy_follower_mask(current_finger_active, finger_event):
    if (current_finger_active.ndim != 2
            or current_finger_active.shape[1] != 4
            or finger_event.shape != (*current_finger_active.shape, 13)):
        raise ValueError(
            "finger synergy activity/events must have shapes [N,4] and [N,4,13]")
    upcoming_move = (
        (finger_event[..., 8] > 0.5)
        & (finger_event[..., 11] > 0.5))
    return ~current_finger_active.bool() & ~upcoming_move


def adjacent_finger_action_synergy(
        actions, previous_actions, flexion_action_indices, follower_allowed,
        half_ranges, action_scale=1.0, coefficients=(0.10, 0.15, 0.18),
        min_driver_delta_deg=0.25, full_driver_delta_deg=1.50,
        max_induced_delta_deg=1.50):
    """비활성 인접 손가락에 작은 굽힘 action 변화를 전달한다."""
    if actions.shape != previous_actions.shape or actions.ndim != 2:
        raise ValueError("actions and previous_actions must share shape [N,A]")
    if flexion_action_indices.shape != (4, 3):
        raise ValueError("flexion action indices must have shape [4,3]")
    if follower_allowed.shape != (actions.shape[0], 4):
        raise ValueError("follower mask must have shape [N,4]")
    coefficients = tuple(float(value) for value in coefficients)
    if len(coefficients) != 3 or any(
            value < 0.0 or value >= 1.0 for value in coefficients):
        raise ValueError("three synergy coefficients must be in [0,1)")
    if not 0.0 <= min_driver_delta_deg < full_driver_delta_deg:
        raise ValueError("synergy driver thresholds are invalid")
    if max_induced_delta_deg <= 0.0 or action_scale <= 0.0:
        raise ValueError("synergy delta and action scale must be positive")

    indices = flexion_action_indices.to(
        device=actions.device, dtype=torch.long)
    if (actions.device.type == "cpu"
            and bool(((indices < 0) | (indices >= actions.shape[1])).any())):
        raise ValueError("synergy action index is outside the action vector")
    half_ranges = torch.as_tensor(
        half_ranges, dtype=actions.dtype, device=actions.device)
    if half_ranges.ndim == 1:
        half_ranges = half_ranges[None].expand(actions.shape[0], -1)
    if half_ranges.shape != actions.shape:
        raise ValueError("half_ranges must be positive with shape [A] or [N,A]")
    if actions.device.type == "cpu" and bool((half_ranges <= 0.0).any()):
        raise ValueError("half_ranges must be positive")

    current = actions[:, indices]
    previous = previous_actions[:, indices]
    scale = float(action_scale) * half_ranges[:, indices]
    driver_delta = (current - previous) * scale

    matrix = actions.new_zeros(4, 4)
    for index, value in enumerate(coefficients):
        matrix[index, index + 1] = value
        matrix[index + 1, index] = value
    induced = torch.einsum("fd,ndj->nfj", matrix, driver_delta)

    driver_speed = torch.rad2deg(
        driver_delta.square().mean(dim=-1).sqrt())
    adjacency = matrix > 0.0
    neighbor_speed = driver_speed[:, None, :].masked_fill(
        ~adjacency[None], -float("inf")).amax(dim=-1)
    driver_gate = smoothstep01(
        (neighbor_speed - float(min_driver_delta_deg))
        / (float(full_driver_delta_deg) - float(min_driver_delta_deg)))
    gate = follower_allowed & (driver_gate > 0.0)

    max_delta = float(max_induced_delta_deg) * torch.pi / 180.0
    induced = induced.clamp(-max_delta, max_delta)
    induced = induced * driver_gate[..., None] * gate[..., None]
    normalized_delta = induced / scale.clamp_min(1e-8)

    result = actions.clone()
    result[:, indices] = (current + normalized_delta).clamp(-1.0, 1.0)
    induced_deg = torch.rad2deg(
        induced.square().mean(dim=-1).sqrt())
    return result, induced_deg, gate


def adjacent_finger_coupling_reward(
        flexion_velocity, follower_allowed, press_protected,
        coefficients=(0.15, 0.20, 0.25),
        min_driver_speed_deg=5.0, full_driver_speed_deg=30.0,
        tolerance_deg_s=15.0):
    """움직이는 손가락의 굽힘 속도를 인접 비활성 손가락이 약하게 따른다."""
    if flexion_velocity.ndim != 3 or flexion_velocity.shape[1:] != (4, 3):
        raise ValueError("finger flexion velocity must have shape [N,4,3]")
    if follower_allowed.shape != flexion_velocity.shape[:2]:
        raise ValueError("follower mask must have shape [N,4]")
    if press_protected.shape != flexion_velocity.shape[:1]:
        raise ValueError("press protection mask must have shape [N]")
    coefficients = tuple(float(value) for value in coefficients)
    if len(coefficients) != 3 or any(
            value < 0.0 or value >= 1.0 for value in coefficients):
        raise ValueError("three adjacent coupling coefficients must be in [0,1)")
    if not 0.0 <= min_driver_speed_deg < full_driver_speed_deg:
        raise ValueError("driver speed thresholds are invalid")
    if tolerance_deg_s <= 0.0:
        raise ValueError("coupling tolerance must be positive")

    matrix = flexion_velocity.new_zeros(4, 4)
    for index, value in enumerate(coefficients):
        matrix[index, index + 1] = value
        matrix[index + 1, index] = value
    target = torch.einsum("fd,ndj->nfj", matrix, flexion_velocity)

    speed = torch.rad2deg(flexion_velocity.square().mean(dim=-1).sqrt())
    adjacency = matrix > 0.0
    neighbor_speed = speed[:, None, :].masked_fill(
        ~adjacency[None], -float("inf")).amax(dim=-1)
    driver_gate = smoothstep01(
        (neighbor_speed - float(min_driver_speed_deg))
        / (float(full_driver_speed_deg) - float(min_driver_speed_deg)))
    gate = follower_allowed & press_protected[:, None] & (driver_gate > 0.0)

    tolerance = float(tolerance_deg_s) * torch.pi / 180.0
    error_energy = ((flexion_velocity - target) / tolerance).square().mean(dim=-1)
    idle_energy = (target / tolerance).square().mean(dim=-1)
    matched = torch.exp(-error_energy)
    idle = torch.exp(-idle_energy)
    improvement = ((matched - idle) / (1.0 - idle).clamp_min(1e-6)).clamp(0.0, 1.0)
    per_finger = improvement * driver_gate
    gate_f = gate.float()
    count = gate_f.sum(dim=-1)
    reward = (per_finger * gate_f).sum(dim=-1) / count.clamp_min(1.0)
    reward = torch.where(count > 0, reward, torch.zeros_like(reward))
    target_speed_deg = torch.rad2deg(target.square().mean(dim=-1).sqrt())
    return reward, per_finger, gate, target_speed_deg


def blend_finger_coupling_reward(
        reward, coupling_reward, press_mask, coupling_gate, weight=0.015):
    """실제로 coupling gate가 열린 환경의 PRESS 채널만 혼합한다."""
    weight = float(weight)
    if (reward.ndim != 2 or coupling_reward.shape != reward.shape[:1]
            or press_mask.shape != reward.shape
            or coupling_gate.shape[:1] != reward.shape[:1]):
        raise ValueError("finger coupling blend tensors have incompatible shapes")
    if not 0.0 <= weight < 1.0:
        raise ValueError("finger coupling blend weight must be in [0,1)")
    active = coupling_gate.any(dim=-1)
    blended = (
        (1.0 - weight) * reward
        + weight * coupling_reward[:, None])
    return torch.where(press_mask & active[:, None], blended, reward), active


def fingertip_slip_reward(distance, gate, free_distance=0.002,
                          decay_scale=0.003):
    if free_distance < 0.0 or decay_scale <= 0.0:
        raise ValueError("slip free distance/decay scale must be non-negative/positive")
    excess = (distance - free_distance).clamp_min(0.0)
    per_finger = torch.exp(-((excess / decay_scale) ** 2))
    gate_f = gate.float()
    count = gate_f.sum(dim=-1)
    reward = (per_finger * gate_f).sum(dim=-1) / count.clamp_min(1.0)
    reward = torch.where(count > 0, reward, torch.ones_like(reward))
    return reward, per_finger


def quat_rotate(q, v):
    q_vec, q_w = q[..., :3], q[..., 3:4]
    return (v * (2.0 * q_w * q_w - 1.0)
            + 2.0 * q_w * torch.cross(q_vec, v, dim=-1)
            + 2.0 * q_vec * (q_vec * v).sum(dim=-1, keepdim=True))


class FretReward:
    # guitar_asset.xml의 프렛·너트 치수
    FRET_HALF_WIDTH = 0.0007
    NUT_HALF_WIDTH = 0.000955
    PAD_RADIUS = 0.0063
    PRESS_ON_DEPTH = 0.0010
    PRESS_OFF_DEPTH = 0.0005
    APPROACH_X = 0.20
    N_SEGMENT_SAMPLES = 5
    # 일반 압현은 손끝 구간만, 바레는 전체 구간을 사용한다.
    TIP_SAMPLE_MIN_ALPHA = 0.85
    FINE_NORMAL_CLEARANCE = 0.0005
    FINGERTIP_TARGET_CLEARANCE = 0.0155

    def __init__(self, env, wrist_weight=0.15, smooth_weight=0.0,
                 wrong_press_penalty=0.25, wrong_press_avoidance_weight=0.10,
                 press_near_miss_penalty=0.0,
                 press_near_miss_distance=0.015,
                 finger_arch_reward_weight=0.10,
                 fine_reach_finger_arch_reward_weight=0.18,
                 isolated_press_arch_reward_weight=0.35,
                 isolated_press_conjunctive_weight=0.30,
                 thumb_weight=0.15,
                 thumb_pad_radius=0.010,
                 thumb_approach_scale=0.020, thumb_reach_scale=0.120,
                 thumb_contact_on_force=0.5,
                 thumb_contact_off_force=0.1,
                 thumb_force_soft_limit=50000.0,
                 thumb_force_decay_scale=100000.0,
                 thumb_compression_free_depth=0.0005,
                 thumb_compression_decay_scale=0.002,
                 thumb_overforce_penalty=0.10,
                 thumb_gate_full_distance=0.025,
                 thumb_gate_zero_distance=0.080,
                 thumb_press_gate_weight=0.15,
                 thumb_base_saturation_threshold=0.90,
                 thumb_base_saturation_penalty_weight=0.01,
                 thumb_base_supported_saturation_fraction=0.0,
                 proximal_weight=0.02, proximal_transition=0.10,
                 hover_weight=0.020, hover_free_gap=0.012,
                 hover_decay_scale=0.020, hover_position_weight=0.55,
                 hover_release_pose_weight=0.30,
                 hover_release_blend_time=0.30,
                 hover_release_relaxed_pip_deg=25.0,
                 hover_release_relaxed_dip_deg=10.0,
                 hover_release_tolerance_deg=(15.0, 20.0, 15.0),
                 hover_free_outward_speed=0.03,
                 hover_speed_decay_scale=0.12,
                 hover_move_release_time=0.25,
                 finger_coupling_weight=0.030,
                 finger_coupling_coefficients=(0.20, 0.28, 0.35),
                 finger_coupling_min_speed_deg=4.0,
                 finger_coupling_full_speed_deg=25.0,
                 finger_coupling_tolerance_deg_s=15.0,
                 reference_motion_prior_path=None,
                 reference_motion_prior_weight=0.0,
                 reference_motion_prior_finger_fraction=0.67,
                 reference_motion_prior_exemplars=64,
                 human_joint_range_path=None,
                 human_joint_range_weight=0.0,
                 human_joint_range_decay_deg=15.0,
                 human_joint_range_active_finger_fraction=0.25,
                 human_joint_range_thumb_fraction=0.10,
                 slip_weight=0.005, slip_stable_frames=3,
                 slip_free_distance=0.002, slip_decay_scale=0.003,
                 pressed_drag_threshold=0.003,
                 press_class_weight=0.75,
                 no_press_class_weight=0.25,
                 no_press_failure_credit=0.10,
                 static_chord_bottleneck_weight=0.50,
                 chord_bridge_bottleneck_weight=0.50,
                 chord_fine_joint_weight=0.40,
                 chord_fine_depth_start=-0.025,
                 static_chord_joint_weight=0.30,
                 static_chord_auxiliary_gate_floor=0.15,
                 static_chord_completion_gate_floor=0.15,
                 static_chord_completion_gate_power=2.0,
                 goal_pair_rehearsal_anchor_weight=0.20,
                 chord_reach_success_pose_guide_weight=0.25,
                 chord_fine_success_pose_guide_weight=0.15,
                 goal_pair_success_pose_guide_weight=0.20,
                 goal_pair_success_pose_focus_weight=0.60,
                 goal_pair_success_pose_proximal_fraction=0.20,
                 static_chord_no_press_failure_credit=0.0,
                 static_chord_no_press_completion_power=2.0,
                 press_hold_min_frames=6,
                 press_hold_full_frames=12,
                 press_dropout_penalty=0.15,
                 press_position_dense_scale=0.20,
                 press_precision_gate_floor=0.40,
                 chord_fine_position_upper=0.90,
                 chord_fine_position_dense_scale=0.30,
                 chord_fine_precision_gate_floor=0.60,
                 chord_multi_region_lower=FRET_VALID_REGION_LOWER,
                 chord_multi_region_upper=FRET_VALID_REGION_UPPER,
                 chord_multi_point_bonus_weight=0.0,
                 next_goal_weight=0.15,
                 goal_pair_transition_next_goal_weight=0.50,
                 goal_pair_context_next_goal_weight=0.35,
                 next_goal_lookahead_s=1.00,
                 next_goal_progress_weight=2.0,
                 next_goal_progress_near=0.010,
                 next_goal_progress_far=0.100,
                 next_goal_preservation_weight=0.35,
                 next_goal_unprotected_progress_scale=0.0,
                 goal_pair_transition_time_gate_floor=0.30,
                 next_goal_prepress_clearance=0.004):
        self.env = env
        self.wrist_weight = float(wrist_weight)
        self.smooth_weight = float(smooth_weight)
        self.finger_arch_reward_weight = float(finger_arch_reward_weight)
        self.fine_reach_finger_arch_reward_weight = float(
            fine_reach_finger_arch_reward_weight)
        self.isolated_press_arch_reward_weight = float(
            isolated_press_arch_reward_weight)
        self.isolated_press_conjunctive_weight = float(
            isolated_press_conjunctive_weight)
        self.thumb_weight = float(thumb_weight)
        self.thumb_overforce_penalty = float(thumb_overforce_penalty)
        self.thumb_gate_full_distance = float(thumb_gate_full_distance)
        self.thumb_gate_zero_distance = float(thumb_gate_zero_distance)
        self.thumb_press_gate_weight = float(thumb_press_gate_weight)
        self.thumb_base_saturation_threshold = float(
            thumb_base_saturation_threshold)
        self.thumb_base_saturation_penalty_weight = float(
            thumb_base_saturation_penalty_weight)
        self.thumb_base_supported_saturation_fraction = float(
            thumb_base_supported_saturation_fraction)
        self.proximal_weight = float(proximal_weight)
        self.hover_weight = float(hover_weight)
        self.hover_free_gap = float(hover_free_gap)
        self.hover_decay_scale = float(hover_decay_scale)
        self.hover_position_weight = float(hover_position_weight)
        self.hover_release_pose_weight = float(hover_release_pose_weight)
        self.hover_release_blend_time = float(hover_release_blend_time)
        self.hover_release_relaxed_pip_deg = float(
            hover_release_relaxed_pip_deg)
        self.hover_release_relaxed_dip_deg = float(
            hover_release_relaxed_dip_deg)
        self.hover_release_tolerance_deg = tuple(
            float(value) for value in hover_release_tolerance_deg)
        self.hover_free_outward_speed = float(hover_free_outward_speed)
        self.hover_speed_decay_scale = float(hover_speed_decay_scale)
        self.hover_move_release_time = float(hover_move_release_time)
        self.finger_coupling_weight = float(finger_coupling_weight)
        self.finger_coupling_coefficients = tuple(
            float(value) for value in finger_coupling_coefficients)
        self.finger_coupling_min_speed_deg = float(
            finger_coupling_min_speed_deg)
        self.finger_coupling_full_speed_deg = float(
            finger_coupling_full_speed_deg)
        self.finger_coupling_tolerance_deg_s = float(
            finger_coupling_tolerance_deg_s)
        self.reference_motion_prior_weight = float(
            reference_motion_prior_weight)
        self.reference_motion_prior_finger_fraction = float(
            reference_motion_prior_finger_fraction)
        self.human_joint_range_weight = float(human_joint_range_weight)
        self.slip_weight = float(slip_weight)
        self.slip_stable_frames = int(slip_stable_frames)
        self.slip_free_distance = float(slip_free_distance)
        self.slip_decay_scale = float(slip_decay_scale)
        self.press_class_weight = float(press_class_weight)
        self.no_press_class_weight = float(no_press_class_weight)
        self.no_press_failure_credit = float(no_press_failure_credit)
        self.static_chord_bottleneck_weight = float(
            static_chord_bottleneck_weight)
        self.chord_bridge_bottleneck_weight = float(
            chord_bridge_bottleneck_weight)
        self.chord_fine_joint_weight = float(chord_fine_joint_weight)
        self.chord_fine_depth_start = float(chord_fine_depth_start)
        self.static_chord_joint_weight = float(static_chord_joint_weight)
        self.static_chord_auxiliary_gate_floor = float(
            static_chord_auxiliary_gate_floor)
        self.static_chord_completion_gate_floor = float(
            static_chord_completion_gate_floor)
        self.static_chord_completion_gate_power = float(
            static_chord_completion_gate_power)
        self.goal_pair_rehearsal_anchor_weight = float(
            goal_pair_rehearsal_anchor_weight)
        self.chord_reach_success_pose_guide_weight = float(
            chord_reach_success_pose_guide_weight)
        self.chord_fine_success_pose_guide_weight = float(
            chord_fine_success_pose_guide_weight)
        self.goal_pair_success_pose_guide_weight = float(
            goal_pair_success_pose_guide_weight)
        self.goal_pair_success_pose_focus_weight = float(
            goal_pair_success_pose_focus_weight)
        self.goal_pair_success_pose_proximal_fraction = float(
            goal_pair_success_pose_proximal_fraction)
        self.static_chord_no_press_failure_credit = float(
            static_chord_no_press_failure_credit)
        self.static_chord_no_press_completion_power = float(
            static_chord_no_press_completion_power)
        self.press_hold_min_frames = int(press_hold_min_frames)
        self.press_hold_full_frames = int(press_hold_full_frames)
        self.press_dropout_penalty = float(press_dropout_penalty)
        self.press_near_miss_penalty = float(press_near_miss_penalty)
        self.press_near_miss_distance = float(press_near_miss_distance)
        self.press_position_dense_scale = float(press_position_dense_scale)
        self.press_precision_gate_floor = float(press_precision_gate_floor)
        self.chord_fine_position_upper = float(
            chord_fine_position_upper)
        self.chord_fine_position_dense_scale = float(
            chord_fine_position_dense_scale)
        self.chord_fine_precision_gate_floor = float(
            chord_fine_precision_gate_floor)
        self.chord_multi_region_lower = float(chord_multi_region_lower)
        self.chord_multi_region_upper = float(chord_multi_region_upper)
        self.chord_multi_point_bonus_weight = float(
            chord_multi_point_bonus_weight)
        self.next_goal_weight = float(next_goal_weight)
        self.goal_pair_transition_next_goal_weight = float(
            goal_pair_transition_next_goal_weight)
        self.goal_pair_context_next_goal_weight = float(
            goal_pair_context_next_goal_weight)
        self.next_goal_lookahead_s = float(next_goal_lookahead_s)
        self.next_goal_progress_weight = float(next_goal_progress_weight)
        self.next_goal_progress_near = float(next_goal_progress_near)
        self.next_goal_progress_far = float(next_goal_progress_far)
        self.next_goal_preservation_weight = float(
            next_goal_preservation_weight)
        self.next_goal_unprotected_progress_scale = float(
            next_goal_unprotected_progress_scale)
        self.goal_pair_transition_time_gate_floor = float(
            goal_pair_transition_time_gate_floor)
        self.next_goal_prepress_clearance = float(
            next_goal_prepress_clearance)
        if self.proximal_weight < 0.0:
            raise ValueError("proximal_weight must be non-negative")
        if not 0.0 <= self.finger_arch_reward_weight < 1.0:
            raise ValueError("finger arch reward weight must be in [0, 1)")
        if not 0.0 <= self.fine_reach_finger_arch_reward_weight < 1.0:
            raise ValueError(
                "fine-reach finger arch reward weight must be in [0, 1)")
        if not 0.0 <= self.isolated_press_arch_reward_weight < 1.0:
            raise ValueError(
                "isolated-press arch reward weight must be in [0, 1)")
        if self.isolated_press_arch_reward_weight + self.thumb_weight >= 1.0:
            raise ValueError(
                "isolated-press arch and thumb weights must sum below 1")
        if not 0.0 <= self.isolated_press_conjunctive_weight <= 1.0:
            raise ValueError(
                "isolated-press conjunctive weight must be in [0, 1]")
        if self.thumb_overforce_penalty < 0.0:
            raise ValueError("thumb overforce penalty must be non-negative")
        if not 0.0 <= self.thumb_gate_full_distance < self.thumb_gate_zero_distance:
            raise ValueError("thumb gate distances must satisfy 0 <= full < zero")
        if not 0.0 <= self.thumb_press_gate_weight < 1.0:
            raise ValueError("thumb press gate weight must be in [0,1)")
        if (not math.isfinite(self.thumb_base_saturation_threshold)
                or not 0.0 <= self.thumb_base_saturation_threshold < 1.0):
            raise ValueError(
                "thumb base saturation threshold must be in [0,1)")
        if (not math.isfinite(self.thumb_base_saturation_penalty_weight)
                or self.thumb_base_saturation_penalty_weight < 0.0):
            raise ValueError(
                "thumb base saturation penalty weight must be non-negative")
        supported_fraction = self.thumb_base_supported_saturation_fraction
        if (not math.isfinite(supported_fraction)
                or not 0.0 <= supported_fraction <= 1.0):
            raise ValueError(
                "supported thumb saturation fraction must be in [0,1]")
        if self.hover_weight < 0.0:
            raise ValueError("hover_weight must be non-negative")
        if self.hover_free_gap < 0.0 or self.hover_decay_scale <= 0.0:
            raise ValueError("hover free gap/decay scale must be non-negative/positive")
        if (self.hover_position_weight < 0.0
                or self.hover_release_pose_weight < 0.0
                or self.hover_position_weight
                + self.hover_release_pose_weight > 1.0):
            raise ValueError("hover position/release-pose weights must sum to <= 1")
        if self.hover_release_blend_time <= 0.0:
            raise ValueError("hover release blend time must be positive")
        if (len(self.hover_release_tolerance_deg) != 3
                or any(value <= 0.0
                       for value in self.hover_release_tolerance_deg)):
            raise ValueError("hover release tolerance must contain 3 positive angles")
        if (self.hover_free_outward_speed < 0.0
                or self.hover_speed_decay_scale <= 0.0
                or self.hover_move_release_time < 0.0):
            raise ValueError("hover speed/time parameters are invalid")
        if not 0.0 <= self.finger_coupling_weight < 1.0:
            raise ValueError("finger coupling weight must be in [0, 1)")
        if not 0.0 <= self.reference_motion_prior_weight < 1.0:
            raise ValueError("reference motion prior weight must be in [0, 1)")
        if not 0.0 <= self.reference_motion_prior_finger_fraction <= 1.0:
            raise ValueError(
                "reference motion finger fraction must be in [0, 1]")
        if self.reference_motion_prior_weight > 0.0:
            if reference_motion_prior_path is None:
                raise ValueError(
                    "reference motion path is required when its prior is enabled")
            self.reference_posture_prior = ReferenceHandPosturePrior(
                env, reference_motion_prior_path,
                max_exemplars=reference_motion_prior_exemplars)
        else:
            self.reference_posture_prior = None
        if not 0.0 <= self.human_joint_range_weight < 1.0:
            raise ValueError("human joint range weight must be in [0, 1)")
        if self.human_joint_range_weight > 0.0:
            if human_joint_range_path is None:
                raise ValueError(
                    "human joint range path is required when enabled")
            self.human_joint_range_prior = HumanJointRangePrior(
                env, human_joint_range_path,
                decay_scale_deg=human_joint_range_decay_deg,
                active_finger_fraction=
                    human_joint_range_active_finger_fraction,
                thumb_fraction=human_joint_range_thumb_fraction)
        else:
            self.human_joint_range_prior = None
        if self.slip_weight < 0.0 or self.slip_stable_frames < 1:
            raise ValueError("slip weight must be non-negative and stable frames >= 1")
        if self.slip_free_distance < 0.0 or self.slip_decay_scale <= 0.0:
            raise ValueError("slip free distance/decay scale must be non-negative/positive")
        if (self.press_class_weight < 0.0
                or self.no_press_class_weight < 0.0
                or abs(self.press_class_weight
                       + self.no_press_class_weight - 1.0) > 1e-6):
            raise ValueError("PRESS/NO_PRESS class weights must sum to 1")
        if not 0.0 <= self.no_press_failure_credit <= self.no_press_class_weight:
            raise ValueError("NO_PRESS failure credit must be in [0, no_press weight]")
        if not 0.0 <= self.static_chord_bottleneck_weight <= 1.0:
            raise ValueError("static chord bottleneck weight must be in [0, 1]")
        if not 0.0 <= self.chord_bridge_bottleneck_weight <= 1.0:
            raise ValueError("chord bridge bottleneck weight must be in [0, 1]")
        if not 0.0 <= self.chord_fine_joint_weight < 1.0:
            raise ValueError("chord-fine joint weight must be in [0, 1)")
        if (not math.isfinite(self.chord_fine_depth_start)
                or self.chord_fine_depth_start >= self.PRESS_ON_DEPTH):
            raise ValueError(
                "chord-fine depth start must precede press depth")
        if not 0.0 <= self.static_chord_joint_weight < 1.0:
            raise ValueError("static chord joint weight must be in [0, 1)")
        if not 0.0 <= self.static_chord_auxiliary_gate_floor <= 1.0:
            raise ValueError(
                "static chord auxiliary gate floor must be in [0, 1]")
        if not 0.0 <= self.static_chord_completion_gate_floor <= 1.0:
            raise ValueError(
                "static chord completion gate floor must be in [0, 1]")
        if self.static_chord_completion_gate_power <= 0.0:
            raise ValueError(
                "static chord completion gate power must be positive")
        if not 0.0 <= self.goal_pair_rehearsal_anchor_weight < 1.0:
            raise ValueError(
                "goal-pair rehearsal anchor weight must be in [0, 1)")
        if not 0.0 <= self.chord_reach_success_pose_guide_weight < 1.0:
            raise ValueError(
                "chord-reach success pose guide weight must be in [0, 1)")
        if not 0.0 <= self.chord_fine_success_pose_guide_weight < 1.0:
            raise ValueError(
                "chord-fine success-pose guide weight must be in [0, 1)")
        if not 0.0 <= self.goal_pair_success_pose_guide_weight < 1.0:
            raise ValueError(
                "goal-pair success-pose guide weight must be in [0, 1)")
        if not 0.0 <= self.goal_pair_success_pose_focus_weight < 1.0:
            raise ValueError(
                "goal-pair success-pose focus weight must be in [0, 1)")
        if not 0.0 <= self.goal_pair_success_pose_proximal_fraction <= 1.0:
            raise ValueError(
                "goal-pair success-pose proximal fraction must be in [0, 1]")
        if not (0.0 <= self.static_chord_no_press_failure_credit
                <= self.no_press_class_weight):
            raise ValueError(
                "static chord NO_PRESS credit must be in [0, no_press weight]")
        if self.static_chord_no_press_completion_power <= 0.0:
            raise ValueError(
                "static chord NO_PRESS completion power must be positive")
        if (self.press_hold_min_frames < 1
                or self.press_hold_full_frames < self.press_hold_min_frames):
            raise ValueError("press hold frames must satisfy 1 <= min <= full")
        if (not math.isfinite(self.press_dropout_penalty)
                or self.press_dropout_penalty < 0.0):
            raise ValueError(
                "press dropout penalty must be finite and non-negative")
        if (not math.isfinite(self.press_near_miss_penalty)
                or self.press_near_miss_penalty < 0.0
                or not math.isfinite(self.press_near_miss_distance)
                or self.press_near_miss_distance <= 0.0):
            raise ValueError(
                "near-miss penalty/distance must be finite and valid")
        if self.press_position_dense_scale <= 0.0:
            raise ValueError("press position dense scale must be positive")
        if not 0.0 <= self.press_precision_gate_floor <= 1.0:
            raise ValueError("press precision gate floor must be in [0, 1]")
        if not self.APPROACH_X < self.chord_fine_position_upper <= 1.0:
            raise ValueError(
                "chord-fine position upper must be above the 20% optimum")
        if self.chord_fine_position_dense_scale <= 0.0:
            raise ValueError(
                "chord-fine position dense scale must be positive")
        if not 0.0 <= self.chord_fine_precision_gate_floor <= 1.0:
            raise ValueError(
                "chord-fine precision gate floor must be in [0, 1]")
        if not (0.0 <= self.chord_multi_region_lower
                < self.chord_multi_region_upper <= 1.0):
            raise ValueError("multi-press fret region is invalid")
        if not 0.0 <= self.chord_multi_point_bonus_weight <= 0.20:
            raise ValueError("multi-press point bonus must be in [0, 0.20]")
        if (self.next_goal_weight < 0.0
                or self.next_goal_lookahead_s <= 0.0
                or self.next_goal_lookahead_s
                    >= FINGER_EVENT_TIME_SCALE_S
                or self.next_goal_progress_weight < 0.0
                or not 0.0 <= self.next_goal_progress_near
                    < self.next_goal_progress_far
                or self.next_goal_prepress_clearance < 0.0):
            raise ValueError(
                "next-goal lookahead must be shorter than the encoded "
                "time range and all shaping parameters must be valid")
        if not 0.0 <= self.next_goal_preservation_weight < 1.0:
            raise ValueError(
                "next-goal preservation weight must be in [0, 1)")
        if (not 0.0 <= self.goal_pair_transition_next_goal_weight < 1.0
                or not 0.0 <= self.goal_pair_context_next_goal_weight < 1.0
                or not 0.0
                    <= self.next_goal_unprotected_progress_scale <= 1.0
                or not 0.0
                    <= self.goal_pair_transition_time_gate_floor <= 1.0):
            raise ValueError(
                "goal-pair transition shaping weights are invalid")
        self.task_weight = (1.0 - self.wrist_weight - self.smooth_weight
                            - self.thumb_weight
                            - self.hover_weight - self.slip_weight)
        if self.task_weight <= 0:
            raise ValueError("auxiliary fret reward weights must sum to < 1")
        self.wrong_press_penalty = float(wrong_press_penalty)
        self.wrong_press_avoidance_weight = float(wrong_press_avoidance_weight)
        if (not math.isfinite(self.wrong_press_penalty)
                or self.wrong_press_penalty < 0.0):
            raise ValueError(
                "wrong_press_penalty must be finite and non-negative")
        if not 0.0 <= self.wrong_press_avoidance_weight < 1.0:
            raise ValueError("wrong_press_avoidance_weight must be in [0, 1)")

        required = ["L_Wrist"]
        for finger in FINGER_NAMES:
            required += [f"LH:{finger}1", f"LH:{finger}2", f"LH:{finger}3",
                         f"LH:{finger}_top"]
        missing = [x for x in required if x not in env.hbody_index]
        if missing:
            raise KeyError(f"missing humanoid reward bodies: {missing}")
        required_guitar = (["G:nut"]
                           + [f"G:fret{i}" for i in range(1, 23)]
                           + [f"G:string{i}" for i in range(1, 7)]
                           + [f"G:string{i}_end" for i in range(1, 7)])
        missing = [x for x in required_guitar if x not in env.gbody_index]
        if missing:
            raise KeyError(f"missing guitar reward bodies: {missing}")

        arch_names = [[f"LH:{finger}1_x", f"LH:{finger}2", f"LH:{finger}3"]
                      for finger in FINGER_NAMES]
        missing_arch = [name for row in arch_names for name in row
                        if name not in env.dof_names]
        if missing_arch:
            raise KeyError(f"missing finger arch DOFs: {missing_arch}")
        self._arch_dof_indices = torch.tensor(
            [[env.dof_names.index(name) for name in row] for row in arch_names],
            dtype=torch.long, device=env.device)

        self.prev_wrist = torch.zeros(env.num_envs, 3, device=env.device)
        self.prev_tips = torch.zeros(env.num_envs, 4, 3, device=env.device)
        self._have_previous = torch.zeros(env.num_envs, dtype=torch.bool, device=env.device)
        self._had_successful_press = torch.zeros(
            env.num_envs, 4, dtype=torch.bool, device=env.device)
        self._previous_hover_gap = torch.zeros(
            env.num_envs, 4, device=env.device)
        self._previous_hover_valid = torch.zeros(
            env.num_envs, 4, dtype=torch.bool, device=env.device)
        self._release_arch_anchor = torch.zeros(
            env.num_envs, 4, 3, device=env.device)
        self._release_arch_valid = torch.zeros(
            env.num_envs, 4, dtype=torch.bool, device=env.device)
        self._release_age = torch.zeros(
            env.num_envs, 4, device=env.device)
        self._previous_approach_distance = torch.zeros(
            env.num_envs, 6, device=env.device)
        self._previous_approach_valid = torch.zeros(
            env.num_envs, 6, dtype=torch.bool, device=env.device)
        self._previous_next_goal_potential = torch.zeros(
            env.num_envs, 4, device=env.device)
        self._previous_next_goal_valid = torch.zeros(
            env.num_envs, 4, dtype=torch.bool, device=env.device)
        self._previous_next_goal_fret = torch.zeros(
            env.num_envs, 4, dtype=torch.long, device=env.device)
        self._previous_next_goal_string_mask = torch.zeros(
            env.num_envs, 4, 6, dtype=torch.bool, device=env.device)
        self._curriculum_success_streak = torch.zeros(
            env.num_envs, dtype=torch.long, device=env.device)
        self._curriculum_episode_success = torch.zeros(
            env.num_envs, dtype=torch.bool, device=env.device)
        self._press_hold_streak = torch.zeros(
            env.num_envs, 6, dtype=torch.long, device=env.device)
        self._press_hold_acquired = torch.zeros(
            env.num_envs, 6, dtype=torch.bool, device=env.device)
        self._press_dropout_streak = torch.zeros(
            env.num_envs, 6, dtype=torch.long, device=env.device)
        self._press_hold_previous_fret = torch.zeros(
            env.num_envs, 6, dtype=torch.long, device=env.device)
        self._press_hold_previous_finger = torch.zeros(
            env.num_envs, 6, dtype=torch.long, device=env.device)
        self._thumb_support_streak = torch.zeros(
            env.num_envs, dtype=torch.long, device=env.device)
        self._slip_streak = torch.zeros(
            env.num_envs, 4, dtype=torch.long, device=env.device)
        self._slip_anchor_xy = torch.zeros(
            env.num_envs, 4, 2, device=env.device)
        self._slip_anchor_valid = torch.zeros(
            env.num_envs, 4, dtype=torch.bool, device=env.device)
        self._slip_previous_xy = torch.zeros(
            env.num_envs, 4, 2, device=env.device)
        self._slip_previous_valid = torch.zeros(
            env.num_envs, 4, dtype=torch.bool, device=env.device)
        self._slip_previous_mask = torch.zeros(
            env.num_envs, 4, 6, dtype=torch.bool, device=env.device)
        self._slip_previous_fret = torch.zeros(
            env.num_envs, 4, dtype=torch.long, device=env.device)
        # 환경·줄·손가락·프렛별 압현 상태다.
        shape = (env.num_envs, 6, 4, 22)
        self._press_distal = torch.zeros(shape, dtype=torch.bool, device=env.device)
        self._press_anyseg = torch.zeros(shape, dtype=torch.bool, device=env.device)
        self._sample_alpha = torch.linspace(0.0, 1.0, self.N_SEGMENT_SAMPLES,
                                            device=env.device).view(1, 1, 1, -1, 1)
        self.thumb_reward = ThumbSupportReward(
            env, pad_radius=thumb_pad_radius, approach_scale=thumb_approach_scale,
            reach_scale=thumb_reach_scale,
            contact_on_force=thumb_contact_on_force,
            contact_off_force=thumb_contact_off_force,
            force_soft_limit=thumb_force_soft_limit,
            force_decay_scale=thumb_force_decay_scale,
            compression_free_depth=thumb_compression_free_depth,
            compression_decay_scale=thumb_compression_decay_scale)
        self.proximal_reward = ProximalMotionReward(
            env, transition=proximal_transition)
        self.pressed_drag_monitor = PressedDragMonitor(
            env.num_envs, env.device, threshold=pressed_drag_threshold)

    def reset(self, env_ids):
        if env_ids.numel() == 0:
            return
        reset_tensors = (
            self._have_previous, self._press_distal, self._press_anyseg,
            self._had_successful_press, self._previous_hover_gap,
            self._previous_hover_valid, self._release_arch_anchor,
            self._release_arch_valid, self._release_age,
            self._previous_approach_distance, self._previous_approach_valid,
            self._previous_next_goal_potential,
            self._previous_next_goal_valid, self._previous_next_goal_fret,
            self._previous_next_goal_string_mask,
            self._curriculum_success_streak,
            self._curriculum_episode_success, self._press_hold_streak,
            self._press_hold_acquired, self._press_dropout_streak,
            self._press_hold_previous_fret, self._press_hold_previous_finger,
            self._thumb_support_streak, self._slip_streak,
            self._slip_anchor_xy, self._slip_anchor_valid,
            self._slip_previous_xy, self._slip_previous_valid,
            self._slip_previous_mask, self._slip_previous_fret,
        )
        for tensor in reset_tensors:
            tensor[env_ids] = 0
        self.thumb_reward.reset(env_ids)
        self.pressed_drag_monitor.reset(env_ids)

    def _finger_points(self):
        points = []
        for finger in FINGER_NAMES:
            points.append(torch.stack([
                self.env.hbody_pos(f"LH:{finger}1"),
                self.env.hbody_pos(f"LH:{finger}2"),
                self.env.hbody_pos(f"LH:{finger}3"),
                self.env.hbody_pos(f"LH:{finger}_top"),
            ], dim=1))
        return torch.stack(points, dim=1)

    @staticmethod
    def _select_finger_samples(values, finger_index):
        index = finger_index[:, :, None, None, None].expand(
            -1, -1, 1, values.shape[3], values.shape[4])
        return torch.gather(values, 2, index).squeeze(2)

    def _allowed_samples(self, reference, barre):
        allowed = torch.zeros_like(reference, dtype=torch.bool)
        allowed[:, :, 2, self._tip_samples] = True
        return allowed | barre[:, :, None, None]

    @property
    def _tip_samples(self):
        return self._sample_alpha.flatten() >= self.TIP_SAMPLE_MIN_ALPHA

    def _string_and_fret_geometry(self):
        p0 = torch.stack([self.env.gbody_pos(f"G:string{k}") for k in range(1, 7)], dim=1)
        p1 = torch.stack([self.env.gbody_pos(f"G:string{k}_end") for k in range(1, 7)], dim=1)
        direction = p1 - p0
        direction = direction / direction.norm(dim=-1, keepdim=True).clamp_min(1e-8)

        wires = torch.stack([self.env.gbody_pos("G:nut")]
                            + [self.env.gbody_pos(f"G:fret{k}") for k in range(1, 23)], dim=1)
        wire_center = ((wires[:, None] - p0[:, :, None])
                       * direction[:, :, None]).sum(-1)
        previous_half = torch.full((23,), self.FRET_HALF_WIDTH, device=self.env.device)
        previous_half[0] = self.NUT_HALF_WIDTH
        cell_lo = wire_center[:, :, :-1] + previous_half[:-1].view(1, 1, 22)
        cell_hi = wire_center[:, :, 1:] - self.FRET_HALF_WIDTH
        usable = (cell_hi - cell_lo).clamp_min(1e-5)
        approach_along = cell_hi - self.APPROACH_X * usable
        approach = p0[:, :, None] + direction[:, :, None] * approach_along[..., None]

        # 기타 로컬 +z를 각 현에 수직인 바깥 방향으로 보정한다.
        _, guitar_quat = self.env.guitar_frame()
        local_z = torch.zeros(self.env.num_envs, 3, device=self.env.device)
        local_z[:, 2] = 1.0
        outward = quat_rotate(guitar_quat, local_z)[:, None]
        outward = outward - (outward * direction).sum(-1, keepdim=True) * direction
        outward = outward / outward.norm(dim=-1, keepdim=True).clamp_min(1e-8)
        return p0, p1, direction, cell_lo, cell_hi, approach, outward

    def _actual_press_states(self, samples, p0, direction, cell_lo, cell_hi, outward):
        axis = samples[:, None]
        base = p0[:, :, None, None, None]
        string_dir = direction[:, :, None, None, None]
        along = ((axis - base) * string_dir).sum(-1)
        string_point = base + along[..., None] * string_dir
        delta = axis - string_point
        normal = outward[:, :, None, None, None]
        depth, lateral_ok = cylindrical_pad_depth(delta, normal, self.PAD_RADIUS)

        in_cell = ((along[..., None] >= cell_lo[:, :, None, None, None])
                   & (along[..., None] <= cell_hi[:, :, None, None, None]))
        valid_depth = lateral_ok[..., None] & in_cell
        depth_by_fret = depth[..., None].masked_fill(
            ~valid_depth, -float("inf"))
        distal_depth = depth_by_fret[
            :, :, :, 2, self._tip_samples].amax(dim=3)
        any_depth = depth_by_fret.amax(dim=(3, 4))
        self._press_distal = update_press_hysteresis(
            self._press_distal, distal_depth,
            self.PRESS_ON_DEPTH, self.PRESS_OFF_DEPTH)
        self._press_anyseg = update_press_hysteresis(
            self._press_anyseg, any_depth,
            self.PRESS_ON_DEPTH, self.PRESS_OFF_DEPTH)

        max_depth_by_fret = depth_by_fret.amax(dim=(2, 3, 4))
        max_depth_by_fret = torch.where(
            torch.isfinite(max_depth_by_fret), max_depth_by_fret,
            torch.full_like(max_depth_by_fret, -self.PAD_RADIUS))
        # Side-effect-free Fret-v2 observation queries remap this complete
        # physical snapshot to the *next* goal after the song clock advances.
        # Keeping the finger axis avoids falsely crediting a different finger
        # that happens to press the requested string/fret cell.
        depth_by_finger_fret = depth_by_fret.amax(dim=(3, 4))
        self._latest_depth_by_finger_fret = torch.where(
            torch.isfinite(depth_by_finger_fret), depth_by_finger_fret,
            torch.full_like(depth_by_finger_fret, -self.PAD_RADIUS))
        return along, depth, lateral_ok, max_depth_by_fret

    def active_press_cells(self):
        """Return the current goal-independent ``[N,6,22]`` press snapshot.

        A cell is active when any non-thumb playing finger geometrically
        depresses that virtual string/fret cell under the existing hysteresis
        detector.  Standalone Fret rewards still evaluate designated-finger
        adherence; the Full Synchronizer deliberately collapses the finger
        axis and derives musical sounding fret separately.
        """
        return self._press_anyseg.any(dim=2)

    def refresh_press_state(self):
        """Refresh the goal-independent physical press snapshot once.

        FullG0 uses this post-physics hook without advancing standalone reward,
        sustain, or success trackers.  Calling it more than once for the same
        physical frame is harmless for the hysteresis values, but the shared
        task owns the once-per-frame scheduling contract.
        """
        p0, _p1, direction, cell_lo, cell_hi, _approach, outward = (
            self._string_and_fret_geometry())
        points = self._finger_points()
        starts, ends = points[:, :, :-1], points[:, :, 1:]
        samples = (
            starts[:, :, :, None]
            + self._sample_alpha * (ends - starts)[:, :, :, None])
        self._actual_press_states(
            samples, p0, direction, cell_lo, cell_hi, outward)
        return self.active_press_cells()

    def observe_fret_v2_state(self, goal):
        """Measure current Fret geometry/contact without advancing trackers.

        ``compute`` updates the all-cell contact hysteresis before the goal
        clock advances.  This method then remaps those goal-independent contact
        tensors to the new current goal and recomputes goal-relative geometry.
        It must remain free of latch/streak mutations because actor observation
        construction may run more than once for a physics snapshot.
        """
        n = self.env.num_envs
        fret = goal["fret"]
        finger = goal["finger"]
        barre = goal["barre"]
        active = fret > 0
        no_press = fret < 0
        fret_index = fret.long().clamp(1, 22) - 1
        finger_index = finger.long().clamp(1, 4) - 1

        p0, _p1, direction, cell_lo, cell_hi, all_approach, outward = \
            self._string_and_fret_geometry()
        target = torch.gather(
            all_approach, 2,
            fret_index[..., None, None].expand(-1, -1, 1, 3)
        ).squeeze(2)
        goal_lo = torch.gather(
            cell_lo, 2, fret_index[..., None]).squeeze(-1)
        goal_hi = torch.gather(
            cell_hi, 2, fret_index[..., None]).squeeze(-1)
        goal_usable = (goal_hi - goal_lo).clamp_min(1e-5)
        target_fraction = chord_aware_target_fraction(
            fret, active, target, goal_usable,
            optimal=self.APPROACH_X,
            fingertip_clearance=self.FINGERTIP_TARGET_CLEARANCE)
        target_along = goal_hi - target_fraction * goal_usable
        target = p0 + direction * target_along[..., None]

        points = self._finger_points()
        starts, ends = points[:, :, :-1], points[:, :, 1:]
        samples = (
            starts[:, :, :, None]
            + self._sample_alpha * (ends - starts)[:, :, :, None])
        approach_distance = self._approach_distance(
            samples, target, outward, finger_index, barre)
        fine = self._fine_alignment_metrics(
            samples, target, direction, outward, finger_index, barre,
            press_compatible=True)
        region = fret_region_alignment(
            fine["fine_signed_longitudinal_error"],
            fine["fine_lateral_error"],
            fine["fine_normal_error"],
            target_fraction, goal_usable,
            lower=self.chord_multi_region_lower,
            upper=self.chord_multi_region_upper)

        env_index = torch.arange(
            n, device=self.env.device)[:, None].expand(n, 6)
        string_index = torch.arange(
            6, device=self.env.device)[None].expand(n, 6)
        distal = self._press_distal[
            env_index, string_index, finger_index, fret_index]
        any_segment = self._press_anyseg[
            env_index, string_index, finger_index, fret_index]
        designated_pressed = torch.where(barre, any_segment, distal)
        pressed_by_fret = self._press_anyseg.any(dim=2)
        _, no_press_required, _ = fret_requirement_masks(fret, max_fret=22)
        wrong_press = wrong_press_mask(pressed_by_fret, no_press_required)

        if hasattr(self, "_latest_depth_by_finger_fret"):
            depth = self._latest_depth_by_finger_fret[
                env_index, string_index, finger_index, fret_index]
        else:
            depth = torch.full_like(fret, -self.PAD_RADIUS)
        depth_quality = (
            (depth - self.PRESS_OFF_DEPTH)
            / (self.PRESS_ON_DEPTH - self.PRESS_OFF_DEPTH)
        ).clamp(0.0, 1.0)
        alignment_quality = region["alignment_quality"]
        press_quality = (
            depth_quality * alignment_quality * active.float())
        ready = (
            active & designated_pressed & ~wrong_press
            & region["inside"] & (alignment_quality >= 0.80))
        return {
            "active": active,
            "no_press": no_press,
            "target_world": target,
            "approach_distance": approach_distance,
            "signed_press_depth": depth,
            "lateral_error": fine["fine_lateral_error"],
            "target_region_inside": region["inside"],
            "press_quality": press_quality,
            "ready": ready,
            "wrong_press": wrong_press,
        }

    def _approach_distance(self, samples, target, outward, finger_index, barre):
        delta = samples[:, None] - target[:, :, None, None, None]
        normal = outward[:, :, None, None, None]
        # 손끝 패드가 현 안쪽을 지나면 접근 거리는 0으로 유지한다.
        distance = one_sided_pad_distance(delta, normal, self.PAD_RADIUS)

        designated = self._select_finger_samples(distance, finger_index)
        segment_allowed = self._allowed_samples(designated, barre)
        return designated.masked_fill(~segment_allowed, float("inf")).flatten(2).min(-1).values

    def _fine_alignment_metrics(self, samples, target, direction, outward,
                                finger_index, barre,
                                press_compatible=False):
        delta = samples[:, None] - target[:, :, None, None, None]
        string_dir = direction[:, :, None, None, None]
        normal = outward[:, :, None, None, None]
        longitudinal = (delta * string_dir).sum(-1)
        normal_offset = (delta * normal).sum(-1)
        lateral_vec = delta - longitudinal[..., None] * string_dir \
            - normal_offset[..., None] * normal
        lateral = lateral_vec.norm(dim=-1)
        if press_compatible:
            maximum_offset = self.PAD_RADIUS - self.PRESS_ON_DEPTH
            normal_error = (normal_offset - maximum_offset).clamp_min(0.0)
        else:
            normal_error = (normal_offset - (
                self.PAD_RADIUS + self.FINE_NORMAL_CLEARANCE)).abs()

        signed_longitudinal = self._select_finger_samples(
            longitudinal, finger_index)
        longitudinal = signed_longitudinal.abs()
        lateral = self._select_finger_samples(lateral, finger_index)
        normal_error = self._select_finger_samples(normal_error, finger_index)

        allowed = self._allowed_samples(longitudinal, barre)
        longitudinal_quality = torch.exp(-((longitudinal / 0.008) ** 2))
        lateral_quality = torch.exp(-((lateral / 0.004) ** 2))
        normal_quality = torch.exp(-((normal_error / 0.006) ** 2))
        quality = (
            longitudinal_quality
            + lateral_quality
            + normal_quality) / 3.0
        flat_quality = quality.masked_fill(~allowed, -float("inf")).flatten(2)
        best_quality, best_index = flat_quality.max(dim=-1)

        def select(value):
            return torch.gather(
                value.flatten(2), 2, best_index[..., None]).squeeze(-1)

        center_distance = torch.sqrt(
            select(longitudinal).square() + select(lateral).square()
            + select(normal_error).square() + 1e-12)
        return {
            "fine_alignment_quality": best_quality.clamp(0.0, 1.0),
            "fine_longitudinal_quality": select(longitudinal_quality),
            "fine_lateral_quality": select(lateral_quality),
            "fine_normal_quality": select(normal_quality),
            "fine_center_distance": center_distance,
            "fine_signed_longitudinal_error": select(signed_longitudinal),
            "fine_lateral_error": select(lateral),
            "fine_normal_error": select(normal_error),
        }

    def _goal_contact_metrics(self, along, depth, lateral_ok, cell_lo, cell_hi,
                              finger_index, fret_index, barre):
        along = self._select_finger_samples(along, finger_index)
        depth = self._select_finger_samples(depth, finger_index)
        lateral_ok = self._select_finger_samples(lateral_ok, finger_index)

        gather_fret = fret_index[..., None]
        lo = torch.gather(cell_lo, 2, gather_fret).squeeze(-1)
        hi = torch.gather(cell_hi, 2, gather_fret).squeeze(-1)
        usable = (hi - lo).clamp_min(1e-5)
        x = (hi[:, :, None, None] - along) / usable[:, :, None, None]
        in_cell = (x >= 0.0) & (x <= 1.0)
        segment_allowed = self._allowed_samples(in_cell, barre)
        valid = in_cell & lateral_ok & segment_allowed
        candidate_depth = depth.masked_fill(~valid, -float("inf")).flatten(2)
        best_depth, best_index = candidate_depth.max(-1)
        best_x = torch.gather(x.flatten(2), 2, best_index[..., None]).squeeze(-1)
        best_x = torch.where(torch.isfinite(best_depth), best_x, torch.ones_like(best_x))
        best_depth = torch.where(torch.isfinite(best_depth), best_depth,
                                 torch.full_like(best_depth, -self.PAD_RADIUS))
        return best_x, best_depth

    def compute(self, goal):
        n = self.env.num_envs
        stage = getattr(self.env, "curriculum_stage", "full_song")
        fret = goal["fret"]
        finger = goal["finger"]
        barre = goal["barre"]
        press_mask = fret > 0
        no_press_mask = fret < 0
        supervised_mask = fret != 0
        fret_index = fret.long().clamp(1, 22) - 1
        finger_index = finger.long().clamp(1, 4) - 1

        dof_state = self.env.dof_state.view(n, self.env.n_dof, 2)
        q = dof_state[:, :, 0]
        arch_angles = q[:, self._arch_dof_indices]
        arch_velocity = dof_state[:, self._arch_dof_indices, 1]
        arch_per_finger = finger_arch_quality(
            arch_angles[..., 0], arch_angles[..., 1], arch_angles[..., 2])
        designated_arch = torch.gather(
            arch_per_finger, 1, finger_index).clamp(0.0, 1.0)
        designated_arch_angles = torch.gather(
            arch_angles, 1,
            finger_index[..., None].expand(-1, -1, 3))

        p0, p1, direction, cell_lo, cell_hi, all_approach, outward = \
            self._string_and_fret_geometry()
        points = self._finger_points()
        starts, ends = points[:, :, :-1], points[:, :, 1:]
        samples = (
            starts[:, :, :, None]
            + self._sample_alpha * (ends - starts)[:, :, :, None])
        along, depth, lateral_ok, max_depth_by_fret = self._actual_press_states(
            samples, p0, direction, cell_lo, cell_hi, outward)

        target = torch.gather(
            all_approach, 2,
            fret_index[..., None, None].expand(-1, -1, 1, 3)
        ).squeeze(2)
        goal_lo = torch.gather(
            cell_lo, 2, fret_index[..., None]).squeeze(-1)
        goal_hi = torch.gather(
            cell_hi, 2, fret_index[..., None]).squeeze(-1)
        goal_usable = (goal_hi - goal_lo).clamp_min(1e-5)
        target_fraction = chord_aware_target_fraction(
            fret, press_mask, target, goal_usable,
            optimal=self.APPROACH_X,
            fingertip_clearance=self.FINGERTIP_TARGET_CLEARANCE)
        target_along = goal_hi - target_fraction * goal_usable
        target = p0 + direction * target_along[..., None]
        finger_chain_length = (
            points[:, :, 1:] - points[:, :, :-1]).norm(dim=-1).sum(dim=-1)
        designated_mcp = torch.gather(
            points[:, :, 0], 1,
            finger_index[..., None].expand(-1, -1, 3))
        designated_chain_length = torch.gather(
            finger_chain_length, 1, finger_index)
        local_reach_margin = (
            designated_chain_length
            - (target - designated_mcp).norm(dim=-1))
        target_min_separation = minimum_active_target_separation(
            target, press_mask)
        target_clearance_ok = (
            (press_mask.sum(dim=1) < 2)
            | (target_min_separation
               >= self.FINGERTIP_TARGET_CLEARANCE - 1e-4))
        approach_distance = self._approach_distance(
            samples, target, outward, finger_index, barre)
        press_compatible_alignment = uses_press_compatible_alignment(stage)
        fine_metrics = self._fine_alignment_metrics(
            samples, target, direction, outward, finger_index, barre,
            press_compatible=press_compatible_alignment)
        region_metrics = fret_region_alignment(
            fine_metrics["fine_signed_longitudinal_error"],
            fine_metrics["fine_lateral_error"],
            fine_metrics["fine_normal_error"],
            target_fraction, goal_usable,
            lower=self.chord_multi_region_lower,
            upper=self.chord_multi_region_upper)
        multi_press = press_mask.sum(dim=1) >= 2
        # Once contact is part of the task, every single- and multi-finger
        # press uses the same uniform 10--90% cell region.  Point alignment is
        # retained only by the preceding reach stages.
        use_region = press_mask & press_compatible_alignment
        effective_fine_distance = torch.where(
            use_region, region_metrics["distance"],
            fine_metrics["fine_center_distance"])
        effective_longitudinal_quality = torch.where(
            use_region, region_metrics["longitudinal_quality"],
            fine_metrics["fine_longitudinal_quality"])
        effective_alignment_quality = torch.where(
            use_region, region_metrics["alignment_quality"],
            fine_metrics["fine_alignment_quality"])
        curriculum_distance = (
            effective_fine_distance
            if stage in ("fine_reach", "chord_fine_reach")
            else approach_distance)
        distance_reward = multi_scale_approach_reward(approach_distance)
        linear_distance_reward = linear_approach_reward(approach_distance)
        fine_distance_reward = fine_alignment_distance_reward(
            effective_fine_distance)
        approach_progress = approach_progress_reward(
            self._previous_approach_distance, curriculum_distance,
            self._previous_approach_valid & press_mask)
        self._previous_approach_distance.copy_(curriculum_distance)
        self._previous_approach_valid.copy_(press_mask)

        env_index = torch.arange(
            n, device=self.env.device)[:, None].expand(n, 6)
        string_index = torch.arange(
            6, device=self.env.device)[None].expand(n, 6)
        designated_distal = self._press_distal[
            env_index, string_index, finger_index, fret_index]
        designated_anyseg = self._press_anyseg[
            env_index, string_index, finger_index, fret_index]
        designated_pressed = torch.where(barre, designated_anyseg, designated_distal)

        pressed_by_fret = self._press_anyseg.any(dim=2)
        _, no_press_required, _ = fret_requirement_masks(fret, max_fret=22)
        wrong_press = wrong_press_mask(pressed_by_fret, no_press_required)
        wrong_press_per_finger = wrong_press_finger_mask(
            self._press_anyseg, no_press_required)
        physical_press = designated_pressed & ~wrong_press & press_mask
        finger_numbers = torch.arange(
            1, 5, device=self.env.device).view(1, 1, 4)
        finger_assignment = finger.long()[..., None] == finger_numbers
        current_finger_active = (
            press_mask[..., None] & finger_assignment).any(dim=1)

        position_x, press_depth = self._goal_contact_metrics(
            along, depth, lateral_ok, cell_lo, cell_hi,
            finger_index, fret_index, barre)
        chord_fine_position_relaxed = stage == "chord_fine_reach"
        position_quality = fret_position_quality(
            position_x,
            lower=self.chord_multi_region_lower,
            upper=self.chord_multi_region_upper)
        position_inside = fret_position_inside(
            position_x,
            lower=self.chord_multi_region_lower,
            upper=self.chord_multi_region_upper)
        # A physical string depression outside the 10--90% margin remains a
        # useful diagnostic, but it is not a correct musical press.
        press_success = physical_press & position_inside
        miss_penalty_stages = (
            "chord_fine_reach", "isolated_press", "integrated_press",
            "static_chord", "frozen_context", "goal_pair",
            "transition_window", "coverage", "integration", "full_song")
        press_near_miss = (
            press_near_miss_mask(
                press_mask, press_success,
                effective_fine_distance,
                self.press_near_miss_distance)
            if stage in miss_penalty_stages
            else torch.zeros_like(press_mask))
        stagger_quality = torch.exp(
            -(((position_x - target_fraction) / 0.15) ** 2))
        staggered = (
            (target_fraction - self.APPROACH_X).abs() > 1e-4)
        ergonomic_position_quality = torch.where(
            staggered,
            torch.maximum(position_quality, 0.70 * stagger_quality),
            position_quality)
        dense_position_quality = dense_fret_position_quality(
            position_x,
            scale=(self.chord_fine_position_dense_scale
                   if chord_fine_position_relaxed
                   else self.press_position_dense_scale),
            lower=self.chord_multi_region_lower,
            upper=self.chord_multi_region_upper)
        precision_gate = press_precision_gate(
            dense_position_quality,
            floor=(self.chord_fine_precision_gate_floor
                   if chord_fine_position_relaxed
                   else self.press_precision_gate_floor))
        good_position_quality = (
            0.50 * ergonomic_position_quality
            + 0.30 * fine_metrics["fine_lateral_quality"]
            + 0.20 * fine_metrics["fine_normal_quality"])
        cell_aligned = press_depth > (-self.PAD_RADIUS + 1e-6)
        depth_progress = press_depth_progress(
            press_depth, start_depth=-0.005,
            success_depth=self.PRESS_ON_DEPTH)
        chord_fine_depth_progress = press_depth_progress(
            press_depth, start_depth=self.chord_fine_depth_start,
            success_depth=self.PRESS_ON_DEPTH)
        press_acquisition = 0.40 * depth_progress + 0.60 * press_success.float()
        (press_hold_streak, press_hold_acquired, press_hold_quality,
         press_dropout, press_hold_same_target) = update_press_hold_state(
            self._press_hold_streak, self._press_hold_acquired,
            self._press_hold_previous_fret, self._press_hold_previous_finger,
            fret.long(), finger.long(), press_success,
            min_frames=self.press_hold_min_frames,
            full_frames=self.press_hold_full_frames)
        self._press_hold_streak.copy_(press_hold_streak)
        self._press_hold_acquired.copy_(press_hold_acquired)
        self._press_dropout_streak.copy_(torch.where(
            press_dropout, self._press_dropout_streak + 1,
            torch.zeros_like(self._press_dropout_streak)))
        self._press_hold_previous_fret.copy_(fret.long())
        self._press_hold_previous_finger.copy_(finger.long())
        has_press_goal = press_mask.any(dim=-1)
        chord_ready = (
            has_press_goal
            & (press_success & (press_hold_quality >= 1.0)
               | ~press_mask).all(dim=-1))
        chord_hold_quality = press_hold_quality.masked_fill(
            ~press_mask, 1.0).amin(dim=-1)
        chord_hold_quality = torch.where(
            has_press_goal, chord_hold_quality,
            torch.zeros_like(chord_hold_quality))
        press_core = (0.30 * distance_reward
                      + precision_gate * (
                          0.35 * press_acquisition
                          + 0.15 * press_hold_quality)
                      + 0.20 * press_success.float() * good_position_quality)
        press_core = apply_binary_penalty(
            press_core, press_dropout, self.press_dropout_penalty)
        integrated_press_core = integrated_press_core_reward(
            distance_reward,
            fine_distance_reward,
            fine_metrics["fine_lateral_quality"],
            fine_metrics["fine_normal_quality"],
            precision_gate,
            press_acquisition,
            press_hold_quality,
            press_success,
            good_position_quality)
        integrated_press_core = apply_binary_penalty(
            integrated_press_core, press_dropout,
            self.press_dropout_penalty)

        # 오압현은 해당 줄 점수를 0으로 만들고 DONT_CARE도 0을 반환한다.
        no_press_success = no_press_mask & ~wrong_press
        core = torch.where(press_mask, press_core,
                           torch.where(no_press_mask, no_press_success.float(),
                                       torch.zeros_like(press_core)))
        core = torch.where(wrong_press & supervised_mask, torch.zeros_like(core), core)

        forbidden_depth = max_depth_by_fret.masked_fill(
            ~no_press_required, -float("inf")).max(dim=-1).values
        forbidden_depth = torch.where(
            torch.isfinite(forbidden_depth), forbidden_depth,
            torch.full_like(forbidden_depth, -self.PAD_RADIUS))
        avoidance_reward = wrong_press_avoidance_reward(
            forbidden_depth, on_depth=self.PRESS_ON_DEPTH)
        core = blend_wrong_press_avoidance(
            core, avoidance_reward, supervised_mask, wrong_press,
            self.wrong_press_avoidance_weight)

        target_press_any = torch.gather(
            self._press_anyseg, 3,
            fret_index[:, :, None, None].expand(-1, -1, 4, 1)).squeeze(-1).any(dim=2)
        correct = torch.where(press_mask, press_success,
                              torch.where(no_press_mask, no_press_success,
                                          torch.ones_like(press_mask)))
        has_requirement = supervised_mask.any(dim=1)
        all_correct = has_requirement & (correct | ~supervised_mask).all(dim=1)
        wrist = self.env.to_guitar_frame(self.env.hbody_pos("L_Wrist")[:, None])[:, 0]
        if self.env.goals.has_wrist_target:
            wrist_error = (wrist - goal["wrist"]).norm(dim=-1) - goal["wrist_radius"]
            wrist_reward = torch.exp(-50.0 * wrist_error.clamp_min(0.0).square())
        else:
            wrist_reward = torch.ones(n, device=self.env.device)

        tips = points[:, :, -1]
        motion = (wrist - self.prev_wrist).square().sum(-1)
        motion += 0.1 * (tips - self.prev_tips).square().sum(dim=(-1, -2))
        smooth = torch.exp(-3000.0 * motion)
        smooth = torch.where(self._have_previous, smooth, torch.ones_like(smooth))
        self.prev_wrist.copy_(wrist)
        self.prev_tips.copy_(tips)
        self._have_previous[:] = True

        successful_finger_press = (
            press_success[..., None] & finger_assignment
        ).any(dim=1)
        required_finger_press_count = (
            press_mask[..., None] & finger_assignment).sum(dim=1)
        successful_finger_press_count = (
            press_success[..., None] & finger_assignment).sum(dim=1)
        current_press_protected = (
            current_finger_active
            & (successful_finger_press_count
               == required_finger_press_count))
        self._had_successful_press |= successful_finger_press
        hover_gate = ~current_finger_active
        hover_position_reward, hover_gap, _ = (
            released_finger_hover_reward(
                tips, p0, p1, hover_gate, pad_radius=self.PAD_RADIUS,
                free_gap=self.hover_free_gap, decay_scale=self.hover_decay_scale))
        hover_outward_speed = (
            (hover_gap - self._previous_hover_gap) * float(self.env.SIM_HZ)
        ).clamp_min(0.0)
        relation_rest = goal["finger_event"][..., 12] > 0.5
        relation_move = goal["finger_event"][..., 11] > 0.5
        time_to_next_s = (goal["finger_event"][..., 7]
                          * FINGER_EVENT_TIME_SCALE_S)
        hover_velocity_gate = released_finger_velocity_gate(
            self._had_successful_press, current_finger_active,
            self._previous_hover_valid, relation_rest, relation_move,
            time_to_next_s, self.next_goal_lookahead_s)
        hover_velocity_reward, _ = (
            released_finger_outward_velocity_reward(
                hover_outward_speed, hover_velocity_gate,
                free_speed=self.hover_free_outward_speed,
                decay_scale=self.hover_speed_decay_scale))

        self._release_arch_anchor.copy_(torch.where(
            successful_finger_press[..., None],
            arch_angles, self._release_arch_anchor))
        self._release_arch_valid |= successful_finger_press
        initial_idle = ~self._release_arch_valid & hover_gate
        self._release_arch_anchor.copy_(torch.where(
            initial_idle[..., None],
            arch_angles, self._release_arch_anchor))
        self._release_arch_valid |= initial_idle
        finger_any_press = self._press_anyseg.any(dim=1).any(dim=-1)
        idle_timing_gate = (
            relation_rest
            | (relation_move
               & (time_to_next_s > self.next_goal_lookahead_s)))
        release_pose_gate = (
            hover_gate & idle_timing_gate & self._release_arch_valid
            & ~finger_any_press)
        self._release_age.copy_(torch.where(
            release_pose_gate,
            self._release_age + 1.0 / float(self.env.SIM_HZ),
            torch.zeros_like(self._release_age)))
        release_pose_reward, _, release_pose_error_deg = (
            released_finger_pose_reward(
                arch_angles, self._release_arch_anchor, self._release_age,
                release_pose_gate,
                blend_time=self.hover_release_blend_time,
                relaxed_pip_deg=self.hover_release_relaxed_pip_deg,
                relaxed_dip_deg=self.hover_release_relaxed_dip_deg,
                tolerance_deg=self.hover_release_tolerance_deg))
        hover_velocity_weight = (
            1.0 - self.hover_position_weight
            - self.hover_release_pose_weight)
        hover_reward = (
            self.hover_position_weight * hover_position_reward
            + self.hover_release_pose_weight * release_pose_reward
            + hover_velocity_weight * hover_velocity_reward)
        self._previous_hover_gap.copy_(hover_gap)
        self._previous_hover_valid[:] = True
        transition_sample = torch.ones(
            n, dtype=torch.bool, device=self.env.device)
        if stage == "goal_pair":
            rehearsal = getattr(
                self.env.goals, "goal_pair_rehearsal_mask", None)
            if rehearsal is not None:
                sequence = getattr(
                    self.env.goals, "goal_pair_sequence_mask", None)
                excluded = rehearsal.bool()
                if sequence is not None:
                    excluded = excluded | sequence.bool()
                transition_sample = ~excluded
        next_goal_time_gate_floor = (
            transition_sample.float()
            * self.goal_pair_transition_time_gate_floor
            if stage == "goal_pair"
            else torch.zeros(
                n, dtype=tips.dtype, device=self.env.device))
        next_goal_reward, next_goal_metrics = next_goal_approach_reward(
            tips, all_approach, outward, goal["finger_event"],
            current_finger_active, pad_radius=self.PAD_RADIUS,
            lookahead_s=self.next_goal_lookahead_s,
            current_press_protected=current_press_protected,
            release_window_s=self.hover_move_release_time,
            prepress_clearance=self.next_goal_prepress_clearance,
            time_gate_floor=next_goal_time_gate_floor)
        context_anchor = getattr(
            self.env.goals, "goal_pair_rehearsal_anchor_finger", None)
        if context_anchor is None:
            context_anchor = torch.zeros(
                n, dtype=torch.long, device=self.env.device)
        (next_goal_reward, anchor_next_reward,
         anchor_next_active) = blend_anchor_finger_reward(
            next_goal_reward,
            next_goal_metrics["next_goal_approach_per_finger"],
            next_goal_metrics["next_goal_approach_gate"],
            context_anchor, self.goal_pair_rehearsal_anchor_weight)
        for gate_name, reward_name in (
                ("next_goal_inactive_move_gate",
                 "next_goal_inactive_move_reward"),
                ("next_goal_active_move_gate",
                 "next_goal_active_move_reward")):
            next_goal_metrics[reward_name], _, _ = (
                blend_anchor_finger_reward(
                    next_goal_metrics[reward_name],
                    next_goal_metrics["next_goal_approach_per_finger"],
                    next_goal_metrics[gate_name], context_anchor,
                    self.goal_pair_rehearsal_anchor_weight))

        all_active_press_held = (
            (~current_finger_active | successful_finger_press).all(dim=1))
        coupling_protected = (
            all_active_press_held & ~wrong_press.any(dim=1))
        current_finger_press_count = (
            press_mask[..., None] & finger_assignment).sum(dim=1)
        current_finger_press_quality = (
            (press_core.clamp(0.0, 1.0)[..., None]
             * (press_mask[..., None] & finger_assignment).float()).sum(dim=1)
            / current_finger_press_count.clamp_min(1))
        current_finger_press_quality = torch.where(
            current_finger_active,
            current_finger_press_quality,
            torch.ones_like(current_finger_press_quality))
        current_press_count = current_finger_active.sum(dim=1)
        current_press_preservation_quality = (
            current_finger_press_quality.amin(dim=1))
        current_press_preservation_quality = torch.where(
            current_press_count > 0,
            current_press_preservation_quality
            * (~wrong_press.any(dim=1)).float(),
            torch.ones_like(current_press_preservation_quality))
        next_string_mask = goal["finger_event"][..., :6] > 0.5
        next_fret = torch.round(
            goal["finger_event"][..., 6] * 22.0).long()
        next_progress_gate = next_goal_metrics[
            "next_goal_inactive_move_gate"]
        next_same_target = (
            (self._previous_next_goal_fret == next_fret)
            & (self._previous_next_goal_string_mask
               == next_string_mask).all(dim=-1))
        # In a goal-pair transition, positive next-target progress is a
        # conditional credit: only an intact outgoing press may earn it.
        # Keep the negative potential delta unmodified so releasing a current
        # note is still visible to the policy.
        if stage == "goal_pair":
            current_press_preservation_gate = (
                (~current_finger_active.any(dim=1)
                 | current_press_protected.all(dim=1))
                & ~wrong_press.any(dim=1))
            transition_positive_progress_gate = torch.where(
                transition_sample,
                current_press_preservation_gate,
                torch.ones_like(transition_sample))
        else:
            transition_positive_progress_gate = torch.ones(
                n, dtype=torch.bool, device=self.env.device)
        next_goal_progress_per_finger, next_potential = (
            next_goal_potential_progress(
                self._previous_next_goal_potential,
                next_goal_metrics["next_goal_approach_distance"],
                self._previous_next_goal_valid,
                next_same_target,
                next_progress_gate,
                current_press_preservation_quality,
                near=self.next_goal_progress_near,
                far=self.next_goal_progress_far,
                unprotected_positive_scale=
                    self.next_goal_unprotected_progress_scale))
        next_goal_progress_per_finger = gate_next_goal_positive_progress(
            next_goal_progress_per_finger,
            transition_positive_progress_gate,
            require_preservation=(stage == "goal_pair"))
        self._previous_next_goal_potential.copy_(next_potential)
        self._previous_next_goal_valid.copy_(next_progress_gate)
        self._previous_next_goal_fret.copy_(next_fret)
        self._previous_next_goal_string_mask.copy_(next_string_mask)
        next_progress_count = next_progress_gate.sum(dim=-1)
        next_goal_progress_reward = (
            next_goal_progress_per_finger.sum(dim=-1)
            / next_progress_count.clamp_min(1))
        next_goal_progress_reward = torch.where(
            next_progress_count > 0,
            next_goal_progress_reward,
            torch.zeros_like(next_goal_progress_reward))
        next_goal_metrics.update({
            "next_goal_progress_per_finger":
                next_goal_progress_per_finger,
            "next_goal_progress_gate": next_progress_gate,
            "next_goal_progress_reward": next_goal_progress_reward,
            "next_goal_current_press_preserved": coupling_protected,
            "next_goal_current_press_preservation_quality":
                current_press_preservation_quality,
            "next_goal_current_press_preservation_per_finger":
                current_finger_press_quality,
            "next_goal_current_press_preserved_per_finger":
                current_press_protected,
            "active_finger_by_number": current_finger_active,
            "next_goal_progress_preservation_gate":
                transition_positive_progress_gate,
        })
        success_pose_guide_reward = torch.zeros(
            n, dtype=q.dtype, device=self.env.device)
        success_pose_guide_per_finger = torch.zeros(
            n, 4, dtype=q.dtype, device=self.env.device)
        success_pose_guide_active = torch.zeros(
            n, 4, dtype=torch.bool, device=self.env.device)
        success_pose_guide_anchor_reward = torch.zeros(
            n, dtype=q.dtype, device=self.env.device)
        success_pose_guide_anchor_active = torch.zeros(
            n, dtype=torch.bool, device=self.env.device)
        success_pose_guide_proximal_reward = torch.zeros(
            n, dtype=q.dtype, device=self.env.device)
        success_pose_guide_proximal_active = torch.zeros(
            n, 4, dtype=torch.bool, device=self.env.device)
        frozen_context_recovery = (
            stage == "frozen_context"
            and bool(getattr(
                self.env, "frozen_context_recovery_active", False)))
        frozen_context_training = torch.zeros(
            n, dtype=torch.bool, device=self.env.device)
        frozen_context_teacher_scale = 0.0
        if frozen_context_recovery:
            frozen_context_training = (
                self.env._frozen_context_training_cohort())
            frozen_context_teacher_scale = float(getattr(
                self.env, "frozen_context_recovery_teacher_scale", 0.0))
        pose_guide_weight = (
            self.chord_reach_success_pose_guide_weight
            if stage == "chord_reach"
            else self.chord_fine_success_pose_guide_weight
            if stage in ("chord_fine_reach", "static_chord")
            else (self.chord_fine_success_pose_guide_weight
                  * frozen_context_teacher_scale)
            if frozen_context_recovery
            else self.goal_pair_success_pose_guide_weight)
        if (stage in (
                "chord_reach", "chord_fine_reach", "static_chord",
                "frozen_context", "goal_pair")
                and (stage != "frozen_context"
                     or frozen_context_recovery)
                and pose_guide_weight > 0.0):
            pose_slot = goal["finger_pose_slot"].long()
            safe_pose_slot = pose_slot.clamp_min(0)
            finger_index_4 = torch.arange(
                4, device=self.env.device).view(1, 4)
            pose_valid = (
                (pose_slot >= 0)
                & self.env._success_finger_pose_valid[
                    safe_pose_slot, finger_index_4])
            target_pose_q = self.env._success_finger_pose_q[
                safe_pose_slot, finger_index_4]
            current_pose_q = q[:, self.env._finger_pose_dof_indices]
            pose_gate = (
                frozen_context_pose_guide_gate(
                    current_finger_active, frozen_context_training)
                if frozen_context_recovery
                else current_finger_active)
            if stage == "goal_pair":
                pose_gate = (
                    pose_gate
                    | next_goal_metrics["next_goal_approach_gate"])
            (success_pose_guide_reward,
             success_pose_guide_per_finger,
             success_pose_guide_active) = cached_finger_pose_guide(
                current_pose_q, target_pose_q,
                self.env._finger_pose_scale, pose_valid, pose_gate)
            if stage == "goal_pair":
                target_proximal_q = (
                    self.env._success_finger_pose_proximal_q[
                        safe_pose_slot, finger_index_4])
                current_proximal_q = q[
                    :, self.env._finger_pose_proximal_dof_indices]
                current_proximal_q = current_proximal_q[:, None].expand(
                    -1, 4, -1)
                anchor_mask = (
                    torch.arange(
                        1, 5, device=self.env.device).view(1, 4)
                    == context_anchor[:, None])
                proximal_gate = (
                    next_goal_metrics["next_goal_inactive_move_gate"]
                    & anchor_mask)
                (success_pose_guide_proximal_reward,
                 success_pose_guide_proximal_per_finger,
                 success_pose_guide_proximal_active) = (
                    cached_finger_pose_guide(
                        current_proximal_q, target_proximal_q,
                        self.env._finger_pose_proximal_scale[None].expand(
                            4, -1),
                        pose_valid, proximal_gate))
                proximal_fraction = (
                    self.goal_pair_success_pose_proximal_fraction)
                success_pose_guide_per_finger = torch.where(
                    success_pose_guide_proximal_active,
                    (1.0 - proximal_fraction)
                    * success_pose_guide_per_finger
                    + proximal_fraction
                    * success_pose_guide_proximal_per_finger,
                    success_pose_guide_per_finger)
            guide_count = success_pose_guide_active.sum(dim=-1)
            success_pose_guide_reward = (
                success_pose_guide_per_finger.sum(dim=-1)
                / guide_count.clamp_min(1))
            success_pose_guide_reward = torch.where(
                guide_count > 0, success_pose_guide_reward,
                torch.zeros_like(success_pose_guide_reward))
            if stage in (
                    "chord_reach", "chord_fine_reach", "static_chord",
                    "frozen_context"):
                guide_minimum = success_pose_guide_per_finger.masked_fill(
                    ~success_pose_guide_active, float("inf")).amin(dim=-1)
                guide_minimum = torch.where(
                    guide_count > 0, guide_minimum,
                    torch.zeros_like(guide_minimum))
                success_pose_guide_reward = (
                    0.25 * success_pose_guide_reward
                    + 0.75 * guide_minimum)
            else:
                (success_pose_guide_reward,
                 success_pose_guide_anchor_reward,
                 success_pose_guide_anchor_active) = (
                    blend_anchor_finger_reward(
                        success_pose_guide_reward,
                        success_pose_guide_per_finger,
                        success_pose_guide_active, context_anchor,
                        self.goal_pair_success_pose_focus_weight))
        coupling_follower = (
            finger_synergy_follower_mask(
                current_finger_active, goal["finger_event"])
            & ~finger_any_press)
        (finger_coupling_reward, _,
         finger_coupling_gate, finger_coupling_target_speed_deg) = (
            adjacent_finger_coupling_reward(
                arch_velocity, coupling_follower, coupling_protected,
                coefficients=self.finger_coupling_coefficients,
                min_driver_speed_deg=self.finger_coupling_min_speed_deg,
                full_driver_speed_deg=self.finger_coupling_full_speed_deg,
                tolerance_deg_s=self.finger_coupling_tolerance_deg_s))

        # R23 기준점은 안정 압현 뒤 생성하고 목표 변경이나 접촉 해제 때 지운다.
        finger_goal_mask = (press_mask[..., None] & finger_assignment).permute(0, 2, 1)
        finger_success_mask = (
            press_success[..., None] & finger_assignment
        ).permute(0, 2, 1)
        required_count = finger_goal_mask.sum(dim=-1)
        stable_press = ((required_count > 0)
                        & (finger_success_mask.sum(dim=-1) == required_count))
        finger_fret = (fret.long()[..., None] * finger_goal_mask.permute(0, 2, 1)) \
            .amax(dim=1)
        same_target = ((finger_goal_mask == self._slip_previous_mask).all(dim=-1)
                       & (finger_fret == self._slip_previous_fret))
        continuing = stable_press & same_target
        self._slip_streak.copy_(torch.where(
            continuing, self._slip_streak + 1,
            torch.where(stable_press, torch.ones_like(self._slip_streak),
                        torch.zeros_like(self._slip_streak))))
        self._slip_anchor_valid &= continuing

        tip_local_xy = self.env.to_guitar_frame(tips)[..., :2]
        new_anchor = (stable_press
                      & (self._slip_streak >= self.slip_stable_frames)
                      & ~self._slip_anchor_valid)
        self._slip_anchor_xy.copy_(torch.where(
            new_anchor[..., None], tip_local_xy, self._slip_anchor_xy))
        self._slip_anchor_valid |= new_anchor
        slip_gate = stable_press & self._slip_anchor_valid
        slip_distance = (tip_local_xy - self._slip_anchor_xy).norm(dim=-1)
        slip_instant = (tip_local_xy - self._slip_previous_xy).norm(dim=-1)
        slip_instant = torch.where(
            stable_press & same_target & self._slip_previous_valid,
            slip_instant, torch.zeros_like(slip_instant))
        slip_reward, _ = fingertip_slip_reward(
            slip_distance, slip_gate, free_distance=self.slip_free_distance,
            decay_scale=self.slip_decay_scale)
        self._slip_previous_xy.copy_(tip_local_xy)
        self._slip_previous_valid.copy_(stable_press)
        self._slip_previous_mask.copy_(finger_goal_mask)
        self._slip_previous_fret.copy_(finger_fret)
        drag_metrics = self.pressed_drag_monitor.update(
            finger_goal_mask, finger_fret,
            goal["finger_event"][..., 11] > 0.5,
            stable_press, tip_local_xy,
            self._press_anyseg.permute(0, 2, 1, 3))

        _, thumb_metrics = self.thumb_reward.compute()
        self._thumb_support_streak.copy_(torch.where(
            thumb_metrics["thumb_support"],
            self._thumb_support_streak + 1,
            torch.zeros_like(self._thumb_support_streak)))
        thumb_gate = thumb_goal_proximity_gate(
            approach_distance, press_mask,
            full_distance=self.thumb_gate_full_distance,
            zero_distance=self.thumb_gate_zero_distance)
        thumb_geometry_ready = (
            thumb_metrics["thumb_geometric_support_quality"] * thumb_gate)
        thumb_support_ready = (
            thumb_metrics["thumb_support_quality"] * thumb_gate)
        thumb_reward = thumb_support_reward(
            thumb_metrics["thumb_approach_reward"],
            thumb_geometry_ready, thumb_support_ready)
        thumb_press_readiness_value = thumb_press_readiness(
            thumb_metrics["thumb_approach_reward"],
            thumb_geometry_ready, thumb_support_ready, thumb_gate)
        thumb_factor_gate = thumb_gate
        if stage == "integrated_press":
            thumb_factor_gate = thumb_gate * press_hold_acquired.any(dim=1).float()
        thumb_press_factor = thumb_press_reward_factor(
            thumb_press_readiness_value, thumb_factor_gate,
            self.thumb_press_gate_weight)
        thumb_base_saturation_penalty = (
            thumb_base_action_saturation_penalty(
                self.env.prev_action[
                    :, self.env._thumb_base_action_indices],
                thumb_metrics["thumb_support"],
                threshold=self.thumb_base_saturation_threshold,
                weight=self.thumb_base_saturation_penalty_weight,
                supported_fraction=
                    self.thumb_base_supported_saturation_fraction))
        thumb_overforce = thumb_metrics["thumb_overforce"]
        proximal_reward, proximal_metrics = self.proximal_reward.compute(
            approach_distance, press_mask)
        active_channels = press_mask.float()
        arch_gate = linear_approach_reward(approach_distance)
        arch_precision_quality = press_arch_shaping_quality(designated_arch)
        isolated_precision_quality = isolated_press_conjunctive_quality(
            press_acquisition, position_quality, arch_precision_quality)
        if stage in ("coarse_reach", "chord_reach"):
            base_reward = (
                0.75 * linear_distance_reward + 0.25 * approach_progress)
            finger_reward = apply_finger_arch_shaping(
                base_reward, designated_arch, approach_distance,
                press_mask & ~wrong_press, self.finger_arch_reward_weight)
            reward = active_channels * (
                (1.0 - self.thumb_weight) * finger_reward
                + self.thumb_weight
                * thumb_metrics["thumb_approach_reward"][:, None])
        elif stage == "fine_reach":
            alignment_core = (
                0.50 * fine_distance_reward
                + 0.50 * fine_metrics["fine_alignment_quality"])
            base_reward = 0.90 * alignment_core + 0.10 * approach_progress
            finger_reward = apply_finger_arch_shaping(
                base_reward, designated_arch, approach_distance,
                press_mask & ~wrong_press,
                self.fine_reach_finger_arch_reward_weight)
            reward = active_channels * (
                (1.0 - self.thumb_weight) * finger_reward
                + self.thumb_weight * thumb_reward[:, None])
        elif stage == "chord_fine_reach":
            point_weight = self.chord_multi_point_bonus_weight
            alignment_core = (
                0.50 * fine_distance_reward
                + 0.50 * effective_alignment_quality)
            base_reward = (
                (0.75 - point_weight) * alignment_core
                + point_weight * fine_metrics["fine_alignment_quality"]
                + 0.15 * press_acquisition
                + 0.10 * approach_progress)
            finger_reward = apply_finger_arch_shaping(
                base_reward, designated_arch, approach_distance,
                press_mask & ~wrong_press, self.finger_arch_reward_weight)
            reward = active_channels * (
                (1.0 - self.thumb_weight) * finger_reward
                + self.thumb_weight * thumb_reward[:, None])
        elif stage == "isolated_press":
            articulation_bonus = arch_precision_quality * arch_gate
            arch_weight = self.isolated_press_arch_reward_weight
            finger_weight = 1.0 - self.thumb_weight
            press_weight = finger_weight - arch_weight
            additive_finger_reward = (
                press_weight * integrated_press_core
                + arch_weight * articulation_bonus) / finger_weight
            conjunction = self.isolated_press_conjunctive_weight
            finger_reward = finger_weight * (
                (1.0 - conjunction) * additive_finger_reward
                + conjunction * isolated_precision_quality)
            reward = active_channels * (
                finger_reward
                + self.thumb_weight * thumb_reward[:, None])
        elif stage == "integrated_press":
            base_reward = (
                (1.0 - self.thumb_weight) * integrated_press_core
                + self.thumb_weight * thumb_reward[:, None])
            reward = active_channels * apply_finger_arch_shaping(
                base_reward, designated_arch, approach_distance,
                press_mask & ~wrong_press,
                self.finger_arch_reward_weight)
        else:
            # 보조 항은 감독 대상 줄에만 적용한다.
            supervised_channels = supervised_mask.float()
            core = apply_finger_arch_shaping(
                core, designated_arch, approach_distance,
                press_mask & ~wrong_press,
                self.finger_arch_reward_weight)
            auxiliary = (self.wrist_weight * wrist_reward
                         + self.smooth_weight * smooth
                         + self.thumb_weight * thumb_reward
                         + self.hover_weight * hover_reward
                         + self.slip_weight * slip_reward)
            reward = (self.task_weight * core
                      + supervised_channels * auxiliary[:, None])
        chord_bridge_aggregate = torch.zeros(
            n, device=self.env.device)
        chord_bridge_mean = torch.zeros_like(chord_bridge_aggregate)
        chord_bridge_min = torch.zeros_like(chord_bridge_aggregate)
        chord_fine_joint = torch.zeros_like(chord_bridge_aggregate)
        chord_fine_joint_mean = torch.zeros_like(chord_bridge_aggregate)
        chord_fine_joint_min = torch.zeros_like(chord_bridge_aggregate)
        chord_fine_axis_min = torch.zeros_like(reward)
        if stage in ("chord_reach", "chord_fine_reach"):
            (reward, chord_bridge_aggregate,
             chord_bridge_mean, chord_bridge_min) = (
                aggregate_active_channel_bottleneck(
                    reward, press_mask,
                    self.chord_bridge_bottleneck_weight))
        if stage == "chord_fine_reach":
            (joint_reward, chord_fine_joint,
             chord_fine_joint_mean, chord_fine_joint_min,
             chord_fine_axis_min) = chord_fine_conjunctive_reward(
                fine_distance_reward,
                effective_longitudinal_quality,
                fine_metrics["fine_lateral_quality"],
                fine_metrics["fine_normal_quality"],
                chord_fine_depth_progress, press_success, press_mask,
                bottleneck_weight=1.0)
            reward = torch.where(
                press_mask,
                (1.0 - self.chord_fine_joint_weight) * reward
                + self.chord_fine_joint_weight * joint_reward,
                reward)
        if stage not in (
                "coarse_reach", "fine_reach",
                "chord_reach", "chord_fine_reach",
                "isolated_press"):
            reward = torch.where(
                press_mask, reward * thumb_press_factor[:, None], reward)
        reward, _ = blend_finger_coupling_reward(
            reward, finger_coupling_reward, press_mask,
            finger_coupling_gate, self.finger_coupling_weight)
        # 움직임 우선순위는 손끝 거리에 따른 곱셈 비용이다.
        hierarchy_factor = 1.0 - self.proximal_weight * (
            1.0 - proximal_reward[:, None])
        reward = torch.where(supervised_mask, reward * hierarchy_factor, reward)
        reward = (
            reward
            - self.thumb_overforce_penalty * thumb_overforce[:, None]
            * torch.where(supervised_mask, torch.ones_like(core),
                          torch.zeros_like(core)))
        reward = apply_binary_penalty(
            reward, wrong_press, self.wrong_press_penalty)
        reward = apply_binary_penalty(
            reward, press_near_miss, self.press_near_miss_penalty)
        rehearsal_anchor = context_anchor
        rehearsal_anchor_mask = (
            press_mask
            & (finger.long() == rehearsal_anchor[:, None])
            & (rehearsal_anchor[:, None] > 0))
        rehearsal_anchor_reward = torch.zeros(
            n, device=self.env.device)
        rehearsal_anchor_active = torch.zeros(
            n, dtype=torch.bool, device=self.env.device)
        press_bridge_stage = stage in (
            "static_chord", "frozen_context",
            "goal_pair", "transition_window")
        balanced_reward, class_balance_metrics = balance_press_no_press_channels(
            reward, press_mask, no_press_mask, press_success,
            press_weight=self.press_class_weight,
            no_press_weight=self.no_press_class_weight,
            no_press_failure_credit=(
                self.static_chord_no_press_failure_credit
                if press_bridge_stage else self.no_press_failure_credit),
            press_bottleneck_weight=(
                self.static_chord_bottleneck_weight
                if press_bridge_stage else 0.0),
            no_press_completion_power=(
                self.static_chord_no_press_completion_power
                if press_bridge_stage else 1.0))
        no_press_count = no_press_mask.sum(dim=-1)
        no_press_completion = (
            no_press_success.sum(dim=-1).float()
            / no_press_count.clamp_min(1).float())
        no_press_completion = torch.where(
            no_press_count > 0,
            no_press_completion,
            torch.ones_like(no_press_completion))
        chord_joint_quality = conjunctive_chord_quality(
            class_balance_metrics["press_class_completion"],
            chord_hold_quality,
            no_press_completion,
            thumb_press_factor)
        class_balance_metrics["no_press_class_completion"] = (
            no_press_completion)
        if press_bridge_stage:
            joint_weight = self.static_chord_joint_weight
            balanced_reward = (
                (1.0 - joint_weight) * balanced_reward
                + joint_weight * chord_joint_quality[:, None])
            class_balance_metrics["class_balanced_reward"] = (
                balanced_reward[:, 0])
        static_chord_completion_gate = torch.ones(
            n, device=self.env.device)
        frozen_context_completion_gate = torch.ones_like(
            static_chord_completion_gate)
        if stage in ("static_chord", "frozen_context"):
            (completion_gated_reward, completion_gate) = (
                gate_chord_completion_for_stage(
                    stage,
                    balanced_reward,
                    class_balance_metrics["press_class_completion"],
                    press_mask.sum(dim=-1),
                    floor=self.static_chord_completion_gate_floor,
                    power=self.static_chord_completion_gate_power))
            if stage == "static_chord":
                balanced_reward = completion_gated_reward
                static_chord_completion_gate = completion_gate
            else:
                balanced_reward = completion_gated_reward
                frozen_context_completion_gate = completion_gate
            class_balance_metrics["class_balanced_reward"] = (
                balanced_reward[:, 0])
        static_chord_auxiliary_gate = torch.ones(
            n, device=self.env.device)
        if stage == "static_chord":
            balanced_reward, static_chord_auxiliary_gate = (
                gate_static_chord_auxiliary_reward(
                    balanced_reward,
                    class_balance_metrics["press_class_reward"],
                    class_balance_metrics["press_class_completion"],
                    self.static_chord_auxiliary_gate_floor))
            class_balance_metrics["class_balanced_reward"] = (
                balanced_reward[:, 0])
        if stage == "goal_pair" and self.goal_pair_rehearsal_anchor_weight > 0.0:
            (balanced_reward, rehearsal_anchor_reward,
             rehearsal_anchor_active) = (
                blend_goal_pair_rehearsal_anchor_reward(
                    balanced_reward, reward, rehearsal_anchor_mask,
                    self.goal_pair_rehearsal_anchor_weight))
            class_balance_metrics["class_balanced_reward"] = (
                balanced_reward[:, 0])
        class_balance_enabled = stage not in (
            "coarse_reach", "fine_reach", "chord_reach",
            "chord_fine_reach", "isolated_press", "integrated_press")
        inactive_move_active = next_goal_metrics[
            "next_goal_inactive_move_gate"].any(dim=-1)
        active_move_active = next_goal_metrics[
            "next_goal_active_move_gate"].any(dim=-1)
        next_goal_active = inactive_move_active | active_move_active
        current_press_preservation_gate = (
            transition_sample
            & inactive_move_active
            & current_finger_active.any(dim=1))
        preservation_shaped = (
            (1.0 - self.next_goal_preservation_weight) * balanced_reward
            + self.next_goal_preservation_weight
            * current_press_preservation_quality[:, None])
        balanced_reward = torch.where(
            current_press_preservation_gate[:, None],
            preservation_shaped,
            balanced_reward)
        class_balance_metrics["class_balanced_reward"] = (
            balanced_reward[:, 0])
        next_goal_metrics[
            "next_goal_current_press_preservation_gate"] = (
                current_press_preservation_gate)
        next_goal_blend_weight = torch.full(
            (n,), self.next_goal_weight,
            dtype=balanced_reward.dtype, device=self.env.device)
        if stage == "goal_pair":
            next_goal_blend_weight = torch.where(
                transition_sample,
                torch.full_like(
                    next_goal_blend_weight,
                    self.goal_pair_transition_next_goal_weight),
                torch.full_like(
                    next_goal_blend_weight,
                    self.goal_pair_context_next_goal_weight))
        joint_inactive_next_goal_quality = conjunctive_next_goal_quality(
            next_goal_metrics["next_goal_inactive_move_reward"],
            current_press_preservation_quality)
        next_goal_metrics["next_goal_joint_preservation_quality"] = (
            joint_inactive_next_goal_quality)
        inactive_next_goal_shaped = (
            (1.0 - next_goal_blend_weight[:, None]) * balanced_reward
            + next_goal_blend_weight[:, None]
            * joint_inactive_next_goal_quality[:, None])
        next_goal_shaped = torch.where(
            inactive_move_active[:, None],
            inactive_next_goal_shaped, balanced_reward)
        active_move_bonus = (
            next_goal_blend_weight[:, None]
            * next_goal_metrics["next_goal_active_move_reward"][:, None]
            * (1.0 - next_goal_shaped.clamp(0.0, 1.0)))
        next_goal_shaped = torch.where(
            active_move_active[:, None],
            next_goal_shaped + active_move_bonus,
            next_goal_shaped)
        if class_balance_enabled:
            reward = torch.where(
                next_goal_active[:, None], next_goal_shaped,
                balanced_reward)
        weighted_next_progress = (
            self.next_goal_progress_weight
            * next_goal_progress_reward)
        positive_next_progress = weighted_next_progress.clamp_min(0.0)
        negative_next_progress = (-weighted_next_progress).clamp_min(0.0)
        reward = (
            reward
            + positive_next_progress[:, None]
            * (1.0 - reward.clamp(0.0, 1.0))
            - negative_next_progress[:, None])
        if (stage in (
                "chord_reach", "chord_fine_reach", "static_chord",
                "frozen_context", "goal_pair")
                and (stage != "frozen_context"
                     or frozen_context_recovery)):
            guide_completion_gate = (
                frozen_context_completion_gate[:, None]
                if stage == "frozen_context" else 1.0)
            guided_reward = (
                reward
                + pose_guide_weight * success_pose_guide_reward[:, None]
                * guide_completion_gate
                * (1.0 - reward.clamp(0.0, 1.0)))
            reward = (
                torch.where(press_mask, guided_reward, reward)
                if stage in (
                    "chord_reach", "chord_fine_reach", "static_chord",
                    "frozen_context")
                else guided_reward)
        reward = reward - thumb_base_saturation_penalty[:, None]
        reference_finger_quality = torch.ones(
            n, device=self.env.device)
        reference_thumb_quality = torch.ones_like(
            reference_finger_quality)
        reference_prior_active = (
            self.reference_posture_prior is not None
            and stage in (
                "frozen_context", "goal_pair", "transition_window",
                "coverage", "integration", "full_song"))
        if reference_prior_active:
            (reference_finger_quality,
             reference_thumb_quality) = self.reference_posture_prior.compute(
                current_finger_active)
        reference_quality = (
            self.reference_motion_prior_finger_fraction
            * reference_finger_quality
            + (1.0 - self.reference_motion_prior_finger_fraction)
            * reference_thumb_quality)
        reference_penalty = (
            self.reference_motion_prior_weight
            * (1.0 - reference_quality))
        if reference_prior_active:
            reward = (
                reward
                - reference_penalty[:, None] * supervised_mask.float())
        human_range_quality = torch.ones(n, device=self.env.device)
        human_range_violation_rate = torch.zeros_like(human_range_quality)
        human_range_max_excess_deg = torch.zeros_like(human_range_quality)
        human_range_active = (
            self.human_joint_range_prior is not None
            and stage in (
                "frozen_context", "goal_pair", "transition_window",
                "coverage", "integration", "full_song"))
        if human_range_active:
            (human_range_quality, human_range_violation_rate,
             human_range_max_excess_deg) = (
                self.human_joint_range_prior.compute(current_finger_active))
        human_range_penalty = (
            self.human_joint_range_weight * (1.0 - human_range_quality))
        if human_range_active:
            reward = (
                reward
                - human_range_penalty[:, None] * supervised_mask.float())

        (precision_press_pass, precision_position_pass,
         precision_arch_pass, precision_precise_pass) = (
            press_precision_components(
                physical_press, position_inside.float(), designated_arch))
        has_active = press_mask.any(dim=1)
        if stage in ("coarse_reach", "chord_reach"):
            frame_success = has_active & (
                (approach_distance <= 0.040) | ~press_mask).all(dim=1)
        elif stage == "fine_reach":
            frame_success = has_active & (
                ((fine_metrics["fine_center_distance"] <= 0.010)
                 & (fine_metrics["fine_alignment_quality"] >= 0.80)
                 | ~press_mask).all(dim=1))
        elif stage == "chord_fine_reach":
            frame_success = has_active & (
                ((effective_fine_distance <= 0.010)
                 & (effective_alignment_quality >= 0.80)
                 & press_success
                 | ~press_mask).all(dim=1))
        elif stage == "isolated_press":
            frame_success = has_active & (
                (precision_precise_pass | ~press_mask).all(dim=1))
        elif stage == "integrated_press":
            frame_success = has_active & (
                (precise_press_success(
                    press_success, position_inside.float())
                 | ~press_mask).all(dim=1))
        elif stage in ("static_chord", "frozen_context"):
            frame_success = chord_ready & all_correct
        elif stage in ("goal_pair", "transition_window"):
            press_acquired = (
                press_hold_acquired | ~press_mask).all(dim=1)
            frame_success = (
                all_correct & (~has_active | press_acquired))
        else:
            frame_success = torch.zeros(n, dtype=torch.bool, device=self.env.device)
        self._curriculum_success_streak.copy_(torch.where(
            frame_success, self._curriculum_success_streak + 1,
            torch.zeros_like(self._curriculum_success_streak)))
        curriculum_success = self._curriculum_success_streak >= 12
        self._curriculum_episode_success |= curriculum_success
        metrics = {
            "correct": correct,
            "active": press_mask,
            "supervised": supervised_mask,
            "no_press_active": no_press_mask,
            "any_finger_on_target": target_press_any,
            "target_distance": curriculum_distance,
            "target_point_distance": fine_metrics["fine_center_distance"],
            "target_region_distance": region_metrics["distance"],
            "target_region_inside": region_metrics["inside"],
            "target_sample_fraction": region_metrics["sample_fraction"],
            "multi_press": multi_press,
            "local_reach_margin": local_reach_margin,
            "linear_distance_reward": linear_distance_reward,
            "fine_distance_reward": fine_distance_reward,
            "effective_alignment_quality": effective_alignment_quality,
            "effective_longitudinal_quality":
                effective_longitudinal_quality,
            "approach_progress": approach_progress,
            # Keep raw depression and musically valid depression separate.
            # The precision funnel needs the former to attribute whether a
            # failure came from contact, longitudinal position, or posture.
            "physical_press": physical_press,
            "press_success": press_success,
            "precision_press_pass": precision_press_pass,
            "precision_position_pass": precision_position_pass,
            "precision_arch_pass": precision_arch_pass,
            "precision_precise_pass": precision_precise_pass,
            "press_depth": press_depth,
            "press_depth_progress": depth_progress,
            "press_hold_acquired": press_hold_acquired,
            "press_hold_quality": press_hold_quality,
            "press_dropout": press_dropout,
            "press_dropout_streak": self._press_dropout_streak.clone(),
            "press_near_miss": press_near_miss,
            "chord_ready": chord_ready,
            "chord_hold_quality": chord_hold_quality,
            "position_quality": position_quality,
            "position_inside": position_inside,
            "ergonomic_position_quality": ergonomic_position_quality,
            "target_fraction": target_fraction,
            "target_min_separation": target_min_separation,
            "target_clearance_ok": target_clearance_ok,
            "dense_position_quality": dense_position_quality,
            "precision_gate": precision_gate,
            "good_position_quality": good_position_quality,
            "arch_quality": designated_arch,
            "arch_precision_quality": arch_precision_quality,
            "isolated_press_conjunctive_quality":
                isolated_precision_quality,
            "designated_arch_angles": designated_arch_angles,
            "finger_assignment": finger_assignment,
            "tip_contact": designated_distal,
            "non_tip_contact": designated_anyseg & ~designated_distal,
            "cell_aligned": (
                effective_alignment_quality >= 0.80
                if stage in ("fine_reach", "chord_fine_reach")
                else cell_aligned),
            "wrong_press": wrong_press,
            "wrong_press_per_finger": wrong_press_per_finger,
            "no_press_success": no_press_success,
            "wrist_distance": (wrist - goal["wrist"]).norm(dim=-1),
            "all_correct": all_correct,
            "curriculum_frame_success": frame_success,
            "curriculum_success": curriculum_success,
            "curriculum_episode_success": self._curriculum_episode_success.clone(),
            "thumb_goal_gate": thumb_gate,
            "thumb_geometry_ready": thumb_geometry_ready,
            "thumb_support_ready": thumb_support_ready,
            "thumb_press_readiness": thumb_press_readiness_value,
            "thumb_press_factor": thumb_press_factor,
            "thumb_press_factor_gate": thumb_factor_gate,
            "thumb_base_saturation_penalty":
                thumb_base_saturation_penalty,
            "thumb_support_streak": self._thumb_support_streak.clone(),
            "thumb_support_stable_6": self._thumb_support_streak >= 6,
            "thumb_support_stable_12": self._thumb_support_streak >= 12,
            "hover_reward": hover_reward,
            "hover_gap": hover_gap,
            "hover_gate": hover_gate,
            "hover_position_reward": hover_position_reward,
            "hover_velocity_reward": hover_velocity_reward,
            "hover_outward_speed": hover_outward_speed,
            "hover_velocity_gate": hover_velocity_gate,
            "release_pose_reward": release_pose_reward,
            "release_pose_error_deg": release_pose_error_deg,
            "release_pose_gate": release_pose_gate,
            "finger_coupling_reward": finger_coupling_reward,
            "finger_coupling_gate": finger_coupling_gate,
            "finger_coupling_target_speed_deg":
                finger_coupling_target_speed_deg,
            "finger_coupling_press_protected": coupling_protected,
            "reference_finger_posture_quality":
                reference_finger_quality,
            "reference_thumb_posture_quality":
                reference_thumb_quality,
            "reference_posture_quality": reference_quality,
            "reference_posture_penalty": reference_penalty,
            "reference_posture_active": torch.full(
                (n,), reference_prior_active, dtype=torch.bool,
                device=self.env.device),
            "human_joint_range_quality": human_range_quality,
            "human_joint_range_violation_rate":
                human_range_violation_rate,
            "human_joint_range_max_excess_deg":
                human_range_max_excess_deg,
            "human_joint_range_penalty": human_range_penalty,
            "human_joint_range_active": torch.full(
                (n,), human_range_active, dtype=torch.bool,
                device=self.env.device),
            "slip_reward": slip_reward,
            "slip_distance": slip_distance,
            "slip_instant": slip_instant,
            "slip_gate": slip_gate,
            "slip_streak": self._slip_streak.clone(),
            "next_goal_approach_reward": next_goal_reward,
            "goal_pair_anchor_next_reward": anchor_next_reward,
            "goal_pair_anchor_next_active": anchor_next_active,
            "success_pose_guide_reward": success_pose_guide_reward,
            "success_pose_guide_per_finger":
                success_pose_guide_per_finger,
            "success_pose_guide_active":
                success_pose_guide_active.any(dim=-1),
            "success_pose_guide_active_per_finger":
                success_pose_guide_active,
            "success_pose_guide_anchor_reward":
                success_pose_guide_anchor_reward,
            "success_pose_guide_anchor_active":
                success_pose_guide_anchor_active,
            "success_pose_guide_proximal_reward":
                success_pose_guide_proximal_reward,
            "success_pose_guide_proximal_active":
                success_pose_guide_proximal_active.any(dim=-1),
            "class_balance_enabled": torch.full(
                (n,), class_balance_enabled, dtype=torch.bool,
                device=self.env.device),
            "chord_joint_quality": chord_joint_quality,
            "static_chord_completion_gate":
                static_chord_completion_gate,
            "frozen_context_completion_gate":
                frozen_context_completion_gate,
            "frozen_context_recovery_training":
                frozen_context_training,
            "static_chord_auxiliary_gate": static_chord_auxiliary_gate,
            "chord_bridge_bottleneck_reward":
                chord_bridge_aggregate,
            "chord_bridge_mean_reward": chord_bridge_mean,
            "chord_bridge_min_reward": chord_bridge_min,
            "chord_fine_joint_reward": chord_fine_joint,
            "chord_fine_joint_mean_reward": chord_fine_joint_mean,
            "chord_fine_joint_min_reward": chord_fine_joint_min,
            "chord_fine_axis_min_quality": (
                chord_fine_axis_min.masked_fill(
                    ~press_mask, 0.0).sum(dim=-1)
                / press_mask.sum(dim=-1).clamp_min(1)),
            "chord_fine_broad_depth_progress": (
                chord_fine_depth_progress.masked_fill(
                    ~press_mask, 0.0).sum(dim=-1)
                / press_mask.sum(dim=-1).clamp_min(1)),
            "goal_pair_rehearsal_anchor_reward":
                rehearsal_anchor_reward,
            "goal_pair_rehearsal_anchor_active":
                rehearsal_anchor_active,
        }
        metrics.update(next_goal_metrics)
        metrics.update(class_balance_metrics)
        metrics.update(fine_metrics)
        metrics.update(thumb_metrics)
        metrics["thumb_reward"] = thumb_reward
        metrics.update(proximal_metrics)
        metrics.update(drag_metrics)
        return bound_fret_reward(
            reward, stage, self.wrong_press_penalty,
            self.press_dropout_penalty,
            self.press_near_miss_penalty), metrics
