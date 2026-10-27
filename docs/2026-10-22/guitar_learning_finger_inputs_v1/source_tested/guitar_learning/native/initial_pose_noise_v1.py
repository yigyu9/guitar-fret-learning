"""Bounded guitar-pose jitter with arm IK; no runtime state writes."""
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

RANGES={'translation_lower_m':[-.005,-.005,0.], 'translation_upper_m':[.005,.005,.005],
        'world_rotvec_component_limit_deg':1., 'arm_delta_limit_rad':.15,
        'position_tolerance_m':.002,'orientation_tolerance_deg':1.}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,d):
    with Path(p).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
def pose(s):
    return np.array([s['pose']['p'][k] for k in 'xyz']),Rotation.from_quat([s['pose']['r'][k] for k in 'xyzw'])

def fit_hands(fk,q0,names,lower,upper,gp,gr,delta_p,rotvec_deg):
    q0=np.asarray(q0,dtype=float);delta_p=np.asarray(delta_p,dtype=float);rv=np.asarray(rotvec_deg,dtype=float)
    if delta_p.shape!=(3,) or rv.shape!=(3,) or not np.isfinite(np.r_[delta_p,rv]).all():raise ValueError('finite pose noise required')
    if np.any(delta_p< RANGES['translation_lower_m']) or np.any(delta_p>RANGES['translation_upper_m']) or np.any(abs(rv)>1):raise ValueError('noise outside declared range')
    dr=Rotation.from_rotvec(np.deg2rad(rv));newp=gp+delta_p;newr=dr*gr
    base=fk(q0);q=q0.copy();goals={};metrics={}
    for side in ('L','R'):
        palm=side+'H:palm';p,r=base[palm]
        target_p=newp+dr.apply(p-gp);target_r=dr*r;goals[palm]=(target_p,target_r)
        idx=np.array([i for i,n in enumerate(names) if n.startswith(tuple(side+'_'+s for s in ('Thorax','Shoulder','Elbow','Wrist')))])
        if len(idx)!=12:raise ValueError('12 arm channels per hand required')
        lo=np.maximum(np.asarray(lower)[idx],q0[idx]-.15);hi=np.minimum(np.asarray(upper)[idx],q0[idx]+.15)
        def residual(v):
            trial=q.copy();trial[idx]=v;pp,rr=fk(trial)[palm]
            return np.r_[1000*(pp-target_p),10*(target_r.inv()*rr).as_rotvec(),.01*(v-q0[idx])]
        fit=least_squares(residual,np.clip(q0[idx],lo+1e-9,hi-1e-9),bounds=(lo,hi),max_nfev=120,ftol=1e-10,xtol=1e-10,gtol=1e-10)
        q[idx]=fit.x;pp,rr=fk(q)[palm]
        metrics[palm]={'fit_success':bool(fit.success),'position_error_m':float(np.linalg.norm(pp-target_p)),
                       'orientation_error_deg':float(np.rad2deg((target_r.inv()*rr).magnitude()))}
    return q,newp,newr,goals,metrics

class PoseBank:
    def __init__(self,path,seed):
        self.path=Path(path);self.data=read(path);self.rng=np.random.default_rng(seed);self.sequence=0
        if self.data.get('schema')!='sa2_coupled_initial_pose_bank_v1' or len(self.data['entries'])<2:raise ValueError('validated pose bank required')
        self.inputs={str(self.path.resolve()):sha(self.path),**self.data['input_sha256']}
        if any(sha(p)!=h for p,h in self.data['input_sha256'].items()):raise ValueError('bank input hash changed')
        for e in self.data['entries']:
            if not e['validated_native'] or not e['source_clear']:raise ValueError('unsafe bank entry')
    def sample(self,index=None):
        if index is None:index=int(self.rng.integers(len(self.data['entries'])))
        if type(index) is not int or not 0<=index<len(self.data['entries']):raise ValueError('bank index outside range')
        self.sequence+=1
        return copy.deepcopy(self.data['entries'][index]),{'index':index,'reset_sequence':self.sequence,'sampling':'uniform discrete with replacement over validated bank'}
