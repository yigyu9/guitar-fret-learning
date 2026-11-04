"""공통 v9에서 실제 팔 운반에 사용할 별도 CPU 경유 후보를 만든다.

출처: prepare_transport_v2.py SHA256 6e39ef07567a1575c065eaccdcd6ad4ec80b6ed77fed406a823fc4be5ef3556c.
이 실험에 필요한 Planner를 독립 복사했다. 과거 Python은 import하지 않는다.
정적 FK 경로 검사는 동적 native 안정성이나 실제 도달의 증명이 아니다.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name]='1'
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
FINGERS=('index','middle','ring','pinky')


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

def path_clearance_threshold(initial_gaps,progress,clearance=.002,ramp_fraction=.20):
    """양수 초기 근접 쌍에만 적용하는 명시적 준비 경로의 요구 여유다.

    초기 교차(음수)는 거부한다. 0 간격은 양수 근접 예외에 속하지 않아 처음부터
    2mm를 요구한다. 경로의 첫20%에서 예외 여유를 선형으로2mm까지 올린다.
    native 물리·준비·압현 판정 또는 끝점 여유를 변경하는 함수가 아니다.
    """
    initial=np.asarray(initial_gaps,dtype=float)
    if initial.ndim!=1 or not np.isfinite(initial).all() or np.any(initial<0):
        raise ValueError('음수 없는 유한 초기 source gap 배열 필요')
    if not np.isfinite([progress,clearance,ramp_fraction]).all() or not 0<=progress<=1 or clearance<=0 or not 0<ramp_fraction<=1:
        raise ValueError('진행률0~1과 양수 요구 여유·상승 구간 필요')
    near=(initial>0)&(initial<clearance)
    fraction=min(progress/ramp_fraction,1.)
    return np.where(near,initial+(clearance-initial)*fraction,clearance)


def joint_path_progress(points):
    """분절마다 누적한 L∞ 관절 경로 길이의 비율. 시간 진행률과 구별한다."""
    if len(points)==0:raise ValueError('경로 표본이 하나 이상 필요')
    lengths=np.array([float(np.abs(np.asarray(b)-a).max()) for a,b in zip(points,points[1:])])
    cumulative=np.r_[0.,np.cumsum(lengths)]
    if cumulative[-1]>0:return cumulative/cumulative[-1]
    # 움직임이 없어도 마지막 표본에는 끝점의 정상 여유를 요구한다.
    return np.linspace(0.,1.,len(points)) if len(points)>1 else np.ones(1)


class Planner:
    """기본 팔12축, 선택적으로 담당 손가락4축을 함께 준비 정렬한다."""
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
        self.catalog_limits={int(i):(float(lo),float(hi)) for i,lo,hi in zip(
            catalog['action_indices'],catalog['action_lower'],catalog['action_upper'])}
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

    def preparation_axes(self,joint_finger=False):
        """공동 준비에서만 native 한계와 카탈로그 행동 한계의 교집합을 사용한다."""
        if not joint_finger:return self.arm,self.lo,self.hi
        names=self.contract['initial']['joint_names']
        finger=[i for i,n in enumerate(names) if n.startswith('LH:'+FINGERS[self.finger])]
        if len(finger)!=4:raise ValueError('담당 손가락4축 필요')
        indices=np.r_[self.arm,finger]
        if len(np.unique(indices))!=16:raise ValueError('팔12축과 손가락4축은 중복되면 안 됨')
        native=self.contract['initial']['native_PD_properties']
        low=[];high=[]
        for i in indices:
            if int(i) not in self.catalog_limits:raise ValueError('공동 준비 축의 카탈로그 한계 누락')
            lo,hi=self.catalog_limits[int(i)]
            low.append(max(lo,float(native['lower'][i])))
            high.append(min(hi,float(native['upper'][i])))
        low=np.asarray(low);high=np.asarray(high)
        if not np.isfinite(np.r_[low,high]).all() or np.any(low>=high):
            raise ValueError('유한하고 폭이 양수인 native/행동 한계 교집합 필요')
        return indices,low,high

    def endpoint(self,seed,max_nfev,joint_finger=False):
        axes,lo,hi=self.preparation_axes(joint_finger)
        seed=np.asarray(seed,dtype=float).copy()
        seed[np.setdiff1d(np.arange(105),axes)]=self.q0[np.setdiff1d(np.arange(105),axes)]
        if joint_finger:seed[axes]=np.clip(seed[axes],lo,hi)
        original=self.measure(seed)
        meta=dict(joint_finger=bool(joint_finger),optimized_indices=axes.tolist(),
            lower_rad=lo.tolist(),upper_rad=hi.tolist(),
            limit_scope='native_PD_properties intersect catalog actions' if joint_finger else 'unchanged catalog arm12')
        if original['candidate_valid']:return seed,dict(method='existing verified-identity CPU seed',geometry=original,**meta)
        def residual(values):
            q=self.q0.copy();q[axes]=values;m=self.measure(q);gaps,_=self.gaps(q)
            point=np.array(m['selected_point_G_m'])
            return np.r_[1000*(point-self.center-.010*self.normal),
                10*max(.2-m['normal_cos'],0),2500*np.maximum(.0025-gaps,0),.5*(values-seed[axes])]
        fit=least_squares(residual,np.clip(seed[axes],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=max_nfev)
        q=self.q0.copy();q[axes]=fit.x;m=self.measure(q)
        def score(metric):
            return (max(.002-metric['minimum_source_shape_gap_m'],0)*3000+
                max(metric['tangent_error_m']-.005,0)*1000+
                max(.005-metric['height_m'],metric['height_m']-.015,0)*1000)
        original_score=score(original)+(10*max(.1-original['normal_cos'],0) if joint_finger else 0.)
        fitted_score=score(m)+(10*max(.1-m['normal_cos'],0) if joint_finger else 0.)
        original_key=(not original['candidate_valid'] if joint_finger else False,original_score)
        fitted_key=(not m['candidate_valid'] if joint_finger else False,fitted_score)
        if original_key<fitted_key:return seed,dict(method='original seed retained after unsuccessful local search',optimizer_nfev=int(fit.nfev),geometry=original,**meta)
        method='bounded arm12 plus assigned finger4 endpoint search' if joint_finger else 'bounded arm-only local endpoint search'
        return q,dict(method=method,optimizer_nfev=int(fit.nfev),geometry=m,**meta)

    def path(self,goal,max_nfev,joint_finger=False):
        goal=np.asarray(goal,dtype=float)
        if goal.shape!=(105,) or not np.isfinite(goal).all():raise ValueError('유한 goal q105 필요')
        if joint_finger:
            axes,lo,hi=self.preparation_axes(True)
            fixed=np.setdiff1d(np.arange(105),axes)
            if not np.array_equal(goal[fixed],self.q0[fixed]):raise ValueError('비담당 관절 변경 금지')
            if np.any(goal[axes]<lo-1e-9) or np.any(goal[axes]>hi+1e-9):raise ValueError('공동 준비 한계 이탈')
        initial,initial_labels=self.gaps(self.q0)
        initial=initial.copy()
        exceptions=(initial>0)&(initial<.002)
        initial_negative=bool((initial<0).any())
        clearance_contract=dict(schema='guitar_learning.positive_initial_clearance_ramp.v1',
            regular_clearance_m=.002,ramp_end_progress=.20,comparison_tolerance_m=1e-6,
            initial_negative_rejected=initial_negative,
            rule='Only positive initial gaps below2mm start at that initial gap; linear rise to2mm by20% path progress; all other pairs always require2mm',
            progress='cumulative joint-position L-infinity path length / total; geometric, not command time; zero-length path uses sample progress to enforce final2mm',
            initial_clearances=[dict(pair=name,gap_m=float(gap),initial_near_exception=bool(near))
                for name,gap,near in zip(initial_labels,initial,exceptions)],
            exception_pairs=[name for name,near in zip(initial_labels,exceptions) if near],
            limitation='Explicit static source geometry path contract only; endpoint2mm and all native criteria unchanged')
        def validate(points):
            minima=[];pairs=[];margins=[];margin_pairs=[];thresholds=[]
            progress=joint_path_progress(points)
            for q,fraction in zip(points,progress):
                gaps,labels=self.gaps(q);j=int(gaps.argmin());minima.append(float(gaps[j]));pairs.append(labels[j])
                if labels!=initial_labels:raise ValueError('경로 중 source 형상 쌍 순서 변경')
                # 음수 시작은 항상 거부한다. 예외 기준을 계산해 정상 경로로 바꾸지 않는다.
                required=np.full_like(initial,.002) if initial_negative else path_clearance_threshold(initial,float(fraction))
                difference=gaps-required;k=int(difference.argmin())
                margins.append(float(difference[k]));margin_pairs.append(labels[k]);thresholds.append(float(required[k]))
            return dict(candidate_valid=not initial_negative and min(margins)>=-1e-6,
                minimum_source_shape_gap_m=min(minima),minimum_contract_margin_m=min(margins),
                waypoint_source_gap_m=minima,limiting_pairs=pairs,
                sample_path_progress=progress.tolist(),sample_minimum_contract_margin_m=margins,
                sample_limiting_contract_pairs=margin_pairs,sample_limiting_required_gap_m=thresholds,
                clearance_contract=clearance_contract,
                sample_count=len(points),maximum_sample_axis_step_rad=float(max(
                    (np.abs(b-a).max() for a,b in zip(points,points[1:])),default=0.)),
                joint_finger=bool(joint_finger),
                collision_scope='hand and wrist source shapes versus all guitar source shapes only; no hand-hand or full-body test',
                scope='sampled joint-position interpolation at <=2 degrees/axis; static source convex only, not swept/native proof')
        direct=joint_path(self.q0,goal);check=validate(direct)
        if initial_negative:
            return direct,dict(method='rejected negative initial source gap; no clearance exception or detour search',
                command_q105=[self.q0.tolist(),goal.tolist()],**check)
        if check['candidate_valid']:return direct,dict(method='direct common-start joint path',command_q105=[self.q0.tolist(),goal.tolist()],**check)
        mid=(self.q0+goal)/2
        # 단일 경유점만 조절하며 외부(+Gx)와 앞면(+Gz)으로 약한 회피 안내를 준다.
        p,r=self.fk(mid)['L_Wrist'];wanted=self.gr.inv().apply(p-self.gp)+np.array([.035,0.,.020])
        def residual(values):
            qmid=goal.copy();qmid[self.arm]=values;p,_=self.fk(qmid)['L_Wrist']
            rows=[200*(self.gr.inv().apply(p-self.gp)-wanted),.5*(values-mid[self.arm])]
            # 각 분절의 L∞ 길이와 누적 진행률을 최종 dense 검사와 동일하게 쓴다.
            first=float(np.abs(qmid-self.q0).max());second=float(np.abs(goal-qmid).max())
            total=first+second;offset=0.
            for segment,(a,b,length) in enumerate(((self.q0,qmid,first),(qmid,goal,second))):
                for f in (.25,.5,.75,1.):
                    progress=(offset+length*f)/total if total>0 else (segment+f)/2
                    gaps,_=self.gaps(a+(b-a)*f)
                    required=path_clearance_threshold(initial,progress)
                    rows.append(2500*np.maximum(required-gaps,0))
                offset+=length
            return np.concatenate(rows)
        fit=least_squares(residual,np.clip(mid[self.arm],self.lo+1e-9,self.hi-1e-9),bounds=(self.lo,self.hi),max_nfev=max_nfev)
        middle=goal.copy();middle[self.arm]=fit.x
        route=joint_path(self.q0,middle)+joint_path(middle,goal)[1:];checked=validate(route)
        if checked['minimum_contract_margin_m']>check['minimum_contract_margin_m']:
            return route,dict(method='one bounded outward waypoint',command_q105=[self.q0.tolist(),middle.tolist(),goal.tolist()],optimizer_nfev=int(fit.nfev),**checked)
        return direct,dict(method='direct retained; detour search did not improve clearance contract margin',command_q105=[self.q0.tolist(),goal.tolist()],optimizer_nfev=int(fit.nfev),**check)


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
        margin=contact_margin(points,heights,lateral,facing,planner.low,planner.high,passing)
        joint=joint_margin(fit.x,native_low,native_high)
        candidates.append(dict(q105=trial.tolist(),finger4_rad=fit.x.tolist(),geometry_candidate=bool(passing.any()),
            passing_samples=np.flatnonzero(passing).tolist(),selected_sample=selected,
            height_m=float(heights[selected]),tangent_m=float(lateral[selected]),facing=float(facing[selected]),
            target_error_m=float(np.linalg.norm(delta)),nfev=int(fit.nfev),native_verified=False,
            **margin,**joint,robust_score=min(margin['contact_margin_normalized'],joint['joint_margin_normalized']),
            collision_checked=False,collision_limitation='finger/body and finger/finger shape collision not tested by this candidate search'))
    candidates.sort(key=lambda r:(not r['geometry_candidate'],r['target_error_m']))
    # 보정점 자체의 위치 재현 오차도 남긴다. 오차가 크면 native 상태 변환을 확인한다.
    calibration=fk(q);reproduction=max(float(np.linalg.norm(calibration[n][0]-np.array([b['pose']['p'][a] for a in 'xyz'])))
        for n,b in zip(bodies,native_state['human_body_states']))
    return dict(indices=indices,candidates=candidates,native_lower_rad=native_low.tolist(),native_upper_rad=native_high.tolist(),
        fk_reproduction_position_error_m=reproduction,
        margin_scope='same passing sample; fixed unchanged contact thresholds; no body-shape collision certification',scope='도착 손목을 고정한 기하 후보. 물리 압현 성공 판정이 아님.')


def contact_margin(points,heights,lateral,facing,low,high,passing):
    """동일 표면점에서 모든 접촉 조건까지 남은 여유의 최솟값을 구한다.

    m 단위 여유에는 높이·현 수직 거리·프렛 셀 경계를 포함한다. 방향 여유는
    단위가 다르므로 정규화 여유에만 포함한다. 실제 압현 문턱은 바꾸지 않는다.
    """
    spatial=np.column_stack((heights+.001,.003-heights,.003-lateral,points[:,1]-low,high-points[:,1]))
    scales=np.array([.002,.002,.003,(high-low)/2,(high-low)/2])
    if np.any(scales<=0):raise ValueError('접촉 셀의 양수 내부 폭 필요')
    normalized=np.column_stack((spatial/scales[None,:],(facing-.1)/.9))
    score=normalized.min(1)
    eligible=np.flatnonzero(passing)
    # 실패 후보에도 진단 여유를 남기지만 유효 표본이 있으면 그 안에서만 고른다.
    choices=eligible if len(eligible) else np.arange(len(points))
    best=int(choices[np.argmax(score[choices])])
    return dict(margin_sample_index=best,margin_sample_valid=bool(passing[best]),
        contact_margin_m=float(spatial[best].min()),contact_margin_normalized=float(score[best]),
        contact_margin_components_m=dict(zip(('height_lower','height_upper','lateral','fret_lower','fret_upper'),map(float,spatial[best]))),
        facing_margin=float(facing[best]-.1),
        contact_margin_scope='one best eligible sample; normalized minimum includes facing; geometric only')


def joint_margin(values,lower,upper):
    """요청한 담당 관절이 native 한계에 얼마나 가까운지 계산한다."""
    width=np.asarray(upper)-np.asarray(lower)
    if np.any(width<=0):raise ValueError('담당 관절의 양수 native 범위 필요')
    margin=np.minimum(np.asarray(values)-lower,np.asarray(upper)-values)
    normalized=2*margin/width
    return dict(joint_margin_per_axis_rad=margin.tolist(),joint_margin_rad=float(margin.min()),
        joint_margin_per_axis_normalized=normalized.tolist(),joint_margin_normalized=float(normalized.min()),
        joint_margin_scope='native requested angle range; 0 at limit and1 at midpoint, not anatomical certification')


def choose_press_candidate(candidates,arrival,indices,robust=False):
    """유효 후보 중 기존 방식은 최소 이동, robust 방식은 최대 내부 여유를 고른다.

    반환값은 입력 candidates 안의 인덱스다. 기하적으로 유효한 후보가 없다면
    호출자가 미해결로 기록하도록 오류를 반환한다. 무효 후보로 대체하지 않는다.
    """
    eligible=[i for i,c in enumerate(candidates) if c['geometry_candidate']]
    if not eligible:raise ValueError('기하적으로 유효한 압현 후보가 없음')
    reference=np.asarray(arrival)[indices]
    def rank(i):
        candidate=candidates[i]
        movement=float(np.square(np.asarray(candidate['finger4_rad'])-reference).sum())
        if not robust:return (movement,i)
        return (-candidate['robust_score'],candidate['target_error_m'],movement,i)
    return min(eligible,key=rank)


def select_robust_candidate(result):
    """press_candidates의 유효 후보 중 최대 내부 여유의 인덱스만 반환한다."""
    candidates=result['candidates']
    eligible=[i for i,c in enumerate(candidates) if c['geometry_candidate']]
    if not eligible:raise ValueError('기하적으로 유효한 압현 후보가 없음')
    return min(eligible,key=lambda i:(-candidates[i]['robust_score'],candidates[i]['target_error_m'],i))


def pad_geometry_jacobian(planner,native_state,native_q105,sample_index,epsilon=1e-4):
    """실제 도착 FK로 보정한 패드 한 점의 3×4 위치 Jacobian을 측정한다.

    sample_index는 기존 selected_sample처럼 유효 패드 표본 부분집합의 번호다.
    중앙 차분은 기하 모델에서만 계산하며 물리 적분·관절 명령 생성은 하지 않는다.
    """
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    q=np.asarray(native_q105,dtype=float)
    if q.shape!=(105,) or not np.isfinite(q).all() or not 0<epsilon<=.001:
        raise ValueError('유한 q105와 0<epsilon<=0.001 필요')
    names=planner.contract['initial']['joint_names'];bodies=planner.contract['initial']['human_body_names']
    prefix='LH:'+FINGERS[planner.finger]
    indices=[i for i,n in enumerate(names) if n.startswith(prefix)]
    if len(indices)!=4:raise ValueError('담당 손가락4축 필요')
    fk=full_fk(SimpleNamespace(names=names,human_bodies=bodies,q_ref=q),native_state)
    gp=native_state['guitar_body_states'][0]['pose']
    position=np.array([gp['p'][a] for a in 'xyz']);rotation=Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
    valid=planner.pad['valid'][planner.finger]
    points=planner.pad['points_local'][planner.finger][valid]
    normals=planner.pad['normals_local'][planner.finger][valid]
    if not 0<=sample_index<len(points):raise ValueError('유효 패드 부분집합의 표본 번호 필요')
    def measure(values):
        trial=q.copy();trial[indices]=values;p,r=fk(trial)[prefix+'3']
        point=rotation.inv().apply(p+r.apply(points[sample_index])-position)
        facing=float(-rotation.inv().apply(r.apply(normals[sample_index]))@planner.normal)
        return np.r_[point,facing]
    measured=measure(q[indices]);jacobian=np.empty((4,4))
    for axis in range(4):
        plus=q[indices].copy();minus=plus.copy();plus[axis]+=epsilon;minus[axis]-=epsilon
        jacobian[:,axis]=(measure(plus)-measure(minus))/(2*epsilon)
    return dict(indices=indices,selected_sample=int(sample_index),point_G_m=measured[:3].tolist(),
        target_G_m=(planner.center-.0005*planner.normal).tolist(),normal_cos=float(measured[3]),
        point_jacobian_G_m_per_rad=jacobian[:3].tolist(),normal_cos_gradient_per_rad=jacobian[3].tolist(),
        finite_difference_epsilon_rad=epsilon,
        scope='native-pose-calibrated local FK derivative; no command, physical integration or collision certification')
