"""Independent hand objectives with the original native stability contract.

Left success is a measured contact-candidate dwell, right success is a timed
geometric crossing. Neither is sound or an integrated musical performance.
"""
import copy
from dataclasses import asdict, dataclass
from unittest.mock import patch
import numpy as np
from . import training_environment
from .training_environment import TrainingEnvironment
from .persistent_environment import PersistentContactEnvironment, _CONSTRUCTION_LOCK
from .music_task import ScoreTask
from .dense_environment import DenseRewardConfig, shaping_sample, pick_guide_evidence


@dataclass(frozen=True)
class SpecialistRewardConfig:
    left_approach_second: float = .2
    left_scale_m: float = .03
    left_acquisition: float = .25
    left_hold_second: float = 2.
    left_dwell_success: float = 1.
    minimum_dwell_s: float = .05
    left_missed: float = -.5
    right_strict_match: float = 1.
    right_lenient_only_match: float = .25
    right_wrong_crossing: float = -.25
    right_missed_strict: float = -.5

    def __post_init__(self):
        values = asdict(self)
        if not np.isfinite(list(values.values())).all():
            raise ValueError('finite specialist reward configuration required')
        if min(self.left_scale_m, self.minimum_dwell_s) <= 0:
            raise ValueError('positive approach scale and dwell required')
        if any(value < 0 for key, value in values.items()
               if key not in ('left_missed', 'right_wrong_crossing', 'right_missed_strict')):
            raise ValueError('nonnegative specialist reward weights required')
        if max(self.left_missed, self.right_wrong_crossing, self.right_missed_strict) > 0:
            raise ValueError('nonpositive specialist penalty weights required')


