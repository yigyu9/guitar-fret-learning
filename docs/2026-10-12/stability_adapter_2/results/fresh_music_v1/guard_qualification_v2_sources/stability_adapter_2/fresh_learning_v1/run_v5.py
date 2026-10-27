"""Independent Stage-A collection, PPO training, and native video evaluation."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import shutil
import sys
import time
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--mode', choices=('baseline', 'train', 'eval'), required=True)
    parser.add_argument('--seed', type=int, default=101)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cuda')
    parser.add_argument('--updates', type=int, default=64)
    parser.add_argument('--rollout-steps', type=int, default=256)
    parser.add_argument('--save-every', type=int, default=4)
    parser.add_argument('--checkpoint', type=Path)
    args = parser.parse_args()
    if args.updates < 1 or args.rollout_steps < 2 or args.save_every < 1:
        parser.error('positive budget and at least two rollout steps required')
    if (args.mode == 'eval') != (args.checkpoint is not None):
        parser.error('checkpoint is required only for eval; training always starts from scratch')
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)

    # Isaac Gym's binding must load before torch.
    import isaacgym  # noqa: F401
    from .environment_v5 import FreshGuitarEnvironment, collect_inputs
    from .policy import Policy
    from .ppo import PPOConfig, PPOTrainer
    from ..gym_trial_recording import GymTrialRecording
    from ..run_joint_hold import native_state
    import numpy as np
    import torch

    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(1)
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA requested but unavailable; use host GPU execution')
    hashes = collect_inputs()
    if not isinstance(hashes, dict):
        hashes = {str(Path(p).resolve()): sha(p) for p in hashes}
    hashes[str(Path(__file__).resolve())] = sha(__file__)
    launcher = Path(__file__).with_name('launch_v5.sh')
    hashes[str(launcher)] = sha(launcher)
    if args.checkpoint:
        hashes[str(args.checkpoint.resolve())] = sha(args.checkpoint)
    project = Path(__file__).resolve().parents[2]
    for name in hashes:
        path = Path(name)
        if path.suffix in ('.py', '.sh') and project in path.parents:
            target = args.out / 'source_before' / path.relative_to(project)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    save(args.out / 'attempt.json', {
        'schema': 'fresh54_stage_a_run_v1',
        'arguments': {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        'input_sha256': hashes, 'old_policy_loaded': False,
        'task': 'Stage A: small palm motions while supporting a free guitar; no music scoring',
        'started_unix': time.time(), 'torch_version': torch.__version__,
    })
    env, recorder, trainer = None, None, None
    failure, videos, initial_parameters = None, {}, None
    steps = episodes = 0
    latest_checkpoint = None
    fault_checkpoint = None
    checkpoint_save_error = None
    buffer = {}
    last_attempt = None
    all_forbidden = []
    metrics = []
    start = time.monotonic()
    try:
        env = FreshGuitarEnvironment(recording=args.mode != 'train', seed=args.seed)
        obs = env.reset(seed=args.seed)
        policy = Policy(env.observation_dim).to(args.device)
        trainer = PPOTrainer(policy, PPOConfig())
        identity = {'environment': env.abi, 'observation_slices': env.observation_slices,
                    'task': 'stage_a_small_hand_motion', 'initial_seed': args.seed}
        if args.checkpoint:
            stored = trainer.load(args.checkpoint)
            if stored['environment'] != identity['environment'] or stored['observation_slices'] != identity['observation_slices']:
                raise ValueError('checkpoint environment ABI mismatch')
        save(args.out / 'config.json', {'identity': identity, 'episode_initialization': env.metadata, 'ppo': asdict(trainer.config)})
        save(args.out / 'initial_state.json', native_state(env.scene))
        properties = env.scene.gym.get_actor_dof_properties(env.scene.env, env.scene.human)
        save(args.out / 'native_properties.json', {
            'guitar': env.scene.mass_properties,
            'joint_names': env.scene.names,
            'PD_properties': [{key: row[key].item() for key in properties.dtype.names} for row in properties],
            'scalar_PD_kp': env.controller.kp.tolist(), 'scalar_PD_kd': env.controller.kd.tolist(),
        })
        initial_parameters = {k: v.detach().clone() for k, v in policy.state_dict().items()}
        if args.mode == 'train':
            candidate_checkpoint = args.out / 'checkpoint_0000.pt'
            trainer.save(candidate_checkpoint, metadata=identity)
            latest_checkpoint = candidate_checkpoint
        else:
            recorder = GymTrialRecording(env.scene, args.out)
            recorder.capture()

        episode_reward = episode_cost = 0.
        episode_steps = 0
        budget = args.updates if args.mode == 'train' else 1
        with (args.out / 'transitions.jsonl').open('x') as transitions, (args.out / 'metrics.jsonl').open('x') as log, (args.out / 'commands.jsonl').open('x') as commands:
            for update in range(budget):
                buffer = {}
                rollout_reward = rollout_cost = 0.
                for _ in range(args.rollout_steps if args.mode == 'train' else 100000):
                    observation = torch.as_tensor(obs, dtype=torch.float32, device=args.device).unsqueeze(0)
                    with torch.no_grad():
                        output = policy.act(observation, deterministic=args.mode != 'train')
                    action = output['action'][0].cpu().numpy()
                    if args.mode == 'baseline':
                        action = np.zeros(54, dtype=np.float32)
                    last_attempt = {'control_attempt': steps+1, 'episode': episodes, 'episode_seed': env.seed,
                                    'physics_step_before': env.scene.steps, 'action54': action.tolist()}
                    commands.write(json.dumps(last_attempt, allow_nan=False) + '\n')
                    commands.flush()
                    active_scene = env.scene
                    try:
                        next_obs, reward, cost, terminated, truncated, info = env.step(action)
                    finally:
                        last_attempt['physics_step_after'] = active_scene.steps
                    steps += 1
                    episode_steps += 1
                    rollout_reward += reward
                    rollout_cost += cost
                    episode_reward += reward
                    episode_cost += cost
                    # Bootstrap the final observation before reset, including time limits.
                    with torch.no_grad():
                        nxt = policy.act(torch.as_tensor(next_obs, dtype=torch.float32, device=args.device).unsqueeze(0), deterministic=True)
                    if args.mode == 'train':
                        row = dict(obs=observation, latent=output['latent'], logp=output['logp'],
                                   reward_value=output['reward_value'], cost_value=output['cost_value'],
                                   next_reward_value=nxt['reward_value'], next_cost_value=nxt['cost_value'])
                        row.update({k: torch.tensor([v], device=args.device) for k, v in dict(
                            reward=float(reward), cost=float(cost), terminated=bool(terminated), truncated=bool(truncated)).items()})
                        for key, value in row.items():
                            buffer.setdefault(key, []).append(value)
                    transitions.write(json.dumps(dict(step=steps, episode=episodes, reward=float(reward),
                        cost=float(cost), terminated=bool(terminated), truncated=bool(truncated), info=info), allow_nan=False) + '\n')
                    if recorder and (env.scene.steps % recorder.interval == 0 or terminated or truncated):
                        recorder.capture()
                    obs = next_obs
                    if terminated or truncated:
                        summary = dict(kind='episode', episode=episodes, steps=episode_steps,
                                       reward=episode_reward, cost=episode_cost,
                                       terminated=bool(terminated), truncated=bool(truncated),
                                       initialization=env.metadata, info=info)
                        log.write(json.dumps(summary, allow_nan=False) + '\n')
                        log.flush()
                        episodes += 1
                        all_forbidden.extend(env.scene.forbidden_calls)
                        if args.mode != 'train':
                            break
                        obs = env.reset(seed=args.seed + episodes)
                        episode_reward = episode_cost = 0.
                        episode_steps = 0
                if args.mode == 'train':
                    measured = trainer.update({key: torch.stack(value) for key, value in buffer.items()})
                    measured.update(kind='update', update=trainer.updates, transitions=steps,
                                    reward_mean=rollout_reward/args.rollout_steps,
                                    cost_mean=rollout_cost/args.rollout_steps,
                                    elapsed_seconds=time.monotonic()-start)
                    metrics.append(measured)
                    log.write(json.dumps(measured, allow_nan=False) + '\n')
                    log.flush()
                    transitions.flush()
                    print(json.dumps(measured, allow_nan=False), flush=True)
                    if trainer.updates % args.save_every == 0 or update+1 == budget:
                        candidate_checkpoint = args.out / ('checkpoint_%04d.pt' % trainer.updates)
                        trainer.save(candidate_checkpoint, metadata=identity)
                        latest_checkpoint = candidate_checkpoint
    except BaseException as error:
        failure = {'type': type(error).__name__, 'message': str(error), 'traceback': traceback.format_exc(),
                   'diagnostic': getattr(error, 'diagnostic', None), 'last_attempt': last_attempt}
        if trainer is not None and args.mode == 'train':
            candidate_checkpoint = args.out / ('fault_checkpoint_%04d.pt' % trainer.updates)
            try:
                trainer.save(candidate_checkpoint, metadata=dict(identity, fault=failure, physical_resume='new episode required'))
                fault_checkpoint = candidate_checkpoint
            except BaseException as save_error:
                checkpoint_save_error = {'type': type(save_error).__name__, 'message': str(save_error)}
    finally:
        last_control_physics_steps = (last_attempt['physics_step_after']-last_attempt['physics_step_before']) if last_attempt and 'physics_step_after' in last_attempt else None
        forbidden = all_forbidden + (list(env.scene.forbidden_calls) if env and env.scene else [])
        if env and env.scene:
            try:
                save(args.out / 'final_state.json', native_state(env.scene))
                if recorder and recorder.frames[-1]['physics_step'] != env.scene.steps:
                    recorder.capture()
            except BaseException as error:
                failure = failure or {'type': type(error).__name__, 'message': str(error)}
            env.close()
        if recorder:
            try:
                videos = recorder.encode()
            except BaseException as error:
                failure = failure or {'type': type(error).__name__, 'message': str(error)}
        changed = [name for name, digest in hashes.items() if not Path(name).is_file() or sha(name) != digest]
        parameter_delta = None
        if trainer is not None and initial_parameters is not None:
            parameter_delta = max(float((trainer.policy.state_dict()[key]-value).abs().max()) for key, value in initial_parameters.items())
        save(args.out / 'report.json', {
            'completed': failure is None and not changed and not forbidden,
            'failure': failure, 'changed_inputs': changed, 'forbidden_calls': forbidden,
            'mode': args.mode, 'training_updates': trainer.updates if trainer and args.mode == 'train' else 0,
            'latest_regular_checkpoint': str(latest_checkpoint) if latest_checkpoint else None,
            'fault_checkpoint': str(fault_checkpoint) if fault_checkpoint else None,
            'checkpoint_save_error': checkpoint_save_error,
            'collected_not_in_completed_update': steps-trainer.updates*args.rollout_steps if trainer and args.mode == 'train' else 0,
            'loaded_checkpoint': str(args.checkpoint.resolve()) if args.checkpoint else None,
            'last_control_physics_steps': last_control_physics_steps,
            'collected_control_steps': steps, 'finished_episodes': episodes,
            'parameter_max_abs_change': parameter_delta, 'videos': videos,
            'elapsed_seconds': time.monotonic()-start,
            'old_policy_loaded': False, 'musical_success_evaluated': False,
            'loaded_project_python_modules': {
                name: str(Path(module.__file__).resolve()) for name, module in list(sys.modules.items())
                if getattr(module, '__file__', None) and str(module.__file__).endswith('.py')
                and project in Path(module.__file__).resolve().parents
            },
        })
    if failure or changed or forbidden:
        raise RuntimeError(failure or {'changed_inputs': changed, 'forbidden_calls': forbidden})


if __name__ == '__main__':
    main()
