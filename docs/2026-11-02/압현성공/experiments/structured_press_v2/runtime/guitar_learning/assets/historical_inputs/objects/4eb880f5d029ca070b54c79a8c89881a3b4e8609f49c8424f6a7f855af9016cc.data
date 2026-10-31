"""Compare four EFFORT physics frames, then restore ordinary position PD for five-second recording."""
from .underneck_pose_trial_v5 import UnderneckEnvironment,NoStrapGym,initial_audit,read,save
from .capture_isaac_gym_initial import GraphicsGym
from .environment import np,gymapi
from .run_joint_hold import native_state
from .native_contacts import plain
from .gym_trial_recording import GymTrialRecording
from isaacgym import gymtorch
import torch
from pathlib import Path
import argparse
import traceback


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--torque',type=int,choices=(0,1),required=True);args=parser.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    env=recorder=None;states=[];commands=[];failure=None;videos={};checks={}
    try:
        candidate=read(args.candidate);env=UnderneckEnvironment(candidate)
        audit=initial_audit(env,candidate);save(out/'initial_audit.json',audit)
        if not all(audit['checks'].values()) or not audit['source_clear']:raise ValueError('initial audit failed')
        initial=native_state(env);props=env.gym.get_actor_dof_properties(env.env,env.human).copy()
        original_props=props.copy()
        idx=np.array([i for i,n in enumerate(env.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);kp=props['stiffness'].copy();limit=props['effort'].copy()
        assert len(idx)==12 and env.gym.get_sim_dof_count(env.sim)==81
        props['driveMode'][idx]=gymapi.DOF_MODE_EFFORT;props['stiffness'][idx]=0;props['damping'][idx]=0
        if not env.gym.set_actor_dof_properties(env.env,env.human,props):raise RuntimeError('EFFORT init failed')
        target=env.target.copy();joint=env.names.index('R_Shoulder_z');delta=.05 if target[joint]+.05<=env.upper[joint] else -.05
        target[joint]=np.clip(target[joint]+delta,env.lower[joint],env.upper[joint])
        save(out/'initial_values.json',{'candidate':str(args.candidate.resolve()),'native_initial_state':initial,'joint_names':env.names,'PD_properties':plain(props),'saved_kp':kp.tolist(),'torque_enabled':bool(args.torque),'requested_targets_rad':target.tolist(),'stepped_joint':'R_Shoulder_z','requested_step_rad':delta,'strap_force_enabled':False,'original_PD_properties':plain(original_props),'EFFORT_probe_physics_steps':4})
        checks.update(PD_expected_schedule=True,no_state_overwrite=True,root_lower_fixed=True,torque_bounds=True,torque_only_right_arm=True,render_readonly=True)
        recorder=GymTrialRecording(env,out/'images');recorder.capture()
        states.append({'physics_step':0,'native_state':initial})
        before=native_state(env);env.target=target;env._submit_targets();checks['no_state_overwrite'] &= native_state(env)==before
        assert isinstance(env.gym,GraphicsGym) and isinstance(env.gym.gym,NoStrapGym)
        joint_api=env.gym.gym.gym.set_dof_actuation_force_tensor
        before_mass=native_state(env)
        mass_tensor=gymtorch.wrap_tensor(env.gym.acquire_mass_matrix_tensor(env.sim,'human'))
        env.gym.refresh_mass_matrix_tensors(env.sim)
        mass=mass_tensor.numpy().copy()
        assert mass.shape==(1,81,81) and np.isfinite(mass).all()
        checks['mass_readonly']=native_state(env)==before_mass
        save(out/'mass_matrix_initial.json',{'shape':list(mass.shape),'matrix':mass.tolist(),'max_asymmetry':float(abs(mass-mass.transpose(0,2,1)).max()),'scope':'read-only initial native mass matrix; not used for these torque commands'})
        command=torch.zeros(81,dtype=torch.float32)
        for tick in range(300):
            s=native_state(env);actual=np.array([r['pos'] for r in s['human_dof_states']],dtype=np.float32)
            torque=np.zeros(81,dtype=np.float32)
            if args.torque and tick==0:torque[idx]=np.clip(kp[idx]*(target[idx]-actual[idx]),-limit[idx],limit[idx])
            command.copy_(torch.from_numpy(torque));commands.append({'before_physics_step':env.steps,'requested_human_joint_torque_Nm':torque.tolist()})
            checks['torque_bounds'] &= bool(np.all(abs(torque)<=limit))
            checks['torque_only_right_arm'] &= bool(np.all(torque[np.setdiff1d(np.arange(81),idx)]==0))
            for _ in range(4):
                if not joint_api(env.sim,gymtorch.unwrap_tensor(command)):raise RuntimeError('human joint tensor API failed')
                env.step_physics()
                current=native_state(env)
                values=[v for r in current['human_dof_states'] for v in (r['pos'],r['vel'])]
                for r in current['human_body_states']+current['guitar_body_states']:
                    for block in (r['pose']['p'],r['pose']['r'],r['vel']['linear'],r['vel']['angular']):values.extend(block.values())
                if not np.isfinite(values).all() or max(abs(r['vel']) for r in current['human_dof_states'])>50:raise ValueError('unsafe native state')
                if env.steps==4 or env.steps%8==0:states.append({'physics_step':env.steps,'native_state':current})
                if env.steps==4:
                    before_restore=native_state(env)
                    if not env.gym.set_actor_dof_properties(env.env,env.human,original_props):raise RuntimeError('ordinary PD restore failed')
                    checks['no_state_overwrite'] &= native_state(env)==before_restore
                    checks['PD_expected_schedule'] &= bool(np.array_equal(original_props,env.gym.get_actor_dof_properties(env.env,env.human)))
                if env.steps%8==0:
                    recorder.capture()
                    checks['root_lower_fixed'] &= all(current['human_body_states'][i]==initial['human_body_states'][i] for i,n in enumerate(env.human_bodies) if i==0 or any(k in n for k in ('Hip','Knee','Ankle','Toe')))
            if env.steps%240==0:print('probe seconds',env.steps/240,'torque command',args.torque,flush=True)
        checks['PD_expected_schedule'] &= bool(np.array_equal(original_props,env.gym.get_actor_dof_properties(env.env,env.human)))
        checks['no_forbidden_calls']=not env.forbidden_calls
        checks['render_readonly']=all(f['render_preserves_states'] for f in recorder.frames)
    except BaseException as exc:
        failure={'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc()};print(failure['traceback'],flush=True)
    finally:
        if env:env.close()
        if recorder and len(recorder.frames)>1:videos=recorder.encode()
        save(out/'states.json',states);save(out/'commands.json',commands)
        save(out/'report.json',{'completed_5s':bool(env and env.steps==1200 and failure is None and all(checks.values())),'physics_steps':env.steps if env else 0,'checks':checks,'failure':failure,'frame_count':len(recorder.frames) if recorder else 0,'videos':videos,'torque_command_enabled':bool(args.torque),'scope':'four-frame EFFORT joint activation then ordinary position PD; no Strike/Fret or learning; requested torque is not measured force'})
    if failure or not all(checks.values()):raise RuntimeError(failure or checks)


if __name__=='__main__':main()
