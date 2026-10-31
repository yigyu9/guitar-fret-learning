"""과거 v2 소스를 복원한 독립 프로젝트에서 strict checkpoint 평가만 실행한다.

원본 source/input/체크포인트 핀은 수정하거나 우회하지 않는다. 이 파일의 평가
행동 해석만 명시적으로 변경하며 학습 재개와 결과를 혼용하지 않는다.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

def expected_requested_action(policy, mean, log_std, *, nodes=32):
    """잠재 Gaussian → tanh → 비대칭 목표각의 기대값을 구하고 행동으로 역변환한다.

    PD·평활화·변화율 제한은 이 계산 다음 기존 제어기에서 그대로 적용한다.
    """
    import numpy as np
    x, weight = np.polynomial.hermite.hermgauss(nodes)
    x = mean.new_tensor(x); weight = mean.new_tensor(weight/math.sqrt(math.pi))
    catalog, _ = natural.catalog_goal(policy.natural_press)
    ref=mean.new_tensor(catalog['reference105'])[torch.tensor(catalog['action_indices'],device=mean.device)]
    lower=mean.new_tensor(catalog['action_lower']); upper=mean.new_tensor(catalog['action_upper'])
    action=torch.tanh(mean[...,None]+math.sqrt(2.)*log_std.exp()[...,None]*x)
    angles=ref[...,None]+torch.where(action>=0,(upper-ref)[...,None],(ref-lower)[...,None])*action
    expected=(angles*weight).sum(-1)
    normalized=natural.normalized_action(expected,ref,lower,upper)
    # 비활성 축은 표본화하지 않는 기존 유지 명령을 그대로 둔다.
    return torch.where(policy._active_mask(),normalized,mean.tanh()),expected


def evaluation_action(policy, inputs, mode='mean', std_scale=1.):
    """평가만의 실행 해석. 학습 Gaussian/우도/보상은 변경하지 않는다."""
    if mode=='mean' or std_scale==0 and mode=='sampled':
        return policy.act(*inputs,deterministic=True)
    result=policy(*inputs); mean=result['mean']; active=policy._active_mask()
    if mode=='sampled':
        noise=torch.zeros_like(mean)
        noise[...,active]=torch.randn_like(mean[...,active])*result['log_std'][...,active].exp()*std_scale
        latent=mean+noise;action=latent.tanh()
    elif mode=='expected-angle':
        if std_scale<=0:raise ValueError('기대각 평가에는 양수 std 배율 필요')
        log_std=result['log_std']+math.log(std_scale)
        action,angles=expected_requested_action(policy,mean,log_std,nodes=32)
        _,coarse=expected_requested_action(policy,mean,log_std,nodes=16)
        error=(angles-coarse)[...,active].abs().max().item()
        policy.expected_angle_max_error_rad=max(getattr(policy,'expected_angle_max_error_rad',0.),error)
        policy.expected_angle_calls=getattr(policy,'expected_angle_calls',0)+1
        latent=torch.atanh(action.clamp(-.999999,.999999))
    else:raise ValueError('명시적 평가 방식 필요')
    result.update(action=action,latent=latent,logp=policy.log_probability(mean,result['log_std'],latent))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--num-envs',type=int,choices=(32,128),default=32)
    parser.add_argument('--action-mode',choices=('mean','sampled','expected-angle'),default='mean')
    parser.add_argument('--std-scale',type=float,choices=(0.,.25,.5,1.),default=1.)
    args=parser.parse_args()
    project=args.project_root.resolve();source=args.checkpoint.resolve();out=args.out.resolve()
    if out.exists():raise FileExistsError(out)
    if not (project/'guitar_learning').is_dir():raise ValueError('복원 프로젝트 필요')
    sys.path.insert(0,str(project))
    import isaacgym  # 반드시 Torch보다 먼저 초기화한다.
    global torch,natural
    import torch
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.portability import localize
    runtime=project/'docs/2026-11-02/압현성공/experiments/target_transition_v2/tools/transition_runtime.py'
    spec=importlib.util.spec_from_file_location('frozen_transition_v2',runtime)
    legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy);natural=legacy.natural
    if legacy.ROOT!=project or Path(runner.__file__).resolve().parents[2]!=project:
        raise ValueError('현재 프로젝트와 복원 프로젝트 import 혼합 금지')
    source_sha=natural.digest(source);payload=torch.load(source,map_location='cpu',weights_only=False)
    runner._validate_pins(payload['metadata'])
    settings=localize(payload['metadata']['settings']);legacy.validate(settings)
    if payload['identity']['architecture']['schema']!=legacy.TransitionPolicy.schema:
        raise ValueError('v2 전용 정책 필요')
    original=runner._DeterministicPolicy;quadrature=dict(max_error_rad=0.,calls=0)
    class EvaluationPolicy(original):
        def act(self,*inputs):
            result=evaluation_action(self.policy,inputs,args.action_mode,args.std_scale)
            quadrature['max_error_rad']=getattr(self.policy,'expected_angle_max_error_rad',0.)
            quadrature['calls']=getattr(self.policy,'expected_angle_calls',0)
            return result
    with legacy.transition_runtime(settings):
        original_pins=runner._pins
        def evaluation_pins(current,destination,extra=()):
            return original_pins(current,destination,list(extra)+[Path(__file__).resolve()])
        runner._pins=evaluation_pins;runner._DeterministicPolicy=EvaluationPolicy
        try:
            report,_=runner.evaluate_checkpoint(source,out,num_envs=args.num_envs,scope='full_song',max_episodes=args.num_envs)
        finally:runner._pins=original_pins;runner._DeterministicPolicy=original
    (out/'action_mode.json').write_text(json.dumps(dict(
        action_mode=args.action_mode,std_scale=args.std_scale,evaluation_seed=settings['seed'],
        first_episodes=args.num_envs,quadrature_nodes=32,convergence_nodes=16,
        quadrature_convergence=quadrature,source_checkpoint_sha256=source_sha,
        frozen_runtime_sha256=natural.digest(runtime),evaluation_wrapper_sha256=natural.digest(Path(__file__)),
        scope='restored historical project; original strict checkpoint validation retained; evaluation action only'),indent=2))
    if natural.digest(source)!=source_sha:raise ValueError('체크포인트 변경')
    if not report.get('completed') or report.get('failure'):raise RuntimeError('평가 미완료')

if __name__=='__main__':main()
