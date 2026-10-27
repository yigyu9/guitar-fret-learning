"""Independent point+wrist teacher with inward-only load guard; no state writes."""
import hashlib
import json
from pathlib import Path
import sys

import current_note_ledger as replay
from current_contact_replay_detailed import detailed_masks


def main():
    import isaacgym
    from isaacgym import gymtorch
    import numpy as np
    import torch
    import guitar_learning.gpu.scene as scene_module
    from guitar_learning.gpu.geometry import apply
    from guitar_learning.gpu.press_surface import project_press_strings
    from guitar_learning.tool.validation import press_acquisition as helpers
    from guitar_learning.tool.validation.thumb_contact_probe import point_jacobian
    out=Path(sys.argv[sys.argv.index('--out')+1])
    ramp=float(sys.argv[sys.argv.index('--ramp-s')+1]) if '--ramp-s' in sys.argv else 2.
    hold=float(sys.argv[sys.argv.index('--hold-s')+1]) if '--hold-s' in sys.argv else 6.
    latest={};records=[];readback={};fixed_samples=None
    original_scene,original_inverse,original_write=scene_module.GpuScene,helpers.trajectory_actions,helpers.write

    def observed_scene(*args,**kwargs):
        scene=original_scene(*args,**kwargs);latest['scene']=scene
        props=scene.gym.get_actor_rigid_shape_properties(scene.envs[0],scene.actors[0][0])
        spans=scene.gym.get_actor_rigid_body_shape_indices(scene.envs[0],scene.actors[0][0])
        fields=('contact_offset','rest_offset','thickness','friction','filter')
        readback.update(human_shapes=[{key:getattr(prop,key) for key in fields} for prop in props],
            human_body_shape_spans=[dict(body=name,start=int(span.start),count=int(span.count)) for name,span in zip(scene.human_bodies,spans)],
            joint_names=scene.names,native_effort_caps=scene.effort_caps.cpu().tolist(),
            native_drive_modes=scene.pd_properties['driveMode'].tolist(),
            interpretation='actual human shape property readback; no properties modified')
        latest['forces']=gymtorch.wrap_tensor(scene.gym.acquire_dof_force_tensor(scene.sim)).view(scene.num_envs,105)
        return scene

    def observed_masks(env,goals,indices):
        latest.update(env=env,goals=goals,indices=indices)
        result=detailed_masks(env,goals,indices)
        scene=latest['scene'];scene.gym.refresh_dof_force_tensor(scene.sim);torch.cuda.synchronize(scene.device)
        result['native_dof_force_sensor']=latest['forces'].clone()
        result['external_effort_submission']=scene.efforts.clone()
        return result

    def teacher_inverse(desired,current,reference,low,high,incremental,max_speed=1.):
        nonlocal fixed_samples
        scene=latest['scene'];now=(scene.physics_steps+4)/240
        if 'env' not in latest or not .5+ramp<now<=.5+ramp+hold:
            return original_inverse(desired,current,reference,low,high,incremental,max_speed=max_speed)
        env,goals,indices=latest['env'],latest['goals'],latest['indices']
        rows=torch.arange(len(goals),device=scene.device)
        finger=env.finger[indices]-1;body=env.pad_indices[finger]
        if fixed_samples is None: fixed_samples=(env.surface_sample[rows,indices]%env.pad_local.shape[1]).clone()
        local=env.pad_local[finger,fixed_samples]
        snapshot=scene.snapshot();state=snapshot['body_state'][rows,body]
        point_world=state[:,:3]+apply(state[:,3:7],local)
        starts,ends=project_press_strings(env.starts,env.ends,env.press_plane)
        start=starts[rows,env.string[indices]];line=ends[rows,env.string[indices]]-start
        a=env.frets[rows,env.fret[indices]-1,1];b=env.frets[rows,env.fret[indices],1]
        center_y=(a+b)/2
        normal=env.press_plane[:3]/torch.linalg.vector_norm(env.press_plane[:3])
        goal_G=start+((center_y-start[:,1])/line[:,1])[:,None]*line-.0005*normal
        goal_world=env.guitar_body[:,:3]+apply(env.guitar_q,goal_G)
        error=goal_world-point_world
        offset=apply(state[:,3:7],local-scene.com[body])
        native=snapshot['jacobian'][rows,body-1]
        jacobian=point_jacobian(native,offset)
        action_names=env.metadata['action_contract']['action_order']
        channels=torch.tensor([[i for i,n in enumerate(action_names) if n.startswith('L_') or
            n.startswith('LH:'+('index','middle','ring','pinky')[g['finger']-1])] for g in goals],device=scene.device)
        native_columns=torch.tensor([[scene.names.index(action_names[i]) for i in row] for row in channels.cpu().tolist()],device=scene.device)
        J=jacobian.gather(2,native_columns[:,None,:].expand(-1,3,-1))
        wrist=env.wrist_index
        wrist_state=snapshot['body_state'][:,wrist]
        wrist_G=env.local_bodies[:,wrist]
        wrist_goal_G=wrist_G.clamp(env.guide['lower_G_m']-.019,env.guide['upper_G_m']+.019)
        wrist_error_world=apply(env.guitar_q,wrist_goal_G-wrist_G)
        wrist_offset=apply(wrist_state[:,3:7],-scene.com[wrist].expand(len(goals),-1))
        wrist_native=snapshot['jacobian'][:,wrist-1]
        wrist_jacobian=point_jacobian(wrist_native,wrist_offset)
        wrist_J=wrist_jacobian.gather(2,native_columns[:,None,:].expand(-1,3,-1))
        outside=(wrist_error_world.abs().amax(-1)>1e-7)
        wrist_J=wrist_J*outside[:,None,None]
        stacked_J=torch.cat((J,wrist_J),dim=1)
        body_force=torch.linalg.vector_norm(snapshot['contact_force'][rows,body],dim=-1)
        high_force=body_force>=2.
        normal_world=apply(env.guitar_q,normal.expand(len(goals),-1))
        normal_error=(error*normal_world).sum(-1)
        removed_inward=torch.where(high_force,normal_error.clamp_max(0),torch.zeros_like(normal_error))
        guarded_error=error-normal_world*removed_inward[:,None]
        stacked_error=torch.cat((guarded_error,wrist_error_world),dim=1)
        identity=torch.eye(6,device=scene.device,dtype=J.dtype)
        delta=(stacked_J.transpose(-1,-2)@torch.linalg.solve(stacked_J@stacked_J.transpose(-1,-2)+1e-5*identity,stacked_error[:,:,None])).squeeze(-1)
        selected=current.gather(1,channels)
        alpha=torch.tensor(env.metadata['action_contract']['smoothing_alpha'],device=scene.device)[channels]
        rate=torch.tensor(env.metadata['action_contract']['rate_rad_s'],device=scene.device)[channels]
        # The requested half-degree step is below both rate limits. The native
        # controller's smoothing scales the arm target step, so constrain that step.
        step=torch.minimum(torch.full_like(selected,.00872664626),rate/60/alpha)
        delta_low=torch.maximum(low[channels]-selected,-step)
        delta_high=torch.minimum(high[channels]-selected,step)
        delta=delta.clamp(delta_low,delta_high)
        normal_J=(normal_world[:,None,:]@J).squeeze(1)*alpha
        before=(normal_J*delta).sum(-1)
        # Project onto the outward half-space inside the existing joint box.
        # This is a first-order target-step guarantee, not a force/penetration bound.
        for _ in range(16):
            inward=(normal_J*delta).sum(-1).clamp_max(0)
            free=((normal_J>0)&(delta<delta_high))|((normal_J<0)&(delta>delta_low))
            direction=normal_J*free
            correction=(-inward/(direction.square().sum(-1).clamp_min(1e-16)))[:,None]*direction
            delta=torch.where(high_force[:,None],(delta+correction).clamp(delta_low,delta_high),delta)
        fallback=high_force&((normal_J*delta).sum(-1)<-1e-9)
        delta=torch.where(fallback[:,None],torch.zeros_like(delta),delta)
        live=~env.tick_failure.any(-1)
        local_time=env._local_time()
        active=live&(local_time>=2.5)&(local_time<=env.end[indices]-env.score_offset)
        delta=torch.where(active[:,None],delta,torch.zeros_like(delta))
        after=(normal_J*delta).sum(-1)
        corrected=desired.clone()
        corrected.scatter_(1,channels,torch.where(active[:,None],selected+delta,desired.gather(1,channels)).clamp(low[channels],high[channels]))
        records.append(dict(time_s=np.asarray(now),sample=fixed_samples.cpu().numpy(),active=active.cpu().numpy(),
            point_error_world_m=error.cpu().numpy(),wrist_error_world_m=wrist_error_world.cpu().numpy(),
            high_force=high_force.cpu().numpy(),removed_inward_error_m=removed_inward.cpu().numpy(),
            predicted_normal_target_step_before_m=before.cpu().numpy(),
            predicted_normal_target_step_after_m=after.cpu().numpy(),normal_guard_fallback=fallback.cpu().numpy(),
            wrist_guide_excess_G_m=env.guide['delta'].cpu().numpy(),requested_delta16_rad=delta.cpu().numpy(),
            corrected_target39_rad=corrected.cpu().numpy(),current_target39_rad=current.cpu().numpy(),
            native_columns16=native_columns.cpu().numpy(),body_force_n=body_force.cpu().numpy()))
        return original_inverse(corrected,current,reference,low,high,incremental,max_speed=max_speed)

    def diagnostic_write(path,value):
        if Path(path).name=='settings.json' and isinstance(value,dict) and value.get('diagnostic_only'):
            value.update(feedback='native_point_wrist_inward_guard_DLS_teacher',
                comparison='independent actual-point closed-loop teacher; not same q trajectory as source-only replay',
                teacher=dict(start='at2.5s after simultaneous2s source-q/B ramp and0.5s reference hold; stop feedback at original selected note end',point='nearest actual eligible pad sample fixed at first correction',
                    goal='original target cell center and press-plane -0.5mm; predicates unchanged',
                    channels='left arm12 plus assigned finger4',
                    wrist_constraint='nearest point in original guidebox expanded19mm; wrist error rows active only outside this target; no guide/termination change',
                    damping=1e-5,max_requested_joint_step_deg=.5,
                    unchanged_finger_speed_cap_rad_s=1.,body_resultant_guard_n=2.,
                    load_guard='at >=2N remove inward pad error; keep tangent/outward pad and wrist tasks; project smoothed target step to non-inward half-space within native action bounds; zero fallback if projection fails',
                    prediction_limit='native instantaneous point Jacobian first-order target-step prediction; no guarantee on actual dynamic penetration',
                    native_J='body-1 index; point offset from COM; existing thumb point_jacobian helper',
                    limitation='diagnostic teacher, no RL/BC and no target or physical-state overwrite'))
        original_write(path,value)

    scene_module.GpuScene=observed_scene;helpers.trajectory_actions=teacher_inverse
    helpers.write=diagnostic_write;replay.sample_masks=observed_masks
    try:
        replay.main()
    finally:
        scene_module.GpuScene=original_scene;helpers.trajectory_actions=original_inverse;helpers.write=original_write
        if records: np.savez_compressed(out/'teacher_trace60.npz',**{k:np.stack([r[k] for r in records]) for k in records[0]})
        if readback:
            readback.update(force_scope='native DOF sensor readback includes drive response; distinct from explicit effort submission0 on POSITION axes',
                wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
            (out/'human_shape_and_force_readback.json').write_text(json.dumps(readback,indent=2)+'\n')


if __name__=='__main__':main()
