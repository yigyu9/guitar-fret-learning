"""Same native/observation contract, corrected note phase and progress reward."""
from unittest.mock import patch
from guitar_learning.song import environment as original
from guitar_learning.runtime.persistent_environment import _CONSTRUCTION_LOCK
from guitar_learning.song.quality import SongLedger, metadata
from guitar_learning.song import progress


class RewardEnvironment(original.SongEnvironment):
    def reset(self):
        with _CONSTRUCTION_LOCK,patch.object(original,'SongLedger',SongLedger),patch.object(original,'metadata',metadata):
            return super().reset()

    def step(self,action):
        if self.finished:
            raise RuntimeError('reset required before stepping a finished/uninitialized episode')
        try:
            before=progress.snapshot(self.task,self.song_ledger.notes,self.last_measured,self.last_sample,self.song_ledger.window_s)
            observation,base_reward,terminated,truncated,info=super().step(action)
            after=progress.snapshot(self.task,self.song_ledger.notes,self.last_measured,self.last_sample,self.song_ledger.window_s)
            shaping=progress.reward(before,after,bool(info['failure_reasons']))
            value=shaping['value'];self.total_reward+=value
            info['reward_terms']['song_right_progress']=value
            info['reward_shaping']=shaping
            if 'episode'in info:info['episode']['reward']=self.total_reward
            return observation,float(base_reward+value),terminated,truncated,info
        except BaseException:
            self.finished=True
            raise


def build_environment(config,out,*,bundle,song,**kwargs):
    task=original.make_task(bundle,pre_roll_s=song['pre_roll_s'],tail_s=song['tail_s'])
    with _CONSTRUCTION_LOCK,patch.object(original.training_environment,'ContactEnvironment',original.PersistentContactEnvironment):
        return RewardEnvironment(config,out,task=task,song=song,**kwargs)
