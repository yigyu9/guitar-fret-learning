"""Unchanged500-state parameter layout; truthful explicit warmstart metadata."""
from guitar_learning.tool.experiments.song.policy import SongPolicy

INITIALIZATION = 'whole_score_actor_and_std_reward_v2_fresh_critic_and_Adam'


class RewardPolicy(SongPolicy):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.architecture['initialization']=INITIALIZATION
