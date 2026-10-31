"""Five-second free-guitar palm/thumb contact comparison, no checkpoint."""
import argparse
import json
import traceback
from pathlib import Path
from .underneck_pose_trial_v5 import UnderneckEnvironment, initial_audit, read, save, pose
from .run_joint_hold import native_state
from .environment import np
from .bounded_arm_hold import BoundedArmHold
from .palm_thumb_posture_support_v1 import PalmThumbPostureSupport as PalmThumbSupport
from .fret_raw_recording import FretRawRecording
from .native_contacts import read_contacts, body_names, plain


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--support',choices=('OFF','ON'),required=True)
    args = parser.parse_args(); out = args.out.resolve(); out.mkdir(parents=True,exist_ok=False)
    journal = (out/'journal.jsonl').open('x')
    env = recorder = None; failure = None; videos = {}; trace = []; contacts = []; controls = []; checks = {}
    try:
        env = UnderneckEnvironment(read(args.candidate)); state0 = native_state(env)
        audit = initial_audit(env,env.candidate); save(out/'initial_audit.json',audit)
        recorder = FretRawRecording(env,out/'images'); recorder.capture()
        props = env.gym.get_actor_dof_properties(env.env,env.human).copy()
        shapes = {label:[dict(friction=p.friction,contact_offset=p.contact_offset,rest_offset=p.rest_offset)
                          for p in env.gym.get_actor_rigid_shape_properties(env.env,actor)]
                  for label,actor in (('human',env.human),('guitar',env.guitar))}
        save(out/'initial_values.json',dict(candidate_path=str(args.candidate.resolve()),joint_names=env.names,
            human_body_names=env.human_bodies,guitar_body_names=env.guitar_bodies,native_initial_state=state0,
            actual_initial_angles_rad=env.initial_q.tolist(),initial_PD_targets_rad=env.target.tolist(),
            native_lower_rad=env.lower.tolist(),native_upper_rad=env.upper.tolist(),PD_properties=plain(props),
            shape_properties=shapes,self_collision_policy=env.self_collision_policy,strap_enabled=False,
            checkpoint_enabled=False,support_mode=args.support))
        if not all(audit['checks'].values()) or not audit['source_clear']:
            raise ValueError('fresh native initial audit failed')
        arm = np.array([i for i,n in enumerate(env.names) if n.startswith(
            ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        hold = BoundedArmHold(env.initial_q[arm],env.lower[arm],env.upper[arm])
        support = PalmThumbSupport(env,state0) if args.support=='ON' else None
        owned = np.union1d(arm,support.indices if support else np.array([],dtype=int))
        other = np.setdiff1d(np.arange(len(env.names)),owned)
        gp0,gr0 = pose(state0['guitar_body_states'][0]); names = body_names(env.gym,env.env)
        checks.update(initial_audit=True,single_target_owner=True,targets_in_limits=True,
                      target_rates=True,other_targets_held=True,root_lower_fixed=True,commands_readonly=True,
                      render_readonly=True,PD_unchanged=True,no_forbidden_calls=True,palm_up=True)
        from .underneck_initial_search import FACETS
        palm_normal = np.array(read(FACETS)['facets']['LH:palm']['normal_local'])
        palm_index = env.human_bodies.index('LH:palm')
        def sample():
            state = native_state(env); gp,gr = pose(state['guitar_body_states'][0])
            trace.append(dict(physics_step=env.steps,time_s=env.steps/240,position_W_m=gp.tolist(),
                quaternion_xyzw=gr.as_quat().tolist(),position_change_m=float(np.linalg.norm(gp-gp0)),
                rotation_change_deg=float(np.degrees((gr*gr0.inv()).magnitude())),native_state=state))
        sample()
        journal.write(json.dumps(dict(kind='initial',trace=trace[-1]))+'\n'); journal.flush()
        for tick in range(300):
            before = native_state(env); actual = np.array([s['pos'] for s in before['human_dof_states']])
            measured = actual[arm].copy()
            if support:
                # Left-arm target has one integrator: task residual replaces joint-hold PI.
                left_in_arm = [j for j,i in enumerate(arm) if env.names[i].startswith('L_')]
                measured[left_in_arm] = env.initial_q[arm][left_in_arm]
            desired = env.initial_q.copy(); desired[arm],diagnostic = hold.update(measured,1/60)
            previous = env.target.copy(); record = None
            if support:
                desired[support.indices],record = support.update(before,desired,previous,1/60)
            rate = np.full(len(env.names),.8)
            if support: rate[support.indices] = support.rate
            env.target = np.clip(np.clip(desired,previous-rate/60,previous+rate/60),env.lower,env.upper).astype(np.float32)
            env._submit_targets()
            checks['commands_readonly'] &= native_state(env)==before
            checks['targets_in_limits'] &= bool(np.all((env.target>=env.lower)&(env.target<=env.upper)))
            checks['target_rates'] &= bool(np.all(abs(env.target-previous)<=rate/60+2e-7))
            checks['other_targets_held'] &= np.array_equal(env.target[other],env.initial_q[other])
            contacts.append(dict(physics_step=env.steps,time_s=env.steps/240,
                palm_normal_up=float(pose(before['human_body_states'][palm_index])[1].apply(palm_normal)[2]),
                contacts=read_contacts(env.gym,env.env,names)))
            controls.append(dict(time_s=env.steps/240,submitted_targets_rad=env.target.tolist(),
                                 hold_diagnostic=diagnostic,support_diagnostic=record))
            for _ in range(4):
                env.step_physics(); state = native_state(env)
                values = [v for r in state['human_dof_states'] for v in (r['pos'],r['vel'])]
                for row in state['human_body_states']+state['guitar_body_states']:
                    for block in (row['pose']['p'],row['pose']['r'],row['vel']['linear'],row['vel']['angular']):
                        values.extend(block.values())
                if not np.isfinite(values).all() or max(abs(r['vel']) for r in state['human_dof_states'])>50:
                    raise ValueError('unsafe native state')
                up = float(pose(state['human_body_states'][palm_index])[1].apply(palm_normal)[2])
                if up<0:
                    checks['palm_up'] = False
                    raise ValueError('palm left upper hemisphere')
                checks['root_lower_fixed'] &= all(state['human_body_states'][i]==state0['human_body_states'][i]
                    for i,n in enumerate(env.human_bodies) if i==0 or any(k in n for k in ('Hip','Knee','Ankle','Toe')))
                if env.steps%8==0: sample(); recorder.capture()
            journal.write(json.dumps(dict(kind='completed_tick',physics_step=env.steps,control=controls[-1],contacts=contacts[-1:],native_state=state))+'\n'); journal.flush()
            if env.steps%240==0: print('native seconds',env.steps/240,'support',args.support,flush=True)
        checks['PD_unchanged'] = np.array_equal(props,env.gym.get_actor_dof_properties(env.env,env.human))
        checks['no_forbidden_calls'] = not env.forbidden_calls
        checks['render_readonly'] = all(f['render_preserves_states'] for f in recorder.frames)
    except BaseException as exc:
        failure = dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
        print(failure['traceback'],flush=True)
        if env:
            failed = dict(physics_step=env.steps,time_s=env.steps/240,native_state=native_state(env),
                          nonfinite_encoding='NaN/Infinity encoded as strings in failed states only')
            save(out/'failure_state.json',json.loads(json.dumps(failed),parse_constant=str))
    finally:
        if env and recorder and trace and trace[-1]['physics_step']!=env.steps:
            try: sample(); recorder.capture()
            except BaseException: pass
        journal.close()
        save(out/'trace.json',json.loads(json.dumps(trace),parse_constant=str))
        save(out/'contacts.json',contacts); save(out/'controls.json',controls)
        errors = []
        try:
            if env: env.close()
        except BaseException as exc: errors.append(dict(stage='close',message=str(exc)))
        try:
            if recorder and len(recorder.frames)>1: videos = recorder.encode()
        except BaseException as exc: errors.append(dict(stage='encode',message=str(exc)))
        save(out/'report.json',dict(failure=failure,finalization_errors=errors,checks=checks,
            physics_steps=env.steps if env else 0,completed_5s=bool(env and env.steps==1200 and failure is None and not errors and all(checks.values())),
            recorded_physics_duration_s=env.steps/240 if env else 0,frame_count=len(recorder.frames) if recorder else 0,
            support_mode=args.support,videos=videos,learning_updates=0,music_success=False))
    if failure or errors or not all(checks.values()): raise RuntimeError(failure or errors or checks)


if __name__=='__main__': main()
