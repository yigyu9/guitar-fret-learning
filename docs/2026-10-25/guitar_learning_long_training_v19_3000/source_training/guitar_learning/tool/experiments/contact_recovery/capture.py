"""Native endpoint accounting and conservative teacher-row selection.

These are collection diagnostics, not a new reward or an alternative to the
full native/source audit. Both endpoints must be clean to earn interval time.
"""
import copy
import math

from guitar_learning.tool.experiments.transition.metrics import TransitionLedger


class RecoveryLedger:
    def __init__(self, target, measured, stability, *, acquisition_dwell_s=.05,
                 recovery_deadline_s=.5, recovery_dwell_s=.5, recovery_fraction=.9):
        values = (acquisition_dwell_s, recovery_deadline_s, recovery_dwell_s)
        if (any(isinstance(v, bool) or not math.isfinite(v) or v <= 0 for v in values)
                or not 0 < recovery_fraction <= 1):
            raise ValueError('positive finite recovery criteria required')
        self.target = target
        self.criteria = dict(acquisition_dwell_s=float(acquisition_dwell_s),
            recovery_deadline_s=float(recovery_deadline_s),
            recovery_dwell_s=float(recovery_dwell_s), recovery_fraction=float(recovery_fraction))
        self.previous = copy.deepcopy(measured)
        self.previous_safe = self._safe(stability)
        TransitionLedger._quality(measured, target.target_id)
        self.safety_invalidated = not self.previous_safe
        self.sample_count = 0
        self.clean_run_s = self.clean_total_s = self.wrong_s = self.missing_s = 0.
        self.first_clean_s = float(measured['task_time_s']) if self.clean and self.previous_safe else None
        self.acquired_s = None
        self.losses = []
        self.intervals = []
        self.perturbations = []

    @staticmethod
    def _safe(stability):
        if not isinstance(stability.get('failure_reasons'), list):
            raise ValueError('actual native stability failure list required')
        return not stability['failure_reasons']

    @property
    def clean(self):
        return TransitionLedger._quality(self.previous, self.target.target_id)[0]

    def mark_perturbation(self, now, diagnostic):
        if abs(now-self.previous['task_time_s']) > 1e-9:
            raise ValueError('perturbation must be marked at current measured time')
        self.perturbations.append(dict(task_time_s=float(now), diagnostic=copy.deepcopy(diagnostic)))

    def update(self, measured, stability):
        before, now = float(self.previous['task_time_s']), float(measured['task_time_s'])
        if (measured['physics_step'] != self.previous['physics_step']+1
                or not math.isfinite(now) or abs(now-before-1/240.) > 1e-9):
            raise ValueError('consecutive actual240Hz native measurements required')
        previous_clean = self.clean
        clean, _ = TransitionLedger._quality(measured, self.target.target_id)
        safe = self._safe(stability)
        self.safety_invalidated |= not safe
        # Do not count release after the prescribed note end as contact loss.
        left, right = max(0., before), min(now, float(self.target.end_s))
        dt = max(0., right-left)
        valid_clean = previous_clean and clean and self.previous_safe and safe
        self.intervals.append((before, now, bool(valid_clean)))
        if dt:
            self.clean_total_s += dt if valid_clean else 0.
            self.clean_run_s = self.clean_run_s+dt if valid_clean else 0.
            status = measured['targets'][self.target.target_id]['fretting_quality'].get('status')
            if status == 'wrong': self.wrong_s += dt
            if status == 'missing': self.missing_s += dt
            if clean and safe and self.first_clean_s is None: self.first_clean_s = now
            if (self.acquired_s is None
                    and self.clean_run_s+1e-12 >= self.criteria['acquisition_dwell_s']):
                self.acquired_s = now
            if self.acquired_s is not None and previous_clean and not clean and now < self.target.end_s-1e-12:
                self.losses.append(dict(loss_s=now, candidates=[], recovered_s=None,
                    first_recontact_s=None, recovery_delay_s=None, clean_dwell_fraction=None))
            for loss in self.losses:
                if loss['recovered_s'] is not None: continue
                if clean and not previous_clean and safe:
                    if loss['first_recontact_s'] is None: loss['first_recontact_s'] = now
                    if now-loss['loss_s'] <= self.criteria['recovery_deadline_s']+1e-12:
                        loss['candidates'].append(now)
                for start in loss['candidates']:
                    end = start+self.criteria['recovery_dwell_s']
                    if now+1e-12 < end or end > self.target.end_s+1e-12:
                        continue
                    amount = sum(max(0., min(b, end)-max(a, start))
                                 for a,b,valid in self.intervals if valid)
                    fraction = min(1., amount/self.criteria['recovery_dwell_s'])
                    if fraction+1e-12 >= self.criteria['recovery_fraction']:
                        loss.update(recovered_s=start, recovery_delay_s=start-loss['loss_s'],
                            clean_dwell_fraction=fraction)
                        break
        self.previous, self.previous_safe = copy.deepcopy(measured), safe
        self.sample_count += 1

    def summary(self, completed=False, musical_success=None):
        losses = [{k:copy.deepcopy(v) for k,v in row.items() if k != 'candidates'} for row in self.losses]
        recovered = sum(row['recovered_s'] is not None for row in losses)
        return dict(schema='guitar_learning.contact_recovery.metrics.v1',
            task_time_s=float(self.previous['task_time_s']), physics_sample_count=self.sample_count,
            completed=bool(completed), safety_valid=not self.safety_invalidated,
            target_id=self.target.target_id, first_clean_s=self.first_clean_s,
            acquired_s=self.acquired_s, clean_continuous_s=self.clean_run_s,
            clean_total_s=self.clean_total_s, wrong_s=self.wrong_s, missing_s=self.missing_s,
            loss_count=len(losses), recovered_count=recovered, losses=losses,
            recovery_success=bool(completed and not self.safety_invalidated and losses
                                  and recovered == len(losses)),
            acquisition_success=bool(completed and not self.safety_invalidated and self.acquired_s is not None),
            musical_success=musical_success, perturbations=copy.deepcopy(self.perturbations),
            criteria=dict(self.criteria, physics_hz=240, interval='both native endpoints; clipped before note end',
                acquisition_scope='50ms collection/loss-probe qualification by default; not the2s/0.3s curriculum gate'),
            scope='native qualified clean contact and safety; not pressure, audio, whole-hand clearance or musical success')


