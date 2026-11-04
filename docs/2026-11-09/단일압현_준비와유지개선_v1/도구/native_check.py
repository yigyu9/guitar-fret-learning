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
SCHEMA='guitar_learning.press_preparation_hold.native.v1'
CONDITIONS=('baseline','joint_prepare','safe_route','robust_candidate','pad_feedback')


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


def make_frames(catalog,row,condition='baseline'):
    """joint_prepare만 팔12축과 담당 손가락4축을 함께 움직인다."""
    if condition not in CONDITIONS:raise ValueError('명시된 비교 조건 필요')
    points=row['transport_waypoints']
    if len(points)<2:raise ValueError('공통 시작과 최종 hover 경유점 필요')
    arm=catalog['action_indices'][:12]
    if any(not name.startswith('L_') for name in catalog['active_names'][:12]):raise ValueError('팔12 순서 필요')
    finger_id=int(row.get('finger_id',1))
    finger=catalog['action_indices'][17+4*(finger_id-1):21+4*(finger_id-1)]
    if len(finger)!=4 or not 1<=finger_id<=4:raise ValueError('담당 손가락4축 필요')
    moving=arm+finger if condition=='joint_prepare' else arm
    rates=torch.tensor([3. if j in arm else 4. for j in moving],dtype=torch.float64)
    initial=torch.tensor(row['q105'],dtype=torch.float64)
    frames=[];time=.5
    for i,point in enumerate(points):
        q=torch.tensor(point['q105'],dtype=torch.float64)
        if q.shape!=(105,) or not torch.isfinite(q).all():raise ValueError('유한 경유점105각 필요')
        rest=[j for j in range(105) if j not in moving]
        if not torch.equal(q[rest],initial[rest]):raise ValueError('운반 중 허용되지 않은 관절 변경 금지')
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
            if not math.isfinite(duration) or duration<0:raise ValueError('유한 양수 경유 시간 필요')
            duration=max(duration,float((1.875*(q[moving]-previous[moving]).abs()/rates).max()),1/60.)
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



class ConditionUnresolved(Exception):
    """설계 단계에서 해결되지 않은 조건이며 native 실행 오류와 구분한다."""


def readiness_components(height,tangent,facing,speed,failed):
    """원래 준비 임계값을 유지하고 각 불합격 원인을 따로 관측한다."""
    return dict(height=(height>=.005)&(height<=.015),tangent=tangent<=.005,
        facing=facing>=.1,wrist_speed=speed<=.05,unfailed=~failed)


def wrist_rotation_error(snapshot,env,goal):
    actual=multiply(conjugate(env.guitar_q),snapshot['body_state'][:,env.wrist_index,3:7])
    difference=multiply(conjugate(goal),actual)
    return 2*torch.atan2(torch.linalg.vector_norm(difference[:,:3],dim=-1),difference[:,3].abs())


def measure_press_substep(pool,snapshot):
    """240Hz 실제 patch 측정을 읽기만 한다. 원래 음 원장이나 접촉 판정을 바꾸지 않는다."""
    env=pool.environment;score=float(env._score_time()[0]);begin=float(env.onset[0]);end=float(env.end[0])
    overlap=max(0.,min(score,end)-max(score-1/240.,begin))
    candidate=bool(env.candidate[0,0]);wrong=bool(env.wrong[0,0])
    previous=pool.raw_previous or dict(candidate=candidate,wrong=wrong)
    interval_clean=candidate and previous['candidate'] and not wrong and not previous['wrong']
    distal=int(env.pad_indices[int(env.finger[0])-1]);indices=pool.controller.active[pool.config['active_axes']]
    record=dict(native_physics_step=int(snapshot['physics_step'][0]),policy_time_s=score,
        audible=begin<=score<end,audible_overlap_s=overlap,
        selected_patch_sample=int(env.surface_sample[0,0]),patch_position_geometry=bool(env.contact_geometry[0,0]),
        patch_facing_geometry=bool(env.contact_facing[0,0]),patch_loaded_geometry=bool(env.contact_loaded_target[0,0]),
        assigned_body_loaded=bool(env.surface_body_loaded[0,0]),candidate=candidate,wrong=wrong,
        clean=candidate and not wrong and begin<=score<end,clean_interval_s=overlap if interval_clean else 0.,
        height_m=float(env.surface_height[0,0]),tangent_m=float(torch.linalg.vector_norm(env.surface_delta[0,0,:2])),
        pad_normal_cos=float(env.surface_alignment[0,0]),surface_delta_G_m=env.surface_delta[0,0].cpu().tolist(),
        assigned_q4_rad=snapshot['q'][0,indices].cpu().tolist(),assigned_target4_rad=pool.controller.target[0,indices].cpu().tolist(),
        assigned_distal_body13=snapshot['body_state'][0,distal].cpu().tolist(),
        guitar_body13=snapshot['body_state'][0,env.guitar_index].cpu().tolist(),
        assigned_body_contact_force_N=snapshot['contact_force'][0,distal].cpu().tolist())
    pool.raw_previous=dict(candidate=candidate,wrong=wrong)
    return record


