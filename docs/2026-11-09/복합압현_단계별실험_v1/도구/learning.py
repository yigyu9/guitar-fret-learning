"""613 손가락별 관측과 과제 전체 제어축으로 복합 압현을 비교한다.

기타 COM 경계 reset은 검증된 정렬 학습기에서 명시 복사했다. 기존 파일을
실행하지 않으며 새 정책·입력·재개 계약으로만 학습한다. 과거601 모델은 거부한다.
"""
import argparse
import copy
from contextlib import contextmanager
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import sys
from types import SimpleNamespace
import time
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
if __name__=='__main__' and '--self-test' not in sys.argv and not any(x in sys.argv for x in ('-h','--help')):import isaacgym
import numpy as np
import torch
from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.tool.experiments.song_finger_progress import SongFingerProgressPolicy,STATE_DIM
from guitar_learning.gpu.finger_progress import FingerProgressEnvironment,FINGER_PROGRESS_FIELDS,progress_contract
from guitar_learning.training import finger_skill_runner as runner,rollout
from guitar_learning.gpu import environment as gpu_environment
from guitar_learning.gpu.control import apply,multiply,conjugate
from guitar_learning.gpu.scene import RigidGuitar,_body_row
from guitar_learning.training.training_log_io import digest,write
from guitar_learning.portability import portable,localize,validate_checkpoint_inputs
SCHEMA='guitar_learning.complex_press.v1'
POLICY_SCHEMA='guitar_learning.complex_press_policy.v1'
RESUME_SCHEMA='guitar_learning.complex_press_resume.v1'
STD_FLOOR=math.exp(-3)
FINGER_STD=.35
COPY_ORIGIN={'path': '/home/ajou/yigyu/3/docs/2026-11-09/단일압현_정렬출발학습_v1/도구/learning.py', 'sha256': '133e0b5aaf8ae0f1d815b70b1f4b45f8eb531f0d59d86a8d77c91310ddbee083'}


def input_module():
    name='complex_press_inputs_v1'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,HERE/'inputs.py')
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name]


def make_task(*args,**kwargs):return input_module().make_task(*args,**kwargs)
def load_inputs(folder):return input_module().load_verified(Path(folder).resolve())


def control_axes(fingers,arm_mode):
    if (not fingers or sorted(set(fingers))!=list(fingers) or
            any(type(f) is not int or f not in (1,2,3,4) for f in fingers) or arm_mode not in ('hold','free')):
        raise ValueError('정렬된 과제 손가락 합집합과 hold/free 팔 조건 필요')
    return list(range(12))*(arm_mode=='free')+[axis for finger in fingers for axis in range(17+4*(finger-1),21+4*(finger-1))]


def configuration(folder,arm_mode=None):
    folder=Path(folder).resolve();folder.relative_to(ROOT)
    catalog,row,known,paths=load_inputs(folder)
    expected='hold' if row['control_scope']=='goal_only' else 'free'
    if row['control_scope'] not in ('goal_only','arm_and_goals') or arm_mode not in (None,expected):
        raise ValueError('입력에 봉인된 팔 제어 조건과 다름')
    axes=control_axes(row['target_fingers'],expected)
    config=dict(schema=SCHEMA,condition='E4',distribution='aligned',axes='target_union',song=row['song'],
        finger=row['finger'],case_id=row['case_id'],arm_mode=expected,target_fingers=row['target_fingers'],
        geometry=str(folder/'catalog.json'),geometry_sha256=digest(folder/'catalog.json'),
        provenance_sha256=digest(folder/'provenance.json'),active_axes=axes,
        observation_extra_fields=list(FINGER_PROGRESS_FIELDS),finger_initial_std=FINGER_STD,finger_std_floor=STD_FLOOR,
        support_initial_std=STD_FLOOR,phase_arm_support=False,
        inactive_execution='과제 비담당 손가락과 엄지는 경계 hold, 오른손6잔차0; 단계별 행동 잠금 없음',
        initial_distribution=dict(v9_fraction=0.,rng='공식 CPU torch RNG 저장복원; episode 경계 정렬 reset'),
        likelihood='과제 전체 고정 활성축의 독립 Gaussian tanh; 비활성축은 표본/logp/entropy/KL 제외',
        aligned_start=dict(input_dir=str(folder),known_press_sha256=digest(folder/'known_press.json'),
            reset='실측 도착 q/body와 역변환 기타 COM root; 과거 시계 복원 없음',
            success_scope='조건부 팔/과제 손가락 제어; 자유 J33 성과 아님'),
        progress_schema=progress_contract(len(row['compiled_targets'])),
        timing_measurement='평가/재생의 실제240Hz 원장을 읽기만 함; tail 포함 엄격값과 내부값 분리')
    return config,catalog,row,known,paths


