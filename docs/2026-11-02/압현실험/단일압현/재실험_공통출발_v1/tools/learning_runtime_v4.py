"""공통 출발 운반 뒤 손가락4축만 학습하는 독립 실행기.

배치의 정책 에피소드가 모두 끝난 뒤에만 실제 운반을 실행한다. 먼저 끝난
행은 유한 유지하며 valid=false로 제외한다. 운반과 대기는 PPO 결정이 아니다.
원문 runtime와 활성 학습 코드는 수정하지 않는다.
"""
if __name__=='__main__':import isaacgym
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import random
import sys
import time
from contextlib import contextmanager
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import numpy as np
import torch

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

transport=load_module('single18_transport_sealed',HERE/'transport_runtime.py')
from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.training import rollout, finger_skill_runner as runner, ppo
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.gpu.environment import TensorSongEnvironment, FAILURE_REASONS
from guitar_learning.gpu.control import apply,conjugate,multiply
from guitar_learning.tool.validation.press_acquisition import trajectory_actions
from guitar_learning.tool.experiments.short_finger_learning.wrist import (
    wrist_error_and_jacobian,bounded_wrist_target,_wrist_position_groups)
from guitar_learning.portability import localize,portable
from guitar_learning.training.training_log_io import dumps as log_dumps,write as log_write
SCHEMA='guitar_learning.single18.transported_learning.v1'
POLICY_SCHEMA='guitar_learning.single18.transported_policy.v1'
ORIGINAL_POOL=rollout.GpuPool
FIELDS=rollout.FIELDS


@contextmanager
def configuration(catalog,provenance,case,evidence):
    """현행 E4 API에 새 운반 계약을 연결한다. 과거 docs Python은 import하지 않는다."""
    catalog,provenance,evidence=map(lambda p:Path(p).resolve(),(catalog,provenance,evidence))
    checked=json.loads(evidence.read_text());document,row,_=transport.load_inputs(catalog,provenance,case)
    if (not checked.get('completed') or not checked.get('transport_ready') or checked.get('condition')!='C'
            or checked.get('case')!=case or checked.get('candidate_sha256')!=transport.row_identity(row)
            or checked.get('runtime_sha256')!=transport.digest(HERE/'transport_runtime.py')):
        raise ValueError('동일 후보의 엄격한 C운반 통과 근거 필요')
    old_load,old_schema,old_policy=natural.load_configuration,natural.SCHEMA,natural.NaturalPolicy.schema
    def load(song,condition='E4',distribution='v9',axes='goal4'):
        if (song,condition,distribution,axes)!=(row['song'],'E4','v9','goal4'):
            raise ValueError('같은 E4/v9/goal4 공통 출발 목표만 허용')
        transport.load_inputs(catalog,provenance,case)
        if transport.digest(evidence)!=evidence_sha:raise ValueError('운반 근거 변경')
        finger=row['finger'] if isinstance(row['finger'],str) else natural.FINGERS[row['finger']-1]
        return dict(schema=SCHEMA,condition='E4',distribution='v9',axes='goal4',song=song,finger=finger,
            geometry=str(catalog),geometry_sha256=transport.digest(catalog),provenance_sha256=transport.digest(provenance),
            active_axes=natural.active_axes('goal4',finger),observation_extra_fields=natural.EXTRA_FIELDS,
            finger_initial_std=.15,finger_std_floor=.10,support_initial_std=math.exp(-3),phase_arm_support=False,
            inactive_execution='transport teacher arm12; non-goal fingers finite hold; no phase relatch',
            initial_distribution=dict(v9_fraction=1.,rng='deterministic common v9; official Torch CPU sampler/checkpoint RNG unchanged'),
            readiness=dict(wrist_axis_excess_m=.010,wrist_continuous_s=.10,tangent_m=.010,
                height_m=[.002,.020],normal_cos=.1,aligned_continuous_s=.10),
            lr=dict(floor=7.5e-6,cap=3e-5,retry_factor=.5,stable_updates=10,stable_kl_below=.005,recovery_factor=1.25),
            likelihood='saved active axes Gaussian tanh latent; phase never blocks active actions',
            single18=dict(case=case,runtime_sha256=transport.digest(__file__),provenance=str(provenance),planned_updates=100,
                validation='independently verified C transport'),
            transport=dict(schema=SCHEMA,case=case,evidence=str(evidence),evidence_sha256=evidence_sha,
                runtime_sha256=transport.digest(__file__),preparation='batch synchronous physical transport; per-env failures retained in start denominator, only ready rows learn; all-failed abort',
                waiting='terminal rows bounded hold, reward and note ledger frozen, invalid PPO decisions',
                clock_mapping='native episode step stays continuous; subtract recorded preparation offset in policy snapshot view; waiting clock continues but no new policy decisions or episode records',
                handoff='preparation feedback ends; hold the actual settled wrist pose in guitar frame, not the original CPU full pose'))
    evidence_sha=transport.digest(evidence)
    natural.load_configuration,natural.SCHEMA,natural.NaturalPolicy.schema=load,SCHEMA,POLICY_SCHEMA
    try:yield load(row['song']),row
    finally:natural.load_configuration,natural.SCHEMA,natural.NaturalPolicy.schema=old_load,old_schema,old_policy


