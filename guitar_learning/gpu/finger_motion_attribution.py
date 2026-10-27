"""Fixed material-point displacement diagnostics, never a force attribution."""
from dataclasses import dataclass

import torch

from guitar_learning.gpu.geometry import apply, conjugate


@dataclass(frozen=True)
class PadMotion:
    total: torch.Tensor
    support: torch.Tensor
    finger: torch.Tensor


def _pose_for_points(pose, points):
    if pose.shape[-1] != 7 or pose.ndim > points.ndim:
        raise ValueError('poses require xyz+xyzw with broadcastable leading dimensions')
    while pose.ndim < points.ndim:
        pose = pose.unsqueeze(-2)
    torch._assert_async((torch.isfinite(pose).all() &
                         (pose[..., 3:7].square().sum(-1) > 0).all()),
                        'finite poses with nonzero quaternions required')
    return pose


def decompose_pad_motion(previous_points, current_points, previous_palm,
                         current_palm, previous_guitar, current_guitar):
    """Decompose the same world-space pad samples over one control interval.

    Points are aligned [..., sample, xyz] material points, normally the fixed
    128 source pad samples, not a nearest-to-target sample selected each tick.
    Poses are [..., xyz+xyzw], with optional omitted point/body dimensions.
    Outputs retain every sample in the guitar's material coordinate axes.

    Transport the previous point's palm-local coordinate with the new palm.
    Its guitar-relative displacement is ``support``; actual-new minus that
    counterfactual is ``finger``. Their vector sum is exactly ``total``.
    Norms/path lengths are not additive, force shares, or causal percentages.
    """
    if (previous_points.shape != current_points.shape or previous_points.ndim < 2 or
            previous_points.shape[-1] != 3 or previous_points.shape[-2] < 1):
        raise ValueError('aligned nonempty world-space material points required')
    old_palm = _pose_for_points(previous_palm, previous_points)
    new_palm = _pose_for_points(current_palm, current_points)
    old_guitar = _pose_for_points(previous_guitar, previous_points)
    new_guitar = _pose_for_points(current_guitar, current_points)
    palm_local = apply(conjugate(old_palm[..., 3:7]), previous_points - old_palm[..., :3])
    carried = new_palm[..., :3] + apply(new_palm[..., 3:7], palm_local)
    old_local = apply(conjugate(old_guitar[..., 3:7]), previous_points - old_guitar[..., :3])
    carried_local = apply(conjugate(new_guitar[..., 3:7]), carried - new_guitar[..., :3])
    new_local = apply(conjugate(new_guitar[..., 3:7]), current_points - new_guitar[..., :3])
    return PadMotion(new_local - old_local, carried_local - old_local,
                     new_local - carried_local)
