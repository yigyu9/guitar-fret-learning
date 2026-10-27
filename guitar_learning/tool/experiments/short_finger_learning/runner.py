"""Fresh-only short-task PPO and strict same-contract evaluation."""
import copy
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import torch

from guitar_learning.training import json_io
from guitar_learning.training.recording import write, project_source_paths, digest
from guitar_learning.training.finger_skill_runner import _pins, _validate_pins
from guitar_learning.training.launch_settings import settings_document
from guitar_learning.training.finger_decisions import DecisionCollector
from guitar_learning.training.decision_ppo import DecisionPPOTrainer
from guitar_learning.training.ppo import PPOConfig
from guitar_learning.training.gpu_pool import FIELDS
from guitar_learning.song.task import make_task
from .spec import SCHEMA, read_teacher, diagnostic_spec, read_reference
from .runtime import ShortPool, ShortPolicy
from guitar_learning.core.control import ACTIVE_NAMES
from guitar_learning.tool.validation.press_acquisition import trajectory_actions


def make_settings(args):
    settings = settings_document('left', learning_family='finger-skill', physics='gpu',
        device='cuda:0', song=args.song, size=args.size, seed=args.seed,
        num_envs=args.num_envs, horizon=args.horizon, updates=args.updates,
        checkpoint_every=args.save_every)
    settings['initial_std'] = float(args.initial_std)
    teacher = read_teacher(args.teacher)
    task = make_task(settings['song_training']['bundle'], pre_roll_s=3., tail_s=.5)
    settings['song']['finger_action_mode'] = args.mode
    settings['song']['short_learning'] = diagnostic_spec(task, teacher, args.mode, args.initial_std)
    settings['simple_start']['initialization'] = 'diagnostic fresh only; no resume or actor transfer'
    return settings


def compact_episode(row, spec):
    index = spec['view']['source_index']
    note = row['left_note_ledger']['values']
    duration = spec['view']['source_target']['end_s']-spec['view']['source_target']['onset_s']
    result = {key: copy.deepcopy(row[key]) for key in (
        'env_id', 'valid', 'reason', 'steps', 'reward', 'cost', 'failure_reasons',
        'termination', 'cost_components', 'reward_components')}
    result.update(target_id=spec['teacher']['source_target_id'], selected_target_count=1,
        achieved=bool(note['left'][index]), clean_fraction=min(1., note['clean'][index]/duration),
        audible_wrong_fraction=min(1., note['wrong'][index]/duration),
        missing_fraction=min(1., note['missing'][index]/duration),
        source_time_s=row['finger_skill']['source_task_time_s'],
        note={key: note[key][index] for key in ('clean', 'wrong', 'missing', 'best_clean_streak',
            'contact_progress', 'performance_paid', 'performance_settled')},
        wrist=row['wrist_termination'])
    motion = row['left_finger_motion']
    result['angles'] = dict(joint_names=motion['joint_names'], sampling_hz=60,
        endpoint_samples=motion['endpoint_samples'], values={key: motion['values'][key] for key in (
            'actual_range_rad', 'target_range_rad', 'tracking_error_rms_rad',
            'tracking_error_max_abs_rad', 'actual_native_limit_fraction', 'target_native_limit_fraction')})
    return result


def summary(rows):
    if not rows:
        return dict(episodes=0)
    return dict(episodes=len(rows), denominator='all assigned evaluation attempts, including failures',
        achieved_fraction=sum(r['achieved'] for r in rows)/len(rows),
        mean_clean_fraction=sum(r['clean_fraction'] for r in rows)/len(rows),
        mean_audible_wrong_fraction=sum(r['audible_wrong_fraction'] for r in rows)/len(rows),
        physical_failure_fraction=sum(r['termination']['physical_failure'] for r in rows)/len(rows),
        wrist_failure_fraction=sum(r['termination']['wrist_failure'] for r in rows)/len(rows),
        any_failure_fraction=sum(r['reason'] == 'terminal_failure' for r in rows)/len(rows))


