"""손가락별 진행 상태를 관측하는 명시적 J33 곡 학습 진입점.

기존 557열 공동 정책에 손가락별 준비·정렬·접촉 상태를 별도 branch로 연결한다.
모든 왼손 33축을 처음부터 공동 제어하며 단계에 따른 행동 잠금이나 교사를 쓰지
않는다. 기본 학습 경로는 수정하지 않고, 이 모듈을 지정한 실행에서만 적용한다.
"""
import argparse
import copy
from contextlib import contextmanager
import os
import math
import sys
from pathlib import Path
from types import SimpleNamespace

# 실제 실행에서는 Isaac Gym이 Torch보다 먼저 로드되어야 한다.
if __name__ == '__main__' and not any(value in ('-h','--help') for value in sys.argv):
    import isaacgym
import torch
from torch import nn

from guitar_learning.training.policy import FingerSkillPolicy, Policy
from guitar_learning.gpu.finger_progress import (
    FingerProgressEnvironment, FINGER_PROGRESS_FIELDS, FINGER_PROGRESS_SCHEMA,
)

SCHEMA='guitar_learning.song_finger_progress.v1'
POLICY_SCHEMA='guitar_learning.song_finger_progress_policy.v1'
RESUME_SCHEMA='guitar_learning.song_finger_progress_resume.v1'
BASE_DIM=557
EXTRA_DIM=len(FINGER_PROGRESS_FIELDS)
STATE_DIM=BASE_DIM+EXTRA_DIM
FINGERS=('index','middle','ring','pinky')


def configuration():
    """추가 정보의 버전과 공동 제어 의미를 저장 설정에 명시한다."""
    return dict(schema=SCHEMA,observation_dimension=STATE_DIM,
        progress_fields=list(FINGER_PROGRESS_FIELDS),
        policy_schema=POLICY_SCHEMA,preparation='same E4 preparation observation/reward; no action gate or teacher',
        control='J33 independent direct position; all33 axes active from first policy tick')


def validate_settings(settings):
    if settings.get('finger_progress')!=configuration():
        raise ValueError('손가락 진행 상태 전용 설정/관측 계약 필요; 기존557/601열 모델은 호환되지 않음')
    from guitar_learning.training.finger_skill_runner import _validate_joint_settings
    _validate_joint_settings(settings)
    if settings.get('song_training',{}).get('observation_dimension')!=STATE_DIM:
        raise ValueError('진행 상태 학습 설정은613열 관측 차원을 명시해야 함')


