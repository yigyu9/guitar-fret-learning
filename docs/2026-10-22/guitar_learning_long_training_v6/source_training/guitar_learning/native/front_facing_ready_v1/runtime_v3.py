"""미검증Chest 자세후보: 원Motion 전에Chest_x 요청만유한하게+.005rad."""
import numpy as np
from .runtime_v1 import Scene as PreviousScene
from .runtime_v2 import Controller

MODE='finite_human_Chest_x_forward_0p005rad_v1'


class Scene(PreviousScene):
    def command(self,named):
        if self.steps<2400:return super().command(named)
        assert self.cfg['ready_chest_pose_mode']==MODE and self.cfg['ready_chest_pose_joint']=='Chest_x'
        assert self.cfg['ready_chest_pose_delta_rad']==.005 and self.cfg['ready_chest_pose_ramp_s']==[10,10.5]
        state=self.native();base=self.foot_target_logic.base_target.copy()
        original=np.array([named[n] for n in self.names],dtype=float);request=original.copy();index=self.names.index('Chest_x');time=self.steps/240
        u=float(np.clip((time-10)/.5,0,1));ramp=u*u*(3-2*u);bias=.005*ramp;request[index]+=bias
        other=np.setdiff1d(np.arange(105),[index]);assert np.array_equal(original[other],request[other])
        row=super().command(dict(zip(self.names,request.tolist())))
        assert self.native()==state and np.array_equal(self.foot_target_logic.base_target,base)
        assert row['requested105_rad'][index]==request[index]
        row['ready_chest_pose']=dict(mode=MODE,joint='Chest_x',index105=index,delta_rad=.005,ramp_s=[10.,10.5],time_s=time,physics_step_before=self.steps,
            ramp_fraction=ramp,bias_rad=bias,original_requested105_rad=original.tolist(),biased_requested105_rad=request.tolist(),other104_exact=True,base_target_unchanged=True,state_preserved=True,
            scope='preMotion원요청에Chest_x만가산;그뒤원LH/RH Motion/foot/명령/float32제한그대로.기타힘/상태주입/원base_target수정없음.새자세가설이며실제지지성공은별도검사.')
        return row
