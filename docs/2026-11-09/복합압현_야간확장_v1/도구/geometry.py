"""야간 복합 과제의 공통 팔·손가락 요청각을 현재 활성 FK로 찾는다.

패드와 전체 virtual-string 오압현은 하중을 모두 참으로 가정해 검사한다.
기하 후보·source 교차·속도 검사는 native 압현이나 접촉 부하의 인증이 아니다.
"""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='1'
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import least_squares,linprog
from scipy.spatial import ConvexHull
from scipy.spatial.transform import Rotation
import torch
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
STUDY=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temp.replace(path)


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

    def classify(self,q,targets):
        full,pads,normals=self.points(q);line=self.ends-self.starts
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

    def solve(self,targets):
        fingers=[t['finger'] for t in targets];indices=np.r_[self.arm,[i for f in fingers for i in range(52+4*f,56+4*f)]]
        center=[]
        for t in targets:
            y=np.mean(self.frets[t['fret']-1:t['fret']+1,1]);start=self.starts[t['string']];line=self.ends[t['string']]-start;p=start+(y-start[1])/line[1]*line
            p[2]=-(p[:2]@self.plane[:2]+self.plane[3])/self.plane[2];center.append(p-.0005*self.normal)
        seed=self.q0.copy()
        for t in targets:
            endpoint=next(v for k,v in self.known['endpoint_states'].items() if k==('index','middle','ring','pinky')[t['finger']-1]+'_s%d_f%d'%(t['string']+1,t['fret']))
            seed[52+4*t['finger']:56+4*t['finger']]=endpoint['finger4_rad']
        seeds=[seed.copy(),seed.copy()];seeds[1][self.arm]=np.mean([np.asarray(v['press_q105'])[self.arm] for v in self.known['endpoint_states'].values()],axis=0)
        candidates=[]
        for seed in seeds:
            _,pads,_=self.points(seed);selected=[int(np.linalg.norm(pads[t['finger']-1]-p,axis=1).argmin()) for t,p in zip(targets,center)]
            def residual(values):
                q=self.q0.copy();q[indices]=values;full,pads,normals=self.points(q);parts=[]
                for t,p,j in zip(targets,center,selected):
                    finger=t['finger']-1;parts.extend(1000*(pads[finger,j]-p));parts.append(10*max(.2+normals[finger,j]@self.normal,0))
                    start=self.starts[t['string']];line=self.ends[t['string']]-start;fraction=(full[:,:,1]-start[1])/line[1];projection=start+fraction[:,:,None]*line
                    clearance=np.maximum(abs(full[:,:,0]-projection[:,:,0])-.003,abs(full[:,:,2]-projection[:,:,2])-.003)
                    foreign=np.repeat(np.arange(5),2)[:,None]!=t['finger'];higher=full[:,:,1]<self.frets[t['fret'],1]-.002
                    parts.extend((1200*np.maximum(.0004-clearance,0)*foreign*higher*self.fullvalid).ravel())
                parts.extend(.3*(q[self.arm]-self.q0[self.arm]))
                return np.array(parts)
            fit=least_squares(residual,np.clip(seed[indices],self.lo[indices]+1e-10,self.hi[indices]-1e-10),bounds=(self.lo[indices],self.hi[indices]),max_nfev=100)
            q=self.q0.copy();q[indices]=fit.x;candidates.append(dict(q105=q.tolist(),metric=self.classify(q,targets),cost=float(fit.cost),nfev=int(fit.nfev)))
        candidates.sort(key=lambda c:(not c['metric']['candidate_valid'],c['cost']))
        return candidates

    def release(self,q,fingers,holding=()):
        indices=self.active;half=np.array([.12 if i in self.arm else .18 for i in indices]);low=np.maximum(self.lo[indices],q[indices]-half);high=np.minimum(self.hi[indices],q[indices]+half)
        _,original,_=self.points(q)
        def residual(values):
            trial=q.copy();trial[indices]=values;_,pads,_=self.points(trial);height=pads[np.array(fingers)-1]@self.normal+self.plane[3]
            preserve=(1000*(pads[np.array(holding,dtype=int)-1]-original[np.array(holding,dtype=int)-1])).ravel() if holding else []
            return np.r_[1000*np.maximum(.004-height,0).ravel(),preserve,.01*(values-q[indices])]
        fit=least_squares(residual,np.clip(q[indices],low+1e-10,high-1e-10),bounds=(low,high),max_nfev=80)
        trial=q.copy();trial[indices]=fit.x;return trial


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



