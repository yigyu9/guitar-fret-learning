"""중지6/7프렛 AB 전체 음열을 활성 J 학습기에 연결하는 격리 실험."""
if __name__=='__main__':
    import isaacgym  # standalone 실행에서도 Torch보다 먼저 native를 초기화한다.

import argparse
import copy
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT))
import torch
from guitar_learning.tool.experiments import natural_press as natural
from guitar_learning.gpu.finger_skill_environment import FingerSkillEnvironment
from guitar_learning.training.rollout import GpuPool

BASE=Path(__file__).resolve().parents[1]
SONG='virtual_middle_s3_f6_f7_AB_v2'
INITIAL_SONG='virtual_finger_v9_middle_s3_f6'
SCHEMA='guitar_learning.target_transition.v2'

def task_times(gap):
    if gap not in (.5,.75,1.):raise ValueError('승인된 휴지 .5/.75/1초만 허용')
    return ((3.,4.5),(4.5+gap,6.+gap))



def initial_configuration(condition='E4'):
    """과거 봉인의 예외를 만들지 않고 v2 재검증 입력을 독립 검증한다."""
    catalog=BASE/'geometry/initial_catalog.json';provenance=BASE/'geometry/initial_provenance.json'
    proof=json.loads(provenance.read_text())
    if proof['catalog_sha256']!=natural.digest(catalog):raise ValueError('v2 초기 catalog SHA 불일치')
    if not proof.get('active_physical_inputs'):raise ValueError('현재 물리 입력 봉인 필요')
    for name,expected in proof['active_physical_inputs'].items():
        if natural.digest(ROOT/name)!=expected:raise ValueError('v2 초기 물리 입력 변경: '+name)
    rows=[r for r in json.loads(catalog.read_text())['goals'] if r['song']==INITIAL_SONG]
    if len(rows)!=1 or not rows[0]['candidate_valid']:raise ValueError('단일 A 초기 후보 필요')
    if condition!='E4':raise ValueError('E4 고정')
    return dict(schema='guitar_learning.target_transition_initial.v2',condition=condition,distribution='aligned',axes='arm16',
        song=INITIAL_SONG,finger='middle',geometry=str(catalog),geometry_sha256=natural.digest(catalog),
        provenance_sha256=natural.digest(provenance),active_axes=natural.active_axes('arm16','middle'),
        observation_extra_fields=natural.EXTRA_FIELDS,finger_initial_std=.15,finger_std_floor=.10,
        support_initial_std=math.exp(-3),phase_arm_support=False,
        inactive_execution='reset actual hold; v9 goal4 arm12 uses fixed aligned IK; no phase relatch',
        initial_distribution=dict(v9_fraction=0.,rng='torch CPU global RNG; official checkpoint restored; episode reset only'),
        readiness=dict(wrist_axis_excess_m=.010,wrist_continuous_s=.10,tangent_m=.010,height_m=[.002,.020],normal_cos=.1,aligned_continuous_s=.10),
        lr=dict(floor=7.5e-6,cap=3e-5,retry_factor=.5,stable_updates=10,stable_kl_below=.005,recovery_factor=1.25),
        likelihood='saved active axes Gaussian tanh latent; phase never blocks active actions')


def sequence_config(condition):
    from guitar_learning.song.task import make_task
    if condition!='E4':raise ValueError('v2는 E4 고정')
    bundle=ROOT/'data/song_bundles'/SONG
    task=make_task(bundle,pre_roll_s=3.,tail_s=.5)
    schedule=[dict(target_id=t.target_id,event_id=t.event_id,string_index=t.string,fret=t.fret,finger=t.finger,
        onset_s=t.onset_s,press_s=t.press_s,end_s=t.end_s) for t in task.targets]
    mapping=json.loads((bundle/'mapping/fingering.json').read_text())
    gap=float(mapping['transition_gap_s']);times=task_times(gap);duration=6.5+gap
    if (len(schedule)!=2 or task.duration_s!=duration or
        any((r['onset_s'],r['end_s'])!=time or r['press_s']!=time[0] or r['fret']!=fret or r['finger']!=2 or r['string_index']!=2
            for r,time,fret in zip(schedule,times,(6,7)))):
        raise ValueError('중지 표준3번줄 6/7프렛의 승인된 AB 시간표 시간표 불일치')
    files={str(p.relative_to(ROOT)):natural.digest(p) for p in sorted(bundle.rglob('*')) if p.is_file()}
    geometry=bundle/'mapping/fingering.json'
    validation=bundle/'manifest.json'
    if not geometry.is_file() or not validation.is_file():raise ValueError('CPU B 기하/번들 검증 입력 필요')
    canonical=json.dumps(schedule,sort_keys=True,separators=(',',':')).encode()
    return dict(schema=SCHEMA,condition=condition,song=SONG,initial_bias_song=INITIAL_SONG,
        sequence_sha256=hashlib.sha256(canonical).hexdigest(),schedule=schedule,duration_s=duration,gap_s=gap,
        bundle_files=files,geometry_inputs={str(p.relative_to(ROOT)):natural.digest(p) for p in (geometry,validation)},
        scope='whole AB from every reset; training evaluation flag unchanged',
        initial_pose='CPU FK-consistent copied middleF6 snapshot; current native validation separate; no target-switch state overwrite',
        active_axes=natural.active_axes('arm16','middle'),phase_arm_support=False,
        detail_physics_rows=int(round(duration*240)),B_native_reachability='queue requires separate native preflight and SHA; geometry is not native success',
        press_adjudication='experiment v2; wrong_press_sources.v3; raw candidates and effective targets separately logged')


