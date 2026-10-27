import os
import json
import math
import numpy as np
import isaacgym
from isaacgym import gymapi, gymtorch
import torch

from .collision import (
    DISABLED_COLLISION_FILTER,
    GUITAR_COLLISION_FILTER,
    HUMANOID_COLLISION_FILTER,
    SHAPE_CONTACT_OFFSET,
    THUMB_PAD_BODY,
    THUMB_SUPPORT_PROXY_BODY,
)
from .safety import dof_torque_limit
from .joint_limits import apply_joint_limit_profile

# quaternion helpers (xyzw), defined locally: isaacgym.torch_utils imports fail on this numpy
# (np.float deprecation). These are the standard Isaac forms.
def quat_rotate_inverse(q, v):
    """rotate vec v (N,3) by the inverse of quat q (N,4 xyzw)."""
    q_w = q[:, 3:4]; q_vec = q[:, 0:3]
    a = v * (2.0 * q_w * q_w - 1.0)
    b = torch.cross(q_vec, v, dim=-1) * (2.0 * q_w)
    c = q_vec * (torch.sum(q_vec * v, dim=-1, keepdim=True) * 2.0)
    return a - b + c


def quat_rotate(q, v):
    """Rotate vector ``v`` by quaternion ``q`` (xyzw)."""
    q_w = q[:, 3:4]; q_vec = q[:, 0:3]
    a = v * (2.0 * q_w * q_w - 1.0)
    b = torch.cross(q_vec, v, dim=-1) * (2.0 * q_w)
    c = q_vec * (torch.sum(q_vec * v, dim=-1, keepdim=True) * 2.0)
    return a + b + c


HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.abspath(os.path.join(HERE, '..', 'assets'))
GEN = os.path.abspath(os.path.join(HERE, '..', '_gen'))

