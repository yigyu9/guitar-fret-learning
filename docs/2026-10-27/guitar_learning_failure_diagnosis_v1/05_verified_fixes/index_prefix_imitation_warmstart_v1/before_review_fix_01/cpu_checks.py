"""Synthetic alignment/fit invariants and original strict checkpoint tests; no native."""
import copy
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


def check(probe):
    import numpy as np
    import torch
    from guitar_learning.tool.experiments.short_finger_learning import runner,runtime
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    torch.set_num_threads(1);assert not torch.cuda.is_available() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    extra=probe.parent.support();impl=probe.support();config=probe.parent.settings();short=config['song']['short_learning']
    b=[short['teacher']['ramp_s'],*extra.timing.boundaries(short['view'])]
    assert [probe.phase(x,short) for x in (0,*b,5.9)]==[0,1,2,3,4,5,5]
    clock=np.repeat(np.arange(4,1417,4),4);env=np.tile(np.arange(4),354)
    phases=np.array([probe.phase(int(c)/240.,short) for c in clock])
    data=dict(env_id=env,clock=clock,start_clock=clock-4,phase=phases,first_attempt=np.ones(len(clock),dtype=bool),
        prior_failure=np.zeros(len(clock),dtype=bool),post_failure=np.zeros(len(clock),dtype=bool),
        source_control=np.zeros(len(clock),dtype=np.int64),requested_reference_action=np.zeros((len(clock),4),dtype=np.float32),executed_action=np.zeros((len(clock),4),dtype=np.float32))
    for k in runner.FIELDS:data[k]=np.zeros((len(clock),1),dtype=np.float32)
    buckets=impl.validate_data(data,short,probe);assert all(len(v)>0 for v in buckets)
    ids=np.concatenate([np.random.RandomState(7).choice(v,32,replace=True) for v in buckets]);assert len(ids)==192
    assert np.bincount(phases[ids],minlength=6).tolist()==[32]*6 and (env[ids]<3).all()
    for key,value in [('phase',np.zeros_like(phases)),('post_failure',np.ones(len(clock),dtype=bool)),('clock',clock+1),
                      ('source_control',np.ones(len(clock),dtype=np.int64)),('requested_reference_action',np.ones((len(clock),4),dtype=np.float32)*1.1)]:
        bad=dict(data);bad[key]=value
        try:impl.validate_data(bad,short,probe)
        except AssertionError:pass
        else:raise AssertionError('Contaminated/misaligned collection accepted: '+key)
    # Precontrol copies survive mutation; requested action differs from guarded final target.
    fake_env=SimpleNamespace(clock=torch.zeros(4,dtype=torch.long),failure=torch.zeros(4,67,dtype=torch.bool),wrist_failure=torch.zeros(4,dtype=torch.bool),wrist_severe_failure=torch.zeros(4,dtype=torch.bool))
    pool=SimpleNamespace(environment=fake_env,spec=short,first=torch.tensor([True,False,True,False]),
        observation={k:torch.ones(4,2) for k in runner.FIELDS},controller=SimpleNamespace(target=torch.zeros(4,105),active=torch.arange(39)),
        scene=SimpleNamespace(target=torch.zeros(4,105)),pending=dict(raw_target_rad=torch.ones(4),final_target_rad=torch.zeros(4),current_goal=torch.full((4,),4)))
    action=torch.zeros(4,39);action[:,17:21]=.25;row=impl.before(pool,action,'collect')
    for v in pool.observation.values():v.zero_()
    fake_env.clock+=4;fake_env.failure[2,4]=True;pool.last_executed_action=action.clone()
    saved=impl.after(probe,pool,row)
    assert len(saved)==2 and [r['env_id'] for r in saved]==[0,2] and saved[1]['post_failure'] and not saved[1]['prior_failure']
    assert all((r['state']==1).all() and (r['requested_reference_action']==.25).all() and r['raw_DIP_target_rad']==1 and r['final_DIP_target_rad']==0 for r in saved)
    nnrow=impl.before(pool,action,'evaluate');assert 'requested_NN_action' in nnrow and 'requested_reference_action' not in nnrow and (nnrow['source_control']==1).all()
    poisoned=dict(data);poisoned['requested_NN_action']=data['requested_reference_action'].copy()
    try:impl.validate_data(poisoned,short,probe)
    except AssertionError:pass
    else:raise AssertionError('NN captured observations admitted as initial fit source')
    contract=probe.grid.read(probe.parent.HERE/'train/training_contract.json')
    torch.manual_seed(7);policy=extra.PrefixPolicy(contract=contract,size='large',fresh=True)
    old=torch.load(probe.parent.checkpoint(0),map_location='cpu',weights_only=False)
    initial={n:v.detach().clone() for n,v in policy.state_dict().items()}
    assert len(initial)==73 and set(initial)==set(old['model']) and all(torch.equal(v,old['model'][n]) for n,v in initial.items())
    flags={n:p.requires_grad for n,p in policy.named_parameters()};chosen=impl.trainable(policy)
    assert chosen and all(n.startswith(('finger_encoder.','finger_heads.index.')) for n in chosen)
    for n,p in policy.named_parameters():p.requires_grad_(n in chosen)
    inputs=dict(state=torch.zeros(2,561),events=torch.zeros(2,67,24),mask=torch.ones(2,67,dtype=torch.bool),
        priority_events=torch.zeros(2,8,24),priority_mask=torch.ones(2,8,dtype=torch.bool))
    opt=torch.optim.Adam(list(chosen.values()),lr=3e-4)
    pred=policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh();loss=(pred-.25).square().mean()
    loss.backward();norm=torch.nn.utils.clip_grad_norm_(list(chosen.values()),.5);assert torch.isfinite(norm);opt.step()
    unchanged=impl.invariants(initial,policy);assert unchanged['changed_names'] and unchanged['cost2zero']
    for n,p in policy.named_parameters():p.requires_grad_(flags[n])
    trainer=DecisionPPOTrainer(policy,PPOConfig(**config['ppo']))
    assert trainer.updates==0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);path=root/'new.pt';metadata=dict(schema=probe.SCHEMA,settings=config,actual_initialization=probe.descriptor(),
            source_settings_initialization=config['simple_start']['initialization'],settings_scope='Unchanged source configuration, not checkpoint initialization')
        trainer.save(path,metadata=metadata)
        loaded=extra.PrefixPolicy(contract=contract,size='large',fresh=False);other=DecisionPPOTrainer(loaded,PPOConfig(**config['ppo']));other.load(path)
        assert all(torch.equal(v,loaded.state_dict()[n]) for n,v in policy.state_dict().items())
        payload=torch.load(path,map_location='cpu',weights_only=False)
        assert payload['updates']==0 and not payload['actor_optimizer']['state'] and not payload['value_optimizer']['state'] and payload['metadata']==metadata
        assert payload['identity']==old['identity']  # Same architecture/environment, explicitly different procedure metadata.
        assert payload['metadata']['schema']!=old['metadata']['schema'] and not torch.equal(loaded.finger_heads['index'][-1].bias,initial['finger_heads.index.2.bias'])
        # Original runner rejects our procedure schema before policy/native creation.
        with patch.object(runner,'SCHEMA',extra.SCHEMA):
            try:runner.run(SimpleNamespace(command='evaluate',checkpoint=str(path),out=str(root/'should_not_exist')))
            except ValueError as error:assert 'Own sealed' in str(error)
            else:raise AssertionError('Original metadata runner accepted warmstart schema')
        assert not (root/'should_not_exist').exists()
        with patch.object(runner,'SCHEMA',probe.SCHEMA):
            try:runner.run(SimpleNamespace(command='evaluate',checkpoint=str(probe.parent.checkpoint(0)),out=str(root/'old_not_allowed')))
            except ValueError as error:assert 'Own sealed' in str(error)
            else:raise AssertionError('Warmstart runner accepted original metadata schema')
        assert not (root/'old_not_allowed').exists()
    # Scoped original cap/evaluator aliases restore on error without creating a scene.
    aliases=(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,runner.SCHEMA,runner.make_settings,
        runner.compact_episode,runner._evaluate,probe.parent.base.output,probe.parent.base.checkpoint,probe.parent.base.effort_scope)
    observed={}
    try:
        with probe.execution_scope('evaluate',{},set(),observed):
            with probe.parent.base.effort_scope(set(),dict(out=Path('/tmp/no_native_imitation'),cleanup_errors=[])) as current:
                assert current.SCHEMA==probe.SCHEMA
                try:extra.reference_action(None,None)
                except RuntimeError:pass
                else:raise AssertionError('NN reference injection admitted')
                raise RuntimeError('CPU primary failure')
    except RuntimeError as error:assert str(error)=='CPU primary failure'
    assert aliases==(runner.ShortPool,runtime.ShortPool,runner.ShortPolicy,runtime.ShortPolicy,runner.SCHEMA,runner.make_settings,
        runner.compact_episode,runner._evaluate,probe.parent.base.output,probe.parent.base.checkpoint,probe.parent.base.effort_scope)
    assert observed['aliases_restored'] and observed['observer_aliases_restored']
    # Existing output and symlink are rejected before gate/native/model import.
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);(root/'runs').mkdir();(root/'runs/collect').mkdir();(root/'runs/collect/keep').write_text('unchanged')
        (root/'runs/fit').symlink_to(root/'runs/collect',target_is_directory=True)
        with patch.object(probe,'HERE',root),patch.object(probe,'gate',side_effect=AssertionError('gate must not run')) as gate:
            for stage in ('collect','fit'):
                try:probe.launch(stage)
                except FileExistsError:pass
                else:raise AssertionError('Existing output admitted')
            gate.assert_not_called()
        assert (root/'runs/collect/keep').read_text()=='unchanged'
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True,GPU_executed=False,six_phase_counts_per_env=[np.bincount(phases[env==i],minlength=6).tolist() for i in range(4)],
        balanced192_no_heldout=True,clock4_and_firstmask_failure_endpoint_labels=True,requested_not_guarded_target_label=True,precontrol_clone_exact=True,
        NN_same_env4_observations_captured_separately_not_fit_source=True,
        fresh73_original_exact=True,supervised_only_encoder_indexhead=True,critic_std_other_state_exact=unchanged['frozen_state_exact'],
        cost2zero=True,original_architecture_identity_unchanged=True,new_metadata_cross_schema_rejected=True,NN_freshFalse_preserves_fitted_weights=True,
        original_PPO_save_load_empty0=True,no_atanh_or_label_clipping=True,NN_reference_injection_rejected=True,aliases_finally_restore=True,
        existing_output_symlink_rejected_before_gate=True,
        limits='Synthetic one optimizer step/CPU model comparison only; no collection,1000step GPU fit,native NN success or CUDA RNG guarantee')
