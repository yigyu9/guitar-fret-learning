"""Read-only torso contact audit on the immutable left-hand cycle controller."""
import isaacgym
from unittest.mock import patch
from . import left_grip_release_cycle_v2 as cycle
from . import run_left_grip_release_cycle_v2 as runner
from . import right_block_body_effort_v5 as support
from .native_contacts import body_names,read_contacts
from .run_joint_hold import native_state
from .initial_pose_noise_v1 import save

MONITORED=('Torso','Spine','Chest','R_Thorax','R_Shoulder','R_Hip')

def run():
    Parent=support.EffortRecording
    class Recording(Parent):
        def __init__(self,env,out):
            super().__init__(env,out);self.chest_audit=[]
            mapping=body_names(env.gym,env.env);previous=env.after_physics
            def observe(owner):
                previous(owner);state=native_state(owner);contacts=read_contacts(owner.gym,owner.env,mapping)
                pairs={name:[c for c in contacts if 'human/'+name in (c['body0_name'],c['body1_name']) and any(n.startswith('guitar/') for n in (c['body0_name'],c['body1_name']))] for name in MONITORED}
                self.chest_audit.append({'physics_step':owner.steps,'time_s':owner.steps/240,'contacts_by_human_body':pairs})
                assert native_state(owner)==state
            env.after_physics=observe
        def encode(self):
            save(self.out/'chest_contact_query.json',{'scope':'post-physics native contact query, read-only; raw lambda not calibrated force N','rows':self.chest_audit})
            return super().encode()
    with patch.object(support,'EffortRecording',Recording):runner.main()

if __name__=='__main__':cycle.main(run)
