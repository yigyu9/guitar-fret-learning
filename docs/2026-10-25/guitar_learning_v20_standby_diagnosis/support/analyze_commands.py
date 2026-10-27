"""Check original video policy requests against its native episode summary."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
sys.path.insert(0, str(ROOT))
from guitar_learning.core.control import ACTIVE_NAMES


def main():
    source = PHASE.parent/'guitar_learning_v20_A500/evaluation_repeat1'
    with (source/'first_episodes.jsonl').open() as stream:
        episode = next(row for row in map(json.loads, stream) if row['env_id'] == 0)
    motion = episode['left_finger_motion']
    pose = np.load(source/'poses_env0000.npz')
    reconstructed = np.load(PHASE/'raw/selected_reconstructed.npz')
    rows = []
    for f, finger in enumerate(('index', 'middle', 'ring', 'pinky')):
        full = reconstructed['known_full'][1:, f]
        for j, suffix in enumerate(('1_x', '1_z', '2', '3')):
            name = 'LH:'+finger+suffix
            a = pose['action'][1:, ACTIVE_NAMES.index(name)]
            i = motion['joint_names'].index(name)
            positive, negative = float((a > 0).mean()), float((a < 0).mean())
            assert abs(positive-motion['values']['action_positive_fraction'][i]) < 1e-12
            assert abs(negative-motion['values']['action_negative_fraction'][i]) < 1e-12
            rows.append(dict(finger=finger, joint=name,
                positive_fraction=positive, negative_fraction=negative,
                known_full_gate_samples=int(full.sum()),
                known_full_positive_fraction=float((a[full] > 0).mean()),
                known_full_negative_fraction=float((a[full] < 0).mean()),
                final_q_deg=float(reconstructed['native_degrees'][-1, f, j]),
                final_target_deg=float(reconstructed['target_native_degrees'][-1, f, j])))
    angles, t = reconstructed['angles_degrees'], reconstructed['times_s']
    events = []
    for name, f, mask in (
        ('index MCP below zero', 0, angles[:, 0, 0] < 0),
        ('index DIP at least89deg', 0, angles[:, 0, 2] >= 89),
        ('index PIP at least89deg', 0, angles[:, 0, 1] >= 89),
        ('ring MCP>=89deg and PIP<=1deg', 2, (angles[:, 2, 0] >= 89) & (angles[:, 2, 1] <= 1)),
        ('pinky PIP at least89deg', 3, angles[:, 3, 1] >= 89)):
        k = int(np.flatnonzero(mask)[0])
        events.append(dict(event=name, physical_time_s=float(t[k]),
            gate_known_off=bool(reconstructed['known_off'][k, f])))
    result = dict(scope='Original repeat1/env0, 1969 completed60Hz control actions; excludes reset',
        rows=rows, first_observed_angle_events=events,
        original_finger_motion=motion,
        caveat='Action sign is a requested incremental target direction, not actual velocity or force. '
               'Known full-gate endpoints are a subset of actual standby endpoints.',
        fingerprints={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (source/'first_episodes.jsonl', source/'poses_env0000.npz',
             PHASE/'raw/selected_reconstructed.npz', Path(__file__).resolve())})
    (PHASE/'selected_native_commands.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    main()
