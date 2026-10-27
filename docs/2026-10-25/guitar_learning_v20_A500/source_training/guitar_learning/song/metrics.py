"""Continuous-score rewards, per-note accounting and compact visible history."""
import copy
import math
import numpy as np
from guitar_learning.core.dense_environment import DenseRewardConfig, pick_guide_evidence

SCHEMA = 'guitar_learning.song_metrics.v1'
HISTORY_FIELDS = (
    'elapsed_fraction', 'remaining_fraction', 'target_count', 'expired_fraction',
    'left_achieved_fraction', 'right_matched_fraction', 'coupled_fraction',
    'left_missed_fraction', 'right_missed_fraction', 'mean_clean_fraction',
    'wrong_crossings', 'repeat_crossings', 'duplicate_crossings', 'safety_invalidated',
    'strict50_fraction', 'strict100_fraction',
    'focus_present', 'focus_current', 'focus_preparing', 'focus_string', 'focus_fret',
    'focus_finger', 'focus_direction', 'focus_onset_delta_s', 'focus_end_delta_s',
    'focus_candidate', 'focus_wrong', 'focus_clean_fraction', 'focus_left_achieved',
    'focus_right_matched', 'focus_coupled', 'focus_required_fraction')
HISTORY_SCALES = tuple(100. if name in ('target_count', 'wrong_crossings', 'repeat_crossings',
    'duplicate_crossings') else 6. if name == 'focus_string' else 22. if name == 'focus_fret'
    else 4. if name == 'focus_finger' else 2. if name.endswith('_delta_s') else 1.
    for name in HISTORY_FIELDS)


def metadata():
    return dict(schema=SCHEMA, history_fields=list(HISTORY_FIELDS), history_scales=list(HISTORY_SCALES),
        scope='continuous all-fretted score; native clean contact/geometric crossings, no pressure/audio',
        matching='one actual eligible crossing consumes nearest unmatched string/direction target within window and before end',
        coupling='both native endpoints must be clean for the matched target',
        release='no forced full hand/string release between successive score targets',
        rewards=dict(clean_held_second=2., left_success=1., right_success=1., coupled=1.,
            wrong_press_second=-1., missing_second=-.5, left_approach_second=.2,
            right_guide_second=.2, missed_each=-.5, wrong_crossing=-.1, repeat_crossing=-.02),
        dense_scope='left distal-origin and right live string sweep are shaping only')


