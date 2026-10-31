"""고정 Gaussian의 요청각 기댓값을 실행하는 배포 규칙 진단이다. 학습은 없다."""
import argparse
from contextlib import contextmanager
from functools import lru_cache
import json
from pathlib import Path
import sys
import reward_trace_probe as trace

MODES=('latent_mean','normalized_action_mean','requested_angle_mean')


@lru_cache(maxsize=2)
def quadrature(nodes):
    import numpy as np
    return np.polynomial.hermite.hermgauss(nodes)


def moments(mean,sigma,nodes=64):
    """E[tanh Z], E|tanh Z|. 절댓값의 1차 kink는 analytic E|Z|로 분리한다."""
    import math
    import torch
    if mean.shape!=sigma.shape or not torch.isfinite(mean).all() or not torch.isfinite(sigma).all() or (sigma<0).any():
        raise ValueError('finite matching mean and nonnegative sigma required')
    x,w=quadrature(nodes)
    m,s=mean.double(),sigma.double()
    x=torch.as_tensor(x,device=m.device,dtype=m.dtype);w=torch.as_tensor(w,device=m.device,dtype=m.dtype)/math.sqrt(math.pi)
    z=m[...,None]+math.sqrt(2)*s[...,None]*x
    normalized=(z.tanh()*w).sum(-1)
    safe=torch.where(s>0,s,torch.ones_like(s))
    absolute_z=s*math.sqrt(2/math.pi)*torch.exp(-m.square()/(2*safe.square()))+m*torch.erf(m/(math.sqrt(2)*safe))
    absolute_z=torch.where(s>0,absolute_z,m.abs())
    absolute=absolute_z+((z.tanh().abs()-z.abs())*w).sum(-1)
    return normalized.clamp(-1,1),absolute.clamp(0,1)


def deployment_action(mean,log_std,positive,negative,mode,nodes=64):
    """평활화·속도 제한 이전 요청각을 평균한 뒤 원래 piecewise codec으로 역변환한다."""
    import torch
    if mode not in MODES:raise ValueError('unknown deployment mode')
    if (positive<=0).any() or (negative<=0).any():raise ValueError('positive codec spans required')
    if mode=='latent_mean':return mean.tanh()
    first,absolute=moments(mean,log_std.exp(),nodes)
    if mode=='normalized_action_mean':return first.to(mean.dtype)
    p,n=positive.double(),negative.double()
    delta=(p+n)/2*first+(p-n)/2*absolute
    action=delta/torch.where(delta>=0,p,n)
    return action.clamp(-1,1).to(mean.dtype)


def codec(payload,sp):
    """실제 저장 제어 계약을 쓰며 catalog와39축 순서·기준·경계를 교차 검증한다."""
    import torch
    from guitar_learning.portability import localize
    settings=localize(payload['metadata']['settings']);config=settings['structured_press']
    if config['stage']!='free_v9' or config['active_axes']!=list(range(33)):
        raise ValueError('saved free_v9 all33 checkpoint required')
    catalog,_=sp.catalog_goal(config)
    contract=payload['identity']['architecture']['contract']['action']['target_contract']
    indices=[contract['joint_names'].index(name) for name in contract['action_order']]
    ref=torch.tensor(contract['reference105_rad'],dtype=torch.float64)[indices]
    low=torch.tensor(contract['action_lower_rad'],dtype=torch.float64)
    high=torch.tensor(contract['action_upper_rad'],dtype=torch.float64)
    c_ref=torch.tensor(catalog['reference105'],dtype=torch.float64)[catalog['action_indices']]
    if (indices!=catalog['action_indices'] or len(indices)!=39 or
        not torch.allclose(ref,c_ref,atol=1e-6,rtol=0) or
        not torch.allclose(low,torch.tensor(catalog['action_lower'],dtype=torch.float64),atol=1e-6,rtol=0) or
        not torch.allclose(high,torch.tensor(catalog['action_upper'],dtype=torch.float64),atol=1e-6,rtol=0)):
        raise ValueError('catalog and saved actual codec disagree')
    p,n=high-ref,ref-low
    if (p<=0).any() or (n<=0).any():raise ValueError('reference must be inside codec bounds')
    return p,n,Path(config['geometry'])