class SpecialistLedger:
    """Separate bookkeeping over actual TaskMeasurement rows; no ledger writes."""
    def __init__(self, task, measured, config=SpecialistRewardConfig()):
        self.task, self.config = task, config
        self.previous_step = measured['physics_step']
        self.previous_time = measured['task_time_s']
        self.previous_candidates = {t.target_id: bool(measured['targets'][t.target_id]['candidate'])
                                    for t in task.targets}
        self.left = {t.target_id: dict(valid_s=0., dwell_s=0., longest_dwell_s=0.,
            acquisitions=0, releases=0, timely_releases=0, candidate=self.previous_candidates[t.target_id])
            for t in task.targets}
        self.acquired = set()
        self.dwelled = set()
        self.left_missed = set()
        self.crossing_ids = set()
        self.right_matches = {.05: {}, .1: {}}
        self.right_missed = set()
        self.geometric_crossings = self.matching_crossings = 0
        self.wrong_crossings = self.duplicate_crossings = 0
        self.safety_reasons = []

    def update(self, measured):
        step, now = measured['physics_step'], measured['task_time_s']
        if step != self.previous_step+1 or abs(now-self.previous_time-1/240.) > 1e-9:
            raise ValueError('consecutive actual 240Hz specialist measurements required')
        cfg = self.config
        terms = dict(left_approach=0., left_acquisition=0., left_hold=0.,
                     left_dwell_success=0., left_missed=0., right_strict_match=0.,
                     right_lenient_only_match=0., right_wrong_crossing=0., right_missed_strict=0.)
        approach = []
        for target in self.task.targets:
            identity = target.target_id
            candidate = bool(measured['targets'][identity]['candidate'])
            previous = self.previous_candidates[identity]
            state = self.left[identity]
            active = target.press_s <= now <= target.end_s
            was_active = target.press_s <= self.previous_time <= target.end_s
            if target.fret and 0 <= now <= target.end_s:
                distance = np.linalg.norm(measured['geometry'][identity]['delta'])
                approach.append(np.exp(-(distance/cfg.left_scale_m)**2))
            if target.fret and active and candidate:
                if not (previous and was_active):
                    state['acquisitions'] += 1
                    if identity not in self.acquired:
                        self.acquired.add(identity)
                        terms['left_acquisition'] += cfg.left_acquisition
                duration = (max(0., min(now, target.end_s)-max(self.previous_time, target.press_s))
                            if previous else 0.)
                state['valid_s'] += duration
                state['dwell_s'] += duration
                state['longest_dwell_s'] = max(state['longest_dwell_s'], state['dwell_s'])
                terms['left_hold'] += cfg.left_hold_second*duration
                if state['dwell_s']+1e-12 >= cfg.minimum_dwell_s and identity not in self.dwelled:
                    self.dwelled.add(identity)
                    terms['left_dwell_success'] += cfg.left_dwell_success
            else:
                state['dwell_s'] = 0.
            if target.fret and previous and not candidate and state['acquisitions']:
                state['releases'] += 1
                if target.end_s <= now <= target.end_s+.1 and state['valid_s'] > 0:
                    state['timely_releases'] += 1
            state['candidate'] = candidate
            self.previous_candidates[identity] = candidate
            if now > target.end_s+1e-12 and identity not in self.dwelled and identity not in self.left_missed:
                self.left_missed.add(identity)
                terms['left_missed'] += cfg.left_missed
        if approach:
            terms['left_approach'] = cfg.left_approach_second*float(np.mean(approach))/240.
        for crossing in measured['crossings']:
            identity = crossing['crossing_id']
            if identity in self.crossing_ids:
                self.duplicate_crossings += 1
                continue
            self.crossing_ids.add(identity)
            at, string, direction = crossing['task_time_s'], crossing['string_number']-1, crossing['direction']
            if (not np.isfinite(at) or not self.previous_time-1e-9 <= at <= now+1e-9
                    or string not in range(6) or direction not in (-1, 1)):
                raise ValueError('valid measured geometric crossing required')
            self.geometric_crossings += 1
            if any((t.string, t.direction) == (string, direction) for t in self.task.targets):
                self.matching_crossings += 1
            matched = {}
            for tolerance in (.05, .1):
                candidates = [t for t in self.task.targets if t.target_id not in self.right_matches[tolerance]
                    and (t.string, t.direction) == (string, direction)
                    and abs(at-t.onset_s) <= tolerance+1e-12]
                if candidates:
                    target = min(candidates, key=lambda t: (abs(at-t.onset_s), t.target_id))
                    self.right_matches[tolerance][target.target_id] = identity
                    matched[tolerance] = target.target_id
            if .05 in matched:
                terms['right_strict_match'] += cfg.right_strict_match
            elif .1 in matched:
                terms['right_lenient_only_match'] += cfg.right_lenient_only_match
            else:
                self.wrong_crossings += 1
                terms['right_wrong_crossing'] += cfg.right_wrong_crossing
        for target in self.task.targets:
            if now > target.onset_s+.05+1e-12 and target.target_id not in self.right_matches[.05] and target.target_id not in self.right_missed:
                self.right_missed.add(target.target_id)
                terms['right_missed_strict'] += cfg.right_missed_strict
        self.previous_step, self.previous_time = step, now
        return terms

    def invalidate(self, reasons):
        for reason in reasons:
            if reason not in self.safety_reasons:
                self.safety_reasons.append(reason)
        for state in self.left.values():
            state['dwell_s'] = 0.

    def summary(self, role, frozen_partner, *, completed=False, music=None):
        left_success = len(self.dwelled) == len(self.task.targets)
        right_success = len(self.right_matches[.05]) == len(self.task.targets)
        joint_success = bool(music and music['matched50'] == music['target_count'])
        provisional = {'left': left_success, 'right': right_success, 'joint': joint_success}[role]
        safe = not self.safety_reasons
        return dict(schema='guitar_learning.specialist_metrics.v1', role=role,
            frozen_partner=frozen_partner, physics_step=self.previous_step, task_time_s=self.previous_time,
            stage_success=bool(completed and safe and provisional),
            provisional_success=bool(safe and provisional), safety_invalidated=not safe,
            safety_reasons=list(self.safety_reasons),
            success_criterion=('native candidate continuous dwell within [press,end]' if role == 'left'
                else 'unique string/direction geometric crossing within50ms; no left contact prerequisite'
                if role == 'right' else 'original contact-conditioned strict matching; original music remains authoritative'),
            completion_criterion='stage_success also requires safe timeline_complete; truncation is not completion',
            left=dict(target_count=len(self.task.targets), valid_s=sum(s['valid_s'] for s in self.left.values()),
                longest_dwell_s=max(s['longest_dwell_s'] for s in self.left.values()),
                acquisitions=sum(s['acquisitions'] for s in self.left.values()),
                releases=sum(s['releases'] for s in self.left.values()),
                timely_releases=sum(s['timely_releases'] for s in self.left.values()),
                dwell_targets=sorted(self.dwelled), valid_dwell_targets=sorted(self.dwelled) if safe else [],
                targets=copy.deepcopy(self.left)),
            right=dict(target_count=len(self.task.targets), geometric_crossings=self.geometric_crossings,
                matching_string_direction_crossings=self.matching_crossings,
                duplicate_crossings=self.duplicate_crossings, wrong_crossings=self.wrong_crossings,
                matched50=len(self.right_matches[.05]), matched100=len(self.right_matches[.1]),
                valid_matched50=len(self.right_matches[.05]) if safe else 0,
                matches50=dict(self.right_matches[.05]), matches100=dict(self.right_matches[.1])),
            scope='contact candidates and geometric marker crossings, not pressure or sound; historical evidence retained after safety invalidation')


