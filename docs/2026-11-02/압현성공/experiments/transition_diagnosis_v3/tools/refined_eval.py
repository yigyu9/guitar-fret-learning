"""봉인된 v3 정책의 요청각 기대값을256/128 또는512/256점으로 재평가한다.

학습·기존 runtime·checkpoint는 바꾸지 않는다. 평가 실행 해석과 실제 적분
노드 수를 별도 기록하며 checkpoint의 기존 엄격 입력 검증은 그대로 수행한다.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

TOOLS=Path(__file__).resolve().parent
ROOT=next(p for p in TOOLS.parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0,str(ROOT))


def load_runtime():
    spec=importlib.util.spec_from_file_location('sealed_runtime_refined_evaluation',TOOLS/'runtime.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def quadrature_factory(runtime,fine_nodes):
    """512점에서 NumPy hermgauss의 overflow를 피하도록 SciPy의 안정된 근을 쓴다."""
    import math
    import torch
    from scipy.special import roots_hermite
    if fine_nodes not in (256,512):raise ValueError('명시적256/512점 필요')
    cache={};calls={fine_nodes:0,fine_nodes//2:0}
    def expected(policy,mean,log_std,*,nodes=32):
        actual=fine_nodes if nodes==32 else fine_nodes//2 if nodes==16 else None
        if actual is None:raise ValueError('봉인 runtime의32/16점 호출만 치환 가능')
        key=(id(policy),str(mean.device),mean.dtype,actual)
        if key not in cache:
            x,weight=roots_hermite(actual)
            catalog,_=runtime.natural.catalog_goal(policy.natural_press)
            reference=mean.new_tensor(catalog['reference105'])[torch.tensor(catalog['action_indices'],device=mean.device)]
            lower=mean.new_tensor(catalog['action_lower']);upper=mean.new_tensor(catalog['action_upper'])
            cache[key]=(mean.new_tensor(x),mean.new_tensor(weight/math.sqrt(math.pi)),reference,lower,upper)
        x,weight,reference,lower,upper=cache[key]
        action=torch.tanh(mean[...,None]+math.sqrt(2.)*log_std.exp()[...,None]*x)
        angles=reference[...,None]+torch.where(action>=0,(upper-reference)[...,None],(reference-lower)[...,None])*action
        requested=(angles*weight).sum(-1)
        normalized=runtime.natural.normalized_action(requested,reference,lower,upper)
        calls[actual]+=1
        return torch.where(policy._active_mask(),normalized,mean.tanh()),requested
    expected.actual_calls=calls
    return expected


def cpu_check(nodes):
    import torch
    r=load_runtime();configuration=r.initial_configuration()
    class Policy:
        natural_press=configuration
        def _active_mask(self):return torch.tensor([index in configuration['active_axes'] for index in range(39)])
    policy=Policy();mean=torch.linspace(-1.,1.,39,dtype=torch.float64).repeat(2,1)
    log_std=torch.full_like(mean,-1.5);fn=quadrature_factory(r,nodes)
    fine,angles=fn(policy,mean,log_std,nodes=32);coarse,coarse_angles=fn(policy,mean,log_std,nodes=16)
    assert torch.isfinite(fine).all() and torch.isfinite(coarse).all()
    assert (fine.abs()<=1.).all()
    assert torch.equal(fine[:,~policy._active_mask()],mean[:,~policy._active_mask()].tanh())
    assert fn.actual_calls=={nodes:1,nodes//2:1}
    print(json.dumps(dict(cpu_check=True,fine_nodes=nodes,coarse_nodes=nodes//2,
        maximum_test_error_rad=float((angles-coarse_angles)[:,policy._active_mask()].abs().max()))))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--out',type=Path);parser.add_argument('--nodes',type=int,choices=(256,512),default=256)
    parser.add_argument('--std-scale',type=float,choices=(.25,.5,1.),default=1.)
    parser.add_argument('--cpu-check',action='store_true');args=parser.parse_args()
    if args.cpu_check:cpu_check(args.nodes);return
    if not args.checkpoint or not args.out:parser.error('checkpoint/out 필요')
    if args.out.exists():raise FileExistsError(args.out)
    import isaacgym  # native를 Torch보다 먼저 초기화한다.
    import torch
    from guitar_learning.training import finger_skill_runner as runner
    from guitar_learning.portability import localize
    r=load_runtime();source=args.checkpoint.resolve();out=args.out.resolve()
    before=r.natural.digest(source);wrapper=Path(__file__).resolve();wrapper_sha=r.natural.digest(wrapper)
    runtime_sha=r.natural.digest(TOOLS/'runtime.py')
    payload=torch.load(source,map_location='cpu',weights_only=False)
    runner._validate_pins(payload['metadata']);settings=localize(payload['metadata']['settings']);r.validate(settings)
    if payload['identity']['architecture']['schema']!=r.TransitionPolicy.schema:raise ValueError('봉인 v3 전용 정책 필요')
    if 'initial_mix' in settings:raise ValueError('I 모델은 자체 초기분포 context 평가 필요; 이 실행기는 baseline D0 전용')
    original_expected=r.expected_requested_action;original_policy=runner._DeterministicPolicy
    refined=quadrature_factory(r,args.nodes);convergence=dict(max_error_rad=0.,calls=0)
    class EvaluationPolicy(original_policy):
        def act(self,*inputs):
            result=r.evaluation_action(self.policy,inputs,'expected-angle',args.std_scale)
            convergence['max_error_rad']=getattr(self.policy,'expected_angle_max_error_rad',0.)
            convergence['calls']=getattr(self.policy,'expected_angle_calls',0)
            return result
    r.expected_requested_action=refined;runner._DeterministicPolicy=EvaluationPolicy
    try:
        with r.transition_runtime(settings):
            original_pins=runner._pins
            def pins(current,destination,extra=()):return original_pins(current,destination,list(extra)+[wrapper])
            runner._pins=pins
            try:report,_=runner.evaluate_checkpoint(source,out,num_envs=32,scope='full_song',max_episodes=32)
            finally:runner._pins=original_pins
    finally:r.expected_requested_action=original_expected;runner._DeterministicPolicy=original_policy
    metadata=dict(action_mode='expected-angle',std_scale=args.std_scale,first_episodes=32,evaluation_seed=settings['seed'],
        quadrature_nodes=args.nodes,convergence_nodes=args.nodes//2,quadrature_algorithm='scipy.special.roots_hermite',
        quadrature_actual_calls=refined.actual_calls,quadrature_convergence=convergence,
        convergence_threshold_rad=.001,converged=convergence['calls']>0 and convergence['max_error_rad']<=.001,
        source_checkpoint_sha256=before,source_runtime_sha256=runtime_sha,evaluation_wrapper_sha256=wrapper_sha,
        scope='sealed v3 D0 evaluation only; checkpoint strict pins unchanged; physical controller unchanged')
    (out/'action_mode.json').write_text(json.dumps(metadata,indent=2)+'\n')
    if r.natural.digest(source)!=before or r.natural.digest(wrapper)!=wrapper_sha or r.natural.digest(TOOLS/'runtime.py')!=runtime_sha:
        raise ValueError('평가 중 봉인 입력 변경')
    if not report.get('completed') or report.get('failure'):raise RuntimeError('재평가 미완료; report 확인')

if __name__=='__main__':main()
