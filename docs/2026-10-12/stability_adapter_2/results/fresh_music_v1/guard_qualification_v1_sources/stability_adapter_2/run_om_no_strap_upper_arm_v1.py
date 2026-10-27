"""Actual strap OFF, left-away constant PD trial with direct support-state logs."""
from pathlib import Path
from unittest.mock import patch
import json
import numpy as np
from .initial_pose_noise_v1 import read,save,sha,pose
from . import strap_trial_recording,string_trial_recording_v1,deadline_native_v4
from .gym_trial_recording import GymTrialRecording
from .run_guitar_focused_view_v1 import FocusedRecording
from .run_om_body_geometry_trial_v2 import main
from . import run_om_body_geometry_trial_v2 as trial
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1'
PLANS=[ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V1.md',ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V2.md',P/'search_v2/search.json']
extra={str(p):sha(p)for p in PLANS};original_save=trial.save;original_factory=deadline_native_v4._strap_scene_class;original_strings=string_trial_recording_v1.draw_strings

def save_metadata(path,data):
    if Path(path).name=='attempt.json':
        data['input_sha256'].update(extra);data={**data,'actual_strap_enabled':False,'control':'constant initial q_ref PD; left initially withdrawn; no attachment or guitar forces','plan':str(PLANS[1])}
    elif Path(path).name=='report.json':
        data={**data,'scope':'actual strap OFF, initial left-away and upper-arm support diagnostic; no music or stability certification','actual_strap_enabled':False}
    original_save(path,data)

def off_strings(*args):
    from PIL import Image,ImageDraw,ImageFont
    counts=original_strings(*args);output=args[1];im=Image.open(output).convert('RGB');draw=ImageDraw.Draw(im);draw.rectangle((12,12,740,49),fill=(15,15,15));draw.text((23,20),'STRAP OFF | left hand withdrawn | free guitar',fill='white',font=ImageFont.truetype(str(strap_trial_recording.FONT),18));im.save(output);return counts

class SupportRecording(FocusedRecording):
    def __init__(self,env,out):
        super().__init__(env,out);self.strap_rows=[];self.support_rows=[]
        from .environment import gymapi
        from .run_joint_hold import native_state
        assert not env.strap_enabled
        before=native_state(env);gp,gr=pose(before['guitar_body_states'][0]);target=gp+gr.apply([-.12,-.34,-.04]);eye=target+np.array([1.15,.15,.15]);props=gymapi.CameraProperties();props.width,props.height=1280,960
        camera=env.gym.create_camera_sensor(env.env,props)
        if camera<0:raise RuntimeError('support side camera missing')
        env.gym.set_camera_location(camera,env.env,gymapi.Vec3(*eye),gymapi.Vec3(*target));env.cameras['support_side']=camera;assert native_state(env)==before
        constant=env.contract.neutral_action
        monitored=['Pelvis','Torso','Spine','Chest','R_Thorax','R_Shoulder','R_Elbow','R_Wrist','RH:palm','L_Shoulder','L_Elbow','L_Wrist','LH:palm']
        def action():
            state=native_state(env);self.support_rows.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'human_body_states':{n:state['human_body_states'][env.human_bodies.index(n)]for n in monitored},'guitar_body_states':{n:state['guitar_body_states'][env.guitar_bodies.index(n)]for n in ['guitar','G:body']}})
            result=constant();assert native_state(env)==state;return result
        env.contract.neutral_action=action

    def capture(self):
        from .run_joint_hold import native_state
        from .environment import gymapi
        before=native_state(self.env);super().capture();self.strap_rows.append({**self.env.strap_state(),'physics_step':self.env.steps,'time_s':self.env.steps/self.env.config['physics_hz']})
        data=read(self.out/'capture.json');data['renderer']='Isaac Gym native camera + depth-tested six strings; strap OFF, no route drawn';data['actual_strap_enabled']=False
        tmp=self.out/'capture.tmp';tmp.write_text(json.dumps(data,indent=2)+'\n');tmp.replace(self.out/'capture.json')
        if len(self.frames)==1:self.env.gym.write_camera_image_to_file(self.env.sim,self.env.env,self.env.cameras['support_side'],gymapi.IMAGE_COLOR,str(self.out/'initial_support_side.png'))
        assert native_state(self.env)==before

    def encode(self):
        save(self.out/'strap_state_samples.json',{'scope':'strap disabled: enabled commanded tension zero; counterfactual cable law is not applied','rows':self.strap_rows});save(self.out/'support_state_samples.json',{'scope':'direct native states at 60Hz before control/integration; no state writes','rows':self.support_rows});return super().encode()

if __name__=='__main__':
    with patch.object(deadline_native_v4,'_strap_scene_class',lambda recording,enabled:original_factory(recording,False)),patch.object(strap_trial_recording,'StrapTrialRecording',SupportRecording),patch.object(string_trial_recording_v1,'StrapTrialRecording',GymTrialRecording),patch.object(string_trial_recording_v1,'draw_strings',off_strings),patch.object(trial,'save',save_metadata):main()
