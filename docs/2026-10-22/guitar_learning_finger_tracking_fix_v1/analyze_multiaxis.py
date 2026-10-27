"""CPU analysis of actual N6 captures, including uncaptured-coordinate rotation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from analyze_body_rotation import relative_rotvec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = args.capture.resolve()
    paths = [root / n for n in ('capture_metadata.json', 'report.json', 'native240.npz')]
    metadata = json.loads(paths[0].read_text())
    report = json.loads(paths[1].read_text())
    assert report['completed'] and report['schedule_completed']
    results = []
    with np.load(str(paths[2])) as fast:
        for case in metadata['cases']:
            path = root / case['path']
            paths.append(path)
            finger, row = case['finger'], case['env_id']
            joints, bodies = metadata['joint_names'], metadata['native_body_names']
            x, z = [joints.index('LH:' + finger + '1_' + a) for a in ('x', 'z')]
            finger_bodies = [bodies.index('human/LH:' + finger + str(i)) for i in (1, 2, 3)]
            with np.load(str(path)) as data:
                assert len(data['q']) == 526
                rv = relative_rotvec(data['body_state'], metadata['body_names'], finger)
                q, target = data['q'], data['target']
                goal_delta = float(target[405, z] - target[285, z])
                movement = float(q[405, z] - q[285, z])
                peak = float(fast['contact_force_norm'][4*285:4*405, row][:, finger_bodies].max())
                results.append(dict(env_id=row, finger=finger, x_target_rad=case['x_target_rad'],
                    contact_free_pulse_and_hold=peak < .01, finger_net_contact_peak_N=peak,
                    z_allowed_target_delta_rad=goal_delta, z_actual_delta_rad=movement,
                    z_response_fraction=movement/goal_delta if goal_delta else None,
                    x_start_actual_rad=float(q[285, x]),
                    x_conditioning_target_error_rad=float(q[285, x]-target[285, x]),
                    z_start_target_error_rad=float(q[285, z]-target[285, z]),
                    z_hold_target_error_rad=float(q[405, z]-target[405, z]),
                    z_return_actual_error_rad=float(q[525, z]-q[285, z]),
                    z_return_target_error_rad=float(target[525, z]-target[285, z]),
                    total_DOF_force_last_100ms_mean_Nm=float(fast['dof_force'][4*399:4*405, row, z].mean()),
                    total_DOF_force_last_100ms_peak_abs_Nm=float(abs(fast['dof_force'][4*399:4*405, row, z]).max()),
                    native_q_xz_vs_body_rotvec_xz_max_error_rad=float(abs(q[:, [x,z]]-rv[:, [0,2]]).max()),
                    rotations=[dict(frame=i, relative_rotvec_xyz_rad=rv[i].tolist()) for i in (0, 240, 285, 345, 405, 465, 525)]))
    result = dict(schema='guitar_learning.multiaxis_analysis.v1',
        inputs_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        actual_physics=report['gpu_scene'], cases=results,
        scope='Response fraction is motion from probe start, not absolute accuracy. Conditioning histories differ. Contacts are preserved and marked. Total solver force is neither drive-only torque nor friction/pressure. Body relative rotation comparison uses this source finger/palm frame.')
    with args.out.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('Analyzed N6:', len(results), 'cases')


if __name__ == '__main__':
    main()
