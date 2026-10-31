"""봉인 runtime을 읽는 CPU finger4 FK 진단. 실제 접촉/충돌/힘 성공이 아니다."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

STUDY = Path(__file__).resolve().parents[3]
RUNTIME = STUDY/'runtime'
sys.path.insert(0, str(RUNTIME))
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def verify():
    seal = json.loads((STUDY/'source_seal.json').read_text())
    changed = [name for name, sha in seal['files'].items()
               if digest(RUNTIME/name) != sha]
    if changed:
        raise ValueError('Sealed runtime changed: '+str(changed))
    return dict(files=len(seal['files']), changed=changed,
                seal_sha256=digest(STUDY/'source_seal.json'))


def write(path, value):
    if path.exists():
        raise FileExistsError(str(path))
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def solve(out, max_nfev, starts, seconds):
    import torch
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.gpu.contact import load_fingertip_pad, pad_target_geometry
    from guitar_learning.tool.validation.press_acquisition import source_geometry
    before = verify()
    catalog_path = RUNTIME/'guitar_learning/assets/structured_press_v2/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    contract = load_gpu_prepared_reset_contract('left')
    names = contract['initial']['joint_names']
    initial_q = np.array([r['pos'] for r in contract['state']['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=names, human_bodies=contract['initial']['human_body_names'],
        q_ref=initial_q), contract['state'])
    active = np.array(catalog['action_indices'])
    lower, upper = np.array(catalog['action_lower']), np.array(catalog['action_upper'])
    pad = load_fingertip_pad()
    gp = contract['state']['guitar_body_states'][0]['pose']
    guitar_p = np.array([gp['p'][axis] for axis in 'xyz'])
    guitar_r = Rotation.from_quat([gp['r'][axis] for axis in 'xyzw'])
    rows = []
    for goal in catalog['goals']:
        if goal['finger'] == 'index':
            continue
        start_time = time.monotonic()
        finger, finger_id = goal['finger'], goal['finger_id']
        q0, hold = np.array(goal['q105']), np.array(goal['hold_target105'])
        channels = np.array([i for i, name in enumerate(catalog['active_names'])
            if name.startswith('LH:'+finger)])
        indices = active[channels]
        lo, hi = lower[channels], upper[channels]
        qref = q0[indices]
        local = pad['points_local'][finger_id-1][pad['valid'][finger_id-1]].astype(float)
        normals = pad['normals_local'][finger_id-1][pad['valid'][finger_id-1]].astype(float)
        ss, ee, low, high, plane, _ = source_geometry(contract, [goal])
        normal = plane[:3]
        line_start = ss[goal['string']]
        line = ee[goal['string']]-line_start
        a, b = (low[0]+.002-line_start[1])/line[1], (high[0]-.002-line_start[1])/line[1]
        aa, bb = min(a, b), max(a, b)

        def evaluate(values):
            trial = q0.copy(); trial[indices] = values
            point, rotation = fk(trial)['LH:'+finger+'3']
            points = guitar_r.inv().apply(point+rotation.apply(local)-guitar_p)
            facing = -guitar_r.inv().apply(rotation.apply(normals))@normal
            heights = points@normal+plane[3]
            projected = points-heights[:, None]*normal
            fraction = np.clip((projected-line_start)@line/(line@line), aa, bb)
            nearest = line_start+fraction[:, None]*line
            tangent = projected-nearest
            objective = np.linalg.norm(tangent+(heights-.0005)[:, None]*normal, axis=1)
            chosen = int(objective.argmin())
            valid = ((np.linalg.norm(tangent, axis=1) <= .003) &
                (points[:, 1] >= low[0]+.002) & (points[:, 1] <= high[0]-.002) &
                (heights >= 0.) & (heights <= .001) & (facing >= .1))
            return trial, points, facing, heights, tangent, chosen, valid

        def residual(values):
            _, points, facing, heights, tangent, chosen, _ = evaluate(values)
            # 작은 변화·극단 회피는 후보 선택용 약한 진단 선호이며 학습 보상이 아니다.
            edge = np.maximum(.087266-(values-lo), 0.)+np.maximum(.087266-(hi-values), 0.)
            return np.r_[1000*tangent[chosen], 1000*(heights[chosen]-.0005),
                10*max(.3-facing[chosen], 0), .03*(values-qref), .01*edge]

        rng = np.random.RandomState(73+finger_id)
        seeds = [qref, qref+np.array([.1, 0., .2, .1]),
                 qref+np.array([-.1, -.15, .1, .1]), qref+np.array([.1, .15, -.1, .2])]
        seeds += [rng.uniform(lo, hi) for _ in range(max(starts-4, 0))]
        attempts = []
        for ordinal, seed in enumerate(seeds[:starts]):
            if time.monotonic()-start_time > seconds:
                break
            fit = least_squares(residual, np.clip(seed, lo+1e-8, hi-1e-8), bounds=(lo, hi),
                max_nfev=max_nfev, ftol=1e-8, xtol=1e-8, gtol=1e-8)
            trial, points, facing, heights, tangent, nearest, valid = evaluate(fit.x)
            chosen = int(np.flatnonzero(valid)[np.argmin(np.linalg.norm(tangent[valid], axis=1))]) if valid.any() else nearest
            values = fit.x
            gaps = np.minimum(values-lo, hi-values)
            attempts.append(dict(seed=ordinal, q105=trial.tolist(), finger_angles_rad=values.tolist(),
                native_range_valid=bool(((values >= lo)&(values <= hi)).all()),
                native_5deg_edge_count=int((gaps < np.deg2rad(5)).sum()),
                change_l2_rad=float(np.linalg.norm(values-qref)),
                change_deg=np.rad2deg(values-qref).tolist(),
                geometric_contact=bool(valid.any()), selected_sample=chosen,
                signed_height_m=float(heights[chosen]), facing_cos=float(facing[chosen]),
                tangent_error_m=float(np.linalg.norm(tangent[chosen])),
                valid_samples=int(valid.sum()), selected_patch_point_G_m=points[chosen].tolist(),
                optimizer_success=bool(fit.success), nfev=int(fit.nfev)))
        best = min(attempts, key=lambda a: (not a['geometric_contact'],
            a['native_5deg_edge_count'], a['change_l2_rad'], a['tangent_error_m']))
        # 공식 표면 판정 함수를 CPU로 다시 실행한다. loaded=False를 유지해 하중을 꾸미지 않는다.
        poses = fk(np.array(best['q105']))
        all_points, all_normals = [], []
        for i, other in enumerate(('index','middle','ring','pinky')):
            p, r = poses['LH:'+other+'3']
            all_points.append(guitar_r.inv().apply(p+r.apply(pad['points_local'][i])-guitar_p))
            all_normals.append(guitar_r.inv().apply(r.apply(pad['normals_local'][i])))
        point_tensor = torch.tensor(np.array(all_points)[None], dtype=torch.float64)
        official = pad_target_geometry(point_tensor, torch.tensor(np.array(all_normals)[None]),
            torch.zeros_like(point_tensor), torch.tensor(pad['valid']),
            torch.tensor(ss[None]), torch.tensor(ee[None]), torch.tensor(low[None]),
            torch.tensor(high[None]), torch.tensor([goal['string']]), torch.tensor([finger_id]),
            torch.zeros((1,4), dtype=torch.bool), torch.tensor(plane))
        row = dict(song=goal['song'], finger=finger, source_catalog_sha256=digest(catalog_path),
            fixed='catalog q105 arm/lower/root/guitar; only assigned four finger q changed',
            finger_joint_names=[names[i] for i in indices], finger_native_indices=indices.tolist(),
            bounds_rad=dict(lower=lo.tolist(), upper=hi.tolist()), initial_angles_rad=qref.tolist(),
            arm_q_vs_hold_max_abs_rad=float(np.max(np.abs(q0[active[:12]]-hold[active[:12]]))),
            all_dof_q_vs_hold_max_abs_rad=float(np.max(np.abs(q0-hold))),
            attempts=attempts, best=best, initial_q105=q0.tolist(),
            official_cpu_facing_geometry=bool(official['facing_geometry'][0,0]),
            official_cpu_positive_with_unavailable_load=bool(official['positive'][0,0]),
            wall_s=time.monotonic()-start_time,
            limitation='CPU source FK only, fixed guitar and arm; no collision, net force, clean, acoustic or learned success proof')
        write(out/(finger+'.json'), row)
        rows.append(row)
        print(finger,'geometric',best['geometric_contact'],'official',row['official_cpu_facing_geometry'],
              'seed_valid',sum(a['geometric_contact'] for a in attempts),'/',len(attempts),
              'angles_deg',np.rad2deg(best['finger_angles_rad']).tolist(),
              'change_deg',best['change_deg'],'seconds',row['wall_s'],flush=True)
    after = verify()
    result = dict(before=before, after=after, runtime_unchanged=before==after,
        script_sha256=digest(__file__), catalog_sha256=digest(catalog_path),
        settings=dict(starts=starts,max_nfev=max_nfev,max_seconds_per_goal=seconds,
            threads=1,gpu=False,desired_signed_height_m=.0005,contact_height_band_m=[0.,.001]),
        goals=[dict(song=r['song'], finger=r['finger'], best=r['best'], wall_s=r['wall_s'],
            official_cpu_facing_geometry=r['official_cpu_facing_geometry']) for r in rows])
    write(out/'summary.json',result)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--starts',type=int,default=12)
    parser.add_argument('--max-nfev',type=int,default=100)
    parser.add_argument('--seconds',type=float,default=150)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    with nested_input_paths():
        solve(args.out,args.max_nfev,args.starts,args.seconds)
