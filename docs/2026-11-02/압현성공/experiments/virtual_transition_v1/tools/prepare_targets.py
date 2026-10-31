"""중지 ABAB 무음 과제와 팔만 움직인 B의 CPU 기하 후보를 생성한다.

기존 실험 코드는 import하지 않는다. 새 번들과 출력은 덮어쓰지 않으며 CPU
패드 적격성은 native 접촉·하중·유지 성공과 구분한다.
"""
import argparse
import copy
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import wave

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[6]
BASE = Path(__file__).resolve().parents[1]
SONG = 'virtual_middle_s3_f6_f7_ABAB_v1'
sys.path.insert(0, str(ROOT))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def fingering():
    """source 저음E 기준 index3을 runtime 표준3번줄 index2로 변환하게 한다."""
    notes, presses, hand = [], [], []
    for i, fret in enumerate((6, 7, 6, 7)):
        start, end = 2.*i, 2.*i+1.5
        notes.append(dict(t_on=start, t_off=end, string=3, fret=fret,
                          midi=55+fret, finger=2, barre=False, grip=None))
        presses.append(dict(finger=2, string=3, fret=fret, barre=False,
                            t_press=start, t_release=end, strikes=[start]))
        hand.append(dict(t=start, P=fret-2+1, grip=None))
    return dict(purpose='synthetic_middle_two_fret_transition_diagnostic',
                convention='string 0 = low-E; no acoustic performance', notes=notes,
                presses=presses, hand=hand, stats=dict(dropped_invalid_fret=0),
                diagnostics=[], violations=[])


def build_bundle():
    from guitar_learning.tool import build_fret_training_data as fret
    from guitar_learning.tool.build_strike_training_data import build_strike_training_data
    from guitar_learning.tool.build_strike_plan import build_strike_plan
    from guitar_learning.tool.register_song_bundle import write_manifest, write_tablature_if_missing
    from guitar_learning.song.task import make_task, load_anchor_track
    bundle = ROOT/'data/song_bundles'/SONG
    bundle.mkdir(parents=True, exist_ok=False)
    for name in ('source', 'mapping', 'training'):
        (bundle/name).mkdir()
    audio = bundle/'source/audio.wav'
    with wave.open(str(audio), 'wb') as stream:
        stream.setparams((1, 2, 16000, 0, 'NONE', 'not compressed'))
        stream.writeframes(b'\0\0'*120000)
    mapping = bundle/'mapping/fingering.json'
    write(mapping, fingering())
    fret.main(['--fingering', str(mapping), '--audio', str(audio),
               '--out', str(bundle/'training/fret_training.json')])
    strike = bundle/'training/strike_training.json'
    document = build_strike_training_data(fingering(), source_path=mapping)
    write(strike, document)
    write(bundle/'training/strike_plan.json', build_strike_plan(document, source_path=strike))
    write_tablature_if_missing(bundle)
    functions = (fret.main, build_strike_training_data, build_strike_plan, write_manifest)
    sources = {str(Path(inspect.getsourcefile(f)).resolve()): digest(inspect.getsourcefile(f))
               for f in functions}
    sources[str(Path(__file__).resolve())] = digest(__file__)
    write_manifest(SONG, bundle, dict(generator_source_sha256=sources,
        mode='new synthetic ABAB; existing generators not imported', immutable_after_creation=True))
    task, anchors = make_task(bundle), load_anchor_track(bundle)
    assert [(t.string, t.fret, t.finger, t.onset_s, t.end_s) for t in task.targets] == [
        (2, f, 2, 3.+i*2, 4.5+i*2) for i, f in enumerate((6, 7, 6, 7))]
    assert task.episode_duration_s == 11.
    assert [anchors['anchors'][i*120] for i in range(4)] == [5., 6., 5., 6.]
    return bundle, task, anchors


def snapshot_for_q(contract, q, fk):
    """인간 DOF/body를 같은 source FK·0속도로 일치시키고 다른 actor는 보존한다."""
    state = copy.deepcopy(contract['state'])
    poses = fk(q)
    for row, value in zip(state['human_dof_states'], q):
        row.update(pos=float(value), vel=0.)
    for name, row in zip(contract['initial']['human_body_names'], state['human_body_states']):
        point, rotation = poses[name]
        row['pose'] = dict(p=dict(zip('xyz', map(float, point))),
                           r=dict(zip('xyzw', map(float, rotation.as_quat()))))
        row['vel'] = {key: dict.fromkeys('xyz', 0.) for key in ('linear', 'angular')}
    return state


