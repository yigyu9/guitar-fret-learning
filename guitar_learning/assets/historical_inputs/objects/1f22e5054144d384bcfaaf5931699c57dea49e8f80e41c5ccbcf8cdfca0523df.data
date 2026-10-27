"""Measured stability costs and explicit starting thresholds for learning.

These thresholds are learning criteria, not a replacement for the V3 pose audit.
Raw positive contact lambda is a contact flag, never a calibrated load in N.
"""
from dataclasses import dataclass, asdict
import numpy as np
from .geometry_v1 import frame


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
