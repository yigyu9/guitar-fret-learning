"""Actual scalar body PD, gravity and proximal support task, all finite human efforts."""
import numpy as np
from . import right_block_effort_v4 as parent
from . import left_near_arm_effort_v2 as arm
from .initial_pose_noise_v1 import save, pose
from .dual_shoulder_effort_v1 import skew, right_indices

LearningScene = parent.LearningScene
base = parent.base


def owned_indices(names):
    return np.r_[[i for i,n in enumerate(names) if n.startswith(('Torso_','Spine_','Chest_'))],
                 right_indices(names), arm.left_arm_indices(names)].astype(int)


class ArmEffortGuard(arm.ArmEffortGuard):
    def __getattr__(self, name):
        if name != 'apply_actor_dof_efforts': return super().__getattr__(name)
        def submit(env, actor, efforts):
            owner = self.owner; value = np.asarray(efforts); mask = np.ones(81,dtype=bool); mask[owned_indices(owner.names)] = False
            if not(owner.integrating_control and owner.right_effort_window and env == owner.env and actor == owner.human and
                   value.shape == (81,) and np.isfinite(value).all() and np.all(value[mask] == 0) and
                   np.all(abs(value) <= owner.pd_properties['effort']+1e-6)):
                owner.forbidden_calls.append(name); raise RuntimeError('human body9+arms24 effort owner/cap violation')
            result = self.gym.apply_actor_dof_efforts(env,actor,value)
            if result is False: raise RuntimeError('human33 effort rejected')
            owner.right_effort_calls += 1
            return result
        return submit


def create_effort(owner):
    parent.create_effort(owner)
    from .environment import gymapi
    assert owner.contract.config.get('body9_effort') is True and not owner.initialization_complete
    indices = owner.contract.body; before = owner.gym.get_actor_dof_properties(owner.env,owner.human).copy(); requested = before.copy()
    requested['driveMode'][indices] = gymapi.DOF_MODE_EFFORT; requested['stiffness'][indices] = 0; requested['damping'][indices] = 0
    if not owner.gym.set_actor_dof_properties(owner.env,owner.human,requested): raise RuntimeError('body EFFORT setup rejected')
    actual = owner.gym.get_actor_dof_properties(owner.env,owner.human).copy(); assert np.array_equal(actual,requested)
    owner.body_mode = {'indices':indices.tolist(),'before':{k:before[k].tolist() for k in before.dtype.names},
                       'applied':{k:actual[k].tolist() for k in actual.dtype.names}}


def factory(recording, enabled):
    Parent = arm.factory(recording,enabled)
    class Scene(Parent):
        def step(self, action):
            from .run_joint_hold import native_state
            if self.contract.clock(self.steps)['diagnostic_time_limit']: raise RuntimeError('time limit reached')
            before = native_state(self); requested,final = self.contract.targets(action,self.target); self.target = final
            self.target_submission_allowed = True
            try: self._submit_targets()
            finally: self.target_submission_allowed = False
            actual = self.gym.get_actor_dof_position_targets(self.env,self.human); mask = np.ones(81,dtype=bool); mask[owned_indices(self.names)] = False
            preserved = native_state(self) == before
            if not(np.isfinite(actual).all() and np.array_equal(actual[mask],final[mask]) and preserved): raise RuntimeError('POSITION48 targets/state changed')
            self.position_command_rows.append({'physics_step':self.steps,'requested_target_rad':requested.tolist(),
                'logical_final_target_rad':final.astype(float).tolist(),'native_position_target_readback_rad':actual.astype(float).tolist(),
                'position48_exact':True,'state_preserved':preserved,'effort_scope':'body9+arms24 EFFORT; remaining48 POSITION'})
            self.integrating_control = True
            try:
                for _ in range(self.contract.physics_per_control): self.step_physics()
            finally: self.integrating_control = False
            return self.observe(),{'clock':self.contract.clock(self.steps),'requested_rad':requested.tolist(),'final_rad':final.astype(float).tolist(),'training_ready':False}
    return Scene


