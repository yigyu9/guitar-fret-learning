"""Read-only learning diagnostics; no reward, termination or success decisions."""
import copy
import math
from collections import Counter

import numpy as np


CONTACT_NAMES = ('chest', 'right_upper_arm', 'right_thigh', 'any_support',
                 'triple_support', 'left_foot', 'right_foot', 'both_feet')


def quality_tick_summary(physics_measurements, target):
    """First actual sample stamps, not inferred release dwell or audio events."""
    first_clean = first_clear = None
    sample_count = 0
    for row in physics_measurements:
        measured = row['music']
        q = measured['targets'][target.target_id]['fretting_quality']
        now = float(measured['task_time_s'])
        sample_count += 1
        if q['clean_target_candidate'] and first_clean is None:
            first_clean = now
        if now >= target.end_s and not q['target_string_contact_evidence_ids'] and first_clear is None:
            first_clear = now
    return dict(schema='guitar_learning.quality_tick_metrics.v1', physics_hz=240,
        sample_count=sample_count, target_id=target.target_id, note_end_s=float(target.end_s),
        first_clean_policy_s=first_clean, first_post_note_clear_policy_s=first_clear,
        scope='first actual240Hz clear sample; not sustained release completion or acoustic clearance')


def safety_tick_summary(physics_measurements):
    """Summarize every actual 240Hz sample, retaining run boundaries for merging."""
    rows = list(physics_measurements)
    if not rows:
        raise ValueError('actual physics measurements required')
    steps = [int(row['physics_step']) for row in rows]
    if any(b != a+1 for a, b in zip(steps, steps[1:])):
        raise ValueError('consecutive physics samples required')
    safety = [row['stability'] for row in rows]
    flags = np.asarray([row['flags'] for row in safety], dtype=float)
    if flags.shape != (len(rows), 10) or not np.isfinite(flags).all():
        raise ValueError('ten finite measured contact flags required')
    def vectors(name, shape):
        values = np.asarray([row[name] for row in safety], dtype=float)
        if values.shape != (len(rows), *shape) or not np.isfinite(values).all():
            raise ValueError('finite measured safety vectors required')
        return values
    delta = vectors('guitar_delta_m', (3,))
    rotation = vectors('guitar_rotation_vector_rad', (3,))
    feet = vectors('foot_delta_m', (2, 3))
    speed = np.asarray([row['max_joint_speed_rad_s'] for row in safety], dtype=float)
    if not np.isfinite(speed).all():
        raise ValueError('finite joint speed required')
    present = flags > 0
    columns = [present[:, 0], present[:, 1], present[:, 2], present[:, :3].any(1),
               present[:, :3].all(1), present[:, -2], present[:, -1], present[:, -2:].all(1)]
    contacts = {}
    for name, column in zip(CONTACT_NAMES, columns):
        absent = (~column).tolist()
        prefix = next((i for i, value in enumerate(absent) if not value), len(rows))
        suffix = next((i for i, value in enumerate(reversed(absent)) if not value), len(rows))
        run = longest = 0
        for value in absent:
            run = run+1 if value else 0
            longest = max(longest, run)
        contacts[name] = dict(absent_s=sum(absent)/240., prefix_absent_s=prefix/240.,
            suffix_absent_s=suffix/240., longest_absent_s=longest/240., all_absent=all(absent))
    return dict(schema='guitar_learning.safety_tick_metrics.v1', physics_hz=240,
        sample_count=len(rows), duration_s=len(rows)/240., first_physics_step=steps[0],
        last_physics_step=steps[-1], contacts=contacts,
        maxima=dict(guitar_displacement_m=float(np.linalg.norm(delta, axis=1).max()),
            guitar_rotation_rad=float(np.linalg.norm(rotation, axis=1).max()),
            left_foot_displacement_m=float(np.linalg.norm(feet[:, 0], axis=1).max()),
            right_foot_displacement_m=float(np.linalg.norm(feet[:, 1], axis=1).max()),
            joint_speed_rad_s=float(speed.max())))


def _merge_safety(total, tick):
    if total is None:
        return copy.deepcopy(tick)
    if tick['first_physics_step'] != total['last_physics_step']+1:
        raise ValueError('episode safety240 samples must be consecutive')
    for key, value in tick['maxima'].items():
        total['maxima'][key] = max(total['maxima'][key], value)
    for key, new in tick['contacts'].items():
        old = total['contacts'][key]
        old['longest_absent_s'] = max(old['longest_absent_s'], new['longest_absent_s'],
                                      old['suffix_absent_s']+new['prefix_absent_s'])
        old['prefix_absent_s'] += new['prefix_absent_s'] if old['all_absent'] else 0.
        old['suffix_absent_s'] = old['suffix_absent_s']+new['suffix_absent_s'] if new['all_absent'] else new['suffix_absent_s']
        old['all_absent'] = old['all_absent'] and new['all_absent']
        old['absent_s'] += new['absent_s']
    total['sample_count'] += tick['sample_count']
    total['duration_s'] += tick['duration_s']
    total['last_physics_step'] = tick['last_physics_step']
    return total


