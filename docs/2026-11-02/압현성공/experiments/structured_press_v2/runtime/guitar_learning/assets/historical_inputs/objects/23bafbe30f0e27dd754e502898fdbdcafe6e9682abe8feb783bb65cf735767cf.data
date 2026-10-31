"""Stage selection and process-private dispatch must preserve legacy runners."""
import gzip
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from guitar_learning import parallel, policy, ppo, train_parallel
from guitar_learning.specialist_settings import settings_document, frozen_partner, expert_paths
from guitar_learning.specialist_parallel import SpecialistPool, specialist_native_environment, specialist_compact
from guitar_learning.train_specialists import run, summarize_run


class SpecialistRunnerTests(unittest.TestCase):
    def test_stages_are_explicit_and_preserve_stability_defaults(self):
        for role in ('left', 'right'):
            settings = settings_document(dict(specialist=dict(role=role)))
            self.assertEqual(settings['specialist']['role'], role)
            self.assertEqual(settings['ppo']['cost_weight'], 1.)
            self.assertEqual(settings['ppo']['cost_gamma'], 1.)
            self.assertFalse(frozen_partner(settings['specialist']))
        for value in ({}, dict(specialist={}), dict(specialist=dict(role='joint')),
                      dict(specialist=dict(role='left'), stage='C'),
                      dict(specialist=dict(role='left'), music=dict(reward_mode='dense_v2')),
                      dict(specialist=dict(role='left'), music=dict(goal_event_indices=[0])),
                      dict(specialist=dict(role='left'), ppo=dict(cost_weight=0.)),
                      dict(specialist=dict(role='left', surprise=True))):
            with self.subTest(value=value), self.assertRaises(ValueError):
                settings_document(value)

    def test_partner_and_joint_require_explicit_existing_experts(self):
        with tempfile.TemporaryDirectory() as temporary:
            left = Path(temporary) / 'left.pt'; left.touch()
            right = Path(temporary) / 'right.pt'; right.touch()
            stage = dict(role='right', left_checkpoint=str(left))
            parsed = settings_document(dict(specialist=stage))['specialist']
            self.assertTrue(frozen_partner(parsed))
            self.assertEqual(expert_paths(parsed), [left.resolve()])
            stage = dict(role='joint', left_checkpoint=str(left), right_checkpoint=str(right))
            self.assertFalse(frozen_partner(settings_document(dict(specialist=stage))['specialist']))
            with self.assertRaises(ValueError):
                settings_document(dict(specialist=dict(role='left', right_checkpoint='missing.pt')))

    def test_pool_injects_stage_without_mutating_caller_specs(self):
        specs = [dict(out='unused')]
        def fixture(spec, index): pass
        with patch.object(parallel.Pool, '__init__', return_value=None) as base:
            SpecialistPool(specs, specialist=dict(role='left'), worker_factory=fixture)
        self.assertNotIn('specialist', specs[0])
        self.assertEqual(base.call_args.args[0][0]['specialist'], dict(role='left'))
        self.assertIs(base.call_args.kwargs['worker_factory'], fixture)

    def test_cli_dispatch_is_subclassable_and_restored_on_failure(self):
        originals = parallel.Pool, policy.Policy, ppo.PPOTrainer, train_parallel.settings_document
        with tempfile.TemporaryDirectory() as temporary:
            args = SimpleNamespace(out=Path(temporary) / 'run', resume=None)
            settings = settings_document(dict(specialist=dict(role='left')))
            def fail():
                class Measured(parallel.Pool): pass
                self.assertTrue(issubclass(Measured, SpecialistPool))
                self.assertEqual(train_parallel.settings_document({}), settings)
                raise KeyboardInterrupt()
            with patch.dict(sys.modules, {'isaacgym': SimpleNamespace()}), \
                 patch.object(train_parallel, 'main', fail), self.assertRaises(KeyboardInterrupt):
                run(settings, args)
        self.assertEqual((parallel.Pool, policy.Policy, ppo.PPOTrainer, train_parallel.settings_document), originals)

    def test_summary_separates_hand_success_and_music(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out / 'report.json').write_text(json.dumps(dict(completed=True, transitions=1,
                settings=dict(specialist=dict(role='right')))))
            evidence = dict(stage_success=True)
            episode = dict(reason='timeline_complete', reward=1., cost=0., steps=1,
                           specialist=evidence, music=dict(strict_matches=0))
            with gzip.open(out / 'transitions.jsonl.gz', 'wt') as stream:
                stream.write(json.dumps(dict(infos=[dict(specialist=evidence, episode=episode)])) + '\n')
            result = summarize_run(out)
            self.assertEqual(result['successful_episodes'], 1)
            self.assertEqual(result['episodes'][0]['music']['strict_matches'], 0)


if __name__ == '__main__':
    unittest.main()