class SongFingerProgressPolicy(nn.Module):
    """기존 J33 분포를 유지하며 4개 손가락별 상태 branch를 추가한다."""
    schema=POLICY_SCHEMA
    phase='J'
    exploration='independent'

    def __init__(self,state_dim,event_dim=24,size='medium',contract=None):
        super().__init__()
        if (state_dim!=STATE_DIM or not isinstance(contract,dict) or
                contract.get('observation',{}).get('dimension')!=STATE_DIM or
                contract['observation'].get('fields',[])[BASE_DIM:]!=list(FINGER_PROGRESS_FIELDS) or
                not isinstance(contract.get('finger_progress'),dict)):
            raise ValueError('별도 손가락 진행 상태 관측 계약과 정확한 추가 열 필요')
        progress_contract=contract['finger_progress']
        if (progress_contract.get('schema')!=FINGER_PROGRESS_SCHEMA or
                progress_contract.get('dimension')!=EXTRA_DIM or
                progress_contract.get('fields')!=list(FINGER_PROGRESS_FIELDS) or
                progress_contract.get('scales')!=contract['observation'].get('scales',[])[BASE_DIM:]):
            raise ValueError('손가락 진행 상태 환경 schema 불일치')
        base=copy.deepcopy(contract);base.pop('finger_progress')
        base['observation']['dimension']=BASE_DIM
        base['observation']['fields']=base['observation']['fields'][:BASE_DIM]
        base['observation']['scales']=base['observation']['scales'][:BASE_DIM]
        self.core=FingerSkillPolicy(BASE_DIM,event_dim=event_dim,size=size,contract=base)
        if EXTRA_DIM%4:raise ValueError('손가락별 같은 수의 진행 상태 열 필요')
        self.support_progress=nn.Sequential(nn.Linear(EXTRA_DIM,64),nn.Tanh(),nn.Linear(64,17))
        self.finger_progress=nn.ModuleDict({finger:nn.Sequential(
            nn.Linear(EXTRA_DIM//4,32),nn.Tanh(),nn.Linear(32,4)) for finger in FINGERS})
        self.value_progress=nn.Sequential(nn.Linear(EXTRA_DIM,64),nn.Tanh(),nn.Linear(64,2))
        for branch in (self.support_progress,*self.finger_progress.values(),self.value_progress):
            nn.init.zeros_(branch[-1].weight);nn.init.zeros_(branch[-1].bias)
        self.architecture=dict(schema=self.schema,state_dim=STATE_DIM,event_dim=event_dim,size=size,
            phase='J',exploration='independent',priority_slots=self.core.architecture['priority_slots'],
            likelihood=self.core.architecture['likelihood'],base=self.core.architecture,
            progress_branch=dict(schema='per_finger_progress_branch.v1',finger_width=EXTRA_DIM//4,
                support_hidden=64,finger_hidden=32,value_hidden=64,output_axes='support17 + finger4 x4',
                initialization='zero final layers; all branches trainable from first update'),
            contract=copy.deepcopy(contract))

    _validate=Policy._validate
    act=FingerSkillPolicy.act
    evaluate=FingerSkillPolicy.evaluate
    log_probability=FingerSkillPolicy.log_probability
    analytic_kl=FingerSkillPolicy.analytic_kl

    def _active_mask(self):return self.core._active_mask()

    def actor_parameters(self):
        return [*self.core.actor_parameters(),*self.support_progress.parameters(),*self.finger_progress.parameters()]

    def value_parameters(self):
        return [*self.core.value_parameters(),*self.value_progress.parameters()]

    def forward(self,state,events,mask,priority_events,priority_mask):
        self._validate(state,events,mask,priority_events,priority_mask)
        result=self.core(state[:,:BASE_DIM],events,mask,priority_events,priority_mask)
        extra=state[:,BASE_DIM:];per_finger=extra.reshape(len(state),4,EXTRA_DIM//4)
        support=self.support_progress(extra)
        fingers=[self.finger_progress[finger](per_finger[:,index]) for index,finger in enumerate(FINGERS)]
        delta=torch.cat((support,*fingers,state.new_zeros(len(state),6)),-1)
        values=self.value_progress(extra)
        return dict(mean=result['mean']+delta,log_std=result['log_std'],
            reward_value=result['reward_value']+values[:,0],cost_value=result['cost_value']+values[:,1])


def validate_metadata(metadata):
    if not isinstance(metadata,dict) or metadata.get('schema')!=RESUME_SCHEMA:
        raise ValueError('손가락 진행 상태 전용 checkpoint 필요; 기존557/601열 모델의 암묵적 변환은 지원하지 않음')
    validate_settings(metadata.get('settings',{}))


def read_checkpoint(checkpoint):
    """실행 전 출처·설정·관측 버전을 검증하며, 실제 로드는 원래 PPO가 엄격 검사한다."""
    from guitar_learning.portability import validate_checkpoint_inputs,localize
    payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
    if not isinstance(payload,dict):raise ValueError('PPO checkpoint 사전 필요')
    metadata=payload.get('metadata');validate_metadata(metadata)
    architecture=payload.get('identity',{}).get('architecture',{})
    if architecture.get('schema')!=POLICY_SCHEMA or architecture.get('state_dim')!=STATE_DIM:
        raise ValueError('진행 상태 정책 architecture 불일치; 기존 모델 불가')
    validate_checkpoint_inputs(metadata)
    return localize(metadata['settings'])


@contextmanager
def runtime():
    """이 명시 실행에서만 환경·정책·metadata factory를 교체하고 예외에도 복원한다."""
    from guitar_learning.training import rollout,finger_skill_runner as runner
    original=(rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)
    base_pool,base_pins=original[0],original[4]
    class ProgressPool(base_pool):
        environment_class_override=FingerProgressEnvironment
        def __init__(self,settings,out):
            validate_settings(settings)
            super().__init__(settings,out)
    def policy(settings,pool):
        validate_settings(settings)
        return SongFingerProgressPolicy(pool.observation['state'].shape[-1],size=settings['size'],contract=pool.contract).to(settings['device'])
    def resume_schema(settings):
        validate_settings(settings);return RESUME_SCHEMA
    def pins(settings,out,extra=()):
        import inspect
        paths=[Path(__file__).resolve(),Path(inspect.getsourcefile(FingerProgressEnvironment)).resolve()]
        return base_pins(settings,out,list(extra)+paths)
    rollout.GpuPool,runner._policy=ProgressPool,policy
    runner.resume_schema,runner._validate_metadata_schema=resume_schema,validate_metadata
    runner._pins,runner.SCHEMA=pins,SCHEMA
    try:yield
    finally:
        (rollout.GpuPool,runner._policy,runner.resume_schema,runner._validate_metadata_schema,runner._pins,runner.SCHEMA)=original


def build_settings(**options):
    from guitar_learning.training.launch import settings_document
    value=settings_document(**options)
    value['finger_progress']=configuration()
    value['song_training']['observation_dimension']=STATE_DIM
    return value


def train(args):
    from guitar_learning.training import finger_skill_runner as runner
    if args.resume:
        settings=read_checkpoint(args.resume)
        # 모델과 입력 identity가 바뀌는 요청은 복원 전에 명시적으로 거부한다.
        for key in ('song','size','num_envs','horizon','seed'):
            requested=getattr(args,key)
            saved=settings['song_training']['song_id'] if key=='song' else settings[key]
            if requested is not None and requested!=saved:raise ValueError('재개에서는 저장된 '+key+'을 유지해야 함')
        settings['updates']=args.updates
        if args.checkpoint_every is not None:settings['checkpoint_every']=args.checkpoint_every
    else:
        options={key:getattr(args,key) for key in ('song','size','num_envs','horizon','seed','checkpoint_every') if getattr(args,key) is not None}
        settings=build_settings(updates=args.updates,**options)
    if args.max_wall_seconds is not None:settings['max_wall_seconds']=args.max_wall_seconds
    validate_settings(settings)
    with runtime():return runner.run(settings,SimpleNamespace(out=args.out,resume=args.resume))


def evaluate(checkpoint,out,*,num_envs=None,scope='full_song'):
    from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
    read_checkpoint(checkpoint)
    with runtime():return evaluate_checkpoint(checkpoint,out,num_envs=num_envs,scope=scope)


def render(checkpoint,out,*,num_envs=None,scope='full_song'):
    from guitar_learning.tool.demonstration.render_finger_skill import render as native_render
    read_checkpoint(checkpoint)
    with runtime():return native_render(checkpoint,out,num_envs=num_envs,scope=scope)


def parser():
    value=argparse.ArgumentParser(description=__doc__);commands=value.add_subparsers(dest='command',required=True)
    command=commands.add_parser('train');command.add_argument('--out',type=Path,required=True)
    command.add_argument('--song');command.add_argument('--size',choices=('small','medium','large'))
    command.add_argument('--num-envs',type=int);command.add_argument('--updates',type=int,default=100)
    command.add_argument('--horizon',type=int);command.add_argument('--seed',type=int)
    command.add_argument('--checkpoint-every',type=int);command.add_argument('--resume',type=Path)
    command.add_argument('--max-wall-seconds',type=float)
    for name in ('evaluate','render'):
        command=commands.add_parser(name);command.add_argument('checkpoint',type=Path)
        command.add_argument('--out',type=Path,required=True);command.add_argument('--num-envs',type=int)
        command.add_argument('--scope',choices=('full_song','phrases'),default='full_song')
    return value


def main():
    args=parser().parse_args()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    if args.command=='train':
        if args.updates<1 or (args.checkpoint_every is not None and args.checkpoint_every<1):raise ValueError('반복과 저장 간격은 양수 필요')
        if args.max_wall_seconds is not None and (not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds<=0):raise ValueError('시간 예산은 유한 양수 필요')
        return train(args)
    return globals()[args.command](args.checkpoint,args.out,num_envs=args.num_envs,scope=args.scope)


if __name__=='__main__':main()
