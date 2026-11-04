"""새 입력과 참조의 정적 FK/전체표면 오압현/source 교차를 CPU로 점검한다.

다른 연구의 Python은 실행하지 않는다. 실제 하중·동적 전환의 성공은 별도 native 검증이다.
"""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import torch
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
STUDY=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(path)

class Search:
    def __init__(self,case):
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        from guitar_learning.gpu.contact import load_fingertip_pad,finger_mesh_surface_samples,pad_contact_cells,wrong_press_sources
        from guitar_learning.gpu import environment
        from guitar_learning.core.control import target_rates
        self.case=case;folder=STUDY/'입력'/case
        self.cat=json.loads((folder/'catalog.json').read_text());self.row=self.cat['goals'][0]
        self.known=json.loads((folder/'known_press.json').read_text());provenance=json.loads((folder/'provenance.json').read_text())
        self.pins=dict(provenance['active_physical_inputs']);self.pins.update({str(folder/n):sha(folder/n) for n in ('catalog.json','known_press.json','provenance.json','manifest.json')})
        contract=load_gpu_prepared_reset_contract('left');self.pins.update(contract['source_sha256'])
        for f in (load_gpu_prepared_reset_contract,full_fk,load_fingertip_pad,finger_mesh_surface_samples,pad_contact_cells,wrong_press_sources,target_rates):
            path=Path(inspect.getsourcefile(f)).resolve();self.pins[str(path)]=sha(path)
        self.pins[str(Path(environment.__file__).resolve())]=sha(environment.__file__)
        self.pins[str(Path(__file__).resolve())]=sha(__file__)
        for name,expected in self.pins.items():
            if sha(name)!=expected:raise ValueError('원문 SHA 변경: '+name)
        self.names=self.cat['joint_names'];self.q0=np.asarray(self.row['q105']);self.state=self.row['state']
        self.fk=full_fk(SimpleNamespace(names=self.names,human_bodies=contract['initial']['human_body_names'],q_ref=self.q0),self.state)
        pose=self.state['guitar_body_states'][0]['pose'];self.gp=np.array([pose['p'][x] for x in 'xyz']);self.gr=Rotation.from_quat([pose['r'][x] for x in 'xyzw'])
        self.markers={n:self.gr.inv().apply(np.array([b['pose']['p'][x] for x in 'xyz'])-self.gp) for n,b in zip(contract['initial']['guitar_body_names'],self.state['guitar_body_states'])}
        self.starts=np.array([self.markers['G:string%d'%i] for i in range(1,7)]);self.ends=np.array([self.markers['G:string%d_end'%i] for i in range(1,7)])
        self.frets=np.array([self.markers['G:nut']]+[self.markers['G:fret%d'%i] for i in range(1,23)])
        from guitar_learning.gpu.contact import load_press_surface
        surface=load_press_surface([t['string'] for t in self.row['compiled_targets']],[t['fret'] for t in self.row['compiled_targets']]);self.pins.update(surface['source_sha256'])
        self.plane=np.array(surface['plane_G']);self.normal=self.plane[:3]/np.linalg.norm(self.plane[:3])
        self.pad=load_fingertip_pad();self.pins.update(self.pad['contract']['source_sha256']);self.cells=pad_contact_cells;self.wrong=wrong_press_sources
        self.fullnames=['LH:'+f+str(s) for f in ('thumb','index','middle','ring','pinky') for s in (2,3)]
        self.full,self.fullvalid=finger_mesh_surface_samples(self.fullnames);self.contact=environment.CONTACT_CONTRACT
        self.arm=np.array(self.cat['action_indices'][:12]);self.active=np.r_[self.arm,[i for f in self.row['target_fingers'] for i in range(52+4*f,56+4*f)]]
        self.lo=np.asarray(contract['initial']['native_PD_properties']['lower']);self.hi=np.asarray(contract['initial']['native_PD_properties']['upper'])
        for i,lo,hi in zip(self.cat['action_indices'],self.cat['action_lower'],self.cat['action_upper']):
            if i in self.arm:self.lo[i]=lo;self.hi[i]=hi
        self.rates=target_rates(self.names);self.rates[51:72]=4.

    def points(self,q):
        poses=self.fk(q);full=[];pads=[];normals=[]
        for n,p in zip(self.fullnames,self.full):
            position,rotation=poses[n];full.append(self.gr.inv().apply(position+rotation.apply(p)-self.gp))
        for i,f in enumerate(('index','middle','ring','pinky')):
            p,r=poses['LH:'+f+'3'];pads.append(self.gr.inv().apply(p+r.apply(self.pad['points_local'][i])-self.gp));normals.append(self.gr.inv().apply(r.apply(self.pad['normals_local'][i])))
        return np.array(full),np.array(pads),np.array(normals)

    def classify(self,q,targets,shift=(0.,0.,0.)):
        full,pads,normals=self.points(q);full=full+np.asarray(shift);pads=pads+np.asarray(shift);line=self.ends-self.starts
        frac=(full[:,:,None,1]-self.starts[None,None,:,1])/line[None,None,:,1];projection=self.starts[None,None]+frac[:,:,:,None]*line[None,None]
        lateral=np.abs(projection[:,:,:,0]-full[:,:,None,0]);nearest=lateral.argmin(-1);pick=nearest[:,:,None]
        best=np.take_along_axis(lateral,pick,2)[:,:,0];height=np.take_along_axis(full[:,:,None,2]-projection[:,:,:,2],pick,2)[:,:,0];fraction=np.take_along_axis(frac,pick,2)[:,:,0]
        unique=(lateral<=best[:,:,None]+1e-12).sum(-1)==1
        qualifies=self.fullvalid&unique&(fraction>=0)&(fraction<=1)&(best<=.003)&(abs(height)<=.003)
        low=np.minimum(self.frets[:-1,1],self.frets[1:,1]);high=np.maximum(self.frets[:-1,1],self.frets[1:,1])
        inside=(full[:,:,1,None]>low[None,None]+.002)&(full[:,:,1,None]<high[None,None]-.002);assigned=np.where(inside.any(-1),inside.argmax(-1)+1,0)
        def tensor(v,dtype=torch.float64):return torch.as_tensor(v,dtype=dtype)
        cells=self.cells(tensor(pads[None]),tensor(normals[None]),tensor(self.pad['valid'],torch.bool),torch.ones(1,4,dtype=torch.bool),tensor(self.starts[None]),tensor(self.ends[None]),tensor(self.frets[None]),tensor(self.plane))
        valid,frets,strings=[c.numpy()[0] for c in cells]
        positive=np.array([bool((valid[t['finger']-1]&(frets[t['finger']-1]==t['fret'])&(strings[t['finger']-1]==t['string'])).any()) for t in targets])
        m=len(targets);result=self.wrong(qualifies=tensor(qualifies.reshape(1,-1),torch.bool),assigned=tensor(assigned.reshape(1,-1),torch.long),nearest=tensor(nearest.reshape(1,-1),torch.long),source_fingers=torch.arange(5).repeat_interleave(2*full.shape[1]),surface_count=full.shape[1],pad_cells=cells,positive=tensor(positive[None],torch.bool),now=tensor([.5]),onset=tensor(np.zeros(m)),end=tensor(np.ones(m)),press=tensor(np.zeros(m)),scope=torch.ones(1,m,dtype=torch.bool),strings=tensor([t['string'] for t in targets],torch.long),frets=tensor([t['fret'] for t in targets],torch.long),fingers=tensor([t['finger'] for t in targets],torch.long),fret_count=23)
        return dict(positive=positive.tolist(),wrong=result['wrong'][0].tolist(),candidate_valid=bool(positive.all() and not result['wrong'].any()),loaded_assumed=True)