class EffortRecording(parent.EffortRecording):
    def __init__(self, env, out):
        super().__init__(env,out)
        from isaacgym import gymtorch
        from .run_joint_hold import native_state
        props = env.gym.get_actor_rigid_body_properties(env.env,env.human); masses = np.array([p.mass for p in props])
        com = np.array([[p.com.x,p.com.y,p.com.z] for p in props]); tensor = gymtorch.wrap_tensor(env.gym.acquire_jacobian_tensor(env.sim,'human'))
        indices = env.contract.body; self.body_rows = []
        save(self.out/'body_effort_configuration.json',{'indices':indices.tolist(),'K_Nm_rad':150,'D_Nms_rad':1,
            'mass_kg':masses.tolist(),'COM_local_m':com.tolist(),'mode_properties':env.body_mode,'rule':'gravity+actual scalar PD+two proximal point tasks; finite human33 effort'})
        previous = env.right_effort_controller
        def control():
            before = previous().copy(); state = native_state(env); jac = tensor.detach().cpu().numpy()[0].astype(float).copy()
            gravity = np.zeros(81); gravity_Jz = []
            for i in range(1,len(env.human_bodies)):
                _,r = pose(state['human_body_states'][i]); block = jac[i-1]
                j = block[:3] if self.mode == 'COM' else block[:3]-skew(r.apply(com[i]))@block[3:]
                gravity_Jz.append(j[2,indices].tolist())
                gravity -= j.T@(masses[i]*np.array([0,0,-9.81]))
            q = np.array([s['pos'] for s in state['human_dof_states']]); qdot = np.array([s['vel'] for s in state['human_dof_states']])
            if not np.isfinite(np.r_[q,qdot]).all() or abs(qdot).max() > 50: raise RuntimeError('unsafe native joint state before physics')
            task = sum((np.array(p['jacobian_all']).T@np.array(p['virtual_force_request_W_N']) for p in self.two_block_rows[-1]['points']),np.zeros(81))
            posture = 150*(env.target[indices]-q[indices])-qdot[indices]; requested = gravity[indices]+task[indices]+posture
            final = before.copy(); final[indices] = np.clip(requested,-env.pd_properties['effort'][indices],env.pd_properties['effort'][indices]).astype(np.float32)
            self.body_rows.append({'physics_step':env.steps,'q_body_rad':q[indices].tolist(),'qdot_body_rad_s':qdot[indices].tolist(),
                'target_body_rad':env.target[indices].astype(float).tolist(),'gravity_body_Nm':gravity[indices].tolist(),'gravity_COM_z_J_body9':gravity_Jz,'task_body_Nm':task[indices].tolist(),
                'posture_body_Nm':posture.tolist(),'requested_body_Nm':requested.tolist(),'before_efforts_Nm':before.astype(float).tolist(),'final_efforts_Nm':final.astype(float).tolist()})
            row = self.tracking_rows[-1]; row['before_body9_efforts_Nm'] = row.pop('actual_combined_submitted_efforts_Nm'); row['actual_combined_submitted_efforts_Nm'] = final.astype(float).tolist()
            assert native_state(env) == state
            return final
        env.right_effort_controller = control

    def encode(self):
        save(self.out/'body_effort_rows.json',{'rows':self.body_rows,'scope':'actual final human81 vector after body9+arms24; two_block final is before body9'})
        from unittest.mock import patch
        def scoped_save(path, value):
            if path.name == 'position_command_rows.json': value = {**value, 'scope':'POSITION48 readback/state preserved; body9+arms24 EFFORT readback ignored'}
            if path.name == 'two_block_rows.json': value = {**value, 'scope':'proximal arm command before body9; actual final in body_effort_rows and updated tracking'}
            return save(path,value)
        with patch.object(parent,'save',scoped_save), patch.object(parent.parent,'save',scoped_save):
            return super().encode()
