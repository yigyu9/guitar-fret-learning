"""Native contact, strike, task-quality and stability measurements at 240 Hz."""
import copy
import math
from dataclasses import dataclass, asdict
import numpy as np
from guitar_learning.core.geometry import (frame, geometry_snapshot, fret_target,
    world_to_guitar, relative_sweep_inputs)
from guitar_learning.song.task import MusicLedger


# Fretting contact evidence.
@dataclass(frozen=True)
class FretTarget:
    string_number: int
    musical_fret: int
    finger: str = None

    def __post_init__(self):
        if type(self.string_number) is not int or not 1 <= self.string_number <= 6:
            raise ValueError('physical string_number must be1..6')
        if type(self.musical_fret) is not int or not 0 <= self.musical_fret <= 22:
            raise ValueError('musical_fret must be0..22; open0 has no press goal')
        if self.musical_fret and self.finger not in ('index', 'middle', 'ring', 'pinky'):
            raise ValueError('pressed target requires a named non-thumb fretting finger')


@dataclass(frozen=True)
class FretContract:
    minimum_dwell_s: float
    marker_approach_max_m: float = .015
    lateral_max_m: float = .003
    height_abs_max_m: float = .003
    fret_cell_margin_m: float = .002
    witness_max_gap_m: float = .0001

    def __post_init__(self):
        if any(not math.isfinite(value) or value <= 0 for value in asdict(self).values()):
            raise ValueError('all explicit diagnostic thresholds/dwell must be finite positive')


def _step(value):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 0:
        raise ValueError('nonnegative integer actual physics_step required')
    return int(value)


def _time_check(value, step):
    if 'time_s' in value and (not math.isfinite(value['time_s']) or abs(value['time_s'] - step / 240.) > 1e-9):
        raise ValueError('sample time_s must equal actual physics_step/240')


def _local_point(body, value):
    local = np.array([value[axis] for axis in 'xyz'], dtype=float)
    if not np.isfinite(local).all():
        raise ValueError('finite native body-origin contact feature required')
    position, rotation = frame(body)
    return position + rotation.apply(local)