class SongLedger:
    def __init__(self, task, measured, window_s=.5, left_fraction=.4):
        if (not task.targets or any(not t.fret for t in task.targets) or
                not math.isfinite(window_s) or window_s <= 0 or
                not math.isfinite(left_fraction) or not 0 < left_fraction <= 1):
            raise ValueError('all-fretted task and positive window/fraction required')
        if measured['task_time_s'] != 0.:
            raise ValueError('song ledger starts at policy clock zero')
        self.task, self.previous = task, copy.deepcopy(measured)
        self.window_s, self.left_fraction = float(window_s), float(left_fraction)
        self.notes = {t.target_id: dict(clean_audible_s=0., wrong_press_s=0., missing_press_s=0.,
            left_achieved=False, right_crossing_id=None, coupled=False,
            error_s=None, left_missed=False, right_missed=False,
            required_dwell_s=min(t.end_s-t.onset_s, max(.05, (t.end_s-t.onset_s)*left_fraction)))
            for t in task.targets}
        if any(t.end_s <= t.onset_s for t in task.targets):
            raise ValueError('positive audible duration required')
        self.crossing_ids, self.safety_reasons, self.events = set(), [], []
        self.wrong_crossings = self.repeat_crossings = self.duplicate_crossings = 0
        self.guide_config = DenseRewardConfig(strike_y_m=-.36, depth_m=.004, sweep_half_width_m=.008)

    @staticmethod
    def _q(measured, identity):
        target = measured['targets'][identity]
        quality = target.get('fretting_quality', {})
        return bool(target['candidate']), quality.get('status') == 'wrong'

    def update(self, measured, geometry_sample=None):
        before, now = self.previous['task_time_s'], measured['task_time_s']
        if (measured['physics_step'] != self.previous['physics_step']+1 or
                not math.isfinite(now) or abs(now-before-1/240.) > 1e-9):
            raise ValueError('consecutive actual240Hz song measurements required')
        terms = {name: 0. for name in ('song_clean_hold', 'song_left_success', 'song_right_success',
            'song_coupled', 'song_wrong_press', 'song_missing_press', 'song_left_approach',
            'song_right_guide', 'song_left_missed', 'song_right_missed',
            'song_wrong_crossing', 'song_repeat_crossing')}
        candidates = {}
        approaches = []
        for target in self.task.targets:
            identity = target.target_id
            note = self.notes[identity]
            p, pw = self._q(self.previous, identity); q, qw = self._q(measured, identity)
            candidates[identity] = p and q
            audible = max(0., min(now, target.end_s)-max(before, target.onset_s))
            press = max(0., min(now, target.end_s)-max(before, target.press_s))
            clean = audible if p and q else 0.
            wrong = press*.5*(pw+qw)
            missing = audible*.5*((not p and not pw)+(not q and not qw))
            note['clean_audible_s'] += clean
            note['wrong_press_s'] += wrong
            note['missing_press_s'] += missing
            terms['song_clean_hold'] += 2.*clean
            terms['song_wrong_press'] -= wrong
            terms['song_missing_press'] -= .5*missing
            if not note['left_achieved'] and note['clean_audible_s']+1e-12 >= note['required_dwell_s']:
                note['left_achieved'] = True
                terms['song_left_success'] += 1.
            if now > target.end_s+1e-12 and not note['left_achieved'] and not note['left_missed']:
                note['left_missed'] = True; terms['song_left_missed'] -= .5
            # Geometry is an approach proxy, never contact success.
            if before <= target.onset_s and 0 <= target.press_s-now <= 2.:
                delta = measured.get('geometry', {}).get(identity, {}).get('delta')
                if delta is not None:
                    distance = float(np.linalg.norm(np.asarray(delta, dtype=float)))
                    if not math.isfinite(distance): raise ValueError('finite approach geometry required')
                    approaches.append(math.exp(-(distance/.03)**2))
        if approaches: terms['song_left_approach'] = .2*sum(approaches)/len(approaches)/240.
        for crossing in measured['crossings']:
            identity, at = crossing['crossing_id'], crossing['task_time_s']
            if identity in self.crossing_ids:
                self.duplicate_crossings += 1
                continue
            if (crossing.get('valid') is not True or crossing.get('reason_flags') or
                    not isinstance(at, (int, float)) or isinstance(at, bool) or not math.isfinite(at) or
                    not before-1e-9 <= at <= now+1e-9 or
                    type(crossing.get('string_number')) is not int or crossing['string_number'] not in range(1, 7) or
                    type(crossing.get('direction')) is not int or crossing['direction'] not in (-1, 1)):
                raise ValueError('actual eligible same-interval crossing required')
            self.crossing_ids.add(identity)
            matching = [t for t in self.task.targets
                if (t.string+1, t.direction) == (crossing['string_number'], crossing['direction'])
                and abs(at-t.onset_s) <= self.window_s+1e-12 and at < t.end_s]
            available = [t for t in matching if self.notes[t.target_id]['right_crossing_id'] is None]
            chosen = min(available, key=lambda t: (abs(at-t.onset_s), t.onset_s, t.target_id)) if available else None
            if chosen is not None:
                note = self.notes[chosen.target_id]
                note.update(right_crossing_id=identity, error_s=at-chosen.onset_s,
                            coupled=bool(candidates[chosen.target_id]))
                terms['song_right_success'] += 1.
                if note['coupled']: terms['song_coupled'] += 1.
                self.events.append(dict(crossing_id=identity, target_id=chosen.target_id,
                    task_time_s=at, error_s=note['error_s'], coupled=note['coupled']))
            elif matching:
                self.repeat_crossings += 1; terms['song_repeat_crossing'] -= .02
            else:
                self.wrong_crossings += 1; terms['song_wrong_crossing'] -= .1
        for target in self.task.targets:
            note = self.notes[target.target_id]
            deadline = min(target.end_s, target.onset_s+self.window_s)
            if now > deadline+1e-12 and note['right_crossing_id'] is None and not note['right_missed']:
                note['right_missed'] = True; terms['song_right_missed'] -= .5
        if geometry_sample is not None:
            if geometry_sample['geometry']['physics_step'] != measured['physics_step']:
                raise ValueError('same-step live guide geometry required')
            guide = pick_guide_evidence(self.task, geometry_sample, now, self.guide_config)
            if guide is not None:
                terms['song_right_guide'] = .2*math.exp(-(guide['distance_m']/.05)**2)/240.
        self.previous = copy.deepcopy(measured)
        if self.safety_reasons:
            terms = {name: min(0., value) for name, value in terms.items()}
        return terms

    def invalidate(self, reasons):
        for reason in reasons:
            if reason not in self.safety_reasons: self.safety_reasons.append(reason)

    def _focus(self):
        now = self.previous['task_time_s']
        current = [t for t in self.task.targets if t.onset_s <= now < t.end_s]
        if current: return min(current, key=lambda t: (t.end_s, t.target_id))
        upcoming = [t for t in self.task.targets if now <= t.onset_s <= now+2.]
        return min(upcoming, key=lambda t: (t.onset_s, t.target_id)) if upcoming else None

    def history(self):
        summary = self.summary()
        now, duration = self.previous['task_time_s'], self.task.duration_s
        count = len(self.notes)
        values = [now/duration, max(0., duration-now)/duration, count,
            sum(t.end_s < now for t in self.task.targets)/count,
            summary['left_success_count']/count, summary['right_success_count']/count,
            summary['coupled_hit_count']/count, summary['left_missed_count']/count,
            summary['right_missed_count']/count, summary['mean_clean_audible_fraction'],
            self.wrong_crossings, self.repeat_crossings, self.duplicate_crossings,
            bool(self.safety_reasons), summary['strict_music']['matched50']/count,
            summary['strict_music']['matched100']/count]
        target = self._focus()
        if target is None: values += [0.]*16
        else:
            note = self.notes[target.target_id]; q, wrong = self._q(self.previous, target.target_id)
            values += [1., target.onset_s <= now < target.end_s, target.press_s <= now < target.onset_s,
                target.string+1, target.fret, target.finger, target.direction,
                target.onset_s-now, target.end_s-now, q, wrong,
                min(1., note['clean_audible_s']/(target.end_s-target.onset_s)),
                note['left_achieved'], note['right_crossing_id'] is not None, note['coupled'],
                note['required_dwell_s']/(target.end_s-target.onset_s)]
        return [float(value) for value in values]

    def summary(self, completed=False):
        count = len(self.notes)
        left = sum(n['left_achieved'] for n in self.notes.values())
        right = sum(n['right_crossing_id'] is not None for n in self.notes.values())
        coupled = sum(n['coupled'] for n in self.notes.values())
        fractions = [min(1., self.notes[t.target_id]['clean_audible_s']/(t.end_s-t.onset_s)) for t in self.task.targets]
        errors = [abs(n['error_s']) for n in self.notes.values() if n['error_s'] is not None]
        safe = not self.safety_reasons
        success = safe and left == right == coupled == count and self.wrong_crossings == self.repeat_crossings == 0
        full = bool(completed and self.previous['task_time_s']+1e-9 >= self.task.duration_s)
        strict = self.previous.get('summary', {})
        return dict(schema=SCHEMA, role='joint', target_count=count, denominator=count,
            expired_count=sum(t.end_s < self.previous['task_time_s'] for t in self.task.targets),
            left_success_count=left, right_success_count=right, coupled_hit_count=coupled,
            left_missed_count=sum(n['left_missed'] for n in self.notes.values()),
            right_missed_count=sum(n['right_missed'] for n in self.notes.values()),
            left_success_fraction=left/count, right_success_fraction=right/count, coupled_fraction=coupled/count,
            mean_clean_audible_fraction=sum(fractions)/count,
            wrong_press_s=sum(n['wrong_press_s'] for n in self.notes.values()),
            missing_press_s=sum(n['missing_press_s'] for n in self.notes.values()),
            wrong_crossings=self.wrong_crossings, repeat_crossings=self.repeat_crossings,
            duplicate_crossings=self.duplicate_crossings, geometric_crossings=len(self.crossing_ids),
            mean_abs_error_s=sum(errors)/len(errors) if errors else None,
            max_abs_error_s=max(errors) if errors else None,
            completed=full, stage_success=bool(full and success), provisional_success=bool(success),
            safety_invalidated=not safe, safety_reasons=list(self.safety_reasons),
            strict_music={name: strict.get(name, 0) for name in ('matched50', 'matched100', 'wrong_crossings', 'missed_strict')},
            task_time_s=self.previous['task_time_s'], window_s=self.window_s, left_fraction=self.left_fraction,
            per_note=copy.deepcopy(self.notes), events=copy.deepcopy(self.events),
            scope=metadata()['scope'])
