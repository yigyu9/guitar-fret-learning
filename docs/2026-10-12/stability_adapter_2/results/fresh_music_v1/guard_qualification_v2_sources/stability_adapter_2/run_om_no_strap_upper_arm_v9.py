"""Three-support starts with existing strap-free right preload and PD hold."""
from unittest.mock import patch
from . import run_om_no_strap_upper_arm_v7 as hold
from .learning_scene_v2 import LearningScene
from .initial_pose_noise_v1 import sha

base=hold.base
PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V10.md'
SEARCH=base.P/'search_v5/search.json'
extra={str(p):sha(p)for p in (PLAN,SEARCH)}

def final_save(path,data):
    if path.name=='attempt.json':
        data['input_sha256'].update(extra)
        data={**data,'current_initial_pose_plan':str(PLAN),'initial_support_rule':'source Chest and minimum Hip near3mm, proximal right upper-arm near1mm; left parked, actual contacts to be verified'}
    hold.final_save(path,data)

if __name__=='__main__':
    with patch.object(LearningScene,'_create_scene',hold.create_right_hold),patch.object(base,'original_save',final_save),patch.object(base.deadline_native_v4,'_strap_scene_class',lambda recording,enabled:base.original_factory(recording,False)),patch.object(base.strap_trial_recording,'StrapTrialRecording',hold.RightHoldRecording),patch.object(base.string_trial_recording_v1,'StrapTrialRecording',base.GymTrialRecording),patch.object(base.string_trial_recording_v1,'draw_strings',hold.preload.parked.labelled_strings),patch.object(base.trial,'save',hold.preload.metadata):base.main()