def summarize_substeps(rows):
    """단일 제어 끝점 대신 실제 240Hz 표본·겹침 시간을 집계한다. 성공은 원장 기준이다."""
    audible=sum(r['audible_overlap_s'] for r in rows)
    clean=sum(r['clean_interval_s'] for r in rows)
    streak=best=0.
    for r in rows:
        streak=streak+r['clean_interval_s'] if r['clean_interval_s']>0 else 0.
        best=max(best,streak)
    return dict(samples=len(rows),sampling_hz=240,audible_s=audible,clean_interval_s=clean,
        clean_fraction=clean/audible if audible else 0.,best_clean_streak_s=best,
        wrong_audible_s=sum(r['audible_overlap_s'] for r in rows if r['wrong']),
        patch_geometry_audible_s=sum(r['audible_overlap_s'] for r in rows if r['patch_position_geometry']),
        loaded_geometry_audible_s=sum(r['audible_overlap_s'] for r in rows if r['patch_loaded_geometry']),
        scope='Independent actual-substep diagnostic; unchanged native episode note ledger remains the success authority')


def propose_pad_feedback(measured,current_q4):
    """실측 FK의 3D 패드 오차와 Jacobian으로만 보정안을 계산한다. 명령은 확정하지 않는다."""
    point=np.asarray(measured['point_G_m'],dtype=float);goal=np.asarray(measured['target_G_m'],dtype=float)
    jacobian=np.asarray(measured['point_jacobian_G_m_per_rad'],dtype=float)
    normal_gradient=np.asarray(measured['normal_cos_gradient_per_rad'],dtype=float)
    current=np.asarray(current_q4,dtype=float);normal=float(measured['normal_cos'])
    if (point.shape!=(3,) or goal.shape!=(3,) or jacobian.shape!=(3,4) or normal_gradient.shape!=(4,) or
            current.shape!=(4,) or not np.isfinite(np.r_[point,goal,jacobian.ravel(),normal_gradient,current,normal]).all()):
        raise ValueError('실측 유한3D 패드와3x4 Jacobian/법선 gradient 필요')
    # 매 호출의 원래 기하 목표에서만 고정 편향을 계산한다. 직전 보정 목표를 누적하지 않는다.
    base_goal=goal.copy();base_distance=float(np.linalg.norm(base_goal-point))
    load_observed='body_loaded' in measured
    inward=bool(load_observed and not measured['body_loaded'] and not measured.get('wrong') and
        base_distance<=.0015 and normal>=.1)
    if inward:
        plane_normal=np.asarray(measured.get('press_plane_normal_G'),dtype=float)
        if plane_normal.shape!=(3,) or not np.isfinite(plane_normal).all() or abs(np.linalg.norm(plane_normal)-1.)>1e-6:
            raise ValueError('무하중 국소 보정에는 유한 단위 압현면 법선3개 필요')
        goal=base_goal-.0003*plane_normal
    error=goal-point;distance=float(np.linalg.norm(error));limited=error*min(1.,.003/max(distance,1e-12))
    # 방향 항은 위치 단위로 환산한 작은 보조 항이다. 높이 하나를 굽힘각으로 바꾸지 않는다.
    matrix=np.vstack((jacobian,.005*normal_gradient))
    rhs=np.r_[limited,.005*max(.15-normal,0.)]
    delta=matrix.T@np.linalg.solve(matrix@matrix.T+.002**2*np.eye(4),rhs)
    delta=np.clip(delta,-.08,.08)
    return dict(target_q4_rad=(current+delta).tolist(),delta_q4_rad=delta.tolist(),error_G_m=error.tolist(),
        error_norm_m=distance,clipped_error_G_m=limited.tolist(),damping_m_per_rad=.002,
        base_target_G_m=base_goal.tolist(),effective_target_G_m=goal.tolist(),
        body_load_observed=load_observed,unloaded_inward_bias_applied=inward,
        fixed_inward_bias_m=.0003 if inward else 0.,bias_accumulates=False,
        body_load_scope='native distal body net contact flag, not string pressure; fixed geometric attempt does not guarantee load')