def validate(settings):
    config=settings['transition']
    if config!=sequence_config(config['condition']):raise ValueError('저장된 AB 시간표/입력 SHA 불일치')
    expected=initial_configuration(config['condition'])
    if settings.get('natural_press')!=expected:raise ValueError('정렬 초기 bias/활성16축 계약 불일치')
    if Path(settings['song_training']['bundle']).resolve()!=ROOT/'data/song_bundles'/SONG:
        raise ValueError('실제 학습 음열과 초기 bias용 단음 구분 필요')
    return config


class TransitionEnvironment(natural.NaturalEnvironment):
    transition=None
    def __init__(self,*args,**kwargs):
        # NaturalEnvironment의 M=1 제한만 우회하며 같은 현행 보상/접촉 기반을 만든다.
        FingerSkillEnvironment.__init__(self,*args,**kwargs)
        if self.M!=2 or self.task.duration_s!=self.transition['duration_s']:raise ValueError('전체 AB2음 환경 필요')
        self.contract['natural_press']=copy.deepcopy(self.natural_press)
        self.contract['transition']=copy.deepcopy(self.transition)
        observation=self.contract['observation']
        plane=observation['surface_geometry']['press_surface']['plane_G']
        if abs(plane[0])+abs(plane[1])>1e-9 or abs(abs(plane[2])-1)>1e-9:raise ValueError('XY 접선·부호 있는 Z 평면 필요')
        observation['fields']+=natural.EXTRA_FIELDS;observation['scales']+=[1.]*natural.EXTRA_DIM
        observation['dimension']+=natural.EXTRA_DIM;self.scales=self._tensor(observation['scales'])
        observation['transition']=copy.deepcopy(self.transition)
        self.contract['task']['transition']=copy.deepcopy(self.transition)
        self.transition_arm_indices=self._tensor([self.names.index(name) for name in natural.ACTIVE_NAMES[:12]],torch.long)
        self.transition_arm_lower=self._tensor(self.metadata['action_contract']['action_lower_rad'][:12])
        self.transition_arm_upper=self._tensor(self.metadata['action_contract']['action_upper_rad'][:12])

    def _allocate(self,count):
        super()._allocate(count)
        self.phase_target=torch.full((count,),-1,dtype=torch.long,device=self.device)
        self.target_switch_count=torch.zeros(count,dtype=torch.long,device=self.device)
        self.target_phase_seconds=torch.zeros(count,2,3,device=self.device)
        self.first_contact_s=torch.full((count,2),-1.,dtype=torch.float64,device=self.device)
        self.first_achievement_s=torch.full_like(self.first_contact_s,-1.)

    def _reset_scope(self,indices):
        flags=self.evaluation,self.evaluation_full_song
        self.evaluation,self.evaluation_full_song=True,True
        try:super()._reset_scope(indices)
        finally:self.evaluation,self.evaluation_full_song=flags
        self.phase_target[indices]=-1;self.target_switch_count[indices]=0;self.target_phase_seconds[indices]=0
        self.first_contact_s[indices]=-1.;self.first_achievement_s[indices]=-1.

    def substep(self,snapshot):
        result=super().substep(snapshot)
        now=self._score_time()[:,None]
        audible=(self.onset<=now)&(now<self.end)&self._scope_mask()
        clean=self.candidate&~self.wrong&audible
        self.first_contact_s.copy_(torch.where((self.first_contact_s<0)&clean,now,self.first_contact_s))
        self.first_achievement_s.copy_(torch.where((self.first_achievement_s<0)&self.note['left'],now,self.first_achievement_s))
        return result

    def selected_target(self):
        targets=self._finger_targets(self._score_time())
        index=targets['indices'][:,1,0];valid=targets['valid'][:,1,0]
        return torch.where(valid,index,torch.full_like(index,-1)),valid

    def readiness(self):
        index,valid=self.selected_target();rows=torch.arange(self.N,device=self.device);index=index.clamp_min(0)
        delta=self.surface_delta[rows,index];height=self.surface_height[rows,index];facing=self.surface_alignment[rows,index]
        wrist=(self.guide['delta'].abs()<=.010).all(-1)
        return torch.stack((wrist,torch.linalg.vector_norm(delta[:,:2],dim=-1)<=.010,
            (height>=.002)&(height<=.020),facing>=.1),-1)&valid[:,None]

    def _advance_phase(self):
        if hasattr(self,'applied_action_getter'):self.last_applied_action.copy_(self.applied_action_getter())
        now=self._local_time();dt=(now-self.last_phase_time).clamp(0,1/60.+1e-8).float();self.last_phase_time.copy_(now)
        target,valid=self.selected_target();switched=target!=self.phase_target
        self.target_switch_count+=switched&(target>=0)&(self.phase_target>=0)
        self.phase_target.copy_(target)
        self.ready_timers[switched]=0;self.phase_elapsed[switched]=0;self.transition_elapsed[switched]=0
        old=self.motion_phase.clone();ready=self.readiness()
        conditions=torch.stack((ready[:,0],ready.all(-1)),-1)
        timer_dt=torch.where(switched,0.,dt)
        self.ready_timers.copy_(torch.where(conditions,self.ready_timers+timer_dt[:,None],0.))
        rows=torch.arange(self.N,device=self.device);index=target.clamp_min(0)
        clean=valid&self.candidate[rows,index]&~self.wrong[rows,index]
        moved=self.ready_timers[:,0]+1e-7>=.10;aligned=self.ready_timers[:,1]+1e-7>=.10
        self.motion_phase.copy_(torch.where(moved,1,0));self.motion_phase.copy_(torch.where(aligned|clean,2,self.motion_phase))
        keep=(old==2)&~switched&valid&(self.guide['delta'].abs().amax(-1)<=.03)
        self.motion_phase[keep]=2
        changed=switched|(old!=self.motion_phase);entering=changed&(self.motion_phase==2)
        self.hold_action[entering,:12]=self.last_applied_action[entering,:12]
        self.transition_elapsed.copy_(torch.where(changed,0.,(self.transition_elapsed+dt).clamp_max(.20)))
        self.phase_elapsed.copy_(torch.where(changed,0.,self.phase_elapsed+dt))
        self.phase_counts.scatter_add_(1,self.motion_phase[:,None],dt[:,None]);self.block_counts+=(~ready).float()*dt[:,None]
        self.target_phase_seconds[rows,index,self.motion_phase]+=dt*valid

    def natural_preparation_trace(self):
        result=super().natural_preparation_trace();now=float(self._score_time()[0]);selection=self._finger_targets(self._score_time())
        selected=[]
        for slot in (0,1):
            index=int(selection['indices'][0,1,slot]) if bool(selection['valid'][0,1,slot]) else None
            selected.append(self.task.targets[index].target_id if index is not None else None)
        events=[]
        for i,t in enumerate(self.task.targets):
            events.append(dict(index=i,target_id=t.target_id,event_id=t.event_id,string_index=t.string,fret=t.fret,
                onset_s=t.onset_s,end_s=t.end_s,press_s=t.press_s,audible=t.onset_s<=now<t.end_s,
                press_candidate=bool(self.candidate[0,i]),wrong=bool(self.wrong[0,i]),clean_streak_s=float(self.note['clean_streak'][0,i]),
                pad_height_m=float(self.surface_height[0,i]),pad_distance_m=float(self.surface_distance[0,i]),
                assigned_body_loaded=bool(self.surface_body_loaded[0,i])))
        action=self.action[0,:12].clamp(-1,1);reference=self.reference[self.transition_arm_indices]
        requested=reference+torch.where(action>=0,self.transition_arm_upper-reference,reference-self.transition_arm_lower)*action
        result['transition']=dict(schema=SCHEMA,sequence_sha256=self.transition['sequence_sha256'],
            current_target_id=selected[0],next_target_id=selected[1],goals=events,
            all_env_ids=list(range(self.N)),all_env_episode_time_s=self._local_time().tolist(),
            all_env_episode_ids=(self.trace_episode_ids().tolist() if hasattr(self,'trace_episode_ids') else None),
            all_env_current_next_indices=torch.where(selection['valid'][:,1,:],selection['indices'][:,1,:],-1).tolist(),
            all_env_candidate=self.candidate.tolist(),all_env_wrong=self.wrong.tolist(),
            all_env_raw_candidate=self.contact_loaded_target.tolist(),
            all_env_height_m=self.surface_height.tolist(),all_env_distance_m=self.surface_distance.tolist(),
            arm_joint_names=list(natural.ACTIVE_NAMES[:12]),arm_actual_rad=self.snapshot['q'][0,self.transition_arm_indices].tolist(),
            arm_requested_rad=requested.tolist(),arm_applied_rad=self.snapshot['target'][0,self.transition_arm_indices].tolist(),
            arm_action=action.tolist(),wrist_error_m=self.guide['delta'][0].tolist(),phase_target_index=int(self.phase_target[0]),
            selection_scope='tracking current/next slot; selected tracking may be upcoming in a rest; audible flags identify sounding events',
            scope='env0 actual240Hz endpoint; repeated cells retain separate event IDs/time windows; candidates are geometry/load proxies')
        return result

    def _episode(self,index,failed):
        result=super()._episode(index,failed)
        result['transition']=dict(**self.transition,target_switch_count=int(self.target_switch_count[index]),
            per_target_phase_seconds=self.target_phase_seconds[index].cpu().tolist(),always_full_sequence=True)
        result['transition_diagnostics']=dict(target_ids=[t.target_id for t in self.task.targets],
            first_contact_s=[None if v<0 else v for v in self.first_contact_s[index].cpu().tolist()],
            first_achievement_s=[None if v<0 else v for v in self.first_achievement_s[index].cpu().tolist()],
            scope='this episode; score seconds at actual240Hz endpoints; onset<=t<end clean candidate and native left achievement; null=not observed; no reward modification')
        return result


