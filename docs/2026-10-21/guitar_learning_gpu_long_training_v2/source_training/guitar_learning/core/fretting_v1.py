"""Read-only 240-Hz contact-conditioned fretting measurements, not pressure/audio."""
from dataclasses import asdict, dataclass
import math
import numpy as np
from guitar_learning.core.geometry_v1 import frame, geometry_snapshot, fret_target, world_to_guitar


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
