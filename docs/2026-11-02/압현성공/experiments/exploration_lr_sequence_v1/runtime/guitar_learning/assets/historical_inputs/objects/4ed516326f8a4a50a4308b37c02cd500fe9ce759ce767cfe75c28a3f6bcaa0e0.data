"""Physical joint-target preload plus bounded right PI, with actual strap OFF."""
from unittest.mock import patch
import numpy as np
from scipy.optimize import least_squares
from . import run_om_no_strap_upper_arm_v4 as parked
from . import run_om_no_strap_upper_arm_v2 as endpoint
from .upper_arm_static_geometry_v1 import calibrated_upper_fk
from .initial_pose_noise_v1 import pose,save,sha
base=parked.base
PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V6.md';PLAN_SHA=sha(PLAN)

def metadata(path,data):
    if path.name=='attempt.json':
        data['input_sha256'][str(PLAN)]=PLAN_SHA;data={**data,'current_control_plan':str(PLAN),'target_rule':'right 8mm support-point preload goal + bounded PI; other goals constant; no pose overwrite'}
    elif path.name=='report.json':data={**data,'control':'right preload+PI+arm target rate3; no direct guitar force or attachment'}
    parked.metadata(path,data)

class PreloadRecording(endpoint.EndpointRecording):
    def __init__(self,env,out):
        super().__init__(env,out)
        from .run_joint_hold import native_state
        before=native_state(env);q0=env.contract.q_ref.copy();names=env.names;self.right=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))]);fk,_=calibrated_upper_fk(names,env.human_bodies,before,q0)
        poses=fk(q0);gp,gr=pose(before['guitar_body_states'][0]);row=env.contract.candidate['no_strap_upper_arm_proposal']['proximal_support'];surface=np.array(row['guitar_surface_G_m']);axis=np.array(row['capsule_axis_G_m']);normal=(axis-surface)/np.linalg.norm(axis-surface)
        witness=gp+gr.apply(surface+normal*row['gap_m']);p,r=poses['R_Shoulder'];self.local=r.inv().apply(witness-p);self.desired=gp+gr.apply(surface-.008*normal)
        lower=np.maximum(env.contract.effective_lower[self.right],q0[self.right]-.12);upper=np.minimum(env.contract.effective_upper[self.right],q0[self.right]+.12)
        def residual(v):
            q=q0.copy();q[self.right]=v;ps=fk(q);point=ps['R_Shoulder'][0]+ps['R_Shoulder'][1].apply(self.local)
            return np.r_[1000*(point-self.desired),2*(ps['RH:palm'][0]-poses['RH:palm'][0]),.01*(v-q0[self.right])]
        fit=least_squares(residual,np.clip(q0[self.right],lower+1e-9,upper-1e-9),bounds=(lower,upper),max_nfev=100)
        self.goal=q0.copy();self.goal[self.right]=fit.x;point=fk(self.goal)['R_Shoulder'];error=np.linalg.norm(point[0]+point[1].apply(self.local)-self.desired)
        if error>=.002:raise RuntimeError('preload IK failed tolerance')
        self.cap=np.zeros(81);self.cap[self.right]=.4;self.integral=np.zeros(81);self.control_rows=[]
        props={}
        for actor,label in [(env.human,'human'),(env.guitar,'guitar')]:
            body_names=list(env.gym.get_actor_rigid_body_names(env.env,actor));ranges=env.gym.get_actor_rigid_body_shape_indices(env.env,actor);shapes=env.gym.get_actor_rigid_shape_properties(env.env,actor)
            props[label]={name:[int(shapes[j].filter)for j in range(ind.start,ind.start+ind.count)]for name,ind in zip(body_names,ranges)}
        assert props['human']['R_Shoulder'] and len(props['guitar']['G:body'])==63 and all(a&b==0 for a in props['human']['R_Shoulder']for b in props['guitar']['G:body'])
        save(self.out/'preload_configuration.json',{'goal_rad':self.goal.tolist(),'initial_q_ref_rad':q0.tolist(),'R_Shoulder_witness_local_m':self.local.tolist(),'desired_point_W_m':self.desired.tolist(),'source_normal_G':normal.tolist(),'point_fit_error_m':float(error),'right_goal_max_delta_rad':float(abs(self.goal[self.right]-q0[self.right]).max()),'residual_cap_rad':self.cap.tolist(),'Kp':1,'Ki_per_s':1,'actual_shape_filters':props})
        original=env.contract.neutral_action
        def action():
            original();state=native_state(env);actual=np.array([s['pos']for s in state['human_dof_states']]);err=self.goal-actual;self.integral=np.clip(self.integral+env.contract.dt*err,-self.cap,self.cap);correction=np.clip(err+self.integral,-self.cap,self.cap);requested=np.clip(self.goal+correction,env.contract.effective_lower,env.contract.effective_upper);normalized=np.clip((requested-env.contract.mid)/env.contract.half,-1,1);p,r=pose(state['human_body_states'][env.human_bodies.index('R_Shoulder')])
            self.control_rows.append({'physics_step':env.steps,'actual_q_rad':actual.tolist(),'error_rad':err.tolist(),'integral_rad':self.integral.tolist(),'residual_rad':correction.tolist(),'requested_target_rad':requested.tolist(),'requested_action':normalized.tolist(),'actual_support_point_W_m':(p+r.apply(self.local)).tolist()});assert native_state(env)==state;return normalized
        env.contract.neutral_action=action;assert native_state(env)==before

    def encode(self):
        save(self.out/'preload_control_rows.json',{'scope':'before-control PI request; actual submitted target is next trace row','rows':self.control_rows});return super().encode()

if __name__=='__main__':
    with patch.object(base.deadline_native_v4,'_strap_scene_class',lambda recording,enabled:base.original_factory(recording,False)),patch.object(base.strap_trial_recording,'StrapTrialRecording',PreloadRecording),patch.object(base.string_trial_recording_v1,'StrapTrialRecording',base.GymTrialRecording),patch.object(base.string_trial_recording_v1,'draw_strings',parked.labelled_strings),patch.object(base.trial,'save',metadata):base.main()
