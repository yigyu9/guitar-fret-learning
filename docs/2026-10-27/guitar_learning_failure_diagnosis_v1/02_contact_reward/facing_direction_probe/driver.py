"""Docs-only finite direction probe. CPU precommit; GPU only on root handoff."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys
import traceback

from protocol import goals,manifest,schedule,summarize

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
SHORT=ROOT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning'
CHECKPOINT=SHORT/'pilot_incremental_seed7_v2_retry2/train/initial.pt'
REFERENCE=SHORT/'reference_middle_row8_v2.json'
CONTRACT=CHECKPOINT.parent/'training_contract.json'
MASK_SOURCE=HERE.parent/'support/current_contact_replay.py'


def inputs():
    import torch
    from guitar_learning.training.finger_skill_runner import _validate_pins
    from guitar_learning.tool.experiments.short_finger_learning.spec import SCHEMA,read_teacher,read_reference
    payload=torch.load(CHECKPOINT,map_location='cpu',weights_only=False)
    metadata=payload['metadata'];_validate_pins(metadata)
    original=metadata['settings'];spec=original['song']['short_learning']
    if (metadata['schema']!=SCHEMA or payload['updates']!=0 or original['num_envs']!=128 or
            spec['mode']!='incremental' or spec['finger']!=2 or spec['learned_action_indices']!=list(range(21,25))):
        raise ValueError('Own initial incremental middle4/128 checkpoint required')
    if read_teacher(spec['teacher']['input_path'])!=spec['teacher']:
        raise ValueError('Strict original teacher differs')
    reference=read_reference(REFERENCE,spec)
    contract=json.loads(CONTRACT.read_text())
    rigid=json.loads((ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json').read_text())
    names=rigid['logical_body_names'];positions=rigid['logical_position_root_m'];s=spec['view']['source_target']['string']+1
    vector=[b-a for a,b in zip(positions[names.index('G:string%d'%s)],positions[names.index('G:string%d_end'%s)])]
    numerical=goals(contract['native_backend']['control'],spec['teacher'],reference,
        contract['reward']['surface_learning']['press_surface']['plane_G'],vector)
    paths=[CHECKPOINT,REFERENCE,CONTRACT,Path(__file__).resolve(),HERE/'protocol.py',HERE/'README.md',HERE/'verify_cpu.py',MASK_SOURCE,
        Path(spec['teacher']['input_path']),*map(Path,metadata['input_pins']),
        *map(Path,reference['source_evidence']),*map(Path,spec['teacher']['source_evidence'])]
    return metadata,manifest(numerical,spec['view']),paths


def precommit(out):
    from guitar_learning.training.recording import digest,write
    metadata,protocol,paths=inputs()
    value=dict(protocol=protocol,input_pins={str(p):digest(p) for p in paths},
        original_checkpoint_settings=metadata['settings'],gpu_executed=False)
    write(out,value)
    return value


def pool_class():
    import torch
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool
    from guitar_learning.tool.experiments.short_finger_learning.wrist import (
        interpolated_pose,wrist_error_and_jacobian,bounded_wrist_target)
    class DirectionPool(ShortPool):
        def _wrist_feedback(self,desired,fraction):
            # Original bounded feedback math; only per-row finite pose goals differ.
            t=(self.environment.clock.to(torch.float64)+4)/240.
            f,clearance=schedule(t,self.condition,torch=torch)
            goal=self.base_position+clearance.to(desired)[:,None]*self.plane_normal
            position,quaternion=interpolated_pose(self.initial_wrist_position,self.initial_wrist_quaternion,
                goal,self.rotation_goal,f.to(desired))
            self.current_position_goal,self.current_rotation_goal=position,quaternion
            snapshot=self.scene.snapshot();env=self.environment
            error,jacobian=wrist_error_and_jacobian(snapshot,env.wrist_index,env.guitar_index,
                self.scene.com[env.wrist_index],self.controller.active[:12],position,quaternion)
            active=~snapshot['reset_body_snapshot'];previous=self.previous_arm_request.clone()
            arm,correction,delta=bounded_wrist_target(desired[:,:12],self.wrist_correction,
                previous,jacobian,error,active,self.controller.action_low[:12],
                self.controller.action_high[:12],self.controller.rate[self.controller.active[:12]])
            unclipped=desired[:,:12]+self.wrist_correction+delta
            self.wrist_correction.copy_(correction);self.previous_arm_request.copy_(arm)
            desired[:,:12]=arm
            self.last_wrist_feedback=dict(active=active,pose_error_world=error,requested_delta_rad=delta,
                requested_arm_rad=arm,preclip_arm_rad=unclipped,
                arm_clipped=(arm-unclipped).abs()>1e-7,
                requested_arm_delta_rad=arm-previous,position_goal_G_m=position,quaternion_goal_G_xyzw=quaternion)
            return desired
    return DirectionPool


def run(precommit_path,out):
    import isaacgym  # must precede NumPy/Torch
    import numpy as np
    import torch
    from guitar_learning.training.recording import digest,write,project_source_paths
    from guitar_learning.training.finger_skill_runner import _pins
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPolicy
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.tool.validation.press_acquisition import trajectory_actions
    from guitar_learning.gpu.geometry import conjugate,multiply,rotvec
    sealed=json.loads(Path(precommit_path).read_text())
    metadata,protocol,paths=inputs()
    if sealed['protocol']!=protocol or any(not Path(p).is_file() or digest(p)!=v for p,v in sealed['input_pins'].items()):
        raise ValueError('Sealed protocol/source inputs differ')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    settings=copy.deepcopy(metadata['settings']);settings['num_envs']=16
    write(out/'settings.json',settings);write(out/'diagnostic_conditions.json',protocol)
    pins=_pins(settings,out,[*paths,Path(precommit_path).resolve(),out/'diagnostic_conditions.json'])
    write(out/'inputs_before.json',pins)
    module_spec=importlib.util.spec_from_file_location('facing_original_masks',MASK_SOURCE)
    masks_module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(masks_module)
    torch.set_num_threads(1);torch.backends.cuda.matmul.allow_tf32=False
    pool=policy=trainer=None;before=None;failure=None;cleanup_errors=[]
    physics=[];controls=[];episodes={};checks={}
    try:
        pool=pool_class()(settings,out)
        write(out/'original_training_contract.json',pool.contract)
        policy=ShortPolicy(contract=pool.contract,size=settings['size']).to(settings['device'])
        trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
        if pool.environment.approach_gamma!=trainer.config.gamma:
            raise ValueError('Original shaping/PPO gamma differs')
        trainer.load(CHECKPOINT)  # unchanged strict identity; only batch-size override
        before={k:v.detach().clone() for k,v in policy.state_dict().items()}
        n=protocol['numerical'];dtype=pool.teacher_reference.dtype;device=pool.scene.device
        tensor=lambda v:torch.tensor(v,dtype=dtype,device=device)
        if not torch.equal(pool.controller.action_low,tensor(n['action_lower_rad'])) or not torch.equal(pool.controller.action_high,tensor(n['action_upper_rad'])):
            raise ValueError('Sealed original action bounds differ from native controller')
        pool.condition=torch.arange(16,device=device)%8
        pool.base_position=tensor(n['wrist_position_G_m']);pool.plane_normal=tensor(n['plane_normal_G'])
        pool.rotation_goal=tensor(n['wrist_goals_G_xyzw'])[pool.condition]
        finger_goal=tensor(n['finger_goals_rad'])[pool.condition];selected=n['selected_action_indices']
        desired_final=pool.teacher_reference.repeat(16,1);desired_final[:,selected]=finger_goal
        if bool(((desired_final<pool.controller.action_low)|(desired_final>pool.controller.action_high)).any()):
            raise ValueError('Finite diagnostic finger goal exceeds original bounds')
        env=pool.environment;env.set_evaluation(True,full_song=False);pool.reset()
        first=torch.ones(16,dtype=torch.bool,device=device);failed_latched=torch.zeros_like(first)
        indices=torch.full((16,),env.selected_index,dtype=torch.long,device=device)
        qids=pool.controller.active[selected];distal=int(env.pad_indices[1]);initial_target=pool.controller.target.clone().cpu().numpy()
        original_substep=env.substep
        def observed(snapshot):
            result=original_substep(snapshot)
            failed_latched.logical_or_(first&env._control_failures())
            m=masks_module.sample_masks(env,[None]*16,indices)
            current_q=multiply(conjugate(env.guitar_q),env.body[:,env.wrist_index,3:7])
            angular=rotvec(multiply(pool.current_rotation_goal,conjugate(current_q)))
            row=dict(first_attempt=first,failed=failed_latched,clock=env.clock,local_time_s=env._local_time(),source_time_s=env._score_time(),
                q4=snapshot['q'][:,qids],target4=pool.controller.target[:,qids],
                target_arm=pool.controller.target[:,pool.controller.active[:12]],
                distal_pose=snapshot['body_state'][:,distal],guitar_pose=snapshot['body_state'][:,env.guitar_index],
                wrist_pose=snapshot['body_state'][:,env.wrist_index],distal_force_n=snapshot['contact_force'][:,distal],
                candidate=env.candidate[:,env.selected_index],positive=env.contact_loaded_target[:,env.selected_index],
                wrong=env.wrong[:,env.selected_index],position_geometry=env.contact_geometry[:,env.selected_index],
                facing_geometry=env.contact_facing[:,env.selected_index],orientation_error_rad=torch.linalg.vector_norm(angular,dim=-1),
                wrist_goal_G_m=pool.current_position_goal,wrist_goal_G_xyzw=pool.current_rotation_goal,
                physical_failure=env.tick_failure.any(-1),wrist_failure=env.wrist_failure|env.wrist_severe_failure)
            row.update(m)
            physics.append({k:v.detach().cpu().numpy().copy() for k,v in row.items()})
            return result
        env.substep=observed
        with torch.no_grad():
            for tick in range(protocol['view']['duration_ticks']):
                t=(env.clock.to(torch.float64)+4)/240.
                f,_=schedule(t,pool.condition,torch=torch)
                desired=pool.teacher_reference+f.to(dtype)[:,None]*(desired_final-pool.teacher_reference)
                action=trajectory_actions(desired,pool.controller.target[:,pool.controller.active],
                    pool.teacher_reference,pool.controller.action_low,pool.controller.action_high,pool.incremental_mask,max_speed=4.)
                previous={k:v.clone() for k,v in env.episode_reward_terms.items()}
                _,reward,cost,terminated,truncated,finished=pool.step(action)
                row=dict(first_attempt=first,failed=failed_latched,clock=env.clock,reward=reward,cost=cost,
                    requested4=pool.last_policy_action[:,selected],executed4=pool.last_executed_action[:,selected])
                row.update({'wrist_'+k:v for k,v in pool.last_wrist_feedback.items()})
                row.update({'reward_increment_'+k:v-previous[k] for k,v in env.episode_reward_terms.items()})
                row.update({'reward_cumulative_'+k:v for k,v in env.episode_reward_terms.items()})
                controls.append({k:v.detach().cpu().numpy().copy() for k,v in row.items()})
                for episode in finished:
                    i=episode['env_id']
                    if bool(first[i]):
                        episode['selected_raw_note']={k:v[i,env.selected_index].detach().cpu().tolist() for k,v in env.note.items()}
                        episodes[i]=episode;first[i]=False
                if not bool(first.any()):break
                ids=(terminated|truncated).nonzero().flatten()
                if ids.numel():pool.reset(ids)
        if len(episodes)!=16:raise RuntimeError('Missing assigned first attempt(s)')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc())
        raise
    finally:
        write(out/'failure.json',failure)  # preserve original exception before serialization/cleanup audit
        if before is not None:
            checks['model_unchanged']=all(torch.equal(v,before[k]) for k,v in policy.state_dict().items())
            checks['updates_zero']=trainer.updates==0
        if pool:
            try:pool.close()
            except BaseException as error:cleanup_errors.append(str(error))
        a={k:np.stack([r[k] for r in physics]) for k in physics[0]} if physics else {}
        c={k:np.stack([r[k] for r in controls]) for k in controls[0]} if controls else {}
        np.savez_compressed(out/'physics240.npz',**a);np.savez_compressed(out/'control60.npz',**c)
        write(out/'first_attempt_episodes.json',[episodes[i] for i in sorted(episodes)])
        checks.update(all_first_attempts=len(episodes)==16,finite=bool(a) and bool(c) and all(np.isfinite(v).all() for v in [*a.values(),*c.values()]),
            four_substeps=len(physics)==4*len(controls),
            clock=bool(a) and all(np.array_equal(a['clock'][:,i][a['first_attempt'][:,i]],np.arange(1,int(a['first_attempt'][:,i].sum())+1)) for i in range(16)))
        if a and c and pool:
            checks['samepoint_geometry']=bool(np.array_equal(a['position_mask'].any(-1),a['position_geometry']) and np.array_equal(a['facing_mask'].any(-1),a['facing_geometry']) and np.array_equal(a['positive_mask'].any(-1),a['positive']))
            targets=a['target4'][3::4];prior=initial_target[:,qids.cpu().numpy()]
            delta=np.diff(np.concatenate((prior[None],targets)),axis=0);live=a['first_attempt'][3::4]
            checks['finger_rate']=bool((np.abs(delta[live])<=4/60+1e-6).all())
            checks['finger_bounds']=bool(((targets[live]>=np.asarray(protocol['numerical']['action_lower_rad'])[selected]-1e-6)&(targets[live]<=np.asarray(protocol['numerical']['action_upper_rad'])[selected]+1e-6)).all())
            checks['arm_request_rate']=bool((np.abs(c['wrist_requested_arm_delta_rad'][live])<=3/60+1e-6).all())
            arms=a['target_arm'][3::4];arm_ids=pool.controller.active[:12].cpu().numpy()
            arm_delta=np.diff(np.concatenate((initial_target[:,arm_ids][None],arms)),axis=0)
            checks['arm_native_rate']=bool((np.abs(arm_delta[live])<=3/60+1e-6).all())
            low=np.asarray(protocol['numerical']['action_lower_rad'])[:12];high=np.asarray(protocol['numerical']['action_upper_rad'])[:12]
            checks['arm_bounds']=bool(((arms[live]>=low-1e-6)&(arms[live]<=high+1e-6)).all())
        audit=pool.scene.diagnostics if pool else {}
        checks['lifecycle']=bool(audit.get('closed') and audit.get('physx_use_gpu') and audit.get('use_gpu_pipeline') and audit.get('simulator_count')==1 and audit.get('environment_count')==16)
        changed=[p for p,v in pins.items() if not Path(p).is_file() or digest(p)!=v]
        missing=sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        checks['pins']=not changed and not missing
        write(out/'inputs_after.json',dict(verified=checks['pins'],changed_paths=changed,unpinned_project_sources=missing,input_pins=pins))
        rows=summarize(a,episodes,protocol) if a else []
        condition_summary=[dict(condition=k,assigned=2,completed=sum(r['env_id'] in episodes for r in rows if r['condition']==k),
            safe_episodes=sum(r['safe_episode'] for r in rows if r['condition']==k),
            loaded_negative_witnesses=sum(r['loaded_negative_witness'] for r in rows if r['condition']==k),
            safe_episode_witnesses=sum(r['safe_episode_witness'] for r in rows if r['condition']==k),
            stable50ms=sum(r['stable50ms'] for r in rows if r['condition']==k)) for k in range(8)]
        write(out/'report.json',dict(completed=failure is None and not cleanup_errors and all(checks.values()),failure=failure,
            cleanup_errors=cleanup_errors,checks=checks,conditions=protocol,episodes=rows,condition_summary=condition_summary,
            missing_env_ids=sorted(set(range(16))-set(episodes)),scene=audit,updates=0,policy_performance=False,
            base_checkpoint=str(CHECKPOINT),diagnostic_overrides='new declared wrist/finger trajectories outside original training contract; original strict load retained',
            observation_hook='read-only after original environment.substep and native safety; failure and later samples excluded from witness',
            limitations=protocol['limitations']))
        if failure is None and (cleanup_errors or not all(checks.values())):
            raise RuntimeError('Diagnostic audit failed; outputs preserved')


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    cpu=sub.add_parser('precommit');cpu.add_argument('--out',type=Path,required=True)
    gpu=sub.add_parser('run-gpu');gpu.add_argument('--precommit',type=Path,required=True);gpu.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    if args.command=='precommit':precommit(args.out)
    else:run(args.precommit,args.out)


if __name__=='__main__':main()