def validate_settings(settings):
    config=settings.get('natural_press',{});start=config.get('aligned_start',{})
    expected,_,row,_,_=configuration(start.get('input_dir',''),config.get('arm_mode'))
    if config!=expected:raise ValueError('복합 압현 입력·mask·관측 계약 불일치')
    runner._validate_joint_settings(settings)
    if settings['song_training']['observation_dimension']!=STATE_DIM or settings['initial_std']!=STD_FLOOR:
        raise ValueError('613관측과 공식 runner 분산 shift0 필요')
    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
    training=settings['song_training']
    if (Path(training['bundle']).resolve()!=Path(row['bundle']).resolve() or training['song_id']!=row['song'] or
            training['target_count']!=len(task.targets) or training['control_ticks']!=task.provenance['song']['control_ticks'] or
            training['episode_duration_s']!=task.duration_s or settings['phrase_events']!=task.provenance['song']['source_event_count']):
        raise ValueError('실제 과제 bundle/목표수/시각 불일치')
    return expected


def build_settings(folder,*,updates=100,num_envs=64,size='large',horizon=32,seed=7,arm_mode=None):
    from guitar_learning.training.launch import settings_document
    config,_,row,_,_=configuration(folder,arm_mode)
    settings=settings_document(updates=updates,num_envs=num_envs,size=size,horizon=horizon,seed=seed,checkpoint_every=50)
    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
    actual=[(t.target_id,t.string,t.fret,t.finger,t.onset_s,t.end_s,t.press_s) for t in task.targets]
    expected=[(t['target_id'],t['string'],t['fret'],t['finger'],t['onset_s'],t['end_s'],t['press_s']) for t in row['compiled_targets']]
    if actual!=expected:raise ValueError('입력 원장과 실제 컴파일 목표 불일치')
    settings['song_training'].update(song_id=row['song'],bundle=str(Path(row['bundle']).resolve()),target_count=len(task.targets),
        control_ticks=task.provenance['song']['control_ticks'],episode_duration_s=task.duration_s,observation_dimension=STATE_DIM)
    settings['phrase_events']=task.provenance['song']['source_event_count'];settings['natural_press']=config;settings['initial_std']=STD_FLOOR
    validate_settings(settings);return settings


def logical_to_root(rigid,logical):
    """논리 기타0의 COM 속도까지 compound 원점·COM 기준으로 정확히 역변환한다."""
    if logical.shape!=(13,) or not torch.isfinite(logical).all():raise ValueError('유한 논리 기타13상태 필요')
    result=logical.clone()
    result[3:7]=multiply(logical[3:7],conjugate(rigid._rotations[0]))
    result[:3]=logical[:3]-apply(result[3:7],rigid._offsets[0])
    logical_com=logical[:3]+apply(logical[3:7],rigid._logical_com[0])
    root_com=result[:3]+apply(result[3:7],rigid._compound_com)
    result[7:10]=logical[7:10]-torch.cross(logical[10:13],logical_com-root_com,dim=-1)
    return result

def predicted_root(root,com,dt=1/240.):
    """외력이 없을 때의 첫 substep 참고값. 물리 성공 인증으로 쓰지 않는다."""
    value=root.clone();omega=root[10:13];angle=torch.linalg.vector_norm(omega)*dt
    axis=omega/torch.linalg.vector_norm(omega).clamp_min(1e-12)
    delta=torch.cat((axis*torch.sin(angle/2),torch.cos(angle/2).reshape(1)))
    value[3:7]=multiply(delta,root[3:7])
    value[:3]=root[:3]+dt*(root[7:10]-torch.cross(omega,apply(root[3:7],com),dim=-1))
    return value

