import unittest
from types import SimpleNamespace

import numpy as np
import torch

from ..fresh_learning_v1.policy import Policy
from ..fresh_learning_v1.ppo import PPOTrainer,PPOConfig,compute_gae
from .run import collect_rollout,validate_resume,cumulative_counts,MUSIC_CHECKPOINT_SCHEMA


class Env:
    def __init__(self, fail_at=None):
        self.calls=0
        self.fail_at=fail_at
        self.metadata={'goals':[1]}
        self.reset(10)

    def reset(self,seed):
        self.seed=seed
        self.scene=SimpleNamespace(steps=0,forbidden_calls=[])
        return np.array([float(seed),0.],dtype=np.float32)

    def step(self,action):
        self.calls+=1
        self.scene.steps+=1
        if self.calls==self.fail_at:
            raise RuntimeError('native guard')
        return np.array([float(self.seed),9.],dtype=np.float32),1.,0.,self.calls==1,self.calls==2,{}


def counters():
    return dict(rollout_id=1,attempted_controls=0,valid_controls=0,pending_valid_controls=0,
        accepted_ppo_steps=0,forbidden_calls=[],finished_episodes=0,next_seed=10,last_attempt=None)


class RunnerTests(unittest.TestCase):
    def test_terminal_and_truncated_final_observation_bootstrap(self):
        env=Env()
        policy=Policy(2,8)
        state=counters()
        episodes=[]
        buffer,obs=collect_rollout(env,policy,np.array([10.,0.]),3,'cpu',state,
            lambda row:None,lambda row:None,episodes.append)
        self.assertEqual(buffer['obs'][:,0,0].tolist(),[10.,11.,12.])
        with torch.no_grad():
            final=policy.act(torch.tensor([[10.,9.],[11.,9.],[12.,9.]]),deterministic=True)
        self.assertTrue(torch.allclose(buffer['next_reward_value'][:,0],final['reward_value']))
        adv,ret=compute_gae(buffer['reward'],buffer['reward_value'],buffer['next_reward_value'],
            buffer['terminated'],buffer['truncated'],.9,.95)
        self.assertAlmostEqual(float(ret[0]),1.,places=5)
        self.assertAlmostEqual(float(ret[1]),1+.9*float(final['reward_value'][1]),places=5)
        self.assertEqual(len(episodes),4)

    def test_partial_rollout_fault_cannot_update(self):
        env=Env(fail_at=2)
        trainer=PPOTrainer(Policy(2,8))
        state=counters()
        commands=[]
        with self.assertRaisesRegex(RuntimeError,'native guard'):
            buffer,obs=collect_rollout(env,trainer.policy,np.array([10.,0.]),3,'cpu',state,
                commands.append,lambda row:None,lambda row:None)
            trainer.update(buffer)
        self.assertEqual(trainer.updates,0)
        self.assertEqual(state['valid_controls'],1)
        self.assertEqual(state['pending_valid_controls'],1)
        self.assertEqual(len(commands),2)
        self.assertEqual(commands[-1]['physics_step_after'],1)

    def test_evaluation_preserves_training_counters(self):
        prior=dict(completed_updates=16,attempted_controls=4096,valid_controls=4096,
            accepted_ppo_steps=4096,excluded_valid_controls=0)
        state=counters()
        state.update(attempted_controls=300,valid_controls=300)
        self.assertEqual(cumulative_counts(prior,state,16,training=False),prior)
        self.assertEqual(cumulative_counts({},state,0,training=False),
            dict(completed_updates=0,attempted_controls=0,valid_controls=0,
                accepted_ppo_steps=0,excluded_valid_controls=0))

    def test_strict_music_resume_contract_and_counters(self):
        trainer=PPOTrainer(Policy(2,8),PPOConfig())
        trainer.schema=MUSIC_CHECKPOINT_SCHEMA
        contract={'timeline':'abc','physics':'xyz','assets':{'mesh':'123'}}
        payload=dict(identity=trainer._identity(),model=trainer.policy.state_dict(),updates=2,
            metadata=dict(contract=contract,cumulative=dict(completed_updates=2,attempted_controls=520,
                valid_controls=519,accepted_ppo_steps=512,excluded_valid_controls=7)))
        metadata=validate_resume(payload,trainer,contract)
        for different in ({'timeline':'changed'},{'physics':'changed'},{'assets':{'mesh':'changed'}}):
            bad=dict(contract,**different)
            with self.assertRaises(ValueError):
                validate_resume(payload,trainer,bad)
        old=dict(payload,identity=dict(payload['identity'],schema='fresh54_dualcritic_ppo_v1'))
        with self.assertRaises(ValueError):
            validate_resume(old,trainer,contract)
        state=counters()
        state.update(attempted_controls=258,valid_controls=257,accepted_ppo_steps=256,pending_valid_controls=1)
        merged=cumulative_counts(metadata['cumulative'],state,3)
        self.assertEqual(merged,dict(completed_updates=3,attempted_controls=778,valid_controls=776,
            accepted_ppo_steps=768,excluded_valid_controls=8))


if __name__=='__main__':
    unittest.main()
