"""Bounded full-relative versus normal-only palm target control in native Gym."""
import argparse
import json
from pathlib import Path
from .palm_side_feedback import PHASE as PREVIOUS,SETTINGS,context,task_error,SideFeedback,np
from .palm_normal_task import prepare,error_from_state
from .self_collision_environment import SelfCollisionEnvironment
from .build_fixed_lower_asset import read,sha,LOWER_BODIES,pose
from .run_joint_hold import native_state,snapshot
from .native_contacts import body_names,read_contacts
from scipy.spatial.transform import Rotation

PHASE=PREVIOUS.parent/'palm_normal_control_v1'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=('bias','full','normal'),required=True)
    parser.add_argument('--steps',type=int,choices=(1,24),required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--camera',action='store_true')
    parser.add_argument('--calibration',type=Path,default=PHASE/'calibration/calibration.json')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False);ctx=prepare(context())
    calibration_path=args.calibration.resolve();calibration=read(calibration_path)
    cap=calibration.get('runtime_cap_rad',.15)
    if cap!=.15:
        if args.mode=='full':raise ValueError('full baseline uses original box')
        ctx['lower']=np.array(calibration['lower_rad']);ctx['upper']=np.array(calibration['upper_rad'])
    if not all(calibration['checks'].values()):raise ValueError('normal calibration failed')
    files=[Path(p) for p in calibration['input_sha256']]
    if any(sha(p)!=calibration['input_sha256'][str(p)] for p in files):raise ValueError('calibration inputs changed')
    files += [Path(__file__).resolve(),calibration_path]
    files += [PREVIOUS/'short/tracking'/f for f in ('report.json','states.json','trace.json','contacts.json','controls.json','tasks.json')]
    if args.camera:
        from .probe_palm_contact_facet import PalmCameraEnvironment
        from .environment import gymapi
        from .audit_palm_side_target import side_target
        files += [Path(__file__).with_name(n) for n in ('probe_palm_contact_facet.py','capture_isaac_gym_initial.py')]
    hashes={str(p):sha(p) for p in files}
    env=(PalmCameraEnvironment if args.camera else SelfCollisionEnvironment)(read(SETTINGS),ctx['shift'])
    arm=ctx['indices'];q0=ctx['q0'][arm];other=np.setdiff1d(np.arange(len(env.names)),arm)
    bias=np.array(read(PREVIOUS/'response/calibration.json')['bias_rad'] if args.mode=='full' else calibration['response']['bias_rad'])
    matrix=read(PREVIOUS/'fk/calibration.json')['matrix'] if args.mode=='full' else calibration['fk']['matrix']
    controller=SideFeedback(matrix,q0,bias,ctx['lower'],ctx['upper'])
    props=env.gym.get_actor_dof_properties(env.env,env.human).copy();names=body_names(env.gym,env.env)
    proxy=np.array(read(PREVIOUS.parent/'palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    states=[];trace=[];tasks=[];normal_tasks=[];contacts=[];controls=[];images={};checks={}
    def save(failure=None):
        up=[float(Rotation.from_quat(pose(s['human_body_states'][ctx['palm_index']])[1]).apply(proxy)[2]) for s in states]
        report={'mode':args.mode,'native_initializations':1,'physics_steps':env.steps,'checks':checks,'failure':failure,
            'source_sha256':hashes,'initial_settings':env.initial_settings,'human_body_names':env.human_bodies,
            'human_joint_names':env.names,'arm_indices':arm.tolist(),'bias_rad':bias.tolist(),
            'lower_rad':ctx['lower'].tolist(),'upper_rad':ctx['upper'].tolist(),'runtime_cap_rad':cap,
            'max_position_error_m':max((t['position_error_m'] for t in trace),default=0),
            'max_rotation_error_deg':max((t['rotation_error_deg'] for t in trace),default=0),
            'minimum_source_palm_up_proxy_z':min(up,default=None),'images':images,
            'camera_specs':env.camera_specs if args.camera else {},'stability_success':False,
            'scope':'normal orientation versus full-relative task, followed by separate runtime box comparison; initial/gains/gap/strap/fingers unchanged; proxy not anatomical certification'}
        if args.mode=='bias' and normal_tasks:
            delta=env.target[arm].astype(float)-q0
            report['predicted_normal_first_error_m_scaled_rad']=(np.array(calibration['response']['baseline_error_m_scaled_rad'])-np.array(calibration['response']['matrix'])@delta).tolist()
            report['actual_normal_first_error_m_scaled_rad']=normal_tasks[min(1,len(normal_tasks)-1)]
        for name,value in (('report',report),('states',states),('trace',trace),('contacts',contacts),('controls',controls),('tasks',tasks),('normal_tasks',normal_tasks)):
            (args.out/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    def capture():
        before=native_state(env);env.gym.step_graphics(env.sim);env.gym.render_all_camera_sensors(env.sim)
        for name in env.camera_specs:
            path=args.out/(name+'_'+str(env.steps).zfill(3)+'.png')
            env.gym.write_camera_image_to_file(env.sim,env.env,env.cameras[name],gymapi.IMAGE_COLOR,str(path))
            _,polygon,_=side_target(env)
            images[str(path)]={'sha256':sha(path),'physics_step':env.steps,'target_polygon_W_m':polygon.tolist()}
        if before!=native_state(env):raise AssertionError('render wrote states')
    try:
        state=native_state(env);states=[state];trace=[snapshot(env)];normal_tasks=[error_from_state(state,ctx).tolist()]
        tasks=[task_error(env,ctx).tolist() if args.mode=='full' else normal_tasks[-1]]
        checks={'initial_state_exact':state==ctx['seed'],'commands_preserve_states':True,
            'nonleftarm_targets_exact':True,'target_bounds':True,'residual_cap_and_rate':True,'queries_preserve_states':True}
        if not checks['initial_state_exact']:raise AssertionError('initial state mismatch')
        if args.camera:capture()
        previous=np.zeros(12);record={};interval=env.config['physics_hz']//env.config['control_hz']
        for step in range(args.steps):
            updated=step%interval==0
            if updated:
                before=native_state(env);error=task_error(env,ctx) if args.mode=='full' else error_from_state(before,ctx)
                if args.mode=='bias':target=q0+bias;record={'task_error_m_scaled_rad':error.tolist()}
                else:
                    target,record=controller.update(error,1/env.config['control_hz'])
                    checks['residual_cap_and_rate'] &= bool((np.abs(controller.delta)<=.15+1e-12).all() and
                        (np.abs(controller.delta-previous)<=1/env.config['control_hz']+1e-12).all())
                    previous=controller.delta.copy()
                offsets=np.zeros(66,dtype=np.float32)
                for i,d in zip(arm,target-q0):offsets[list(env.main_indices).index(i)]=d
                env.set_main_offsets(offsets);checks['commands_preserve_states'] &= native_state(env)==before
            checks['nonleftarm_targets_exact'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
            checks['target_bounds'] &= bool(((env.target[arm]>=ctx['lower']-2e-7)&(env.target[arm]<=ctx['upper']+2e-7)).all())
            controls.append(dict(record,updated_before_step=updated,physics_step=step+1,final_target_rad=env.target[arm].astype(float).tolist()))
            env.step_physics();state=native_state(env);states.append(state);trace.append(snapshot(env))
            normal_tasks.append(error_from_state(state,ctx).tolist())
            tasks.append(task_error(env,ctx).tolist() if args.mode=='full' else normal_tasks[-1])
            contacts.append({'physics_step':env.steps,'contacts':read_contacts(env.gym,env.env,names)})
            checks['queries_preserve_states'] &= native_state(env)==state
        checks.update(root_lower_exact=all(s['human_body_states'][env.human_bodies.index(n)]==states[0]['human_body_states'][env.human_bodies.index(n)]
                for s in states for n in ('Pelvis',)+LOWER_BODIES),
            pd_unchanged=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))),
            fixed_absolute_length=all(t['strap_rest_length_m']==read(SETTINGS)['strap_rest_length_m'] for t in trace),
            finite_trace=all(t['finite'] for t in trace),inputs_unchanged=all(sha(Path(p))==h for p,h in hashes.items()))
        if args.mode=='full' and args.steps==24:
            checks['full_exact_prior_tracking']=all(value==read(PREVIOUS/'short/tracking'/(name+'.json')) for name,value in
                (('states',states),('trace',trace),('contacts',contacts),('controls',controls),('tasks',tasks)))
        if args.camera:
            capture();prefix=PHASE/'short'/args.mode
            checks['camera_exact_headless_raw']=all(value==read(prefix/(name+'.json')) for name,value in
                (('states',states),('trace',trace),('contacts',contacts),('controls',controls),('tasks',tasks),('normal_tasks',normal_tasks)))
        save()
        if not all(checks.values()):raise AssertionError(checks)
        print(json.dumps({'mode':args.mode,'checks':checks,'max_guitar_mm':max(t['position_error_m'] for t in trace)*1000}),flush=True)
    except Exception as error:
        save({'type':type(error).__name__,'message':str(error)});raise
    finally:env.close()


if __name__=='__main__':main()