@contextmanager
def deployment_context(official,positive,negative,mode,*,goal_axes,arm_axes):
    import torch
    original=official._DeterministicPolicy,official._pins
    groups=dict(goal4=list(goal_axes),arm12=list(arm_axes))
    groups['other17']=[i for i in range(33) if i not in groups['goal4']+groups['arm12']]
    if [len(groups[k]) for k in ('goal4','arm12','other17')]!=[4,12,17]:raise ValueError('explicit33-axis grouping required')
    record=dict(policy_act_calls=0,env_action_samples=0,active_action_latent_verified_calls=0,finite_latent_adjustment=dict(saturated_active_count=0,max_normalized_action_change=0.,max_requested_angle_change_degrees=0.),observed_latent_mean_min=None,observed_latent_mean_max=None,
        observed_sigma_min=None,observed_sigma_max=None,
        requested_angle_difference_degrees={key:dict(count=0,absolute_sum=0.,signed_sum=0.,max_absolute=0.,axes=axes)
            for key,axes in groups.items()},scope='all evaluated act observations; requested angle BEFORE smoothing/rate/physics, relative to latent-mean request')
    class Deployment:
        def __init__(self,policy):self.policy,self.phase=policy,policy.phase
        def __call__(self,*inputs):return self.policy(*inputs)
        def act(self,*inputs):
            baseline=mode=='latent_mean'
            result=self.policy.act(*inputs,deterministic=True) if baseline else self.policy(*inputs)
            mean=result['mean'];active=self.policy._active_mask()
            if active.shape!=(39,) or active.nonzero().flatten().tolist()!=list(range(33)):
                raise ValueError('exact33 active policy required')
            old=mean.tanh();p,n=positive.to(mean.device),negative.to(mean.device)
            if not baseline:
                requested=deployment_action(mean,result['log_std'],p,n,mode)
                eps=torch.finfo(mean.dtype).eps
                selected=requested[...,active].clamp(-1+eps,1-eps)
                latent=mean.clone();latent[...,active]=torch.atanh(selected)
                # 반환 행동·latent·원래 정책 logp가 포화 경계에서도 같은 점을 뜻한다.
                action=old.clone();action[...,active]=latent[...,active].tanh()
                adjustment=record['finite_latent_adjustment']
                adjustment['saturated_active_count']+=int((requested[...,active].abs()>1-eps).sum())
                adjustment['max_normalized_action_change']=max(adjustment['max_normalized_action_change'],
                    float((action[...,active]-requested[...,active]).abs().max()))
                angle_change=(torch.where(action>=0,p,n)*action-torch.where(requested>=0,p,n)*requested)[...,active]
                adjustment['max_requested_angle_change_degrees']=max(adjustment['max_requested_angle_change_degrees'],
                    float(angle_change.abs().max()*180/torch.pi))
                # 원래 정책의 이 지점 밀도이며 새 결정적 배포 규칙의 밀도가 아니다.
                result.update(action=action,latent=latent,logp=self.policy.log_probability(mean,result['log_std'],latent))
            if (not torch.equal(result['action'][...,active],result['latent'][...,active].tanh()) or
                not torch.isfinite(result['latent']).all() or not torch.isfinite(result['logp']).all()):
                raise ValueError('actual act action/latent/logp point mismatch or nonfinite')
            record['active_action_latent_verified_calls']+=1
            delta=(torch.where(result['action']>=0,p,n)*result['action']-torch.where(old>=0,p,n)*old)*180/torch.pi
            record['policy_act_calls']+=1;record['env_action_samples']+=len(mean)
            for key,axes in groups.items():
                values=delta[...,axes].detach().double();summary=record['requested_angle_difference_degrees'][key]
                summary['count']+=values.numel();summary['absolute_sum']+=float(values.abs().sum())
                summary['signed_sum']+=float(values.sum());summary['max_absolute']=max(summary['max_absolute'],float(values.abs().max()))
            for field,value,operation in (('observed_latent_mean_min',mean[...,active].min(),min),
                ('observed_latent_mean_max',mean[...,active].max(),max),('observed_sigma_min',result['log_std'][...,active].exp().min(),min),
                ('observed_sigma_max',result['log_std'][...,active].exp().max(),max)):
                record[field]=float(value) if record[field] is None else operation(record[field],float(value))
            return result
    def pins(settings,out,extra=()):return original[1](settings,out,list(extra)+[Path(__file__).resolve()])
    official._DeterministicPolicy,official._pins=Deployment,pins
    try:yield record
    finally:
        for summary in record['requested_angle_difference_degrees'].values():
            summary['mean_absolute']=summary['absolute_sum']/summary['count'] if summary['count'] else None
            summary['mean_signed']=summary['signed_sum']/summary['count'] if summary['count'] else None
        official._DeterministicPolicy,official._pins=original


