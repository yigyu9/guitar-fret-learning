"""Bounded training-only rejection of uncertain v5 Jacobian rollouts."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import sys
import time
import traceback

from .run_v5 import sha, save


def emit(stream, record):
    stream.write(json.dumps(record, allow_nan=False) + '\n')
    stream.flush()


class StepFault(Exception):
    def __init__(self, error):
        self.error = error


def collect_rollout(env, policy, obs, rollout_steps, device, state, command_sink, transition_sink, error_type=()):
    """Collect without catching faults; caller must discard this entire buffer on error."""
    import torch
    buffer = {}
    state['rollout_valid_controls'] = 0
    for index in range(rollout_steps):
        if state['attempted_controls'] >= state['attempt_cap']:
            raise RuntimeError('attempted control budget exhausted')
        observation = torch.as_tensor(obs, dtype=torch.float32, device=device).unsqueeze(0)
        with torch.no_grad():
            output = policy.act(observation)
        action = output['action'][0].cpu().numpy()
        state['attempted_controls'] += 1
        command = dict(rollout_id=state['rollout_id'], rollout_index=index,
                       control_attempt=state['attempted_controls'], episode_seed=env.seed,
                       physics_step_before=env.scene.steps, action54=action.tolist())
        state['last_attempt'] = command
        command_sink(command)
        try:
            next_obs, reward, cost, terminated, truncated, info = env.step(action)
        except error_type as error:
            raise StepFault(error) from error
        finally:
            command['physics_step_after'] = env.scene.steps
        state['valid_controls'] += 1
        state['rollout_valid_controls'] += 1
        with torch.no_grad():
            nxt = policy.act(torch.as_tensor(next_obs, dtype=torch.float32, device=device).unsqueeze(0), deterministic=True)
        row = dict(obs=observation, latent=output['latent'], logp=output['logp'],
                   reward_value=output['reward_value'], cost_value=output['cost_value'],
                   next_reward_value=nxt['reward_value'], next_cost_value=nxt['cost_value'])
        row.update({k: torch.tensor([v], device=device) for k, v in dict(reward=float(reward),
            cost=float(cost), terminated=bool(terminated), truncated=bool(truncated)).items()})
        for key, value in row.items():
            buffer.setdefault(key, []).append(value)
        transition_sink(dict(rollout_id=state['rollout_id'], control_attempt=state['attempted_controls'],
            episode_seed=env.seed, reward=float(reward), cost=float(cost), terminated=bool(terminated),
            truncated=bool(truncated), info=info, acceptance='see rollouts.jsonl'))
        obs = next_obs
        if terminated or truncated:
            state['next_seed'] += 1
            state['finished_episodes'] += 1
            state['forbidden_calls'].extend(env.scene.forbidden_calls)
            obs = env.reset(seed=state['next_seed'])
    return {key: torch.stack(value) for key, value in buffer.items()}, obs


def finite_tree(value):
    import math
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(v) for v in value)
    if isinstance(value, (float, int)):
        return math.isfinite(value)
    return True


def recovery_guard(env, native):
    return dict(no_forbidden_calls=not env.scene.forbidden_calls,
        fixed_lower_unchanged=all(native['human_body_states'][i] == env.initial['human_body_states'][i] for i in env.fixed),
        all_native_finite=finite_tree(native),
        joint_speed_within_50=all(abs(row['vel']) <= 50 for row in native['human_dof_states']))


def train_loop(env, trainer, obs, state, target_updates, rollout_steps, device,
               error_type, command_sink, transition_sink, rollout_sink, reject, accepted):
    while trainer.updates < target_updates:
        state['rollout_id'] += 1
        start_attempt = state['attempted_controls']
        try:
            buffer, obs = collect_rollout(env, trainer.policy, obs, rollout_steps, device, state, command_sink, transition_sink, error_type)
        except StepFault as step_fault:
            error = step_fault.error
            state['rejected_rollouts'] += 1
            state['discarded_controls'] += state['rollout_valid_controls']
            record = dict(rollout_id=state['rollout_id'], status='rejected',
                attempted_controls=state['attempted_controls']-start_attempt,
                discarded_valid_controls=state['rollout_valid_controls'], ppo_updated=False)
            rollout_sink(record)
            reject(error, record)
            if state['rejected_rollouts'] + state['prior_rejected_rollouts'] >= state['max_rejected_rollouts']:
                raise RuntimeError('rejected rollout budget exhausted') from error
            state['forbidden_calls'].extend(env.scene.forbidden_calls)
            state['next_seed'] += 1
            obs = env.reset(seed=state['next_seed'])
            continue
        metrics = trainer.update(buffer)
        state['accepted_ppo_steps'] += rollout_steps
        record = dict(rollout_id=state['rollout_id'], status='accepted',
            attempted_controls=state['attempted_controls']-start_attempt,
            accepted_controls=rollout_steps, ppo_updated=True, update=trainer.updates, metrics=metrics)
        rollout_sink(record)
        accepted(record)
    return obs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=125)
    parser.add_argument('--target-updates', type=int, default=64)
    parser.add_argument('--rollout-steps', type=int, default=256)
    parser.add_argument('--max-rejected-rollouts', type=int, default=8)
    parser.add_argument('--prior-rejected-rollouts', type=int, default=1)
    parser.add_argument('--save-every', type=int, default=4)
    parser.add_argument('--device', choices=('cpu', 'cuda'), default='cuda')
    args = parser.parse_args()
    if min(args.target_updates, args.rollout_steps, args.max_rejected_rollouts, args.save_every) < 1 or args.rollout_steps != 256 or args.max_rejected_rollouts > 8 or not 0 <= args.prior_rejected_rollouts < args.max_rejected_rollouts:
        parser.error('positive budgets required; rollout steps must be256; rejection limit at most8')
    args.out = args.out.resolve()
    args.checkpoint = args.checkpoint.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    import isaacgym  # noqa: F401: must precede torch
    from .environment_v5 import FreshGuitarEnvironment, JacobianConsistencyError, collect_inputs
    from .policy import Policy
    from .ppo import PPOConfig, PPOTrainer
    from ..run_joint_hold import native_state
    import torch
    torch.set_num_threads(1)
    project = Path(__file__).resolve().parents[2]
    hashes = collect_inputs()
    if not isinstance(hashes, dict):
        hashes = {str(Path(p).resolve()): sha(p) for p in hashes}
    for path in (Path(__file__).resolve(), Path(__file__).with_name('launch_recovery_v1.sh'), args.checkpoint):
        hashes[str(path)] = sha(path)
    for name in hashes:
        path = Path(name)
        if path.suffix in ('.py', '.sh') and project in path.parents:
            target = args.out/'source_before'/path.relative_to(project)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    save(args.out/'attempt.json', dict(arguments={k:str(v) if isinstance(v, Path) else v for k,v in vars(args).items()},
        input_sha256=hashes, started_unix=time.time(), old_policy_loaded=False,
        recovery='discard entire uncertain rollout; strict v5 physics unchanged; training only; selection-biased accepted rollouts, not standard unbiased PPO or safety guarantee'))
    env = trainer = None
    failure = None
    latest = fault_checkpoint = None
    identity = None
    source_control_accounting = None
    initial_updates = None
    initial_parameters = None
    start = time.monotonic()
    state = dict(rollout_id=0, attempted_controls=0, valid_controls=0, discarded_controls=0,
        accepted_ppo_steps=0, rejected_rollouts=0, rollout_valid_controls=0, finished_episodes=0,
        next_seed=args.seed, forbidden_calls=[], max_rejected_rollouts=args.max_rejected_rollouts,
        last_attempt=None, attempt_cap=0, prior_rejected_rollouts=args.prior_rejected_rollouts)
    try:
        env = FreshGuitarEnvironment(recording=False, seed=args.seed)
        obs = env.reset(seed=args.seed)
        trainer = PPOTrainer(Policy(env.observation_dim).to(args.device), PPOConfig())
        # Validate own exact schema and metadata before loading any model/optimizer/RNG.
        payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
        metadata = payload.get('metadata', {})
        if payload.get('identity') != trainer._identity():
            raise ValueError('checkpoint schema/config mismatch')
        if metadata.get('environment') != env.abi or metadata.get('observation_slices') != env.observation_slices or metadata.get('task') != 'stage_a_small_hand_motion' or metadata.get('initial_seed') != 101:
            raise ValueError('checkpoint environment ABI/task/initial seed mismatch')
        if 'fault' in metadata and metadata['fault'].get('type') != 'JacobianConsistencyError':
            raise ValueError('only typed Jacobian fault checkpoint may resume')
        if not all(torch.isfinite(v).all() for v in payload['model'].values()):
            raise ValueError('nonfinite source model')
        prior_rejections = metadata.get('recovery_total_rejections', args.prior_rejected_rollouts)
        if not isinstance(prior_rejections, int) or not 0 <= prior_rejections < args.max_rejected_rollouts:
            raise ValueError('source rejection budget exhausted or invalid')
        state['prior_rejected_rollouts'] = prior_rejections
        trainer.load(args.checkpoint)
        initial_updates = trainer.updates
        source_last_attempt = metadata.get('fault', {}).get('last_attempt') or {}
        source_attempts = source_last_attempt.get('control_attempt')
        source_control_accounting = dict(accepted_controls=initial_updates*args.rollout_steps,
            valid_controls_before_failed_attempt=source_attempts-1 if source_attempts is not None else None,
            discarded_valid_controls=(source_attempts-1-initial_updates*args.rollout_steps) if source_attempts is not None else None,
            note='source counters separate from this process; source fault attempted command did not produce a valid transition')
        if not 0 <= initial_updates < args.target_updates:
            raise ValueError('target updates must exceed source completed updates')
        state['attempt_cap'] = (args.target_updates-initial_updates+args.max_rejected_rollouts-state['prior_rejected_rollouts'])*args.rollout_steps
        identity = {key: metadata[key] for key in ('environment','observation_slices','task','initial_seed')}
        identity.update(current_process_seed=args.seed, resume_source=str(args.checkpoint), physical_resume='new episode required')
        initial_parameters = {k:v.detach().clone() for k,v in trainer.policy.state_dict().items()}
        save(args.out/'config.json', dict(identity=identity, ppo=asdict(trainer.config), episode_initialization=env.metadata,
            initial_updates=initial_updates, target_updates=args.target_updates, attempted_controls_cap=state['attempt_cap']))
        save(args.out/'initial_state.json', native_state(env.scene))
        properties = env.scene.gym.get_actor_dof_properties(env.scene.env, env.scene.human)
        save(args.out/'native_properties.json', dict(guitar=env.scene.mass_properties, joint_names=env.scene.names,
            PD_properties=[{key:row[key].item() for key in properties.dtype.names} for row in properties],
            scalar_PD_kp=env.controller.kp.tolist(), scalar_PD_kd=env.controller.kd.tolist()))
        with (args.out/'commands.jsonl').open('x') as commands, (args.out/'transitions.jsonl').open('x') as transitions, (args.out/'rollouts.jsonl').open('x') as rollouts, (args.out/'metrics.jsonl').open('x') as metrics:
            def reject(error, record):
                nonlocal fault_checkpoint
                native = native_state(env.scene)
                guards = recovery_guard(env, native)
                fault = dict(type=type(error).__name__, message=str(error), diagnostic=error.diagnostic,
                    last_attempt=state['last_attempt'], native_state=native, recovery_guards=guards,
                    counters=dict(state), rollout=record)
                save(args.out/('rejection_%02d.json'%state['rejected_rollouts']), fault)
                candidate = args.out/('rejection_%02d_checkpoint_%04d.pt'%(state['rejected_rollouts'],trainer.updates))
                trainer.save(candidate, metadata=dict(identity, fault=fault, recovery_total_rejections=state['prior_rejected_rollouts']+state['rejected_rollouts']))
                fault_checkpoint = candidate
                if not all(guards.values()) or state['forbidden_calls']:
                    raise RuntimeError('Jacobian fault recovery safety guard failed') from error
            def accepted(record):
                nonlocal latest
                emit(metrics, record)
                print(json.dumps(record, allow_nan=False), flush=True)
                if trainer.updates % args.save_every == 0 or trainer.updates == args.target_updates:
                    candidate = args.out/('checkpoint_%04d.pt'%trainer.updates)
                    trainer.save(candidate, metadata=dict(identity, recovery_total_rejections=state['prior_rejected_rollouts']+state['rejected_rollouts']))
                    latest = candidate
            obs = train_loop(env, trainer, obs, state, args.target_updates, args.rollout_steps, args.device,
                JacobianConsistencyError, lambda row:emit(commands,row), lambda row:emit(transitions,row),
                lambda row:emit(rollouts,row), reject, accepted)
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc(),
            diagnostic=getattr(error,'diagnostic',None), last_attempt=state['last_attempt'])
        if trainer is not None and identity is not None:
            try:
                candidate=args.out/('fatal_checkpoint_%04d.pt'%trainer.updates)
                trainer.save(candidate, metadata=dict(identity, fault=failure, recovery_total_rejections=state['prior_rejected_rollouts']+state['rejected_rollouts']))
                fault_checkpoint=candidate
            except BaseException as save_error:
                failure['checkpoint_save_error']=str(save_error)
    finally:
        if env and env.scene:
            try:
                save(args.out/'final_state.json', native_state(env.scene))
                state['forbidden_calls'].extend(env.scene.forbidden_calls)
            except BaseException as error:
                failure=failure or dict(type=type(error).__name__,message=str(error))
            env.close()
        state['total_rejected_rollouts'] = state['prior_rejected_rollouts']+state['rejected_rollouts']
        state['failed_control_attempts'] = state['attempted_controls']-state['valid_controls']
        state['pending_valid_controls'] = state['valid_controls']-state['accepted_ppo_steps']-state['discarded_controls']
        last = state['last_attempt']
        state['last_attempt_physics_steps'] = last.get('physics_step_after',last['physics_step_before'])-last['physics_step_before'] if last else None
        changed=[name for name,digest in hashes.items() if not Path(name).is_file() or sha(name)!=digest]
        final_updates=trainer.updates if trainer else None
        delta=max(float((trainer.policy.state_dict()[k]-v).abs().max()) for k,v in initial_parameters.items()) if initial_parameters else None
        save(args.out/'report.json', dict(completed=failure is None and not changed and not state['forbidden_calls'],
            failure=failure, changed_inputs=changed, counters=state, source_control_accounting=source_control_accounting, initial_updates=initial_updates,
            performed_updates=final_updates-initial_updates if initial_updates is not None else 0,
            final_updates=final_updates, target_updates=args.target_updates,
            latest_regular_checkpoint=str(latest) if latest else None, fault_checkpoint=str(fault_checkpoint) if fault_checkpoint else None,
            resume_source=str(args.checkpoint), original_initial_seed=101, current_process_seed=args.seed,
            parameter_max_abs_change=delta, elapsed_seconds=time.monotonic()-start,
            old_policy_loaded=False, musical_success_evaluated=False,
            loaded_project_python_modules={name:str(Path(module.__file__).resolve()) for name,module in list(sys.modules.items())
                if getattr(module,'__file__',None) and str(module.__file__).endswith('.py') and project in Path(module.__file__).resolve().parents}))
    if failure or changed or state['forbidden_calls']:
        raise RuntimeError(failure or dict(changed_inputs=changed,forbidden_calls=state['forbidden_calls']))


if __name__ == '__main__':
    main()
