"""Goal-independent finite relative pick sweeps; geometric events, not sound.

Numpy transcription of tab2body/env/strike_detector.py segment intersection,
with an explicit upper depth bound and allowed zone applied to eligibility.
Each endpoint is expressed in its own measured guitar-root frame. Linear
relative interpolation is a one-physics-interval approximation, not CCD.
"""
from dataclasses import dataclass
import math
import numpy as np
from guitar_learning.core.geometry_v1 import relative_sweep_inputs


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
