"""Current-first whole-frame sampling compatibility, with qualified k-1 fallback.

Only validation selection changes. Torque Jacobians, gains, support forces and
caps are copied unchanged from the consumed v5 controller. A passing candidate
certifies the stated velocity residual tolerance, not a solver cause or torque
Jacobian accuracy. No body/component-wise minimum mixes timestamps.
"""
import numpy as np
from scipy.spatial.transform import Rotation
from .environment_v2 import MusicGuitarEnvironment as PreviousEnvironment, collect_inputs
from ..fresh_learning_v1.environment_v5 import ScalarEffortController as PreviousController
from ..fresh_learning_v1.environment_v5 import JacobianConsistencyError, aligned_validation_jacobian


def choose_validation_alignment(current_error,previous_error,threshold=.01):
    if not np.isfinite(current_error) or current_error<0:
        raise ValueError('finite nonnegative current residual required')
    if previous_error is not None and (not np.isfinite(previous_error) or previous_error<0):
        raise ValueError('finite nonnegative previous residual required')
    if current_error<=threshold: return 'current'
    if previous_error is not None and previous_error<=threshold: return 'previous_k_minus_1'
    raise ValueError('neither whole-frame candidate meets velocity tolerance')


class ScalarEffortController(PreviousController):
    def _point_residual(self,jac,body,local,rotation,state,qdot):
        from ..dual_shoulder_effort_v1 import skew
        row = state['human_body_states'][body]
        vec = lambda key:np.array([row['vel'][key][k] for k in 'xyz'])
        lever = rotation.apply(local-self.com[body])
        point_j = jac[body-1,:3]-skew(lever)@jac[body-1,3:]
        reference = vec('linear')+np.cross(vec('angular'),lever)
        return float(np.linalg.norm(point_j@qdot-reference))

    def _validation_jacobian(self,current,state,qdot):
        s = self.scene
        previous,previous_step = aligned_validation_jacobian(current,self.previous_jacobian,
            s.steps,self.previous_jacobian_step,qdot)
        self.current_rotations = [Rotation.from_quat([row['pose']['r'][k] for k in 'xyzw'])
                                  for row in state['human_body_states']]
        candidates = {'current':(current,s.steps,self.current_rotations)}
        if s.steps:
            if not hasattr(self,'previous_rotations'): raise RuntimeError('missing exact k-1 pose history')
            candidates['previous_k_minus_1'] = (previous,previous_step,self.previous_rotations)
        reports = {}
        for name,(jac,step,rotations) in candidates.items():
            com,angular,points = [],[],[]
            for i,row in enumerate(state['human_body_states'][1:],1):
                linear = np.array([row['vel']['linear'][k] for k in 'xyz'])
                omega = np.array([row['vel']['angular'][k] for k in 'xyz'])
                if not np.isfinite(np.r_[linear,omega]).all(): raise RuntimeError('nonfinite native velocity')
                com.append(dict(body=s.human_bodies[i],error_m_s=float(np.linalg.norm(jac[i-1,:3]@qdot-linear))))
                angular.append(dict(body=s.human_bodies[i],error_rad_s=float(np.linalg.norm(jac[i-1,3:]@qdot-omega))))
            for i,local,goal,cap,owned in self.references:
                points.append(dict(body=s.human_bodies[i],error_m_s=self._point_residual(jac,i,local,rotations[i],state,qdot)))
            reports[name] = dict(jacobian_physics_step=step,COM_max_m_s=max(r['error_m_s'] for r in com),
                support_point_max_m_s=max((r['error_m_s'] for r in points),default=0.),
                angular_max_rad_s=max(r['error_rad_s'] for r in angular),body_COM_errors=com,
                body_angular_errors=angular,support_point_errors=points)
            reports[name]['gate_max_m_s'] = max(reports[name]['COM_max_m_s'],reports[name]['support_point_max_m_s'])
        report = dict(physics_step=s.steps,threshold_m_s=.01,candidates=reports,
            selection_rule='current first; exact k-1 whole candidate fallback; both invalid fatal',
            support_point_definition='candidate J and candidate pose lever on both Jpoint and native COM+omega cross lever; no mixed pose lever',
            angular_scope='rad/s diagnostics only; no new angular threshold',
            effort_jacobian_physics_step=s.steps)
        try:
            selected = choose_validation_alignment(reports['current']['gate_max_m_s'],
                reports.get('previous_k_minus_1',{}).get('gate_max_m_s'))
        except ValueError:
            report.update(kind='whole_frame_sampling_compatibility_failure',native_state=state,
                          faulting_controller_effort_submitted=False)
            self.last_diagnostic = report
            raise JacobianConsistencyError('neither coherent Jacobian candidate matches native velocities',report)
        report['selected'] = selected
        self.alignment_report = report
        self.selected_rotations = candidates[selected][2]
        return candidates[selected][:2]

    def __call__(self):
        from ..run_joint_hold import native_state
        from ..initial_pose_noise_v1 import pose
        from ..dual_shoulder_effort_v1 import skew
        from ..strap import point_kinematics
        s = self.scene
        state = native_state(s)
        q = np.array([v['pos'] for v in state['human_dof_states']])
        qdot = np.array([v['vel'] for v in state['human_dof_states']])
        if not np.isfinite(np.r_[q,qdot]).all() or abs(qdot).max()>50: raise RuntimeError('unsafe native joint state')
        s.gym.refresh_jacobian_tensors(s.sim)
        jac = self.tensor.detach().cpu().numpy()[0].astype(float)
        if not np.isfinite(jac).all(): raise RuntimeError('nonfinite Jacobian')
        # Fixed-root native Jacobians are COM Jacobians. The exact replay in
        # diagnostic_v4 identifies solver velocity / updated pose timestamp lag.
        validation_jac,validation_step = self._validation_jacobian(jac,state,qdot)
        vec = lambda body,key:np.array([body['vel'][key][k] for k in 'xyz'])
        errors = {'current_COM':0.,'selected_COM':0.}
        body_errors = []
        for i in range(1,len(s.human_bodies)):
            body = state['human_body_states'][i]
            native = vec(body,'linear')
            if not np.isfinite(native).all(): raise RuntimeError('nonfinite native COM velocity')
            current_error = float(np.linalg.norm(jac[i-1,:3]@qdot-native))
            validation_error = float(np.linalg.norm(validation_jac[i-1,:3]@qdot-native))
            errors['current_COM'] = max(errors['current_COM'],current_error)
            errors['selected_COM'] = max(errors['selected_COM'],validation_error)
            body_errors.append({'body':s.human_bodies[i],'current_error_m_s':current_error,
                'validation_error_m_s':validation_error,'native_COM_velocity_W_m_s':native.tolist(),
                'validation_J_qdot_W_m_s':(validation_jac[i-1,:3]@qdot).tolist()})
        if errors['selected_COM']>.01:
            diagnostic = {'kind':'aligned_COM_Jacobian_velocity_consistency','physics_step':s.steps,
                'validation_jacobian_physics_step':validation_step,'threshold_m_s':.01,
                'mode_max_errors_m_s':errors,'body_errors':body_errors,'native_state':state,
                'faulting_controller_effort_submitted':False}
            self.last_diagnostic = diagnostic
            raise JacobianConsistencyError('aligned COM Jacobian native velocity mismatch',diagnostic)
        mode = 'COM'
        gravity = np.zeros(81)
        for i in range(1,len(s.human_bodies)):
            _,r = pose(state['human_body_states'][i])
            j = jac[i-1,:3] if mode=='COM' else jac[i-1,:3]-skew(r.apply(self.com[i]))@jac[i-1,3:]
            gravity += 9.81*self.mass[i]*j[2]
        task = np.zeros(81)
        guitar = state['guitar_body_states'][0]
        gp,gr = pose(guitar)
        for i,local,goal,cap,owned in self.references:
            body = state['human_body_states'][i]
            p,r = pose(body)
            point,velocity = point_kinematics(p,r.as_quat(),vec(body,'linear'),vec(body,'angular'),local,self.com[i])
            desired,dvelocity = point_kinematics(gp,gr.as_quat(),vec(guitar,'linear'),vec(guitar,'angular'),goal,s.com[s.guitar_bodies[0]])
            j = jac[i-1,:3]-skew(r.apply(local-(self.com[i] if mode=='COM' else 0)))@jac[i-1,3:]
            point_error = self._point_residual(validation_jac,i,local,self.selected_rotations[i],state,qdot)
            if point_error>.01:
                diagnostic = {'kind':'aligned_support_point_consistency','physics_step':s.steps,
                    'validation_jacobian_physics_step':validation_step,'body':s.human_bodies[i],
                    'threshold_m_s':.01,'error_m_s':point_error,'native_state':state,
                    'mode_max_errors_m_s':errors,'body_errors':body_errors,'faulting_controller_effort_submitted':False}
                self.last_diagnostic = diagnostic
                raise JacobianConsistencyError('aligned support point Jacobian mismatch',diagnostic)
            force = 2000*(desired-point)+30*(dvelocity-velocity)
            force *= min(1.,cap/max(float(np.linalg.norm(force)),1e-12))
            task[owned] += (j.T@force)[owned]
        request = gravity+self.kp*(s.target-q)-self.kd*qdot+task
        efforts = np.zeros(81,dtype=np.float32)
        efforts[self.indices] = np.clip(request[self.indices],-s.pd_properties['effort'][self.indices],s.pd_properties['effort'][self.indices])
        if not np.isfinite(efforts).all(): raise RuntimeError('nonfinite effort')
        self.last = {'physics_step':s.steps,'target81_rad':s.target.tolist(),'submitted_effort81_Nm':efforts.tolist(),
            'jacobian_mode':mode,'velocity_error_m_s':errors['selected_COM'],
            'current_pose_velocity_error_m_s':errors['current_COM'],'validation_jacobian_physics_step':validation_step,
            'effort_jacobian_physics_step':s.steps,'validation_alignment':self.alignment_report}
        self.previous_rotations = self.current_rotations
        self.previous_jacobian = jac.copy()
        self.previous_jacobian_step = s.steps
        return efforts


class MusicGuitarEnvironment(PreviousEnvironment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.abi.update(version='fresh_music_native_v3',velocity_validation=dict(
            rule='current-first whole COM+support; qualified exact k-1 fallback; both fail fatal',
            threshold_m_s=.01,angular='diagnostic rad/s only',
            support_lever='candidate pose on both sides',effort_J='current unchanged'))

    def reset(self,seed=None):
        observation = super().reset(seed=seed)
        self.controller = ScalarEffortController(self.scene,self.config['proximal_feedback'])
        self.scene.right_effort_controller = self.controller
        self.metadata['velocity_validation'] = self.abi['velocity_validation']
        return observation
