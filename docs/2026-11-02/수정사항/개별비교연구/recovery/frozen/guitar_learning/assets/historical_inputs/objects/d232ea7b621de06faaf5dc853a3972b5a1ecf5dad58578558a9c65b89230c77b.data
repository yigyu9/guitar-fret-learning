"""Endpoint-measured quality rewards; no simulator writes or acoustic claims."""
from dataclasses import asdict, dataclass
import math

HISTORY_FIELDS = (
    'positive_candidate', 'clean_candidate', 'wrong', 'missing', 'wrong_assignment',
    'higher_fret', 'incidental_other_string', 'uncertain', 'target_string_contact',
    'wrong_press_s', 'missing_press_s', 'clean_audible_s', 'audible_wrong_s', 'dropouts',
    'release_clear_dwell_s', 'release_complete', 'release_awarded', 'release_late_s',
    'recovery_awarded', 'strike_ready', 'strike_ready_dwell_s', 'strike_accepted', 'unprepared_count',
    'extra_count', 'other_blocked_count', 'strike_recovered', 'recovery_dwell_s')


@dataclass(frozen=True)
class QualityConfig:
    wrong_press_second: float = -1.
    missing_press_second: float = -.5
    dropout_penalty: float = -.1
    release_late_second: float = -.5
    release_bonus: float = .25
    unprepared_penalty: float = -.1
    extra_strike_penalty: float = -.1
    blocked_crossing_penalty: float = -.1
    recovery_bonus: float = .1
    release_grace_s: float = .1
    release_dwell_s: float = .05

    def __post_init__(self):
        values = asdict(self)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values.values()):
            raise ValueError('finite quality weights required')
        if (max(self.wrong_press_second, self.missing_press_second, self.dropout_penalty,
                self.release_late_second, self.unprepared_penalty, self.extra_strike_penalty, self.blocked_crossing_penalty) > 0
                or min(self.release_bonus, self.recovery_bonus, self.release_grace_s) < 0
                or self.release_dwell_s <= 0):
            raise ValueError('nonpositive penalties, nonnegative bonuses and positive dwell required')


def history_scales():
    return [7. if name.endswith('_s') else 1680. if name in (
        'dropouts', 'unprepared_count', 'extra_count', 'other_blocked_count') else 1. for name in HISTORY_FIELDS]


def preparation_metadata():
    from guitar_learning.quality.actionable_preparation_environment import REWARD_METADATA
    value = dict(REWARD_METADATA)
    value.update(schema='guitar_learning.preparation_contact.v2',
        measurement='clean native target candidate; original positive candidate retained separately')
    return value


def metadata():
    from guitar_learning.quality.fretting_quality import FRETTING_QUALITY_METADATA
    from guitar_learning.quality.strike_quality import STRIKE_QUALITY_METADATA
    return dict(schema='guitar_learning.musical_quality.v1',
        fretting=FRETTING_QUALITY_METADATA, strike=STRIKE_QUALITY_METADATA,
        config=asdict(QualityConfig()), history_fields=list(HISTORY_FIELDS),
        scope='single fretted target; clean contact and prepared geometric crossing, no pressure/audio',
        candidate_source='clean candidate replaces eligibility in music/timing/preparation; original positive candidate retained separately',
        integration='negative occupancy uses endpoint trapezoid clipped to score intervals; clean/release dwell needs both endpoints',
        timing_reward_override='LH post-note relaxed hold is canceled; timing-only success bonus replaced by one audible clean-dwell achievement',
        completion='timing achievement plus audible clean fraction and final release for LH; zero wrong/blocked/extra and final recovery for RH')