def build_settings(config,row,*,num_envs=64,seed=7):
    from guitar_learning.training.launch import settings_document
    from guitar_learning.song.task import make_task
    settings=settings_document(song='virtual_finger_v9_middle_s3_f6',size='large',num_envs=num_envs,
        horizon=32,updates=100,seed=seed,checkpoint_every=10,device='cuda:0',physics='gpu')
    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
    if len(task.targets)!=1 or (task.targets[0].string,task.targets[0].fret,task.targets[0].finger)!=(row['string'],row['fret'],row['finger_id']):
        raise ValueError('단일 목표 bundle/catalog 불일치')
    settings['song_training'].update(song_id=row['song'],bundle=str(Path(row['bundle']).resolve()),
        target_count=1,control_ticks=task.provenance['song']['control_ticks'],episode_duration_s=task.duration_s)
    settings['phrase_events']=task.provenance['song']['source_event_count']
    settings['natural_press']=config;settings['ppo']['retry_lr_factor']=.5
    settings['simple_start']['initial_pose']=SCHEMA+':common_transport'
    return settings


def preparation_failure_mask(physical,severe,ordinary,contact,wrong):
    """기존 행별 실패 임계값과 준비 중 무압현 조건을 그대로 적용한다."""
    return physical.any(-1)|(severe>=.10-1e-9)|(ordinary>=1.5-1e-9)|contact|wrong


def policy_snapshot_view(environment,snapshot):
    """native 물리 시계를 검증하고 준비 길이만 뺀 정책 관측 view를 만든다."""
    native=snapshot['physics_step']
    if not torch.equal(native,environment.last_native_policy_step+1):
        raise RuntimeError('native 물리 끝점 연속성 위반')
    translated=native-environment.preparation_physics_offset
    if not torch.equal(translated,environment.clock+1):
        raise RuntimeError('물리→정책 시계 offset 불일치')
    environment.last_native_policy_step=native.clone()
    result=dict(snapshot);result['physics_step']=translated
    return result


