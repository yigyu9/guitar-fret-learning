"""Bounded current-policy fit and composition of the existing PPO/evaluator loops."""
import bisect
from contextlib import contextmanager
import copy
import hashlib
import inspect
from pathlib import Path
import random
import sys
from types import FunctionType, SimpleNamespace

import numpy as np
import torch
import runtime as rt
from guitar_learning.tool.experiments.short_finger_learning import runner
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.training.finger_skill_runner import _validate_pins


def seed():
    random.seed(7); np.random.seed(7); torch.manual_seed(7)
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False


def metadata(settings, pins, *, fit_steps=1000):
    assert fit_steps in (0,1000)
    return dict(schema=rt.SCHEMA, settings=copy.deepcopy(settings), input_pins=dict(pins),
        fresh_only=True, actual_initialization=('fresh current557/Jv3 seed7; normalized goal MSE1000x192'
            if fit_steps else 'fresh current557/Jv3 seed7; no fit or PPO'),
        policy_output_adapter=copy.deepcopy(rt.ADAPTER), fit_steps=fit_steps,
        selected_policy_control='NN-only four axes; native nonselected support retained')


def load(trainer, path, settings):
    data = torch.load(path,map_location='cpu',weights_only=False)['metadata']
    if (data['schema'] != rt.SCHEMA or data['settings'] != settings or data['policy_output_adapter'] != rt.ADAPTER
            or not data.get('input_pins') or data.get('fresh_only') is not True or data.get('fit_steps') not in (0,1000)):
        raise ValueError('Own fresh V4 metadata required')
    _validate_pins(data)
    trainer.load(path)  # Own full architecture/contract/config equality and strict=True.
    return data


def fingerprint(trainer):
    digest = hashlib.sha256()
    def add(value):
        if isinstance(value,torch.Tensor):
            digest.update(str((value.dtype,tuple(value.shape))).encode())
            digest.update(value.detach().cpu().contiguous().numpy().tobytes())
        elif isinstance(value,dict):
            for key,item in value.items(): add(key); add(item)
        elif isinstance(value,(list,tuple)):
            for item in value: add(item)
        else: digest.update(repr(value).encode())
    add((trainer.policy.state_dict(),trainer.actor_optimizer.state_dict(),
         trainer.value_optimizer.state_dict(),trainer.cost_weight,trainer.updates))
    return digest.hexdigest()


def dataset(capture, settings):
    capture = Path(capture)
    with np.load(capture/'observations4.npz', allow_pickle=False) as z:
        data = {k:z[k].copy() for k in z.files}
    assert len(data['env_id']) == 1416 and data['state'].shape == (1416,557)
    assert data['raw_goal_normalized'].shape == data['decoded_goal_rad'].shape == (1416,4)
    assert set(data['env_id']) == {0,1,2,3}
    for key in (*runner.FIELDS, 'raw_goal_normalized', 'decoded_goal_rad'):
        assert np.isfinite(data[key]).all(), key
    for env_id in range(4):
        time = data['time_s'][data['env_id'] == env_id]
        np.testing.assert_allclose(time, np.arange(354)/60., rtol=0, atol=1e-12)
        np.testing.assert_array_equal(data['clock'][data['env_id'] == env_id],np.arange(354)*4)
    short = settings['song']['short_learning']
    bounds = [short['teacher']['ramp_s'], *rt.shared.boundaries(short['view'])]
    phases = np.asarray([bisect.bisect_right(bounds, float(t)+1/60.) for t in data['time_s']])
    buckets = [np.flatnonzero((data['env_id'] < 3) & (phases == i)) for i in range(6)]
    assert all(len(b) for b in buckets)
    contract = rt.attach(rt.base.read(capture/'training_contract.json'))
    control = contract['action']['target_contract']
    active = [control['joint_names'].index(n) for n in control['action_order']]
    reference = torch.tensor(control['reference105_rad'])[active][17:21]
    low, high = (torch.tensor(control[k])[17:21] for k in ('action_lower_rad','action_upper_rad'))
    decoded = rt.shared.decode(torch.from_numpy(data['raw_goal_normalized']), reference, low, high)
    np.testing.assert_allclose(decoded.numpy(), data['decoded_goal_rad'], rtol=0, atol=2e-7)
    return data, buckets, phases, contract


