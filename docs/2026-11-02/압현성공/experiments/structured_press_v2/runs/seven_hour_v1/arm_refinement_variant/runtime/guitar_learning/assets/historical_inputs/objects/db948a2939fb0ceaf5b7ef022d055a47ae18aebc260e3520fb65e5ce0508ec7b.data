"""Full upper native-calibrated FK and fixed-source geometry audit."""

import copy

from pathlib import Path

import xml.etree.ElementTree as ET

import numpy as np

from scipy.spatial.transform import Rotation

from .initial_pose_noise_v1 import pose

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

def capsule_witness(poses,normal):
    xml=ET.parse(ASSET).getroot();body=next(b for b in xml.iter('body') if b.get('name')=='R_Shoulder');geom=body.find('geom');a,b=np.fromstring(geom.get('fromto'),sep=' ').reshape(2,3);radius=float(geom.get('size'))
    p,r=poses['R_Shoulder'];ends=np.array([p+r.apply(a),p+r.apply(b)]);end=ends[np.argmin(ends@normal)]
    return end-radius*normal


from .paths import ROOT, A
ASSET=A/"assets/humanoid_fixed_lower.xml"