def _add(total, values):
    for key, value in values.items():
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('finite metric contributions required')
        total[key] = total.get(key, 0.)+value


class LearningMetrics:
    """Aggregate interval contributions and terminal ledgers independently.

    observe accepts the existing multi-worker transition row, returns newly
    closed episode records for the caller to append/flush. No file IO is done.
    Open episodes survive update_summary; cumulative ledgers are never summed.
    """
    def __init__(self, settings=None):
        self.settings = copy.deepcopy(settings or {})
        self.active, self.next_episode = {}, Counter()
        self.window_episodes = []
        self.episode_counts, self.groups = self._empty_counts(), {}
        self.totals = self._empty()
        self.window = self._empty()

    @staticmethod
    def _empty():
        return dict(transitions=0, reward=0., cost=0., reward_terms={},
            preparation=dict(total_logged_transitions=0, first2s_logged_transitions=0,
                first2s_nonzero_action_transitions=0, first2s_action_observed_transitions=0,
                first2s_reward_terms={}))

    @staticmethod
    def _empty_counts():
        return dict.fromkeys(('completed_episodes', 'incomplete_closed_episodes', 'invalid_episodes',
            'timeout_episodes', 'physical_failure_episodes', 'time_limit_episodes',
            'timing_only_successful_episodes', 'quality_successful_episodes',
            'specialist_successful_episodes', 'timing_successful_episodes',
            'timing_evaluated_episodes', 'quality_evaluated_episodes',
            'specialist_evaluated_episodes', 'timing_stage_evaluated_episodes'), 0)

    @staticmethod
    def _count_episode(counts, groups, row):
        valid = row['complete'] and row['valid'] is True
        counts['completed_episodes'] += valid
        counts['incomplete_closed_episodes'] += not valid
        counts['invalid_episodes'] += row['valid'] is False
        counts['timeout_episodes'] += 'timeout' in row['reason']
        counts['physical_failure_episodes'] += row['physical_failure']
        counts['time_limit_episodes'] += row['reason'] == 'time_limit'
        if not valid:
            return
        key = (row['role'], row['stage_index'], row['window_s'], tuple(row['goal_ids']))
        group = groups.setdefault(key, dict(role=row['role'], stage_index=row['stage_index'],
            window_s=row['window_s'], goal_ids=list(row['goal_ids']), episodes=0,
            timing_only_successes=0, quality_successes=0, specialist_successes=0, timing_successes=0,
            timing_evaluated_episodes=0, quality_evaluated_episodes=0,
            specialist_evaluated_episodes=0, timing_stage_evaluated_episodes=0,
            joint_evaluated_episodes=0, joint_target_count=0, joint_matched50=0, joint_matched100=0))
        group['episodes'] += 1
        for field, successful, evaluated, group_success in (
                ('timing_only_success', 'timing_only_successful_episodes', 'timing_evaluated_episodes', 'timing_only_successes'),
                ('quality_stage_success', 'quality_successful_episodes', 'quality_evaluated_episodes', 'quality_successes'),
                ('specialist_stage_success', 'specialist_successful_episodes', 'specialist_evaluated_episodes', 'specialist_successes'),
                ('timing_stage_success', 'timing_successful_episodes', 'timing_stage_evaluated_episodes', 'timing_successes')):
            counts[successful] += row[field] is True
            counts[evaluated] += row[field] is not None
            group[group_success] += row[field] is True
            group[evaluated] += row[field] is not None
        joint = row['joint_music']
        if all(joint[key] is not None for key in ('target_count', 'matched50', 'matched100')):
            group['joint_evaluated_episodes'] += 1
            for target, source in (('joint_target_count', 'target_count'),
                    ('joint_matched50', 'matched50'), ('joint_matched100', 'matched100')):
                group[target] += joint[source]

    def _start(self, worker, info):
        timing = info.get('timing', {})
        specialist = info.get('specialist', {})
        role = info.get('musical_quality', {}).get('role', specialist.get('role',
                    self.settings.get('specialist', {}).get('role')))
        goals = list(specialist.get('left', {}).get('targets', {}))
        target_id=info.get('musical_quality', {}).get('strike', {}).get('target_id')
        if not goals and target_id:goals=[target_id]
        return dict(worker_id=worker, episode_id=self.next_episode[worker], ticks=0,
            reward=0., cost=0., reward_terms={}, safety240=None, safety240_ticks=0,
            role=role, stage_index=timing.get('config', self.settings.get('timing', {})).get('stage_index'),
            window_s=timing.get('window_s'), goal_ids=goals, last_time_s=None,
            first_clear_observed_policy_s=None, first_clean_actual_policy_s=None,
            first_post_note_clear_actual_policy_s=None, note_end_s=None, last_info={})

    def _record(self, worker, *, complete, reason):
        state = self.active.pop(worker)
        info = state.pop('last_info')
        q, timing, music = (info.get(key, {}) for key in ('musical_quality', 'timing', 'music'))
        terminal = info.get('episode', {})
        state.update(complete=complete, reason=reason,
            valid=terminal.get('valid') if terminal else None,
            physical_failure=bool(info.get('failure_reasons') or reason == 'terminal_failure'),
            failure_reasons=copy.deepcopy(info.get('failure_reasons', [])),
            timing_only_success=timing.get('timing_only_stage_success', q.get('timing_achievement', timing.get('stage_success'))) if complete else None,
            quality_stage_success=q.get('stage_success') if complete else None,
            specialist_stage_success=info.get('specialist', {}).get('stage_success') if complete else None,
            timing_stage_success=timing.get('stage_success') if complete else None,
            joint_music={key: copy.deepcopy(music.get(key)) for key in
                         ('target_count', 'matched50', 'matched100', 'missed_strict')},
            cumulative_quality=copy.deepcopy(q),
            first_clear_observation_resolution_s=1/60.,
            release_delay_scope='first positive clear-dwell observed at60Hz; not exact240Hz release latency',
            safety240_scope='all actual substeps for recorded ticks; no60Hz fallback',
            safety240_complete=state['safety240_ticks'] == state['ticks'])
        at, end = state['first_post_note_clear_actual_policy_s'], state['note_end_s']
        delay = None if at is None or end is None else at-end
        state['first_post_note_clear_delay_s'] = delay
        state['first_post_note_clear_delay_ms'] = None if delay is None else delay*1000.
        if end is not None:
            state['release_delay_scope'] = 'first actual240Hz clear sample after note end; not sustained release or late contact occupancy'
        if state['role'] == 'left':
            state['left'] = {key: copy.deepcopy(q.get(key)) for key in
                ('clean_audible_fraction', 'wrong_press_s', 'missing_press_s', 'audible_wrong_s',
                 'dropouts', 'release_complete', 'release_clear_dwell_s', 'release_late_s')}
            state['right'] = None
        elif state['role'] == 'right':
            strike = q.get('strike', {})
            accepted = list(dict.fromkeys(strike.get('accepted_crossing_ids', [])))
            extra = set(strike.get('extra_crossing_ids', []))
            unprepared = set(strike.get('unprepared_crossing_ids', []))
            blocked = set(strike.get('blocked_event_ids', []))
            accepted_rows = [row for row in timing.get('crossings', [])
                             if row.get('crossing_id') in accepted]
            first = accepted_rows[0] if accepted_rows else None
            state['right'] = dict(accepted_crossing_ids=accepted,
                first_accepted_crossing=copy.deepcopy(first),
                first_accepted_signed_error_s=None if first is None else first['error_s'],
                best_accepted_abs_error_s=min((abs(row['error_s']) for row in accepted_rows), default=None),
                timing_best_abs_error_s=timing.get('best_abs_error_s'),
                wrong_crossings=timing.get('wrong_crossings'), extra_count=strike.get('extra_count'),
                unprepared_count=strike.get('unprepared_count'),
                other_blocked_count=len(blocked-extra-unprepared),
                distinct_blocked_ids=sorted(blocked), recovered=strike.get('recovered'),
                ready=strike.get('ready'), ready_dwell_s=strike.get('ready_dwell_s'),
                recovery_dwell_s=strike.get('recovery_dwell_s'))
            state['left'] = None
        else:
            state['left'] = state['right'] = None
        self.next_episode[worker] += 1
        self._count_episode(self.episode_counts, self.groups, state)
        self.window_episodes.append(state)
        return copy.deepcopy(state)

    def observe(self, row):
        infos = row['infos']
        arrays = [np.atleast_1d(row[key]) for key in ('reward', 'terminated', 'truncated')]
        if any(len(value) != len(infos) for value in arrays):
            raise ValueError('one reward and done flag per worker required')
        closed = []
        for worker, info in enumerate(infos):
            now = float(info['task_time_s'])
            if not math.isfinite(now):
                raise ValueError('finite policy clock required')
            previous = self.active.get(worker)
            if previous and previous['last_time_s'] is not None and now <= previous['last_time_s']:
                closed.append(self._record(worker, complete=False, reason='reset_without_terminal'))
            if worker not in self.active:
                self.active[worker] = self._start(worker, info)
            state = self.active[worker]
            reward, cost = float(arrays[0][worker]), float(info['cost'])
            terms = info.get('reward_terms', {})
            for total in (state, self.totals, self.window):
                key = 'ticks' if total is state else 'transitions'
                total[key] += 1
                _add(total, dict(reward=reward, cost=cost))
                _add(total['reward_terms'], terms)
            for total in (self.totals, self.window):
                prep = total['preparation']
                prep['total_logged_transitions'] += 1
                if now <= 2.+1e-12:
                    prep['first2s_logged_transitions'] += 1
                    _add(prep['first2s_reward_terms'], terms)
                    active_nonzero = info.get('action_summary', {}).get('active_nonzero')
                    if active_nonzero is None and 'action' in info.get('debug', {}):
                        action = np.asarray(info['debug']['action'])
                        active = action[:33] if state['role'] == 'left' else action[33:] if state['role'] == 'right' else action
                        active_nonzero = bool(np.any(active != 0))
                    if active_nonzero is not None:
                        prep['first2s_action_observed_transitions'] += 1
                        prep['first2s_nonzero_action_transitions'] += bool(active_nonzero)
            if info.get('safety240') is not None:
                state['safety240'] = _merge_safety(state['safety240'], info['safety240'])
                state['safety240_ticks'] += 1
            if info.get('quality240') is not None:
                quality = info['quality240']
                state['note_end_s'] = quality['note_end_s']
                for dest, source in (('first_clean_actual_policy_s', 'first_clean_policy_s'),
                        ('first_post_note_clear_actual_policy_s', 'first_post_note_clear_policy_s')):
                    if state[dest] is None and quality[source] is not None:
                        state[dest] = quality[source]
            q = info.get('musical_quality', {})
            if state['role'] == 'left' and q.get('release_clear_dwell_s', 0.) > 0 and state['first_clear_observed_policy_s'] is None:
                state['first_clear_observed_policy_s'] = now
            state['last_time_s'], state['last_info'] = now, copy.deepcopy(info)
            if bool(arrays[1][worker]) or bool(arrays[2][worker]):
                reason = info.get('termination_reason') or info.get('episode', {}).get('reason') or 'unknown_done'
                closed.append(self._record(worker, complete='episode' in info, reason=reason))
        return closed

    def close_incomplete(self, reason='interrupted'):
        """Explicit caller notification; never infer worker timeout from silence."""
        return [self._record(worker, complete=False, reason=reason) for worker in list(self.active)]

    def _report(self, totals, counts, groups, episodes=None):
        result = copy.deepcopy(totals)
        result.update(counts)
        result.update(schema='guitar_learning.learning_metrics.v1',
            open_episodes=[dict(worker_id=row['worker_id'], episode_id=row['episode_id'],
                                ticks=row['ticks'], last_time_s=row['last_time_s']) for row in self.active.values()],
            scope='interval sums; terminal cumulative quality once per episode; inactive hand summaries null')
        if episodes is not None:
            result['episodes'] = copy.deepcopy(episodes)
        result['groups'] = copy.deepcopy(list(groups.values()))
        result['quality_success_rate']=(result['quality_successful_episodes']/result['quality_evaluated_episodes']
            if result['quality_evaluated_episodes'] else None)
        result['timing_only_success_rate']=(result['timing_only_successful_episodes']/result['timing_evaluated_episodes']
            if result['timing_evaluated_episodes'] else None)
        result['specialist_success_rate']=(result['specialist_successful_episodes']/result['specialist_evaluated_episodes']
            if result['specialist_evaluated_episodes'] else None)
        result['timing_success_rate']=(result['timing_successful_episodes']/result['timing_stage_evaluated_episodes']
            if result['timing_stage_evaluated_episodes'] else None)
        return result

    def update_summary(self, reset_window=True):
        counts, groups = self._empty_counts(), {}
        for episode in self.window_episodes:
            self._count_episode(counts, groups, episode)
        result = self._report(self.window, counts, groups, self.window_episodes)
        if reset_window:
            self.window, self.window_episodes = self._empty(), []
        return result

    def summary(self):
        return self._report(self.totals, self.episode_counts, self.groups)