class LearningPool(ORIGINAL_POOL):
    """전체 배치 경계에서만 공통 reset·운반을 수행한다."""
    def _create_scene(self,settings,out):return GpuScene(self.num_envs,'left',device=settings['device'],out=out)

    def __init__(self,settings,out):
        self.config=settings['natural_press'];self.row=natural.catalog_goal(self.config)[1]
        self.catalog=natural.catalog_goal(self.config)[0]
        self.frames=transport.make_frames(self.catalog,self.row)
        self.waiting=None;self.needs_preparation=True;self.preparation_records=[];self.frame_callback=None
        config=self.config
        class Environment(natural.NaturalEnvironment):
            natural_press=config
            natural_preparation=dict(schema='guitar_learning.natural_preparation.v3',condition='E4')
            policy_mask=None
            def _episode(env,index,failed):
                result=super(Environment,env)._episode(index,failed)
                result['transport_initialization']=dict(physical_reset='common_v9',
                    policy_initial='native_arrived_after_transport',
                    preparation_physics_steps=int(env.preparation_physics_offset[index]))
                return result
            def substep(env,snapshot):
                return super(Environment,env).substep(policy_snapshot_view(env,snapshot))
            def begin_control(env,actions):
                finished=env.finished.clone();env.finished.zero_()
                try:return super(Environment,env).begin_control(actions)
                finally:env.finished.copy_(finished)
            def _reward_components(env,components):
                result=super(Environment,env)._reward_components(components)
                if env.policy_mask is not None:
                    result={key:value*env.policy_mask for key,value in result.items()}
                return result
        self.environment_class_override=Environment
        super().__init__(settings,out)
        self.groups=_wrist_position_groups(self.controller,self.scene.body_names,self.controller.active[:12])
        self.correction=torch.zeros(self.num_envs,12,device=self.scene.device)
        self.previous_request=self.controller.target[:,self.controller.active[:12]].clone()
        self.contract['transport']=copy.deepcopy(self.config['transport'])
        self.environment.applied_action_getter=lambda:natural.normalized_action(
            self.controller.target[:,self.controller.active],self.controller.reference[self.controller.active],
            self.controller.action_low,self.controller.action_high)

    def reset(self,indices=None):
        ids=(torch.arange(self.num_envs,device=self.scene.device) if indices is None else torch.as_tensor(indices,device=self.scene.device,dtype=torch.long))
        if self.waiting is not None:
            self.waiting[ids]=True
            if not bool(self.waiting.all()):return self.observation,[]
        self.waiting=torch.zeros(self.num_envs,dtype=torch.bool,device=self.scene.device)
        self.needs_preparation=True
        result=ORIGINAL_POOL.reset(self,torch.arange(self.num_envs,device=self.scene.device))
        self.controller.target[:,self.controller.active]=self.scene.snapshot()['q'][:,self.controller.active]
        self.environment.policy_mask=torch.zeros_like(self.waiting)
        return result

    def wrist_request(self,desired,goal,rotation,snapshot):
        error,jacobian=wrist_error_and_jacobian(snapshot,self.environment.wrist_index,self.environment.guitar_index,
            self.scene.com[self.environment.wrist_index],self.groups,goal,rotation)
        arm,self.correction,_,_=bounded_wrist_target(desired[:,:12],self.correction,self.previous_request,
            snapshot['q'][:,self.controller.active[:12]],jacobian,error,
            ~snapshot['reset_body_snapshot'] & ~getattr(self,'feedback_disabled',torch.zeros_like(snapshot['reset_body_snapshot'])),
            self.controller.action_low[:12],self.controller.action_high[:12],self.controller.rate[self.controller.active[:12]])
        disabled=getattr(self,'feedback_disabled',torch.zeros(len(arm),dtype=torch.bool,device=arm.device))
        arm[disabled]=desired[disabled,:12];self.correction[disabled]=0
        self.previous_request=arm.clone();desired[:,:12]=arm
        return desired

    @torch.no_grad()
    def prepare(self):
        if not self.needs_preparation:return
        if bool(self.waiting.any()):raise RuntimeError('진행중 정책을 둔 운반 금지')
        env,scene,control=self.environment,self.scene,self.controller
        snapshot=scene.snapshot();initial_reset_calls=scene.reset_calls
        refs=(env.reference_guitar.clone(),env.reference_feet.clone())
        self.correction.zero_();self.previous_request=control.target[:,control.active[:12]].clone()
        stable=torch.zeros(self.num_envs,device=scene.device);severe=torch.zeros_like(stable);ordinary=torch.zeros_like(stable)
        ordinary_active=torch.zeros(self.num_envs,dtype=torch.bool,device=scene.device)
        contact=torch.zeros_like(ordinary_active);wrong=torch.zeros_like(contact);failed=torch.zeros_like(contact)
        self.feedback_disabled=failed.clone()
        first_failures=[None]*self.num_envs
        half=(env.guide['upper_G_m']-env.guide['lower_G_m'])/2
        previous_wrist=env.local_bodies[:,env.wrist_index].clone();last_valid=scene.efforts.clone()
        env.tick_failure=torch.zeros(self.num_envs,len(FAILURE_REASONS),dtype=torch.bool,device=scene.device)
        env.tick_cost=torch.zeros(self.num_envs,device=scene.device)
        left_ids=[i for i,name in enumerate(scene.body_names) if name.startswith(('human/LH:','human/L_'))]
        count=math.ceil((self.frames[-1]['time_s']+2)*60);trace=[]
        def mark_failure(mask,kind,elapsed):
            new=mask&~failed
            for identity in new.nonzero().flatten().cpu().tolist():
                body=snapshot['body_state'][identity]
                first_failures[identity]=dict(env_id=identity,kind=kind,time_s=elapsed,
                    physical_reasons=[name for name,flag in zip(FAILURE_REASONS,env.tick_failure[identity].cpu().tolist()) if flag],
                    guitar_displacement_m=float(torch.linalg.vector_norm(env.guitar_delta[identity])),
                    guitar_rotation_rad=float(torch.linalg.vector_norm(env.guitar_rotation[identity])),
                    maximum_foot_displacement_m=float(torch.linalg.vector_norm(env.foot_delta[identity],dim=-1).max()),
                    maximum_qd_rad_s=float(snapshot['qd'][identity].abs().max()),
                    q105=snapshot['q'][identity].cpu().tolist(),target105=control.target[identity].cpu().tolist(),
                    guitar_body13=body[env.guitar_index].cpu().tolist(),wrist_body13=body[env.wrist_index].cpu().tolist(),
                    left_body_names=[scene.body_names[i] for i in left_ids],
                    left_body_contact_force=snapshot['contact_force'][identity,left_ids].cpu().tolist(),
                    candidate=bool(contact[identity]),wrong=bool(wrong[identity]),
                    severe_outside_s=float(severe[identity]),ordinary_outside_s=float(ordinary[identity]))
            failed.logical_or_(mask)
            self.feedback_disabled=failed.clone()
        for tick in range(count):
            now=(tick+1)/60
            q,goal,rotation,_=transport.sample_frames(self.frames,now,scene.device)
            desired=q[control.active].expand(self.num_envs,-1).clone()
            desired[failed]=control.target[failed][:,control.active]
            goal=goal.expand(self.num_envs,-1);rotation=rotation.expand(self.num_envs,-1)
            desired=self.wrist_request(desired,goal,rotation,snapshot)
            action=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
            target=control.targets(action,snapshot)
            for sub in range(4):
                efforts=control.efforts(snapshot);checks=control.diagnostics
                uncertified=~(checks['finite']&checks['chest_witness_certified'])
                invalid=~checks['chest_normal_defined']
                # 실패 행은 재배치하지 않고 마지막 인증된 유한 힘·제한 목표를 유지한다.
                effort_disabled=failed|uncertified|invalid
                efforts=torch.where(effort_disabled[:,None],last_valid,efforts)
                last_valid=torch.where(effort_disabled[:,None],last_valid,efforts)
                snapshot=scene.step(target,efforts);env._snapshot(snapshot);TensorSongEnvironment._safety(env)
                env.tick_failure[:,-1]|=invalid|uncertified
                contact|=env.candidate[:,0];wrong|=env.wrong[:,0]
                excess=((env.local_bodies[:,env.wrist_index]-goal).abs()-half).clamp_min(0).amax(-1)
                severe=torch.where(excess>=.1,severe+1/240.,0.)
                elapsed=(tick*4+sub+1)/240.
                ordinary_active=(elapsed>=3.)&((ordinary_active|(excess>.03))&(excess>.02))
                ordinary=torch.where(ordinary_active,torch.where(excess>.03,ordinary+1/240.,(ordinary-1/240.).clamp_min(0)),0.)
                bad=preparation_failure_mask(env.tick_failure,severe,ordinary,contact,wrong)
                mark_failure(bad,'physical_wrist_or_contact_failure',elapsed)
            speed=torch.linalg.vector_norm(env.local_bodies[:,env.wrist_index]-previous_wrist,dim=-1)*60
            previous_wrist=env.local_bodies[:,env.wrist_index].clone()
            ready=((env.surface_height[:,0]>=.005)&(env.surface_height[:,0]<=.015)&
                (torch.linalg.vector_norm(env.surface_delta[:,0,:2],dim=-1)<=.005)&(env.surface_alignment[:,0]>=.1)&
                (speed<=.05)&~failed)
            stable=torch.where(ready&(now>=self.frames[-1]['time_s']),stable+1/60.,0.)
            ready=stable>=.5-1e-9
            trace.append(dict(tick=tick+1,stable_s=stable.cpu().tolist(),contact=contact.cpu().tolist(),wrong=wrong.cpu().tolist(),
                height_m=env.surface_height[:,0].cpu().tolist(),physical_failure=env.tick_failure.cpu().tolist(),
                guitar_displacement_m=torch.linalg.vector_norm(env.guitar_delta,dim=-1).cpu().tolist(),
                guitar_rotation_rad=torch.linalg.vector_norm(env.guitar_rotation,dim=-1).cpu().tolist(),
                maximum_foot_displacement_m=torch.linalg.vector_norm(env.foot_delta,dim=-1).amax(-1).cpu().tolist(),
                maximum_qd_rad_s=snapshot['qd'].abs().amax(-1).cpu().tolist(),failed=failed.cpu().tolist()))
            if self.frame_callback:self.frame_callback('transport',None)
            if bool((ready|failed).all()):break
        ready=(stable>=.5-1e-9)&~failed
        mark_failure(~ready&~failed,'preparation_timeout',len(trace)/60.)
        passed=bool(ready.any())
        record=dict(batch=len(self.preparation_records),passed=passed,all_ready=bool(ready.all()),environments=self.num_envs,
            start_denominator=self.num_envs,ready_count=int(ready.sum()),failed_count=int(failed.sum()),
            ready=ready.cpu().tolist(),failed=failed.cpu().tolist(),first_failures=first_failures,
            ticks=len(trace),raw_physics_steps=len(trace)*4,trace=trace,policy_decisions=0,
            reset_calls_before=initial_reset_calls,reset_calls_after=scene.reset_calls)
        self.preparation_records.append(record)
        with (Path(self.out)/'preparation.jsonl').open('a') as stream:stream.write(log_dumps(record,allow_nan=False)+'\n')
        if scene.reset_calls!=initial_reset_calls or int(env.clock.max())!=0:raise RuntimeError('운반 상태reset 또는 정책시계 진행')
        if not passed:raise RuntimeError('PreparationFailed: 전환경 준비 실패; 전체 시작분모 보존')
        loss=env.loss.clone()
        env.reset(torch.arange(self.num_envs,device=scene.device),snapshot)
        env.reference_guitar.copy_(refs[0]);env.reference_feet.copy_(refs[1]);env.loss.copy_(loss)
        env.preparation_physics_offset=snapshot['physics_step'].clone()
        env.last_native_policy_step=snapshot['physics_step'].clone()
        applied=natural.normalized_action(control.target[:,control.active],control.reference[control.active],control.action_low,control.action_high)
        env.hold_action.copy_(applied);env.execution_hold_action.copy_(applied);env.last_applied_action.copy_(applied)
        self.waiting=failed.clone();self.feedback_disabled=failed.clone();env.finished[failed]=True
        env.previous_action.copy_(applied);env.policy_mask=~self.waiting;env.start_v9.fill_(True)
        self.last_valid_efforts.copy_(last_valid)
        self.policy_wrist_position=env.local_bodies[:,env.wrist_index].clone()
        self.policy_wrist_quaternion=multiply(conjugate(env.guitar_q),env.body[:,env.wrist_index,3:7]).clone()
        self.needs_preparation=False;self.observation=env.observation()

    def policy_physics_step(self,actions,waiting):
        env,control=self.environment,self.controller
        sample=self.scene.snapshot();env.begin_control(actions);target=control.targets(actions,sample)
        reference=control.reference[control.active]
        requested=reference+torch.where(actions>=0,control.action_high-reference,reference-control.action_low)*actions
        requested=requested[:,env.finger_action_indices]
        for sub in range(4):
            efforts=control.efforts(sample);checks=control.diagnostics
            certified=checks['finite']&checks['chest_witness_certified']
            if bool((~certified&~waiting).any()):raise RuntimeError('활성 정책 행 native 제어 인증 실패')
            invalid=~checks['chest_normal_defined'];env.invalidate_control(invalid&~waiting)
            disabled=waiting|env.control_invalid
            efforts=torch.where(disabled[:,None],self.last_valid_efforts,efforts)
            self.last_valid_efforts=torch.where(disabled[:,None],self.last_valid_efforts,efforts)
            sample=self.scene.step(target,efforts);env.substep(sample)
            if self.finger_control_diagnostics is not None:
                self.finger_control_diagnostics.record(requested,target,sample,efforts,env)
        result=env.end_control();self.observation=result[0]
        return result

    def step(self,actions):
        if self.needs_preparation:raise RuntimeError('수집기 운반 없이 정책 실행 금지')
        env,control=self.environment,self.controller;waiting=self.waiting.clone()
        env.policy_mask=~waiting;self.feedback_disabled=waiting.clone()
        frozen={key:value[waiting].clone() for key,value in env.note.items()}
        totals={key:getattr(env,key)[waiting].clone() for key in ('steps','total_reward','total_cost')}
        snapshot=self.scene.snapshot()
        desired=control.target[:,control.active].clone()
        goal=self.policy_wrist_position
        rotation=self.policy_wrist_quaternion
        desired=self.wrist_request(desired,goal,rotation,snapshot)
        teacher=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
        active=torch.tensor([i in self.config['active_axes'] for i in range(39)],device=actions.device)
        executed=torch.where(active,actions,teacher)
        executed[waiting]=teacher[waiting]
        executed[:,33:]=0  # 왼손 전문 실행의 비활성 오른손 잔차는 항상0이다.
        env.action_min.copy_(torch.where(waiting[:,None],env.action_min,torch.minimum(env.action_min,executed)))
        env.action_max.copy_(torch.where(waiting[:,None],env.action_max,torch.maximum(env.action_max,executed)))
        observation,reward,cost,terminated,truncated,episodes=self.policy_physics_step(executed,waiting)
        for key,value in frozen.items():env.note[key][waiting]=value
        for key,value in totals.items():getattr(env,key)[waiting]=value
        env.finished[waiting]=True
        reward=reward.masked_fill(waiting,0);cost=cost.masked_fill(waiting,0)
        terminated=terminated&~waiting;truncated=truncated&~waiting
        episodes=[row for row in episodes if not bool(waiting[row['env_id']])]
        env.last_applied_action.copy_(natural.normalized_action(control.target[:,control.active],control.reference[control.active],control.action_low,control.action_high))
        self.observation=env.observation()
        if self.frame_callback:self.frame_callback('policy',episodes)
        return self.observation,reward,cost,terminated,truncated,episodes


