"""Preparation and contact rewards using the declared native transition gates.

The old 32 song-history channels retain their original 40% progress meaning.
These rewards never read that progress flag as the current success criterion.
"""
import copy
import math

import numpy as np

from ..transition.metrics import TransitionLedger
from ..transition.task import validate


SCHEMA = 'guitar_learning.transition_refinement.reward.v1'
WEIGHTS = dict(prepare_progress=.25, prepare_ready_second=1., clean_hold_second=2.,
    hold_success=1., wrong_press_second=-1., missing_press_second=-.5,
    hold_missed=-.5, release_absent_second=.5, release_success=.5)
TERMS = tuple('refinement_'+name for name in (
    'prepare_progress', 'prepare_ready', 'clean_hold', 'hold_success',
    'wrong_press', 'missing_press', 'hold_missed', 'release_absent', 'release_success'))
RIGHT_TERMS = frozenset(('song_right_success', 'song_coupled', 'song_right_guide',
    'song_right_missed', 'song_wrong_crossing', 'song_repeat_crossing', 'song_right_progress'))


def metadata(task, transition):
    config = validate(transition)
    plan = task.provenance['transition']
    if any(plan[key] != value for key, value in config.items()):
        raise ValueError('transition task/config mismatch')
    return dict(schema=SCHEMA, weights=copy.deepcopy(WEIGHTS),
        active_reward_terms=sorted(set(TERMS) | {'action_change', 'terminal_failure'}
            | (set(RIGHT_TERMS) if config['role'] == 'joint' else set())),
        legacy_reward_sections_diagnostic_only=['song', 'transition.projection'],
        hold_fraction=plan['hold_fraction'],
        hold_minimum_s=.05 if config['mode'] == 'pair' else None,
        release_absent_fraction=plan['release_absent_fraction'],
        release_windows=copy.deepcopy(plan['release_windows']),
        preparation=dict(window='press_s <= time < onset_s, including press_s=0',
            progress='signed endpoint potential difference, clipped interval fraction; geometry is shaping only',
            potential='exp(-(distal-origin distance_m / .03)^2)', progress_scale_m=.03,
            readiness_window_s=.2,
            readiness='both native endpoints clean; positive lower target plus clean active higher target allowed only when all wrong-fret evidence belongs to that higher target'),
        bonuses='hold once at declared native dwell; release once at release-window end',
        legacy_song_history='unchanged500-state compatibility: original40% progress flag is not current success',
        safety='all positive musical terms suppressed for entire unsafe60Hz tick; physical costs unchanged',
        scope='native qualified contact and geometric shaping; no pressure/audio')


