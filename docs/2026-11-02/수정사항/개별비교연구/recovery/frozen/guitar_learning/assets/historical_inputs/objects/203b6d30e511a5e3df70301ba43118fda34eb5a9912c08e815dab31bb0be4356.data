"""Compose 66 relative targets in float64 before submitting native float32 values."""
from .environment import np


def compose(initial, main_indices, offsets, lower, upper):
    offsets=np.asarray(offsets,dtype=np.float64)
    if offsets.shape!=(66,) or len(main_indices)!=66 or not np.isfinite(offsets).all() or np.any(np.abs(offsets)>.3):
        raise ValueError('66 finite relative offsets within +/-0.3rad required')
    target=np.asarray(initial,dtype=np.float64).copy();target[main_indices]+=offsets
    target=target.astype(np.float32)
    if not np.isfinite(target).all() or np.any(target<lower) or np.any(target>upper):
        raise ValueError('composed native target outside bounds; no clipping')
    return target


def submit(env, offsets):
    target=compose(env.initial_q,env.main_indices,offsets,env.lower,env.upper)
    if not env.gym.set_actor_dof_position_targets(env.env,env.human,target):
        raise RuntimeError('native position-target setter failed')
    env.target=target
