"""Only prefix environment/policy, current-goal guard and three-note evaluation."""
import copy
import importlib.util
import math
from pathlib import Path
import sys
import numpy as np
import torch
from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.gpu.simplified_finger_environment import SimplifiedFingerEnvironment
from guitar_learning.skills.finger_skill_policy import FingerSkillPolicy, FINGERS
from guitar_learning.song.finger_phrases import BalancedPhraseSampler
from guitar_learning.tool.experiments.short_finger_learning import runner,runtime

HERE=Path(__file__).resolve().parent
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);sys.modules[name]=v;spec.loader.exec_module(v);return v
prefix=module('learning_original_prefix',HERE.parent/'index_prefix_4_7_8_v1/prefix_runtime.py')
timing=module('learning_original_staged_timing',HERE.parent/'index_prefix_release_transfer_v1/schedule.py')
guard=module('learning_original_DIP_filter',HERE.parent/'index_candidate_dip_guard_v1/probe.py')
SCHEMA='diagnostic.index_prefix_learning.v1'
INDICES=(4,7,8)
SINGLE_COMPACT=runner.compact_episode


def guard_descriptor():
    return dict(schema='diagnostic.current_goal_candidate_DIP.v1',source_indices=list(INDICES),
        current_goal='earliest selected target with precontrol score_time<original end; none after8; achieved/released flags ignored',
        eligibility='current candidate & ~wrong & valid current episode & finite & ~reset & ~prior failure',
        operation='LH:index3 positive original target increment only held at old target; negative/zero and other104 unchanged; no backlog',
        training='every episode incl preparation from first tick; no permanent first-attempt mask',
        control_hz=60,physics_hz=240)


class PrefixLearningEnvironment(prefix.PrefixEnvironment):
    def __init__(self,metadata,*,bundle,song,skill,device='cuda:0',hand='left'):
        short=copy.deepcopy(song['short_learning'])
        if short['schema']!=SCHEMA or short['mode']!='incremental' or short['candidate_dip_guard']!=guard_descriptor():raise ValueError('Exact prefix learning schema/control required')
        SimplifiedFingerEnvironment.__init__(self,metadata,bundle=bundle,song=song,skill=skill,device=device,hand=hand)
        view,self.catalog=prefix.view_and_catalog(self.task)
        if view!=short['view'] or short['learned_action_indices']!=list(runtime.selected_actions(1)):raise ValueError('Original3-note view/F4 mismatch')
        self.selected_indices=INDICES;self.sampler=BalancedPhraseSampler(self.catalog)
        self.contract['task']['short_learning']=short
        self.contract['task']['finger_skill'].update(scope='fixed_source_subset',catalog_sha256=self.catalog.fingerprint,
            reset_selection='same original notes4/7/8 on every reset',planned_transitions=None,full_song_after=None)
        self.contract['diagnostics']['short_learning']=dict(scope='conditional3note F4 policy; reference N only in declared noNN reference control')
        self.contract['action']['target_contract']['diagnostic_candidate_dip_guard']=guard_descriptor()


class PrefixPolicy(FingerSkillPolicy):
    schema='diagnostic.index_prefix_policy.v1'
    def __init__(self,*,contract,size='large',fresh=False):
        short=contract['task']['short_learning']
        if (short['schema']!=SCHEMA or short['finger']!=1 or short['learned_action_indices']!=list(runtime.selected_actions(1)) or
            short['candidate_dip_guard']!=guard_descriptor() or contract['action']['target_contract'].get('diagnostic_candidate_dip_guard')!=guard_descriptor() or
            short['ablation']!=guard.B.variants.descriptor('B_zero_cost_head')):raise ValueError('Exact new prefix policy/control/initialization contract required')
        super().__init__(561,size=size,contract=contract,phase='J',exploration='independent')
        self.finger=1;self.architecture['learned_action_indices']=short['learned_action_indices']
        self.architecture['likelihood']='selected_four_physical_tanh_latents_only'
        self.support_encoder.requires_grad_(False);self.support_head.requires_grad_(False);self.support_log_std.requires_grad_(False)
        for finger,head in self.finger_heads.items():head.requires_grad_(finger==FINGERS[0])
        with torch.no_grad():
            self.finger_log_std.fill_(math.log(short['initial_std']))
            if fresh:self.cost_critic.weight.zero_();self.cost_critic.bias.zero_()
    def _active_mask(self):
        mask=torch.zeros(39,dtype=torch.bool,device=self.support_log_std.device);mask[list(runtime.selected_actions(1))]=True;return mask


