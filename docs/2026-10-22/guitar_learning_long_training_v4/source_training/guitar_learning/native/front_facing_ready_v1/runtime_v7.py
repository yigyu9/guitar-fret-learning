"""선택적 Body9 상수추가후보. 기존Chest scalar는부모에서나중에가산한다."""
import numpy as np
from .runtime_v3 import Scene as PreviousScene
from .runtime_v6 import Controller

MODE='finite_static_Body9_selective0p4mm_Spine_away0p15mm_tilt0_v1'
JOINTS=[b+'_'+a for b in ('Torso','Spine','Chest') for a in 'xyz']
DELTA=[-0.004008260734436661, 0.0017667417361826626, 0.0003640881449152731, 0.01649421893556516, 0.0004271675536552073, -0.0016944454411247111, -0.01212016928275683, -0.002887329958038188, 0.0034321297572885157]


class Scene(PreviousScene):
    def command(self,named):
        if self.steps<2400:return super().command(named)
        assert self.cfg['ready_body9_pose_mode']==MODE and self.cfg['ready_body9_pose_joints']==JOINTS
        assert self.cfg['ready_body9_pose_delta_rad']==DELTA and self.cfg['ready_body9_pose_ramp_s']==[10,10.5]
        state=self.native();base=self.foot_target_logic.base_target.copy()
        original=np.array([named[n] for n in self.names],dtype=float);request=original.copy();indices=np.array([self.names.index(n) for n in JOINTS]);time=self.steps/240
        u=float(np.clip((time-10)/.5,0,1));fraction=u*u*(3-2*u);bias=np.array(DELTA)*fraction;request[indices]+=bias
        other=np.setdiff1d(np.arange(105),indices);assert np.array_equal(original[other],request[other])
        row=super().command(dict(zip(self.names,request.tolist())))
        assert self.native()==state and np.array_equal(self.foot_target_logic.base_target,base)
        assert np.array_equal(row['ready_chest_pose']['original_requested105_rad'],request)
        row['ready_body9_pose']=dict(mode=MODE,joints=JOINTS.copy(),indices105=indices.tolist(),delta_rad=DELTA.copy(),ramp_s=[10.,10.5],time_s=time,physics_step_before=self.steps,
            ramp_fraction=fraction,bias9_rad=bias.tolist(),original_requested105_rad=original.tolist(),biased_requested105_rad=request.tolist(),other96_exact=True,base_target_unchanged=True,state_preserved=True,
            scope='원105→추가Body9→부모기존Chest+.005→원Motion/foot/명령순서.상수벡터이며접촉/타현추종·base수정·상태주입·기타힘없음.source예측은실제지지성공보장아님.')
        return row