class TransitionPolicy(natural.NaturalPolicy):
    schema='guitar_learning.target_transition_policy.v2'
    def __init__(self,*args,transition,**kwargs):
        if transition.get('schema')!=SCHEMA or kwargs['contract'].get('transition')!=transition:
            raise ValueError('명시적 AB 관측/정책 동일 계약 필요')
        super().__init__(*args,**kwargs)
        self.architecture['transition']=copy.deepcopy(transition)


class TransitionScene(natural.NaturalScene):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.metadata['reset_body_source'].update(schema=SCHEMA,verified=False,
            cpu_fk_snapshot_verified=True,native_validation='separate preflight required; legacy flag not inherited')


class TransitionPool(natural.NaturalPool):
    def _create_scene(self,settings,out):
        self.natural_press=settings['natural_press']
        return TransitionScene(self.num_envs,'left',device=settings['device'],out=out,natural_press=self.natural_press)

    def __init__(self,settings,out):
        config=validate(settings);bias=copy.deepcopy(settings['natural_press'])
        class Environment(TransitionEnvironment):
            transition=config
            natural_press=bias
            natural_preparation=dict(schema='guitar_learning.natural_preparation.v3',condition=config['condition'])
        self.environment_class_override=Environment
        GpuPool.__init__(self,settings,out)
        self.environment.applied_action_getter=lambda:natural.normalized_action(self.controller.target[:,self.controller.active],
            self.controller.reference[self.controller.active],self.controller.action_low,self.controller.action_high)
        self.finger_control_diagnostics.detail_limit=config['detail_physics_rows']
        self.environment.trace_episode_ids=lambda:self.finger_control_diagnostics.episode_id
        for contract in (self.contract,self.environment.contract):
            contract['diagnostics']['transition_trace']=dict(env_id=0,max_physics_rows=config['detail_physics_rows'],
                duration_s=config['duration_s'],event_ids='per-event IDs and clock windows distinguish repeated physical cells')


