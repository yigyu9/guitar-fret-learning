"""기록된 A 손목에서 중지 S3F6·약지 S2F7의 공통 압현 기하 후보를 찾는다.

과거 Python은 실행하지 않는다. 현재 활성 FK·유효 끝마디 패드·표면 도구만
사용한다. 정적 기하 후보이며 native 접촉·하중·안전·정책 성공의 증명이 아니다.
"""
import os
for _name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares, linprog
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
STUDY = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


class Search:
    def __init__(self):
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        from guitar_learning.gpu.contact import load_fingertip_pad
        from guitar_learning.tool.validation.press_acquisition import source_geometry
        contract = load_gpu_prepared_reset_contract('left')
        self.pins = dict(contract['source_sha256'])
        for function in (load_gpu_prepared_reset_contract,full_fk,load_fingertip_pad,source_geometry):
            source = Path(inspect.getsourcefile(function)).resolve();self.pins[str(source)] = sha(source)
        for name in ('catalog.json','known_press.json','provenance.json','manifest.json'):
            source = STUDY/'입력/C1'/name;self.pins[str(source)] = sha(source)
        cat = json.loads((STUDY/'입력/C1/catalog.json').read_text())
        provenance = json.loads((STUDY/'입력/C1/provenance.json').read_text())
        self.pins.update(provenance['active_physical_inputs'])
        for name,expected in self.pins.items():
            if sha(name) != expected:raise ValueError('원문 입력 SHA 불일치: '+name)
        row = cat['goals'][0];self.state = row['state'];self.q0 = np.asarray(row['q105'])
        self.names = cat['joint_names'];self.bodies = contract['initial']['human_body_names']
        self.fk = full_fk(SimpleNamespace(names=self.names,human_bodies=self.bodies,q_ref=self.q0),self.state)
        pose = self.state['guitar_body_states'][0]['pose']
        self.gp = np.array([pose['p'][a] for a in 'xyz'])
        self.gr = Rotation.from_quat([pose['r'][a] for a in 'xyzw'])
        self.lo = np.asarray(contract['initial']['native_PD_properties']['lower'])
        self.hi = np.asarray(contract['initial']['native_PD_properties']['upper'])
        self.arm = np.array(cat['action_indices'][:12]);self.middle = np.arange(60,64);self.ring = np.arange(64,68)
        known = json.loads((STUDY/'입력/C1/known_press.json').read_text())['endpoint_states']
        self.qa = np.array(known['middle_s3_f6']['press_q105'])
        self.qd = np.array(known['ring_s2_f7']['press_q105'])
        self.pad = load_fingertip_pad();self.pins.update(self.pad['contract']['source_sha256'])
        goals = [dict(string=2,fret=6),dict(string=1,fret=7)]
        starts,ends,low,high,self.plane,surface = source_geometry(contract,goals)
        self.pins.update(surface['source_sha256'])
        self.normal = self.plane[:3]/np.linalg.norm(self.plane[:3]);self.goals = []
        for finger,goal,lo,hi in zip((1,2),goals,low,high):
            start,end = starts[goal['string']],ends[goal['string']];line = end-start
            center = start+((lo+hi)/2-start[1])/line[1]*line
            self.goals.append(dict(finger=finger,body='LH:'+('middle','ring')[finger-1]+'3',
                start=start,line=line,low=lo+.002,high=hi-.002,center=center,
                local=self.pad['points_local'][finger][self.pad['valid'][finger]],
                normals=self.pad['normals_local'][finger][self.pad['valid'][finger]]))
        poses = self.fk(self.q0)
        self.reproduction_error = max(float(np.linalg.norm(poses[n][0]-np.array([b['pose']['p'][a] for a in 'xyz'])))
            for n,b in zip(self.bodies,self.state['human_body_states']))
        self.pins[str(Path(__file__).resolve())] = sha(__file__)

    def samples(self,q):
        poses = self.fk(q);rows = []
        for goal in self.goals:
            p,r = poses[goal['body']]
            points = self.gr.inv().apply(p+r.apply(goal['local'])-self.gp)
            facing = -self.gr.inv().apply(r.apply(goal['normals']))@self.normal
            height = points@self.normal+self.plane[3]
            projected = points-height[:,None]*self.normal
            t = (projected-goal['start'])@goal['line']/(goal['line']@goal['line'])
            lateral = np.linalg.norm(projected-goal['start']-t[:,None]*goal['line'],axis=1)
            passing = ((height>=-.001)&(height<=.003)&(lateral<=.003)&
                (points[:,1]>=goal['low'])&(points[:,1]<=goal['high'])&(facing>=.1))
            rows.append(dict(points=points,facing=facing,height=height,lateral=lateral,passing=passing))
        return rows

    def measure(self,q):
        rows = []
        for goal,result in zip(self.goals,self.samples(q)):
            selected = int(np.linalg.norm(result['points']-(goal['center']-.0005*self.normal),axis=1).argmin())
            rows.append(dict(body=goal['body'],geometry_candidate=bool(result['passing'].any()),
                passing_samples=np.flatnonzero(result['passing']).tolist(),selected_sample=selected,
                selected_point_G_m=result['points'][selected].tolist(),height_m=float(result['height'][selected]),
                lateral_m=float(result['lateral'][selected]),normal_cos=float(result['facing'][selected])))
        wrist = self.fk(q)['L_Wrist']
        return dict(goals=rows,both_geometry_candidate=all(r['geometry_candidate'] for r in rows),
            wrist_G_m=self.gr.inv().apply(wrist[0]-self.gp).tolist(),
            min_native_joint_margin_rad=float(np.minimum(q-self.lo,self.hi-q).min()),
            active20_min_native_joint_margin_rad=float(np.minimum(q-self.lo,self.hi-q)[np.r_[self.arm,self.middle,self.ring]].min()),
            native_verified=False)

    def search(self,free_arm=False):
        indices = np.r_[self.arm,self.middle,self.ring] if free_arm else self.ring
        seeds = [self.qa.copy() for _ in range(4)]
        seeds[1][self.ring] = self.qd[self.ring]
        seeds[2][self.ring] = (self.lo[self.ring]+self.hi[self.ring])/2
        seeds[3][self.ring] += np.array([.3,-.1,.3,.2])
        if free_arm:
            for seed,fraction in zip(seeds,(0.,.25,.5,.75)):
                seed[self.arm] = (1-fraction)*self.qa[self.arm]+fraction*self.qd[self.arm]
        results = []
        for seed in seeds:
            selected = [int(np.linalg.norm(r['points']-(g['center']-.0005*self.normal),axis=1).argmin())
                for g,r in zip(self.goals,self.samples(seed))]
            def residual(values):
                q = self.qa.copy();q[indices] = values;rows = self.samples(q);parts = []
                for goal,row,j in zip(self.goals,rows,selected):
                    parts.extend(1000*(row['points'][j]-(goal['center']-.0005*self.normal)))
                    parts.append(10*max(.2-row['facing'][j],0))
                if free_arm:parts.extend(.03*(q[self.arm]-self.qa[self.arm]))
                return np.asarray(parts)
            fit = least_squares(residual,np.clip(seed[indices],self.lo[indices]+1e-10,self.hi[indices]-1e-10),
                bounds=(self.lo[indices],self.hi[indices]),max_nfev=120)
            q = self.qa.copy();q[indices] = fit.x
            results.append(dict(q105=q.tolist(),fit_success=bool(fit.success),cost=float(fit.cost),nfev=int(fit.nfev),
                scope='arm12+middle4+ring4' if free_arm else 'A arm and middle fixed; ring4 only',
                measure=self.measure(q)))
        return sorted(results,key=lambda r:(not r['measure']['both_geometry_candidate'],r['cost']))


