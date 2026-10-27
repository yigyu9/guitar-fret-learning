"""Constant-PD lower starts, with initial side camera and strap command logging."""
from pathlib import Path
from unittest.mock import patch
import numpy as np
from .initial_pose_noise_v1 import sha,save,pose
from . import strap_trial_recording
from .run_guitar_focused_view_v1 import FocusedRecording
from .run_om_body_geometry_trial_v2 import main
from . import run_om_body_geometry_trial_v2 as trial

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1'
PIN_PATHS=[ROOT/'stability_adapter_2/OM_THIGH_HEIGHT_INITIAL_PLAN_V1.md',ROOT/'stability_adapter_2/OM_THIGH_HEIGHT_INITIAL_PLAN_V2.md',P/'search_v2/search.json']
extra_inputs={str(p):sha(p) for p in PIN_PATHS}
original_save=trial.save

def save_metadata(path,data):
    if Path(path).name=='attempt.json':
        data['input_sha256'].update(extra_inputs)
        data={**data,'initial_height_rule':'min left/right Hip capsule–OM source gap; constant PD, no PI','height_plan':str(PIN_PATHS[1]),'height_plan_sha256':extra_inputs[str(PIN_PATHS[1])]}
    elif Path(path).name=='report.json':
        data={**data,'scope':'lower OM initial pose, actual free-guitar five-second diagnostic; constant PD, no music or stability success claim'}
    original_save(path,data)

class ThighHeightRecording(FocusedRecording):
    def __init__(self,env,out):
        super().__init__(env,out);self.strap_rows=[]
        from .environment import gymapi
        from .run_joint_hold import native_state
        before=native_state(env);gp,gr=pose(before['guitar_body_states'][0]);target=gp+gr.apply([-.12,-.34,-.04]);eye=target+np.array([1.15,.15,.15])
        props=gymapi.CameraProperties();props.width,props.height=1280,960;camera=env.gym.create_camera_sensor(env.env,props)
        if camera<0:raise RuntimeError('side camera creation failed')
        env.gym.set_camera_location(camera,env.env,gymapi.Vec3(*eye),gymapi.Vec3(*target));env.cameras['thigh_side']=camera
        assert native_state(env)==before

    def capture(self):
        from .run_joint_hold import native_state
        from .environment import gymapi
        before=native_state(self.env);super().capture()
        row=self.env.strap_state();row.update(physics_step=self.env.steps,time_s=self.env.steps/self.env.config['physics_hz']);self.strap_rows.append(row)
        if len(self.frames)==1:self.env.gym.write_camera_image_to_file(self.env.sim,self.env.env,self.env.cameras['thigh_side'],gymapi.IMAGE_COLOR,str(self.out/'initial_thigh_side.png'))
        assert native_state(self.env)==before

    def encode(self):
        save(self.out/'strap_state_samples.json',{'sample_rate_hz':self.fps,'scope':'current calculated and previous-step commanded tension, not sensor force','rows':self.strap_rows})
        return super().encode()

if __name__=='__main__':
    with patch.object(strap_trial_recording,'StrapTrialRecording',ThighHeightRecording),patch.object(trial,'save',save_metadata):main()