@contextmanager
def transition_runtime(settings):
    from guitar_learning.training import finger_skill_runner as runner,rollout,ppo
    config=validate(settings)
    original=runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins,runner.checkpoint_metadata
    def factory(current,pool):
        if validate(current)!=config:raise ValueError('정책/환경 AB 계약 불일치')
        return TransitionPolicy(pool.observation['state'].shape[-1],size=current['size'],contract=pool.contract,
            natural_press=current['natural_press'],transition=config).to(current['device'])
    def pins(current,out,extra=()):
        paths=[Path(__file__).resolve(),*(ROOT/name for name in config['bundle_files']),*(ROOT/name for name in config['geometry_inputs']),
            BASE/'geometry/initial_catalog.json',BASE/'geometry/initial_provenance.json']
        return original[3](current,out,list(extra)+paths)
    def metadata(*args,**kwargs):
        kwargs['transition']=copy.deepcopy(config)
        kwargs['transition_runtime_sha256']=natural.digest(Path(__file__).resolve())
        return original[4](*args,**kwargs)
    runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins,runner.checkpoint_metadata=factory,TransitionPool,natural.NaturalTrainer,pins,metadata
    try:yield
    finally:runner._policy,rollout.GpuPool,ppo.DecisionPPOTrainer,runner._pins,runner.checkpoint_metadata=original


