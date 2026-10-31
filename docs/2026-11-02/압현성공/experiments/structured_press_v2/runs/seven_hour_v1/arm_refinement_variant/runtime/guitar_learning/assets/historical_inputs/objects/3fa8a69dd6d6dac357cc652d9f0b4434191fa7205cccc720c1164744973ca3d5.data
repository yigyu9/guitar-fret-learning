"""CPU contracts for a Fret policy view on one shared physical backend."""
from __future__ import annotations

import numpy as np
from pathlib import Path
import sys
from types import SimpleNamespace

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.env.base import GuitarEnvBase
from tab2body.env.collision import (
    DISABLED_COLLISION_FILTER,
    GUITAR_COLLISION_FILTER,
    HUMANOID_COLLISION_FILTER,
)
from tab2body.env.tasks.task_fret import (
    FRET_OBS_BODIES,
    FRET_POLICY_ACTION_NAMES,
    FretTask,
)
import torch


def _fake_backend(num_envs=2):
    backend = GuitarEnvBase.__new__(GuitarEnvBase)
    backend.num_envs = num_envs
    backend.device = "cpu"
    backend.locked_dof_keywords = ("Hip", "Knee", "Ankle", "Toe")
    backend.human_hard_limits_enabled = False
    backend.human_hard_limit_path = None
    backend.pose = {"params": {}}
    backend.P = backend.pose["params"]
    backend._gains_src = {}
    backend.gym = backend.sim = object()
    backend.asset_human = backend.asset_guitar = backend.asset_chair = object()
    backend.envs = [object() for _ in range(num_envs)]
    backend.h_actors = [object() for _ in range(num_envs)]
    backend.g_actors = [object() for _ in range(num_envs)]
    backend.dof_names = list(FRET_POLICY_ACTION_NAMES) + ["R_Wrist_x"]
    backend.body_names = list(FRET_OBS_BODIES)
    backend.gbody_names = ["guitar"]
    backend._init_pose_np = np.zeros(len(backend.dof_names), dtype=np.float32)
    backend._kp_np = np.ones(len(backend.dof_names), dtype=np.float32)
    backend._kd_np = np.ones(len(backend.dof_names), dtype=np.float32)
    backend._authored_dof_lower_np = -np.ones(
        len(backend.dof_names), dtype=np.float32)
    backend._authored_dof_upper_np = np.ones(
        len(backend.dof_names), dtype=np.float32)
    backend._dof_props = object()
    backend.human_hard_limit_audit = {"enabled": False}
    backend.collision_audit = {"thumb_support_enabled": False}

    n_dof = len(backend.dof_names)
    backend.n_dof = n_dof
    backend.n_hbody = len(backend.body_names)
    backend._bpe = len(backend.body_names)
    backend.hbody_index = {
        name: index for index, name in enumerate(backend.body_names)}
    backend.gbody_index = {"guitar": 0}
    backend.dof_state = torch.zeros(num_envs * n_dof, 2)
    backend.root_state = torch.zeros(num_envs * 3, 13)
    backend.body_state = torch.zeros(num_envs * backend._bpe, 13)
    backend.contact_force = torch.zeros(num_envs * backend._bpe, 3)
    backend.locked = torch.zeros(n_dof, dtype=torch.bool)
    backend._locked_flat = backend.locked.repeat(num_envs)
    backend._zeros_dof = torch.zeros(num_envs * n_dof)
    backend.kp = torch.ones(num_envs * n_dof)
    backend.tau_limit = torch.ones(num_envs * n_dof)
    backend.applied_tau = torch.zeros(num_envs, n_dof)
    backend.dof_lower = -torch.ones(num_envs * n_dof)
    backend.dof_upper = torch.ones(num_envs * n_dof)
    backend.authored_dof_lower = -torch.ones(n_dof)
    backend.authored_dof_upper = torch.ones(n_dof)
    backend.raw_init_pose = torch.zeros(n_dof)
    backend.init_pose_limit_adjustment = torch.zeros(n_dof)
    backend.init_pose = torch.zeros(n_dof)
    backend.pd_target = torch.zeros(num_envs * n_dof)
    backend.nonlocked_idx = torch.arange(n_dof)
    backend.n_nonlocked = n_dof
    backend.root_init = backend.root_state.clone()
    backend.progress_buf = torch.zeros(num_envs, dtype=torch.long)
    backend.prev_action = torch.full((num_envs, 30), 0.25)
    return backend


