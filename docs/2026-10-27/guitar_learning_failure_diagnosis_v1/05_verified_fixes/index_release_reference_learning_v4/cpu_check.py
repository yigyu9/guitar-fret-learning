"""Real rl38 CPU fixtures; no native scene, full fit, or PPO update."""
import copy
import inspect
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
import torch
import numpy as np
import runtime as rt
import learn


def check():
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    learn.seed()
    native = rt.base.read(rt.SOURCE/'runs/candidate/training_contract.json')
    contract = rt.attach(native)
    policy = rt.GoalPolicy(contract=contract,size='small')
    assert policy.architecture['state_dim'] == 557 and policy.architecture['phase'] == 'J'
    assert policy._active_mask().nonzero().flatten().tolist() == [17,18,19,20]
    inputs = [torch.zeros(2,557),torch.zeros(2,2,24),torch.zeros(2,2,dtype=torch.bool),
              torch.zeros(2,8,24),torch.zeros(2,8,dtype=torch.bool)]
    with torch.no_grad():
        action = policy.act(*inputs,deterministic=True)
        assert action['action'].shape == (2,39) and bool((action['action'][:,33:] == 0).all())
        torch.testing.assert_close(action['log_std'][0,17:21].exp(),rt.sigma4(),rtol=0,atol=0)
        latent = action['latent'].clone(); latent[:, :17] = 2.; latent[:,21:] = -2.
        assert torch.equal(policy.log_probability(action['mean'],action['log_std'],latent),action['logp'])
        other_mean = action['mean'].clone(); other_mean[:,:17] += 1.; other_mean[:,21:] -= 1.
        assert bool((policy.analytic_kl(action['mean'],action['log_std'],other_mean,action['log_std']) == 0).all())
        other_mean[:,17:21] += .01
        kl = policy.analytic_kl(action['mean'],action['log_std'],other_mean,action['log_std'])
        expected_kl = (.01**2/(2*action['log_std'][:,17:21].mul(2).exp())).sum(-1)
        torch.testing.assert_close(kl,expected_kl,rtol=1e-4,atol=1e-6)
    chosen = {n:p for n,p in policy.named_parameters() if n.startswith(('finger_encoder.','finger_heads.index.'))}
    flags = {n:p.requires_grad for n,p in policy.named_parameters()}
    initial = {n:v.clone() for n,v in policy.state_dict().items()}
    for n,p in policy.named_parameters(): p.requires_grad_(n in chosen)
    value = (policy(*inputs)['mean'][:,17:21].tanh()-.25).square().mean()
    opt = torch.optim.Adam(list(chosen.values()),lr=3e-4)
    value.backward(); opt.step()
    assert any(not torch.equal(initial[n],policy.state_dict()[n]) for n in chosen)
    assert all(torch.equal(initial[n],policy.state_dict()[n]) for n in initial if n not in chosen)
    for n,p in policy.named_parameters(): p.requires_grad_(flags[n])
    config = rt.settings(); assert config['size'] == 'large'
    config['device'],config['size'] = 'cpu','small'
    trainer = learn.DecisionPPOTrainer(policy,learn.PPOConfig(**config['ppo']))
    assert trainer.updates == 0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
    with tempfile.TemporaryDirectory() as temp:
        folder = Path(temp)
        checkpoint = folder/'fixture.pt'
        pins = {str(Path(__file__).resolve()):rt.base.sha(Path(__file__))}
        trainer.save(checkpoint,metadata=learn.metadata(config,pins))
        trainer.save(folder/'fresh.pt',metadata=learn.metadata(config,pins,fit_steps=0))
        restored = rt.GoalPolicy(contract=contract,size='small')
        other = learn.DecisionPPOTrainer(restored,learn.PPOConfig(**config['ppo']))
        fitted_metadata = learn.load(other,checkpoint,config)
        assert fitted_metadata['fit_steps'] == 1000 and 'MSE1000x192' in fitted_metadata['actual_initialization']
        fresh_metadata = learn.load(other,folder/'fresh.pt',config)
        assert fresh_metadata['fit_steps'] == 0 and fresh_metadata['actual_initialization'].endswith('no fit or PPO')
        before = learn.fingerprint(other)
        assert learn.fingerprint(other) == before
        other.updates += 1
        assert learn.fingerprint(other) != before
        other.updates -= 1
        assert learn.fingerprint(other) == before
        assert all(torch.equal(v,restored.state_dict()[n]) for n,v in policy.state_dict().items())
        bad = copy.deepcopy(contract); bad['action']['policy_output_adapter']['selected_teacher_blending'] = True
        try: rt.GoalPolicy(contract=bad,size='small')
        except ValueError: pass
        else: raise AssertionError('Altered selected policy contract admitted')
        payload = torch.load(checkpoint,map_location='cpu',weights_only=False)
        payload['identity']['architecture']['schema'] = 'old_goal_codec'
        torch.save(payload,folder/'old.pt')
        try: learn.load(other,folder/'old.pt',config)
        except ValueError: pass
        else: raise AssertionError('Old checkpoint identity admitted')
        data = {k:np.zeros((1416,*tuple(v.shape[1:])),dtype=v.numpy().dtype) for k,v in zip(learn.runner.FIELDS,inputs)}
        c = native['action']['target_contract']
        active_ids = [c['joint_names'].index(n) for n in c['action_order']]
        reference4 = np.asarray(c['reference105_rad'],dtype=np.float32)[active_ids][17:21]
        data.update(env_id=np.tile(np.arange(4),354),clock=np.repeat(np.arange(354)*4,4),
            time_s=np.repeat(np.arange(354)/60.,4),raw_goal_normalized=np.zeros((1416,4),dtype=np.float32),
            decoded_goal_rad=np.repeat(reference4[None],1416,axis=0))
        np.savez_compressed(folder/'observations4.npz',**data)
        rt.base.write(folder/'training_contract.json',native)
        _,buckets,phases,_ = learn.dataset(folder,config)
        assert len(buckets) == 6 and all(len(b) for b in buckets)
        assert all(bool((data['env_id'][b] < 3).all()) for b in buckets)
    control = native['action']['target_contract']
    active = torch.tensor([control['joint_names'].index(n) for n in control['action_order']])
    reference = torch.tensor(control['reference105_rad'])
    pool = rt.GoalPool.__new__(rt.GoalPool)
    pool.spec = config['song']['short_learning']
    pool.teacher_reference = reference[active]
    pool.controller = SimpleNamespace(reference=reference,active=active,target=reference.repeat(128,1),
        action_low=torch.tensor(control['action_lower_rad']),action_high=torch.tensor(control['action_upper_rad']))
    pool.incremental_mask = torch.zeros(39,dtype=torch.bool); pool.incremental_mask[17:33] = True
    pool.first = torch.ones(128,dtype=torch.bool); pool.capture_learning_trace = False
    called = []
    def native_step(self,request):
        called.append(request.clone()); return (None,)*6
    def forbidden(*args,**kwargs): raise AssertionError('Selected teacher called')
    raw = torch.full((128,39),.9); raw[:,17:21] = .1
    with patch.object(rt.shared.Pool,'step',native_step), patch.object(rt.v2,'reference_raw',forbidden), \
         patch.object(rt.shared,'reference_raw',forbidden), patch.object(rt.shared,'desired_reference',forbidden):
        pool.step(raw)
    others = [i for i in range(39) if not 17 <= i < 21]
    assert len(called) == 1 and bool((called[0][:,others] == 0).all())
    expected = torch.zeros_like(raw); expected[:,17:21] = raw[:,17:21]
    assert torch.equal(called[0],rt.shared.convert(pool,expected)[0])
    pool.num_envs = 128
    pool.observation = {k:v[:1].repeat(128,*([1]*(v.ndim-1))) for k,v in zip(learn.runner.FIELDS,inputs)}
    def physical_step(self,request):
        called.append(request.clone())
        return (self.observation,torch.ones(128),torch.zeros(128),
                torch.zeros(128,dtype=torch.bool),torch.zeros(128,dtype=torch.bool),[])
    with patch.object(rt.shared.Pool,'step',physical_step), patch.object(rt.v2,'reference_raw',forbidden), \
         patch.object(rt.shared,'reference_raw',forbidden), patch.object(rt.shared,'desired_reference',forbidden):
        buffer,episodes = learn.runner.DecisionCollector(policy,pool).collect(1)
    selected = torch.zeros(128,39); selected[:,17:21] = buffer['latent'][0,:,17:21].tanh()
    assert torch.equal(called[-1],rt.shared.convert(pool,selected)[0])
    observations = [pool.observation[k] for k in learn.runner.FIELDS]
    learn.seed()
    with torch.no_grad(): stochastic = policy.act(*observations)
    learn.seed()
    expected_noise = torch.distributions.Normal(torch.zeros(128,4),stochastic['log_std'][:,17:21].exp()).sample()
    assert torch.equal(stochastic['latent'][:,17:21],stochastic['mean'][:,17:21]+expected_noise)
    assert buffer['duration'].shape == (1,128) and bool((buffer['duration'] == 1).all())
    init_source = inspect.getsource(rt.GoalPool.__init__)
    assert 'self.record_first_controls = not training' in init_source
    original_compact = learn.runner.compact_episode
    assert learn.common(learn.runner._train).__globals__['compact_episode'] is rt.shared.compact_episode
    assert inspect.unwrap(learn.common(learn.runner._evaluate)).__globals__['compact_episode'] is rt.shared.compact_episode
    assert inspect.unwrap(learn.common(learn.runner._evaluate)).__globals__['SCHEMA'] == rt.SCHEMA
    assert learn.runner.compact_episode is original_compact
    targets = ((rt.shared,'reference_raw'),(rt.shared,'desired_reference'),(rt.v2,'reference_raw'))
    originals = [getattr(module,name) for module,name in targets]
    for module,name in targets:
        state = dict(counters=dict(selected_reference_calls=0))
        try:
            with learn.selected_reference_guard(state): getattr(module,name)(None)
        except RuntimeError as error:
            assert 'Selected reference helper forbidden' in str(error)
        else: raise AssertionError('Evaluation selected teacher call admitted')
        assert state['counters']['selected_reference_calls'] == 1
        assert all(getattr(m,n) is old for (m,n),old in zip(targets,originals))
    sentinel = RuntimeError('evaluation failure fixture')
    try:
        with learn.selected_reference_guard(dict(counters=dict(selected_reference_calls=0))):
            raise sentinel
    except RuntimeError as error: assert error is sentinel
    assert all(getattr(m,n) is old for (m,n),old in zip(targets,originals))
    assert rt.GoalPool.__dict__.get('record_first_controls') is None  # Per-instance training-only override.
    with tempfile.TemporaryDirectory() as temp:
        sentinel = RuntimeError('primary fixture')
        class BrokenClose:
            learning_trace,guard_rows,closed = [],[],False
            def close(self): raise OSError('secondary close fixture')
        try:
            with learn.audit(Path(temp)/'audit',config,pins,dict(pool=BrokenClose())):
                raise sentinel
        except RuntimeError as error:
            assert error is sentinel
        report = rt.base.read(Path(temp)/'audit/learning_report.json')
        assert not report['completed'] and report['failure']['message'] == 'primary fixture'
        assert report['cleanup_errors'][0]['stage'] == 'scene_close'
    actual = rt.HERE/'capture/runs/candidate'
    actual_capture = None
    if (actual/'observations4.npz').is_file():
        data,buckets,phases,actual_contract = learn.dataset(actual,rt.settings())
        learn.seed()
        large = rt.GoalPolicy(contract=actual_contract,size='large')
        with torch.no_grad():
            output = large.act(*(torch.as_tensor(data[k][:4]) for k in learn.runner.FIELDS),deterministic=True)
        assert output['action'].shape == (4,39)
        actual_capture = dict(rows=1416,state_dimension=557,event_shape=list(data['events'].shape[1:]),
            train_bucket_counts=[len(b) for b in buckets],heldout_rows=int((data['env_id']==3).sum()),large_forward=True)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    return dict(CPU_only=True, native_runs=0, full_fit_steps=0, PPO_updates=0,
        CPU_optimizer_fixture_steps=1, fixture_policy_size='small', configured_policy_size='large',
        current557_J_full39=True, selected17_21_likelihood_and_KL_only=True, effective4sigma_bitexact=True,
        supervised_only_declared_parameters_changed=True, own_strict_checkpoint_roundtrip=True,
        fresh0_fit1000_metadata_explicit=True, model_optimizer_update_fingerprint_stable_and_sensitive=True,
        old_checkpoint_and_changed_contract_rejected=True, no_selected_teacher_calls=True,
        other35_NN_inputs_zero=True, current_PPO_and_eval_loops_reused_without_global_mutation=True,
        current_collector_latent_to_native_request_exact=True, training_record_cap_disabled_only_for_training=True,
        post_construction_seed7_selected128x4_draw_boundary_exact=True,
        evaluation_SCHEMA_is_V4=True, three_reference_helpers_forbidden_and_counted=True,
        reference_aliases_restored_after_forbidden_call_and_unrelated_failure=True,
        synthetic1416_dataset_sixwindows_and_envsplit=True,
        primary_failure_survives_cleanup_with_partial_report=True,
        actual_capture=actual_capture,
        python_version=sys.version.split()[0], interpreter=sys.executable)


if __name__ == '__main__':
    result = check()
    print(json.dumps(result,indent=2))
