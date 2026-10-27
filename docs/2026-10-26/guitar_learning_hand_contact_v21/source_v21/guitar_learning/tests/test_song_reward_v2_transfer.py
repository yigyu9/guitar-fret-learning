"""Full trained score actors transfer without carrying old value/Adam/RNG state."""
import copy
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import torch

from guitar_learning.training.ppo import PPOTrainer
from guitar_learning.tool.experiments.song_reward_v2.policy import RewardPolicy as SongPolicy
from guitar_learning.tool.experiments.song_reward_v2 import transfer

SOURCE = Path(__file__).resolve().parents[2] / 'docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2'


def raw_settings():
    value = json.loads((SOURCE / 'settings.json').read_text())
    value['reward_revision'] = dict(schema='guitar_learning.song_reward.v2',
        initialization_checkpoint=str(SOURCE / 'final.pt'))
    return value


class SongRewardTransferTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1)
        cls.evidence = transfer.validate_experts(raw_settings())
        cls.contract = copy.deepcopy(cls.evidence['warmstart_payload']['identity']['architecture']['contract'])
        cls.contract['reward']['song'] = dict(schema='guitar_learning.song_metrics.v2', different_rewards=True)

    def test_real_source_evidence_binds_all_inputs_and_publication(self):
        evidence = self.evidence
        consumed = json.loads((SOURCE / 'inputs_before.json').read_text())
        self.assertEqual(len(consumed), 1753)
        self.assertTrue(set(consumed).issubset(evidence['source_pins']))
        for name in ('final.pt', 'settings.json', 'training_contract.json', 'inputs_before.json', 'final_checkpoint.json'):
            self.assertIn(str(SOURCE / name), evidence['source_pins'])
        self.assertEqual(evidence['warmstart_payload']['updates'], 8)

    def test_actor_exact_critic_and_rng_fresh(self):
        model = SongPolicy(500, contract=self.contract)
        before = {key:value.clone() for key,value in model.state_dict().items()}
        torch_rng = torch.get_rng_state().clone(); numpy_rng=np.random.get_state(); python_rng=random.getstate()
        with patch.object(transfer, 'validate_experts', return_value=self.evidence):
            report = transfer.apply_experts(model, raw_settings())
        self.assertTrue(torch.equal(torch_rng, torch.get_rng_state()))
        np.testing.assert_equal(numpy_rng, np.random.get_state()); self.assertEqual(python_rng, random.getstate())
        source = self.evidence['warmstart_payload']['model']
        for key,value in model.state_dict().items():
            actor = key == 'log_std' or key.startswith(('actor_encoders.', 'actor_heads.'))
            torch.testing.assert_close(value, source[key] if actor else before[key], rtol=0, atol=0)
        trainer=PPOTrainer(model)
        self.assertEqual(trainer.updates,0);self.assertFalse(trainer.actor_optimizer.state);self.assertFalse(trainer.value_optimizer.state)
        self.assertEqual(report['source_ppo_updates'],8);self.assertEqual(report['ppo_updates'],0)
        self.assertEqual(model.trainable_roles,('left','right'))

    def test_nonreward_changes_rejected_before_mutation(self):
        for section in ('observation','action','task','termination'):
            with self.subTest(section=section):
                contract=copy.deepcopy(self.contract);contract[section]['unexpected']=True
                model=SongPolicy(500,contract=contract);before={key:value.clone() for key,value in model.state_dict().items()}
                with patch.object(transfer,'validate_experts',return_value=self.evidence),self.assertRaisesRegex(ValueError,'exact observation'):
                    transfer.apply_experts(model,raw_settings())
                for key,value in model.state_dict().items():torch.testing.assert_close(value,before[key],rtol=0,atol=0)
        model=SongPolicy(500,contract=self.contract);model.architecture['size']='large'
        with patch.object(transfer,'validate_experts',return_value=self.evidence),self.assertRaises(ValueError):
            transfer.apply_experts(model,raw_settings())

    def test_strict_resume_keeps_reward_identity_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            trainer=PPOTrainer(SongPolicy(500,contract=self.contract))
            checkpoint=Path(folder)/'new.pt';trainer.save(checkpoint)
            PPOTrainer(SongPolicy(500,contract=self.contract)).load(checkpoint)
            with self.assertRaises(ValueError):
                trainer.load(SOURCE/'final.pt')

    def test_changed_consumed_file_is_rejected(self):
        original=transfer.dataset_manifest
        def changed(paths):
            result=original(paths)
            if isinstance(paths,dict) and len(paths)==1753:result[next(iter(result))]='0'*64
            return result
        with patch.object(transfer,'dataset_manifest',changed),self.assertRaisesRegex(RuntimeError,'inputs changed'):
            transfer.validate_experts(raw_settings())

    def test_wrong_published_checkpoint_hash_is_rejected(self):
        original=transfer.dataset_manifest
        def changed(paths):
            result=original(paths)
            if isinstance(paths,list) and len(paths)==5:result[str(SOURCE/'final.pt')]='0'*64
            return result
        with patch.object(transfer,'dataset_manifest',changed),self.assertRaisesRegex(ValueError,'published'):
            transfer.validate_experts(raw_settings())


if __name__=='__main__':unittest.main()