class QualityLedger:
    def __init__(self, task, measured, role, left_fraction, config=QualityConfig()):
        if role not in ('left', 'right') or len(task.targets) != 1 or not task.targets[0].fret:
            raise ValueError('single fretted target and explicit hand required')
        self.target, self.role, self.config = task.targets[0], role, config
        self.left_fraction = left_fraction
        self.previous = measured
        self.wrong_press_s = self.missing_press_s = self.clean_audible_s = self.audible_wrong_s = 0.
        self.release_clear_dwell_s = self.release_late_s = 0.
        self.dropouts = 0
        self.release_complete = self.release_awarded = self.recovery_awarded = False
        self.unprepared_count = self.extra_count = self.other_blocked_count = 0

    def _q(self, measured):
        return measured['targets'][self.target.target_id]['fretting_quality']

    def update(self, measured):
        previous, cfg, t = self.previous, self.config, self.target
        a, b = previous['task_time_s'], measured['task_time_s']
        if measured['physics_step'] != previous['physics_step']+1 or abs(b-a-1/240.) > 1e-9:
            raise ValueError('quality rewards require consecutive actual240Hz samples')
        p, q = self._q(previous), self._q(measured)
        overlap = lambda lo, hi: max(0., min(b, hi)-max(a, lo))
        occupancy = lambda label: .5*(float(p['status'] == label)+float(q['status'] == label))
        audible = overlap(t.onset_s, t.end_s)
        wrong = overlap(0., t.end_s)*occupancy('wrong')
        missing = audible*occupancy('missing')
        clean = audible if p['clean_target_candidate'] and q['clean_target_candidate'] else 0.
        self.wrong_press_s += wrong
        self.missing_press_s += missing
        self.clean_audible_s += clean
        self.audible_wrong_s += audible*occupancy('wrong')
        dropped = bool(p['clean_target_candidate'] and not q['clean_target_candidate'] and t.onset_s < b < t.end_s)
        self.dropouts += dropped
        clear = not q['target_string_contact_evidence_ids']
        previous_clear = not p['target_string_contact_evidence_ids']
        release_span = overlap(t.end_s, b)
        if clear and previous_clear and release_span > 0:
            self.release_clear_dwell_s += release_span
        elif not clear:
            self.release_clear_dwell_s = 0.
        self.release_complete = self.release_clear_dwell_s+1e-12 >= cfg.release_dwell_s
        late = overlap(t.end_s+cfg.release_grace_s, b)*.5*(float(not previous_clear)+float(not clear))
        self.release_late_s += late
        release_bonus = 0.
        if (self.release_complete and not self.release_awarded
                and self.clean_audible_s+1e-12 >= min(.05, t.end_s-t.onset_s)):
            self.release_awarded = True
            release_bonus = cfg.release_bonus
        strike = measured['strike_quality']
        unprepared = strike['unprepared_count']-self.unprepared_count
        extra = strike['extra_count']-self.extra_count
        other_blocked_count = len(set(strike.get('blocked_event_ids', []))-set(strike.get('unprepared_crossing_ids', []))-set(strike.get('extra_crossing_ids', [])))
        other_blocked = other_blocked_count-self.other_blocked_count
        if min(unprepared, extra, other_blocked) < 0:
            raise ValueError('strike quality counters cannot decrease')
        recovery_bonus = 0.
        if strike['recovered'] and not self.recovery_awarded:
            self.recovery_awarded = True
            recovery_bonus = cfg.recovery_bonus
        self.unprepared_count, self.extra_count = strike['unprepared_count'], strike['extra_count']
        self.other_blocked_count = other_blocked_count
        self.previous = measured
        return dict(quality_wrong_press=cfg.wrong_press_second*wrong if self.role == 'left' else 0.,
            quality_missing_press=cfg.missing_press_second*missing if self.role == 'left' else 0.,
            quality_dropout=cfg.dropout_penalty*dropped if self.role == 'left' else 0.,
            quality_late_release=cfg.release_late_second*late if self.role == 'left' else 0.,
            quality_release=release_bonus if self.role == 'left' else 0.,
            quality_unprepared=cfg.unprepared_penalty*unprepared if self.role == 'right' else 0.,
            quality_extra_strike=cfg.extra_strike_penalty*extra if self.role == 'right' else 0.,
            quality_other_blocked=cfg.blocked_crossing_penalty*other_blocked if self.role == 'right' else 0.,
            quality_recovery=recovery_bonus if self.role == 'right' else 0.)

    def history(self):
        q = self._q(self.previous); s = self.previous['strike_quality']
        values = (q['positive_target_candidate'], q['clean_target_candidate'], q['status'] == 'wrong',
            q['status'] == 'missing', q['wrong_assignment'], q['higher_fret'],
            q['incidental_other_string'], q['uncertain'], bool(q['target_string_contact_evidence_ids']),
            self.wrong_press_s, self.missing_press_s, self.clean_audible_s, self.audible_wrong_s,
            self.dropouts, self.release_clear_dwell_s, self.release_complete, self.release_awarded,
            self.release_late_s, self.recovery_awarded, s['ready'], s['ready_dwell_s'], bool(s['accepted_crossing_ids']),
            self.unprepared_count, self.extra_count, self.other_blocked_count, s['recovered'], s['recovery_dwell_s'])
        return [float(v) for v in values]

    def summary(self, timing):
        duration = self.target.end_s-self.target.onset_s
        fraction = min(1., self.clean_audible_s/duration)
        strike = self.previous['strike_quality']
        passed = (fraction+1e-9 >= self.left_fraction and self.release_complete) if self.role == 'left' else (
            bool(strike['accepted_crossing_ids']) and strike['recovered'] and
            self.unprepared_count == self.extra_count == self.other_blocked_count == timing['wrong_crossings'] == 0)
        return dict(schema='guitar_learning.musical_quality_metrics.v1', role=self.role,
            stage_success=bool(timing['stage_success'] and passed),
            provisional_success=bool(timing['provisional_success'] and passed),
            timing_achievement=bool(timing['stage_success']), clean_audible_fraction=fraction,
            fretting_state=dict(self._q(self.previous)),
            wrong_press_s=self.wrong_press_s, missing_press_s=self.missing_press_s,
            audible_wrong_s=self.audible_wrong_s, dropouts=self.dropouts,
            release_complete=self.release_complete, release_clear_dwell_s=self.release_clear_dwell_s,
            release_late_s=self.release_late_s, strike=strike,
            scope='relaxed stage quality, not error-free full song or acoustic success')
