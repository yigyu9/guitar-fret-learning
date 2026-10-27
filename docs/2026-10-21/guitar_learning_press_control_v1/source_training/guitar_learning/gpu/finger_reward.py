"""Bounded positive rates for selected left-finger surface targets; no control."""
import torch


FINGER_REWARD_CONTRACT = dict(
    schema='guitar_learning.gpu_finger_tracking_rate.v1',
    preparation_s=2., distance_scale_m=.02, approach_gain_per_s=4.,
    maximum_approach_speed_m_s=.1, velocity_error_scale_m_s=.05,
    requested_velocity_scale_rad_s=4., requested_velocity_reference_rad_s=.2,
    base_rate_per_s=2., candidate_multiplier=2.,
    selection='one per present finger: audible earliest end, else press-2..end earliest onset; original-order ties',
    window='onset<=now<end for audible; press-2<=now<end for preparation',
    error='target minus selected physical finger surface; actual velocity=-surface_velocity',
    desired_velocity='clip_norm(4*error,0.1m/s); zero for selected current candidate',
    quality='exp(-distance/0.02)*(1+candidate)/(1+velocity_error_squared/0.05^2+mean((4*LH21_action/0.2)^2))',
    rate='2/s * sum(valid selected qualities) / song-present finger count',
    rate_bounds_per_s=[0., 4.], integration='caller integrates actual physics dt; helper returns rate only',
    action_scope='all21 requested incremental velocities, including thumb; not actual joint velocity',
    limitation='geometric/load candidate; no contact pair, pressure or acoustic certification')


def finger_tracking_reward(now, onset, end, press, finger, delta, velocity,
                           candidate, actions):
    """Return rate[N], indices/valid/quality[N,4]; invalid indices are -1.

    ``actions`` follows the21 LEFT_HAND_NAMES order. No action, joint target or
    input tensor is changed. The denominator includes song-present fingers even
    when they have no target in the current window.
    """
    n, m = now.numel(), onset.numel()
    if (now.shape != (n,) or any(t.shape != (m,) for t in (onset, end, press, finger)) or
            delta.shape != (n, m, 3) or velocity.shape != delta.shape or
            candidate.shape != (n, m) or candidate.dtype != torch.bool or
            finger.dtype != torch.long or actions.shape != (n, 21)):
        raise ValueError('Aligned now[N], song[M], surface[N,M,3], candidate bool[N,M], LH21 actions required')
    if not m:
        return dict(rate=delta.new_zeros(n), quality=delta.new_zeros(n, 4),
                    indices=torch.full((n, 4), -1, device=delta.device, dtype=torch.long),
                    valid=torch.zeros(n, 4, device=delta.device, dtype=torch.bool))
    assigned = finger[None] == torch.arange(1, 5, device=finger.device)[:, None]
    audible = assigned[None] & ((onset <= now[:, None]) & (now[:, None] < end))[:, None]
    preparing = assigned[None] & ((press-2 <= now[:, None]) & (now[:, None] < end))[:, None]
    current = end.expand(n, 4, m).masked_fill(~audible, torch.inf).argmin(-1)
    upcoming = onset.expand(n, 4, m).masked_fill(~preparing, torch.inf).argmin(-1)
    valid = audible.any(-1) | preparing.any(-1)
    selected = torch.where(audible.any(-1), current, upcoming)
    selected_delta = delta.gather(1, selected[..., None].expand(-1, -1, 3))
    actual_velocity = -velocity.gather(1, selected[..., None].expand(-1, -1, 3))
    selected_candidate = candidate.gather(1, selected)
    desired = 4*selected_delta
    speed = torch.linalg.vector_norm(desired, dim=-1, keepdim=True)
    desired = desired*(.1/speed.clamp_min(.1))
    desired = torch.where(selected_candidate[..., None], 0., desired)
    distance = torch.linalg.vector_norm(selected_delta, dim=-1)
    velocity_error = (actual_velocity-desired).square().sum(-1)/.05**2
    requested_speed = (4*actions/.2).square().mean(-1, keepdim=True)
    quality = torch.exp(-distance/.02)*(1+selected_candidate.to(delta.dtype)) / (
        1+velocity_error+requested_speed)
    quality = torch.where(valid, quality, 0.)
    present_fingers = assigned.any(-1).sum().clamp_min(1)
    return dict(rate=2*quality.sum(-1)/present_fingers, quality=quality,
                indices=torch.where(valid, selected, -1), valid=valid)
