"""Single-target preparation, one crossing and recovery over native geometry.

``ready`` is episode-latched; ``recovered`` describes current consecutive clear
observations, with ``ever_recovered`` preserving history. Two qualifying
observations establish one measured 1/240-second interval, not sample_count/hz.
Native crossing eligibility and candidate dictionaries remain unchanged. Only
matching events rejected by this wrapper are removed from the returned events.
"""
import copy
import numpy as np
from guitar_learning.music_task import ScoreTarget
from guitar_learning.core.strike import StrikeDetector


STRIKE_QUALITY_METADATA = dict(schema='guitar_learning.strike_quality.v1',
    separation_m=.003, required_observations=2, physics_hz=240.,
    preparation='target-direction departure side; finite target segment and original depth/zone; previous readiness only',
    ready='latched achievement; ready_dwell_s is longest consecutive qualifying interval',
    recovery='current two separated observations strictly after accepted crossing; finite target segment3D distance',
    recovery_dwell_s='current consecutive separated interval; resets on approach; ever_recovered preserves history',
    extra='matching eligible repeats, including wait_rearm-only repeats, blocked for separate quality penalty',
    diagnostic='depth/zone/speed failures, including lifted XY passages, are not wrong-strike events',
    wait_rearm='blocked log only when depth/zone/speed all qualify',
    scope='point-marker geometry only; no physical grip-force gate, string vibration or sound; original held hand shape remains')


class StrikeQualityDetector:
    separation_m = .003
    required_observations = 2

    def __init__(self, target):
        if (not isinstance(target, ScoreTarget) or type(target.string) is not int
                or not 0 <= target.string < 6 or type(target.direction) is not int
                or target.direction not in (-1, 1)):
            raise ValueError('one ScoreTarget with canonical string/direction required')
        self.target = target
        self.detector = StrikeDetector()
        self.reset()

    @property
    def contract(self): return self.detector.contract

    @property
    def armed(self): return self.detector.armed

    @property
    def last_hit_step(self): return self.detector.last_hit_step

    @property
    def last_step(self): return self.detector.last_step

    def reset(self):
        self.detector.reset()
        self.ready = self.recovered = self.ever_recovered = False
        self.ready_dwell_s = self.recovery_dwell_s = 0.
        self._ready_samples = self._recovery_samples = 0
        self.accepted_crossing_ids = []
        self.unprepared_crossing_ids = []
        self.extra_crossing_ids = []
        self.blocked_reasons = {}
        self.counts = dict(raw_candidates=0, native_eligible=0, matching_native_eligible=0,
            wrong_native_eligible=0, diagnostic_ineligible=0, wait_rearm=0)

    def _geometry(self, sample):
        start = np.asarray(sample['starts_G_m'])[self.target.string]
        end = np.asarray(sample['ends_G_m'])[self.target.string]
        pick = np.asarray(sample['pick_G_m'])
        line = end-start
        normal = np.array([-line[1], line[0]])/np.linalg.norm(line[:2])
        if normal[0] < 0: normal = -normal
        u = float(np.dot(pick[:2]-start[:2], line[:2])/np.dot(line[:2], line[:2]))
        depth = float((start+u*line)[2]-pick[2])
        signed = float(np.dot(pick[:2]-start[:2], normal))
        preparation = (0. <= u <= 1. and
            -self.target.direction*signed >= self.separation_m and
            self.contract.min_depth_m <= depth <= self.contract.max_depth_m and
            self.contract.allowed_y_m[0] <= pick[1] <= self.contract.allowed_y_m[1])
        nearest = start+np.clip(np.dot(pick-start, line)/np.dot(line, line), 0., 1.)*line
        separated = float(np.linalg.norm(pick-nearest)) >= self.separation_m
        return preparation, separated

    def _observe(self, sample, *, recovery):
        preparation, separated = self._geometry(sample)
        self._ready_samples = self._ready_samples+1 if preparation else 0
        self.ready_dwell_s = max(self.ready_dwell_s, max(0, self._ready_samples-1)/240.)
        self.ready |= self._ready_samples >= self.required_observations
        if recovery:
            self._recovery_samples = self._recovery_samples+1 if separated else 0
            self.recovery_dwell_s = max(0, self._recovery_samples-1)/240.
            self.recovered = self._recovery_samples >= self.required_observations
            self.ever_recovered |= self.recovered

    def _matching(self, event):
        return (event['string_number'] == self.target.string+1 and
                event['direction'] == self.target.direction)

    def _block(self, event, reasons):
        self.blocked_reasons[event['crossing_id']] = list(reasons)

    def update(self, previous, current):
        # Original detector validates consecutive frames before our history
        # changes. Initial previous frame counts as only one ready observation.
        first = self.detector.last_step is None
        detected = self.detector.update(previous, current)
        if first: self._observe(previous, recovery=False)
        ready_before = self.ready
        accepted_before = bool(self.accepted_crossing_ids)
        events = []
        self.counts['raw_candidates'] += len(detected['candidates'])
        for event in detected['events']:
            self.counts['native_eligible'] += 1
            if not self._matching(event):
                self.counts['wrong_native_eligible'] += 1
                events.append(event)  # existing timing ledger penalizes once
                continue
            self.counts['matching_native_eligible'] += 1
            identity = event['crossing_id']
            if self.accepted_crossing_ids:
                self.extra_crossing_ids.append(identity)
                self._block(event, ['extra_matching_crossing'])
            elif not ready_before:
                self.unprepared_crossing_ids.append(identity)
                self._block(event, ['unprepared_matching_crossing'])
            else:
                self.accepted_crossing_ids.append(identity)
                events.append(event)
        for candidate in detected['candidates']:
            reasons = candidate['reason_flags']
            if reasons == ['wait_rearm']:
                self.counts['wait_rearm'] += 1
                blocked = ['wait_rearm']
                if self.accepted_crossing_ids and self._matching(candidate):
                    self.extra_crossing_ids.append(candidate['crossing_id'])
                    blocked.append('extra_matching_crossing')
                self._block(candidate, blocked)
            elif reasons:
                # XY passage above/deep/outside/too slow is diagnostic only.
                self.counts['diagnostic_ineligible'] += 1
        # Current preparation cannot change earlier crossing decisions. Recovery
        # starts with observations strictly after the accepted crossing frame.
        self._observe(current, recovery=accepted_before)
        return dict(detected, events=events, quality=self.summary())

    def summary(self):
        counts = dict(self.counts, accepted=len(self.accepted_crossing_ids),
            unprepared=len(self.unprepared_crossing_ids), extra=len(self.extra_crossing_ids),
            blocked=len(self.blocked_reasons))
        return dict(schema='guitar_learning.strike_quality.v1', target_id=self.target.target_id,
            ready=bool(self.ready), ready_dwell_s=self.ready_dwell_s,
            ready_consecutive_samples=self._ready_samples,
            accepted_crossing_ids=list(self.accepted_crossing_ids),
            unprepared_count=counts['unprepared'], extra_count=counts['extra'],
            unprepared_crossing_ids=list(self.unprepared_crossing_ids),
            extra_crossing_ids=list(self.extra_crossing_ids),
            recovered=bool(self.recovered), recovery_dwell_s=self.recovery_dwell_s,
            ever_recovered=bool(self.ever_recovered),
            recovery_consecutive_samples=self._recovery_samples,
            blocked_event_ids=list(self.blocked_reasons), blocked_reasons=copy.deepcopy(self.blocked_reasons),
            counts=counts, previous_actual_step=self.detector.last_step,
            preparation=copy.deepcopy(STRIKE_QUALITY_METADATA))