def select_bc_rows(rows, summary, *, completed, input_pins_verified, native_audit_verified):
    """Return indices of teacher corrective rows only after finalized evidence.

    Keep all original rows, including override and failure rows, in the capture.
    This selector is an additional gate; callers must actually replay the native
    measurements and verify immutable input pins before setting either proof.
    """
    if (completed is not True or input_pins_verified is not True or native_audit_verified is not True
            or summary.get('completed') is not True or summary.get('safety_valid') is not True
            or not (summary.get('recovery_success') if summary.get('loss_count', 0)
                    else summary.get('acquisition_success'))):
        raise ValueError('completed safe native-audited source-pinned success required before BC publication')
    selected = []
    previous = None
    for index, row in enumerate(rows):
        now = row['task_time_s']
        if (not math.isfinite(now) or (previous is not None and abs(now-previous-1/60.) > 1e-8)):
            raise ValueError('consecutive before-action60Hz rows required')
        previous = now
        action, teacher = row['action39'], row['teacher_action39']
        if (len(action) != 39 or len(teacher) != 39
                or any(not math.isfinite(v) or abs(v) > 1 for v in (*action, *teacher))
                or any(v != 0 for v in (*action[33:], *teacher[33:]))):
            raise ValueError('finite bounded39 actions with fixed right6 required')
        if type(row['override_active']) is not bool or type(row['native_safe']) is not bool:
            raise ValueError('explicit override and native safety labels required')
        if not row['override_active'] and action != teacher:
            raise ValueError('unperturbed expert action must be the actual teacher command')
        if not row['override_active'] and row['native_safe'] and row.get('teacher_corrective') is True:
            selected.append(index)
    return selected
