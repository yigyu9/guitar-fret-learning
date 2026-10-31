"""구조 v2의 정렬 초기 자세 후보를 현재 소스 FK로 만든다.

CPU 기하 후보이며 충돌·힘·실제 초기 접촉 없음의 증명이 아니다. native 검증을
통과한 후보만 학습에 사용할 수 있다. 기타·의자·몸통 root를 옮기지 않는다.
"""
import argparse
import copy
import hashlib
import json
import inspect
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

DEFAULT_SONGS = ('virtual_finger_v9_index_s3_f4', 'virtual_finger_v9_middle_s3_f6',
                 'virtual_finger_v9_ring_s2_f7', 'virtual_finger_v9_pinky_s3_f9')
FINGERS = ('index', 'middle', 'ring', 'pinky')


@contextmanager
def nested_input_paths():
    """봉인 native 매핑을 우선하며 연구 사본·그 형제 출력 경로를 유지한다."""
    from guitar_learning.native import paths
    original = paths.resolve_input_path

    def resolve(path):
        lexical = paths._lexical(path)
        if str(lexical) in paths._mapping()[0]:
            return original(path)
        # 사본 안 입력과 연구 디렉토리의 출력은 HISTORICAL_ROOT로 재기반하지 않는다.
        roots = (paths.ROOT,) + tuple(paths.ROOT.parent/name for name in
            ('runs', 'smoke', 'rendering', 'validation', 'geometry'))
        if any(lexical == root or root in lexical.parents for root in roots):
            return lexical.resolve()
        return original(path)

    paths.resolve_input_path = resolve
    try:
        yield
    finally:
        paths.resolve_input_path = original


def snapshot_for_q(contract, q105, fk=None):
    """에피소드 경계용 DOF와 모든 인간 body pose를 같은 FK로 일치시킨다.

    기타·의자와 나머지 actor 상태는 원본 그대로다. 실제 물리 tick 중에는 호출하지
    않는다. 정지 초기 분포이므로 인간 DOF/body 속도는 모두 0으로 설정한다.
    """
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    q = np.asarray(q105, dtype=float)
    if q.shape != (105,) or not np.isfinite(q).all():
        raise ValueError('Finite q105 required')
    state = copy.deepcopy(contract['state'])
    if fk is None:
        initial = contract['initial']
        reference = np.array([row['pos'] for row in state['human_dof_states']])
        fk = full_fk(SimpleNamespace(names=initial['joint_names'],
            human_bodies=initial['human_body_names'], q_ref=reference), state)
    poses = fk(q)
    for row, value in zip(state['human_dof_states'], q):
        row['pos'], row['vel'] = float(value), 0.
    for name, row in zip(contract['initial']['human_body_names'], state['human_body_states']):
        point, rotation = poses[name]
        row['pose']['p'] = dict(zip('xyz', map(float, point)))
        row['pose']['r'] = dict(zip('xyzw', map(float, rotation.as_quat())))
        for kind in ('linear', 'angular'):
            row['vel'][kind] = dict.fromkeys('xyz', 0.)
    return state


def alignment_metrics(points, facing, center, normal, nominal_height=.010):
    """유효 안쪽 패드 각각의 셀 중앙 접선 거리·높이·법선을 함께 판정한다."""
    delta = np.asarray(points)-center
    height = delta@normal
    tangent = np.linalg.norm(delta-height[:, None]*normal, axis=1)
    valid = (tangent <= .005) & (height >= .005) & (height <= .015) & (facing >= .1)
    nearest = int(np.argmin(np.linalg.norm(delta-nominal_height*normal, axis=1)))
    return dict(candidate_valid=bool(valid.any()), selected_sample=nearest,
        tangent_error_m=float(tangent[nearest]), height_m=float(height[nearest]),
        normal_cos=float(facing[nearest]), valid_sample_count=int(valid.sum()))


