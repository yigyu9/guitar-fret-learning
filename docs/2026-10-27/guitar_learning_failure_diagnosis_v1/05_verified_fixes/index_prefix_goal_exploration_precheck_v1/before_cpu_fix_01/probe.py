"""Two root-only native evaluations; original strict model, explicit std execution override."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent

def module(name,path):
    if name not in sys.modules:
        s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);sys.modules[name]=v;s.loader.exec_module(v)
    return sys.modules[name]
recovery=module('exploration_precheck_recovery',HERE.parent/'index_prefix_goal_codec_v1/recovery_v1/probe.py')
source=recovery.source;parent=source.parent;grid,cap=source.grid,source.cap
EXPLORATION=HERE.parents[1]/'04_ablation/prefix_release_alignment_v1/exploration/results_v1'
MODES=('deterministic','stochastic')
SCHEMA='diagnostic.index_prefix_goal_exploration.execution.v1'
CHECKPOINT=recovery.CHECKPOINT


def output(mode):
    if mode not in MODES:raise ValueError('Only deterministic/stochastic evaluation')
    return HERE/'runs'/mode


def evidence():
    _,paths=recovery.gate();paths.update(parent.base.reviewed(source.HERE/'analysis/results_recovery_v1/review.json'))
    review=grid.read(EXPLORATION/'review.json');assert review['verdict']=='PASS' and not review['findings']
    verification=grid.read(EXPLORATION/'verification.json');assert verification['completed'] and str(EXPLORATION/'verification.json') in review['reviewed_sha256']
    for mapping in (review['reviewed_sha256'],verification['input_sha256']):
        assert all(grid.sha(p)==h for p,h in mapping.items());paths.update(map(Path,mapping))
    value=grid.read(EXPLORATION/'comparison.json');sigma=value['candidate_sigma4'];assert len(sigma)==4 and all(math.isfinite(x) and x>0 for x in sigma)
    assert value['original_effective_std']==0.17117105424404144 and abs(value['nominal_rad']-(4/60)*value['original_effective_std'])<1e-17
    assert all(abs(x*l-value['nominal_rad'])<1e-15 for x,l in zip(sigma,value['L_rad_per_raw4']))
    return paths|{EXPLORATION/'review.json',HERE/'probe.py',HERE/'cpu_checks.py',HERE/'PLAN.md',HERE/'README.md'},sigma


def gate(mode='deterministic',require_review=True):
    output(mode);paths,sigma=evidence();seal=grid.read(HERE/'preparation_seal.json')
    assert all(Path(p).is_file() and grid.sha(p)==h for p,h in seal['input_pins'].items())
    if require_review:
        r=grid.read(HERE/'review.json');assert seal['independent_review']=='passed_no_findings' and r['verdict']=='PASS' and not r['findings']
        assert seal['input_pins'][str(HERE/'review.json')]==grid.sha(HERE/'review.json') and all(grid.sha(p)==h for p,h in r['reviewed_sha256'].items())
    return seal,paths|{HERE/'preparation_seal.json',*map(Path,seal['input_pins'])},sigma


def install(policy,observation,sigma):
    import torch
    from guitar_learning.training.gpu_pool import FIELDS
    original={k:v.detach().clone() for k,v in policy.state_dict().items()};assert len(original)==73
    assert policy.architecture['learned_action_indices']==[17,18,19,20]
    with torch.no_grad():
        before=policy(*(observation[k] for k in FIELDS));proposed=policy.finger_log_std.new_tensor(sigma).log()
        assert ((proposed>=-5)&(proposed<=2)).all();policy.finger_log_std[:4].copy_(proposed)
        after=policy(*(observation[k] for k in FIELDS))
    changed=[n for n,v in policy.state_dict().items() if not torch.equal(v,original[n])];assert changed==['finger_log_std']
    assert torch.equal(policy.finger_log_std[4:],original['finger_log_std'][4:])
    other=[i for i in range(39) if i not in (17,18,19,20)]
    assert torch.equal(before['log_std'][:,other],after['log_std'][:,other]) and all(torch.equal(before[k],after[k]) for k in ('mean','reward_value','cost_value'))
    return dict(changed_state_names=changed,other_state_tensors_exact=72,changed_parameter='finger_log_std[0:4]',other12_finger_std_exact=True,other35_effective_std_exact=True,mean_and_critics_exact=True,
        original_log_std4=original['finger_log_std'][:4].cpu().tolist(),new_log_std4=proposed.cpu().tolist(),actual_effective_std4=after['log_std'][0,17:21].exp().cpu().tolist(),formula_sigma4=list(sigma))


def rng():
    import pickle,random
    import numpy as np
    import torch
    value=(random.getstate(),np.random.get_state(),torch.get_rng_state().numpy(),[x.cpu().numpy() for x in torch.cuda.get_rng_state_all()] if torch.cuda.is_initialized() else [])
    return hashlib.sha256(pickle.dumps(value)).hexdigest()


class Actions:
    def __init__(self,policy,mode,audit):self.policy,self.mode,self.audit=policy,mode,audit
    def act(self,*args,deterministic):
        import torch
        assert deterministic is True  # Original evaluator control='policy'; actual override is separately declared.
        actual=self.mode=='deterministic';before=rng();result=self.policy.act(*args,deterministic=actual);advanced=rng()!=before
        assert advanced is not actual and torch.equal(result['action'],result['latent'].tanh()) and torch.isfinite(result['logp']).all()
        self.audit['calls']+=1;self.audit['requested_deterministic_true']+=1;self.audit['actual_deterministic_true']+=int(actual);self.audit['actor_RNG_advances']+=int(advanced)
        return result


@contextmanager
def adapter(mode,sigma,observed):
    import random
    import numpy as np
    import torch
    codec=source.support();extra=parent.support()
    facade=SimpleNamespace(parent=parent,source=source.source,SCHEMA=source.SCHEMA,output=lambda stage:output(mode) if stage=='evaluate' else source.output(stage))
    with codec.execution_scope(facade,'evaluate',observed['seal'],observed['paths'],observed):
        prior=parent.base.effort_scope
        @contextmanager
        def scoped(paths,state):
            with prior(paths,state) as runner:
                old=(runner._evaluate,runner.DecisionPPOTrainer,codec.convert);trainers=[]
                def trainer(*a,**k):
                    value=old[1](*a,**k);trainers.append(value);return value
                def convert(*a,**k):observed['conversion_calls']+=1;return old[2](*a,**k)
                def evaluate(pool,policy,spec,args,out):
                    assert args.control=='policy' and args.episodes==pool.num_envs==128 and len(trainers)==1 and trainers[0].updates==0
                    assert Path(args.checkpoint).resolve()==CHECKPOINT
                    observed['strict_load_reached_before_override']=True;observed['std_override']=install(policy,pool.observation,sigma)
                    # Original full load restored checkpoint RNG; declared seed7 override follows it.
                    random.seed(7);np.random.seed(7);torch.manual_seed(7)
                    before=parent.guard.fingerprints(policy,trainers[0]);observed['policy_before']=before
                    try:return extra.evaluate(pool,Actions(policy,mode,observed['sampling']),spec,args,out)
                    finally:
                        after=parent.guard.fingerprints(policy,trainers[0]);observed['policy_after']=after
                        assert all(before[k]==after[k] for k in ('model_sha256','updates','cost_weight'))
                runner._evaluate=evaluate;runner.DecisionPPOTrainer=trainer;codec.convert=convert
                try:yield runner
                finally:
                    runner._evaluate,runner.DecisionPPOTrainer,codec.convert=old;observed['sampling_aliases_restored']=(runner._evaluate,runner.DecisionPPOTrainer,codec.convert)==old
        parent.base.effort_scope=scoped
        try:yield
        finally:parent.base.effort_scope=prior


def finish(mode,observed,completed,failure):
    import numpy as np
    out=output(mode);state=observed.get('state',{});pool=state.get('pool');cap.owned(out,state['identity']);secondary=None
    try:
        rows=observed.get('records',[])
        if rows:
            with (out/'observations4.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in rows]) for k in rows[0]})
            env0=[r for r in rows if r['env_id']==0];keys=('start_clock','clock','raw_goal_normalized','decoded_goal_rad','requested_NN_action','old_target_rad','final_target_rad','raw_DIP_target_rad','final_DIP_target_rad','current_goal')
            with (out/'goal_codec_env0.npz').open('xb') as f:np.savez_compressed(f,**{k:np.asarray([r[k] for r in env0]) for k in keys})
        if pool is not None and pool.guard_rows:
            with (out/'current_goal_DIP60.npz').open('xb') as f:np.savez_compressed(f,**{k:np.stack([r[k] for r in pool.guard_rows]) for k in pool.guard_rows[0]})
        if (out/'evaluation.json').is_file():grid.write(out/'prefix_acceptance.json',parent.acceptance(grid.read(out/'evaluation.json')['episodes']))
    except BaseException as error:secondary=error
    sampling=observed['sampling'];before=observed.get('policy_before',{});after=observed.get('policy_after',{})
    checks=dict(strict_load_before_override=observed.get('strict_load_reached_before_override',False),model_after_override_frozen=bool(before) and all(before.get(k)==after.get(k) for k in ('model_sha256','updates','cost_weight')),
        sampling_calls=bool(sampling['calls']) and sampling['requested_deterministic_true']==sampling['calls'] and sampling['actual_deterministic_true']==(sampling['calls'] if mode=='deterministic' else 0) and sampling['actor_RNG_advances']==(sampling['calls'] if mode=='stochastic' else 0),
        conversion_once=observed['conversion_calls']==sampling['calls'],aliases_restored=observed.get('aliases_restored',False) and observed.get('goal_aliases_restored',False) and observed.get('sampling_aliases_restored',False),
        native_completed=grid.read(out/'diagnostic_report.json').get('completed') is True,NN1_reference0=observed.get('NN_constructors')==1 and observed.get('reference_calls')==0,checkpoint_unchanged=grid.sha(CHECKPOINT)==recovery.MODEL_SHA,typed_outputs_saved=secondary is None)
    value=dict(schema=SCHEMA,completed=completed and all(checks.values()),failure=failure,secondary_failure=dict(type=type(secondary).__name__,message=str(secondary)) if secondary else None,checks=checks,mode=mode,sampling=sampling,conversion_calls=observed['conversion_calls'],std_override=observed.get('std_override'),policy_before=before,policy_after=after,overall_RNG_changed=before.get('RNG_sha256')!=after.get('RNG_sha256'),
        old_model_RNG_frozen_callback_used=False,legacy_goal_codec_report_written=False,checkpoint=str(CHECKPOINT),checkpoint_sha256=recovery.MODEL_SHA,original_checkpoint_schema=source.SCHEMA,metadata_rewritten=False,seed_after_full_strict_load=7,PPO_updates=0,supervised_steps=1000,scope='Original full strict load and original prefix evaluator/GoalPool/128cap; declared std4+sampling override, not original model/distribution identity; actor RNG and model freeze audited separately')
    try:grid.write(out/'execution_override.json',value)
    except BaseException as error:
        if secondary is not None:print('Secondary execution report error: '+repr(error),file=sys.stderr);raise secondary from None
        raise
    if secondary is not None:raise secondary
    if failure is None and not all(checks.values()):raise RuntimeError('Goal exploration execution audit failed')


def launch(mode):
    out=output(mode);cap.reject_existing(out);seal,paths,sigma=gate(mode);observed=dict(seal=seal,paths=paths,conversion_calls=0,sampling=dict(calls=0,requested_deterministic_true=0,actual_deterministic_true=0,actor_RNG_advances=0));completed=False;failure=None
    try:
        import isaacgym  # Entire stdlib gate precedes numerical/native imports.
        with adapter(mode,sigma,observed):parent.base.launch('evaluate',None,0)
        completed=True
    except BaseException as error:failure=dict(type=type(error).__name__,message=str(error));raise
    finally:
        if out.is_dir():
            try:finish(mode,observed,completed,failure)
            except BaseException as error:
                if failure is None:raise
                print('Secondary exploration audit error: '+repr(error),file=sys.stderr)


def commands():return {mode:[grid.PYTHON,'-B',str(Path(__file__).resolve()),'--execute',mode] for mode in MODES}


def prepare():
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));paths,sigma=evidence();cap.reject_existing(HERE/'cpu_inputs');cap.reject_existing(HERE/'preparation_seal.json')
    checks=module('goal_exploration_precheck_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__],sigma);inputs=HERE/'cpu_inputs';inputs.mkdir()
    for name,value in (('commands.json',commands()),('settings.json',parent.settings()),('execution_override.json',dict(schema=SCHEMA,sigma4=sigma,checkpoint=str(CHECKPOINT),seed=7,strict_load_then_override=True))):grid.write(inputs/name,value)
    grid.write(HERE/'cpu_verification.json',checks);paths|={HERE/'cpu_verification.json',*inputs.glob('*.json')}
    from guitar_learning.tool.experiments.short_finger_learning import runner
    grid.write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=runner._pins(parent.settings(),inputs,paths)))
    result=subprocess.run([grid.PYTHON,'-B',str(Path(__file__).resolve()),'--gate-check'],capture_output=True,text=True,check=True);grid.write(HERE/'fresh_process_gate.json',json.loads(result.stdout));seal=grid.read(HERE/'preparation_seal.json');seal['input_pins'][str(HERE/'fresh_process_gate.json')]=grid.sha(HERE/'fresh_process_gate.json');(HERE/'preparation_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(CPU_only=True,GPU_executed=False,pins=len(seal['input_pins']),commands=commands())))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    for n in ('prepare','self-test','gate-check','dry-plan'):g.add_argument('--'+n,action='store_true')
    g.add_argument('--execute',choices=MODES);a=p.parse_args();sys.path.insert(0,str(grid.ROOT))
    if a.prepare:prepare()
    elif a.self_test:
        value=grid.read(EXPLORATION/'comparison.json');print(json.dumps(module('goal_exploration_precheck_CPU',HERE/'cpu_checks.py').check(sys.modules[__name__],value['candidate_sigma4']),indent=2))
    elif a.execute:launch(a.execute)
    elif a.dry_plan:print(json.dumps(commands(),indent=2))
    else:
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));seal,_,_=gate(require_review=False)
        if seal['independent_review']=='pending':
            try:gate()
            except (FileNotFoundError,AssertionError):pass
            else:raise AssertionError('Pending native admitted')
        else:gate()
        assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'));print(json.dumps(dict(stdlib_only=True,GPU_executed=False,modes=list(MODES))))
