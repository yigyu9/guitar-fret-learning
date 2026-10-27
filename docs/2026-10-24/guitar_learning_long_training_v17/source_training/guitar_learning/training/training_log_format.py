"""Training-only detail reduction; evaluation and environment info stay intact."""
import copy
import numpy as np


def contract(detail):
    return dict(schema='guitar_learning.training_log_format.v2', detail=detail,
        transition_hz=60, physics_summary_hz=240,
        episode_and_tick_indices='zero based, local to each worker/run',
        omitted_in_standard=['debug.action', 'resource', 'specialist.timing duplicate',
            'per-tick timing/skill config and strike preparation descriptions',
            'per-tick contact feature diagnostics'],
        retained_evidence='full terminal episode; first tick, classification change and physical failure raw samples',
        timing_reference='specialist.timing_ref refers to same info.timing; full config in training_contract.json',
        safety='safety240 reduces every native substep; stability remains last-substep endpoint',
        action='active-hand statistics, not evidence of physical pick grasp')


def classification_signature(info):
    q = info.get('musical_quality', {}).get('fretting_state', {})
    quality=info.get('musical_quality',{})
    role=quality.get('role',info.get('specialist',{}).get('role','joint'))
    fret=tuple(q.get(key) for key in ('status', 'wrong_assignment', 'wrong_finger', 'higher_fret'))
    strike=quality.get('strike',{})
    right=(len(strike.get('accepted_crossing_ids',[])),strike.get('unprepared_count'),strike.get('extra_count'),
        len(strike.get('blocked_event_ids',[])),strike.get('ready'),strike.get('recovered'),
        info.get('timing',{}).get('wrong_crossings'))
    return fret if role=='left' else right if role=='right' else fret+right


def format_info(info, action, *, detail='standard'):
    if detail not in ('standard', 'diagnostic'):
        raise ValueError('standard or diagnostic training log detail required')
    result = copy.deepcopy(info)
    role = result.get('musical_quality', {}).get('role', result.get('specialist', {}).get('role', 'joint'))
    active = np.asarray(action)[slice(0, 33) if role == 'left' else slice(33, 39) if role == 'right' else slice(None)]
    result['action_summary'] = dict(role=role, active_channels=int(active.size),
        active_nonzero=bool(np.any(np.abs(active) > 1e-8)),
        mean_abs=float(np.abs(active).mean()), max_abs=float(np.abs(active).max()),
        saturation_fraction=float(np.mean(np.abs(active) >= .99)))
    if detail == 'diagnostic':
        return result
    terminal=copy.deepcopy(result['episode']) if 'episode' in result else None
    result.pop('debug', None)
    specialist = result.get('specialist', {})
    if 'timing' in specialist:
        specialist.pop('timing')
        specialist['timing_ref'] = 'timing'
    specialist.get('skill', {}).pop('config', None)
    timing = result.get('timing', {})
    for key in ('config', 'scope', 'success_criterion'):
        timing.pop(key, None)
    quality = result.get('musical_quality', {})
    quality.get('strike', {}).pop('preparation', None)
    quality.get('fretting_state', {}).pop('feature_diagnostics', None)
    # A terminal quality snapshot is needed by legacy summaries. Its full
    # evidence lives in episode, with per-tick numeric quality still available.
    if terminal is not None:
        result['episode']=terminal
        if 'musical_quality' in terminal:
            result['musical_quality'] = copy.deepcopy(terminal['musical_quality'])
    return result