class ComplexScene(natural.NaturalScene):
    """새 episode 경계에서만 실제 기타 root도 정렬된 논리 snapshot과 일치시킨다."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.metadata['reset_body_source'].update(schema=SCHEMA,verified=False,
            scope='new aligned reset requires this pool oracle; historical source success alone is not certification',
            native_guitar_root='inverse logical0 pose and COM velocity at episode boundary')

    def reset(self,indices):
        if not getattr(self,'_configured',False):return super().reset(indices)
        ids=torch.as_tensor(indices,device=self.device,dtype=torch.long)
        logical=torch.tensor(_body_row(self.goal['state']['guitar_body_states'][0]),device=self.device,dtype=self.rigid_guitar.prepared_root.dtype)
        root=logical_to_root(self.rigid_guitar,logical)
        old=self.rigid_guitar.prepared_root
        try:
            self.rigid_guitar.prepared_root=root
            result=super().reset(ids)
        finally:self.rigid_guitar.prepared_root=old
        if not hasattr(self,'aligned_pending'):
            self.aligned_pending=torch.zeros(self.num_envs,dtype=torch.bool,device=self.device)
            self.aligned_audit=[];self.aligned_first_steps=0;self.aligned_max_prediction_error_m=0.
        self.aligned_pending[ids]=True;self.aligned_root=root.clone();self.aligned_logical=logical.clone()
        if not torch.allclose(self._roots[ids,1],root.expand(len(ids),-1),atol=1e-6,rtol=0):
            raise RuntimeError('정렬 경계에서 실제 native 기타 root 불일치')
        return result

    def step(self,targets,efforts):
        pending=getattr(self,'aligned_pending',None)
        selected=pending.nonzero().flatten().clone() if pending is not None else []
        result=super().step(targets,efforts)
        for identity in selected:
            index=int(identity);actual=self._roots[index,1].clone()
            prediction=predicted_root(self.aligned_root,self.rigid_guitar._compound_com)
            error=float(torch.linalg.vector_norm(actual[:3]-prediction[:3]))
            self.aligned_max_prediction_error_m=max(self.aligned_max_prediction_error_m,error)
            self.aligned_first_steps+=1
            if len(self.aligned_audit)<128:
                self.aligned_audit.append(dict(env_id=index,physics_step=int(self.episode_steps[index]),
                    boundary_root13=self.aligned_root.cpu().tolist(),first_native_root13=actual.cpu().tolist(),
                    source_arrived_logical0_body13=self.aligned_logical.cpu().tolist(),
                    source_arrived_q105=self.goal['q105'],first_native_q105=result['q'][index].cpu().tolist(),
                    first_native_arm_max_delta_rad=float((result['q'][index,self.catalog['action_indices'][:12]]-
                        result['q'].new_tensor(self.goal['q105'])[self.catalog['action_indices'][:12]]).abs().max()),
                    first_native_finger_max_delta_rad=float((result['q'][index,self.catalog['action_indices'][12:33]]-
                        result['q'].new_tensor(self.goal['q105'])[self.catalog['action_indices'][12:33]]).abs().max()),
                    first_native_logical0_body13=result['body_state'][index,len(self.human_bodies)].cpu().tolist(),
                    source_to_first_logical_position_delta_m=float(torch.linalg.vector_norm(
                        result['body_state'][index,len(self.human_bodies),:3]-self.aligned_logical[:3])),
                    no_force_prediction_root13=prediction.cpu().tolist(),position_prediction_error_m=error,
                    scope='actual first240Hz step readback; prediction ignores contacts/gravity, residual is diagnostic only'))
        if pending is not None:pending[selected]=False
        return result

    @property
    def diagnostics(self):
        result=super().diagnostics
        result['aligned_reset']=dict(schema=SCHEMA,first_steps_measured=getattr(self,'aligned_first_steps',0),
            maximum_position_prediction_error_m=getattr(self,'aligned_max_prediction_error_m',None),
            first128=getattr(self,'aligned_audit',[]),state_setters='episode boundaries only')
        return result

class TimingTracker:
    """실제240Hz clean 원장 증가와 후보를 읽어 시각 기준만 측정한다."""
    def __init__(self,targets,count):
        self.targets=targets;self.rows=[None]*count;self.generations=[-1]*count
        boundaries=sorted({x[key] for x in targets for key in ('onset_s','end_s')})
        self.overlaps=[];self.active_segments=[]
        for lo,hi in zip(boundaries,boundaries[1:]):
            selected=[i for i,t in enumerate(targets) if t['onset_s']<=lo and t['end_s']>=hi]
            if selected:self.active_segments.append((lo,hi,selected))
            if len(selected)>1:self.overlaps.append((lo,hi,selected))
        self.reset(range(count))

    def reset(self,indices):
        for i in indices:
            self.generations[i]+=1
            self.rows[i]=dict(first=[None]*len(self.targets),release=[None]*len(self.targets),
                audible=[0.]*len(self.targets),release_seen=[0.]*len(self.targets),
                overlap=[0.]*len(self.overlaps),overlap_seen=[0.]*len(self.overlaps),samples=0,last_time=0.,wrong_union=0.,active_union=0.)

    def observe(self,times,credits,candidates,active,wrong=None):
        for i,now in enumerate(times):
            if not active[i]:continue
            row=self.rows[i];before=row['last_time'];row['last_time']=now;row['samples']+=1
            for lo,hi,selected in self.active_segments:
                interval=max(0.,min(now,hi)-max(before,lo));row['active_union']+=interval
                if wrong is not None and any(wrong[i][j] for j in selected):row['wrong_union']+=interval
            for j,t in enumerate(self.targets):
                overlap=max(0.,min(now,t['end_s'])-max(before,t['onset_s']))
                row['audible'][j]+=overlap
                if credits[i][j]>1e-12 and row['first'][j] is None:row['first'][j]=now
                release_overlap=max(0.,min(now,t['end_s']+.1)-max(before,t['end_s']))
                row['release_seen'][j]+=release_overlap
                # 같은 손가락의 다음 유효 목표가 곧바로 이어지면 이전 목표 해제 검사를 면제한다.
                successor=any(k!=j and x['finger']==t['finger'] and x['onset_s']<=t['end_s']+1e-9<x['end_s'] for k,x in enumerate(self.targets))
                if not successor and now>=t['end_s']-1e-9 and not candidates[i][j] and row['release'][j] is None:
                    row['release'][j]=now
            for j,(lo,hi,indices) in enumerate(self.overlaps):
                overlap=max(0.,min(now,hi)-max(before,lo));row['overlap_seen'][j]+=overlap
                if all(credits[i][k]>1e-12 for k in indices):row['overlap'][j]+=overlap

    def episode(self,index):
        row=self.rows[index];goals=[];internal=True;terminal=True;onsets=True
        final=max(x['end_s'] for x in self.targets)
        for j,t in enumerate(self.targets):
            first=row['first'][j];release=row['release'][j]
            delay=None if first is None else max(0.,first-t['onset_s'])
            release_delay=None if release is None else max(0.,release-t['end_s'])
            successor=any(k!=j and x['finger']==t['finger'] and x['onset_s']<=t['end_s']+1e-9<x['end_s'] for k,x in enumerate(self.targets))
            first_ok=delay is not None and delay<=.1+1e-9
            covered=row['release_seen'][j]>=.1-1e-8
            release_ok=successor or (covered and release_delay is not None and release_delay<=.1+1e-9)
            tail=t['end_s']>=final-1e-9
            onsets &= first_ok
            if tail:terminal &= release_ok
            else:internal &= release_ok
            goals.append(dict(target_id=t['target_id'],finger=t['finger'],string=t['string'],fret=t['fret'],
                onset_s=t['onset_s'],end_s=t['end_s'],first_clean_time_s=first,first_clean_delay_s=delay,
                release_time_s=release,release_delay_s=release_delay,onset_pass=first_ok,release_pass=release_ok,
                release_exempt_immediate_same_finger_successor=successor,terminal_release=tail,
                audible_observed_s=row['audible'][j],release_window_observed_s=row['release_seen'][j]))
        overlaps=[dict(start_s=lo,end_s=hi,target_ids=[self.targets[k]['target_id'] for k in ids],
            observed_s=row['overlap_seen'][j],clean_s=row['overlap'][j],clean_fraction=row['overlap'][j]/(hi-lo),
            complete=row['overlap_seen'][j]>=hi-lo-1e-8) for j,(lo,hi,ids) in enumerate(self.overlaps)]
        result=dict(exact_hz=240,episode_generation=self.generations[index],physics_samples=row['samples'],targets=goals,overlaps=overlaps,
            wrong_press_active_union_s=row['wrong_union'],active_union_observed_s=row['active_union'],
            planned_active_union_s=sum(hi-lo for lo,hi,_ in self.active_segments),
            timing_pass=onsets and internal and terminal,internal_timing_pass=onsets and internal,
            terminal_release_pass=terminal,overlap_pass=all(x['complete'] and x['clean_fraction']>=.9-1e-9 for x in overlaps),
            scope='실제240Hz 원장 증가와 유효 목표별 후보; 실패·미관측도 분모에 보존')
        return result


class ComplexEnvironment(FingerProgressEnvironment):
    config=None
    measure=False

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.contract['natural_press']=copy.deepcopy(self.config)
        self.timing=TimingTracker([dict(target_id=t.target_id,string=t.string,fret=t.fret,finger=t.finger,
            onset_s=t.onset_s,end_s=t.end_s,press_s=t.press_s) for t in self.task.targets],0)
        self.diagnostic_episodes=[];self.diagnostic_seen=set()
        self.raw_diagnostic=None

    def reset(self,indices,snapshot):
        result=super().reset(indices,snapshot)
        if self.measure:
            if len(self.timing.rows)!=self.N:
                self.timing=TimingTracker(self.timing.targets,self.N)
            else:self.timing.reset(torch.as_tensor(indices).cpu().tolist())
        return result

    def substep(self,snapshot):
        before=self.note['clean'].clone() if self.measure else None
        active=(~self.finished).clone() if self.measure else None
        result=super().substep(snapshot)
        if self.measure:
            times=self._score_time().cpu().tolist();credits=(self.note['clean']-before).cpu().tolist()
            candidates=self.candidate.cpu().tolist();wrong=self.wrong.cpu().tolist()
            self.timing.observe(times,credits,candidates,active.cpu().tolist(),wrong)
            if self.raw_diagnostic is not None:
                self.raw_diagnostic.write(json.dumps(dict(episode_generation=self.timing.generations,time_s=times,active=active.cpu().tolist(),
                    clean_increment_s=credits,candidate=candidates,wrong=wrong,phase=self.finger_progress['phase'].cpu().tolist(),
                    target_index=self.finger_progress['target'].cpu().tolist()),separators=(',',':'))+'\n')
        return result

    def _episode(self,index,failed):
        episode=super()._episode(index,failed)
        episode['complex_press']=dict(schema=SCHEMA,case_id=self.config['case_id'],active_axes=self.config['active_axes'],
            target_fingers=self.config['target_fingers'],arm_mode=self.config['arm_mode'],policy_teacher=False)
        if self.measure:
            diagnostic=self.timing.episode(index);diagnostic.update(env_id=index,
                valid=episode['valid'],physical_failure=episode['termination']['physical_failure'],
                wrist_failure=episode['termination']['wrist_failure'])
            if not episode['valid'] or diagnostic['physical_failure'] or diagnostic['wrist_failure']:
                diagnostic.update(timing_pass=False,internal_timing_pass=False,overlap_pass=False)
            episode['complex_timing']=diagnostic
            if index not in self.diagnostic_seen:
                self.diagnostic_episodes.append(diagnostic);self.diagnostic_seen.add(index)
        return episode


class ComplexPool(rollout.GpuPool):
    measure=False

    def __init__(self,settings,out):
        config=copy.deepcopy(validate_settings(settings));self.natural_press=config
        class Environment(ComplexEnvironment):pass
        Environment.config=config;Environment.measure=self.measure
        self.environment_class_override=Environment
        super().__init__(settings,out)
        self.environment.applied_action_getter=lambda:natural.normalized_action(
            self.controller.target[:,self.controller.active],self.controller.reference[self.controller.active],
            self.controller.action_low,self.controller.action_high)
        if self.measure:
            import gzip
            self.environment.raw_diagnostic=gzip.open(Path(out)/'diagnostic_trace.jsonl.gz','wt',encoding='utf-8')

    def _create_scene(self,settings,out):
        return ComplexScene(self.num_envs,'left',device=settings['device'],out=out,natural_press=self.natural_press)

    def reset(self,indices=None):
        _,rows=super().reset(indices)
        ids=torch.arange(self.num_envs,device=self.scene.device) if indices is None else torch.as_tensor(indices,device=self.scene.device,dtype=torch.long)
        c=self.controller;c.target[ids]=self.scene.initial_hold[ids]
        action=natural.normalized_action(self.scene.initial_hold[ids][:,c.active],c.reference[c.active],c.action_low,c.action_high)
        action[:,33:]=0
        if not hasattr(self,'execution_hold_action'):self.execution_hold_action=torch.zeros(self.num_envs,39,device=self.scene.device)
        self.execution_hold_action[ids]=action;self.environment.previous_action[ids]=action
        right=c.active[33:];c.target[ids[:,None],right[None]]=c.reference[right]
        self.scene.target[ids[:,None],right[None]]=c.reference[right]
        self.observation=self.environment.observation();return self.observation,rows

    def step(self,actions):
        mask=torch.tensor([i in self.natural_press['active_axes'] for i in range(39)],device=actions.device)
        return super().step(torch.where(mask,actions,self.execution_hold_action))

    def close(self):
        try:
            environment=getattr(self,'environment',None)
            if environment is not None and self.measure:
                if environment.raw_diagnostic is not None:
                    environment.raw_diagnostic.close();environment.raw_diagnostic=None
                episodes=environment.diagnostic_episodes
                summary=dict(episodes=len(episodes),exact_hz=240,
                    timing_pass_episodes=sum(e['timing_pass'] for e in episodes),
                    internal_timing_pass_episodes=sum(e['internal_timing_pass'] for e in episodes),
                    terminal_release_pass_episodes=sum(e['terminal_release_pass'] for e in episodes),
                    overlap_pass_episodes=sum(e['overlap_pass'] for e in episodes),
                    wrong_press_active_union_s=sum(e['wrong_press_active_union_s'] for e in episodes),
                    planned_active_union_s_per_episode=sum(hi-lo for lo,hi,_ in environment.timing.active_segments))
                write(Path(self.out)/'diagnostics.json',dict(schema=SCHEMA+'.timing',summary=summary,episodes=episodes,
                    target_ids=[t.target_id for t in environment.task.targets],scope='환경별 첫 episode만 집계. 실제240Hz wrong은활성구간의우측끝점any-wrong을중복없이적분, clean은기존원장증가. raw trace는episode_generation으로구분'))
        finally:super().close()


class ComplexPolicy(SongFingerProgressPolicy):
    schema=POLICY_SCHEMA

    def __init__(self,state_dim,*,size,contract,natural_press):
        if contract.get('natural_press')!=natural_press:raise ValueError('정책·환경 복합제어 계약 불일치')
        super().__init__(state_dim,size=size,contract=contract)
        self.config=copy.deepcopy(natural_press)
        self.register_buffer('active_mask',torch.tensor([i in natural_press['active_axes'] for i in range(39)]))
        catalog,row=natural.catalog_goal(natural_press)
        indices=torch.tensor(catalog['action_indices']);reference=torch.tensor(catalog['reference105'])[indices]
        hold=natural.normalized_action(torch.tensor(row['hold_target105'])[indices],reference,
            torch.tensor(catalog['action_lower']),torch.tensor(catalog['action_upper']))
        hold[33:]=0;self.register_buffer('held_latent',torch.atanh(hold.clamp(-.999999,.999999)))
        with torch.no_grad():
            self.core.support_head.bias.copy_(self.held_latent[:17])
            for i,finger in enumerate(natural.FINGERS):
                self.core.finger_heads[finger][-1].bias.copy_(self.held_latent[17+4*i:21+4*i])
                self.core.finger_log_std[4*i:4*i+4].fill_(math.log(FINGER_STD if i+1 in natural_press['target_fingers'] else STD_FLOOR))
            self.core.support_log_std.fill_(math.log(STD_FLOOR))
        if natural_press['arm_mode']=='hold':
            for group in (self.core.support_encoder,self.core.support_head,self.support_progress):group.requires_grad_(False)
            self.core.support_log_std.requires_grad_(False)
        for i,finger in enumerate(natural.FINGERS):
            if i+1 not in natural_press['target_fingers']:
                self.core.finger_heads[finger].requires_grad_(False);self.finger_progress[finger].requires_grad_(False)
        self.architecture.update(schema=POLICY_SCHEMA,complex_press=copy.deepcopy(natural_press),
            active_axes=natural_press['active_axes'],inactive_execution='고정된 경계 유지각; 비활성 우도 제외',
            std_floor=dict(finger=STD_FLOOR,support=math.exp(-5)))

    @property
    def support_log_std(self):return self.core.support_log_std
    @property
    def finger_log_std(self):return self.core.finger_log_std
    def _active_mask(self):return self.active_mask
    def actor_parameters(self):return [p for p in super().actor_parameters() if p.requires_grad]

    def forward(self,state,*inputs):
        result=super().forward(state,*inputs)
        result['mean']=torch.where(self.active_mask,result['mean'],self.held_latent.expand(len(state),-1))
        raw=torch.cat((self.core.support_log_std.clamp(-5.,2.),self.core.finger_log_std.clamp(math.log(STD_FLOOR),2.),
            self.core.support_log_std.new_full((6,),math.log(STD_FLOOR))))
        result['log_std']=raw.expand(len(state),-1)
        return result


def validate_metadata(metadata):
    if not isinstance(metadata,dict) or metadata.get('schema')!=RESUME_SCHEMA:raise ValueError('복합 압현 전용 checkpoint만 허용')
    validate_settings(localize(metadata['settings']))


def read_checkpoint(path):
    payload=torch.load(path,map_location='cpu',weights_only=False);validate_metadata(payload.get('metadata'))
    if payload.get('identity',{}).get('architecture',{}).get('schema')!=POLICY_SCHEMA:raise ValueError('복합 압현 정책 구조 불일치')
    validate_checkpoint_inputs(payload['metadata']);return localize(payload['metadata']['settings'])


@contextmanager
def runtime(measure=False):
    original=(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA,gpu_environment.make_task)
    class Pool(ComplexPool):pass
    Pool.measure=measure
    def policy(settings,pool):
        config=validate_settings(settings)
        return ComplexPolicy(pool.observation['state'].shape[-1],size=settings['size'],contract=pool.contract,natural_press=config).to(settings['device'])
    def resume_schema(settings):validate_settings(settings);return RESUME_SCHEMA
    def pins(settings,out,extra=()):
        config=validate_settings(settings);_,_,_,paths=load_inputs(config['aligned_start']['input_dir'])
        return original[4](settings,out,list(extra)+[Path(__file__).resolve(),HERE/'inputs.py',HERE/'test_learning.py',*paths])
    rollout.GpuPool,runner._policy=Pool,policy
    runner.resume_schema,runner._validate_metadata_schema=resume_schema,validate_metadata
    runner._pins,runner.SCHEMA,gpu_environment.make_task=pins,SCHEMA,make_task
    try:yield
    finally:(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA,gpu_environment.make_task)=original


def train(args):
    if args.resume:
        settings=read_checkpoint(args.resume);config=settings['natural_press']
        if args.inputs and Path(args.inputs).resolve()!=Path(config['aligned_start']['input_dir']):raise ValueError('재개 입력 변경 불가')
        if args.arm_mode is not None and args.arm_mode!=config['arm_mode']:raise ValueError('재개 mask 변경 불가')
        for key in ('size','num_envs','horizon','seed'):
            if getattr(args,key) is not None and getattr(args,key)!=settings[key]:raise ValueError('재개 '+key+' 변경 불가')
        settings['updates']=args.updates
    else:
        defaults=dict(updates=args.updates,size='large',num_envs=64,horizon=32,seed=7)
        for key in ('size','num_envs','horizon','seed'):
            if getattr(args,key) is not None:defaults[key]=getattr(args,key)
        settings=build_settings(args.inputs,arm_mode=args.arm_mode,**defaults)
    if args.checkpoint_every is not None:settings['checkpoint_every']=args.checkpoint_every
    with runtime():return runner.run(settings,SimpleNamespace(out=args.out,resume=args.resume))

def replay_targets(row,known,config,controller,duration,reference=None):
    """끝점 기록을 유한한 전환 요청으로 구성한다. 실제 도착 성공은 native 원장만 판단한다."""
    events=sorted(known['events'],key=lambda e:e['onset_s'])
    active=controller.active[config['active_axes']]
    initial=torch.tensor(row['hold_target105'],device=controller.device,dtype=controller.reference.dtype)
    if reference is not None:
        if reference.get('candidate_valid') is not True:raise NotImplementedError('공통 기하 참조 후보가 유효하지 않음')
        points=[(float(p['time_s']),torch.tensor(p['q105'],device=controller.device,dtype=initial.dtype)) for p in reference['waypoints']]
        if (not points or points[0][0]!=0. or points[-1][0]<duration or
                any(not math.isfinite(t) or q.shape!=(105,) for t,q in points) or
                any(a[0]>b[0] for a,b in zip(points,points[1:]))):raise ValueError('참조 경유점의형상/시각이과제전체를덮지못함')
        if not torch.allclose(points[0][1][active],initial[active],atol=1e-6,rtol=0):raise ValueError('참조 경유점이실제정렬초기상태와다름')
    else:
        if any(a['onset_s']<b['end_s'] and b['onset_s']<a['end_s'] for i,a in enumerate(events) for b in events[i+1:]):
            raise NotImplementedError('동시 목표의 공통 손목·손가락 해가 아직 검증되지 않아 재생하지 않음')
        points=[(0.,initial),(.5,initial)]
        for i,event in enumerate(events):
            press=torch.tensor(event['press_q105'],device=controller.device,dtype=initial.dtype)
            points.append((event['onset_s']-(.5 if i==0 else .1),press));points.append((event['end_s'],press))
        end=events[-1]['end_s'];release=points[-1][1].clone()
        for finger in config['target_fingers']:
            slots=controller.active[17+4*(finger-1):21+4*(finger-1)];release[slots]=initial[slots]
        points.append((min(duration,end+.1),release));points.append((duration,release))
    for lo,q in points:
        if not bool(torch.isfinite(q).all()):raise ValueError('재생 요청 비유한')
        if bool(((q[active]<controller.action_low[config['active_axes']]-1e-6)|
                 (q[active]>controller.action_high[config['active_axes']]+1e-6)).any()):
            raise ValueError('재생 활성 요청각 native 한계 위반')
    rates=[]
    for (start,a),(end,b) in zip(points,points[1:]):
        if end<=start:
            if not torch.allclose(a[active],b[active],atol=1e-8,rtol=0):raise ValueError('재생 경유점 시각 충돌')
            continue
        ratio=1.875*(b[active]-a[active]).abs()/((end-start)*controller.rate[active])
        rates.append(dict(start_s=start,end_s=end,maximum_peak_rate_ratio=float(ratio.max()),
            requested_rate_feasible=bool((ratio<=1.+1e-6).all())))
    # controller가제한해내는명령과기하경로 자체의속도적합을구분한다.
    def target(now):
        for (start,a),(end,b) in zip(points,points[1:]):
            if now<=end:
                x=max(0.,min(1.,(now-start)/max(end-start,1e-12)));weight=x*x*x*(10-15*x+6*x*x)
                return a+weight*(b-a)
        return points[-1][1]
    return target,rates


def load_reference(path,config):
    if path is None:return None,[]
    path=Path(path).resolve();path.relative_to(ROOT);value=json.loads(path.read_text())
    if value.get('schema')!='guitar_learning.complex_press_reference.v1' or value.get('case_id')!=config['case_id'] or value.get('catalog_sha256')!=config['geometry_sha256']:
        raise ValueError('별도 재생 참조의schema/조건/catalog SHA 불일치')
    sources=value.get('source_sha256',{})
    if not isinstance(sources,dict) or not sources:raise ValueError('재생참조 출처SHA필요')
    paths=[path]
    for name,expected in sources.items():
        source=Path(name);source=source if source.is_absolute() else ROOT/source;source=source.resolve();source.relative_to(ROOT)
        if digest(source)!=expected:raise ValueError('재생참조 출처변경: '+str(source))
        paths.append(source)
    return value,paths


def replay(args):
    settings=build_settings(args.inputs,num_envs=1,updates=1,size='small',arm_mode=args.arm_mode)
    config=validate_settings(settings);_,row,known,_=load_inputs(args.inputs)
    reference,reference_paths=load_reference(args.reference_json,config)
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False);write(out/'settings.json',portable(settings))
    pool=None;pins=None;failure=None;episode=None;supported=True;rates=[];started=time.monotonic()
    try:
        random.seed(settings['seed']);np.random.seed(settings['seed']);torch.manual_seed(settings['seed']);torch.set_num_threads(1)
        with runtime(measure=True):
            pins=runner._pins(settings,out,extra=reference_paths);write(out/'inputs_before.json',pins)
            pool_class=rollout.GpuPool;pool=pool_class(settings,out)
        pool.environment.set_evaluation(True,full_song=True);pool.observation=pool.reset()[0]
        target,rates=replay_targets(row,known,config,pool.controller,pool.environment.task.duration_s,reference)
        for tick in range(math.ceil(pool.environment.task.duration_s*60)+2):
            desired=target((tick+1)/60)[pool.controller.active]
            action=natural.normalized_action(desired,pool.controller.reference[pool.controller.active],
                pool.controller.action_low,pool.controller.action_high)[None];action[:,33:]=0
            _,_,_,_,_,episodes=pool.step(action)
            if episodes:episode=episodes[0];write(out/'episode.json',episode);break
        if episode is None:raise RuntimeError('재생 에피소드 종료 원장 누락')
    except NotImplementedError as error:
        supported=False;failure=None;unavailable_reason=str(error)
    except BaseException as error:failure=repr(error)
    finally:
        cleanup=[]
        if pool:
            try:pool.close()
            except BaseException as error:cleanup.append(repr(error))
        changed=[p for p,value in (pins or {}).items() if not Path(p).is_file() or digest(p)!=value]
        closed=bool(pool and pool.closed and pool.scene.closed)
        completed=(episode is not None or not supported) and failure is None and closed and not changed and not cleanup
        safe=bool(episode and episode['valid'] and episode['song']['stage_success'] and
            not episode['song']['safety_invalidated'] and not episode['termination']['physical_failure'] and not episode['termination']['wrist_failure'])
        report=dict(schema=SCHEMA+'.replay',completed=completed,failure=failure,supported=supported,
            task_success=bool(completed and supported and safe),lifecycle_verified=closed and not cleanup,
            execution_status='completed' if supported else 'reference_unavailable',
            unavailable_reason=None if supported else unavailable_reason,reference_json=str(args.reference_json) if args.reference_json else None,
            reference_sha256=digest(args.reference_json) if args.reference_json else None,
            changed_inputs=changed,cleanup_errors=cleanup,scene_closed=closed,
            source_pins_unchanged=not changed,optimizer_updates=0,learned_policy=False,
            native_episode_measured=episode is not None,simultaneous_certified=bool(completed and supported and safe and episode.get('complex_timing',{}).get('overlap_pass',False) and episode.get('complex_timing',{}).get('timing_pass',False) and rates and all(r['requested_rate_feasible'] for r in rates) and any(a['onset_s']<b['end_s'] and b['onset_s']<a['end_s'] for i,a in enumerate(known['events']) for b in known['events'][i+1:])),
            controlled_axes=config['active_axes'],requested_path_rate_checks=rates,
            requested_path_rate_feasible=bool(rates and all(r['requested_rate_feasible'] for r in rates)),
            native_reference_pass=bool(completed and supported and safe and rates and all(r['requested_rate_feasible'] for r in rates) and episode.get('complex_timing',{}).get('overlap_pass',False) and episode.get('complex_timing',{}).get('internal_timing_pass' if config['case_id'] in ('B1','B2','S1','S2','S3','D1','D2') else 'timing_pass',False)),
            actual_control='기존 위치제어기의 native 범위·rate 제한 그대로 적용; 제어기 제한과 요청경로 적합은 별도',
            gpu_scene=pool.scene.diagnostics if pool else None,wall_s=time.monotonic()-started)
        write(out/'report.json',report)
    return report


def self_test():
    import unittest
    spec=importlib.util.spec_from_file_location('complex_press_cpu_tests',HERE/'test_learning.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    if not result.wasSuccessful():raise SystemExit(1)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true')
    commands=parser.add_subparsers(dest='command')
    for name in ('train','replay'):
        p=commands.add_parser(name);p.add_argument('--inputs',type=Path);p.add_argument('--out',required=True,type=Path)
        p.add_argument('--arm-mode',choices=('hold','free'))
        if name=='replay':p.add_argument('--reference-json',type=Path)
        if name=='train':
            p.add_argument('--updates',type=int,default=100);p.add_argument('--num-envs',type=int);p.add_argument('--size',choices=('small','medium','large'))
            p.add_argument('--horizon',type=int);p.add_argument('--seed',type=int);p.add_argument('--checkpoint-every',type=int);p.add_argument('--resume',type=Path)
    for name in ('evaluate','render'):
        p=commands.add_parser(name);p.add_argument('--checkpoint',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--num-envs',type=int)
    args=parser.parse_args()
    if args.self_test:return self_test()
    if args.command is None:parser.error('train/evaluate/render/replay 필요')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    torch.set_num_threads(1)
    if args.command=='train':
        if args.updates<1 or (args.checkpoint_every is not None and args.checkpoint_every<1):parser.error('양수 반복/저장 간격 필요')
        if not args.resume and args.inputs is None:parser.error('새 학습은 --inputs 필요')
        return train(args)
    if args.command=='replay':
        if args.inputs is None:parser.error('--inputs 필요')
        result=replay(args)
        if not result['completed']:raise SystemExit(1)
        return result
    read_checkpoint(args.checkpoint)
    with runtime(measure=True):
        if args.command=='evaluate':return runner.evaluate_checkpoint(args.checkpoint,args.out,num_envs=args.num_envs,scope='full_song')
        from guitar_learning.tool.demonstration.render_finger_skill import render
        return render(args.checkpoint,args.out,num_envs=args.num_envs,scope='full_song')


if __name__=='__main__':main()
