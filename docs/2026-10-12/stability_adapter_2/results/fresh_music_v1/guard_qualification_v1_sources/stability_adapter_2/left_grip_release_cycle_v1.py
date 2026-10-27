"""Two current-guitar hand stations, bounded human actuation, measured contacts."""
from unittest.mock import patch
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import pose, save
from .upper_arm_static_geometry_v1 import calibrated_upper_fk

TIMES = np.array([0, 2, 3, 4.5, 6, 7, 8.5, 10, 11.5, 13, 16.])
# [neck-axis translation, underside withdrawal, extra finger flexion], metres/radians.
VALUES = np.array([[0,0,0],[0,0,0],[0,0,.18],[0,0,.18],
                   [0,.045,0],[0,.045,0],[.04,.045,0],[.04,0,.18],
                   [.04,0,.18],[.04,.045,0],[.04,.045,0]])
STAGES = ['prepare','close_A','hold_A','release_A','open_A',
          'move_open_B','close_B','hold_B','release_B','open_B']


def trajectory(t):
    k = min(max(np.searchsorted(TIMES,t,side='right')-1,0),len(TIMES)-2)
    u = np.clip((t-TIMES[k])/(TIMES[k+1]-TIMES[k]),0,1)
    s = u*u*(3-2*u)
    v = VALUES[k]+s*(VALUES[k+1]-VALUES[k])
    derivative = 6*u*(1-u)*(VALUES[k+1]-VALUES[k])/(TIMES[k+1]-TIMES[k])
    return STAGES[k],v,derivative