class RewardLedger:
    def __init__(self, task, initial_measured, transition):
        self.task = task
        self.native = TransitionLedger(task, initial_measured, transition)
        self.plan = task.provenance['transition']
        self.previous = copy.deepcopy(initial_measured)
        self.safety_reasons = []
        self.notes = {t.target_id: dict(prepare_ready_s=0., prepare_progress=0.,
            hold_bonus_given=False, hold_missed=False, release_bonus_given=False,
            release_evaluated=False) for t in task.targets}
        self.totals = dict.fromkeys(TERMS, 0.)

    def metadata(self):
        return metadata(self.task, self.native.config)

    @staticmethod
    def _potential(measured, identity):
        delta = measured.get('geometry', {}).get(identity, {}).get('delta')
        if delta is None:
            return None
        vector = np.asarray(delta, dtype=float)
        if vector.shape != (3,) or not np.isfinite(vector).all():
            raise ValueError('finite three-dimensional preparation geometry required')
        return math.exp(-float(np.dot(vector, vector))/(.03**2))

    def _ready(self, measured, target):
        clean, positive = self.native._quality(measured, target.target_id)
        if clean:
            return True
        if not positive:
            return False
        now = measured['task_time_s']
        # The lower finger may prepare while the higher fret owns this string.
        # Do not waive other wrong-finger/fret evidence merely because B is positive.
        higher = [other for other in self.task.targets if other.target_id != target.target_id
            and other.string == target.string and other.fret > target.fret
            and other.onset_s <= now <= other.end_s
            and self.native._quality(measured, other.target_id)[0]]
        if not higher:
            return False
        quality = measured['targets'][target.target_id]['fretting_quality']
        allowed = set(identity for other in higher for identity in
            measured['targets'][other.target_id]['fretting_quality']['positive_evidence_ids'])
        wrong_fret = set(quality.get('wrong_fret_evidence_ids', ()))
        higher_fret = set(quality.get('higher_fret_evidence_ids', ()))
        return bool(higher_fret and higher_fret <= allowed and wrong_fret == higher_fret
            and not quality.get('wrong_finger') and not quality.get('wrong_assignment')
            and not quality.get('wrong_finger_evidence_ids')
            and not quality.get('wrong_assignment_evidence_ids'))

    def update(self, measured):
        # This also validates the clock and actual clean/positive evidence.
        report = self.native.update(measured)
        before, now = self.previous['task_time_s'], measured['task_time_s']
        dt = now-before
        terms = dict.fromkeys(TERMS, 0.)
        for target in self.task.targets:
            identity = target.target_id
            note = self.notes[identity]
            p, pp = self.native._quality(self.previous, identity)
            q, qp = self.native._quality(measured, identity)
            audible = self.native._amount(before, now, target.onset_s, target.end_s)
            clean = audible if p and q else 0.
            pw = self.previous['targets'][identity]['fretting_quality'].get('status') == 'wrong'
            qw = measured['targets'][identity]['fretting_quality'].get('status') == 'wrong'
            terms['refinement_clean_hold'] += WEIGHTS['clean_hold_second']*clean
            terms['refinement_wrong_press'] += WEIGHTS['wrong_press_second']*audible*.5*(pw+qw)
            terms['refinement_missing_press'] += WEIGHTS['missing_press_second']*audible*.5*((not p and not pw)+(not q and not qw))
            preparation = self.native._amount(before, now, target.press_s, target.onset_s)
            if preparation:
                first, last = self._potential(self.previous, identity), self._potential(measured, identity)
                if first is not None and last is not None:
                    progress = WEIGHTS['prepare_progress']*(last-first)*preparation/dt
                    note['prepare_progress'] += progress
                    terms['refinement_prepare_progress'] += progress
                ready_window = self.native._amount(before, now,
                    max(target.press_s, target.onset_s-.2), target.onset_s)
                if ready_window and self._ready(self.previous, target) and self._ready(measured, target):
                    note['prepare_ready_s'] += ready_window
                    terms['refinement_prepare_ready'] += WEIGHTS['prepare_ready_second']*ready_window
            row = report['per_target'][identity]
            required = self.plan['hold_fraction']*(target.end_s-target.onset_s)
            if self.native.config['mode'] == 'pair':
                required = min(target.end_s-target.onset_s, max(.05, required))
            if not note['hold_bonus_given'] and row['clean_hold_s']+1e-12 >= required:
                note['hold_bonus_given'] = True
                terms['refinement_hold_success'] += WEIGHTS['hold_success']
            if now > target.end_s+1e-12 and not note['hold_bonus_given'] and not note['hold_missed']:
                note['hold_missed'] = True
                terms['refinement_hold_missed'] += WEIGHTS['hold_missed']
            left, right = self.plan['release_windows'][identity]
            absent = self.native._amount(before, now, left, right) if not pp and not qp else 0.
            terms['refinement_release_absent'] += WEIGHTS['release_absent_second']*absent
            if now+1e-12 >= right and not note['release_evaluated']:
                note['release_evaluated'] = True
                if row['release_pass']:
                    note['release_bonus_given'] = True
                    terms['refinement_release_success'] += WEIGHTS['release_success']
        if not all(math.isfinite(value) for value in terms.values()):
            raise ValueError('finite refinement rewards required')
        self.previous = copy.deepcopy(measured)
        for name, value in terms.items():
            self.totals[name] += value
        return terms

    def invalidate(self, reasons):
        for reason in reasons:
            if reason not in self.safety_reasons:
                self.safety_reasons.append(reason)

    def summary(self, completed=False):
        report = self.native.summary(completed)
        safe = not self.safety_reasons
        return dict(schema=SCHEMA, task_time_s=self.previous['task_time_s'],
            criterion=dict(hold_fraction=self.plan['hold_fraction'],
                minimum_pair_hold_s=.05 if self.native.config['mode'] == 'pair' else None,
                release_absent_fraction=self.plan['release_absent_fraction']),
            per_target=copy.deepcopy(self.notes), raw_reward_terms_total=copy.deepcopy(self.totals),
            safety_invalidated=not safe, safety_reasons=list(self.safety_reasons),
            native=report, native_success=bool(safe and report['diagnostic_success']),
            legacy_song_history='40% progress compatibility only; current success is native transition plus role/safety')
