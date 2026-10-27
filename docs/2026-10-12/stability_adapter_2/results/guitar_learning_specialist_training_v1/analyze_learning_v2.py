"""Read-only streaming analysis; final artifacts require closed specialist runs.

Usage: python analyze_learning_v2.py [--final]
Without --final only provisional prefix counts are printed, never saved.
"""
import argparse
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import torch

PHASE = Path(__file__).resolve().parent
ROOT = PHASE.parents[4]
sys.path.insert(0, str(ROOT))
torch.set_num_threads(1)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            digest.update(block)
    return digest.hexdigest()


def metric(values):
    return (dict(count=len(values), mean=float(np.mean(values)), min=float(min(values)),
                 max=float(max(values))) if values else dict(count=0, mean=None, min=None, max=None))


def bucket():
    return dict(count=0, reward=0., cost=0., terms=collections.Counter(), episodes=[],
                failures=collections.Counter(), candidate_endpoints=0, provisional_endpoints=0,
                safety_invalidated_endpoints=0, any_support=0, triple_support=0, both_feet=0,
                guitar_max_m=0., rotation_max_rad=0., foot_max_m=0., joint_speed_max_rad_s=0.,
                metrics=collections.defaultdict(list), action_sum=np.zeros(39),
                action_square_sum=np.zeros(39), action_abs_max=np.zeros(39))


def add(target, info, reward, episode=None):
    target['count'] += 1
    target['reward'] += float(reward)
    target['cost'] += info['cost']
    target['terms'].update(info['reward_terms'])
    target['failures'].update(info['failure_reasons'])
    target['candidate_endpoints'] += int(any(info['fret_candidates'].values()))
    target['provisional_endpoints'] += int(info['specialist']['provisional_success'])
    target['safety_invalidated_endpoints'] += int(info['specialist']['safety_invalidated'])
    stability = info['stability']
    flags = stability['flags']
    target['any_support'] += int(any(flags[:3]))
    target['triple_support'] += int(all(flags[:3]))
    target['both_feet'] += int(all(flags[-2:]))
    target['guitar_max_m'] = max(target['guitar_max_m'], float(np.linalg.norm(stability['guitar_delta_m'])))
    target['rotation_max_rad'] = max(target['rotation_max_rad'], float(np.linalg.norm(stability['guitar_rotation_vector_rad'])))
    target['foot_max_m'] = max(target['foot_max_m'], float(np.linalg.norm(stability['foot_delta_m'], axis=1).max()))
    target['joint_speed_max_rad_s'] = max(target['joint_speed_max_rad_s'], stability['max_joint_speed_rad_s'])
    distance = min(info['goal_distance_m'].values())
    target['metrics']['left_all_m'].append(distance)
    now = info['task_time_s']
    if 1.-1e-9 <= now <= 1.12+1e-9:
        target['metrics']['left_press_to_onset_m'].append(distance)
    if abs(now-67/60.) < 1e-9:
        target['metrics']['left_near_onset_m'].append(distance)
    guide = info.get('pick_guide')
    if guide:
        target['metrics']['right_guide_all_m'].append(guide['distance_m'])
        if guide['sweep_active']:
            target['metrics']['right_sweep_m'].append(guide['distance_m'])
    action = np.asarray(info['debug']['action'])
    assert action.shape == (39,) and np.isfinite(action).all()
    target['action_sum'] += action
    target['action_square_sum'] += action**2
    target['action_abs_max'] = np.maximum(target['action_abs_max'], np.abs(action))
    if episode is not None:
        target['episodes'].append(episode)


