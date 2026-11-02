"""동일 중지의 프렛 전환 참조 목표각을 CPU 기하로 탐색한다.

이 경로는 정책도 물리적 성공 증명도 아니다. 실제 reset은 첫 상태에만 적용하고,
이후 q105는 직접 위치 제어기로 보내는 요청각이다. 팔12·중지4만 변경한다.
"""
import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
from scipy.optimize import least_squares

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def quintic(u):
    u = np.clip(u, 0., 1.)
    return u*u*u*(10.+u*(-15.+6.*u))


SETTLE_S = .30


def keyframes(candidates, gap, hold=1.5):
    """A3~4.5초, B5.25~6.75초를 실제 물리 시계에서 유지한다."""
    if gap != .75 or hold != 1.5:
        raise ValueError('이번 진단은 휴지 .75초·유지1.5초 고정')
    q = {k: np.asarray(v['q105']) for k, v in candidates.items()}
    initial = np.asarray(json.loads((BASE/'geometry/initial_catalog.json').read_text())['goals'][0]['hold_target105'])
    move = gap-SETTLE_S
    return [(0., 'initial', initial), (.5, 'initial', initial),
            (2.8, 'A_press', q['A_press']), (3., 'A_press', q['A_press']),
            (4.5, 'A_press', q['A_press']),
            (4.5+.25*move, 'A_hover', q['A_hover']),
            (4.5+.75*move, 'B_hover', q['B_hover']),
            (4.5+move, 'B_press', q['B_press']),
            (5.25, 'B_press', q['B_press']), (6.75, 'B_press', q['B_press']),
            (7.25, 'B_press', q['B_press'])]


def trajectory(candidates, gap, hz=60):
    frames = keyframes(candidates, gap)
    ts = np.arange(round(frames[-1][0]*hz)+1)/float(hz)
    values = []
    for t in ts:
        i = min(np.searchsorted([v[0] for v in frames], t, side='right')-1, len(frames)-2)
        a, b = frames[i], frames[i+1]
        u = quintic((t-a[0])/(b[0]-a[0]))
        values.append(a[2]+u*(b[2]-a[2]))
    return ts, np.asarray(values), [(t, name) for t, name, _ in frames]