def current_goal(score,end):
    available=score[:,None]<end[None]
    column=available.long().argmax(-1)
    return column,available.any(-1)


class LearningPool(prefix.PrefixPool):
    environment_class_override=PrefixLearningEnvironment
    record_first_controls=False
    def __init__(self,settings,out):
        super().__init__(settings,out)
        try:
            self.first=torch.ones(self.num_envs,dtype=torch.bool,device=self.scene.device)
            self.dip=self.scene.names.index('LH:index3');self.ai=self.controller.active.tolist().index(self.dip)
            self.native_targets=self.controller.targets;self.controller.targets=self.targets
            self.guard_rows=[];self.guard_counts=torch.zeros(4,3,dtype=torch.long,device=self.scene.device)
            self.obs_index=self.contract['observation']['fields'].index('target_error.LH:index3');self.pending=None
        except BaseException:
            try:self.close()
            except BaseException as error:self.guard_cleanup_error=dict(type=type(error).__name__,message=str(error))
            raise
    def targets(self,action,snapshot):
        env=self.environment;score=env._score_time();col,present=current_goal(score,env.end[list(INDICES)])
        index=col.new_tensor(INDICES)[col];rows=torch.arange(self.num_envs,device=self.scene.device)
        live=torch.ones_like(present)  # All current episodes, including episodes after reset.
        failed=env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure
        target,self.pending=guard.target_filter(self.controller,self.native_targets,action,snapshot,live,
            env.candidate[rows,index]&present,env.wrong[rows,index],failed,self.dip,self.ai,True)
        self.pending.update(first_attempt=self.first.clone(),current_goal=torch.where(present,index,-torch.ones_like(index)),start_clock=env.clock.clone())
        return target
    def step(self,action):
        self.pending=None;result=super().step(action);r=self.pending
        if r is None:raise RuntimeError('Missing current-goal DIP audit')
        env=self.environment;r['clock']=env.clock.clone();r['post_failure']=(env.failure.any(-1)|env.wrist_failure|env.wrist_severe_failure).clone()
        r['submit_error_rad']=(self.scene.target[:,self.dip]-r['final_target_rad']).abs()
        expected=((self.scene.target[:,self.dip]-self.scene.q[:,self.dip])/env.scales[self.obs_index]).clamp(-10,10)
        r['observation_error']=(result[0]['state'][:,self.obs_index]-expected).abs()
        valid=r['finite'];assert bool(((r['submit_error_rad'][valid]==0)&(r['observation_error'][valid]==0)).all())
        for j,i in enumerate((*INDICES,-1)):
            mask=r['current_goal']==i
            self.guard_counts[j]+=torch.stack((mask.sum(),(mask&r['blocked']).sum(),(mask&(r['raw_target_rad']<r['old_target_rad'])).sum()))
        if self.record_first_controls:
            self.guard_rows.append({k:np.where(r['first_attempt'].cpu().numpy(),v.detach().cpu().numpy(),np.zeros_like(v.detach().cpu().numpy())) for k,v in r.items()})
            assert len(self.guard_rows)<=self.spec['view']['duration_ticks']
        for row in result[-1]:self.first[row['env_id']]=False
        return result


def compact_episode(row,spec):
    # The frozen3note helper calls runner.compact_episode for each source note.
    previous=runner.compact_episode;runner.compact_episode=SINGLE_COMPACT
    try:return prefix.compact_episode(row,spec)
    finally:runner.compact_episode=previous