def summary(value):
    count = value['count']
    episodes = value['episodes']
    excluded = ('metrics', 'action_sum', 'action_square_sum', 'action_abs_max', 'episodes')
    result = {key: item for key, item in value.items() if key not in excluded}
    result['terms'] = dict(result['terms'])
    result['failures'] = dict(result['failures'])
    result['mean_cost_per_transition'] = value['cost']/count if count else None
    result['mean_reward_per_transition'] = value['reward']/count if count else None
    result['metrics'] = {key: metric(items) for key, items in value['metrics'].items()}
    mean = value['action_sum']/max(1, count)
    result['action_channel_mean'] = mean.tolist()
    result['action_channel_std'] = np.sqrt(np.maximum(value['action_square_sum']/max(1, count)-mean**2, 0.)).tolist()
    result['action_channel_abs_max'] = value['action_abs_max'].tolist()
    result['episode_count'] = len(episodes)
    result['episode_reward_mean'] = metric([episode['reward'] for episode in episodes])['mean']
    result['episode_cost_mean'] = metric([episode['cost'] for episode in episodes])['mean']
    result['episode_reasons'] = dict(collections.Counter(episode['reason'] for episode in episodes))
    result['episode_stage_successes'] = sum(episode['specialist']['stage_success'] for episode in episodes)
    result['episode_provisional_successes'] = sum(episode['specialist']['provisional_success'] for episode in episodes)
    result['episode_physical_failures'] = sum(e['reason'] == 'terminal_failure' for e in episodes)
    result['episode_safety_invalidated'] = sum(episode['specialist']['safety_invalidated'] for episode in episodes)
    result['left'] = dict(valid_s=sum(e['specialist']['left']['valid_s'] for e in episodes),
        longest_dwell_s=max((e['specialist']['left']['longest_dwell_s'] for e in episodes), default=0.),
        **{key: sum(e['specialist']['left'][key] for e in episodes)
           for key in ('acquisitions', 'releases', 'timely_releases')})
    result['right'] = {key: sum(e['specialist']['right'][key] for e in episodes)
        for key in ('geometric_crossings', 'matching_string_direction_crossings', 'duplicate_crossings',
                    'wrong_crossings', 'matched50', 'matched100', 'valid_matched50')}
    result['joint_music'] = {key: sum(e['music'][key] for e in episodes)
        for key in ('matched50', 'matched100', 'held_total_s', 'released_count', 'missed_strict', 'wrong_crossings')}
    return result


def checkpoint_audit(run, role, first_actions, updates):
    from guitar_learning.specialist_policy import SpecialistPolicy
    initial = torch.load(run/'initial.pt', map_location='cpu', weights_only=False)
    final = torch.load(run/'final.pt', map_location='cpu', weights_only=False)
    assert initial['updates'] == 0 and final['updates'] == len(updates)
    architecture = initial['identity']['architecture']
    policy = SpecialistPolicy(architecture['state_dim'], architecture['event_dim'],
        architecture['size'], architecture['contract'], role=role, frozen_partner=False)
    policy.load_state_dict(initial['model'])
    assert initial['identity'] == final['identity']
    inactive_role = 'right' if role == 'left' else 'left'
    active = slice(0, 33) if role == 'left' else slice(33, 39)
    inactive = slice(33, 39) if role == 'left' else slice(0, 33)
    inactive_keys = [key for key in initial['model']
        if key.startswith(('actor_encoders.'+inactive_role+'.', 'actor_heads.'+inactive_role+'.'))]
    assert inactive_keys and all(torch.equal(initial['model'][key], final['model'][key]) for key in inactive_keys)
    assert torch.equal(initial['model']['log_std'][inactive], final['model']['log_std'][inactive])
    finite = all(torch.isfinite(value).all().item() for value in final['model'].values())
    assert finite
    active_changes = {prefix: any(not torch.equal(initial['model'][key], final['model'][key])
        for key in initial['model'] if key.startswith(prefix))
        for prefix in ('actor_encoders.'+role+'.', 'actor_heads.'+role+'.', 'value_encoder.')}
    assert all(active_changes.values())
    names = {id(parameter): name for name, parameter in policy.named_parameters()}
    actor_names = [names[id(parameter)] for parameter in policy.actor_parameters()]
    groups = final['actor_optimizer']['param_groups']
    param_ids = [index for group in groups for index in group['params']]
    assert len(param_ids) == len(actor_names)
    assert not any(name.startswith(('actor_encoders.'+inactive_role+'.', 'actor_heads.'+inactive_role+'.')) for name in actor_names)
    optimizer = final['actor_optimizer']['state']
    assert set(param_ids) == set(optimizer)
    log_std_id = param_ids[actor_names.index('log_std')]
    inactive_moments_zero = all(torch.count_nonzero(optimizer[log_std_id][key][inactive]).item() == 0
                                for key in ('exp_avg', 'exp_avg_sq'))
    assert inactive_moments_zero
    rollout = torch.load(run/'rollout_first.pt', map_location='cpu', weights_only=False)
    action_array = np.asarray(first_actions)
    expected = rollout['latent'].tanh().numpy()
    assert action_array.shape == expected.shape
    error = float(np.max(np.abs(action_array-expected)))
    assert error <= 1e-7
    assert torch.count_nonzero(rollout['latent'][..., inactive]).item() == 0
    assert torch.count_nonzero(rollout['old_mean'][..., inactive]).item() == 0
    assert torch.all(rollout['old_log_std'][..., inactive] == -3.)
    with torch.no_grad():
        # CUDA/CPU reductions can round differently; the original saved latent
        # actions are compared exactly above, distribution evaluation tolerantly.
        flattened = {key: rollout[key].flatten(0, 1) for key in
            ('state', 'events', 'mask', 'priority_events', 'priority_mask', 'latent')}
        result = policy.evaluate(**flattened)
    logp_error = float((result['logp']-rollout['logp'].flatten()).abs().max())
    assert logp_error < 1e-4
    assert torch.allclose(result['mean'], rollout['old_mean'].flatten(0, 1), atol=1e-6, rtol=1e-5)
    std = final['model']['log_std'].clamp(-5, 2).exp()
    return dict(initial_updates=0, final_updates=final['updates'], final_path=str(run/'final.pt'),
        final_sha256=sha(run/'final.pt'), model_finite=finite, inactive_actor_tensors_unchanged=len(inactive_keys),
        inactive_log_std_unchanged=True, inactive_optimizer_moments_zero=inactive_moments_zero,
        actor_optimizer_parameter_count=len(actor_names), active_parameter_groups_changed=active_changes,
        active_std=metric(std[active].tolist()), inactive_stored_std=metric(std[inactive].tolist()),
        inactive_forward_placeholder_std=math.exp(-3.), inactive_forward_placeholder_is_sampled=False,
        first_rollout_action_max_abs_error=error, first_rollout_inactive_latent_zero=True,
        initial_policy_logp_max_abs_cpu_error=logp_error,
        optimizer_steps=sorted({float(optimizer[index]['step']) for index in param_ids}),
        std_scope='pre-tanh normalized Gaussian; active channels sampled, inactive Gaussian is a KL placeholder, not radians')


