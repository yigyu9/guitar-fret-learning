"""Compare spring request anchors with saved native body samples and final goals."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation


def main():
    phase = Path(__file__).resolve().parent
    paths = [Path(__file__).resolve()] + [phase/'native/data'/n for n in (
        'human_torque_commands.json', 'human_rotation_spring.json', 'controls.json', 'trace.json')]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    torques, metadata, controls, trace = [json.loads(p.read_text()) for p in paths[1:]]
    samples = {r['physics_step']: r['native_state'] for r in trace}
    indices = [i for g in metadata['groups'] for i in g['joint_indices']]
    rows = 0

    def rotation(body):
        return Rotation.from_quat([body['pose']['r'][k] for k in 'xyzw'])

    for command in torques:
        step = command['before_physics_step']
        final = np.array(controls[step//4]['final_targets_rad'], dtype=np.float32)
        assert np.array_equal(final[indices], np.array(command['logical_targets_rad'], dtype=np.float32))
        if step not in samples:
            continue
        sample = samples[step]
        q = np.array([r['pos'] for r in sample['human_dof_states']], dtype=np.float32)
        assert np.array_equal(q[indices], np.array(command['actual_R9_rad'], dtype=np.float32))
        for group, saved in zip(metadata['groups'], command['rotation_groups']):
            parent = rotation(sample['human_body_states'][group['parent_body_index']])
            child = rotation(sample['human_body_states'][group['child_body_index']])
            expected = parent.inv()*child
            logged = Rotation.from_quat(saved['actual_parent_relative_xyzw'])
            assert (expected.inv()*logged).magnitude() < 1e-12
        rows += 1
    assert rows == 125
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items())
    (phase/'native_spring_anchor_check.json').write_text(json.dumps({
        'input_sha256': hashes, 'inputs_unchanged': True,
        'final_goals_exact_command_rows': len(torques), 'actual_pose_and_q_exact_saved_native_rows': rows,
        'scope': 'saved native sample anchors only; no force measurement or force-dual mapping certification'
    }, indent=2)+'\n')
    print('1004 final goals / 125 sampled native q and body rotation anchors exact')


if __name__ == '__main__':
    main()
