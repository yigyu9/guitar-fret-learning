import tempfile
import unittest
from pathlib import Path

import torch

from ..fresh_learning_v1.policy import Policy
from ..fresh_learning_v1.ppo import PPOTrainer
from .run_v4 import initialize_policy, INITIALIZATION_PROFILE, MUSIC_CHECKPOINT_SCHEMA, validate_resume


class InitializationTests(unittest.TestCase):
    def test_initial_std_and_full_action_authority(self):
        policy=initialize_policy(Policy(2,8))
        self.assertTrue(torch.equal(policy.log_std,torch.full((54,),-3.)))
        self.assertTrue(policy.log_std.requires_grad)
        with torch.no_grad():
            for head in policy.actor_heads:
                head.bias.fill_(3.)
        action=policy.act(torch.zeros(1,2),deterministic=True)['action']
        self.assertGreater(float(action.min()),.99)

    def test_resume_restores_learned_std_and_requires_profile(self):
        trainer=PPOTrainer(initialize_policy(Policy(2,8)))
        trainer.schema=MUSIC_CHECKPOINT_SCHEMA
        with torch.no_grad():
            trainer.policy.log_std.fill_(-2.7)
        contract=dict(environment={'abi':'v3'},initialization_profile=INITIALIZATION_PROFILE)
        metadata=dict(contract=contract,cumulative={'completed_updates':0})
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'own_music.pt'
            trainer.save(path,metadata)
            restored=PPOTrainer(initialize_policy(Policy(2,8)))
            restored.schema=MUSIC_CHECKPOINT_SCHEMA
            payload=torch.load(path,map_location='cpu',weights_only=False)
            validate_resume(payload,restored,contract)
            restored.load(path)
            self.assertTrue(torch.equal(restored.policy.log_std,torch.full((54,),-2.7)))
            incompatible=dict(contract,initialization_profile=dict(INITIALIZATION_PROFILE,initial_log_std=-1.))
            with self.assertRaises(ValueError):
                validate_resume(payload,restored,incompatible)


if __name__=='__main__':
    unittest.main()