def analyze(run, role):
    report = read(run/'report.json')
    assert report['completed'] is True
    assert all((run/name).is_file() for name in ('core_report.json', 'persistent_audit.json',
        'specialist_report.json', 'final.pt', 'rollout_first.pt'))
    updates = report['updates']
    count = len(updates)
    assert count > 0
    horizon, workers = report['settings']['horizon'], report['settings']['num_envs']
    assert report['settings']['specialist']['role'] == role
    initialization = read(run/'expert_initialization.json')
    assert initialization == dict(mode='actor_only_warm_start_new_critics_and_optimizers',
                                  transfers=[], strict_resume=None)
    per = [bucket() for _ in range(count+1)]
    groups = {name: bucket() for name in ('committed', 'discarded', 'first_five_updates', 'last_five_updates')}
    pending = [dict(steps=0, reward=0., cost=0., source=None, first_update=None) for _ in range(workers)]
    episodes, first_actions = [], []
    checks = collections.Counter()
    precision_errors = dict(native_episode_vs_float32_reward_sum_max=0.,
        native_episode_vs_float64_cost_sum_max=0.,
        native_episode_vs_float32_collector_reward_max=0.,
        native_episode_vs_float32_collector_cost_max=0.)
    frames = 0
    with gzip.open(run/'transitions.jsonl.gz', 'rt') as stream:
        for frame, line in enumerate(stream):
            row = json.loads(line)
            index = frame//horizon
            assert index <= count
            assert len(row['infos']) == len(row['reward']) == workers
            if frame < horizon:
                first_actions.append([info['debug']['action'] for info in row['infos']])
            for worker, (info, reward, terminated, truncated) in enumerate(zip(
                    row['infos'], row['reward'], row['terminated'], row['truncated'])):
                assert info['specialist']['role'] == role
                specialist = info['specialist']
                safe = not specialist['safety_invalidated']
                criterion = (len(specialist['left']['dwell_targets']) == specialist['left']['target_count']
                             if role == 'left' else specialist['right']['matched50'] == specialist['right']['target_count'])
                assert specialist['provisional_success'] == bool(safe and criterion)
                assert specialist['stage_success'] == bool(safe and criterion and terminated
                    and info['termination_reason'] == 'timeline_complete')
                action = info['debug']['action']
                inactive_action = action[33:] if role == 'left' else action[:33]
                assert all(value == 0. for value in inactive_action)
                checks['inactive_zero_action_transitions'] += 1
                assert abs(float(reward)-sum(info['reward_terms'].values())) < 1e-6
                state = pending[worker]
                if state['steps'] == 0:
                    assert info.get('raw_sample_path')
                    state['source'] = info['raw_sample_path']
                    state['first_update'] = index
                state['steps'] += 1
                state['reward'] += reward
                state['cost'] += info['cost']
                assert abs(info['task_time_s']-state['steps']/60.) < 1e-8
                episode = None
                if 'episode' in info:
                    assert terminated or truncated
                    episode = dict(info['episode'], source_first_transition=state['source'], worker=worker,
                        first_update=state['first_update'], completed_update=index,
                        spans_updates=state['first_update'] != index)
                    assert state['steps'] == episode['steps']
                    precision_errors['native_episode_vs_float32_reward_sum_max'] = max(
                        precision_errors['native_episode_vs_float32_reward_sum_max'], abs(state['reward']-episode['reward']))
                    precision_errors['native_episode_vs_float64_cost_sum_max'] = max(
                        precision_errors['native_episode_vs_float64_cost_sum_max'], abs(state['cost']-episode['cost']))
                    assert math.isclose(state['reward'], episode['reward'], abs_tol=1e-6, rel_tol=1e-6)
                    assert math.isclose(state['cost'], episode['cost'], abs_tol=1e-8, rel_tol=1e-6)
                    assert episode['music'] == info['music']
                    assert episode['specialist'] == info['specialist']
                    episodes.append(episode)
                    checks['episodes_reconstructed_from_all_ticks'] += 1
                    pending[worker] = dict(steps=0, reward=0., cost=0., source=None, first_update=None)
                else:
                    assert not terminated and not truncated
                add(per[index], info, reward, episode)
                add(groups['committed' if index < count else 'discarded'], info, reward, episode)
                if index < min(5, count):
                    add(groups['first_five_updates'], info, reward, episode)
                if max(0, count-5) <= index < count:
                    add(groups['last_five_updates'], info, reward, episode)
            frames += 1
    committed = groups['committed']['count']
    discarded = groups['discarded']['count']
    assert committed == report['transitions'] == count*horizon*workers
    expected_discarded = (report.get('partial_collection') or {}).get('discarded_transitions', 0)
    assert discarded == expected_discarded
    for index, update in enumerate(updates):
        assert update == read(run/('update_%06d.json' % index))
        assert per[index]['count'] == horizon*workers
        assert len(per[index]['episodes']) == len(update['completed_episodes'])
        for reconstructed, logged in zip(per[index]['episodes'], update['completed_episodes']):
            assert reconstructed['steps'] == logged['steps']
            precision_errors['native_episode_vs_float32_collector_reward_max'] = max(
                precision_errors['native_episode_vs_float32_collector_reward_max'], abs(reconstructed['reward']-logged['reward']))
            precision_errors['native_episode_vs_float32_collector_cost_max'] = max(
                precision_errors['native_episode_vs_float32_collector_cost_max'], abs(reconstructed['cost']-logged['cost']))
            assert math.isclose(reconstructed['reward'], logged['reward'], abs_tol=1e-6, rel_tol=1e-6)
            assert math.isclose(reconstructed['cost'], logged['cost'], abs_tol=1e-8, rel_tol=1e-6)
    specialist_report = read(run/'specialist_report.json')
    assert specialist_report['completed_episodes'] == len(episodes)
    assert specialist_report['successful_episodes'] == sum(e['specialist']['stage_success'] for e in episodes)
    ppo_fields = ('analytic_kl', 'max_attempted_kl', 'actor_grad_norm', 'actor_loss',
                  'reward_value_loss', 'cost_value_loss', 'actor_lr', 'cost_weight')
    assert all(math.isfinite(update[key]) for update in updates for key in ppo_fields)
    assert all(update['analytic_kl'] <= report['settings']['ppo']['target_kl'] for update in updates)
    result = dict(run=str(run), role=role, completed=True, stopped=report['stopped'],
        completed_updates=count, frames=frames, committed_transitions=committed,
        discarded_transitions=discarded, unfinished_episodes=pending,
        groups={name: summary(value) for name, value in groups.items()},
        per_update=[dict(update_index=index, committed=index < count, **summary(value))
                    for index, value in enumerate(per) if value['count']],
        completed_episodes=episodes,
        ppo=dict(metrics={key: metric([update[key] for update in updates]) for key in ppo_fields},
                 kl_retries=sum(update['kl_retries'] for update in updates),
                 first={key: updates[0][key] for key in ppo_fields},
                 last={key: updates[-1][key] for key in ppo_fields},
                 actor_grad_norm_scope='last actor minibatch before clipping; not an all-minibatch maximum'),
        checkpoint=checkpoint_audit(run, role, first_actions, updates), checks=dict(checks),
        episode_precision_audit=dict(max_abs_errors=precision_errors,
            reward_atol=1e-6, cost_atol=1e-8, rtol=1e-6,
            sources='native episode is float64; serialized per-tick reward and PPO completed episode reward/cost use float32'),
        scope=dict(geometry='60Hz endpoint marker proxies; no pad distance, pressure, sound certification',
            success='240Hz integrated specialist ledger; full completed episodes counted once at terminal update',
            boundary='episode returns include preceding update ticks; first/last-five transition means use only their own ticks',
            incomplete='unfinished episodes remain separate; their committed transitions are bootstrapped, not discarded',
            comparison='two fresh-seed role runs, no controlled comparison against prior joint training'))
    return result


