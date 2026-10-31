"""Canonical targets and conservative 240 Hz joint crossing diagnostics."""
from pathlib import Path
import numpy as np
from tab2body.full.events import compile_song_bundle_events

BUNDLE = Path(__file__).resolve().parents[1]/'data/song_bundles/02_Jazz1-200-B_solo'


class JointMusicClock:
    def __init__(self, bundle=BUNDLE, dwell_s=0., tolerance_s=.05):
        self.timeline = compile_song_bundle_events(bundle)
        if self.timeline.fps != 60: raise ValueError('60Hz music required')
        self.events = self.timeline.events
        self.dwell_s, self.tolerance = float(dwell_s), float(tolerance_s)
        self.index, self.physics_step = 0, 0
        self.dwell = np.zeros(6)
        self.sounding = np.zeros(6, dtype=int)
        self.hits, self.bad = set(), False
        self.crossings, self.results = [], []

    def time(self, step=None):
        return (self.physics_step if step is None else step)/240-2

    def current(self):
        return self.events[self.index] if self.index < len(self.events) else None

    def targets(self):
        out = np.full(6, -1, dtype=int)
        event = self.current()
        if event:
            for target in event.string_targets: out[target.string] = target.fret
        return out

    def update(self, physics_step, sounding, releases=()):
        if physics_step != self.physics_step+1: raise ValueError('one authoritative physics tick')
        sounding = np.asarray(sounding, dtype=int)
        if sounding.shape != (6,) or np.any(sounding < 0) or np.any(sounding > 22):
            raise ValueError('valid measured sounding frets required')
        previous, prior_dwell = self.sounding.copy(), self.dwell.copy()
        self.dwell = np.where(sounding == previous, self.dwell+1/240, 1/240)
        self.sounding, self.physics_step = sounding, physics_step
        for string, fraction, direction, zone_valid in sorted(releases, key=lambda r:r[1]):
            if not 0 <= string < 6 or not np.isfinite(fraction) or not 0 <= fraction <= 1:
                raise ValueError('invalid crossing fact')
            cross_time = self.time(physics_step-1)+fraction/240
            event = self.current()
            row = {'physics_step':physics_step,'string':int(string),'fraction':float(fraction),
                   'score_time_s':float(cross_time),'event_id':event.event_id if event else None,
                   'accepted':False,'reason':'PREP' if cross_time < 0 else 'no_event',
                   'press_snapshot':'conservative_endpoint_bracket_240Hz'}
            if cross_time >= 0 and event:
                target = next((t for t in event.string_targets if t.string == string), None)
                expected = [s for s in event.strike.traversal_strings if s in event.strike.audible_strings]
                remaining = [s for s in expected if s not in self.hits]
                want_direction = 1 if event.strike.direction == 'down' else -1
                ready = target is not None and previous[string] == sounding[string] == target.fret
                dwell = prior_dwell[string]+fraction/240
                row.update(sounding_before=int(previous[string]),sounding_after=int(sounding[string]),
                           bracket_ready=bool(ready),dwell_s=float(dwell))
                checks = [('wrong_string',target is not None),('duplicate',string not in self.hits),
                          ('direction',direction == want_direction),('zone',bool(zone_valid)),
                          ('order',bool(remaining) and string == remaining[0]),
                          ('timing',target is not None and abs(cross_time-(event.score_time_s+target.traversal_offset_s)) <= self.tolerance+1e-9),
                          ('wrong_pitch_or_uncertain',ready),('dwell',ready and dwell >= self.dwell_s-1e-9)]
                row['reason'] = next((why for why,ok in checks if not ok),'accepted')
                row['accepted'] = row['reason']=='accepted'
                if row['accepted']: self.hits.add(string)
                else: self.bad = True
            self.crossings.append(row)
        # Resolve at the authored last crossing + fixed tolerance, never pause score time.
        while self.current() and self.time() > self.current().traversal_end_time_s+self.tolerance:
            e=self.current();required=set(e.strike.audible_strings)
            self.results.append({'event_id':e.event_id,'joint_success':self.hits==required and not self.bad,
                                 'accepted_strings':sorted(self.hits),'required_strings':sorted(required),
                                 'bad_crossing':self.bad,'reason':'success' if self.hits==required and not self.bad else 'miss_or_error'})
            self.index+=1;self.hits,self.bad=set(),False

    def observation(self):
        e=self.current();required=self.targets()
        accepted=np.array([i in self.hits for i in range(6)],float)
        return np.r_[required/22,self.sounding/22,self.dwell.clip(0,1),accepted,
                     float(e is not None),self.index/max(len(self.events),1),max(0,self.time())/60,
                     float(self.bad)].astype(np.float32)
