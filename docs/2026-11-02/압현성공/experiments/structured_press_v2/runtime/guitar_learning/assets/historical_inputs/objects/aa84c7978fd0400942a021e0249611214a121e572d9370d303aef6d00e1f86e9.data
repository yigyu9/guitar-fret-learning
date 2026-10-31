"""Analytic capsule vs source convex OM pieces; no native state or model changes."""
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import ConvexHull
from scipy.optimize import minimize


def segment_convex(a,b,vertices,planes):
    # Metres, centred on this hull; strict tolerance resolves thin source pieces.
    centre=vertices.mean(0);v=vertices-centre;a=a-centre;b=b-centre
    axis=b-a;A=planes[:,:3];offset=planes[:,3]+A@centre
    def objective(z):
        delta=z[:3]-a-z[3]*axis
        return float(delta@delta),np.r_[2*delta,-2*delta@axis]
    fit=minimize(lambda z:objective(z)[0],np.r_[v.mean(0),.5],jac=lambda z:objective(z)[1],method='SLSQP',bounds=[(None,None)]*3+[(0,1)],constraints={'type':'ineq','fun':lambda z:-offset-A@z[:3],'jac':lambda z:np.c_[-A,np.zeros(len(A))]},options={'ftol':1e-14,'maxiter':100})
    if not fit.success or max(A@fit.x[:3]+offset)>1e-9:raise RuntimeError('capsule projection failed: '+fit.message)
    line=a+fit.x[3]*axis;surface=fit.x[:3]
    return float(np.linalg.norm(line-surface)),centre+line,centre+surface,float(fit.x[3])


class CapsuleBodyDistance:
    def __init__(self,asset,human):
        root=ET.parse(asset);body=next(b for b in root.iter('body') if b.get('name')=='G:body')
        shift=np.fromstring(body.get('pos'),sep=' ');assets={m.get('name'):m for m in root.findall('./asset/mesh')};self.pieces=[]
        for g in body.findall('geom'):
            if g.get('contype')=='0' or g.get('conaffinity')=='0':continue
            file=(Path(asset).parent/assets[g.get('mesh')].get('file')).resolve()
            v=np.array([[float(x) for x in s.split()[1:4]] for s in file.read_text().splitlines() if s.startswith('v ')])+shift
            planes=ConvexHull(v).equations;_,idx=np.unique(np.round(planes,10),axis=0,return_index=True);planes=planes[idx]
            self.pieces.append((v,planes,v.min(0),v.max(0)))
        self.capsules={}
        for b in ET.parse(human).iter('body'):
            g=b.find('geom')
            if g is not None and g.get('type')=='capsule':self.capsules[b.get('name')]=(np.fromstring(g.get('fromto'),sep=' ').reshape(2,3),float(g.get('size')))

    def measure(self,poses,name,gp,gr):
        points,radius=self.capsules[name];p,r=poses[name];a,b=gr.inv().apply(p+r.apply(points)-gp)
        lower=[]
        for i,(_,_,lo,hi) in enumerate(self.pieces):
            delta=np.maximum(np.maximum(lo-np.maximum(a,b),np.minimum(a,b)-hi),0)
            lower.append((float(np.linalg.norm(delta)-radius),i))
        best=None
        for bound,i in sorted(lower):
            if best is not None and bound>=best['gap_m']:break
            v,planes,_,_=self.pieces[i];distance,centre,surface,t=segment_convex(a,b,v,planes);gap=distance-radius
            if best is None or gap<best['gap_m']:
                best={'gap_m':gap,'guitar_surface_G_m':surface.tolist(),'capsule_axis_G_m':centre.tolist(),'segment_fraction':t,'piece_index':i,'scope':'source analytic capsule vs convex mesh; negative gap is intersection indication, not cooked penetration depth'}
        return best