class Collector:
    def __init__(self,policy,pool,*,gamma=.99,cost_gamma=1.):
        self.policy,self.pool=policy,pool;self.gamma,self.cost_gamma=gamma,cost_gamma
        self.control_ticks=0;self.episode_ids=torch.zeros(pool.num_envs,dtype=torch.long,device=pool.scene.device)
    @torch.no_grad()
    def collect(self,horizon,**kwargs):
        rows=[];episodes=[]
        for tick in range(horizon):
            self.pool.prepare()
            observation=self.pool.observation;inputs=[observation[k].detach().clone() for k in FIELDS]
            valid=~self.pool.waiting.clone();result=self.policy.act(*inputs);action=result['action'].clone();action[:,33:]=0
            after,reward,cost,terminated,truncated,completed=self.pool.step(action)
            future=self.policy(*(after[k] for k in FIELDS))
            row=dict(zip(FIELDS,inputs));row.update(latent=result['latent'],logp=result['logp'],old_mean=result['mean'],old_log_std=result['log_std'],
                reward_value=result['reward_value'],cost_value=result['cost_value'],reward=reward,cost=cost,
                terminated=terminated,truncated=truncated,next_reward_value=future['reward_value']*~terminated,
                next_cost_value=future['cost_value']*~terminated,duration=torch.ones_like(terminated,dtype=torch.long),valid=valid,
                start_control_tick=torch.full_like(terminated,self.control_ticks+tick,dtype=torch.long),episode_id=self.episode_ids)
            rows.append({k:v.detach().clone() for k,v in row.items()});episodes.extend(copy.deepcopy(completed))
            if kwargs.get('transition_callback'):kwargs['transition_callback'](tick,reward,cost,terminated,truncated,completed)
            if kwargs.get('progress_callback'):kwargs['progress_callback'](dict(ticks=tick+1,horizon=horizon,phase='transported_policy_tick'))
            done=(terminated|truncated).nonzero().flatten()
            if done.numel():self.episode_ids[done]+=1;self.pool.reset(done)
        self.control_ticks+=horizon
        buffer={key:torch.stack([r[key] for r in rows]) for key in rows[0]}
        # 환경마다 종료 후 대기 길이가 달라도 GAE 입력은 시간순 유효 prefix로 모은다.
        mask=buffer['valid'].clone()
        packed={key:torch.zeros_like(value) for key,value in buffer.items()}
        for identity in range(self.pool.num_envs):
            ids=mask[:,identity].nonzero().flatten()
            for key,value in buffer.items():packed[key][:len(ids),identity]=value[ids,identity]
        return packed,episodes