def measure_sample(state, human_names, guitar_names, contact_row, target, contract):
    """Match raw pair rows to current measured strings and fret-cell geometry.

    Native body-origin localPos is transformed without adding COM. Guitar-side
    feature coordinates supply x lane and z height at that feature's y. The
    nearest string uses actual nonparallel finite lines at the same y. The fret
    interval includes its wire boundaries plus the fixed diagnostic margin;
    the midpoint approach goal is a separate marker diagnostic.
    """
    if not isinstance(target, FretTarget) or not isinstance(contract, FretContract):
        raise TypeError('FretTarget and FretContract required')
    step = _step(state['physics_step'])
    if _step(contact_row['physics_step']) != step:
        raise ValueError('native contact/state physics_step mismatch')
    _time_check(state, step); _time_check(contact_row, step)
    snapshot = geometry_snapshot(state, human_names, guitar_names)
    humans = dict(zip(human_names, state['human_body_states']))
    guitars = dict(zip(guitar_names, state['guitar_body_states']))
    bodies = {'human/' + name: body for name, body in humans.items()}
    bodies.update({'guitar/' + name: body for name, body in guitars.items()})
    result = dict(physics_step=step, time_s=step / 240., target=asdict(target),
                  contract=asdict(contract), press_required=target.musical_fret != 0,
                  source_fingertip_shape_candidate=None,
                  source_shape_scope='not measured in this compact stage; distal origin is not a calibrated pad',
                  measurement_scope='Contact-conditioned diagnostic, not string force, actual pressure, sound or musical success; raw lambda is not calibrated N. Pair query and state share the post-fetch step; internal CC_LAST_SUBSTEP feature timing is not independently certified.',
                  contact_evidence=[], valid_evidence_ids=[], valid_contact_finger_bodies=[])
    if target.musical_fret == 0:
        result.update(marker_approach_distance_m=None, marker_approach=False,
                      fretting_contact_candidate=False, reason_flags=['open_string_no_press_required'])
        return result
    goal = fret_target(snapshot, target.string_number, target.musical_fret)
    marker_distance = float(np.linalg.norm(snapshot['finger_distal_origins_G_m'][target.finger] - goal))
    fret_y = snapshot['fret_markers_G_m'][target.musical_fret - 1:target.musical_fret + 1, 1]
    low_y, high_y = float(np.min(fret_y)), float(np.max(fret_y))
    allowed_human = {'human/LH:' + target.finger + str(index) for index in (2, 3)}
    allowed_guitar = {'guitar/guitar', 'guitar/G:fret' + str(target.musical_fret)}
    for index, raw in enumerate(contact_row['contacts']):
        names = [raw['body0_name'], raw['body1_name']]
        if not any(name.startswith('human/') for name in names) or not any(name.startswith('guitar/') for name in names):
            continue
        gi = 0 if names[0].startswith('guitar/') else 1
        human, guitar = names[1 - gi], names[gi]
        reasons = []
        if human not in allowed_human:
            reasons.append('wrong_finger_or_disallowed_human_body')
        if guitar not in allowed_guitar:
            reasons.append('wrong_fret_or_disallowed_guitar_body')
        value = float(raw['lambda'])
        if not math.isfinite(value):
            raise ValueError('finite raw native lambda required')
        if value <= 0:
            reasons.append('no_positive_native_contact')
        if any(name not in bodies for name in names):
            raise ValueError('native contact body name absent from aligned state')
        world = [_local_point(bodies[name], raw['localPos' + str(i)]) for i, name in enumerate(names)]
        gap = float(np.linalg.norm(world[0] - world[1]))
        point = world_to_guitar(world[gi], guitars['guitar'])
        if gap > contract.witness_max_gap_m:
            reasons.append('body_pair_witness_mismatch')
        start, end = snapshot['starts_G_m'], snapshot['ends_G_m']
        dy = end[:, 1] - start[:, 1]
        if np.any(np.abs(dy) < 1e-12):
            raise ValueError('finite strings must span the fret direction')
        fraction = (point[1] - start[:, 1]) / dy
        projected = start + fraction[:, None] * (end - start)
        lateral = np.abs(projected[:, 0] - point[0])
        chosen = target.string_number - 1
        nearest = int(np.argmin(lateral))
        other = np.delete(lateral, chosen)
        if nearest != chosen or np.any(other <= lateral[chosen] + 1e-12):
            reasons.append('wrong_string_or_ambiguous_lane')
        if not 0 <= fraction[chosen] <= 1:
            reasons.append('outside_finite_string')
        if lateral[chosen] > contract.lateral_max_m:
            reasons.append('lateral_distance_exceeds_contract')
        height = float(point[2] - projected[chosen, 2])
        if abs(height) > contract.height_abs_max_m:
            reasons.append('height_distance_exceeds_contract')
        if not low_y - contract.fret_cell_margin_m <= point[1] <= high_y + contract.fret_cell_margin_m:
            reasons.append('outside_target_fret_cell_with_wire_margin')
        identity = str(step) + ':' + str(index)
        evidence = dict(evidence_id=identity, raw_contact_index=index, human_body=human,
                        guitar_body=guitar, raw_lambda=value, positive_lambda=value > 0,
                        guitar_feature_W_m=world[gi].tolist(), human_feature_W_m=world[1 - gi].tolist(),
                        guitar_feature_G_m=point.tolist(), body_pair_witness_gap_m=gap,
                        nearest_physical_string=nearest + 1, lateral_to_target_string_m=float(lateral[chosen]),
                        signed_height_to_target_string_m=height, finite_string_fraction=float(fraction[chosen]),
                        valid=not reasons, reason_flags=reasons)
        result['contact_evidence'].append(evidence)
        if not reasons:
            result['valid_evidence_ids'].append(identity)
            result['valid_contact_finger_bodies'].append(human)
    valid = bool(result['valid_evidence_ids'])
    result.update(marker_approach_distance_m=marker_distance,
                  marker_approach=marker_distance <= contract.marker_approach_max_m,
                  midpoint_target_G_m=goal.tolist(), fret_cell_y_interval_m=[low_y, high_y],
                  fretting_contact_candidate=valid,
                  reason_flags=[] if valid else ['no_qualifying_same_finger_native_contact'])
    result['valid_contact_finger_bodies'] = sorted(set(result['valid_contact_finger_bodies']))
    return result


