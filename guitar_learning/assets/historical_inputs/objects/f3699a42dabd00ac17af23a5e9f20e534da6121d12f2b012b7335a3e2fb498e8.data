"""CPU contracts for the 81-DOF physics foundation, without music rewards."""
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


CONFIG = Path(__file__).with_name('environment_foundation_v1.json')
MARKERS = ['L_Wrist', 'LH:palm'] + ['LH:'+s+'3' for s in
    ('thumb', 'index', 'middle', 'ring', 'pinky')] + ['R_Wrist', 'RH:palm'] + [
    'RH:'+s+'3' for s in ('thumb', 'index', 'middle', 'ring', 'pinky')] + ['RH:pick']


def finite(value, shape, label):
    result = np.asarray(value, dtype=np.float64)
    if result.shape != shape or not np.isfinite(result).all():
        raise ValueError('invalid finite shape: '+label)
    return result


def rotation6(matrix):
    return np.asarray(matrix)[:, :2].T.reshape(6)


def relative_motion(point, velocity, guitar_p, guitar_v, guitar_omega, guitar_r):
    delta = point - guitar_p
    return guitar_r.T @ delta, guitar_r.T @ (
        velocity - guitar_v - np.cross(guitar_omega, delta))


class EnvironmentContract:
    def __init__(self, config_path=CONFIG):
        self.config_path = Path(config_path)
        self.config = json.loads(self.config_path.read_text())
        self.inputs = {str(self.config_path): hashlib.sha256(self.config_path.read_bytes()).hexdigest()}
        objects = []
        for key in ('initial_candidate', 'native_reference'):
            path = Path(self.config[key])
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != self.config[key+'_sha256']:
                raise ValueError('input hash mismatch: '+str(path))
            self.inputs[str(path)] = digest
            objects.append(json.loads(path.read_text()))
        self.candidate, self.reference = objects
        self.names = self.candidate['joint_names']
        if len(self.names) != 81 or len(set(self.names)) != 81 or self.names != self.reference['joint_names']:
            raise ValueError('native ordered 81 joint names required')
        props = self.reference['PD_properties']
        self.lower = finite([p['lower'] for p in props], (81,), 'lower')
        self.upper = finite([p['upper'] for p in props], (81,), 'upper')
        self.q_ref = finite(self.candidate['joint_angles_rad'], (81,), 'q_ref').astype(np.float32).astype(float)
        if np.any(self.lower >= self.upper) or np.any(self.q_ref < self.lower) or np.any(self.q_ref > self.upper):
            raise ValueError('initial angles must satisfy native limits without clipping')
        self.groups = []
        for name in self.names:
            if name.startswith(('Torso_', 'Spine_', 'Chest_')): group = 'body'
            elif name.startswith(('Neck_', 'Head_')): group = 'head'
            elif name.startswith(('LH:', 'RH:')): group = 'finger'
            elif name.startswith(('L_', 'R_')): group = 'arm'
            else: raise ValueError('unknown upper joint: '+name)
            self.groups.append(group)
        if [self.groups.count(k) for k in ('body', 'head', 'arm', 'finger')] != [9, 6, 24, 42]:
            raise ValueError('upper joint grouping mismatch')
        self.body = np.array([i for i, g in enumerate(self.groups) if g == 'body'])
        self.effective_lower, self.effective_upper = self.lower.copy(), self.upper.copy()
        width = np.deg2rad(self.config['body_target_half_range_deg'])
        self.effective_lower[self.body] = np.maximum(self.lower[self.body], self.q_ref[self.body]-width)
        self.effective_upper[self.body] = np.minimum(self.upper[self.body], self.q_ref[self.body]+width)
        self.mid = (self.effective_lower + self.effective_upper)/2
        self.half = (self.effective_upper - self.effective_lower)/2
        if np.any(self.half <= 0): raise ValueError('empty effective action range')
        self.rates = np.array([self.config['target_rates_rad_s'][g] for g in self.groups])
        self.dt = 1 / self.config['control_hz']
        self.physics_per_control = self.config['physics_hz'] // self.config['control_hz']
        if self.config['control_hz'] != 60 or self.config['physics_hz'] != 240:
            raise ValueError('60 Hz control and 240 Hz physics contract required')

    def normalized_native(self, q):
        return 2*(q-self.lower)/(self.upper-self.lower)-1

    def neutral_action(self):
        return (self.q_ref-self.mid)/self.half

    def targets(self, action, previous):
        action = finite(action, (81,), 'squashed_action')
        previous = finite(previous, (81,), 'previous_target')
        if np.any(np.abs(action) > 1) or np.any(previous < self.effective_lower-1e-7) or np.any(previous > self.effective_upper+1e-7):
            raise ValueError('action/previous target outside contract')
        requested = self.mid + self.half*action
        final = np.clip(requested, previous-self.rates*self.dt, previous+self.rates*self.dt)
        final = np.clip(final, self.effective_lower, self.effective_upper).astype(np.float32)
        return requested, final

    def clock(self, physics_step):
        if type(physics_step) is not int or physics_step < 0:
            raise ValueError('nonnegative integer physics step required')
        time = physics_step/self.config['physics_hz']
        prep = self.config['prep_seconds']
        horizon = self.config['diagnostic_seconds']
        return {'physics_step': physics_step, 'physics_time_s': time,
                'score_time_s': max(0., time-prep), 'phase': 'PREP' if time < prep else 'PLAY',
                'diagnostic_time_limit': time >= horizon}

    def encode(self, state, previous, chest_delta, guitar, markers, palms, z_chest, physics_step):
        """Consume same-timestamp world body-origin data; never fabricate music fields."""
        q = finite(state['q'], (81,), 'q')
        qdot = finite(state['qdot'], (81,), 'qdot')
        gp, gr, gv, gw = guitar
        gp, gv, gw = [finite(v, (3,), 'guitar vector') for v in (gp, gv, gw)]
        gr = finite(gr, (3, 3), 'guitar rotation')
        if not np.isfinite(z_chest) or z_chest <= .65: raise ValueError('invalid frozen chest height')
        low, high = np.array([-.50, -.15, .65]), np.array([-.15, .15, z_chest])
        clock = self.clock(physics_step)
        relative = [relative_motion(p, v, gp, gv, gw, gr) for p, v in markers]
        if len(relative) != 15 or len(palms) != 2: raise ValueError('marker/palm count mismatch')
        horizon = self.config['diagnostic_seconds']
        prep = self.config['prep_seconds']
        blocks = [
            ('q_native', self.normalized_native(q), 'rad→native normalized', 'joint', 1),
            ('qdot', qdot, 'rad/s', 'joint', 10),
            ('previous_final_target', self.normalized_native(finite(previous, (81,), 'previous')), 'rad→native normalized', 'joint', 1),
            ('effective_lower', self.normalized_native(self.effective_lower), 'native normalized', 'joint', 1),
            ('effective_upper', self.normalized_native(self.effective_upper), 'native normalized', 'joint', 1),
            ('body_delta', q[self.body]-self.q_ref[self.body], 'rad', 'joint', np.deg2rad(5)),
            ('chest_reset_rotation', rotation6(chest_delta), 'rotation columns', 'Pelvis relative reset', 1),
            ('guitar_position', gp, 'm', 'W actor-root', .5),
            ('guitar_rotation', rotation6(gr), 'rotation columns', 'G→W', 1),
            ('guitar_origin_velocity', gv, 'm/s', 'W', 1),
            ('guitar_angular_velocity', gw, 'rad/s', 'W', 5),
            ('position_signed_margins', np.r_[gp-low, high-gp], 'm', 'W actor-root', .25),
            ('hand_origins_position', np.array([p for p, v in relative]), 'm', 'G', .25),
            ('hand_origins_velocity', np.array([v for p, v in relative]), 'm/s', 'moving G', 1),
            ('palm_rotation', np.array([rotation6(gr.T @ pr) for pr in palms]), 'rotation columns', 'palm→G', 1),
            ('clock', np.array([clock['phase']=='PREP', clock['phase']=='PLAY', clock['physics_time_s']/horizon,
                clock['score_time_s']/(horizon-prep), max(0., horizon-clock['physics_time_s'])/horizon]), 'one-hot/time ratio', 'simulation', 1),
        ]
        values, manifest, offset = [], [], 0
        for name, raw, unit, frame, scale in blocks:
            raw = np.asarray(raw)
            if not np.isfinite(raw).all(): raise ValueError('invalid observation: '+name)
            flat = (raw/scale).reshape(-1)
            values.append(flat)
            manifest.append({'name': name, 'offset': offset, 'length': flat.size,
                             'shape': list(raw.shape), 'dtype': 'float32', 'unit_before_scale': unit,
                             'frame': frame, 'scale_divisor': float(scale), 'clip': None,
                             'valid_rule': 'required finite same-timestamp source; error aborts'})
            offset += flat.size
        result = np.concatenate(values).astype(np.float32)
        if result.shape != (548,) or not np.isfinite(result).all(): raise ValueError('invalid 548D observation')
        return result, manifest
