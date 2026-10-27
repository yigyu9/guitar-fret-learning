"""Three approved 0.1s controls at the same initial pose; guitar remains free."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path

from .environment import InitialEnvironment, gymapi, np
from .audit_palm_frames import pose
from .initial_overlap import build_probe, query_pairs
from .pose_strap_inputs import pose_metrics
from .run_initialization import snapshot
from .run_physx_contacts import native_state
from .native_contacts import body_names, read_contacts
from .joint_hold_residual import JointHoldResidual
from .palm_position_residual import RatePalmResidual, source_position_jacobian
from .strap import rotate
from .trial_settings import source_hashes


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('PI', 'RATE_PI', 'PALM_RATE'), required=True)
    parser.add_argument('--settings', type=Path, required=True)
    parser.add_argument('--reference-run', type=Path, required=True)
    parser.add_argument('--frame-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise FileExistsError('preserve previous run; use empty directory')
    args.out.mkdir(parents=True, exist_ok=True)
    reference, audit = read(args.reference_run/'report.json'), read(args.frame_dir/'audit.json')
    inputs = dict(reference['source_sha256'], **audit['input_sha256'])
    if not all(reference['checks'].values()) or not all(audit['checks'].values()) or not all(sha(p)==h for p,h in inputs.items()):
        raise ValueError('reference or frame contracts/sources differ')
    inputs.update(source_hashes())
    paths = [args.settings, args.reference_run/'report.json', args.frame_dir/'audit.json']
    paths += [args.reference_run/(n+'.json') for n in ('states', 'trace', 'controls', 'contacts', 'leg_torques')]
    paths += [Path(__file__).with_name(n) for n in ('run_palm_position_compare.py', 'palm_position_residual.py',
        'joint_hold_residual.py', 'compare_palm_fk_coordinates.py', 'audit_palm_frames.py', 'pose_strap_inputs.py', 'plot_neck_palm.py')]
    inputs.update({str(p.resolve()):sha(p) for p in paths})
    outputs = {n:[] for n in ('trace', 'states', 'contacts', 'controls', 'leg_torques', 'hands', 'queries')}
    env = InitialEnvironment(read(args.settings))
    try:
        arm = np.array(reference['arm_indices'])
        expected = [side+'_'+group+'_'+axis for side in ('L', 'R')
            for group in ('Thorax', 'Shoulder', 'Elbow', 'Wrist') for axis in ('x', 'y', 'z')]
        if [env.names[i] for i in arm] != expected or len(env.main_indices)!=66:
            raise ValueError('approved arm24/main66 layout differs')
        if env.config['physics_hz']!=240 or env.config['control_hz']!=60:
            raise ValueError('approved 240/60Hz timing differs')
        if env.names!=reference['human_joint_names'] or env.initial_q.tolist()!=reference['initial_joint_targets_rad']:
            raise ValueError('current initial pose differs')
        low, high = np.array(reference['diagnostic_lower_rad']), np.array(reference['diagnostic_upper_rad'])
        controller = (JointHoldResidual(env.initial_q[arm], low, high) if args.mode=='PI'
            else RatePalmResidual(env.initial_q[arm], low, high, args.mode=='PALM_RATE'))
        other = np.array([i for i in range(len(env.names)) if i not in arm])
        props = env.gym.get_actor_dof_properties(env.env, env.human).copy()
        root = env.bodies(env.human)[0].copy()
        initial_probe = build_probe(env)
        initial_geometry, initial_hand = query_pairs(*initial_probe), pose_metrics(env, initial_probe)
        initial_ok = (initial_geometry['negative_gap_pair_count']==0 and initial_hand['palm_normal_valid']
            and initial_hand['palm_up_dot']>=0 and initial_hand['neck_projection_in_range']
            and initial_hand['palm_height_vs_local_lower_m']<=0)
        (args.out/'initial_source.json').write_text(json.dumps({'accepted':bool(initial_ok),
            'geometry':initial_geometry, 'hand':initial_hand}, indent=2, allow_nan=False)+'\n')
        if not initial_ok:
            raise ValueError('existing initial source/LH conditions failed')
        descriptor = env.gym.acquire_jacobian_tensor(env.sim, 'human')
        shape = (1, len(env.human_bodies)-1, 6, len(env.names))
        if descriptor is None or descriptor.device!=-1 or descriptor.dtype!=gymapi.DTYPE_FLOAT32 or tuple(descriptor.shape)!=shape or not descriptor.data_address:
            raise ValueError('CPU fixed-root float32 Jacobian descriptor differs')
        buffer = np.ctypeslib.as_array(ctypes.cast(descriptor.data_address, ctypes.POINTER(ctypes.c_float)), shape=shape)
        row = env.human_bodies.index('LH:palm')-1
        com_prop = env.gym.get_actor_rigid_body_properties(env.env, env.human)[row+1].com
        local_com = np.array([com_prop.x, com_prop.y, com_prop.z])
        offsets = {s:np.array(audit['saved_points'][0]['palms'][s]['local_offset_m']) for s in ('L', 'R')}
        goal = None
        names = body_names(env.gym, env.env)
        reads_held, targets_held, bounded, rate_bounded = True, True, True, True
        for step in range(25):
            before, before_target = native_state(env), env.target.copy()
            env.gym.refresh_jacobian_tensors(env.sim)
            native = buffer[0, row][:, arm[:12]].copy()
            hand = pose_metrics(env, initial_probe if step==0 else build_probe(env))
            points = {}
            for side, prefix in (('L', 'LH'), ('R', 'RH')):
                body = before['human_body_states'][env.human_bodies.index(prefix+':palm')]
                origin, quat = pose(body)
                points[side] = origin+rotate(quat, offsets[side])
            origin, quat = pose(before['human_body_states'][row+1])
            com = origin+rotate(quat, local_com)
            actual = np.array([d['pos'] for d in before['human_dof_states']])
            matrix = source_position_jacobian(native, actual[arm[:12]], points['L']-com)
            if goal is None:
                goal = points['L'].copy()
                if np.linalg.norm(goal-np.array(initial_hand['palm_center_world_m']))>1e-8:
                    raise ValueError('native source point and source hull center differ')
            reads_held &= bool(before==native_state(env) and np.array_equal(before_target, env.target)
                and np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human)))
            outputs['states'].append(before)
            outputs['trace'].append(snapshot(env))
            outputs['leg_torques'].append(env.last_leg_torques.tolist())
            outputs['hands'].append(dict(hand, physics_step=step))
            outputs['queries'].append({'physics_step':step, 'time_s':step/240,
                'left_source_world_m':points['L'].tolist(), 'right_source_world_m':points['R'].tolist(),
                'left_COM_world_m':com.tolist(), 'left_native_COM_J':native.tolist(),
                'left_position_J_m_per_rad':matrix.tolist(), 'palm_goal_world_m':goal.tolist()})
            if step==24:
                break
            updated = step%4==0
            if updated:
                previous = env.target[arm].astype(float)
                if args.mode=='PI':
                    command, record = controller.update(actual[arm], 1/60)
                else:
                    controller.previous = previous.copy()
                    command, record = controller.update(actual[arm], 1/60, matrix, goal-points['L'])
                main_offsets = np.zeros(66, dtype=np.float32)
                for index, value in zip(arm, command-env.initial_q[arm]):
                    main_offsets[list(env.main_indices).index(index)] = value
                env.set_main_offsets(main_offsets)
                reads_held &= before==native_state(env)
                rate_bounded &= args.mode=='PI' or bool((np.abs(env.target[arm]-previous)<=.02+2e-7).all())
            targets_held &= bool(np.array_equal(env.target[other], env.initial_q[other]))
            bounded &= bool(((env.target[arm]>=low-2e-7)&(env.target[arm]<=high+2e-7)).all()
                and (np.abs(env.target[arm]-env.initial_q[arm])<=.15+2e-7).all())
            outputs['controls'].append(dict(record, physics_step=step+1, updated_before_step=updated,
                final_arm_targets_rad=env.target[arm].astype(float).tolist()))
            env.step_physics()
            before_contacts = native_state(env)
            outputs['contacts'].append({'physics_step':env.steps, 'time_s':env.steps/240,
                'contacts':read_contacts(env.gym, env.env, names)})
            reads_held &= before_contacts==native_state(env)
        checks = {'initial_source_conditions':bool(initial_ok), '25_samples_24_steps':env.steps==24,
            'root_unchanged':bool(np.array_equal(root, env.bodies(env.human)[0])),
            'nonarm_targets_held':targets_held, 'final_target_bounds':bounded, 'final_target_rate_bound':rate_bounded,
            'queries_commands_contacts_preserve_states':bool(reads_held),
            'native_PD_unchanged':bool(np.array_equal(props, env.gym.get_actor_dof_properties(env.env, env.human))),
            'initial_settings_physics_goal_unchanged':env.rest_length==reference['absolute_rest_length_m']
                and env.physics_parameters==reference['physics_parameters']
                and env.goal_position.tolist()==reference['guitar_goal_position_m']
                and env.goal_quaternion.tolist()==reference['guitar_goal_quaternion_xyzw'],
            'fixed_strap_length':all(t['strap_rest_length_m']==env.rest_length for t in outputs['trace']),
            'finite_snapshots':all(t['finite'] for t in outputs['trace']),
            'sources_unchanged':all(sha(p)==h for p,h in inputs.items())}
        if args.mode=='PI':
            for name, count in (('states',25), ('trace',25), ('controls',24), ('contacts',24), ('leg_torques',25)):
                checks[name+'_prefix_exact'] = outputs[name]==read(args.reference_run/(name+'.json'))[:count]
        report = {'mode':args.mode, 'checks':checks, 'input_sha256':inputs,
            'max_position_error_m':max(t['position_error_m'] for t in outputs['trace']),
            'max_rotation_error_deg':max(t['rotation_error_deg'] for t in outputs['trace']),
            'max_left_palm_displacement_m':max(float(np.linalg.norm(np.array(q['left_source_world_m'])-goal)) for q in outputs['queries']),
            'min_palm_up_dot':min(h['palm_up_dot'] for h in outputs['hands']),
            'stability_success':None, 'native_physics_steps':env.steps, 'arm_indices':arm.tolist(),
            'diagnostic_lower_rad':low.tolist(), 'diagnostic_upper_rad':high.tolist(),
            'initial_joint_targets_rad':env.initial_q.astype(float).tolist(),
            'target_precision':'solver/anti-windup float64; native target float32; bound tolerance 2e-7rad; rate uses previous delivered target',
            'scope':'source-center target task diagnostic, not guitar p/q feedback, physical support or playing success'}
        for name, value in dict(outputs, report=report).items():
            (args.out/(name+'.json')).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
        print(json.dumps({'mode':args.mode, 'checks':checks, 'position_mm':report['max_position_error_m']*1000,
            'rotation_deg':report['max_rotation_error_deg'], 'left_palm_mm':report['max_left_palm_displacement_m']*1000}, indent=2))
        if not all(checks.values()):
            raise AssertionError(checks)
    except Exception as error:
        (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__, 'error':str(error),
            'completed_physics_steps':env.steps, 'mode':args.mode}, indent=2)+'\n')
        for name, value in outputs.items():
            (args.out/(name+'.json')).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
        raise
    finally:
        env.close()


if __name__=='__main__':
    main()
