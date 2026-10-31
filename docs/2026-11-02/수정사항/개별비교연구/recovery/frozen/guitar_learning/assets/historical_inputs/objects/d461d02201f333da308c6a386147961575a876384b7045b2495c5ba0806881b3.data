import unittest
from types import SimpleNamespace

import numpy as np
import torch

from .policy import Policy
from .run_recovery_v1 import train_loop


class JacobianFault(RuntimeError):
    pass


class FakeEnv:
    def __init__(self, faults=None, terminal=False):
        self.faults = faults or {}
        self.terminal = terminal
        self.calls = 0
        self.resets = []
        self.reset(125)

    def reset(self, seed):
        self.seed = seed
        self.resets.append(seed)
        self.scene = SimpleNamespace(steps=0, forbidden_calls=[])
        return np.array([float(seed), 0], dtype=np.float32)

    def step(self, action):
        self.calls += 1
        self.scene.steps += 1
        if self.calls in self.faults:
            raise self.faults[self.calls]
        return np.array([float(self.seed), 9],dtype=np.float32), 1., 0., False, self.terminal, {}


class FakeTrainer:
    def __init__(self):
        self.policy = Policy(2, 8)
        self.updates = 27
        self.buffers = []

    def update(self, buffer):
        self.buffers.append(buffer)
        self.updates += 1
        return {}


class RecoveryTests(unittest.TestCase):
    def run_loop(self, env, target=28, max_reject=8, reject=None):
        trainer = FakeTrainer()
        state = dict(rollout_id=0, attempted_controls=0, valid_controls=0, discarded_controls=0,
            accepted_ppo_steps=0, rejected_rollouts=0, rollout_valid_controls=0, finished_episodes=0,
            next_seed=125, forbidden_calls=[], max_rejected_rollouts=max_reject,
            prior_rejected_rollouts=1, last_attempt=None, attempt_cap=100)
        records, commands = [], []
        try:
            train_loop(env, trainer, np.array([125.,0.]), state, target, 3, 'cpu', JacobianFault,
                commands.append, lambda row:None, records.append, reject or (lambda *a:None), lambda row:None)
        except BaseException as error:
            return trainer,state,records,commands,error
        return trainer,state,records,commands,None

    def test_rejected_whole_rollout_excluded(self):
        trainer,state,records,commands,error = self.run_loop(FakeEnv({2:JacobianFault('uncertain')}))
        self.assertIsNone(error)
        self.assertEqual(len(trainer.buffers),1)
        self.assertTrue(torch.equal(trainer.buffers[0]['obs'][:,0,0],torch.full((3,),126.)))
        self.assertEqual(state['discarded_controls'],1)
        self.assertEqual(state['attempted_controls'],5)
        self.assertEqual([r['status'] for r in records],['rejected','accepted'])
        self.assertEqual([c['control_attempt'] for c in commands],list(range(1,6)))

    def test_final_observation_bootstrap_before_reset(self):
        env = FakeEnv(terminal=True)
        trainer,state,records,commands,error=self.run_loop(env)
        self.assertIsNone(error)
        buffer=trainer.buffers[0]
        self.assertTrue(buffer['truncated'].all())
        self.assertEqual(buffer['obs'][:,0,0].tolist(),[125.,126.,127.])
        with torch.no_grad():
            expected=trainer.policy.act(torch.tensor([[125.,9.],[126.,9.],[127.,9.]]),deterministic=True)
        self.assertTrue(torch.allclose(buffer['next_reward_value'][:,0],expected['reward_value']))

    def test_other_error_fatal(self):
        trainer,state,records,commands,error=self.run_loop(FakeEnv({2:ValueError('fatal')}))
        self.assertIsInstance(error,ValueError)
        self.assertEqual(trainer.updates,27)
        self.assertEqual(state['rejected_rollouts'],0)

    def test_eighth_total_rejection_stops_before_reset(self):
        env=FakeEnv({1:JacobianFault('uncertain')})
        trainer,state,records,commands,error=self.run_loop(env,max_reject=2)
        self.assertIsInstance(error,RuntimeError)
        self.assertEqual(trainer.updates,27)
        self.assertEqual(env.resets,[125])

    def test_preservation_failure_fatal(self):
        def reject(*args):
            raise OSError('checkpoint failed')
        env=FakeEnv({1:JacobianFault('uncertain')})
        trainer,state,records,commands,error=self.run_loop(env,reject=reject)
        self.assertIsInstance(error,OSError)
        self.assertEqual(env.resets,[125])

    def test_policy_typed_error_is_not_recovered(self):
        # Native-error recovery is scoped to env.step, not arbitrary typed errors.
        from .run_recovery_v1 import collect_rollout
        policy=SimpleNamespace(act=lambda *a,**k:(_ for _ in ()).throw(JacobianFault('policy')))
        with self.assertRaises(JacobianFault):
            collect_rollout(FakeEnv(),policy,np.zeros(2),3,'cpu',
                dict(attempted_controls=0,attempt_cap=3),lambda row:None,lambda row:None,JacobianFault)


if __name__=='__main__':
    unittest.main()
