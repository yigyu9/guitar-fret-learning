"""Fresh native facet placement, contact trace and actual Gym camera frames."""
import argparse
import json
from pathlib import Path

from .capture_isaac_gym_initial import CameraEnvironment
from .audit_palm_side_target import PHASE,BASE,side_target,closest_polygon
from .finger_grip_probe import SUPPORT_PHASE
from .environment import np,gymapi,quaternion
from .build_fixed_lower_asset import read,sha,pose,LOWER_BODIES
from .run_joint_hold import native_state,snapshot
from .initial_overlap import build_probe
from .palm_side_source_checks import source_checks
from .native_contacts import body_names,read_contacts
from .search_palm_neck_side import REFERENCE
from scipy.spatial.transform import Rotation


class PalmCameraEnvironment(CameraEnvironment):
    def _create_scene(self):
        super()._create_scene()
        _,polygon,_=side_target(self)
        target=polygon.mean(0)
        body=self.bodies(self.guitar)[0]['pose']
        rotation=Rotation.from_quat(quaternion(body['r']))
        self.camera_specs={}
        for name,direction in (('blue_front',(.9,-.35,1.5)),('blue_side',(1.2,-.15,-.1))):
            direction=np.array(direction);direction/=np.linalg.norm(direction)
            eye=target+rotation.apply(direction)*.30
            props=gymapi.CameraProperties()
            props.width,props.height,props.horizontal_fov=1280,720,45
            handle=self.gym.create_camera_sensor(self.env,props)
            if handle<0:raise RuntimeError('palm camera creation failed')
            self.gym.set_camera_location(handle,self.env,gymapi.Vec3(*eye),gymapi.Vec3(*target))
            self.cameras[name]=handle
            self.camera_specs[name]={'eye':eye.tolist(),'target':target.tolist(),
                'width':1280,'height':720,'horizontal_fov_deg':45}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--search',type=Path)
    mode.add_argument('--baseline',action='store_true')
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--steps',type=int,choices=(0,1,24),default=0)
    args=parser.parse_args()
    if args.baseline and args.steps:raise ValueError('baseline capture uses zero steps')
    initial_path=PHASE/'initial_audit_v2/audit.json';initial=read(initial_path)
    reference=read(REFERENCE/'report.json')
    if args.baseline:
        candidate=None;settings=BASE;predicted=initial['initial_state']
    else:
        search=read(args.search)
        selected=[r for r in search['rows'] if r['accepted_for_fresh_native']]
        if not selected:raise ValueError('no accepted source candidate')
        candidate=selected[0];settings=Path(candidate['settings_path']);predicted=candidate['source_state']
        if sha(settings)!=candidate['settings_sha256']:raise ValueError('settings changed')
        if not all(sha(Path(p))==h for p,h in search['input_sha256'].items()):raise ValueError('search inputs changed')
    shift_path=SUPPORT_PHASE/'search_near_touch.json'
    files=[Path(__file__).resolve(),settings,initial_path,shift_path]
    files += [Path(p) for p in initial['input_sha256']]
    files += [Path(__file__).with_name(n) for n in ('capture_isaac_gym_initial.py','palm_side_source_checks.py',
        'face_referenced_geometry.py','native_contacts.py','self_collision_environment.py')]
    if args.search:files += [args.search]+[Path(p) for p in search['input_sha256']]
    hashes={str(p):sha(p) for p in files}
    args.out.mkdir(parents=True,exist_ok=False)
    env=PalmCameraEnvironment(read(settings),read(shift_path)['guitar_initial_translation_m'])
    states=[];trace=[];contacts=[];images={};checks={}
    def save():
        (args.out/'probe.json').write_text(json.dumps({'name':'baseline' if candidate is None else candidate['name'],
            'checks':checks,'native_initializations':1,'physics_steps':env.steps,
            'states':states,'trace':trace,'contacts':contacts,'images':images,'camera_specs':env.camera_specs,
            'input_sha256':hashes,'scope':'actual Gym camera and native contact diagnostic; source clear is not cooked certification'},
            indent=2,allow_nan=False)+'\n')
    def capture():
        before=native_state(env)
        env.gym.step_graphics(env.sim);env.gym.render_all_camera_sensors(env.sim)
        for name in env.camera_specs:
            path=args.out/(name+'_'+str(env.steps).zfill(3)+'.png')
            env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras[name],gymapi.IMAGE_COLOR,str(path))
            _,polygon,_=side_target(env)
            images[str(path)]={'sha256':sha(path),'physics_step':env.steps,'target_polygon_W_m':polygon.tolist()}
        if before!=native_state(env):raise AssertionError('render changed native states')
    try:
        state=native_state(env);states.append(state);trace.append(snapshot(env))
        position_errors=[];rotation_errors=[]
        for actual,expected in zip(state['human_body_states'],predicted['human_body_states']):
            p,r=pose(actual);pp,rr=pose(expected)
            position_errors.append(np.linalg.norm(p-pp))
            rotation_errors.append(np.linalg.norm((Rotation.from_quat(r)*Rotation.from_quat(rr).inv()).as_rotvec()))
        props=env.gym.get_actor_dof_properties(env.env,env.human)
        arm=set(reference['arm_indices'][:12]);base=initial['initial_state']
        checks.update({'fk_position_match':bool(max(position_errors)<1e-6),
            'fk_rotation_match':bool(max(rotation_errors)<1e-5),
            'nonleftarm_q_exact':all(d==base['human_dof_states'][i] for i,d in enumerate(state['human_dof_states']) if i not in arm),
            'guitar_initial_exact':state['guitar_body_states']==base['guitar_body_states'],
            'pd_exact':all(props[k].astype(float).tolist()==reference[r] for k,r in
                (('stiffness','native_pd_kp'),('damping','native_pd_kd'),('effort','native_effort_caps_nm'),('driveMode','native_drive_modes'))),
            'absolute_length_exact':env.rest_length==initial['absolute_rest_length_m']})
        probe=build_probe(env);meshes,overlaps,crosshands=source_checks(probe)
        palm=next(s for s in probe[2] if s['body']=='LH:palm');_,polygon,_=side_target(env)
        (args.out/'initial_geometry.json').write_text(json.dumps({'overlaps':overlaps,'crosshands':crosshands,
            'palm_to_blue':closest_polygon(meshes[palm['geom_id']],polygon),
            'max_fk_position_error_m':float(max(position_errors)),'max_fk_rotation_error_rad':float(max(rotation_errors)),
            'initial_route_length_m':env.initial_route_length,'absolute_rest_length_m':env.rest_length},indent=2)+'\n')
        checks['queries_preserve_states']=state==native_state(env)
        if candidate is not None:checks['fresh_source_clear']=not overlaps and not crosshands
        if not all(checks.values()):raise AssertionError(checks)
        capture();names=body_names(env.gym,env.env)
        for _ in range(args.steps):
            env.step_physics();states.append(native_state(env));trace.append(snapshot(env))
            contacts.append({'physics_step':env.steps,'contacts':read_contacts(env.gym,env.env,names)})
        if args.steps:capture()
        checks['root_lower_exact']=all(s['human_body_states'][env.human_bodies.index(n)]==state['human_body_states'][env.human_bodies.index(n)]
            for s in states for n in ('Pelvis',)+LOWER_BODIES)
        checks['inputs_unchanged']=all(sha(Path(p))==h for p,h in hashes.items())
        save()
        if not all(checks.values()):raise AssertionError(checks)
        print(json.dumps({'checks':checks,'physics_steps':env.steps,'last_trace':trace[-1]}),flush=True)
    except Exception as error:
        save()
        (args.out/'failure.json').write_text(json.dumps({'type':type(error).__name__,'message':str(error),
            'native_initializations':1,'physics_steps':env.steps},indent=2)+'\n')
        raise
    finally:env.close()


if __name__=='__main__':main()
