"""A6 초기 자세의 B8 단독 과제: 최초 팔 정책 bias의 포화만 줄인다."""
if __name__=='__main__':
    import isaacgym

import copy
from contextlib import contextmanager
import importlib.util
import math
from pathlib import Path
import sys

PARENT_PATH=Path(__file__).resolve().parents[2]/'전환개선_단독목표와준비시간_20261101/tools/runtime.py'
MODULE_NAME='guitar_middle_f8_single_gap_runtime'
if MODULE_NAME not in sys.modules:
    spec=importlib.util.spec_from_file_location(MODULE_NAME,PARENT_PATH)
    module=importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME]=module
    spec.loader.exec_module(module)
parent=sys.modules[MODULE_NAME]
torch=parent.torch
ROOT=parent.ROOT
BASE=Path(__file__).resolve().parents[1]
OriginalPolicy=parent.TransitionPolicy
_original_build=parent.build_settings
_original_validate=parent.validate
_original_runtime=parent.transition_runtime


def initialization_contract():
    return dict(schema='guitar_learning.initial_arm_bias_cap.v1',normalized_limit=.9,
        axes=list(parent.natural.ACTIVE_NAMES[:12]),operation='fresh constructor only: clamp support_head.bias[:12] to atanh(+-0.9)',
        scope='A6 reset; B8 single target; thumb inactive; learned means remain unrestricted',
        source_sha256={str(p.relative_to(ROOT)):parent.natural.digest(p) for p in (Path(__file__).resolve(),PARENT_PATH)})


def validate(settings):
    config=_original_validate(settings)
    if config['condition']!='b_only' or config['thumb_active']:
        raise ValueError('초기 bias 비교는 엄지 비활성 B8 단독 조건만 허용')
    if settings.get('policy_initialization')!=initialization_contract():
        raise ValueError('새 초기화 계약·소스 SHA 필요; 기존 checkpoint 재개 불가')
    return config


def build_settings(condition='b_only',**kwargs):
    if condition!='b_only':raise ValueError('B8 단독 조건만 허용')
    settings=_original_build(condition,**kwargs)
    settings['policy_initialization']=initialization_contract()
    validate(settings)
    return settings


class TransitionPolicy(OriginalPolicy):
    """새 정책 생성 때만 초기 팔 bias를 조정한다. forward·load는 그대로 둔다."""
    schema='guitar_learning.middle_f8_initial_arm_bias_cap_policy.v1'

    def __init__(self,*args,transition,**kwargs):
        if transition['condition']!='b_only' or transition['thumb_active']:
            raise ValueError('B8 단독·엄지 비활성 정책만 허용')
        super().__init__(*args,transition=transition,**kwargs)
        with torch.no_grad():
            self.core.support_head.bias[:12].clamp_(-math.atanh(.9),math.atanh(.9))
        self.architecture['policy_initialization']=initialization_contract()


@contextmanager
def _parent_bindings():
    names=('TransitionPolicy','build_settings','validate','transition_runtime')
    previous=[getattr(parent,name) for name in names]
    replacements=(TransitionPolicy,build_settings,validate,transition_runtime)
    for name,value in zip(names,replacements):setattr(parent,name,value)
    try:yield
    finally:
        for name,value in zip(names,previous):setattr(parent,name,value)


@contextmanager
def transition_runtime(settings):
    """기존 입력·관측·PPO 실행을 유지하며 새 wrapper도 엄격하게 봉인한다."""
    validate(settings)
    from guitar_learning.training import finger_skill_runner as runner
    with _parent_bindings(),_original_runtime(settings):
        old_pins,old_metadata=runner._pins,runner.checkpoint_metadata
        def pins(current,out,extra=()):
            validate(current)
            return old_pins(current,out,list(extra)+[Path(__file__).resolve(),PARENT_PATH])
        def metadata(*args,**kwargs):
            kwargs['policy_initialization']=copy.deepcopy(initialization_contract())
            return old_metadata(*args,**kwargs)
        runner._pins,runner.checkpoint_metadata=pins,metadata
        try:yield
        finally:runner._pins,runner.checkpoint_metadata=old_pins,old_metadata


def main():
    # 부모의 CLI/strict checkpoint 검증을 그대로 재사용한다. BASE·기하는 변경하지 않는다.
    with _parent_bindings():parent.main()


if __name__=='__main__':main()
