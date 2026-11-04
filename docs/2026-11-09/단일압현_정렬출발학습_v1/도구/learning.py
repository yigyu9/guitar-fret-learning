"""실제 정렬 도착 상태에서 담당 손가락4축만 배우는 조건부 진단.

현재 NaturalScene/Pool/Policy를 재사용하지만 새 입력·정책·재개 계약으로 봉인한다.
전체33축 학습이 아니며, 압현 중 팔은 도착 목표각을 유한하게 유지한다.
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
from guitar_learning.training import finger_skill_runner as runner,rollout
from guitar_learning.gpu.control import apply,multiply,conjugate
from guitar_learning.gpu.scene import RigidGuitar,_body_row
from guitar_learning.gpu.environment import FAILURE_REASONS
from guitar_learning.song.task import make_task
from guitar_learning.training.training_log_io import digest,write,dumps
from guitar_learning.portability import portable,localize,validate_checkpoint_inputs
SCHEMA='guitar_learning.aligned_start_goal4.v1'
POLICY_SCHEMA='guitar_learning.aligned_start_goal4_policy.v1'
RESUME_SCHEMA='guitar_learning.aligned_start_goal4_resume.v1'
STD_FLOOR=math.exp(-3)


def input_module():
    """이 연구의 새 입력 검증기만 import한다. 과거 봉인 Python은 실행하지 않는다."""
    name='aligned_start_inputs_v1'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,HERE/'inputs.py')
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name]


def load_inputs(folder):return input_module().load_verified(Path(folder).resolve())


def configuration(folder,std_initial=STD_FLOOR):
    if not math.isfinite(std_initial) or not STD_FLOOR<=std_initial<=.5:raise ValueError('표준편차는exp(-3)~0.5 필요')
    catalog,row,known,paths=load_inputs(folder)
    folder=Path(folder).resolve();folder.relative_to(ROOT)
    config=dict(schema=SCHEMA,condition='E4',distribution='aligned',axes='goal4',song=row['song'],finger=row['finger'],
        geometry=str(folder/'catalog.json'),geometry_sha256=digest(folder/'catalog.json'),
        provenance_sha256=digest(folder/'provenance.json'),active_axes=natural.active_axes('goal4',row['finger']),
        observation_extra_fields=natural.EXTRA_FIELDS,finger_initial_std=std_initial,finger_std_floor=STD_FLOOR,
        support_initial_std=STD_FLOOR,phase_arm_support=False,
        inactive_execution='left non-goal axes bounded static hold; right6 exact zero residual; no wrist teacher or phase action gate',
        initial_distribution=dict(v9_fraction=0.,rng='official CPU torch RNG retained; aligned state at episode boundaries only'),
        likelihood='saved active4 independent Gaussian tanh latent; other35 channels excluded',
        aligned_start=dict(input_dir=str(folder),known_press_sha256=digest(folder/'known_press.json'),
            reset='native arrived q/body and reconstructed compound guitar root; no historical state clock restoration',
            native_new_pool_certified=False,success_scope='conditional goal4, not free J33 song performance'))
    return config,catalog,row,known,paths


def validate_settings(settings):
    config=settings.get('natural_press',{});start=config.get('aligned_start',{})
    expected,catalog,row,known,paths=configuration(start.get('input_dir',''),config.get('finger_initial_std',0.))
    if config!=expected:raise ValueError('새 정렬 입력·조건·표준편차 계약 불일치')
    runner._validate_joint_settings(settings)
    if settings['song_training']['observation_dimension']!=601 or settings['initial_std']!=STD_FLOOR:
        raise ValueError('601열 관측과 공식 runner 초기 분산 shift0 계약 필요')
    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
    training=settings['song_training']
    if (Path(training['bundle']).resolve()!=Path(row['bundle']).resolve() or training['song_id']!=row['song'] or
            training['target_count']!=1 or training['control_ticks']!=task.provenance['song']['control_ticks'] or
            training['episode_duration_s']!=task.duration_s or settings['phrase_events']!=task.provenance['song']['source_event_count']):
        raise ValueError('정렬 catalog와 실제 학습 bundle/음 수/시간 불일치')
    return expected


def build_settings(folder,*,updates=100,num_envs=64,size='large',horizon=32,seed=7,std_initial=STD_FLOOR):
    from guitar_learning.training.launch import settings_document
    config,catalog,row,known,paths=configuration(folder,std_initial)
    settings=settings_document(updates=updates,num_envs=num_envs,size=size,horizon=horizon,seed=seed,checkpoint_every=50)
    task=make_task(Path(row['bundle']),pre_roll_s=settings['song']['pre_roll_s'],tail_s=settings['song']['tail_s'])
    if len(task.targets)!=1 or (task.targets[0].string,task.targets[0].fret,task.targets[0].finger)!=(row['string'],row['fret'],row['finger_id']):
        raise ValueError('새 단음 번들과 catalog 목표 불일치')
    settings['song_training'].update(song_id=row['song'],bundle=str(Path(row['bundle']).resolve()),target_count=1,
        control_ticks=task.provenance['song']['control_ticks'],episode_duration_s=task.duration_s,observation_dimension=601)
    settings['phrase_events']=task.provenance['song']['source_event_count'];settings['natural_press']=config
    settings['initial_std']=STD_FLOOR
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


class AlignedScene(natural.NaturalScene):
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


class AlignedPool(natural.NaturalPool):
    def reset(self,indices=None):
        _,rows=super().reset(indices)
        ids=(torch.arange(self.num_envs,device=self.scene.device) if indices is None else
            torch.as_tensor(indices,device=self.scene.device,dtype=torch.long))
        # 정렬 실측 q는 비활성 오른손의 미세 추종 오차를 포함한다. 이를 행동으로 재주입하지 않는다.
        self.execution_hold_action[ids,33:]=0
        for name in ('hold_action','execution_hold_action','last_applied_action','previous_action'):
            getattr(self.environment,name)[ids,33:]=0
        right=self.controller.active[33:]
        self.controller.target[ids[:,None],right[None]]=self.controller.reference[right]
        self.scene.target[ids[:,None],right[None]]=self.controller.reference[right]
        self.observation=self.environment.observation()
        return self.observation,rows

    def _create_scene(self,settings,out):
        self.natural_press=settings['natural_press']
        return AlignedScene(self.num_envs,'left',device=settings['device'],out=out,natural_press=self.natural_press)


class AlignedPolicy(natural.NaturalPolicy):
    """기존 active4 정책을 유지하며 명시한 초기 분산과 새 floor만 적용한다."""
    schema=POLICY_SCHEMA
    def __init__(self,state_dim,*,size,contract,natural_press):
        super().__init__(state_dim,size=size,contract=contract,natural_press=natural_press)
        slot=4*natural.FINGERS.index(natural_press['finger'])
        with torch.no_grad():self.core.finger_log_std[slot:slot+4].fill_(math.log(natural_press['finger_initial_std']))
        self.architecture['aligned_std']=dict(initial=natural_press['finger_initial_std'],floor=STD_FLOOR,
            runner_initial_shift=0.,inactive_sampling=False)

    def forward(self,state,*inputs):
        result=super().forward(state,*inputs)
        slot=4*natural.FINGERS.index(self.natural_press['finger']);action=17+slot
        # 상위 NaturalPolicy의0.10 floor 결과를 쓰지 않고 실제 core Parameter에서 재구성한다.
        std=self.core.finger_log_std[slot:slot+4].clamp(math.log(STD_FLOOR),2.).expand(len(state),-1)
        result['log_std']=torch.cat((result['log_std'][:,:action],std,result['log_std'][:,action+4:]),-1)
        return result


def validate_metadata(metadata):
    if not isinstance(metadata,dict) or metadata.get('schema')!=RESUME_SCHEMA:raise ValueError('새 정렬출발goal4 checkpoint 전용')
    validate_settings(localize(metadata['settings']))


def read_checkpoint(path):
    payload=torch.load(path,map_location='cpu',weights_only=False);validate_metadata(payload.get('metadata'))
    if payload.get('identity',{}).get('architecture',{}).get('schema')!=POLICY_SCHEMA:raise ValueError('정렬출발 정책 구조 불일치')
    validate_checkpoint_inputs(payload['metadata']);return localize(payload['metadata']['settings'])


@contextmanager
def runtime():
    original=(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)
    def policy(settings,pool):
        config=validate_settings(settings)
        return AlignedPolicy(pool.observation['state'].shape[-1],size=settings['size'],contract=pool.contract,natural_press=config).to(settings['device'])
    def resume_schema(settings):validate_settings(settings);return RESUME_SCHEMA
    def pins(settings,out,extra=()):
        config=validate_settings(settings);_,_,_,paths=load_inputs(config['aligned_start']['input_dir'])
        return original[4](settings,out,list(extra)+[Path(__file__).resolve(),HERE/'inputs.py',*paths])
    rollout.GpuPool,runner._policy=AlignedPool,policy
    runner.resume_schema,runner._validate_metadata_schema=resume_schema,validate_metadata
    runner._pins,runner.SCHEMA=pins,SCHEMA
    try:yield
    finally:(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)=original


def train(args):
    if args.resume:
        settings=read_checkpoint(args.resume)
        if args.inputs and Path(args.inputs).resolve()!=Path(settings['natural_press']['aligned_start']['input_dir']):raise ValueError('재개 입력 변경 불가')
        for key in ('size','num_envs','horizon','seed'):
            if getattr(args,key) is not None and getattr(args,key)!=settings[key]:raise ValueError('재개 '+key+' 변경 불가')
        if args.std_initial is not None and args.std_initial!=settings['natural_press']['finger_initial_std']:raise ValueError('재개 표준편차 변경 불가')
        settings['updates']=args.updates
    else:
        defaults=dict(updates=args.updates,size='large',num_envs=64,horizon=32,seed=7,std_initial=STD_FLOOR)
        for key in ('size','num_envs','horizon','seed','std_initial'):
            if getattr(args,key) is not None:defaults[key]=getattr(args,key)
        settings=build_settings(args.inputs or HERE.parent/'입력',**defaults)
    if args.checkpoint_every is not None:settings['checkpoint_every']=args.checkpoint_every
    with runtime():return runner.run(settings,SimpleNamespace(out=args.out,resume=args.resume))


def oracle(args):
    settings=build_settings(args.inputs or HERE.parent/'입력',num_envs=1,updates=1,size='small')
    config=validate_settings(settings);_,row,known,_=load_inputs(config['aligned_start']['input_dir'])
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=False);write(out/'settings.json',portable(settings))
    pool=None;pins=None;failure=None;episode=None;trace=[];started=time.monotonic()
    try:
        random.seed(settings['seed']);np.random.seed(settings['seed']);torch.manual_seed(settings['seed']);torch.set_num_threads(1)
        with runtime():pins=runner._pins(settings,out)
        write(out/'inputs_before.json',pins);pool=AlignedPool(settings,out)
        pool.environment.set_evaluation(True,full_song=True);pool.observation=pool.reset()[0]
        env,control=pool.environment,pool.controller
        indices=control.active[config['active_axes']]
        if indices.cpu().tolist()!=known['indices']:raise ValueError('oracle과 활성 손가락4축 불일치')
        arrival=pool.scene.snapshot()['q'][0,indices].clone()
        goal=torch.tensor(known['finger4_rad'],device=pool.scene.device,dtype=arrival.dtype)
        if not bool(((goal>=pool.scene.lower[indices])&(goal<=pool.scene.upper[indices])).all()):raise ValueError('oracle4각 native 한계 불일치')
        for tick in range(math.ceil(env.task.duration_s*60)+2):
            fraction=min(1.,max(0.,((tick+1)/60.-.5)/2.));blend=fraction**3*(10-15*fraction+6*fraction*fraction)
            desired=control.target[:,control.active].clone();desired[:,config['active_axes']]=arrival+blend*(goal-arrival)
            action=natural.normalized_action(desired,control.reference[control.active],control.action_low,control.action_high)
            action[:,33:]=0
            _,_,_,term,trunc,episodes=pool.step(action)
            sample=pool.scene.snapshot();distal=int(env.pad_indices[int(env.finger[0])-1])
            trace.append(dict(tick=tick+1,score_time_s=float(env._score_time()[0]),native_physics_step=int(sample['physics_step'][0]),
                candidate=bool(env.candidate[0,0]),wrong=bool(env.wrong[0,0]),
                pad_height_m=float(env.surface_height[0,0]),pad_alignment_cos=float(env.surface_alignment[0,0]),
                pad_delta_G_m=env.surface_delta[0,0].cpu().tolist(),
                pad_tangent_m=float(torch.linalg.vector_norm(env.surface_delta[0,0,:2])),
                pad_distance_m=float(env.surface_distance[0,0]),selected_patch_sample_global=int(env.surface_sample[0,0]),
                assigned_body_net_loaded=bool(env.surface_body_loaded[0,0]),
                patch_position_geometry=bool(env.contact_geometry[0,0]),patch_facing_geometry=bool(env.contact_facing[0,0]),
                patch_loaded_geometry=bool(env.contact_loaded_target[0,0]),
                distal_net_contact_force_N=sample['contact_force'][0,distal].cpu().tolist(),
                wrist_G_m=env.local_bodies[0,env.wrist_index].cpu().tolist(),wrist_guide_delta_m=env.guide['delta'][0].cpu().tolist(),
                guitar_displacement_m=float(torch.linalg.vector_norm(env.guitar_delta[0])),
                guitar_rotation_rad=float(torch.linalg.vector_norm(env.guitar_rotation[0])),
                arm_actual_rad=sample['q'][0,control.active[:12]].cpu().tolist(),arm_target_rad=control.target[0,control.active[:12]].cpu().tolist(),
                physical_failure_reasons=[name for name,flag in zip(FAILURE_REASONS,env.tick_failure[0].cpu().tolist()) if flag],
                q4=sample['q'][0,indices].cpu().tolist(),target4=control.target[0,indices].cpu().tolist()))
            if episodes:episode=episodes[0];write(out/'episode.json',episode);break
        if episode is None:raise RuntimeError('oracle 음 원장 종료 누락')
    except BaseException as exc:failure=repr(exc)
    finally:
        cleanup=[]
        if pool:
            try:pool.close()
            except BaseException as exc:cleanup.append(repr(exc))
        changed=[path for path,value in (pins or {}).items() if not Path(path).is_file() or digest(path)!=value]
        closed=bool(pool and pool.closed and pool.scene.closed)
        report=dict(schema=SCHEMA+'.oracle',completed=episode is not None and failure is None and closed and not changed and not cleanup,
            task_success=bool(episode and episode['song']['stage_success'] and failure is None and closed and not changed and not cleanup),failure=failure,source_pins_unchanged=not changed,
            changed_inputs=changed,cleanup_errors=cleanup,scene_closed=closed,optimizer_updates=0,learned_policy=False,
            first_environment_only=True,environments=1,denominator=1,
            trace_scope='60Hz native endpoints; pad geometry/net body load are not calibrated string pressure; native240Hz episode ledger judges success',control='static finite arm hold + knownfinger4 ramp0.5..2.5; no wrist teacher',
            gpu_scene=pool.scene.diagnostics if pool else None,wall_s=time.monotonic()-started)
        write(out/'trace.json',trace);write(out/'report.json',report)
    return report


def self_test():
    """역변환·정책 분포·active4·엄격 모델 구조를 CPU에서 검증한다."""
    import tempfile
    from unittest.mock import patch
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.tests.test_finger_skill_policy import contract as base_contract
    from guitar_learning.training.ppo import DecisionPPOTrainer
    torch.set_num_threads(1)
    contract=load_gpu_prepared_reset_contract('left');rigid=RigidGuitar(contract,'cpu')
    logical=torch.tensor(_body_row(contract['state']['guitar_body_states'][0]),dtype=torch.float32)
    inverse=logical_to_root(rigid,logical)
    torch.testing.assert_close(inverse,rigid.prepared_root,atol=2e-7,rtol=0)
    # 임의 비영 회전/속도에서도 COM 속도 역변환이 보존되는지 roundtrip한다.
    root=rigid.prepared_root.clone();root[7:10]=torch.tensor([.1,-.2,.3]);root[10:13]=torch.tensor([.3,.2,-.1])
    logical=root.clone();logical[:3]=root[:3]+apply(root[3:7],rigid._offsets[0])
    logical[3:7]=multiply(root[3:7],rigid._rotations[0])
    logical_com=logical[:3]+apply(logical[3:7],rigid._logical_com[0])
    root_com=root[:3]+apply(root[3:7],rigid._compound_com)
    logical[7:10]=root[7:10]+torch.cross(root[10:13],logical_com-root_com,dim=-1)
    torch.testing.assert_close(logical_to_root(rigid,logical),root,atol=2e-7,rtol=0)
    folder=HERE.parent/'입력'
    if not (folder/'manifest.json').is_file():
        print('CPU root 역변환 통과. 입력 생성 후 전체 policy 검사를 다시 실행해야 함. GPU 실행 없음.')
        return
    settings=build_settings(folder,updates=2,num_envs=2,size='small')
    config=settings['natural_press'];value=base_contract();value['natural_press']=config
    value['observation']['fields']+=natural.EXTRA_FIELDS;value['observation']['scales']+=[1.]*natural.EXTRA_DIM
    value['observation']['dimension']+=natural.EXTRA_DIM
    model=AlignedPolicy(601,size='small',contract=value,natural_press=config)
    data=(torch.zeros(2,601),torch.zeros(2,2,24),torch.ones(2,2,dtype=torch.bool),
        torch.zeros(2,8,24),torch.ones(2,8,dtype=torch.bool))
    result=model.act(*data)
    assert int(model._active_mask().sum())==4 and set(model._active_mask().nonzero().flatten().tolist())==set(config['active_axes'])
    torch.testing.assert_close(result['log_std'][:,config['active_axes']].exp(),torch.full((2,4),STD_FLOOR))
    assert math.log(settings['initial_std'])+3.==0.
    assert model.support_log_std is model.core.support_log_std and model.finger_log_std is model.core.finger_log_std
    assert all(torch.isfinite(v).all() for v in result.values())
    cfg=copy.deepcopy(config);cfg['finger_initial_std']=.15
    larger=AlignedPolicy(601,size='small',contract=dict(value,natural_press=cfg),natural_press=cfg)
    torch.testing.assert_close(larger(*data)['log_std'][:,cfg['active_axes']].exp(),torch.full((2,4),.15))
    with torch.no_grad():model.core.finger_log_std.fill_(-5)
    torch.testing.assert_close(model(*data)['log_std'][:,config['active_axes']].exp(),torch.full((2,4),STD_FLOOR))
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'policy.pt';DecisionPPOTrainer(model).save(path)
        target=AlignedPolicy(601,size='small',contract=value,natural_press=config)
        DecisionPPOTrainer(target).load(path)
        assert all(torch.equal(v,target.state_dict()[k]) for k,v in model.state_dict().items())
        try:DecisionPPOTrainer(larger).load(path)
        except ValueError:pass
        else:raise AssertionError('표준편차 비교 조건 사이 strict identity 혼용')
    # 부분 reset에서도 해당 행의 오른손6축만 정확히0으로 만들고 다른 행은 보존한다.
    fake=object.__new__(AlignedPool);fake.num_envs=2;fake.scene=SimpleNamespace(device='cpu',target=torch.ones(2,105))
    fake.controller=SimpleNamespace(active=torch.arange(39),reference=torch.arange(105,dtype=torch.float32)/100,
        target=torch.ones(2,105))
    fake.execution_hold_action=torch.full((2,39),.001)
    fake.environment=SimpleNamespace(**{name:torch.full((2,39),.001) for name in
        ('hold_action','execution_hold_action','last_applied_action','previous_action')})
    fake.environment.observation=lambda:{'state':torch.zeros(2,601)}
    with patch.object(natural.NaturalPool,'reset',return_value=({},[])):
        AlignedPool.reset(fake,[0])
    assert (fake.execution_hold_action[0,33:]==0).all() and (fake.execution_hold_action[1,33:]!=0).all()
    for name in ('hold_action','execution_hold_action','last_applied_action','previous_action'):
        assert (getattr(fake.environment,name)[0,33:]==0).all()
    torch.testing.assert_close(fake.controller.target[0,33:39],fake.controller.reference[33:39])
    torch.testing.assert_close(fake.scene.target[0,33:39],fake.controller.reference[33:39])
    assert torch.equal(fake.scene.target[1],torch.ones(105))
    old=(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)
    try:
        with runtime():raise RuntimeError('검사 예외')
    except RuntimeError:pass
    assert old==(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)
    print('CPU 검사 통과: v9/native root COM 역변환,601/active4,초기 std/floor/runner shift0,비교조건 구분,strict PPO 저장복원,오른손6축zero/부분reset보존,factory 예외복원. GPU 실행 없음.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true')
    commands=parser.add_subparsers(dest='command')
    for name in ('train','oracle'):
        p=commands.add_parser(name);p.add_argument('--inputs',type=Path);p.add_argument('--out',required=True,type=Path)
        if name=='train':
            p.add_argument('--updates',type=int,default=100);p.add_argument('--num-envs',type=int);p.add_argument('--size',choices=('small','medium','large'))
            p.add_argument('--horizon',type=int);p.add_argument('--seed',type=int);p.add_argument('--std-initial',type=float)
            p.add_argument('--checkpoint-every',type=int);p.add_argument('--resume',type=Path)
    for name in ('evaluate','render'):
        p=commands.add_parser(name);p.add_argument('--checkpoint',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--num-envs',type=int)
    args=parser.parse_args()
    if args.self_test:return self_test()
    if args.command is None:parser.error('train/evaluate/render/oracle 필요')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    if args.command=='train':
        if args.updates<1 or (args.checkpoint_every is not None and args.checkpoint_every<1):parser.error('양수 학습/저장 반복 필요')
        return train(args)
    if args.command=='oracle':
        result=oracle(args)
        if not result['completed']:raise SystemExit(1)
        return result
    read_checkpoint(args.checkpoint)
    with runtime():
        if args.command=='evaluate':return runner.evaluate_checkpoint(args.checkpoint,args.out,num_envs=args.num_envs,scope='full_song')
        from guitar_learning.tool.demonstration.render_finger_skill import render
        return render(args.checkpoint,args.out,num_envs=args.num_envs,scope='full_song')


if __name__=='__main__':main()
