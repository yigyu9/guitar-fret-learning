"""미검증goal-Chest보존증분: oldBody9→new16ramp→부모Chest순서."""
import numpy as np
from .runtime_v3 import Scene as PreviousScene
from .runtime_v6 import Controller
from .runtime_v7 import MODE,JOINTS,DELTA

INCREMENT_MODE='finite_static_Body9_goalChest_preserve_Spine_away0p12mm_v1'
INCREMENT_DELTA=[-0.0011205811960882453,0.003459068038147298,-0.0029109733620387344,0.0033940985035895346,0.0020668419691073155,0.00715526267499531,-0.0022953485701123484,-0.005611835199274916,-0.0044118129739800175]
INCREMENT_RAMP=[16.,16.5]


class Scene(PreviousScene):
    def command(self,named):
        assert self.cfg['ready_spine_target_increment_mode']==INCREMENT_MODE and self.cfg['ready_spine_target_increment_joints']==JOINTS
        assert self.cfg['ready_spine_target_increment_delta_rad']==INCREMENT_DELTA and self.cfg['ready_spine_target_increment_ramp_s']==INCREMENT_RAMP
        if self.steps<2400:return super().command(named)
        assert self.cfg['ready_body9_pose_mode']==MODE and self.cfg['ready_body9_pose_joints']==JOINTS
        assert self.cfg['ready_body9_pose_delta_rad']==DELTA and self.cfg['ready_body9_pose_ramp_s']==[10,10.5]
        state=self.native();base=self.foot_target_logic.base_target.copy()
        original=np.array([named[n] for n in self.names],dtype=float);afterold=original.copy();indices=np.array([self.names.index(n) for n in JOINTS]);time=self.steps/240
        u=float(np.clip((time-10)/.5,0,1));fraction=u*u*(3-2*u);bias=np.array(DELTA)*fraction;afterold[indices]+=bias
        afternew=afterold.copy();newu=float(np.clip((time-16)/.5,0,1));newfraction=newu*newu*(3-2*newu);newbias=np.array(INCREMENT_DELTA)*newfraction
        if self.steps>3840:afternew[indices]+=newbias
        other=np.setdiff1d(np.arange(105),indices);assert np.array_equal(original[other],afterold[other]) and np.array_equal(afterold[other],afternew[other])
        assert np.intersect1d(indices,self.zero_indices).size==0 and np.array_equal(original[self.zero_indices],afternew[self.zero_indices])
        row=super().command(dict(zip(self.names,afternew.tolist())))
        assert self.native()==state and np.array_equal(self.foot_target_logic.base_target,base)
        assert np.array_equal(row['ready_chest_pose']['original_requested105_rad'],afternew)
        scope='원105→추가Body9→부모기존Chest+.005→원Motion/foot/명령순서.상수벡터이며접촉/타현추종·base수정·상태주입·기타힘없음.source예측은실제지지성공보장아님.' if self.steps<=3840 else 'oldBody9단계만기록:원105→oldBody9.후속newIncrement와Chest는별도metadata.단일oldBody실행전체와동일하다고주장하지않는다.'
        row['ready_body9_pose']=dict(mode=MODE,joints=JOINTS.copy(),indices105=indices.tolist(),delta_rad=DELTA.copy(),ramp_s=[10.,10.5],time_s=time,physics_step_before=self.steps,
            ramp_fraction=fraction,bias9_rad=bias.tolist(),original_requested105_rad=original.tolist(),biased_requested105_rad=afterold.tolist(),other96_exact=True,base_target_unchanged=True,state_preserved=True,scope=scope)
        if self.steps>3840:
            row['ready_spine_target_increment']=dict(mode=INCREMENT_MODE,joints=JOINTS.copy(),indices105=indices.tolist(),delta_rad=INCREMENT_DELTA.copy(),ramp_s=INCREMENT_RAMP.copy(),time_s=time,physics_step_before=self.steps,
                ramp_fraction=newfraction,bias9_rad=newbias.tolist(),original_requested105_rad=afterold.tolist(),biased_requested105_rad=afternew.tolist(),other96_exact=True,zero8_exact=True,base_target_unchanged=True,state_preserved=True,
                scope='oldBody9→newIncrement→부모Chestlast→원Motion/foot/명령.16..16.5별도유한목표가설/원gain·cap그대로.원strict실패·LH실패보존/새실제추종·지지·채택미검증.')
        return row
