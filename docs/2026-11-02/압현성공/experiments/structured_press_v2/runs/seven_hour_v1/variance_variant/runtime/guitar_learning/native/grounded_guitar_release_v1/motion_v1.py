"""Finite left-wrist world withdrawal and original weighted finger opening."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from ..initial_pose_noise_v1 import pose
from guitar_learning.native.paths import read, save, sha

WEIGHTS={**{'LH:'+digit+suffix:weight for digit in ('index','middle','ring','pinky')
            for suffix,weight in (('1_x',.7),('2',1.),('3',.6))},'LH:thumb2':1.,'LH:thumb3':.6}


def smoothstep(t,start,end):
    u=float(np.clip((t-start)/(end-start),0.,1.))
    return u*u*(3-2*u)


def solve_wrist(fk,q,indices,lower,upper,qref,goal,rotation,start):
    lo=np.maximum(lower[indices]+1e-6,qref[indices]-.8)
    hi=np.minimum(upper[indices]-1e-6,qref[indices]+.8)
    def residual(v):
        trial=q.copy();trial[indices]=v;p,r=fk(trial)['L_Wrist']
        return np.r_[1000*(p-goal),100*(rotation.inv()*r).as_rotvec(),.05*(v-qref[indices])]
    fit=least_squares(residual,np.clip(start,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=30,ftol=1e-7,xtol=1e-7)
    trial=q.copy();trial[indices]=fit.x;p,r=fk(trial)['L_Wrist']
    return fit.x,float(np.linalg.norm(p-goal)),float((rotation.inv()*r).magnitude()),fit.nfev


class Motion:
    def __init__(self,scene,fk):
        self.s=scene;self.fk=fk;self.spec=read(scene.cfg['release_spec'])
        assert sha(scene.cfg['release_spec'])==scene.cfg['release_spec_sha256']
        self.arm=np.array([j for j,n in enumerate(scene.names) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))])
        assert self.spec['joint_names']==[scene.names[j] for j in self.arm]
        assert self.spec['joint_indices105']==self.arm.tolist()
        assert self.spec['open_interval_s']==[10,11] and self.spec['withdraw_interval_s']==[11,13]
        assert self.spec['opening_rad']==.3 and self.spec['finger_opening_weights']==WEIGHTS
        assert self.spec['reference_time_s']==10 and len(self.arm)==12
        self.started=False;self.stage='prepared';self.info={}

    def apply(self,named):
        s=self.s;t=s.steps/240
        if t<10:return named
        state=s.native();q=np.array([v['pos'] for v in state['human_dof_states']]);gp,gr=pose(state['guitar_body_states'][0])
        if not self.started:
            assert s.steps==2400
            self.origin,self.rotation=pose(state['human_body_states'][s.human_bodies.index('L_Wrist')])
            self.delta=gr.apply([.08,0.,0.])
            assert np.linalg.norm(self.origin-self.spec['wrist_origin_W_m'])<=1e-10
            assert (self.rotation.inv()*Rotation.from_quat(self.spec['wrist_rotation_xyzw'])).magnitude()<=1e-10
            assert np.linalg.norm(self.delta-self.spec['withdraw_delta_W_m'])<=1e-10
            save(Path(s.cfg['attempt_out'])/'release_reference.json',dict(time_s=t,state=state,wrist_origin_W_m=self.origin.tolist(),
                wrist_rotation_xyzw=self.rotation.as_quat().tolist(),withdraw_delta_W_m=self.delta.tolist(),spec=self.spec))
            self.started=True
        original=np.array([named[n] for n in s.names]);request=original.copy()
        opening=.3*smoothstep(t,10,11);fraction=smoothstep(t,11,13);goal=self.origin+self.delta*fraction
        values,position_error,rotation_error,nfev=solve_wrist(self.fk,q,self.arm,s.lower,s.upper,s.q_ref,goal,self.rotation,s.target[self.arm].astype(float))
        if not np.isfinite(values).all() or position_error>.01 or rotation_error>.05 or np.any(np.linalg.norm(values.reshape(4,3),axis=1)>=np.deg2rad(160)):
            raise RuntimeError('finite left release wrist IK hard gate')
        request[self.arm]=values
        finger=[]
        for name,weight in WEIGHTS.items():
            j=s.names.index(name);finger.append(j);request[j]=np.clip(request[j]-weight*opening,s.lower[j],s.upper[j])
        mask=np.ones(105,dtype=bool);mask[np.r_[self.arm,finger]]=False
        assert np.array_equal(request[mask],original[mask]) and s.native()==state
        self.stage='open' if t<11 else 'withdraw' if t<13 else 'released_hold'
        self.info=dict(opening_rad=opening,withdraw_fraction=fraction,wrist_origin_W_m=self.origin.tolist(),
            wrist_rotation_xyzw=self.rotation.as_quat().tolist(),withdraw_delta_W_m=self.delta.tolist(),goal_wrist_W_m=goal.tolist(),
            source_IK_position_error_m=position_error,source_IK_rotation_error_rad=rotation_error,source_IK_nfev=nfev,
            left_indices105=self.arm.tolist(),finger_indices105=finger,other_base_request_channels_exact=True,
            scope='Finite human targets from actual10s world wrist and fixed G10+X direction. Source IK error is not actual tracking or contact clearance; no state or guitar command.')
        return dict(zip(s.names,request.tolist()))
