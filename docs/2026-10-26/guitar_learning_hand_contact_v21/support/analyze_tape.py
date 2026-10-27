"""Describe fixed-action native replays; no musical success is inferred."""
import json
from pathlib import Path

import numpy as np

PHASE = Path(__file__).resolve().parents[1]


def analyze(folder):
    report = json.loads((folder/'report.json').read_text())
    data = np.load(folder/'physics_env0000.npz')
    fingers = ('thumb', 'index', 'middle', 'ring', 'pinky')
    joints = [n for n in report['joint_names'] if n.startswith('LH:')]
    indices = [report['joint_names'].index(n) for n in joints]
    force = np.linalg.norm(data['segment_net_force'], axis=-1)
    thumb_force = np.linalg.norm(data['thumb_net_force'], axis=-1)
    result = dict(scope=report['scope'], controls=report['controls'],
        physics_endpoints=report['physics_endpoints_per_environment'], physical_end_s=float(data['time_s'][-1]),
        completed=report['completed'], protocol_completed=report['protocol_completed'],
        stopped_by_safety=report['stopped_by_safety'],
        original_LH21_target_max_difference_rad=report['tape_LH21_reference_target_max_error_rad'],
        codec_max_difference_rad=report['max_codec_error_rad'],
        finger_rows=list(fingers[1:]), segment_columns=['proximal', 'middle', 'distal'],
        finger_net_force_max_N=force.max(0).tolist(),
        finger_net_force_mean_N=force.mean(0).tolist(),
        finger_net_force_over_001N_fraction=(force >= .01).mean(0).tolist(),
        thumb_net_force_max_N=thumb_force.max(0).tolist(),
        thumb_net_force_mean_N=thumb_force.mean(0).tolist(),
        thumb_net_force_over_001N_fraction=(thumb_force >= .01).mean(0).tolist(),
        final_LH21={n:dict(actual_degrees=float(np.rad2deg(data['q'][-1,j])),
                           target_degrees=float(np.rad2deg(data['target'][-1,j]))) for n,j in zip(joints,indices)},
        all_environment_extrema=report['all_environment_extrema'], reset_check=report['reset_check'],
        source_changes=report['changed_inputs'])
    (folder/'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    return result


if __name__ == '__main__':
    both = [analyze(PHASE/name) for name in ('action_tape_source_filters','action_tape_selective_filters')]
    (PHASE/'support'/'tape_analysis.json').write_text(json.dumps(both,indent=2,allow_nan=False))
    for item in both:
        print(item['all_environment_extrema'])
        print('finger_max',item['finger_net_force_max_N'],'thumb_max',item['thumb_net_force_max_N'])
