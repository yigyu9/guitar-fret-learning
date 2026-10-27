"""CPU final audit of the fresh438 reward-v8 GPU left544/eight-priority run or a committed prefix.

Logs are checked one update/transition at a time, never retained for the full run.
This verifies execution/data consistency, not pressure, sound or policy efficacy.
"""
import argparse
from collections import Counter
from contextlib import closing
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
from guitar_learning.training import json_io
from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
from guitar_learning.training.training_log_io import iter_transitions
from guitar_learning.gpu.finger_reward import (FINGER_REWARD_CONTRACT, FINGER_COORDINATION_CONTRACT,
    FINGER_TARGET_CONTRACT, source_finger_frame_contract)
ENVS, HORIZON = 1024, 32
DEFAULT_RUN = Path('/media/ajou/새 볼륨1/guitar_learning_runs/20261022_v8_long/train2000')
REWARD_KEYS = ('song_clean_hold', 'song_left_success', 'song_wrong_press',
               'song_missing_press', 'song_left_approach', 'song_left_missed',
               'song_wrist_position', 'song_left_contact', 'action_change', 'terminal_failure', 'song_finger_tracking',
               'song_finger_coordination', 'song_finger_standby')
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
    return json_io.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def lines(path, live_tail=False):
    require(path.is_file(), 'Required log missing: '+str(path))
    with path.open() as stream:
        for number, line in enumerate(stream, 1):
            if not line.endswith('\n') and live_tail:
                require(stream.read(1) == '', 'Incomplete non-tail log line')
                return
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
    require(value['completed_members'] == updates, 'Expected one synced gzip member per committed update')


def verify_episode(value, schedule, duration, action_contract):
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
    require(ledger['schema'] == 'guitar_learning.surface_note_ledger.v2', 'Ledger schema')
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
    verify_motion(value, action_contract)
    components = value['reward_components']
    require(set(components) == set(REWARD_KEYS+RIGHT_KEYS) and all(components[key] == 0 for key in RIGHT_KEYS),
            'Episode reward fields/unused right-hand components')
    verify_rate_components(components, value['task_time_s'])
    error = component_sum(components, value['reward'], 'Episode reward', episode=True)
    costs = value['cost_components']
    expected = 5*max(duration-value['task_time_s'], 0.) if failed else 0.
    require(costs['failure_rate_cost_per_s'] == 5 and math.isclose(costs['remaining_song_failure'], expected,
            rel_tol=2e-6, abs_tol=1e-4), 'Remaining-song failure cost')
    component_sum({k: costs[k] for k in ('original_physics_and_terminal', 'remaining_song_failure')},
                  value['cost'], 'Episode cost', episode=True)
    return error


MOTION_FIELDS = ('actual_min_rad', 'actual_max_rad', 'actual_range_rad',
    'target_min_rad', 'target_max_rad', 'target_range_rad', 'action_mean', 'action_mean_abs',
    'action_positive_fraction', 'action_negative_fraction', 'action_zero_fraction',
    'action_mean_abs_change', 'action_opposite_sign_fraction', 'limit_outward_command_fraction',
    'tracking_error_rms_rad', 'tracking_error_max_abs_rad')


