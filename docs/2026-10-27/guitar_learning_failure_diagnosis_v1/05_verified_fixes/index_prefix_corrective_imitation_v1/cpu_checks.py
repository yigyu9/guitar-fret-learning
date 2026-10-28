"""Typed-label/budget/condition checks using one synthetic CPU step, no native."""
from contextlib import redirect_stderr
import copy
import io
from pathlib import Path
import shutil
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
    fit=probe.support();ref,nn=fit.datasets(probe);labels=dict(np.load(probe.HERE/'cpu_inputs/labels.npz',allow_pickle=False))
    np.testing.assert_array_equal(labels['native_reference_request4'],ref['requested_reference_action'])
    np.testing.assert_array_equal(fit.requested_reference(probe,ref),labels['native_reference_request4'])
    np.testing.assert_array_equal(fit.requested_reference(probe,nn),labels['shadow_reference_request4'])
    np.testing.assert_array_equal(labels['NN_actual_requested4'],nn['requested_NN_action']);np.testing.assert_array_equal(labels['NN_actual_executed4'],nn['executed_action'])
    assert abs(labels['shadow_reference_request4']-labels['NN_actual_requested4']).max()>1
    r0=np.random.RandomState(7);r1=np.random.RandomState(7)
    for _ in range(1000):
        a=fit.batches('reference_only',r0,ref,nn);b=fit.batches('corrective_mixed',r1,ref,nn)
        assert len(a)==len(b)==192 and (a<len(ref['env_id'])).all()
        np.testing.assert_array_equal(a,b%len(ref['env_id']))
        for c,ids in [('reference_only',a),('corrective_mixed',b)]:
            env=np.concatenate([ref['env_id'],nn['env_id']])[ids];phase=np.concatenate([ref['phase'],nn['phase']])[ids]
            assert (env<3).all() and np.bincount(phase,minlength=6).tolist()==[32]*6
            assert int((ids>=len(ref['env_id'])).sum())==(96 if c=='corrective_mixed' else 0)
    assert np.array_equal(r0.get_state()[1],r1.get_state()[1]) and r0.get_state()[2:]==r1.get_state()[2:]
    config=probe.source.parent.settings();extra=probe.source.parent.support();impl=probe.source.support()
    start=torch.load(probe.START,map_location='cpu',weights_only=False);assert probe.grid.sha(probe.START)==probe.START_SHA
    assert start['updates']==0 and not start['actor_optimizer']['state'] and not start['value_optimizer']['state']
    assert start['metadata']['schema']==probe.base.SCHEMA and start['metadata']['actual_initialization']==probe.base.descriptor()
    policy=extra.PrefixPolicy(contract=start['identity']['architecture']['contract'],size='large',fresh=False);policy.load_state_dict(start['model'],strict=True)
    trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));assert trainer._identity()==start['identity']
    initial={n:v.detach().clone() for n,v in policy.state_dict().items()};flags={n:p.requires_grad for n,p in policy.named_parameters()};chosen=impl.trainable(policy)
    for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
    ids=fit.batches('corrective_mixed',np.random.RandomState(7),ref,nn)
    x={k:torch.as_tensor(np.concatenate([ref[k],nn[k]])[ids]) for k in runner.FIELDS}
    y=torch.as_tensor(np.concatenate([labels['native_reference_request4'],labels['shadow_reference_request4']])[ids])
    pred=policy(*(x[k] for k in runner.FIELDS))['mean'][:,17:21].tanh();assert pred.shape==y.shape==(192,4)
    opt=torch.optim.Adam(list(chosen.values()),lr=3e-4);loss=(pred-y).square().mean();loss.backward();torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);opt.step()
    invariant=impl.invariants(initial,policy);assert invariant['frozen_state_exact'] and invariant['changed_names']
    for n,p in policy.named_parameters():p.requires_grad_(flags[n])
    trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));assert not trainer.actor_optimizer.state and not trainer.value_optimizer.state and trainer.updates==0
    original=(probe.source.gate,probe.source.output,probe.source.SCHEMA,probe.source.descriptor,runner.DecisionPPOTrainer)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);(root/'cpu_inputs').mkdir()
        for name in ('labels.npz','label_manifest.json'):shutil.copy2(probe.HERE/'cpu_inputs'/name,root/'cpu_inputs'/name)
        with patch.object(probe,'HERE',root):
            for condition in probe.CONDITIONS:
                path=probe.output(condition,'fit')/'initial.pt'
                meta=dict(schema=probe.SCHEMA,settings=config,actual_initialization=probe.descriptor(condition),starting_checkpoint_sha256=probe.START_SHA,
                    settings_scope='Unchanged source configuration; actual_initialization declares additional supervised continuation')
                trainer.save(path,metadata=meta)
                report=dict(completed=True,condition=condition,procedure=probe.descriptor(condition),checkpoint_path=str(path),checkpoint_sha256=probe.grid.sha(path),checks=dict(CPU=True))
                probe.fitted(condition,report,path);probe.check_metadata(meta,condition)
                other=next(c for c in probe.CONDITIONS if c!=condition)
                for badmeta in [dict(meta,actual_initialization=probe.descriptor(other)),dict(meta,starting_checkpoint_sha256='wrong'),dict(meta,schema=probe.base.SCHEMA)]:
                    try:probe.check_metadata(badmeta,condition)
                    except AssertionError:pass
                    else:raise AssertionError('Wrong condition/source metadata admitted')
                for badreport in [dict(report,condition=other),dict(report,checkpoint_path=str(probe.START)),dict(report,checkpoint_sha256='wrong')]:
                    try:probe.fitted(condition,badreport,path)
                    except AssertionError:pass
                    else:raise AssertionError('Wrong condition/path/checkpoint admitted')
                try:
                    with probe.evaluation_scope(condition,{},set()):
                        checked=runner.DecisionPPOTrainer(policy,PPOConfig(**config['ppo']));checked.load(path)
                        try:checked.load(probe.START)
                        except AssertionError:pass
                        else:raise AssertionError('Original warmstart path admitted as condition checkpoint')
                        assert probe.source.SCHEMA==probe.SCHEMA and probe.source.output('fit')==path.parent
                        raise RuntimeError('CPU primary scope failure')
                except RuntimeError as error:assert str(error)=='CPU primary scope failure'
                assert original==(probe.source.gate,probe.source.output,probe.source.SCHEMA,probe.source.descriptor,runner.DecisionPPOTrainer)
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);stderr=io.StringIO()
        def write(path,value):
            if Path(path).name=='inputs_after.json':raise OSError('secondary audit write')
        with patch.object(probe,'HERE',root),patch.object(runner,'_pins',return_value={}),patch.object(runner,'write',side_effect=write),\
                patch.object(fit,'datasets',side_effect=ValueError('primary data error')),redirect_stderr(stderr):
            try:fit.fit(probe,'reference_only',set())
            except ValueError as error:assert str(error)=='primary data error'
            else:raise AssertionError('Primary fit error lost')
        assert 'secondary audit write' in stderr.getvalue()
        (root/'runs/reference_only_fit/keep').write_text('unchanged')
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('must not gate')) as gate:
            try:probe.launch('reference_only','fit')
            except FileExistsError:pass
            else:raise AssertionError('Existing output admitted')
            gate.assert_not_called()
        assert (root/'runs/reference_only_fit/keep').read_text()=='unchanged'
    return dict(CPU_only=True,GPU_executed=False,original_reference_labels_bitexact=True,typed_shadow_and_NN_actual_separate=True,
        starting_checkpoint73_exact_model_only=True,original_identity_same=True,actual_native_full_strict_load_pending=True,
        additional1000x192_two16_draws_same_RNG_consumption=True,train_env012_only_heldout3=True,loss_exactly4_columns=True,
        frozen_critic_std_other_state_exact=invariant['frozen_state_exact'],cost2zero=True,PPO_save_load_empty0=True,
        wrong_condition_metadata_path_checkpoint_rejected=True,evaluation_aliases_finally_restored=True,primary_plus_secondary_fit_error_preserved=True,
        preexisting_output_rejected_before_gate=True,new_capture=False,new_training_executed=False,
        limits='CPU1step/model-only and temporary CPU strict save/load; actual CUDA RNG/fullnative fitting/evaluation remain unverified')
