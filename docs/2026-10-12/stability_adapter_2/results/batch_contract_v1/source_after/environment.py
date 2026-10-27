"""Single CPU PhysX scene: fixed human root, free guitar, 66 main joint targets.

This diagnostic backend has no policy, WAIT gate, dynamic strap or renderer.
"""
import json
from pathlib import Path

import isaacgym  # noqa: F401 - must precede imports that might load torch
from isaacgym import gymapi
import numpy as np

from .control import control_indices, compose_targets
from .strap import point_kinematics, cable_forces
from .trial_settings import validate_settings, initial_targets

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(__file__).with_name("config.json")


def transform(position, wxyz):
    result = gymapi.Transform()
    result.p = gymapi.Vec3(*position)
    w, x, y, z = wxyz
    result.r = gymapi.Quat(x, y, z, w)
    return result


def vector(value):
    return np.array([value[axis] for axis in ("x", "y", "z")], dtype=np.float64)


def quaternion(value):
    return np.array([value[axis] for axis in ("x", "y", "z", "w")], dtype=np.float64)


class InitialEnvironment:
    def __init__(self, initial_settings=None):
        self.initial_settings = validate_settings({} if initial_settings is None else initial_settings)
        self.config = json.loads(CONFIG_PATH.read_text())
        self.pose = json.loads((ROOT / self.config["pose_source"]).read_text())
        self.gym = gymapi.acquire_gym()
        params = gymapi.SimParams()
        params.dt = 1 / self.config["physics_hz"]
        params.substeps = 1
        params.up_axis = gymapi.UP_AXIS_Z
        params.gravity = gymapi.Vec3(0, 0, -9.81)
        params.use_gpu_pipeline = False
        params.physx.use_gpu = False
        params.physx.solver_type = 1
        params.physx.num_position_iterations = 4
        params.physx.num_velocity_iterations = 2
        params.physx.contact_collection = gymapi.ContactCollection.CC_LAST_SUBSTEP
        params.physx.contact_offset = .002
        params.physx.rest_offset = 0
        params.physx.max_depenetration_velocity = 10
        self.sim = self.gym.create_sim(0, -1, gymapi.SIM_PHYSX, params)
        if self.sim is None:
            raise RuntimeError("CPU PhysX creation failed")
        try:
            self._create_scene()
            if not self.gym.prepare_sim(self.sim):
                raise RuntimeError("prepare_sim failed")
            # Native preparation can advance the free actor. Reset exactly once
            # to the creation pose before defining t=0; never submit body state in step().
            if not self.gym.set_actor_rigid_body_states(
                    self.env, self.guitar, self.initial_guitar_bodies, gymapi.STATE_ALL):
                raise RuntimeError("initial guitar state submission failed")
            states = np.zeros(len(self.names), dtype=gymapi.DofState.dtype)
            states["pos"] = self.initial_q
            if not self.gym.set_actor_dof_states(self.env, self.human, states, gymapi.STATE_ALL):
                raise RuntimeError("initial DOF state submission failed")
            self.target = self.initial_q.copy()
            self.goal_position = np.array(self.pose["params"]["guitar_pos_computed"])
            w, x, y, z = self.pose["params"]["guitar_quat_wxyz_computed"]
            self.goal_quaternion = np.array([x, y, z, w])
            self.goal_quaternion /= np.linalg.norm(self.goal_quaternion)
            self._submit_targets()
            self.steps = 0
            # CPU native set_actor_dof_states refreshes link transforms before simulate.
            # Verify that property in the initialization audit; GPU tensors have a different contract.
            points, _ = self.route()
            self.initial_route_length = float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())
            requested_length = self.initial_settings['strap_rest_length_m']
            self.rest_length = self.initial_route_length if requested_length is None else requested_length
            self.tension = 0.0
        except Exception:
            self.close()
            raise

    def _create_scene(self):
        ground = gymapi.PlaneParams()
        ground.normal = gymapi.Vec3(0, 0, 1)
        self.gym.add_ground(self.sim, ground)
        human_options = gymapi.AssetOptions()
        human_options.fix_base_link = True
        guitar_options = gymapi.AssetOptions()
        guitar_options.fix_base_link = False
        guitar_options.disable_gravity = False
        guitar_options.override_com = True
        guitar_options.override_inertia = True
        def load(path, options):
            path = ROOT / path
            asset = self.gym.load_asset(self.sim, str(path.parent), path.name, options)
            if asset is None:
                raise RuntimeError("asset load failed: " + str(path))
            return asset
        human_asset = load(self.config["humanoid_asset"], human_options)
        guitar_asset = load(self.config["guitar_asset"], guitar_options)
        self.human_root_fixed = human_options.fix_base_link
        self.guitar_root_fixed = guitar_options.fix_base_link
        self.guitar_gravity_disabled = guitar_options.disable_gravity
        self.env = self.gym.create_env(self.sim, gymapi.Vec3(-1.5, -1.5, 0),
                                       gymapi.Vec3(1.5, 1.5, 2.5), 1)
        rq = self.pose["root_qpos"]
        self.human = self.gym.create_actor(self.env, human_asset, transform(rq[:3], rq[3:]), "human", 0, 1)
        p = self.pose["params"]
        self.guitar = self.gym.create_actor(self.env, guitar_asset,
            transform(p["guitar_pos_computed"], p["guitar_quat_wxyz_computed"]), "guitar", 0, 2)
        self.initial_guitar_bodies = self.bodies(self.guitar)
        self.initial_guitar_bodies["vel"]["linear"].fill(0)
        self.initial_guitar_bodies["vel"]["angular"].fill(0)
        chair = p["chair"]
        chair_options = gymapi.AssetOptions()
        chair_options.fix_base_link = True
        chair_asset = self.gym.create_box(self.sim, *(2*np.array(chair["half"])), chair_options)
        self.gym.create_actor(self.env, chair_asset,
            transform([*chair["center_xy"], chair["half"][2]], [1, 0, 0, 0]), "chair", 0, 0)
        self.names = list(self.gym.get_actor_dof_names(self.env, self.human))
        self.main_indices, self.torso_indices = control_indices(self.names)
        props = self.gym.get_actor_dof_properties(self.env, self.human)
        self.lower, self.upper = props["lower"].copy(), props["upper"].copy()
        raw_q = np.array([self.pose["joints_isaac"][n] for n in self.names], dtype=np.float32)
        self.initial_q = np.clip(raw_q, self.lower, self.upper)
        self.initial_adjustment = self.initial_q - raw_q
        self.initial_q = initial_targets(self.initial_q, self.names, self.main_indices,
            self.lower, self.upper, self.initial_settings)
        gains = json.loads((ROOT / self.config["gain_source"]).read_text())
        kp, kd, effort = [], [], []
        for name in self.names:
            finger = name.startswith(("LH:", "RH:"))
            cap = (20 if finger else 150 if "Neck" in name or "Head" in name else
                   60 if "Wrist" in name or "Elbow_y" in name or "Elbow_z" in name else 600)
            floor = 100 if "Neck" in name or "Head" in name else 30
            gain = min(max(gains.get(name, [50, 5])[0], floor), cap)
            kp.append(gain)
            kd.append(max(.25*gain, gains.get(name, [50, 5])[1]))
            effort.append(4 if name.startswith("LH:thumb") else 20 if finger else
                60 if "Wrist" in name else 100 if "Elbow" in name else
                150 if "Shoulder" in name or "Thorax" in name else 300)
        self.kp, self.kd, self.effort = (np.array(values, np.float32) for values in (kp, kd, effort))
        props["driveMode"][:] = gymapi.DOF_MODE_POS
        # Native apply_actor_dof_efforts is ignored in POS mode. Use solver PD
        # with shared gain/cap values for this CPU diagnostic backend.
        props["stiffness"][:] = kp
        props["damping"][:] = kd
        props["effort"][:] = effort
        self.gym.set_actor_dof_properties(self.env, self.human, props)
        self.collision_filters = {}
        for actor, disabled in [(self.human, {"LH:thumb_pad"}),
                                (self.guitar, {"G:thumb_support_proxy", "G:pluck_range"})]:
            names = self.gym.get_actor_rigid_body_names(self.env, actor)
            ranges = self.gym.get_actor_rigid_body_shape_indices(self.env, actor)
            shapes = self.gym.get_actor_rigid_shape_properties(self.env, actor)
            for name in disabled:
                record = ranges[names.index(name)]
                for i in range(record.start, record.start+record.count):
                    shapes[i].filter = 3
            for shape in shapes:
                shape.contact_offset, shape.rest_offset = .0001, 0
            self.gym.set_actor_rigid_shape_properties(self.env, actor, shapes)
            actual = self.gym.get_actor_rigid_shape_properties(self.env, actor)
            for name in disabled:
                record = ranges[names.index(name)]
                self.collision_filters[name] = [actual[i].filter for i in range(record.start, record.start+record.count)]
        self.human_bodies = list(self.gym.get_actor_rigid_body_names(self.env, self.human))
        self.guitar_bodies = list(self.gym.get_actor_rigid_body_names(self.env, self.guitar))
        self.guide_indices = [self.human_bodies.index(name) for name, _ in self.config["strap"]["guides"]]
        guitar_handle = self.gym.get_actor_rigid_body_handle(self.env, self.guitar, 0)
        self.route_handles = [guitar_handle] + [self.gym.get_actor_rigid_body_handle(self.env, self.human, i)
            for i in self.guide_indices] + [guitar_handle]
        body_props = self.gym.get_actor_rigid_body_properties(self.env, self.guitar)
        human_props = self.gym.get_actor_rigid_body_properties(self.env, self.human)
        com = lambda prop: np.array([prop.com.x, prop.com.y, prop.com.z])
        self.route_com = [com(body_props[0])] + [com(human_props[i]) for i in self.guide_indices] + [com(body_props[0])]
        self.guitar_mass = sum(prop.mass for prop in body_props)
        if any(prop.mass <= 0 or min(prop.inertia.x.x, prop.inertia.y.y, prop.inertia.z.z) <= 0 for prop in body_props):
            raise RuntimeError("nonpositive free guitar mass/inertia; no automatic repair")

    def bodies(self, actor):
        return self.gym.get_actor_rigid_body_states(self.env, actor, gymapi.STATE_ALL).copy()

    def route(self):
        human, guitar = self.bodies(self.human), self.bodies(self.guitar)[0]
        strap = self.config["strap"]
        states = [guitar] + [human[i] for i in self.guide_indices] + [guitar]
        local_points = [strap["buttons_G_m"][0]] + [v for _, v in strap["guides"]] + [strap["buttons_G_m"][1]]
        points, velocities = [], []
        for state, local, com in zip(states, local_points, self.route_com):
            point, velocity = point_kinematics(vector(state["pose"]["p"]), quaternion(state["pose"]["r"]),
                vector(state["vel"]["linear"]), vector(state["vel"]["angular"]), np.array(local), com)
            points.append(point)
            velocities.append(velocity)
        return np.array(points), np.array(velocities)

    def _submit_targets(self):
        if not self.gym.set_actor_dof_position_targets(self.env, self.human, self.target):
            raise RuntimeError("joint target submission failed")

    def set_main_offsets(self, offsets):
        """Diagnostic target offsets from initial q; does not write joint/root state.

        Feedback rate limits and playing-target checks belong to the next control stage.
        """
        self.target = compose_targets(self.initial_q, self.main_indices, offsets, self.lower, self.upper)
        self._submit_targets()

    def step(self):
        for _ in range(self.config["physics_hz"] // self.config["control_hz"]):
            points, velocities = self.route()
            strap = self.config["strap"]
            forces, self.tension, _, _ = cable_forces(points, velocities, self.rest_length,
                strap["stiffness_n_per_m"], strap["damping_n_s_per_m"], strap["max_tension_n"])
            if not np.isfinite(forces).all():
                raise FloatingPointError("nonfinite strap force")
            for handle, point, force in zip(self.route_handles, points, forces):
                self.gym.apply_body_force_at_pos(self.env, handle, gymapi.Vec3(*force), gymapi.Vec3(*point), gymapi.ENV_SPACE)
            self.gym.simulate(self.sim)
            self.gym.fetch_results(self.sim, True)
            self.steps += 1

    def close(self):
        if self.sim is not None:
            self.gym.destroy_sim(self.sim)
            self.sim = None