def collision_diagnostics(search,q,targets):
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
            if human and not ((name or '').startswith('LH:') or name=='L_Wrist'):continue
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
    def family(name):return ''.join(c for c in name.split(':')[-1].split('_')[0] if not c.isdigit())
    pairs = [compare(a,b) for a,b in combinations(transformed,2)
        if a[0].startswith('LH:') and b[0].startswith('LH:') and family(a[0]) != family(b[0]) and 'palm' not in (family(a[0]),family(b[0]))]
    neck = [compare(a,b) for a in transformed for b in guitar]
    return dict(finger_pairs=pairs,neck_pairs=neck,
        finger_convex_intersections=[r for r in pairs if r.get('convex_source_intersection')],
        neck_convex_intersections=[r for r in neck if r.get('convex_source_intersection')],
        non_target_neck_convex_intersections=[r for r in neck if r.get('convex_source_intersection')
            and r['first'] not in {'LH:'+('index','middle','ring','pinky')[t['finger']-1]+'3' for t in targets}],
        scope='native source convex-hull static intersection; thumb_pad capsule uses conservative outer box; no cooked penetration/load/dynamic proof')


def main():
    import importlib.util
    spec=importlib.util.spec_from_file_location('local_transition_inputs',STUDY/'도구/inputs.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    folder=STUDY/'입력/A0';cat,row,known,paths=module.load_verified(folder)
    reference_path=STUDY/'검증/참조/경로_v1/A0_reference.json';reference=json.loads(reference_path.read_text());search=Search('A0')
    assert row['target_fingers']==[2] and row['control_scope']=='arm_and_goals'
    assert [(t['string'],t['fret'],t['finger'],t['onset_s'],t['end_s']) for t in row['compiled_targets']]==[(2,5,2,3.,4.5),(3,8,2,5.5,7.)]
    assert row['duration_s']==7.5
    a=json.loads((module.SWEEP/module.A/'attempt01/arrival.json').read_text());assert a['state']==row['state'] and a['q105']==row['q105']
    task=module.make_task(Path(row['bundle']));assert task.duration_s==7.5 and len(task.targets)==2
    assert [(t.string,t.fret,t.finger,t.onset_s,t.end_s) for t in task.targets]==[(2,5,2,3.,4.5),(3,8,2,5.5,7.)]
    assert cat['joint_names']==search.names and reference['active_indices']==cat['action_indices'][:12]+list(range(60,64))
    endpoints=[]
    for index,wp_index in ((0,2),(1,6)):
        q=np.asarray(reference['waypoints'][wp_index]['q105']);target=row['compiled_targets'][index];metric=search.classify(q,[target]);c=collision_diagnostics(search,q,[target])
        endpoints.append(dict(target=target,time_s=reference['waypoints'][wp_index]['time_s'],metric=metric,finger_source_intersections=c['finger_convex_intersections'],non_target_neck_source_intersections=c['non_target_neck_convex_intersections'],target_neck_source_intersections=c['neck_convex_intersections']))
    trajectory=[];wp=reference['waypoints']
    for tm in (4.5,4.6,4.8,5.,5.2,5.3,5.4,5.5,7.,7.1):
        j=next(i for i in range(len(wp)-1) if wp[i]['time_s']<=tm<=wp[i+1]['time_s']);u=(tm-wp[j]['time_s'])/(wp[j+1]['time_s']-wp[j]['time_s']);f=10*u**3-15*u**4+6*u**5;q=(1-f)*np.asarray(wp[j]['q105'])+f*np.asarray(wp[j+1]['q105']);c=collision_diagnostics(search,q,row['compiled_targets'])
        target=row['compiled_targets'][0 if tm<=4.5 else 1];trajectory.append(dict(time_s=tm,metric=search.classify(q,[target]),finger_source_intersections=c['finger_convex_intersections'],non_target_neck_source_intersections=c['non_target_neck_convex_intersections']))
    pins=dict(search.pins);pins.update({str(p):sha(p) for p in paths});pins[str(reference_path)]=sha(reference_path)
    for p,h in pins.items():assert sha(p)==h,p
    checks=dict(actual_A_arrival_snapshot_exact=True,all105_q_and_state_exact=True,joint_order_exact=True,task_schedule_exact=True,full_length_s=task.duration_s,active_axes=16,source_pins_verified=len(pins),native_success_inherited=False)
    # 카탈로그를 복사한 뒤 SHA를 바꾸어 입력 변조 거부를 확인한다.
    import tempfile,shutil
    temporary=Path(tempfile.mkdtemp(prefix='변조검사_',dir=STUDY/'검증'))
    try:
        for name in ('catalog.json','known_press.json','manifest.json','provenance.json'):shutil.copy2(folder/name,temporary/name)
        d=json.loads((temporary/'catalog.json').read_text());d['goals'][0]['q105'][0]+=.01;(temporary/'catalog.json').write_text(json.dumps(d))
        try:module.load_verified(temporary)
        except ValueError:checks['tamper_rejected']=True
        else:raise AssertionError('변조 입력 허용')
    finally:shutil.rmtree(temporary)
    write(STUDY/'검증/입력CPU검증.json',dict(schema='middle_s3f5_s4f8_input_cpu.v1',completed=True,checks=checks,endpoints=endpoints,transition_samples=trajectory,reference_candidate_valid=reference['candidate_valid'],native_verified=False,source_sha256=pins,limitations=['원문 두 끝점은 별도 native 성공만 인증한다. 새로운 팔/기타 상태의 연결 경로와 하중은 fresh native에서 확인한다.','Source convex 교차는 실제 cooked collision·침투 깊이를 인증하지 않는다. 경로 source 검사는 명시된 이산 시점만 확인했다.','이상 FK에서 B는 A의 기타/몸체 기준에 oracle 활성16축만 이식한다. 나머지89축을 B원문으로 바꾸지 않는다.']))
    print(json.dumps(dict(completed=True,checks=checks,endpoints=[dict(metric=d['metric'],finger_intersections=len(d['finger_source_intersections']),non_target_neck_intersections=len(d['non_target_neck_source_intersections'])) for d in endpoints],transition=[dict(time_s=d['time_s'],finger_intersections=len(d['finger_source_intersections']),non_target_neck_intersections=len(d['non_target_neck_source_intersections'])) for d in trajectory]),ensure_ascii=False),flush=True)

if __name__=='__main__':main()
