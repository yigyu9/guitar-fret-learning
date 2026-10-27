"""CPU contracts for the shared-task post-physics bridge."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.env.tasks.task_full import (  # noqa: E402
    FullG0SharedActuator,
    FullG0PhysicsSnapshot,
    FullG0TaskController,
    current_pose_hold_action,
)
from tab2body.full.action import FullActionManifest  # noqa: E402
from tab2body.full.runtime import G0RuntimeCommand  # noqa: E402


class _SpyRuntime:
    """Small runtime double for the controller-only contract."""

    num_envs = 1
    device = torch.device("cpu")
    fret_postprocessor = None

    def __init__(self):
        self.reset_calls = []
        self.before_calls = 0
        self.commit_calls = []
        self.after_calls = 0
        self.command = G0RuntimeCommand(
            decision=None, event=None, action=None,
            actor_fret_action=torch.zeros(1, 30),
            actor_strike_action=torch.zeros(1, 30),
            actor_fret_observation=torch.zeros(1, 420),
            actor_strike_observation=torch.zeros(1, 303))

    def reset(self, hold_action, env_ids=None):
        self.reset_calls.append((hold_action, env_ids))

    def before_physics(self, **kwargs):
        self.before_calls += 1
        return self.command

    def commit_executed_action(self, value):
        self.commit_calls.append(value)

    def after_physics(self, **kwargs):
        self.after_calls += 1
        return "synchronizer-result"


# FullG0TaskController intentionally requires the concrete runtime type.  Use
# a tiny concrete subclass so the test stays independent of local checkpoints.
from tab2body.full.runtime import G0SynchronizationRuntime  # noqa: E402,E501


class _ConcreteSpyRuntime(_SpyRuntime, G0SynchronizationRuntime):
    pass


def _snapshot(*, action_value=0.0):
    return FullG0PhysicsSnapshot(
        executed_full_action=torch.full(
            (1, 105), action_value, dtype=torch.float32),
        crossing_mask=torch.zeros(1, 6, dtype=torch.bool),
        crossing_subframe_t=torch.zeros(1, 6, dtype=torch.float32),
        crossing_direction=torch.zeros(1, 6, dtype=torch.int8),
        fret_ready_mask=torch.ones(1, 6, dtype=torch.bool),
    )


def _step(controller, runtime, snapshot):
    zero_fret = torch.zeros(1, 420, dtype=torch.float32)
    zero_strike = torch.zeros(1, 303, dtype=torch.float32)
    hold = torch.zeros(1, 105, dtype=torch.float32)
    ready = torch.ones(1, 6, dtype=torch.bool)
    return controller.step(
        fret_observation=zero_fret,
        strike_observation=zero_strike,
        hold_action=hold,
        fret_ready_mask=ready,
        strike_ready=torch.ones(1, dtype=torch.bool),
        guitar_stable=torch.ones(1, dtype=torch.bool),
        simulate_once=lambda command: snapshot,
    )


def test_bridge_executes_one_simulation_and_commits_exact_action():
    runtime = _ConcreteSpyRuntime()
    controller = FullG0TaskController(runtime)
    hold = torch.zeros(1, 105, dtype=torch.float32)
    controller.reset(hold)

    result = _step(controller, runtime, _snapshot(action_value=0.25))

    assert result.synchronization == "synchronizer-result"
    assert runtime.before_calls == 1
    assert runtime.after_calls == 1
    assert len(runtime.commit_calls) == 1
    assert torch.equal(runtime.commit_calls[0], result.physics.executed_full_action)
    assert len(runtime.reset_calls) == 1


def test_bridge_rejects_malformed_post_physics_action_before_commit():
    runtime = _ConcreteSpyRuntime()
    controller = FullG0TaskController(runtime)
    invalid = _snapshot(action_value=1.25)

    try:
        _step(controller, runtime, invalid)
    except ValueError as exc:
        assert "executed_full_action" in str(exc)
    else:
        raise AssertionError("malformed post-physics action was accepted")

    assert runtime.before_calls == 1
    assert runtime.commit_calls == []
    assert runtime.after_calls == 0


def test_current_pose_hold_inverts_the_first_shared_ema_update():
    q_now = torch.tensor([[0.25, -0.5]], dtype=torch.float32)
    mid = torch.zeros_like(q_now)
    half = torch.ones_like(q_now)
    previous = torch.tensor([[-0.25, 0.0]], dtype=torch.float32)
    hold = current_pose_hold_action(
        q_now, previous, mid, half,
        action_scale=1.0, action_alpha=0.5)

    executed = 0.5 * previous + 0.5 * hold.pre_ema_action
    assert torch.allclose(executed, hold.pose_action)
    assert torch.allclose(executed, q_now)
    assert not bool(hold.saturated.any().item())


def test_current_pose_hold_exposes_unrepresentable_first_frame():
    q_now = torch.tensor([[0.9]], dtype=torch.float32)
    previous = torch.tensor([[-0.9]], dtype=torch.float32)
    hold = current_pose_hold_action(
        q_now, previous, torch.zeros_like(q_now), torch.ones_like(q_now),
        action_scale=1.0, action_alpha=0.9)

    assert bool(hold.saturated.item())
    assert torch.equal(hold.pre_ema_action, torch.ones_like(q_now))


class _FakeSharedBackend:
    def __init__(self):
        self.num_envs = 1
        self.device = torch.device("cpu")
        self.dof_names = [f"J{i}" for i in range(97)]
        self.n_dof = len(self.dof_names)
        self.dof_lower = torch.full((self.n_dof,), -1.0)
        self.dof_upper = torch.full((self.n_dof,), 1.0)
        self.dof_state = torch.zeros(self.n_dof, 2)
        self.pd_target = torch.zeros(self.n_dof)
        self.init_pose = torch.zeros(self.n_dof)
        self.action_alpha = 0.5
        self.action_scale = 1.0
        self.steps = 0
        self.refreshes = 0

    def step_physics(self):
        self.steps += 1

    def refresh(self):
        self.refreshes += 1


def test_shared_actuator_maps_105d_by_name_and_steps_once():
    names = tuple(f"J{i}" for i in range(105))
    manifest = FullActionManifest.from_joint_names(
        names, fret_action_names=names[:30],
        strike_action_names=names[30:60])
    backend = _FakeSharedBackend()
    actuator = FullG0SharedActuator(backend, manifest)
    command = torch.full((1, 105), 0.4, dtype=torch.float32)

    executed = actuator.apply_and_step(command)

    assert backend.steps == 1
    assert backend.refreshes == 1
    assert actuator.physics_step_count == 1
    assert torch.allclose(executed[:, :97], torch.full((1, 97), 0.2))
    assert torch.equal(executed[:, 97:], torch.zeros(1, 8))
    assert torch.allclose(backend.pd_target, torch.full((97,), 0.2))


def test_shared_actuator_latches_first_strike_hold_pose():
    names = tuple(f"J{i}" for i in range(105))
    manifest = FullActionManifest.from_joint_names(
        names, fret_action_names=names[:30],
        strike_action_names=names[30:60])
    backend = _FakeSharedBackend()
    actuator = FullG0SharedActuator(backend, manifest)
    strike_sim = torch.arange(30, 60)
    backend.dof_state[strike_sim, 0] = 0.2

    first = actuator.strike_entry_hold()
    actuator.commit_strike_hold(torch.tensor([True]), first.pose_action)
    actuator.previous_full_action[:, actuator.strike_indices] = (
        first.pose_action)
    # Simulate inertia after the entry frame.  The next hold target must stay
    # at the latched 0.2 action rather than following the new 0.35 pose.
    backend.dof_state[strike_sim, 0] = 0.35
    second = actuator.strike_entry_hold()

    assert torch.allclose(
        second.pose_action, torch.full((1, 30), 0.2))
    assert torch.allclose(
        second.pre_ema_action, torch.full((1, 30), 0.2))
    actuator.commit_strike_hold(torch.tensor([False]), second.pose_action)
    third = actuator.strike_entry_hold()
    assert torch.allclose(
        third.pose_action, torch.full((1, 30), 0.35))


def test_shared_actuator_first_hold_can_brake_against_joint_velocity():
    names = tuple(f"J{i}" for i in range(105))
    manifest = FullActionManifest.from_joint_names(
        names, fret_action_names=names[:30],
        strike_action_names=names[30:60])
    backend = _FakeSharedBackend()
    actuator = FullG0SharedActuator(backend, manifest)
    strike_sim = torch.arange(30, 60)
    backend.dof_state[strike_sim, 0] = 0.2
    backend.dof_state[strike_sim, 1] = 0.2

    hold = actuator.strike_entry_hold(braking_horizon_s=0.5)

    assert torch.allclose(hold.pose_action, torch.full((1, 30), 0.1))
    assert torch.allclose(hold.pre_ema_action, torch.full((1, 30), 0.2))


def main():
    test_bridge_executes_one_simulation_and_commits_exact_action()
    test_bridge_rejects_malformed_post_physics_action_before_commit()
    test_current_pose_hold_inverts_the_first_shared_ema_update()
    test_current_pose_hold_exposes_unrepresentable_first_frame()
    test_shared_actuator_maps_105d_by_name_and_steps_once()
    test_shared_actuator_latches_first_strike_hold_pose()
    test_shared_actuator_first_hold_can_brake_against_joint_velocity()
    print("PASS: Full G0 task bridge")


if __name__ == "__main__":
    main()
