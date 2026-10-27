"""Small isolated source-hip drive diagnostics; never changes the main scene."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .environment import ROOT, gymapi, np, transform
from .native_contacts import plain, body_names, read_contacts


SOURCE = ROOT/'tab2body/assets/smpl_mpl_hands_body.xml'


def fixture_xml(count, wide):
    hip = ET.parse(SOURCE).find('.//body[@name="L_Hip"]')
    root = ET.Element('mujoco',model='hip_drive_probe')
    ET.SubElement(root,'compiler',angle='degree')
    world = ET.SubElement(root,'worldbody')
    base = ET.SubElement(world,'body',name='base')
    ET.SubElement(base,'freejoint',name='base')
    ET.SubElement(base,'geom',type='box',size='.05 .05 .05',mass='1')
    child = ET.SubElement(base,'body',name='L_Hip',pos=hip.get('pos'))
    for source in hip.findall('joint')[:count]:
        fields = dict(source.attrib)
        fields['limited'] = 'true'
        if wide:
            fields['range'] = '-180 180'
        ET.SubElement(child,'joint',fields)
    ET.SubElement(child,'geom',dict(hip.find('geom').attrib))
    return ET.tostring(root,encoding='unicode')


def run_case(path, count, x, drive):
    gym = gymapi.acquire_gym()
    params = gymapi.SimParams()
    params.dt,params.substeps = 1/240,1
    params.up_axis = gymapi.UP_AXIS_Z
    params.gravity = gymapi.Vec3(0,0,0)
    params.use_gpu_pipeline = params.physx.use_gpu = False
    params.physx.solver_type = 1
    params.physx.num_position_iterations = 4
    params.physx.num_velocity_iterations = 2
    params.physx.contact_collection = gymapi.ContactCollection.CC_LAST_SUBSTEP
    sim = gym.create_sim(0,-1,gymapi.SIM_PHYSX,params)
    if sim is None:
        raise RuntimeError('native fixture sim creation failed')
    try:
        options = gymapi.AssetOptions()
        options.fix_base_link = True
        asset = gym.load_asset(sim,str(path.parent),path.name,options)
        if asset is None:
            raise RuntimeError('fixture asset load failed')
        env = gym.create_env(sim,gymapi.Vec3(-1,-1,-1),gymapi.Vec3(1,1,1),1)
        actor = gym.create_actor(env,asset,transform([0,0,1],[1,0,0,0]),'fixture',0,1)
        names = list(gym.get_actor_dof_names(env,actor))
        if len(names)!=count or names[0]!='L_Hip_x':
            raise AssertionError('unexpected fixture DOFs')
        props = gym.get_actor_dof_properties(env,actor)
        props['driveMode'][:]=gymapi.DOF_MODE_POS
        props['stiffness'][:],props['damping'][:],props['effort'][:]=300,75,300
        if drive in ('off','effort'):
            props['driveMode'][:]=gymapi.DOF_MODE_NONE if drive=='off' else gymapi.DOF_MODE_EFFORT
            props['stiffness'][:]=props['damping'][:]=0
        if not gym.set_actor_dof_properties(env,actor,props) or not gym.prepare_sim(sim):
            raise RuntimeError('fixture initialization failed')
        q0 = np.zeros(count,dtype=np.float32)
        q0[0]=x
        states = np.zeros(count,dtype=gymapi.DofState.dtype)
        states['pos']=q0
        if not gym.set_actor_dof_states(env,actor,states,gymapi.STATE_ALL):
            raise RuntimeError('initial state rejected')
        if drive=='position' and not gym.set_actor_dof_position_targets(env,actor,q0):
            raise RuntimeError('initial target rejected')
        actual = gym.get_actor_dof_properties(env,actor)
        initial = gym.get_actor_dof_states(env,actor,gymapi.STATE_ALL)
        runtime = gym.get_sim_params(sim)
        checks = {'initial_positions_match':bool(np.array_equal(initial['pos'],q0)),
            'initial_velocity_zero':bool(np.all(initial['vel']==0)),
            'properties_match':all(np.array_equal(actual[k],props[k]) for k in
                ('lower','upper','driveMode','stiffness','damping','effort','armature')),
            'solver_matches':bool(runtime.physx.solver_type==1 and runtime.substeps==1
                and np.isclose(runtime.dt,1/240) and runtime.physx.num_position_iterations==4
                and runtime.physx.num_velocity_iterations==2),
            'gravity_zero':bool(runtime.gravity.x==runtime.gravity.y==runtime.gravity.z==0),
            'initial_angles_within_native_limits':bool(np.all(q0>=actual['lower']) and np.all(q0<=actual['upper']))}
        if drive=='position':
            checks['position_targets_match'] = bool(np.array_equal(gym.get_actor_dof_position_targets(env,actor),q0))
        trace,contacts = [],[]
        last_torque = None
        mapping = body_names(gym,env)
        for step in range(25):
            trace.append({'physics_step':step,
                'dofs':plain(gym.get_actor_dof_states(env,actor,gymapi.STATE_ALL)),
                'bodies':plain(gym.get_actor_rigid_body_states(env,actor,gymapi.STATE_ALL)),
                'previous_submitted_torque_nm':last_torque})
            if step==24:
                break
            if drive=='effort':
                state = gym.get_actor_dof_states(env,actor,gymapi.STATE_ALL)
                torque = np.clip(300*(q0-state['pos'])-75*state['vel'],-300,300).astype(np.float32)
                if not np.isfinite(torque).all() or not gym.apply_actor_dof_efforts(env,actor,torque):
                    raise RuntimeError('fixture effort rejected or nonfinite')
                last_torque = torque.tolist()
            gym.simulate(sim)
            gym.fetch_results(sim,True)
            contacts.append(read_contacts(gym,env,mapping))
        q = np.array([[d['pos'] for d in s['dofs']] for s in trace])
        checks['q_finite'] = bool(np.isfinite(q).all())
        checks['no_contact_records'] = all(not sample for sample in contacts)
        if not all(checks.values()):
            raise AssertionError(checks)
        return {'drive':drive,'joint_names':names,'initial_targets_rad':q0.tolist(),
            'native_velocity_targets_rad_s':gym.get_actor_dof_velocity_targets(env,actor).tolist(),
            'native_properties':plain(actual),'checks':checks,
            'native_joint_types':[gym.get_joint_type_string(gym.get_asset_joint_type(asset,i))
                for i in range(gym.get_asset_joint_count(asset))],
            'max_raw_target_deviation_deg':float(np.degrees(abs(q-q0).max())),
            'trace':trace,'contacts':contacts}
    finally:
        gym.destroy_sim(sim)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    paths = [SOURCE,Path(__file__).resolve(),Path(__file__).with_name('native_contacts.py'),
        Path(__file__).with_name('environment.py')]
    before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    rows = []
    for count in (1,3):
        for wide in (False,True):
            path = args.out/('hip_'+str(count)+('_wide' if wide else '_authored')+'.xml')
            path.write_text(fixture_xml(count,wide))
            for x in (0,-np.pi/2):
                for drive in ('position','off','effort'):
                    result = run_case(path,count,x,drive)
                    result.update({'dof_count':count,'wide_limits':wide,'initial_x_deg':float(np.degrees(x)),
                        'fixture_xml_path':str(path.resolve()),'fixture_xml_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                        'source_sha256':before})
                    case_id = path.stem+('_zero_' if x==0 else '_minus90_')+drive
                    (args.out/(case_id+'.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
                    rows.append(result)
                    print(json.dumps({k:result[k] for k in ('drive','dof_count','wide_limits','initial_x_deg','max_raw_target_deviation_deg','native_joint_types')}),flush=True)
    after = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    if before!=after:
        raise AssertionError('probe source changed during run')
    report = {'scope':'isolated hip diagnostic fixtures, not main humanoid or guitar stability',
        'physics_steps':24,'physics_hz':240,'source_sha256':before,
        'runtime_sources_unchanged':True,'rows':rows}
    (args.out/'report.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    main()