@contextmanager
def audit(out, settings, pins, state):
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    rt.base.write(out/'settings.json', settings)
    rt.base.write(out/'inputs_before.json', pins)
    failure, cleanup = None, []
    try:
        assert not rt.base.changed_pins(pins)
        yield out
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        def emit(name,value):
            try: rt.base.write(out/name,value)
            except BaseException as error:
                if failure is None: raise
                cleanup.append(dict(stage=name,message=repr(error)))
                print('Secondary learning audit error: '+repr(error),file=sys.stderr)
        pool = state.get('pool')
        if pool is not None:
            for name, rows in (('learning_control_env0.npz', pool.learning_trace),
                               ('current_goal_DIP60.npz', pool.guard_rows)):
                try: rt.base.save_rows(out/name, rows)
                except BaseException as error: cleanup.append(dict(stage=name, message=repr(error)))
            try: pool.close()
            except BaseException as error: cleanup.append(dict(stage='scene_close', message=repr(error)))
        changed = rt.base.changed_pins(pins)
        missing = sorted(runner.project_source_paths(list(sys.modules.items()))-set(pins))
        if failure is not None:
            emit('partial_progress.json',dict(counters=state.get('counters',{}),fit_losses=state.get('fit_losses',[])))
            if pool is not None and getattr(pool,'capture_learning_trace',False):
                emit('partial_evaluation.json',dict(assigned_quotas=[1]*128,complete=False,
                    completed_attempts=len(pool.learning_episodes),episodes=pool.learning_episodes))
        emit('inputs_after.json', dict(verified=not changed and not missing,
            changed_paths=changed, unpinned_project_sources=missing, input_pins=pins))
        emit('learning_report.json', dict(schema=rt.SCHEMA,
            completed=failure is None and not cleanup and not changed and not missing, failure=failure,
            cleanup_errors=cleanup, closed=pool is None or pool.closed, changed_inputs=changed,
            unpinned_project_sources=missing, **state.get('counters', {})))
        if failure is None and (cleanup or changed or missing):
            raise RuntimeError('Learning lifecycle/input audit failed')


def fit(capture, settings, pins, out):
    assert settings['seed'] == 7 and settings['size'] == 'large' and settings['num_envs'] == 128
    state = dict(counters=dict(fit_steps=0, PPO_updates=0, native_runs=0))
    with audit(out, settings, pins, state) as out:
        data, buckets, phases, contract = dataset(capture, settings)
        seed()
        policy = rt.GoalPolicy(contract=contract, size=settings['size']).to(settings['device'])
        fresh = metadata(settings,pins,fit_steps=0)
        DecisionPPOTrainer(policy,PPOConfig(**settings['ppo'])).save(out/'fresh.pt',metadata=fresh)
        flags = {n:p.requires_grad for n,p in policy.named_parameters()}
        chosen = {n:p for n,p in policy.named_parameters() if n.startswith(('finger_encoder.','finger_heads.index.'))}
        initial = {n:v.detach().clone() for n,v in policy.state_dict().items()}
        for n,p in policy.named_parameters(): p.requires_grad_(n in chosen)
        inputs = {k:torch.as_tensor(data[k], device=settings['device']) for k in runner.FIELDS}
        labels = torch.as_tensor(data['raw_goal_normalized'], device=settings['device'])
        optimizer = torch.optim.Adam(list(chosen.values()), lr=3e-4)
        rng, losses = np.random.RandomState(7), []
        state['fit_losses'] = losses
        for step in range(1000):
            index = torch.as_tensor(np.concatenate([rng.choice(b,32,replace=True) for b in buckets]), device=settings['device'])
            pred = policy(*(inputs[k][index] for k in runner.FIELDS))['mean'][:,17:21].tanh()
            value = (pred-labels[index]).square().mean()
            assert bool(torch.isfinite(value))
            optimizer.zero_grad(); value.backward()
            torch.nn.utils.clip_grad_norm_(list(chosen.values()), .5, error_if_nonfinite=True)
            optimizer.step(); losses.append(float(value)); state['counters']['fit_steps'] = step+1
        frozen = [n for n in initial if n not in chosen]
        assert all(torch.equal(initial[n],policy.state_dict()[n]) for n in frozen)
        with torch.no_grad(): pred = policy(*(inputs[k] for k in runner.FIELDS))['mean'][:,17:21].tanh().cpu().numpy()
        errors = {split:[dict(phase=i, samples=int((keep & (phases == i)).sum()),
            rms4=np.sqrt(np.mean((pred[keep & (phases == i)]-data['raw_goal_normalized'][keep & (phases == i)])**2,axis=0)).tolist())
            for i in range(6)] for split,keep in [('train',data['env_id']<3),('heldout_same_scene',data['env_id']==3)]}
        rt.base.write(out/'offline_errors.json', dict(loss='normalized goal MSE', losses=losses,
            errors=errors, frozen_tensors=len(frozen), frozen_exact=True))
        for n,p in policy.named_parameters(): p.requires_grad_(flags[n])
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        assert trainer.updates == 0 and not trainer.actor_optimizer.state and not trainer.value_optimizer.state
        trainer.save(out/'fit.pt', metadata=metadata(settings,pins))
        restored = rt.GoalPolicy(contract=contract, size=settings['size']).to(settings['device'])
        load(DecisionPPOTrainer(restored,PPOConfig(**settings['ppo'])), out/'fit.pt', settings)


