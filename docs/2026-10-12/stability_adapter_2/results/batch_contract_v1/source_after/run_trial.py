"""One isolated initial-setting diagnostic; completion is not stability success."""
import argparse
import json
from pathlib import Path
import time

from .environment import InitialEnvironment, gymapi, np, vector, quaternion
from .initial_overlap import build_probe, query_pairs
from .run_initialization import snapshot
from .trial_settings import source_hashes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--steps', type=int, default=6)
    args = parser.parse_args()
    if args.steps < 0:
        parser.error('steps must be nonnegative')
    args.out.mkdir(parents=True, exist_ok=True)
    if any((args.out/n).exists() for n in ('report.json','trace.json')):
        raise FileExistsError('use a new trial attempt directory')
    started = time.perf_counter()
    env = InitialEnvironment(json.loads(args.settings.read_text()))
    try:
        initial = env.gym.get_actor_dof_states(env.env, env.human, gymapi.STATE_ALL).copy()
        root = env.bodies(env.human)[0].copy()
        bodies = env.bodies(env.human)
        points = {n:vector(bodies[env.human_bodies.index(n)]['pose']['p'])
            for n in ('L_Wrist','LH:index1','LH:middle1','LH:pinky1')}
        normal = np.cross(points['LH:middle1']-points['L_Wrist'],points['LH:index1']-points['LH:pinky1'])
        norm = np.linalg.norm(normal)
        palm_valid = norm > 1e-8
        normal = normal/norm if palm_valid else None
        model, data, shapes = build_probe(env)
        geometry = query_pairs(model,data,shapes)
        if not np.array_equal(initial,env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)):
            raise AssertionError('static query changed initial joints')
        trace = [snapshot(env)]
        for _ in range(args.steps):
            env.step()
            trace.append(snapshot(env))
        for s in trace:
            if not s['finite'] or not all(np.isfinite(s[k]) for k in (
                    'position_error_m','rotation_error_deg','linear_speed_mps','angular_speed_rad_s')):
                raise FloatingPointError('nonfinite diagnostic trace')
        root_after = env.bodies(env.human)[0]
        checks = {'initial_joint_state_matches_target':bool(np.array_equal(initial['pos'],env.initial_q)),
            'initial_joint_velocity_zero':bool((initial['vel']==0).all()),
            'initial_guitar_matches_immutable_source':trace[0]['position_error_m']<1e-6 and trace[0]['rotation_error_deg']<.001,
            'initial_guitar_velocity_zero':trace[0]['linear_speed_mps']==0 and trace[0]['angular_speed_rad_s']==0,
            'held_targets_unchanged':bool(np.array_equal(env.target,env.initial_q)),
            'fixed_human_root_unchanged':bool(np.allclose(vector(root['pose']['p']),vector(root_after['pose']['p']),atol=1e-6,rtol=0)
                and np.allclose(quaternion(root['pose']['r']),quaternion(root_after['pose']['r']),atol=1e-6,rtol=0))}
        if not all(checks.values()):
            raise AssertionError('initial-setting contract failed: '+str(checks))
        report = {'completed':True, 'scope':'initial input/short rollout diagnostic; not a cleared stable candidate',
            'stability_success':None, 'control_steps':args.steps, 'physics_steps':env.steps,
            'wall_time_s':time.perf_counter()-started,
            'initial_settings':env.initial_settings, 'checks':checks,
            'initial_joint_angles_rad':dict(zip(env.names,initial['pos'].astype(float).tolist())),
            'initial_route_length_m':env.initial_route_length, 'absolute_rest_length_m':env.rest_length,
            'guitar_goal_position_m':env.goal_position.tolist(),'guitar_goal_quaternion_xyzw':env.goal_quaternion.tolist(),
            'initial_geometry':geometry, 'initial_palm_normal_world':None if normal is None else normal.tolist(),
            'initial_palm_up_dot':None if normal is None else float(normal[2]),'initial_palm_normal_valid':bool(palm_valid),
            'initial_palm_normal_definition':'normalize(cross(middle1-wrist,index1-pinky1)); anatomical sign awaits visual validation',
            'peak_position_error_m':max(s['position_error_m'] for s in trace),
            'peak_rotation_error_deg':max(s['rotation_error_deg'] for s in trace),
            'last_sample':trace[-1], 'source_sha256':source_hashes(),
            'not_verified':['PhysX clearance/start gate','palm anatomical sign','local neck workspace gate',
                'runtime penetration/contact','feedback','stability success','playing compatibility']}
        (args.out/'trace.json').write_text(json.dumps(trace,indent=2,allow_nan=False)+'\n')
        temp = args.out/'report.tmp'
        temp.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        temp.replace(args.out/'report.json')
        print(json.dumps({k:report[k] for k in ('completed','checks','absolute_rest_length_m','peak_position_error_m','peak_rotation_error_deg')},indent=2))
    finally:
        env.close()


if __name__=='__main__':
    main()