def verify_surface_contract(contract):
    observation, reward = contract['observation'], contract['reward']
    require(reward['schema'] == 'guitar_learning.gpu_tensor_song_reward.v8' and
            observation['surface_geometry']['schema'] == 'guitar_learning.left_surface_events.v2' and
            observation['dimension'] == 544 and observation['event_dim'] == 24 and
            observation['priority_slots'] == 8, 'GPU left rewardv8/state544/eight-priority contract')
    require(observation['finger_targets'] == FINGER_TARGET_CONTRACT, 'Shared finger target selector contract')
    require(observation['finger_posture']['schema'] == 'guitar_learning.left_finger_posture_observation.v1',
            'Actual posture observation schema')
    fields = ['finger_posture.'+f+'.'+joint+'.'+trig
              for f in ('index', 'middle', 'ring', 'pinky') for joint in ('MCP', 'PIP', 'DIP') for trig in ('sin', 'cos')]
    fields += ['finger_posture.'+f+'.'+name for name in ('valid', 'idle_weight')
               for f in ('index', 'middle', 'ring', 'pinky')]
    require(len(observation['fields']) == len(observation['scales']) == 544 and
            observation['fields'][-32:] == fields and observation['scales'][-32:] == [1.]*32,
            'Posture sin/cos24, valid4, idle4 field/scaling order')
    require(reward['finger_tracking'] == FINGER_REWARD_CONTRACT and
            reward['finger_tracking']['schema'] == 'guitar_learning.gpu_finger_tracking_rate.v5' and
            reward['finger_tracking']['motion_cost'] == 'none; no requested-motion or surface-velocity suppression',
            'V8 rational-distance tracking without motion cost')
    surface = reward['surface_learning']
    require(surface['schema'] == 'guitar_learning.surface_fretting.v3' and
            surface['approach_gamma'] == .99 and surface['potential_distance_scale_m'] == .03 and
            surface['target_selector_schema'] == FINGER_TARGET_CONTRACT['schema'] and
            'shared-selector tracking slot0' in surface['potential'], 'Shared-selector approach potential')
    posture = dict(reward['finger_posture'])
    frame = posture.pop('frame_source')
    require(posture == FINGER_COORDINATION_CONTRACT and frame == source_finger_frame_contract(),
            'Soft posture rates/source-frame contract')
    require(reward['left_curriculum']['weights']['approach'] == [1., 1., 1.], 'Fixed approach weight for realized rate bounds')
    require(contract['native_backend']['pipeline'] == 'gpu', 'Actual GPU contract required')


