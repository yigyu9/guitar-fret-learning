"""공통 v9에서 실제 팔 운반에 사용할 별도 CPU 경유 후보를 만든다.

과거 catalog는 해시를 검증한 데이터로만 읽는다. 과거 Python은 import하지 않는다.
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
        self.hand,self.guitar=collision_meshes(self.pins)
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
        poses=self.fk(q);values=[];labels=[]
        for body,mesh,vertices in self.hand:
            p,r=poses[body];points=self.gr.inv().apply(p+r.apply(vertices)-self.gp)
            broad=np.linalg.norm(np.maximum(np.maximum(self.guitar_lo-points.max(0),points.min(0)-self.guitar_hi),0.),axis=1)
            for k,(name,planes,_,_) in enumerate(self.guitar):
                gap=broad[k]
                if gap<.003:gap=(points@planes[:,:3].T+planes[:,3]).min(0).max()
                values.append(float(gap));labels.append(body+' vs '+name)
        return np.array(values),labels

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


def prepare(args):
    source=args.catalog.resolve() if args.catalog else BASE/'입력/전체기타후보'/args.case/'catalog.json'
    provenance=source.with_name('provenance.json')
    catalog,original_provenance=verify_inputs(source,provenance)
    rows=[r for r in catalog['goals'] if args.case in (r.get('case'),r.get('case_id'))]
    if len(rows)!=1:raise ValueError('Single case identity required')
    if args.out.exists():raise FileExistsError('Immutable output already exists: '+str(args.out))
    original=rows[0];planner=Planner(catalog,original)
    goal,endpoint_search=planner.endpoint(original['q105'],args.max_nfev)
    route,path_search=planner.path(goal,args.path_nfev)
    # CPU 검증 표본을 제어 경유점으로 쓰면 매 표본에서 정지하므로 둘을 분리한다.
    commands=[np.array(q) for q in path_search['command_q105']]
    lengths=[float(np.max(np.abs(b-a))) for a,b in zip(commands,commands[1:])]
    length=sum(lengths)
    total_duration=max(2.,min(6.,length/.5))
    waypoints=[]
    for i,q in enumerate(commands):
        m=planner.measure(q)
        duration=0. if i==0 else total_duration*(lengths[i-1]/length if length>1e-12 else 1./len(lengths))
        waypoints.append(dict(label='start' if i==0 else 'hover' if i==len(commands)-1 else 'retreat',
            q105=q.tolist(),wrist_position_G_m=m['wrist_position_G_m'],wrist_quaternion_G_xyzw=m['wrist_quaternion_G_xyzw'],
            minimum_duration_s=duration,geometry=m,native_verified=False))
    validation_samples=[]
    for i,q in enumerate(route):
        validation_samples.append(dict(q105=q.tolist(),geometry=planner.measure(q),
            command_waypoint=False,native_verified=False))
    row=copy.deepcopy(original)
    row.pop('native_validation',None)
    row.update(q105=planner.q0.tolist(),state=copy.deepcopy(planner.contract['state']),
        body_snapshot=copy.deepcopy(planner.contract['state']),hold_target105=goal.tolist(),
        final_hover_q105=goal.tolist(),final_hover_state=snapshot(planner.contract,goal,planner.fk(goal)),
        geometry=endpoint_search['geometry'],candidate_valid=endpoint_search['geometry']['candidate_valid'],
        native_verified=False,transport_waypoints=waypoints,
        transport_path_candidate_valid=path_search['candidate_valid'],transport_validation_samples=validation_samples,
        transport=dict(schema=SCHEMA,reset_source='common_v9',finger_condition='fixed_v9_all_fingers',
            final_target_scope='CPU proposal; never state overwrite after reset',
            endpoint_search=endpoint_search,path_search=path_search,
            minimum_transport_duration_s=sum(w['minimum_duration_s'] for w in waypoints),
            command_waypoint_scope='start/(optional retreat)/hover only; dense FK samples are validation data, not stop-go commands',
            requires_new_native_probe=True))
    result=copy.deepcopy(catalog)
    pins=dict(original_provenance['active_physical_inputs']);pins.update(planner.pins)
    for p in (source,provenance,Path(__file__).resolve()):pins[str(p)]=sha(p)
    result.update(schema=SCHEMA+'.catalog',goals=[row],initial_q105=planner.q0.tolist(),source_sha256=pins,native_verified=False)
    args.out.mkdir(parents=True)
    write(args.out/'catalog.json',result)
    write(args.out/'provenance.json',dict(schema=SCHEMA+'.provenance',catalog_sha256=sha(args.out/'catalog.json'),
        active_physical_inputs=pins,source_catalog=str(source),source_provenance=str(provenance),native_verified=False))
    for path,expected in pins.items():
        if sha(path)!=expected:raise ValueError('Input changed during planning: '+path)
    status='cpu_proposal_ready' if row['candidate_valid'] and row['transport_path_candidate_valid'] else 'endpoint_unresolved' if not row['candidate_valid'] else 'path_unresolved'
    report=dict(schema=SCHEMA+'.report',completed=True,case=args.case,status=status,
        candidate_valid=row['candidate_valid'],path_candidate_valid=row['transport_path_candidate_valid'],
        waypoints=len(waypoints),validation_samples=len(validation_samples),minimum_transport_duration_s=row['transport']['minimum_transport_duration_s'],
        endpoint=endpoint_search,path=path_search,native_verified=False,
        limitations=['Finite local search does not prove impossibility','Static source shape interpolation does not certify native transport','Only arm12 changes; all LH fingers/thumb remain common v9'])
    write(args.out/'report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('endpoint','path')},ensure_ascii=False),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--catalog',type=Path)
    parser.add_argument('--max-nfev',type=int,default=40)
    parser.add_argument('--path-nfev',type=int,default=30)
    args=parser.parse_args()
    prepare(args)


if __name__=='__main__':main()
