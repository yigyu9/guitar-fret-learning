"""Two cheap analytic source clearance terms; final whole-mesh audit remains required."""
import itertools
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import ConvexHull
from .om_axilla_source_geometry_v3 import segment_convex


def segment_gap(a,b,c,d):
    u,v,w=b-a,d-c,a-c; aa=u@u;bb=u@v;cc=v@v;dd=u@w;ee=v@w
    s=np.clip((bb*ee-cc*dd)/max(aa*cc-bb*bb,1e-15),0,1); t=(bb*s+ee)/cc
    if t<0:t=0.;s=np.clip(-dd/aa,0,1)
    elif t>1:t=1.;s=np.clip((bb-dd)/aa,0,1)
    return float(np.linalg.norm(a+s*u-c-t*v))


def clearance_function(asset,analytic,original):
    box=next(b for b in ET.parse(asset).iter('body') if b.get('name')=='Pelvis').find('geom')
    assert box.get('type')=='box' and np.array_equal(np.fromstring(box.get('quat'),sep=' '),[1,0,0,0])
    centre=np.fromstring(box.get('pos'),sep=' ');size=np.fromstring(box.get('size'),sep=' ')
    p,r=original['Pelvis'];verts=p+r.apply(centre+np.array(list(itertools.product((-1,1),repeat=3)))*size);planes=ConvexHull(verts).equations
    def endpoints(poses,name):
        ep,radius=analytic.capsules[name];p,r=poses[name];return p+r.apply(ep),radius
    def measure(poses):
        arm,ra=endpoints(poses,'L_Shoulder');torso,rt=endpoints(poses,'Torso');forearm,rf=endpoints(poses,'L_Elbow')
        return np.array([segment_gap(*arm,*torso)-ra-rt,segment_convex(*forearm,verts,planes)[0]-rf])
    return measure
