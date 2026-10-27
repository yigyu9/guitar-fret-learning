"""Measure motion in the final R video without rerunning or changing physics."""
import json
import os
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation


RESULT = Path(__file__).resolve().parents[1]
video = RESULT/'video'
metadata = json.loads((video/'capture_metadata.json').read_text())
episode = json.loads((video/'episode_env0000.json').read_text())
data = np.load(video/'poses_env0000.npz')
names, bodies = metadata['joint_names'], metadata['body_names']
arm = [i for i, name in enumerate(names) if name.startswith(('L_Thorax_', 'L_Shoulder_', 'L_Elbow_', 'L_Wrist_'))]
thumb = [i for i, name in enumerate(names) if name.startswith('LH:thumb')]
fingers = [i for i, name in enumerate(names) if name.startswith(('LH:index', 'LH:middle', 'LH:ring', 'LH:pinky'))]
guitar = data['body_state'][:, bodies.index('guitar/guitar')]
wrist = data['body_state'][:, bodies.index('human/L_Wrist')]
wrist_g = Rotation.from_quat(guitar[:, 3:7]).inv().apply(wrist[:, :3]-guitar[:, :3])
time_s = data['time_s']

def joints(indices):
    return {names[i]: dict(actual_range_deg=float(np.rad2deg(np.ptp(data['q'][:, i]))),
        target_range_deg=float(np.rad2deg(np.ptp(data['target'][:, i]))),
        actual_target_max_abs_error_deg=float(np.rad2deg(np.max(np.abs(data['q'][:, i]-data['target'][:, i])))))
        for i in indices}

result = dict(schema='guitar_learning.hour01_video_motion_analysis.v1',
    scope='predeclared env0 final R32 model first whole song only',
    control_endpoints=len(time_s), duration_s=float(time_s[-1]),
    arm_action_max_abs=float(np.abs(data['action'][:, :12]).max()),
    arm_action_mean_abs=float(np.abs(data['action'][:, :12]).mean()),
    arm_max_adjacent_action_change=float(np.abs(np.diff(data['action'][:, :12], axis=0)).max()),
    action_change_reward=episode['reward_components']['action_change'],
    nonthumb_action_max_abs=float(np.abs(data['action'][:, 17:33]).max()),
    wrist_g_axis_ranges_mm=(1000*np.ptp(wrist_g, axis=0)).tolist(),
    wrist_g_max_distance_from_first_mm=float(1000*np.linalg.norm(wrist_g-wrist_g[0], axis=1).max()),
    arm=joints(arm), thumb=joints(thumb), nonthumb_fingers=joints(fingers),
    thumb_target_first_deg=np.rad2deg(data['target'][0, thumb]).tolist(),
    thumb_target_last_deg=np.rad2deg(data['target'][-1, thumb]).tolist())
assert result['nonthumb_action_max_abs'] == 0
assert max(x['target_range_deg'] for x in result['nonthumb_fingers'].values()) == 0
(RESULT/'motion_analysis.json').write_text(json.dumps(result, indent=2)+'\n')

os.environ.setdefault('MPLCONFIGDIR', '/tmp/guitar_learning_hour01_matplotlib')
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
axes[0, 0].plot(time_s, data['action'][:, :12])
axes[0, 0].set(title='Arm/wrist12: small deterministic commands', ylabel='Normalized action', ylim=(-.05, .05))
axes[0, 1].plot(time_s, np.rad2deg(data['q'][:, arm]-data['q'][0, arm]))
axes[0, 1].set(title='Arm/wrist12: actual joint-coordinate change', ylabel='Degrees from first endpoint')
for i in (thumb[1], thumb[3], thumb[4]):
    axes[1, 0].plot(time_s, np.rad2deg(data['q'][:, i]-data['q'][0, i]), label=names[i])
axes[1, 0].set(title='Thumb: cumulative drift in selected coordinates', ylabel='Degrees from first endpoint')
axes[1, 0].legend(frameon=False)
axes[1, 1].plot(time_s, np.rad2deg(data['q'][:, fingers]-data['q'][0, fingers]))
axes[1, 1].set(title='Nonthumb16: passive motion, zero policy commands', ylabel='Degrees from first endpoint', ylim=(-1, 1))
for axis in axes.flat:
    axis.set_xlabel('Control time (s)')
    axis.grid(alpha=.2)
fig.suptitle('Final R32 native capture | active support, frozen nonthumb fingers')
fig.savefig(RESULT/'motion_trace.png', dpi=160)
plt.close(fig)
print('Motion metrics and trace saved.')
