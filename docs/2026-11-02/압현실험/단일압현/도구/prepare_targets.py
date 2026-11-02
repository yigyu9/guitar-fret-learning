"""18개 단음 번들과 현재 FK 정렬 후보를 만든다. native 성공은 상속하지 않는다.

합성 음은 정책 시각 3~4.5초, 에피소드 5초다. CPU 후보는 정렬 지원의
가능성만 뜻하며 실제 충돌·초기 무압현·안정성은 별도 GPU probe로 확인한다.
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

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0, str(ROOT))
BASE = Path(__file__).resolve().parents[1]
FINGERS = ('index', 'middle', 'ring', 'pinky')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def generate_bundle(bundle, case):
    """기존 builder가 줄 번호를 변환하도록 입력은 0=낮은 E로 기록한다."""
    from guitar_learning.tool import (build_fret_training_data, build_strike_training_data,
        build_strike_plan, register_song_bundle)
    if (bundle/'manifest.json').is_file():
        return
    bundle.mkdir(parents=True, exist_ok=True)
    finger = FINGERS.index(case['finger'])+1
    string = 6-case['string_standard_1based']
    fret = case['fret']
    mapping = dict(purpose='single_press_18.v1', convention='string 0 = low-E',
        notes=[dict(t_on=0., t_off=1.5, string=string, fret=fret,
                    midi=(40,45,50,55,59,64)[string]+fret, finger=finger, barre=False, grip=None)],
        presses=[dict(finger=finger, string=string, fret=fret, barre=False,
                      t_press=0., t_release=1.5, strikes=[0.])],
        hand=[dict(t=0., P=max(1,min(22,fret-finger+1)), grip=None)],
        stats=dict(dropped_invalid_fret=0), diagnostics=[], violations=[])
    path = bundle/'mapping/fingering.json'
    write(path, mapping)
    register_song_bundle.write_tablature_if_missing(bundle)
    audio = bundle/'source/audio.wav'
    audio.parent.mkdir(exist_ok=True)
    with wave.open(str(audio), 'wb') as stream:
        stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(16000)
        stream.writeframes(b'\0\0'*24000)
    training = bundle/'training'; training.mkdir(exist_ok=True)
    build_fret_training_data.main(['--fingering',str(path),'--audio',str(audio),'--out',str(training/'fret_training.json')])
    build_strike_training_data.main([str(path),'--out',str(training/'strike_training.json')])
    build_strike_plan.main([str(training/'strike_training.json'),'--out',str(training/'strike_plan.json')])
    register_song_bundle.write_manifest(bundle.name,bundle,dict(registration_mode='single_press_18.v1',
        generator=str(Path(__file__).resolve().relative_to(ROOT)), generator_sha256=sha(__file__),
        audio='1.5 seconds digital silence; clock only'))


def snapshot(contract, q, poses):
    """reset 때만 쓰는 DOF와 body FK 일치 상태. 기타·다른 actor는 보존한다."""
    state = copy.deepcopy(contract['state'])
    for row, value in zip(state['human_dof_states'],q):
        row.update(pos=float(value),vel=0.)
    for name,row in zip(contract['initial']['human_body_names'],state['human_body_states']):
        point, rotation = poses[name]
        row['pose']['p'] = dict(zip('xyz',map(float,point)))
        row['pose']['r'] = dict(zip('xyzw',map(float,rotation.as_quat())))
        for kind in ('linear','angular'):
            row['vel'][kind] = dict.fromkeys('xyz',0.)
    return state


def build(args):
    import numpy as np
    from scipy.optimize import least_squares
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.contact import load_fingertip_pad
    from guitar_learning.song.task import make_task
    from guitar_learning.tool.validation.press_acquisition import action_bounds, source_geometry
    cases = json.loads((BASE/'설계/cases.json').read_text())['cases']
    if args.case:
        cases = [c for c in cases if c['case_id'] in args.case]
        if len(cases) != len(set(args.case)):
            raise ValueError('Unknown or duplicate requested cases')
    out = args.out.resolve() if args.out else BASE/'입력'
    out.mkdir(parents=True, exist_ok=True)
    contract = load_gpu_prepared_reset_contract('left')
    names = contract['initial']['joint_names']
    q0 = np.array([r['pos'] for r in contract['state']['human_dof_states']])
    ref = np.asarray(contract['target105'])
    fk = full_fk(SimpleNamespace(names=names,human_bodies=contract['initial']['human_body_names'],q_ref=q0),contract['state'])
    active, lower, upper = action_bounds(contract)
    pad = load_fingertip_pad()
    gp = contract['state']['guitar_body_states'][0]['pose']
    guitar_p = np.array([gp['p'][a] for a in 'xyz'])
    guitar_r = Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
    pins = dict(contract['source_sha256']); pins.update(pad['contract']['source_sha256'])
    for f in (full_fk,action_bounds,source_geometry,load_fingertip_pad,load_gpu_prepared_reset_contract,make_task):
        p = Path(inspect.getsourcefile(f)).resolve(); pins[str(p)] = sha(p)
    pins[str(Path(__file__).resolve())] = sha(__file__)
    target_file = out/'catalog.json'
    old = json.loads(target_file.read_text()) if target_file.exists() else {}
    by_id = {r['case_id']:r for r in old.get('goals',[])}
    for case in cases:
        if case['case_id'] in by_id and not args.retry:
            continue
        song = 'single18_'+case['case_id']
        bundle = out/'song_bundles'/song
        generate_bundle(bundle,case)
        task = make_task(bundle)
        target = task.targets[0]
        if len(task.targets)!=1 or (target.string,target.fret,target.finger)!=(case['string_standard_1based']-1,case['fret'],FINGERS.index(case['finger'])+1):
            raise ValueError('Bundle target mismatch')
        if (target.onset_s,target.end_s,task.duration_s)!=(3.,4.5,5.):
            raise ValueError('Bundle timing mismatch')
        for entry in task.provenance['provenance']:
            pins[entry['path']] = entry['sha256']
        starts,ends,low,high,plane,surface = source_geometry(contract,[dict(string=target.string,fret=target.fret)])
        pins.update(surface['source_sha256'])
        normal = plane[:3]/np.linalg.norm(plane[:3]); start = starts[target.string]
        line = ends[target.string]-start
        center = start+((low[0]+high[0])/2-start[1])/line[1]*line
        finger = case['finger']; number = target.finger-1
        local = pad['points_local'][number][pad['valid'][number]].astype(float)
        normals = pad['normals_local'][number][pad['valid'][number]].astype(float)
        arm = [i for i,n in enumerate(ACTIVE_NAMES) if n.startswith('L_')]
        digit = [i for i,n in enumerate(ACTIVE_NAMES) if n.startswith('LH:'+finger)]
        attempts = []
        for channels in (arm,arm+digit):
            native = active[channels]; lo,hi = lower[channels],upper[channels]
            def evaluate(values):
                trial = q0.copy(); trial[native] = values
                p,r = fk(trial)['LH:'+finger+'3']
                points = guitar_r.inv().apply(p+r.apply(local)-guitar_p)
                facing = -guitar_r.inv().apply(r.apply(normals))@normal
                nearest = np.argmin(np.linalg.norm(points-center-.010*normal,axis=1))
                return trial,points,facing,int(nearest)
            def residual(values):
                trial,points,facing,j = evaluate(values)
                return np.r_[1000*(points[j]-center-.010*normal),10*max(.3-facing[j],0),.05*(values-q0[native])]
            seed = np.clip(q0[native],lo+1e-9,hi-1e-9)
            guesses = (seed,.75*seed+.25*(lo+hi)/2)
            fits = [least_squares(residual,g,bounds=(lo,hi),max_nfev=args.max_nfev,
                    ftol=1e-8,xtol=1e-8,gtol=1e-8) for g in guesses]
            fit = min(fits,key=lambda f:np.linalg.norm(residual(f.x)))
            q,points,facing,j = evaluate(fit.x)
            delta = points-center; height = delta@normal
            tangent = np.linalg.norm(delta-height[:,None]*normal,axis=1)
            valid = (tangent<=.005)&(height>=.005)&(height<=.015)&(facing>=.1)
            metrics = dict(candidate_valid=bool(valid.any()),selected_sample=j,
                tangent_error_m=float(tangent[j]),height_m=float(height[j]),normal_cos=float(facing[j]),
                valid_sample_count=int(valid.sum()))
            attempts.append(dict(scope='arm_only' if channels==arm else 'arm_and_target_finger',
                **metrics,optimizer_nfev=int(fit.nfev),optimizer_converged=bool(fit.success)))
            if metrics['candidate_valid']:
                break
        hold = ref.copy(); hold[native] = q[native]
        state = snapshot(contract,q,fk(q))
        by_id[case['case_id']] = dict(case_id=case['case_id'],case=case['case_id'],song=song,bundle=str(bundle.resolve()),
            finger=finger,finger_id=target.finger,string=target.string,physical_string=target.string+1,
            fret=target.fret,q105=q.tolist(),hold_target105=hold.tolist(),body_snapshot=state,state=state,
            geometry=metrics,candidate_valid=metrics['candidate_valid'],native_verified=False,
            search_attempts=attempts,target_finger_change_rad=(q[active[digit]]-q0[active[digit]]).tolist(),
            center_G_m=center.tolist(),normal_G=normal.tolist(),nominal_height_m=.010,
            pad_points_G_m=points.tolist(),normal_cos=facing.tolist(),perturbations=[],
            native_probe_required=dict(initial_no_press=True,finite_hold_s=.5,body_dof_consistency=True,
                                       physical_and_wrist_safety=True))
        changed = [p for p,h in pins.items() if sha(p)!=h]
        if changed:
            raise RuntimeError('Source/input changed: '+str(changed))
        catalog = dict(schema='guitar_learning.single18_geometry.v1',goals=list(by_id.values()),
            reference105=ref.tolist(),initial_q105=q0.tolist(),joint_names=names,
            active_names=list(ACTIVE_NAMES),action_indices=active.tolist(),action_lower=lower.tolist(),
            action_upper=upper.tolist(),source_sha256=pins,initial_pose=contract['initial_pose'],
            native_verified=False,limitation='CPU FK only; native probe required; failed optimization is not impossibility')
        write(target_file,catalog)
        write(out/'provenance.json',dict(schema='single18_inputs.v1',catalog_sha256=sha(target_file),
            case_design_sha256=sha(BASE/'설계/cases.json'),active_physical_inputs=pins,
            candidate_count=len(by_id),native_verified_count=sum(bool(r['native_verified']) for r in by_id.values())))
        print(case['case_id'],metrics,flush=True)
    return by_id


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',action='append',default=[])
    parser.add_argument('--out',type=Path)
    parser.add_argument('--max-nfev',type=int,default=100)
    parser.add_argument('--retry',action='store_true')
    build(parser.parse_args())
