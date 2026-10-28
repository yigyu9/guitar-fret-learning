"""Narrow CPU std/mode/codec/cleanup checks; no native imports or checkpoint writes."""
import copy
from contextlib import contextmanager
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe,sigma):
    import numpy as np
    import torch
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.gpu_pool import FIELDS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    codec=probe.source.support();extra=probe.parent.support();folder=probe.recovery.output('evaluate')
    payload=torch.load(probe.CHECKPOINT,map_location='cpu',weights_only=False);metadata=copy.deepcopy(payload['metadata']);contract=probe.grid.read(folder/'training_contract.json');settings=probe.parent.settings()
    policy=codec.policy_type(probe.source)(contract=contract,size='large',fresh=False);assert policy.architecture==payload['identity']['architecture'];policy.load_state_dict(payload['model'],strict=True)
    trainer=DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']));assert trainer._identity()==payload['identity']
    try:trainer.load(probe.CHECKPOINT)
    except ValueError as error:assert str(error)=='CUDA RNG topology mismatch'
    else:raise AssertionError('CPU unexpectedly restored native CUDA RNG')
    data=dict(np.load(folder/'observations4.npz',allow_pickle=False));observation={k:torch.from_numpy(data[k][:1].copy()).expand((128,)+data[k].shape[1:]).clone() for k in FIELDS};frozen={k:v.clone() for k,v in observation.items()}
    original={k:v.clone() for k,v in policy.state_dict().items()};override=probe.install(policy,observation,sigma)
    with torch.no_grad():result=policy(*(observation[k] for k in FIELDS))
    np.testing.assert_allclose(result['log_std'][0,17:21].exp().numpy(),sigma,rtol=2e-7,atol=0)
    for deterministic in (True,False):
        before=probe.rng()
        with torch.no_grad():r=policy.act(*(observation[k] for k in FIELDS),deterministic=deterministic)
        assert (probe.rng()!=before) is (not deterministic) and torch.equal(r['action'],r['latent'].tanh())
        assert torch.equal(r['logp'],policy.log_probability(r['mean'],r['log_std'],r['latent']))
    policy.load_state_dict(original,strict=True)
    action=contract['action']['target_contract'];active=torch.tensor([action['joint_names'].index(n) for n in action['action_order']]);reference=torch.tensor(action['reference105_rad']);ids=contract['task']['short_learning']['learned_action_indices']
    fakepool=SimpleNamespace(spec=contract['task']['short_learning'],num_envs=128,observation=observation,teacher_reference=reference[active],incremental_mask=torch.tensor([17<=i<33 for i in range(39)]),controller=SimpleNamespace(reference=reference,target=reference[None].repeat(128,1),active=active,action_low=torch.tensor(action['action_lower_rad']),action_high=torch.tensor(action['action_upper_rad'])))
    runner=SimpleNamespace(_evaluate=object(),DecisionPPOTrainer=lambda *a,**k:SimpleNamespace(updates=0,cost_weight=1))
    priorcap=probe.parent.base.effort_scope;old=(runner._evaluate,runner.DecisionPPOTrainer,codec.convert)
    @contextmanager
    def fakecap(paths,state):yield runner
    @contextmanager
    def fakegoal(producer,stage,seal,paths,observed):
        assert stage=='evaluate' and producer.SCHEMA==probe.source.SCHEMA
        previous=probe.parent.base.effort_scope;probe.parent.base.effort_scope=fakecap
        try:yield
        finally:probe.parent.base.effort_scope=previous
    def loop(pool,actions,spec,args,out):
        with torch.no_grad():
            for _ in range(2):
                r=actions.act(*(observation[k] for k in FIELDS),deterministic=True);request,goal=codec.convert(pool,r['action'])
                other=[i for i in range(39) if i not in ids];assert torch.equal(request[:,other],r['action'][:,other]);assert (request[:,ids].abs()<=1).all()
                np.testing.assert_allclose(goal.numpy(),codec.decode(r['action'][:,ids],*codec.bounds(pool)).numpy(),rtol=0,atol=0)
        raise ValueError('CPU original evaluation primary')
    results={}
    for mode in probe.MODES:
        policy.load_state_dict(original,strict=True);observed=dict(seal={},paths=set(),conversion_calls=0,sampling=dict(calls=0,requested_deterministic_true=0,actual_deterministic_true=0,actor_RNG_advances=0))
        with patch.object(codec,'execution_scope',fakegoal),patch.object(extra,'evaluate',loop):
            try:
                with probe.adapter(mode,sigma,observed):
                    with probe.parent.base.effort_scope(set(),{}) as current:
                        current.DecisionPPOTrainer();current._evaluate(fakepool,policy,fakepool.spec,SimpleNamespace(control='policy',episodes=128,checkpoint=str(probe.CHECKPOINT)),Path('/tmp/no-native-output'))
            except ValueError as error:assert str(error)=='CPU original evaluation primary'
            else:raise AssertionError('Original primary error lost')
        assert probe.parent.base.effort_scope is priorcap and (runner._evaluate,runner.DecisionPPOTrainer,codec.convert)==old and observed['sampling_aliases_restored']
        s=observed['sampling'];assert s['calls']==observed['conversion_calls']==2 and s['requested_deterministic_true']==2
        assert s['actual_deterministic_true']==(2 if mode=='deterministic' else 0) and s['actor_RNG_advances']==(2 if mode=='stochastic' else 0)
        assert observed['strict_load_reached_before_override'] and observed['policy_before']['model_sha256']==observed['policy_after']['model_sha256'];results[mode]=s
    assert all(torch.equal(observation[k],frozen[k]) for k in FIELDS)
    bad=copy.deepcopy(contract);bad['action']['policy_output_adapter']={}
    try:codec.policy_type(probe.source)(contract=bad,size='large',fresh=False)
    except ValueError:pass
    else:raise AssertionError('Wrong original layered identity admitted')
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp)
        for name in ('existing','symlink'):
            out=root/name
            if name=='existing':out.mkdir()
            else:out.symlink_to(root/'missing')
            with patch.object(probe,'output',return_value=out),patch.object(probe,'gate',side_effect=AssertionError('late gate')) as gate:
                try:probe.launch('deterministic')
                except FileExistsError:pass
                else:raise AssertionError('Existing output admitted')
                gate.assert_not_called()
    static=probe.recovery.module('exploration_global_names',probe.recovery.HERE/'audit.py');unresolved={p.name:static.unresolved(p) for p in probe.HERE.glob('*.py')};assert not any(unresolved.values())
    assert payload['metadata']==metadata and probe.grid.sha(probe.CHECKPOINT)==probe.recovery.MODEL_SHA and 'isaacgym' not in sys.modules and not torch.cuda.is_initialized()
    return dict(CPU_only=True,GPU_executed=False,model_writes=0,original_identity_exact=True,original_CPU_CUDA_topology_rejected=True,CPU_full_CUDA_load_claimed=False,std_override=override,sampling=results,
        original_full_load_runtime_seam='runner.run original trainer.load(checkpoint) precedes own evaluator hook; original metadata and architecture unchanged',
        logp_latent_action_consistent=True,goal_physical_conversion_once=True,other35_actions_exact=True,original_primary_and_aliases_preserved=True,observation_unchanged=True,existing_symlink_output_rejected_before_gate=True,symtable_referenced_globals=unresolved,
        scope='CPU original model state/identity and sampling/codec fixtures only; native128/fullCUDA strict load/physics and first-attempt outcomes unverified')
