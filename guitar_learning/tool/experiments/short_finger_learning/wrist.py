"""Finite arm-only wrist pose feedback; no finger or pad measurements."""
import math
import torch

from guitar_learning.gpu.geometry import apply, conjugate, multiply, rotvec
from guitar_learning.tool.validation.thumb_contact_probe import point_jacobian

WRIST_CONTROL = dict(schema='guitar_learning.fixed_wrist_teacher.v1',
    feedback='fixed guitar-local wrist origin and xyzw orientation; arm12 only; no pad error',
    ramp_s=2., policy_onset_s=3., position_interpolation='linear in guitar frame',
    orientation_interpolation='shortest-hemisphere normalized quaternion linear interpolation',
    rotation_length_scale_m=.1, damping=1e-5, correction_step_rad=math.radians(.5),
    correction_rate_bound_rad_s=math.radians(.5)*60,
    target_bounds='actual controller action bounds; accumulated correction clamped without windup',
    requested_target_rate='existing per-axis controller rate, arm3rad/s; native alpha0.2 remains',
    reset='reset only affected teacher rows; no physics step; first native-reset tick skips feedback',
    limitation='finite feedback target request; actual pose or3s arrival not guaranteed')


def interpolated_pose(initial_position, initial_quaternion, goal_position, goal_quaternion, fraction):
    goal_quaternion = torch.where((initial_quaternion*goal_quaternion).sum(-1, keepdim=True) < 0,
                                  -goal_quaternion, goal_quaternion)
    quaternion = initial_quaternion+fraction[:, None]*(goal_quaternion-initial_quaternion)
    quaternion = quaternion/torch.linalg.vector_norm(quaternion, dim=-1, keepdim=True).clamp_min(1e-12)
    position = initial_position+fraction[:, None]*(goal_position-initial_position)
    return position, quaternion


def wrist_error_and_jacobian(snapshot, wrist, guitar, com, columns, goal_position_G, goal_quaternion_G):
    body = snapshot['body_state']
    current = body[:, wrist]
    instrument = body[:, guitar]
    goal_world = instrument[:, :3]+apply(instrument[:, 3:7], goal_position_G)
    goal_rotation_world = multiply(instrument[:, 3:7], goal_quaternion_G)
    angular_error = rotvec(multiply(goal_rotation_world, conjugate(current[:, 3:7])))
    native = snapshot['jacobian'][:, wrist-1]
    linear = point_jacobian(native, apply(current[:, 3:7], -com))
    scale = WRIST_CONTROL['rotation_length_scale_m']
    jacobian = torch.cat((linear[:, :, columns], scale*native[:, 3:, columns]), dim=1)
    error = torch.cat((goal_world-current[:, :3], scale*angular_error), dim=1)
    return error, jacobian


def bounded_wrist_target(base, correction, previous_request, jacobian, error, feedback_active,
                         lower, upper, rate):
    # Stale reset-row Jacobians never enter the linear solve, even if nonfinite.
    jacobian = torch.where(feedback_active[:, None, None], jacobian, torch.zeros_like(jacobian))
    error = torch.where(feedback_active[:, None], error, torch.zeros_like(error))
    eye = torch.eye(6, device=base.device, dtype=base.dtype)
    delta = (jacobian.transpose(-1,-2)@torch.linalg.solve(
        jacobian@jacobian.transpose(-1,-2)+WRIST_CONTROL['damping']*eye, error[..., None])).squeeze(-1)
    step = WRIST_CONTROL['correction_step_rad']
    delta = delta.clamp(-step, step)
    desired = base+correction+delta
    desired = torch.maximum(torch.minimum(desired, previous_request+rate/60), previous_request-rate/60)
    desired = torch.maximum(torch.minimum(desired, upper), lower)
    return desired, desired-base, delta