# Lower body = "furniture": held rigid at the seated pose, out of the policy's control. Kept stable
# by THREE layers, each closing a measured failure mode (tools/hold_compare.py, verify_stability.py):
#   1. pinch limits (lower==upper==pose±1e-4) — a HARD kinematic constraint. Soft hybrid PD alone
#      can't hold the leg: its gravity torque saturates the 300 N·m clamp and it drifts 60°+.
#   2. high armature on the locked dofs — sluggish inertia kills the ~30Hz sub-step limit tremor
#      (0.10° p2p -> 0.0015°). Only touches furniture dofs, so training is unaffected.
#   3. per-step re-inject to init (step_physics) — removes the slow (~0.7°/50s) settle of the soft
#      limit under sustained gravity. (DIGIT double-enforced the pinch the same way.)
# Net: 0.0000° lower-body drift over 50 s (verify_stability). The legs sit at the floor-grounded
# angles solved by tools/foot_settle.py (feet flat, ~1 cm above the floor; no foot-floor contact,
# which would re-introduce a pinch-vs-contact tremor — see the design doc).
LOCK_KEYWORDS = ('Hip', 'Knee', 'Ankle', 'Toe')
LOCKED_ARMATURE = 10.0
class GuitarEnvBase:
    SIM_HZ = 60
    SUBSTEPS = 4

    def __init__(self, num_envs=512, control_dofs=None, device='cuda:0', headless=True,
                 seed=0, max_episode_length=300, action_alpha=0.5, action_scale=1.0,
                 reset_noise=0.0, reset_soft_limit_fraction=0.0,
                 human_hard_limits_enabled=False,
                 human_hard_limit_path=None,
                 obs_body_names=('L_Wrist', 'R_Wrist'),
                 locked_dof_keywords=LOCK_KEYWORDS,
                 shared_backend=None):
        """control_dofs: dof-name prefixes the policy controls (task decides); the rest are held.
        max_episode_length: control steps per episode. action_alpha: EMA smoothing on actions.
        action_scale: PD-target scale (1.0 maps bounded actions one-to-one to limits).
        reset_noise: RSI
        exploration noise (rad) on controlled dofs. obs_body_names: humanoid bodies whose
        guitar-relative position enters the base observation (tasks extend)."""
        self.num_envs = num_envs
        self.device = device
        self.max_episode_length = max_episode_length
        self.action_alpha = float(action_alpha)
        self.action_scale = float(action_scale)
        self.reset_noise = float(reset_noise)
        self.reset_soft_limit_fraction = float(reset_soft_limit_fraction)
        self.human_hard_limits_enabled = bool(human_hard_limits_enabled)
        self.human_hard_limit_path = (
            str(human_hard_limit_path) if human_hard_limit_path is not None
            else None)
        self.locked_dof_keywords = tuple(
            str(value) for value in locked_dof_keywords)
        if self.human_hard_limits_enabled and self.human_hard_limit_path is None:
            raise ValueError("human hard limit을 켜려면 profile path가 필요하다")
        if not 0.0 <= self.action_alpha <= 1.0:
            raise ValueError("action_alpha must be in [0, 1]")
        if not np.isfinite(self.action_scale) or self.action_scale <= 0.0:
            raise ValueError("action_scale must be finite and positive")
        if not np.isfinite(self.reset_noise) or self.reset_noise < 0.0:
            raise ValueError("reset_noise must be finite and non-negative")
        if (not np.isfinite(self.reset_soft_limit_fraction)
                or not 0.0 <= self.reset_soft_limit_fraction < 0.5):
            raise ValueError("reset_soft_limit_fraction must be in [0, 0.5)")
        self.obs_body_names = list(obs_body_names)
        self.rng = torch.Generator(device=device); self.rng.manual_seed(seed)
        self._shared_backend = shared_backend
        if shared_backend is None:
            self.pose = json.load(open(os.path.join(ASSETS, 'seated_pose.json')))
            self.P = self.pose['params']
            self._gains_src = json.load(open(os.path.join(GEN, 'mjcf_gains.json')))

            self.gym = gymapi.acquire_gym()
            self._create_sim(headless)
            self._load_assets()
            self._create_envs()
            self.gym.prepare_sim(self.sim)
            self._init_tensors(control_dofs or [])
        else:
            self._init_shared_backend(shared_backend, control_dofs or [])

    def _init_shared_backend(self, backend, control_prefixes):
        """Attach a task-local policy view to an existing physical backend.

        Simulator objects, state tensors, the authoritative pose/PD target and
        song clock are aliases.  Policy routing, action history, observations
        and termination bookkeeping are allocated for this view so one hand
        cannot overwrite the other hand's source-policy state.
        """
        if not isinstance(backend, GuitarEnvBase) or backend is self:
            raise TypeError("shared_backend must be another GuitarEnvBase")
        if int(self.num_envs) != int(backend.num_envs):
            raise ValueError(
                "shared_backend num_envs differs from the task view")
        if torch.device(self.device) != torch.device(backend.device):
            raise ValueError(
                "shared_backend device differs from the task view")
        if self.locked_dof_keywords != tuple(backend.locked_dof_keywords):
            raise ValueError(
                "shared_backend locked DOF contract differs from the task view")
        if (self.human_hard_limits_enabled
                != bool(backend.human_hard_limits_enabled)):
            raise ValueError(
                "shared_backend human hard-limit profile is already fixed")
        if self.human_hard_limits_enabled:
            requested_profile = os.path.realpath(self.human_hard_limit_path)
            backend_profile = os.path.realpath(
                backend.human_hard_limit_path)
            if requested_profile != backend_profile:
                raise ValueError(
                    "shared_backend human hard-limit profile path differs "
                    "from the task view")
            self.human_hard_limit_path = backend.human_hard_limit_path

        shared_names = (
            "pose", "P", "_gains_src", "gym", "sim", "asset_human",
            "asset_guitar", "asset_chair", "envs", "h_actors", "g_actors",
            "body_names", "gbody_names", "dof_names", "_init_pose_np",
            "_kp_np", "_kd_np", "_authored_dof_lower_np",
            "_authored_dof_upper_np", "_dof_props", "human_hard_limit_audit",
            "collision_audit", "dof_state", "root_state", "body_state",
            "contact_force", "locked", "_locked_flat", "_zeros_dof", "kp",
            "tau_limit", "applied_tau", "dof_lower", "dof_upper",
            "authored_dof_lower", "authored_dof_upper", "raw_init_pose",
            "init_pose_limit_adjustment", "init_pose", "pd_target",
            "nonlocked_idx", "root_init", "progress_buf",
        )
        for name in shared_names:
            if not hasattr(backend, name):
                raise RuntimeError(
                    f"shared_backend is not initialized: missing {name}")
            setattr(self, name, getattr(backend, name))
        for name in (
                "solver_position_iterations", "solver_velocity_iterations",
                "contact_collection_contract", "max_depenetration_velocity"):
            if hasattr(backend, name):
                setattr(self, name, getattr(backend, name))

        d = self.device
        self.n_dof = len(self.dof_names)
        self.n_hbody = len(self.body_names)
        self._bpe = backend._bpe
        self.hbody_index = backend.hbody_index
        self.gbody_index = backend.gbody_index
        self.n_nonlocked = backend.n_nonlocked

        self.controlled = torch.tensor(
            [any(name.startswith(prefix) for prefix in control_prefixes)
             and not any(keyword in name
                         for keyword in self.locked_dof_keywords)
             for name in self.dof_names], device=d)
        self.ctrl_idx = torch.nonzero(self.controlled).squeeze(-1)
        self.num_actions = int(self.controlled.sum())

        lower = self.dof_lower.view(
            self.num_envs, self.n_dof)[:, self.ctrl_idx].clone()
        upper = self.dof_upper.view(
            self.num_envs, self.n_dof)[:, self.ctrl_idx].clone()
        self.ctrl_lo, self.ctrl_hi = lower, upper
        self.ctrl_mid = 0.5 * (lower + upper)
        self.ctrl_half = 0.5 * (upper - lower)
        if (not torch.isfinite(self.ctrl_mid).all()
                or not torch.isfinite(self.ctrl_half).all()
                or not (self.ctrl_half > 0.0).all()):
            raise RuntimeError(
                "shared task view has an invalid controlled DOF range")

        full_lower = self.dof_lower.view(self.num_envs, self.n_dof)
        full_upper = self.dof_upper.view(self.num_envs, self.n_dof)
        span = full_upper - full_lower
        soft_lower = full_lower + self.reset_soft_limit_fraction * span
        soft_upper = full_upper - self.reset_soft_limit_fraction * span
        self.reset_ctrl_lo = soft_lower[:, self.ctrl_idx].clone()
        self.reset_ctrl_hi = soft_upper[:, self.ctrl_idx].clone()

        # Task-local policy/diagnostic state.  In particular, ``prev_action``
        # must never alias the Strike policy's 30D EMA history.
        self.prev_action = torch.zeros(
            self.num_envs, self.num_actions, device=d)
        self._nonfinite_action_state = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_dof_pos = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_dof_vel = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_root_state = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_body_state = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_contact_force = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self.last_nonfinite_observation = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self.obs_body_idx = [
            self.hbody_index[name] for name in self.obs_body_names]
        self.num_obs = 2 * self.n_nonlocked + 3 * len(self.obs_body_names)
        self.obs_buf = torch.zeros(self.num_envs, self.num_obs, device=d)
        self.reset_buf = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)

    def _create_sim(self, headless):
        sp = gymapi.SimParams()
        sp.dt = 1.0 / self.SIM_HZ
        sp.substeps = self.SUBSTEPS
        sp.up_axis = gymapi.UP_AXIS_Z
        sp.gravity = gymapi.Vec3(0, 0, -9.81)
        sp.physx.solver_type = 1
        self.solver_position_iterations = getattr(self, "PHYSX_POSITION_ITERATIONS", 4)
        self.solver_velocity_iterations = getattr(self, "PHYSX_VELOCITY_ITERATIONS", 2)
        sp.physx.num_position_iterations = self.solver_position_iterations
        sp.physx.num_velocity_iterations = self.solver_velocity_iterations
        sp.physx.contact_offset = 0.002
        sp.physx.rest_offset = 0.0
        # Net-contact tensors are consumed as an end-of-control-step state
        # (thumb support, safety and observations).  The Isaac Gym default,
        # CC_ALL_SUBSTEPS, aggregates impulses from all four substeps and can
        # report kN-scale values even when the final contact is only a few N.
        # Sampling the last substep keeps force and end-step geometry on the
        # same temporal boundary.
        sp.physx.contact_collection = (
            gymapi.ContactCollection.CC_LAST_SUBSTEP)
        # Bound overlap recovery explicitly.  Isaac's 100 m/s default makes a
        # newly formed fingertip contact unnecessarily impulsive.
        sp.physx.max_depenetration_velocity = 10.0
        self.contact_collection_contract = "last_substep"
        self.max_depenetration_velocity = 10.0
        sp.use_gpu_pipeline = True
        sp.physx.use_gpu = True
        device = torch.device(self.device)
        if device.type != "cuda":
            raise ValueError("GPU PhysX requires a CUDA device")
        compute_device_id = (
            torch.cuda.current_device()
            if device.index is None else device.index)
        self.sim = self.gym.create_sim(
            compute_device_id, compute_device_id,
            gymapi.SIM_PHYSX, sp)
        plane = gymapi.PlaneParams(); plane.normal = gymapi.Vec3(0, 0, 1)
        self.gym.add_ground(self.sim, plane)

    def _load_assets(self):
        oh = gymapi.AssetOptions(); oh.fix_base_link = True
        self.asset_human = self.gym.load_asset(self.sim, ASSETS, 'smpl_mpl_hands_body.xml', oh)
        og = gymapi.AssetOptions(); og.fix_base_link = True; og.disable_gravity = True
        self.asset_guitar = self.gym.load_asset(self.sim, ASSETS, 'guitar_asset.xml', og)
        ch = self.P['chair']['half']
        oc = gymapi.AssetOptions(); oc.fix_base_link = True
        self.asset_chair = self.gym.create_box(
            self.sim, 2 * ch[0], 2 * ch[1], 2 * ch[2], oc)

    def _compute_gains(self):
        def cap_for(n):
            if n.startswith(('LH:', 'RH:')):
                return 20.0
            if 'Neck' in n or 'Head' in n:
                return 150.0
            if 'Wrist' in n or 'Elbow_y' in n or 'Elbow_z' in n:
                return 60.0
            return 600.0
        def floor_for(n):
            return 100.0 if ('Neck' in n or 'Head' in n) else 30.0
        kp = np.array([min(max(self._gains_src.get(n, (50, 5))[0], floor_for(n)), cap_for(n))
                       for n in self.dof_names], dtype=np.float32)
        kd = np.maximum(0.25 * kp, np.array(
            [self._gains_src.get(n, (50, 5))[1] for n in self.dof_names], dtype=np.float32))
        return kp, kd.astype(np.float32)

    @staticmethod
    def _tf(pos, quat_wxyz):
        t = gymapi.Transform()
        t.p = gymapi.Vec3(*pos)
        w, x, y, z = quat_wxyz
        t.r = gymapi.Quat(x, y, z, w)
        return t

    def _create_envs(self):
        n_side = int(np.ceil(np.sqrt(self.num_envs)))
        self.envs, self.h_actors, self.g_actors = [], [], []
        rq = self.pose['root_qpos']
        ch = self.P['chair']
        for i in range(self.num_envs):
            env = self.gym.create_env(self.sim, gymapi.Vec3(-1.5, -1.5, 0),
                                      gymapi.Vec3(1.5, 1.5, 2.5), n_side)
            h = self.gym.create_actor(env, self.asset_human, self._tf(rq[:3], rq[3:]),
                                      'humanoid', i, HUMANOID_COLLISION_FILTER)
            g = self.gym.create_actor(env, self.asset_guitar,
                                      self._tf(self.P['guitar_pos_computed'],
                                               self.P['guitar_quat_wxyz_computed']),
                                      'guitar', i, GUITAR_COLLISION_FILTER)
            if i == 0:
                self.body_names = self.gym.get_actor_rigid_body_names(env, h)
                self.gbody_names = self.gym.get_actor_rigid_body_names(env, g)
            cp = gymapi.Transform(); cp.p = gymapi.Vec3(ch['center_xy'][0], ch['center_xy'][1], ch['half'][2])
            self.gym.create_actor(env, self.asset_chair, cp, 'chair', i, 0)
            if i == 0:
                self.dof_names = self.gym.get_actor_dof_names(env, h)
                self.body_names = self.gym.get_actor_rigid_body_names(env, h)
                self.gbody_names = self.gym.get_actor_rigid_body_names(env, g)
                self._init_pose_np = np.array(
                    [self.pose['joints_isaac'][n] for n in self.dof_names], dtype=np.float32)
                self._kp_np, self._kd_np = self._compute_gains()
                props = self.gym.get_actor_dof_properties(env, h)
                self._authored_dof_lower_np = props['lower'].copy()
                self._authored_dof_upper_np = props['upper'].copy()
                self.human_hard_limit_audit = {
                    "enabled": False, "profile_path": self.human_hard_limit_path,
                    "applied_joint_count": 0, "applied": []}
                if self.human_hard_limits_enabled:
                    limited_lower, limited_upper, audit = apply_joint_limit_profile(
                        self.dof_names, props['lower'], props['upper'],
                        self.human_hard_limit_path)
                    props['lower'][:] = limited_lower
                    props['upper'][:] = limited_upper
                    self.human_hard_limit_audit = audit
                for j, n in enumerate(self.dof_names):
                    if any(k in n for k in self.locked_dof_keywords):
                        # furniture lock (see LOCK_KEYWORDS note): pinch limits + drive damping +
                        # high armature. driveMode=POS/stiffness=0 gives solver-side damping only;
                        # the explicit stiffness torque is masked off for these dofs in step_physics.
                        props['lower'][j] = self._init_pose_np[j] - 1e-4
                        props['upper'][j] = self._init_pose_np[j] + 1e-4
                        props['driveMode'][j] = gymapi.DOF_MODE_POS
                        props['stiffness'][j] = 0.0
                        props['damping'][j] = float(self._kd_np[j])
                        props['armature'][j] = LOCKED_ARMATURE
                    else:
                        # HYBRID PD: damping runs INSIDE the solver (implicit -> stable);
                        # stiffness is applied explicitly each control step as torque.
                        # (pure explicit PD went bang-bang: qd ~ -90 rad/s, tau saturated)
                        props['driveMode'][j] = gymapi.DOF_MODE_POS
                        props['stiffness'][j] = 0.0
                        props['damping'][j] = float(self._kd_np[j])
                self._dof_props = props
            self.gym.set_actor_dof_properties(env, h, self._dof_props)
            for actor in (h, g):                            # per-shape 1e-4 offset: kill the 2cm phantom-contact gap
                shp = self.gym.get_actor_rigid_shape_properties(env, actor)
                for p_ in shp:
                    p_.contact_offset = SHAPE_CONTACT_OFFSET; p_.rest_offset = 0.0
                self.gym.set_actor_rigid_shape_properties(env, actor, shp)
            self._set_body_shape_filter(
                env, h, self.body_names, THUMB_PAD_BODY,
                DISABLED_COLLISION_FILTER)
            self._set_body_shape_filter(
                env, g, self.gbody_names, THUMB_SUPPORT_PROXY_BODY,
                DISABLED_COLLISION_FILTER)
            self.envs.append(env); self.h_actors.append(h); self.g_actors.append(g)
        actual = self.gym.get_actor_dof_properties(
            self.envs[0], self.h_actors[0])
        if (not np.allclose(actual['lower'], self._dof_props['lower'], atol=1e-7)
                or not np.allclose(
                    actual['upper'], self._dof_props['upper'], atol=1e-7)):
            raise RuntimeError("PhysX actor에 런타임 관절 hard limit이 반영되지 않았다")
        self.human_hard_limit_audit["physx_verified"] = True
        self._audit_collision_setup()

    def _body_shape_indices(self, env, actor, body_names, body_name):
        try:
            body_index = body_names.index(body_name)
        except ValueError as exc:
            raise RuntimeError(f"asset is missing rigid body {body_name}") from exc
        records = self.gym.get_actor_rigid_body_shape_indices(env, actor)
        record = records[body_index]
        start, count = int(record.start), int(record.count)
        if count < 1:
            raise RuntimeError(f"rigid body {body_name} has no collision shape")
        return tuple(range(start, start + count))

    def _set_body_shape_filter(
            self, env, actor, body_names, body_name, filter_value):
        shape_indices = self._body_shape_indices(
            env, actor, body_names, body_name)
        properties = self.gym.get_actor_rigid_shape_properties(env, actor)
        for shape_index in shape_indices:
            properties[shape_index].filter = int(filter_value)
        self.gym.set_actor_rigid_shape_properties(env, actor, properties)

    def enable_thumb_support_collision(self, preserve_other_filters=False):
        """Enable only the dedicated thumb-pad/neck-proxy collision pair.

        A shared Strike backend has already disabled its pluck-range helper.
        Preserve and audit those unrelated physical filters when attaching the
        Fret view instead of assuming a pristine standalone scene.
        """
        previous_human_filters = previous_guitar_filters = None
        if preserve_other_filters:
            previous_human_filters = tuple(
                int(prop.filter) for prop in
                self.gym.get_actor_rigid_shape_properties(
                    self.envs[0], self.h_actors[0]))
            previous_guitar_filters = tuple(
                int(prop.filter) for prop in
                self.gym.get_actor_rigid_shape_properties(
                    self.envs[0], self.g_actors[0]))
        for env, human, guitar in zip(
                self.envs, self.h_actors, self.g_actors):
            self._set_body_shape_filter(
                env, human, self.body_names, THUMB_PAD_BODY,
                GUITAR_COLLISION_FILTER)
            self._set_body_shape_filter(
                env, guitar, self.gbody_names, THUMB_SUPPORT_PROXY_BODY,
                HUMANOID_COLLISION_FILTER)
        self._audit_thumb_support_collision(
            previous_human_filters=previous_human_filters,
            previous_guitar_filters=previous_guitar_filters)

    def _audit_thumb_support_collision(
            self, previous_human_filters=None,
            previous_guitar_filters=None):
        env, human, guitar = (
            self.envs[0], self.h_actors[0], self.g_actors[0])
        human_props = self.gym.get_actor_rigid_shape_properties(env, human)
        guitar_props = self.gym.get_actor_rigid_shape_properties(env, guitar)
        pad_indices = set(self._body_shape_indices(
            env, human, self.body_names, THUMB_PAD_BODY))
        proxy_indices = set(self._body_shape_indices(
            env, guitar, self.gbody_names, THUMB_SUPPORT_PROXY_BODY))
        for index, prop in enumerate(human_props):
            expected = (
                GUITAR_COLLISION_FILTER if index in pad_indices
                else previous_human_filters[index]
                if previous_human_filters is not None
                else HUMANOID_COLLISION_FILTER)
            if int(prop.filter) != expected:
                raise RuntimeError(
                    f"unexpected humanoid shape filter at {index}: "
                    f"{int(prop.filter)} != {expected}")
        for index, prop in enumerate(guitar_props):
            expected = (
                HUMANOID_COLLISION_FILTER if index in proxy_indices
                else previous_guitar_filters[index]
                if previous_guitar_filters is not None
                else GUITAR_COLLISION_FILTER)
            if int(prop.filter) != expected:
                raise RuntimeError(
                    f"unexpected guitar shape filter at {index}: "
                    f"{int(prop.filter)} != {expected}")
        if GUITAR_COLLISION_FILTER & HUMANOID_COLLISION_FILTER:
            raise RuntimeError("thumb pad/proxy filters disable their contact")
        if not (GUITAR_COLLISION_FILTER & GUITAR_COLLISION_FILTER):
            raise RuntimeError("thumb pad still collides with ordinary guitar")
        if not (HUMANOID_COLLISION_FILTER & HUMANOID_COLLISION_FILTER):
            raise RuntimeError("ordinary humanoid still collides with thumb proxy")
        self.collision_audit.update({
            "thumb_support_enabled": True,
            "thumb_pad_shapes": len(pad_indices),
            "thumb_proxy_shapes": len(proxy_indices),
            "thumb_pad_filter": GUITAR_COLLISION_FILTER,
            "thumb_proxy_filter": HUMANOID_COLLISION_FILTER,
        })

    def _audit_collision_setup(self):
        """Fail at startup if an asset/filter edit silently disables guitar contact."""
        if HUMANOID_COLLISION_FILTER & GUITAR_COLLISION_FILTER:
            raise RuntimeError("humanoid and guitar collision filters overlap; contact is disabled")
        hp = self.gym.get_actor_rigid_shape_properties(self.envs[0], self.h_actors[0])
        gp = self.gym.get_actor_rigid_shape_properties(self.envs[0], self.g_actors[0])
        if not hp or not gp:
            raise RuntimeError("humanoid or guitar has no collision shapes")
        pad_indices = set(self._body_shape_indices(
            self.envs[0], self.h_actors[0], self.body_names, THUMB_PAD_BODY))
        proxy_indices = set(self._body_shape_indices(
            self.envs[0], self.g_actors[0], self.gbody_names,
            THUMB_SUPPORT_PROXY_BODY))
        for index, prop in enumerate(hp):
            expected = (DISABLED_COLLISION_FILTER if index in pad_indices
                        else HUMANOID_COLLISION_FILTER)
            if int(prop.filter) != expected:
                raise RuntimeError(
                    f"unexpected humanoid shape filter at {index}: "
                    f"{int(prop.filter)} != {expected}")
        for index, prop in enumerate(gp):
            expected = (DISABLED_COLLISION_FILTER if index in proxy_indices
                        else GUITAR_COLLISION_FILTER)
            if int(prop.filter) != expected:
                raise RuntimeError(
                    f"unexpected guitar shape filter at {index}: "
                    f"{int(prop.filter)} != {expected}")
        offsets = [float(p.contact_offset) for p in hp] + [float(p.contact_offset) for p in gp]
        if max(abs(x - SHAPE_CONTACT_OFFSET) for x in offsets) > 1e-7:
            raise RuntimeError("humanoid/guitar contact_offset audit failed")
        self.collision_audit = {
            "human_shapes": len(hp), "guitar_shapes": len(gp),
            "human_filter": HUMANOID_COLLISION_FILTER,
            "guitar_filter": GUITAR_COLLISION_FILTER,
            "thumb_support_enabled": False,
            "thumb_pad_shapes": len(pad_indices),
            "thumb_proxy_shapes": len(proxy_indices),
            "thumb_disabled_filter": DISABLED_COLLISION_FILTER,
            "contact_offset": SHAPE_CONTACT_OFFSET,
        }

    def _init_tensors(self, control_prefixes):
        d = self.device
        self.n_dof = len(self.dof_names)
        self.dof_state = gymtorch.wrap_tensor(self.gym.acquire_dof_state_tensor(self.sim))
        self.root_state = gymtorch.wrap_tensor(self.gym.acquire_actor_root_state_tensor(self.sim))
        self.body_state = gymtorch.wrap_tensor(self.gym.acquire_rigid_body_state_tensor(self.sim))
        if getattr(self, "defer_reset_state_submission", False):
            self._pending_reset_envs = torch.zeros(self.num_envs, dtype=torch.bool, device=d)
            self._reset_human_actor_indices = torch.tensor([
                self.gym.get_actor_index(env, actor, gymapi.DOMAIN_SIM)
                for env, actor in zip(self.envs, self.h_actors)], dtype=torch.int32, device=d)
            self._dof_state_refreshed = self._root_state_refreshed = False
        raw_init_pose = torch.tensor(self._init_pose_np, device=d)

        self.locked = torch.tensor([any(k in n for k in self.locked_dof_keywords) for n in self.dof_names],
                                   device=d)
        self.controlled = torch.tensor(
            [any(n.startswith(p) for p in control_prefixes) and not any(k in n for k in self.locked_dof_keywords)
             for n in self.dof_names], device=d)
        self.ctrl_idx = torch.nonzero(self.controlled).squeeze(-1)
        self.num_actions = int(self.controlled.sum())
        self._locked_flat = self.locked.repeat(self.num_envs)       # (num_envs*n_dof,) for step_physics
        self._zeros_dof = torch.zeros(self.num_envs * self.n_dof, device=d)

        self.kp = torch.tensor(self._kp_np, device=d).repeat(self.num_envs)
        self.tau_limit = torch.tensor(
            [dof_torque_limit(name) for name in self.dof_names],
            device=d).repeat(self.num_envs)
        self.applied_tau = torch.zeros(self.num_envs, self.n_dof, device=d)

        lower_1d = torch.tensor(self._dof_props['lower'].copy(), device=d)
        upper_1d = torch.tensor(self._dof_props['upper'].copy(), device=d)
        self.authored_dof_lower = torch.tensor(
            self._authored_dof_lower_np, device=d)
        self.authored_dof_upper = torch.tensor(
            self._authored_dof_upper_np, device=d)
        if not torch.isfinite(lower_1d).all() or not torch.isfinite(upper_1d).all():
            raise RuntimeError("all humanoid DOFs must have finite hard limits")
        if not torch.all(lower_1d <= upper_1d):
            raise RuntimeError("a humanoid DOF has lower limit above its upper limit")

        # The authored seated pose historically put a few hand joints just outside their XML
        # hard limits.  Starting there makes every noisy RSI reset invalid before the policy has
        # acted.  Keep the raw pose for diagnostics, but make the environment's authoritative
        # reset pose satisfy the exact simulator limits.
        self.raw_init_pose = raw_init_pose
        hard_clamped_init = torch.maximum(
            torch.minimum(raw_init_pose, upper_1d), lower_1d)
        self.init_pose_limit_adjustment = hard_clamped_init - self.raw_init_pose
        self.init_pose = hard_clamped_init.clone()
        adjusted = torch.nonzero(
            self.init_pose_limit_adjustment.abs() > 1e-6).flatten().tolist()
        self.human_hard_limit_audit["initial_pose_adjustments"] = [
            {
                "name": self.dof_names[index],
                "adjustment_deg": math.degrees(float(
                    self.init_pose_limit_adjustment[index].detach().cpu())),
            }
            for index in adjusted
        ]

        # A tanh-bounded actor cannot learn away from an initial mean exactly at
        # +/-1 because the transform is saturated there.  A small, explicit
        # Joint Soft Range inset gives boundary-authored hand joints a finite
        # policy gradient while the simulator hard limits remain authoritative.
        # Only controlled joints are adjusted; fixed posture joints are left at
        # the hard-clamped authored pose.
        span_1d = upper_1d - lower_1d
        reset_soft_lo_1d = lower_1d + self.reset_soft_limit_fraction * span_1d
        reset_soft_hi_1d = upper_1d - self.reset_soft_limit_fraction * span_1d
        controlled_init = self.init_pose[self.ctrl_idx]
        controlled_init = torch.maximum(
            torch.minimum(controlled_init, reset_soft_hi_1d[self.ctrl_idx]),
            reset_soft_lo_1d[self.ctrl_idx])
        self.init_pose[self.ctrl_idx] = controlled_init
        self.dof_lower = lower_1d.repeat(self.num_envs)
        self.dof_upper = upper_1d.repeat(self.num_envs)
        self.reset_ctrl_lo = reset_soft_lo_1d[self.ctrl_idx].repeat(
            self.num_envs, 1)
        self.reset_ctrl_hi = reset_soft_hi_1d[self.ctrl_idx].repeat(
            self.num_envs, 1)
        self.pd_target = self.init_pose.repeat(self.num_envs).clone()

        # humanoid body-state slice: actors per env = humanoid, guitar, chair (in order)
        self.n_hbody = len(self.body_names)
        bodies_per_env = self.body_state.shape[0] // self.num_envs
        self._bpe = bodies_per_env
        self.hbody_index = {n: i for i, n in enumerate(self.body_names)}
        self.gbody_index = {n: i for i, n in enumerate(self.gbody_names)}

        # ---------- RL-loop tensors ----------
        self.contact_force = gymtorch.wrap_tensor(       # (total_bodies, 3) net contact force
            self.gym.acquire_net_contact_force_tensor(self.sim))
        self.nonlocked_idx = torch.nonzero(~self.locked).squeeze(-1)
        self.n_nonlocked = int((~self.locked).sum())
        # action -> PD-target map, precomputed per controlled dof: tgt = mid + scale*a*half, clamped
        lo = self.dof_lower.view(self.num_envs, self.n_dof)[:, self.ctrl_idx].clone()
        hi = self.dof_upper.view(self.num_envs, self.n_dof)[:, self.ctrl_idx].clone()
        self.ctrl_lo, self.ctrl_hi = lo, hi
        self.ctrl_mid = 0.5 * (lo + hi); self.ctrl_half = 0.5 * (hi - lo)
        assert torch.isfinite(self.ctrl_mid).all() and torch.isfinite(self.ctrl_half).all(), \
            "a controlled dof has non-finite limits (unbounded joint) -> NaN targets; check control_dofs"
        assert (self.ctrl_half > 0.0).all(), \
            "a controlled dof has a zero/reversed range; inverse action mapping is undefined"
        self.prev_action = torch.zeros(self.num_envs, self.num_actions, device=d)
        self._nonfinite_action_state = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_dof_pos = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_dof_vel = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_root_state = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_body_state = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self._nonfinite_contact_force = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        self.last_nonfinite_observation = torch.zeros(
            self.num_envs, dtype=torch.bool, device=d)
        # guitar-relative obs bodies (humanoid) + obs sizing (tasks append goal obs on top)
        self.obs_body_idx = [self.hbody_index[n] for n in self.obs_body_names]
        self.num_obs = 2 * self.n_nonlocked + 3 * len(self.obs_body_names)
        self.obs_buf = torch.zeros(self.num_envs, self.num_obs, device=d)
        # episode bookkeeping
        self.progress_buf = torch.zeros(self.num_envs, dtype=torch.long, device=d)
        self.reset_buf = torch.zeros(self.num_envs, dtype=torch.bool, device=d)
        # root snapshot (roots are welded in G0; this is the reset target once the guitar frees in G1)
        self._refresh_root_state()
        self.root_init = self.root_state.clone()

    # ---------- RL loop ----------
    def reset(self):
        """reset all envs to the seated init pose; returns the initial observation. Runs one held
        physics step so the rigid-body (guitar-relative) obs channels reflect the init pose — a bare
        set_dof_state does NOT recompute link world transforms until a simulate()."""
        self.reset_idx(torch.arange(self.num_envs, device=self.device))
        self.step_physics()
        self.refresh()
        return self.compute_observations()

    def reset_idx(self, env_ids):
        """RSI reset of the given envs -> seated init pose (+ optional exploration noise on the
        controlled dofs). Fixed-scene roots return to ``root_init``; that same snapshot is the
        reset hook for a future free guitar in G1/G2. Locked furniture is re-injected every step
        anyway."""
        env_ids = torch.as_tensor(
            env_ids, dtype=torch.long, device=self.device).reshape(-1)
        if env_ids.numel() == 0:
            return
        self._refresh_dof_state()
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        q_reset = self.init_pose[None].expand(env_ids.numel(), -1).clone()
        ds[env_ids, :, 1] = 0.0
        if self.reset_noise > 0 and self.num_actions > 0:            # RSI exploration noise
            noise = (torch.rand(env_ids.numel(), self.num_actions, generator=self.rng,
                                device=self.device) - 0.5) * (2 * self.reset_noise)
            q_reset[:, self.ctrl_idx] += noise

        # Both the authored pose and its RSI perturbation are subject to hard limits.  Clamping
        # after adding noise is important for joints whose seated value is exactly on a limit.
        lo = self.dof_lower.view(self.num_envs, self.n_dof)[env_ids]
        hi = self.dof_upper.view(self.num_envs, self.n_dof)[env_ids]
        q_reset = torch.maximum(torch.minimum(q_reset, hi), lo)
        reset_ctrl = q_reset[:, self.ctrl_idx]
        reset_ctrl = torch.maximum(
            torch.minimum(reset_ctrl, self.reset_ctrl_hi[env_ids]),
            self.reset_ctrl_lo[env_ids])
        q_reset[:, self.ctrl_idx] = reset_ctrl
        ds[env_ids, :, 0] = q_reset
        if not getattr(self, "defer_reset_state_submission", False):
            self.gym.set_dof_state_tensor(self.sim, gymtorch.unwrap_tensor(self.dof_state))

        # Restore the complete fixed-scene root snapshot as well.  This is normally a no-op in
        # G0, but it lets a non-finite root state recover instead of immediately poisoning the
        # freshly reset episode.  ``root_init`` is already the documented G1/G2 reset hook.
        self._refresh_root_state()
        roots = self.root_state.view(self.num_envs, -1, 13)
        roots_init = self.root_init.view(self.num_envs, -1, 13)
        roots[env_ids] = roots_init[env_ids]
        if getattr(self, "defer_reset_state_submission", False):
            self._pending_reset_envs[env_ids] = True
        else:
            self.gym.set_actor_root_state_tensor(
                self.sim, gymtorch.unwrap_tensor(self.root_state))
        self.pd_target.view(self.num_envs, self.n_dof)[env_ids] = q_reset

        # EMA is part of the actuator state.  Zero means the midpoint of every joint, not the
        # reset pose.  Initialising it with the exact inverse target prevents the first hold/init
        # action from producing a large artificial shoulder/finger target jump.
        reset_ctrl_q = q_reset[:, self.ctrl_idx]
        self.prev_action[env_ids] = self.actions_for_pd_targets(reset_ctrl_q, env_ids)
        self.applied_tau[env_ids] = 0.0
        self.progress_buf[env_ids] = 0
        self.reset_buf[env_ids] = False

        for name in ("_nonfinite_action_state", "_nonfinite_dof_pos",
                     "_nonfinite_dof_vel", "_nonfinite_root_state",
                     "_nonfinite_body_state", "_nonfinite_contact_force",
                     "last_nonfinite_observation"):
            getattr(self, name)[env_ids] = False

    def _refresh_dof_state(self):
        if not getattr(self, "defer_reset_state_submission", False):
            self.gym.refresh_dof_state_tensor(self.sim)
        elif not self._dof_state_refreshed:
            self.gym.refresh_dof_state_tensor(self.sim)
            self._dof_state_refreshed = True

    def _refresh_root_state(self):
        if not getattr(self, "defer_reset_state_submission", False):
            self.gym.refresh_actor_root_state_tensor(self.sim)
        elif not self._root_state_refreshed:
            self.gym.refresh_actor_root_state_tensor(self.sim)
            self._root_state_refreshed = True

    def _submit_pending_reset_state(self):
        """Submit final reset buffers once, immediately before simulate.

        Higher-level reset methods can finish joint/reference/noise edits first.
        Keep index tensors alive through simulate and touch only selected actors.
        """
        if not getattr(self, "defer_reset_state_submission", False):
            return
        ids = self._pending_reset_envs.nonzero(as_tuple=False).flatten()
        if not ids.numel():
            return
        self._submitted_dof_actor_indices = self._reset_human_actor_indices[ids].contiguous()
        actors = torch.arange(self.root_state.shape[0], device=self.device, dtype=torch.int32)
        self._submitted_root_actor_indices = actors.view(self.num_envs, -1)[ids].reshape(-1).contiguous()
        self.gym.set_dof_state_tensor_indexed(
            self.sim, gymtorch.unwrap_tensor(self.dof_state),
            gymtorch.unwrap_tensor(self._submitted_dof_actor_indices),
            self._submitted_dof_actor_indices.numel())
        self.gym.set_actor_root_state_tensor_indexed(
            self.sim, gymtorch.unwrap_tensor(self.root_state),
            gymtorch.unwrap_tensor(self._submitted_root_actor_indices),
            self._submitted_root_actor_indices.numel())
        self._pending_reset_envs.zero_()

    def actions_for_pd_targets(self, controlled_targets, env_ids=None):
        """Invert the controlled action-to-PD-target mapping.

        ``controlled_targets`` contains one target per controlled DOF and is clamped to the hard
        range before inversion.  The returned action is always in ``[-1, 1]`` and accounts for
        ``action_scale``.  This helper defines the reset/hold contract and is also suitable for
        diagnostic policies that want to hold an explicit joint pose.
        """
        if env_ids is None:
            mid, half = self.ctrl_mid, self.ctrl_half
        else:
            env_ids = torch.as_tensor(
                env_ids, dtype=torch.long, device=self.device).reshape(-1)
            mid, half = self.ctrl_mid[env_ids], self.ctrl_half[env_ids]
        if controlled_targets.shape != mid.shape:
            raise ValueError(
                f"controlled_targets must have shape {tuple(mid.shape)}, "
                f"got {tuple(controlled_targets.shape)}")
        if not torch.isfinite(controlled_targets).all():
            raise ValueError("controlled_targets must be finite")
        targets = torch.maximum(
            torch.minimum(controlled_targets, mid + half), mid - half)
        return ((targets - mid) / (self.action_scale * half)).clamp(-1.0, 1.0)

    @staticmethod
    def rows_with_nonfinite(value):
        """Return a per-leading-row mask for tensors containing NaN or Inf."""
        if value.ndim == 0:
            return ~torch.isfinite(value).reshape(1)
        if value.ndim == 1:
            return ~torch.isfinite(value)
        return ~torch.isfinite(value).reshape(value.shape[0], -1).all(dim=1)

    @staticmethod
    def sanitize_finite(value, fill=0.0):
        """Replace every NaN/Inf without changing finite values.

        Tasks can use this on rewards or appended observations before handing a transition to
        PPO.  It deliberately returns a new tensor so diagnostics may still inspect the original.
        """
        replacement = torch.as_tensor(fill, dtype=value.dtype, device=value.device)
        return torch.where(torch.isfinite(value), value, replacement)

    def _clear_step_nonfinite_flags(self):
        for name in ("_nonfinite_action_state", "_nonfinite_dof_pos",
                     "_nonfinite_dof_vel", "_nonfinite_root_state",
                     "_nonfinite_body_state", "_nonfinite_contact_force"):
            getattr(self, name).zero_()

    def _capture_and_sanitize_dof_state(self):
        """Latch invalid simulator DOFs, then keep downstream reward/PD math finite."""
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        bad_q = ~torch.isfinite(ds[:, :, 0])
        bad_qd = ~torch.isfinite(ds[:, :, 1])
        self._nonfinite_dof_pos |= bad_q.any(dim=1)
        self._nonfinite_dof_vel |= bad_qd.any(dim=1)
        ds[:, :, 0] = torch.where(bad_q, self.init_pose[None], ds[:, :, 0])
        ds[:, :, 1] = torch.where(bad_qd, torch.zeros_like(ds[:, :, 1]), ds[:, :, 1])

    def apply_actions(self, actions):
        """actions (num_envs, num_actions) in [-1,1] -> EMA-smoothed, scaled PD targets on the
        controlled dofs. Shared by every task so fret/strike policies compose with identical
        action semantics. tgt = mid + action_scale*ema(a)*half_range, clamped to the dof limits."""
        if actions.shape != self.prev_action.shape:
            raise ValueError(
                f"actions must have shape {tuple(self.prev_action.shape)}, "
                f"got {tuple(actions.shape)}")
        self._clear_step_nonfinite_flags()
        invalid_input = ~torch.isfinite(actions)
        invalid_prev = ~torch.isfinite(self.prev_action)
        invalid_target = ~torch.isfinite(
            self.pd_target.view(self.num_envs, self.n_dof))
        invalid_tau = ~torch.isfinite(self.applied_tau)
        self._nonfinite_action_state.copy_(
            invalid_input.any(dim=1) | invalid_prev.any(dim=1)
            | invalid_target.any(dim=1) | invalid_tau.any(dim=1))

        pd = self.pd_target.view(self.num_envs, self.n_dof)
        pd.copy_(torch.where(
            torch.isfinite(pd), pd,
            self.init_pose[None].expand_as(pd)))
        self.applied_tau.copy_(torch.where(
            torch.isfinite(self.applied_tau), self.applied_tau,
            torch.zeros_like(self.applied_tau)))

        # A non-finite actor output must terminate the transition, but must never reach PhysX.
        # Holding the previous finite command is the least disruptive one-step fallback.
        safe_prev = torch.where(
            torch.isfinite(self.prev_action), self.prev_action,
            torch.zeros_like(self.prev_action))
        safe_actions = torch.where(torch.isfinite(actions), actions, safe_prev).clamp(-1, 1)
        a = self.action_alpha * safe_prev + (1 - self.action_alpha) * safe_actions
        self.prev_action.copy_(a)
        tgt = (self.ctrl_mid + self.action_scale * a * self.ctrl_half).clamp(self.ctrl_lo, self.ctrl_hi)
        self.pd_target.view(self.num_envs, self.n_dof)[:, self.ctrl_idx] = tgt

    def step(self, actions):
        """one control step: apply actions -> simulate -> refresh -> advance time -> terminate,
        then auto-reset done envs FOR THE NEXT STEP. Returns (obs, done). obs is computed from the
        fresh post-simulate state (so the guitar-relative body channels are valid, incl. the
        terminal obs of done envs); reset_idx is applied AFTER, taking effect next step — this is
        the IsaacGymEnvs order and avoids reading stale (pre-simulate) body transforms right after
        set_dof_state. Reward + goal advancement are the task's job."""
        self.apply_actions(actions)
        self.step_physics()
        self.refresh()
        self.progress_buf += 1
        self.reset_buf = self.check_termination()
        done = self.reset_buf.clone()
        obs = self.compute_observations()              # fresh; terminal obs for done envs
        env_ids = torch.nonzero(self.reset_buf).squeeze(-1)
        if len(env_ids) > 0:
            self.reset_idx(env_ids)                    # sets state for next step (no stale obs read)
        return obs, done

    def termination_reasons(self):
        """Return named, full-batch base termination masks.

        A task can distinguish an ordinary time-limit truncation from simulator/control failure
        without duplicating base internals.  Latched masks retain invalid values that were made
        finite before reward/observation computation, while the direct checks also support unit
        tests and callers that invoke this method without :meth:`refresh`.
        """
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        q, qd = ds[:, :, 0], ds[:, :, 1]
        nonfinite_dof_pos = self._nonfinite_dof_pos | self.rows_with_nonfinite(q)
        nonfinite_dof_vel = self._nonfinite_dof_vel | self.rows_with_nonfinite(qd)

        roots = self.root_state.view(self.num_envs, -1, 13)
        bodies = self.body_state.view(self.num_envs, self._bpe, 13)
        contacts = self.contact_force.view(self.num_envs, self._bpe, 3)
        nonfinite_root_state = (
            self._nonfinite_root_state | self.rows_with_nonfinite(roots))
        nonfinite_body_state = (
            self._nonfinite_body_state | self.rows_with_nonfinite(bodies))
        nonfinite_contact_force = (
            self._nonfinite_contact_force | self.rows_with_nonfinite(contacts))
        nonfinite_action_state = (
            self._nonfinite_action_state
            | self.rows_with_nonfinite(self.prev_action)
            | self.rows_with_nonfinite(
                self.pd_target.view(self.num_envs, self.n_dof))
            | self.rows_with_nonfinite(self.applied_tau))
        nonfinite_observation = self.last_nonfinite_observation.clone()

        timeout = self.progress_buf >= self.max_episode_length
        # Keep non-finite velocity separate from a finite but physically unstable speed.
        velocity_blowup = (torch.isfinite(qd) & (qd.abs() > 50.0)).any(dim=1)
        base_termination = (timeout | nonfinite_dof_pos | nonfinite_dof_vel
                            | nonfinite_root_state | nonfinite_body_state
                            | nonfinite_contact_force | nonfinite_action_state
                            | nonfinite_observation | velocity_blowup)
        return {
            "timeout": timeout,
            "nonfinite_dof_pos": nonfinite_dof_pos,
            "nonfinite_dof_vel": nonfinite_dof_vel,
            "nonfinite_root_state": nonfinite_root_state,
            "nonfinite_body_state": nonfinite_body_state,
            "nonfinite_contact_force": nonfinite_contact_force,
            "nonfinite_action_state": nonfinite_action_state,
            "nonfinite_observation": nonfinite_observation,
            "velocity_blowup": velocity_blowup,
            "base_termination": base_termination,
        }

    def check_termination(self):
        """Backward-compatible aggregate base termination mask."""
        return self.termination_reasons()["base_termination"]

    def step_physics(self):
        """one sim step: custom PD torques on all non-locked dofs, simulate, then re-freeze the
        locked furniture. Stability of the locked lower body = three layers:
          (1) pinch limits (lower==upper) — hard position constraint, cannot drift far;
          (2) high armature (LOCKED_ARMATURE) — sluggish dofs, kills the ~30Hz sub-step tremor;
          (3) per-step re-inject to the init pose (DIGIT recipe) — removes the slow (~0.7deg/50s)
              settle of the *soft* limit under sustained gravity. Measured: 0.72deg -> ~0deg drift.
        """
        self._refresh_dof_state()
        self._capture_and_sanitize_dof_state()
        q = self.dof_state[:, 0]
        tau = self.kp * (self.pd_target - q)          # damping is implicit (drive damping)
        tau = torch.where(self._locked_flat, torch.zeros_like(tau), tau)
        tau = torch.maximum(torch.minimum(tau, self.tau_limit), -self.tau_limit)
        self.applied_tau.copy_(tau.view(self.num_envs, self.n_dof))
        self.gym.set_dof_actuation_force_tensor(self.sim, gymtorch.unwrap_tensor(tau.contiguous()))
        self._submit_pending_reset_state()
        self.gym.simulate(self.sim)
        self.gym.fetch_results(self.sim, True)
        if getattr(self, "defer_reset_state_submission", False):
            self._dof_state_refreshed = self._root_state_refreshed = False
        if not getattr(self, "reinject_locked_dof_state", True):
            return
        # (3) freeze locked furniture: overwrite its dof state back to the init pose every step
        self._refresh_dof_state()
        self._capture_and_sanitize_dof_state()
        self.dof_state[:, 0] = torch.where(self._locked_flat, self.pd_target, self.dof_state[:, 0])
        self.dof_state[:, 1] = torch.where(self._locked_flat, self._zeros_dof, self.dof_state[:, 1])
        self.gym.set_dof_state_tensor(self.sim, gymtorch.unwrap_tensor(self.dof_state))

    # ---------- observation helpers ----------
    def refresh(self):
        self._refresh_dof_state()
        self._refresh_root_state()
        self.gym.refresh_rigid_body_state_tensor(self.sim)
        self.gym.refresh_net_contact_force_tensor(self.sim)   # so contact_force is live for tasks
        self._capture_and_sanitize_dof_state()

        roots = self.root_state.view(self.num_envs, -1, 13)
        bodies = self.body_state.view(self.num_envs, self._bpe, 13)
        contacts = self.contact_force.view(self.num_envs, self._bpe, 3)
        bad_roots = ~torch.isfinite(roots)
        bad_bodies = ~torch.isfinite(bodies)
        bad_contacts = ~torch.isfinite(contacts)
        self._nonfinite_root_state |= bad_roots.reshape(self.num_envs, -1).any(dim=1)
        self._nonfinite_body_state |= bad_bodies.reshape(self.num_envs, -1).any(dim=1)
        self._nonfinite_contact_force |= bad_contacts.reshape(
            self.num_envs, -1).any(dim=1)

        # Reward and observation code runs before an async reset.  Preserve the failure masks,
        # but keep those calculations finite so a single broken environment cannot contaminate
        # vectorised reward statistics or PPO normalisation.
        roots[:] = torch.where(bad_roots, torch.zeros_like(roots), roots)
        bodies[:] = torch.where(bad_bodies, torch.zeros_like(bodies), bodies)
        contacts[:] = torch.where(bad_contacts, torch.zeros_like(contacts), contacts)

    def hbody_pos(self, name):
        """world positions (num_envs, 3) of a humanoid body."""
        bs = self.body_state.view(self.num_envs, self._bpe, 13)
        return bs[:, self.hbody_index[name], 0:3]

    def hbody_state(self, name):
        """World pose and twist of one humanoid rigid body, shape ``[N,13]``."""
        bs = self.body_state.view(self.num_envs, self._bpe, 13)
        return bs[:, self.hbody_index[name]]

    def hbody_contact_force(self, name):
        """World net contact force on one humanoid rigid body, per environment."""
        force = self.contact_force.view(self.num_envs, self._bpe, 3)
        return force[:, self.hbody_index[name]]

    def gbody_pos(self, name):
        bs = self.body_state.view(self.num_envs, self._bpe, 13)
        return bs[:, self.n_hbody + self.gbody_index[name], 0:3]

    def guitar_frame(self):
        """guitar root pose (pos, quat xyzw) per env — the observation frame.
        G0: constant; G1/G2: live. All task observations must be expressed here."""
        rs = self.root_state.view(self.num_envs, -1, 13)
        return rs[:, 1, 0:3], rs[:, 1, 3:7]

    def guitar_root_state(self):
        """Guitar world pose and twist, shape ``[N,13]``."""
        rs = self.root_state.view(self.num_envs, -1, 13)
        return rs[:, 1]

    def to_guitar_frame(self, world_pos):
        """world_pos (num_envs, K, 3) -> the guitar's LOCAL frame (the invariant obs frame).
        G0: the guitar is static, so this is just world-minus-a-constant; the IDENTICAL code path
        carries into G1/G2 where the guitar moves, making the weld->free transition invisible to
        the policy (the old pipeline's 0.90->0.18 collapse was exactly this obs-frame break). Uses
        the correct inverse rotation — NOT guitar/env.py's L879/L884 quaternion-conjugation bug,
        which is harmless only because that guitar is world-fixed; ours moves."""
        gp, gq = self.guitar_frame()                          # (num_envs,3), (num_envs,4 xyzw)
        K = world_pos.shape[1]
        rel = (world_pos - gp.unsqueeze(1)).reshape(-1, 3)
        q = gq.unsqueeze(1).expand(-1, K, -1).reshape(-1, 4)
        return quat_rotate_inverse(q, rel).reshape(self.num_envs, K, 3)

    def body_pose_twist_in_guitar_frame(self, name):
        """Return a humanoid body's guitar-relative pose/twist.

        Linear velocity is the derivative in the translating and rotating
        guitar frame, not merely the body's world velocity rotated into G.
        Rotation uses the first two body axes (continuous 6D representation).
        """
        body = self.hbody_state(name)
        guitar = self.guitar_root_state()
        guitar_pos, guitar_quat = guitar[:, 0:3], guitar[:, 3:7]
        offset_world = body[:, 0:3] - guitar_pos
        position_g = quat_rotate_inverse(guitar_quat, offset_world)

        local_axes = torch.tensor(
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            dtype=body.dtype, device=body.device)
        axes = local_axes[None].expand(self.num_envs, -1, -1)
        body_quat = body[:, 3:7]
        body_quat_expanded = body_quat[:, None].expand(-1, 2, -1).reshape(-1, 4)
        world_axes = quat_rotate(
            body_quat_expanded, axes.reshape(-1, 3)).reshape(
                self.num_envs, 2, 3)
        guitar_quat_expanded = guitar_quat[:, None].expand(
            -1, 2, -1).reshape(-1, 4)
        rotation6d_g = quat_rotate_inverse(
            guitar_quat_expanded, world_axes.reshape(-1, 3)).reshape(
                self.num_envs, 6)

        guitar_linear = guitar[:, 7:10]
        guitar_angular = guitar[:, 10:13]
        body_linear = body[:, 7:10]
        body_angular = body[:, 10:13]
        moving_origin_velocity = (
            guitar_linear
            + torch.cross(guitar_angular, offset_world, dim=-1))
        linear_velocity_g = quat_rotate_inverse(
            guitar_quat, body_linear - moving_origin_velocity)
        angular_velocity_g = quat_rotate_inverse(
            guitar_quat, body_angular - guitar_angular)
        return {
            "position_g": position_g,
            "rotation6d_g": rotation6d_g,
            "linear_velocity_g": linear_velocity_g,
            "angular_velocity_g": angular_velocity_g,
        }

    def compute_observations(self):
        """Base proprioceptive + guitar-relative observation (num_obs = 2*n_nonlocked + 3*K).
        Tasks OVERRIDE this: call super().compute_observations() and torch.cat their goal obs.
          - proprioception: non-locked dof positions + velocities (the locked furniture is excluded)
          - egocentric geometry: obs_body_names world positions expressed in the guitar frame"""
        ds = self.dof_state.view(self.num_envs, self.n_dof, 2)
        dof_pos = ds[:, self.nonlocked_idx, 0]
        dof_vel = ds[:, self.nonlocked_idx, 1]
        bs = self.body_state.view(self.num_envs, self._bpe, 13)
        rel = self.to_guitar_frame(bs[:, self.obs_body_idx, 0:3])
        obs = torch.cat([dof_pos, dof_vel, rel.reshape(self.num_envs, -1)], dim=1)
        self.last_nonfinite_observation.copy_(self.rows_with_nonfinite(obs))
        obs = self.sanitize_finite(obs)
        # Task subclasses append goal channels and therefore own a wider obs_buf. Keep the
        # base prefix writable without forcing every task to duplicate this implementation.
        self.obs_buf[:, :obs.shape[1]] = obs
        return obs