def verify_architecture(architecture):
    require(architecture['state_dim'] == 544 and architecture['event_dim'] == 24 and
            list(architecture['priority_slots']) == FINGER_TARGET_CONTRACT['slots'],
            'Checkpoint left544/eight-priority architecture')
    actor = architecture.get('finger_actor', {})
    require(actor.get('schema') == 'guitar_learning.targeted_finger_actor.v1' and
            list(actor['fingers']) == ['index', 'middle', 'ring', 'pinky'] and
            list(actor['shared_action_names']) == list(ACTIVE_NAMES[:17]) and
            (actor['priority_slots_per_finger'], actor['token_width'], actor['local_width'],
             tuple(actor['hidden']), actor['output_per_finger']) == (2, 128, 20, (128,), 4),
            'Target-conditioned hidden finger branches')
    for finger in actor['fingers']:
        fields, indices = actor['local_fields'][finger], actor['local_indices'][finger]
        joints = ['LH:'+finger+suffix for suffix in ('1_x', '1_z', '2', '3')]
        expected = [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error') for joint in joints]
        expected += ['finger_posture.'+finger+'.'+joint+'.'+trig
                     for joint in ('MCP', 'PIP', 'DIP') for trig in ('sin', 'cos')]
        expected += ['finger_posture.'+finger+'.'+field for field in ('valid', 'idle_weight')]
        observation_fields = architecture['contract']['observation']['fields']
        require(list(fields) == expected and list(indices) == [observation_fields.index(field) for field in expected],
                'Named own-finger input mapping')


def verify_ppo_config(config):
    require(config['advantage_normalization'] == 'separate' and config['gae_lambda'] == .98 and
            config['gamma'] == .99 and config['cost_gamma'] == config['cost_weight'] == 1. and
            config['episode_cost_budget'] is None, 'V8 explicit separate GAE/PPO configuration')


def verify_advantages(diagnostic):
    """Summary identities with float32 roundoff, not individual GAE reconstruction.

    Summaries are float64 but production centering/std use float32. For a
    large offset and small variance, mean roundoff is amplified by division.
    Eight float32 eps times source magnitude is the reduction/centering error
    budget; the possible mean shift also widens the std's lower bound. This
    precision-aware check is not a universal GPU reduction error proof.
    """
    finite(diagnostic)
    require(diagnostic['normalization'] == 'separate' and diagnostic['cost_weight_used'] == 1.,
            'Separate reward/cost normalization and fixed multiplier')
    keys = ('reward_raw', 'cost_raw', 'weighted_cost_raw', 'raw_combined',
            'reward_normalized', 'cost_normalized', 'weighted_cost_normalized',
            'combined_raw', 'combined_normalized')
    for key in keys:
        require(diagnostic[key]['count'] == ENVS*HORIZON and diagnostic[key]['std'] >= 0,
                'Advantage sample count/std: '+key)
    eps = float(np.finfo(np.float32).eps)
    magnitude = lambda row: max(abs(row[key]) for key in ('mean', 'min', 'max'))
    max_mean_tolerance = 0.
    for raw, normalized in (('reward_raw', 'reward_normalized'), ('cost_raw', 'cost_normalized'),
                            ('combined_raw', 'combined_normalized')):
        source, target = diagnostic[raw], diagnostic[normalized]
        expected = source['std']/max(source['std'], 1e-8)
        roundoff = 8*eps*magnitude(source)
        mean_tolerance = max(2e-5, roundoff/max(source['std'], 1e-8))
        lower_std = source['std']/max(math.hypot(source['std'], roundoff), 1e-8)
        require(abs(target['mean']) <= mean_tolerance and
                max(0., lower_std-2e-5) <= target['std'] <= expected+2e-5,
                'Centered/clamped normalized advantage: '+normalized)
        max_mean_tolerance = max(max_mean_tolerance, mean_tolerance)
    for left, right in (('cost_raw', 'weighted_cost_raw'), ('cost_normalized', 'weighted_cost_normalized')):
        require(summary_close(diagnostic[left], diagnostic[right]), 'Unit cost multiplier summary')
    for mixed, reward, cost in (('raw_combined', 'reward_raw', 'cost_raw'),
                                ('combined_raw', 'reward_normalized', 'cost_normalized')):
        require(math.isclose(diagnostic[mixed]['mean'], diagnostic[reward]['mean']-diagnostic[cost]['mean'],
                rel_tol=2e-5, abs_tol=max(2e-5, 8*eps*(magnitude(diagnostic[reward])+magnitude(diagnostic[cost])))),
                'Mixed advantage mean identity')
    return max_mean_tolerance


def verify_rate_components(components, seconds):
    # Approach-stage weight is1 throughout this pinned curriculum. Failed ticks
    # can suppress positive terms, so only nonnegativity and upper bounds apply.
    for key, rate in (('song_finger_tracking', 4.), ('song_finger_coordination', .05),
                      ('song_finger_standby', .05)):
        require(0 <= components[key] <= rate*seconds+max(1e-6, rate*seconds*1e-4),
                'Bounded realized reward component: '+key)


def verify_codec(contract):
    verify_surface_contract(contract)
    control = contract['native_backend']['control']
    require(control['schema'] == 'guitar_learning.gpu_finite_control.v3', 'Incremental control schema')
    codec = control['action_codec']
    require(codec['schema'] == 'guitar_learning.gpu_left_incremental_fingers.v1' and
            codec['incremental_joint_names'] == list(LEFT_HAND_NAMES) and
            codec['incremental_action_indices'] == [ACTIVE_NAMES.index(n) for n in LEFT_HAND_NAMES] and
            codec['velocity_scale_rad_s'] == 4 and codec['control_hz'] == 60 and
            codec['zero_action'] == 'hold previous target', 'Incremental left21 codec')
    require(all(control['smoothing_alpha'][i] == 1 and
                control['rate_rad_s'][control['joint_names'].index(n)] == 4
                for i, n in zip(codec['incremental_action_indices'], LEFT_HAND_NAMES)), 'Left21 direct/rate contract')
    require((control['action_dim'], control['target_dim'], control['native_position_count'],
             control['native_effort_count']) == (39, 105, 48, 57), 'Unchanged native control ownership')
    require(contract['diagnostics']['left_finger_motion']['schema'] == 'guitar_learning.gpu_left_finger_motion.v2',
            'Motion diagnostic contract missing')
    require(contract['diagnostics']['left_finger_motion']['base_rotation']['schema'] ==
            'guitar_learning.gpu_left_finger_base_rotation.v1', 'Base rotation contract missing')
    return control


BASE_FIELDS = ('palm_relative_rotvec_y_rms_rad', 'palm_relative_rotvec_y_max_abs_rad',
    'zero_y_command_rotation_error_rms_rad', 'zero_y_command_rotation_error_max_rad',
    'zero_y_command_local_xz_error_rms_rad', 'zero_y_command_local_xz_error_max_rad')
BASE_NAMES = ['human/LH:'+name+'1' for name in ('index','middle','ring','pinky')]


def verify_motion(episode, control):
    row = episode['left_finger_motion']; steps = episode['steps']
    require(row['schema'] == 'guitar_learning.gpu_left_finger_motion.v2' and
            row['joint_names'] == list(LEFT_HAND_NAMES) and row['sampling_hz'] == 60 and
            row['range_samples'] == steps+1 and row['endpoint_samples'] == row['action_samples'] == steps and
            row['action_change_pairs'] == max(steps-1, 0), 'Motion identities/sample denominators')
    base = row['base_rotation']; bv = base['values']; finite(bv)
    require(base['schema'] == 'guitar_learning.gpu_left_finger_base_rotation.v1' and
            base['body_names'] == BASE_NAMES and base['sampling_hz'] == 60 and base['endpoint_samples'] == steps,
            'Base pose identity/sampling')
    require(set(bv) == set(BASE_FIELDS) and all(len(v) == 4 for v in bv.values()), 'Base pose six fields/four fingers')
    for i in range(4):
        for rms, maximum in zip(BASE_FIELDS[::2], BASE_FIELDS[1::2]):
            require(0 <= bv[rms][i] <= bv[maximum][i]+2e-6, 'Base pose RMS/max bounds')
        require(bv[BASE_FIELDS[4]][i] <= bv[BASE_FIELDS[2]][i]+2e-6 and
                bv[BASE_FIELDS[5]][i] <= bv[BASE_FIELDS[3]][i]+2e-6, 'Projected/full rotation error order')
    values = row['values']; finite(values)
    require(set(values) == set(MOTION_FIELDS) and all(len(v) == 21 for v in values.values()), 'Motion fields/left21')
    for j, name in enumerate(LEFT_HAND_NAMES):
        action_id = ACTIVE_NAMES.index(name)
        for kind in ('actual', 'target'):
            lo, hi, span = (values[kind+key][j] for key in ('_min_rad', '_max_rad', '_range_rad'))
            require(hi >= lo and math.isclose(hi-lo, span, rel_tol=2e-5, abs_tol=2e-6), 'Motion range/extrema')
        require(values['target_min_rad'][j] >= control['action_lower_rad'][action_id]-2e-6 and
                values['target_max_rad'][j] <= control['action_upper_rad'][action_id]+2e-6, 'Native target boundary')
        fractions = [values['action_'+kind+'_fraction'][j] for kind in ('positive', 'negative', 'zero')]
        require(all(0 <= v <= 1 for v in fractions) and math.isclose(sum(fractions), 1., abs_tol=2e-6), 'Motion direction fractions')
        require(-1 <= values['action_mean'][j] <= 1 and
                abs(values['action_mean'][j]) <= values['action_mean_abs'][j]+2e-6 and
                0 <= values['action_mean_abs'][j] <= 1, 'Bounded action moments')
        require(0 <= values['action_mean_abs_change'][j] <= 2 and
                0 <= values['action_opposite_sign_fraction'][j] <= 1 and
                0 <= values['limit_outward_command_fraction'][j] <= 1, 'Motion action change/limit fractions')
        require(0 <= values['tracking_error_rms_rad'][j] <= values['tracking_error_max_abs_rad'][j]+2e-6,
                'Motion tracking error RMS/max')
        if steps == 1:
            require(values['action_mean_abs_change'][j] == values['action_opposite_sign_fraction'][j] == 0,
                    'No artificial reset action-change pair')



def raw_rows(path, final_mode, diagnostics):
    if not final_mode:
        # This reader yields only after the current gzip member passed CRC.
        with closing(iter_transitions(path, strict=True, diagnostics=diagnostics)) as stream:
            yield from stream
        return
    # Final mode also rejects blank/non-terminated JSONL rows, then reaches EOF.
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            require(line.endswith('\n'), 'Incomplete final raw JSONL row')
            yield json.loads(line)
    diagnostics['complete'] = True


def same(a, b):
    if isinstance(a, torch.Tensor):
        return isinstance(b, torch.Tensor) and a.dtype == b.dtype and torch.equal(a, b)
    if isinstance(a, np.ndarray):
        return isinstance(b, np.ndarray) and a.dtype == b.dtype and np.array_equal(a, b)
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)):
        return isinstance(b, type(a)) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def restore_boundary(parent, initial):
    require(same({k: v for k, v in parent.items() if k != 'metadata'},
                 {k: v for k, v in initial.items() if k != 'metadata'}),
            'Strict resume nonmetadata state mismatch')


