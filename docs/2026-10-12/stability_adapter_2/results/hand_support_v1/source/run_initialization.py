"""Audit the initial scene and short target-hold rollout; no stability success gate."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, ROOT, CONFIG_PATH, vector, quaternion, gymapi, np


def snapshot(env):
    guitar = env.bodies(env.guitar)[0]
    pos = vector(guitar["pose"]["p"])
    q = quaternion(guitar["pose"]["r"])
    q /= np.linalg.norm(q)
    dof = env.gym.get_actor_dof_states(env.env, env.human, gymapi.STATE_ALL)
    points, velocities = env.route()
    return {
        "time_s": env.steps / env.config["physics_hz"],
        "guitar_position_m": pos.tolist(), "guitar_quaternion_xyzw": q.tolist(),
        "position_error_m": float(np.linalg.norm(pos-env.goal_position)),
        "source_position_error_m": float(np.linalg.norm(pos-env.source_goal_position)),
        "rotation_error_deg": float(np.degrees(2*np.arccos(np.clip(abs(q @ env.goal_quaternion), 0, 1)))),
        "linear_speed_mps": float(np.linalg.norm(vector(guitar["vel"]["linear"]))),
        "angular_speed_rad_s": float(np.linalg.norm(vector(guitar["vel"]["angular"]))),
        "torso_drift_deg": np.degrees(dof["pos"][env.torso_indices]-env.initial_q[env.torso_indices]).tolist(),
        "strap_length_m": float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum()),
        "strap_rest_length_m": env.rest_length, "last_applied_tension_n": env.tension,
        "route_points_m": points.tolist(), "route_point_velocities_mps": velocities.tolist(),
        "finite": bool(np.isfinite(dof["pos"]).all() and np.isfinite(dof["vel"]).all()
                       and np.isfinite(points).all() and np.isfinite(velocities).all()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=6, help="control steps; default 0.1s")
    args = parser.parse_args()
    if args.steps < 0:
        parser.error("steps must be nonnegative")
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / "report.json").exists():
        raise FileExistsError("use a new output directory")
    env = InitialEnvironment()
    try:
        dof = env.gym.get_actor_dof_states(env.env, env.human, gymapi.STATE_ALL).copy()
        root_before = env.bodies(env.human)[0].copy()
        props = env.gym.get_actor_dof_properties(env.env, env.human)
        checks = {
            "main_joint_count_66": len(env.main_indices) == 66,
            "torso_joint_count_9": len(env.torso_indices) == 9,
            "initial_joint_state_matches_target": bool(np.array_equal(dof["pos"], env.initial_q)),
            "initial_joint_velocity_zero": bool((dof["vel"] == 0).all()),
            "initial_target_inside_limits": bool(((env.target >= env.lower) & (env.target <= env.upper)).all()),
            "human_root_fixed_option": bool(env.human_root_fixed),
            "guitar_root_free_option": not env.guitar_root_fixed,
            "guitar_gravity_enabled_option": not env.guitar_gravity_disabled,
            "native_position_drive_with_shared_gains": bool((props["driveMode"] == gymapi.DOF_MODE_POS).all()
                and np.array_equal(props["stiffness"], env.kp) and np.array_equal(props["damping"], env.kd)
                and np.array_equal(props["effort"], env.effort)),
            "marker_collision_filters_disabled": all(all(v == 3 for v in values) for values in env.collision_filters.values()),
        }
        env.set_main_offsets(np.full(66, .001, dtype=np.float32))
        others = np.ones(len(env.names), dtype=bool)
        others[env.main_indices] = False
        checks["target_command_preserves_torso_and_other_joints"] = bool(np.array_equal(env.target[others], env.initial_q[others]))
        checks["target_command_does_not_write_joint_state"] = bool(np.array_equal(
            env.gym.get_actor_dof_states(env.env, env.human, gymapi.STATE_ALL), dof))
        env.set_main_offsets(np.zeros(66, dtype=np.float32))
        trace = [snapshot(env)]
        checks["initial_guitar_pose_matches_source"] = trace[0]["position_error_m"] < 1e-6 and trace[0]["rotation_error_deg"] < .001
        checks["initial_guitar_velocity_zero"] = trace[0]["linear_speed_mps"] == 0 and trace[0]["angular_speed_rad_s"] == 0
        for _ in range(args.steps):
            env.step()
            trace.append(snapshot(env))
        root_after = env.bodies(env.human)[0]
        checks["human_root_unchanged_after_short_rollout"] = bool(np.allclose(
            vector(root_before["pose"]["p"]), vector(root_after["pose"]["p"]), atol=1e-6, rtol=0)
            and np.allclose(quaternion(root_before["pose"]["r"]), quaternion(root_after["pose"]["r"]), atol=1e-6, rtol=0))
        checks["finite_short_rollout"] = all(s["finite"] for s in trace)
        sources = [CONFIG_PATH] + [ROOT/env.config[k] for k in ("humanoid_asset", "guitar_asset", "pose_source", "gain_source")]
        sources += [Path(__file__), Path(__file__).with_name("environment.py"), Path(__file__).with_name("control.py"), Path(__file__).with_name("strap.py")]
        report = {
            "scope": "CPU initialization and short target-hold rollout only; native actuation tested separately; no pose stability or rendering gate",
            "checks": checks, "initialization_checks_passed": all(checks.values()),
            "backend": "CPU PhysX; native NumPy API", "physics_steps": env.steps,
            "joint_controller": "native solver POS PD; shared kp/kd/effort caps; differs from common tensor hybrid PD",
            "collision_filters_readback": env.collision_filters,
            "route_local_com_m": [v.tolist() for v in env.route_com],
            "main_joint_names": [env.names[i] for i in env.main_indices],
            "torso_held_joint_names": [env.names[i] for i in env.torso_indices],
            "initial_limit_adjustments_rad": {n:float(v) for n,v in zip(env.names,env.initial_adjustment) if abs(v)>1e-7},
            "guitar_mass_kg": env.guitar_mass, "initial_rest_length_m": env.rest_length,
            "kp": dict(zip(env.names, env.kp.tolist())), "kd": dict(zip(env.names, env.kd.tolist())),
            "configured_effort_caps_nm": dict(zip(env.names, env.effort.tolist())),
            "last_sample": trace[-1], "source_sha256": {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            "not_verified": ["GPU/rendering", "initial penetration/contact quality", "position/orientation stability", "feedback controller", "playing compatibility"],
        }
        (args.out / "trace.json").write_text(json.dumps(trace, indent=2)+'\n')
        (args.out / "report.json").write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps({"checks":checks, "last_sample":trace[-1]}, indent=2))
        if not report["initialization_checks_passed"]:
            raise SystemExit(1)
    finally:
        env.close()


if __name__ == "__main__":
    main()
