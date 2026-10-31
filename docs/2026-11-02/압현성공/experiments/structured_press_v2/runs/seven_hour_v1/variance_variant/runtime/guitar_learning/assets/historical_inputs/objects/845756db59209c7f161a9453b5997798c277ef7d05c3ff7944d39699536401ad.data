"""Compare bounded Y/Z guitar-error feedback on the recorded quiet baseline."""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import signal

ROOT=Path(__file__).resolve().parents[1]
BASELINE=ROOT/'docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/native/initial_values.json'
BASE_REPORT=BASELINE.with_name('report.json')
COMPARISON=ROOT/'docs/2026-10-12/stability_adapter_2/results/quiet_wrist_z_support_authority_v1/comparison_v2.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--trial',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--inputs',type=Path,required=True);parser.add_argument('--condition',choices=('off','on'),required=True);args=parser.parse_args()
    args.out=args.out.resolve();args.trial=args.trial.resolve();args.out.mkdir(parents=True,exist_ok=False)
    input_manifest=args.inputs.resolve();hashes=read(input_manifest)
    if not all(sha(p)==h for p,h in hashes.items()):raise AssertionError('sealed runtime input changed')
    hashes[str(input_manifest)]=sha(input_manifest)
    baseline=read(BASELINE);base_report=read(BASE_REPORT);trial=read(args.trial)
    if trial!=baseline['input_trial']:raise AssertionError('quiet baseline trial must remain exact')
    if sha(args.trial)!=hashes[str(args.trial)]:raise AssertionError('trial hash mismatch')
    feedback_command={'joints':['L_Wrist_y','L_Wrist_z'],'enabled':args.condition=='on','active_after_s':2.,'end_s':5.,'angle_limit_rad':.005,'rate_limit_rad_s':.002,'kappa_rad2_s':.00242502989755426,'response_path':str(COMPARISON),'response_sha256':sha(COMPARISON)}
    motion={'joint':'L_Wrist_x','amplitude_rad':.005,'frequency_hz':1.,'start_s':0.,'duration_s':5.}
    save(args.out/'attempt.json',{'trial_path':str(args.trial),'trial':trial,'input_sha256':hashes,'motion_command':motion,'guitar_feedback_command':feedback_command,'requested_simulation_s':5.,'requested_physics_steps':1200,'renderer':'Isaac Gym native camera + actual strap-route overlay'})
    from .capture_isaac_gym_initial import CameraEnvironment
    from .strap_trial_recording import StrapTrialRecording
    from .run_joint_hold import native_state,snapshot
    from .palm_side_feedback import context
    from .palm_normal_task import prepare,error_from_state
    from .environment import np
    from .build_fixed_lower_asset import LOWER_BODIES,pose
    from .native_contacts import body_names,read_contacts
    from .trial_settings import validate_settings
    from scipy.spatial.transform import Rotation
    from .warmstart_targets import compose,submit
    from .wrist_yz_guitar_feedback import update,JOINTS
    comparison=read(COMPARISON)
    if not all(comparison['checks'].values()) or comparison['columns']!=list(JOINTS) or comparison['row_units']!=['m/rad']*3+['rad/rad']*3:raise AssertionError('sealed world Y/Z response required')
    response=np.array(comparison['response_matrix_world_6x2'],dtype=np.float64);corrections=np.zeros(2)
    settings=validate_settings(trial['initial_settings'],require_length=True);shift=np.array(trial['guitar_initial_translation_m'],dtype=float)
    if shift.shape!=(3,) or not np.isfinite(shift).all():raise ValueError('finite xyz creation translation required')
    if any(type(trial[n]) not in (int,float) or not 0<trial[n]<=2 for n in ('left_arm_kp_scale','left_arm_kd_scale')):raise ValueError('PD scale must be positive and at most 2')
    if not isinstance(trial['main_target_offsets_rad'],dict):raise ValueError('named main target offsets required')
    ctx=prepare(context());proxy=np.array(read(ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_neck_side_v1/initial_audit_v2/audit.json')['palmar_normal_proxy_local'])
    env=None;recorder=None;failure=None;videos={};violations=[];prefix={n:[] for n in ('states','trace','tasks','contacts','controls')};checks={};last_state=None;initialization_attempted=False
    previous_term=signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
    try:
        initialization_attempted=True;env=CameraEnvironment(settings,shift)
        if env.config['physics_hz']!=240 or env.config['control_hz']!=60:raise AssertionError('240Hz physics and 60Hz control required')
        wrist=env.names.index(motion['joint']);support=np.array([env.names.index(n) for n in JOINTS]);other79=np.setdiff1d(np.arange(len(env.names)),support)
        left=np.array([env.names.index(n) for n in baseline['left33_names']]);other=np.setdiff1d(np.arange(len(env.names)),left)
        offsets=np.zeros(66,dtype=np.float64)
        allowed={env.names[i]:k for k,i in enumerate(env.main_indices)}
        for name,value in trial['main_target_offsets_rad'].items():
            if name not in allowed or type(value) not in (float,int) or not np.isfinite(value) or abs(value)>.3:raise ValueError('main offsets must be named finite +/-0.3rad targets')
            offsets[allowed[name]]=value
        state0=native_state(env);target0=env.target.copy();before=env.gym.get_actor_dof_properties(env.env,env.human).copy();expected=before.copy()
        if trial['left_arm_kp_scale']!=1 or trial['left_arm_kd_scale']!=1:raise AssertionError('unchanged arm gains required')
        torso=env.torso_indices
        if [env.names[i] for i in torso]!=[body+'_'+axis for body in ('Torso','Spine','Chest') for axis in 'xyz']:raise AssertionError('exact body9 indices required')
        expected['stiffness'][torso]*=2.;expected['damping'][torso]*=np.sqrt(2.)
        unchanged=np.setdiff1d(np.arange(len(env.names)),torso)
        if not np.array_equal(expected[unchanged],before[unchanged]):raise AssertionError('nonbody9 PD changed')
        if not env.gym.set_actor_dof_properties(env.env,env.human,expected):raise RuntimeError('PD setter failed')
        props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        checks={'PD_readback_exact':bool(np.array_equal(props,expected)),'only_body9_PD_changed':bool(np.array_equal(props[unchanged],before[unchanged])),'PD_setter_preserves_state_and_Python_target':native_state(env)==state0 and bool(np.array_equal(target0,env.target)),'commands_preserve_states':True,'torso_other_targets_held':True,'root_lower_exact':True,'queries_preserve_states':True,'only_two_support_targets_differ_from_baseline_motion':True}
        if not all(checks.values()):raise AssertionError(checks)
        initial={'motion_command':motion,'input_trial':trial,'effective_initial_settings':env.initial_settings,'human_joint_names':env.names,'human_body_names':env.human_bodies,'main_control_joint_names':[env.names[i] for i in env.main_indices],'actual_initial_angles_rad':{n:float(d['pos']) for n,d in zip(env.names,state0['human_dof_states'])},
            'initial_PD_target_rad':env.target.astype(float).tolist(),'native_initial_state':state0,'guitar_goal_position_W_m':env.goal_position.tolist(),'guitar_goal_quaternion_xyzw':env.goal_quaternion.tolist(),
            'absolute_strap_rest_length_m':env.rest_length,'initial_route_length_m':env.initial_route_length,'PD_properties':{n:props[n].astype(int if n=='driveMode' else float).tolist() for n in props.dtype.names},
            'physics_parameters':env.physics_parameters,'input_sha256':hashes,'scope':'native t0 after one initialization; startup offsets applied before first integration; no later state/pose writes'}
        initial['body9_gain_change']={'names':[env.names[i] for i in torso],'kp_scale':2.,'kd_scale':float(np.sqrt(2.)),'before_PD_properties':{n:before[n].astype(int if n=='driveMode' else float).tolist() for n in before.dtype.names}};initial['strap_law_parameters']=env.config['strap'];initial['warmstart_alpha']=baseline['warmstart_alpha'];initial['preserved_absolute_targets_rad']=baseline['preserved_absolute_targets_rad'];initial['left33_names']=baseline['left33_names'];initial['guitar_feedback_command']=feedback_command
        save(args.out/'initial_values.json',initial);recorder=StrapTrialRecording(env,args.out);names=body_names(env.gym,env.env);record={}
        with ExitStack() as stack:
            writers={n:stack.enter_context((args.out/(n+'.jsonl')).open('w')) for n in prefix}
            def append(name,value):
                writers[name].write(json.dumps(value,allow_nan=False)+'\n');writers[name].flush()
                if len(prefix[name])<(25 if name in ('states','trace','tasks') else 24):prefix[name].append(value)
            def observe():
                nonlocal last_state
                state=native_state(env);trace=snapshot(env);task=error_from_state(state,ctx).tolist();last_state=state
                if not trace['finite'] or not np.isfinite(task).all():raise RuntimeError('nonfinite physics observation')
                for n in ('Pelvis',)+LOWER_BODIES:
                    i=env.human_bodies.index(n);checks['root_lower_exact'] &= state['human_body_states'][i]==state0['human_body_states'][i]
                if not checks['root_lower_exact']:raise AssertionError('fixed root/lower changed')
                palm_q=pose(state['human_body_states'][ctx['palm_index']])[1];up=float(Rotation.from_quat(palm_q).apply(proxy)[2])
                if up<=0:violations.append({'physics_step':env.steps,'constraint':'source_palm_up_proxy_upper_hemisphere','value':up})
                append('states',state);append('trace',trace);append('tasks',task)
                return task
            task=observe();recorder.capture()
            from .run_source_hand_initial import audit_initial
            admission=audit_initial(env,{}, {})
            q=np.array([d['pos'] for d in state0['human_dof_states']]);q0=np.array([d['pos'] for d in baseline['native_initial_state']['human_dof_states']])
            admission['checks']['all_actual_initial_q_candidate_exact_native_bounds']=bool(np.array_equal(q,q0) and np.all(q>=props['lower']) and np.all(q<=props['upper']))
            admission['checks']['actual_q_matches_initial_PD_target']=bool(np.array_equal(q,env.target.astype(float)))
            admission['checks']['declared_absolute_LA_exact']=env.rest_length==baseline['absolute_strap_rest_length_m']
            save(args.out/'initial_grip_audit.json',admission)
            checks['direct_native_source_gate']=all(admission['checks'].values())
            if not checks['direct_native_source_gate']:raise AssertionError('fresh direct native source gate rejected; t0 partial video saved')
            for step in range(1200):
                updated=step%4==0
                if updated:
                    before_state=native_state(env)
                    base=compose(env.initial_q,env.main_indices,offsets,env.lower,env.upper)
                    if not np.array_equal(base,np.array(baseline['preserved_absolute_targets_rad'],dtype=np.float32)):raise AssertionError('baseline PD targets changed')
                    command_time=step/240.;delta=motion['amplitude_rad']*np.sin(2*np.pi*motion['frequency_hz']*command_time)
                    moving_offsets=offsets.copy();moving_offsets[allowed[motion['joint']]]+=delta
                    unperturbed=compose(env.initial_q,env.main_indices,moving_offsets,env.lower,env.upper)
                    gp,gq=pose(before_state['guitar_body_states'][0])
                    corrections,feedback_record=update(response,env.goal_position,env.goal_quaternion,gp,gq,corrections,args.condition=='on',command_time)
                    for name,value in zip(JOINTS,corrections):moving_offsets[allowed[name]]+=value
                    submitted=compose(env.initial_q,env.main_indices,moving_offsets,env.lower,env.upper)
                    checks['only_two_support_targets_differ_from_baseline_motion'] &= bool(np.array_equal(submitted[other79],unperturbed[other79]))
                    if not checks['only_two_support_targets_differ_from_baseline_motion']:raise AssertionError('other79 baseline target changed')
                    submit(env,moving_offsets);checks['commands_preserve_states'] &= native_state(env)==before_state
                    if not np.array_equal(env.target,submitted):raise AssertionError('target mirror mismatch')
                    record={'command_time_s':command_time,'wrist_motion_delta_rad':float(delta),'feedback':feedback_record,
                        'wrist_actual_at_update_rad':float(before_state['human_dof_states'][wrist]['pos']),
                        'support_actual_at_update_rad':[float(before_state['human_dof_states'][i]['pos']) for i in support],
                        'task_error_m_scaled_rad':task,'other48_targets_held':bool(np.array_equal(env.target[other],env.initial_q[other]))}
                checks['torso_other_targets_held'] &= bool(np.array_equal(env.target[other],env.initial_q[other]))
                append('controls',dict(record,updated_before_step=updated,physics_step=step+1,final_target_rad=env.target.astype(float).tolist()))
                env.step_physics();task=observe();append('contacts',{'physics_step':env.steps,'contacts':read_contacts(env.gym,env.env,names)})
                checks['queries_preserve_states'] &= native_state(env)==last_state
                if env.steps%recorder.interval==0:recorder.capture()
                if env.steps%240==0:print('recorded simulation seconds',env.steps/240,flush=True)
            checks['PD_unchanged']=bool(np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human)))
            if not all(checks.values()):raise AssertionError(checks)
    except BaseException as error:failure={'type':type(error).__name__,'message':str(error)}
    finally:
        signal.signal(signal.SIGTERM,previous_term)
        if env is not None:env.close()
        if recorder is not None:
            try:videos=recorder.encode()
            except Exception as error:
                if failure is None:failure={'type':type(error).__name__,'message':str(error)}
                else:failure['video_error']=str(error)
        checks['inputs_unchanged']=all(sha(p)==h for p,h in hashes.items())
        completed=failure is None and all(checks.values()) and env is not None and env.steps==1200 and len(recorder.frames)==151 and len(videos)==2
        save(args.out/'report.json',{'completed':completed,'failure':failure,'checks':checks,'native_initialization_attempts':int(initialization_attempted),'native_initializations':int(env is not None),'physics_steps':getattr(env,'steps',0),
            'simulation_elapsed_s':getattr(env,'steps',0)/240,'frame_count':len(recorder.frames) if recorder else 0,'constraint_violations':violations,'palm_up_proxy_passed':not violations if last_state is not None else None,
            'input_sha256':hashes,'videos':videos,'motion_command':motion,'guitar_feedback_command':feedback_command,'stability_success':None,'diagnostic_only':True,'source_support_search_passed':False,'source_support_search_reasons':base_report['source_support_search_reasons'],'finger_target_policy':base_report['finger_target_policy'],'scope':'Actual quiet baseline with body9 PD x2/sqrt2 and original wrist sinusoid; L_Wrist_y/z target correction OFF/ON from current world guitar error after2s; bounded +/-0.005rad and0.002rad/s; direct fresh native source HG/cross/self1188 and bounds gate; fixed LA/root/lower, free guitar; no actor/training/extra guitar force/pose replay; source-profile/policy transition remains unverified'})
    if not completed:raise RuntimeError(failure or checks)
    print(json.dumps({'completed':completed,'physics_steps':env.steps,'frame_count':len(recorder.frames),'constraint_violations':len(violations)}),flush=True)


if __name__=='__main__':main()