class FrettingTracker:
    """Fractional-step note interval; credit only consecutive observed spans.

    Adjacent valid samples credit their clipped interval, not an invented dwell
    per sample. A fractional music boundary is never rounded to the physics grid.
    To observe the entire interval, samples must bracket both boundaries.
    """
    def __init__(self, contract, note_start_step, note_end_step):
        if not isinstance(contract, FretContract):
            raise TypeError('FretContract required')
        self.contract = contract
        if any(isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)) or not math.isfinite(value) or value < 0 for value in (note_start_step, note_end_step)):
            raise ValueError('finite nonnegative fractional note boundaries required')
        self.start, self.end = float(note_start_step), float(note_end_step)
        if self.end <= self.start:
            raise ValueError('positive half-open note interval required')
        self.previous_step = self.target_key = self.streak_start = None
        self.previous_valid = self.acquired = False
        self.observed_note_steps = self.valid_note_steps = 0.
        self.note_target_changed = False

    def update(self, physics_step, measurement):
        step = _step(physics_step)
        if measurement.get('contract') != asdict(self.contract):
            raise ValueError('measurement/tracker contract mismatch')
        if _step(measurement['physics_step']) != step:
            raise ValueError('tracker/measurement physics_step mismatch')
        _time_check(measurement, step)
        if self.previous_step is not None and step <= self.previous_step:
            raise ValueError('duplicate or backward physics_step rejected')
        key = tuple(measurement['target'][name] for name in ('string_number', 'musical_fret', 'finger'))
        changed = self.target_key is not None and key != self.target_key
        gap = self.previous_step is not None and step != self.previous_step + 1
        old_acquired = self.acquired
        release = not gap and not changed and self.previous_valid and not measurement['fretting_contact_candidate']
        if gap or changed:
            self.streak_start = None
            self.acquired = False
        valid = bool(measurement['fretting_contact_candidate']) and bool(measurement['press_required'])
        if valid:
            if self.streak_start is None:
                self.streak_start = step
            duration = (step - self.streak_start) / 240.
            self.acquired = self.acquired or duration >= self.contract.minimum_dwell_s
        else:
            self.streak_start = None
            self.acquired = False
            duration = 0.
        if self.previous_step is not None and not gap:
            overlap = max(0., min(float(step), self.end) - max(float(self.previous_step), self.start))
            self.observed_note_steps += overlap
            if self.previous_valid and valid and not changed:
                self.valid_note_steps += overlap
            if overlap > 0:
                self.note_target_changed |= changed
        note_width = self.end - self.start
        coverage_fraction = self.observed_note_steps / note_width
        hold_fraction = self.valid_note_steps / note_width
        coverage = abs(coverage_fraction - 1.) <= 1e-12
        hold = coverage and abs(hold_fraction - 1.) <= 1e-12 and not self.note_target_changed
        observed_span = self.observed_note_steps / 240.
        self.previous_step, self.target_key, self.previous_valid = step, key, valid
        return dict(physics_step=step, target=measurement['target'], fretting_contact_candidate=valid,
                    consecutive_valid_span_s=duration, minimum_dwell_s=self.contract.minimum_dwell_s,
                    minimum_dwell_acquired=self.acquired, physics_step_gap=gap, target_changed=changed,
                    measured_contact_release=release, acquired_hold_dropout=bool(release and old_acquired),
                    intentional_music_release=None,
                    release_scope='Measured loss for the same observed target only; no intentional music-release claim',
                    note_interval_steps=[self.start, self.end], note_interval_half_open=True,
                    note_sample_coverage_complete=coverage, note_observed_sample_span_s=observed_span,
                    note_duration_s=note_width / 240., note_observed_coverage_fraction=coverage_fraction,
                    note_contact_hold_fraction=hold_fraction,
                    note_interval_hold_observed=hold,
                    note_shorter_than_required_dwell=note_width / 240. < self.contract.minimum_dwell_s,
                    note_interval_meets_minimum_dwell=hold and note_width / 240. >= self.contract.minimum_dwell_s,
                    valid_evidence_ids=list(measurement['valid_evidence_ids']))