def bounded_pad_request(nominal,previous,proposal,lower,upper,measured,previous_correction=None,dt=1/60.):
    """보정 총각도·변화율·기존4rad/s·native한계를 확인한 뒤에만 목표를 확정한다."""
    nominal,previous,lower,upper=[np.asarray(x,dtype=float) for x in (nominal,previous,lower,upper)]
    last=np.zeros(4) if previous_correction is None else np.asarray(previous_correction,dtype=float)
    desired=np.asarray(proposal['target_q4_rad'],dtype=float)
    if (any(x.shape!=(4,) for x in (nominal,previous,lower,upper,last,desired)) or
            not np.isfinite(np.r_[nominal,previous,lower,upper,last,desired,dt]).all() or dt<=0 or np.any(lower>upper)):
        raise ValueError('유한4축/관절한계/양수dt 필요')
    wrong_blocked=bool(measured.get('wrong'))
    held=bool(wrong_blocked or (measured.get('candidate') and measured.get('body_loaded',True) and not measured.get('wrong') and
        proposal['error_norm_m']<=.0015 and measured['normal_cos']>=.1))
    correction=np.clip((previous if held else desired)-nominal,-.12,.12)
    correction=last+np.clip(correction-last,-.5*dt,.5*dt)
    correction=np.clip(correction,-.12,.12)
    requested=np.clip(nominal+correction,previous-4.*dt,previous+4.*dt)
    requested=np.clip(requested,lower,upper)
    actual_correction=requested-nominal
    # 호출자가 넘긴 이전 명령/nominal 자체가 native 한계 밖이면 조용히 보정하지 않는다.
    if (np.any(previous<lower-1e-8) or np.any(previous>upper+1e-8) or
            np.any(nominal<lower-1e-8) or np.any(nominal>upper+1e-8)):
        raise ValueError('기준/이전명령이 native 한계를 벗어남')
    if np.any(np.abs(actual_correction)>.12+1e-8):raise ValueError('총보정각 한계와 속도제약이 양립하지 않음')
    if np.any(np.abs(actual_correction-last)>.5*dt+1e-8):raise ValueError('보정 변화율 한계 위반')
    return requested,dict(applied_correction_rad=actual_correction.tolist(),requested_q4_rad=requested.tolist(),
        wrong_feedback_hold=wrong_blocked,contact_hold_deadband_requested=held and not wrong_blocked,contact_hold_exact=held and bool(np.allclose(requested,previous,atol=1e-10,rtol=0)),
        maximum_correction_rad=.12,correction_rate_rad_s=.5,total_request_rate_rad_s=4.,normal_deadband_cos=.1,position_deadband_m=.0015)


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
        self.condition=self.config['diagnostic_condition']
        self.frames=make_frames(self.catalog,self.row,self.condition)
        self.substep_records=[];self.substep_stream=None;self.raw_previous=None
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
            passes=readiness_components(env.surface_height[:,0],torch.linalg.vector_norm(env.surface_delta[:,0,:2],dim=-1),
                env.surface_alignment[:,0],speed,failed)
            ready=torch.stack(list(passes.values()),-1).all(-1)
            stable=torch.where(ready&(now>=self.frames[-1]['time_s']),stable+1/60.,0.)
            ready=stable>=.5-1e-9
            trace.append(dict(tick=tick+1,stable_s=stable.cpu().tolist(),contact=contact.cpu().tolist(),wrong=wrong.cpu().tolist(),
                height_m=env.surface_height[:,0].cpu().tolist(),
                tangent_m=torch.linalg.vector_norm(env.surface_delta[:,0,:2],dim=-1).cpu().tolist(),
                facing_cos=env.surface_alignment[:,0].cpu().tolist(),wrist_speed_m_s=speed.cpu().tolist(),
                condition=self.condition,readiness_pass={k:v.cpu().tolist() for k,v in passes.items()},
                target_wrist_position_G_m=goal.cpu().tolist(),actual_wrist_position_G_m=env.local_bodies[:,env.wrist_index].cpu().tolist(),
                target_wrist_position_error_m=torch.linalg.vector_norm(env.local_bodies[:,env.wrist_index]-goal,dim=-1).cpu().tolist(),
                target_wrist_rotation_error_rad=wrist_rotation_error(snapshot,env,rotation).cpu().tolist(),
                planned_q105=q.cpu().tolist(),actual_q105=snapshot['q'].cpu().tolist(),target105=control.target.cpu().tolist(),
                target_q105_error_rad=(control.target-snapshot['q']).cpu().tolist(),
                planned_q105_error_rad=(q[None]-snapshot['q']).cpu().tolist(),physical_failure=env.tick_failure.cpu().tolist(),
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
            if self.substep_stream is not None:
                measured=measure_press_substep(self,sample)
                self.substep_records.append(measured)
                self.substep_stream.write(log_dumps(measured,allow_nan=False)+'\n')
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
    if 'diagnostic_condition' in document:catalog['diagnostic_condition']=document['diagnostic_condition']
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


def settings_for(catalog_path,row,seed,condition='baseline'):
    from guitar_learning.training.launch import settings_document
    from guitar_learning.song.task import make_task
    config=dict(schema=SCHEMA,diagnostic_condition=condition,condition='E4',distribution='v9',axes='goal4',song=row['song'],finger=row['finger'],
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
    report=dict(schema=SCHEMA,condition=args.condition,case=args.case,seed=args.seed,environments=1,start_denominator=1,
        optimizer_updates=0,policy_decisions=0,learned_policy=False,
        success_scope='현행 native 기하+body 하중+오압현 판정이며, 보정된 현 압력이나 음향 측정이 아님',
        requested_nonassigned_target_policy='bounded current targets; actual joints may move under physics',
        patch_sample_index_contract=dict(selected_patch_sample='GPU original pad sample axis index (all source samples)',
            chosen_selected_sample='index within valid source pad subset; used by local FK Jacobian only; not interchangeable'),
        completed=False,execution_completed=False,task_success=False,source_sha256_match_after=False)
    if args.condition=='pad_feedback':
        report['feedback_contract']=dict(activation_policy_s=2.5,scope='압현 램프 종료 후 국소 패드 추종; candidate가 없어도2.5초부터 작동하며 첫 접촉 개선은 미검증',
            maximum_correction_rad=.12,correction_rate_rad_s=.5,total_request_rate_rad_s=4.,
            wrong_behavior='hold previous bounded request, no extra pressing',state_injection=False,
            position_deadband_m=.0015,normal_deadband_cos=.1,
            unloaded_bias=dict(near_base_target_m=.0015,minimum_normal_cos=.1,inward_m=.0003,
                base_target_height_m=-.0005,effective_target_height_m=-.0008,accumulates=False,
                body_load='native distal body net contact flag; not calibrated string pressure or guaranteed guitar contact',
                scope='무하중/목표근처/정상방향/오압현없음일 때 고정 기하 시도; 하중 획득 보장 아님'))
    started=time.monotonic()
    try:
        signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
        random.seed(args.seed);np.random.seed(args.seed);torch.manual_seed(args.seed)
        catalog_path,catalog,row,source_paths=make_inputs(args,out)
        for label,value in (('document',catalog.get('diagnostic_condition')),('row',row.get('diagnostic_condition'))):
            if value!=args.condition and not(value is None and args.condition=='baseline'):
                raise ValueError(label+' 조건과 CLI condition 불일치')
        settings,config=settings_for(catalog_path,row,args.seed,args.condition)
        write(out/'settings.json',portable(settings))
        pins=runner._pins(settings,out,[Path(__file__).resolve(),HERE/'geometry.py',HERE/'copy_origin.json',catalog_path,*source_paths])
        write(out/'inputs_before.json',pins)
        if args.condition=='safe_route' and row.get('transport_path_candidate_valid') is not True:
            outcome='safe_route_unresolved';report['task_failure']='source shape 경로 검증 미해결; 안전 운반으로 주장하지 않고 GPU 실행 보류'
            raise ConditionUnresolved(report['task_failure'])
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
                if args.condition=='robust_candidate':
                    selected=geometry.select_robust_candidate(candidates)
                    chosen=candidates['candidates'][selected]
                    if not chosen['geometry_candidate']:raise ValueError('robust 선택이 기하 후보를 벗어남')
                else:chosen=min(options,key=lambda c:sum((c['q105'][i]-float(arrival[i]))**2 for i in indices))
                report['chosen_candidate']=chosen
                goal=torch.tensor(chosen['finger4_rad'],device=arrival.device,dtype=arrival.dtype)
                lower,upper=pool.scene.lower[indices],pool.scene.upper[indices]
                if not bool(((goal>=lower)&(goal<=upper)).all()):raise ValueError('손가락 native한계 이탈')
                feedback_previous=arrival[indices].cpu().numpy().copy();feedback_correction=np.zeros(4)
                phase='native_press';maximum_ticks=math.ceil(float(env._episode_duration()[0])*60)+2
                with (out/'trace.jsonl').open('a') as stream,(out/'substeps240.jsonl').open('a') as raw_stream:
                    pool.substep_stream=raw_stream
                    for tick in range(maximum_ticks):
                        requested=arrival[indices]+ramp((tick+1)/60.)*(goal-arrival[indices])
                        feedback=None
                        if args.condition=='pad_feedback' and (tick+1)/60.>=2.5:
                            observed=pool.scene.snapshot()
                            measured=geometry.pad_geometry_jacobian(planner,actual_state(pool.scene,observed),
                                observed['q'][0].cpu().numpy(),chosen['selected_sample'])
                            measured.update(candidate=bool(env.candidate[0,0]),wrong=bool(env.wrong[0,0]),
                                body_loaded=bool(env.surface_body_loaded[0,0]),press_plane_normal_G=planner.normal.tolist())
                            if measured['indices']!=indices:raise ValueError('feedback 담당 손가락 축 불일치')
                            proposal=propose_pad_feedback(measured,observed['q'][0,indices].cpu().numpy())
                            applied,feedback=bounded_pad_request(requested.cpu().numpy(),feedback_previous,proposal,
                                lower.cpu().numpy(),upper.cpu().numpy(),measured,feedback_correction)
                            feedback_correction=np.asarray(feedback['applied_correction_rad'])
                            requested=torch.tensor(applied,device=arrival.device,dtype=arrival.dtype)
                            feedback['measurement']=measured;feedback['proposal']=proposal
                        feedback_previous=requested.cpu().numpy().copy()
                        desired=control.target[:,control.active].clone();desired[:,config['active_axes']]=requested
                        actions=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
                        _,reward,cost,terminated,truncated,episodes=pool.step(actions)
                        snapshot=pool.scene.snapshot();score=float(env._score_time()[0]);audible=bool((env.onset[0]<=score)&(score<env.end[0]))
                        record=dict(tick=tick+1,policy_time_s=score,native_physics_step=int(snapshot['physics_step'][0]),audible=audible,
                            requested_finger4_rad=requested.cpu().tolist(),actual_q105=snapshot['q'][0].cpu().tolist(),target105=control.target[0].cpu().tolist(),
                            feedback=feedback,assigned_q4_rad=snapshot['q'][0,indices].cpu().tolist(),assigned_target4_rad=control.target[0,indices].cpu().tolist(),
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
                pool.substep_stream=None
                report['trace_summary']=summarize(trace,indices)
        report['execution_completed']=True
    except ConditionUnresolved:
        report['execution_completed']=True
    except BaseException as exc:
        failure=type(exc).__name__+': '+str(exc);report['error_phase']=phase
    finally:
        if pool is not None:
            report['preparation']=pool.preparation_records
            report['substep240_summary']=summarize_substeps(pool.substep_records)
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
            completed=bool(report['execution_completed'] and failure is None and report['source_sha256_match_after'] and report['scene_closed'] and report['pool_closed']),
            task_success=bool(outcome=='press_success' and failure is None and report['source_sha256_match_after'] and report['scene_closed'] and report['pool_closed']),preparation_ready=bool(pool and pool.preparation_records and pool.preparation_records[-1]['ready_count']==1))
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
    # baseline의 팔 경유점 시간/요청각 수식과 준비 경계는 원본 정의 그대로다.
    h=torch.tensor([.005,.015,.004,.016,.01,.01,.01,.01])
    t=torch.tensor([.005,.005,0.,0.,.006,0.,0.,0.])
    f=torch.tensor([.1,.1,1.,1.,1.,.09,1.,1.]);v=torch.tensor([.05,.05,0.,0.,0.,0.,.051,0.])
    failed=torch.tensor([False]*7+[True])
    components=readiness_components(h,t,f,v,failed)
    original=((h>=.005)&(h<=.015)&(t<=.005)&(f>=.1)&(v<=.05)&~failed)
    assert torch.equal(torch.stack(list(components.values()),-1).all(-1),original)
    common=[0.]*105;hover=common.copy();hover[0]=.1
    baseline_row=dict(q105=common,final_hover_q105=hover,transport_waypoints=[dict(q105=q,wrist_position_G_m=[0.,0.,0.],
        wrist_quaternion_G_xyzw=[0.,0.,0.,1.],minimum_duration_s=2.) for q in (common,hover)])
    baseline_frames=make_frames(catalog,baseline_row,'baseline')
    assert baseline_frames[-1]['time_s']==2.5
    for tick in range(31):
        elapsed=.5+tick/30*2.;fraction=(elapsed-.5)/2.
        expected=.1*(fraction**3*(10-15*fraction+6*fraction*fraction))
        assert abs(float(sample_frames(baseline_frames,elapsed)[0][0])-expected)<1e-7
    # joint_prepare만 담당 손가락을 허용하고 다른 손가락/엄지는 거부한다.
    common=[0.]*105;hover=common.copy();hover[17]=.4
    row=dict(finger_id=1,q105=common,transport_waypoints=[dict(q105=q,wrist_position_G_m=[0.,0.,0.],
        wrist_quaternion_G_xyzw=[0.,0.,0.,1.],minimum_duration_s=.001) for q in (common,hover)],final_hover_q105=hover)
    try:make_frames(catalog,row,'baseline')
    except ValueError:pass
    else:raise AssertionError('baseline에서 손가락 운반 허용')
    joint_frames=make_frames(catalog,row,'joint_prepare')
    assert joint_frames[-1]['time_s']-.5>=1.875*.4/4.-1e-12
    row['transport_waypoints'][1]['q105'][21]=.1
    try:make_frames(catalog,row,'joint_prepare')
    except ValueError:pass
    else:raise AssertionError('joint_prepare에서 다른 손가락 변경 허용')
    measured=dict(point_G_m=[0.,0.,0.],target_G_m=[.001,-.001,.001],normal_cos=1.,
        point_jacobian_G_m_per_rad=[[.02,0,0,0],[0,.02,0,0],[0,0,.02,0]],
        normal_cos_gradient_per_rad=[0.,0.,0.,0.],candidate=False,wrong=False,body_loaded=True,press_plane_normal_G=[0.,0.,1.])
    proposal=propose_pad_feedback(measured,[0.]*4)
    assert proposal['delta_q4_rad'][0]>0 and proposal['delta_q4_rad'][1]<0 and proposal['delta_q4_rad'][2]>0
    request,details=bounded_pad_request([0.]*4,[0.]*4,proposal,[-1.]*4,[1.]*4,measured)
    assert max(abs(request))<=.5/60.+1e-12
    previous=np.zeros(4);correction=np.zeros(4)
    far=dict(proposal,target_q4_rad=[.8]*4)
    for _ in range(120):
        value,detail=bounded_pad_request([0.]*4,previous,far,[-1.]*4,[.1]*4,measured,correction)
        assert np.all(np.abs(value-previous)<=4./60.+1e-12) and np.all(value<=.1+1e-12)
        assert np.all(np.abs(value)<=.12+1e-12)
        correction=np.asarray(detail['applied_correction_rad']);previous=value
    held=dict(measured,candidate=True,target_G_m=[0.,0.,0.])
    hold_proposal=propose_pad_feedback(held,[0.]*4)
    request,details=bounded_pad_request([0.]*4,[0.]*4,hold_proposal,[-1.]*4,[1.]*4,held)
    assert details['contact_hold_exact'] and np.array_equal(request,np.zeros(4))
    blocked=dict(measured,wrong=True,candidate=False)
    request,details=bounded_pad_request([0.]*4,[0.]*4,proposal,[-1.]*4,[1.]*4,blocked)
    assert details['wrong_feedback_hold'] and np.array_equal(request,np.zeros(4))
    # 무하중이며 목표 근처일 때만 원래 -.5mm에서 비누적 -.8mm로 시도한다.
    unloaded=dict(measured,body_loaded=False,point_G_m=[0.,0.,-.0005],target_G_m=[0.,0.,-.0005])
    first=propose_pad_feedback(unloaded,[0.]*4)
    assert first['unloaded_inward_bias_applied'] and not first['bias_accumulates']
    np.testing.assert_allclose(first['effective_target_G_m'],[0.,0.,-.0008],rtol=0,atol=1e-15)
    for _ in range(100):
        again=propose_pad_feedback(unloaded,[0.]*4)
        assert again['effective_target_G_m']==first['effective_target_G_m']
    assert unloaded['target_G_m']==[0.,0.,-.0005]
    at_bias=propose_pad_feedback(dict(unloaded,point_G_m=[0.,0.,-.0008]),[0.]*4)
    assert at_bias['effective_target_G_m']==first['effective_target_G_m']
    for changed in (dict(unloaded,body_loaded=True),dict(unloaded,wrong=True),
            dict(unloaded,point_G_m=[.005,0.,-.0005]),dict(unloaded,normal_cos=0.)):
        result=propose_pad_feedback(changed,[0.]*4)
        assert not result['unloaded_inward_bias_applied'] and result['effective_target_G_m']==changed['target_G_m']
    loaded_hold=dict(unloaded,body_loaded=True,candidate=True)
    result=propose_pad_feedback(loaded_hold,[0.]*4)
    value,details=bounded_pad_request([0.]*4,[0.]*4,result,[-1.]*4,[1.]*4,loaded_hold)
    assert details['contact_hold_exact'] and np.array_equal(value,np.zeros(4))
    for bad in (dict(measured,point_G_m=[float('nan'),0,0]),dict(measured,point_jacobian_G_m_per_rad=[[0.]*4])):
        try:propose_pad_feedback(bad,[0.]*4)
        except ValueError:pass
        else:raise AssertionError('비유한/잘못된 Jacobian 입력 허용')
    assert summarize([],list(range(4)))['audible_clean_fraction']==0
    assert summarize_substeps([])['samples']==0
    print('CPU 자체검사 통과: 시간곡선/경유점 속도, joint 준비 허용축, 다른 손가락 변경 거부, 3D 보정/한계/접촉 hold/무하중 고정편향 비누적/비유한 거부. GPU 실행 없음.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true');parser.add_argument('--case');parser.add_argument('--out')
    parser.add_argument('--condition',choices=CONDITIONS,default='baseline');parser.add_argument('--geometry');parser.add_argument('--catalog');parser.add_argument('--provenance');parser.add_argument('--seed',type=int,default=7)
    args=parser.parse_args()
    if args.self_test:self_test();return 0
    if not args.case or not args.out or (bool(args.geometry)==bool(args.catalog)):parser.error('case/out 및 geometry 또는 catalog/provenance 필요')
    return run(args)


if __name__=='__main__':raise SystemExit(main())