def provisional():
    result = dict(provisional=True, scope='open gzip prefix; no final artifacts written', roles={})
    for role in ('left', 'right'):
        run = PHASE/(role+'_run_v1')
        frames = 0
        completed = success = provisional_count = candidates = 0
        try:
            with gzip.open(run/'transitions.jsonl.gz', 'rt') as stream:
                for line in stream:
                    row = json.loads(line)
                    frames += 1
                    for info in row['infos']:
                        completed += int('episode' in info)
                        success += int(info.get('episode', {}).get('specialist', {}).get('stage_success', False))
                        provisional_count += int(info['specialist']['provisional_success'])
                        candidates += int(any(info['fret_candidates'].values()))
        except (EOFError, json.JSONDecodeError):
            pass
        result['roles'][role] = dict(frames=frames, completed_episodes=completed,
            stage_successes=success, provisional_endpoints=provisional_count, candidate_endpoints=candidates,
            complete_update_files=len(list(run.glob('update_*.json'))))
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--final', action='store_true')
    arguments = parser.parse_args()
    if not arguments.final:
        provisional()
        return
    # Fail before creating outputs if either native run is still active.
    for role in ('left', 'right'):
        run = PHASE/(role+'_run_v1')
        assert (run/'report.json').is_file() and read(run/'report.json')['completed'] is True
    inputs = {Path(__file__).resolve(), ROOT/'guitar_learning/specialist_policy.py', ROOT/'guitar_learning/policy.py'}
    for role in ('left', 'right'):
        run = PHASE/(role+'_run_v1')
        for pattern in ('report.json', 'core_report.json', 'persistent_audit.json', 'specialist_report.json',
                'settings.json', 'training_contract.json', 'expert_initialization.json', 'transitions.jsonl.gz',
                'update_*.json', 'initial.pt', 'final.pt', 'rollout_first.pt'):
            inputs.update(run.glob(pattern))
    pins = {str(path): sha(path) for path in sorted(inputs)}
    result = dict(schema='specialist_training_learning_analysis_v1', analyzer_version=2,
        roles={role: analyze(PHASE/(role+'_run_v1'), role) for role in ('left', 'right')})
    changed = [path for path, digest in pins.items() if sha(Path(path)) != digest]
    assert not changed
    with (PHASE/'learning_analysis_v1.json').open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    with (PHASE/'learning_verification_v1.json').open('x') as stream:
        json.dump(dict(completed=True, changed_inputs=changed, input_count=len(pins), input_sha256=pins,
            checks={role: row['checks'] for role, row in result['roles'].items()}),
            stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({role: dict(updates=row['completed_updates'],
        transitions=row['committed_transitions'], episodes=row['groups']['committed']['episode_count'],
        successes=row['groups']['committed']['episode_stage_successes'])
        for role, row in result['roles'].items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
