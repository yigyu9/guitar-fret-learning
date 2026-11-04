"""약지의 인접 S3/F7 오압현 표본을 피하는 다른 동시 압현 후보를 찾는다.

담당 패드만 보는 기존 후보와 달리 현행 전체 표면 virtual-string 분류도
검사한다. body load는 예측할 수 없어 전부 loaded로 두는 보수적 CPU 대조다.
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
import torch

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
sys.path.insert(0,str(ROOT))
STUDY=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n');temporary.replace(path)


class Search:
    def __init__(self):
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        from guitar_learning.gpu.contact import load_fingertip_pad,finger_mesh_surface_samples,pad_contact_cells,wrong_press_sources
        from guitar_learning.gpu.environment import CONTACT_CONTRACT
        from guitar_learning.tool.validation.press_acquisition import source_geometry
        contract=load_gpu_prepared_reset_contract('left');self.pins=dict(contract['source_sha256'])
        for f in (load_gpu_prepared_reset_contract,full_fk,load_fingertip_pad,finger_mesh_surface_samples,pad_contact_cells,wrong_press_sources,source_geometry):
            p=Path(inspect.getsourcefile(f)).resolve();self.pins[str(p)]=sha(p)
        from guitar_learning.gpu import environment
        self.pins[str(Path(environment.__file__).resolve())]=sha(environment.__file__)
        self.contact=dict(CONTACT_CONTRACT);self.pad_cells=pad_contact_cells;self.wrong_sources=wrong_press_sources
        folder=STUDY/'입력/C1';cat=json.loads((folder/'catalog.json').read_text());prov=json.loads((folder/'provenance.json').read_text())
        self.pins.update(prov['active_physical_inputs'])
        for name in ('catalog.json','known_press.json','provenance.json','manifest.json'):
            self.pins[str(folder/name)]=sha(folder/name)
        row=cat['goals'][0];self.initial=np.asarray(row['q105']);self.state=row['state'];self.names=cat['joint_names']
        self.fk=full_fk(SimpleNamespace(names=self.names,human_bodies=contract['initial']['human_body_names'],q_ref=self.initial),self.state)
        gp=self.state['guitar_body_states'][0]['pose'];self.gp=np.array([gp['p'][a] for a in 'xyz']);self.gr=Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
        self.markers={name:self.gr.inv().apply(np.array([body['pose']['p'][a] for a in 'xyz'])-self.gp)
            for name,body in zip(contract['initial']['guitar_body_names'],self.state['guitar_body_states'])}
        self.starts=np.array([self.markers['G:string%d'%i] for i in range(1,7)])
        self.ends=np.array([self.markers['G:string%d_end'%i] for i in range(1,7)])
        self.frets=np.array([self.markers['G:nut']]+[self.markers['G:fret%d'%i] for i in range(1,23)])
        self.full_bodies=['LH:'+f+str(s) for f in ('thumb','index','middle','ring','pinky') for s in (2,3)]
        self.full,self.full_valid=finger_mesh_surface_samples(self.full_bodies)
        self.pad=load_fingertip_pad();self.pins.update(self.pad['contract']['source_sha256'])
        starts,ends,low,high,self.plane,surface=source_geometry(contract,[dict(string=2,fret=6),dict(string=1,fret=7)])
        self.pins.update(surface['source_sha256']);self.normal=self.plane[:3]/np.linalg.norm(self.plane[:3])
        self.goals=[]
        for string,lo,hi in zip((2,1),low,high):
            line=ends[string]-starts[string];center=starts[string]+((lo+hi)/2-starts[string,1])/line[1]*line
            self.goals.append(dict(start=starts[string],line=line,low=lo+.002,high=hi-.002,center=center))
        self.lower=np.asarray(contract['initial']['native_PD_properties']['lower'])
        self.upper=np.asarray(contract['initial']['native_PD_properties']['upper'])
        self.lo=self.lower[64:68];self.hi=self.upper[64:68];self.arm=np.array(cat['action_indices'][:12])
        self.active=np.r_[self.arm,np.arange(60,68)]
        for i,lo,hi in zip(cat['action_indices'],cat['action_lower'],cat['action_upper']):
            if i in self.arm:self.lower[i]=lo;self.upper[i]=hi
        baseline=STUDY/'검증/복합기하/탐색_v4/후보탐색.json';self.pins[str(baseline)]=sha(baseline)
        doc=json.loads(baseline.read_text());self.pins.update(doc['source_sha256']);self.old=np.asarray(doc['selected']['q105'])
        self.pins[str(Path(__file__).resolve())]=sha(__file__)
        for name,expected in self.pins.items():
            if sha(name)!=expected:raise ValueError('입력 SHA 불일치: '+name)

    def points(self,q):
        poses=self.fk(q);full=[];pads=[];normals=[]
        for name,local in zip(self.full_bodies,self.full):
            p,r=poses[name];full.append(self.gr.inv().apply(p+r.apply(local)-self.gp))
        for i,name in enumerate(('index','middle','ring','pinky')):
            p,r=poses['LH:'+name+'3'];pads.append(self.gr.inv().apply(p+r.apply(self.pad['points_local'][i])-self.gp))
            normals.append(self.gr.inv().apply(r.apply(self.pad['normals_local'][i])))
        return np.array(full),np.array(pads),np.array(normals)

    def full_cells(self,points):
        line=self.ends-self.starts
        fraction=(points[:,:,None,1]-self.starts[None,None,:,1])/line[None,None,:,1]
        projected=self.starts[None,None]+fraction[:,:,:,None]*line[None,None]
        lateral=np.abs(projected[:,:,:,0]-points[:,:,None,0]);nearest=lateral.argmin(-1)
        best=np.take_along_axis(lateral,nearest[:,:,None],axis=2)[:,:,0]
        height=np.take_along_axis(points[:,:,None,2]-projected[:,:,:,2],nearest[:,:,None],axis=2)[:,:,0]
        frac=np.take_along_axis(fraction,nearest[:,:,None],axis=2)[:,:,0]
        unique=(lateral<=best[:,:,None]+1e-12).sum(-1)==1
        qualifies=self.full_valid&unique&(frac>=0)&(frac<=1)&(best<=self.contact['lateral_max_m'])&(np.abs(height)<=self.contact['height_abs_max_m'])
        low=np.minimum(self.frets[:-1,1],self.frets[1:,1]);high=np.maximum(self.frets[:-1,1],self.frets[1:,1]);margin=self.contact['fret_cell_margin_m']
        interior=(points[:,:,1,None]>low[None,None]+margin)&(points[:,:,1,None]<high[None,None]-margin)
        assigned=np.where(interior.any(-1),interior.argmax(-1)+1,0)
        return qualifies,assigned,nearest

    def measure(self,q):
        full,pads,normals=self.points(q);qualifies,assigned,nearest=self.full_cells(full)
        def tensor(a,dtype=torch.float64):return torch.as_tensor(a,dtype=dtype)
        pad_cells=self.pad_cells(tensor(pads[None]),tensor(normals[None]),tensor(self.pad['valid'],torch.bool),
            torch.ones(1,4,dtype=torch.bool),tensor(self.starts[None]),tensor(self.ends[None]),tensor(self.frets[None]),tensor(self.plane))
        pad_valid,pad_fret,pad_string=[x.numpy()[0] for x in pad_cells]
        positive=np.array([bool((pad_valid[f]& (pad_fret[f]==fr)&(pad_string[f]==st)).any()) for f,st,fr in [(1,2,6),(2,1,7)]])
        wrong=self.wrong_sources(qualifies=tensor(qualifies.reshape(1,-1),torch.bool),
            assigned=tensor(assigned.reshape(1,-1),torch.long),nearest=tensor(nearest.reshape(1,-1),torch.long),
            source_fingers=torch.arange(5).repeat_interleave(2*full.shape[1]),surface_count=full.shape[1],
            pad_cells=tuple(tensor(x[None],torch.bool if i==0 else torch.long) for i,x in enumerate((pad_valid,pad_fret,pad_string))),
            positive=tensor(positive[None],torch.bool),now=tensor([3.5]),onset=tensor([3.,3.]),end=tensor([4.5,4.5]),
            press=tensor([3.,3.]),scope=torch.ones(1,2,dtype=torch.bool),strings=tensor([2,1],torch.long),
            frets=tensor([6,7],torch.long),fingers=tensor([2,3],torch.long),fret_count=23)
        bad=qualifies[7]&(assigned[7]>6)&(nearest[7]==2)
        return dict(both_positive=bool(positive.all()),positive=positive.tolist(),wrong=wrong['wrong'][0].tolist(),
            ring3_higher_S3_samples=np.flatnonzero(bad).tolist(),
            ring3_higher_S3_points_G_m=full[7,bad].tolist(),
            wrong_flags=wrong['flags'][0].tolist(),all_loaded_assumption=True)

    def avoidance(self,full):
        ring=full[6:8].reshape(-1,3);start=self.starts[2];line=self.ends[2]-start
        fraction=(ring[:,1]-start[1])/line[1];projected=start+fraction[:,None]*line
        dx=np.abs(ring[:,0]-projected[:,0]);height=np.abs(ring[:,2]-projected[:,2])
        relevant=(ring[:,1]<self.frets[6,1]-.002)&(ring[:,1]>self.frets[14,1]+.002)
        return np.maximum(.0005-np.maximum(dx-.003,height-.003),0)*relevant

    def candidates(self):
        seeds=[self.old[64:68],self.initial[64:68],(self.lo+self.hi)/2]
        candidates=[]
        for seed in seeds:
            q=self.old.copy();q[64:68]=seed;_,pads,_=self.points(q)
            selected=int(np.linalg.norm(pads[2]-self.goals[1]['center'],axis=1).argmin())
            for offset in (0.,.0015,.0025):
                for depth in (-.0005,.0005,.0015):
                    target=self.goals[1]['center'].copy();target[0]+=offset;target-=depth*(-self.normal)
                    def residual(value):
                        q=self.old.copy();q[64:68]=value;full,pad,normals=self.points(q)
                        # 분류 경계보다 0.5mm 여유: lateral 또는 height에서 벗어나야 한다.
                        return np.r_[1000*(pad[2,selected]-target),1500*self.avoidance(full),
                            10*max(.2+normals[2,selected]@self.normal,0),.001*(value-self.old[64:68])]
                    fit=least_squares(residual,np.clip(seed,self.lo+1e-10,self.hi-1e-10),bounds=(self.lo,self.hi),max_nfev=100)
                    q=self.old.copy();q[64:68]=fit.x;metric=self.measure(q)
                    candidates.append(dict(q105=q.tolist(),finger4_rad=fit.x.tolist(),nfev=int(fit.nfev),cost=float(fit.cost),
                        goal_x_offset_m=offset,goal_signed_height_m=depth,metric=metric,native_verified=False))
        candidates.sort(key=lambda r:(not r['metric']['both_positive'],sum(r['metric']['wrong']),
            len(r['metric']['ring3_higher_S3_samples']),r['cost']))
        return candidates

    def joint_candidates(self,fixed):
        seeds=[np.asarray(fixed[0]['q105']),self.old.copy()]
        candidates=[]
        for seed in seeds:
            _,pads,_=self.points(seed)
            selected=[int(np.linalg.norm(pads[f]-g['center'],axis=1).argmin()) for f,g in zip((1,2),self.goals)]
            for ring_offset in (.0015,.0025):
                targets=[g['center']-.0005*self.normal for g in self.goals];targets[1][0]+=ring_offset
                def residual(values):
                    q=self.old.copy();q[self.active]=values;full,pad,normals=self.points(q)
                    return np.r_[1000*(pad[1,selected[0]]-targets[0]),1000*(pad[2,selected[1]]-targets[1]),
                        1800*self.avoidance(full),20*max(.1-q[67],0),5*max(q[66]-1.45,0),
                        .3*(q[self.arm]-self.old[self.arm]),.005*(q[60:68]-self.old[60:68])]
                fit=least_squares(residual,np.clip(seed[self.active],self.lower[self.active]+1e-10,self.upper[self.active]-1e-10),
                    bounds=(self.lower[self.active],self.upper[self.active]),max_nfev=120)
                q=self.old.copy();q[self.active]=fit.x
                candidates.append(dict(q105=q.tolist(),finger4_rad=q[64:68].tolist(),nfev=int(fit.nfev),cost=float(fit.cost),
                    scope='arm12+middle4+ring4; non-active q preserved; soft DIP margin for geometry search only',
                    metric=self.measure(q),native_verified=False))
        return candidates

    def release(self,q,which):
        """원래 압현각에서 조금 이동해 유효 패드 접촉을 해제하는 정적 후보를 찾는다."""
        fingers=(1,2) if which=='both' else (2,)
        indices=self.active if which=='both' else np.arange(64,68)
        half=np.array([.12 if i in self.arm else .18 for i in indices])
        low=np.maximum(self.lower[indices],q[indices]-half)
        high=np.minimum(self.upper[indices],q[indices]+half)
        def residual(values):
            trial=q.copy();trial[indices]=values;_,pads,_=self.points(trial)
            heights=pads[list(fingers)]@self.normal+self.plane[3]
            return np.r_[1000*np.maximum(.004-heights,0).ravel(),.01*(values-q[indices])]
        seeds=[q[indices],np.clip(self.initial[indices],low+1e-10,high-1e-10)]
        for seed in seeds:
            fit=least_squares(residual,np.clip(seed,low+1e-10,high-1e-10),bounds=(low,high),max_nfev=100)
            trial=q.copy();trial[indices]=fit.x
            _,pads,normals=self.points(trial)
            valid,_,_=self.pad_cells(torch.tensor(pads[None]),torch.tensor(normals[None]),torch.tensor(self.pad['valid']),
                torch.ones(1,4,dtype=torch.bool),torch.tensor(self.starts[None]),torch.tensor(self.ends[None]),
                torch.tensor(self.frets[None]),torch.tensor(self.plane))
            if not bool(valid[0,list(fingers)].any()):return trial
        raise ValueError('0.1초·관절속도 범위에서 정적 패드 해제 후보 미확보: '+which)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,default=STUDY/'검증/복합기하/후보개선_v1')
    args=parser.parse_args();out=args.out.resolve();out.relative_to(ROOT);out.mkdir(parents=True,exist_ok=True)
    if (out/'CPU검증.json').exists() and json.loads((out/'CPU검증.json').read_text()).get('completed'):
        raise FileExistsError('완성한 후보판본은 덮어쓰지 않음')
    write(out/'CPU검증.json',dict(completed=False,reason='원자적 완료 표시 전 후보·참조·속도 검증 진행 중'))
    search=Search();baseline=search.measure(search.old);write(out/'기존후보기하.json',dict(completed=True,metric=baseline,source_sha256=search.pins))
    fixed=search.candidates();joint=search.joint_candidates(fixed);candidates=fixed+joint
    candidates.sort(key=lambda r:(not r['metric']['both_positive'],sum(r['metric']['wrong']),
        max(.05-r['q105'][67],0)>0,r['cost']))
    best=candidates[0]
    valid=best['metric']['both_positive'] and not any(best['metric']['wrong'])
    references={};reference_validity={}
    if valid:
        from guitar_learning.core.control import target_rates
        q=np.asarray(best['q105']);rates=target_rates(search.names);rates[51:72]=4.
        release=search.release(q,'both');ring_release=search.release(q,'ring')
        qa=q.copy();qa[64:68]=search.initial[64:68]
        known_path=STUDY/'입력/C2/known_press.json';known=json.loads(known_path.read_text())
        b=known['endpoint_states']['middle_s3_f8'];bh=search.initial.copy();bp=search.initial.copy()
        for trial,key in ((bh,'arrival_q105'),(bp,'press_q105')):trial[search.active]=np.asarray(b[key])[search.active]
        schedules={
            'C1':[(0.,search.initial),(.5,search.initial),(2.5,q),(4.5,q),(4.6,release),(5.,release)],
            'O1':[(0.,search.initial),(.5,search.initial),(2.5,qa),(3.7,qa),(4.,q),(5.,q),
                  (5.1,ring_release),(5.5,ring_release),(5.6,release),(6.,release)],
            'C2':[(0.,search.initial),(.5,search.initial),(2.5,q),(4.5,q),(4.6,release),
                  (5.3,bh),(5.4,bp),(7.,bp),(7.1,bh),(7.5,bh)]}
        for case in ('C1','O1','C2'):
            original=STUDY/'검증/복합기하/탐색_v4'/(case+'_reference.json')
            ref=json.loads(original.read_text());ref['source_sha256'].update(search.pins);ref['source_sha256'][str(original)]=sha(original)
            ref['source_sha256'][str(known_path)]=sha(known_path)
            ref['waypoints']=[dict(time_s=t,q105=v.tolist()) for t,v in schedules[case]]
            ratios=[float((1.875*np.abs(b[search.active]-a[search.active])/((tb-ta)*rates[search.active])).max())
                for (ta,a),(tb,b) in zip(schedules[case],schedules[case][1:])]
            peaks=[float((1.875*np.abs(b[search.active]-a[search.active])/(tb-ta)).max())
                for (ta,a),(tb,b) in zip(schedules[case],schedules[case][1:])]
            action_valid=all(np.all(v[search.active]>=search.lower[search.active]-1e-6) and
                np.all(v[search.active]<=search.upper[search.active]+1e-6) for _,v in schedules[case])
            reference_validity[case]=action_valid and all(r<=1.+1e-6 for r in ratios)
            ref.update(native_verified=False,candidate_valid=reference_validity[case],
                segment_quintic_peak_rate_ratio=ratios,segment_quintic_peak_rate_rad_s=peaks,
                quintic_rate_within_4=all(r<=1.+1e-6 for r in ratios),
                scope='refined arm12+middle4+ring4 avoids all-loaded exact virtual-string wrong source; no native success certification')
            path=out/(case+'_reference.json');write(path,ref);references[case]=dict(path=str(path),sha256=sha(path))
    write(out/'후보탐색.json',dict(completed=True,source_sha256=search.pins,candidate_valid=bool(valid),
        baseline=baseline,selected=best,candidates=candidates,references=references,native_verified=False,
        limitation='actual active pad and wrong-source classifiers with all bodies loaded; no dynamic load, collision, pressure or stability certification'))
    complete=valid and set(reference_validity)=={'C1','O1','C2'} and all(reference_validity.values())
    write(out/'CPU검증.json',dict(completed=bool(complete),candidate_valid=bool(valid),generator_sha256=sha(__file__),
        reference_validity=reference_validity,
        source_sha256=search.pins,references=references,native_verified=False,
        wrong_geometry_uses_actual_unprojected_strings=True,
        all_loaded_assumption=True,load_limitation='middle native distal load was zero in C1 v1; static positive cannot establish body load',
        original_v4_preserved=True))
    print(json.dumps(dict(completed=True,candidate_valid=bool(valid),baseline_wrong=baseline['wrong'],selected=best['metric'],references=references),ensure_ascii=False))


if __name__=='__main__':main()
