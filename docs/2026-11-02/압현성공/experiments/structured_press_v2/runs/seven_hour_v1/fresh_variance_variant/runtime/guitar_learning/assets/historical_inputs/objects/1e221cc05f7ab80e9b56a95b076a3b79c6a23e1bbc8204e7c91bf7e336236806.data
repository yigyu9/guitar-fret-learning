"""Read-only timing curriculum over eligible native contacts and crossings.

The task already includes the execution pre-roll offset. Original music50/100ms
bookkeeping is never changed. Success requires safe full-episode completion.
"""
import copy
from dataclasses import asdict, dataclass
import math

WINDOWS_S = (1.5, .5, .2, .1, .05)
LEFT_FRACTIONS = (.2, .4, .6, .8, 1.)
TIMING_HISTORY_FIELDS = (
    'stage_index', 'window_s', 'pre_roll_s', 'left_fraction', 'left_required_dwell_s',
    'policy_time_s', 'score_time_s', 'previous_candidate', 'window_acquired',
    'window_dwell_s', 'window_longest_dwell_s', 'window_valid_s',
    'audible_dwell_s', 'audible_longest_dwell_s', 'audible_valid_s',
    'achieved', 'has_first_success', 'first_success_s', 'missed',
    'has_best_error', 'best_abs_error_s', 'best_precision_quality',
    'acquisitions', 'releases', 'geometric_crossings', 'matching_window_crossings',
    'matched_crossing', 'wrong_crossings', 'unnecessary_crossings',
    'duplicate_crossings', 'safety_invalidated',
)


@dataclass(frozen=True)
class TimingConfig:
    stage_index: int = 0
    pre_roll_s: float = 1.
    success_bonus: float = 1.
    precision_bonus: float = .5
    acquisition_bonus: float = .25
    held_second: float = 2.
    right_guide_second: float = .2
    right_guide_scale_m: float = .05
    missed_penalty: float = -.5
    wrong_crossing_penalty: float = -.1
    unnecessary_crossing_penalty: float = -.02

    def __post_init__(self):
        if type(self.stage_index) is not int or self.stage_index not in range(5):
            raise ValueError('explicit timing stage index0..4 required')
        values = {k: v for k, v in asdict(self).items() if k != 'stage_index'}
        if (any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                for v in values.values()) or self.pre_roll_s <= 0 or
                abs(self.pre_roll_s*60-round(self.pre_roll_s*60)) > 1e-9 or
                self.right_guide_scale_m <= 0 or
                min(self.success_bonus, self.precision_bonus, self.acquisition_bonus,
                    self.held_second, self.right_guide_second) < 0 or
                max(self.missed_penalty, self.wrong_crossing_penalty,
                    self.unnecessary_crossing_penalty) > 0):
            raise ValueError('finite timing weights and positive control-tick pre-roll/guide scale required')

    @property
    def window_s(self):
        return WINDOWS_S[self.stage_index]

    @property
    def left_fraction(self):
        return LEFT_FRACTIONS[self.stage_index]

    @property
    def horizon_s(self):
        return 4.+self.pre_roll_s


def history_scales(task, config):
    counts = {'acquisitions', 'releases', 'geometric_crossings', 'matching_window_crossings',
              'wrong_crossings', 'unnecessary_crossings', 'duplicate_crossings'}
    times = {'policy_time_s', 'score_time_s', 'first_success_s', 'window_dwell_s',
             'window_longest_dwell_s', 'window_valid_s', 'audible_dwell_s',
             'audible_longest_dwell_s', 'audible_valid_s', 'best_abs_error_s'}
    return [4. if name == 'stage_index' else config.horizon_s*240 if name in counts
            else config.horizon_s if name in times else 1. for name in TIMING_HISTORY_FIELDS]


