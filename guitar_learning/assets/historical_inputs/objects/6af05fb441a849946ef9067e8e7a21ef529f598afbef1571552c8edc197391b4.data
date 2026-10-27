"""Same constant PD physics, adding nonmutating 240Hz contact observations."""
from unittest.mock import patch
from . import run_om_no_strap_upper_arm_v1 as base
from .initial_pose_noise_v1 import save,sha
PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V3.md'
PLAN_SHA=sha(PLAN)

def metadata(path,data):
    if path.name=='attempt.json':
        data['input_sha256'][str(PLAN)]=PLAN_SHA;data={**data,'endpoint_observation_plan':str(PLAN),'contact_endpoint_hz':240}
    elif path.name=='report.json':data={**data,'contact_endpoint_hz':240}
    base.save_metadata(path,data)

class EndpointRecording(base.SupportRecording):
    def __init__(self,env,out):
        super().__init__(env,out);self.endpoint_rows=[]
        from .native_contacts import body_names,read_contacts
        from .run_joint_hold import native_state
        mapping=body_names(env.gym,env.env);previous=env.after_physics
        def observe(owner):
            if previous is not None:previous(owner)
            before=native_state(owner);contacts=read_contacts(owner.gym,owner.env,mapping)
            is_left=lambda name:name.startswith(('human/L_Thorax','human/L_Shoulder','human/L_Elbow','human/L_Wrist','human/LH:'))
            left=[c for c in contacts if (is_left(c['body0_name']) and c['body1_name'].startswith('guitar/')) or (is_left(c['body1_name']) and c['body0_name'].startswith('guitar/'))]
            right=[c for c in contacts if 'human/R_Shoulder' in [c['body0_name'],c['body1_name']] and 'guitar/G:body' in [c['body0_name'],c['body1_name']]]
            human={n:before['human_body_states'][owner.human_bodies.index(n)]for n in ['R_Shoulder','LH:palm','L_Wrist']};guitar={n:before['guitar_body_states'][owner.guitar_bodies.index(n)]for n in ['guitar','G:body']}
            self.endpoint_rows.append({'physics_step':owner.steps,'time_s':owner.steps/owner.config['physics_hz'],'left_arm_hand_guitar_contacts':left,'right_upper_arm_body_contacts':right,'human_body_states':human,'guitar_body_states':guitar})
            assert native_state(owner)==before
        env.after_physics=observe

    def encode(self):
        save(self.out/'physics_endpoint_contacts.json',{'scope':'240Hz after-physics contact query, not all solver internal substeps or continuous force measurement','rows':self.endpoint_rows});return super().encode()

if __name__=='__main__':
    with patch.object(base.deadline_native_v4,'_strap_scene_class',lambda recording,enabled:base.original_factory(recording,False)),patch.object(base.strap_trial_recording,'StrapTrialRecording',EndpointRecording),patch.object(base.string_trial_recording_v1,'StrapTrialRecording',base.GymTrialRecording),patch.object(base.string_trial_recording_v1,'draw_strings',base.off_strings),patch.object(base.trial,'save',metadata):base.main()
