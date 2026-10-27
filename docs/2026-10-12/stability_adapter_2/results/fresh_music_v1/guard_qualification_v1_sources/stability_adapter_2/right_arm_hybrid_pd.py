"""Right-arm human joint PD torque plus implicit damping, no guitar/root forces."""
from .underneck_pose_trial_v5 import UnderneckEnvironment
from .environment import np, gymapi
from isaacgym import gymtorch
import torch


class RightArmHybridEnvironment(UnderneckEnvironment):
    def __init__(self,candidate):
        super().__init__(candidate)
        self.hybrid_indices=np.array([i for i,n in enumerate(self.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
        props=self.gym.get_actor_dof_properties(self.env,self.human).copy()
        self.hybrid_kp=props['stiffness'].copy();self.hybrid_limits=props['effort'].copy()
        props['stiffness'][self.hybrid_indices]=0
        if not self.gym.set_actor_dof_properties(self.env,self.human,props):raise RuntimeError('hybrid PD init failed')
        if self.gym.get_sim_dof_count(self.sim)!=len(self.names):raise RuntimeError('human-only DOF layout required')
        self.hybrid_torque=torch.zeros(len(self.names),dtype=torch.float32)
        self.hybrid_commands=[]

    def step_physics(self):
        if self.steps%4==0:
            actual=self.gym.get_actor_dof_states(self.env,self.human,gymapi.STATE_ALL)['pos']
            torque=np.zeros(len(self.names),dtype=np.float32);idx=self.hybrid_indices
            torque[idx]=np.clip(self.hybrid_kp[idx]*(self.target[idx]-actual[idx]),-self.hybrid_limits[idx],self.hybrid_limits[idx])
            if not np.isfinite(torque).all():raise ValueError('nonfinite human joint PD torque')
            self.hybrid_torque.copy_(torch.from_numpy(torque))
            self.hybrid_commands.append({'before_physics_step':self.steps,'target_rad':self.target.tolist(),'actual_rad':actual.tolist(),'human_joint_torque_Nm':torque.tolist()})
        # Exactly the human joint actuator API used by source Strike. NoStrapGym still
        # guards root/body forces and state writes. Only this bounded joint vector
        # bypasses that older, deliberately broad force/effort guard.
        if not self.gym.gym.set_dof_actuation_force_tensor(self.sim,gymtorch.unwrap_tensor(self.hybrid_torque)):
            raise RuntimeError('native human joint torque submission failed')
        super().step_physics()
