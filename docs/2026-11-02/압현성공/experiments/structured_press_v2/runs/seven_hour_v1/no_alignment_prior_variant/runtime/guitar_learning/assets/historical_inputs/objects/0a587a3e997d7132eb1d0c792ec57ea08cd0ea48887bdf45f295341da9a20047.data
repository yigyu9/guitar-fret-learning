"""Read-only joint fretting/strike coordination on the same native sample."""
import copy
import math
from guitar_learning.tool.experiments.joint.spec import COORDINATION_FIELDS, COORDINATION_SCALES, SCHEMA


def metadata():
    return dict(schema=SCHEMA, coupled_bonus=1., uncoupled_accepted_penalty=-.5,
        history_fields=list(COORDINATION_FIELDS), history_scales=list(COORDINATION_SCALES),
        coupling='new accepted strike ID must occur in current eligible crossing rows, match target string/direction and onset window before note end, with clean LH candidates at both native endpoints',
        success='safe full timeline plus both original hand quality criteria plus at least one coupled hit',
        safety='all positive terms suppressed for the entire failed control tick',
        scope='native clean contact and geometric crossing; not string pressure, vibration or audio')


class CoordinationLedger:
    def __init__(self, task, measured, timing):
        if len(task.targets) != 1 or task.targets[0].fret == 0:
            raise ValueError('one fretted target required for joint coordination')
        self.target, self.timing = task.targets[0], timing
        self.previous = measured
        self.accepted_ids = set(measured['strike_quality']['accepted_crossing_ids'])
        self.coupled, self.uncoupled, self.events, self.safety_reasons = [], [], [], []
        self.best_abs_error_s = None
        self.awarded = False

    def update(self, measured):
        previous = self.previous
        now, before = measured['task_time_s'], previous['task_time_s']
        if (measured['physics_step'] != previous['physics_step']+1
                or not math.isfinite(now) or abs(now-before-1/240.) > 1e-9):
            raise ValueError('consecutive actual240Hz joint measurements required')
        accepted = set(measured['strike_quality']['accepted_crossing_ids'])
        if not self.accepted_ids <= accepted:
            raise ValueError('accepted strike IDs cannot disappear')
        new = accepted-self.accepted_ids
        crossings = {row['crossing_id']: row for row in measured['crossings']}
        terms = dict(coordination_coupled=0., coordination_uncoupled=0.)
        t = self.target
        both_clean = all(row['targets'][t.target_id]['fretting_quality']['clean_target_candidate']
                         for row in (previous, measured))
        for identity in sorted(new):
            crossing = crossings.get(identity)
            actual = bool(crossing and crossing.get('valid') is True and not crossing.get('reason_flags'))
            at = crossing.get('task_time_s') if crossing else None
            interval = bool(actual and isinstance(at, (int, float)) and not isinstance(at, bool)
                            and math.isfinite(at) and before-1e-9 <= at <= now+1e-9)
            matching = bool(interval and (crossing['string_number'], crossing['direction'])
                            == (t.string+1, t.direction))
            error = at-t.onset_s if interval else None
            timely = bool(matching and abs(error) <= self.timing.window_s+1e-12 and at < t.end_s)
            coupled = bool(timely and both_clean)
            if coupled:
                self.coupled.append(identity)
                self.best_abs_error_s = abs(error) if self.best_abs_error_s is None else min(self.best_abs_error_s, abs(error))
                if not self.awarded:
                    terms['coordination_coupled'] += 1.
                    self.awarded = True
            else:
                self.uncoupled.append(identity)
                terms['coordination_uncoupled'] -= .5
            self.events.append(dict(crossing_id=identity, coupled=coupled, actual_current_crossing=interval,
                matching_string_direction=matching, within_stage_window_before_end=timely,
                both_endpoints_clean=bool(both_clean), error_s=error, task_time_s=now))
        self.accepted_ids = accepted
        self.previous = measured
        if self.safety_reasons:
            terms = {key: min(0., value) for key, value in terms.items()}
        return terms

    def invalidate(self, reasons):
        for reason in reasons:
            if reason not in self.safety_reasons:
                self.safety_reasons.append(reason)

    def history(self):
        return [float(len(self.coupled)), float(len(self.uncoupled)),
                float(self.best_abs_error_s is not None), self.best_abs_error_s or 0.,
                float(bool(self.safety_reasons)), float(self.awarded)]

    def summary(self, completed=False):
        safe = not self.safety_reasons
        return dict(schema=SCHEMA, coupled_hit_count=len(self.coupled), uncoupled_hit_count=len(self.uncoupled),
            coupled_crossing_ids=list(self.coupled), uncoupled_crossing_ids=list(self.uncoupled),
            best_abs_error_s=self.best_abs_error_s, coordination_awarded=self.awarded,
            provisional_success=bool(safe and self.coupled), stage_success=bool(completed and safe and self.coupled),
            safety_invalidated=not safe, safety_reasons=list(self.safety_reasons), events=copy.deepcopy(self.events),
            task_time_s=self.previous['task_time_s'], scope=metadata()['scope'])


def joint_quality(left, right, coordination):
    """Whole joint success cannot be inherited from separate hand checkpoints."""
    stage = all(row['stage_success'] for row in (left, right, coordination))
    provisional = all(row['provisional_success'] for row in (left, right, coordination))
    return dict(schema=SCHEMA, role='joint', stage_success=bool(stage), provisional_success=bool(provisional),
                left=copy.deepcopy(left), right=copy.deepcopy(right), coordination=copy.deepcopy(coordination),
                scope=metadata()['scope'])