def run(args):
    out = Path(args.out).resolve()
    payload = None
    if args.command == 'evaluate':
        payload = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
        metadata = payload.get('metadata', {})
        if metadata.get('schema') != SCHEMA or not metadata.get('input_pins'):
            raise ValueError('Own sealed short-learning checkpoint required')
        _validate_pins(metadata)
        settings = copy.deepcopy(metadata['settings'])
        if args.control == 'random' and payload.get('updates') != 0:
            raise ValueError('Random-action comparison requires own fresh initial checkpoint')
        # Check the external teacher evidence again, not only the JSON bytes.
        spec = settings['song']['short_learning']
        if read_teacher(spec['teacher']['input_path']) != spec['teacher']:
            raise ValueError('Teacher inputs differ from checkpoint')
    else:
        settings = make_settings(args)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    spec = settings['song']['short_learning']
    teacher = spec['teacher']
    extra = [Path(teacher['input_path']), *map(Path, teacher['source_evidence'])]
    if payload is not None:
        extra.append(Path(args.checkpoint).resolve())
        if args.reference:
            reference = read_reference(args.reference, spec)
            extra.extend([Path(args.reference).resolve(), *map(Path, reference['source_evidence'])])
    pins = _pins(settings, out, extra)
    write(out/'inputs_before.json', pins)
    write(out/'invocation.json', dict(argv=sys.argv, command=args.command,
        control=getattr(args, 'control', None), reference=getattr(args, 'reference', None), evaluation_episodes=getattr(args, 'episodes', None)))
    random.seed(settings['seed']); np.random.seed(settings['seed']); torch.manual_seed(settings['seed'])
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool = None
    completed = False
    failure = None
    started = time.monotonic()
    try:
        pool = ShortPool(settings, out)
        write(out/'training_contract.json', pool.contract)
        policy = ShortPolicy(contract=pool.contract, size=settings['size']).to(settings['device'])
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        if pool.environment.approach_gamma != trainer.config.gamma:
            raise ValueError('Reward shaping and PPO gamma mismatch')
        metadata = dict(schema=SCHEMA, settings=settings, input_pins=pins,
            scope=spec['result_scope'], fresh_only=True)
        if payload is None:
            _train(pool, policy, trainer, settings, metadata, out)
        else:
            trainer.load(args.checkpoint)  # Complete architecture/config equality; no relaxed state load.
            _evaluate(pool, policy, spec, args, out)
        completed = True
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        if pool is not None:
            pool.close()
        missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins))
        changed = [path for path, sha in pins.items()
                   if not Path(path).is_file() or digest(path) != sha]
        write(out/'inputs_after.json', dict(verified=not changed and not missing,
            changed_paths=changed, unpinned_project_sources=missing, input_pins=pins))
        write(out/'report.json', dict(schema=SCHEMA, completed=completed and not changed and not missing,
            failure=failure, changed_inputs=changed, unpinned_project_sources=missing,
            closed=pool is None or pool.closed, wall_s=time.monotonic()-started,
            result_scope=spec['result_scope']))
        if failure is None and (changed or missing):
            raise RuntimeError('Diagnostic source seal failed')


def _train(pool, policy, trainer, settings, metadata, out):
    collector = DecisionCollector(policy, pool, gamma=trainer.config.gamma, cost_gamma=trainer.config.cost_gamma)
    spec = settings['song']['short_learning']
    trainer.save(out/'initial.pt', metadata=metadata)
    with (out/'metrics.jsonl').open('x') as metrics, (out/'episodes.jsonl').open('x') as episodes:
        for update in range(settings['updates']):
            pool.environment.reset_reward_window()
            buffer, rows = collector.collect(settings['horizon'])
            result = trainer.update(buffer, rows)
            transitions = settings['horizon']*settings['num_envs']
            pool.set_training_progress((update+1)*transitions)
            compact = [compact_episode(row, spec) for row in rows]
            for row in compact:
                episodes.write(json_io.dumps(dict(update=update+1, **row), allow_nan=False)+'\n')
            result.update(update=update+1, transitions=transitions, total_transitions=(update+1)*transitions,
                reward_component_means=pool.environment.reward_window_means(transitions),
                mean_reward=float(buffer['reward'][buffer['valid']].mean()),
                mean_failure_cost=float(buffer['cost'][buffer['valid']].mean()), episodes=summary(compact),
                mean_scope='all raw60Hz transitions; K1; preparation included')
            metrics.write(json_io.dumps(result, allow_nan=False)+'\n')
            metrics.flush(); episodes.flush()
            if (update+1) % settings['checkpoint_every'] == 0 and update+1 < settings['updates']:
                trainer.save(out/('evaluation_%06d.pt'%(update+1)), metadata=metadata)
            print(json_io.dumps(dict(update=update+1, episodes=len(rows), mean_reward=result['mean_reward'])), flush=True)
        _validate_pins(metadata)
        trainer.save(out/'final.pt', metadata=metadata)


