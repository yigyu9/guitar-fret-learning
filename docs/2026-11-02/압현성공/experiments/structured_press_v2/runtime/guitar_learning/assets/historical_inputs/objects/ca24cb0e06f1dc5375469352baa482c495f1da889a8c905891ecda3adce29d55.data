"""Full upper native-calibrated FK and fixed-source geometry audit."""
import copy
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import pose
ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'stability_adapter_2/assets/humanoid_fixed_lower.xml'

def calibrated_upper_fk(names,bodies,state,q0):
    xml=ET.parse(ASSET).getroot();parents={c.get('name'):p.get('name') for p in xml.iter('body') for c in p.findall('body')}
    original={n:pose(s) for n,s in zip(bodies,state['human_body_states'])};rows=[]
    for body in next(b for b in xml.iter('body') if b.get('name')=='Torso').iter('body'):
        n=body.get('name');parent=parents[n]
        if n not in original:continue
        pp,pr=original[parent];bp,br=original[n];idx=[names.index(j.get('name')) for j in body.findall('joint')]
        basis=np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in body.findall('joint')]) if idx else np.zeros((3,0))
        relative=pr.inv()*br;zero=Rotation.from_rotvec(basis@q0[idx]).inv()*relative if idx else relative
        rows.append((n,parent,pr.inv().apply(bp-pp),zero,basis,idx))
    def fk(q):
        poses=dict(original)
        for n,parent,t,zero,basis,idx in rows:
            pp,pr=poses[parent];rel=Rotation.from_rotvec(basis@q[idx])*zero if idx else zero
            poses[n]=(pp+pr.apply(t),pr*rel)
        return poses
    return fk,parents

def state_from_fk(state,bodies,q,fk):
    out=copy.deepcopy(state)
    for n,(p,r) in fk(q).items():out['human_body_states'][bodies.index(n)]['pose']={'p':dict(zip('xyz',p.tolist())),'r':dict(zip('xyzw',r.as_quat().tolist()))}
    for s,v in zip(out['human_dof_states'],q):s['pos']=float(v)
    return out

def source_audit(state,bodies,parents):
    from .underneck_initial_search import source_scene
    from .initial_overlap import build_probe
    from .palm_side_source_checks import source_checks,intersection
    gp,gr=pose(state['guitar_body_states'][0]);scene,_=source_scene(state,{'human_body_names':bodies},gp,gr);probe=build_probe(scene);meshes,overlap,cross=source_checks(probe)
    def distance(a,b):
        chain=[]
        while a in parents:chain.append(a);a=parents[a]
        chain.append(a);steps=0
        while b not in chain and b in parents:steps+=1;b=parents[b]
        return steps+chain.index(b) if b in chain else 99
    human=[s for s in probe[2] if s['actor']=='human'];selfcross=[]
    changed=lambda n:n in ('Torso','Spine','Chest','Neck','Head') or n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:'))
    for i,a in enumerate(human):
        for b in human[i+1:]:
            if not(changed(a['body']) or changed(b['body'])) or distance(a['body'],b['body'])<=2:continue
            radius=intersection(meshes[a['geom_id']],meshes[b['geom_id']])
            if radius>1e-7:selfcross.append({'a':a['body'],'b':b['body'],'common_radius_m':radius})
    return {'source_clear':not(overlap or cross or selfcross),'human_guitar_overlap':overlap,'crosshands':cross,'nonadjacent_human_overlap':selfcross}

def capsule_witness(poses,normal):
    xml=ET.parse(ASSET).getroot();body=next(b for b in xml.iter('body') if b.get('name')=='R_Shoulder');geom=body.find('geom');a,b=np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3);radius=float(geom.get('size'))
    p,r=poses['R_Shoulder'];ends=np.array([p+r.apply(a),p+r.apply(b)]);end=ends[np.argmin(ends@normal)]
    return end-radius*normal