# Pick crossings.
@dataclass(frozen=True)
class StrikeContract:
    physics_hz: float = 240.
    min_across_speed_m_s: float = .05
    min_depth_m: float = .001
    max_depth_m: float = .015
    allowed_y_m: tuple = (-.385, -.255)
    rearm_separation_m: float = .003
    rearm_steps: int = 2

    def __post_init__(self):
        scalars = (self.physics_hz, self.min_across_speed_m_s, self.min_depth_m,
                   self.max_depth_m, self.rearm_separation_m, *self.allowed_y_m)
        if not all(math.isfinite(x) for x in scalars):
            raise ValueError('finite strike contract required')
        if (self.physics_hz != 240 or self.min_across_speed_m_s < 0 or
                not 0 <= self.min_depth_m <= self.max_depth_m or
                self.rearm_separation_m <= 0 or len(self.allowed_y_m) != 2 or
                self.allowed_y_m[0] >= self.allowed_y_m[1] or
                type(self.rearm_steps) is not int or self.rearm_steps < 1):
            raise ValueError('invalid 240-Hz strike contract')


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


class StrikeDetector:
    def __init__(self, contract=None):
        self.contract = contract or StrikeContract()
        self.reset()

    def reset(self):
        self.last_hit_step = np.full(6, -np.inf)
        self.armed = np.ones(6, dtype=bool)
        self.last_step = None

    def update(self, previous, current):
        args = relative_sweep_inputs(previous, current, self.contract.physics_hz)
        step = current['physics_step']
        if self.last_step is not None and previous['physics_step'] != self.last_step:
            raise ValueError('detector updates must be consecutive and unique')
        a, b = np.asarray(args['previous_tip_g']), np.asarray(args['current_tip_g'])
        starts, ends = np.asarray(args['string_start_g']), np.asarray(args['string_end_g'])
        if starts.shape != (6, 3) or ends.shape != (6, 3) or a.shape != (3,) or b.shape != (3,) or not np.isfinite(np.r_[a,b,starts.ravel(),ends.ravel()]).all():
            raise ValueError('finite six-string geometry required')
        events, candidates = [], []
        delta = b - a
        for i, (start, end) in enumerate(zip(starts, ends)):
            line = end - start
            length = np.linalg.norm(line[:2])
            if length <= 1e-12:
                raise ValueError('nondegenerate strings required')
            denominator = _cross(delta[:2], line[:2])
            waiting_before = not self.armed[i]
            if abs(denominator) > 1e-12:
                alpha = _cross((start-a)[:2], line[:2]) / denominator
                u = _cross((start-a)[:2], delta[:2]) / denominator
                if 0 < alpha <= 1 and 0 <= u <= 1:
                    pick, string = a + alpha * delta, start + u * line
                    normal = np.array([-line[1], line[0]]) / length
                    if normal[0] < 0:
                        normal = -normal
                    speed = float(delta[:2] @ normal * self.contract.physics_hz)
                    depth = float(string[2] - pick[2])
                    reasons = []
                    if abs(speed) < self.contract.min_across_speed_m_s: reasons.append('speed')
                    if not self.contract.min_depth_m <= depth <= self.contract.max_depth_m: reasons.append('depth')
                    if not self.contract.allowed_y_m[0] <= pick[1] <= self.contract.allowed_y_m[1]: reasons.append('zone')
                    if waiting_before: reasons.append('wait_rearm')
                    event = dict(crossing_id=f'{step}:{i+1}', string_number=i+1,
                                 direction=int(np.sign(speed)), subframe_fraction=float(alpha),
                                 physics_step_fraction=float(step-1+alpha),
                                 crossing_G_m=pick.tolist(), depth_m=depth,
                                 across_speed_m_s=speed, valid=not reasons, reason_flags=reasons)
                    candidates.append(event)
                    if not reasons:
                        events.append(event)
                        self.armed[i] = False
                        self.last_hit_step[i] = step
            u_near = np.clip(np.dot(b-start, line)/np.dot(line,line), 0, 1)
            distance = np.linalg.norm(b-(start+u_near*line))
            if waiting_before and step-self.last_hit_step[i] >= self.contract.rearm_steps and distance >= self.contract.rearm_separation_m:
                self.armed[i] = True
        self.last_step = step
        return dict(events=sorted(events, key=lambda e:(e['subframe_fraction'],e['string_number'])),
                    candidates=candidates, scope='relative point-marker geometry; no string collision or sound')


