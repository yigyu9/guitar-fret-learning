"""저장 BASE B16의 지원·초기 후보를 유지하는 요청각 기댓값 배포 진단이다."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import sys
import fixed_reset_evaluate as fixed
import expected_angle_probe as expected

MODES=('latent_mean','requested_angle_mean')


def codec(payload,sp):
    """B를 free33으로 바꾸지 않고 실제 저장39축 codec을 catalog와 대조한다."""
    import torch
    from guitar_learning.portability import localize
    settings=localize(payload['metadata']['settings']);config=settings['structured_press']
    if config['stage']!='B' or config['active_axes']!=sp.active_axes('B',config['finger']) or len(config['active_axes'])!=16:
        raise ValueError('saved BASE B16 required')
    if payload['identity']['architecture']['schema']!=sp.StructuredPolicy.schema:raise ValueError('base policy schema required')
    catalog,_=sp.catalog_goal(config)
    c=payload['identity']['architecture']['contract']['action']['target_contract']
    indices=[c['joint_names'].index(name) for name in c['action_order']]
    ref=torch.tensor(c['reference105_rad'],dtype=torch.float64)[indices]
    lo,hi=(torch.tensor(c[key],dtype=torch.float64) for key in ('action_lower_rad','action_upper_rad'))
    values=((ref,torch.tensor(catalog['reference105'],dtype=torch.float64)[catalog['action_indices']]),
        (lo,torch.tensor(catalog['action_lower'],dtype=torch.float64)),(hi,torch.tensor(catalog['action_upper'],dtype=torch.float64)))
    if len(indices)!=39 or indices!=catalog['action_indices'] or any(not torch.allclose(a,b,atol=1e-6,rtol=0) for a,b in values):
        raise ValueError('actual39 codec/catalog mismatch')
    if not all(torch.isfinite(x).all() for x in (ref,lo,hi)) or not ((hi>ref).all() and (lo<ref).all()):raise ValueError('finite positive spans required')
    return config,hi-ref,ref-lo,Path(config['geometry'])


@contextmanager
def execution_context(sp,official,axes,positive,negative,mode):
    import torch
    if mode not in MODES:raise ValueError('unknown mode')
    original=official._DeterministicPolicy,official._pins,sp.StructuredTrainer.load
    owned='load' in sp.StructuredTrainer.__dict__
    record=dict(strict_loaded=False,act_calls=0,inactive_exact_calls=0,active_point_exact_calls=0,
        saturated_count=0,max_numerical_action_adjustment=0.)
    def load(trainer,*args,**kwargs):
        result=original[2](trainer,*args,**kwargs)
        record.update(strict_loaded=True,trainer=trainer,updates=trainer.updates,
            model_before={k:v.detach().cpu().clone() for k,v in trainer.policy.state_dict().items()})
        return result
    class Deployment:
        def __init__(self,policy):self.policy,self.phase=policy,policy.phase
        def __call__(self,*args):return self.policy(*args)
        def act(self,*args):
            result=self.policy.act(*args,deterministic=True)
            mask=self.policy._active_mask()
            if mask.nonzero().flatten().tolist()!=list(axes):raise ValueError('actual B16 active mask mismatch')
            old_action,old_latent=result['action'],result['latent']
            if mode!='latent_mean':
                mean,std=result['mean'],result['log_std']
                requested=expected.deployment_action(mean,std,positive.to(mean.device),negative.to(mean.device),'requested_angle_mean')
                eps=torch.finfo(mean.dtype).eps;latent=old_latent.clone();action=old_action.clone()
                latent[...,mask]=torch.atanh(requested[...,mask].clamp(-1+eps,1-eps));action[...,mask]=latent[...,mask].tanh()
                record['saturated_count']+=int((requested[...,mask].abs()>1-eps).sum())
                record['max_numerical_action_adjustment']=max(record['max_numerical_action_adjustment'],float((action[...,mask]-requested[...,mask]).abs().max()))
                result.update(action=action,latent=latent,logp=self.policy.log_probability(mean,std,latent))
            if not (torch.equal(result['action'][...,~mask],old_action[...,~mask]) and torch.equal(result['latent'][...,~mask],old_latent[...,~mask])):
                raise ValueError('inactive23 changed')
            if not torch.equal(result['action'][...,mask],result['latent'][...,mask].tanh()) or not all(torch.isfinite(result[key]).all() for key in ('action','latent','logp')):
                raise ValueError('active action/latent/logp mismatch or nonfinite')
            record['act_calls']+=1;record['inactive_exact_calls']+=1;record['active_point_exact_calls']+=1
            return result
    helpers=[Path(__file__).resolve(),Path(expected.__file__).resolve(),Path(fixed.__file__).resolve(),Path(expected.trace.__file__).resolve()]
    def pins(settings,out,extra=()):return original[1](settings,out,list(extra)+helpers)
    official._DeterministicPolicy,official._pins,sp.StructuredTrainer.load=Deployment,pins,load
    try:yield record
    finally:
        official._DeterministicPolicy,official._pins=original[:2]
        if owned:sp.StructuredTrainer.load=original[2]
        else:delattr(sp.StructuredTrainer,'load')


def raw_metrics(out):
    from guitar_learning.training.training_log_io import iter_episode_rows
    episodes=[row['episode'] for row in iter_episode_rows(out)]
    if len(episodes)!=32 or {e['env_id'] for e in episodes}!=set(range(32)):raise ValueError('unique first32 denominator required')
    terms=expected.trace.TERMS
    for e in episodes:
        if (set(e['reward_components'])!=set(terms) or abs(sum(e['reward_components'].values())-e['reward'])>2e-5 or
            abs(sum(e['cost_components'].values())-e['cost'])>2e-5):
            raise ValueError('raw nine-term reconciliation failed')
    failed=lambda e:bool(e['termination']['physical_failure'] or e['termination']['wrist_failure'])
    avg=lambda values:sum(values)/32
    cost_keys=set().union(*(e['cost_components'] for e in episodes))
    return dict(count=32,safe_success=sum(e['song']['left_success_count']>0 and not failed(e) for e in episodes),
        failure_episodes=sum(failed(e) for e in episodes),mean_reward=avg([e['reward'] for e in episodes]),mean_cost=avg([e['cost'] for e in episodes]),
        mean_safe_clean_s=avg([0. if failed(e) else e['left_note_ledger']['values']['clean'][0] for e in episodes]),
        reward_components_mean={k:avg([e['reward_components'][k] for e in episodes]) for k in terms},
        cost_components_mean={k:avg([e['cost_components'].get(k,0.) for e in episodes]) for k in cost_keys},
        scope='undiscounted raw completed first32 episodes; no per-step discounted-return claim')


def run(checkpoint,out,mode='requested_angle_mean'):
    if mode not in MODES:raise ValueError('unknown mode')
    checkpoint,out=checkpoint.resolve(),out.resolve()
    if out.exists():raise FileExistsError(str(out))
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    with nested_input_paths():
        import torch
        from guitar_learning.tool.experiments import structured_press as sp
        from guitar_learning.training import finger_skill_runner as official
        payload=torch.load(checkpoint,map_location='cpu',weights_only=False)
        official._validate_metadata_schema(payload['metadata']);official._validate_pins(payload['metadata'])
        config,positive,negative,catalog=codec(payload,sp)
        sources=(checkpoint,Path(__file__).resolve(),Path(expected.__file__).resolve(),Path(fixed.__file__).resolve(),Path(expected.trace.__file__).resolve(),catalog)
        before={str(p):fixed.digest(p) for p in sources};record=None
        facts=dict(diagnostic_only=True,deployment_rule=mode,policy_mode='saved_B16_'+mode,
            stage_B_support_unchanged=True,initial_distribution_unchanged=True,clamp_unchanged=True,
            saved_gaussian_mean_std_unchanged=True,optimizer_updates_difference=0,
            deterministic_policy_unchanged=mode=='latent_mean',source_weights_unchanged=True,
            likelihood='original saved policy density at selected finite latent; not deterministic deployment-rule density',
            limitation='requested angle mean BEFORE unchanged B support clamp/smoothing/rate/physics; not final supported-target or physical expectation',
            per_step_discounted_return_available=False,reward_gamma=payload['metadata']['settings']['ppo']['gamma'],cost_gamma=payload['metadata']['settings']['ppo']['cost_gamma'])
        try:
            with execution_context(sp,official,config['active_axes'],positive,negative,mode) as record:report=fixed.run(checkpoint,out,4242)
            if not record['strict_loaded'] or record['act_calls']<=0:raise ValueError('strict load/action evidence missing')
            trainer=record['trainer'];actual=trainer.policy.state_dict()
            if trainer.updates!=payload['updates'] or trainer.updates!=record['updates'] or set(actual)!=set(payload['model']) or any(
                not torch.equal(value.detach().cpu(),payload['model'][key]) or not torch.equal(value.detach().cpu(),record['model_before'][key]) for key,value in actual.items()):
                raise ValueError('source model/updates changed')
            if not report.get('completed') or report.get('lifecycle_verified') is not True or not report.get('original_strict_load_completed'):
                raise ValueError('original native incomplete')
            if any(fixed.digest(Path(p))!=h for p,h in before.items()):raise ValueError('source/helper changed')
            facts['raw_metrics']=raw_metrics(out)
        except BaseException as error:
            facts.update(completed=False,expected_B_failure=type(error).__name__+': '+str(error));raise
        finally:
            path=out/'report.json'
            if path.exists():
                report=json.loads(path.read_text());facts['original_fixed_report_sha256']=fixed.digest(path)
                facts['expected_B_input_sha256']=before
                if record:facts['execution_audit']={k:v for k,v in record.items() if k not in ('trainer','model_before')}
                report.update(facts);path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--mode',choices=MODES,default='requested_angle_mean');args=parser.parse_args()
    import isaacgym
    run(args.checkpoint,args.out,args.mode)
