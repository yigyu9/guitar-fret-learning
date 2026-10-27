"""Small ring/pinky target reversals from prepared and actual policy10s poses.

Root runs native GPU physics. This tool never injects q/body state, edits the
controller, resets a finished row, trains a policy or changes contact settings.
Any first native termination stops the entire variant, preserving censorship.
"""
import argparse
import copy
import faulthandler
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[2]
SOURCE = ROOT/'docs/2026-10-21/guitar_learning_press_control_v1'
SEAL_SHA = '855ad6dd2f5e56eea43705e9c3f3b54abc1251bf12787ab9e1dab394cd83747a'
JOINTS = tuple('LH:'+finger+part for finger in ('ring','pinky') for part in ('1_x','1_z','2','3'))
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json_io.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def case_specs():
    return [dict(env_id=2*i+j,kind='pulse',joint=name,axis_index=i,direction=sign,
                 action_amplitude=sign*.05,requested_velocity_rad_s=sign*.2)
            for i,name in enumerate(JOINTS) for j,sign in enumerate((1,-1))]+[
        dict(env_id=16,kind='hold',joint=None,axis_index=None,direction=0),
        dict(env_id=17,kind='coordinated_return',joint=None,axis_index=None,direction=0)]


def segment(tick, row):
    if row == 17:
        return 6
    if row == 16:
        return 3
    return 2 if tick < 60 else 3 if tick < 90 else 4 if tick < 150 else 5


def finger_actions(tick, current, original, reference):
    """Normalized incremental actions; only requested targets, never actual q."""
    import torch
    require(type(tick) is int and 0 <= tick < 180 and current.shape == original.shape == (18,8)
            and reference.shape == (8,), 'Probe tick0..179 and aligned18x8 targets required')
    action = torch.zeros_like(current)
    rows = torch.arange(16, device=current.device)
    axes = rows//2
    if tick < 60:
        amplitude = torch.full_like(rows,.05,dtype=current.dtype)
        action[rows, axes] = torch.where(rows%2 == 0, amplitude, -amplitude)
    elif 90 <= tick < 150:
        action[rows, axes] = ((original[rows, axes]-current[rows, axes])*15.).clamp(-.05,.05)
    action[17] = ((reference-current[17])*15.).clamp(-.05,.05)
    return action


def absolute_hold_actions(target, reference, low, high, left_hand):
    """Invert only absolute channels; incremental LH21 is zero-to-hold."""
    import torch
    require(target.ndim == 2 and target.shape[1] == 39 and
            reference.shape == low.shape == high.shape == left_hand.shape == (39,), 'Named active39 arrays required')
    delta = target-reference
    span = torch.where(delta >= 0, high-reference, reference-low)
    require(not bool(((span == 0) & (delta.abs() > 3e-6) & ~left_hand).any()), 'Zero-span absolute channel cannot hold a different target')
    action = torch.where(span > 0, delta/span.clamp_min(1e-30), torch.zeros_like(delta))
    action[:,left_hand] = 0
    require(bool(torch.isfinite(action).all()) and bool((action.abs() <= 1+1e-6).all()), 'Bounded finite inverse codec action required')
    return action.clamp(-1,1)


def verify_seal(source):
    manifest = source/'result_manifest.json'
    require(sha(manifest) == SEAL_SHA, 'Original sealed phase manifest changed')
    seal = json.loads(manifest.read_text())
    require(seal['file_count'] == len(seal['files']) == 881 and seal['total_bytes'] == 788097551,
            'Unexpected sealed phase size/count')
    pins = {str(manifest):SEAL_SHA}
    for relative, record in seal['files'].items():
        path = source/relative
        require(path.is_file() and path.stat().st_size == record['bytes'] and sha(path) == record['sha256'],
                'Sealed result changed: '+relative)
        pins[str(path)] = record['sha256']
    return pins


