"""Fresh PPO entrance is gated; scoped runner patches keep source parsers intact."""
import copy
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import torch
import torch._dynamo

from guitar_learning.training import runner as train_parallel
from guitar_learning.training import parallel, policy, ppo
from guitar_learning.tool.experiments.transition import train, transfer, learning
from guitar_learning.tool.experiments.transition.policy import SpecialistPolicy
from guitar_learning.tests.test_transition_transfer import contract,SOURCE


def settings():
    raw=json.loads((SOURCE/'settings.json').read_text())
    for key in ('song','joint_experts','reward_revision'):raw.pop(key)
    raw['transition']=dict(schema='guitar_learning.transition.v1',mode='single_a',tempo_scale=1.,role='left')
    raw['initialization']=dict(mode='source_actor',checkpoint=str(SOURCE/'final.pt'),gate_evaluations=[])
    raw.update(device='cpu',num_envs=1,horizon=2,updates=1)
    return train.settings_document(raw)


class TransitionTrainingTests(unittest.TestCase):
    def test_source_actor_is_available_for_probe_but_never_PPO_shortcut(self):
        value=settings()
        with self.assertRaisesRegex(ValueError,'four unassisted'):
            train.initialization_evidence(value,require_gate=True)
        for key,wrong in (('role','right'),('tempo_scale',True),('mode','full')):
            raw=copy.deepcopy(value);raw['transition'][key]=wrong
            with self.assertRaises(ValueError):train.settings_document(raw)

    def test_BC_requires_four_distinct_exact_checkpoint_policy_proofs(self):
        fake=types.ModuleType('guitar_learning.tool.experiments.transition.capture')
        value=settings();value['initialization'].update(mode='bc',gate_evaluations=['/eval/%d'%i for i in range(4)])
        arch=SpecialistPolicy(contract=contract()).architecture
        evidence=dict(payload=dict(architecture=arch),source_pins={})
        report=dict(action_source='policy',teacher_intervention=False,initialization_checkpoint_sha256='sha')
        fake.audit_capture=lambda path:dict(contract=contract(),report=copy.deepcopy(report),source_pins={})
        with patch.dict('sys.modules',{'guitar_learning.tool.experiments.transition.capture':fake}), \
                patch.object(learning,'validate_initialization',return_value=evidence), \
                patch('guitar_learning.imitation.imitation.dataset_manifest',return_value={str(SOURCE/'final.pt'):'sha'}):
            train.initialization_evidence(value,require_gate=True)
            report['teacher_intervention']=True
            with self.assertRaisesRegex(ValueError,'unassisted'):train.initialization_evidence(value,require_gate=True)
            report['teacher_intervention']=False;report['initialization_checkpoint_sha256']='other'
            with self.assertRaises(ValueError):train.initialization_evidence(value,require_gate=True)
            value['initialization']['gate_evaluations']=['/eval/a']*4
            with self.assertRaisesRegex(ValueError,'distinct'):train.initialization_evidence(value,require_gate=True)

    def test_reused_runner_patches_do_not_capture_original_source_settings(self):
        # Exercise the actual PPO constructor and source validator while all
        # temporary dispatch/model/trainer replacements are active.
        value=settings();value['initialization']['mode']='bc'
        original_settings=train_parallel.settings_document
        original_model=policy.Policy;original_trainer=ppo.PPOTrainer;original_pool=parallel.Pool
        from guitar_learning.tool.experiments.transition import worker
        from guitar_learning.training import persistent_audit
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';config=Path(folder)/'settings.json';config.write_text(json.dumps(value))
            args=types.SimpleNamespace(settings=config,out=out,resume=None)
            def generic_main():
                self.assertEqual(train_parallel.settings_document(json.loads(config.read_text())),value)
                # The frozen reward-v2 and original single-note parsers still
                # execute their real evidence checks under this dispatch.
                evidence=transfer.validate_source(SOURCE/'final.pt')
                self.assertEqual(evidence['payload']['updates'],24)
                model=policy.Policy(500,contract=contract())
                trainer=ppo.PPOTrainer(model)
                self.assertEqual(trainer.updates,0);self.assertFalse(trainer.actor_optimizer.state)
                (out/'report.json').write_text(json.dumps(dict(completed=True)))
            def initialize(model,settings):
                out.mkdir();return dict(critic='fresh',optimizer='fresh')
            with patch.dict('sys.modules',{'isaacgym':types.ModuleType('isaacgym')}), \
                    patch.object(train,'initialization_evidence',return_value=dict(source_pins={})), \
                    patch.object(transfer,'initialize_actor',side_effect=initialize), \
                    patch.object(train_parallel,'main',side_effect=generic_main), \
                    patch('guitar_learning.training.monitoring.available_memory_bytes',return_value=16*1024**3), \
                    patch.object(persistent_audit,'finalize_persistent_run',return_value=True):
                self.assertTrue(train.run(value,args)['completed'])
            self.assertIs(train_parallel.settings_document,original_settings)
            self.assertIs(policy.Policy,original_model);self.assertIs(ppo.PPOTrainer,original_trainer)
            self.assertIs(parallel.Pool,original_pool)


if __name__=='__main__':unittest.main()