def perturbation_candidates(fk, q, arm_indices, lower, upper, max_nfev=80):
    """팔 관절만으로 손목 ±10mm/±5도 범위의 도달 가능한 자세를 구성한다.

    8개 위치 모서리와 6개 방향 끝점을 시도한다. 실제 달성 오차와 범위 적격성을
    모두 저장하며 단순히 요청값을 달성한 값으로 기록하지 않는다.
    """
    from itertools import product
    base_p, base_r = fk(q)['L_Wrist']
    requests = [(np.asarray(v)*.010, np.zeros(3)) for v in product((-1., 1.), repeat=3)]
    for axis in range(3):
        for sign in (-1, 1):
            angle = np.zeros(3); angle[axis] = sign*np.deg2rad(5)
            requests.append((np.zeros(3), angle))
    rows = []
    for displacement, angle in requests:
        wanted_r = base_r*Rotation.from_rotvec(angle)

        def residual(values):
            trial = q.copy(); trial[arm_indices] = values
            point, rotation = fk(trial)['L_Wrist']
            return np.r_[1000*(point-base_p-displacement),
                100*(wanted_r.inv()*rotation).as_rotvec(), .03*(values-q[arm_indices])]

        fit = least_squares(residual, np.clip(q[arm_indices], lower+1e-9, upper-1e-9),
            bounds=(lower, upper), max_nfev=max_nfev)
        trial = q.copy(); trial[arm_indices] = fit.x
        point, rotation = fk(trial)['L_Wrist']
        dp, dr = point-base_p, (base_r.inv()*rotation).as_rotvec()
        in_range = bool((np.abs(dp) <= .010001).all() and
                        (np.abs(dr) <= np.deg2rad(5)+1e-6).all())
        accurate = np.linalg.norm(dp-displacement) <= .002 and np.linalg.norm(dr-angle) <= np.deg2rad(1)
        rows.append(dict(q105=trial.tolist(), requested_position_delta_world_m=displacement.tolist(),
            requested_rotation_delta_local_rad=angle.tolist(), actual_position_delta_world_m=dp.tolist(),
            actual_rotation_delta_local_rad=dr.tolist(), range_valid=in_range,
            request_reached=bool(accurate), candidate_valid=bool(in_range and accurate),
            native_verified=False, optimizer_nfev=int(fit.nfev)))
    return rows


