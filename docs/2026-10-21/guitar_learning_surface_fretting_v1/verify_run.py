"""CPU-only verification after the actual 64-update run and one-update resume.

No simulator, CUDA model, training, or evaluation is started. Missing/incomplete
evidence is an error; verification.json is created only after every check passes.
Ledger geometry/load/cause times can overlap. A zero surface_min with zero
exposure is an unobserved note, not evidence of contact or acoustic success.
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
        return sum(finite(item) for item in (value.values() if isinstance(value, dict) else value))
    if isinstance(value, (float, np.floating)):
        require(math.isfinite(value), 'Nonfinite scalar')
    return 0


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and np.array_equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(v, b[k]) for k, v in a.items())
    if isinstance(a, (list, tuple)):
        return type(a) is type(b) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


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


def verify_run(run, updates, previous_updates, source):
    report, settings, contract = (read(run/name) for name in ('report.json', 'settings.json', 'training_contract.json'))
    require(report.get('completed') is True and report['failure'] is None and report['stopped'] == 'updates_complete',
            'Run incomplete/failed: '+str(run))
    require(not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'], 'Run integrity errors')
    require(settings == report['settings'], 'Settings/report mismatch')
    require((settings['size'], settings['num_envs'], settings['horizon'], settings['updates'], settings['seed']) ==
            ('large', ENVS, HORIZON, updates, 7), 'Expected large1024 H32 seed7 budget')
    require(settings['specialist']['role'] == 'left' and settings['device'] == 'cuda:0', 'Expected CUDA left run')
    require(report['optimizer_updates'] == previous_updates+updates and report['transitions'] == updates*HORIZON*ENVS, 'Update/transition totals')
    require(contract['reward']['schema'] == 'guitar_learning.gpu_tensor_song_reward.v3' and
            contract['observation']['surface_geometry']['schema'] == 'guitar_learning.left_surface_events.v1', 'Surface contract versions')
    require(contract['observation']['dimension'] == 512 and contract['observation']['event_dim'] == 24, 'Observation dimensions')
    journal(report['journal'], updates, True)
    require(report['journal']['compressed_bytes'] == (run/'transitions.jsonl.gz').stat().st_size, 'Gzip byte count')
    scene = read(run/'gpu_scene_final.json')
    require(scene == report['gpu_scene'] and report['lifecycle_verified'] is True and scene['closed'] is True, 'GPU scene lifecycle')
    require(scene['physx_use_gpu'] is True and scene['use_gpu_pipeline'] is True and scene['simulator_count'] == 1 and
            scene['environment_count'] == scene['num_envs'] == ENVS, 'Actual GPU pipeline/batch flags')
    require(scene['physics_steps'] == updates*HORIZON*4 and all(v == 'cuda:0' for v in scene['tensor_devices'].values()), 'GPU steps/devices')
    aggregate = scene['environment_aggregate']
    require((aggregate['max_bodies'], aggregate['max_shapes'], aggregate['self_collisions']) == (68, 145, True), 'Aggregate contract')
    pins = read(run/'inputs_before.json')
    for name, expected in pins.items():
        require(digest(Path(name)) == expected, 'Input SHA mismatch: '+name)
    require(all(pins.get(name) == value for name, value in source.items()), 'Training source/input pins mismatch')
    schedule = contract['task']['provenance']['song']['schedule']
    require(len(schedule) == 67, 'Expected 67-note schedule')
    require(settings['song']['left_fraction'] == .4, 'Original40% clean requirement')
    duration = settings['song_training']['episode_duration_s']
    initial = torch.load(run/'initial.pt', map_location='cpu', weights_only=False)
    finite(initial)
    from guitar_learning.song.gpu_left_curriculum import CurriculumState
    finger_counts = [sum(t['finger'] == f for t in schedule) for f in range(1, 5)]
    curriculum = CurriculumState(finger_counts)
    curriculum.load_state(initial['model']['left_curriculum_state'].numpy())
    require(len(report['updates']) == len(list(run.glob('update_*.json'))) == updates, 'Update file/report counts')
    rows, counts, max_episode_error, max_update_error = [], Counter(), 0., 0.
    for index in range(updates):
        row = read(run/('update_%06d.json' % index))
        finite(row)
        require(row['update_index'] == index and row['optimizer_updates'] == previous_updates+index+1 and
                row['transitions'] == HORIZON*ENVS and row['physics_steps'] == (index+1)*HORIZON*4, 'Update sequence')
        journal(row['journal'], index+1, False)
        require(all(report['updates'][index][key] == row[key] for key in report['updates'][index]), 'Report/update summary mismatch')
        max_update_error = max(max_update_error, component_sum(row['reward_component_means'], row['mean_reward'], 'Update reward'))
        require(set(row['reward_component_means']) == set(REWARD_KEYS+RIGHT_KEYS) and
                all(row['reward_component_means'][key] == 0 for key in RIGHT_KEYS), 'Update unused right-hand components')
        for value in row['completed_episodes']:
            max_episode_error = max(max_episode_error, verify_episode(value, schedule, duration))
            counts['all'] += 1
            counts['physical_failure' if value['reason'] == 'terminal_failure' else 'timeline_complete'] += 1
            counts['stage_success'] += bool(value['song']['stage_success'])
        before = curriculum.progress
        summary = curriculum.observe([dict(full_safe=value['reason'] == 'timeline_complete',
            finger_metrics=value['left_curriculum']['finger_metrics']) for value in row['completed_episodes']])
        summary.update(completed_episodes_in_update=len(row['completed_episodes']), progress_before=before,
                       boundary='after committed PPO collection; no scene reset')
        require(summary_close(summary, row['left_curriculum']), 'Replayed curriculum summary/count/finger metrics')
        rows.append(row)
    metrics = list(lines(run/'learning_metrics.jsonl'))
    require(len(metrics) == updates and all(encoded(a) == encoded(b) for a, b in zip(metrics, rows)), 'Metrics/update correspondence')
    expected_episodes = [dict(update_index=i, episode=e) for i, row in enumerate(rows) for e in row['completed_episodes']]
    require(list(lines(run/'episodes.jsonl')) == expected_episodes, 'Episode log/update correspondence')
    raw_rows = 0
    # Reading all concatenated gzip members through EOF verifies CRC/trailers.
    with gzip.open(run/'transitions.jsonl.gz', 'rt') as stream:
        for index, update in enumerate(rows):
            rewards, costs, episodes = 0., 0., []
            for tick in range(HORIZON):
                line = stream.readline()
                require(line.endswith('\n'), 'Missing/incomplete gzip row')
                row = json.loads(line)
                finite(row)
                require(row['schema'] == 'guitar_learning.gpu_transition.v1' and row['update_index'] == index and row['tick_in_update'] == tick, 'Raw row order')
                require(all(len(row[key]) == ENVS for key in ('reward', 'cost', 'terminated', 'truncated')), 'Raw batch dimensions')
                require(all(isinstance(v, bool) for k in ('terminated', 'truncated') for v in row[k]) and not any(row['truncated']), 'Raw terminal mask')
                require(all(v >= 0 for v in row['cost']), 'Negative raw cost')
                ids = [value['env_id'] for value in row['episodes']]
                require(len(ids) == len(set(ids)) and set(ids) == {i for i, v in enumerate(row['terminated']) if v}, 'Raw terminal/episode correspondence')
                rewards += math.fsum(row['reward'])
                costs += math.fsum(row['cost'])
                episodes.extend(row['episodes'])
                raw_rows += 1
            require(episodes == update['completed_episodes'], 'Raw/update episode correspondence')
            require(math.isclose(rewards/(HORIZON*ENVS), update['mean_reward'], rel_tol=1e-5, abs_tol=1e-6), 'Raw reward mean')
            require(math.isclose(costs/(HORIZON*ENVS), update['mean_cost'], rel_tol=1e-5, abs_tol=1e-6), 'Raw cost mean')
        require(stream.read() == '', 'Unexpected extra gzip rows')
    song = read(run/'song_report.json')
    require(song['completed'] is True and song['partial_trajectories_are_successes'] is False and
            song['completed_episodes'] == report['completed_episodes'] == counts['all'], 'Song episode count/lifecycle')
    require(all(song['episode_counts'][key] == counts[key] for key in ('physical_failure', 'timeline_complete', 'stage_success')), 'Song outcome counts')
    checkpoint = torch.load(run/'final.pt', map_location='cpu', weights_only=False)
    require(math.isfinite(checkpoint['cost_weight']) and checkpoint['cost_weight'] >= 0, 'Checkpoint cost weight')
    require(initial['updates'] == previous_updates and checkpoint['updates'] == previous_updates+updates, 'Checkpoint update counts')
    require(checkpoint['identity']['architecture']['contract'] == contract and checkpoint['identity']['config'] == settings['ppo'], 'Checkpoint contract/PPO config')
    tensor_counts = {key: finite(checkpoint[key]) for key in ('model', 'actor_optimizer', 'value_optimizer')}
    require(all(tensor_counts.values()) and checkpoint['actor_optimizer']['state'] and checkpoint['value_optimizer']['state'], 'Empty checkpoint/optimizer state')
    state = checkpoint['model']['left_curriculum_state']
    require(state.shape == (3331,), 'GPU curriculum checkpoint must have3331 values')
    saved_curriculum = CurriculumState(finger_counts)
    saved_curriculum.load_state(state.numpy())
    expected_state = curriculum.state_vector()
    require(np.allclose(state.numpy(), expected_state, rtol=1e-10, atol=1e-12), 'Full3331 checkpoint curriculum differs from episode replay')
    curriculum_error = float(np.max(np.abs(state.numpy()-expected_state)))
    require(report['resources']['cuda_free_guard_sample_min_bytes'] >= 1024**3, 'GPU free-memory floor')
    return (dict(completed=True, committed_updates=updates, final_optimizer_updates=previous_updates+updates,
                 committed_transitions=report['transitions'], raw_rows=raw_rows, raw_gzip_CRC_EOF=True,
                 exact_episode_log_correspondence=True, ended_episode_counts=dict(counts), input_pins=len(pins),
                 max_episode_reward_sum_abs_error=max_episode_error, max_update_reward_sum_abs_error=max_update_error,
                 finite_tensor_counts=tensor_counts, curriculum_values=state.numel(),
                 curriculum_replay_max_abs_error=curriculum_error, all_update_curriculum_summaries_verified=True,
                 gpu_lifecycle_verified=True),
            initial, checkpoint)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--old-checkpoint', type=Path, default=ROOT/'docs/2026-10-21/guitar_learning_gpu_long_training_v3/train1024_large_2000/final.pt')
    args = parser.parse_args()
    phase = args.phase.resolve()
    output = phase/'verification.json'
    require(not output.exists(), 'Refusing to overwrite verification.json')
    require(args.old_checkpoint.is_file(), 'Required old2000-update checkpoint missing: '+str(args.old_checkpoint))
    for run in ('train1024_large_64', 'resume_1'):
        for name in ('report.json', 'settings.json', 'training_contract.json', 'inputs_before.json',
                     'gpu_scene_final.json', 'transitions.jsonl.gz', 'learning_metrics.jsonl',
                     'episodes.jsonl', 'song_report.json', 'initial.pt', 'final.pt'):
            require((phase/run/name).is_file(), 'Required completed-run evidence missing: '+str(phase/run/name))
    manifest = read(phase/'training_source_manifest.json')
    source = manifest['source']
    require(manifest['active_python_count'] == len(source), 'Source manifest count')
    active = {str(p.resolve()) for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    require(active == set(source), 'Active Python source set changed')
    for name, expected in source.items():
        require(digest(Path(name)) == expected and digest(phase/'source_training'/Path(name).relative_to(ROOT)) == expected,
                'Active/snapshot source SHA mismatch: '+name)
    torch.set_num_threads(1)
    main_result, _, trained = verify_run(phase/'train1024_large_64', 64, 0, source)
    require(main_result['ended_episode_counts'].get('timeline_complete', 0) > 0, 'No whole-song timeline completed to verify ledgers')
    resumed_result, restored, resumed = verify_run(phase/'resume_1', 1, 64, source)
    require(trained.keys() == restored.keys() and all(same(value, restored[key]) for key, value in trained.items() if key != 'metadata'),
            '64→65 initial nonmetadata state was not restored exactly')
    require(same(trained['identity'], resumed['identity']), 'Resume checkpoint identity changed')
    require(all(not same(restored[key], resumed[key]) for key in ('actor_optimizer', 'value_optimizer')), 'Both optimizers must advance')
    changed = [key for key, value in restored['model'].items() if not same(value, resumed['model'][key])]
    require(any(key.startswith(('actor_encoders.left.', 'actor_heads.left.')) for key in changed) and
            not any(key.startswith(('actor_encoders.right.', 'actor_heads.right.')) for key in changed) and
            torch.equal(restored['model']['log_std'][33:], resumed['model']['log_std'][33:]), 'Resume active/inactive actor updates')
    resume_pins = read(phase/'resume_1/inputs_before.json')
    require(resume_pins.get(str(phase/'train1024_large_64/final.pt')) == digest(phase/'train1024_large_64/final.pt'), 'Resume source checkpoint pin')
    old = torch.load(args.old_checkpoint, map_location='cpu', weights_only=False)
    require(old['updates'] == 2000 and old['identity']['architecture']['contract']['reward']['schema'] ==
            'guitar_learning.gpu_tensor_song_reward.v2', 'Expected actual old2000-update v2 checkpoint')
    from guitar_learning.skills.specialist_policy import SpecialistPolicy
    from guitar_learning.training.ppo import PPOConfig, PPOTrainer
    architecture = trained['identity']['architecture']
    policy = SpecialistPolicy(512, size='large', contract=architecture['contract'], role='left')
    trainer = PPOTrainer(policy, PPOConfig(**trained['identity']['config']))
    require(trainer._identity() == trained['identity'], 'CPU strict-load test identity differs from the actual new run')
    try:
        trainer.load(args.old_checkpoint)
    except ValueError as error:
        require(str(error) == 'own schema/architecture/input/control/config mismatch', 'Old checkpoint rejected for the wrong reason: '+str(error))
        rejection = str(error)
    else:
        raise ValueError('Old v2 checkpoint unexpectedly accepted by the actual strict loader')
    result = dict(completed=True, scope='CPU audit of actual GPU run/resume evidence; no pressure, sound or learning efficacy claim',
                  main=main_result, resume=resumed_result, frozen_python_verified=len(source),
                  resume_initial_all_nonmetadata_exact=True, both_optimizers_and_left_actor_updated=True,
                  inactive_right_unchanged=True, old_v2_actual_strict_rejection=rejection,
                  old_checkpoint_sha256=digest(args.old_checkpoint),
                  reward_sum_tolerance=dict(episode=dict(rel_tol=1e-4, abs_tol=1e-3),
                                            update=dict(rel_tol=1e-5, abs_tol=1e-6)),
                  ledger_scope=__doc__.split('Ledger ', 1)[1])
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
