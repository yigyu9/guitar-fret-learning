"""Actions-only smooth diagnostic replay of previously measured thumb targets."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path('/home/ajou/yigyu/3')
PHASE = ROOT/'docs/2026-10-26/guitar_learning_hand_contact_v22'
OUT = Path(__file__).resolve().parent
source = PHASE/'native_thumb_contact_zero_gap'
report = json.loads((source/'report.json').read_text())
raw = np.load(source/'physics_env0000.npz')
reference = raw['target'][0].copy()
joints = report['thumb_joint_indices']
names = report['native_joint_names']
from guitar_learning.core.control import ACTIVE_NAMES
actions = [ACTIVE_NAMES.index(names[j]) for j in joints]
transitions = {r['next']:r for r in report['transitions']}
contact = np.array(transitions['contact_hold']['thumb_target_rad'])
release = np.array(transitions['reapproach']['thumb_target_rad'])
initial = reference[joints].copy()

def goal(t):
    if t <= 1.:
        return initial, 'initial_hold'
    for start, end, lo, hi, label in ((1.,4.,initial,contact,'approach'),
            (4.,6.,contact,contact,'contact_hold'), (6.,9.,contact,release,'release'),
            (9.,10.,release,release,'released_hold'), (10.,13.,release,contact,'reapproach'),
            (13.,15.,contact,contact,'final_hold')):
        if t <= end+1e-8:
            u = min(max((t-start)/(end-start), 0.), 1.)
            u = u*u*(3-2*u)
            return lo+(hi-lo)*u, label
    raise ValueError('Protocol outside15s')

targets = np.tile(reference, (901,1))
requested = np.zeros((901,39), dtype=np.float32)
stages = ['initial_hold']
for i in range(1,901):
    targets[i,joints], stage = goal(i/60.)
    requested[i,actions] = (targets[i,joints]-targets[i-1,joints])*60./4.
    stages.append(stage)
if np.max(np.abs(requested)) > 1.:
    raise AssertionError('Tape exceeded unchanged production4rad/s codec')
np.savez_compressed(OUT/'smooth_thumb_target_tape.npz', action=requested,
    target=targets, clock=np.arange(901)*4, stage=np.array(stages))
inputs = [source/'report.json', source/'physics_env0000.npz', Path(__file__).resolve()]
(OUT/'tape_metadata.json').write_text(json.dumps(dict(
    input_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
    thumb_joint_indices=joints, thumb_action_indices=actions,
    initial_thumb_rad=initial.tolist(), contact_thumb_rad=contact.tolist(), released_thumb_rad=release.tolist(),
    duration_s=15., controls=900, max_abs_action=float(np.abs(requested).max()),
    scope='Only39 bounded actions replayed through productioncontroller; target rows are comparison metadata, not submitted state. Initial reference then3s smooth moves to previously observed contact/release targets; no q/body injection or PD edits.'),indent=2))
