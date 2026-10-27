"""Root-only native N6 finger-base drive diagnosis; no model, PPO or state injection.

Source assets/gains/limits/safety are unchanged. Any first native episode end
stops every row; unfinished rows are right-censored and never reset.
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

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[2]
SOURCE=ROOT/'docs/2026-10-21/guitar_learning_press_control_v1'
SEAL_SHA='855ad6dd2f5e56eea43705e9c3f3b54abc1251bf12787ab9e1dab394cd83747a'
TICKS=525
JOINTS=('LH:ring1_x','LH:ring1_z','LH:pinky1_x','LH:pinky1_z')
sys.path.insert(0,str(ROOT))
from guitar_learning.training import json_io


def require(condition,message):
    if not condition:raise ValueError(message)


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()


def write(path,value):
    with Path(path).open('x') as stream:
        json_io.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def case_specs():
    return [dict(env_id=i,finger=finger,x_target_rad=x,x_axis_index=2*(i//3),z_axis_index=2*(i//3)+1)
            for i,(finger,x) in enumerate((f,x) for f in ('ring','pinky') for x in (0.,.8,1.56))]


def segment(tick):
    require(type(tick) is int and 0<=tick<TICKS,'Expected tick0..524')
    return 1 if tick<240 else 2 if tick<285 else 3 if tick<345 else 4 if tick<405 else 5 if tick<465 else 6


def finger_actions(tick,current,original_z):
    """Normal incremental actions: x conditioning .4rad/s; z pulse .1rad/s."""
    import torch
    code=segment(tick)
    require(current.shape==(6,4) and original_z.shape==(6,),'Aligned six-row target arrays required')
    rows=torch.arange(6,device=current.device);xs=(rows//3)*2;zs=xs+1
    result=torch.zeros_like(current)
    if code==1:
        goals=current.new_tensor([0.,.8,1.56,0.,.8,1.56])
        result[rows,xs]=((goals-current[rows,xs])*15.).clamp(-.1,.1)
    elif code==3:result[rows,zs]=.025
    elif code==5:result[rows,zs]=((original_z-current[rows,zs])*15.).clamp(-.025,.025)
    return result


def absolute_hold_actions(target,reference,low,high,left_hand):
    """LH21 is zero-to-hold; invert only absolute native target channels."""
    import torch
    delta=target-reference
    span=torch.where(delta>=0,high-reference,reference-low)
    require(not bool(((span==0)&(delta.abs()>3e-6)&~left_hand).any()),'Zero-span absolute target differs')
    action=torch.where(span>0,delta/span.clamp_min(1e-30),torch.zeros_like(delta))
    action[:,left_hand]=0
    require(bool(torch.isfinite(action).all()) and bool((action.abs()<=1+1e-6).all()),'Invalid absolute inverse codec')
    return action.clamp(-1,1)


def allocate():
    import numpy as np
    slow={k:np.empty((TICKS+1,6)+shape,dtype=dtype) for k,shape,dtype in (
        ('body_state',(106,13),np.float32),('q',(105,),np.float32),('qd',(105,),np.float32),
        ('target',(105,),np.float32),('action',(39,),np.float32),('clock',(),np.int64),('segment',(),np.int8))}
    slow['global_physics_step']=np.empty(TICKS+1,np.int64)
    fast={k:np.empty((TICKS*4,6)+shape,dtype=dtype) for k,shape,dtype in (
        ('q',(105,),np.float32),('qd',(105,),np.float32),('target',(105,),np.float32),
        ('dof_force',(105,),np.float32),('contact_force_norm',(68,),np.float32),('clock',(),np.int64))}
    fast['global_physics_step']=np.empty(TICKS*4,np.int64)
    return slow,fast


def audit_capture(slow,fast,ticks):
    import numpy as np
    require(all(np.isfinite(a).all() for a in (*slow.values(),*fast.values())),'Nonfinite native capture')
    require(slow['body_state'].shape==(ticks+1,6,106,13) and fast['dof_force'].shape==(4*ticks,6,105), 'Unexpected capture shape')
    require(np.array_equal(slow['clock'],np.repeat((np.arange(ticks+1)*4)[:,None],6,axis=1)) and
        np.array_equal(fast['clock'],np.repeat(np.arange(1,4*ticks+1)[:,None],6,axis=1)), 'Episode clock mismatch')
    require(np.array_equal(slow['global_physics_step'],np.arange(ticks+1)*4) and
        np.array_equal(fast['global_physics_step'],np.arange(1,4*ticks+1)), 'Global physical clock mismatch')
    for key in ('q','qd','target'):
        require(np.array_equal(slow[key][1:],fast[key][3::4]),'Native endpoint readback mismatch: '+key)
    require(np.array_equal(fast['target'],np.repeat(slow['target'][1:],4,axis=0)),'Within-control target changed')
    require(np.max(abs(np.linalg.norm(slow['body_state'][...,3:7],axis=-1)-1))<1e-3,'Invalid quaternion')
    return dict(finite=True,clock_exact=True,native_endpoint_readback_exact=True,frames=ticks+1,native_samples=4*ticks)


def main():
    faulthandler.enable(all_threads=True)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--source-phase',type=Path,default=SOURCE)
    args=parser.parse_args();source=args.source_phase.resolve();out=args.out.resolve()
    require(source not in (out,*out.parents),'Output must be outside sealed source')
    seal_path=source/'result_manifest.json';require(sha(seal_path)==SEAL_SHA,'Source phase seal changed')
    seal=json.loads(seal_path.read_text());run=source/'smoke100'
    manifest_path=source/'training_source_manifest.json';manifest=json.loads(manifest_path.read_text())
    require(manifest['active_python_count']==len(manifest['source'])==435,'Expected frozen435 source')
    pins=dict(manifest['source']);pins.update(json.loads((run/'inputs_before.json').read_text()))
    for path in (run/'settings.json',run/'training_contract.json',run/'report.json',manifest_path):
        record=seal['files'][str(path.relative_to(source))]
        require(path.stat().st_size==record['bytes'] and sha(path)==record['sha256'],'Sealed source input differs: '+str(path))
        pins[str(path)]=record['sha256']
    pins[str(seal_path)]=SEAL_SHA;pins[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
    require(all(Path(p).is_file() and sha(p)==h for p,h in pins.items()),'Input/source pin mismatch')
    settings=json.loads((run/'settings.json').read_text());contract=json.loads((run/'training_contract.json').read_text())
    require(settings['num_envs']==1024 and settings['horizon']==32 and settings['size']=='large' and settings['seed']==7 and
        settings['specialist']['role']=='left','Expected source large1024/H32/seed7 left settings')
    # Native SDK first; no Torch/NumPy/native context exists above this boundary.
    import isaacgym
    from isaacgym import gymtorch
    import numpy as np
    import torch
    from guitar_learning.training.gpu_pool import GpuPool
    from guitar_learning.training.recording import project_source_paths
    torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
    out.mkdir(parents=True,exist_ok=False)
    settings=copy.deepcopy(settings);settings['num_envs']=6;write(out/'settings.json',settings)
    pins[str(out/'settings.json')]=sha(out/'settings.json')
    write(out/'inputs_before.json',pins)
    slow,fast=allocate();pool,hook,metadata=None,None,None
    ticks,physics,frames=0,0,0
    error,cleanup,ended=None,[],[];recurrence_error,hold_error=0.,0.
    original_z=None;started=time.perf_counter();readback_end=None;condition_error=None
    def status(stage):
        path=out/'lifecycle.json';temporary=path.with_suffix('.tmp')
        temporary.write_text(json_io.dumps(dict(stage=stage,control_ticks=ticks,physics_steps=physics,
            wall_s=time.perf_counter()-started),allow_nan=False)+'\n');temporary.replace(path)
    def capture(action,code):
        nonlocal frames
        snap=pool.environment.snapshot
        for key in ('body_state','q','qd','target'):slow[key][ticks]=snap[key].detach().cpu().numpy()
        slow['action'][ticks]=action.cpu().numpy();slow['clock'][ticks]=pool.environment.clock.cpu().numpy()
        slow['global_physics_step'][ticks]=pool.scene.physics_steps;slow['segment'][ticks]=code;frames=ticks+1
    def read_properties():
        result=[]
        for env,actors in zip(pool.scene.envs,pool.scene.actors):
            props=pool.scene.gym.get_actor_dof_properties(env,actors[0])
            require(np.array_equal(props,pool.scene.pd_properties),'Actual actor PD properties differ')
            result.append({field:props[field].tolist() for field in props.dtype.names})
        return result
    try:
        status('creating_pool');pool=GpuPool(settings,out);control=pool.controller;scene=pool.scene
        require(pool.contract==contract,'N6 strict source training contract differs')
        action_ids=torch.tensor([control.contract['action_order'].index(n) for n in JOINTS],device=scene.device)
        native_ids=control.active[action_ids];rows=torch.arange(6,device=scene.device);xs=(rows//3)*2;zs=xs+1
        hand=torch.tensor([n.startswith('LH:') for n in control.contract['action_order']],device=scene.device)
        held=control.target[:,control.active].clone()
        base=absolute_hold_actions(held,control.reference[control.active],control.action_low,control.action_high,hand)
        testing=torch.zeros(6,39,dtype=torch.bool,device=scene.device)
        testing[rows,action_ids[xs]]=True;testing[rows,action_ids[zs]]=True
        asset=scene.gym.get_actor_asset(scene.envs[0],scene.actors[0][0])
        joint_types=[dict(name=name,type=scene.gym.get_joint_type_string(scene.gym.get_asset_joint_type(asset,i)))
            for i,name in enumerate(scene.gym.get_asset_joint_names(asset))]
        descriptor=scene.gym.acquire_dof_force_tensor(scene.sim)
        require(descriptor is not None,'Native GPU DOF force tensor acquisition unsupported')
        dof_force=gymtorch.wrap_tensor(descriptor).view(6,105)
        require(dof_force.is_cuda and dof_force.dtype==torch.float32,'Actual CUDA float32 DOF force tensor required')
        native_names=['human/'+n for n in scene.human_bodies]+['guitar/guitar','chair/box']
        require(len(native_names)==scene.native_body_count==68,'Expected68 native bodies')
        metadata=dict(schema='guitar_learning.multiaxis_native_probe.v1',cases=case_specs(),joint_names=scene.names,
            tested_joint_names=list(JOINTS),tested_action_indices=action_ids.cpu().tolist(),tested_native_indices=native_ids.cpu().tolist(),
            native_body_names=native_names,body_names=scene.body_names,native_lower_rad=scene.lower[native_ids].cpu().tolist(),
            native_upper_rad=scene.upper[native_ids].cpu().tolist(),asset_joint_types=joint_types,
            post_prepare_actor_dof_properties=read_properties(),
            pinned_original_PD_properties=scene.contract['initial']['native_PD_properties'],
            axes=[dict(joint=n,native_body_index=int(control.joint_bodies[j].item()),
                native_body_name=native_names[int(control.joint_bodies[j].item())],source_body_local_axis=control.axes[j].cpu().tolist())
                for n,j in zip(JOINTS,native_ids.cpu().tolist())],
            schedule=dict(control_hz=60,native_hz=240,total_ticks=525,condition_x_ticks=240,hold_x_ticks=45,
                z_pulse_ticks=60,z_hold_ticks=60,z_return_ticks=60,z_posthold_ticks=60,x_rate_cap_rad_s=.4,z_rate_cap_rad_s=.1),
            segment_codes=dict(initial=0,condition_x=1,hold_x=2,pulse_z=3,hold_z=4,return_z=5,posthold_z=6),
            other_channels='Other LH incremental actions zero; absolute18 inverse codec holds initial targets. No model/state/target injection.',
            force_scope='Native body net-contact norms and total DOF force sensors; neither force pair, drive-only torque, friction-only torque nor pressure. Contact cases retained; distinguish them during gain analysis.',
            stopping='Any native episode end stops all rows without reset; others right-censored. Schedule end is not a whole-song success.',
            allocated_bytes=sum(v.nbytes for v in (*slow.values(),*fast.values())))
        write(out/'training_contract.json',pool.contract);write(out/'visual_initial.json',scene.contract['initial'])
        hook=pool.environment.substep
        def recorded(snapshot):
            nonlocal physics
            hook(snapshot)
            require(scene.gym.refresh_dof_force_tensor(scene.sim) is not False,'Native GPU DOF force refresh unsupported')
            torch.cuda.synchronize(scene.device)
            for key in ('q','qd','target'):fast[key][physics]=snapshot[key].detach().cpu().numpy()
            fast['dof_force'][physics]=dof_force.cpu().numpy()
            fast['contact_force_norm'][physics]=torch.linalg.vector_norm(scene._native_contact_force,dim=-1).cpu().numpy()
            fast['clock'][physics]=pool.environment.clock.cpu().numpy();fast['global_physics_step'][physics]=scene.physics_steps
            physics+=1
        pool.environment.substep=recorded
        zero=torch.zeros(6,39,device=scene.device);capture(zero,0)
        original_z=control.target[rows,native_ids[zs]].clone()
        metadata['initial_target4_rad']=control.target[:,native_ids].cpu().tolist()
        with torch.no_grad():
            for tick in range(TICKS):
                if tick==285:
                    original_z=control.target[rows,native_ids[zs]].clone()
                    metadata['z_probe_start_frame']=ticks
                    metadata['z_probe_start_target4_rad']=control.target[:,native_ids].cpu().tolist()
                    metadata['z_probe_start_q4_rad']=scene.snapshot()['q'][:,native_ids].cpu().tolist()
                action=base.clone();action[:,action_ids]=finger_actions(tick,control.target[:,native_ids],original_z)
                require(bool(torch.isfinite(action).all()) and bool((action.abs()<=1).all()),'Invalid bounded action')
                before=control.target.clone()
                _,reward,cost,terminated,truncated,episodes=pool.step(action)
                ticks+=1;capture(action,segment(tick))
                if ticks==240:
                    goals=control.target.new_tensor([0.,.8,1.56,0.,.8,1.56])
                    goals=goals.clamp(scene.lower[native_ids[xs]],scene.upper[native_ids[xs]])
                    condition_error=float((control.target[rows,native_ids[xs]]-goals).abs().max().item())
                    require(condition_error<=4e-6,'Four-second conditioning target differs')
                expected=(before[:,native_ids]+action[:,action_ids]*(4./60)).clamp(scene.lower[native_ids],scene.upper[native_ids])
                recurrence_error=max(recurrence_error,float((control.target[:,native_ids]-expected).abs().max().item()))
                hold_error=max(hold_error,float((control.target[:,control.active]-held).abs().masked_fill(testing,0).max().item()))
                require(bool(torch.isfinite(reward).all() and torch.isfinite(cost).all()) and not bool(truncated.any()),'Nonfinite/truncated transition')
                if bool((terminated|truncated).any()):ended=episodes;break
                if ticks%60==0:status('stepping')
        require(recurrence_error<=4e-6 and hold_error<=3e-6,'Target recurrence or other-channel hold differs')
        readback_end=read_properties()
    except BaseException as exc:
        error=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());traceback.print_exc()
    finally:
        if pool is not None:
            if hook is not None:pool.environment.substep=hook
            try:pool.close()
            except BaseException as exc:cleanup.append(repr(exc))
    slow={k:v[:frames] for k,v in slow.items()};fast={k:v[:physics] for k,v in fast.items()}
    proof=None
    if frames:
        try:proof=audit_capture(slow,fast,ticks)
        except BaseException as exc:
            if error is None:error=dict(type='CaptureAuditError',message=repr(exc))
    native_path=out/'native240.npz';np.savez_compressed(str(native_path),**fast)
    if metadata is not None:
        metadata.update(native_capture=dict(path=native_path.name,sha256=sha(native_path),samples=physics),
            end_actor_dof_properties=readback_end,conditioning_target_max_error_rad=condition_error,recurrence_max_error_rad=recurrence_error,non_tested_target_hold_error_rad=hold_error)
        ended_ids={e['env_id']:e for e in ended}
        for case in metadata['cases']:
            row=case['env_id'];path=out/('case_%03d.npz'%row)
            arrays={k:(v if k=='global_physics_step' else v[:,row]) for k,v in slow.items()}
            np.savez_compressed(str(path),**arrays)
            case.update(path=path.name,sha256=sha(path),frames=frames,first_episode=ended_ids.get(row),
                outcome=ended_ids[row]['reason'] if row in ended_ids else 'right_censored_at_variant_stop' if ended else 'schedule_complete')
            if ticks>=285:
                j=metadata['tested_native_indices'][case['z_axis_index']]
                start=float(arrays['target'][285,j]);high=metadata['native_upper_rad'][case['z_axis_index']]
                case['z_pulse_readback']=dict(start_target_rad=start,requested_delta_rad=.1,expected_clipped_delta_rad=min(.1,max(0.,high-start)),
                    actual_delta_rad=float(arrays['target'][min(345,ticks),j]-start),full_pulse=ticks>=345,
                    return_error_rad=float(arrays['target'][min(465,ticks),j]-start),full_return=ticks>=465)
                rb=case['z_pulse_readback']
                if ((rb['full_pulse'] and abs(rb['actual_delta_rad']-rb['expected_clipped_delta_rad'])>4e-6) or
                    (rb['full_return'] and abs(rb['return_error_rad'])>4e-6)) and error is None:
                    error=dict(type='PulseReadbackError',message='Clipped pulse/return differs for row'+str(row))
        write(out/'capture_metadata.json',metadata)
    scene_report=pool.scene.diagnostics if pool is not None and pool.scene is not None else None
    changed=[p for p,h in pins.items() if not Path(p).is_file() or sha(p)!=h]
    missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins))
    native_ok=bool(scene_report and scene_report['closed'] and scene_report['physx_use_gpu'] and scene_report['use_gpu_pipeline'] and
        scene_report['num_envs']==6 and scene_report['physics_steps']==physics==ticks*4 and scene_report['simulator_count']==1)
    result=dict(completed=error is None and not(cleanup or changed or missing) and native_ok,schedule_completed=ticks==TICKS,
        actual_control_ticks=ticks,actual_physics_steps=physics,first_ended_episodes=ended,failure=error,cleanup_errors=cleanup,
        changed_inputs=changed,missing_import_pins=missing,gpu_scene=scene_report,capture_audit=proof,PPO_updates=0,model_loaded=False,
        wall_s=time.perf_counter()-started,source_phase=str(source),source_seal_sha256=SEAL_SHA,
        scope='N6 fixed IDs and distinct x-conditioning/contact histories; coordinate/drive diagnosis, not identification of friction/pressure or policy benefit. Early native episode ends remain censored.')
    write(out/'report.json',result);status('report_written');print(json_io.dumps(dict(completed=result['completed'],ticks=ticks),allow_nan=False))
    return 0 if result['completed'] else 1


if __name__=='__main__':sys.exit(main())