def allocate(ticks):
    import numpy as np
    slow = {k:np.empty((ticks+1,18)+shape,dtype=dtype) for k,shape,dtype in (
        ('body_state',(106,13),np.float32),('q',(105,),np.float32),('qd',(105,),np.float32),
        ('target',(105,),np.float32),('action',(39,),np.float32),('raw_policy_action',(39,),np.float32),
        ('clock',(),np.int64),('global_physics_step',(),np.int64),('segment',(),np.int8))}
    fast = {k:np.empty((ticks*4,18)+shape,dtype=dtype) for k,shape,dtype in (
        ('q',(105,),np.float32),('qd',(105,),np.float32),('target',(105,),np.float32),
        ('contact_force_norm',(68,),np.float32),('clock',(),np.int64))}
    fast['global_physics_step'] = np.empty(ticks*4,dtype=np.int64)
    return slow, fast


def audit_capture(slow, fast, ticks):
    import numpy as np
    require(all(np.isfinite(a).all() for a in (*slow.values(),*fast.values())), 'Nonfinite capture')
    require(slow['body_state'].shape == (ticks+1,18,106,13) and
            fast['contact_force_norm'].shape == (4*ticks,18,68), 'Native body capture layout differs')
    require(np.array_equal(slow['clock'],np.repeat((np.arange(ticks+1)*4)[:,None],18,axis=1)) and
            np.array_equal(fast['clock'],np.repeat(np.arange(1,4*ticks+1)[:,None],18,axis=1)), 'Consecutive episode clocks required')
    require(np.array_equal(slow['global_physics_step'],slow['clock']) and
            np.array_equal(fast['global_physics_step'],np.arange(1,4*ticks+1)), 'Native global clock mismatch')
    for key in ('q','qd','target'):
        require(np.array_equal(slow[key][1:],fast[key][3::4]), '240Hz/60Hz endpoint readback mismatch: '+key)
    require(np.array_equal(fast['target'],np.repeat(slow['target'][1:],4,axis=0)), 'Within-control target changed')
    require(np.max(np.abs(np.linalg.norm(slow['body_state'][...,3:7],axis=-1)-1)) < 1e-3,
            'Invalid body quaternion')
    return dict(finite=True,clock_exact=True,native_endpoint_readback_exact=True,
                native_samples=4*ticks,capture_frames=ticks+1)


