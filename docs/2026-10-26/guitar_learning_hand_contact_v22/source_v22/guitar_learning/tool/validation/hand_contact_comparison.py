"""Matched short hand-contact ablations; legacy timing is a diagnostic control only."""
import argparse
import hashlib
from pathlib import Path


def legacy_gate(now, onset, end, press, finger, contact, distance):
    """Frozen v20 gate formula, with explicit tracking-on control weight.

    Reproduces the preceding experiment's timing, without importing archive or
    loading an old checkpoint into the changed collision/observation contract.
    """
    import torch
    n,m=now.numel(),onset.numel()
    assigned=finger[None]==torch.arange(1,5,device=finger.device)[:,None]
    relevant=(now[:,None]>=press[None]-2)&(now[:,None]<=end[None])
    own=relevant[:,None]&assigned[None]
    near=((distance<=.04)[:,None]&own).any(-1)
    invalid=((~torch.isfinite(distance))[:,None]&own).any(-1)
    contact_veto=contact&own.any(-1)
    idle=now.new_ones(n,4)
    if m:
        busy=torch.minimum(((now[:,None]-(press[None]-.5))/.15).clamp(0,1),
                           ((end[None]+.15-now[:,None])/.15).clamp(0,1))
        protected=(now[:,None]>=press[None]-.35)&(now[:,None]<=end[None])
        busy=torch.where(protected,1.,busy)
        idle=(1-(busy[:,None]*assigned[None]).amax(-1)).to(now.dtype)
    gate=idle*~(contact_veto|near|invalid)
    if not m:gate=torch.zeros_like(gate)
    return dict(gate=gate,idle_weight=idle,near_veto=near,nonfinite_veto=invalid,
                contact_veto=contact_veto,relevant_targets=relevant,
                tracking_weight=torch.ones_like(idle))


def install_ablation(arm):
    """Process-local test adapter, reflected in the saved strict contract."""
    if arm not in ('collision_only','recovery','full'):
        raise ValueError('Unknown hand-contact comparison arm')
    from guitar_learning.gpu import finger_reward
    from guitar_learning.gpu.environment import TensorSongEnvironment
    if arm=='collision_only':finger_reward.finger_preparation_gate=legacy_gate
    original=TensorSongEnvironment.__init__
    def initialize(self,*args,**kwargs):
        original(self,*args,**kwargs)
        if self.hand!='left':raise ValueError('Comparison is GPU left only')
        self.contract['reward']['hand_contact_comparison']=dict(
            arm=arm, schema='guitar_learning.hand_contact_ablation.v1',
            timing='v20 gate/tracking' if arm=='collision_only' else 'v21 shared recovery/tracking',
            thumb_rate_per_s=self.thumb_support_rate,
            initialization=f"same new{self.contract['observation']['dimension']} model structure and seed, fresh optimizer; old performance not inherited",
            adapter_path=str(Path(__file__).resolve()),
            adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        if arm=='collision_only':
            self.contract['reward']['finger_posture'].update(schema='experiment.v20_timing_control.v1',
                gate='v20 press-.35..end plus .15 fade, own press-2..end near/contact veto',
                tracking='full v20 two-second finger tracking, no B recovery attenuation')
            self.contract['reward']['finger_tracking']['recovery']='disabled in timing control'
            self.contract['observation']['finger_posture']['role']='actual v20 temporal gate in named standby_gate columns'
    TensorSongEnvironment.__init__=initialize


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm',choices=('collision_only','recovery','full'),required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--updates',type=int,default=100)
    parser.add_argument('--num-envs',type=int,default=128)
    parser.add_argument('--resume',type=Path)
    args=parser.parse_args()
    import isaacgym  # Before Torch imports from the environment.
    from guitar_learning.training.start import settings_document,run
    install_ablation(args.arm)
    settings=settings_document('left',updates=args.updates,num_envs=args.num_envs,
                               device='cuda:0',physics='gpu',size='large',seed=7,horizon=32)
    settings['song']['thumb_support_rate_per_s']=.02 if args.arm=='full' else 0.
    settings['song']['hand_contact_comparison']=args.arm
    args.allow_stale=False
    run(settings,args)


if __name__=='__main__':main()