@contextmanager
def runtime(config):
    with natural.natural_runtime(config):
        old_pool,old_collector,old_pins=rollout.GpuPool,rollout.DecisionCollector,runner._pins
        def pins(settings,out,extra=()):
            paths=[Path(__file__).resolve(),HERE/'transport_runtime.py',Path(config['transport']['evidence']),
                Path(config['geometry']),Path(config['single18']['provenance'])]
            return old_pins(settings,out,list(extra)+paths)
        rollout.GpuPool,rollout.DecisionCollector,runner._pins=LearningPool,Collector,pins
        try:yield
        finally:rollout.GpuPool,rollout.DecisionCollector,runner._pins=old_pool,old_collector,old_pins


def training_checkpoint_metadata(settings,schedule,pool,pins,settings_path,resume,optimizer_updates):
    """공식 재개 필드와 운반 진단 필드를 중복 없이 함께 구성한다."""
    return runner.checkpoint_metadata(settings,schedule,pool,input_pins=pins,settings_path=settings_path,
        lineage=[resume] if resume else (),exposure_transitions=dict(phrases=0,full_song=schedule.committed_transitions),
        optimizer_updates=optimizer_updates,training_valid_decisions=schedule.committed_transitions,
        transport_records=len(pool.preparation_records),
        transport_resume_scope='model/Adam/RNG/exposure/sampler; fresh common-start transport at batch boundary')