def run(case,out):
    search=Search(case);targets=search.row['compiled_targets'];groups=[]
    for onset in sorted({t['onset_s'] for t in targets}):
        active=[t for t in targets if t['onset_s']<=onset<t['end_s']]
        candidates=search.solve(active);groups.append(dict(onset_s=onset,end_s=min(t['end_s'] for t in active),targets=active,candidates=candidates,selected=candidates[0]))
    valid=all(g['selected']['metric']['candidate_valid'] for g in groups);points=[(0.,search.q0),(.5,search.q0)];previous=None
    for group in groups:
        collision=collision_diagnostics(search,np.asarray(group['selected']['q105']),group['targets'])
        group['collision']=collision
        valid=valid and not collision['finger_convex_intersections'] and not collision['non_target_neck_convex_intersections']
    for group in groups:
        q=np.asarray(group['selected']['q105']);onset=group['onset_s'];end=group['end_s']
        points.extend([(onset-.5 if previous is None else onset-.2,q),(end,q)])
        release=search.release(q,[t['finger'] for t in group['targets']]);points.append((end+.1,release));previous=group
    points.append((search.row['duration_s'],points[-1][1]));points.sort(key=lambda p:p[0])
    reason=None
    if case=='N10':
        a,b=[np.asarray(g['selected']['q105']) for g in groups]
        first_release=search.release(a,[3],holding=[2]);second_hover=search.release(b,[4],holding=[2]);final=search.release(b,[2,4])
        points=[(0.,search.q0),(.5,search.q0),(2.5,a),(4.5,a),(4.6,first_release),(5.3,second_hover),(5.5,b),(7.,b),(7.1,final),(7.5,final)]
    if case=='N11':
        together=np.asarray(groups[1]['selected']['q105']);single=search.release(together,[2],holding=[1]);final=search.release(single,[1])
        points=[(0.,search.q0),(.5,search.q0),(2.5,single),(3.7,single),(4.,together),(5.,together),(5.1,single),(5.5,single),(5.6,final),(6.,final)]
    hold_checks=[]
    if case in ('N10','N11'):
        hold=targets[0]
        for now in np.linspace(3.,hold['end_s'],61):
            for (ta,a),(tb,b) in zip(points,points[1:]):
                if ta<=now<=tb:
                    x=(now-ta)/(tb-ta);w=x*x*x*(10-15*x+6*x*x);q=a+w*(b-a);break
            metric=search.classify(q,[hold]);hold_checks.append(dict(time_s=float(now),candidate_valid=metric['candidate_valid']))
        if not all(x['candidate_valid'] for x in hold_checks):
            valid=False;reason='연속 유지 담당음의 정적 경로 표본 중 접촉/오압현 기준 미달'
    rates=[float((1.875*abs(b[search.active]-a[search.active])/((tb-ta)*search.rates[search.active])).max()) for (ta,a),(tb,b) in zip(points,points[1:]) if tb>ta]
    native_limits=all(np.all(q[search.active]>=search.lo[search.active]-1e-6) and np.all(q[search.active]<=search.hi[search.active]+1e-6) for _,q in points)
    valid=valid and native_limits and all(r<=1.+1e-6 for r in rates)
    # source 교차 미검증은 후보를 native 인증으로 승격하지 않는다.
    reference=dict(schema='guitar_learning.complex_press_night_reference.v1',case_id=case,catalog_sha256=sha(STUDY/'입력'/case/'catalog.json'),source_sha256=search.pins,candidate_valid=bool(valid),native_verified=False,active_indices=search.active.tolist(),waypoints=[dict(time_s=t,q105=q.tolist()) for t,q in points],segment_peak_rate_ratio=rates,source_collision_verified=True,scope='CPU current pad/full virtual-string all-loaded candidate with source convex endpoints; native load/transition must be checked separately')
    folder=out/case;folder.mkdir(parents=True,exist_ok=False);write(folder/'reference.json',reference);write(folder/'검증.json',dict(completed=True,case_id=case,candidate_valid=bool(valid),groups=groups,reason=reason,hold_path_checks=hold_checks,native_limits_valid=bool(native_limits),rates=rates,native_verified=False,reference_sha256=sha(folder/'reference.json')))
    return dict(case_id=case,candidate_valid=bool(valid),reference=str(folder/'reference.json'),reason=reason)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cases',nargs='+',default=['A0']+['N%02d'%i for i in range(1,13)]);parser.add_argument('--out',type=Path,default=STUDY/'검증/기하/후보_v1');args=parser.parse_args();out=args.out.resolve();out.relative_to(ROOT);out.mkdir(parents=True,exist_ok=True)
    results=[]
    for case in args.cases:
        result=run(case,out);results.append(result);write(out/'진행.json',dict(completed=False,results=results));print(json.dumps(result,ensure_ascii=False),flush=True)
    write(out/'진행.json',dict(completed=True,results=results))
