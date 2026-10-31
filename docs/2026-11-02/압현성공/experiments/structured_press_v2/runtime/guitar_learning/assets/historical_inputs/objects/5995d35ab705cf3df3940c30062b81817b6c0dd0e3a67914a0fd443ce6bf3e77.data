"""Explicit curriculum settings and reversible process-private dispatch."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from guitar_learning import parallel, specialist_parallel, train_specialists, train_parallel
from guitar_learning.skill_settings import settings_document, SKILLS
from guitar_learning.skill_parallel import SkillPool, skill_native_environment
from guitar_learning.train_skills import run, summarize_run


class SkillRunnerTests(unittest.TestCase):
    def test_each_skill_explicit_and_cost_weight_preserved(self):
        for role, skills in SKILLS.items():
            for skill in skills:
                source = dict(specialist=dict(role=role), skill=skill, ppo=dict(cost_weight=.1))
                saved = copy.deepcopy(source)
                result = settings_document(source)
                self.assertEqual(result['skill'], skill)
                self.assertEqual(result['specialist']['role'], role)
                self.assertEqual(result['ppo']['cost_weight'], .1)
                self.assertEqual(source, saved)
        invalid = ({}, dict(skill='reach'), dict(specialist=dict(role='left')),
            dict(specialist=dict(role='joint'), skill='timed'),
            dict(specialist=dict(role='left'), skill='cross'),
            dict(specialist=dict(role='right'), skill='hold'),
            dict(specialist=dict(role='left'), skill=True),
            dict(specialist=dict(role='left'), skill='reach', ppo=dict(cost_weight=0)))
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError): settings_document(value)

    def test_only_same_hand_existing_checkpoint_can_warm_start(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary)/'expert.pt'; checkpoint.touch()
            for role in ('left', 'right'):
                result = settings_document(dict(specialist=dict(role=role, **{role+'_checkpoint':str(checkpoint)}), skill=SKILLS[role][0]))
                self.assertEqual(result['specialist'][role+'_checkpoint'], str(checkpoint.resolve()))
                other = 'right' if role == 'left' else 'left'
                with self.assertRaisesRegex(ValueError, 'partner'):
                    settings_document(dict(specialist=dict(role=role, **{other+'_checkpoint':str(checkpoint)}), skill=SKILLS[role][0]))

    def test_pool_injects_hand_and_skill_without_changing_callers(self):
        specs = [dict(out='unused')]
        stage = dict(role='left', left_checkpoint=None, right_checkpoint=None)
        with patch.object(parallel.Pool, '__init__', return_value=None) as base:
            SkillPool(specs, specialist=stage, skill='reach')
        self.assertEqual(specs, [dict(out='unused')])
        actual = base.call_args.args[0][0]
        self.assertEqual(actual['skill'], 'reach')
        self.assertEqual(actual['specialist'], stage)
        self.assertIs(base.call_args.kwargs['worker_factory'], skill_native_environment)
        with self.assertRaises(ValueError): SkillPool(specs, specialist=stage, skill='cross')

    def test_dispatch_nested_runner_and_settings_restored_after_interrupt(self):
        originals = specialist_parallel.SpecialistPool, parallel.Pool, train_parallel.settings_document
        with tempfile.TemporaryDirectory() as temporary:
            args = SimpleNamespace(out=Path(temporary)/'run', resume=None)
            settings = settings_document(dict(specialist=dict(role='right'), skill='cross'))
            def fail():
                self.assertEqual(train_parallel.settings_document({}), settings)
                with patch.object(originals[1], '__init__', return_value=None) as base:
                    parallel.Pool([dict(out='unused')])
                self.assertEqual(base.call_args.args[0][0]['skill'], 'cross')
                raise KeyboardInterrupt()
            with patch.dict(sys.modules, {'isaacgym':SimpleNamespace()}), \
                 patch.object(train_parallel, 'main', fail), self.assertRaises(KeyboardInterrupt):
                run(settings, args)
        self.assertEqual((specialist_parallel.SpecialistPool, parallel.Pool, train_parallel.settings_document), originals)

    def test_preparation_report_never_claims_contact_or_music_success(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            (out/'report.json').write_text(json.dumps(dict(settings=dict(skill='ready'))))
            (out/'specialist_report.json').write_text(json.dumps(dict(role='right', successful_episodes=1,
                episodes=[dict(music=dict(matched50=0), specialist=dict(stage_success=True))])))
            summary = summarize_run(out)
            self.assertEqual(summary['success_scope'], 'preparation_geometry_only')
            self.assertEqual(summary['episodes'][0]['music']['matched50'], 0)
            self.assertTrue((out/'skill_report.json').is_file())


if __name__ == '__main__': unittest.main()