def train(settings,out,resume,updates):
    from guitar_learning.training.training_log_io import EpisodeWriter
    from guitar_learning.training.ppo import PPOConfig
    out.mkdir(parents=True,exist_ok=False);log_write(out/'settings.json',portable(settings))
    pins=runner._pins(settings,out,[resume] if resume else ())
    log_write(out/'inputs_before.json',pins)
    random.seed(settings['seed']);np.random.seed(settings['seed']);torch.manual_seed(settings['seed']);torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32=False
    pool=trainer=None;failure=None;completed=False;used=0;valid_total=0;waiting_total=0;started=time.monotonic()
    writer=EpisodeWriter(out);stream=(out/'learning_metrics.jsonl').open('x')
    try:
        pool=LearningPool(settings,out)
        policy=runner._policy(settings,pool)
        trainer=natural.NaturalTrainer(policy,PPOConfig(**settings['ppo']))
        schedule=runner.ExposureSchedule(settings['finger_skill']['planned_transitions'],settings['finger_skill']['full_song_after'])
        if resume:
            runner.restore_checkpoint(trainer,pool,schedule,resume)
        if trainer.updates+updates>100:raise ValueError('최초100회 계획 초과 금지')
        def save(name):
            metadata=training_checkpoint_metadata(settings,schedule,pool,pins,out/'settings.json',resume,trainer.updates)
            trainer.save(out/name,metadata=metadata)
        save('initial.pt');collector=Collector(policy,pool)
        for index in range(updates):
            window_episodes=[]
            def record(tick,reward,cost,terminated,truncated,episodes):
                for episode in episodes:writer.append(episode,trainer.updates,tick)
                window_episodes.extend(episodes)
            pool.environment.reset_reward_window()
            begin=time.monotonic();buffer,episodes=collector.collect(settings['horizon'],transition_callback=record)
            valid=int(buffer['valid'].sum());waiting=buffer['valid'].numel()-valid
            if valid<2:raise RuntimeError('학습 유효 결정 부족')
            collection_s=time.monotonic()-begin;metrics=trainer.update(buffer,episodes)
            schedule.commit(valid);pool.set_training_progress(schedule.committed_transitions)
            valid_total+=valid;waiting_total+=waiting;used+=1
            metrics.update(update_index=trainer.updates,valid_policy_decisions=valid,waiting_invalid=waiting,
                cumulative_valid_policy_decisions=schedule.committed_transitions,collection_s=collection_s,
                preparation_batches=len(pool.preparation_records),completed_episodes=len(episodes),
                reward_component_means=pool.environment.reward_window_means(valid))
            stream.write(log_dumps(metrics,allow_nan=False)+'\n');stream.flush();writer.sync()
            if (index+1)%10==0 and index+1<updates:save('checkpoint_%06d.pt'%trainer.updates)
        save('final.pt');completed=True
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error))
    finally:
        stream.close();writer.close()
        if pool is not None:
            try:pool.close()
            except BaseException as error:failure=failure or dict(type='CleanupError',message=str(error));completed=False
    changed=[path for path,sha in pins.items() if not Path(path).is_file() or transport.digest(path)!=sha]
    report=dict(schema=SCHEMA,completed=completed and not failure and not changed,failure=failure,changed_inputs=changed,
        optimizer_updates=trainer.updates if trainer else None,updates_in_run=used,valid_policy_decisions=valid_total,
        waiting_invalid_decisions=waiting_total,preparation_batches=pool.preparation_records if pool else [],
        planned_updates=100,wall_s=time.monotonic()-started,lifecycle_verified=bool(pool and pool.closed))
    log_write(out/'report.json',report)
    return report


