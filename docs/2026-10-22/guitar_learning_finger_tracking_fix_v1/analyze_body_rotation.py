"""CPU reconstruction of captured finger-base rotations; no native simulation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / 'docs/2026-10-22/guitar_learning_ring_pinky_probe_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative_rotvec(body, names, finger):
    palm = Rotation.from_quat(body[:, names.index('human/LH:palm'), 3:7])
    base = Rotation.from_quat(body[:, names.index('human/LH:' + finger + '1'), 3:7])
    return (palm.inv() * base).as_rotvec()


def main():
    output = Path(__file__).with_name('body_rotation_diagnosis.json')
    cases = []
    inputs = {}
    for case_id, finger in ((2, 'ring'), (3, 'ring'), (10, 'pinky'), (11, 'pinky'), (16, 'pinky')):
        folder = OLD / 'native_run/prepared'
        metadata_path = folder / 'capture_metadata.json'
        metadata = json.loads(metadata_path.read_text())
        path = folder / ('case_%03d.npz' % case_id)
        inputs[str(path)] = digest(path)
        inputs[str(metadata_path)] = digest(metadata_path)
        with np.load(str(path)) as data:
            indices = [metadata['joint_names'].index('LH:' + finger + '1_' + a) for a in ('x', 'z')]
            rv = relative_rotvec(data['body_state'], metadata['body_names'], finger)
            q = data['q'][:, indices]
            projected = np.column_stack((q[:, 0], np.zeros(len(q)), q[:, 1]))
            error = (Rotation.from_rotvec(projected).inv() * Rotation.from_rotvec(rv)).magnitude()
            cases.append(dict(case_id=case_id, finger=finger,
                native_q_xz_vs_body_rotvec_xz_max_error_rad=float(np.max(abs(q-rv[:, (0, 2)]))),
                samples=[dict(frame=t, q_xz=q[t].tolist(), relative_rotvec_xyz=rv[t].tolist(),
                    omitted_y_rotation_error_rad=float(error[t])) for t in (0, 30, 60, 90, 150, 180)]))
    result = dict(inputs_sha256=inputs, cases=cases,
        scope='Actual saved body quaternions relative to palm. Missing rotation-vector component is an observation, not proof of an extra physical DOF or SDK fault.')
    with output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print('Saved body rotation diagnosis:', len(cases), 'cases')


if __name__ == '__main__':
    main()