def build_geometry(bundle, task, anchors):
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.gpu.contact import load_fingertip_pad
    from guitar_learning.tool.validation.press_acquisition import action_bounds, source_geometry
    from guitar_learning.core.geometry import frame, geometry_snapshot
    from guitar_learning.song.task import WristGuide
    out = BASE/'geometry'
    out.mkdir(exist_ok=False)
    catalog_path = ROOT/'guitar_learning/assets/natural_press_v3/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    A = next(row for row in catalog['goals'] if row['finger']=='middle')
    assert A['fret']==6 and A['string']==2 and A['native_verified']
    contract = load_gpu_prepared_reset_contract('left')
    initial = contract['initial']; names = initial['joint_names']
    qA = np.array(A['q105'])
    # full_fk는 주어진 표본으로 body 상대 영점도 보정한다. 검증 A의 q/state를
    # 함께 기준으로 삼아 v9의 다른 표본 보정과 섞지 않는다.
    contract = dict(contract, state=copy.deepcopy(A['state']))
    fk = full_fk(SimpleNamespace(names=names, human_bodies=initial['human_body_names'], q_ref=qA), contract['state'])
    active, lo, hi = action_bounds(contract)
    arm = np.array([i for i, name in enumerate(catalog['active_names']) if name.startswith('L_')])
    native = active[arm]; lower, upper = lo[arm], hi[arm]
    pad = load_fingertip_pad(); valid = pad['valid'][1]
    local = pad['points_local'][1][valid].astype(float)
    normals = pad['normals_local'][1][valid].astype(float)
    gp, gr = frame(A['state']['guitar_body_states'][0])
    starts, ends, lows, highs, plane, surface = source_geometry(contract, [dict(string=2, fret=7)])
    normal = plane[:3]/np.linalg.norm(plane[:3]); line = ends[2]-starts[2]
    center = starts[2]+((lows[0]+highs[0])/2-starts[2,1])/line[1]*line
    wristA, rotationA = fk(qA)['L_Wrist']
    selected = int(A['geometry']['selected_sample'])
    nominal_height = .0135

    def measure(q):
        p, rot = fk(q)['LH:middle3']
        points = gr.inv().apply(p+rot.apply(local)-gp)
        facing = -gr.inv().apply(rot.apply(normals))@normal
        return points, facing

    def residual(values):
        q = qA.copy(); q[native] = values
        points, facing = measure(q)
        _, wr = fk(q)['L_Wrist']
        return np.r_[1000*(points[selected]-center-nominal_height*normal),
                     100*(rotationA.inv()*wr).as_rotvec(),
                     10*max(.1-facing[selected], 0), .05*(values-qA[native])]

    fit = least_squares(residual, np.clip(qA[native], lower+1e-9, upper-1e-9),
        bounds=(lower, upper), max_nfev=250, ftol=1e-10, xtol=1e-10, gtol=1e-10)
    qB = qA.copy(); qB[native] = fit.x
    points, facing = measure(qB); height = points@normal+plane[3]
    delta = points-center; tangent = np.linalg.norm(delta-(delta@normal)[:,None]*normal, axis=1)
    cell = (points[:,1]>=lows[0]+.002)&(points[:,1]<=highs[0]-.002)
    eligible = cell&(tangent<=.005)&(height>=.010)&(height<=.014)&(facing>=.1)
    k = selected
    assert eligible[k], 'The original validated A pad sample must remain suitable'
    state = snapshot_for_q(contract, qB, fk)
    hold = np.array(A['hold_target105']); hold[native] = qB[native]
    unchanged = np.ones(105, dtype=bool); unchanged[native] = False
    assert np.array_equal(qB[unchanged], qA[unchanged])
    native_lo, native_hi = np.array(initial['native_PD_properties']['lower']), np.array(initial['native_PD_properties']['upper'])
    assert (qB[native]>=native_lo[native]).all() and (qB[native]<=native_hi[native]).all()
    # 검증된 A 원본의 고정 무릎축 미세 오차도 보존하며 팔 최적화와 구분한다.
    inherited = np.maximum(np.maximum(native_lo-qA, qA-native_hi), 0.)
    assert (np.maximum(np.maximum(native_lo-qB, qB-native_hi), 0.) <= inherited+1e-12).all()
    # 평면 교차만으로 오압현이라 부르지 않고 같은 점의 유한 셀·줄·법선을 본다.
    _, _, all_low, all_high, _, _ = source_geometry(contract,
        [dict(string=2, fret=f) for f in range(1,23)])
    other = {}
    for pose_label, trial in (('A',qA),('B',qB)):
        rows = {}; patches = {}
        for fi, name in enumerate(('index','middle','ring','pinky')):
            p, rot = fk(trial)['LH:'+name+'3']; mask=pad['valid'][fi]
            pts = gr.inv().apply(p+rot.apply(pad['points_local'][fi][mask])-gp)
            face = -gr.inv().apply(rot.apply(pad['normals_local'][fi][mask]))@normal
            h = pts@normal+plane[3]; projected=pts-h[:,None]*normal
            lines = ends-starts
            fraction=((projected[:,None,:]-starts)*lines).sum(-1)/(lines*lines).sum(-1)
            lateral=np.linalg.norm(projected[:,None,:]-starts-fraction[:,:,None]*lines,axis=-1)
            near=(lateral<=.003).any(axis=1)&(pts[:,1]>=all_low.min()+.002)&(pts[:,1]<=all_high.max()-.002)
            gate=near&(h>=-.001)&(h<=.003)&(face>=.1)
            rows[name]=dict(min_plane_height_m=float(h.min()),
                finite_neck_string_height_facing_sample_count=int(gate.sum()),
                minimum_lateral_to_any_string_m=float(lateral.min()))
            patches[name]=pts
        pair_gap={name:float(np.linalg.norm(patches['middle'][:,None,:]-pts[None,:,:],axis=-1).min())
                  for name,pts in patches.items() if name!='middle'}
        other[pose_label]=dict(distal_pads=rows,middle_to_other_valid_sample_min_distance_m=pair_gap,
            limitation='sampled source distal patches only; not full mesh/cooked pair contact or thumb interference')
    sample = dict(native=state, geometry=geometry_snapshot(state, initial['human_body_names'], initial['guitar_body_names']))
    sampleA = dict(native=A['state'], geometry=geometry_snapshot(A['state'], initial['human_body_names'], initial['guitar_body_names']))
    guide = WristGuide(bundle, sampleA, initial['human_body_names'], initial['guitar_body_names'])
    guide_samples = {str(t):guide.measure(sample,t) for t in (3.,4.5,4.75,5.,6.5,7.,9.,10.5,11.)}
    pins = dict(contract['source_sha256']); pins.update(pad['contract']['source_sha256']); pins.update(surface['source_sha256'])
    for func in (full_fk, source_geometry, load_fingertip_pad, build_geometry):
        source = Path(inspect.getsourcefile(func)).resolve(); pins[str(source)] = digest(source)
    pins[str(catalog_path)] = digest(catalog_path)
    pins.update({str(p):digest(p) for p in bundle.rglob('*') if p.is_file()})
    for p,h in pins.items():
        if digest(p)!=h: raise ValueError('Input changed: '+p)
    row = dict(schema='virtual_transition.cpu_candidate.v1', goal=dict(finger='middle',finger_id=2,string=2,physical_string=3,fret=7),
        native_verified=False, candidate_valid=bool(eligible.any()), q105=qB.tolist(), hold_target105=hold.tolist(),
        state=state, body_snapshot=state, A_q105=qA.tolist(), arm_native_indices=native.tolist(),
        finger_and_nonarm_q_unchanged=True,
        inherited_native_bound_deviation_rad={names[i]:float(inherited[i]) for i in np.flatnonzero(inherited)},
        center_G_m=center.tolist(), cell_inset_m=.002,
        nominal_height_m=nominal_height, selected_sample=k,
        selected_sample_rule='same valid source-local pad sample as native-validated A; no closest-point switching',
        geometry=dict(tangent_error_m=float(tangent[k]),height_m=float(height[k]),normal_cos=float(facing[k]),valid_sample_count=int(eligible.sum()),cell_low_m=float(lows[0]+.002),cell_high_m=float(highs[0]-.002)),
        same_point_pad_G_m=points[k].tolist(), pad_points_G_m=points.tolist(), normal_cos=facing.tolist(),
        wrist_rotation_change_deg=float(np.rad2deg((rotationA.inv()*fk(qB)['L_Wrist'][1]).magnitude())),
        wrist_position_change_world_m=(fk(qB)['L_Wrist'][0]-wristA).tolist(), other_distal_pad_clearance=other,
        wrist_guide_samples=guide_samples, source_sha256=pins, optimizer_nfev=fit.nfev,
        limitation='CPU source mesh/FK only; not collision, load, native reachability or successful pressing; thumb and inter-finger contact unverified')
    write(out/'candidate_B.json', row)
    write(out/'bundle_validation.json', dict(song=SONG, bundle=str(bundle), manifest_sha256=digest(bundle/'manifest.json'),
        generator_sha256=digest(__file__), schedule=task.provenance['song']['schedule'], episode_duration_s=task.episode_duration_s,
        anchor_samples=[anchors['anchors'][i*120] for i in range(4)], native_verified=False))
    return row


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    bundle, task, anchors = build_bundle()
    row = build_geometry(bundle, task, anchors)
    print(json.dumps(dict(bundle=str(bundle), candidate_valid=row['candidate_valid'], geometry=row['geometry']), indent=2))


if __name__=='__main__':
    main()
