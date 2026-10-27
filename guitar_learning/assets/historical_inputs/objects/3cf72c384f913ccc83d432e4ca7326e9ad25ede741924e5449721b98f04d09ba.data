"""Finite right-arm task-point impedance via guarded human joint efforts."""
from unittest.mock import patch
import numpy as np
from . import run_om_no_strap_upper_arm_v9 as pose_trial
from .learning_scene_v2 import LearningScene
from . import construction_property_guard_v1 as guard_module
from .initial_pose_noise_v1 import save,pose
from .strap import point_kinematics

hold=pose_trial.hold;preload=hold.preload;base=hold.base
create_original=LearningScene._create_scene

def right_indices(names):
    indices=np.array([i for i,n in enumerate(names)if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
    assert len(indices)==12
    return indices

class ArmEffortGuard(guard_module.ConstructionPropertyGuard):
    def __getattr__(self,name):
        if name!='apply_actor_dof_efforts':return super().__getattr__(name)
        def controlled(env,actor,efforts):
            owner=self.owner;value=np.asarray(efforts);right=right_indices(owner.names);other=np.ones(81,dtype=bool);other[right]=False
            if not (owner.integrating_control and owner.right_effort_window and env==owner.env and actor==owner.human and value.shape==(81,) and np.isfinite(value).all() and np.all(value[other]==0) and np.all(abs(value)<=owner.pd_properties['effort']+1e-6)):
                owner.forbidden_calls.append(name);raise RuntimeError('human effort outside declared right-arm owner/caps')
            result=self.gym.apply_actor_dof_efforts(env,actor,value)
            if result is False:raise RuntimeError('right human actuator effort rejected')
            owner.right_effort_calls+=1
            return result
        return controlled

def create_effort(self):
    create_original(self);assert not self.initialization_complete
    right=right_indices(self.names);before=self.gym.get_actor_dof_properties(self.env,self.human).copy();requested=before.copy()
    from .environment import gymapi
    requested['driveMode'][right]=gymapi.DOF_MODE_EFFORT;requested['stiffness'][right]=0;requested['damping'][right]=0
    if not self.gym.set_actor_dof_properties(self.env,self.human,requested):raise RuntimeError('right EFFORT construction rejected')
    actual=self.gym.get_actor_dof_properties(self.env,self.human).copy();assert np.array_equal(actual,requested)
    self.right_effort_window=False;self.right_effort_calls=0
    self.right_effort_properties={'before':{n:before[n].tolist()for n in before.dtype.names},'applied':{n:actual[n].tolist()for n in actual.dtype.names},'right_indices':right.tolist(),'construction_override_calls':1,'scope':'right12 EFFORT; POSITION targets ignored there; other69 POSITION'}

def skew(v):
    x,y,z=v;return np.array([[0,-z,y],[z,0,-x],[-y,x,0]])

def factory(recording,enabled):
    Parent=base.original_factory(recording,False)
    class EffortScene(Parent):
        def step(self,action):
            from .run_joint_hold import native_state
            if self.contract.clock(self.steps)['diagnostic_time_limit']:raise RuntimeError('diagnostic time limit reached')
            before=native_state(self);requested,final=self.contract.targets(action,self.target);self.target=final;self.target_submission_allowed=True
            try:self._submit_targets()
            finally:self.target_submission_allowed=False
            actual=self.gym.get_actor_dof_position_targets(self.env,self.human);after=native_state(self);right=right_indices(self.names);mask=np.ones(81,dtype=bool);mask[right]=False
            self.position_command_rows.append({'physics_step':self.steps,'requested_target_rad':requested.tolist(),'logical_final_target_rad':final.astype(float).tolist(),'native_position_target_readback_rad':actual.astype(float).tolist(),'position69_exact':bool(np.array_equal(actual[mask],final[mask])),'state_preserved':after==before,'right_scope':'EFFORT mode; position target readback is not an actuator command'})
            if not np.isfinite(actual).all() or not np.array_equal(actual[mask],final[mask]) or after!=before:raise AssertionError('POSITION69 readback or state preservation failed')
            self.integrating_control=True
            try:
                for _ in range(self.contract.physics_per_control):self.step_physics()
            finally:self.integrating_control=False
            return self.observe(),{'clock':self.contract.clock(self.steps),'requested_rad':requested.tolist(),'final_rad':final.astype(float).tolist(),'training_ready':False}

        def step_physics(self):
            assert self.integrating_control and not self.right_effort_window
            efforts=self.right_effort_controller()
            self.right_effort_window=True
            try:self.gym.apply_actor_dof_efforts(self.env,self.human,efforts)
            finally:self.right_effort_window=False
            super().step_physics()
    return EffortScene

class EffortRecording(preload.endpoint.EndpointRecording):
    def __init__(self,env,out):
        super().__init__(env,out)
        from .run_joint_hold import native_state
        from .environment import gymapi
        from isaacgym import gymtorch
        before=native_state(env);self.right=right_indices(env.names);q0=env.contract.q_ref.copy();gp,gr=pose(before['guitar_body_states'][0]);row=env.contract.candidate['no_strap_upper_arm_proposal']['proximal_support'];surface=np.array(row['guitar_surface_G_m']);normal=np.array(row['capsule_axis_G_m'])-surface;normal/=np.linalg.norm(normal)
        p,r=pose(before['human_body_states'][env.human_bodies.index('R_Elbow')]);witness=gp+gr.apply(surface+normal*row['gap_m']);local=r.inv().apply(witness-p);desired=witness.copy()
        props=env.gym.get_actor_rigid_body_properties(env.env,env.human);com=np.array([[v.com.x,v.com.y,v.com.z]for v in props]);mass=np.array([v.mass for v in props]);tensor=gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim,'human'));expected=(1,len(env.human_bodies)-1,6,81);assert tuple(tensor.shape)==expected
        shape_props={}
        for actor,label in [(env.human,'human'),(env.guitar,'guitar')]:
            names=env.gym.get_actor_rigid_body_names(env.env,actor);ranges=env.gym.get_actor_rigid_body_shape_indices(env.env,actor);shapes=env.gym.get_actor_rigid_shape_properties(env.env,actor)
            shape_props[label]={name:[{'filter':int(shapes[j].filter),'contact_offset_m':float(shapes[j].contact_offset),'rest_offset_m':float(shapes[j].rest_offset),'friction':float(shapes[j].friction),'rolling_friction':float(shapes[j].rolling_friction),'torsion_friction':float(shapes[j].torsion_friction)}for j in range(span.start,span.start+span.count)]for name,span in zip(names,ranges)}
        save(self.out/'actual_shape_properties.json',shape_props);assert all(a['filter']&b['filter']==0 for a in shape_props['human']['R_Elbow']for b in shape_props['guitar']['G:body'])
        kp=np.zeros(81);kd=np.zeros(81)
        for i in self.right:
            prefix=env.names[i].split('_')[1];kp[i],kd[i]={'Thorax':(30,1),'Shoulder':(60,3),'Elbow':(60,3),'Wrist':(20,1)}[prefix]
        save(self.out/'effort_configuration.json',{'right_indices':self.right.tolist(),'motor_reference_local_m':local.tolist(),'desired_motor_point_W_m':desired.tolist(),'source_normal_G':normal.tolist(),'K_point_N_m':0,'D_point_Ns_m':0,'point_force_cap_N':0,'K_posture_Nm_rad':kp.tolist(),'D_posture_Nms_rad':kd.tolist(),'q_ref_rad':q0.tolist(),'human_mass_kg':mass.tolist(),'human_COM_local_m':com.tolist(),'jacobian_shape':list(expected),'joint_effort_caps_Nm':env.pd_properties['effort'].tolist(),'right_mode_properties':env.right_effort_properties,'world_goal_fixed':True,'source_target_local_G_m':gr.inv().apply(desired-gp).tolist(),'initial_guitar_p_W_m':gp.tolist(),'initial_guitar_q_xyzw':gr.as_quat().tolist(),'guitar_root_COM_local_m':env.com[env.guitar_bodies[0]].tolist(),'support_body':'R_Elbow','reference_point_scope':'source forearm motor reference, not measured contact point/penetration/force; desired setup is initial only; rows keep initial world human motor goal; current guitar is observed'})
        self.elbow_index=env.names.index('R_Elbow_y');self.motion_amplitude=float(env.contract.config.get('elbow_motion_amplitude_rad',0));assert self.motion_amplitude in (0,float(np.deg2rad(2)),float(np.deg2rad(5)));assert q0[self.elbow_index]-self.motion_amplitude>=env.contract.lower[self.elbow_index] and q0[self.elbow_index]+self.motion_amplitude<=env.contract.upper[self.elbow_index]
        save(self.out/'elbow_motion_configuration.json',{'index':self.elbow_index,'joint_name':'R_Elbow_y','amplitude_rad':self.motion_amplitude,'start_s':2.5,'end_s':4.5,'frequency_Hz':.5,'scope':'single native scalar DOF target, not world rotation axis'})
        self.effort_rows=[];env.position_command_rows=[];self.mode='COM';self.initial_gp,self.initial_gr=gp,gr;self.last_desired=desired.copy();self.safety_stopped=False;index=env.human_bodies.index('R_Elbow')
        def control():
            state=native_state(env);env.gym.refresh_jacobian_tensors(env.sim);jac=tensor.detach().cpu().numpy()[0].astype(float).copy();assert np.isfinite(jac).all();actual=np.array([v['pos']for v in state['human_dof_states']]);velocity=np.array([v['vel']for v in state['human_dof_states']]);body=state['human_body_states'][index];p,r=pose(body);linear=np.array([body['vel']['linear'][k]for k in 'xyz']);angular=np.array([body['vel']['angular'][k]for k in 'xyz']);point,point_velocity=point_kinematics(p,r.as_quat(),linear,angular,local,com[index]);block=jac[index-1]
            candidates={mode:block[:3]-skew(r.apply(local-(com[index]if mode=='COM' else 0)) )@block[3:]for mode in ('COM','origin')};errors={mode:float(np.linalg.norm(j@velocity-point_velocity))for mode,j in candidates.items()}
            if abs(errors['COM']-errors['origin'])>1e-9:self.mode=min(errors,key=errors.get)
            if errors[self.mode]>.01:raise RuntimeError('native point Jacobian velocity mismatch')
            point_j=candidates[self.mode];gbody=state['guitar_body_states'][0];current_gp,current_gr=pose(gbody);self.safety_stopped=self.safety_stopped or np.linalg.norm(current_gp-self.initial_gp)>.20 or np.rad2deg((self.initial_gr.inv()*current_gr).magnitude())>35
            target_velocity=np.zeros(3);glinear=np.array([gbody['vel']['linear'][k]for k in 'xyz']);gangular=np.array([gbody['vel']['angular'][k]for k in 'xyz'])
            # Initial world motor goal is kept for this static support test; guitar pose remains free.
            desired=self.last_desired;force=np.zeros(3);gravity=np.zeros(81)
            for i in range(1,len(env.human_bodies)):
                j=jac[i-1];_,rot=pose(state['human_body_states'][i]);jcom=j[:3]if self.mode=='COM'else j[:3]-skew(rot.apply(com[i]))@j[3:];gravity-=jcom.T@(mass[i]*np.array([0,0,-9.81]))
            time=env.steps/240;target=env.target.astype(float).copy();target_vel=np.zeros(81)
            if 2.5<=time<4.5:target[self.elbow_index]+=self.motion_amplitude*np.sin(np.pi*(time-2.5));target_vel[self.elbow_index]=self.motion_amplitude*np.pi*np.cos(np.pi*(time-2.5))
            task=point_j.T@force;posture=kp*(target-actual)-kd*(velocity-target_vel);request=np.zeros(81);request[self.right]=(gravity+task+posture)[self.right];submitted=np.clip(request,-env.pd_properties['effort'],env.pd_properties['effort']).astype(np.float32)
            self.effort_rows.append({'physics_step':env.steps,'motor_point_W_m':point.tolist(),'desired_motor_point_W_m':desired.tolist(),'desired_velocity_W_m_s':target_velocity.tolist(),'current_guitar_p_W_m':current_gp.tolist(),'current_guitar_q_xyzw':current_gr.as_quat().tolist(),'guitar_root_linear_COM_W_m_s':glinear.tolist(),'guitar_root_angular_W_rad_s':gangular.tolist(),'safety_stopped':bool(self.safety_stopped),'motor_velocity_W_m_s':point_velocity.tolist(),'selected_jacobian_frame':self.mode,'jacobian_velocity_errors_m_s':errors,'point_jacobian_right':point_j[:,self.right].tolist(),'point_jacobian_all':point_j.tolist(),'qdot_all_rad_s':velocity.tolist(),'point_force_request_W_N':force.tolist(),'gravity_right_Nm':gravity[self.right].tolist(),'posture_right_Nm':posture[self.right].tolist(),'requested_efforts_Nm':request.tolist(),'submitted_efforts_Nm':submitted.astype(float).tolist(),'posture_target_rad':target.tolist(),'posture_target_velocity_rad_s':target_vel.tolist(),'q_right_rad':actual[self.right].tolist(),'qdot_right_rad_s':velocity[self.right].tolist()});assert native_state(env)==state
            return submitted
        sh_index=env.human_bodies.index('R_Shoulder');sp,sr=pose(before['human_body_states'][sh_index]);upper=env.contract.candidate['body_side_lean_axilla']['proximal_upper_arm65_witness'];upper_surface=np.array(upper['guitar_surface_G_m']);upper_normal=np.array(upper['capsule_axis_G_m'])-upper_surface;upper_normal/=np.linalg.norm(upper_normal);upper_witness=gp+gr.apply(upper_surface+upper_normal*upper['gap_m']);upper_local=sr.inv().apply(upper_witness-sp);upper_desired=upper_witness-.004*gr.apply(upper_normal)
        save(self.out/'axilla_effort_configuration.json',{'source_segment_fraction_limit':.3,'support_body':'R_Shoulder','motor_reference_local_m':upper_local.tolist(),'desired_motor_point_W_m':upper_desired.tolist(),'source_upper_normal_G':upper_normal.tolist(),'K_point_N_m':2000,'D_point_Ns_m':30,'point_force_cap_N':10,'world_goal_fixed':True,'scope':'human proximal upper-arm motor reference only; not measured contact point or force; combined human actuator efforts only'})
        self.axilla_rows=[]
        def combined_control():
            control();state=native_state(env);row=self.effort_rows[-1];actual_velocity=np.array([v['vel']for v in state['human_dof_states']]);sh=state['human_body_states'][sh_index];sp,sr=pose(sh);linear=np.array([sh['vel']['linear'][k]for k in 'xyz']);angular=np.array([sh['vel']['angular'][k]for k in 'xyz']);point,velocity=point_kinematics(sp,sr.as_quat(),linear,angular,upper_local,com[sh_index]);jac=tensor.detach().cpu().numpy()[0].astype(float).copy();block=jac[sh_index-1];candidates={mode:block[:3]-skew(sr.apply(upper_local-(com[sh_index]if mode=='COM'else 0)))@block[3:]for mode in ('COM','origin')};errors={mode:float(np.linalg.norm(j@actual_velocity-velocity))for mode,j in candidates.items()};mode=min(errors,key=errors.get)
            if errors[mode]>.01:raise RuntimeError('native axilla point Jacobian velocity mismatch')
            point_j=candidates[mode];child=np.array([i for i,n in enumerate(env.names)if n.startswith(('R_Elbow','R_Wrist'))]);child_max=float(np.abs(point_j[:,child]).max());assert child_max<1e-10
            force=2000*(upper_desired-point)-30*velocity;force*=min(1,10/max(float(np.linalg.norm(force)),1e-12));task=point_j.T@force;request=np.array(row['requested_efforts_Nm']);request[self.right]+=task[self.right];submitted=np.clip(request,-env.pd_properties['effort'],env.pd_properties['effort']).astype(np.float32);row['axilla_point_task_right_Nm']=task[self.right].tolist();row['requested_efforts_Nm']=request.tolist();row['submitted_efforts_Nm']=submitted.astype(float).tolist()
            self.axilla_rows.append({'physics_step':env.steps,'motor_point_W_m':point.tolist(),'motor_velocity_W_m_s':velocity.tolist(),'desired_motor_point_W_m':upper_desired.tolist(),'selected_jacobian_frame':mode,'jacobian_velocity_errors_m_s':errors,'point_jacobian_all':point_j.tolist(),'qdot_all_rad_s':actual_velocity.tolist(),'point_force_request_W_N':force.tolist(),'child_jacobian_max_abs':child_max,'task_right_Nm':task[self.right].tolist()});assert native_state(env)==state
            return submitted
        env.right_effort_controller=combined_control
        from .native_contacts import body_names,read_contacts
        mapping=body_names(env.gym,env.env);previous=env.after_physics
        def head_observation(owner):
            previous(owner);state=native_state(owner);contacts=read_contacts(owner.gym,owner.env,mapping);self.endpoint_rows[-1]['head_guitar_contacts']=[c for c in contacts if 'human/Head'in(c['body0_name'],c['body1_name']) and any(n.startswith('guitar/')for n in(c['body0_name'],c['body1_name']))];self.endpoint_rows[-1]['right_forearm_body_contacts']=[c for c in contacts if 'human/R_Elbow'in(c['body0_name'],c['body1_name'])and'guitar/G:body'in(c['body0_name'],c['body1_name'])];self.endpoint_rows[-1]['human_body_states'].update({n:state['human_body_states'][owner.human_bodies.index(n)]for n in ['R_Elbow','R_Wrist','RH:palm','Chest','R_Thorax','R_Hip','L_Hip','Torso','Spine','Neck','Head','L_Thorax']});self.endpoint_rows[-1]['right_distal_guitar_contacts']=[c for c in contacts if any(n.startswith('guitar/')for n in(c['body0_name'],c['body1_name']))and any(n in('human/R_Elbow','human/R_Wrist')or n.startswith('human/RH:')for n in(c['body0_name'],c['body1_name']))];self.endpoint_rows[-1]['right_thorax_body_contacts']=[c for c in contacts if 'human/R_Thorax'in(c['body0_name'],c['body1_name'])and'guitar/G:body'in(c['body0_name'],c['body1_name'])];self.endpoint_rows[-1]['right_hip_body_contacts']=[c for c in contacts if 'human/R_Hip'in(c['body0_name'],c['body1_name'])and'guitar/G:body'in(c['body0_name'],c['body1_name'])];assert native_state(owner)==state
        env.after_physics=head_observation;assert native_state(env)==before

    def encode(self):
        save(self.out/'axilla_effort_rows.json',{'scope':'additional human upper-arm point command, not measured contact force','rows':self.axilla_rows})
        save(self.out/'position_command_rows.json',{'scope':'POSITION69 exact readback; right EFFORT12 ignored position readback recorded separately','rows':self.env.position_command_rows});save(self.out/'effort_control_rows.json',{'scope':'human actuator commands before each physics step; not measured drive/contact force','rows':self.effort_rows,'right_effort_calls':self.env.right_effort_calls,'right_effort_window_closed':not self.env.right_effort_window});return super().encode()
