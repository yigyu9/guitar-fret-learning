"""Strict frozen short-task checkpoint; seven consecutive H32x128 gradient probes."""
import argparse
import copy
import hashlib
from pathlib import Path
import random
import sys
import time


def run(checkpoint, out, seed):
    import isaacgym  # Native extension must precede NumPy/Torch.
    import numpy as np
    import torch
    from probe_math import decompose, gradient_probe, actor_groups, check_close
    from guitar_learning.training.decision_ppo import DecisionPPOTrainer
    from guitar_learning.training.ppo import PPOConfig
    from guitar_learning.training.finger_decisions import DecisionCollector
    from guitar_learning.training.finger_skill_runner import _pins, _validate_pins
    from guitar_learning.training.recording import write, digest, project_source_paths
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortPool, ShortPolicy
    from guitar_learning.tool.experiments.short_finger_learning.spec import SCHEMA, read_teacher
    from guitar_learning.tool.experiments.short_finger_learning.runner import compact_episode
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS

    checkpoint, out = Path(checkpoint), Path(out).resolve()
    if not checkpoint.is_absolute() or not checkpoint.is_file():
        raise ValueError('Existing absolute checkpoint path required')
    checkpoint = checkpoint.resolve()
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    metadata = payload.get('metadata', {})
    if metadata.get('schema') != SCHEMA or not metadata.get('input_pins'):
        raise ValueError('Sealed short_finger_learning.v2 checkpoint required')
    _validate_pins(metadata)
    settings = copy.deepcopy(metadata['settings'])
    spec = settings['song']['short_learning']
    if (spec.get('schema') != SCHEMA or read_teacher(spec['teacher']['input_path']) != spec['teacher']
            or settings['num_envs'] != 128 or settings['horizon'] != 32
            or settings['ppo']['minibatch_size'] != 4096
            or payload['updates'] not in (50, 100, 300)):
        raise ValueError('Exact teacher and original cp50/100/300 H32x128 required')
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    extra = [checkpoint, Path(__file__).resolve(), Path(__file__).with_name('probe_math.py'),
             *map(Path, metadata['input_pins']), Path(spec['teacher']['input_path']),
             *map(Path, spec['teacher']['source_evidence'])]
    pins = _pins(settings, out, extra)
    write(out/'inputs_before.json', pins)
    write(out/'invocation.json', dict(argv=sys.argv, seed=seed, seed_scope='paired diagnostic seed after strict load; new on-policy rollout, not historical batches',
        checkpoint=str(checkpoint), checkpoint_sha256=pins[str(checkpoint)], checkpoint_updates=payload['updates'],
        horizon=32, num_envs=128, consecutive_batches=7, normalization='4096 valid decisions independently per batch',
        optimizer_steps=0, source_physics_hz=240, gradient_scope='first whole-minibatch surrogate before clip/Adam; chunked sum, no parameter update'))
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool, policy, model_before = None, None, None
    completed, failure, unchanged, rows, cleanup_errors = False, None, False, [], []
    started = time.monotonic()
    try:
        pool = ShortPool(settings, out/'scene')
        write(out/'training_contract.json', pool.contract)
        policy = ShortPolicy(contract=pool.contract, size=settings['size']).to(settings['device'])
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        if pool.environment.approach_gamma != trainer.config.gamma:
            raise ValueError('Shaping/PPO gamma mismatch')
        trainer.load(checkpoint)
        model_before = {key: value.detach().cpu().clone() for key, value in policy.state_dict().items()}
        updates_before, cost_weight_before = trainer.updates, trainer.cost_weight
        # The same declared seed is used for each cp, after restoring its strict identity/RNG.
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed); torch.cuda.manual_seed_all(seed)
        write(out/'rng_before.json', dict(python=repr(random.getstate()), numpy=repr(np.random.get_state()),
            torch_cpu_sha256=hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest(),
            torch_cuda_sha256=[hashlib.sha256(x.cpu().numpy().tobytes()).hexdigest() for x in torch.cuda.get_rng_state_all()]))
        policy.eval()
        pool.observation = pool.reset()[0]
        collector = DecisionCollector(policy, pool, gamma=trainer.config.gamma, cost_gamma=trainer.config.cost_gamma)
        physics_before = pool.scene.physics_steps
        groups, parameter_rows = actor_groups(policy)
        write(out/'actor_parameters.json', dict(parameters=parameter_rows,
            groups=list(groups), component_order=[*REWARD_TERMS, 'reward_value_residual', 'negative_weighted_cost_gae']))
        for batch in range(7):
            raw, context, episodes = [], [], []
            def callback(tick, reward, cost, terminated, truncated, finished):
                env = pool.environment
                pieces = env._reward_components({})
                if tuple(pieces) != REWARD_TERMS:
                    raise ValueError('Reward component identity/order changed')
                values = torch.stack([pieces[key].detach().clone() for key in REWARD_TERMS], -1)
                check_close(values.sum(-1), reward, atol=2e-6, rtol=2e-6)
                raw.append(values)
                context.append(dict(local_time_s=env._local_time().detach().clone(),
                    source_time_s=env._score_time().detach().clone(),
                    episode_id=collector.episode_ids.detach().clone()))
                episodes.extend(compact_episode(row, spec) for row in finished)
            batch_started = time.monotonic()
            buffer, _ = collector.collect(32, transition_callback=callback)
            components = torch.stack(raw)
            if buffer['valid'].shape != (32,128) or not bool(buffer['valid'].all()) or not bool((buffer['duration'] == 1).all()):
                raise AssertionError('K1 identity ordering required')
            expected_tick = torch.arange(batch*32, (batch+1)*32, device=components.device)[:,None].expand(32,128)
            if not torch.equal(buffer['start_control_tick'], expected_tick):
                raise AssertionError('Collector tick alignment changed')
            if not torch.equal(buffer['episode_id'], torch.stack([x['episode_id'] for x in context])):
                raise AssertionError('Callback episode identity differs from decision buffer')
            if bool((buffer['next_reward_value'][buffer['terminated']] != 0).any()) or bool((buffer['next_cost_value'][buffer['terminated']] != 0).any()):
                raise AssertionError('True terminal must zero both next values')
            decomposition = decompose(buffer, components, trainer.config, trainer.cost_weight)
            collected_s = time.monotonic()-batch_started
            gradients = gradient_probe(policy, buffer, decomposition, groups, clip_ratio=trainer.config.clip_ratio)
            if any(value != 0 for value in gradients['groups']['inactive_std']['component_norm']) or gradients['groups']['inactive_std']['total_norm'] != 0:
                raise AssertionError('Inactive std gradient must remain zero')
            if pool.scene.physics_steps-physics_before != (batch+1)*32*4:
                raise AssertionError('Physical clock must advance four actual steps per control tick')
            data = {key: buffer[key].cpu().numpy() for key in ('reward', 'cost', 'reward_value', 'next_reward_value',
                'cost_value', 'next_cost_value', 'valid', 'duration', 'terminated', 'truncated', 'episode_id', 'start_control_tick')}
            data.update(reward_components=components.cpu().numpy(),
                local_time_s=torch.stack([x['local_time_s'] for x in context]).cpu().numpy(),
                source_time_s=torch.stack([x['source_time_s'] for x in context]).cpu().numpy())
            for key in ('raw', 'normalized_pieces', 'reward_gae', 'cost_gae', 'combined', 'normalized'):
                data['advantage_'+key] = decomposition[key].cpu().numpy()
            if not all(np.isfinite(value).all() for value in data.values()):
                raise AssertionError('Nonfinite compact capture')
            np.savez_compressed(out/('batch_%02d.npz'%(batch+1)), **data)
            summary = dict(batch=batch+1, start_control_tick=batch*32, end_control_tick=(batch+1)*32,
                reward_checks=decomposition['checks'], shared_std=float(decomposition['sigma']), gradients=gradients,
                raw_component_mean=decomposition['raw'].mean(0).tolist(), raw_component_std=decomposition['raw'].std(0,unbiased=False).tolist(),
                episode_completions=episodes, terminal_count=int(buffer['terminated'].sum()), truncated_count=int(buffer['truncated'].sum()),
                physics_steps_since_start=pool.scene.physics_steps-physics_before,
                collection_s=collected_s, gradient_s=time.monotonic()-batch_started-collected_s)
            write(out/('batch_%02d.json'%(batch+1)), summary)
            rows.append(summary)
            print('batch %d/7 completed: %.1fs'%(batch+1,time.monotonic()-batch_started), flush=True)
        unchanged = all(torch.equal(value.detach().cpu(), model_before[key]) for key,value in policy.state_dict().items())
        if not unchanged or trainer.updates != updates_before or trainer.cost_weight != cost_weight_before:
            raise AssertionError('Frozen model/trainer changed')
        completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        if model_before is not None:
            unchanged = all(torch.equal(value.detach().cpu(), model_before[key]) for key,value in policy.state_dict().items())
        if pool is not None:
            try:
                pool.close()
            except BaseException as error:
                cleanup_errors.append(dict(type=type(error).__name__, message=str(error)))
        changed = [path for path,value in pins.items() if not Path(path).is_file() or digest(path) != value]
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        write(out/'inputs_after.json', dict(verified=not changed and not missing, changed_paths=changed,
            unpinned_project_sources=missing, input_pins=pins))
        audit = pool.scene.diagnostics if pool and pool.scene else None
        valid_scene = bool(audit and audit.get('closed') and audit.get('physx_use_gpu') and audit.get('use_gpu_pipeline') and
            audit.get('simulator_count') == 1 and audit.get('environment_count') == 128)
        complete = completed and unchanged and not changed and not missing and valid_scene and not cleanup_errors
        write(out/'report.json', dict(schema='frozen_short_gradient_probe.v1', completed=complete, failure=failure,
            model_unchanged=unchanged, checkpoint_unchanged=str(checkpoint) not in changed, source_pins_unchanged=not changed,
            changed_inputs=changed, unpinned_project_sources=missing, scene_closed=pool is None or pool.closed,
            gpu_scene=audit, lifecycle_verified=valid_scene, batches_completed=len(rows), optimizer_steps=0,
            cleanup_errors=cleanup_errors,
            checkpoint_updates=payload['updates'], seed=seed, wall_s=time.monotonic()-started,
            gradient_numeric_scope='float32 forward/backward, whole4096 objective in256 chunks; metrics float64 on CPU',
            scope='fresh frozen-policy local gradient; not historical training gradients or causal performance contribution'))
        if failure is None and not complete:
            raise RuntimeError('Frozen model/source/scene audit failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=20261027)
    args = parser.parse_args()
    run(args.checkpoint, args.out, args.seed)


if __name__ == '__main__':
    main()
