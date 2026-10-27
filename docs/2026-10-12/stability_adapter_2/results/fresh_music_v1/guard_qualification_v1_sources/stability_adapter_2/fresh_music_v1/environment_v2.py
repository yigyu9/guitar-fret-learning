"""Dense 15 cm approach curriculum; preserved v1 mechanics and guard.

The recorded B baseline starts about 0.154 m from its assigned fret1 target.
exp(-d/.15) stays bounded in [0,1] and changes measurably over that distance;
the former 25 mm squared-exponential was effectively zero there. This is
distance shaping, not evidence of reachable contact or a verified press.
"""
import numpy as np

from .environment import MusicGuitarEnvironment as PreviousEnvironment
from .environment import collect_inputs

APPROACH_SCALE_M = .15


def dense_approach_quality(distance_m):
    distance = np.asarray(distance_m,dtype=float)
    if not np.isfinite(distance).all() or np.any(distance<0):
        raise ValueError('finite nonnegative approach distance required')
    return np.exp(-distance/APPROACH_SCALE_M)


def confirmed_release_quality(press_history):
    """Idle distance from the strings earns no release reward."""
    rows = list(press_history)
    if not rows: return 0.
    return float(np.mean([bool(row['released_after_hold']) and
                          row['assigned_contact_geometric_seconds']>=.1-1e-12 for row in rows]))


class MusicGuitarEnvironment(PreviousEnvironment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.abi.update(version='fresh_music_native_v2',reward_profile=dict(
            name='dense_approach_15cm_confirmed_release_v2',approach='exp(-distance_m/.15)',
            approach_scale_m=APPROACH_SCALE_M,approach_range=[0.,1.],
            release='released_after_hold and assigned_contact_geometric_seconds >= .1',
            other_reward_terms='unchanged from v1',guard='unchanged strict v5 Jacobian consistency'))

    def reset(self,seed=None):
        observation = super().reset(seed=seed)
        self.metadata['reward_profile'] = self.abi['reward_profile']
        return observation

    def _measure_music(self,score):
        metrics = super()._measure_music(score)
        distances = [r['distance_m'] for r in metrics['fret_rows']
                     if r['required'] or r['anticipatory_approach']]
        metrics['approach_quality_v1_diagnostic'] = metrics['approach_quality']
        metrics['approach_quality'] = float(np.mean(dense_approach_quality(distances))) if distances else 0.
        metrics['active_approach_distances_m'] = distances
        metrics['release_quality_v1_diagnostic'] = metrics['release_quality']
        metrics['release_quality'] = confirmed_release_quality(metrics['press_hold_release'])
        metrics['reward_profile'] = 'dense_approach_15cm_confirmed_release_v2'
        return metrics