def common(function):
    original = inspect.unwrap(function)
    namespace = dict(original.__globals__, compact_episode=rt.shared.compact_episode, SCHEMA=rt.SCHEMA)
    result = FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
    return torch.no_grad()(result) if original is not function else result


@contextmanager
def selected_reference_guard(state):
    targets = ((rt.shared,'reference_raw'),(rt.shared,'desired_reference'),(rt.v2,'reference_raw'))
    originals = [getattr(module,name) for module,name in targets]
    def forbidden(*args,**kwargs):
        state['counters']['selected_reference_calls'] += 1
        raise RuntimeError('Selected reference helper forbidden during NN-only evaluation')
    try:
        for module,name in targets: setattr(module,name,forbidden)
        yield
        assert state['counters']['selected_reference_calls'] == 0
    finally:
        for (module,name),original in zip(targets,originals): setattr(module,name,original)


def train(checkpoint, settings, pins, out):
    assert (settings['num_envs'],settings['horizon'],settings['updates'],settings['checkpoint_every']) == (128,32,300,50)
    state = dict(counters=dict(fit_steps=0, PPO_updates=0, initialization_fit_steps=1000))
    with audit(out,settings,pins,state) as out:
        seed(); pool = state['pool'] = rt.GoalPool(settings,out,training=True)
        rt.base.write(out/'training_contract.json',pool.contract)
        policy = rt.GoalPolicy(contract=pool.contract,size=settings['size']).to(settings['device'])
        trainer = DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
        fitted = load(trainer,checkpoint,settings)
        assert fitted['fit_steps'] == 1000
        state['counters']['checkpoint_updates'] = trainer.updates
        assert trainer.updates == 0
        try:
            common(runner._train)(pool,policy,trainer,settings,metadata(settings,pins),out)
        finally:
            state['counters']['PPO_updates'] = trainer.updates
        assert trainer.updates == 300
        state['counters']['PPO_updates'] = trainer.updates


def evaluate(checkpoint, settings, pins, out, *, stochastic=False):
    state = dict(counters=dict(fit_steps=0, PPO_updates=0, selected_reference_calls=0))
    with audit(out,settings,pins,state) as out:
        seed(); pool = state['pool'] = rt.GoalPool(settings,out)
        rt.base.write(out/'training_contract.json',pool.contract)
        policy = rt.GoalPolicy(contract=pool.contract,size=settings['size']).to(settings['device'])
        trainer = DecisionPPOTrainer(policy,PPOConfig(**settings['ppo']))
        loaded = load(trainer,checkpoint,settings)
        state['counters']['initialization_fit_steps'] = loaded['fit_steps']
        before = fingerprint(trainer)
        checkpoint_sha = rt.base.sha(checkpoint)
        version = trainer.updates
        state['counters']['checkpoint_updates'] = version
        class EvaluationPolicy:
            def act(self,*args,**kwargs):
                return policy.act(*args,deterministic=not stochastic)
        primary = None
        try:
            seed()  # Match V2's post-construction seed7 draw boundary after checkpoint RNG restoration.
            with selected_reference_guard(state):
                common(runner._evaluate)(pool,EvaluationPolicy(),pool.spec,
                    SimpleNamespace(episodes=128,control='policy'),out)
        except BaseException as error:
            primary = error
            raise
        finally:
            try:
                after = fingerprint(trainer)
                checkpoint_after = rt.base.sha(checkpoint)
                rt.base.write(out/'evaluation_freeze.json',dict(before=before,after=after,
                    checkpoint_sha_before=checkpoint_sha,checkpoint_sha_after=checkpoint_after,
                    model_optimizers_updates_frozen=before == after,checkpoint_frozen=checkpoint_sha == checkpoint_after))
                assert before == after and checkpoint_sha == checkpoint_after
            except BaseException as error:
                if primary is None: raise
                print('Secondary evaluation freeze audit error: '+repr(error),file=sys.stderr)
        evaluation = rt.base.read(out/'evaluation.json')
        assert evaluation['assigned_quotas'] == [1]*128 and len(evaluation['episodes']) == 128
        rt.base.write(out/'acceptance.json',dict(acceptance=rt.base.acceptance(evaluation['episodes']),
            stochastic=stochastic, policy_performance=True, selected_control='NN-only', checkpoint_updates=version))
