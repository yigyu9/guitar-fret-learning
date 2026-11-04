"""프로젝트 내부 가상 악보 번들로 현행 613열 J33 곡 학습을 실행한다.

공식 손가락별 진행 상태 환경·정책·PPO·엄격 checkpoint를 그대로 사용한다.
초기 자세는 v9이며 별도 준비 servo나 손목 교사를 학습에 연결하지 않는다.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').is_file())
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
# GPU 실행에서는 공식 모듈의 Torch보다 Isaac Gym을 먼저 import한다.
if __name__=='__main__' and '--self-test' not in sys.argv and not any(v in sys.argv for v in ('-h','--help')):
    import isaacgym
from guitar_learning.tool.experiments import song_finger_progress as progress
from guitar_learning.song.task import make_task,load_anchor_track
from guitar_learning.training import finger_skill_runner as runner

SCHEMA='guitar_learning.transition_bundle_learning.v1'


class BundlePolicy(progress.SongFingerProgressPolicy):
    """공식 runner가 초기 분산을 설정할 때 core의 기존 Parameter를 그대로 노출한다.

    property는 Parameter를 추가 등록하지 않는다. 저장 키·구조·확률 계산과
    엄격한 PPO identity는 상위613열 정책의 정의를 그대로 유지한다.
    """
    @property
    def support_log_std(self):return self.core.support_log_std

    @property
    def finger_log_std(self):return self.core.finger_log_std


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def local_bundle(path):
    """symlink 해석 후에도 프로젝트 내부의 디렉토리만 허용한다."""
    value=Path(path).resolve(strict=True)
    value.relative_to(ROOT)
    if not value.is_dir():raise ValueError('내부 곡 번들 디렉토리 필요')
    return value


def bundle_descriptor(bundle,task):
    manifest=json.loads((bundle/'manifest.json').read_text())
    files={}
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            path.resolve().relative_to(ROOT)
            files[str(path.relative_to(bundle))]=sha(path)
    if not files or 'manifest.json' not in files:raise ValueError('manifest를 포함한 완결 번들 필요')
    return dict(schema=SCHEMA,bundle=str(bundle),song_id=manifest['song_id'],files_sha256=files,
        target_count=len(task.targets),control_ticks=task.provenance['song']['control_ticks'],
        episode_duration_s=task.duration_s,source_event_count=task.provenance['song']['source_event_count'],
        family='613-state J33 E4 per-finger progress; official PPO and exposure schedule',
        preparation='common v9; no diagnostic servo, support teacher or phase action lock')


def actual_task(bundle,song):
    task=make_task(bundle,pre_roll_s=song['pre_roll_s'],tail_s=song['tail_s'])
    load_anchor_track(bundle)
    if any(target.fret==0 for target in task.targets):
        raise ValueError('현행 왼손 학습은 압현 음만 지원한다')
    return task


def validate_settings(settings):
    progress.validate_settings(settings)
    descriptor=settings.get('transition_bundle')
    if not isinstance(descriptor,dict) or descriptor.get('schema')!=SCHEMA:
        raise ValueError('이 가상 번들 진입점에서 만든 명시적 입력 계약 필요')
    bundle=local_bundle(settings['song_training']['bundle'])
    task=actual_task(bundle,settings['song'])
    expected=bundle_descriptor(bundle,task)
    if descriptor!=expected:raise ValueError('저장 번들 경로·파일 SHA·음 과제 변경')
    expected_training=dict(schema='guitar_learning.song_training.v1',song_id=expected['song_id'],bundle=str(bundle),
        target_count=expected['target_count'],control_ticks=expected['control_ticks'],episode_duration_s=task.duration_s,
        score_clock='original_audio_plus_policy_pre_roll',observation_dimension=progress.STATE_DIM)
    if settings['song_training']!=expected_training or settings['phrase_events']!=expected['source_event_count']:
        raise ValueError('실제 번들과 학습 시간·음 수·관측 설정 불일치')
    return task


def build_settings(bundle,*,updates=100,num_envs=64,size='large',horizon=32,seed=7,checkpoint_every=50):
    # 기본 존재 곡은 설정 뼈대 생성에만 쓴다. 아래에서 과제 관련 필드를 전부 실제 번들로 교체한다.
    settings=progress.build_settings(updates=updates,num_envs=num_envs,size=size,horizon=horizon,
        seed=seed,checkpoint_every=checkpoint_every)
    bundle=local_bundle(bundle);task=actual_task(bundle,settings['song']);record=bundle_descriptor(bundle,task)
    settings['song_training']=dict(schema='guitar_learning.song_training.v1',song_id=record['song_id'],bundle=str(bundle),
        target_count=len(task.targets),control_ticks=record['control_ticks'],episode_duration_s=task.duration_s,
        score_clock='original_audio_plus_policy_pre_roll',observation_dimension=progress.STATE_DIM)
    settings['phrase_events']=record['source_event_count'];settings['transition_bundle']=record
    validate_settings(settings)
    return settings


@contextmanager
def runtime():
    """공식 실행 연결 안에서 wrapper와 모든 생성 입력을 추가 봉인하고 항상 복원한다."""
    with progress.runtime():
        old_pins,old_policy,old_metadata=runner._pins,runner._policy,runner._validate_metadata_schema
        def pins(settings,out,extra=()):
            validate_settings(settings)
            return old_pins(settings,out,list(extra)+[Path(__file__).resolve()])
        def policy(settings,pool):
            validate_settings(settings)
            return BundlePolicy(pool.observation['state'].shape[-1],size=settings['size'],contract=pool.contract).to(settings['device'])
        def metadata(value):
            old_metadata(value)
            from guitar_learning.portability import localize
            validate_settings(localize(value['settings']))
        runner._pins,runner._policy,runner._validate_metadata_schema=pins,policy,metadata
        try:yield
        finally:runner._pins,runner._policy,runner._validate_metadata_schema=old_pins,old_policy,old_metadata


def read_checkpoint(path):
    settings=progress.read_checkpoint(path)
    validate_settings(settings)
    return settings


def train(args):
    if args.resume:
        settings=read_checkpoint(args.resume)
        if args.bundle is not None and local_bundle(args.bundle)!=local_bundle(settings['song_training']['bundle']):
            raise ValueError('재개에서는 저장 번들을 유지해야 함')
        for key in ('num_envs','size','horizon','seed'):
            value=getattr(args,key)
            if value is not None and value!=settings[key]:raise ValueError('재개에서는 저장된 '+key+' 유지 필요')
        settings['updates']=args.updates
        if args.checkpoint_every is not None:settings['checkpoint_every']=args.checkpoint_every
    else:
        if args.bundle is None:raise ValueError('새 학습에는 --bundle 필요')
        defaults=dict(num_envs=64,size='large',horizon=32,seed=7,checkpoint_every=50)
        options={key:getattr(args,key) if getattr(args,key) is not None else value for key,value in defaults.items()}
        settings=build_settings(args.bundle,updates=args.updates,**options)
    validate_settings(settings)
    with runtime():return runner.run(settings,SimpleNamespace(out=args.out,resume=args.resume))


def evaluate(checkpoint,out,num_envs=None):
    read_checkpoint(checkpoint)
    with runtime():return runner.evaluate_checkpoint(checkpoint,out,num_envs=num_envs,scope='full_song',max_batches=1,max_episodes=1024)


def render(checkpoint,out,num_envs=None):
    read_checkpoint(checkpoint)
    from guitar_learning.tool.demonstration.render_finger_skill import render as render_native
    with runtime():return render_native(checkpoint,out,num_envs=num_envs,scope='full_song')


def self_test():
    """실제 입력 검증과 설정 치환·factory 복원만 검사한다. GPU 학습은 하지 않는다."""
    import tempfile
    import copy
    from dataclasses import replace
    from unittest.mock import patch
    from guitar_learning.portability import portable,localize
    from guitar_learning.training.training_log_io import write
    from guitar_learning.training.ppo import DecisionPPOTrainer
    from guitar_learning.tests.test_song_finger_progress import policy
    from guitar_learning.portability import checkpoint_inputs,settings_digest
    import torch
    torch.set_num_threads(1)
    # runner의 초기 분산 변경은 core의 두 기존 Parameter만 변경해야 한다.
    reference=policy();adapter=BundlePolicy(613,size='small',contract=reference.architecture['contract'])
    assert adapter.state_dict().keys()==reference.state_dict().keys()
    assert adapter.architecture==reference.architecture
    assert adapter.support_log_std is adapter.core.support_log_std
    assert adapter.finger_log_std is adapter.core.finger_log_std
    before={key:value.clone() for key,value in adapter.state_dict().items()}
    shift=.17
    with torch.no_grad():
        adapter.support_log_std.add_(shift);adapter.finger_log_std.add_(shift)
    changed={key for key,value in adapter.state_dict().items() if not torch.equal(value,before[key])}
    assert changed=={'core.support_log_std','core.finger_log_std'}
    torch.testing.assert_close(adapter.core.support_log_std,before['core.support_log_std']+shift)
    torch.testing.assert_close(adapter.core.finger_log_std,before['core.finger_log_std']+shift)
    settings=build_settings(ROOT/'data/song_bundles/05_BN2-131-B_solo',updates=2,num_envs=2,size='small')
    task=validate_settings(settings)
    assert len(task.targets)==settings['song_training']['target_count']
    assert settings['song_training']['observation_dimension']==613
    assert settings['phrase_events']==task.provenance['song']['source_event_count']
    # 뼈대 곡의67음·길이가 실험 번들에 남지 않는지, 다른 과제의 모든 필드를 검사한다.
    provenance=copy.deepcopy(task.provenance);provenance['song']['source_event_count']=2
    provenance['song']['control_ticks']+=60
    alternate=replace(task,targets=task.targets[:2],provenance=provenance,episode_duration_s=task.duration_s+1.)
    with patch(__name__+'.actual_task',return_value=alternate):
        injected=build_settings(ROOT/'data/song_bundles/05_BN2-131-B_solo',updates=2,num_envs=2,size='small')
    assert injected['song_training']['target_count']==2 and injected['phrase_events']==2
    assert injected['song_training']['control_ticks']==provenance['song']['control_ticks']
    assert injected['song_training']['episode_duration_s']==alternate.duration_s
    broken=localize(portable(settings));broken['song_training']['target_count']+=1
    try:validate_settings(broken)
    except ValueError:pass
    else:raise AssertionError('실제 음 수 불일치 허용')
    broken=localize(portable(settings));broken['transition_bundle']['files_sha256']['manifest.json']='0'*64
    try:validate_settings(broken)
    except ValueError:pass
    else:raise AssertionError('번들 SHA 변경 허용')
    try:local_bundle('/tmp')
    except ValueError:pass
    else:raise AssertionError('외부 경로 허용')
    original=(runner._pins,runner._policy,runner._validate_metadata_schema)
    try:
        with runtime():
            assert runner._pins is not original[0]
            raise RuntimeError('검사 예외')
    except RuntimeError:pass
    assert (runner._pins,runner._policy,runner._validate_metadata_schema)==original
    with tempfile.TemporaryDirectory(dir=ROOT/'runs') as directory:
        directory=Path(directory);settings_path=directory/'settings.json';write(settings_path,portable(settings))
        metadata=dict(schema=progress.RESUME_SCHEMA,settings=portable(settings),settings_sha256=settings_digest(settings),
            input_contract=checkpoint_inputs({str(settings_path):sha(settings_path),str(Path(__file__).resolve()):sha(__file__)},
                settings,settings_path=settings_path))
        checkpoint=directory/'test.pt';DecisionPPOTrainer(adapter).save(checkpoint,metadata=metadata)
        restored=BundlePolicy(613,size='small',contract=reference.architecture['contract'])
        DecisionPPOTrainer(restored).load(checkpoint)
        assert all(torch.equal(value,restored.state_dict()[key]) for key,value in adapter.state_dict().items())
        assert read_checkpoint(checkpoint)==settings
        settings['transition_bundle']['files_sha256']['manifest.json']='0'*64
        with patch.object(progress,'read_checkpoint',return_value=settings):
            try:read_checkpoint(checkpoint)
            except ValueError:pass
            else:raise AssertionError('복원 입력 SHA 불일치 허용')
    print('CPU 검사 통과: 실제 과제 치환,613관측,번들 SHA/경로,엄격 checkpoint 입력/재개,runner 분산 alias/core 단독변경/저장키 불변,예외 factory 복원. GPU 실행 없음.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true')
    commands=parser.add_subparsers(dest='command')
    train_parser=commands.add_parser('train');train_parser.add_argument('--bundle',type=Path)
    train_parser.add_argument('--out',type=Path,required=True);train_parser.add_argument('--updates',type=int,default=100)
    train_parser.add_argument('--num-envs',type=int);train_parser.add_argument('--size',choices=('small','medium','large'))
    train_parser.add_argument('--horizon',type=int);train_parser.add_argument('--seed',type=int)
    train_parser.add_argument('--checkpoint-every',type=int);train_parser.add_argument('--resume',type=Path)
    for name in ('evaluate','render'):
        command=commands.add_parser(name);command.add_argument('--checkpoint',type=Path,required=True)
        command.add_argument('--out',type=Path,required=True);command.add_argument('--num-envs',type=int)
    args=parser.parse_args()
    if args.self_test:self_test();return
    if args.command is None:parser.error('train/evaluate/render 중 하나 필요')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    if args.command=='train':
        if args.updates<1 or (args.checkpoint_every is not None and args.checkpoint_every<1):parser.error('양수 학습·저장 반복 필요')
        return train(args)
    return globals()[args.command](args.checkpoint,args.out,args.num_envs)


if __name__=='__main__':main()
