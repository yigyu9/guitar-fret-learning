"""Bounded joint-goal PI through the existing sole target owner; no pose writes."""
from unittest.mock import patch
from pathlib import Path
import json
import numpy as np
from . import strap_trial_recording
from .run_guitar_focused_view_v1 import FocusedRecording
from .run_om_body_geometry_trial_v2 import main
from . import run_om_body_geometry_trial_v2 as trial

original_save=trial.save
def save_control_metadata(path,data):
    if Path(path).name=='attempt.json':
        data={**data,'target_rule':'initial pose goal + bounded body/arm PI via contract.targets; no pose overwrite','control_plan':str(Path(__file__).parent/'OM_AXILLA_HOLD_CORRECTION_PLAN_V1.md')}
    elif Path(path).name=='report.json':
        data={**data,'scope':'same source-cleared OM initial pose with bounded joint-goal PI; no music or stabilization success claim','control':'body/arm PI Kp1 Ki1/s; body cap.05rad arm cap.3rad; model/effective limits and contract rates apply'}
    original_save(path,data)

class HoldRecording(FocusedRecording):
    def __init__(self,env,out):
        super().__init__(env,out)
        self.control_rows=[];self.strap_rows=[];self.integral=np.zeros(len(env.names))
        self.cap=np.array([.05 if g=='body' else .3 if g=='arm' else 0. for g in env.contract.groups])
        self.goal=env.contract.q_ref.copy()
        from .environment import gymapi
        from .initial_pose_noise_v1 import pose
        from .run_joint_hold import native_state
        state=native_state(env);gp,gr=pose(state['guitar_body_states'][0]);target=gp+gr.apply([-.12,-.34,-.04]);eye=target+np.array([1.15,.15,.15])
        props=gymapi.CameraProperties();props.width,props.height=1280,960
        camera=env.gym.create_camera_sensor(env.env,props)
        if camera<0:raise RuntimeError('axilla side camera creation failed')
        env.gym.set_camera_location(camera,env.env,gymapi.Vec3(*eye),gymapi.Vec3(*target));env.cameras['axilla_side']=camera
        if native_state(env)!=state:raise AssertionError('side camera creation changed state')
        def action():
            actual=np.array([s['pos'] for s in native_state(env)['human_dof_states']]);error=self.goal-actual
            self.integral=np.clip(self.integral+env.contract.dt*error,-self.cap,self.cap)
            residual=np.clip(error+self.integral,-self.cap,self.cap)
            requested=np.clip(self.goal+residual,env.contract.effective_lower,env.contract.effective_upper)
            normalized=np.clip((requested-env.contract.mid)/env.contract.half,-1,1)
            self.control_rows.append({'physics_step':env.steps,'time_s':env.steps/env.config['physics_hz'],'actual_q_rad':actual.tolist(),'error_rad':error.tolist(),'integral_rad':self.integral.tolist(),'residual_rad':residual.tolist(),'requested_target_rad':requested.tolist(),'requested_action':normalized.tolist()})
            return normalized
        env.contract.neutral_action=action

    def capture(self):
        from .run_joint_hold import native_state
        from .environment import gymapi
        before=native_state(self.env);super().capture()
        record=self.env.strap_state();record['physics_step']=self.env.steps;record['time_s']=self.env.steps/self.env.config['physics_hz'];self.strap_rows.append(record)
        if len(self.frames)==1:
            self.env.gym.write_camera_image_to_file(self.env.sim,self.env.env,self.env.cameras['axilla_side'],gymapi.IMAGE_COLOR,str(self.out/'initial_axilla_side.png'))
        if native_state(self.env)!=before:raise AssertionError('hold/strap recording changed state')

    def encode(self):
        for name,data in [('joint_hold_correction.json',{'Kp':1,'Ki_per_s':1,'residual_cap_rad':self.cap.tolist(),'initial_goal_rad':self.goal.tolist(),'joint_names':self.env.names,'rows':self.control_rows}),('strap_state_samples.json',{'sample_rate_hz':self.fps,'scope':'current calculated and previous-step commanded tension, not sensor force','rows':self.strap_rows})]:
            path=self.out/name
            if path.exists():raise FileExistsError(str(path))
            path.write_text(json.dumps(data,indent=2)+'\n')
        return super().encode()

if __name__=='__main__':
    with patch.object(strap_trial_recording,'StrapTrialRecording',HoldRecording),patch.object(trial,'save',save_control_metadata):main()
