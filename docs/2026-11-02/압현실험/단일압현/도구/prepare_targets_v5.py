"""손 전체와 기타 전체 활성 충돌 형상의 분리를 요구하는 팔 자세 보정.

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


def collision_meshes(pins):
    """현재 native XML의 scale/geom 변환과 실제 STL/OBJ convex 정점을 읽는다.

    기타 convex face 축만으로 얻는 분리 간격은 보수적이다. 양수는 분리를
    증명하지만 음수는 실제 교차의 증명이 아니다. cooked 형상은 native 검증한다.
    """
    import numpy as np
    import trimesh
    import xml.etree.ElementTree as ET
    from scipy.spatial import ConvexHull
    from scipy.spatial.transform import Rotation
    from guitar_learning.native.paths import HUMAN
    # ElementTree Element에는 사용자 속성을 붙일 수 없어 경로를 closure로 관리한다.
    def load_rows(path,select):
        root = ET.parse(path).getroot(); pins[str(Path(path).resolve())]=sha(path)
        compiler = root.find('compiler');folder=Path(path).parent/(compiler.get('meshdir','') if compiler is not None else '')
        assets = {m.get('name'):m for m in root.findall('asset/mesh')};rows=[]
        for body in root.iter('body'):
            if not select(body.get('name')): continue
            for geom in body.findall('geom'):
                if geom.get('contype')=='0' or geom.get('conaffinity')=='0':continue
                if geom.get('type')=='mesh':
                    mesh=assets[geom.get('mesh')]
                    path=(folder/mesh.get('file')).resolve();pins[str(path)]=sha(path)
                    vertices=np.array(trimesh.load(str(path),process=False).vertices)
                    vertices*=np.fromstring(mesh.get('scale','1 1 1'),sep=' ')
                    label=geom.get('mesh')
                elif geom.get('type')=='box':
                    from itertools import product
                    vertices=np.array(list(product((-1.,1.),repeat=3)))*np.fromstring(geom.get('size'),sep=' ')
                    label='box_'+str(len(rows))
                elif geom.get('type')=='capsule':
                    from itertools import product
                    endpoints=np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3)
                    radius=float(geom.get('size'))
                    corners=np.array(list(product((-1.,1.),repeat=3)))*radius
                    vertices=(endpoints[:,None,:]+corners[None,:,:]).reshape(-1,3)
                    label='capsule_outer_box_'+str(len(rows))
                else:
                    raise ValueError('Unsupported active collision geom: '+str(geom.attrib))
                quat=np.fromstring(geom.get('quat','1 0 0 0'),sep=' ')
                vertices=Rotation.from_quat(quat[[1,2,3,0]]).apply(vertices)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
                rows.append((body.get('name'),label,vertices))
        return rows
    hand = load_rows(HUMAN,lambda n:n=='L_Wrist' or (n is not None and n.startswith('LH:')))
    hand = [(n,m,v[ConvexHull(v).vertices]) for n,m,v in hand]
    guitar = load_rows(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml',lambda n:True)
    neck=[]
    for n,m,v in guitar:
        planes=ConvexHull(v).equations
        _,indices=np.unique(np.round(planes,8),axis=0,return_index=True)
        neck.append((m,planes[indices],v.min(0),v.max(0)))
    return hand,neck


def build(args):
    import numpy as np
    from scipy.optimize import least_squares, minimize
    from scipy.spatial.transform import Rotation
    from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.core.control import ACTIVE_NAMES
    from guitar_learning.gpu.contact import load_fingertip_pad
    from guitar_learning.song.task import make_task
    from guitar_learning.tool.validation.press_acquisition import action_bounds, source_geometry
    if not 5. <= args.hover_mm <= 30.:
        raise ValueError('CPU hover must be 5..30 mm; native validation remains 5..15 mm')
    hover = args.hover_mm/1000.
    if not 5. <= args.clearance_mm <= 15.:
        raise ValueError('Non-target clearance must be 5..15 mm')
    clearance = args.clearance_mm/1000.
    cases = json.loads((BASE/'설계/cases.json').read_text())['cases']
    if args.case:
        cases = [c for c in cases if c['case_id'] in args.case]
        if len(cases) != len(set(args.case)):
            raise ValueError('Unknown or duplicate requested cases')
    out = args.out.resolve() if args.out else BASE/'입력/전체기타후보'
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
    hand_meshes, neck_planes = collision_meshes(pins)
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
        # 실제 fingerboard 전체 y범위와 최대 폭. 끝마디 유효 안쪽 표본만 검사한다.
        _,_,neck_low,neck_high,_,_ = source_geometry(contract,[dict(string=0,fret=f) for f in range(1,23)])
        neck_y = (neck_low.min()-.010,neck_high.max()+.010)
        neck_x = (min(starts[:,0].min(),ends[:,0].min())-.012,
                  max(starts[:,0].max(),ends[:,0].max())+.012)
        other_ids = [i for i in range(4) if i!=number]
        def other_metrics(poses):
            minima = []; violations = []
            for other in other_ids:
                op,orr = poses['LH:'+FINGERS[other]+'3']
                olocal = pad['points_local'][other][pad['valid'][other]].astype(float)
                pts = guitar_r.inv().apply(op+orr.apply(olocal)-guitar_p)
                near = ((pts[:,0]>=neck_x[0])&(pts[:,0]<=neck_x[1])&
                        (pts[:,1]>=neck_y[0])&(pts[:,1]<=neck_y[1]))
                heights = pts@normal+plane[3]
                # 고정3차원 residual. 해당 손가락이 넥 범위 밖이면 간격 위반은0이다.
                minima.append(float(heights[near].min()) if near.any() else 1.)
                violations.append(max(clearance+.0015-minima[-1],0.))
            return np.array(minima),np.array(violations)
        warm = BASE/'입력/후보'/case['case_id']/'catalog.json'
        anchor = q0.copy()
        if warm.exists():
            pins[str(warm.resolve())] = sha(warm)
            anchor = np.array(json.loads(warm.read_text())['goals'][0]['q105'])
        guitar_lower=np.array([row[2] for row in neck_planes])
        guitar_upper=np.array([row[3] for row in neck_planes])
        def collision_gaps(poses):
            gaps=[];labels=[]
            for body,mesh,vertices in hand_meshes:
                p,r=poses[body]
                points=guitar_r.inv().apply(p+r.apply(vertices)-guitar_p)
                # AABB간 거리는 실제 convex거리의 하한이다. 3mm 이상이면
                # 2.5mm목적 여유까지 이미 증명되므로 많은 body 조각의 plane검사를 생략한다.
                minimum,maximum=points.min(0),points.max(0)
                broad=np.linalg.norm(np.maximum(np.maximum(guitar_lower-maximum,
                    minimum-guitar_upper),0.),axis=1)
                for k,(guitar,planes,_,_) in enumerate(neck_planes):
                    separation=broad[k]
                    if separation<.003:
                        separation=(points@planes[:,:3].T+planes[:,3]).min(axis=0).max()
                    gaps.append(float(separation));labels.append(body+'/'+mesh+' vs '+guitar)
            return np.array(gaps),labels
        attempts=[]
        for radius in (.10,.20,.35):
            channels=arm;native=active[channels]
            lo=np.maximum(lower[channels],anchor[native]-radius)
            hi=np.minimum(upper[channels],anchor[native]+radius)
            def evaluate(values):
                trial=q0.copy();trial[native]=values;poses=fk(trial)
                p,r=poses['LH:'+finger+'3']
                points=guitar_r.inv().apply(p+r.apply(local)-guitar_p)
                facing=-guitar_r.inv().apply(r.apply(normals))@normal
                a=(low[0]+.002-start[1])/line[1];b=(high[0]-.002-start[1])/line[1]
                fraction=np.clip((points-start)@line/(line@line),min(a,b),max(a,b))
                closest=start+fraction[:,None]*line
                j=int(np.linalg.norm(points-closest,axis=1).argmin())
                minimum,violation=other_metrics(poses)
                gaps,labels=collision_gaps(poses)
                return trial,points,facing,j,closest,minimum,violation,gaps,labels
            def residual(values):
                trial,points,facing,j,closest,minimum,violation,gaps,labels=evaluate(values)
                return np.r_[1000*(points[j]-center-hover*normal),
                    15*max(.3-facing[j],0),2000*violation,
                    3000*np.maximum(.0025-gaps,0),2.*(values-anchor[native])]
            seed=np.clip(anchor[native],lo+1e-9,hi-1e-9)
            fit=least_squares(residual,seed,bounds=(lo,hi),max_nfev=args.max_nfev,
                ftol=1e-8,xtol=1e-8,gtol=1e-8)
            if radius == .20:
                def constraints(values):
                    trial,pts,cos,j,close,mn,vi,gp,labels=evaluate(values)
                    h=pts[j]@normal+plane[3]
                    delta=pts[j]-close[j]
                    tangent=np.linalg.norm(delta-(delta@normal)*normal)
                    return np.r_[1000*(gp-.00205),1000*(mn-.00505),
                        1000*(h-.00505),1000*(.01495-h),1000*(.00495-tangent),cos[j]-.101]
                def objective(values):
                    trial,pts,cos,j,close,mn,vi,gp,labels=evaluate(values)
                    return float(np.sum((1000*(pts[j]-center-hover*normal))**2)+
                        .1*np.sum((values-anchor[native])**2))
                refined=minimize(objective,fit.x,method='SLSQP',bounds=list(zip(lo,hi)),
                    constraints=[dict(type='ineq',fun=constraints)],
                    options=dict(maxiter=80,ftol=1e-9))
                if np.min(constraints(refined.x))>=-1e-4:
                    fit=refined
            q,points,facing,j,closest,minimum,violation,gaps,labels=evaluate(fit.x)
            height=points@normal+plane[3]
            delta=points-closest
            tangent=np.linalg.norm(delta-(delta@normal)[:,None]*normal,axis=1)
            valid=(tangent<=.005)&(height>=hover-.005)&(height<=hover+.005)&(facing>=.1)
            clearance_valid=bool((minimum>=clearance-1e-6).all())
            mesh_valid=bool((gaps>=.002-1e-6).all())
            metrics=dict(candidate_valid=bool(valid[j] and clearance_valid and mesh_valid),selected_sample=j,
                tangent_error_m=float(tangent[j]),height_m=float(height[j]),normal_cos=float(facing[j]),
                valid_sample_count=int(valid.sum()),selector='runtime finite fret segment nearest valid sample',
                non_target_fingers=[FINGERS[i] for i in other_ids],non_target_min_heights_m=minimum.tolist(),
                non_target_clearance_m=clearance,clearance_valid=clearance_valid,
                full_hand_mesh_valid=mesh_valid,full_hand_min_neck_gap_m=float(gaps.min()),
                full_hand_mesh_gaps_m=dict(zip(labels,gaps.tolist())),
                full_hand_collision_scope='native source full guitar convex shapes (mesh and boxes), conservative AABB/face separation; cooked native unverified',
                max_arm_delta_from_v1_rad=float(np.abs(q[native]-anchor[native]).max()))
            attempts.append(dict(scope='arm_only',radius_rad=radius,**metrics,
                optimizer_nfev=int(fit.nfev),optimizer_converged=bool(fit.success)))
            if metrics['candidate_valid']:break
        hold = ref.copy(); hold[native] = q[native]
        state = snapshot(contract,q,fk(q))
        by_id[case['case_id']] = dict(case_id=case['case_id'],case=case['case_id'],song=song,bundle=str(bundle.resolve()),
            finger=finger,finger_id=target.finger,string=target.string,physical_string=target.string+1,
            fret=target.fret,q105=q.tolist(),hold_target105=hold.tolist(),body_snapshot=state,state=state,
            geometry=metrics,candidate_valid=metrics['candidate_valid'],native_verified=False,
            search_attempts=attempts,target_finger_change_rad=(q[active[digit]]-q0[active[digit]]).tolist(),
            center_G_m=center.tolist(),normal_G=normal.tolist(),nominal_height_m=hover,
            pad_points_G_m=points.tolist(),normal_cos=facing.tolist(),perturbations=[],
            native_probe_required=dict(initial_no_press=True,finite_hold_s=.5,body_dof_consistency=True,
                                       physical_and_wrist_safety=True))
        changed = [p for p,h in pins.items() if sha(p)!=h]
        if changed:
            raise RuntimeError('Source/input changed: '+str(changed))
        catalog = dict(schema='guitar_learning.single18_geometry.v5',goals=list(by_id.values()),
            reference105=ref.tolist(),initial_q105=q0.tolist(),joint_names=names,
            active_names=list(ACTIVE_NAMES),action_indices=active.tolist(),action_lower=lower.tolist(),
            action_upper=upper.tolist(),source_sha256=pins,initial_pose=contract['initial_pose'],
            native_verified=False,requested_cpu_hover_mm=args.hover_mm, native_height_band_m=[.005,.015],
            limitation='CPU full hand versus full guitar conservative source convex separation; cooked native probe required')
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
    parser.add_argument('--hover-mm',type=float,default=10.)
    parser.add_argument('--clearance-mm',type=float,default=5.)
    parser.add_argument('--retry',action='store_true')
    build(parser.parse_args())
