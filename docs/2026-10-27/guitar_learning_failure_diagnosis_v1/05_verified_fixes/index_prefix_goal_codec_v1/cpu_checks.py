"""CPU affine/label/identity and narrow scope/lifecycle regressions; no native."""
import copy
from contextlib import contextmanager,redirect_stderr
import io
from pathlib import Path
from types import SimpleNamespace
import tempfile
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in __import__('sys').modules
    c=probe.support();data,buckets,labels,contract,label_evidence=c.dataset(probe)
    assert label_evidence['source_requested_reference_bitexact'] and len(data['clock'])==1416 and len(buckets)==6
    assert labels.dtype==torch.float32 and labels.shape==(1416,4) and labels.abs().max()<=1
    config=probe.parent.settings();short=config['song']['short_learning'];target=contract['action']['target_contract'];names=target['joint_names']
    active=torch.tensor([names.index(n) for n in target['action_order']]);ids=short['learned_action_indices'];ref=torch.tensor(target['reference105_rad']);low=torch.tensor(target['action_lower_rad']);high=torch.tensor(target['action_upper_rad']);r=ref[active][ids]
    extremes=torch.stack((low[ids],r,high[ids],r+.37*(high[ids]-r),r+.37*(low[ids]-r)))
    encoded=c.encode(extremes,r,low[ids],high[ids]);decoded=c.decode(encoded,r,low[ids],high[ids]);residual=float((decoded-extremes).abs().max())
    assert torch.equal(encoded[:3],torch.stack((-torch.ones(4),torch.zeros(4),torch.ones(4)))) and residual<=4*torch.finfo(torch.float32).eps
    for bad in (torch.full((1,4),1.01),torch.full((1,4),float('nan'))):
        try:c.decode(bad,r,low[ids],high[ids])
        except ValueError:pass
        else:raise AssertionError('Invalid normalized goal accepted')
    controller=SimpleNamespace(reference=ref,active=active,action_low=low,action_high=high,target=ref.expand(4,-1).clone())
    incremental=torch.zeros(39,dtype=torch.bool);incremental[17:33]=True
    pool=SimpleNamespace(controller=controller,spec=short,teacher_reference=ref[active],incremental_mask=incremental)
    raw=torch.linspace(-1,1,156).reshape(4,39);prior=raw.clone();old=controller.target.clone();request,goal=c.convert(pool,raw)
    other=[i for i in range(39) if i not in ids]
    assert torch.equal(raw,prior) and torch.equal(controller.target,old) and torch.equal(request[:,other],raw[:,other]) and request[:,ids].abs().max()<=1
    expected=runtime.trajectory_actions(torch.cat((ref[active].expand(4,-1)[:,:17],goal,ref[active].expand(4,-1)[:,21:]),-1),old[:,active],ref[active],low,high,incremental,max_speed=4.)
    assert torch.equal(request[:,ids],expected[:,ids])
    controller.target[1,active[ids]]=high[ids];request_reset,_=c.convert(pool,raw)
    assert torch.equal(request_reset[[0,2,3]],request[[0,2,3]]) and (request_reset[1,ids]<=0).all()
    newtarget=(controller.target[:,active[ids]]+request_reset[:,ids]*(4/60)).clamp(low[ids],high[ids])
    assert bool(((newtarget-controller.target[:,active[ids]]).abs()<=4/60+1e-7).all())
    torch.manual_seed(7);GoalPolicy=c.policy_type(probe);policy=GoalPolicy(contract=contract,size='large',fresh=True)
    original=torch.load(probe.parent.checkpoint(0),map_location='cpu',weights_only=False);initial={n:v.detach().clone() for n,v in policy.state_dict().items()}
    assert len(initial)==73 and all(torch.equal(v,original['model'][n]) for n,v in initial.items()) and policy.architecture!=original['identity']['architecture']
    impl=probe.source.source.support();chosen=impl.trainable(policy);flags={n:p.requires_grad for n,p in policy.named_parameters()}
    for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
    inputs={k:torch.as_tensor(data[k][:2]) for k in runner.FIELDS};opt=torch.optim.Adam(list(chosen.values()),lr=3e-4)
    loss=(policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh()-labels[:2]).square().mean();opt.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);opt.step()
    invariant=impl.invariants(initial,policy);assert invariant['changed_names']
    for n,p in policy.named_parameters():p.requires_grad_(flags[n])
    trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);path=root/'goal.pt';metadata=dict(schema=probe.SCHEMA,policy_output_adapter=c.ADAPTER,PPO_updates=0)
        trainer.save(path,metadata=metadata);other_policy=GoalPolicy(contract=contract,size='large',fresh=False);same=DecisionPPOTrainer(other_policy,PPOConfig(**config['ppo']));same.load(path)
        assert same.updates==0 and not same.actor_optimizer.state and not same.value_optimizer.state and all(torch.equal(v,other_policy.state_dict()[n]) for n,v in policy.state_dict().items())
        try:same.load(probe.parent.checkpoint(0))
        except ValueError as error:assert 'architecture/input/control/config' in str(error)
        else:raise AssertionError('Old incremental checkpoint accepted')
        bad=copy.deepcopy(contract);bad['action']['policy_output_adapter']['schema']='wrong'
        try:GoalPolicy(contract=bad)
        except ValueError:pass
        else:raise AssertionError('Wrong output layer admitted')
        try:GoalPolicy(contract=probe.grid.read(probe.source.COLLECT/'training_contract.json'))
        except ValueError:pass
        else:raise AssertionError('Missing output layer admitted')
        with patch.object(runner,'SCHEMA',probe.SCHEMA):
            try:runner.run(SimpleNamespace(command='evaluate',checkpoint=str(probe.parent.checkpoint(0)),out=str(root/'absent')))
            except ValueError as error:assert 'Own sealed' in str(error)
            else:raise AssertionError('Old metadata admitted')
        assert not (root/'absent').exists()
        # Existing/symlink output rejected before evidence, Torch/native loading or model reading.
        for kind in ('directory','symlink'):
            out=root/kind
            if kind=='directory':out.mkdir()
            else:out.symlink_to(root/'missing')
            with patch.object(probe,'output',return_value=out),patch.object(probe,'gate',side_effect=AssertionError('late gate')) as g:
                try:probe.launch('reference')
                except FileExistsError:pass
                else:raise AssertionError('Existing output admitted')
                g.assert_not_called()
    aliases=lambda:(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,runner.SCHEMA,runner._evaluate,runner.DecisionPPOTrainer,probe.parent.base.effort_scope,probe.parent.base.output,probe.parent.base.checkpoint,probe.parent.support().reference_action)
    before=aliases();observed={}
    try:
        with c.execution_scope(probe,'evaluate',{},set(),observed):
            with probe.parent.base.effort_scope(set(),dict(out=Path('/tmp/goal_no_native'),cleanup_errors=[])) as current:
                assert current.SCHEMA==probe.SCHEMA
                try:probe.parent.support().reference_action(None,None)
                except RuntimeError:pass
                else:raise AssertionError('NN-only reference injection admitted')
                raise RuntimeError('CPU primary')
    except RuntimeError as error:assert str(error)=='CPU primary'
    assert before==aliases() and observed['aliases_restored'] and observed['goal_aliases_restored']
    # Test our exact wrapper against a minimal scene-free base, including virtual ctor reset and attach failure cleanup.
    closed=[]
    class FakePool:
        def __init__(self,*args):
            self.contract=probe.grid.read(probe.source.COLLECT/'training_contract.json');self.reset()
        def reset(self):self.constructor_reset_safe=True
        def close(self):closed.append(True);raise OSError('secondary close')
    @contextmanager
    def fake_parent(*args):
        old=(probe.parent.base.effort_scope,runner.ShortPool,runtime.ShortPool)
        @contextmanager
        def original(*args):
            runner.ShortPool=runtime.ShortPool=FakePool
            try:yield runner
            finally:runner.ShortPool,runtime.ShortPool=old[1:]
        probe.parent.base.effort_scope=original
        try:yield
        finally:probe.parent.base.effort_scope=old[0]
    for fail in (False,True):
        observed={}
        with patch.object(probe.parent,'execution_scope',fake_parent):
            with c.execution_scope(probe,'reference',{},set(),observed):
                with probe.parent.base.effort_scope(set(),{}) as current:
                    if fail:
                        with patch.object(c,'attach',side_effect=ValueError('primary attach')):
                            try:current.ShortPool({},Path('/tmp/no_scene'))
                            except ValueError as error:assert str(error)=='primary attach'
                            else:raise AssertionError('Attach error lost')
                    else:assert current.ShortPool({},Path('/tmp/no_scene')).constructor_reset_safe
        assert observed['goal_aliases_restored']
    assert closed and observed['cleanup_errors'][0]['message']=='secondary close'
    sample=np.concatenate([np.random.RandomState(7).choice(b,32,replace=True) for b in buckets]);assert np.bincount(data['phase'][sample],minlength=6).tolist()==[32]*6 and (data['env_id'][sample]<3).all()
    return dict(CPU_only=True,GPU_executed=False,labels=label_evidence,affine_extreme_middle_max_rad=residual,source_fresh73_exact=True,new_identity_old_strict_rejected=True,same_new_strict_load=True,
        only_trainable_goal_encoder_head_changed=invariant['frozen_state_exact'],PPO_empty0=True,cost2zero=True,unchanged_other_actions35_and_input=True,partial_reset_current_target_independent=True,
        original_rate_bounds_inverse_codec=True,NN_reference_forbidden=True,aliases_restore_on_error=True,virtual_ctor_reset_and_primary_plus_close_failure_preserved=True,
        original_phase_split_192_and_same_budget=True,scope='CPU scalar/math/model/source only; native128 new reference/fit/evaluation not executed')
