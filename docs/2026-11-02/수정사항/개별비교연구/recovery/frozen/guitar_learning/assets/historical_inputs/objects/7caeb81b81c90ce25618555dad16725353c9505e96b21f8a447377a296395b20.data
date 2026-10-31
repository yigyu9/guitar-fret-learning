"""Six-scalar moving-guitar pick IK feeds the existing guarded human PD controller."""
from unittest.mock import patch
import numpy as np
from .initial_pose_noise_v1 import save,pose
from .upper_arm_static_geometry_v1 import calibrated_upper_fk
from .elbow_wrist_strike_source_v1 import solve_pick


def desired_point(time,initial,points):
    times=np.array([2.,2.6,2.9,3.2,3.55,3.75,4.45,4.7,5.])
    vertices=np.vstack([initial,points[0],points[1],points[1],points[2],points[2],points[3],points[3],points[4]])
    if time<=2:return initial.copy()
    k=min(np.searchsorted(times,time,side='right')-1,len(times)-2);t=np.clip((time-times[k])/(times[k+1]-times[k]),0,1)
    return (1-t)*vertices[k]+t*vertices[k+1]


def main():
    import isaacgym
    from . import run_right_body_approach_v1 as runner
    from . import right_block_body_effort_v5 as support
    from . import left_near_scene_v3 as scene_module
    from . import left_near_arm_effort_v3 as tracking
    from .left_wrist_tracking_off_v2 import EffortRecording as TrackingOff
    from .run_joint_hold import native_state
    from .native_contacts import body_names,read_contacts
    original_factory=support.factory;original_recording=support.EffortRecording

    def factory(recording,enabled):
        Parent=original_factory(recording,enabled)
        class Scene(Parent):
            def step(self,action):
                if not hasattr(self,'six_rows'):
                    initial=native_state(self);self.six_rows=[];self.six_fk,_=calibrated_upper_fk(self.names,self.human_bodies,initial,self.contract.q_ref)
                    self.six_indices=np.array([self.names.index(n+'_'+ax) for n in ('R_Elbow','R_Wrist') for ax in 'xyz']);gp,gr=pose(initial['guitar_body_states'][0]);self.six_initial_G=gr.inv().apply(pose(initial['human_body_states'][self.human_bodies.index('RH:pick')])[0]-gp)
                before=native_state(self);q=np.array([s['pos'] for s in before['human_dof_states']]);gp,gr=pose(before['guitar_body_states'][0]);time=self.steps/240;enabled=self.contract.config.get('six_joint_strike_enabled') is True
                request=self.contract.q_ref.copy();target=self.six_initial_G.copy();error=0.
                if enabled and time>=2:
                    target=desired_point(time,self.six_initial_G,np.array(self.contract.config['six_joint_strike_waypoints_G_m']))
                    fitted,error,_=solve_pick(self.six_fk,q,self.six_indices,self.contract.lower,self.contract.upper,self.contract.q_ref,gp+gr.apply(target),self.target[self.six_indices].astype(float))
                    values=fitted[self.six_indices]
                    norm=np.linalg.norm(values.reshape(2,3),axis=1)
                    if not(np.isfinite(values).all() and np.isfinite(error) and error<=.002 and np.all(norm<np.deg2rad(160)) and np.all(abs(values-self.contract.q_ref[self.six_indices])<=1.+1e-8) and np.all(values>=self.contract.lower[self.six_indices]) and np.all(values<=self.contract.upper[self.six_indices])):
                        raise RuntimeError('six-joint IK finite/position/bounds/principal hard gate rejected')
                    request[self.six_indices]=values
                mask=np.ones(81,dtype=bool);mask[self.six_indices]=False;assert np.array_equal(request[mask],self.contract.q_ref[mask])
                action=np.clip((request-self.contract.mid)/self.contract.half,-1,1)
                _,expected_final=self.contract.targets(action,self.target)
                final_norm=np.linalg.norm(expected_final[self.six_indices].astype(float).reshape(2,3),axis=1)
                if not(np.isfinite(expected_final).all() and np.all(final_norm<np.deg2rad(160))):
                    raise RuntimeError('rate-limited six-joint principal hard gate rejected')
                self.six_target_velocity=np.zeros(81)
                self.six_target_velocity[self.six_indices]=(expected_final[self.six_indices].astype(float)-self.target[self.six_indices].astype(float))*60
                if abs(self.six_target_velocity).max()>3.0001:raise RuntimeError('six target velocity exceeds original rate')
                result=super().step(action)
                assert np.array_equal(self.target,expected_final)
                assert np.array_equal(self.target[mask].astype(float),self.contract.q_ref[mask])
                self.six_rows.append({'physics_step_before':self.steps-4,'time_before_s':time,'enabled':enabled,'desired_pick_G_m':target.tolist(),'IK_position_error_m':error,'requested_target81_rad':request.tolist(),'final_target81_rad':self.target.astype(float).tolist(),'other75_exact':True,'actual_q81_before_rad':q.tolist()})
                return result
        return Scene

    class Recording(original_recording):
        def __init__(self,env,out):
            super().__init__(env,out);mapping=body_names(env.gym,env.env);previous=env.after_physics
            def observe(owner):
                previous(owner);state=native_state(owner);contacts=read_contacts(owner.gym,owner.env,mapping);row=self.endpoint_rows[-1]
                row['human_body_states']['RH:pick']=state['human_body_states'][owner.human_bodies.index('RH:pick')]
                row['chest_guitar_contacts']=[c for c in contacts if 'human/Chest' in (c['body0_name'],c['body1_name']) and any(n.startswith('guitar/') for n in (c['body0_name'],c['body1_name']))]
                row['trunk_guitar_contacts']=[c for c in contacts if any(n in ('human/Torso','human/Spine','human/Chest') for n in (c['body0_name'],c['body1_name'])) and any(n.startswith('guitar/') for n in (c['body0_name'],c['body1_name']))]
                assert native_state(owner)==state
            env.after_physics=observe
            self.velocity_rows=[];previous_control=env.right_effort_controller
            distal=np.array([env.names.index(n+'_'+ax) for n in ('R_Elbow','R_Wrist') for ax in 'xyz'])
            damping=np.array([3.,3.,3.,1.,1.,1.]);mask=np.ones(81,dtype=bool);mask[distal]=False
            def control():
                before=previous_control().copy()
                velocity=getattr(env,'six_target_velocity',np.zeros(81))[distal]
                requested=np.array(self.effort_rows[-1]['requested_efforts_Nm'])[distal]+damping*velocity
                final=before.copy();final[distal]=np.clip(requested,-env.pd_properties['effort'][distal],env.pd_properties['effort'][distal]).astype(np.float32)
                assert np.array_equal(final[mask],before[mask]) and np.isfinite(final).all()
                self.velocity_rows.append({'physics_step':env.steps,'indices':distal.tolist(),'D_Nms_rad':damping.tolist(),'target_velocity6_rad_s':velocity.tolist(),'original_raw_request6_Nm':np.array(self.effort_rows[-1]['requested_efforts_Nm'])[distal].tolist(),'velocity_term6_Nm':(damping*velocity).tolist(),'requested6_Nm':requested.tolist(),'before_velocity_efforts81_Nm':before.astype(float).tolist(),'actual_submitted_efforts81_Nm':final.astype(float).tolist(),'other75_efforts_exact':True})
                return final
            env.right_effort_controller=control
        def encode(self):
            save(self.out/'six_joint_target_rows.json',{'rows':getattr(self.env,'six_rows',[]),'scope':'6 requested/final target channels change; other75 fixed logical targets, not frozen actual states; current guitar pose, original rate and finite PD'})
            save(self.out/'six_velocity_effort_rows.json',{'rows':self.velocity_rows,'scope':'actual final submitted human81 after bounded target-velocity term on6 only'})
            import stability_adapter_2.left_wrist_tracking_off_v2 as off_module
            def scoped_save(path,value):
                if path.name in ('body_effort_rows.json','left_wrist_tracking_rows.json'):
                    value={**value,'scope':'before six target-velocity addition; actual final command in six_velocity_effort_rows.json'}
                return save(path,value)
            with patch.object(support,'save',scoped_save),patch.object(off_module,'save',scoped_save):
                return super().encode()

    with patch.object(scene_module.support,'factory',factory),patch.object(scene_module.support,'ArmEffortGuard',support.ArmEffortGuard),patch.object(support.LearningScene,'_create_scene',support.create_effort),patch.object(support.base.string_trial_recording_v1,'StrapTrialRecording',support.base.GymTrialRecording),patch.object(support,'EffortRecording',Recording),patch.object(tracking.EffortRecording,'__init__',TrackingOff.__init__):
        runner.main()


if __name__=='__main__':main()
