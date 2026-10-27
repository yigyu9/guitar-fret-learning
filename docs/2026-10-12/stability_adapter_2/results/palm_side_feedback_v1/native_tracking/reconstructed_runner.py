"""Same-pose OFF/bias/tracking native trials with bounded left-arm targets."""
import argparse
import json
from pathlib import Path
from .palm_side_feedback import PHASE,SETTINGS,context,observation,task_error,input_paths,SideFeedback
from .self_collision_environment import SelfCollisionEnvironment
from .environment import np
from .build_fixed_lower_asset import read,sha,LOWER_BODIES
from .run_joint_hold import native_state,snapshot
from .native_contacts import body_names,read_contacts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('off','bias','tracking'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--steps',type=int,choices=(24,120),default=24)
    parser.add_argument('--camera',action='store_true')
    args=parser.parse_args();ctx=context();args.out.mkdir(parents=True,exist_ok=False)
    fk_path=PHASE/'fk/calibration.json';response_path=PHASE/'response/calibration.json'
    fk,response=read(fk_path),read(response_path)
    if not all(fk['checks'].values()) or not all(response['checks'].values()):raise ValueError('calibration failed')
    if fk['settings_sha256']!=sha(SETTINGS) or response['settings_sha256']!=sha(SETTINGS):raise ValueError('calibration settings changed')
    files=input_paths()+[Path(__file__).resolve(),fk_path,response_path]
    files += [Path(p) for p in read(input_paths()[6])['input_sha256']]
    files += [Path(__file__).with_name(n) for n in ('self_collision_environment.py','native_contacts.py')]
    hashes={str(p):sha(p) for p in files}
    if args.camera:
        from .probe_palm_contact_facet import PalmCameraEnvironment
        from .environment import gymapi
        from .audit_palm_side_target import side_target
        for n in ('probe_palm_contact_facet.py','capture_isaac_gym_initial.py'):hashes[str(Path(__file__).with_name(n))]=sha(Path(__file__).with_name(n))
    environment=PalmCameraEnvironment if args.camera else SelfCollisionEnvironment
    env=environment(read(SETTINGS),ctx['shift']);arm=ctx['indices'];q0=ctx['q0'][arm]
    bias=np.zeros(12) if args.mode=='off' else np.array(response['bias_rad'])
    controller=SideFeedback(fk['matrix'],q0,bias,ctx['lower'],ctx['upper'])
    states=[];trace=[];contacts=[];controls=[];tasks=[];checks={};images={}
    props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
    names=body_names(env.gym,env.env);interval=env.config['physics_hz']//env.config['control_hz']
    def save(error=None):
        report={'mode':args.mode,'checks':checks,'physics_steps':env.steps,'native_initializations':1,
            'source_sha256':hashes,'initial_settings':env.initial_settings,'human_joint_names':env.names,
            'human_body_names':env.human_bodies,'arm_names':[env.names[i] for i in arm],
            'arm_indices':arm.tolist(),'initial_q_rad':env.initial_q.astype(float).tolist(),
            'bias_rad':bias.tolist(),'lower_rad':ctx['lower'].tolist(),'upper_rad':ctx['upper'].tolist(),
            'images':images,'camera_specs':env.camera_specs if args.camera else {},
            'max_position_error_m':max((t['position_error_m'] for t in trace),default=0),
            'max_rotation_error_deg':max((t['rotation_error_deg'] for t in trace),default=0),
            'scope':'bounded target correction; no finger closure, new gain, or guitar-return feedback',
            'failure':error,'stability_success':False}
        for name,value in (('report',report),('states',states),('trace',trace),('contacts',contacts),('controls',controls),('tasks',tasks)):
            (args.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    def capture():
        before=native_state(env)
        env.gym.step_graphics(env.sim);env.gym.render_all_camera_sensors(env.sim)
        for name in env.camera_specs:
            path=args.out/(name+'_'+str(env.steps).zfill(3)+'.png')
            env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras[name],gymapi.IMAGE_COLOR,str(path))
            _,polygon,_=side_target(env)
            images[str(path)]={'sha256':sha(path),'physics_step':env.steps,'target_polygon_W_m':polygon.tolist()}
        if before!=native_state(env):raise AssertionError('render wrote states')
    try:
        states=[native_state(env)];trace=[snapshot(env)];tasks=[task_error(env,ctx).tolist()]
        checks={'initial_state_exact':states[0]==ctx['seed'],'commands_preserve_states':True,
            'nonleftarm_targets_exact':True,'target_bounds':True,'residual_cap_and_rate':True,
            'queries_preserve_states':True}
        if not checks['initial_state_exact']:raise AssertionError('initial state mismatch')
        if args.camera:capture()
        other=np.setdiff1d(np.arange(len(env.names)),arm);record={};previous=np.zeros(12)
        for step in range(args.steps):
            updated=step%interval==0
            if updated:
                before=native_state(env);error=task_error(env,ctx)
                if args.mode=='tracking':
                    target,record=controller.update(error,1/env.config['control_hz'])
                    checks['residual_cap_and_rate'] &= bool((np.abs(controller.delta)<=.15+1e-12).all() and
                        (np.abs(controller.delta-previous)<=1/env.config['control_hz']+1e-12).all())
                    previous=controller.delta.copy()
                else:target=q0+bias;record={'task_error_m_scaled_rad':error.tolist()}
                offsets=np.zeros(66,dtype=np.float32)
                for i,d in zip(arm,target-q0):offsets[list(env.main_indices).index(i)]=d
                env.set_main_offsets(offsets)
                checks['commands_preserve_states'] &= native_state(env)==before
            checks['nonleftarm_targets_exact'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            checks['target_bounds'] &= bool(((env.target[arm]>=ctx['lower']-2e-7)&(env.target[arm]<=ctx['upper']+2e-7)).all())
            controls.append(dict(record,updated_before_step=updated,physics_step=step+1,final_target_rad=env.target[arm].astype(float).tolist()))
            env.step_physics();state=native_state(env);states.append(state);trace.append(snapshot(env))
            tasks.append(task_error(env,ctx).tolist())
            contacts.append({'physics_step':env.steps,'contacts':read_contacts(env.gym,env.env,names)})
            checks['queries_preserve_states'] &= native_state(env)==state
        checks.update(root_lower_exact=all(s['human_body_states'][env.human_bodies.index(n)]==states[0]['human_body_states'][env.human_bodies.index(n)]
            for s in states for n in ('Pelvis',)+LOWER_BODIES),
            pd_unchanged=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))),
            fixed_absolute_length=all(t['strap_rest_length_m']==read(SETTINGS)['strap_rest_length_m'] for t in trace),
            finite_trace=all(t['finite'] for t in trace),inputs_unchanged=all(sha(Path(p))==h for p,h in hashes.items()))
        if args.mode=='off' and args.steps==24:
            prior=read(input_paths()[5])
            checks['off_exact_prior_prefix']=all(v==prior[k] for k,v in (('states',states),('trace',trace),('contacts',contacts)))
        if args.mode=='bias':checks['bias_exact_validated_first_step']=states[1]==read(PHASE/'response/columns.json')['rows'][-1]['after_state']
        if args.camera:
            capture()
            prefix=PHASE/'short'/args.mode
            checks['camera_exact_headless_raw']=all(value==read(prefix/(name+'.json')) for name,value in
                (('states',states),('trace',trace),('contacts',contacts),('controls',controls),('tasks',tasks)))
        save()
        if not all(checks.values()):raise AssertionError(checks)
        print(json.dumps({'mode':args.mode,'checks':checks,'last_point_error_mm':float(np.linalg.norm(tasks[-1][:3])*1000),
            'max_guitar_mm':max(t['position_error_m'] for t in trace)*1000}),flush=True)
    except Exception as error:
        save({'type':type(error).__name__,'message':str(error)})
        raise
    finally:env.close()


if __name__=='__main__':main()