def run_variant(out, prefix, settings, checkpoint, training_contract, pins):
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool,FIELDS
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOTrainer,PPOConfig
    from guitar_learning.song.curriculum_runtime import CurriculumCoordinator
    from guitar_learning.training.recording import project_source_paths
    out.mkdir()
    write(out/'settings.json',settings)
    local_pins = dict(pins);local_pins[str(out/'settings.json')] = sha(out/'settings.json')
    write(out/'inputs_before.json',local_pins)
    slow,fast = allocate(prefix+180)
    pool,original_substep = None,None
    ticks,physics,frame_count = 0,0,0
    failure,cleanup,ended = None,[],[]
    started = time.perf_counter()
    metadata = None
    origin,base,probe_frame = None,None,None
    recurrence_error,hold_error = 0.,0.
    freeze_passed = False
    def status(stage):
        path = out/'lifecycle.json'
        path.with_suffix('.tmp').write_text(json_io.dumps(dict(stage=stage,control_ticks=ticks,
            physics_steps=physics,wall_s=time.perf_counter()-started),allow_nan=False)+'\n')
        path.with_suffix('.tmp').replace(path)
    def capture(action,raw,code):
        nonlocal frame_count
        snap = pool.environment.snapshot
        for key in ('body_state','q','qd','target'):
            slow[key][ticks] = snap[key].detach().cpu().numpy()
        slow['action'][ticks] = action.detach().cpu().numpy()
        slow['raw_policy_action'][ticks] = raw.detach().cpu().numpy()
        slow['clock'][ticks] = pool.environment.clock.cpu().numpy()
        slow['global_physics_step'][ticks] = pool.scene.physics_steps
        slow['segment'][ticks] = code
        frame_count=ticks+1
    try:
        status('creating_pool');pool = GpuPool(settings,out)
        require(pool.contract == training_contract,'N18 strict training contract changed')
        control = pool.controller
        action_ids = torch.tensor([control.contract['action_order'].index(n) for n in JOINTS],device=pool.scene.device)
        native_ids = control.active[action_ids]
        hand = torch.tensor([n.startswith('LH:') for n in control.contract['action_order']],device=pool.scene.device)
        policy = SpecialistPolicy(512,size='large',contract=pool.contract,role='left').to(settings['device'])
        coordinator = CurriculumCoordinator(policy,pool)
        trainer = PPOTrainer(policy,PPOConfig(**settings['ppo']));trainer.load(checkpoint)
        require(trainer.updates == 100,'Expected optimizer100 strict checkpoint')
        observation = coordinator.restore();policy.eval()
        frozen = {k:v.detach().clone() for k,v in policy.state_dict().items()}
        require(policy.left_curriculum_state.numel() == 3331,'Expected3331 curriculum values')
        progress = coordinator.state.progress
        native_names = ['human/'+n for n in pool.scene.human_bodies]+['guitar/guitar','chair/box']
        require(len(native_names) == pool.scene.native_body_count == 68,'Expected actual68 native bodies')
        metadata = dict(schema='guitar_learning.ring_pinky_probe.v1',prefix_ticks=prefix,probe_ticks=180,
            probe_start_frame=None,tested_joint_names=list(JOINTS),tested_native_indices=native_ids.cpu().tolist(),
            tested_action_indices=action_ids.cpu().tolist(),native_lower_rad=pool.scene.lower[native_ids].cpu().tolist(),
            native_upper_rad=pool.scene.upper[native_ids].cpu().tolist(),prepared_reference8=control.reference[native_ids].cpu().tolist(),
            joint_names=pool.scene.names,body_names=pool.scene.body_names,native_body_names=native_names,
            axes=[dict(joint=n,native_body_index=int(control.joint_bodies[j].item()),
                native_body_name=native_names[int(control.joint_bodies[j].item())],source_body_local_axis=control.axes[j].cpu().tolist())
                for n,j in zip(JOINTS,native_ids.cpu().tolist())],
            source_checkpoint=str(checkpoint),source_checkpoint_sha256=sha(checkpoint),curriculum_values=3331,
            restored_curriculum_progress=progress,capture_hz=60,native_capture_hz=240,
            slow_capture_allocated_bytes=sum(v.nbytes for v in slow.values()),native_capture_allocated_bytes=sum(v.nbytes for v in fast.values()),
            segment_codes=dict(initial=0,policy_prefix=1,push=2,hold=3,return_original_target=4,posthold=5,coordinated_return=6),
            schedule='Pulse±0.2rad/s1s,hold0.5s,return-original-target at<=0.2rad/s1s,hold0.5s. Row16hold;row17 all8 toward prepared targets at<=0.2rad/s for3s; may not reach prepared targets.',
            other_channels='Incremental non-tested LH channels action0 hold current targets; absolute active18 use inverse codec constant actions to hold prefix-end targets. No q/body state injection.',
            frames='60Hz frame0 prepared reset and every actual control endpoint; raw_policy_action nonzero only in actual prefix. Clock=4*frame. Native240 begins at physics1; q/qd/target105 and all68 body contact force norms.',
            force_scope='Native net body contact norm, not pair/local witness, joint reaction torque or pressure.',
            stopping='Any first native termination stops whole variant with no reset or finished-flag modification; other rows right-censored. Probe end is not whole-song success.',
            cases=case_specs())
        write(out/'training_contract.json',pool.contract);write(out/'visual_initial.json',pool.scene.contract['initial'])
        original_substep = pool.environment.substep
        def recorded(snapshot):
            nonlocal physics
            original_substep(snapshot)
            for key in ('q','qd','target'):
                fast[key][physics] = snapshot[key].detach().cpu().numpy()
            fast['contact_force_norm'][physics] = torch.linalg.vector_norm(pool.scene._native_contact_force,dim=-1).cpu().numpy()
            fast['clock'][physics] = pool.environment.clock.cpu().numpy()
            fast['global_physics_step'][physics] = pool.scene.physics_steps
            physics += 1
        pool.environment.substep = recorded
        zero = torch.zeros(18,39,device=pool.scene.device);capture(zero,zero,0)
        with torch.no_grad():
            for tick in range(prefix+180):
                if tick < prefix:
                    raw = policy.act(*(observation[k] for k in FIELDS),deterministic=True)['action']
                    action,code = raw,1
                else:
                    if origin is None:
                        probe_frame = ticks
                        origin = control.target[:,native_ids].clone()
                        held = control.target[:,control.active].clone()
                        base = absolute_hold_actions(held,control.reference[control.active],control.action_low,control.action_high,hand)
                        require(not base[:,33:].any(),'Inactive right action must remain zero')
                        metadata.update(probe_start_frame=probe_frame,probe_start_target_rad=origin.cpu().tolist(),
                            hold_action39=base.cpu().tolist(),probe_start_active_target_rad=held.cpu().tolist())
                        q = slow['q'][ticks];tar = slow['target'][ticks];body = slow['body_state'][ticks]
                        metadata['probe_start_between_row_difference'] = dict(q_max_abs_rad=float(np.abs(q-q[0]).max()),
                            target_max_abs_rad=float(np.abs(tar-tar[0]).max()),
                            body_max_abs_component=float(np.abs(body-body[0]).max()),
                            body_position_max_distance_m=float(np.linalg.norm(body[...,:3]-body[0,:,:3],axis=-1).max()))
                        for case in metadata['cases']:
                            row=case['env_id'];axis=case['axis_index']
                            if axis is not None:
                                start=float(origin[row,axis].item());sign=case['direction']
                                room=(metadata['native_upper_rad'][axis]-start if sign>0 else start-metadata['native_lower_rad'][axis])
                                case.update(available_native_room_rad=max(0.,room),expected_clipped_pulse_delta_rad=sign*min(.2,max(0.,room)),
                                    zero_requested_room=room<=1e-7)
                    raw = zero
                    action = base.clone()
                    action[:,action_ids] = finger_actions(tick-prefix,control.target[:,native_ids],origin,control.reference[native_ids])
                    code = [segment(tick-prefix,row) for row in range(18)]
                require(torch.isfinite(action).all() and (action.abs()<=1).all(),'Finite bounded actual action39 required')
                previous_target = control.target.clone()
                observation,reward,cost,terminated,truncated,episodes = pool.step(action)
                ticks += 1;capture(action,raw,code)
                require(torch.isfinite(reward).all() and torch.isfinite(cost).all() and not truncated.any(),'Nonfinite/truncated native transition')
                if tick >= prefix:
                    expected=(previous_target[:,native_ids]+action[:,action_ids]*(4./60)).clamp(
                        pool.scene.lower[native_ids],pool.scene.upper[native_ids])
                    recurrence_error=max(recurrence_error,float((control.target[:,native_ids]-expected).abs().max().item()))
                    testing=torch.zeros(18,39,dtype=torch.bool,device=pool.scene.device)
                    pulse_rows=torch.arange(16,device=pool.scene.device)
                    testing[pulse_rows,action_ids[pulse_rows//2]]=True;testing[17,action_ids]=True
                    hold_error=max(hold_error,float((control.target[:,control.active]-held).abs().masked_fill(testing,0).max().item()))
                if bool((terminated|truncated).any()):
                    ended=episodes;break
                if ticks%60==0:
                    status('stepping')
        require(recurrence_error<=4e-6 and hold_error<=3e-6,'Probe recurrence or non-tested active target hold mismatch')
        freeze_passed=trainer.updates==100 and coordinator.state.progress==progress and all(
            torch.equal(v,frozen[k]) for k,v in policy.state_dict().items())
        require(freeze_passed,'Probe changed model/curriculum')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        traceback.print_exc()
    finally:
        if pool is not None:
            if original_substep is not None:
                pool.environment.substep=original_substep
            try:pool.close()
            except BaseException as error:cleanup.append(repr(error))
    slow={k:v[:frame_count] for k,v in slow.items()};fast={k:v[:physics] for k,v in fast.items()}
    proof=None
    try:
        proof=audit_capture(slow,fast,ticks)
    except BaseException as error:
        if failure is None:failure=dict(type='CaptureAuditError',message=repr(error))
    raw_path=out/'native240.npz';np.savez_compressed(str(raw_path),**fast)
    if metadata is not None:
        metadata.update(native_capture=dict(path=raw_path.name,sha256=sha(raw_path),samples=physics),
            non_tested_active_target_hold_max_error_rad=hold_error,probe_target_recurrence_max_error_rad=recurrence_error)
        ended_by_id={e['env_id']:e for e in ended}
        for case in metadata['cases']:
            row=case['env_id'];path=out/('case_%03d.npz'%row)
            arrays={k:v[:,row] for k,v in slow.items()};np.savez_compressed(str(path),**arrays)
            case.update(path=path.name,sha256=sha(path),frames=frame_count,first_episode=ended_by_id.get(row),
                outcome=ended_by_id[row]['reason'] if row in ended_by_id else 'right_censored_at_variant_stop' if ended else 'probe_schedule_complete_no_episode_end')
            if origin is not None and frame_count>prefix and case['axis_index'] is not None:
                j=metadata['tested_native_indices'][case['axis_index']]
                available=frame_count-1
                end_push=min(prefix+60,available);end_hold=min(prefix+90,available);end_return=min(prefix+150,available)
                case['target_readback']=dict(pulse_delta_rad=float(arrays['target'][end_push,j]-arrays['target'][prefix,j]),
                    hold_delta_rad=float(arrays['target'][end_hold,j]-arrays['target'][end_push,j]),
                    return_error_to_original_rad=float(arrays['target'][end_return,j]-arrays['target'][prefix,j]),
                    actual_q_pulse_delta_rad=float(arrays['q'][end_push,j]-arrays['q'][prefix,j]),
                    actual_q_return_delta_rad=float(arrays['q'][end_return,j]-arrays['q'][prefix,j]),
                    complete_pulse=available>=prefix+60,complete_return=available>=prefix+150)
                readback=case['target_readback']
                checks=(not readback['complete_pulse'] or abs(readback['pulse_delta_rad']-case['expected_clipped_pulse_delta_rad'])<=4e-6) and (
                    not readback['complete_return'] or abs(readback['return_error_to_original_rad'])<=4e-6) and abs(readback['hold_delta_rad'])<=3e-6
                case['target_readback']['passed']=bool(checks)
                if not checks and failure is None:
                    failure=dict(type='TargetReadbackError',message='Pulse/hold/return readback differs for row'+str(row))
        if origin is not None and frame_count>prefix:
            actual=slow['target'][-1,17,metadata['tested_native_indices']]-np.asarray(metadata['probe_start_target_rad'][17])
            reference=np.asarray(metadata['prepared_reference8'])
            start=np.asarray(metadata['probe_start_target_rad'][17])
            elapsed=(frame_count-1-prefix)/60.
            expected=np.clip(reference-start,-.2*elapsed,.2*elapsed)
            error=float(np.abs(actual-expected).max())
            metadata['coordinated_target_readback']=dict(expected_delta_rad=expected.tolist(),
                actual_delta_rad=actual.tolist(),maximum_error_rad=error,
                prepared_targets_reached=bool(np.max(np.abs(start+actual-reference))<=4e-6),
                scope='Target only; actual joint/body pose is not forced to the prepared state.')
            if error>4e-6 and failure is None:
                failure=dict(type='TargetReadbackError',message='Coordinated rate-clamped return differs')
        write(out/'capture_metadata.json',metadata)
    scene=pool.scene.diagnostics if pool is not None and pool.scene is not None else None
    changed=[p for p,v in local_pins.items() if not Path(p).is_file() or sha(p)!=v]
    missing=sorted(project_source_paths(list(sys.modules.items()))-set(local_pins))
    native_ok=bool(scene and scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and
        scene['num_envs']==18 and scene['physics_steps']==ticks*4==physics and scene['simulator_count']==1)
    result=dict(completed=failure is None and not(cleanup or changed or missing) and native_ok,
        schedule_completed=ticks==prefix+180,probe_started=origin is not None,prefix_ticks=prefix,
        actual_control_ticks=ticks,actual_physics_steps=physics,first_ended_episodes=ended,failure=failure,
        policy_batched_calls=min(prefix,ticks),probe_control_ticks=max(0,ticks-prefix),
        cleanup_errors=cleanup,changed_inputs=changed,missing_import_pins=missing,gpu_scene=scene,
        capture_audit=proof,model_and_curriculum_unchanged=bool(freeze_passed),PPO_updates=0,
        probe_target_recurrence_max_error_rad=recurrence_error,non_tested_active_target_hold_max_error_rad=hold_error,
        wall_s=time.perf_counter()-started,
        scope='Early native termination is preserved and stops whole variant; other rows are right-censored, never reset. Normal3s probe end is not whole-song completion or absence of all possible sticking.')
    write(out/'report.json',result);status('report_written')
    return result


def main():
    faulthandler.enable(all_threads=True)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source-phase',type=Path,default=SOURCE)
    args=parser.parse_args();source=args.source_phase.resolve();out=args.out.resolve()
    require(source not in (out,*out.parents),'Output must be outside the sealed source phase')
    pins=verify_seal(source)
    run=source/'smoke100';checkpoint=run/'final.pt'
    settings=json.loads((run/'settings.json').read_text());report=json.loads((run/'report.json').read_text())
    training=json.loads((run/'training_contract.json').read_text())
    require(report['completed'] and report['optimizer_updates']==100 and not(report['failure'] or report['cleanup_errors'] or
            report['changed_inputs'] or report['missing_import_pins']),'Intact completed100 source run required')
    require(settings['num_envs']==1024 and settings['horizon']==32 and settings['size']=='large' and settings['seed']==7,
            'Expected large1024/H32/seed7 source')
    manifest=json.loads((source/'training_source_manifest.json').read_text())
    require(manifest['active_python_count']==len(manifest['source'])==435,'Expected frozen435 source manifest')
    pins.update(json.loads((run/'inputs_before.json').read_text()));pins.update(manifest['source'])
    require(all(Path(p).is_file() and sha(p)==v for p,v in pins.items()),'Current source/input SHA mismatch')
    pins[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    # No native import or context exists before the strict source checks above.
    import isaacgym
    import torch
    torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
    out.mkdir(parents=True,exist_ok=False);write(out/'inputs_before.json',pins)
    settings=copy.deepcopy(settings);settings['num_envs']=18
    results=[]
    for variant,prefix in (('prepared',0),('learned10',600)):
        result=run_variant(out/variant,prefix,settings,checkpoint,training,pins)
        results.append(dict(variant=variant,**result))
        if not result['completed']:
            break  # Do not start a second simulator after an invalid native run.
    seal_after=verify_seal(source)
    require(seal_after=={p:v for p,v in pins.items() if p in seal_after},'Source seal changed')
    write(out/'report.json',dict(completed=len(results)==2 and all(r['completed'] for r in results),
        variants=results,source_phase=str(source),source_seal_sha256=SEAL_SHA,source_seal_files=881,
        source_python_count=435,checkpoint=str(checkpoint),checkpoint_sha256=sha(checkpoint),
        limitations='N18 fixed condition IDs and actual per-row prefix differences; no contact pair/pressure witness, physical reachability proof, learning-benefit or N1024 parity claim.'))
    print(json_io.dumps(dict(completed=len(results)==2 and all(r['completed'] for r in results),
        ticks=[r['actual_control_ticks'] for r in results]),allow_nan=False))
    return 0 if len(results)==2 and all(r['completed'] for r in results) else 1


if __name__=='__main__':sys.exit(main())
