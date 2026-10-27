"""CPU final audit of the fresh surface-reward2000-update GPU training run.

Logs are checked one update/transition at a time, never retained for the full run.
This verifies execution/data consistency, not pressure, sound or policy efficacy.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import sys

os.environ['CUDA_VISIBLE_DEVICES'] = ''
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
ENVS, HORIZON = 1024, 32
REWARD_KEYS = ('song_clean_hold', 'song_left_success', 'song_wrong_press',
               'song_missing_press', 'song_left_approach', 'song_left_missed',
               'song_wrist_position', 'song_left_contact', 'action_change', 'terminal_failure')
RIGHT_KEYS = ('song_right_success', 'song_right_missed', 'song_wrong_crossing',
              'song_repeat_crossing', 'song_right_progress')
LEDGER_KEYS = ('left', 'near_done', 'contact_done', 'clean', 'wrong', 'missing',
               'contact_time', 'exposure_time', 'near_time', 'surface_min', 'geometry_time',
               'loaded_target_time', 'body_load_time', 'higher_time', 'lower_time', 'assignment_time')


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    require(path.is_file(), 'Required evidence missing: '+str(path))
    return json.loads(path.read_text())


def digest(path):
    require(path.is_file(), 'Required input/snapshot missing: '+str(path))
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def lines(path):
    require(path.is_file(), 'Required log missing: '+str(path))
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            require(line.endswith('\n'), 'Incomplete log line %s:%d' % (path, number))
            yield json.loads(line)


def finite(value):
    if isinstance(value, torch.Tensor):
        require(value.device.type == 'cpu' and bool(torch.isfinite(value).all()), 'Nonfinite/non-CPU tensor')
        return 1
    if isinstance(value, (dict, list, tuple)):
        if isinstance(value, dict):
            require(value.get('nonfinite_count', 0) == 0 and not value.get('nonfinite_steps', {}), 'Reported PPO nonfinite samples/steps')
        return sum(finite(item) for item in (value.values() if isinstance(value, dict) else value))
    if isinstance(value, (float, np.floating)):
        require(math.isfinite(value), 'Nonfinite scalar')
    return 0


def summary_close(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(summary_close(v, b[k]) for k, v in a.items())
    if isinstance(a, (list, tuple)):
        return len(a) == len(b) and all(summary_close(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)
    return a == b


def component_sum(parts, total, location, episode=False):
    finite(parts)
    # Float32 step/episode accumulators have different summation orders.
    actual = math.fsum(parts.values())
    error = abs(actual-total)
    relative, absolute = (1e-4, 1e-3) if episode else (1e-5, 1e-6)
    tolerance = max(absolute, relative*max(abs(actual), abs(total)))
    require(error <= tolerance, location+' component sum mismatch: '+str((error, tolerance)))
    return error


def journal(value, updates, closed):
    transitions, rows = updates*HORIZON*ENVS, updates*HORIZON
    require(all(value[k] == transitions for k in ('sampled', 'logged', 'durable', 'committed')), 'Journal transition counts')
    require(all(value[k] == rows for k in ('sampled_rows', 'logged_rows', 'durable_rows')), 'Journal row counts')
    require(all(value[k] == 0 for k in ('discarded', 'pending_rows', 'pending_transitions',
                                       'unresolved_sampled', 'logged_not_committed')), 'Journal uncommitted/discarded data')
    require(value['closed'] is closed and value['failed'] is False, 'Journal lifecycle')


def verify_episode(value, schedule, duration):
    finite(value)
    require(value['valid'] is True and value['reason'] in ('terminal_failure', 'timeline_complete'), 'Invalid episode')
    require(0 <= value['env_id'] < ENVS and value['env_id'] == value['worker_id'], 'Episode row identity')
    require(value['steps'] > 0 and math.isclose(value['steps']/60., value['task_time_s'], abs_tol=1e-8), 'Episode clock')
    failed = value['reason'] == 'terminal_failure'
    require(bool(value['failure_reasons']) is failed and value['song']['completed'] is (not failed), 'Episode termination')
    require(value['song']['target_count'] == value['song']['denominator'] == 67, 'Song denominator')
    require(value['left_curriculum']['full_safe'] is (not failed), 'Curriculum safety evidence')
    if not failed:
        require(value['steps'] == 1969, 'Whole-song endpoint')
    ledger = value['left_note_ledger']
    require(ledger['schema'] == 'guitar_learning.surface_note_ledger.v1', 'Ledger schema')
    require(ledger['target_ids'] == [row['target_id'] for row in schedule], 'Ledger target order')
    notes = ledger['values']
    require(set(notes) == set(LEDGER_KEYS) and all(len(v) == 67 for v in notes.values()), 'Ledger fields/67-note lengths')
    require(len(ledger['required_clean_s']) == 67, 'Required clean lengths')
    for index, target in enumerate(schedule):
        length = target['end_s']-target['onset_s']
        required = min(length, max(.05, .4*length))
        require(math.isclose(ledger['required_clean_s'][index], required, rel_tol=1e-10, abs_tol=1e-12), 'Original40%/50ms success threshold')
        require(notes['left'][index] == (notes['clean'][index]+1e-12 >= required), 'Clean time/achievement correspondence')
        require(notes['contact_done'][index] == (notes['contact_time'][index]+1e-12 >= min(.05, target['end_s']-target['press_s'])),
                'Contact time/achievement correspondence')
    for key in ('left', 'near_done', 'contact_done'):
        require(all(isinstance(v, bool) for v in notes[key]), 'Ledger boolean '+key)
    for key in LEDGER_KEYS[3:]:
        require(all(v >= 0 for v in notes[key]), 'Negative ledger '+key)
    require(sum(notes['left']) == value['song']['left_success_count'], 'Ledger/song achievement count')
    metrics = value['left_curriculum']['finger_metrics']
    require(len(metrics) == 4, 'Four finger metrics required')
    for finger, row in enumerate(metrics, 1):
        indices = [i for i, target in enumerate(schedule) if target['finger'] == finger]
        require(row['target_count'] == len(indices), 'Finger denominator')
        for field, key in (('near_fraction', 'near_done'), ('contact_fraction', 'contact_done'), ('success_fraction', 'left')):
            expected = sum(notes[key][i] for i in indices)/len(indices) if indices else 0.
            require(math.isclose(row[field], expected, rel_tol=2e-6, abs_tol=1e-7), 'Finger/ledger '+field)
    components = value['reward_components']
    require(set(components) == set(REWARD_KEYS+RIGHT_KEYS) and all(components[key] == 0 for key in RIGHT_KEYS),
            'Episode reward fields/unused right-hand components')
    error = component_sum(components, value['reward'], 'Episode reward', episode=True)
    costs = value['cost_components']
    expected = 5*max(duration-value['task_time_s'], 0.) if failed else 0.
    require(costs['failure_rate_cost_per_s'] == 5 and math.isclose(costs['remaining_song_failure'], expected,
            rel_tol=2e-6, abs_tol=1e-4), 'Remaining-song failure cost')
    component_sum({k: costs[k] for k in ('original_physics_and_terminal', 'remaining_song_failure')},
                  value['cost'], 'Episode cost', episode=True)
    return error


def verify(run, phase, updates=2000):
    report, settings, contract = (read(run/name) for name in ('report.json', 'settings.json', 'training_contract.json'))
    require(report.get('completed') is True and report['failure'] is None and report['stopped'] == 'updates_complete', 'Training incomplete/failed')
    require(not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'], 'Run integrity errors')
    require(settings == report['settings'] and (settings['size'], settings['num_envs'], settings['horizon'], settings['updates'], settings['seed']) ==
            ('large', ENVS, HORIZON, updates, 7), 'Expected fresh large1024/H32/seed7 budget')
    require(settings['specialist']['role'] == 'left' and settings['device'] == 'cuda:0' and settings['song']['left_fraction'] == .4, 'Left GPU/song settings')
    require(report['optimizer_updates'] == updates and report['transitions'] == updates*HORIZON*ENVS, 'Update/transition totals')
    require(contract['reward']['schema'] == 'guitar_learning.gpu_tensor_song_reward.v3' and
            contract['observation']['surface_geometry']['schema'] == 'guitar_learning.left_surface_events.v1' and
            contract['observation']['dimension'] == 512 and contract['observation']['event_dim'] == 24, 'Surface contract')
    journal(report['journal'], updates, True)
    require(report['journal']['compressed_bytes'] == (run/'transitions.jsonl.gz').stat().st_size, 'Gzip byte count')
    scene = read(run/'gpu_scene_final.json')
    require(scene == report['gpu_scene'] and report['lifecycle_verified'] is True and scene['closed'] is True, 'Actual GPU lifecycle')
    require(scene['physx_use_gpu'] is True and scene['use_gpu_pipeline'] is True and scene['simulator_count'] == 1 and
            scene['environment_count'] == scene['num_envs'] == ENVS and scene['physics_steps'] == updates*HORIZON*4, 'GPU physics/batch/steps')
    require(set(scene['tensor_devices']) == {'dof', 'roots', 'bodies', 'contact_force', 'jacobian'} and
            all(v == 'cuda:0' for v in scene['tensor_devices'].values()), 'Actual CUDA tensor devices')
    aggregate = scene['environment_aggregate']
    require((aggregate['max_bodies'], aggregate['max_shapes'], aggregate['self_collisions']) == (68, 145, True), 'Aggregate contract')
    pins, manifest = read(run/'inputs_before.json'), read(phase/'training_source_manifest.json')
    source = manifest['source']
    require(manifest['active_python_count'] == len(source), 'Frozen source count')
    active = {str(p.resolve()) for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    require(active == set(source), 'Active Python source set changed')
    for name, expected in pins.items():
        require(digest(Path(name)) == expected, 'Input SHA mismatch: '+name)
    for name, expected in source.items():
        require(pins.get(name) == expected and digest(phase/'source_training'/Path(name).relative_to(ROOT)) == expected, 'Training snapshot/source pin mismatch: '+name)
    schedule = contract['task']['provenance']['song']['schedule']
    require(len(schedule) == 67, 'Expected67-note schedule')
    duration = settings['song_training']['episode_duration_s']
    initial = torch.load(run/'initial.pt', map_location='cpu', weights_only=False)
    finite(initial)
    require(initial['updates'] == 0 and not initial['actor_optimizer']['state'] and not initial['value_optimizer']['state'], 'Expected fresh optimizer state')
    require(bool((initial['model']['log_std'][:33] == -3.).all()) and bool((initial['model']['actor_heads.left.weight'] == 0).all()) and
            bool((initial['model']['actor_heads.left.bias'] == 0).all()), 'Expected fresh zero-mean/default-std left actor')
    from guitar_learning.song.gpu_left_curriculum import CurriculumState
    counts = [sum(t['finger'] == f for t in schedule) for f in range(1, 5)]
    curriculum = CurriculumState(counts)
    require(np.array_equal(initial['model']['left_curriculum_state'].numpy(), curriculum.state_vector()), 'Expected fresh3331 curriculum')
    require(len(report['updates']) == len(list(run.glob('update_*.json'))) == updates, 'Update file/report counts')
    metrics, logged = iter(lines(run/'learning_metrics.jsonl')), iter(lines(run/'episodes.jsonl'))
    totals = Counter(all=0, physical_failure=0, timeline_complete=0, stage_success=0)
    raw_count = max_episode_error = max_update_error = 0
    with gzip.open(run/'transitions.jsonl.gz', 'rt') as stream:
        for index in range(updates):
            row = read(run/('update_%06d.json' % index))
            finite(row)
            require(row['update_index'] == index and row['optimizer_updates'] == index+1 and row['transitions'] == HORIZON*ENVS and
                    row['physics_steps'] == (index+1)*HORIZON*4, 'Update sequence')
            journal(row['journal'], index+1, False)
            require(all(report['updates'][index][key] == row[key] for key in report['updates'][index]), 'Report/update summary')
            require(encoded(next(metrics, None)) == encoded(row), 'Metrics/update correspondence')
            parts = row['reward_component_means']
            require(set(parts) == set(REWARD_KEYS+RIGHT_KEYS) and all(parts[k] == 0 for k in RIGHT_KEYS), 'Update reward fields/right zeros')
            max_update_error = max(max_update_error, component_sum(parts, row['mean_reward'], 'Update reward'))
            expected_hash, logged_hash, raw_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
            episodes = row['completed_episodes']
            for episode in episodes:
                max_episode_error = max(max_episode_error, verify_episode(episode, schedule, duration))
                expected_hash.update(encoded(episode)+b'\n')
                item = next(logged, None)
                require(item is not None and item['update_index'] == index, 'Episode log update/order')
                logged_hash.update(encoded(item['episode'])+b'\n')
                totals['all'] += 1
                totals['physical_failure' if episode['reason'] == 'terminal_failure' else 'timeline_complete'] += 1
                totals['stage_success'] += bool(episode['song']['stage_success'])
            before = curriculum.progress
            summary = curriculum.observe([dict(full_safe=e['reason'] == 'timeline_complete',
                finger_metrics=e['left_curriculum']['finger_metrics']) for e in episodes])
            summary.update(completed_episodes_in_update=len(episodes), progress_before=before,
                           boundary='after committed PPO collection; no scene reset')
            require(summary_close(summary, row['left_curriculum']), 'Full curriculum summary replay')
            reward_sum = cost_sum = raw_episodes = 0
            for tick in range(HORIZON):
                line = stream.readline()
                require(line.endswith('\n'), 'Missing/incomplete gzip row')
                raw = json.loads(line)
                finite(raw)
                require(raw['schema'] == 'guitar_learning.gpu_transition.v1' and raw['update_index'] == index and raw['tick_in_update'] == tick, 'Raw transition order')
                require(all(len(raw[k]) == ENVS for k in ('reward', 'cost', 'terminated', 'truncated')), 'Raw batch dimensions')
                require(all(isinstance(v, bool) for k in ('terminated', 'truncated') for v in raw[k]) and not any(raw['truncated']), 'Raw done masks')
                require(all(v >= 0 for v in raw['cost']), 'Negative raw cost')
                ids = [e['env_id'] for e in raw['episodes']]
                require(len(ids) == len(set(ids)) and set(ids) == {i for i, v in enumerate(raw['terminated']) if v}, 'Raw terminal/episode correspondence')
                for episode in raw['episodes']:
                    raw_hash.update(encoded(episode)+b'\n')
                raw_episodes += len(ids)
                reward_sum += math.fsum(raw['reward'])
                cost_sum += math.fsum(raw['cost'])
                raw_count += 1
            require(raw_episodes == len(episodes) and expected_hash.digest() == logged_hash.digest() == raw_hash.digest(), 'Exact episode correspondence across logs')
            require(math.isclose(reward_sum/(HORIZON*ENVS), row['mean_reward'], rel_tol=1e-5, abs_tol=1e-6), 'Raw reward mean')
            require(math.isclose(cost_sum/(HORIZON*ENVS), row['mean_cost'], rel_tol=1e-5, abs_tol=1e-6), 'Raw cost mean')
            if (index+1) % 100 == 0:
                print('Verified updates', index+1, flush=True)
        require(stream.read() == '', 'Extra gzip data; EOF/CRC verification failed')
    require(next(metrics, None) is None and next(logged, None) is None, 'Extra metric/episode log rows')
    require(totals['timeline_complete'] > 0, 'No whole-song timeline completion')
    song = read(run/'song_report.json')
    require(song['completed'] is True and song['partial_trajectories_are_successes'] is False and
            song['completed_episodes'] == report['completed_episodes'] == totals['all'] and
            all(song['episode_counts'][k] == totals[k] for k in ('physical_failure', 'timeline_complete', 'stage_success')), 'Final song counters')
    final = torch.load(run/'final.pt', map_location='cpu', weights_only=False)
    require(final['updates'] == updates and final['identity']['architecture']['contract'] == contract and final['identity']['config'] == settings['ppo'], 'Final checkpoint identity/updates')
    require(math.isfinite(final['cost_weight']) and final['cost_weight'] >= 0, 'Checkpoint cost weight')
    tensor_counts = {k: finite(final[k]) for k in ('model', 'actor_optimizer', 'value_optimizer')}
    require(all(tensor_counts.values()) and final['actor_optimizer']['state'] and final['value_optimizer']['state'], 'Final optimizer/model state')
    saved = final['model']['left_curriculum_state'].numpy()
    require(saved.shape == (3331,) and np.allclose(saved, curriculum.state_vector(), rtol=1e-10, atol=1e-12), 'Final3331 curriculum replay')
    restored = CurriculumState(counts)
    restored.load_state(saved)
    boundaries, reasons = [], Counter()
    for event in lines(run/'events.jsonl'):
        if event.get('event') == 'cuda_cache_release':
            require(event['after']['free_bytes'] >= 1024**3, 'GPU floor after cache recovery')
            reasons[event['reason']] += 1
            if event['reason'] == 'optimizer_boundary':
                boundaries.append((event['update_index'], event['after']))
    require([i for i, _ in boundaries] == list(range(updates)), 'Cache boundary sequence')
    free = [v['free_bytes'] for _, v in boundaries]
    base = free[0]+boundaries[0][1]['reserved_bytes']
    growth = [base-v['free_bytes']-v['reserved_bytes'] for _, v in boundaries]
    require(report['resources']['cuda_free_guard_sample_min_bytes'] >= 1024**3, 'GPU resource floor')
    ram_floor = int(settings['min_available_memory_gib']*1024**3)
    ram_min = None
    for row in lines(run/'resources.jsonl'):
        require(row['low_memory'] is None and row['available_memory_bytes'] >= ram_floor, 'RAM resource floor')
        ram_min = row['available_memory_bytes'] if ram_min is None else min(ram_min, row['available_memory_bytes'])
    require(ram_min is not None, 'Missing RAM samples')
    return dict(completed=True, scope=__doc__.strip(), committed_updates=updates,
                committed_transitions=report['transitions'], raw_rows=raw_count, raw_gzip_CRC_EOF=True,
                exact_episode_log_correspondence=True, ended_episode_counts=dict(totals), input_pins=len(pins),
                frozen_python_verified=len(source), finite_checkpoint_tensors=tensor_counts,
                curriculum_values=3331, curriculum_replay_max_abs_error=float(np.max(np.abs(saved-curriculum.state_vector()))),
                max_episode_reward_sum_abs_error=max_episode_error, max_update_reward_sum_abs_error=max_update_error,
                reward_sum_tolerance=dict(episode=dict(rel_tol=1e-4, abs_tol=1e-3), update=dict(rel_tol=1e-5, abs_tol=1e-6)),
                PPO_reported_nonfinite_counts_zero=True, GPU_lifecycle_verified=True,
                memory=dict(post_cache_free_min_GiB=min(free)/1024**3, post_cache_free_final_GiB=free[-1]/1024**3,
                            estimated_nonTorch_growth_final_GiB=growth[-1]/1024**3,
                            estimated_nonTorch_growth_max_GiB=max(growth)/1024**3,
                            estimated_nonTorch_last100_range_GiB=(max(growth[-100:])-min(growth[-100:]))/1024**3,
                            RAM_min_GiB=ram_min/1024**3, cache_release_reasons=dict(reasons)),
                final_checkpoint_sha256=digest(run/'final.pt'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    phase = args.phase.resolve()
    output = args.out or phase/'training_verification.json'
    require(not output.exists(), 'Refusing to overwrite verification output')
    torch.set_num_threads(1)
    result = verify(phase/'train1024_large_2000', phase)
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
