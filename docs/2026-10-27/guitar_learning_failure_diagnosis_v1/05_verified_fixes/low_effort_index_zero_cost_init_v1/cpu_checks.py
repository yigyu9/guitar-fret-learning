"""Bounded CPU proof of B-only initialization; original index128 fixtures reused."""
import copy
from contextlib import contextmanager
import hashlib
from pathlib import Path
import pickle
import random
import sys
import tempfile
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer,compute_decision_gae
    from guitar_learning.training.ppo import PPOConfig
    assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    torch.set_num_threads(1)
    original=probe.module('zero_cost_reused_index_checks',probe.BASE/'cpu_checks.py')
    declaration,base_checks=original.check(probe.base)
    config=runner.make_settings(probe.base.train_args(probe.HERE/'train'))
    assert config==probe.grid.read(probe.BASE/'cpu_inputs/settings.json')
    assert config['ppo']['gamma']==config['song']['surface_approach_gamma']==.99
    contract=probe.grid.read(probe.BASE/'train/training_contract.json')
    assert contract['native_backend']['diagnostic_native_effort']==declaration
    tagged=copy.deepcopy(contract);probe.tag(tagged)
    reverted=copy.deepcopy(tagged);reverted['task']['short_learning'].pop('ablation');assert reverted==contract
    def seed():random.seed(7);np.random.seed(7);torch.manual_seed(7)
    def rng():return hashlib.sha256(pickle.dumps((random.getstate(),np.random.get_state()))+torch.get_rng_state().numpy().tobytes()).hexdigest()
    seed();normal=runtime.ShortPolicy(contract=contract,size='large');normal_rng=rng()
    seed();zero=probe.variants.policy_type(probe.VARIANT,fresh=True)(contract=tagged,size='large');zero_rng=rng()
    initialization=probe.initial_comparison(zero.state_dict(),normal.state_dict());assert normal_rng==zero_rng
    baseline=probe.BASE/'train/initial.pt';saved=torch.load(baseline,map_location='cpu',weights_only=False)
    assert set(saved['model'])==set(normal.state_dict()) and all(torch.equal(v,saved['model'][k]) for k,v in normal.state_dict().items())
    assert probe.initial_comparison(zero.state_dict(),saved['model'])==initialization
    seed();evaluation=probe.variants.policy_type(probe.VARIANT,fresh=False)(contract=tagged,size='large')
    assert all(torch.equal(v,evaluation.state_dict()[k]) for k,v in normal.state_dict().items())
    observation=(torch.randn(8,561)*.01,torch.randn(8,2,24)*.01,torch.ones(8,2,dtype=torch.bool),torch.randn(8,8,24)*.01,torch.ones(8,8,dtype=torch.bool))
    state=torch.get_rng_state().clone();a=normal.act(*observation);after_a=torch.get_rng_state().clone()
    torch.set_rng_state(state);b=zero.act(*observation);assert torch.equal(after_a,torch.get_rng_state())
    for key in ('mean','log_std','reward_value','latent','action','logp'):assert torch.equal(a[key],b[key]),key
    assert not b['cost_value'].any()
    normal_trainer=DecisionPPOTrainer(normal,PPOConfig(**config['ppo']))
    trainer=DecisionPPOTrainer(zero,PPOConfig(**config['ppo']))
    assert normal_trainer.actor_optimizer.state_dict()==trainer.actor_optimizer.state_dict()
    assert normal_trainer.value_optimizer.state_dict()==trainer.value_optimizer.state_dict()
    assert [k for k,v in normal.named_parameters() if v.requires_grad]==[k for k,v in zero.named_parameters() if v.requires_grad]
    encoder={k:v.clone() for k,v in zero.value_encoder.state_dict().items()}
    initial=zero(*observation);trainer.value_optimizer.zero_grad()
    ((initial['reward_value']-1).square().mean()+initial['cost_value'].square().mean()).backward();trainer.value_optimizer.step()
    assert any(not torch.equal(v,encoder[k]) for k,v in zero.value_encoder.state_dict().items())
    values=zero(*observation)['cost_value'].detach().reshape(4,2);assert not values.any()
    flags=torch.zeros(4,2,dtype=torch.bool);flags[-1]=True
    gae=compute_decision_gae(torch.zeros_like(values),values,values,flags,torch.zeros_like(flags),torch.ones(4,2,dtype=torch.long),torch.ones(4,2,dtype=torch.bool),1.,.98)[0]
    assert not gae.any()
    trainer.value_optimizer.zero_grad();loss=(zero(*observation)['cost_value']-1).square().mean();loss.backward()
    gradient=float(zero.cost_critic.weight.grad.norm());assert gradient>0 and float(zero.cost_critic.bias.grad.abs())>0
    trainer.value_optimizer.step()
    assert float((zero(*observation)['cost_value']-1).square().mean())<float(loss.detach()) and zero.cost_critic.weight.any()
    with tempfile.TemporaryDirectory() as temp:
        plain_path,zero_path=[Path(temp)/x for x in ('plain.pt','B.pt')]
        normal_trainer.save(plain_path);trainer.save(zero_path)
        target=DecisionPPOTrainer(evaluation,PPOConfig(**config['ppo']));target.load(zero_path)
        assert torch.equal(evaluation.cost_critic.weight,zero.cost_critic.weight) and evaluation.cost_critic.weight.any()
        for loader,path in ((normal_trainer,zero_path),(target,plain_path)):
            try:loader.load(path)
            except ValueError as error:assert 'mismatch' in str(error)
            else:raise AssertionError('Cross-initialization strict load accepted')
    aliases=(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy)
    outer=(probe.base.HERE,probe.base.gate,probe.base.effort_scope)
    try:
        with probe.execution_scope('train',{},set(),{}):
            assert probe.base.HERE==probe.HERE and probe.base.gate('train')==({},set())
            raise RuntimeError('CPU outer scope failure')
    except RuntimeError as error:assert str(error)=='CPU outer scope failure'
    assert (probe.base.HERE,probe.base.gate,probe.base.effort_scope)==outer
    @contextmanager
    def fake_scope(paths,state):
        old=(runner.ShortPool,runtime.ShortPool)
        class Pool:
            def __init__(self,config,out):self.contract=copy.deepcopy(contract);self.closed=False
            def close(self):self.closed=True
        runner.ShortPool=runtime.ShortPool=Pool
        try:yield runner
        finally:runner.ShortPool,runtime.ShortPool=old
    with tempfile.TemporaryDirectory() as temp:
        for failed in (False,True):
            state={};out=Path(temp)/str(failed);out.mkdir()
            try:
                with probe.initialization_scope(fake_scope,fresh=True)(set(),state) as r:
                    pool=r.ShortPool(config,out)
                    assert pool.contract==tagged and r.ShortPolicy is runtime.ShortPolicy
                    if failed:raise RuntimeError('CPU initializer body error')
            except RuntimeError as error:assert failed and str(error)=='CPU initializer body error'
            assert state['initialization_contract_tagged'] and state['initialization_aliases_restored']
            assert (runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy)==aliases
        old=Path(temp)/'runs';out=old/'train';out.mkdir(parents=True);sentinel=out/'sentinel';sentinel.write_bytes(b'keep')
        with patch.object(probe,'HERE',old),patch.object(probe,'gate',side_effect=AssertionError('gate must not run')):
            try:probe.launch('train',0)
            except FileExistsError:pass
            else:raise AssertionError('Existing output admitted')
            assert sentinel.read_bytes()==b'keep' and not list(out.glob('*.json'))
            sentinel.unlink();out.rmdir();out.symlink_to(old/'absent')
            try:probe.launch('train',0)
            except (FileExistsError,ValueError):pass
            else:raise AssertionError('Dangling output admitted')
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    initialization.update(RNG_and_actor_reward_exact=True,additional_initialization_RNG_draws=0,initial_std_exact=True,
        optimizer_config_and_grouping_exact=True,baseline_actual_initial73_exact=True,baseline_initial=str(baseline),baseline_initial_sha256=probe.grid.sha(baseline),
        zero_cost_after_encoder_update=True,zero_cost_GAE_zero=True,positive_cost_head_gradient_norm=gradient,
        positive_cost_head_trainable=True,evaluation_freshFalse_nonzero_preserved=True,cross_baseline_B_strict_load_rejected=True)
    return declaration,dict(CPU_only=True,GPU_executed=False,CUDA_initialized=False,initialization=initialization,
        original_index128_CPU_regressions=base_checks,settings_exact=True,contract_only_B_tag=True,
        original_precheck384_reused_not_rerun=True,initialization_aliases_restored_after_body_error=True,outer_HERE_gate_scope_restored_after_error=True,
        existing_output_unchanged_and_symlink_rejected_before_gate=True,native128_actual_unverified=True,
        limitations=['CPU RNG/action proof is not CUDA draw equality','No new training/native/evaluation performance certified'])
