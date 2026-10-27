"""Summarize the native 240Hz fixed hand probe without changing its inputs."""
import argparse
import json
from pathlib import Path

import numpy as np


def analyze(folder):
    report = json.loads((folder/'report.json').read_text())
    trace = np.load(folder/'physics_env0000.npz')
    control = np.load(folder/'controls_env0000.npz')
    names = report['joint_names']
    fingers = ('index', 'middle', 'ring', 'pinky')
    joint_ids = [names.index('LH:'+f+s) for f in fingers for s in ('1_x', '1_z', '2', '3')]
    q, target = np.rad2deg(trace['q'][:, joint_ids]), np.rad2deg(trace['target'][:, joint_ids])
    stage_rows = np.repeat(control['stage'], 4)
    forces = np.linalg.norm(trace['segment_net_force'], axis=-1)
    stages = {}
    for stage in dict.fromkeys(control['stage']):
        rows = np.flatnonzero(stage_rows == stage)
        first, last = rows[0], rows[-1]
        prior = max(first-1, 0)
        stages[str(stage)] = dict(samples=len(rows), duration_s=len(rows)/240,
            target_change_degrees=(target[last]-target[prior]).reshape(4, 4).tolist(),
            actual_change_degrees=(q[last]-q[prior]).reshape(4, 4).tolist(),
            tracking_rms_degrees=np.sqrt(np.mean((q[rows]-target[rows])**2, axis=0)).reshape(4, 4).tolist(),
            segment_net_force_mean_N=forces[rows].mean(0).tolist(),
            segment_net_force_max_N=forces[rows].max(0).tolist(),
            segment_net_force_over_001N_fraction=(forces[rows] >= .01).mean(0).tolist())
    # H32 means a sampling/PPO boundary only; this probe never resets there.
    steps = control['physics_step_before']
    boundaries = np.arange(31, len(steps)-1, 32)
    result = dict(scope=report['scope'], completed=report['completed'],
        measured_environment=0, num_simulated_environments=report['num_envs'],
        measured_physics_endpoints=len(q), sample_hz=240,
        matrix_rows=list(fingers), matrix_columns=['native_MCP_x', 'native_spread_z', 'PIP', 'DIP'],
        stages=stages, max_codec_error_rad=report['max_codec_error_rad'],
        H32_boundaries_tested=len(boundaries),
        H32_all_physics_clocks_contiguous=bool(np.all(steps[boundaries+1]-steps[boundaries] == 4)),
        reset_check=report['reset_check'],
        final_actual_degrees=q[-1].reshape(4, 4).tolist(),
        final_target_degrees=target[-1].reshape(4, 4).tolist(),
        final_tracking_max_degrees=float(np.max(np.abs(q[-1]-target[-1]))),
        source_changes=report['changed_inputs'],
        all_environment_extrema=report.get('all_environment_extrema'),
        hand_collision_native_readback_environments=report['scene'].get('hand_collision_native_readback_environments'),
        caveat='Net forces neither identify contact pairs nor certify pressure. Native spherical DOF values and actual palm-relative quaternion/rotvec are stored separately.')
    (folder/'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder', type=Path)
    args = parser.parse_args()
    result = analyze(args.folder)
    print(json.dumps({k: v for k, v in result.items() if k != 'stages'}, indent=2))