def collision_diagnostics(search,q):
    """실제 source mesh convex hull의 손가락간·넥 간섭을 정적으로 진단한다.

    양수 face-axis 간격은 분리 증거다. 그 외에는 선형계획으로 두 convex
    hull의 공통점 존재를 확인한다. native cooked 모양·침투 깊이의 인증은 아니다.
    """
    import trimesh
    from itertools import product,combinations
    from guitar_learning.native.paths import HUMAN
    def meshes(path,human):
        path = Path(path).resolve();search.pins[str(path)] = sha(path)
        xml = ET.parse(path).getroot();folder = path.parent/xml.find('compiler').get('meshdir','')
        assets = {m.get('name'):m for m in xml.findall('asset/mesh')};rows = []
        for body in xml.iter('body'):
            name = body.get('name')
            if human and not (name or '').startswith('LH:'):continue
            for i,geom in enumerate(body.findall('geom')):
                if geom.get('contype')=='0' or geom.get('conaffinity')=='0':continue
                label = geom.get('mesh',geom.get('type','')+'_'+str(i))
                if not human and not (label.startswith('guitar_neck') or geom.get('type')=='box'):continue
                if geom.get('type')=='mesh':
                    asset = assets[geom.get('mesh')];file = (folder/asset.get('file')).resolve()
                    search.pins[str(file)] = sha(file)
                    vertices = np.asarray(trimesh.load(str(file),process=False).vertices,dtype=float)
                    vertices *= np.fromstring(asset.get('scale','1 1 1'),sep=' ')
                elif geom.get('type')=='box':
                    vertices = np.array(list(product((-1.,1.),repeat=3)))*np.fromstring(geom.get('size'),sep=' ')
                elif geom.get('type')=='capsule':
                    endpoints = np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3)
                    corners = np.array(list(product((-1.,1.),repeat=3)))*float(geom.get('size'))
                    vertices = (endpoints[:,None,:]+corners[None,:,:]).reshape(-1,3)
                    label = 'capsule_conservative_outer_box_'+str(i)
                else:raise ValueError('지원하지 않는 source hand collision 형상: '+str(geom.attrib))
                quat = np.fromstring(geom.get('quat','1 0 0 0'),sep=' ')
                vertices = Rotation.from_quat(quat[[1,2,3,0]]).apply(vertices)+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
                vertices = vertices[ConvexHull(vertices).vertices]
                rows.append((name,label,vertices))
        return rows
    hand = meshes(HUMAN,True)
    guitar = meshes(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/guitar_compound.xml',False)
    poses = search.fk(q)
    transformed = []
    for name,label,vertices in hand:
        p,r = poses[name]
        points = search.gr.inv().apply(p+r.apply(vertices)-search.gp)
        transformed.append((name,label,points))
    def compare(first,second):
        a,b = first[2],second[2]
        broad = float(np.linalg.norm(np.maximum(np.maximum(a.min(0)-b.max(0),b.min(0)-a.max(0)),0)))
        if broad > .003:return dict(first=first[0],second=second[0]+'/'+second[1],separated=True,axis_gap_lower_bound_m=broad)
        ah,bh = ConvexHull(a),ConvexHull(b)
        axes = np.r_[ah.equations[:,:3],bh.equations[:,:3]]
        gap = float(np.maximum((a@axes.T).min(0)-(b@axes.T).max(0),
            (b@axes.T).min(0)-(a@axes.T).max(0)).max())
        overlap = False;lp_status = None
        if gap <= 1e-9:
            planes = np.r_[ah.equations,bh.equations]
            fit = linprog(np.zeros(3),A_ub=planes[:,:3],b_ub=-planes[:,3],bounds=[(None,None)]*3,method='highs')
            overlap = bool(fit.success);lp_status = int(fit.status)
        return dict(first=first[0],second=second[0]+'/'+second[1],separated=gap>1e-9 or lp_status==2,
            axis_gap_lower_bound_m=gap,convex_source_intersection=overlap,lp_status=lp_status)
    def family(name):return ''.join(c for c in name.split(':')[1].split('_')[0] if not c.isdigit())
    pairs = [compare(a,b) for a,b in combinations(transformed,2)
        if family(a[0]) != family(b[0]) and 'palm' not in (family(a[0]),family(b[0]))]
    neck = [compare(a,b) for a in transformed for b in guitar]
    return dict(finger_pairs=pairs,neck_pairs=neck,
        finger_convex_intersections=[r for r in pairs if r.get('convex_source_intersection')],
        neck_convex_intersections=[r for r in neck if r.get('convex_source_intersection')],
        non_target_neck_convex_intersections=[r for r in neck if r.get('convex_source_intersection')
            and r['first'] not in ('LH:middle3','LH:ring3')],
        scope='native source convex-hull static intersection; thumb_pad capsule uses conservative outer box; no cooked penetration/load/dynamic proof')


def references(search,q,out,candidate_valid):
    """동시 후보를 학습과 분리한 유한 속도 재생 요청각으로 저장한다."""
    qa = search.qa;initial = search.q0
    # 다른 전신 snapshot을 섞지 않고 움직이는 20축만 A 실측 기준에 옮긴다.
    known_path = STUDY/'입력/C2/known_press.json';search.pins[str(known_path)] = sha(known_path)
    bk = json.loads(known_path.read_text())['endpoint_states']['middle_s3_f8']
    qb = initial.copy();qb[np.r_[search.arm,search.middle]] = np.asarray(bk['press_q105'])[np.r_[search.arm,search.middle]]
    bh = qb.copy();bh[search.middle] = np.asarray(bk['arrival_q105'])[search.middle]
    schedules = {
        'C1':[(0.,initial),(2.8,initial),(3.,q),(4.45,q),(4.55,initial),(5.,initial)],
        'O1':[(0.,initial),(2.8,initial),(3.,qa),(3.8,qa),(4.,q),(4.95,q),
              (5.05,qa),(5.45,qa),(5.55,initial),(6.,initial)],
        'C2':[(0.,initial),(2.8,initial),(3.,q),(4.45,q),(4.55,initial),
              (5.25,bh),(5.5,qb),(6.95,qb),(7.05,bh),(7.5,bh)],
    }
    saved = {}
    for case,points in schedules.items():
        peaks = [float(1.875*np.abs(b-a).max()/(tb-ta)) for (ta,a),(tb,b) in zip(points,points[1:])]
        source = STUDY/'입력'/case/'catalog.json';pins = dict(search.pins);pins[str(source)] = sha(source)
        result = dict(schema='guitar_learning.complex_press_reference.v1',case_id=case,
            catalog_sha256=sha(source),source_sha256=pins,candidate_valid=bool(candidate_valid),native_verified=False,
            waypoints=[dict(time_s=t,q105=v.tolist()) for t,v in points],
            segment_quintic_peak_rate_rad_s=peaks,quintic_rate_within_4=all(x<=4. for x in peaks),
            active_indices=np.r_[search.arm,search.middle,search.ring].tolist(),
            expected_distal_neck_intersection=True,
            scope='CPU source-pad candidate and explicit request-angle replay only; no reset, teacher injection or native success certification',
            limitation='C2 B endpoint request uses recorded B arm/finger values in A calibrated frame; native transition proof required')
        path = out/(case+'_reference.json');write(path,result);saved[case] = dict(path=str(path),sha256=sha(path))
    return saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=STUDY/'검증/복합기하')
    args = parser.parse_args();out = args.out.resolve();out.relative_to(ROOT);out.mkdir(parents=True,exist_ok=False)
    search = Search();fixed = search.search();joint = []
    if not fixed[0]['measure']['both_geometry_candidate']:joint = search.search(free_arm=True)
    rows = fixed+joint;rows.sort(key=lambda r:(not r['measure']['both_geometry_candidate'],r['cost']))
    q = np.asarray(rows[0]['q105'])
    collision = collision_diagnostics(search,q)
    baseline_collision = collision_diagnostics(search,search.qa)
    write(out/'정적간섭진단.json',dict(completed=True,native_verified=False,
        common=collision,baseline_A_press=baseline_collision,
        limitation='겹침은 source convex 후보 간섭이며 native 접촉·안전 종료 결과로 확인해야 함'))
    valid = (rows[0]['measure']['both_geometry_candidate'] and not collision['finger_convex_intersections']
        and not collision['non_target_neck_convex_intersections'])
    reference = references(search,q,out,valid)
    result = dict(completed=True,native_verified=False,fk_reproduction_position_error_m=search.reproduction_error,
        fixed_arm_candidates=fixed,joint_candidates=joint,selected=rows[0],source_sha256=search.pins,references=reference,
        limitation='유효 굽힘면 끝마디 패드만. 정적 기하 후보; 하중·물리·유지·전환 안전 미검증')
    write(out/'후보탐색.json',result)
    print(json.dumps(dict(completed=True,both_geometry_candidate=rows[0]['measure']['both_geometry_candidate'],
        scope=rows[0]['scope'],out=str(out)),ensure_ascii=False))


if __name__ == '__main__':main()