def annotate(out,before,mode,impact):
    path=out/'summary.json'
    if not path.exists():return
    summary=json.loads(path.read_text());native_path=out/'native/report.json'
    facts=dict(diagnostic_only=True,deployment_rule=mode,policy_mode='deterministic_expectation_deployment_diagnostic',
        saved_gaussian_mean_std_unchanged=True,optimizer_updates_difference=0,
        finite_latent_boundary='nonbaseline active action clamped to ±(1-dtype epsilon), latent=atanh(selected), returned action=tanh(latent); baseline and inactive6 unchanged; measured numerical adjustment in observed_request_impact',
        requested_angle_definition='reference + piecewise positive/negative span*tanh Z, BEFORE smoothing/rate/physical response',
        quadrature=dict(method='64-node Gauss-Hermite; analytic E|Z| plus smooth residual for E|tanh Z|',nodes=64),
        likelihood='original policy log_probability at selected latent=atanh(action); latent_mean baseline uses original deterministic act; not deployment-rule density',
        limitations=['요청각/정규화 행동 기댓값이며 실제 물리 응답의 기댓값이 아님','학습·원래 평균 정책 성능과 분리할 진단 배포 규칙','실패 포함 최초32환경; 실제 q/hold 일치 확인 후 비교'])
    try:
        if any(trace.digest(Path(p))!=h for p,h in before.items()):raise ValueError('source/checkpoint changed')
        if summary.get('completed'):
            for p,h in summary['output_sha256'].items():
                if trace.digest(Path(p))!=h:raise ValueError('native output changed')
        if native_path.exists():
            native=json.loads(native_path.read_text())
            if summary.get('completed') and (not native.get('completed') or native.get('lifecycle_verified') is not True or
                any(native.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))):
                raise ValueError('native lifecycle/integrity incomplete')
            facts['original_native_report_sha256']=trace.digest(native_path)
            native.update(facts);native_path.write_text(json.dumps(native,ensure_ascii=False,indent=2)+'\n')
            if summary.get('completed'):summary['output_sha256'][str(native_path)]=trace.digest(native_path)
        summary.update(facts);summary['observed_request_impact']=impact;summary.setdefault('input_sha256',{}).update(before)
    except BaseException as error:
        summary.update(completed=False,annotation_failure=type(error).__name__+': '+str(error));raise
    finally:
        path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
        (out/'SUMMARY.md').write_text('# 요청각 기댓값 배포 진단\n\n배포 규칙: '+mode+'\n\n완료: '+str(summary.get('completed',False))+
            '\n\n저장 Gaussian·가중치·물리·보상·초기 분포는 유지하고 실행 요청만 바꾼다. '
            '학습이나 원래 평균 정책으로 표기하지 않는다. 평활화/속도제한 이전 요청의 기댓값이며 물리 기댓값이 아니다.\n')


def run(checkpoint,out,mode):
    if mode not in MODES:raise ValueError('unknown mode')
    if out.exists():raise FileExistsError(str(out))
    sys.path.insert(0,str(trace.STUDY/'runtime'))
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        import torch
        from guitar_learning.tool.experiments import structured_press as sp
        from guitar_learning.training import finger_skill_runner as official
        payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
        official._validate_metadata_schema(payload['metadata']);official._validate_pins(payload['metadata'])
        positive,negative,catalog=codec(payload,sp)
        paths=(checkpoint,Path(__file__).resolve(),Path(trace.__file__).resolve(),trace.PROTOCOL,catalog)
        before={str(p):trace.digest(p) for p in paths}
        contract=payload['identity']['architecture']['contract']['action']['target_contract']
        finger=payload['metadata']['settings']['structured_press']['finger']
        goal=[i for i,name in enumerate(contract['action_order']) if name.startswith('LH:'+finger)]
        arm=[i for i,name in enumerate(contract['action_order'][:33]) if not name.startswith('LH:')]
        impact=None
        try:
            with deployment_context(official,positive,negative,mode,goal_axes=goal,arm_axes=arm) as impact:
                trace.run(checkpoint,out,'base')
        finally:annotate(out,before,mode,impact)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--mode',choices=MODES,default='requested_angle_mean');args=parser.parse_args()
    import isaacgym
    run(args.checkpoint.resolve(),args.out.resolve(),args.mode)
