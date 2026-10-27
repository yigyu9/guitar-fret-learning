"""t0-calibrated left FK with explicit two-axis rotation-product hypotheses."""
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[1]
def left_fk(names,bodies,initial,q0,two_axis_mode):
    if two_axis_mode not in ('exp_sum','xml_product','reverse_product'):raise ValueError('unknown two-axis hypothesis')
    from .build_fixed_lower_asset import pose
    xml=ET.parse(ROOT/'tab2body/assets/smpl_mpl_hands_body.xml').getroot();parents={c:p for p in xml.iter('body') for c in p.findall('body')};tree=next(b for b in xml.iter('body') if b.get('name')=='L_Thorax');relatives={}
    def joint_rotation(axes,angles):
        if len(angles)!=2 or two_axis_mode=='exp_sum':return Rotation.from_rotvec(axes@angles)
        rotations=[Rotation.from_rotvec(axes[:,i]*angles[i]) for i in range(2)]
        return rotations[0]*rotations[1] if two_axis_mode=='xml_product' else rotations[1]*rotations[0]
    for body in tree.iter('body'):
        name=body.get('name');parent=parents[body].get('name');pp,pq=pose(initial['human_body_states'][bodies.index(parent)]);bp,bq=pose(initial['human_body_states'][bodies.index(name)]);rp=Rotation.from_quat(pq);joints=body.findall('joint');ids=[names.index(j.get('name')) for j in joints];axes=np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in joints]) if joints else np.zeros((3,0));relatives[name]=(parent,rp.inv().apply(bp-pp),rp.inv()*Rotation.from_quat(bq),axes,ids)
    anchor=pose(initial['human_body_states'][bodies.index('Chest')])
    def fk(q):
        poses={'Chest':(anchor[0],Rotation.from_quat(anchor[1]))}
        for name,(parent,p,r0,axes,ids) in relatives.items():
            pp,rp=poses[parent];relative=joint_rotation(axes,q[ids])*joint_rotation(axes,q0[ids]).inv()*r0 if ids else r0;poses[name]=(pp+rp.apply(p),rp*relative)
        return poses
    return fk,relatives