def build_catalog(out, songs=DEFAULT_SONGS, max_nfev=200, perturb=True,
                  nominal_height=.010, height_overrides=None,
                  clearance_overrides=None, arm_only=False):
    """정렬 후보와 B 오차 후보를 만들고 원본 source SHA를 봉인한다."""
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.native import paths
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.contact import load_fingertip_pad
    from guitar_learning.song.task import make_task
    from guitar_learning.tool.validation.press_acquisition import action_bounds, source_geometry
    height_overrides = dict(height_overrides or {})
    clearance_overrides = dict(clearance_overrides or {})
    if any(not 0. <= height <= .030 for height in clearance_overrides.values()):
        raise ValueError('Non-target pad clearance must be within 0..30mm')
    if not .005 <= nominal_height <= .015 or any(
            not .005 <= height <= .015 for height in height_overrides.values()):
        raise ValueError('Nominal pad height must remain in approved 5..15mm band')
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    contract = load_gpu_prepared_reset_contract('left')
    names = contract['initial']['joint_names']
    q0 = np.array([row['pos'] for row in contract['state']['human_dof_states']])
    reference = np.asarray(contract['target105'])
    fk = full_fk(SimpleNamespace(names=names, human_bodies=contract['initial']['human_body_names'],
        q_ref=q0), contract['state'])
    active, lower, upper = action_bounds(contract)
    pad = load_fingertip_pad()
    gp = contract['state']['guitar_body_states'][0]['pose']
    guitar_p = np.array([gp['p'][axis] for axis in 'xyz'])
    guitar_r = Rotation.from_quat([gp['r'][axis] for axis in 'xyzw'])
    pins = dict(contract['source_sha256'])
    pins.update(pad['contract']['source_sha256'])
    for function in (build_catalog, full_fk, action_bounds, source_geometry, make_task,
                     load_fingertip_pad, load_gpu_prepared_reset_contract):
        source = Path(inspect.getsourcefile(function)).resolve()
        pins[str(source)] = hashlib.sha256(source.read_bytes()).hexdigest()
    rows = []
    for song in songs:
        # 실제 입력 bundle을 읽는다. 임의 가상 물리 목표나 teacher 궤적을 주입하지 않는다.
        bundle = Path(song) if Path(song).is_dir() else paths.ROOT/'data/song_bundles'/song
        task = make_task(bundle)
        requested_height = height_overrides.get(bundle.name, nominal_height)
        requested_clearance = clearance_overrides.get(bundle.name, 0.)
        if len(task.targets) != 1:
            raise ValueError('Exactly one virtual note required')
        target = task.targets[0]
        goal = dict(string=target.string, fret=target.fret)
        starts, ends, low, high, plane, surface = source_geometry(contract, [goal])
        pins.update(surface['source_sha256'])
        pins.update({entry['path']: entry['sha256'] for entry in task.provenance['provenance']})
        normal = plane[:3]/np.linalg.norm(plane[:3])
        start, line = starts[target.string], ends[target.string]-starts[target.string]
        center = start+((low[0]+high[0])/2-start[1])/line[1]*line
        finger = FINGERS[target.finger-1]
        if requested_clearance and finger == 'pinky':
            raise ValueError('Clearance override is for a non-target pinky only')
        other_names = [name for name in FINGERS if name != finger]
        clearance_floors = np.array([requested_clearance if name == 'pinky' else .005
                                    for name in other_names])
        valid = pad['valid'][target.finger-1]
        local = pad['points_local'][target.finger-1][valid].astype(float)
        normals = pad['normals_local'][target.finger-1][valid].astype(float)
        arm_channels = [i for i, name in enumerate(ACTIVE_NAMES) if name.startswith('L_')]
        finger_channels = [i for i, name in enumerate(ACTIVE_NAMES) if name.startswith('LH:'+finger)]
        attempts = []

        def measure(trial):
            point, rotation = fk(trial)['LH:'+finger+'3']
            points = guitar_r.inv().apply(point+rotation.apply(local)-guitar_p)
            facing = -guitar_r.inv().apply(rotation.apply(normals))@normal
            return points, facing

        def other_pad_heights(trial):
            poses = fk(trial)
            heights = []
            for other, other_name in enumerate(FINGERS):
                if other == target.finger-1:
                    continue
                p, r = poses['LH:'+other_name+'3']
                points = guitar_r.inv().apply(p+r.apply(
                    pad['points_local'][other][pad['valid'][other]])-guitar_p)
                heights.append(float((points@normal+plane[3]).min()))
            return np.array(heights)

        channel_groups = (arm_channels,) if arm_only else (arm_channels, arm_channels+finger_channels)
        for channels in channel_groups:
            native = active[channels]
            lo, hi = lower[channels], upper[channels]

            def evaluate(values):
                trial = q0.copy(); trial[native] = values
                points, facing = measure(trial)
                selected = int(np.argmin(np.linalg.norm(points-center-requested_height*normal, axis=1)))
                return trial, points, facing, selected

            def residual(values):
                trial, points, facing, selected = evaluate(values)
                clearance = (1000*np.maximum(clearance_floors-other_pad_heights(trial), 0.)
                             if requested_clearance else np.empty(0))
                return np.r_[1000*(points[selected]-center-requested_height*normal),
                    10*max(.3-facing[selected], 0), .05*(values-q0[native]), clearance]

            seed = np.clip(q0[native], lo+1e-9, hi-1e-9)
            guesses = [seed, .75*seed+.25*(lo+hi)/2]
            fits = [least_squares(residual, guess, bounds=(lo, hi), max_nfev=max_nfev,
                ftol=1e-9, xtol=1e-9, gtol=1e-9) for guess in guesses]
            fit = min(fits, key=lambda value: np.linalg.norm(residual(value.x)))
            q, points, facing, _ = evaluate(fit.x)
            metrics = alignment_metrics(points, facing, center, normal, requested_height)
            if requested_clearance:
                other_heights = other_pad_heights(q)
                clearance_valid = bool((other_heights >= clearance_floors-1e-6).all())
                metrics.update(non_target_min_heights_m=other_heights.tolist(),
                    requested_pinky_min_height_m=requested_clearance,
                    non_target_fingers=other_names,
                    requested_non_target_min_heights_m=clearance_floors.tolist(),
                    clearance_valid=clearance_valid)
                metrics['candidate_valid'] = metrics['candidate_valid'] and clearance_valid
            attempts.append(dict(scope='arm_only' if channels == arm_channels else 'arm_and_target_finger',
                **metrics, optimizer_nfev=int(fit.nfev), optimizer_converged=bool(fit.success)))
            if metrics['candidate_valid']:
                break
        hold = reference.copy(); hold[active[channels]] = q[active[channels]]
        body_snapshot = snapshot_for_q(contract, q, fk)
        variations = perturbation_candidates(fk, q, active[arm_channels], lower[arm_channels],
            upper[arm_channels]) if perturb and metrics['candidate_valid'] else []
        finger_native = active[finger_channels]
        row = dict(song=bundle.name, bundle=str(bundle.resolve()), finger=finger,
            finger_id=target.finger, string=target.string, physical_string=target.string+1,
            fret=target.fret, q105=q.tolist(), hold_target105=hold.tolist(),
            body_snapshot=body_snapshot, state=body_snapshot, geometry=metrics,
            candidate_valid=metrics['candidate_valid'], native_verified=False,
            search_attempts=attempts, target_finger_change_rad=(q[finger_native]-q0[finger_native]).tolist(),
            center_G_m=center.tolist(), normal_G=normal.tolist(),
            nominal_height_m=requested_height,
            pad_points_G_m=points.tolist(), normal_cos=facing.tolist(), perturbations=variations)
        rows.append(row)
        print(bundle.name, attempts[-1]['scope'], metrics, flush=True)
    changed = [path for path, sha in pins.items() if hashlib.sha256(Path(path).read_bytes()).hexdigest() != sha]
    if changed:
        raise RuntimeError('Geometry input changed: '+str(changed))
    catalog = dict(schema='guitar_learning.structured_press_geometry.v1', goals=rows,
        reference105=reference.tolist(), initial_q105=q0.tolist(), joint_names=names,
        active_names=list(ACTIVE_NAMES), action_indices=active.tolist(),
        action_lower=lower.tolist(), action_upper=upper.tolist(), source_sha256=pins,
        initial_pose=contract['initial_pose'], native_verified=False,
        limitation='CPU source FK candidates only; native collision/contact/load verification required before training')
    (out/'catalog.json').write_text(json.dumps(catalog, indent=2, allow_nan=False)+'\n')
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--songs', nargs='+', default=DEFAULT_SONGS)
    parser.add_argument('--max-nfev', type=int, default=200)
    parser.add_argument('--no-perturb', action='store_true')
    parser.add_argument('--nominal-height-m', type=float, default=.010)
    parser.add_argument('--height-override', action='append', default=[], metavar='SONG=METERS')
    parser.add_argument('--clearance-override', action='append', default=[], metavar='SONG=METERS',
        help='비목표 소지 패드 최소 높이. 나머지 비목표 패드는 5mm 이상 유지한다.')
    parser.add_argument('--arm-only', action='store_true')
    args = parser.parse_args()
    with nested_input_paths():
        overrides = {}
        for item in args.height_override:
            song, height = item.rsplit('=', 1)
            overrides[song] = float(height)
        clearances = {}
        for item in args.clearance_override:
            song, height = item.rsplit('=', 1)
            clearances[song] = float(height)
        build_catalog(args.out, args.songs, args.max_nfev, not args.no_perturb,
                      args.nominal_height_m, overrides, clearances, args.arm_only)


if __name__ == '__main__':
    main()