def evaluate_checkpoint(checkpoint,out,episodes):
    """모든 초기 시작을 분모로 두고 준비 실패와 조건부 압현 성과를 분리한다."""
    from guitar_learning.training.training_log_io import EpisodeWriter
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False);runner._validate_pins(payload['metadata'])
    settings=localize(payload['metadata']['settings']);settings['num_envs']=episodes
    out.mkdir(parents=True,exist_ok=False);log_write(out/'settings.json',portable(settings))
    pins=runner._pins(settings,out,[checkpoint]);log_write(out/'inputs_before.json',pins)
    pool=None;failure=None;rows=[];initial=None;closed=False
    writer=EpisodeWriter(out)
    try:
        pool=LearningPool(settings,out);policy=runner._policy(settings,pool)
        trainer=natural.NaturalTrainer(policy,ppo.PPOConfig(**settings['ppo']));trainer.load(checkpoint)
        pool.environment.set_evaluation(True,full_song=True)
        try:pool.prepare()
        except RuntimeError as error:
            if not str(error).startswith('PreparationFailed:'):raise
        initial=copy.deepcopy(pool.preparation_records[0])
        selected={i for i,ready in enumerate(initial['ready']) if ready}
        if selected:
            collector=Collector(runner._DeterministicPolicy(policy),pool);seen=set()
            def record(tick,reward,cost,terminated,truncated,completed):
                for row in completed:
                    if row['env_id'] in selected and row['env_id'] not in seen:
                        seen.add(row['env_id']);rows.append(copy.deepcopy(row));writer.append(row,trainer.updates,tick)
            for tick in range(math.ceil(pool.environment.task.duration_s*60)+32):
                collector.collect(1,transition_callback=record)
                if seen==selected:break
            if seen!=selected:raise RuntimeError('준비 성공 행의 최초 정책episode 미완결')
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        writer.close()
        if pool:
            try:pool.close();closed=pool.closed
            except BaseException as error:failure=failure or dict(type='CleanupError',message=str(error))
    changed=[p for p,sha in pins.items() if not Path(p).is_file() or transport.digest(p)!=sha]
    def safe(row):return row['valid'] and not row['termination']['physical_failure'] and not row['termination']['wrist_failure']
    ledger=lambda row:row['left_note_ledger']['values']
    achieved=sum(safe(row) and ledger(row)['left'][0] for row in rows)
    from guitar_learning.song.task import make_task
    task=make_task(Path(settings['song_training']['bundle']));duration=task.targets[0].end_s-task.targets[0].onset_s
    ready_count=sum(initial['ready']) if initial else 0
    metrics=dict(episodes=episodes,initial_start_count=episodes,prepared_count=ready_count,
        preparation_failed_count=episodes-ready_count,policy_episodes=len(rows),achievement=achieved,
        all_start_achievement_rate=achieved/episodes,conditional_achievement_rate=achieved/ready_count if ready_count else None,
        contact=sum(ledger(row)['contact_done'][0] for row in rows),
        clean_fraction=sum(ledger(row)['clean'][0]/duration for row in rows)/episodes,
        conditional_clean_fraction=sum(ledger(row)['clean'][0]/duration for row in rows)/ready_count if ready_count else None,
        entire_hold=sum(safe(row) and ledger(row)['clean'][0]>=duration-1e-8 for row in rows),
        hold90=sum(safe(row) and ledger(row)['clean'][0]>=.9*duration-1e-8 for row in rows),
        policy_physical=sum(row['termination']['physical_failure'] for row in rows),
        policy_wrist=sum(row['termination']['wrist_failure'] for row in rows),
        wrong_s=sum(ledger(row)['wrong'][0] for row in rows)/episodes)
    log_write(out/'metrics.json',metrics)
    report=dict(schema=SCHEMA+'.evaluation',completed=failure is None and not changed and closed,failure=failure,
        changed_inputs=changed,lifecycle_verified=closed,episodes=episodes,policy_episodes=len(rows),
        first_episode_per_env_per_batch=True,failed_episodes_in_denominator=True,
        preparation=initial,summary=metrics,checkpoint_sha256=transport.digest(checkpoint),
        scope='all fixed initial starts; preparation failures contribute zero, conditional policy rates separate')
    log_write(out/'report.json',report);return report


