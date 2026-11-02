"""1~14프렛 336조합의 실제 운반과 손가락 압현을 검사한다. 학습은 수행하지 않는다.

운반/도착손목 유지 핵심은 copy_origin.json의 기존 소스에서 명시적으로 복사했다.
과거 Python을 import하지 않는다. 자체 준비 검사와 실제 도착 FK를 새로 생성하며
기하 후보와 물리 성공을 구분한다. 물리 상태는 최초 공통 reset 이후 재주입하지 않는다.
"""
if __name__=='__main__' and '--self-test' not in __import__('sys').argv:import isaacgym
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import sys
import time
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import numpy as np
import torch
from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.training import rollout, finger_skill_runner as runner
from guitar_learning.gpu.scene import GpuScene
from guitar_learning.gpu.environment import TensorSongEnvironment, FAILURE_REASONS
from guitar_learning.gpu.control import apply,conjugate,multiply
from guitar_learning.tool.validation.press_acquisition import trajectory_actions
from guitar_learning.tool.experiments.short_finger_learning.wrist import (
    interpolated_pose,wrist_error_and_jacobian,bounded_wrist_target,_wrist_position_groups)
from guitar_learning.training.training_log_io import dumps as log_dumps
ORIGINAL_POOL=rollout.GpuPool
SCHEMA='guitar_learning.range336.native_single_press.v1'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    """검사 중단 때도 기존 완결 문서를 손상하지 않는 원자 저장."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(log_dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def ramp(time_s):
    fraction=max(0.,min(1.,(time_s-.5)/2.))
    return fraction**3*(10-15*fraction+6*fraction*fraction)


def make_frames(catalog,row):
    """서로 다른 손가락을 움직이지 않는 팔12축 경유점만 허용한다."""
    points=row['transport_waypoints']
    if len(points)<2:raise ValueError('공통 시작과 최종 hover 경유점 필요')
    arm=catalog['action_indices'][:12]
    if any(not name.startswith('L_') for name in catalog['active_names'][:12]):raise ValueError('팔12 순서 필요')
    initial=torch.tensor(row['q105'],dtype=torch.float64)
    frames=[];time=.5
    for i,point in enumerate(points):
        q=torch.tensor(point['q105'],dtype=torch.float64)
        if q.shape!=(105,) or not torch.isfinite(q).all():raise ValueError('유한 경유점105각 필요')
        rest=[j for j in range(105) if j not in arm]
        if not torch.equal(q[rest],initial[rest]):raise ValueError('운반 중 비팔 관절 변경 금지')
        active=q[catalog['action_indices']]
        if bool(((active<torch.tensor(catalog['action_lower'],dtype=active.dtype)-1e-7)|(active>torch.tensor(catalog['action_upper'],dtype=active.dtype)+1e-7)).any()):
            raise ValueError('운반 경유점 행동 범위 초과')
        if i==0:
            if not torch.equal(q,initial):raise ValueError('첫 운반 경유점은 공통 초기각이어야 함')
            frames.append(dict(time_s=0.,q105=q.tolist(),**{k:point[k] for k in ('wrist_position_G_m','wrist_quaternion_G_xyzw')}))
            frames.append(dict(frames[0],time_s=.5))
        else:
            duration=float(point.get('minimum_duration_s',2.))
            previous=torch.tensor(frames[-1]['q105'],dtype=torch.float64)
            duration=max(duration,float((1.875*(q[arm]-previous[arm]).abs()/3.).max()),1/60.)
            time+=duration
            frames.append(dict(time_s=time,q105=q.tolist(),**{k:point[k] for k in ('wrist_position_G_m','wrist_quaternion_G_xyzw')}))
    if max(abs(a-b) for a,b in zip(frames[-1]['q105'],row['final_hover_q105']))>1e-7:
        raise ValueError('최종 경유점과 hover각 불일치')
    return frames


def sample_frames(frames,time_s,device='cpu'):
    index=next((i for i in range(len(frames)-1) if time_s<=frames[i+1]['time_s']),len(frames)-2)
    a,b=frames[index:index+2]
    fraction=min(1.,max(0.,(time_s-a['time_s'])/(b['time_s']-a['time_s'])))
    smooth=fraction**3*(10-15*fraction+6*fraction*fraction)
    q=torch.tensor(a['q105'],dtype=torch.float32,device=device)
    q=q+smooth*(torch.tensor(b['q105'],dtype=torch.float32,device=device)-q)
    pa=torch.tensor([a['wrist_position_G_m']],dtype=torch.float32,device=device)
    pb=torch.tensor([b['wrist_position_G_m']],dtype=torch.float32,device=device)
    qa=torch.tensor([a['wrist_quaternion_G_xyzw']],dtype=torch.float32,device=device)
    qb=torch.tensor([b['wrist_quaternion_G_xyzw']],dtype=torch.float32,device=device)
    position,quaternion=interpolated_pose(pa,qa,pb,qb,pa.new_tensor([smooth]))
    return q,position,quaternion,index



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
        self.frames=make_frames(self.catalog,self.row)
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
            q,goal,rotation,_=sample_frames(self.frames,now,scene.device)
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



def generate_bundle(bundle,case):
    """현행 builder로 3~4.5초의 단일 가상 음을 만든다. 줄은 1=높은 e현이다."""
    import wave
    from guitar_learning.tool import build_fret_training_data,build_strike_training_data,build_strike_plan,register_song_bundle
    finger=('index','middle','ring','pinky').index(case['finger'])+1
    standard=case['string_standard_1based'];string=6-standard;fret=case['fret']
    if not (1<=standard<=6 and 1<=fret<=14):raise ValueError('표준 줄1~6 / 프렛1~14 필요')
    mapping=dict(purpose=SCHEMA,convention='string 0 = low-E',
        notes=[dict(t_on=0.,t_off=1.5,string=string,fret=fret,midi=(40,45,50,55,59,64)[string]+fret,finger=finger,barre=False,grip=None)],
        presses=[dict(finger=finger,string=string,fret=fret,barre=False,t_press=0.,t_release=1.5,strikes=[0.])],
        hand=[dict(t=0.,P=max(1,min(22,fret-finger+1)),grip=None)],stats=dict(dropped_invalid_fret=0),diagnostics=[],violations=[])
    path=bundle/'mapping/fingering.json';write(path,mapping)
    register_song_bundle.write_tablature_if_missing(bundle)
    audio=bundle/'source/audio.wav';audio.parent.mkdir(exist_ok=True)
    with wave.open(str(audio),'wb') as stream:
        stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000);stream.writeframes(b'\0\0'*24000)
    training=bundle/'training';training.mkdir(exist_ok=True)
    build_fret_training_data.main(['--fingering',str(path),'--audio',str(audio),'--out',str(training/'fret_training.json')])
    build_strike_training_data.main([str(path),'--out',str(training/'strike_training.json')])
    build_strike_plan.main([str(training/'strike_training.json'),'--out',str(training/'strike_plan.json')])
    register_song_bundle.write_manifest(bundle.name,bundle,dict(registration_mode=SCHEMA,
        generator=str(Path(__file__).resolve().relative_to(ROOT)),generator_sha256=digest(__file__),audio='1.5 seconds silence; clock only'))


def make_inputs(args,out):
    """새 geometry 결과 또는 원본 JSON을 복사한다. native 검증 근거를 조작하지 않는다."""
    if args.catalog:
        document=json.loads(Path(args.catalog).read_text())
        rows=[r for r in document['goals'] if r.get('case_id',r.get('case'))==args.case]
        if len(rows)!=1:raise ValueError('단일 원본 목표 필요')
        row=copy.deepcopy(rows[0]);catalog={k:copy.deepcopy(v) for k,v in document.items() if k!='goals'}
        source_paths=[Path(args.catalog)]
        if not args.provenance:raise ValueError('원본 catalog에는 provenance 필수')
        provenance=json.loads(Path(args.provenance).read_text());source_paths.append(Path(args.provenance))
        if digest(args.catalog)!=provenance['catalog_sha256']:raise ValueError('원본 catalog SHA 불일치')
        physical=dict(provenance['active_physical_inputs'])
    else:
        document=json.loads(Path(args.geometry).read_text());source_paths=[Path(args.geometry)]
        rows=[r for r in document['rows'] if r.get('case_id',r.get('case'))==args.case]
        if len(rows)!=1:raise ValueError('geometry의 단일 목표 필요')
        row=copy.deepcopy(rows[0]);catalog=copy.deepcopy(document['catalog_base'])
        physical=dict(document['source_sha256'])
        row['q105']=copy.deepcopy(row['transport_waypoints'][0]['q105'])
        row['final_hover_q105']=copy.deepcopy(row['transport_waypoints'][-1]['q105'])
        row['hold_target105']=copy.deepcopy(row['final_hover_q105'])
    for name,expected in physical.items():
        path=Path(name);path=path if path.is_absolute() else ROOT/path
        path=path.resolve();path.relative_to(ROOT)
        if digest(path)!=expected:raise ValueError('원본 물리 입력 SHA 불일치: '+str(path))
    # 과거 판정 결과는 현재 검사의 증거로 취급하지 않는다.
    row.pop('native_verified',None);row.pop('native_validation',None)
    row['case']=row['case_id']=args.case
    finger=row['finger'];finger=('index','middle','ring','pinky')[finger-1] if isinstance(finger,int) else finger
    row['finger']=finger;row['finger_id']=('index','middle','ring','pinky').index(finger)+1
    standard=row.get('physical_string',int(row['string'])+1)
    case=dict(finger=finger,string_standard_1based=standard,fret=int(row['fret']))
    row['string']=standard-1;row['physical_string']=standard
    row['song']='range336_'+args.case
    bundle=out/'inputs/song_bundles'/row['song'];generate_bundle(bundle,case);row['bundle']=str(bundle)
    catalog['goals']=[row];path=out/'inputs/catalog.json';write(path,catalog)
    write(out/'inputs/origin.json',dict(source_sha256={str(p.resolve()):digest(p) for p in source_paths},
        active_physical_inputs=physical,original_native_results_reused=False))
    return path,catalog,row,source_paths+[Path(name) if Path(name).is_absolute() else ROOT/name for name in physical]


def settings_for(catalog_path,row,seed):
    from guitar_learning.training.launch import settings_document
    from guitar_learning.song.task import make_task
    config=dict(schema=SCHEMA,condition='E4',distribution='v9',axes='goal4',song=row['song'],finger=row['finger'],
        geometry=str(catalog_path),geometry_sha256=digest(catalog_path),
        active_axes=natural.active_axes('goal4',row['finger']),observation_extra_fields=natural.EXTRA_FIELDS,
        phase_arm_support=False,initial_distribution=dict(v9_fraction=1.),
        transport=dict(schema=SCHEMA,preparation='self-generated actual common-v9 transport; no prior native validation claimed'))
    settings=settings_document(song='virtual_finger_v9_middle_s3_f6',size='large',num_envs=1,
        horizon=32,updates=1,seed=seed,checkpoint_every=1,device='cuda:0',physics='gpu')
    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
    if len(task.targets)!=1 or (task.targets[0].string,task.targets[0].fret,task.targets[0].finger)!=(row['string'],row['fret'],row['finger_id']):
        raise ValueError('가상 음과 catalog 불일치')
    if (task.targets[0].onset_s,task.targets[0].end_s)!=(3.,4.5):raise ValueError('음 구간3~4.5초 필요')
    settings['song_training'].update(song_id=row['song'],bundle=row['bundle'],target_count=1,
        control_ticks=task.provenance['song']['control_ticks'],episode_duration_s=task.duration_s)
    settings['phrase_events']=task.provenance['song']['source_event_count'];settings['natural_press']=config
    return settings,config


def actual_state(scene,snapshot):
    """실제 q와 모든 논리 body 자세를 FK 기준으로 변환한다. 상태를 scene에 쓰지 않는다."""
    state=copy.deepcopy(scene.contract['state']);body=snapshot['body_state'][0].cpu().tolist();offset=0
    for kind in ('human','guitar','chair'):
        for row,values in zip(state[kind+'_body_states'],body[offset:]):
            row['pose']['p']=dict(zip('xyz',values[:3]));row['pose']['r']=dict(zip('xyzw',values[3:7]))
            row['vel']['linear']=dict(zip('xyz',values[7:10]));row['vel']['angular']=dict(zip('xyz',values[10:13]))
        offset+=len(state[kind+'_body_states'])
    for row,q,qd in zip(state['human_dof_states'],snapshot['q'][0].cpu().tolist(),snapshot['qd'][0].cpu().tolist()):
        row.update(pos=q,vel=qd)
    return state


def summarize(trace,indices):
    audible=[r for r in trace if r['audible']]
    nong=[i for i in range(105) if i not in indices]
    first=trace[0]['actual_q105'] if trace else [0.]*105
    return dict(audible_control_ticks=len(audible),audible_clean_control_ticks=sum(r['clean'] for r in audible),
        audible_clean_fraction=sum(r['clean'] for r in audible)/len(audible) if audible else 0.,
        audible_wrong_control_s=sum(r['wrong'] for r in audible)/60.,
        assigned_tracking_max_error_rad=max((max(abs(r['actual_q105'][i]-r['target105'][i]) for i in indices) for r in trace),default=None),
        nonassigned_actual_max_change_from_first_policy_tick_rad=max((max(abs(r['actual_q105'][i]-first[i]) for i in nong) for r in trace),default=None),
        scope='60Hz endpoint samples; episode note ledger supplies native 240Hz clean streak/hold criterion. Nonassigned requested targets are held, actual joints remain physical.')


def run(args):
    import geometry
    from guitar_learning.native.paths import verify
    from guitar_learning.portability import portable
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=False)
    pool=None;pins=None;trace=[];episode=None;failure=None;phase='inputs';outcome=None
    report=dict(schema=SCHEMA,case=args.case,seed=args.seed,environments=1,start_denominator=1,
        optimizer_updates=0,policy_decisions=0,learned_policy=False,
        success_scope='현행 native 기하+body 하중+오압현 판정이며, 보정된 현 압력이나 음향 측정이 아님',
        requested_nonassigned_target_policy='bounded current targets; actual joints may move under physics',
        completed=False,execution_completed=False,task_success=False,source_sha256_match_after=False)
    started=time.monotonic()
    try:
        signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
        random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
        catalog_path,catalog,row,source_paths=make_inputs(args,out)
        settings,config=settings_for(catalog_path,row,args.seed)
        write(out/'settings.json',portable(settings))
        pins=runner._pins(settings,out,[Path(__file__).resolve(),HERE/'geometry.py',HERE/'copy_origin.json',catalog_path,*source_paths])
        write(out/'inputs_before.json',pins)
        phase='preparation';pool=LearningPool(settings,out);pool.environment.set_evaluation(True,full_song=True)
        try:pool.prepare()
        except RuntimeError as exc:
            if str(exc).startswith('PreparationFailed:'):
                outcome='preparation_failed';report['task_failure']=str(exc)
            else:raise
        if outcome is None:
            phase='arrived_finger_ik';env,control=pool.environment,pool.controller
            snapshot=pool.scene.snapshot();arrival=snapshot['q'][0].clone();state=actual_state(pool.scene,snapshot)
            write(out/'arrival.json',dict(state=state,q105=arrival.cpu().tolist(),native_body_state13=snapshot['body_state'][0].cpu().tolist()))
            planner=geometry.Planner(catalog,row)
            candidates=geometry.press_candidates(planner,state,arrival.cpu().numpy(),pool.scene.lower.cpu().numpy(),pool.scene.upper.cpu().numpy())
            write(out/'press_candidates.json',candidates)
            indices=candidates['indices']
            if [control.active[i].item() for i in config['active_axes']]!=indices:raise ValueError('담당 손가락 4축 순서 불일치')
            options=[c for c in candidates['candidates'] if c['geometry_candidate']]
            if not options:outcome='finger_ik_unresolved'
            else:
                chosen=min(options,key=lambda c:sum((c['q105'][i]-float(arrival[i]))**2 for i in indices))
                report['chosen_candidate']=chosen
                goal=torch.tensor(chosen['finger4_rad'],device=arrival.device,dtype=arrival.dtype)
                lower,upper=pool.scene.lower[indices],pool.scene.upper[indices]
                if not bool(((goal>=lower)&(goal<=upper)).all()):raise ValueError('손가락 native한계 이탈')
                phase='native_press';maximum_ticks=math.ceil(float(env._episode_duration()[0])*60)+2
                with (out/'trace.jsonl').open('a') as stream:
                    for tick in range(maximum_ticks):
                        requested=arrival[indices]+ramp((tick+1)/60.)*(goal-arrival[indices])
                        desired=control.target[:,control.active].clone();desired[:,config['active_axes']]=requested
                        actions=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
                        _,reward,cost,terminated,truncated,episodes=pool.step(actions)
                        snapshot=pool.scene.snapshot();score=float(env._score_time()[0]);audible=bool((env.onset[0]<=score)&(score<env.end[0]))
                        record=dict(tick=tick+1,policy_time_s=score,native_physics_step=int(snapshot['physics_step'][0]),audible=audible,
                            requested_finger4_rad=requested.cpu().tolist(),actual_q105=snapshot['q'][0].cpu().tolist(),target105=control.target[0].cpu().tolist(),
                            assigned_q4_rad=snapshot['q'][0,indices].cpu().tolist(),assigned_target4_rad=control.target[0,indices].cpu().tolist(),
                            height_m=float(env.surface_height[0,0]),tangent_m=float(torch.linalg.vector_norm(env.surface_delta[0,0,:2])),
                            candidate=bool(env.candidate[0,0]),wrong=bool(env.wrong[0,0]),clean=bool(env.candidate[0,0]&~env.wrong[0,0]) and audible,
                            assigned_body_loaded=bool(env.surface_body_loaded[0,0]),guitar_displacement_m=float(torch.linalg.vector_norm(env.guitar_delta[0])),
                            guitar_rotation_rad=float(torch.linalg.vector_norm(env.guitar_rotation[0])),
                            physical_reasons=[n for n,f in zip(FAILURE_REASONS,env.tick_failure[0].cpu().tolist()) if f],
                            terminated=bool(terminated[0]),truncated=bool(truncated[0]),reward=float(reward[0]),cost=float(cost[0]))
                        trace.append(record);stream.write(log_dumps(record,allow_nan=False)+'\n')
                        if episodes:
                            if len(episodes)!=1 or episodes[0]['env_id']!=0:raise RuntimeError('분모1 에피소드 불일치')
                            episode=episodes[0];write(out/'episode.json',episode)
                            outcome='press_success' if episode.get('song',{}).get('stage_success') else 'native_press_failed'
                            break
                        if bool(terminated[0]|truncated[0]):raise RuntimeError('종료 원장 누락')
                if outcome is None:raise RuntimeError('에피소드 시간 초과')
                report['trace_summary']=summarize(trace,indices)
        report['execution_completed']=True
    except BaseException as exc:
        failure=type(exc).__name__+': '+str(exc);report['error_phase']=phase
    finally:
        if pool is not None:
            report['preparation']=pool.preparation_records
            report['reset_calls']=pool.scene.reset_calls
            try:pool.close()
            except BaseException as exc:failure=(failure+'; ' if failure else '')+'정리 오류: '+repr(exc)
            report['pool_closed']=pool.closed;report['scene_closed']=bool(pool.scene.closed)
        else:report.update(pool_closed=True,scene_closed=True)
        if pins is not None:
            try:report['source_sha256_match_after']=bool(verify(pins))
            except Exception as exc:report['seal_error']=repr(exc)
            if not report['source_sha256_match_after']:failure=(failure+'; ' if failure else '')+'종료 SHA 불일치'
        report.update(outcome=outcome or 'inspection_error',failure=failure,ticks=len(trace),elapsed_s=time.monotonic()-started,
            completed=bool(report['execution_completed'] and failure is None and report['source_sha256_match_after'] and report['scene_closed']),
            task_success=outcome=='press_success',preparation_ready=bool(pool and pool.preparation_records and pool.preparation_records[-1]['ready_count']==1))
        write(out/'report.json',report)
    print(log_dumps({k:report[k] for k in ('completed','outcome','failure','task_success','elapsed_s')},ensure_ascii=False))
    return 0 if report['completed'] else 1


def self_test():
    assert ramp(-1)==ramp(.5)==0 and ramp(2.5)==ramp(5)==1 and abs(ramp(1.5)-.5)<1e-12
    assert all(ramp(i/100)<=ramp((i+1)/100) for i in range(300))
    import tempfile
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'state.json';write(p,dict(value=.1));assert json.loads(p.read_text())==dict(value=.1)
    common=[0.]*105;hover=common.copy();hover[0]=.1
    points=[dict(q105=q,wrist_position_G_m=[0.,0.,0.],wrist_quaternion_G_xyzw=[0.,0.,0.,1.]) for q in (common,hover)]
    catalog=dict(action_indices=list(range(39)),active_names=['L_'+str(i) for i in range(12)]+['finger']*27,action_lower=[-1.]*39,action_upper=[1.]*39)
    row=dict(q105=common,transport_waypoints=points,final_hover_q105=hover)
    frames=make_frames(catalog,row);assert sample_frames(frames,0)[0].shape==(105,)
    row['transport_waypoints'][1]['q105'][40]=.1
    try:make_frames(catalog,row)
    except ValueError:pass
    else:raise AssertionError('운반 비팔 축 변경 허용')
    assert summarize([],list(range(4)))['audible_clean_fraction']==0
    print('CPU 자체검사 통과: 시간곡선, 원자 저장, 경유점 유한성/비팔 불변, 빈 시도 분모. GPU 실행 없음.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true');parser.add_argument('--case');parser.add_argument('--out')
    parser.add_argument('--geometry');parser.add_argument('--catalog');parser.add_argument('--provenance');parser.add_argument('--seed',type=int,default=7)
    args=parser.parse_args()
    if args.self_test:self_test();return 0
    if not args.case or not args.out or (bool(args.geometry)==bool(args.catalog)):parser.error('case/out 및 geometry 또는 catalog/provenance 필요')
    return run(args)


if __name__=='__main__':raise SystemExit(main())