def search(out, budget=120):
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.gpu.contact import load_fingertip_pad
    from guitar_learning.tool.validation.press_acquisition import action_bounds, source_geometry
    from guitar_learning.core.geometry import frame
    from guitar_learning.core.control import ACTIVE_NAMES

    out.mkdir(parents=True, exist_ok=False)
    catalog_path = ROOT/'guitar_learning/assets/natural_press_v3/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    original = next(r for r in catalog['goals'] if r['finger']=='middle')
    contract = load_gpu_prepared_reset_contract('left')
    initial = contract['initial']; names = initial['joint_names']
    q0 = np.array(original['q105']); state = original['state']
    fk = full_fk(SimpleNamespace(names=names, human_bodies=initial['human_body_names'], q_ref=q0), state)
    indices, lower, upper = action_bounds(contract)
    channels = [i for i, name in enumerate(ACTIVE_NAMES) if name.startswith(('L_', 'LH:middle'))]
    native = indices[channels]; lo, hi = lower[channels], upper[channels]
    pad = load_fingertip_pad(); valid = pad['valid'][1]
    local = pad['points_local'][1][valid].astype(float)
    normals = pad['normals_local'][1][valid].astype(float)
    gp, gr = frame(state['guitar_body_states'][0])
    starts, ends, lows, highs, plane, surface = source_geometry(contract, [dict(string=2, fret=f) for f in range(1,23)])
    normal = plane[:3]/np.linalg.norm(plane[:3]); d = plane[3]/np.linalg.norm(plane[:3])
    start = starts[2]; line = ends[2]-start
    seed = np.clip(q0[native], lo+1e-8, hi-1e-8)

    def measure(q):
        pos, rot = fk(q)['LH:middle3']
        points = gr.inv().apply(pos+rot.apply(local)-gp)
        facing = -gr.inv().apply(rot.apply(normals))@normal
        height = points@normal+d
        projected = points-height[:,None]*normal
        fraction = ((projected-start)*line).sum(-1)/(line@line)
        lateral = np.linalg.norm(projected-start-fraction[:,None]*line, axis=-1)
        cells = (points[:,1,None]>lows[None]+.002)&(points[:,1,None]<highs[None]-.002)
        near = (lateral<=.003)&(height>=-.001)&(height<=.003)&(facing>=.1)
        candidate = (near[:,None]&cells).any(0)
        return points, facing, height, lateral, cells, candidate

    def non_target_height(q):
        heights=[]
        for fi,name in ((0,'index'),(2,'ring'),(3,'pinky')):
            p,r=fk(q)['LH:'+name+'3']
            pts=gr.inv().apply(p+r.apply(pad['points_local'][fi][pad['valid'][fi]])-gp)
            heights.extend((pts@normal+d).tolist())
        return np.array(heights)

    candidates = {}
    for label, fret in (('A',6), ('B',8)):
        y = (lows[fret-1]+highs[fret-1])/2
        center = start+(y-start[1])/line[1]*line
        for role, target_height in (('press', -.0005), ('hover', .010)):
            desired = center+target_height*normal
            trials = []
            # 같은 표본을 fit 내내 고정한다. 서로 다른 표본의 축별 최솟값은 쓰지 않는다.
            choices = sorted(set((int(original['geometry']['selected_sample']),
                                  int(np.argmin(local[:,1])), int(np.argmax(local[:,1])))))
            for sample in choices:
                def residual(x):
                    q = q0.copy(); q[native] = x
                    pts, facing, height, _, _, _ = measure(q)
                    # 목표 셀 밖 패드가 저면에 눕는 것을 억제한다. 이는 기하 탐색
                    # 목적일 뿐 실제 contact/하중을 대체하지 않는다.
                    outside = np.maximum(lows[fret-1]+.002-pts[:,1], 0.)+np.maximum(pts[:,1]-highs[fret-1]+.002, 0.)
                    outside_weight = np.clip(outside/.002, 0., 1.)
                    return np.r_[1000*(pts[sample]-desired),
                                 30*max(.3-facing[sample], 0.),
                                 500*outside_weight*np.maximum(.004-height, 0.),
                                 80*np.maximum(-.001-height, 0.),
                                 1000*np.maximum(.006-non_target_height(q),0.),
                                 .04*(x-seed)]
                fit = least_squares(residual, seed, bounds=(lo, hi), max_nfev=budget,
                                    ftol=1e-8, xtol=1e-8, gtol=1e-8)
                q = q0.copy(); q[native] = fit.x
                pts, facing, height, lateral, cells, flags = measure(q)
                same = (cells[:,fret-1]&(lateral<=.003)&(height>=-.001)&(height<=.003)&(facing>=.1))
                other = flags.copy(); other[fret-1]=False
                other_heights=non_target_height(q)
                is_ok = (bool(same.any() and not other.any()) if role=='press' else bool(height.min()>.004)) and bool(other_heights.min()>=.005)
                score = (not is_ok, np.linalg.norm(residual(fit.x)))
                trials.append((score, q, fit, sample, pts, facing, height, flags, is_ok))
            _, q, fit, sample, pts, facing, height, flags, is_ok = min(trials, key=lambda v:v[0])
            hold = np.array(original['hold_target105']); hold[native]=q[native]
            row = dict(q105=q.tolist(), hold_target105=hold.tolist(), native_verified=False,
                cpu_candidate_valid=is_ok, fret=fret, string=2, finger=2,
                requested_pad_height_m=target_height, sample=sample,
                sample_height_m=float(height[sample]), sample_normal_cos=float(facing[sample]),
                sample_position_G_m=pts[sample].tolist(), minimum_pad_height_m=float(height.min()),
                minimum_other_distal_pad_height_m=float(non_target_height(q).min()),
                candidate_frets_geometry_only=(np.flatnonzero(flags)+1).tolist(),
                optimizer_nfev=int(fit.nfev), optimizer_success=bool(fit.success))
            candidates[label+'_'+role]=row
            print(label, role, row['cpu_candidate_valid'], row['candidate_frets_geometry_only'], flush=True)
    # 일관된 몸체 상태는 오직 최초 reset용으로만 저장한다.
    q = np.array(candidates['A_press']['q105']); reset_state=copy.deepcopy(state)
    poses=fk(q)
    for dof,value in zip(reset_state['human_dof_states'],q):
        dof.update(pos=float(value),vel=0.)
    for name,body in zip(initial['human_body_names'],reset_state['human_body_states']):
        p,r=poses[name]
        body['pose']=dict(p=dict(zip('xyz',map(float,p))),r=dict(zip('xyzw',map(float,r.as_quat()))))
        body['vel']={k:dict.fromkeys('xyz',0.) for k in ('linear','angular')}
    pins=dict(contract['source_sha256']); pins.update(pad['contract']['source_sha256']); pins.update(surface['source_sha256'])
    for func in (full_fk, source_geometry, search):
        path=Path(inspect.getsourcefile(func)).resolve(); pins[str(path)]=sha(path)
    pins[str(catalog_path)]=sha(catalog_path)
    result=dict(schema='middle_f6_f8.reference_motion.v1', candidates=candidates, initial_state=reset_state,
        initial_q105=q.tolist(), initial_hold_target105=candidates['A_press']['hold_target105'],
        native_indices=native.tolist(), active_channels=channels, action_native_indices=indices.tolist(),
        action_lower=lower.tolist(), action_upper=upper.tolist(), reference105=np.asarray(contract['target105']).tolist(),
        source_sha256=pins, candidate_rule='source valid distal pad same point cell/string/height/facing; no native load',
        native_verified=False, limitation='Finite local source-FK candidates only. Native replay required. No policy training or impossibility proof.',
        search_budget_per_fit=budget, seeds_per_endpoint=3)
    write(out/'reference_candidates.json',result)
    for gap in (.75,):
        times, qs, frames=trajectory(candidates,gap)
        raw_frames=keyframes(candidates,gap)
        continuous_rate=np.max([1.875*np.abs(b[2][native]-a[2][native])/(b[0]-a[0])
            for a,b in zip(raw_frames,raw_frames[1:])],axis=0)
        rate=np.max(np.abs(np.diff(qs[:,native],axis=0))*60,axis=0)
        rates=np.array([4. if names[i].startswith('LH:') else 3. for i in native])
        write(out/('trajectory_gap_'+str(gap)+'.json'),dict(schema=result['schema'],gap_s=gap,hz=60,settle_s=SETTLE_S,
            candidate_sha256=sha(out/'reference_candidates.json'), keyframes=frames,
            times_s=times.tolist(), requested_q105=qs.tolist(),
            maximum_requested_rate_rad_s=rate.tolist(), control_rate_rad_s=rates.tolist(),
            continuous_quintic_peak_rate_rad_s=continuous_rate.tolist(),
            requested_rate_feasible=bool((rate<=rates+1e-8).all() and (continuous_rate<=rates+1e-8).all()),
            instruction='q105 are controller requests only; never overwrite native state per frame'))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--out',type=Path,default=BASE/'geometry/reference_v1')
    p.add_argument('--budget',type=int,default=120)
    args=p.parse_args(); search(args.out,args.budget)


if __name__=='__main__':
    main()
