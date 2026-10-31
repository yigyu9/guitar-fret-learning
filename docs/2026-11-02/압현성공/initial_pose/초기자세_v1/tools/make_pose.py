"""원준비 자세의 왼손 21축만 바꾸어 간섭을 줄인 대기 초기 상태를 만든다."""
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
from scipy.optimize import differential_evolution, minimize
from scipy.spatial.transform import Rotation
from scipy.spatial import ConvexHull
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
from guitar_learning.native.paths import HUMAN
from guitar_learning.gpu.finger_reward import B_PREPARATION_INPUT_DEGREES, B_PREPARATION_SPREAD_DEGREES

OUT = Path(__file__).resolve().parents[1]
FINGERS = ('thumb','index','middle','ring','pinky')


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')


def obj_vertices(path):
    import trimesh
    mesh = trimesh.load(str(path), force='mesh', process=False)
    return np.unique(mesh.vertices[np.unique(mesh.faces)], axis=0)



class PoseGeometry:
    """실제 사용 정점과 넥/줄을 덮는 볼록 형상의 분리 평면 간격 하한을 검사한다."""
    def __init__(self, contract):
        self.contract = contract
        self.names = contract['initial']['joint_names']
        self.state = contract['state']
        self.q0 = np.array([r['pos'] for r in self.state['human_dof_states']])
        self.fk = full_fk(SimpleNamespace(names=self.names,
            human_bodies=contract['initial']['human_body_names'],q_ref=self.q0),self.state)
        root = ET.parse(HUMAN)
        meshdir = HUMAN.parent/root.find('compiler').get('meshdir','')
        meshes = {m.get('name'):obj_vertices((meshdir/m.get('file')).resolve()) for m in root.findall('./asset/mesh') if m.get('name','').startswith('LH:')}
        self.parts = {}
        for body in root.iter('body'):
            name=body.get('name','')
            if not any(name.startswith('LH:'+f) for f in FINGERS): continue
            for geom in body.findall('geom'):
                if geom.get('type')=='mesh':
                    points=meshes[geom.get('mesh')]+np.fromstring(geom.get('pos','0 0 0'),sep=' ')
                    self.parts[name]=points
                elif geom.get('type')=='capsule':
                    # 양 끝점 구를 덮는 박스로 전체 캡슐을 보수적으로 포함한다.
                    ends=np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3);r=float(geom.get('size'))
                    corners=np.array(np.meshgrid(*[[-r,r]]*3)).T.reshape(-1,3)
                    self.parts[name]=(ends[:,None]+corners).reshape(-1,3)
        gp=self.state['guitar_body_states'][0]['pose']
        self.gp=np.array([gp['p'][a] for a in 'xyz']);self.gr=Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
        guitar_xml=Path(contract['initial']['loaded_assets'][1]['path'])
        gx=ET.parse(guitar_xml);folder=guitar_xml.parent/gx.find('compiler').get('meshdir','')
        gm={m.get('name'):(folder/m.get('file')).resolve() for m in gx.findall('./asset/mesh')}
        neck=obj_vertices(gm['guitar_neck1']);head=obj_vertices(gm['guitar_neck2'])
        neck_points=[neck];self.geometry_sources=list(gm[n] for n in ('guitar_neck1','guitar_neck2'))
        for body in gx.iter('body'):
            if body.get('name','').startswith('G:fret') or body.get('name')=='G:nut':
                for geom in body.findall('geom'):
                    if geom.get('type')=='box':
                        half=np.fromstring(geom.get('size'),sep=' ')
                        corners=np.array(np.meshgrid(*[[-h,h] for h in half])).T.reshape(-1,3)
                        neck_points.append(corners+np.fromstring(body.get('pos','0 0 0'),sep=' ')+np.fromstring(geom.get('pos','0 0 0'),sep=' '))
        markers={b.get('name'):np.fromstring(b.get('pos','0 0 0'),sep=' ') for b in gx.iter('body')}
        for k in range(1,7):
            a,b=markers['G:string%d'%k],markers['G:string%d_end'%k]
            for y in (neck[:,1].min(),neck[:,1].max()):
                point=a+(b-a)*(y-a[1])/(b[1]-a[1])
                # Include a conservative 0.5mm radius around rendered strings.
                corners=np.array(np.meshgrid(*[[-.0005,.0005]]*3)).T.reshape(-1,3)
                neck_points.append(point+corners)
        self.envelopes=[ConvexHull(np.vstack(neck_points)).equations,ConvexHull(head).equations]

    def gaps(self,q,finger):
        poses=self.fk(q);out={}
        for name,points in self.parts.items():
            if not name.startswith('LH:'+finger):continue
            p,r=poses[name];local=self.gr.inv().apply(p+r.apply(points)-self.gp)
            # Positive separating-plane distance is a conservative whole-mesh gap.
            gap=min(float(np.max(np.min(local@planes[:,:3].T+planes[:,3],axis=0))) for planes in self.envelopes)
            out[name]=gap
        return out

    def state_for(self,q):
        result=copy.deepcopy(self.state);poses=self.fk(q)
        for i,name in enumerate(self.names):
            if name.startswith('LH:'):
                result['human_dof_states'][i]=dict(pos=float(q[i]),vel=0.)
        for i,name in enumerate(self.contract['initial']['human_body_names']):
            if any(name.startswith('LH:'+f) for f in FINGERS):
                p,r=poses[name];result['human_body_states'][i]['pose']=dict(p=dict(zip('xyz',p.tolist())),r=dict(zip('xyzw',r.as_quat().tolist())))
                result['human_body_states'][i]['vel']=dict(linear=dict.fromkeys('xyz',0.),angular=dict.fromkeys('xyz',0.))
        return result


