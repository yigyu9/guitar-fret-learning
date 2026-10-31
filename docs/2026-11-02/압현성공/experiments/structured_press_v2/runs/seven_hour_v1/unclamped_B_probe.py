"""동일 B 정책·초기 후보에서 press 단계의 팔 clamp만 제거하는 외부 진단."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
import copy
import fixed_reset_evaluate as fixed


def unclamped_step(pool,actions,sp):
    """원래 StructuredPool.step에서 B press 팔 지원 branch만 생략한다."""
    import torch
    env=pool.environment
    active=torch.tensor([i in pool.structured['active_axes'] for i in range(39)],dtype=torch.bool,device=actions.device)
    executed=torch.where(active,actions,env.hold_action)
    env.action_min.copy_(torch.minimum(env.action_min,executed))
    env.action_max.copy_(torch.maximum(env.action_max,executed))
    result=super(sp.StructuredPool,pool).step(executed)
    c=pool.controller
    applied=sp.normalized_action(c.target[:,c.active],c.reference[c.active],c.action_low,c.action_high)
    env.last_applied_action.copy_(applied)
    pool.observation=env.observation()
    return (pool.observation,)+result[1:]


@contextmanager
def execution_context(sp,official):
    original=sp.StructuredPool.step,sp.StructuredTrainer.load,official._pins
    owned='load' in sp.StructuredTrainer.__dict__
    record=dict(armed=False)
    def load(trainer,*args,**kwargs):
        result=original[1](trainer,*args,**kwargs)
        record.update(armed=True,trainer=trainer,updates=trainer.updates,
            model_before={k:v.detach().cpu().clone() for k,v in trainer.policy.state_dict().items()})
        return result
    def step(pool,actions):
        if not record['armed']:return original[0](pool,actions)
        return unclamped_step(pool,actions,sp)
    def pins(settings,out,extra=()):return original[2](settings,out,list(extra)+[Path(__file__).resolve()])
    sp.StructuredPool.step,sp.StructuredTrainer.load,official._pins=step,load,pins
    try:yield record
    finally:
        sp.StructuredPool.step,official._pins=original[0],original[2]
        if owned:sp.StructuredTrainer.load=original[1]
        else:delattr(sp.StructuredTrainer,'load')


def run(checkpoint,out):
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    # fixed.run 진입 전에 이루어지는 첫 structured_press import도 보호한다.
    with nested_input_paths():return _run(checkpoint,out)


def _run(checkpoint,out):
    import torch
    from guitar_learning.tool.experiments import structured_press as sp
    from guitar_learning.training import finger_skill_runner as official
    if out.exists():raise FileExistsError(str(out))
    saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    config=saved['metadata']['settings']['structured_press'];before_config=copy.deepcopy(config)
    if config['stage']!='B' or config['active_axes']!=sp.active_axes('B',config['finger']):
        raise ValueError('saved B16 aligned checkpoint required')
    sources={str(p):fixed.digest(p) for p in (checkpoint,Path(__file__).resolve(),Path(fixed.__file__).resolve())}
    record=None
    facts=dict(diagnostic_only=True,execution_override='remove_B_press_arm_clamp_only',
        official_B_promotion=False,policy_mode='deterministic_saved_B_mean',changed_stage_or_initial_distribution=False,
        cross_model_pairing_verified=False,pairing_requirement='compare actual captured q105/hold with respective fixed control before effect claims')
    try:
        with execution_context(sp,official) as record:report=fixed.run(checkpoint,out,4242)
        trainer=record['trainer'];actual=trainer.policy.state_dict()
        if not record['armed'] or trainer.updates!=saved['updates'] or trainer.updates!=record['updates']:
            raise ValueError('strict load/update proof missing')
        if set(actual)!=set(saved['model']) or any(not torch.equal(v.detach().cpu(),saved['model'][k]) or
                not torch.equal(v.detach().cpu(),record['model_before'][k]) for k,v in actual.items()):
            raise ValueError('source weights changed')
        if config!=before_config or any(fixed.digest(Path(p))!=h for p,h in sources.items()):raise ValueError('source/config changed')
        if not report.get('completed') or not report.get('original_strict_load_completed') or not report.get('lifecycle_verified'):
            raise ValueError('native incomplete')
        facts.update(execution_input_sha256=sources,source_model_exact_unchanged=True,optimizer_updates_difference=0)
    except BaseException as error:
        facts.update(completed=False,execution_diagnostic_failure=type(error).__name__+': '+str(error));raise
    finally:
        path=out/'report.json'
        if path.exists():
            report=json.loads(path.read_text())
            report['original_fixed_reset_limitations']=report.get('limitations')
            facts['limitations']=['only B press arm clamp removed; saved B stage16/aligned distribution unchanged',
                'diagnostic execution override is not official B promotion; actual q/hold must match control before effect claims']
            report.update(facts)
            path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    import isaacgym
    run(args.checkpoint.resolve(),args.out.resolve())
