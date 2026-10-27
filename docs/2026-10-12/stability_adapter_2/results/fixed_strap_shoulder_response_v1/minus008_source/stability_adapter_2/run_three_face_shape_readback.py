"""Repeat a recorded grip with read-only native shape properties and actual 5s video."""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import signal

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_hold_pd_v2/analysis.json'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def read_native_shapes(env):
    fields=('compliance','contact_offset','filter','friction','rest_offset',
            'restitution','rolling_friction','thickness','torsion_friction')
    actors={}
    for label,actor in (('human',env.human),('guitar',env.guitar)):
        names=list(env.gym.get_actor_rigid_body_names(env.env,actor))
        ranges=env.gym.get_actor_rigid_body_shape_indices(env.env,actor)
        props=env.gym.get_actor_rigid_shape_properties(env.env,actor)
        count=env.gym.get_actor_rigid_shape_count(env.env,actor)
        if len(ranges)!=len(names) or len(props)!=count:
            raise AssertionError('native body/shape property dimensions')
        mapping=[];indices=[]
        for name,r in zip(names,ranges):
            ids=list(range(r.start,r.start+r.count))
            if any(i<0 or i>=count for i in ids):
                raise AssertionError('native body shape range out of bounds')
            indices.extend(ids);mapping.append({'body':name,'start':r.start,'count':r.count,'shape_indices':ids})
        if sorted(indices)!=list(range(count)):
            raise AssertionError('native shape mapping must cover each shape once')
        actors[label]={'shape_count':count,'body_ranges':mapping,'shape_properties':[
            {n:int(getattr(p,n)) if n=='filter' else float(getattr(p,n)) for n in fields} for p in props]}
    return actors


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--trial',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--proposal',type=Path,default=ROOT/'docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/proposal.json');args=parser.parse_args()
    args.out=args.out.resolve();args.trial=args.trial.resolve();args.out.mkdir(parents=True,exist_ok=False)
    hashes={str(SOURCE):sha(SOURCE),str(args.trial):sha(args.trial)};source=read(SOURCE);trial=read(args.trial)
    fields={'initial_settings','guitar_initial_translation_m','main_target_offsets_rad','left_arm_kp_scale','left_arm_kd_scale'}
    if set(trial)!=fields:raise ValueError('explicit initial settings, guitar translation, named offsets and left-arm PD scales required')
    paths=[ROOT/'stability_adapter_2/THREE_FACE_SUPPORT_LOSS_DIAGNOSTIC_PLAN.md',ROOT/'isaacgym/docs/api/python/gym_py.html',ROOT/'isaacgym/docs/api/python/struct_py.html',ROOT/'stability_adapter_2/run_seed2_support_warmstart.py']+[Path(p) for p in source['input_sha256']]+[Path(__file__).resolve()]+[Path(__file__).with_name(n) for n in ('gym_trial_recording.py','capture_isaac_gym_initial.py','FIVE_SECOND_RECORDING_PLAN.md')]
    hashes.update({str(p.resolve()):sha(p) for p in paths})
    if not all(source['checks'].values()) or any(sha(p)!=h for p,h in source['input_sha256'].items()):raise AssertionError('source closure changed')
    grip_path=args.proposal.resolve()
    hashes[str(grip_path)]=sha(grip_path);grip=read(grip_path)
    hashes.update({p:sha(p) for p in grip['input_sha256']})
    hashes.update({str(Path(__file__).with_name(n)):sha(Path(__file__).with_name(n)) for n in ('multi_face_grip_audit.py','search_multi_face_grip.py','prepare_three_face_same_target_trials.py','warmstart_targets.py','SEED2_SUPPORT_POSE_WARMSTART_PLAN.md','SEED2_SUPPORT_WARMSTART_EXECUTION.md','THREE_FACE_INITIAL_SAME_TARGET_PLAN.md')})
    if not all(grip['checks'].values()) or any(sha(p)!=h for p,h in grip['input_sha256'].items()):raise AssertionError('local grip proposal inputs changed')
    grip_row=next((r for r in grip['rows'] if Path(r['trial_path']).resolve()==args.trial),None)
    if grip_row is None:raise ValueError('trial is not a declared local grip candidate')
    if not grip_row['accepted_for_fresh_native'] or sha(args.trial)!=grip_row['trial_sha256']:raise AssertionError('local grip did not pass source admission')
    if set(trial['main_target_offsets_rad'])!=set(grip['left33_names']):raise AssertionError('left33 offsets required')
    save(args.out/'attempt.json',{'trial_path':str(args.trial),'trial':trial,'input_sha256':hashes,'requested_simulation_s':5.,'requested_physics_steps':1200,'renderer':'Isaac Gym native camera'})
    from .capture_isaac_gym_initial import CameraEnvironment
    from .gym_trial_recording import GymTrialRecording
    from .run_joint_hold import native_state,snapshot
    from .palm_side_feedback import context
    from .palm_normal_task import prepare,error_from_state
    from .environment import np
    from .build_fixed_lower_asset import LOWER_BODIES,pose
    from .native_contacts import body_names,read_contacts
    from .trial_settings import validate_settings
    from scipy.spatial.transform import Rotation
    from .warmstart_targets import compose,submit
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
        arm=ctx['indices'];left=np.array([env.names.index(n) for n in grip['left33_names']]);other=np.setdiff1d(np.arange(len(env.names)),left)
        offsets=np.zeros(66,dtype=np.float64)
        allowed={env.names[i]:k for k,i in enumerate(env.main_indices)}
        for name,value in trial['main_target_offsets_rad'].items():
            if name not in allowed or type(value) not in (float,int) or not np.isfinite(value) or abs(value)>.3:raise ValueError('main offsets must be named finite +/-0.3rad targets')
            offsets[allowed[name]]=value
        state0=native_state(env);target0=env.target.copy();before=env.gym.get_actor_dof_properties(env.env,env.human).copy();expected=before.copy()
        expected['stiffness'][arm]*=trial['left_arm_kp_scale'];expected['damping'][arm]*=trial['left_arm_kd_scale']
        if not env.gym.set_actor_dof_properties(env.env,env.human,expected):raise RuntimeError('PD setter failed')
        props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        checks={'PD_readback_exact':bool(np.array_equal(props,expected)),'PD_setter_preserves_state_and_Python_target':native_state(env)==state0 and bool(np.array_equal(target0,env.target)),'commands_preserve_states':True,'torso_other_targets_held':True,'root_lower_exact':True,'queries_preserve_states':True}
        if not all(checks.values()):raise AssertionError(checks)
        initial={'input_trial':trial,'effective_initial_settings':env.initial_settings,'human_joint_names':env.names,'human_body_names':env.human_bodies,'main_control_joint_names':[env.names[i] for i in env.main_indices],'actual_initial_angles_rad':{n:float(d['pos']) for n,d in zip(env.names,state0['human_dof_states'])},
            'initial_PD_target_rad':env.target.astype(float).tolist(),'native_initial_state':state0,'guitar_goal_position_W_m':env.goal_position.tolist(),'guitar_goal_quaternion_xyzw':env.goal_quaternion.tolist(),
            'absolute_strap_rest_length_m':env.rest_length,'initial_route_length_m':env.initial_route_length,'PD_properties':{n:props[n].astype(int if n=='driveMode' else float).tolist() for n in props.dtype.names},
            'physics_parameters':env.physics_parameters,'input_sha256':hashes,'scope':'native t0 after one initialization; startup offsets applied before first integration; no later state/pose writes'}
        initial['strap_law_parameters']=env.config['strap'];initial['warmstart_alpha']=grip_row['alpha'];initial['preserved_absolute_targets_rad']=grip_row['expected_absolute_targets_rad'];initial['left33_names']=grip['left33_names']
        save(args.out/'initial_values.json',initial);recorder=GymTrialRecording(env,args.out);names=body_names(env.gym,env.env);record={}
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
            before_shape_state=native_state(env);before_shape_target=env.target.copy();before_shape_PD=env.gym.get_actor_dof_properties(env.env,env.human).copy()
            shape_readback=read_native_shapes(env)
            checks['native_shape_queries_preserve_state_target_and_PD']=native_state(env)==before_shape_state and bool(np.array_equal(env.target,before_shape_target)) and bool(np.array_equal(env.gym.get_actor_dof_properties(env.env,env.human),before_shape_PD))
            save(args.out/'shape_properties.json',{'physics_step':env.steps,'actors':shape_readback,'queries_preserve_state_target_and_PD':checks['native_shape_queries_preserve_state_target_and_PD'],'scope':'SDK rigid shape material/readback and body ranges only; no cooked mesh/face-contact certification; all nine SDK fields retained'})
            if not checks['native_shape_queries_preserve_state_target_and_PD']:raise AssertionError('shape query changed state/target/PD')
            from .multi_face_grip_audit import audit_initial
            admission=audit_initial(env,grip,grip_row)
            q=np.array([d['pos'] for d in state0['human_dof_states']]);q0=np.array(grip_row['expected_initial_angles_rad'])
            admission['checks']['all_actual_initial_q_candidate_exact_native_bounds']=bool(np.array_equal(q,q0) and np.all(q>=props['lower']) and np.all(q<=props['upper']))
            admission['checks']['actual_q_matches_initial_PD_target']=bool(np.array_equal(q,env.target.astype(float)))
            admission['checks']['declared_absolute_LA_exact']=env.rest_length==grip_row['absolute_strap_rest_length_m']
            save(args.out/'initial_grip_audit.json',admission)
            checks['initial_grip_source_and_FK_gate']=all(admission['checks'].values())
            if not checks['initial_grip_source_and_FK_gate']:raise AssertionError('initial grip source/FK gate rejected; t0 partial video saved')
            for step in range(1200):
                updated=step%4==0
                if updated:
                    before_state=native_state(env)
                    submitted=compose(env.initial_q,env.main_indices,offsets,env.lower,env.upper)
                    if not np.array_equal(submitted,np.array(grip_row['expected_absolute_targets_rad'],dtype=np.float32)):raise AssertionError('absolute PD targets changed')
                    submit(env,offsets);checks['commands_preserve_states'] &= native_state(env)==before_state
                    if not np.array_equal(env.target,submitted):raise AssertionError('target mirror mismatch')
                    record={'task_error_m_scaled_rad':task,'other48_targets_held':bool(np.array_equal(env.target[other],env.initial_q[other]))}
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
            'input_sha256':hashes,'videos':videos,'stability_success':False,'scope':'actual continuous 5s Gym same recorded initial81 and absolute targets; read-only native shape query; fresh source/FK admission; source palm-up proxy violations logged; other pose constraints not certified; fixed root/lower and held targets checked separately; no stability certification or pose replay'})
    if not completed:raise RuntimeError(failure or checks)
    print(json.dumps({'completed':completed,'physics_steps':env.steps,'frame_count':len(recorder.frames),'constraint_violations':len(violations)}),flush=True)


if __name__=='__main__':main()
