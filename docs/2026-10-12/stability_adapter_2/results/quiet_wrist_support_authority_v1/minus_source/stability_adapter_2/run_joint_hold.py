"""Paired native joint-hold correction diagnostic; guitar remains free."""
import argparse
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, np, gymapi
from .run_physx_contacts import native_state
from .run_initialization import snapshot
from .native_contacts import body_names, read_contacts
from .trial_settings import source_hashes
from .joint_hold_residual import JointHoldResidual


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode',choices=('off','on'),required=True)
    parser.add_argument('--settings',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--physics-steps',type=int,default=24)
    args = parser.parse_args()
    if args.physics_steps<1:
        parser.error('positive physics steps required')
    args.out.mkdir(parents=True,exist_ok=True)
    if any(args.out.iterdir()):
        raise FileExistsError('preserve existing run; use empty directory')
    base_path = Path(__file__).with_name('trials')/'lower_initial_pose_c02.json'
    hashes = source_hashes()
    for path in (Path(__file__).resolve(),Path(__file__).with_name('joint_hold_residual.py'),base_path,args.settings.resolve()):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    base = InitialEnvironment(json.loads(base_path.read_text()))
    try:
        c02 = base.initial_q.copy()
    finally:
        base.close()
    env = InitialEnvironment(json.loads(args.settings.read_text()))
    try:
        arm = np.array([i for i in env.main_indices if not env.names[i].startswith(('LH:','RH:'))])
        other = np.array([i for i in range(len(env.names)) if i not in arm])
        low,high = np.maximum(env.lower[arm],c02[arm]-.3),np.minimum(env.upper[arm],c02[arm]+.3)
        controller = JointHoldResidual(env.initial_q[arm],low,high)
        names = body_names(env.gym,env.env)
        props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
        trace,states,contacts,torques,controls = [snapshot(env)],[native_state(env)],[],[env.last_leg_torques.tolist()],[]
        command_reads_unchanged,nonarm_held,target_bounds,contact_reads = True,True,True,True
        state0 = env.bodies(env.human)[0].copy()
        record = {'error_at_update_rad':[0.]*24,'integral_rad_s':[0.]*24,'raw_delta_rad':[0.]*24,
            'applied_delta_rad':[0.]*24,'integral_blocked':[False]*24,'saturated':[False]*24}
        interval = env.config['physics_hz']//env.config['control_hz']
        if interval*env.config['control_hz']!=env.config['physics_hz']:
            raise ValueError('control rate must divide physics rate')
        for step in range(args.physics_steps):
            updated = args.mode=='on' and step%interval==0
            if updated:
                dofs = env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL).copy()
                before_h,before_g = env.bodies(env.human),env.bodies(env.guitar)
                target,record = controller.update(dofs['pos'][arm],1/env.config['control_hz'])
                offsets = np.zeros(66,dtype=np.float32)
                for i,value in zip(arm,target-env.initial_q[arm]):
                    offsets[list(env.main_indices).index(i)] = value
                env.set_main_offsets(offsets)
                command_reads_unchanged &= bool(np.array_equal(dofs,env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL)) and np.array_equal(before_h,env.bodies(env.human)) and np.array_equal(before_g,env.bodies(env.guitar)))
            nonarm_held &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            target_bounds &= bool(((env.target[arm]>=low-2e-7)&(env.target[arm]<=high+2e-7)).all() and (np.abs(env.target[arm]-env.initial_q[arm])<=.15+2e-7).all())
            controls.append(dict(record,physics_step=step+1,updated_before_step=updated,
                final_arm_targets_rad=env.target[arm].astype(float).tolist()))
            env.step_physics()
            before_h,before_g = env.bodies(env.human),env.bodies(env.guitar)
            contacts.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'contacts':read_contacts(env.gym,env.env,names)})
            contact_reads &= bool(np.array_equal(before_h,env.bodies(env.human)) and np.array_equal(before_g,env.bodies(env.guitar)))
            trace.append(snapshot(env));states.append(native_state(env));torques.append(env.last_leg_torques.tolist())
        current_hashes = {p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in hashes}
        checks = {'arm24_layout':len(arm)==24,'initial_guitar_goal_match':trace[0]['position_error_m']<1e-6 and trace[0]['rotation_error_deg']<.001,
            'root_unchanged':bool(np.array_equal(state0,env.bodies(env.human)[0])),
            'torso_fingers_lower_targets_held':nonarm_held,'arm_target_bounds':target_bounds,
            'commands_do_not_write_states':command_reads_unchanged,'contact_reads_preserve_states':contact_reads,
            'native_pd_unchanged':bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))),
            'fixed_absolute_length':all(s['strap_rest_length_m']==env.rest_length for s in trace),
            'all_snapshots_finite':all(s['finite'] for s in trace),'runtime_sources_unchanged':hashes==current_hashes}
        report = {'scope':'joint-error target correction only; no guitar-error feedback or stability success','mode':args.mode,'checks':checks,
            'initial_settings':env.initial_settings,'human_joint_names':list(env.names),'human_body_names':env.human_bodies,'guitar_body_names':env.guitar_bodies,
            'initial_joint_targets_rad':env.initial_q.astype(float).tolist(),'arm_indices':arm.tolist(),'arm_names':[env.names[i] for i in arm],
            'diagnostic_lower_rad':low.astype(float).tolist(),'diagnostic_upper_rad':high.astype(float).tolist(),
            'native_joint_lower_rad':env.lower.astype(float).tolist(),'native_joint_upper_rad':env.upper.astype(float).tolist(),
            'native_pd_kp':props['stiffness'].astype(float).tolist(),'native_pd_kd':props['damping'].astype(float).tolist(),
            'native_drive_modes':props['driveMode'].astype(int).tolist(),'native_effort_caps_nm':props['effort'].astype(float).tolist(),
            'physics_parameters':env.physics_parameters,'physics_steps':env.steps,'physics_hz':env.config['physics_hz'],'control_hz':env.config['control_hz'],
            'guitar_goal_position_m':env.goal_position.tolist(),'guitar_goal_quaternion_xyzw':env.goal_quaternion.tolist(),
            'absolute_rest_length_m':env.rest_length,'initial_route_length_m':env.initial_route_length,
            'max_position_error_m':max(s['position_error_m'] for s in trace),'max_rotation_error_deg':max(s['rotation_error_deg'] for s in trace),
            'max_applied_strap_tension_n':max(s['last_applied_tension_n'] for s in trace[1:]),
            'controller':{'proportional_gain':1.,'integral_gain_per_s':2.,'delta_cap_rad':.15,'global_initial_box_rad':.3,'anti_windup':'conditional integration using final clipped delta'},
            'source_sha256':hashes,'stability_success':None}
        for name,value in (('report',report),('trace',trace),('states',states),('contacts',contacts),('leg_torques',torques),('controls',controls)):
            (args.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'checks':checks,'p_m':report['max_position_error_m'],'q_deg':report['max_rotation_error_deg']},indent=2))
        if not all(checks.values()):
            raise SystemExit(1)
    finally:
        env.close()


if __name__=='__main__':
    main()