def build_settings(condition='E4',*,updates=100,seed=7,num_envs=64,size='large'):
    from guitar_learning.training.launch import settings_document
    config=sequence_config(condition)
    settings=settings_document(song=SONG,size=size,num_envs=num_envs,horizon=32,updates=updates,seed=seed,checkpoint_every=100)
    settings['natural_press']=initial_configuration(condition)
    settings['transition']=config;settings['ppo']['retry_lr_factor']=.5
    settings['simple_start']['initial_pose']='transition_v2:A_aligned; whole AB; learned arm16; no phase clamp'
    return settings


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=('train','evaluate','render'))
    parser.add_argument('--out',type=Path,required=True);parser.add_argument('--condition',choices=('E4',))
    parser.add_argument('--updates',type=int,default=100);parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--num-envs',type=int);parser.add_argument('--size',choices=('small','medium','large'),default='large')
    parser.add_argument('--action-mode',choices=('mean','sampled'),default='mean')
    parser.add_argument('--checkpoint',type=Path);parser.add_argument('--resume',type=Path);args=parser.parse_args()
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.portability import localize
    out=args.out.resolve()
    if out.exists():raise FileExistsError('기존 출력 보존: '+str(out))
    if args.updates<1:parser.error('양수 updates 필요')
    source=args.resume if args.operation=='train' else args.checkpoint
    if args.operation=='train' and args.checkpoint:parser.error('train은 --resume만 허용')
    if args.operation!='train' and (not source or args.resume):parser.error('평가/영상은 --checkpoint 필요')
    if args.operation=='evaluate' and args.num_envs not in (None,32):parser.error('평가는 고정32환경')
    if source:
        source=source.resolve();before=natural.digest(source);payload=torch.load(source,map_location='cpu',weights_only=False)
        runner._validate_pins(payload['metadata']);settings=localize(payload['metadata']['settings']);validate(settings)
        if payload['identity']['architecture']['schema']!=TransitionPolicy.schema:raise ValueError('새 AB 전용 체크포인트만 허용')
        if args.condition is not None and args.condition!=settings['transition']['condition']:raise ValueError('저장 조건 변경 불가')
    else:settings=build_settings(args.condition or 'E4',updates=args.updates,seed=args.seed,num_envs=args.num_envs or 64,size=args.size)
    with transition_runtime(settings):
        if args.operation=='train':
            if source and (args.seed!=settings['seed'] or args.num_envs is not None and args.num_envs!=settings['num_envs']):
                raise ValueError('strict resume seed/환경 수 유지')
            settings['updates']=args.updates
            report=runner.run(settings,SimpleNamespace(out=out,resume=source))
        elif args.operation=='evaluate':
            original=runner._DeterministicPolicy
            class EvaluationPolicy(original):
                def act(self,*inputs):return self.policy.act(*inputs,deterministic=args.action_mode=='mean')
            runner._DeterministicPolicy=EvaluationPolicy
            try:
                report,_=runner.evaluate_checkpoint(source,out,num_envs=32,scope='full_song',max_episodes=32)
                (out/'action_mode.json').write_text(json.dumps(dict(action_mode=args.action_mode,evaluation_seed=settings['seed'],first_episodes=32)))
            finally:runner._DeterministicPolicy=original
        else:
            from guitar_learning.tool.demonstration.render_finger_skill import render
            report=render(source,out,num_envs=args.num_envs or 4,scope='full_song')
    if source and natural.digest(source)!=before:raise ValueError('실행 중 원본 체크포인트 변경')
    if not report.get('completed') or report.get('failure'):raise RuntimeError('실행 미완료; 보고서 확인')


if __name__=='__main__':main()