def test_shared_fret_view_aliases_physics_but_owns_policy_state():
    backend = _fake_backend()
    view = GuitarEnvBase(
        num_envs=backend.num_envs,
        control_dofs=(
            "L_Shoulder", "L_Elbow", "L_Wrist", "LH:thumb",
            "LH:index", "LH:middle", "LH:ring", "LH:pinky"),
        device="cpu",
        obs_body_names=FRET_OBS_BODIES,
        shared_backend=backend,
    )

    assert view.gym is backend.gym and view.sim is backend.sim
    assert view.dof_state is backend.dof_state
    assert view.body_state is backend.body_state
    assert view.contact_force is backend.contact_force
    assert view.init_pose is backend.init_pose
    assert view.pd_target is backend.pd_target
    assert view.progress_buf is backend.progress_buf
    assert view.prev_action is not backend.prev_action
    assert view.reset_buf is not getattr(backend, "reset_buf", None)
    assert tuple(view.dof_names[index] for index in view.ctrl_idx.tolist()) \
        == FRET_POLICY_ACTION_NAMES

    view.progress_buf.add_(3)
    assert torch.equal(backend.progress_buf, torch.full((2,), 3))
    view.apply_actions(torch.ones(2, 30))
    assert torch.equal(backend.prev_action, torch.full((2, 30), 0.25))
    assert torch.count_nonzero(
        backend.pd_target.view(2, -1)[:, -1]).item() == 0


def test_shared_backend_rejects_a_different_batch():
    backend = _fake_backend(num_envs=2)
    try:
        GuitarEnvBase(
            num_envs=1, device="cpu", shared_backend=backend)
    except ValueError as exc:
        assert "num_envs" in str(exc)
    else:
        raise AssertionError("mismatched shared backend batch was accepted")


def test_shared_fret_view_cannot_own_reset_or_step():
    view = FretTask.__new__(FretTask)
    view._shared_backend = object()
    for operation in (
            lambda: view.reset(),
            lambda: view.reset_idx(torch.tensor([0])),
            lambda: view.step(torch.zeros(1, 30)),
            lambda: view.apply_actions(torch.zeros(1, 30))):
        try:
            operation()
        except RuntimeError as exc:
            assert "shared" in str(exc)
        else:
            raise AssertionError("shared Fret view mutated physical lifecycle")


class _FilterGym:
    def __init__(self, properties):
        self.properties = properties

    def get_actor_rigid_shape_properties(self, env, actor):
        return [SimpleNamespace(filter=value) for value in self.properties[actor]]

    def set_actor_rigid_shape_properties(self, env, actor, properties):
        self.properties[actor] = [int(value.filter) for value in properties]


def _collision_view(human_filters, guitar_filters):
    view = GuitarEnvBase.__new__(GuitarEnvBase)
    env, human, guitar = object(), object(), object()
    view.envs, view.h_actors, view.g_actors = [env], [human], [guitar]
    view.body_names, view.gbody_names = ["thumb"], ["proxy"]
    view.gym = _FilterGym({
        human: list(human_filters), guitar: list(guitar_filters)})
    view.collision_audit = {}
    view._body_shape_indices = lambda *args: (0,)
    return view, human, guitar


def test_thumb_support_preserves_strike_collision_filters():
    view, human, guitar = _collision_view(
        (DISABLED_COLLISION_FILTER, 123),
        (DISABLED_COLLISION_FILTER, 456))

    view.enable_thumb_support_collision(preserve_other_filters=True)

    assert view.gym.properties[human] == [GUITAR_COLLISION_FILTER, 123]
    assert view.gym.properties[guitar] == [HUMANOID_COLLISION_FILTER, 456]
    assert view.collision_audit["thumb_support_enabled"] is True

    standalone, _, _ = _collision_view(
        (GUITAR_COLLISION_FILTER, HUMANOID_COLLISION_FILTER),
        (HUMANOID_COLLISION_FILTER, GUITAR_COLLISION_FILTER))
    standalone._audit_thumb_support_collision()


def test_shared_backend_rejects_a_different_hard_limit_profile():
    backend = _fake_backend()
    backend.human_hard_limits_enabled = True
    backend.human_hard_limit_path = "/profiles/backend.json"
    try:
        GuitarEnvBase(
            num_envs=backend.num_envs, device="cpu",
            human_hard_limits_enabled=True,
            human_hard_limit_path="/profiles/view.json",
            shared_backend=backend)
    except ValueError as exc:
        assert "profile path" in str(exc)
    else:
        raise AssertionError("mismatched hard-limit profile was accepted")


def main():
    test_shared_fret_view_aliases_physics_but_owns_policy_state()
    test_shared_backend_rejects_a_different_batch()
    test_shared_fret_view_cannot_own_reset_or_step()
    test_thumb_support_preserves_strike_collision_filters()
    test_shared_backend_rejects_a_different_hard_limit_profile()
    print("PASS: shared Fret backend view")


if __name__ == "__main__":
    main()
