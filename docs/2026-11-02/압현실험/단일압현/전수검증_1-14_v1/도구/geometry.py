"""공통 v9에서 실제 팔 운반에 사용할 별도 CPU 경유 후보를 만든다.

출처: prepare_transport_v2.py SHA256 6e39ef07567a1575c065eaccdcd6ad4ec80b6ed77fed406a823fc4be5ef3556c.
이 실험에 필요한 Planner를 독립 복사했다. 과거 Python은 import하지 않는다.
정적 FK 경로 검사는 동적 native 안정성이나 실제 도달의 증명이 아니다.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
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
from scipy.spatial.transform import Rotation

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
BASE=Path(__file__).resolve().parents[2]
STUDY=Path(__file__).resolve().parents[1]
FINGERS=('index','middle','ring','pinky')
SCHEMA='guitar_learning.common_start_transport.v2'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def verify_inputs(catalog_path,provenance_path):
    provenance=json.loads(Path(provenance_path).read_text())
    if sha(catalog_path)!=provenance['catalog_sha256']:
        raise ValueError('catalog SHA mismatch')
    for path,expected in provenance['active_physical_inputs'].items():
        if sha(path)!=expected:raise ValueError('Pinned input changed: '+path)
    return json.loads(Path(catalog_path).read_text()),provenance


def joint_path(start,end,max_step_rad=np.deg2rad(2)):
    a,b=np.asarray(start,dtype=float),np.asarray(end,dtype=float)
    if a.shape!=(105,) or b.shape!=(105,) or not np.isfinite([a,b]).all() or max_step_rad<=0:
        raise ValueError('Finite q105 and positive interpolation step required')
    steps=max(1,int(np.ceil(np.abs(b-a).max()/max_step_rad)))
    return [a+(b-a)*i/steps for i in range(steps+1)]


def snapshot(contract,q,poses):
    state=copy.deepcopy(contract['state'])
    for row,value in zip(state['human_dof_states'],q):row.update(pos=float(value),vel=0.)
    for name,row in zip(contract['initial']['human_body_names'],state['human_body_states']):
        p,r=poses[name];row['pose']['p']=dict(zip('xyz',map(float,p)));row['pose']['r']=dict(zip('xyzw',map(float,r.as_quat())))
        for key in ('linear','angular'):row['vel'][key]=dict.fromkeys('xyz',0.)
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

_COLLISION_CACHE=None
def cached_collision_meshes(pins):
    """같은 고정 자산은 한 번만 읽되 모든 호출에 입력 해시를 남긴다."""
    global _COLLISION_CACHE
    if _COLLISION_CACHE is None:
        source_pins={}; rows=collision_meshes(source_pins)
        _COLLISION_CACHE=(rows,source_pins)
    pins.update(_COLLISION_CACHE[1])
    return _COLLISION_CACHE[0]

class Planner:
    """팔12축만 바꾸며 실제 contact selector와 전체 기타 source 충돌을 대조한다."""
    def __init__(self,catalog,row):
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        from guitar_learning.gpu.contact import load_fingertip_pad
        from guitar_learning.tool.validation.press_acquisition import source_geometry
        self.contract=load_gpu_prepared_reset_contract('left')
        c=self.contract;self.q0=np.array([r['pos'] for r in c['state']['human_dof_states']])
        self.fk=full_fk(SimpleNamespace(names=c['initial']['joint_names'],human_bodies=c['initial']['human_body_names'],q_ref=self.q0),c['state'])
        self.pins=dict(c['source_sha256'])
        for function in (load_gpu_prepared_reset_contract,full_fk,load_fingertip_pad,source_geometry):
            p=Path(inspect.getsourcefile(function)).resolve();self.pins[str(p)]=sha(p)
        self.hand,self.guitar=cached_collision_meshes(self.pins)
        self.guitar_lo=np.array([g[2] for g in self.guitar]);self.guitar_hi=np.array([g[3] for g in self.guitar])
        gp=c['state']['guitar_body_states'][0]['pose']
        self.gp=np.array([gp['p'][a] for a in 'xyz']);self.gr=Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
        self.arm=np.array(catalog['action_indices'][:12]);self.lo=np.array(catalog['action_lower'][:12]);self.hi=np.array(catalog['action_upper'][:12])
        self.row=row;self.finger=row['finger_id']-1
        pad=load_fingertip_pad();self.pad=pad;self.pins.update(pad['contract']['source_sha256'])
        starts,ends,low,high,plane,surface=source_geometry(c,[row]);self.pins.update(surface['source_sha256'])
        self.start=starts[row['string']];self.line=ends[row['string']]-self.start
        self.plane=plane;self.normal=plane[:3]/np.linalg.norm(plane[:3]);self.low=low[0]+.002;self.high=high[0]-.002
        self.center=self.start+((low[0]+high[0])/2-self.start[1])/self.line[1]*self.line

    def gaps(self,q):
        if hasattr(self,"_cached_gaps") and np.array_equal(q,self._cached_gaps[0]):
            return self._cached_gaps[1:]
        poses=self.fk(q);values=[];labels=[]
        for body,mesh,vertices in self.hand:
            p,r=poses[body];points=self.gr.inv().apply(p+r.apply(vertices)-self.gp)
            broad=np.linalg.norm(np.maximum(np.maximum(self.guitar_lo-points.max(0),points.min(0)-self.guitar_hi),0.),axis=1)
            for k,(name,planes,_,_) in enumerate(self.guitar):
                gap=broad[k]
                if gap<.003:gap=(points@planes[:,:3].T+planes[:,3]).min(0).max()
                values.append(float(gap));labels.append(body+' vs '+name)
        self._cached_gaps=(np.array(q).copy(),np.array(values),labels)
        return self._cached_gaps[1:]

    def measure(self,q):
        poses=self.fk(q);p,r=poses['LH:'+FINGERS[self.finger]+'3']
        local=self.pad['points_local'][self.finger][self.pad['valid'][self.finger]]
        normals=self.pad['normals_local'][self.finger][self.pad['valid'][self.finger]]
        points=self.gr.inv().apply(p+r.apply(local)-self.gp)
        facing=-self.gr.inv().apply(r.apply(normals))@self.normal
        a=(self.low-self.start[1])/self.line[1];b=(self.high-self.start[1])/self.line[1]
        fraction=np.clip((points-self.start)@self.line/(self.line@self.line),min(a,b),max(a,b))
        closest=self.start+fraction[:,None]*self.line
        j=int(np.linalg.norm(points-closest,axis=1).argmin())
        delta=points[j]-closest[j];height=float(points[j]@self.normal+self.plane[3])
        tangent=float(np.linalg.norm(delta-(delta@self.normal)*self.normal))
        gaps,labels=self.gaps(q);lowest=int(gaps.argmin())
        wrist_p,wrist_r=poses['L_Wrist'];wp=self.gr.inv().apply(wrist_p-self.gp);wr=self.gr.inv()*wrist_r
        valid=bool(.005<=height<=.015 and tangent<=.005 and facing[j]>=.1 and gaps.min()>=.002-1e-6)
        return dict(candidate_valid=valid,selected_sample=j,height_m=height,tangent_error_m=tangent,
            normal_cos=float(facing[j]),minimum_source_shape_gap_m=float(gaps[lowest]),limiting_shape_pair=labels[lowest],
            wrist_position_G_m=wp.tolist(),wrist_quaternion_G_xyzw=wr.as_quat().tolist(),
            selected_point_G_m=points[j].tolist(),native_verified=False)

    def endpoint(self,seed,max_nfev):
        seed=np.asarray(seed,dtype=float).copy();seed[np.setdiff1d(np.arange(105),self.arm)]=self.q0[np.setdiff1d(np.arange(105),self.arm)]
        original=self.measure(seed)
        if original['candidate_valid']:return seed,dict(method='existing verified-identity CPU seed',geometry=original)
        def residual(values):
            q=self.q0.copy();q[self.arm]=values;m=self.measure(q);gaps,_=self.gaps(q)
            point=np.array(m['selected_point_G_m'])
            return np.r_[1000*(point-self.center-.010*self.normal),
                10*max(.2-m['normal_cos'],0),2500*np.maximum(.0025-gaps,0),.5*(values-seed[self.arm])]
        fit=least_squares(residual,np.clip(seed[self.arm],self.lo+1e-9,self.hi-1e-9),bounds=(self.lo,self.hi),max_nfev=max_nfev)
        q=self.q0.copy();q[self.arm]=fit.x;m=self.measure(q)
        # 원본보다 나빠진 국소해를 무조건 대표로 고르지 않는다.
        def score(metric):
            return (max(.002-metric['minimum_source_shape_gap_m'],0)*3000+
                max(metric['tangent_error_m']-.005,0)*1000+
                max(.005-metric['height_m'],metric['height_m']-.015,0)*1000)
        if score(original)<score(m):return seed,dict(method='original seed retained after unsuccessful local search',optimizer_nfev=int(fit.nfev),geometry=original)
        return q,dict(method='bounded arm-only local endpoint search',optimizer_nfev=int(fit.nfev),geometry=m)

    def path(self,goal,max_nfev):
        def validate(points):
            minima=[];pairs=[]
            for q in points:
                gaps,labels=self.gaps(q);j=int(gaps.argmin());minima.append(float(gaps[j]));pairs.append(labels[j])
            return dict(candidate_valid=bool(min(minima)>=.002-1e-6),minimum_source_shape_gap_m=min(minima),
                waypoint_source_gap_m=minima,limiting_pairs=pairs,
                scope='sampled joint-position interpolation at <=2 degrees/axis; static source convex only, not swept/native proof')
        direct=joint_path(self.q0,goal);check=validate(direct)
        if check['candidate_valid']:return direct,dict(method='direct common-start joint path',command_q105=[self.q0.tolist(),goal.tolist()],**check)
        mid=(self.q0+goal)/2
        # 단일 경유점만 조절하며 외부(+Gx)와 앞면(+Gz)으로 약한 회피 안내를 준다.
        p,r=self.fk(mid)['L_Wrist'];wanted=self.gr.inv().apply(p-self.gp)+np.array([.035,0.,.020])
        def residual(values):
            qmid=self.q0.copy();qmid[self.arm]=values;p,_=self.fk(qmid)['L_Wrist']
            rows=[200*(self.gr.inv().apply(p-self.gp)-wanted),.5*(values-mid[self.arm])]
            for a,b in ((self.q0,qmid),(qmid,goal)):
                for f in (.25,.5,.75,1.):
                    gaps,_=self.gaps(a+(b-a)*f);rows.append(2500*np.maximum(.0025-gaps,0))
            return np.concatenate(rows)
        fit=least_squares(residual,np.clip(mid[self.arm],self.lo+1e-9,self.hi-1e-9),bounds=(self.lo,self.hi),max_nfev=max_nfev)
        middle=self.q0.copy();middle[self.arm]=fit.x
        route=joint_path(self.q0,middle)+joint_path(middle,goal)[1:];checked=validate(route)
        if checked['minimum_source_shape_gap_m']>check['minimum_source_shape_gap_m']:
            return route,dict(method='one bounded outward waypoint',command_q105=[self.q0.tolist(),middle.tolist(),goal.tolist()],optimizer_nfev=int(fit.nfev),**checked)
        return direct,dict(method='direct retained; detour search did not improve clearance',command_q105=[self.q0.tolist(),goal.tolist()],optimizer_nfev=int(fit.nfev),**check)


def press_candidates(planner,native_state,native_q105,lower105,upper105,starts=3,max_nfev=60):
    """도착한 실제 q와 몸체 pose를 기준으로 담당 손가락 4축만 국소 탐색한다.

    반환값은 기하 후보일 뿐 압현 성공 판정이 아니다. 움직이는 기타에 대한
    접촉·하중·오압현·유지는 반드시 별도 native 실행에서 검사한다.
    """
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    q=np.asarray(native_q105,dtype=float)
    lower=np.asarray(lower105,dtype=float);upper=np.asarray(upper105,dtype=float)
    if q.shape!=(105,) or lower.shape!=(105,) or upper.shape!=(105,) or not np.isfinite(np.r_[q,lower,upper]).all():
        raise ValueError('유한 native q105와 실제 native 한계105 필요')
    if not 1<=starts<=4 or not 1<=max_nfev<=100:raise ValueError('시작점1~4, nfev1~100 필요')
    names=planner.contract['initial']['joint_names'];bodies=planner.contract['initial']['human_body_names']
    prefix='LH:'+FINGERS[planner.finger]
    indices=[i for i,n in enumerate(names) if n.startswith(prefix)]
    if len(indices)!=4:raise ValueError('담당 손가락4축 필요')
    fk=full_fk(SimpleNamespace(names=names,human_bodies=bodies,q_ref=q),native_state)
    gp=native_state['guitar_body_states'][0]['pose']
    position=np.array([gp['p'][a] for a in 'xyz']);rotation=Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
    valid=planner.pad['valid'][planner.finger]
    local=planner.pad['points_local'][planner.finger][valid]
    normals=planner.pad['normals_local'][planner.finger][valid]
    def samples(values):
        trial=q.copy();trial[indices]=values;p,r=fk(trial)[prefix+'3']
        return rotation.inv().apply(p+r.apply(local)-position),-rotation.inv().apply(r.apply(normals))@planner.normal,trial
    initial_points,_,_=samples(q[indices])
    selected=int(np.linalg.norm(initial_points-planner.center,axis=1).argmin())
    target=planner.center-.0005*planner.normal
    native_low,native_high=lower[indices],upper[indices]
    seeds=[q[indices],q[indices]+np.array([.15,0,.15,.1]),
        (native_low+native_high)/2,q[indices]+np.array([.3,-.1,.3,.2])]
    candidates=[]
    for seed in seeds[:starts]:
        def residual(values):
            points,facing,_=samples(values)
            return np.r_[1000*(points[selected]-target),10*max(.2-facing[selected],0)]
        fit=least_squares(residual,np.clip(seed,native_low+1e-10,native_high-1e-10),
            bounds=(native_low,native_high),max_nfev=max_nfev)
        points,facing,trial=samples(fit.x)
        heights=points@planner.normal+planner.plane[3]
        projected=points-heights[:,None]*planner.normal
        fraction=(projected-planner.start)@planner.line/(planner.line@planner.line)
        lateral=np.linalg.norm(projected-planner.start-fraction[:,None]*planner.line,axis=1)
        passing=(heights>=-.001)&(heights<=.003)&(lateral<=.003)&(points[:,1]>=planner.low)&(points[:,1]<=planner.high)&(facing>=.1)
        delta=points[selected]-target
        candidates.append(dict(q105=trial.tolist(),finger4_rad=fit.x.tolist(),geometry_candidate=bool(passing.any()),
            passing_samples=np.flatnonzero(passing).tolist(),selected_sample=selected,
            height_m=float(heights[selected]),tangent_m=float(lateral[selected]),facing=float(facing[selected]),
            target_error_m=float(np.linalg.norm(delta)),nfev=int(fit.nfev),native_verified=False))
    candidates.sort(key=lambda r:(not r['geometry_candidate'],r['target_error_m']))
    # 보정점 자체의 위치 재현 오차도 남긴다. 오차가 크면 native 상태 변환을 확인한다.
    calibration=fk(q);reproduction=max(float(np.linalg.norm(calibration[n][0]-np.array([b['pose']['p'][a] for a in 'xyz'])))
        for n,b in zip(bodies,native_state['human_body_states']))
    return dict(indices=indices,candidates=candidates,native_lower_rad=native_low.tolist(),native_upper_rad=native_high.tolist(),
        fk_reproduction_position_error_m=reproduction,scope='도착 손목을 고정한 기하 후보. 물리 압현 성공 판정이 아님.')


def scan(out,max_nfev=16):
    """336조합을 인접 프렛·기존 후보에서 탐색하고 미해결도 모두 기록한다."""
    import time
    if out.exists():raise FileExistsError('기존 출력 덮어쓰기 금지')
    old=BASE/'재실험_공통출발_v1'
    control_path=old/'inputs_v2/middle_s1_f12/catalog.json'
    template,provenance=verify_inputs(control_path,control_path.with_name('provenance.json'))
    seeds=[];pins={str(Path(__file__).resolve()):sha(__file__)}
    for path in sorted((BASE/'입력/전체기타후보').glob('*/catalog.json')):
        document,_=verify_inputs(path,path.with_name('provenance.json'));row=document['goals'][0]
        seeds.append((row,np.asarray(row['q105'])))
        pins[str(path.resolve())]=sha(path);pins[str(path.with_name('provenance.json').resolve())]=sha(path.with_name('provenance.json'))
    for path in sorted((old/'inputs_v2').glob('*/catalog.json')):
        document,_=verify_inputs(path,path.with_name('provenance.json'));row=document['goals'][0]
        seeds.append((row,np.asarray(row['final_hover_q105'])))
        pins[str(path.resolve())]=sha(path);pins[str(path.with_name('provenance.json').resolve())]=sha(path.with_name('provenance.json'))
    pins.update(provenance['active_physical_inputs'])
    baseline=Planner(template,dict(finger_id=2,string=0,fret=12));known=np.asarray(template['goals'][0]['final_hover_q105'])
    metric=baseline.measure(known)
    if not metric['candidate_valid']:raise ValueError('기존 middle S1 F12의 정확한 기준 재현 실패')
    out.mkdir(parents=True)
    write(out/'baseline_reproduction.json',dict(case='middle_s1_f12',geometry=metric,q105=known.tolist(),source_sha256=pins))
    started=time.monotonic();rows=[]
    report=dict(schema='guitar_learning.range336.geometry.v1',completed=False,rows=rows,source_sha256=pins,
        catalog_base={k:v for k,v in template.items() if k!='goals'},
        max_nfev_per_seed=max_nfev,expected_total=336,limitation='CPU geometry only; finite search misses are not physical impossibility')
    for finger_id,finger in enumerate(FINGERS,1):
        for physical_string in range(1,7):
            # 12프렛 근처의 기존 후보에서 양쪽으로 이어가며 직전 유효 후보를 우선한다.
            last=None
            for fret in [12,11,10,9,8,7,6,5,4,3,2,1,13,14]:
                goal=dict(case=f'{finger}_s{physical_string}_f{fret}',case_id=f'{finger}_s{physical_string}_f{fret}',
                    finger=finger,finger_id=finger_id,string=physical_string-1,physical_string=physical_string,fret=fret)
                planner=Planner(template,goal);pins.update(planner.pins)
                nearby=sorted(seeds,key=lambda pair:20*(pair[0]['finger_id']!=finger_id)+3*abs(pair[0]['string']-goal['string'])+abs(pair[0]['fret']-fret))
                candidates=([('previous_valid_neighbor',last)] if last is not None else [])+[(r['case'],q) for r,q in nearby[:2]]
                attempts=[];best=None
                for label,seed in candidates:
                    q,search=planner.endpoint(seed,max_nfev)
                    attempts.append(dict(seed=label,search=search))
                    quality=(not search['geometry']['candidate_valid'],
                        3000*max(.002-search['geometry']['minimum_source_shape_gap_m'],0)+1000*search['geometry']['tangent_error_m']+
                        1000*abs(search['geometry']['height_m']-.01))
                    if best is None or quality<best[0]:best=(quality,q,search)
                    if search['geometry']['candidate_valid']:break
                _,q,search=best
                if search['geometry']['candidate_valid']:last=q
                fixed=np.setdiff1d(np.arange(105),planner.arm)
                if not np.array_equal(q[fixed],planner.q0[fixed]):raise ValueError('고정된 비팔 관절 변경')
                duration=max(2.,min(6.,np.abs(q-planner.q0).max()/.5))
                route=[]
                for label,point,t in [('start',planner.q0,0.),('hover',q,duration)]:
                    m=planner.measure(point)
                    route.append(dict(label=label,q105=point.tolist(),wrist_position_G_m=m['wrist_position_G_m'],
                        wrist_quaternion_G_xyzw=m['wrist_quaternion_G_xyzw'],minimum_duration_s=t,geometry=m,native_verified=False))
                rows.append(dict(**goal,q105=q.tolist(),geometry=search['geometry'],candidate_valid=search['geometry']['candidate_valid'],
                    transport_waypoints=route,transport_path_candidate_valid=None,attempts=attempts,native_verified=False,
                    path_scope='Direct command route; not collision-certified. Native failure must be retained.'))
                report['elapsed_s']=time.monotonic()-started
                write(out/'geometry_candidates.json',report)
                print(goal['case'],search['geometry']['candidate_valid'],round(report['elapsed_s'],1),flush=True)
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('탐색 중 입력 변경: '+path)
    report.update(completed=True,counts=dict(total=len(rows),candidate=sum(r['candidate_valid'] for r in rows)),elapsed_s=time.monotonic()-started)
    write(out/'geometry_candidates.json',report)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--max-nfev',type=int,default=16)
    args=parser.parse_args();scan(args.out.resolve(),args.max_nfev)