class TimingLedger:
    def __init__(self, task, measured, role, config=TimingConfig()):
        if role not in ('left', 'right') or len(task.targets) != 1 or task.targets[0].fret == 0:
            raise ValueError('single fretted target and left/right role required')
        self.task, self.target, self.role, self.config = task, task.targets[0], role, config
        self.previous_step, self.previous_time = self._clock(measured)
        if self.previous_time != 0.:
            raise ValueError('timing ledger must start at policy clock zero')
        self.previous_candidate = bool(measured['targets'][self.target.target_id]['candidate'])
        self.note_duration = self.target.end_s-self.target.onset_s
        if self.note_duration <= 0:
            raise ValueError('positive audible note duration required')
        self.left_required_dwell_s = min(self.note_duration,
            max(.05, self.note_duration*config.left_fraction))
        self.window_start = self.target.press_s-config.window_s
        self.window_end = self.target.end_s+config.window_s
        self.window_dwell_s = self.window_longest_dwell_s = self.window_valid_s = 0.
        self.audible_dwell_s = self.audible_longest_dwell_s = self.audible_valid_s = 0.
        self.window_acquired = self.achieved = self.missed = False
        self.first_success_s = self.best_abs_error_s = None
        self.best_precision_quality = 0.
        self.acquisitions = self.releases = 0
        self.geometric_crossings = self.matching_window_crossings = 0
        self.wrong_crossings = self.unnecessary_crossings = self.duplicate_crossings = 0
        self.matched_crossing = None
        self.crossing_ids, self.crossings, self.safety_reasons = set(), [], []

    @staticmethod
    def _clock(measured):
        step, now = measured['physics_step'], measured['task_time_s']
        if type(step) is not int or step < 0 or isinstance(now, bool) or not math.isfinite(now) or now < 0:
            raise ValueError('actual nonnegative policy/native clock required')
        return step, float(now)

    def _precision(self, error):
        error = abs(error)
        self.best_abs_error_s = error if self.best_abs_error_s is None else min(self.best_abs_error_s, error)
        quality = math.exp(-.5*(error/self.config.window_s)**2)
        improvement = max(0., quality-self.best_precision_quality)
        self.best_precision_quality = max(self.best_precision_quality, quality)
        return self.config.precision_bonus*improvement

    def update(self, measured, guide=None):
        step, now = self._clock(measured)
        if step != self.previous_step+1 or abs(now-self.previous_time-1/240.) > 1e-9:
            raise ValueError('consecutive actual240Hz timing measurements required')
        cfg, t = self.config, self.target
        candidate = bool(measured['targets'][t.target_id]['candidate'])
        both = candidate and self.previous_candidate
        terms = dict(timing_hold=0., timing_acquisition=0., timing_success=0.,
            timing_precision=0., timing_missed=0., timing_wrong_crossing=0.,
            timing_unnecessary_crossing=0., timing_right_guide=0.)
        window_credit = max(0., min(now, self.window_end)-max(self.previous_time, self.window_start)) if both else 0.
        audible_credit = max(0., min(now, t.end_s)-max(self.previous_time, t.onset_s)) if both else 0.
        self.window_dwell_s = self.window_dwell_s+window_credit if window_credit > 0 else 0.
        self.audible_dwell_s = self.audible_dwell_s+audible_credit if audible_credit > 0 else 0.
        self.window_longest_dwell_s = max(self.window_longest_dwell_s, self.window_dwell_s)
        self.audible_longest_dwell_s = max(self.audible_longest_dwell_s, self.audible_dwell_s)
        self.window_valid_s += window_credit
        self.audible_valid_s += audible_credit
        if self.previous_candidate and not candidate:
            self.releases += 1
        was_achieved = self.achieved
        if self.role == 'left':
            active = self.window_start <= now <= self.window_end
            if candidate and active:
                if not self.previous_candidate or not self.window_start <= self.previous_time <= self.window_end:
                    self.acquisitions += 1
                if not self.window_acquired:
                    self.window_acquired = True
                    terms['timing_acquisition'] = cfg.acquisition_bonus
                terms['timing_precision'] += self._precision(now-t.press_s)
            credit = audible_credit if cfg.stage_index == 4 else window_credit
            terms['timing_hold'] = cfg.held_second*credit
            if cfg.stage_index == 4:
                self.achieved |= self.audible_longest_dwell_s+1e-12 >= self.note_duration
            else:
                self.achieved |= self.window_longest_dwell_s+1e-12 >= self.left_required_dwell_s
        for crossing in measured['crossings']:
            identity = crossing['crossing_id']
            if identity in self.crossing_ids:
                self.duplicate_crossings += 1
                continue
            at = crossing['task_time_s']
            if (crossing.get('valid') is not True or crossing.get('reason_flags') or
                    not math.isfinite(at) or not self.previous_time-1e-9 <= at <= now+1e-9 or
                    type(crossing['string_number']) is not int or crossing['string_number'] not in range(1, 7) or
                    type(crossing['direction']) is not int or crossing['direction'] not in (-1, 1)):
                raise ValueError('eligible same-interval original geometric crossing required')
            self.crossing_ids.add(identity)
            self.geometric_crossings += 1
            matching = (crossing['string_number'], crossing['direction']) == (t.string+1, t.direction)
            error = at-t.onset_s
            in_window = matching and abs(error) <= cfg.window_s+1e-12
            self.crossings.append(dict(crossing_id=identity, policy_time_s=at,
                score_time_s=at-cfg.pre_roll_s, string_number=crossing['string_number'],
                direction=crossing['direction'], error_s=error, matching=in_window))
            if matching and self.role == 'right':
                self.best_abs_error_s = abs(error) if self.best_abs_error_s is None else min(self.best_abs_error_s, abs(error))
            if in_window:
                self.matching_window_crossings += 1
                if self.role == 'right':
                    terms['timing_precision'] += self._precision(error)
                    if self.matched_crossing is None:
                        self.matched_crossing = identity
                        self.achieved = True
                    else:
                        self.unnecessary_crossings += 1
                        terms['timing_unnecessary_crossing'] += cfg.unnecessary_crossing_penalty
            else:
                self.wrong_crossings += 1
                if self.role == 'right':
                    terms['timing_wrong_crossing'] += cfg.wrong_crossing_penalty
        if self.achieved and not was_achieved:
            self.first_success_s = now
            terms['timing_success'] = cfg.success_bonus
        deadline = (t.end_s if cfg.stage_index == 4 else self.window_end) if self.role == 'left' else t.onset_s+cfg.window_s
        if now > deadline+1e-12 and not self.achieved and not self.missed:
            self.missed = True
            terms['timing_missed'] = cfg.missed_penalty
        if self.role == 'right' and guide is not None:
            distance = guide['distance_m']
            if not math.isfinite(distance) or distance < 0:
                raise ValueError('finite nonnegative measured guide distance required')
            terms['timing_right_guide'] = cfg.right_guide_second*math.exp(-(distance/cfg.right_guide_scale_m)**2)/240.
        self.previous_step, self.previous_time, self.previous_candidate = step, now, candidate
        if self.safety_reasons:
            terms = {key: min(0., value) for key, value in terms.items()}
        return terms

    def invalidate(self, reasons):
        for reason in reasons:
            if reason not in self.safety_reasons:
                self.safety_reasons.append(reason)
        self.window_dwell_s = self.audible_dwell_s = 0.

    def history(self):
        c = self.config
        values = [c.stage_index, c.window_s, c.pre_roll_s, c.left_fraction, self.left_required_dwell_s,
            self.previous_time, self.previous_time-c.pre_roll_s, self.previous_candidate, self.window_acquired,
            self.window_dwell_s, self.window_longest_dwell_s, self.window_valid_s,
            self.audible_dwell_s, self.audible_longest_dwell_s, self.audible_valid_s,
            self.achieved, self.first_success_s is not None, self.first_success_s or 0., self.missed,
            self.best_abs_error_s is not None, self.best_abs_error_s or 0., self.best_precision_quality,
            self.acquisitions, self.releases, self.geometric_crossings, self.matching_window_crossings,
            self.matched_crossing is not None, self.wrong_crossings, self.unnecessary_crossings,
            self.duplicate_crossings, bool(self.safety_reasons)]
        return [float(value) for value in values]

    def summary(self, completed=False):
        safe = not self.safety_reasons
        complete_horizon = bool(completed and self.previous_time+1e-9 >= self.config.horizon_s)
        return dict(schema='guitar_learning.timing_metrics.v1', role=self.role,
            config=asdict(self.config), window_s=self.config.window_s,
            stage_success=bool(complete_horizon and safe and self.achieved),
            provisional_success=bool(safe and self.achieved), completed=complete_horizon,
            policy_time_s=self.previous_time, score_time_s=self.previous_time-self.config.pre_roll_s,
            first_success_s=self.first_success_s,
            first_success_score_s=None if self.first_success_s is None else self.first_success_s-self.config.pre_roll_s,
            required_dwell_s=self.left_required_dwell_s, left_fraction=self.config.left_fraction,
            window=[self.window_start, self.window_end],
            window_valid_s=self.window_valid_s, window_longest_dwell_s=self.window_longest_dwell_s,
            audible_valid_s=self.audible_valid_s, audible_longest_dwell_s=self.audible_longest_dwell_s,
            audible_hold_fraction=min(1., self.audible_valid_s/self.note_duration),
            first_matched_crossing=self.matched_crossing, missed=self.missed,
            best_abs_error_s=self.best_abs_error_s, best_precision_quality=self.best_precision_quality,
            geometric_crossings=self.geometric_crossings,
            matching_window_crossings=self.matching_window_crossings,
            wrong_crossings=self.wrong_crossings, unnecessary_crossings=self.unnecessary_crossings,
            duplicate_crossings=self.duplicate_crossings, crossings=copy.deepcopy(self.crossings),
            safety_invalidated=not safe, safety_reasons=list(self.safety_reasons),
            success_criterion=('continuous native candidate in expanded press/end window' if self.role == 'left' and self.config.stage_index < 4 else
                'continuous native candidate covering entire original onset/end interval' if self.role == 'left' else
                'one original eligible target string/direction crossing within current onset tolerance'),
            scope='read-only native candidates/geometric crossings; original music ledger is separate; no pressure or sound certification')
