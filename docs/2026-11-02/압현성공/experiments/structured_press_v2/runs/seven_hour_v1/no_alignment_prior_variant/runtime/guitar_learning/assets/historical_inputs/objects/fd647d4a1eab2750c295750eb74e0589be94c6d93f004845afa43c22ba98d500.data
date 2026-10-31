"""Revised left-clear starts with the unchanged endpoint-only observation wrapper."""
from unittest.mock import patch
from . import run_om_no_strap_upper_arm_v2 as endpoint
from .initial_pose_noise_v1 import sha
base=endpoint.base
PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V5.md'
SEARCH=base.P/'search_v4/search.json'
extra={str(p):sha(p)for p in [PLAN,SEARCH]}

def metadata(path,data):
    if path.name=='attempt.json':
        data['input_sha256'].update(extra);data={**data,'current_initial_pose_plan':str(PLAN),'left_initial_target_rule':'back30cm/down10cm relative to low3 source posture'}
    endpoint.metadata(path,data)

def labelled_strings(*args):
    from PIL import Image,ImageDraw,ImageFont
    result=base.original_strings(*args);image=Image.open(args[1]).convert('RGB');draw=ImageDraw.Draw(image);draw.rectangle((12,12,780,49),fill=(15,15,15));draw.text((23,20),'STRAP OFF | left-away initial target | free guitar',fill='white',font=ImageFont.truetype(str(base.strap_trial_recording.FONT),18));image.save(args[1]);return result

if __name__=='__main__':
    with patch.object(base.deadline_native_v4,'_strap_scene_class',lambda recording,enabled:base.original_factory(recording,False)),patch.object(base.strap_trial_recording,'StrapTrialRecording',endpoint.EndpointRecording),patch.object(base.string_trial_recording_v1,'StrapTrialRecording',base.GymTrialRecording),patch.object(base.string_trial_recording_v1,'draw_strings',labelled_strings),patch.object(base.trial,'save',metadata):base.main()
