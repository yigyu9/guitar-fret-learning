"""Control-rate discounted potential difference, with no hover-time bonus."""
import math
import numpy as np
from guitar_learning.core.dense_environment import DenseRewardConfig, pick_guide

BETA = .25
GAMMA = .99
SCALE_M = .03
GUIDE = DenseRewardConfig(strike_y_m=-.36,depth_m=.004,sweep_half_width_m=.008)


def snapshot(task, notes, measured, sample, window_s):
    now = measured['task_time_s']
    if sample['geometry']['physics_step'] != measured['physics_step']:
        raise ValueError('same-step progress sample required')
    eligible = [t for t in task.targets if notes[t.target_id]['right_crossing_id'] is None
        and now < min(t.end_s,t.onset_s+window_s) and t.onset_s <= now+task.lookahead_s]
    if not eligible: return dict(target_id=None,potential=0.)
    target = min(eligible,key=lambda t:(t.onset_s,t.target_id))
    # A fixed departure-side endpoint: the time-varying guide cannot move
    # underneath a stationary pick and manufacture progress.
    goal,_ = pick_guide(sample['geometry'],target,target.onset_s-GUIDE.sweep_half_window_s,GUIDE)
    distance = float(np.linalg.norm(np.asarray(sample['geometry']['pick_G_m'])-goal))
    if not math.isfinite(distance): raise ValueError('finite live progress geometry required')
    return dict(target_id=target.target_id,potential=math.exp(-(distance/SCALE_M)**2),distance_m=distance)


def reward(before,after,failed=False):
    same = before['target_id'] is not None and before['target_id'] == after['target_id']
    value = BETA*(GAMMA*after['potential']-before['potential']) if same else 0.
    if failed: value=min(0.,value)
    return dict(value=float(value),before=before,after=after,same_owner=same,
        scope='60Hz control-boundary potential difference; no goal-entry/exit bonus or continuous distance reward')
