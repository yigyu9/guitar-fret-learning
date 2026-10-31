"""Compare saved native torso geometry with the original and current waist poses."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import pose, sha

R = Path(__file__).resolve().parents[1]
D = R / 'docs/2026-10-19/stability_adapter_2/results'
REFERENCES = {
    'original_waist': D / 'right_thigh_waist_v1/native_static_v2/initial_values.json',
    'previous_relief4': D / 'waist_upright_right_arm_v1/native_relief4_static/initial_values.json',
}


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cases', type=Path, nargs='+', required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    files = list(REFERENCES.values()) + [Path(__file__), R / 'stability_adapter_2/initial_pose_noise_v1.py']
    for case in args.cases:
        files += [case / name for name in ('initial_values.json', 'final_state.json', 'report.json')]
    inputs = {str(f.resolve()): sha(f) for f in files}
    refs = {name: read(file) for name, file in REFERENCES.items()}
    names = refs['previous_relief4']['human_body_names']
    joints = refs['previous_relief4']['joint_names']

    def poses(state):
        return {name: pose(value) for name, value in zip(names, state['human_body_states'])}

    current = poses(refs['previous_relief4']['native_initial_state'])
    right = current['R_Hip'][0] - current['L_Hip'][0]
    right[2] = 0
    right /= np.linalg.norm(right)
    front = np.array([-right[1], right[0], 0.])

    def geometry(state):
        ps = poses(state)
        return {name: float(np.rad2deg(np.arctan2(ps[name][1].apply([0, 0, 1]) @ front,
                                                  ps[name][1].apply([0, 0, 1])[2])))
                for name in ('Torso', 'Spine', 'Chest')}

    results = {}
    for case in args.cases:
        initial = read(case / 'initial_values.json')
        assert initial['human_body_names'] == names and initial['joint_names'] == joints
        assert read(case / 'report.json')['completed']
        state = initial['native_initial_state']
        ps = poses(state)
        comparisons = {}
        for label, ref in refs.items():
            original = poses(ref['native_initial_state'])
            relatives = {}
            for parent, child in (('Pelvis', 'Torso'), ('Torso', 'Spine'), ('Spine', 'Chest')):
                before = original[parent][1].inv() * original[child][1]
                after = ps[parent][1].inv() * ps[child][1]
                relatives[parent + '->' + child] = float(np.rad2deg((before.inv() * after).magnitude()))
            errors = []
            old_guitar = ref['native_initial_state']['guitar_body_states']
            assert len(old_guitar) == len(state['guitar_body_states']) == 39
            for old, new in zip(old_guitar, state['guitar_body_states']):
                p0, r0 = pose(old)
                p1, r1 = pose(new)
                errors.append((np.linalg.norm(p1 - p0), (r0.inv() * r1).magnitude()))
            assert max(e[0] for e in errors) < 3e-6 and max(e[1] for e in errors) < 1e-5
            comparisons[label] = {
                'initial_tilt_reduction_deg': {name: geometry(ref['native_initial_state'])[name] - geometry(state)[name]
                                               for name in ('Torso', 'Spine', 'Chest')},
                'initial_parent_child_rotation_difference_deg': relatives,
                'guitar39_max_position_difference_m': float(max(e[0] for e in errors)),
                'guitar39_max_rotation_difference_rad': float(max(e[1] for e in errors)),
            }
        results[case.name] = {'initial_forward_tilt_proxy_deg': geometry(state),
                              'final_forward_tilt_proxy_deg': geometry(read(case / 'final_state.json')),
                              'comparisons': comparisons}
    assert all(sha(path) == digest for path, digest in inputs.items())
    with args.out.open('x') as stream:
        json.dump({'input_sha256': inputs, 'references': {k: str(v) for k, v in REFERENCES.items()},
                   'reference_forward_tilt_proxy_deg': {k: geometry(v['native_initial_state']) for k, v in refs.items()},
                   'cases': results, 'scope': 'native local-Z world-forward tilt proxies and parent-child rotations; not clinical spine angles or scalar DOF sums'},
                  stream, ensure_ascii=False, indent=2, allow_nan=False)


if __name__ == '__main__':
    main()