# Stability and failure measurements.
def contact_flags(sample):
    pairs = []
    for row in sample['native_contacts']['contacts']:
        if not np.isfinite(float(row['lambda'])):
            raise ValueError('nonfinite native contact lambda')
        if float(row['lambda']) > 0:
            pairs.append({row['body0_name'], row['body1_name']})
    def touches(name, other):
        return any(name in pair and any(x.startswith(other) for x in pair if x != name) for pair in pairs)
    support = [touches('human/'+name, 'guitar/') for name in ('Chest','R_Shoulder','R_Hip')]
    fingers = [any(touches('human/LH:'+finger+str(n), 'guitar/') for n in (1,2,3))
               for finger in ('thumb','index','middle','ring','pinky')]
    feet = [any({'human/'+side+'_'+part,'ground'} <= pair for pair in pairs)
            for side in ('L','R') for part in ('Ankle',)]
    # A toe-only ground contact is still measured ground support.
    for i, side in enumerate(('L','R')):
        feet[i] = feet[i] or any({'human/'+side+'_Toe','ground'} <= pair for pair in pairs)
    return np.array(support+fingers+feet, dtype=float)


@dataclass(frozen=True)
class SafetyConfig:
    guitar_displacement_m: float = .08
    guitar_rotation_rad: float = .35
    foot_displacement_m: float = .04
    contact_loss_grace_s: float = .25
    joint_speed_rad_s: float = 50.
    failure_cost: float = 5.


