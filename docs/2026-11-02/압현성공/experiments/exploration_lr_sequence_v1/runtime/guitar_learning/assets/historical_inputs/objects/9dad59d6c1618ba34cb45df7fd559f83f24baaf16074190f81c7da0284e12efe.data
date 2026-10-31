"""Guitar-relative right motor-point targets with bounded joint PI, strap OFF."""
from unittest.mock import patch
import numpy as np
from scipy.optimize import least_squares
from . import run_om_no_strap_upper_arm_v4 as parked
from . import run_om_no_strap_upper_arm_v7 as hold
from .learning_scene_v2 import LearningScene
from . import run_om_no_strap_upper_arm_v2 as endpoint
from .upper_arm_static_geometry_v1 import calibrated_upper_fk
from .initial_pose_noise_v1 import pose,save,sha
base=parked.base
PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V9.md';PLAN_SHA=sha(PLAN)
METADATA_PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V7.md';METADATA_SHA=sha(METADATA_PLAN)
physical_save=base.original_save

def final_save(path,data):
    if path.name=='attempt.json':
        data['input_sha256'].update({str(PLAN):PLAN_SHA,str(hold.PLAN):hold.PLAN_SHA})
        data={**data,'control':'current-guitar-relative motor reference IK + right PI cap.4rad, initial-relative final target cap.8rad and arm rate3; right PD x4/x2','current_control_plan':str(PLAN),'reference_point_scope':'subset source body-local motor reference, not measured physical surface/contact point'}
    physical_save(path,data)

def metadata(path,data):
    if path.name=='attempt.json':
        data['input_sha256'][str(PLAN)]=PLAN_SHA;data['input_sha256'][str(METADATA_PLAN)]=METADATA_SHA;data={**data,'current_control_plan':str(PLAN),'target_rule':'current-guitar-relative right IK plus PI; others constant; no pose overwrite'}
    elif path.name=='report.json':data={**data,'control':'current-guitar-relative right IK+PI+PD x4/x2; no direct guitar force or attachment'}
    parked.metadata(path,data)

