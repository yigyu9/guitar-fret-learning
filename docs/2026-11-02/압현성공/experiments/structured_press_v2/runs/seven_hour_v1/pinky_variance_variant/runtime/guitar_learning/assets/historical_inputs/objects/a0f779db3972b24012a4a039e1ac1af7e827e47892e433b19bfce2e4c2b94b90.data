"""Construction-only right-arm PD hold-strength diagnostic, strap OFF."""
from unittest.mock import patch
import numpy as np
from . import run_om_no_strap_upper_arm_v6 as preload
from .learning_scene_v2 import LearningScene
from .initial_pose_noise_v1 import save,sha

base=preload.base
PLAN=base.ROOT/'stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V8.md'
PLAN_SHA=sha(PLAN)
create_original=LearningScene._create_scene

def create_right_hold(self):
    create_original(self)
    assert not self.initialization_complete
    indices=np.array([i for i,n in enumerate(self.names) if n.startswith(('R_Thorax','R_Shoulder','R_Elbow','R_Wrist'))])
    assert len(indices)==12
    before=self.gym.get_actor_dof_properties(self.env,self.human).copy()
    requested=before.copy()
    requested['stiffness'][indices]*=4
    requested['damping'][indices]*=2
    if not self.gym.set_actor_dof_properties(self.env,self.human,requested):
        raise RuntimeError('right-arm construction PD rejected')
    actual=self.gym.get_actor_dof_properties(self.env,self.human).copy()
    assert np.array_equal(actual,requested)
    self.right_hold_record={'before':{n:before[n].tolist()for n in before.dtype.names},'applied':{n:actual[n].tolist()for n in actual.dtype.names},'right_indices':indices.tolist(),'stiffness_factor':4,'damping_factor':2,'construction_override_calls':1}

def final_save(path,data):
    if path.name=='attempt.json':
        data['input_sha256'][str(PLAN)]=PLAN_SHA
        data={**data,'right_hold_plan':str(PLAN),'right_PD_override':'construction only; right12 stiffness x4, damping x2; effort unchanged'}
    preload.final_save(path,data)

class RightHoldRecording(preload.PreloadRecording):
    def __init__(self,env,out):
        super().__init__(env,out)
        save(self.out/'right_hold_properties.json',env.right_hold_record)

if __name__=='__main__':
    with patch.object(LearningScene,'_create_scene',create_right_hold),patch.object(base,'original_save',final_save),patch.object(base.deadline_native_v4,'_strap_scene_class',lambda recording,enabled:base.original_factory(recording,False)),patch.object(base.strap_trial_recording,'StrapTrialRecording',RightHoldRecording),patch.object(base.string_trial_recording_v1,'StrapTrialRecording',base.GymTrialRecording),patch.object(base.string_trial_recording_v1,'draw_strings',preload.parked.labelled_strings),patch.object(base.trial,'save',preload.metadata):base.main()
