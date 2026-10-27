"""240Hz diagnostic accounting independent of geometric reach proxies."""
import copy
import math

from guitar_learning.tool.experiments.transition.task import validate


class TransitionLedger:
    def __init__(self, task, measured, transition):
        self.config = validate(transition)
        self.task = task
        self.plan = task.provenance['transition']
        if any(self.plan[k] != v for k, v in self.config.items()):
            raise ValueError('transition task/config mismatch')
        if measured['task_time_s'] != 0.:
            raise ValueError('transition starts at policy clock zero')
        self.previous = copy.deepcopy(measured)
        self.hold = {t.target_id: 0. for t in task.targets}
        self.release = {t.target_id: 0. for t in task.targets}
        self.clean_absent = {t.target_id: 0. for t in task.targets}
        self.first_contact_absent = {t.target_id: None for t in task.targets}
        self.first_clean_absent = {t.target_id: None for t in task.targets}
        self.overlap_s = 0.
        self.handover_s = None
        self.sample_count = 0
        self.last_quality = {}

    @staticmethod
    def _quality(measured, identity):
        row = measured['targets'][identity]
        quality = row['fretting_quality']
        clean = row['candidate']
        positive = quality['positive_target_candidate']
        ids = quality['positive_evidence_ids']
        if (type(clean) is not bool or type(positive) is not bool or
                positive != bool(ids) or clean != quality['clean_target_candidate'] or clean and not positive):
            raise ValueError('native clean/positive contact evidence required')
        return clean, positive

    @staticmethod
    def _amount(start, end, left, right):
        return max(0., min(end, right)-max(start, left))

    def update(self, measured):
        before, now = self.previous['task_time_s'], measured['task_time_s']
        if (measured['physics_step'] != self.previous['physics_step']+1 or
                not math.isfinite(now) or abs(now-before-1/240.) > 1e-9):
            raise ValueError('consecutive actual240Hz transition measurements required')
        qualities = {}
        for target in self.task.targets:
            identity = target.target_id
            p, pp = self._quality(self.previous, identity)
            q, qp = self._quality(measured, identity)
            qualities[identity] = (p, pp, q, qp)
            if p and q:
                self.hold[identity] += self._amount(before, now, target.onset_s, target.end_s)
            left, right = self.plan['release_windows'][identity]
            release = self._amount(before, now, left, right)
            if not pp and not qp:
                self.release[identity] += release
                if before >= target.end_s and self.first_contact_absent[identity] is None:
                    self.first_contact_absent[identity] = now
            if not p and not q:
                self.clean_absent[identity] += release
                if before >= target.end_s and self.first_clean_absent[identity] is None:
                    self.first_clean_absent[identity] = now
            self.last_quality[identity] = dict(clean=q, positive=qp,
                                              positive_evidence_ids=list(measured['targets'][identity]['fretting_quality']['positive_evidence_ids']))
        if len(self.task.targets) == 2:
            a, b = self.task.targets
            ac, ap, az, aq = qualities[a.target_id]
            bc, bp, bz, bq = qualities[b.target_id]
            left, right = self.plan['preparation_window']
            if ac and az and bp and bq:
                self.overlap_s += self._amount(before, now, left, right)
            if now >= b.onset_s and not ap and not aq and bc and bz and self.handover_s is None:
                self.handover_s = now
        self.previous = copy.deepcopy(measured)
        self.sample_count += 1
        return self.summary()

    def summary(self, completed=False):
        per_target = {}
        for target in self.task.targets:
            identity = target.target_id
            hold_fraction = min(1., self.hold[identity]/(target.end_s-target.onset_s))
            window = self.plan['release_windows'][identity]
            release_fraction = min(1., self.release[identity]/(window[1]-window[0]))
            per_target[identity] = dict(clean_hold_s=self.hold[identity],
                clean_hold_fraction=hold_fraction, hold_pass=hold_fraction+1e-12 >= self.plan['hold_fraction'],
                qualified_target_contact_absent_s=self.release[identity],
                qualified_target_contact_absent_fraction=release_fraction,
                release_pass=release_fraction+1e-12 >= self.plan['release_absent_fraction'],
                clean_absent_s=self.clean_absent[identity],
                first_qualified_contact_absent_s=self.first_contact_absent[identity],
                qualified_contact_absent_latency_s=(self.first_contact_absent[identity]-target.end_s
                    if self.first_contact_absent[identity] is not None else None),
                first_clean_absent_s=self.first_clean_absent[identity])
        window = self.plan['preparation_window']
        overlap_fraction = min(1., self.overlap_s/(window[1]-window[0])) if window else None
        overlap_pass = bool(overlap_fraction is not None and overlap_fraction+1e-12 >= .9)
        complete = bool(completed and self.previous['task_time_s']+1e-9 >= self.task.duration_s)
        hold_pass = all(row['hold_pass'] for row in per_target.values())
        # Pair LH success retains the original minimum50ms/40% audible dwell.
        if self.config['mode'] == 'pair':
            hold_pass = all(self.hold[t.target_id]+1e-12 >=
                            min(t.end_s-t.onset_s, max(.05, .4*(t.end_s-t.onset_s)))
                            for t in self.task.targets)
        release_pass = all(row['release_pass'] for row in per_target.values())
        diagnostic = hold_pass and release_pass and (self.config['mode'] != 'overlap' or overlap_pass)
        return dict(self.config, schema='guitar_learning.transition_metrics.v1',
            task_time_s=self.previous['task_time_s'], physics_sample_count=self.sample_count,
            completed=complete, diagnostic_success=bool(complete and diagnostic),
            provisional_diagnostic_success=bool(diagnostic),
            per_target=per_target, last_quality=copy.deepcopy(self.last_quality),
            clean_a_and_positive_b_preparation_s=self.overlap_s,
            clean_a_and_positive_b_preparation_fraction=overlap_fraction,
            preparation_overlap_pass=overlap_pass,
            first_a_qualified_contact_absent_and_b_clean_s=self.handover_s,
            handover_latency_from_b_onset_s=(self.handover_s-self.task.targets[1].onset_s
                if self.handover_s is not None else None),
            criterion=dict(hold_fraction=self.plan['hold_fraction'], release_absent_fraction=.9,
                           release_grace_s=self.plan['release_grace_s'],
                           release_windows=copy.deepcopy(self.plan['release_windows']),
                           overlap_required=self.config['mode'] == 'overlap',
                           physics_hz=240, interval='both native endpoints; window clipped',
                           release='designated finger qualified target-contact evidence absent; not mere clean-candidate loss or whole-hand neck clearance'),
            scope='native contact diagnostics only; caller must combine episode safety and role-specific musical criteria')
