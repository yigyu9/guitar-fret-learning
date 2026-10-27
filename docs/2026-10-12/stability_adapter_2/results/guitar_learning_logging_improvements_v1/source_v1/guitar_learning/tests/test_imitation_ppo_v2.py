"""The v2 entrypoint replaces BC comparison only, restoring process bindings."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from guitar_learning import imitation, ppo, train_imitation_ppo, train_skills_v2
from guitar_learning.train_imitation_ppo_v2 import run


class ImitationPPOV2Tests(unittest.TestCase):
    def test_dispatch_preserves_settings_and_restores_loader_after_interrupt(self):
        original = imitation.apply_actor_initialization
        sentinel = lambda model, path: None
        settings, args = object(), object()
        def inner(actual_settings, actual_args):
            self.assertIs(actual_settings, settings)
            self.assertIs(actual_args, args)
            self.assertIs(imitation.apply_actor_initialization, sentinel)
            raise KeyboardInterrupt()
        with patch.dict(sys.modules, {'isaacgym': SimpleNamespace(),
                'guitar_learning.imitation_v2': SimpleNamespace(apply_actor_initialization=sentinel)}), \
             patch.object(train_imitation_ppo, 'run', inner):
            with self.assertRaises(KeyboardInterrupt): run(settings, args)
        self.assertIs(imitation.apply_actor_initialization, original)

    def transfer_through_original_runner(self, resume):
        calls = []
        original = imitation.apply_actor_initialization
        class Trainer:
            def __init__(self, model, config=None): calls.append('optimizer')
        def canonical_transfer(model, path):
            self.assertEqual(model.architecture['contract']['tuple_field'], ('same',))
            calls.append('canonical_transfer')
            return dict(contract_comparison='JSON_equivalent')
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            actor = out/'actor.pt'; actor.write_bytes(b'BC fixture')
            settings = dict(actor_initialization=str(actor))
            args = SimpleNamespace(out=out, resume=out/'resume.pt' if resume else None)
            model = SimpleNamespace(architecture=dict(contract=dict(tuple_field=('same',))))
            raw_architecture = model.architecture
            def nested(actual_settings, actual_args):
                self.assertIs(actual_settings, settings)
                self.assertIs(actual_args, args)
                ppo.PPOTrainer(model)
                return 'same_legacy_runner'
            with patch.dict(sys.modules, {'isaacgym': SimpleNamespace(),
                    'guitar_learning.imitation_v2': SimpleNamespace(apply_actor_initialization=canonical_transfer)}), \
                 patch.object(ppo, 'PPOTrainer', Trainer), \
                 patch.object(train_skills_v2, 'run', nested):
                self.assertEqual(run(settings, args), 'same_legacy_runner')
                self.assertIs(ppo.PPOTrainer, Trainer)
            self.assertIs(model.architecture, raw_architecture)
            self.assertEqual(model.architecture['contract']['tuple_field'], ('same',))
            report = json.loads((out/'actor_initialization.json').read_text())
            self.assertEqual(report['mode'], 'strict_resume' if resume else
                             'BC_actor_only_new_critics_and_optimizers')
        self.assertIs(imitation.apply_actor_initialization, original)
        return calls

    def test_canonical_initializer_is_used_before_unchanged_ppo_optimizer(self):
        self.assertEqual(self.transfer_through_original_runner(False),
                         ['canonical_transfer', 'optimizer'])

    def test_strict_resume_keeps_original_identity_and_skips_bc_transfer(self):
        self.assertEqual(self.transfer_through_original_runner(True), ['optimizer'])


if __name__ == '__main__': unittest.main()