def verify(run, phase, updates=None, prefix=None, parent_checkpoint=None):
    settings, contract = (read(run/name) for name in ('settings.json', 'training_contract.json'))
    expected_updates = settings['updates'] if updates is None else updates
    require(settings['updates'] == expected_updates, 'Requested run budget differs from settings')
    updates = expected_updates if prefix is None else prefix
    require(type(updates) is int and 0 < updates <= expected_updates, 'Positive prefix within run budget required')
    final_mode = prefix is None
    report = read(run/'report.json') if final_mode else None
    control = verify_codec(contract)
    require((settings['size'], settings['num_envs'], settings['horizon'], settings['updates'], settings['seed']) ==
            ('large', ENVS, HORIZON, expected_updates, 7), 'Expected fresh large1024/H32/seed7 budget')
    require(settings['checkpoint_every'] == 100, 'Expected checkpoint100 budget')
    require(settings['specialist']['role'] == 'left' and settings['device'] == 'cuda:0' and settings['song']['left_fraction'] == .4, 'Left GPU/song settings')
    require(settings['song_training']['observation_dimension'] == 544, 'Settings left544 inputs')
    verify_ppo_config(settings['ppo'])
    require(settings['song']['surface_approach_gamma'] == settings['ppo']['gamma'], 'PBRS/PPO discount equality')
    offset = 0
    parent = None
    if parent_checkpoint is not None:
        require(prefix is None and expected_updates == 1, 'Strict resume audit is a separate completed one-update run')
        parent = torch.load(parent_checkpoint, map_location='cpu', weights_only=False)
        finite(parent)
        offset = parent['updates']
    if final_mode:
        require(report.get('completed') is True and report['failure'] is None and report['stopped'] == 'updates_complete', 'Training incomplete/failed')
        require(not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'], 'Run integrity errors')
        require(settings == report['settings'], 'Report/settings mismatch')
        require(report['optimizer_updates'] == offset+updates and report['transitions'] == updates*HORIZON*ENVS, 'Update/transition totals')
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
    require(manifest['active_python_count'] == len(source) == 438, 'Frozen438 source count')
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
    verify_architecture(initial['identity']['architecture'])
    require(initial['identity']['architecture']['contract'] == contract and initial['identity']['config'] == settings['ppo'],
            'Fresh initial checkpoint contract/config')
    if parent is None:
        require(initial['updates'] == 0 and not initial['actor_optimizer']['state'] and not initial['value_optimizer']['state'], 'Expected fresh optimizer state')
        require(bool((initial['model']['log_std'][:33] == -3.).all()) and
                bool((initial['model']['actor_heads.left.weight'] == 0).all()) and
                bool((initial['model']['actor_heads.left.bias'] == 0).all()), 'Expected fresh shared zero-mean/default-std actor')
        for finger in ('index', 'middle', 'ring', 'pinky'):
            require(all(bool((initial['model']['finger_heads.'+finger+'.2.'+key] == 0).all())
                        for key in ('weight', 'bias')), 'Expected fresh zero-mean finger output')
    else:
        restore_boundary(parent, initial)
    from guitar_learning.song.gpu_left_curriculum import CurriculumState
    counts = [sum(t['finger'] == f for t in schedule) for f in range(1, 5)]
    curriculum = CurriculumState(counts)
    if parent is None:
        require(np.array_equal(initial['model']['left_curriculum_state'].numpy(), curriculum.state_vector()), 'Expected fresh3331 curriculum')
    else:
        curriculum.load_state(initial['model']['left_curriculum_state'].numpy())
    if final_mode:
        expected_checkpoints={('checkpoint_%06d.pt'%(i-1)) for i in range(settings['checkpoint_every'],updates,settings['checkpoint_every'])}
        require({p.name for p in run.glob('checkpoint_*.pt')} == expected_checkpoints, 'Checkpoint100 file sequence')
        require(len(report['updates']) == len(list(run.glob('update_*.json'))) == updates, 'Update file/report counts')
    checkpoint = (run/'final.pt' if final_mode else next((path for count, path in sorted(
        [(int(path.stem.split('_')[-1])+1, path) for path in run.glob('checkpoint_*.pt')
         if int(path.stem.split('_')[-1])+1 <= updates], reverse=True)), run/'initial.pt'))
    checkpoint_update = updates if final_mode else (int(checkpoint.stem.split('_')[-1])+1 if checkpoint.name != 'initial.pt' else 0)
    checkpoint_curriculum = curriculum.state_vector().copy() if checkpoint_update == 0 else None
    metrics, logged = iter(lines(run/'learning_metrics.jsonl')), iter(lines(run/'episodes.jsonl'))
    totals = Counter(all=0, physical_failure=0, timeline_complete=0, stage_success=0)
    raw_count = max_episode_error = max_update_error = max_center_tolerance = 0
    raw_status = {}
    with closing(raw_rows(run/'transitions.jsonl.gz', final_mode, raw_status)) as stream:
        for index in range(updates):
            row = read(run/('update_%06d.json' % index))
            finite(row)
            require(row['update_index'] == index and row['optimizer_updates'] == offset+index+1 and row['transitions'] == HORIZON*ENVS and
                    row['physics_steps'] == (index+1)*HORIZON*4, 'Update sequence')
            journal(row['journal'], index+1, False)
            max_center_tolerance = max(max_center_tolerance, verify_advantages(row['diagnostics']['advantages']))
            if final_mode:
                require(all(report['updates'][index][key] == row[key] for key in report['updates'][index]), 'Report/update summary')
            require(encoded(next(metrics, None)) == encoded(row), 'Metrics/update correspondence')
            parts = row['reward_component_means']
            require(set(parts) == set(REWARD_KEYS+RIGHT_KEYS) and all(parts[k] == 0 for k in RIGHT_KEYS), 'Update reward fields/right zeros')
            verify_rate_components(parts, 1/60.)
            max_update_error = max(max_update_error, component_sum(parts, row['mean_reward'], 'Update reward'))
            expected_hash, logged_hash, raw_hash = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
            episodes = row['completed_episodes']
            for episode in episodes:
                max_episode_error = max(max_episode_error, verify_episode(episode, schedule, duration, control))
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
            if index+1 == checkpoint_update:
                checkpoint_curriculum = curriculum.state_vector().copy()
            reward_sum = cost_sum = raw_episodes = 0
            for tick in range(HORIZON):
                raw = next(stream, None)
                require(raw is not None, 'Missing CRC-verified gzip row')
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
        if final_mode:
            require(next(stream, None) is None and raw_status['complete'], 'Extra gzip data; EOF/CRC verification failed')
    if final_mode:
        require(next(metrics, None) is None and next(logged, None) is None, 'Extra metric/episode log rows')
        if parent is None and updates*HORIZON >= 1969:
            require(totals['timeline_complete'] > 0, 'No whole-song timeline completion')
        song = read(run/'song_report.json')
        require(song['completed'] is True and song['partial_trajectories_are_successes'] is False and
                song['completed_episodes'] == report['completed_episodes'] == totals['all'] and
                all(song['episode_counts'][k] == totals[k] for k in ('physical_failure', 'timeline_complete', 'stage_success')), 'Final song counters')
    final = torch.load(checkpoint, map_location='cpu', weights_only=False)
    verify_architecture(final['identity']['architecture'])
    require(final['updates'] == offset+checkpoint_update and final['identity']['architecture']['contract'] == contract and final['identity']['config'] == settings['ppo'], 'Final checkpoint identity/updates')
    require(math.isfinite(final['cost_weight']) and final['cost_weight'] >= 0, 'Checkpoint cost weight')
    tensor_counts = {k: finite(final[k]) for k in ('model', 'actor_optimizer', 'value_optimizer')}
    require(tensor_counts['model'] and (checkpoint_update == 0 or
            (tensor_counts['actor_optimizer'] and tensor_counts['value_optimizer'] and final['actor_optimizer']['state'] and final['value_optimizer']['state'])), 'Checkpoint optimizer/model state')
    saved = final['model']['left_curriculum_state'].numpy()
    require(saved.shape == (3331,) and np.allclose(saved, checkpoint_curriculum, rtol=1e-10, atol=1e-12), 'Final3331 curriculum replay')
    restored = CurriculumState(counts)
    restored.load_state(saved)
    if parent is not None:
        require(not same(initial['model'], final['model']) and
                all(not same(initial[key], final[key]) for key in ('actor_optimizer', 'value_optimizer')),
                'Resume model/both optimizers did not update')
    boundaries, reasons = [], Counter()
    for event in lines(run/'events.jsonl', live_tail=not final_mode):
        if prefix is not None and event.get('update_index') is not None and event['update_index'] >= updates:
            break
        if event.get('event') == 'cuda_cache_release':
            require(event['after']['free_bytes'] >= 1024**3, 'GPU floor after cache recovery')
            reasons[event['reason']] += 1
            if event['reason'] == 'optimizer_boundary':
                boundaries.append((event['update_index'], event['after']))
    require([i for i, _ in boundaries] == list(range(updates)), 'Cache boundary sequence')
    free = [v['free_bytes'] for _, v in boundaries]
    base = free[0]+boundaries[0][1]['reserved_bytes']
    growth = [base-v['free_bytes']-v['reserved_bytes'] for _, v in boundaries]
    if final_mode:
        require(report['resources']['cuda_free_guard_sample_min_bytes'] >= 1024**3, 'GPU resource floor')
    ram_floor = int(settings['min_available_memory_gib']*1024**3)
    ram_min = None
    for row in lines(run/'resources.jsonl', live_tail=not final_mode):
        if prefix is not None and row.get('update_index') is not None and row['update_index'] >= updates:
            break
        require(row['low_memory'] is None and row['available_memory_bytes'] >= ram_floor, 'RAM resource floor')
        ram_min = row['available_memory_bytes'] if ram_min is None else min(ram_min, row['available_memory_bytes'])
    require(ram_min is not None, 'Missing RAM samples')
    return dict(schema='guitar_learning.long_training_v8_verification.v1', run=str(run.resolve()),
                training_contract_sha256=digest(run/'training_contract.json'), source_manifest_sha256=digest(phase/'training_source_manifest.json'), completed=final_mode, prefix_verified=not final_mode, scope=__doc__.strip(), committed_updates=updates,
                committed_transitions=updates*HORIZON*ENVS, raw_rows=raw_count, raw_gzip_CRC_EOF=final_mode, selected_raw_rows_in_CRC_verified_members=True,
                exact_episode_log_correspondence=True, ended_episode_counts=dict(totals), input_pins=len(pins),
                frozen_python_verified=len(source), finite_checkpoint_tensors=tensor_counts,
                curriculum_values=3331, curriculum_replay_max_abs_error=float(np.max(np.abs(saved-checkpoint_curriculum))),
                max_episode_reward_sum_abs_error=max_episode_error, max_update_reward_sum_abs_error=max_update_error,
                reward_sum_tolerance=dict(episode=dict(rel_tol=1e-4, abs_tol=1e-3), update=dict(rel_tol=1e-5, abs_tol=1e-6)),
                PPO_reported_nonfinite_counts_zero=True, GPU_lifecycle_verified=final_mode, incremental_codec_verified=True, observation_dimension=544, priority_slots=8,
                reward_v8_contract_verified=True, new_reward_rate_bounds_verified=True, left_finger_motion_contract_verified=True, left_finger_motion_verified=totals['all']>0,
                left_finger_base_pose_verified=totals['all']>0, motion_episodes_checked=totals['all'],
                memory=dict(post_cache_free_min_GiB=min(free)/1024**3, post_cache_free_final_GiB=free[-1]/1024**3,
                            estimated_nonTorch_growth_final_GiB=growth[-1]/1024**3,
                            estimated_nonTorch_growth_max_GiB=max(growth)/1024**3,
                            estimated_nonTorch_last100_range_GiB=(max(growth[-100:])-min(growth[-100:]))/1024**3,
                            RAM_min_GiB=ram_min/1024**3, cache_release_reasons=dict(reasons)),
                checkpoint_updates=checkpoint_update, final_checkpoint_sha256=digest(checkpoint) if final_mode else None,
                optimizer_updates=offset+updates, starting_optimizer_updates=offset,
                separate_advantages_verified=True, gae_lambda=.98, targeted_finger_actor_verified=True,
                advantage_numeric_checks=dict(production_dtype='float32', summary_dtype='float64',
                    mean_roundoff_budget='max(2e-5,8*float32_eps*raw_magnitude/max(raw_std,1e-8))',
                    maximum_center_mean_tolerance=max_center_tolerance,
                    scope='Summary bounds only; source-scale cancellation allowed, not per-sample GAE reconstruction'),
                exact_nonmetadata_resume=parent is not None,
                parent_checkpoint_sha256=digest(parent_checkpoint) if parent_checkpoint is not None else None,
                physical_resume='new prepared environment episodes; no simulator state restore' if parent is not None else None,
                checked_checkpoint_path=str(checkpoint), checked_checkpoint_sha256=digest(checkpoint))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--run', type=Path, help='Fresh completed run or live prefix; defaults to the external v8 train2000 path')
    parser.add_argument('--updates', type=int, help='Expected total run budget, e.g.100 or2000')
    parser.add_argument('--prefix', type=int, help='Audit exactly N committed updates; no final close/whole gzip claim')
    parser.add_argument('--resume', type=Path, help='Also verify a separate strict one-update resume from the completed final checkpoint')
    parser.add_argument('--parent-checkpoint', type=Path,
                        help='Audit only --run as a one-update strict resume; parent execution requires its separate verification')
    args = parser.parse_args()
    phase = args.phase.resolve()
    output = args.out or phase/('training_verification.json' if args.prefix is None else 'verification_prefix_%06d.json' % args.prefix)
    require(not output.exists(), 'Refusing to overwrite verification output')
    torch.set_num_threads(1)
    require(not (args.resume and args.parent_checkpoint), 'Choose combined or resume-only verification')
    result = verify((args.run or DEFAULT_RUN).resolve(), phase, args.updates, args.prefix,
                    args.parent_checkpoint.resolve() if args.parent_checkpoint else None)
    if args.resume is not None:
        require(args.prefix is None and result['completed'], 'Resume proof requires a completed parent run')
        result['strict_resume_one_update'] = verify(args.resume.resolve(), phase, 1,
            parent_checkpoint=(args.run or DEFAULT_RUN).resolve()/'final.pt')
        result['resume_transitions_excluded_from_training_budget'] = HORIZON*ENVS
    with output.open('x') as stream:
        json_io.dump(result, stream, indent=2, allow_nan=False)
    print(json_io.dumps(result, indent=2))


if __name__ == '__main__':
    main()
