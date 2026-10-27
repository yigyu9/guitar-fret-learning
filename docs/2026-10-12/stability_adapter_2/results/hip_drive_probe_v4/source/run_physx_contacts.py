"""Read contacts, strap tension and free-guitar state at every physics step."""
import argparse
import json
from pathlib import Path

from .environment import InitialEnvironment, gymapi, np, vector, quaternion
from .native_contacts import body_names, read_contacts, plain
from .run_initialization import snapshot
from .trial_settings import source_hashes
from .physics_presets import PRESETS


def native_state(env):
    return {'physics_step':env.steps,'human_body_states':plain(env.bodies(env.human)),
        'guitar_body_states':plain(env.bodies(env.guitar)),
        'human_dof_states':plain(env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--physics-steps',type=int,default=24)
    parser.add_argument('--preset',choices=list(PRESETS),default='baseline')
    args = parser.parse_args()
    if args.physics_steps<1:
        parser.error('physics-steps must be positive')
    args.out.mkdir(parents=True,exist_ok=True)
    if any((args.out/name).exists() for name in ('report.json','trace.json','contacts.json','states.json','leg_torques.json')):
        raise FileExistsError('preserve existing run; use new directory')
    hashes = source_hashes()
    env = InitialEnvironment(json.loads(args.settings.read_text()),diagnostic_preset=args.preset)
    try:
        names = body_names(env.gym,env.env)
        params = env.gym.get_sim_params(env.sim)
        props = env.gym.get_actor_dof_properties(env.env,env.human)
        root = env.bodies(env.human)[0].copy()
        trace = [snapshot(env)]
        states = [native_state(env)]
        torques = [env.last_leg_torques.tolist()]
        samples = []
        queries_unchanged = True
        for _ in range(args.physics_steps):
            env.step_physics()
            human_before,guitar_before = env.bodies(env.human),env.bodies(env.guitar)
            contacts = read_contacts(env.gym,env.env,names)
            queries_unchanged &= bool(np.array_equal(human_before,env.bodies(env.human))
                and np.array_equal(guitar_before,env.bodies(env.guitar)))
            trace.append(snapshot(env))
            states.append(native_state(env))
            torques.append(env.last_leg_torques.tolist())
            samples.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],
                            'contacts':contacts})
        root_after = env.bodies(env.human)[0]
        checks = {'initial_guitar_matches_source':trace[0]['position_error_m']<1e-6 and trace[0]['rotation_error_deg']<.001,
            'initial_guitar_velocity_zero':trace[0]['linear_speed_mps']==0 and trace[0]['angular_speed_rad_s']==0,
            'held_targets_unchanged':bool(np.array_equal(env.target,env.initial_q)),
            'human_root_unchanged':bool(np.array_equal(vector(root['pose']['p']),vector(root_after['pose']['p']))
                and np.array_equal(quaternion(root['pose']['r']),quaternion(root_after['pose']['r']))),
            'contact_reads_preserve_native_states':queries_unchanged,
            'all_snapshots_finite':all(s['finite'] for s in trace),
            'runtime_sources_unchanged':hashes==source_hashes()}
        checks['native_solver_parameters_match'] = bool(params.substeps==env.physics_parameters.get('substeps',1)
            and params.physx.solver_type==env.physics_parameters.get('solver_type',1)
            and params.physx.num_position_iterations==env.physics_parameters['position_iterations']
            and params.physx.num_velocity_iterations==env.physics_parameters['velocity_iterations']
            and np.isclose(params.physx.max_depenetration_velocity,env.physics_parameters.get('max_depenetration_velocity',10.)))
        expected_kp,expected_kd = env.kp.copy(),env.kd.copy()
        if env.physics_parameters.get('leg_drive') in ('effort','none'):
            expected_kp[env.leg_indices]=expected_kd[env.leg_indices]=0
        checks['native_pd_properties_match'] = bool(np.array_equal(props['stiffness'],expected_kp)
            and np.array_equal(props['damping'],expected_kd) and np.array_equal(props['effort'],env.effort))
        report = {'scope':'240Hz native contact/strap diagnostic; no start gate or stability success',
            'diagnostic_preset':env.diagnostic_preset,'physics_parameters':env.physics_parameters,
            'initial_settings':env.initial_settings,'checks':checks,'physics_steps':env.steps,
            'physics_hz':env.config['physics_hz'],'substeps':params.substeps,'contact_collection':'CC_LAST_SUBSTEP',
            'body_names_by_env_id':names,'human_body_names':env.human_bodies,
            'guitar_body_names':env.guitar_bodies,'human_joint_names':env.names,
            'initial_joint_targets_rad':env.initial_q.astype(float).tolist(),
            'native_joint_lower_rad':env.lower.astype(float).tolist(),
            'native_joint_upper_rad':env.upper.astype(float).tolist(),
            'native_pd_kp':props['stiffness'].astype(float).tolist(),'native_pd_kd':props['damping'].astype(float).tolist(),
            'controller_kp':env.kp.astype(float).tolist(),'controller_kd':env.kd.astype(float).tolist(),
            'native_drive_modes':props['driveMode'].astype(int).tolist(),
            'leg_torque_joint_names':[env.names[i] for i in env.leg_indices],
            'native_effort_caps_nm':env.effort.astype(float).tolist(),
            'guitar_goal_position_m':env.goal_position.tolist(),
            'guitar_goal_quaternion_xyzw':env.goal_quaternion.tolist(),
            'initial_route_length_m':env.initial_route_length,'absolute_rest_length_m':env.rest_length,
            'contact_time_semantics':'sample at completed simulate/fetch; CC_LAST_SUBSTEP initialOverlap refers to start of last internal substep; no t=0 cached contact read',
            'field_semantics':{'initialOverlap':'raw native signed feature gap in metres; analytic box calibration required',
                'minDist':'raw native target feature distance; not measured clearance',
                'lambda':'raw native API scalar; force/impulse units uncalibrated',
                'last_applied_tension_n':'strap force magnitude applied over immediately preceding single physics step'},
            'max_position_error_m':max(s['position_error_m'] for s in trace),
            'max_rotation_error_deg':max(s['rotation_error_deg'] for s in trace),
            'max_applied_strap_tension_n':max(s['last_applied_tension_n'] for s in trace[1:]),
            'last_sample':trace[-1],'stability_success':None,'source_sha256':hashes,
            'not_verified':['full initial clearance','cooked/source geometry equivalence','contact causal attribution',
                'palm/local-neck start gate','actual joint torque','feedback','playing compatibility']}
        for name,value in (('trace.json',trace),('contacts.json',samples),('states.json',states),('leg_torques.json',torques),('report.json',report)):
            (args.out/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:report[k] for k in ('checks','max_position_error_m','max_rotation_error_deg','max_applied_strap_tension_n')},indent=2))
        if not all(checks.values()):
            raise SystemExit(1)
    finally:
        env.close()


if __name__ == '__main__':
    main()