def render_checkpoint(checkpoint,out,num_envs=4):
    from isaacgym import gymapi
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym,finish_video
    from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras,_encoder
    out.mkdir(parents=True,exist_ok=False)
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False);runner._validate_pins(payload['metadata'])
    settings=localize(payload['metadata']['settings']);settings['num_envs']=num_envs
    log_write(out/'settings.json',portable(settings));pins=runner._pins(settings,out,[checkpoint])
    log_write(out/'inputs_before.json',pins)
    original=gymapi.acquire_gym;pool=None;videos={};episode=None;failure=None;initial_preparation_failure=None;ticks=0;frames=0;poses=[]
    try:
        gymapi.acquire_gym=lambda:GraphicsGym(original())
        try:pool=LearningPool(settings,out)
        finally:gymapi.acquire_gym=original
        policy=runner._policy(settings,pool);trainer=natural.NaturalTrainer(policy,ppo.PPOConfig(**settings['ppo']));trainer.load(checkpoint)
        pool.environment.set_evaluation(True,full_song=True)
        cameras=_create_cameras(pool.scene,gymapi);videos={name:_encoder(out/(name+'.mp4')) for name in cameras}
        def capture(phase,episodes):
            nonlocal ticks,frames,episode
            if episode is not None:return
            ticks+=1
            snapshot=pool.scene.snapshot()
            poses.append(dict(phase=phase,tick=ticks,q105=snapshot['q'][0].cpu().tolist(),
                body_state=snapshot['body_state'][0].cpu().tolist(),native_physics_step=int(snapshot['physics_step'][0])))
            if ticks%2==0:
                pool.scene.gym.step_graphics(pool.scene.sim);pool.scene.gym.render_all_camera_sensors(pool.scene.sim)
                for name,camera in cameras.items():
                    pixels=pool.scene.gym.get_camera_image(pool.scene.sim,pool.scene.envs[0],camera,gymapi.IMAGE_COLOR)
                    videos[name].stdin.write(np.asarray(pixels).reshape(720,1280,4)[...,:3].copy().tobytes())
                frames+=1
            for row in episodes or []:
                if row['env_id']==0:episode=copy.deepcopy(row)
        pool.frame_callback=capture
        try:pool.prepare()
        except RuntimeError as error:
            if not str(error).startswith('PreparationFailed:'):raise
        if bool(pool.waiting[0]) or pool.needs_preparation:
            initial_preparation_failure=copy.deepcopy(pool.preparation_records[0]['first_failures'][0])
        collector=Collector(runner._DeterministicPolicy(policy),pool)
        for index in range(0 if initial_preparation_failure else math.ceil(pool.environment.task.duration_s*60)+32):
            collector.collect(1)
            if episode is not None:break
        if episode is None and initial_preparation_failure is None:raise RuntimeError('첫 정책episode 완결 실패')
        if episode is not None:log_write(out/'episode_env0000.json',episode)
        if initial_preparation_failure is not None:log_write(out/'preparation_failure_env0000.json',initial_preparation_failure)
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error))
    finally:
        gymapi.acquire_gym=original
        for name,process in videos.items():
            code,errors=finish_video(process)
            if code or errors:failure=failure or dict(type='VideoError',message=str((code,errors)))
        if pool:
            try:pool.close()
            except BaseException as error:failure=failure or dict(type='CleanupError',message=str(error))
    log_write(out/'poses.json',poses)
    changed=[p for p,sha in pins.items() if not Path(p).is_file() or transport.digest(p)!=sha]
    report=dict(schema=SCHEMA+'.render',completed=failure is None and (episode is not None or initial_preparation_failure is not None) and not changed,
        failure=failure,changed_inputs=changed,frames=frames,fps=30,native_pixels=True,
        initial_preparation_failure=initial_preparation_failure,transport_ready=initial_preparation_failure is None,
        scope='env0 first common transport plus first policy episode; no reset frames',
        checkpoint_sha256=transport.digest(checkpoint),lifecycle_verified=bool(pool and pool.closed))
    log_write(out/'report.json',report);return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('train','evaluate','render'))
    for name in ('catalog','provenance','evidence','out'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--case',required=True);parser.add_argument('--resume',type=Path);parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--updates',type=int,default=25);parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--num-envs',type=int);parser.add_argument('--episodes',type=int,choices=(16,32),default=16)
    args=parser.parse_args()
    if args.out.exists():raise FileExistsError(args.out)
    if not 1<=args.updates<=100:parser.error('추가 학습1..100회 필요')
    if args.operation!='train' and not args.checkpoint:parser.error('평가/렌더 checkpoint 필요')
    if args.operation=='train' and args.checkpoint:parser.error('학습은 resume만 허용')
    with configuration(args.catalog,args.provenance,args.case,args.evidence) as (config,row):
        source=args.resume if args.operation=='train' else args.checkpoint
        source_sha=transport.digest(source) if source else None
        if source:
            payload=torch.load(source,map_location='cpu',weights_only=False);runner._validate_pins(payload['metadata'])
            settings=localize(payload['metadata']['settings'])
            if settings.get('natural_press')!=config or payload['identity']['architecture']['schema']!=POLICY_SCHEMA:
                raise ValueError('같은 운반 정책·입력만 재개/평가 가능')
            if args.operation=='train' and (settings['seed']!=args.seed or args.num_envs is not None and settings['num_envs']!=args.num_envs):
                raise ValueError('재개 seed/환경수 유지 필요')
        else:settings=build_settings(config,row,num_envs=args.num_envs or 64,seed=args.seed)
        with runtime(config):
            if args.operation=='train':
                settings['updates']=args.updates;report=train(settings,args.out.resolve(),source,args.updates)
            elif args.operation=='evaluate':
                report=evaluate_checkpoint(source,args.out,args.episodes)
            else:report=render_checkpoint(source,args.out,args.num_envs or 4)
        if source and transport.digest(source)!=source_sha:raise ValueError('실행 중 원본 모델 변경')
        if not report['completed']:raise RuntimeError('운반 학습 실행 미완료; report.json 확인')


if __name__=='__main__':main()