def reference_action(pool,reference):
    short=pool.spec;fraction=((pool.environment._local_time()+1/60)/reference['ramp_s']).clamp(0,1).to(pool.teacher_reference)
    goal=pool.teacher_reference.clone()
    for name,value in reference['selected_targets_rad'].items():goal[ACTIVE_NAMES.index(name)]=value
    desired=pool.teacher_reference+fraction[:,None]*(goal-pool.teacher_reference)
    schedule=short['reference_release_schedule'];ids=short['learned_action_indices']
    weight=timing.negative_weight(pool.environment._local_time()+1/60,short['view']).to(desired)
    desired[:,ids]+=weight[:,None]*(desired.new_tensor(schedule['negative_selected_rad'])-desired.new_tensor(schedule['reference_selected_rad']))
    return runtime.trajectory_actions(desired,pool.controller.target[:,pool.controller.active],pool.teacher_reference,
        pool.controller.action_low,pool.controller.action_high,pool.incremental_mask,max_speed=4.)


@torch.no_grad()
def evaluate(pool,policy,spec,args,out):
    if pool.num_envs!=128 or args.episodes!=128 or args.control not in ('policy','reference','zero','random'):raise ValueError('Fixed128 first-attempt controls required')
    reference=runner.read_reference(args.reference,spec) if args.control=='reference' else None
    counts=[0]*128;rows=[];trace=[];observation=pool.observation;pool.environment.set_evaluation(True,full_song=False)
    for _ in range(spec['view']['duration_ticks']):
        action=policy.act(*(observation[k] for k in runner.FIELDS),deterministic=args.control!='random')['action']
        if args.control=='zero':action.zero_()
        elif reference is not None:action=reference_action(pool,reference)
        observation,_,_,terminated,truncated,finished=pool.step(action)
        if counts[0]==0:
            env,scene=pool.environment,pool.scene;ids=list(INDICES)
            t=dict(time_s=float(env._local_time()[0]),source_time_s=float(env._score_time()[0]),policy_action=pool.last_policy_action[0].cpu().numpy().copy(),
                executed_action=pool.last_executed_action[0].cpu().numpy().copy(),q=scene.q[0].cpu().numpy().copy(),target=scene.target[0].cpu().numpy().copy(),
                body_state=scene.body_state[0].cpu().numpy().copy(),net_body_force_n=scene.snapshot()['contact_force'][0].cpu().numpy().copy(),
                candidate=env.candidate[0,ids].cpu().numpy().copy(),wrong=env.wrong[0,ids].cpu().numpy().copy(),surface_distance_m=env.surface_distance[0,ids].cpu().numpy().copy(),
                surface_height_m=env.surface_height[0,ids].cpu().numpy().copy(),released=env.note['released'][0,ids].cpu().numpy().copy(),release_s=env.note['release_s'][0,ids].cpu().numpy().copy())
            for name,value in pool.last_wrist_feedback.items():t['wrist_'+name]=value[0].cpu().numpy().copy()
            trace.append(t)
        for row in finished:
            i=row['env_id']
            if counts[i]==0:rows.append(compact_episode(row,spec));counts[i]+=1
        if counts==[1]*128:break
        ids=(terminated|truncated).nonzero().flatten()
        if ids.numel():observation=pool.reset(ids)[0]
    if counts!=[1]*128:raise RuntimeError('Prefix first-attempt quotas incomplete')
    runner.write(out/'evaluation.json',dict(schema=SCHEMA,condition=args.control,policy_performance=args.control=='policy',assigned_quotas=[1]*128,
        summary=runner.summary(rows),episodes=rows,scope=spec['result_scope']))
    if trace:
        np.savez_compressed(out/'trace_env0_episode0.npz',**{k:np.asarray([r[k] for r in trace]) for k in trace[0]})
        runner.write(out/'trace_metadata.json',dict(scope='env0 first attempt60Hz incl failure endpoint;3note columns; other127 detailedforce absent',
            joint_names=pool.scene.names,body_names=pool.scene.metadata['body_names'],source_indices=list(INDICES),wrist_control=spec['wrist_control']))
