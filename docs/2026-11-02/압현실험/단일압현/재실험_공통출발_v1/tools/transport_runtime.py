"""공통 준비 자세에서 자유 기타의 목표 hover까지 실제 제어로 운반한다.

A=정렬 reset 유지, B=공통 출발 요청각 운반, C=동일 운반+실제 손목 피드백.
운반은 정책·보상 시계와 분리된 진단이며 native 상태는 최초 reset에서만 쓴다.
기존 PD·속도·힘 상한·물리 실패는 유지하고 이동 손목 corridor를 별도 적용한다.
"""
if __name__=='__main__':
    import isaacgym
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import torch
from guitar_learning.gpu.scene import GpuScene, _body_row
from guitar_learning.gpu.control import BatchedController, apply, conjugate, multiply
from guitar_learning.gpu.environment import TensorSongEnvironment, FAILURE_REASONS
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.tool.validation.press_acquisition import trajectory_actions
from guitar_learning.tool.experiments.short_finger_learning.wrist import (
    interpolated_pose,wrist_error_and_jacobian,bounded_wrist_target,_wrist_position_groups)
SCHEMA='guitar_learning.single18.common_transport.v1'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def row_identity(row):
    clean={k:v for k,v in row.items() if k not in ('native_verified','native_validation')}
    return hashlib.sha256(json.dumps(clean,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def load_inputs(catalog_path,provenance_path,case):
    catalog_path,provenance_path=Path(catalog_path).resolve(),Path(provenance_path).resolve()
    catalog=json.loads(catalog_path.read_text());provenance=json.loads(provenance_path.read_text())
    if digest(catalog_path)!=provenance['catalog_sha256']:raise ValueError('운반 catalog SHA 불일치')
    pins=dict(provenance['active_physical_inputs'])
    for name,expected in list(pins.items()):
        path=Path(name) if Path(name).is_absolute() else ROOT/name
        path.resolve().relative_to(ROOT)
        if digest(path)!=expected:raise ValueError('운반 원본 입력 변경: '+name)
        if name!=str(path):pins[str(path.resolve())]=pins.pop(name)
    rows=[r for r in catalog['goals'] if case in (r.get('case'),r.get('case_id'))]
    if len(rows)!=1:raise ValueError('명시적인 단일 운반 후보 필요')
    row=rows[0]
    for path in (catalog_path,provenance_path,Path(__file__).resolve()):pins[str(path)]=digest(path)
    return catalog,row,pins


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
        if bool(((active<torch.tensor(catalog['action_lower'])-1e-7)|(active>torch.tensor(catalog['action_upper'])+1e-7)).any()):
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


class AlignedScene(GpuScene):
    """비교A만 최초reset에서 정렬하며 construction 중 reset은 한 번만 호출한다."""
    def __init__(self,*args,row,**kwargs):
        self.aligned_row=row
        super().__init__(*args,**kwargs)

    def reset(self,indices):
        state=self.aligned_row['final_hover_state']
        self._prepared_dofs=torch.tensor([[r['pos'],r['vel']] for r in state['human_dof_states']],dtype=torch.float32,device=self.device)
        self._prepared_bodies=torch.tensor([_body_row(r) for kind in ('human','guitar','chair') for r in state[kind+'_body_states']],dtype=torch.float32,device=self.device)
        result=super().reset(indices)
        self.target[indices]=torch.tensor(self.aligned_row['hold_target105'],device=self.device)
        return self.snapshot()


def run(catalog_path,provenance_path,case,out,condition='C',num_envs=4,render=False):
    catalog,row,pins=load_inputs(catalog_path,provenance_path,case)
    frames=make_frames(catalog,row)
    if condition not in ('A','B','C'):raise ValueError('A/B/C 명시 필요')
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    scene=env=control=None;exception=None;failure=None;samples=[];endpoints=[]
    videos={};capture=None;graphics_original=None;closed=False;final_stable=0.;stable_by_env=None;ever_contact=None;ever_wrong=None
    settings=dict(schema=SCHEMA,case=case,condition=condition,seed=7,num_envs=num_envs,
        policy_training=False,physics_hz=240,control_hz=60,policy_clock='frozen at zero throughout transport',
        corridor=dict(normal_axis_excess_m=.03,normal_recovery_m=.02,normal_continuous_s=1.5,normal_enabled_after_s=3.,
            severe_axis_excess_m=.10,severe_continuous_s=.10,center='moving guitar-local wrist waypoint',
            halfextents='unchanged original per-case wrist guide half extents; translated to current waypoint'),
        final_hover=dict(height_m=[.005,.015],tangent_max_m=.005,facing_min=.1,
            wrist_speed_max_m_s=.05,stable_s=.5,settle_timeout_s=2.),
        reset='one actual initial reset only; no later q/body/guitar reset',frames=frames,
        candidate_sha256=row_identity(row),catalog_sha256=digest(catalog_path),runtime_sha256=digest(__file__))
    write(out/'settings.json',settings)
    try:
        if render:
            from isaacgym import gymapi
            from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym
            from guitar_learning.tool.demonstration.render_finger_skill import _create_cameras,_encoder
            graphics_original=gymapi.acquire_gym
            gymapi.acquire_gym=lambda:GraphicsGym(graphics_original())
        try:
            scene=(AlignedScene(num_envs,'left',device='cuda:0',out=out,row=row) if condition=='A' else
                GpuScene(num_envs,'left',device='cuda:0',out=out))
        finally:
            if graphics_original is not None:gymapi.acquire_gym=graphics_original
        control=BatchedController(scene,finger_action_mode='position')
        metadata=copy.deepcopy(scene.metadata);metadata['action_contract']=copy.deepcopy(control.contract)
        from guitar_learning.tool.experiments import natural_press
        class Environment(natural_press.NaturalEnvironment):
            natural_press=dict(condition='E4',active_axes=[],schema=SCHEMA)
            natural_preparation=dict(schema='guitar_learning.natural_preparation.v3',condition='E4')
        env=Environment(metadata,bundle=row['bundle'],song=dict(pre_roll_s=3.,tail_s=.5,left_fraction=.4,window_s=.5,finger_action_mode='position'),
            skill=dict(schema='guitar_learning.finger_skill.v3',phase='J',exploration='independent',hold_ticks=1,scope='scheduled',planned_transitions=204800,full_song_after=51200),
            device='cuda:0',hand='left')
        snapshot=scene.snapshot();ids=torch.arange(num_envs,device=scene.device)
        expected_q=torch.tensor(row['final_hover_q105'] if condition=='A' else row['q105'],device=scene.device)
        if not torch.allclose(snapshot['q'],expected_q.expand_as(snapshot['q']),atol=1e-6,rtol=0):
            raise ValueError('최초 native reset과 선언된 초기 관절 불일치')
        if not (torch.allclose(control.action_low.cpu(),torch.tensor(catalog['action_lower']),atol=1e-6,rtol=0)
                and torch.allclose(control.action_high.cpu(),torch.tensor(catalog['action_upper']),atol=1e-6,rtol=0)):
            raise ValueError('계획과 native 제어 행동범위 불일치')
        write(out/'initial_snapshot.json',dict(joint_names=scene.names,q105=snapshot['q'][0].cpu().tolist(),
            body_names=scene.body_names,body_state=snapshot['body_state'][0].cpu().tolist(),
            reset_body_snapshot=bool(snapshot['reset_body_snapshot'][0])))
        control.reset(ids,snapshot);env.reset(ids,snapshot)
        if condition=='A':control.target[:]=torch.tensor(row['hold_target105'],device=scene.device)
        groups=_wrist_position_groups(control,scene.body_names,control.active[:12])
        correction=torch.zeros(num_envs,12,device=scene.device);previous=control.target[:,control.active[:12]].clone()
        severe=torch.zeros(num_envs,device=scene.device);normal=torch.zeros_like(severe)
        normal_active=torch.zeros(num_envs,dtype=torch.bool,device=scene.device)
        last_valid=scene.efforts.clone()
        env.tick_failure=torch.zeros(num_envs,len(FAILURE_REASONS),dtype=torch.bool,device=scene.device)
        env.tick_cost=torch.zeros(num_envs,device=scene.device)
        halfextents=(env.guide['upper_G_m']-env.guide['lower_G_m'])/2
        settings['corridor']['actual_halfextents_G_m']=halfextents.cpu().tolist()
        write(out/'settings.json',settings)
        old_count=scene.reset_calls
        if old_count!=1:raise ValueError('운반 최초reset 정확히1회 필요')
        if render:
            cameras=_create_cameras(scene,gymapi)
            videos={name:_encoder(out/(name+'.mp4')) for name in cameras}
            def capture():
                scene.gym.step_graphics(scene.sim);scene.gym.render_all_camera_sensors(scene.sim)
                import numpy as np
                for name,camera in cameras.items():
                    pixels=scene.gym.get_camera_image(scene.sim,scene.envs[0],camera,gymapi.IMAGE_COLOR)
                    videos[name].stdin.write(np.asarray(pixels).reshape(720,1280,4)[...,:3].copy().tobytes())
            capture()
        from guitar_learning.training.training_log_io import project_source_paths
        pins.update({p:digest(p) for p in project_source_paths(sys.modules.items())})
        for path in Path(row['bundle']).rglob('*'):
            if path.is_file():pins[str(path.resolve())]=digest(path)
        pins[str(out/'settings.json')]=digest(out/'settings.json')
        write(out/'inputs_before.json',pins)
        stable_by_env=torch.zeros(num_envs,device=scene.device)
        ever_contact=torch.zeros(num_envs,dtype=torch.bool,device=scene.device)
        ever_wrong=torch.zeros_like(ever_contact)
        previous_wrist=env.local_bodies[:,env.wrist_index].clone()
        total=frames[-1]['time_s']+2.
        for tick in range(math.ceil(total*60)):
            now=(tick+1)/60.
            desired,goal,rotation,segment=sample_frames(frames,now,scene.device)
            if condition=='A':
                desired=torch.tensor(row['hold_target105'],device=scene.device)
                goal=torch.tensor([frames[-1]['wrist_position_G_m']],device=scene.device)
                rotation=torch.tensor([frames[-1]['wrist_quaternion_G_xyzw']],device=scene.device)
            desired=desired[control.active].expand(num_envs,-1).clone()
            goal=goal.expand(num_envs,-1);rotation=rotation.expand(num_envs,-1)
            if condition=='C':
                error,jacobian=wrist_error_and_jacobian(snapshot,env.wrist_index,env.guitar_index,
                    scene.com[env.wrist_index],groups,goal,rotation)
                arm,correction,_,_=bounded_wrist_target(desired[:,:12],correction,previous,
                    snapshot['q'][:,control.active[:12]],jacobian,error,~snapshot['reset_body_snapshot'],
                    control.action_low[:12],control.action_high[:12],control.rate[control.active[:12]])
                desired[:,:12]=arm;previous=arm.clone()
            action=trajectory_actions(desired,control.reference[control.active],control.action_low,control.action_high)
            target=control.targets(action,snapshot)
            for substep in range(4):
                efforts=control.efforts(snapshot);checks=control.diagnostics
                if not bool((checks['finite']&checks['chest_witness_certified']).all()):raise RuntimeError('native 제어 인증 실패')
                invalid=~checks['chest_normal_defined']
                efforts=torch.where(invalid[:,None],last_valid,efforts);last_valid=efforts.clone()
                snapshot=scene.step(target,efforts)
                env._snapshot(snapshot)
                TensorSongEnvironment._safety(env)
                env.tick_failure[:,-1]|=invalid
                ever_contact|=env.candidate[:,0];ever_wrong|=env.wrong[:,0]
                delta=(env.local_bodies[:,env.wrist_index]-goal).abs()
                excess=(delta-halfextents).clamp_min(0).amax(-1)
                severe=torch.where(excess>=.10,severe+1/240.,0.)
                elapsed_s=(tick*4+substep+1)/240.
                normal_active=(elapsed_s>=3.) & ((normal_active | (excess>.03)) & (excess>.02))
                normal=torch.where(normal_active,torch.where(excess>.03,normal+1/240.,(normal-1/240.).clamp_min(0)),0.)
                if bool(env.tick_failure.any() or (severe>=.10-1e-9).any() or (normal>=1.5-1e-9).any()):
                    failure=dict(kind='physical_or_moving_wrist_failure',time_s=(tick*4+substep+1)/240.,
                        physical=env.tick_failure.cpu().tolist(),moving_wrist_severe=(severe>=.10-1e-9).cpu().tolist(),
                        moving_wrist_ordinary=(normal>=1.5-1e-9).cpu().tolist())
                    break
            speed=torch.linalg.vector_norm(env.local_bodies[:,env.wrist_index]-previous_wrist,dim=-1)*60
            previous_wrist=env.local_bodies[:,env.wrist_index].clone()
            tangent=torch.linalg.vector_norm(env.surface_delta[:,0,:2],dim=-1)
            ready=((env.surface_height[:,0]>=.005)&(env.surface_height[:,0]<=.015)&(tangent<=.005)&
                (env.surface_alignment[:,0]>=.1)&(speed<=.05)&~env.candidate[:,0]&~env.wrong[:,0])
            ever_contact|=env.candidate[:,0];ever_wrong|=env.wrong[:,0]
            ready &= ~ever_contact & ~ever_wrong
            stable_by_env=torch.where(ready & (now>=frames[-1]['time_s']),stable_by_env+1/60.,0.)
            final_stable=float(stable_by_env.min())
            samples.append(dict(tick=tick+1,time_s=now,segment=segment,policy_time_s=0.,
                height_m=env.surface_height[:,0].cpu().tolist(),tangent_m=tangent.cpu().tolist(),
                facing=env.surface_alignment[:,0].cpu().tolist(),candidate=env.candidate[:,0].cpu().tolist(),
                wrong=env.wrong[:,0].cpu().tolist(),wrist_speed_m_s=speed.cpu().tolist(),
                wrist_axis_excess_m=excess.cpu().tolist(),normal_outside_s=normal.cpu().tolist(),severe_outside_s=severe.cpu().tolist(),stable_s=final_stable,physical=env.tick_failure.cpu().tolist()))
            if tick==0 or failure or final_stable>=.5-1e-9 or tick==math.ceil(total*60)-1:
                endpoints.append(dict(tick=tick+1,q105=snapshot['q'][0].cpu().tolist(),target105=target[0].cpu().tolist(),
                    body_state=snapshot['body_state'][0].cpu().tolist(),contact_force=snapshot['contact_force'][0].cpu().tolist()))
            if render and (tick+1)%2==0:capture()
            if failure or final_stable>=.5-1e-9:break
        if scene.reset_calls!=old_count:raise ValueError('운반 중 상태reset 발생')
        if int(env.clock.max())!=0:raise ValueError('운반 중 정책시계 진행 금지')
    except BaseException as error:
        exception=dict(type=type(error).__name__,message=str(error))
    finally:
        if graphics_original is not None:gymapi.acquire_gym=graphics_original
        if videos:
            from guitar_learning.tool.validation.hand_contact_probe import finish_video
            for name,process in videos.items():
                code,errors=finish_video(process)
                if code or errors:exception=exception or dict(type='VideoError',message=str((code,errors)))
        if scene is not None:
            try:
                scene.close();closed=scene.closed
            except BaseException as error:
                exception=exception or dict(type='CleanupError',message=str(error))
    changed=[p for p,sha in pins.items() if not Path(p).is_file() or digest(p)!=sha]
    passed=exception is None and failure is None and final_stable>=.5-1e-9 and not changed and closed
    report=dict(schema=SCHEMA,completed=exception is None and not changed and closed,accepted=passed,native_verified=passed,
        case=case,condition=condition,seed=7,failure=exception,transport_failure=failure,
        final_stable_s=final_stable,samples=samples,endpoints=endpoints,changed_inputs=changed,
        lifecycle_verified=closed,reset_calls=scene.reset_calls if scene else None,
        transport_ready=passed,candidate_valid=bool(row['candidate_valid']),
        per_environment=[dict(env_id=i,transport_ready=bool(stable_by_env[i]>=.5-1e-9) and failure is None,
            stable_s=float(stable_by_env[i]),ever_contact=bool(ever_contact[i]),ever_wrong=bool(ever_wrong[i]),
            censored_by_batch_failure=failure is not None) for i in range(num_envs)] if stable_by_env is not None else [],
        candidate_sha256=row_identity(row),runtime_sha256=digest(__file__),policy_training=False,
        limitation='teacher-supported transport feasibility only; no learned arm or acoustic success')
    write(out/'report.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation',choices=('probe',))
    parser.add_argument('--catalog','--plan',dest='catalog',type=Path,required=True);parser.add_argument('--provenance',type=Path,required=True)
    parser.add_argument('--case',required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--condition',choices=('A','B','C'),default='C')
    parser.add_argument('--num-envs',type=int,default=4);parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    if not 1<=args.num_envs<=64:parser.error('진단환경1..64 필요')
    report=run(args.catalog,args.provenance,args.case,args.out,args.condition,args.num_envs,args.render)
    if not report['completed']:raise RuntimeError('운반 실행 미완료; report.json 확인')


if __name__=='__main__':main()