def main(run):
    import isaacgym
    from isaacgym import gymtorch
    from . import right_block_body_effort_v5 as support
    from . import left_near_scene_v3 as scene_module
    from . import left_near_arm_effort_v3 as tracking
    from . import left_wrist_tracking_off_v2 as off
    from .run_joint_hold import native_state
    from .native_contacts import body_names,read_contacts
    from .dual_shoulder_effort_v1 import skew
    from .strap import point_kinematics
    original_factory,original_recording = support.factory,support.EffortRecording

    def factory(recording,enabled):
        Parent = original_factory(recording,enabled)
        class Scene(Parent):
            def step(self,action):
                state=native_state(self);q=np.array([x['pos'] for x in state['human_dof_states']])
                if not hasattr(self,'cycle_rows'):
                    self.cycle_rows=[];self.cycle_fk,_=calibrated_upper_fk(self.names,self.human_bodies,state,self.contract.q_ref)
                    self.cycle_arm=np.array([i for i,n in enumerate(self.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))])
                    self.cycle_hand=np.array([i for i,n in enumerate(self.names) if n.startswith('LH:')])
                    gp,gr=pose(state['guitar_body_states'][0]);wp,wr=pose(state['human_body_states'][self.human_bodies.index('L_Wrist')])
                    self.cycle_point=gr.inv().apply(wp-gp);self.cycle_rotation=gr.inv()*wr
                t=self.steps/240;stage,v,vd=trajectory(t);request=self.contract.q_ref.copy();gp,gr=pose(state['guitar_body_states'][0])
                target_G=self.cycle_point+np.array([v[1],v[0],0]);target_R=gr*self.cycle_rotation
                error=rotation_error=0.
                if t>=2:
                    lo=np.maximum(self.contract.lower[self.cycle_arm],self.contract.q_ref[self.cycle_arm]-.8)
                    hi=np.minimum(self.contract.upper[self.cycle_arm],self.contract.q_ref[self.cycle_arm]+.8)
                    def residual(values):
                        fitted=q.copy();fitted[self.cycle_arm]=values;p,r=self.cycle_fk(fitted)['L_Wrist']
                        return np.r_[1000*(p-gp-gr.apply(target_G)),100*(target_R.inv()*r).as_rotvec(),.05*(values-self.contract.q_ref[self.cycle_arm])]
                    fit=least_squares(residual,np.clip(self.target[self.cycle_arm],lo+1e-8,hi-1e-8),bounds=(lo,hi),max_nfev=30,ftol=1e-7)
                    request[self.cycle_arm]=fit.x;pp,rr=self.cycle_fk(np.where(np.isin(np.arange(81),self.cycle_arm),request,q))['L_Wrist']
                    error=float(np.linalg.norm(pp-gp-gr.apply(target_G)));rotation_error=float((target_R.inv()*rr).magnitude())
                    if not np.isfinite(fit.x).all() or error>.010 or rotation_error>.05 or np.any(np.linalg.norm(fit.x.reshape(4,3),axis=1)>=np.deg2rad(160)):
                        raise RuntimeError('left cycle IK bounds/position/orientation gate')
                    for digit in ('index','middle','ring','pinky'):
                        for suffix,weight in (('1_x',.7),('2',1.),('3',.6)):
                            i=self.names.index('LH:'+digit+suffix);request[i]=np.clip(request[i]+weight*v[2],self.contract.lower[i],self.contract.upper[i])
                owned=np.r_[self.cycle_arm,self.cycle_hand];mask=np.ones(81,dtype=bool);mask[owned]=False
                assert np.array_equal(request[mask],self.contract.q_ref[mask])
                self.cycle_goal_G=target_G;self.cycle_goal_velocity_G=np.array([vd[1],vd[0],0]);self.cycle_goal_rotation=target_R
                action=np.clip((request-self.contract.mid)/self.contract.half,-1,1)
                result=super().step(action)
                assert np.array_equal(self.target[mask].astype(float),self.contract.q_ref[mask])
                self.cycle_rows.append({'physics_step_before':self.steps-4,'stage':stage,'time_s':t,'trajectory':v.tolist(),'goal_wrist_G_m':target_G.tolist(),
                    'IK_error_m':error,'IK_rotation_error_rad':rotation_error,'requested81_rad':request.tolist(),'final81_rad':self.target.astype(float).tolist(),'other48_targets_exact':True})
                return result
        return Scene

    class Recording(original_recording):
        def __init__(self,env,out):
            super().__init__(env,out);self.cycle_efforts=[];self.cycle_contacts=[]
            mapping=body_names(env.gym,env.env);previous_observe=env.after_physics
            def observe(owner):
                previous_observe(owner);state=native_state(owner);contacts=read_contacts(owner.gym,owner.env,mapping)
                left=[];right=[]
                for c in contacts:
                    a,b=c['body0_name'],c['body1_name'];human=a if a.startswith('human/') and b.startswith('guitar/') else b if b.startswith('human/') and a.startswith('guitar/') else None
                    if human and human.startswith(('human/LH:','human/L_')):left.append(c)
                    if human and human.startswith(('human/RH:','human/R_','human/R_Hip')):right.append(c)
                self.cycle_contacts.append({'physics_step':owner.steps,'time_s':owner.steps/240,'stage':trajectory(owner.steps/240)[0],
                    'left_guitar_contacts':left,'right_guitar_contacts':right,'wrist_state':state['human_body_states'][owner.human_bodies.index('L_Wrist')]})
                assert native_state(owner)==state
            env.after_physics=observe
            tensor=gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim,'human'));index=env.human_bodies.index('L_Wrist')
            props=env.gym.get_actor_rigid_body_properties(env.env,env.human);com=np.array([props[index].com.x,props[index].com.y,props[index].com.z])
            left=np.array([i for i,n in enumerate(env.names) if n.startswith(('L_Thorax','L_Shoulder','L_Elbow','L_Wrist'))]);mask=np.ones(81,dtype=bool);mask[left]=False
            previous_control=env.right_effort_controller
            vec=lambda body,field:np.array([body['vel'][field][k] for k in 'xyz'])
            def control():
                before=previous_control().copy();state=native_state(env);wrist=state['human_body_states'][index];guitar=state['guitar_body_states'][0]
                p,r=pose(wrist);gp,gr=pose(guitar);t=env.steps/240
                point,velocity=point_kinematics(p,r.as_quat(),vec(wrist,'linear'),vec(wrist,'angular'),np.zeros(3),com)
                block=tensor.detach().cpu().numpy()[0,index-1].astype(float).copy();qdot=np.array([x['vel'] for x in state['human_dof_states']])
                candidates={mode:block[:3]-skew(r.apply(-(com if mode=='COM' else np.zeros(3))))@block[3:] for mode in ('COM','origin')}
                errors={mode:float(np.linalg.norm(j@qdot-velocity)) for mode,j in candidates.items()};mode=min(errors,key=errors.get);j=candidates[mode]
                if errors[mode]>.01:raise RuntimeError('left cycle Jacobian velocity mismatch')
                local=env.cycle_goal_G;goal,goalvel=point_kinematics(gp,gr.as_quat(),vec(guitar,'linear'),vec(guitar,'angular'),local,env.com[env.guitar_bodies[0]])
                goalvel+=gr.apply(env.cycle_goal_velocity_G);rot_error=(env.cycle_goal_rotation*r.inv()).as_rotvec()
                ramp=float(np.clip((t-2)/.3,0,1));rawF=ramp*(1500*(goal-point)+40*(goalvel-velocity));F=rawF*min(1.,25/max(np.linalg.norm(rawF),1e-12))
                rawM=ramp*(15*rot_error+1*(vec(guitar,'angular')-vec(wrist,'angular')));M=rawM*min(1.,2/max(np.linalg.norm(rawM),1e-12))
                task=j[:,left].T@F+block[3:,left].T@M;request=before[left].astype(float)+task;final=before.copy()
                final[left]=np.clip(request,-env.pd_properties['effort'][left],env.pd_properties['effort'][left]).astype(np.float32)
                assert np.array_equal(final[mask],before[mask]) and np.isfinite(final).all() and native_state(env)==state
                self.cycle_efforts.append({'physics_step':env.steps,'stage':trajectory(t)[0],'point_error_m':float(np.linalg.norm(goal-point)),
                    'rotation_error_rad':float(np.linalg.norm(rot_error)),'jacobian_velocity_errors_m_s':errors,'jacobian_frame':mode,
                    'virtual_force_W_N':F.tolist(),'virtual_moment_W_Nm':M.tolist(),'left_task12_Nm':task.tolist(),
                    'actual_submitted_efforts81_Nm':final.astype(float).tolist(),'other69_efforts_exact':True})
                return final
            env.right_effort_controller=control
        def encode(self):
            save(self.out/'left_cycle_targets.json',{'rows':getattr(self.env,'cycle_rows',[]),'scope':'left33 requests; body/head/right48 logical targets preserved'})
            save(self.out/'left_cycle_contacts.json',{'rows':self.cycle_contacts,'scope':'post-physics actual native contact query; raw lambda is not calibrated force N'})
            save(self.out/'left_cycle_efforts.json',{'rows':self.cycle_efforts,'K_N_m':1500,'D_Ns_m':40,'force_cap_N':25,'K_Nm_rad':15,'D_Nms_rad':1,'moment_cap_Nm':2,
                'scope':'actual final human81 commands after all inherited stages; bounded left wrist virtual task only, no guitar wrench'})
            original_save=support.save
            def scoped(path,value):
                if path.name in ('body_effort_rows.json','left_wrist_tracking_rows.json'):
                    value={**value,'scope':'before left cycle wrist task; superseded by actual final human81 vector in left_cycle_efforts.json','superseded_by':'left_cycle_efforts.json'}
                return original_save(path,value)
            with patch.object(support,'save',scoped),patch.object(off,'save',scoped):return super().encode()

    with patch.object(scene_module.support,'factory',factory),patch.object(scene_module.support,'ArmEffortGuard',support.ArmEffortGuard),patch.object(support.LearningScene,'_create_scene',support.create_effort),patch.object(support.base.string_trial_recording_v1,'StrapTrialRecording',support.base.GymTrialRecording),patch.object(support,'EffortRecording',Recording),patch.object(tracking.EffortRecording,'__init__',off.EffortRecording.__init__):
        run()
