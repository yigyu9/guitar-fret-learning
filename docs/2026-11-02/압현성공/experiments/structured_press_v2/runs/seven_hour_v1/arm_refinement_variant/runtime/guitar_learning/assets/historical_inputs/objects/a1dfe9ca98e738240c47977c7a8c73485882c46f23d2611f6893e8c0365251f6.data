"""Read-only per-physics-step musical evidence; no reward or simulator writes.

Contact candidates are not calibrated pressure; marker sweeps are not sound.
A sample is a post-fetch native state, its current guitar geometry, and the
same-step raw contact query. Internal solver feature timing remains uncertified.
"""
import copy
import numpy as np
from guitar_learning.core.fretting_v1 import FretTarget, FretContract, measure_sample
from guitar_learning.core.geometry_v1 import fret_target
from guitar_learning.music_task import MusicLedger
from guitar_learning.core.strike import StrikeDetector

FINGERS = {1:'index', 2:'middle', 3:'ring', 4:'pinky'}


class TaskMeasurement:
    def __init__(self, task, human_names, guitar_names, physics_hz=240.):
        if physics_hz != 240:
            raise ValueError('native contact measurement contract is 240Hz')
        self.task, self.human_names, self.guitar_names = task, tuple(human_names), tuple(guitar_names)
        self.hz = physics_hz
        self.contract = FretContract(minimum_dwell_s=.05)
        self.detector = StrikeDetector()
        self.release_required = {t.target_id: not any(
            u.target_id != t.target_id and (u.string,u.fret,u.finger)==(t.string,t.fret,t.finger)
            and t.onset_s < u.onset_s <= t.end_s + 1e-12
            for u in task.targets) and t.fret != 0 for t in task.targets}
        self.previous = None

    def reset(self, sample):
        self.ledger = MusicLedger(self.task)
        self.detector.reset()
        self.start_step = self._step(sample)
        self.previous = None
        self.previous_valid = set()
        self.seen_valid = set()
        self.last_valid_s = {}
        self.missed = set()
        self.wrong_total = 0
        return self._observe(sample, initial=True)

    def update(self, sample):
        if self.previous is None:
            raise RuntimeError('reset(sample) required')
        if self._step(sample) != self._step(self.previous) + 1:
            raise ValueError('consecutive unique native physics samples required')
        return self._observe(sample, initial=False)

    @staticmethod
    def _step(sample):
        native, geometry, contacts = sample['native'], sample['geometry'], sample['native_contacts']
        step = native['physics_step']
        if isinstance(step, bool) or not isinstance(step, (int, np.integer)) or step < 0:
            raise ValueError('integer actual physics step required')
        if geometry['physics_step'] != step or contacts['physics_step'] != step:
            raise ValueError('native/geometry/contact samples must have identical steps')
        if abs(contacts['time_s'] - step/240.) > 1e-9 or not np.isfinite(contacts['time_s']):
            raise ValueError('contact query time must match actual physics clock')
        return int(step)

    def _contacts(self, sample):
        # Cache identical physical targets; no target is silently selected away.
        cache, evidence, valid = {}, {}, set()
        def measured(string, fret, finger):
            key = (string,fret,finger)
            if key not in cache:
                cache[key] = measure_sample(sample['native'], self.human_names, self.guitar_names,
                    sample['native_contacts'], FretTarget(string,fret,finger), self.contract)
            return cache[key]
        for t in self.task.targets:
            if t.fret:
                m = measured(t.string+1,t.fret,FINGERS[t.finger])
                good = m['fretting_contact_candidate']
                evidence[t.target_id] = m
            else:
                blockers = []
                # Use native features independently of selected fret cell/body;
                # positive finger2/3 contacts anywhere on this finite string lane
                # can obstruct an open target. Thumb is included conservatively.
                m = measured(t.string+1,1,'index')
                for e in m['contact_evidence']:
                    name = e['human_body'][len('human/LH:'):] if e['human_body'].startswith('human/LH:') else ''
                    allowed_body = any(name == f+str(n) for f in ('thumb',*FINGERS.values()) for n in (2,3))
                    allowed_guitar = e['guitar_body'] in {'guitar/guitar', *('guitar/G:fret'+str(n) for n in range(1,23))}
                    if (allowed_body and allowed_guitar and e['positive_lambda'] and
                        e['body_pair_witness_gap_m'] <= self.contract.witness_max_gap_m and
                        e['nearest_physical_string'] == t.string+1 and
                        e['lateral_to_target_string_m'] <= self.contract.lateral_max_m and
                        abs(e['signed_height_to_target_string_m']) <= self.contract.height_abs_max_m and
                        0 <= e['finite_string_fraction'] <= 1):
                        blockers.append(e['evidence_id'])
                good = not blockers
                evidence[t.target_id] = dict(press_required=False, open_string_clear_candidate=good,
                    blocking_contact_evidence_ids=blockers, contact_evidence=m['contact_evidence'],
                    scope='no qualifying measured finger obstruction; not acoustic open-string certification')
            if good:
                valid.add(t.target_id)
        return evidence, valid

    def _geometry(self, sample, dt):
        g, result = dict(sample['geometry']), {}
        for key in ('starts_G_m', 'ends_G_m', 'fret_markers_G_m'):
            g[key] = np.asarray(g[key], dtype=float)
        starts, ends = g['starts_G_m'], g['ends_G_m']
        for t in self.task.targets:
            s, e = starts[t.string], ends[t.string]
            # Measured finite string point nearest the fixed strike-zone center.
            u = np.clip((-.32-s[1])/(e[1]-s[1]),0,1)
            pick_delta = s+u*(e-s)-np.asarray(g['pick_G_m'])
            if t.fret:
                delta = fret_target(g,t.string+1,t.fret)-np.asarray(g['finger_distal_origins_G_m'][FINGERS[t.finger]])
            else:
                delta = pick_delta
            prev = self.previous_geometry.get(t.target_id) if dt else None
            result[t.target_id] = dict(delta=delta.tolist(),
                velocity=((delta-np.asarray(prev['delta']))/dt).tolist() if prev else [0.,0.,0.],
                pick_delta=pick_delta.tolist(),
                pick_velocity=((pick_delta-np.asarray(prev['pick_delta']))/dt).tolist() if prev else [0.,0.,0.])
        return result

    def _detector_state(self, geometry):
        start, end = np.asarray(geometry['starts_G_m']), np.asarray(geometry['ends_G_m'])
        line = end-start
        normal = np.stack((-line[:,1],line[:,0]),axis=1)
        normal *= np.where(normal[:,0]<0,-1,1)[:,None]
        side = np.sign(np.sum((np.asarray(geometry['pick_G_m'])[:2]-start[:,:2])*normal,axis=1))
        cooldown = np.maximum(0,self.detector.contract.rearm_steps-(geometry['physics_step']-self.detector.last_hit_step))
        return (self.detector.armed.astype(float).tolist()+side.tolist()+cooldown.tolist(),
                [f'{field}_string{n}' for field in ('armed','side','cooldown_steps') for n in range(1,7)])

    def _observe(self, sample, initial):
        step = self._step(sample)
        now = (step-self.start_step)/self.hz
        dt = 0 if initial else 1/self.hz
        if initial:
            self.previous_geometry = {}
        geometry = self._geometry(sample,dt)
        evidence, valid = self._contacts(sample)
        old50, old100 = set(self.ledger.matches[.05]), set(self.ledger.matches[.1])
        held_before = sum(p.held_s for p in self.ledger.progress.values())
        lost, releases, crossings = [], [], []
        wrong = 0
        if not initial:
            both = valid & self.previous_valid
            self.ledger.update_interval((self._step(self.previous)-self.start_step)/self.hz,now,both)
            for t in self.task.targets:
                if t.target_id in self.previous_valid and t.target_id not in valid:
                    lost.append(t.target_id)
                    p = self.ledger.progress[t.target_id]
                    if t.fret and t.end_s <= now <= t.end_s+.1 and t.target_id in self.seen_valid and not p.released:
                        self.ledger.release(t.target_id,now)
                        if self.release_required[t.target_id]: releases.append(t.target_id)
            detected = self.detector.update(self.previous['geometry'],sample['geometry'])
            for event in detected['events']:
                at = (event['physics_step_fraction']-self.start_step)/self.hz
                matched = self.ledger.crossing(event['crossing_id'],at,event['string_number']-1,event['direction'],both)
                if not matched: wrong += 1
                crossings.append(dict(event, task_time_s=at, matched={str(k):v for k,v in matched.items()}))
        else:
            detected = dict(events=[],candidates=[])
        for identity in valid:
            self.last_valid_s[identity] = now
            self.ledger.progress[identity].ever_valid = True
        self.seen_valid |= valid
        new_missed = {t.target_id for t in self.task.targets if now > t.onset_s+.05+1e-12 and t.target_id not in self.ledger.matches[.05]}-self.missed
        self.missed |= new_missed
        self.wrong_total += wrong
        features, mask, identities = self.task.tokens(now,geometry,self.ledger)
        priority, priority_mask, priority_ids = self.task.priority_tokens(features,mask,identities)
        state, state_fields = self._detector_state(sample['geometry'])
        new50 = set(self.ledger.matches[.05])-old50
        new100 = set(self.ledger.matches[.1])-old100
        summary = dict(matched50=len(self.ledger.matches[.05]), matched100=len(self.ledger.matches[.1]),
            target_count=len(self.task.targets), held_total_s=sum(p.held_s for p in self.ledger.progress.values()),
            hold_fractions={t.target_id:self.ledger.progress[t.target_id].held_s/(t.end_s-t.onset_s) if t.end_s>t.onset_s else 0. for t in self.task.targets},
            released_count=sum(p.released for p in self.ledger.progress.values()),
            missed_strict=len(self.missed),wrong_crossings=self.wrong_total,elapsed_s=now)
        result = dict(physics_step=step,task_time_s=now,summary=summary,
            delta=dict(new_strict_matches=len(new50),new_lenient_only_matches=len(new100-new50),
                wrong_crossings=wrong,new_missed_strict=len(new_missed),
                held_delta_s=summary['held_total_s']-held_before,timely_releases=len(releases)),
            observation=dict(tokens=features,mask=mask,target_ids=identities,state=self.task.state(now,self.ledger),
                priority_tokens=priority,priority_mask=priority_mask,priority_ids=priority_ids),
            geometry=geometry,detector_state=state,detector_state_fields=state_fields,
            targets={t.target_id:dict(evidence=evidence[t.target_id],candidate=t.target_id in valid,
                last_contact_time_s=self.last_valid_s.get(t.target_id),
                time_since_last_contact_s=now-self.last_valid_s[t.target_id] if t.target_id in self.last_valid_s else None,
                measured_contact_lost=t.target_id in lost,
                dwell_s=self.ledger.progress[t.target_id].dwell_s,held_s=self.ledger.progress[t.target_id].held_s,
                release_required=self.release_required[t.target_id],final_release_measured=self.ledger.progress[t.target_id].released,
                final_release_time_s=self.ledger.progress[t.target_id].release_s)
                for t in self.task.targets},
            contact_lost_target_ids=lost,timely_release_target_ids=releases,new_strict_target_ids=sorted(new50),
            new_missed_strict_target_ids=sorted(new_missed),crossings=crossings,
            crossing_candidates=detected['candidates'],terminated=now>=self.task.duration_s,
            scope='native contact-conditioned fretting and geometric marker strikes; no pressure/audio certification')
        # Private copies prevent a caller mutating prior samples or cached state.
        self.previous = copy.deepcopy(sample)
        self.previous_valid = valid
        self.previous_geometry = geometry
        return result