class SpecialistTrainingEnvironment(TrainingEnvironment):
    def __init__(self, *args, role='left', frozen_partner=False,
                 specialist_reward_config=SpecialistRewardConfig(), guide_config=DenseRewardConfig(), **kwargs):
        if role not in ('left', 'right', 'joint') or type(frozen_partner) is not bool:
            raise ValueError('specialist role left/right/joint and boolean frozen_partner required')
        self.role, self.frozen_partner = role, frozen_partner
        self.specialist_reward_config, self.guide_config = specialist_reward_config, guide_config
        super().__init__(*args, **kwargs)
        if any(t.fret == 0 for t in self.task.targets):
            raise ValueError('specialist phases currently require fretted targets')

    def reset(self):
        observation, info = super().reset()
        self.specialist_ledger = SpecialistLedger(self.task, self.last_measured, self.specialist_reward_config)
        self._guide_previous_geometry = copy.deepcopy(self.last_sample['geometry'])
        self.contract['task']['specialist'] = dict(schema='guitar_learning.specialist.v1',
            role=self.role, frozen_partner=self.frozen_partner,
            inactive_action='nonzero inactive actions rejected before physics unless frozen_partner',
            left_window='[press_s,end_s] inclusive; both endpoint native candidates required for interval dwell',
            right_windows_s=[.05, .1], success='safe timeline completion plus role criterion')
        self.contract['reward']['specialist'] = dict(config=asdict(self.specialist_reward_config),
            role=self.role, right_guide=asdict(self.guide_config),
            replacement='left/right replace integrated music terms; retain action_change and terminal_failure; joint uses original reward unchanged',
            left_approach='exp(-(distal_origin_target_distance/left_scale_m)^2) during[0,end], actual240Hz seconds',
            left_contact='first acquisition and first continuous dwell bonus per target, plus valid interval seconds; independent of RH',
            right='read-only dense_right_guide/direction plus independent unique geometric timing matches; no LH prerequisite',
            safety='positive role rewards suppressed on any failed control tick; costs and original termination unchanged')
        info['training_contract'] = self.contract
        info['specialist'] = self.specialist_ledger.summary(self.role, self.frozen_partner,
                                                          music=self.last_measured['summary'])
        if self.role == 'right':
            info['pick_guide'] = pick_guide_evidence(self.task, self.last_sample, 0., self.guide_config)
        return observation, info

    def step(self, action):
        action = np.asarray(action, dtype=float)
        if action.shape != (39,) or not np.isfinite(action).all() or np.any(np.abs(action) > 1):
            raise ValueError('finite normalized action39 required')
        inactive = action[33:] if self.role == 'left' else action[:33] if self.role == 'right' else ()
        if not self.frozen_partner and np.any(np.asarray(inactive) != 0):
            raise ValueError('inactive hand action must be zero before physics')
        observation, base_reward, terminated, truncated, info = super().step(action)
        try:
            samples, rows = info['native_control']['physics_samples240'], info['physics_measurements']
            if len(samples) != 4 or len(rows) != 4:
                raise ValueError('four native specialist samples required')
            stage_terms = {}
            previous = self._guide_previous_geometry
            for sample, row in zip(samples, rows):
                if sample['native']['physics_step'] != row['physics_step'] or sample['geometry']['physics_step'] != row['physics_step']:
                    raise ValueError('same-step specialist evidence required')
                terms = self.specialist_ledger.update(row['music'])
                if self.role == 'right':
                    rates = shaping_sample(self.task, sample, row['music'], previous, self.guide_config)
                    terms.update(right_guide=rates['dense_right_guide']/240.,
                                 right_direction=rates['dense_right_direction']/240.)
                prefix = self.role+'_'
                for key, value in terms.items():
                    if key.startswith(prefix): stage_terms[key] = stage_terms.get(key, 0.)+value
                previous = sample['geometry']
            self._guide_previous_geometry = copy.deepcopy(previous)
            if info['failure_reasons']:
                self.specialist_ledger.invalidate(info['failure_reasons'])
                stage_terms = {key: min(0., value) for key, value in stage_terms.items()}
            if self.role == 'joint':
                reward = base_reward
            else:
                terms = {key: info['reward_terms'][key] for key in ('action_change', 'terminal_failure')}
                terms.update(stage_terms)
                reward = float(sum(terms.values()))
                if not np.isfinite(reward): raise ValueError('finite specialist reward required')
                info['reward_terms'] = terms
                self.total_reward += reward-base_reward
            info['specialist'] = self.specialist_ledger.summary(self.role, self.frozen_partner,
                completed=bool(terminated and info['termination_reason'] == 'timeline_complete'), music=info['music'])
            if self.role == 'right':
                info['pick_guide'] = pick_guide_evidence(self.task, samples[-1], info['task_time_s'], self.guide_config)
            if 'episode' in info:
                info['episode']['reward'] = self.total_reward
                info['episode']['specialist'] = copy.deepcopy(info['specialist'])
            return observation, reward, terminated, truncated, info
        except BaseException:
            self.finished = True
            raise


def build_specialist_environment(config, out, *, role='left', frozen_partner=False,
        bundle, stage='B', start_event_index=0, phrase_events=8, tempo_scale=1.,
        music=None, seed=7, worker_id=0, **kwargs):
    music = dict(music or {})
    if (set(music)-{'reward_mode', 'goal_event_indices'} or music.get('reward_mode', 'legacy') != 'legacy'
            or music.get('goal_event_indices') is not None or stage != 'B'):
        raise ValueError('specialist environment currently requires fixed stage B, legacy reward setting and no goal pool')
    task = ScoreTask.from_bundle(bundle, stage='B', start_event_index=start_event_index,
                                 phrase_events=phrase_events, tempo_scale=tempo_scale)
    with _CONSTRUCTION_LOCK:
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            return SpecialistTrainingEnvironment(config, out, task=task, role=role,
                                                  frozen_partner=frozen_partner, **kwargs)