def main():
    c=load_prepared_reset_contract();geometry=PoseGeometry(c);q=geometry.q0.copy();names=geometry.names
    low=np.asarray(c['initial']['native_PD_properties']['lower']);high=np.asarray(c['initial']['native_PD_properties']['upper'])
    reports=[]
    for f in FINGERS:
        ids=[i for i,n in enumerate(names) if n.startswith('LH:'+f)]
        if f=='thumb':seed=np.radians([12,-35,30,30,15])
        else:
            k=FINGERS.index(f)-1;b=B_PREPARATION_INPUT_DEGREES[k]
            seed=np.radians([b[0],B_PREPARATION_SPREAD_DEGREES[k],b[1],b[2]])
        def trial(x):
            candidate=q.copy();candidate[ids]=x;return candidate
        initial_gaps=geometry.gaps(trial(seed),f)
        # Minimal departure from standby; 20mm search margin targets 10mm readback clearance.
        def cost(x):
            gaps=np.array(list(geometry.gaps(trial(x),f).values()))
            return 1e6*np.maximum(.020-gaps,0).dot(np.maximum(.020-gaps,0))+np.sum((x-seed)**2)
        bounds=list(zip(low[ids]+1e-6,high[ids]-1e-6))
        result=minimize(cost,np.clip(seed,low[ids]+1e-6,high[ids]-1e-6),bounds=bounds,method='L-BFGS-B')
        if min(geometry.gaps(trial(result.x),f).values())<.01:
            global_fit=differential_evolution(cost,bounds,seed=7,maxiter=100,popsize=8,polish=True)
            if global_fit.fun<result.fun:result=global_fit
        q[ids]=result.x
        reports.append(dict(finger=f,joint_names=[names[i] for i in ids],seed_degrees=np.degrees(seed).tolist(),
            requested_degrees=np.degrees(result.x).tolist(),seed_gap_lower_bound_m=initial_gaps,
            final_gap_lower_bound_m=geometry.gaps(q,f),minimum_gap_lower_bound_m=min(geometry.gaps(q,f).values())))
        print(f,reports[-1]['requested_degrees'],reports[-1]['minimum_gap_lower_bound_m'],flush=True)
    state=geometry.state_for(q);target=np.asarray(c['target105']).copy();finger_ids=[i for i,n in enumerate(names) if n.startswith('LH:')];target[finger_ids]=q[finger_ids]
    other=[i for i in range(105) if i not in finger_ids]
    assert np.array_equal(q[other],geometry.q0[other])
    assert all(state['human_dof_states'][i]==c['state']['human_dof_states'][i] for i in other)
    assert state['guitar_body_states']==c['state']['guitar_body_states'] and state['chair_body_states']==c['state']['chair_body_states']
    assert all(state['human_body_states'][i]==s for i,s in enumerate(c['state']['human_body_states']) if not any(c['initial']['human_body_names'][i].startswith('LH:'+f) for f in FINGERS))
    artifact=dict(schema='left_standby_initial.v1',diagnostic_only=True,joint_names=names,q105_rad=q.tolist(),target105_rad=target.tolist(),state=state,
        changed_joint_names=[names[i] for i in finger_ids],source_sha256=c['source_sha256'],geometry=dict(envelope_planes_G=[e.tolist() for e in geometry.envelopes],
        interpretation='Conservative separating-plane lower bound for whole finger source meshes and thumb capsule vs two convex envelopes enclosing neck/headstock/frets/nut/strings; not native collision-cooking certification'),fingers=reports)
    write(OUT/'initial_pose.json',artifact)
    write(OUT/'baseline_state.json',c['state'])
    write(OUT/'source_pins.json',{**c['source_sha256'],str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('minimum',min(r['minimum_gap_lower_bound_m'] for r in reports),flush=True)


if __name__=='__main__':main()