class StabilityMonitor:
    def __init__(self, human_names, guitar_names, config=SafetyConfig()):
        self.human_names, self.guitar_names, self.config = tuple(human_names), tuple(guitar_names), config
        if any(not np.isfinite(x) or x <= 0 for x in asdict(config).values()):
            raise ValueError('positive finite stability thresholds required')

    def _poses(self, sample):
        native = sample['native']
        humans = dict(zip(self.human_names, native['human_body_states']))
        guitars = dict(zip(self.guitar_names, native['guitar_body_states']))
        return frame(guitars['guitar']), np.array([frame(humans[s+'_Ankle'])[0] for s in ('L','R')])

    def reset(self, sample):
        self.guitar0, self.feet0 = self._poses(sample)
        self.last_step = sample['native']['physics_step']
        # whole support loss, individual feet loss; support-sharing changes allowed.
        self.loss_s = np.zeros(3)
        return self._measure(sample, 0.)

    def update(self, sample):
        step = sample['native']['physics_step']
        if step != self.last_step+1:
            raise ValueError('stability requires consecutive 240Hz samples')
        self.last_step = step
        return self._measure(sample, 1/240.)

    def _measure(self, sample, dt):
        (position, rotation), feet = self._poses(sample)
        delta = position-self.guitar0[0]
        angle = (self.guitar0[1].inv()*rotation).as_rotvec()
        foot_delta = feet-self.feet0
        flags = contact_flags(sample)
        present = np.r_[bool(flags[:3].any()), flags[-2:].astype(bool)]
        self.loss_s = np.where(present, 0., self.loss_s+dt)
        speed = np.array([r['vel'] for r in sample['native']['human_dof_states']], dtype=float)
        if not np.isfinite(np.r_[delta,angle,foot_delta.ravel(),speed]).all():
            raise ValueError('nonfinite native state invalidates collection')
        c = self.config
        reasons = []
        if np.linalg.norm(delta) > c.guitar_displacement_m: reasons.append('guitar_displacement')
        if np.linalg.norm(angle) > c.guitar_rotation_rad: reasons.append('guitar_rotation')
        if np.max(np.linalg.norm(foot_delta,axis=1)) > c.foot_displacement_m: reasons.append('foot_displacement')
        if self.loss_s[0] > c.contact_loss_grace_s: reasons.append('support_lost')
        if np.any(self.loss_s[1:] > c.contact_loss_grace_s): reasons.append('ground_contact_lost')
        if np.max(np.abs(speed)) > c.joint_speed_rad_s: reasons.append('joint_speed')
        # Integrate rates in seconds; short support sharing changes have no penalty.
        rate = ((np.linalg.norm(delta)/.02)**2 + (np.linalg.norm(angle)/.15)**2
                + np.mean((np.linalg.norm(foot_delta,axis=1)/.02)**2)
                + float(not present[0]) + float(np.mean(~present[1:])))
        return dict(flags=flags, loss_s=self.loss_s.copy(), guitar_delta_m=delta,
                    guitar_rotation_vector_rad=angle, foot_delta_m=foot_delta,
                    cost_rate=float(rate), cost=float(rate*dt), failure_reasons=reasons,
                    max_joint_speed_rad_s=float(np.max(np.abs(speed))))


# Target history and clean-contact classification.
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


class TaskMeasurementV2(TaskMeasurement):
    def __init__(self, task, human_names, guitar_names, physics_hz=240.):
        if len(task.targets) != 1 or not task.targets[0].fret:
            raise ValueError('quality measurement supports one fretted target only')
        super().__init__(task,human_names,guitar_names,physics_hz)
        from guitar_learning.quality.strike_quality import StrikeQualityDetector
        self.detector = StrikeQualityDetector(task.targets[0])
        self.fretting_quality = {}

    def _contacts(self, sample):
        from guitar_learning.quality.fretting_quality import classify_fretting
        evidence, _ = super()._contacts(sample)
        quality = {t.target_id:classify_fretting(sample['geometry'],t,evidence[t.target_id],self.contract)
                   for t in self.task.targets}
        self.fretting_quality = copy.deepcopy(quality)
        return evidence,{identity for identity,q in quality.items() if q['clean_target_candidate']}

    def _observe(self, sample, initial):
        result = super()._observe(sample,initial)
        result['schema'] = 'guitar_learning.task_measurement.v2'
        result['scope'] = 'clean single-target fretting and preparation-filtered geometric strikes; no pressure/audio certification'
        result['fretting_quality'] = copy.deepcopy(self.fretting_quality)
        for identity,quality in self.fretting_quality.items():
            result['targets'][identity].update(
                positive_target_candidate=quality['positive_target_candidate'],
                clean_target_candidate=quality['clean_target_candidate'],
                fretting_quality=copy.deepcopy(quality))
        result['strike_quality'] = copy.deepcopy(self.detector.summary())
        return result
