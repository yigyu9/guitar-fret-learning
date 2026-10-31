"""Real full-score evidence and explicit task migration, never permissive resume."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch
import torch._dynamo  # Keep lazy registrations outside scoped module fixtures.

from guitar_learning.training.ppo import PPOTrainer
from guitar_learning.tool.experiments.transition.policy import SpecialistPolicy
from guitar_learning.tool.experiments.transition import transfer

SOURCE=Path(__file__).resolve().parents[2]/'docs/2026-10-12/stability_adapter_2/results/guitar_learning_reward_v2/training_v1'


def contract(role='left',mode='single_a'):
    value=json.loads((SOURCE/'training_contract.json').read_text())
    value['task']['transition']=dict(schema='guitar_learning.transition.v1',mode=mode,tempo_scale=1.,role=role)
    value['task']['specialist']=dict(role=role,frozen_partner=False)
    value['reward']['transition']=dict(schema='guitar_learning.transition.v1',role=role,projection='left')
    return value


class TransitionTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.evidence=transfer.validate_source(SOURCE/'final.pt')

    def test_real_published24_source(self):
        self.assertEqual(self.evidence['payload']['updates'],24)
        consumed=json.loads((SOURCE/'inputs_before.json').read_text())
        self.assertTrue(set(consumed).issubset(self.evidence['source_pins']))
        self.assertEqual(self.evidence['source_pins'][str(SOURCE/'final.pt')],transfer.SOURCE_SHA256)

    def test_selected_actor_only_preserves_all_rng_critic_partner_and_Adam(self):
        model=SpecialistPolicy(contract=contract())
        before={key:value.clone() for key,value in model.state_dict().items()}
        trng=torch.get_rng_state().clone();nrng=np.random.get_state();prng=random.getstate()
        with patch.object(transfer,'validate_source',return_value=self.evidence):
            report=transfer.apply_source(model,SOURCE/'final.pt')
        self.assertTrue(torch.equal(trng,torch.get_rng_state()));np.testing.assert_equal(nrng,np.random.get_state())
        self.assertEqual(prng,random.getstate())
        source=self.evidence['payload']['model']
        for key,value in model.state_dict().items():
            if key.startswith(('actor_encoders.left.','actor_heads.left.')):
                expected=source[key]
            elif key=='log_std':expected=torch.cat((source[key][:33],before[key][33:]))
            else:expected=before[key]
            torch.testing.assert_close(value,expected,rtol=0,atol=0)
        trainer=PPOTrainer(model)
        self.assertFalse(trainer.actor_optimizer.state);self.assertFalse(trainer.value_optimizer.state)
        self.assertEqual(trainer.updates,0);self.assertEqual(report['source_updates'],24)

    def test_physical_or_observation_changes_fail_before_copy(self):
        for section in ('observation','action','termination'):
            changed=contract();changed[section]['unexpected']=True
            model=SpecialistPolicy(contract=changed)
            before={key:value.clone() for key,value in model.state_dict().items()}
            with patch.object(transfer,'validate_source',return_value=self.evidence),self.assertRaises(ValueError):
                transfer.apply_source(model,SOURCE/'final.pt')
            for key,value in model.state_dict().items():torch.testing.assert_close(value,before[key],rtol=0,atol=0)

    def test_source_PPO_and_other_task_are_not_resumable(self):
        with tempfile.TemporaryDirectory() as folder:
            model=SpecialistPolicy(contract=contract());trainer=PPOTrainer(model)
            path=Path(folder)/'transition.pt';trainer.save(path)
            PPOTrainer(SpecialistPolicy(contract=contract())).load(path)
            for other in (SOURCE/'final.pt',):
                with self.assertRaises(ValueError):trainer.load(other)
            with self.assertRaises(ValueError):
                PPOTrainer(SpecialistPolicy(contract=contract(mode='single_b'))).load(path)

    def test_nonpublished_source_hash_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'final.pt';path.write_bytes(b'forged')
            for name in ('settings.json','training_contract.json','inputs_before.json','final_checkpoint.json'):
                (path.parent/name).write_text('{}')
            with self.assertRaisesRegex(ValueError,'audited reward-v2'):
                transfer.validate_source(path)


if __name__=='__main__':unittest.main()
