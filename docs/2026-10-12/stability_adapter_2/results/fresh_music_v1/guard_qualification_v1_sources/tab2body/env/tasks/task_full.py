"""One-step integration boundary for the fixed-guitar G0 Full player.

This module intentionally does not instantiate ``FretTask`` and ``StrikeTask``:
each of those owns a different Isaac simulator.  Instead it defines the exact
control-loop seam that a single-simulator backend must implement while the
policy/timeline/Synchronizer logic lives in :mod:`tab2body.full`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import torch

from tab2body.full.action import FULL_ACTION_DIM, FullActionManifest
from tab2body.full.runtime import G0RuntimeCommand, G0SynchronizationRuntime
from tab2body.full.synchronizer import (
    N_GUITAR_STRINGS,
    SynchronizerResult,
)


FULL_G0_TASK_BRIDGE_SCHEMA = "tab2body.full_g0_task_bridge.v2"


@dataclass(frozen=True)
class CurrentPoseHold:
    """Pre-EMA command that makes the next PD target equal ``q_now``.

    ``pose_action`` is the normalized post-EMA action corresponding to the
    measured pose.  ``pre_ema_action`` is the value that must be fed through
    the one shared actuator EMA on the first hold frame.  A saturated row is
    not an exact hold and must remain visible to the physical rollout audit.
    """

    pre_ema_action: torch.Tensor
    pose_action: torch.Tensor
    saturated: torch.Tensor


def current_pose_hold_action(
        q_now: torch.Tensor, previous_post_ema_action: torch.Tensor,
        control_mid: torch.Tensor, control_half: torch.Tensor, *,
        action_scale: float, action_alpha: float,
        tolerance: float = 1e-6) -> CurrentPoseHold:
    """Invert the shared EMA/PD transform for an exact first-frame hold.

    All tensors use source-action order and have shape ``[N,D]``.  Zero-range
    joints are represented by a normalized action of zero.  The returned
    saturation mask has shape ``[N]`` and is true when an exact one-frame hold
    cannot be expressed inside the normalized action range.
    """
    tensors = {
        "q_now": q_now,
        "previous_post_ema_action": previous_post_ema_action,
        "control_mid": control_mid,
        "control_half": control_half,
    }
    shape = tuple(q_now.shape) if isinstance(q_now, torch.Tensor) else None
    if shape is None or len(shape) != 2:
        raise ValueError("q_now must have shape [N,D]")
    for name, value in tensors.items():
        if (not isinstance(value, torch.Tensor)
                or tuple(value.shape) != shape
                or value.dtype != q_now.dtype
                or value.device != q_now.device
                or not value.is_floating_point()
                or not torch.isfinite(value).all()):
            raise ValueError(
                f"{name} must be a finite floating tensor with shape {shape} "
                "on the same device and dtype as q_now")
    scale = float(action_scale)
    alpha = float(action_alpha)
    if not scale > 0.0:
        raise ValueError("action_scale must be positive")
    if not 0.0 <= alpha < 1.0:
        raise ValueError("action_alpha must be in [0,1)")
    if tolerance < 0.0:
        raise ValueError("tolerance must be non-negative")

    movable = control_half > tolerance
    safe_half = torch.where(
        movable, control_half, torch.ones_like(control_half))
    pose_action_unclamped = (
        (q_now - control_mid) / (scale * safe_half))
    pose_action_unclamped = torch.where(
        movable, pose_action_unclamped,
        torch.zeros_like(pose_action_unclamped))
    pose_action = pose_action_unclamped.clamp(-1.0, 1.0)
    pre_ema_unclamped = (
        pose_action - alpha * previous_post_ema_action) / (1.0 - alpha)
    saturated = (
        (pose_action_unclamped.abs() > 1.0 + tolerance)
        | (pre_ema_unclamped.abs() > 1.0 + tolerance)
    ).any(dim=1)
    return CurrentPoseHold(
        pre_ema_action=pre_ema_unclamped.clamp(-1.0, 1.0),
        pose_action=pose_action,
        saturated=saturated,
    )


class FullG0SharedActuator:
    """Map the named 105D ABI onto one shared Isaac humanoid actuator.

    Isaac omits authored zero-range joints from its DOF tensor, so direct
    positional slicing of a 105D command is invalid.  This adapter performs a
    one-time name mapping, owns the one common EMA state, updates the shared
    PD target once, and advances physics once.  Missing authored joints remain
    explicit zero-valued slots in the external ABI.
    """

    def __init__(self, backend, manifest: FullActionManifest):
        if not isinstance(manifest, FullActionManifest):
            raise TypeError("manifest must be a FullActionManifest")
        for name in (
                "num_envs", "device", "n_dof", "dof_names", "dof_lower",
                "dof_upper", "dof_state", "pd_target", "init_pose",
                "action_alpha", "action_scale", "step_physics", "refresh"):
            if not hasattr(backend, name):
                raise TypeError(f"shared backend is missing {name}")
        if not 0.0 <= float(backend.action_alpha) < 1.0:
            raise ValueError("shared backend action_alpha must be in [0,1)")
        if float(backend.action_scale) <= 0.0:
            raise ValueError("shared backend action_scale must be positive")
        names = tuple(str(name) for name in backend.dof_names)
        if len(names) != int(backend.n_dof) or len(set(names)) != len(names):
            raise ValueError("shared backend DOF names must be unique")
        full_index = {name: i for i, name in enumerate(manifest.joint_names)}
        unknown = sorted(set(names) - set(full_index))
        if unknown:
            raise ValueError(
                f"Isaac backend has joints outside the Full ABI: {unknown}")

        self.backend = backend
        self.manifest = manifest
        self.num_envs = int(backend.num_envs)
        self.device = torch.device(backend.device)
        self.dtype = backend.dof_state.dtype
        self.action_alpha = float(backend.action_alpha)
        self.action_scale = float(backend.action_scale)
        self.sim_full_indices = torch.as_tensor(
            [full_index[name] for name in names],
            dtype=torch.long, device=self.device)
        self.fret_indices = torch.as_tensor(
            manifest.fret_indices, dtype=torch.long, device=self.device)
        self.strike_indices = torch.as_tensor(
            manifest.strike_indices, dtype=torch.long, device=self.device)

        lower = backend.dof_lower.view(
            self.num_envs, int(backend.n_dof))
        upper = backend.dof_upper.view(
            self.num_envs, int(backend.n_dof))
        self.full_mid = torch.zeros(
            self.num_envs, FULL_ACTION_DIM,
            dtype=self.dtype, device=self.device)
        self.full_half = torch.zeros_like(self.full_mid)
        self.full_mid[:, self.sim_full_indices] = 0.5 * (lower + upper)
        self.full_half[:, self.sim_full_indices] = 0.5 * (upper - lower)
        self.physically_mapped_mask = torch.zeros(
            FULL_ACTION_DIM, dtype=torch.bool, device=self.device)
        self.physically_mapped_mask[self.sim_full_indices] = True
        self.physically_movable_mask = (
            self.physically_mapped_mask[None]
            & (self.full_half > 1e-8)).all(dim=0)
        self.previous_full_action = torch.zeros_like(self.full_mid)
        self._strike_hold_active = torch.zeros(
            self.num_envs, dtype=torch.bool, device=self.device)
        self._strike_hold_pose_action = torch.zeros(
            self.num_envs, len(manifest.strike_indices),
            dtype=self.dtype, device=self.device)
        self.physics_step_count = 0
        self.reset_from_physics()

    def _full_q(self):
        q = self.backend.dof_state.view(
            self.num_envs, int(self.backend.n_dof), 2)[:, :, 0]
        full_q = self.full_mid.clone()
        full_q[:, self.sim_full_indices] = q
        return full_q

    def _full_qd(self):
        qd = self.backend.dof_state.view(
            self.num_envs, int(self.backend.n_dof), 2)[:, :, 1]
        full_qd = torch.zeros_like(self.full_mid)
        full_qd[:, self.sim_full_indices] = qd
        return full_qd

    def action_for_pose(self, full_q: torch.Tensor):
        if (not isinstance(full_q, torch.Tensor)
                or full_q.shape != self.full_mid.shape
                or full_q.dtype != self.dtype
                or full_q.device != self.device
                or not torch.isfinite(full_q).all()):
            raise ValueError("full_q must be finite and match the 105D actuator")
        movable = self.full_half > 1e-8
        safe_half = torch.where(
            movable, self.full_half, torch.ones_like(self.full_half))
        action = (full_q - self.full_mid) / (
            self.action_scale * safe_half)
        return torch.where(
            movable, action, torch.zeros_like(action)).clamp(-1.0, 1.0)

    def reset_from_physics(self, env_ids=None):
        full_q = self._full_q()
        action = self.action_for_pose(full_q)
        if env_ids is None:
            self.previous_full_action.copy_(action)
            self._strike_hold_active.zero_()
            self._strike_hold_pose_action.zero_()
        else:
            ids = torch.as_tensor(
                env_ids, dtype=torch.long, device=self.device).reshape(-1)
            self.previous_full_action[ids] = action[ids]
            self._strike_hold_active[ids] = False
            self._strike_hold_pose_action[ids] = 0.0
        return action

    def strike_entry_hold(
            self, *, braking_horizon_s: float = 0.0) -> CurrentPoseHold:
        horizon = float(braking_horizon_s)
        if not 0.0 <= horizon < float("inf"):
            raise ValueError("braking_horizon_s must be finite and non-negative")
        q = self._full_q()[:, self.strike_indices]
        if horizon:
            q = q - horizon * self._full_qd()[:, self.strike_indices]
        current = current_pose_hold_action(
            q, self.previous_full_action[:, self.strike_indices],
            self.full_mid[:, self.strike_indices],
            self.full_half[:, self.strike_indices],
            action_scale=self.action_scale,
            action_alpha=self.action_alpha)
        desired = torch.where(
            self._strike_hold_active[:, None],
            self._strike_hold_pose_action, current.pose_action)
        pre_ema_unclamped = (
            desired
            - self.action_alpha
            * self.previous_full_action[:, self.strike_indices]
        ) / (1.0 - self.action_alpha)
        saturated = (
            current.saturated & ~self._strike_hold_active
        ) | (pre_ema_unclamped.abs() > 1.0 + 1e-6).any(dim=1)
        return CurrentPoseHold(
            pre_ema_action=pre_ema_unclamped.clamp(-1.0, 1.0),
            pose_action=desired,
            saturated=saturated)

    def commit_strike_hold(
            self, hold_mask: torch.Tensor,
            candidate_pose_action: torch.Tensor) -> None:
        """Latch the first physical entry pose until the supervisor releases it."""
        mask = torch.as_tensor(
            hold_mask, dtype=torch.bool, device=self.device)
        if mask.shape != (self.num_envs,):
            raise ValueError("hold_mask must have shape [N]")
        if (not isinstance(candidate_pose_action, torch.Tensor)
                or candidate_pose_action.shape
                != self._strike_hold_pose_action.shape
                or candidate_pose_action.dtype != self.dtype
                or candidate_pose_action.device != self.device
                or not torch.isfinite(candidate_pose_action).all()):
            raise ValueError(
                "candidate_pose_action must be finite Strike source actions")
        entering = mask & ~self._strike_hold_active
        self._strike_hold_pose_action[entering] = (
            candidate_pose_action[entering])
        self._strike_hold_active.copy_(mask)

    def apply_and_step(self, full_command: torch.Tensor) -> torch.Tensor:
        if (not isinstance(full_command, torch.Tensor)
                or full_command.shape
                != (self.num_envs, FULL_ACTION_DIM)
                or full_command.dtype != self.dtype
                or full_command.device != self.device
                or not torch.isfinite(full_command).all()):
            raise ValueError(
                "full_command must be finite and match the 105D actuator")
        if bool((full_command.abs() > 1.0 + 1e-6).any().item()):
            raise ValueError("full_command must remain in [-1,1]")
        executed = (
            self.action_alpha * self.previous_full_action
            + (1.0 - self.action_alpha) * full_command.clamp(-1.0, 1.0))
        # Authored zero-range joints have no Isaac DOF.  Keep those ABI slots
        # deterministic instead of pretending an actuator executed them.
        executed = torch.where(
            self.physically_mapped_mask[None], executed,
            torch.zeros_like(executed))
        self.previous_full_action.copy_(executed)

        target = (
            self.full_mid
            + self.action_scale * executed * self.full_half)
        sim_target = target[:, self.sim_full_indices]
        sim_lo = self.backend.dof_lower.view(
            self.num_envs, int(self.backend.n_dof))
        sim_hi = self.backend.dof_upper.view(
            self.num_envs, int(self.backend.n_dof))
        sim_target = torch.maximum(torch.minimum(sim_target, sim_hi), sim_lo)
        self.backend.pd_target.view(
            self.num_envs, int(self.backend.n_dof)).copy_(sim_target)
        self.backend.step_physics()
        self.backend.refresh()
        self.physics_step_count += 1
        return executed.clone()


@dataclass(frozen=True)
class FullG0PhysicsSnapshot:
    """Post-step facts returned by one shared Isaac physics backend.

    ``executed_full_action`` is the normalized action after the one common EMA
    update.  ``crossing_mask``, ``crossing_subframe_t`` and
    ``crossing_direction`` are the detector's ``release``, ``subframe_t`` and
    ``direction`` facts from exactly that same physics step.  The backend
    receives the Synchronizer decision before simulation and is responsible for
    enforcing its release boundary; any physical crossing while closed is still
    reported for audit.  This bridge does not claim that the future physical
    entry-plane barrier already exists.
    """

    executed_full_action: torch.Tensor
    crossing_mask: torch.Tensor
    crossing_subframe_t: torch.Tensor
    crossing_direction: torch.Tensor
    fret_ready_mask: torch.Tensor

    def validate(self, *, num_envs: int, device) -> "FullG0PhysicsSnapshot":
        """Validate the post-physics ABI before it mutates runtime history.

        The Synchronizer validates these values too, but keeping the check at
        the shared-task boundary makes a malformed Isaac result fail before
        the runtime commits any source action history.  No casts or clamps are
        performed: the backend must return the exact normalized/detector ABI.
        """
        expected_device = torch.device(device)
        batch = int(num_envs)

        def require_tensor(value, *, shape, dtype, name):
            if (not isinstance(value, torch.Tensor)
                    or tuple(value.shape) != tuple(shape)
                    or value.dtype != dtype
                    or value.device != expected_device):
                raise ValueError(
                    f"{name} must be {dtype} {tuple(shape)} on "
                    f"{expected_device}")
            if value.is_floating_point() and not torch.isfinite(value).all():
                raise ValueError(f"{name} must be finite")

        action_shape = (batch, 105)
        string_shape = (batch, N_GUITAR_STRINGS)
        require_tensor(
            self.executed_full_action, shape=action_shape,
            dtype=torch.float32, name="executed_full_action")
        require_tensor(
            self.crossing_mask, shape=string_shape,
            dtype=torch.bool, name="crossing_mask")
        require_tensor(
            self.crossing_subframe_t, shape=string_shape,
            dtype=torch.float32, name="crossing_subframe_t")
        require_tensor(
            self.crossing_direction, shape=string_shape,
            dtype=torch.int8, name="crossing_direction")
        require_tensor(
            self.fret_ready_mask, shape=string_shape,
            dtype=torch.bool, name="fret_ready_mask")

        if bool((self.executed_full_action.abs() > 1.0 + 1e-6).any().item()):
            raise ValueError("executed_full_action must remain in [-1,1]")
        if bool((self.crossing_mask & (
                (self.crossing_subframe_t < 0.0)
                | (self.crossing_subframe_t > 1.0))).any().item()):
            raise ValueError(
                "crossing_subframe_t must be in [0,1] for every crossing")
        if bool(((self.crossing_direction < -1)
                 | (self.crossing_direction > 1)).any().item()):
            raise ValueError(
                "crossing_direction entries must be -1, 0, or +1")
        if bool((self.crossing_mask & (
                (self.crossing_direction != -1)
                & (self.crossing_direction != 1))).any().item()):
            raise ValueError(
                "crossing_direction must be -1 or +1 for every crossing")
        return self


@dataclass(frozen=True)
class FullG0Step:
    command: G0RuntimeCommand
    physics: FullG0PhysicsSnapshot
    synchronization: SynchronizerResult


class FullG0TaskController:
    """Run one command/physics/result transaction without double stepping.

    The callable supplied as ``simulate_once`` is the narrow adapter point for
    the future Isaac ``GuitarEnvBase`` implementation.  It is invoked exactly
    once with the 105D pre-EMA command and the timing decision.
    """

    def __init__(self, runtime: G0SynchronizationRuntime):
        if not isinstance(runtime, G0SynchronizationRuntime):
            raise TypeError("runtime must be a G0SynchronizationRuntime")
        self.runtime = runtime

    def reset(self, hold_action: torch.Tensor, env_ids=None):
        self.runtime.reset(hold_action, env_ids=env_ids)

    def step(
            self, *, fret_observation: torch.Tensor,
            strike_observation: torch.Tensor, hold_action: torch.Tensor,
            fret_ready_mask: torch.Tensor, strike_ready: torch.Tensor,
            guitar_stable: torch.Tensor,
            strike_entry_hold_action: torch.Tensor = None,
            fret_current_finger_active: torch.Tensor = None,
            fret_finger_event: torch.Tensor = None,
            simulate_once: Callable[[G0RuntimeCommand], FullG0PhysicsSnapshot]
            ) -> FullG0Step:
        if not callable(simulate_once):
            raise TypeError("simulate_once must be callable")
        fret_postprocessor = self.runtime.fret_postprocessor
        if fret_postprocessor is not None:
            if (fret_current_finger_active is None
                    or fret_finger_event is None):
                raise ValueError(
                    "physical G0 step requires current Fret finger state for "
                    "the source-exact synergy transform")
            fret_postprocessor.prepare_step(
                current_finger_active=fret_current_finger_active,
                finger_event=fret_finger_event)
        elif (fret_current_finger_active is not None
              or fret_finger_event is not None):
            raise ValueError(
                "Fret postprocessing state was supplied to an identity probe")
        command = self.runtime.before_physics(
            fret_observation=fret_observation,
            strike_observation=strike_observation,
            hold_action=hold_action,
            fret_ready_mask=fret_ready_mask,
            strike_ready=strike_ready,
            guitar_stable=guitar_stable,
            strike_entry_hold_action=strike_entry_hold_action)
        physics = simulate_once(command)
        if not isinstance(physics, FullG0PhysicsSnapshot):
            raise TypeError(
                "simulate_once must return FullG0PhysicsSnapshot")
        physics.validate(
            num_envs=self.runtime.num_envs, device=self.runtime.device)
        self.runtime.commit_executed_action(physics.executed_full_action)
        result = self.runtime.after_physics(
            crossing_mask=physics.crossing_mask,
            crossing_subframe_t=physics.crossing_subframe_t,
            crossing_direction=physics.crossing_direction,
            fret_ready_mask=physics.fret_ready_mask)
        return FullG0Step(
            command=command, physics=physics, synchronization=result)


__all__ = [
    "CurrentPoseHold",
    "FULL_G0_TASK_BRIDGE_SCHEMA",
    "FullG0SharedActuator",
    "FullG0PhysicsSnapshot",
    "FullG0Step",
    "FullG0TaskController",
    "current_pose_hold_action",
]
