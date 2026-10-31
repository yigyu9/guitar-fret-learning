"""실측 첫마디를 고정한 조건에서만 단일 해제 후보의 기하를 계산한다."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))

from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract

CANDIDATE_DEGREES = np.array([40., 10.])
MARGIN_M = .005
POSITION_TOLERANCE_M = .00001
ANGLE_TOLERANCE_RAD = .0001


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def anchored_distal(fk, q, first_pose):
    """실측 index1을 기준으로 원FK의 두 downstream hinge만 사용한다."""
    poses = fk(q)
    first_p, first_r = poses['LH:index1']
    distal_p, distal_r = poses['LH:index3']
    correction = Rotation.from_quat(first_pose[3:7]) * first_r.inv()
    return first_pose[:3] + correction.apply(distal_p - first_p), correction * distal_r


def to_guitar(points, p, r, guitar_pose):
    return Rotation.from_quat(guitar_pose[3:7]).inv().apply(p + r.apply(points) - guitar_pose[:3])


def self_check():
    """공통 강체변환은 소거되며, 양의 signedheight만 여유로 해석한다."""
    first = np.r_[np.array([.1, .2, .3]), Rotation.from_rotvec([.2, -.1, .3]).as_quat()]
    q = np.zeros(105)
    def fixture(_):
        return {'LH:index1': (np.zeros(3), Rotation.identity()),
                'LH:index3': (np.array([.02, 0., 0.]), Rotation.identity())}
    p, r = anchored_distal(fixture, q, first)
    np.testing.assert_allclose(p, first[:3] + Rotation.from_quat(first[3:]).apply([.02, 0, 0]))
    np.testing.assert_allclose((Rotation.from_quat(first[3:]).inv()*r).magnitude(), 0, atol=1e-14)
    transform = Rotation.from_rotvec([-.2, .4, .1])
    offset = np.array([.4, .3, .2])
    def transformed(_):
        return {n: (offset + transform.apply(x), transform*y) for n, (x, y) in fixture(q).items()}
    pp, rr = anchored_distal(transformed, q, first)
    np.testing.assert_allclose(pp, p, atol=1e-14)
    np.testing.assert_allclose((rr.inv()*r).magnitude(), 0, atol=1e-14)
    assert not bool((np.array([-.01, .006]) >= MARGIN_M).all())
    assert np.array_equal(q, np.zeros(105))
    return dict(anchor_rigid_frame_invariant=True, negative_height_not_clearance=True,
                input_q_unchanged=True)


def main():
    if (HERE/'results.json').exists():
        raise FileExistsError('원 결과를 덮어쓰지 않습니다: results.json')
    contract = load_prepared_reset_contract()
    names = contract['initial']['joint_names']
    q0 = np.array([r['pos'] for r in contract['state']['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=names, human_bodies=contract['initial']['human_body_names'],
                                q_ref=q0), contract['state'])
    hinges = [names.index(n) for n in ('LH:index2', 'LH:index3')]
    candidate = np.deg2rad(CANDIDATE_DEGREES)
    props = contract['initial']['native_PD_properties']
    assert np.all(candidate >= np.asarray(props['lower'])[hinges])
    assert np.all(candidate <= np.asarray(props['upper'])[hinges])
    paths = {Path(p) for p in contract['source_sha256']}
    paths.update([HERE/'PLAN.md', Path(__file__),
                  ROOT/'guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py'])
    base = HERE.parent/'index_release_clearance_v1/runs'
    for mode in ('reference', 'noisy_reference'):
        paths.update(base/mode/n for n in ('trace_env0_episode0.npz', 'trace_metadata.json',
                                           'goal_codec_env0.npz', 'release_clearance4.npz', 'surface_static.npz'))
    before = {str(p): digest(p) for p in sorted(paths)}
    result = dict(program_completed=False, CPU_only=True, native_runs=0, PPO_updates=0, fit_steps=0,
                  candidate_degrees=CANDIDATE_DEGREES.tolist(), design_height_margin_m=MARGIN_M,
                  minimum_target_time_from_original_N_s=float(np.max(abs(candidate-np.asarray(contract['target105'])[hinges]))/4.),
                  limitations='Conditional geometry with measured index1/guitar fixed. Not physical tracking, contact, pressure, or whole-skin certification.',
                  self_check=self_check(), modes={})
    plot = []
    for mode in ('reference', 'noisy_reference'):
        run = base/mode
        with np.load(run/'trace_env0_episode0.npz', allow_pickle=False) as z, \
             np.load(run/'goal_codec_env0.npz', allow_pickle=False) as codec, \
             np.load(run/'release_clearance4.npz', allow_pickle=False) as clearance, \
             np.load(run/'surface_static.npz', allow_pickle=False) as static:
            meta = json.loads((run/'trace_metadata.json').read_text())
            assert names == meta['joint_names']
            bodies = meta['body_names']
            first_id = bodies.index('human/LH:index1')
            distal_id = bodies.index('human/LH:index3')
            guitar_id = bodies.index('guitar/guitar_body') if 'guitar/guitar_body' in bodies else next(i for i, n in enumerate(bodies) if n.startswith('guitar/'))
            assert static['source_valid'].shape == (4, 128) and static['source_valid'].all()
            local, plane = static['local_points'].astype(float), static['plane'].astype(float)
            unit = plane[:3]/np.linalg.norm(plane[:3])
            intercept = plane[3]/np.linalg.norm(plane[:3])
            selected = np.flatnonzero((z['time_s'] > 3.2703) & (z['time_s'] <= 3.712))
            assert len(selected) == 26
            baseline_error, rotation_error, height_old, height_new, clocks = [], [], [], [], []
            for row in selected:
                clock = int(codec['clock'][row])
                matches = np.flatnonzero((clearance['env_id'] == 0) & (clearance['clock'] == clock))
                assert len(matches) == 1
                ci = matches[0]
                assert clearance['valid_snapshot'][ci] and not clearance['post_failure'][ci]
                np.testing.assert_array_equal(clearance['distal_pose'][ci], z['body_state'][row, distal_id, :7])
                q = z['q'][row].astype(float)
                first = z['body_state'][row, first_id, :7].astype(float)
                guitar = clearance['guitar_pose'][ci].astype(float)
                # 실측 기타 pose와 body_state의 첫 기타 body를 별도 확인한다.
                np.testing.assert_array_equal(guitar, z['body_state'][row, guitar_id, :7].astype(float))
                p, r = anchored_distal(fk, q, first)
                points = to_guitar(local, p, r, guitar)
                baseline_error.append(float(np.max(np.linalg.norm(points-clearance['points_G'][ci], axis=-1))))
                actual_r = Rotation.from_quat(z['body_state'][row, distal_id, 3:7])
                rotation_error.append(float((actual_r.inv()*r).magnitude()))
                np.testing.assert_allclose(points, clearance['points_G'][ci], atol=POSITION_TOLERANCE_M, rtol=0)
                original_q = q.copy()
                trial = q.copy()
                trial[hinges] = candidate
                p, r = anchored_distal(fk, trial, first)
                candidate_points = to_guitar(local, p, r, guitar)
                np.testing.assert_array_equal(q, original_q)
                height_old.append(float(np.min(clearance['points_G'][ci]@unit+intercept)))
                height_new.append(float(np.min(candidate_points@unit+intercept)))
                clocks.append(clock)
            assert max(baseline_error) <= POSITION_TOLERANCE_M
            assert max(rotation_error) <= ANGLE_TOLERANCE_RAD
            result['modes'][mode] = dict(samples=len(selected), clocks=clocks,
                anchored_baseline_max_point_error_m=max(baseline_error),
                anchored_baseline_max_rotation_error_rad=max(rotation_error),
                original_min_height_m=height_old, candidate_min_height_m=height_new,
                original_minimum_height_m=min(height_old), candidate_minimum_height_m=min(height_new),
                all_saved_env0_phase3_points_meet_design_margin=bool(min(height_new) >= MARGIN_M))
            plot.append((mode, np.asarray(clocks)/240, np.asarray(height_old)*1000, np.asarray(height_new)*1000))
    after = {str(p): digest(p) for p in sorted(paths)}
    assert before == after
    result.update(program_completed=True, input_sha256=before, inputs_unchanged=True)
    result['candidate_design_passed'] = all(v['all_saved_env0_phase3_points_meet_design_margin'] for v in result['modes'].values())
    (HERE/'results.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True, constrained_layout=True)
    for ax, (mode, t, old, new) in zip(axes, plot):
        ax.plot(t, old, label='Observed original N')
        ax.plot(t, new, label='Conditional PIP40 / DIP10')
        ax.axhline(5, color='gray', linestyle='--', label='Design request 5 mm')
        ax.set(title=mode, xlabel='Local time (s)', ylabel='Minimum signed height of 128 points (mm)')
        ax.grid(alpha=.2)
    axes[0].legend(fontsize=8)
    fig.suptitle('Measured index1/guitar held fixed; candidate is NOT native replay')
    fig.savefig(HERE/'candidate_clearance.png', dpi=150)
    print(json.dumps({k: result[k] for k in ('program_completed', 'candidate_design_passed', 'inputs_unchanged')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
