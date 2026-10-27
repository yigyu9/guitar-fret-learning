"""Six isolated CPU shoulder-hinge cases; no main humanoid/guitar changes."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .environment import ROOT, gymapi, np, transform
from .native_contacts import plain, body_names, read_contacts

SOURCE = ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def finite(value):
    if isinstance(value, dict):
        return all(finite(v) for v in value.values())
    if isinstance(value, list):
        return all(finite(v) for v in value)
    return bool(np.isfinite(value))


def fixture_xml():
    shoulder = ET.parse(SOURCE).find('.//body[@name="L_Shoulder"]')
    joint = shoulder.find('joint[@name="L_Shoulder_x"]')
    root = ET.Element('mujoco', model='tensor_effort_api_probe')
    ET.SubElement(root, 'compiler', angle='degree')
    base = ET.SubElement(ET.SubElement(root, 'worldbody'), 'body', name='base')
    ET.SubElement(base, 'freejoint', name='base')
    ET.SubElement(base, 'geom', type='box', size='.05 .05 .05', mass='1')
    child = ET.SubElement(base, 'body', name='L_Shoulder', pos=shoulder.get('pos'))
    ET.SubElement(child, 'joint', dict(joint.attrib))
    ET.SubElement(child, 'geom', dict(shoulder.find('geom').attrib))
    return ET.tostring(root, encoding='unicode')


def run_case(fixture, drive, torque, output):
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams()
    params.dt, params.substeps = 1/240, 1
    params.up_axis, params.gravity = gymapi.UP_AXIS_Z, gymapi.Vec3(0, 0, 0)
    params.use_gpu_pipeline = params.physx.use_gpu = False
    params.physx.solver_type = 1
    params.physx.num_position_iterations, params.physx.num_velocity_iterations = 4, 2
    params.physx.contact_collection = gymapi.ContactCollection.CC_LAST_SUBSTEP
    sim = gym.create_sim(0, -1, gymapi.SIM_PHYSX, params)
    if sim is None:
        raise RuntimeError('fixture simulation creation failed')
    record = {'drive':drive, 'torque_nm':torque, 'trace':[], 'submissions':[], 'contacts':[]}
    try:
        options = gymapi.AssetOptions()
        options.fix_base_link = True
        asset = gym.load_asset(sim, str(fixture.parent), fixture.name, options)
        if asset is None:
            raise RuntimeError('fixture load failed')
        env = gym.create_env(sim, gymapi.Vec3(-1,-1,-1), gymapi.Vec3(1,1,1), 1)
        actor = gym.create_actor(env, asset, transform([0,0,1], [1,0,0,0]), 'fixture', 0, 1)
        names = list(gym.get_actor_dof_names(env, actor))
        if names != ['L_Shoulder_x'] or gym.get_sim_dof_count(sim) != 1:
            raise AssertionError('expected one global shoulder DOF')
        props = gym.get_actor_dof_properties(env, actor)
        props['driveMode'][:] = gymapi.DOF_MODE_POS if drive == 'POS' else gymapi.DOF_MODE_EFFORT
        props['stiffness'][:], props['damping'][:], props['effort'][:] = 0, 50, 150
        if not gym.set_actor_dof_properties(env, actor, props) or not gym.prepare_sim(sim):
            raise RuntimeError('fixture prepare failed')
        initial = np.zeros(1, dtype=gymapi.DofState.dtype)
        if not gym.set_actor_dof_states(env, actor, initial, gymapi.STATE_ALL):
            raise RuntimeError('initial state rejected')
        if drive == 'POS' and not gym.set_actor_dof_position_targets(env, actor, np.zeros(1,np.float32)):
            raise RuntimeError('initial target rejected')
        actual = gym.get_actor_dof_properties(env, actor)
        state = gym.get_actor_dof_states(env, actor, gymapi.STATE_ALL)
        runtime = gym.get_sim_params(sim)
        command = np.array([torque], dtype=np.float32)
        descriptor = gymapi.Tensor()
        descriptor.device, descriptor.dtype = -1, gymapi.DTYPE_FLOAT32
        descriptor.shape, descriptor.data_address = [1], command.ctypes.data
        descriptor.own_data = False
        checks = {
            'initial_state_exact':bool(np.array_equal(state, initial)),
            'initial_within_limits':bool(actual['lower'][0] <= 0 <= actual['upper'][0]),
            'native_properties_exact':bool(np.array_equal(actual, props)),
            'CPU_solver_matches':bool(not runtime.use_gpu_pipeline and not runtime.physx.use_gpu
                and np.isclose(runtime.dt, 1/240) and runtime.substeps == 1
                and runtime.physx.solver_type == 1 and runtime.physx.num_position_iterations == 4
                and runtime.physx.num_velocity_iterations == 2),
            'gravity_zero':bool(runtime.gravity.x == runtime.gravity.y == runtime.gravity.z == 0),
            'velocity_target_zero':bool(np.all(gym.get_actor_dof_velocity_targets(env,actor) == 0)),
            'descriptor_matches':bool(descriptor.device == -1 and descriptor.dtype == gymapi.DTYPE_FLOAT32
                and tuple(descriptor.shape) == (1,) and descriptor.data_address == command.ctypes.data
                and not descriptor.own_data and command.flags.c_contiguous),
        }
        record.update({'checks':checks, 'joint_names':names, 'native_properties':plain(actual),
            'runtime':{'dt_s':runtime.dt, 'substeps':runtime.substeps,
                'use_gpu_pipeline':runtime.use_gpu_pipeline, 'physx_use_gpu':runtime.physx.use_gpu,
                'solver_type':runtime.physx.solver_type,
                'position_iterations':runtime.physx.num_position_iterations,
                'velocity_iterations':runtime.physx.num_velocity_iterations,
                'gravity':[runtime.gravity.x,runtime.gravity.y,runtime.gravity.z]},
            'descriptor':{'device':descriptor.device, 'shape':list(descriptor.shape),
                'dtype':int(descriptor.dtype), 'own_data':descriptor.own_data},
            'fixture_sha256':sha(fixture)})
        if not all(checks.values()):
            raise AssertionError(checks)
        mapping = body_names(gym, env)
        for step in range(25):
            state = gym.get_actor_dof_states(env, actor, gymapi.STATE_ALL)
            bodies = gym.get_actor_rigid_body_states(env, actor, gymapi.STATE_ALL)
            if not finite(plain(state)) or not finite(plain(bodies)):
                raise FloatingPointError('nonfinite fixture state')
            record['trace'].append({'physics_step':step, 'time_s':step/240,
                'q_rad':float(state['pos'][0]), 'velocity_rad_s':float(state['vel'][0]),
                'bodies':plain(bodies)})
            if step == 24:
                break
            accepted = gym.set_dof_actuation_force_tensor(sim, descriptor)
            record['submissions'].append({'physics_step':step, 'torque_nm':float(command[0]),
                'API_accepted':bool(accepted)})
            if not accepted:
                raise RuntimeError('force tensor API rejected')
            gym.simulate(sim)
            gym.fetch_results(sim, True)
            contacts = read_contacts(gym, env, mapping)
            record['contacts'].append(contacts)
            if contacts:
                raise AssertionError('unexpected fixture contact')
        checks['runtime_properties_unchanged'] = bool(np.array_equal(actual,gym.get_actor_dof_properties(env,actor)))
        checks['coverage25_states24_commands'] = len(record['trace']) == 25 and len(record['submissions']) == 24
        if not all(checks.values()):
            raise AssertionError(checks)
        record['status'] = 'complete'
        return record
    except Exception as error:
        record.update({'status':'failed', 'error':repr(error)})
        raise
    finally:
        try:
            save(output, record)
        finally:
            gym.destroy_sim(sim)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    sources = [SOURCE, Path(__file__).resolve(), Path(__file__).with_name('environment.py'),
        Path(__file__).with_name('native_contacts.py'), ROOT/'isaacgym/python/isaacgym/gymtorch.py']
    inputs = {str(p):sha(p) for p in sources}
    fixture = args.out/'shoulder_hinge.xml'
    fixture.write_text(fixture_xml())
    save(args.out/'inputs.json', {'input_sha256':inputs, 'fixture_sha256':sha(fixture)})
    rows = []
    for drive in ('EFFORT', 'POS'):
        for torque in (0, 1, -1):
            case = drive+'_'+str(torque)
            print('starting '+case, flush=True)
            rows.append(run_case(fixture, drive, torque, args.out/(case+'.json')))
            print('completed '+case, flush=True)
    if not all(sha(p) == h for p,h in inputs.items()):
        raise AssertionError('source changed during execution')
    comparisons = {}
    for drive in ('EFFORT', 'POS'):
        baseline = np.array([[r['q_rad'],r['velocity_rad_s']] for r in next(x for x in rows if x['drive']==drive and x['torque_nm']==0)['trace']])
        comparisons[drive] = []
        for row in (x for x in rows if x['drive']==drive and x['torque_nm']!=0):
            measured = np.array([[r['q_rad'],r['velocity_rad_s']] for r in row['trace']])
            delta = measured-baseline
            comparisons[drive].append({'torque_nm':row['torque_nm'], 'exact_zero_baseline':bool(np.array_equal(measured,baseline)),
                'final_delta_q_rad':float(delta[-1,0]), 'final_delta_velocity_rad_s':float(delta[-1,1]),
                'max_abs_delta_q_rad':float(abs(delta[:,0]).max())})
    save(args.out/'comparison.json', {'comparisons':comparisons, 'input_sha256':inputs,
        'fresh_simulations':6, 'physics_steps':144,
        'scope':'isolated CPU single hinge only; not original GPU/humanoid/guitar actuator equivalence'})


if __name__ == '__main__':
    main()