class RelativeRecording(endpoint.EndpointRecording):
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
        self.cap=np.zeros(81);self.cap[self.right]=.4;self.integral=np.zeros(81);self.control_rows=[];self.relative_rows=[];self.safe_goal=self.goal.copy();self.stopped=False
        self.initial_gp,self.initial_gr=gp,gr;self.surface,self.normal=surface,normal;self.initial_q=q0;self.palm_G=gr.inv().apply(poses['RH:palm'][0]-gp)
        self.target_lo=env.contract.effective_lower.copy();self.target_hi=env.contract.effective_upper.copy();self.target_lo[self.right]=np.maximum(self.target_lo[self.right],q0[self.right]-.8);self.target_hi[self.right]=np.minimum(self.target_hi[self.right],q0[self.right]+.8)
        save(self.out/'right_hold_properties.json',env.right_hold_record)
        props={}
        for actor,label in [(env.human,'human'),(env.guitar,'guitar')]:
            body_names=list(env.gym.get_actor_rigid_body_names(env.env,actor));ranges=env.gym.get_actor_rigid_body_shape_indices(env.env,actor);shapes=env.gym.get_actor_rigid_shape_properties(env.env,actor)
            props[label]={name:[int(shapes[j].filter)for j in range(ind.start,ind.start+ind.count)]for name,ind in zip(body_names,ranges)}
        save(self.out/'actual_shape_filters.json',props)
        assert props['human']['R_Shoulder'] and len(props['guitar']['G:body'])==63 and all(a&b==0 for a in props['human']['R_Shoulder']for b in props['guitar']['G:body'])
        save(self.out/'preload_configuration.json',{'goal_rad':self.goal.tolist(),'initial_q_ref_rad':q0.tolist(),'R_Shoulder_witness_local_m':self.local.tolist(),'desired_point_W_m':self.desired.tolist(),'source_normal_G':normal.tolist(),'reference_point_scope':'subset source body-local motor reference, not a measured physical surface','point_fit_error_m':float(error),'right_goal_max_delta_rad':float(abs(self.goal[self.right]-q0[self.right]).max()),'residual_cap_rad':self.cap.tolist(),'Kp':1,'Ki_per_s':1,'actual_shape_filters':props})
        original=env.contract.neutral_action
        def action():
            original();state=native_state(env);actual=np.array([s['pos']for s in state['human_dof_states']]);gp,gr=pose(state['guitar_body_states'][0]);shift=float(np.linalg.norm(gp-self.initial_gp));rotation=float(np.rad2deg((self.initial_gr.inv()*gr).magnitude()));self.stopped=self.stopped or shift>.15 or rotation>25
            desired=gp+gr.apply(self.surface-.008*self.normal);palm=gp+gr.apply(self.palm_G);fit_error=None;fit_status='safety_hold'
            if not self.stopped:
                current_fk,_=calibrated_upper_fk(names,env.human_bodies,state,actual);low=np.maximum(env.contract.effective_lower[self.right],q0[self.right]-.4);high=np.minimum(env.contract.effective_upper[self.right],q0[self.right]+.4)
                def current_residual(v):
                    q=actual.copy();q[self.right]=v;ps=current_fk(q);point=ps['R_Shoulder'][0]+ps['R_Shoulder'][1].apply(self.local)
                    return np.r_[1000*(point-desired),10*(ps['RH:palm'][0]-palm),.2*(v-self.safe_goal[self.right])]
                result=least_squares(current_residual,np.clip(self.safe_goal[self.right],low+1e-9,high-1e-9),bounds=(low,high),max_nfev=60)
                q=actual.copy();q[self.right]=result.x;p,r=current_fk(q)['R_Shoulder'];fit_error=float(np.linalg.norm(p+r.apply(self.local)-desired));fit_status='accepted' if result.success and fit_error<.005 else 'fit_hold'
                if fit_status=='accepted':self.safe_goal[self.right]=result.x
            self.goal=self.safe_goal.copy();err=self.goal-actual;self.integral=np.clip(self.integral+env.contract.dt*err,-self.cap,self.cap);correction=np.clip(err+self.integral,-self.cap,self.cap);requested=np.clip(self.goal+correction,self.target_lo,self.target_hi);normalized=np.clip((requested-env.contract.mid)/env.contract.half,-1,1);p,r=pose(state['human_body_states'][env.human_bodies.index('R_Shoulder')])
            self.relative_rows.append({'physics_step':env.steps,'current_guitar_p_W_m':gp.tolist(),'current_guitar_q_xyzw':gr.as_quat().tolist(),'desired_motor_point_W_m':desired.tolist(),'goal_rad':self.goal.tolist(),'point_fit_error_m':fit_error,'fit_status':fit_status,'safety_stopped':self.stopped})
            self.control_rows.append({'physics_step':env.steps,'actual_q_rad':actual.tolist(),'error_rad':err.tolist(),'integral_rad':self.integral.tolist(),'residual_rad':correction.tolist(),'requested_target_rad':requested.tolist(),'requested_action':normalized.tolist(),'actual_support_point_W_m':(p+r.apply(self.local)).tolist()});assert native_state(env)==state;return normalized
        env.contract.neutral_action=action;assert native_state(env)==before

    def encode(self):
        save(self.out/'relative_goal_rows.json',{'scope':'current-guitar-relative motor reference; 15cm/25degree latched safety; fit error below5mm acceptance','rows':self.relative_rows});save(self.out/'preload_control_rows.json',{'scope':'before-control PI request; actual submitted target is next trace row','rows':self.control_rows});return super().encode()

if __name__=='__main__':
    with patch.object(LearningScene,'_create_scene',hold.create_right_hold),patch.object(base,'original_save',final_save),patch.object(base.deadline_native_v4,'_strap_scene_class',lambda recording,enabled:base.original_factory(recording,False)),patch.object(base.strap_trial_recording,'StrapTrialRecording',RelativeRecording),patch.object(base.string_trial_recording_v1,'StrapTrialRecording',base.GymTrialRecording),patch.object(base.string_trial_recording_v1,'draw_strings',parked.labelled_strings),patch.object(base.trial,'save',metadata):base.main()
