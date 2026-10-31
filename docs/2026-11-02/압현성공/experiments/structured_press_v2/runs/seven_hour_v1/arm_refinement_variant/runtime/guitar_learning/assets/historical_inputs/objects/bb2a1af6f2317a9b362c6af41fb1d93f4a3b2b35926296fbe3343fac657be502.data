"""Distal6 pick IK with soft G-relative hand orientation and source clearance spec."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from ..initial_pose_noise_v1 import pose
from ..lower_body_release_v1.common import save
from .motion_v1 import Motion as PreviousMotion, pick_goal, command_gate


def palm_goal_G(spec,time):
    cfg=spec['clearance_solver_v2'];lo,hi=cfg['orientation_ramp_s']
    u=float(np.clip((time-lo)/(hi-lo),0,1));u=u*u*(3-2*u)
    delta=Rotation.from_rotvec([0.,np.deg2rad(cfg['rotation_G_y_deg'])*u,0.])
    return delta*Rotation.from_quat(cfg['palm_G_reference_xyzw'])


def solve_pick_oriented(fk,qbase,indices,lower,upper,qref,goal_W,palm_goal_W,seed):
    lo=np.maximum(lower[indices]+1e-6,qref[indices]-1.);hi=np.minimum(upper[indices]-1e-6,qref[indices]+1.)
    def residual(v):
        q=qbase.copy();q[indices]=v;ps=fk(q)
        return np.r_[1000*(ps['RH:pick'][0]-goal_W),10*(palm_goal_W.inv()*ps['RH:palm'][1]).as_rotvec(),
            .1*(v-qref[indices]),.1*(v-seed),1000*np.maximum(np.linalg.norm(v.reshape(2,3),axis=1)-np.deg2rad(158),0)]
    fit=least_squares(residual,np.clip(seed,lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=60,ftol=1e-8,xtol=1e-8,gtol=1e-8)
    q=qbase.copy();q[indices]=fit.x
    return q,float(np.linalg.norm(fk(q)['RH:pick'][0]-goal_W)),fit.nfev


class Motion(PreviousMotion):
    def apply(self,named):
        s=self.s;time=s.steps/240
        if time<10:return named
        cfg=self.spec['clearance_solver_v2']
        assert cfg['orientation_weight']==10 and cfg['qref_weight']==cfg['continuity_weight']==.1
        state=s.native();q=np.array([r['pos'] for r in state['human_dof_states']]);gp,gr=pose(state['guitar_body_states'][0])
        if not self.started:
            assert s.steps==2400
            self.initial_pick=gr.inv().apply(pose(state['human_body_states'][s.human_bodies.index('RH:pick')])[0]-gp)
            assert np.array_equal(self.initial_pick,self.spec['initial_pick_G_m'])
            save(Path(s.cfg['attempt_out'])/'play_reference.json',dict(time_s=time,state=state,initial_pick_G_m=self.initial_pick.tolist(),spec=self.spec))
            self.started=True
        original=np.array([named[n] for n in s.names]);request=original.copy()
        self.stage='baseline_hold' if self.case=='baseline' else ('playing' if time<13.5 else 'observe')
        self.info=dict(case=self.case,press_enabled=False,strike_enabled=self.case=='strike',changed_joint_indices105=self.distal.tolist() if self.case=='strike' else [],right_world_palm_IK_active=False,clearance_solver_version=2)
        if self.case=='strike':
            goal=pick_goal(time,self.initial_pick,np.array(self.spec['strike']['waypoints_G_m']));orientation=gr*palm_goal_G(self.spec,time)
            fitted,error64,nfev=solve_pick_oriented(self.fk,q,self.distal,s.lower,s.upper,s.q_ref,gp+gr.apply(goal),orientation,s.target[self.distal].astype(float))
            values=fitted[self.distal].astype(np.float32).astype(float);trial=q.copy();trial[self.distal]=values;ps=self.fk(trial)
            error=float(np.linalg.norm(ps['RH:pick'][0]-(gp+gr.apply(goal))))
            if not command_gate(values,s.lower[self.distal],s.upper[self.distal],s.q_ref[self.distal]) or not np.isfinite(error) or error>.002:
                raise RuntimeError('새 soft-hand distal6 float32 strict bounds/qref/principal/reach2mm gate')
            request[self.distal]=values
            self.info.update(pick_goal_G_m=goal.tolist(),pick_IK_error_m=error,pick_IK_float64_error_m=error64,pick_IK_nfev=int(nfev),requested_distal6_rad=values.tolist(),palm_goal_G_xyzw=palm_goal_G(self.spec,time).as_quat().tolist(),palm_soft_orientation_error_rad=float((orientation.inv()*ps['RH:palm'][1]).magnitude()))
        unchanged=np.setdiff1d(np.arange(105),self.distal if self.case=='strike' else [])
        assert np.array_equal(request[unchanged],original[unchanged]) and s.native()==state
        assert np.array_equal(request[self.proximal],self.spec['proximal_latch']['final6_rad'])
        self.info['other_base_request_channels_exact']=True
        return dict(zip(s.names,request.tolist()))
