"""Frozen V6 rollout and ratio-one actor gradient audit; no fitting or PPO updates."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
V6 = HERE.parent/'index_cost_prior_zero_v6'
ROOT = HERE.parents[4]
TERMS = ('song_left_approach','song_left_contact','song_clean_hold','song_left_success',
         'song_wrong_press','song_performance_deficit','song_finger_standby','song_thumb_support','action_change')
CASES = {'fit': V6/'runs/fit/fit.pt', '50': V6/'runs/ppo/evaluation_000050.pt',
         '100': V6/'runs/ppo/evaluation_000100.pt', '300': V6/'runs/ppo/final.pt'}
FIELDS = ('state','events','mask','priority_events','priority_mask')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write(path, value):
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')

def experiment():
    spec = importlib.util.spec_from_file_location('reward_gradient_v6_experiment',V6/'experiment.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def prepare():
    exp = experiment()
    pins = exp.gate()
    for path in [HERE/n for n in ('PLAN.md','audit.py','cpu_check.py','cpu_verification.json')]+list(CASES.values()):
        pins[str(path)] = sha(path)
    write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=pins,
        cases={k:str(v) for k,v in CASES.items()},PPO_updates=0,fit_steps=0))
    assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'))
    return pins

def gate():
    exp = experiment()
    original = exp.gate()
    old = exp.base.HERE
    try:
        exp.base.HERE = HERE
        pins = exp.base.gate()
    finally:
        exp.base.HERE = old
    assert all(pins.get(k) == v for k,v in original.items())
    assert all(pins[str(p)] == sha(p) for p in CASES.values())
    return exp,pins

@contextmanager
def capture(pool, codec=None):
    """Clone final terms and endpoint ledgers before collector can reset any environment."""
    import torch
    env = pool.environment
    originals = (pool.step,env._reward_components)
    own_step = 'step' in pool.__dict__
    own_reward = '_reward_components' in env.__dict__
    rows, final = [], []
    boundaries = sorted(set(float(getattr(env,k)[i]) for k in ('press','onset','end') for i in (4,7,8)) |
                        {float(env.end[4])+.1})
    def reward(components):
        result = originals[1](components)
        assert set(result) == set(TERMS)
        final.append(torch.stack([result[k].detach().clone() for k in TERMS],-1))
        return result
    def step(action):
        before = env._score_time().detach().clone()
        row = dict(clock=env.clock.detach().clone(),local_time=env._local_time().detach().clone(),score_time=before)
        final.clear()
        row['requested_raw_goal4'] = action[:,17:21].detach().clone()
        if codec is not None:
            selected = torch.zeros_like(action)
            selected[:,17:21] = action[:,17:21]
            row['decoded_goal4'] = codec.convert(pool,selected)[1].detach().clone()
        result = originals[0](action)
        assert len(final) == 1, 'exactly one final reward calculation per control tick required'
        row['terms'] = final[0]
        torch.testing.assert_close(final[0].sum(-1),result[1],rtol=1e-5,atol=2e-6)
        after = env._score_time().detach().clone()
        bounds = torch.tensor(boundaries,device=before.device,dtype=before.dtype)
        row['phase'] = torch.bucketize(before,bounds,right=True)
        row['boundary_crossed'] = (before[:,None] < bounds) & (after[:,None] >= bounds)
        for key in ('wrong_source_flags','wrong_source_fret_min','wrong_source_fret_max','wrong_supported',
                    'wrong_ambiguous','wrong_next_preparation','contact_geometry','contact_facing',
                    'surface_body_loaded','candidate','wrong','surface_distance','surface_height'):
            value = getattr(env,key)  # Missing evidence is an error, never a fabricated zero.
            row['endpoint_'+key] = value[:,[4,7,8]].detach().clone()
        for key in ('wrong_source_time','wrong_supported_time','wrong_ambiguous_time','wrong_next_preparation_time'):
            row['note_'+key] = env.note[key][:,[4,7,8]].detach().clone()
        row['endpoint_q105'] = pool.scene.q.detach().clone()
        row['endpoint_target105'] = pool.scene.target.detach().clone()
        rows.append(row)
        return result
    try:
        env._reward_components = reward
        pool.step = step
        yield rows,boundaries
    finally:
        if own_step: pool.step = originals[0]
        else: del pool.step
        if own_reward: env._reward_components = originals[1]
        else: del env._reward_components


def first_attempts(rows):
    assert len(rows) == 128 and {r['env_id'] for r in rows} == set(range(128))
    assert all(r['valid'] is True and len(r['notes']) == 3 and
               {n['source_index'] for n in r['notes']} == {4,7,8} for r in rows)
    return sum(len(r['notes']) for r in rows)

@contextmanager
def analysis_audit(out,inputs):
    out = Path(out)
    out.mkdir(parents=True,exist_ok=False)
    write(out/'inputs_before.json',dict(inputs))
    failure = None
    try:
        assert all(sha(p) == h for p,h in inputs.items())
        yield out
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error))
        raise
    finally:
        changed = []
        for path,digest in inputs.items():
            try:
                if sha(path) != digest: changed.append(path)
            except BaseException: changed.append(path)
        verification = dict(completed=failure is None and not changed,failure=failure,
            changed_inputs=changed,input_pins=inputs,CPU_only=True,PPO_updates=0,fit_steps=0)
        try:
            write(out/'verification.json',verification)
        except BaseException as error:
            if failure is None: raise
            print('Secondary analysis verification error: '+repr(error),file=sys.stderr)
        if failure is None and changed:
            raise RuntimeError('Analysis input mutation detected')


def collect(case, out):
    exp,pins = gate()  # Must precede numerical and native imports.
    import isaacgym
    import numpy as np
    import torch
    from guitar_learning.training.rollout import DecisionCollector
    with exp.local_modules(include_learn=True) as modules:
        rt,learn = modules['runtime'],modules['learn']
        impl = learn.parent
        settings = exp.base.read(V6/'inputs/settings.json')
        assert (settings['num_envs'],settings['horizon'],settings['seed']) == (128,32,7)
        state = dict(counters=dict(PPO_updates=0,fit_steps=0,selected_reference_calls=0))
        with impl.audit(out,settings,pins,state) as out:
            learn.seed()
            pool = state['pool'] = rt.GoalPool(settings,out)
            write(out/'training_contract.json',pool.contract)
            policy = rt.GoalPolicy(contract=pool.contract,size=settings['size']).to(settings['device'])
            trainer = learn.DecisionPPOTrainer(policy,learn.PPOConfig(**settings['ppo']))
            learn.load(trainer,CASES[case],settings)
            expected_updates = 0 if case == 'fit' else int(case)
            assert trainer.updates == expected_updates
            checkpoint_before = sha(CASES[case])
            state['counters']['checkpoint_updates'] = trainer.updates
            before = impl.fingerprint(trainer)
            learn.seed()
            collector = DecisionCollector(policy,pool,gamma=trainer.config.gamma,cost_gamma=trainer.config.cost_gamma)
            episodes = []
            with impl.selected_reference_guard(state),capture(pool,rt.shared) as (rows,boundaries):
                for chunk,horizon in enumerate([32]*11+[2]):
                    rows.clear()
                    buffer,completed = collector.collect(horizon)
                    episodes.extend(completed)
                    assert len(rows) == horizon
                    arrays = {k:v.cpu().numpy() for k,v in buffer.items()}
                    arrays.update({'audit_'+k:torch.stack([r[k] for r in rows]).cpu().numpy() for k in rows[0]})
                    np.savez_compressed(out/('buffer_%02d.npz'%chunk),**arrays)
                    state['counters']['control_ticks'] = collector.control_ticks
            assert impl.fingerprint(trainer) == before and sha(CASES[case]) == checkpoint_before
            write(out/'episodes.json',episodes)
            first = pool.learning_episodes
            denominator = first_attempts(first)
            assert denominator == 384
            write(out/'first_attempts.json',dict(assigned_quotas=[1]*128,completed_attempts=len(first),
                incomplete_env_ids=sorted(set(range(128))-{r['env_id'] for r in first}),episodes=first))
            write(out/'collection.json',dict(case=case,checkpoint=str(CASES[case]),checkpoint_sha=sha(CASES[case]),
                checkpoint_updates=trainer.updates,selected_reference_calls=state['counters']['selected_reference_calls'],
                scene_count_created=1,scene_count_closed='verified by learning_report.closed after audit context',
                stochastic=True,H32_chunks=11,final_horizon=2,control_ticks=354,num_envs=128,
                model_optimizers_updates_frozen=True,before_fingerprint=before,after_fingerprint=impl.fingerprint(trainer),checkpoint_sha_before=checkpoint_before,phase_boundaries_score_s=boundaries,
                endpoint_rate_hz=60,note_ledger_integration_hz=240,first_attempt_note_denominator=384,
                all_reset_attempts=len(episodes),PPO_updates=0,fit_steps=0))


def decompose(buffer, config, weight):
    import torch
    from guitar_learning.training.ppo import compute_decision_gae,policy_advantages
    assert config.advantage_normalization == 'joint'
    b = buffer
    def gae(reward,value,next_value,gamma):
        return compute_decision_gae(reward,value,next_value,b['terminated'],b['truncated'],b['duration'],
                                    b['valid'],gamma,config.gae_lambda)[0]
    zero = torch.zeros_like(b['reward'])
    streams = [gae(b['audit_terms'][...,i],zero,zero,config.gamma) for i in range(9)]
    streams.append(gae(zero,b['reward_value'],b['next_reward_value'],config.gamma))
    streams.append(-weight*gae(b['cost'],b['cost_value'],b['next_cost_value'],config.cost_gamma))
    ar = gae(b['reward'],b['reward_value'],b['next_reward_value'],config.gamma)
    ac = gae(b['cost'],b['cost_value'],b['next_cost_value'],config.cost_gamma)
    valid = b['valid']
    combined,normalized,_,_ = policy_advantages(ar[valid],ac[valid],weight,'joint')
    raw = torch.stack([x[valid] for x in streams])
    torch.testing.assert_close(raw.sum(0),combined,rtol=3e-5,atol=3e-5)
    components = (raw-raw.mean(1,keepdim=True))/combined.std(unbiased=False).clamp_min(1e-8)
    torch.testing.assert_close(components.sum(0),normalized,rtol=3e-5,atol=3e-5)
    return components.detach(),normalized.detach()


def gradient_report(policy,buffer,config,weight,accumulator=None):
    import torch
    components,advantage = decompose(buffer,config,weight)
    valid = buffer['valid']
    count = int(valid.sum())
    result = policy.evaluate(*(buffer[k][valid] for k in FIELDS),buffer['latent'][valid])
    torch.testing.assert_close(result['mean'],buffer['old_mean'][valid],rtol=2e-5,atol=3e-6)
    torch.testing.assert_close(result['log_std'],buffer['old_log_std'][valid],rtol=2e-5,atol=3e-6)
    saved_ratio = (result['logp']-buffer['logp'][valid]).exp()
    ratio = (result['logp']-result['logp'].detach()).exp()
    assert torch.equal(ratio,torch.ones_like(ratio))
    parameters = [p for p in policy.actor_parameters() if p.requires_grad]
    def grad(loss):
        values = torch.autograd.grad(loss,parameters,retain_graph=True,allow_unused=True)
        return torch.cat([(torch.zeros_like(p) if v is None else v).reshape(-1) for p,v in zip(parameters,values)]).detach()
    total = grad(-torch.minimum(ratio*advantage,ratio.clamp(1-config.clip_ratio,1+config.clip_ratio)*advantage).mean())
    names = [*TERMS,'common_reward_critic_bootstrap','negative_weighted_cost_advantage']
    vectors = [grad(-(ratio*component).sum()/count) for component in components]
    torch.testing.assert_close(sum(vectors),total,rtol=2e-4,atol=3e-5)
    def cosine(a,b):
        denom = a.norm()*b.norm()
        return float(a.dot(b)/denom) if float(denom) else None
    phases = buffer['audit_phase'][valid]
    phase_vectors,phase_rows = [],[]
    for phase in sorted(set(phases.tolist())):
        mask = phases == phase
        vector = grad(-(ratio*advantage*mask).sum()/count)
        phase_vectors.append(vector)
        mean_gradient = torch.autograd.grad(-(ratio*advantage*mask).sum()/count,result['mean'],retain_graph=True)[0]
        phase_rows.append(dict(phase=phase,count=int(mask.sum()),norm=float(vector.norm()),
            cosine_total=cosine(vector,total),selected4_mean_raw_loss_gradient=mean_gradient[:,17:21].sum(0).tolist()))
    torch.testing.assert_close(sum(phase_vectors),total,rtol=2e-4,atol=3e-5)
    cross = []
    for phase in sorted(set(phases.tolist())):
        mask = phases == phase
        term_rows = []
        for name,component in zip(names,components):
            vector = grad(-(ratio*component*mask).sum()/count)
            term_rows.append(dict(term=name,norm=float(vector.norm()),cosine_total=cosine(vector,total)))
        cross.append(dict(phase=phase,terms=term_rows))
    if accumulator is not None:
        scale = count/(354.*128)
        accumulator['total'] = accumulator.get('total',torch.zeros_like(total))+scale*total
        for name,vector in zip(names,vectors):
            accumulator[name] = accumulator.get(name,torch.zeros_like(vector))+scale*vector
        for row,vector in zip(phase_rows,phase_vectors):
            name = 'phase_%d'%row['phase']
            accumulator[name] = accumulator.get(name,torch.zeros_like(vector))+scale*vector
    mean_total = torch.autograd.grad(-(ratio*advantage).sum()/count,result['mean'],retain_graph=True)[0]
    term_directions = [torch.autograd.grad(-(ratio*c).sum()/count,result['mean'],retain_graph=True)[0][:,17:21].sum(0).tolist() for c in components]
    return dict(count=count,total_norm=float(total.norm()),ratio_max_error=float((ratio-1).abs().max()),
        selected4_mean_raw_loss_gradient=mean_total[:,17:21].sum(0).tolist(),
        CPU_anchor='same CPU forward detached logp; saved GPU logp retained unchanged',
        saved_logp_max_difference=float((result['logp']-buffer['logp'][valid]).abs().max()),
        saved_ratio_max_error=float((saved_ratio-1).abs().max()),
        saved_mean_max_difference=float((result['mean']-buffer['old_mean'][valid]).abs().max()),
        saved_log_std_max_difference=float((result['log_std']-buffer['old_log_std'][valid]).abs().max()),
        components=[dict(term=n,norm=float(v.norm()),cosine_total=cosine(v,total),selected4_mean_raw_loss_gradient=d) for n,v,d in zip(names,vectors,term_directions)],
        component_cosines=[[cosine(a,b) for b in vectors] for a in vectors],phases=phase_rows,
        phase_cosines=[[cosine(a,b) for b in phase_vectors] for a in phase_vectors],phase_terms=cross,
        component_gradient_max_error=float((sum(vectors)-total).abs().max()),
        phase_gradient_max_error=float((sum(phase_vectors)-total).abs().max()))


def cpu_load(trainer,path,settings,learn,rt):
    """Read-only CPU model audit: exact identity/pins/tensors; no optimizer or RNG resume."""
    import torch
    from guitar_learning.training.finger_skill_runner import _validate_pins
    payload = torch.load(path,map_location='cpu',weights_only=False)
    data = payload['metadata']
    assert data['schema'] == rt.SCHEMA and data['settings'] == settings
    assert data['policy_output_adapter'] == rt.ADAPTER and data['cost_prior'] == rt.COST_PRIOR
    assert data['fresh_only'] is True and data['fit_steps'] == 1000 and data['input_pins']
    _validate_pins(data)
    assert payload['identity'] == trainer._identity()
    assert all(torch.isfinite(v).all() for v in payload['model'].values())
    current = trainer.policy.state_dict()
    assert current.keys() == payload['model'].keys()
    assert all(current[k].shape == v.shape and current[k].dtype == v.dtype for k,v in payload['model'].items())
    trainer.policy.load_state_dict(payload['model'],strict=True)
    assert all(torch.equal(trainer.policy.state_dict()[k],v) for k,v in payload['model'].items())
    trainer.cost_weight,trainer.updates = payload['cost_weight'],payload['updates']
    assert trainer.cost_weight == 1.
    return data


def _analyze(runs,out,exp,pins,inputs):
    import numpy as np
    import torch
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized() and not torch.cuda.is_available()
    out = Path(out)
    with exp.local_modules(include_learn=True) as modules:
        rt,learn = modules['runtime'],modules['learn']
        impl = learn.parent
        settings = exp.base.read(V6/'inputs/settings.json')
        reports = {}
        for case in CASES:
            folder = Path(runs)/case
            for filename in ('collection.json','training_contract.json','inputs_before.json','inputs_after.json','learning_report.json','episodes.json','first_attempts.json'):
                path = folder/filename
                assert inputs[str(path.resolve())] == sha(path)
            after = json.loads((folder/'inputs_after.json').read_text())
            assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources']
            assert after['input_pins'] == pins == json.loads((folder/'inputs_before.json').read_text())
            status = json.loads((folder/'learning_report.json').read_text())
            assert status['completed'] and status['closed'] and not status['failure'] and not status['cleanup_errors']
            assert status['PPO_updates'] == status['fit_steps'] == status['selected_reference_calls'] == 0
            expected_updates = 0 if case == 'fit' else int(case)
            assert status['checkpoint_updates'] == expected_updates and status['control_ticks'] == 354
            collection = json.loads((folder/'collection.json').read_text())
            assert collection['case'] == case and collection['checkpoint_sha'] == collection['checkpoint_sha_before'] == sha(CASES[case])
            assert collection['checkpoint_updates'] == expected_updates
            assert collection['stochastic'] is True and collection['num_envs'] == 128 and collection['control_ticks'] == 354
            assert collection['H32_chunks'] == 11 and collection['final_horizon'] == 2
            assert collection['PPO_updates'] == collection['fit_steps'] == collection['selected_reference_calls'] == 0
            assert collection['model_optimizers_updates_frozen'] is True and collection['before_fingerprint'] == collection['after_fingerprint']
            first = json.loads((folder/'first_attempts.json').read_text())
            assert first['assigned_quotas'] == [1]*128 and first['completed_attempts'] == 128 and not first['incomplete_env_ids']
            assert first_attempts(first['episodes']) == collection['first_attempt_note_denominator'] == 384
            episodes = json.loads((folder/'episodes.json').read_text())
            assert len(episodes) == collection['all_reset_attempts'] >= 128
            contract = json.loads((folder/'training_contract.json').read_text())
            policy = rt.GoalPolicy(contract=contract,size=settings['size']).cpu()
            trainer = learn.DecisionPPOTrainer(policy,learn.PPOConfig(**settings['ppo']))
            cpu_load(trainer,CASES[case],settings,learn,rt)
            before = impl.fingerprint(trainer)
            rng = torch.get_rng_state().clone()
            grads = [None if p.grad is None else p.grad.clone() for p in policy.parameters()]
            chunks,accumulator = [],{}
            files = sorted(folder.glob('buffer_*.npz'))
            assert len(files) == 12
            previous = None
            for index,path in enumerate(files):
                assert inputs[str(path.resolve())] == sha(path)
                with np.load(path,allow_pickle=False) as archive:
                    buffer = {k:torch.from_numpy(archive[k].copy()) for k in archive.files}
                assert buffer['reward'].shape == ((32 if index < 11 else 2),128)
                validate_buffer(buffer,index,previous)
                previous = {k:v[-1].clone() for k,v in buffer.items()}
                torch.testing.assert_close(buffer['audit_terms'].sum(-1),buffer['reward'],rtol=1e-5,atol=2e-6)
                chunks.append(gradient_report(policy,buffer,trainer.config,trainer.cost_weight,accumulator))
            assert before == impl.fingerprint(trainer) and torch.equal(rng,torch.get_rng_state())
            assert all((p.grad is None if g is None else torch.equal(p.grad,g)) for p,g in zip(policy.parameters(),grads))
            reports[case] = dict(chunks=chunks,weighted_chunk_gradient=aggregate_gradients(accumulator))
        write(out/'analysis.json',dict(reports=reports,input_pins=inputs,
            CPU_load='Exact identity/source pins and strict=True model tensors, original state exact equality; optimizers and CUDA RNG never restored; read-only CPU model audit, not a training resume.',
            scope='Frozen-policy full-buffer initial loss gradients, averaged over each complete H32 or final H2 valid count; no entropy term. Not Adam deltas, clipping attribution or historical training minibatch gradients.',
            selected4='Gradient of loss with respect to raw latent Gaussian mean; negative gradient is local improvement direction, not a physical joint direction.',
            invariants=dict(model_optimizer_updates_unchanged=True,parameter_grad_unchanged=True,torch_CPU_RNG_unchanged=True)))

def aggregate_gradients(accumulator):
    import torch
    total = accumulator['total']
    terms = [*TERMS,'common_reward_critic_bootstrap','negative_weighted_cost_advantage']
    phases = sorted(k for k in accumulator if k.startswith('phase_'))
    torch.testing.assert_close(sum(accumulator[k] for k in terms),total,rtol=2e-4,atol=3e-5)
    torch.testing.assert_close(sum(accumulator[k] for k in phases),total,rtol=2e-4,atol=3e-5)
    def cosine(a,b):
        denominator = a.norm()*b.norm()
        return float(a.dot(b)/denominator) if float(denominator) else None
    return dict(scope='Valid-count weighted mean of H32/finalH2 initial gradients, each with its own original GAE and joint normalization. Not 354tick integrated GAE, historical training minibatch gradients or Adam.',
        total_norm=float(total.norm()),components=[dict(term=k,norm=float(accumulator[k].norm()),cosine_total=cosine(accumulator[k],total)) for k in terms],
        component_cosines=[[cosine(accumulator[a],accumulator[b]) for b in terms] for a in terms],
        phases=[dict(phase=int(k.split('_')[1]),norm=float(accumulator[k].norm()),cosine_total=cosine(accumulator[k],total)) for k in phases],
        phase_cosines=[[cosine(accumulator[a],accumulator[b]) for b in phases] for a in phases],
        component_sum_max_error=float((sum(accumulator[k] for k in terms)-total).abs().max()),
        phase_sum_max_error=float((sum(accumulator[k] for k in phases)-total).abs().max()))


def validate_buffer(buffer,index,previous):
    import torch
    h = 32 if index < 11 else 2
    assert buffer['reward'].shape == (h,128)
    for key,value in buffer.items():
        if value.is_floating_point(): assert bool(torch.isfinite(value).all()), key
    for key in ('terminated','truncated','valid'):
        assert buffer[key].dtype == torch.bool
    assert bool(buffer['valid'].all()) and bool((buffer['duration'] == 1).all())
    expected = torch.arange(index*32,index*32+h)[:,None].expand(h,128)
    assert torch.equal(buffer['start_control_tick'],expected)
    if previous is not None:
        expected_id = previous['episode_id']+(previous['terminated']|previous['truncated']).long()
        assert torch.equal(buffer['episode_id'][0],expected_id)
        expected_clock = torch.where(previous['terminated']|previous['truncated'],0,previous['audit_clock']+4)
        assert torch.equal(buffer['audit_clock'][0],expected_clock)
    else:
        assert bool((buffer['episode_id'][0] == 0).all()) and bool((buffer['audit_clock'][0] == 0).all())
    for tick in range(1,h):
        done = buffer['terminated'][tick-1]|buffer['truncated'][tick-1]
        assert torch.equal(buffer['episode_id'][tick],buffer['episode_id'][tick-1]+done.long())
        assert torch.equal(buffer['audit_clock'][tick],torch.where(done,0,buffer['audit_clock'][tick-1]+4))
    assert bool((buffer['next_reward_value'][buffer['terminated']] == 0).all())
    assert bool((buffer['next_cost_value'][buffer['terminated']] == 0).all())

def analyze(runs,out):
    exp,pins = gate()
    inputs = dict(pins)
    for case in CASES:
        folder = Path(runs)/case
        for name in ('collection.json','training_contract.json','inputs_before.json','inputs_after.json',
                     'learning_report.json','episodes.json','first_attempts.json'):
            path = folder/name
            inputs[str(path.resolve())] = sha(path)
        for path in sorted(folder.glob('buffer_*.npz')): inputs[str(path.resolve())] = sha(path)
    with analysis_audit(out,inputs) as output:
        _analyze(runs,output,exp,pins,inputs)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare');sub.add_parser('gate-check')
    p = sub.add_parser('collect');p.add_argument('--case',choices=CASES,required=True);p.add_argument('--out',required=True)
    p = sub.add_parser('analyze');p.add_argument('--runs',required=True);p.add_argument('--out',required=True)
    args = parser.parse_args()
    if args.command == 'prepare': print(json.dumps(dict(prepared=True,pins=len(prepare()))))
    elif args.command == 'gate-check':
        gate();assert not any(k in sys.modules for k in ('numpy','torch','isaacgym'));print('{"ready":true,"stdlib_only":true}')
    elif args.command == 'collect': collect(args.case,args.out)
    else: analyze(args.runs,args.out)