@torch.no_grad()
def _evaluate(pool, policy, spec, args, out):
    # Predetermined per-environment quotas avoid selecting only fast completions.
    quota = [args.episodes//pool.num_envs+int(i < args.episodes%pool.num_envs) for i in range(pool.num_envs)]
    counts = [0]*pool.num_envs
    rows, trace = [], []
    observation = pool.observation
    max_ticks = spec['view']['duration_ticks']*max(quota)
    pool.environment.set_evaluation(True, full_song=False)
    reference_goal = None
    if args.control == 'reference':
        reference = read_reference(args.reference, spec)
        reference_goal = pool.teacher_reference.clone()
        for name, value in reference['selected_targets_rad'].items():
            reference_goal[ACTIVE_NAMES.index(name)] = value
        if bool(((reference_goal < pool.controller.action_low) | (reference_goal > pool.controller.action_high)).any()):
            raise ValueError('Scripted reference exceeds controller bounds')
    for _ in range(max_ticks):
        action = policy.act(*(observation[key] for key in FIELDS), deterministic=args.control != 'random')['action']
        if args.control == 'zero':
            action.zero_()
        elif args.control == 'reference':
            fraction = ((pool.environment._local_time()+1/60)/reference['ramp_s']).clamp(0,1).to(action)
            desired = pool.teacher_reference+fraction[:,None]*(reference_goal-pool.teacher_reference)
            action = trajectory_actions(desired, pool.controller.target[:,pool.controller.active],
                pool.teacher_reference, pool.controller.action_low, pool.controller.action_high,
                pool.incremental_mask, max_speed=4.)
        observation, _, _, terminated, truncated, finished = pool.step(action)
        if counts[0] == 0:
            scene, env = pool.scene, pool.environment
            trace.append(dict(time_s=float(env._local_time()[0]), source_time_s=float(env._score_time()[0]),
                policy_action=pool.last_policy_action[0].cpu().numpy().copy(),
                executed_action=pool.last_executed_action[0].cpu().numpy().copy(),
                q=scene.q[0].cpu().numpy().copy(), target=scene.target[0].cpu().numpy().copy(),
                body_state=scene.body_state[0].cpu().numpy().copy(),
                candidate=bool(env.candidate[0, env.selected_index]), wrong=bool(env.wrong[0, env.selected_index]),
                surface_distance_m=float(env.surface_distance[0, env.selected_index]),
                surface_height_m=float(env.surface_height[0, env.selected_index]),
                net_body_force_n=scene.snapshot()['contact_force'][0].cpu().numpy().copy(),
                wrist_delta=env.guide['delta'][0].cpu().numpy().copy(),
                wrist_feedback_active=bool(pool.last_wrist_feedback['active'][0]),
                wrist_pose_error_world=pool.last_wrist_feedback['pose_error_world'][0].cpu().numpy().copy(),
                wrist_requested_delta_rad=pool.last_wrist_feedback['requested_delta_rad'][0].cpu().numpy().copy(),
                wrist_requested_arm_rad=pool.last_wrist_feedback['requested_arm_rad'][0].cpu().numpy().copy(),
                wrist_goal_G_m=pool.last_wrist_feedback['position_goal_G_m'][0].cpu().numpy().copy(),
                wrist_goal_G_xyzw=pool.last_wrist_feedback['quaternion_goal_G_xyzw'][0].cpu().numpy().copy()))
        for row in finished:
            index = row['env_id']
            if counts[index] < quota[index]:
                rows.append(compact_episode(row, spec)); counts[index] += 1
        if counts == quota:
            break
        ids = (terminated | truncated).nonzero().flatten()
        if ids.numel():
            observation = pool.reset(ids)[0]
    if counts != quota:
        raise RuntimeError('Evaluation did not finish predetermined attempt quotas')
    write(out/'evaluation.json', dict(schema=SCHEMA, condition=args.control, policy_performance=args.control == 'policy',
        assigned_quotas=quota, summary=summary(rows), episodes=rows, scope=spec['result_scope']))
    if trace:
        np.savez_compressed(out/'trace_env0_episode0.npz', **{k: np.asarray([r[k] for r in trace]) for k in trace[0]})
        write(out/'trace_metadata.json', dict(scope='env0 first attempt;60Hz; includes failure endpoint',
            joint_names=pool.scene.names, body_names=pool.scene.metadata['body_names'],
            learned_action_indices=spec['learned_action_indices'], wrist_control=spec['wrist_control'],
            wrist_pose_error_scope='pre-control actual wrist versus next target pose; world xyz meters then0.1*world rotation-vector radians',
            wrist_requested_delta_scope='bounded DLS correction before combined requested-target rate/bound clipping'))
