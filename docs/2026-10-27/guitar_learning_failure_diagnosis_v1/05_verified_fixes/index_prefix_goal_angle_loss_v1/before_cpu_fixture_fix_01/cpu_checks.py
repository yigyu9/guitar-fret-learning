"""Narrow CPU loss, frozen-state, strict-boundary and real report-path checks."""
import copy
from contextlib import redirect_stderr
import io
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    fit=probe.support();codec=probe.source.support();data,buckets,raw_labels,desired,bounds,contract,evidence=fit.dataset(probe)
    assert desired.shape==raw_labels.shape==(1416,4) and len(buckets)==6 and torch.isfinite(desired).all()
    checker=probe.module('angle_loss_unresolved_globals',probe.source.HERE/'recovery_v1/audit.py')
    unresolved={n:checker.unresolved(probe.HERE/n) for n in ('probe.py','fit.py','cpu_checks.py')};assert not any(unresolved.values()),unresolved
    raw=torch.tensor([[-.2,.3,-.4,.1],[.4,-.3,.2,-.1]],dtype=torch.float64,requires_grad=True);target=desired[:2].to(torch.float64)
    value=fit.loss(codec,raw,target,bounds);decoded=codec.decode(raw,*bounds)
    independent=np.mean((decoded.detach().numpy()-target.numpy())**2);assert abs(float(value)-independent)<1e-15
    value.backward();span=torch.where(raw>=0,bounds[2]-bounds[0],bounds[0]-bounds[1]);expected=2*(decoded.detach()-target)*span/raw.numel()
    assert torch.allclose(raw.grad,expected,rtol=0,atol=1e-14)
    finite=[]
    for j in range(4):
        plus=raw.detach().clone();minus=plus.clone();plus[0,j]+=1e-6;minus[0,j]-=1e-6
        finite.append(float((fit.loss(codec,plus,target,bounds)-fit.loss(codec,minus,target,bounds))/(2e-6)))
    np.testing.assert_allclose(finite,raw.grad[0].numpy(),rtol=0,atol=2e-10)
    assert fit.loss(codec,raw_labels,desired,bounds)==0  # Original typed goal labels reproduce original desired exactly.
    first=np.random.RandomState(7);second=np.random.RandomState(7)
    for _ in range(1000):
        a=np.concatenate([first.choice(b,32,replace=True) for b in buckets]);b=np.concatenate([second.choice(b,32,replace=True) for b in buckets]);assert np.array_equal(a,b)
        assert np.bincount(data['phase'][a],minlength=6).tolist()==[32]*6 and (data['env_id'][a]<3).all()
    config=probe.parent.settings();GoalPolicy=codec.policy_type(probe.source);torch.manual_seed(7);policy=GoalPolicy(contract=contract,size='large',fresh=True)
    original=torch.load(probe.parent.checkpoint(0),map_location='cpu',weights_only=False);initial={n:v.detach().clone() for n,v in policy.state_dict().items()}
    assert len(initial)==73 and all(torch.equal(v,original['model'][n]) for n,v in initial.items())
    impl=probe.source.source.source.support();chosen=impl.trainable(policy);flags={n:p.requires_grad for n,p in policy.named_parameters()}
    for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
    inputs={k:torch.as_tensor(data[k][:2]) for k in runner.FIELDS};opt=torch.optim.Adam(list(chosen.values()),lr=3e-4);rng=torch.get_rng_state().clone()
    pred=policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh();value=fit.loss(codec,pred,desired[:2],bounds);opt.zero_grad();value.backward();torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);opt.step()
    assert torch.equal(rng,torch.get_rng_state());invariant=impl.invariants(initial,policy);assert invariant['frozen_state_tensors']==54 and len(invariant['changed_names'])==19 and invariant['frozen_state_exact'] and invariant['cost2zero']
    for n,p in policy.named_parameters():p.requires_grad_(flags[n])
    trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))
    metadata=dict(schema=probe.SCHEMA,actual_initialization=probe.descriptor(),settings=config,policy_output_adapter=codec.ADAPTER,
        settings_scope='source environment configuration; new decoded-angle supervised loss declared separately',CPU_fixture=True)
    probe.check_metadata(metadata)
    for key,badvalue in [('schema',probe.source.SCHEMA),('actual_initialization',probe.source.descriptor()),('settings_scope','old raw-loss run')]:
        bad=copy.deepcopy(metadata);bad[key]=badvalue
        try:probe.check_metadata(bad)
        except AssertionError:pass
        else:raise AssertionError('Wrong initialization provenance accepted')
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);path=root/'fixture.pt';trainer.save(path,metadata=metadata);restored=GoalPolicy(contract=contract,size='large',fresh=False);loaded=DecisionPPOTrainer(restored,PPOConfig(**config['ppo']));probe.check_metadata(loaded.load(path))
        assert loaded.updates==0 and not loaded.actor_optimizer.state and not loaded.value_optimizer.state and all(torch.equal(v,restored.state_dict()[n]) for n,v in policy.state_dict().items())
        try:loaded.load(probe.parent.checkpoint(0))
        except ValueError as error:assert 'architecture/input/control/config' in str(error)
        else:raise AssertionError('Old incremental identity accepted')
        own=root/'own';own.mkdir();trainer.save(own/'initial.pt',metadata=metadata)
        with patch.object(probe,'output',return_value=own),probe.evaluation_scope({},set()):
            strict=runner.DecisionPPOTrainer(GoalPolicy(contract=contract,size='large',fresh=False),PPOConfig(**config['ppo']))
            probe.check_metadata(strict.load(own/'initial.pt'))
            try:strict.load(path)
            except AssertionError:pass
            else:raise AssertionError('Wrong checkpoint path accepted')
            bad=copy.deepcopy(metadata);bad['schema']='diagnostic.index_prefix_goal_initialization.v1';trainer.save(own/'initial.pt',metadata=bad)
            try:strict.load(own/'initial.pt')
            except AssertionError:pass
            else:raise AssertionError('Original raw-loss metadata accepted by wrapped full loader')
        # Run the actual post-fit audit writer with a scene-free fixture, not a real fitted checkpoint.
        out=root/'report_fixture';out.mkdir();identity=(out.stat().st_dev,out.stat().st_ino);(out/'initial.pt').write_bytes(b'CPU report path fixture')
        with patch.object(runner,'project_source_paths',return_value=set()):fit.finish(probe,out,identity,{},True,None,dict(CPU_fixture=True))
        report=probe.grid.read(out/'angle_loss_fit_report.json');assert report['completed'] and report['failure'] is None and report['checkpoint_sha256']==probe.grid.sha(out/'initial.pt') and probe.grid.read(out/'inputs_after.json')['verified']
        # Partial fit + secondary report I/O preserves the original exception and partial output.
        partial=root/'partial';stderr=io.StringIO();write=runner.write
        def broken(path,value):
            if Path(path).name=='inputs_after.json':raise OSError('CPU secondary audit')
            return write(path,value)
        with patch.object(probe,'output',return_value=partial),patch.object(runner,'_pins',return_value={}),patch.object(fit,'dataset',side_effect=ValueError('CPU primary fit')),patch.object(runner,'write',side_effect=broken),redirect_stderr(stderr):
            try:fit.fit(probe,set())
            except ValueError as error:assert str(error)=='CPU primary fit'
            else:raise AssertionError('Primary fit error lost')
        assert partial.is_dir() and 'CPU secondary audit' in stderr.getvalue()
        for kind in ('existing','symlink'):
            out=root/kind
            if kind=='existing':out.mkdir();(out/'sentinel').write_text('unchanged')
            else:out.symlink_to(root/'absent')
            with patch.object(probe,'output',return_value=out),patch.object(probe,'gate',side_effect=AssertionError('late gate')) as g:
                try:probe.launch('fit')
                except FileExistsError:pass
                else:raise AssertionError('Existing/symlink output admitted')
                g.assert_not_called()
            if kind=='existing':assert (out/'sentinel').read_text()=='unchanged'
    aliases=lambda:(probe.source.gate,probe.source.output,probe.source.SCHEMA,runner.DecisionPPOTrainer)
    before=aliases()
    try:
        with probe.evaluation_scope({},set()):
            assert probe.source.SCHEMA==probe.SCHEMA
            raise ValueError('CPU scope primary')
    except ValueError as error:assert str(error)=='CPU scope primary'
    assert before==aliases()
    return dict(CPU_only=True,GPU_executed=False,source_labels=evidence,planned_desired_direct_exact=True,rad2_loss_numpy_exact=True,loss_gradient_finite_difference=True,
        source_fresh73_exact=True,only_declared_modules_changed=invariant['frozen_state_exact'],cost2zero=True,critic_std_other_state_exact=True,CPU_one_step_extra_RNG0=True,
        original_1000_sampler_and_env_split_exact=True,original_GoalPolicy_same_strict_load=True,old_incremental_identity_rejected=True,old_raw_loss_metadata_rejected=True,wrong_checkpoint_path_rejected=True,PPO_empty0=True,frozen_state_tensors=54,allowed_changed_tensors=19,
        real_finish_report_and_hash_path_pass=True,primary_secondary_fit_error_preserved=True,existing_output_and_symlink_rejected_before_gate=True,evaluation_aliases_restore_on_error=True,
        unresolved_globals=unresolved,scope='CPU one-step/math/metadata/report fixtures only; no native/reference recapture/1000-step fit executed')
