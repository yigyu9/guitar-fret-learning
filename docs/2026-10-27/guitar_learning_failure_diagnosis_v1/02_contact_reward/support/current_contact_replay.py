"""Bounded physical reachability replay with current simplified positive/wrong rules.

Static original-note clocks are explicit diagnostic inputs. This path does not
run a song ledger or report song reward/learning success. Wrist failure is a
shadow signal; original physical failures censor each row's first trajectory.
"""
import argparse
import copy
import json
from pathlib import Path
import time

ROOT = Path('/home/ajou/yigyu/3')
BASE = Path(__file__).resolve().parents[1]


def sample_masks(env, goals, indices):
    """Expose same-point conjunctions; compare aggregates with current predicate."""
    import torch
    from guitar_learning.gpu.geometry import apply, conjugate
    from guitar_learning.gpu.press_surface import project_press_strings
    rows = torch.arange(len(goals),device=env.device)
    finger = env.finger[indices]-1
    body = env.body[rows,env.pad_indices[finger]]
    local, local_normals = env.pad_local[finger],env.pad_normals[finger]
    points = apply(conjugate(env.guitar_q[:,None]),
        body[:,None,:3]+apply(body[:,None,3:7],local)-env.guitar_body[:,None,:3])
    normals = apply(conjugate(env.guitar_q[:,None]),apply(body[:,None,3:7],local_normals))
    starts,ends = project_press_strings(env.starts,env.ends,env.press_plane)
    start = starts[rows,env.string[indices]]
    line = ends[rows,env.string[indices]]-start
    unit = env.press_plane[:3]/torch.linalg.vector_norm(env.press_plane[:3])
    height = (points*unit).sum(-1)+env.press_plane[3]/torch.linalg.vector_norm(env.press_plane[:3])
    fraction = ((points-start[:,None])*line[:,None]).sum(-1)/line.square().sum(-1)[:,None]
    lateral2 = (points-height[...,None]*unit-start[:,None]-fraction[...,None]*line[:,None]).square().sum(-1)
    low = torch.minimum(env.frets[rows,env.fret[indices]-1,1],env.frets[rows,env.fret[indices],1])+.002
    high = torch.maximum(env.frets[rows,env.fret[indices]-1,1],env.frets[rows,env.fret[indices],1])-.002
    cell = (points[...,1]>=low[:,None])&(points[...,1]<=high[:,None])
    height_ok = (height>=-.001)&(height<=.003)
    lateral_ok = lateral2<=.003**2
    normal_cos = -(normals*unit).sum(-1)
    facing_ok = normal_cos>=.1
    valid = env.pad_valid[finger]
    position = valid&cell&height_ok&lateral_ok
    facing = position&facing_ok
    loaded = env.surface_body_loaded[rows,indices]
    return dict(points_G=points,normals_G=normals,signed_height_m=height,
        lateral_m=lateral2.sqrt(),normal_cos=normal_cos,valid_mask=valid,
        cell_mask=cell,height_mask=height_ok,lateral_mask=lateral_ok,
        normal_mask=facing_ok,position_mask=position,facing_mask=facing,
        positive_mask=facing&loaded[:,None])


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--geometry',type=Path,required=True)
    p.add_argument('--mode',choices=('fixed','free'),required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--other-fingers',choices=('prepared','B'),default='prepared')
    p.add_argument('--feedback',choices=('none','joint_error_integral'),default='none')
    p.add_argument('--ramp-s',type=float,default=6.)
    p.add_argument('--hold-s',type=float,default=6.)
    p.add_argument('--release-s',type=float,default=2.)
    args=p.parse_args()
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.gpu.scene import GpuScene
    from guitar_learning.gpu.control import BatchedController
    from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment
    from guitar_learning.gpu.environment import FAILURE_REASONS
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.training.start import settings_document
    from guitar_learning.training.recording import active_source_paths
    from guitar_learning.gpu.finger_reward import B_PREPARATION_INPUT_DEGREES,B_PREPARATION_SPREAD_DEGREES
    from guitar_learning.tool.validation.press_acquisition import (
        sha,write,trajectory_actions,diagnostic_streak,integral_tracking_offset)
    torch.set_num_threads(1)
    candidates=json.loads((args.geometry/'candidates.json').read_text())
    selection=json.loads((args.geometry/'targets.json').read_text())
    goals=candidates['goals'];n=len(goals);trace_rows=selection['representative_rows']
    if n not in (16,24) or len(trace_rows)!=6:
        raise ValueError('Precommitted16/24 goals and six trace rows required')
    pins=json.loads((args.geometry/'inputs_before.json').read_text())
    if any(sha(k)!=v for k,v in pins.items()):
        raise ValueError('Geometry sources changed; regenerate candidates')
    pins.update({str(p.resolve()):sha(p) for p in active_source_paths(ROOT/'guitar_learning')})
    pins.update({str(p.resolve()):sha(p) for p in (Path(__file__),args.geometry/'candidates.json',args.geometry/'targets.json')})
    args.out.mkdir(parents=True,exist_ok=False)
    write(args.out/'inputs_before.json',pins)
    settings=settings_document(num_envs=n,size='large',updates=1)
    protocol=dict(diagnostic_only=True,training_success=False,scope='static original-note geometry and wrong v2; no song ledger payments',
        guitar_mode=args.mode,other_fingers=args.other_fingers,feedback=args.feedback,
        initial_hold_s=.5,other_finger_precondition_s=3.,
        precondition='reference control holds3s; B control moves only other fingers to B over3s before identical arm/assigned-finger approach',
        ramp_s=args.ramp_s,hold_s=args.hold_s,release_s=args.release_s,
        finger_speed_cap_rad_s=1.,state_writes='prepared episode reset only; all later targets through finite39-actions',
        wrist='current wristv2 shadow; actual native time; not an alive training episode after shadow failure',
        physical_failure='censor first failed row; bounded hold without reset while other rows finish',
        release='return full active target to prepared reference (other fingers B if explicitly selected); no guaranteed release assumed',
        trace_rows=trace_rows,comparison='nominal same q target path when feedback none; B and integral correction are independent conditions')
    write(args.out/'settings.json',protocol)
    scene=None;trace=[];poses=[];report=None;failure=None;started=time.monotonic()
    try:
        scene=GpuScene(n,'left',device='cuda:0',out=args.out,diagnostic_guitar_mode=args.mode)
        controller=BatchedController(scene,finger_action_mode='incremental')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(controller.contract)
        ids=torch.arange(n,device='cuda:0');indices=torch.tensor([g['source_note_index'] for g in goals],device='cuda:0')
        from guitar_learning.song.task import make_task
        task=make_task(candidates['bundle'])
        selected_onset=torch.tensor([v.onset_s for v in task.targets],device='cuda:0',dtype=torch.float64)
        selected_end=torch.tensor([v.end_s for v in task.targets],device='cuda:0',dtype=torch.float64)
        static_time=(selected_onset[indices]+selected_end[indices])/2
        local_time=torch.zeros(n,device='cuda:0',dtype=torch.float64)

        class StaticSelectedEnvironment(SimplifiedFingerEnvironment):
            def _score_time(self): return static_time
            def _local_time(self): return local_time
            def _reset_scope(self,reset_ids):
                super()._reset_scope(reset_ids)
                self.focus_mask[reset_ids]=False
                self.focus_mask[reset_ids,indices[reset_ids]]=True
                self.recovery_mask[reset_ids]=self.focus_mask[reset_ids]
                self.finger_weights[reset_ids]=self.focus_mask[reset_ids].to(self.finger_weights.dtype)

        env=StaticSelectedEnvironment(metadata,bundle=candidates['bundle'],song=settings['song'],
            skill=settings['finger_skill'],device='cuda:0')
        sample=scene.snapshot();controller.reset(ids,sample);env.set_evaluation(enabled=True,full_song=True);env.reset(ids,sample)
        write(args.out/'training_predicate_contract.json',env.contract)
        write(args.out/'metadata.json',metadata)
        write(args.out/'static_scope.json',dict(source_note_indices=indices.tolist(),
            score_time_s=static_time.tolist(),focus_mask=env.focus_mask.cpu().tolist(),
            original_onset_s=env.onset.cpu().tolist(),original_end_s=env.end.cpu().tolist(),
            scope='one original note per row; fixed audible midpoint; no note-duration/ledger modification'))
        reference=controller.reference[controller.active]
        requested=torch.tensor([g['q_target105'] for g in goals],device='cuda:0')[:,controller.active]
        if not torch.allclose(controller.action_low.cpu(),torch.tensor(candidates['action_lower']),atol=1e-6,rtol=0):
            raise ValueError('CPU/GPU lower action bounds differ')
        if not torch.allclose(controller.action_high.cpu(),torch.tensor(candidates['action_upper']),atol=1e-6,rtol=0):
            raise ValueError('CPU/GPU upper action bounds differ')
        release=reference.expand(n,-1).clone()
        if args.other_fingers=='B':
            for row,g in enumerate(goals):
                for f,name in enumerate(('index','middle','ring','pinky')):
                    if f+1==g['finger']: continue
                    values=dict(zip((name+'1_x',name+'1_z',name+'2',name+'3'),
                        (B_PREPARATION_INPUT_DEGREES[f][0],B_PREPARATION_SPREAD_DEGREES[f],
                         B_PREPARATION_INPUT_DEGREES[f][1],B_PREPARATION_INPUT_DEGREES[f][2])))
                    for suffix,degrees in values.items():
                        col=ACTIVE_NAMES.index('LH:'+suffix);requested[row,col]=release[row,col]=degrees*np.pi/180
        incremental=torch.tensor([v.startswith('LH:') for v in ACTIVE_NAMES],device='cuda:0')
        initial=controller.target[:,controller.active].clone();offset=torch.zeros_like(initial)
        feedback_mask=torch.tensor([[v.startswith('L_') or v.startswith('LH:'+('index','middle','ring','pinky')[g['finger']-1])
                                     for v in ACTIVE_NAMES] for g in goals],device='cuda:0')
        alive=np.ones(n,dtype=bool);previous=env.candidate[ids,indices].cpu().numpy();initial_candidate=previous.copy()
        streak=np.zeros(n);best=np.zeros(n);hold_streak=np.zeros(n);hold_best=np.zeros(n)
        seconds={key:np.zeros((n,4)) for key in ('positive_before_wrong','wrong','candidate','position','facing','loaded')}
        minimum=np.full(n,np.inf);failures=[None]*n;wrist_shadow=[None]*n;mask_mismatch=np.zeros(n,dtype=int)
        maximum_error=np.zeros(n);max_guitar_distance=np.zeros(n);max_guitar_rotation=np.zeros(n)
        last_valid=scene.efforts.clone();trace_ids=torch.tensor(trace_rows,device='cuda:0')
        chosen_joint=torch.tensor([[scene.names.index('LH:'+('index','middle','ring','pinky')[g['finger']-1]+suffix)
            for suffix in ('1_x','1_z','2','3')] for g in goals],device='cuda:0')
        env.tick_failure=torch.zeros(n,len(FAILURE_REASONS),dtype=torch.bool,device='cuda:0');env.tick_cost=torch.zeros(n,device='cuda:0')
        ticks=round((3.5+args.ramp_s+args.hold_s+args.release_s)*60)
        for tick in range(ticks):
            now=(tick+1)/60
            if now<=3.5:
                phase=0;nominal=initial+(release-initial)*min(max((now-.5)/3,0),1)
            elif now<=3.5+args.ramp_s:
                phase=1;nominal=release+(requested-release)*((now-3.5)/args.ramp_s)
            elif now<=3.5+args.ramp_s+args.hold_s: phase=2;nominal=requested
            else:
                phase=3;nominal=requested+(release-requested)*min((now-3.5-args.ramp_s-args.hold_s)/args.release_s,1.)
            live=torch.tensor(alive,device='cuda:0')
            if args.feedback=='joint_error_integral' and phase==2:
                offset=integral_tracking_offset(offset,nominal,scene.q[:,controller.active],
                    controller.action_low,controller.action_high,feedback_mask&live[:,None])
            elif phase!=2: offset.zero_()
            desired=torch.where(live[:,None],nominal+offset,controller.target[:,controller.active])
            actions=trajectory_actions(desired,controller.target[:,controller.active],reference,
                controller.action_low,controller.action_high,incremental,max_speed=1.)
            actions[:,33:]=0;target=controller.targets(actions,sample)
            for sub in range(4):
                efforts=controller.efforts(sample);checks=controller.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):
                    raise RuntimeError('Nonfinite or uncertified support controller')
                undefined=~checks['chest_normal_defined']
                efforts=torch.where(undefined[:,None],last_valid,efforts);last_valid.copy_(efforts)
                sample=scene.step(target,efforts);local_time.fill_(scene.physics_steps/240)
                env._snapshot(sample);env._safety();env.tick_failure[:,-1]|=undefined
                physical=env.tick_failure.cpu().numpy().any(-1);accepted=alive&~physical
                for row in np.flatnonzero(alive&physical):
                    failures[row]=dict(time_s=scene.physics_steps/240,reasons=[v for i,v in enumerate(FAILURE_REASONS) if env.tick_failure[row,i]])
                for row in np.flatnonzero(alive&(env.wrist_failure|env.wrist_severe_failure).cpu().numpy()):
                    if wrist_shadow[row] is None: wrist_shadow[row]=scene.physics_steps/240
                flags=dict(position=env.contact_geometry[ids,indices],facing=env.contact_facing[ids,indices],
                    loaded=env.surface_body_loaded[ids,indices],wrong=env.wrong[ids,indices],candidate=env.candidate[ids,indices])
                flags['positive_before_wrong']=flags['facing']&flags['loaded']
                current=flags['candidate'].cpu().numpy()&accepted
                streak,best=diagnostic_streak(previous,current,streak,best)
                hold_streak,hold_best=diagnostic_streak(previous&(phase==2),current&(phase==2),hold_streak,hold_best)
                previous=current.copy()
                for key,value in flags.items(): seconds[key][:,phase]+=accepted*value.cpu().numpy()/240
                distance=env.surface_distance[ids,indices].cpu().numpy();minimum=np.where(accepted,np.minimum(minimum,distance),minimum)
                error=(scene.q.gather(1,chosen_joint)-target.gather(1,chosen_joint)).abs().amax(-1).cpu().numpy()
                maximum_error=np.where(accepted,np.maximum(maximum_error,error),maximum_error)
                max_guitar_distance=np.where(alive,np.maximum(max_guitar_distance,torch.linalg.vector_norm(env.guitar_delta,dim=-1).cpu().numpy()),max_guitar_distance)
                max_guitar_rotation=np.where(alive,np.maximum(max_guitar_rotation,torch.linalg.vector_norm(env.guitar_rotation,dim=-1).cpu().numpy()),max_guitar_rotation)
                masks=sample_masks(env,goals,indices)
                mismatch=masks['facing_mask'].any(-1)!=flags['facing'];mask_mismatch+=accepted*mismatch.cpu().numpy()
                trace.append(dict(physics_step=np.asarray(scene.physics_steps),phase=np.asarray(phase),
                    valid=accepted[trace_rows],distance=distance[trace_rows],
                    candidate=current[trace_rows],positive_before_wrong=flags['positive_before_wrong'][trace_ids].cpu().numpy(),
                    wrong=flags['wrong'][trace_ids].cpu().numpy(),
                    wrong_source_flags=env.wrong_source_flags[trace_ids,indices[trace_ids]].cpu().numpy(),
                    wrong_fret_min=env.wrong_source_fret_min[trace_ids,indices[trace_ids]].cpu().numpy(),
                    wrong_fret_max=env.wrong_source_fret_max[trace_ids,indices[trace_ids]].cpu().numpy(),
                    q=scene.q[trace_ids].cpu().numpy(),target=target[trace_ids].cpu().numpy(),
                    **{key:value[trace_ids].cpu().numpy() for key,value in masks.items()}))
                alive&=~physical
            poses.append(dict(tick=np.asarray(tick+1),valid=alive[trace_rows].copy(),
                q=scene.q[trace_ids].cpu().numpy(),target=target[trace_ids].cpu().numpy(),
                action=actions[trace_ids].cpu().numpy(),body_state=scene.body_state[trace_ids].cpu().numpy()))
            if tick%60==0: print(args.mode,'tick',tick+1,'alive',int(alive.sum()),'best_s',best.tolist(),flush=True)
            if not alive.any(): break
        report=dict(completed=True,diagnostic_only=True,training_success=False,protocol=protocol,
            control_ticks=tick+1,physics_steps=scene.physics_steps,wall_s=time.monotonic()-started,
            goals=[dict(goal,initial_candidate=bool(initial_candidate[i]),
                minimum_actual_distance_m=float(minimum[i]) if np.isfinite(minimum[i]) else None,
                best_static_contact_streak_s=float(best[i]),best_hold_contact_streak_s=float(hold_best[i]),
                source_geometry_minimum_distance_m=goal['minimum_distance_m'],
                seconds_by_phase={k:seconds[k][i].tolist() for k in seconds},
                phase_names=['initial','ramp','hold','release'],failure=failures[i],
                wrist_shadow_failure_time_s=wrist_shadow[i],same_sample_predicate_mismatch_count=int(mask_mismatch[i]),
                maximum_assigned_finger_tracking_error_rad=float(maximum_error[i])) for i,goal in enumerate(goals)])
        for i,row in enumerate(report['goals']):
            row.update(maximum_guitar_displacement_m=float(max_guitar_distance[i]),
                       maximum_guitar_rotation_rad=float(max_guitar_rotation[i]))
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        for name,rows in (('trace240.npz',trace),('poses60.npz',poses)):
            if rows: np.savez_compressed(args.out/name,**{k:np.stack([v[k] for v in rows]) for k in rows[0]})
        if scene: scene.close()
        changed=[p for p,v in pins.items() if sha(p)!=v]
        audit=scene.diagnostics if scene else None
        report=dict(report or {},completed=bool(report and not failure and not changed and audit and audit['closed']),
            failure=failure,changed_inputs=changed,scene=audit,
            current_environment='SimplifiedFingerEnvironment positive/wrong v2; static clocks/selected scope diagnostic overrides',
            no_song_ledger_payments=True,wall_s=time.monotonic()-started)
        write(args.out/'report.json',report)
    if not report['completed']: raise RuntimeError('Static replay audit failed')
    print('COMPLETE',args.mode,args.out,flush=True)


if __name__=='__main__': main()
