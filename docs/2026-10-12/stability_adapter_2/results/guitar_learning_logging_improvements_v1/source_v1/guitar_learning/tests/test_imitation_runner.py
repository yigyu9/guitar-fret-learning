"""Grounded profile identity, actor transfer order and reversible PPO dispatch."""
import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning import imitation_environment, parallel, ppo, skill_parallel_v2
from guitar_learning import train_parallel, train_skills
from guitar_learning.imitation_environment import build_environment, profile_settings
from guitar_learning.skill_environment_v2 import SkillTrainingEnvironmentV2
from guitar_learning.train_imitation_ppo import (settings_document, run,
                                                imitation_native_environment)
from guitar_learning.tests import test_skill_environment as fixtures


class ImitationProfileTests(unittest.TestCase):
    setUp = fixtures.SkillEnvironmentTests.setUp
    tearDown = fixtures.SkillEnvironmentTests.tearDown

    def test_profile_controls_and_505_observation_have_exact_reset_identity(self):
        for role, skill in (('left', 'hold'), ('right', 'cross')):
            def construct(config, out, **kwargs):
                kwargs.pop('bundle')
                with patch.object(fixtures, 'SkillTrainingEnvironment', SkillTrainingEnvironmentV2):
                    return fixtures.SkillEnvironmentTests.environment(self, **kwargs)
            with patch.object(imitation_environment, 'build_skill_environment', construct):
                env = build_environment({}, 'unused', role=role, skill=skill, bundle='fixture')
            observation, info = env.reset()
            first_contract = copy.deepcopy(info['training_contract'])
            self.assertEqual(observation['state'].shape, (505,))
            self.assertEqual(env.task.duration_s, 4.)
            self.assertEqual(env.control.preparation_seconds, 2.)
            profile = first_contract['task']['specialist']['imitation_profile']
            self.assertEqual(profile['name'], 'guitar_learning.grounded_imitation.v1')
            self.assertEqual(profile['role'], role)
            if role == 'left':
                self.assertEqual(env.skill_config.approach_second, 0.)
            else:
                self.assertEqual(env.guide_config.strike_y_m, -.36)
                self.assertEqual(env.guide_config.depth_m, .004)
                self.assertEqual(env.guide_config.sweep_half_width_m, .008)
            session = env.control.session
            _, reward, terminated, truncated, step_info = env.step(np.zeros(39))
            self.assertFalse(terminated or truncated)
            self.assertTrue(np.isfinite(reward))
            self.assertEqual(step_info['music']['matched50'], 0)
            _, reset_info = env.reset()
            self.assertIs(env.control.session, session)
            self.assertEqual(reset_info['training_contract'], first_contract)

    def test_profile_rejects_other_skills_and_configuration_override(self):
        for role, skill in (('left', 'reach'), ('right', 'timed'), ('joint', 'hold')):
            with self.assertRaises(ValueError): profile_settings(role, skill)
        for kwargs in ({'skill_config': None}, {'guide_config': None},
                       {'start_event_index': 1}, {'tempo_scale': .5}):
            with self.assertRaises(ValueError):
                build_environment({}, 'unused', role='left', skill='hold', **kwargs)


class ImitationRunnerTests(unittest.TestCase):
    def test_settings_require_explicit_new_actor_and_fixed_supported_profile(self):
        with tempfile.TemporaryDirectory() as temporary:
            checkpoint = Path(temporary)/'actor.pt'; checkpoint.touch()
            source = dict(actor_initialization=str(checkpoint),
                          specialist=dict(role='left'), skill='hold')
            original = copy.deepcopy(source)
            settings = settings_document(source)
            self.assertEqual(source, original)
            self.assertEqual(settings['actor_initialization'], str(checkpoint.resolve()))
            variants = [dict(source, actor_initialization=None),
                dict(source, actor_initialization='relative.pt'), dict(source, skill='reach'),
                dict(source, start_event_index=1), dict(source, tempo_scale=.5),
                dict(source, specialist=dict(role='left', left_checkpoint=str(checkpoint))),
                dict(source, specialist=dict(role='left', right_checkpoint=str(checkpoint)))]
            for value in variants:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    settings_document(value)
            self.assertEqual(settings_document(dict(source, skill='cross',
                specialist=dict(role='right')))['skill'], 'cross')

    def dispatch(self, resume=False, failure=False):
        from guitar_learning.recording import digest
        from stability_adapter_2.lower_body_release_v1 import common
        calls = []
        class OriginalTrainer:
            def __init__(self, model, config=None): calls.append('optimizer_construction')
        def transfer(model, path):
            calls.append('actor_transfer')
            return dict(scope='actor_only')
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            actor = folder/'actor.pt'; actor.write_bytes(b'fixed BC input')
            settings = settings_document(dict(actor_initialization=str(actor),
                specialist=dict(role='left'), skill='hold'))
            args = SimpleNamespace(out=folder/'run', resume=folder/'resume.pt' if resume else None)
            args.out.mkdir()
            original_pool = skill_parallel_v2.SkillPool
            original_native_pool = parallel.Pool
            def core():
                self.assertEqual(train_parallel.settings_document({}), settings)
                with patch.object(original_native_pool, '__init__', return_value=None) as native_pool:
                    parallel.Pool([dict(out='unused')])
                self.assertIs(native_pool.call_args.kwargs['worker_factory'], imitation_native_environment)
                self.assertEqual(native_pool.call_args.args[0][0]['skill'], 'hold')
                pins = common.pin('unused', extra=())
                self.assertEqual(pins[str(actor.resolve())], digest(actor))
                ppo.PPOTrainer(object(), None)
                if failure: raise KeyboardInterrupt()
            def pin(config, extra=()):
                self.assertIn(actor.resolve(), extra)
                return {str(p.resolve()): digest(p) for p in extra}
            with patch.dict(sys.modules, {'isaacgym': SimpleNamespace(),
                    'guitar_learning.imitation': SimpleNamespace(apply_actor_initialization=transfer)}), \
                 patch.object(ppo, 'PPOTrainer', OriginalTrainer), \
                 patch.object(common, 'pin', pin), \
                 patch.object(train_parallel, 'main', core), \
                 patch.object(train_skills, 'summarize_run', return_value='summary'):
                if failure:
                    with self.assertRaises(KeyboardInterrupt): run(settings, args)
                else:
                    self.assertEqual(run(settings, args), 'summary')
                self.assertIs(ppo.PPOTrainer, OriginalTrainer)
                self.assertIs(skill_parallel_v2.SkillPool, original_pool)
                self.assertIs(common.pin, pin)
            metadata = json.loads((args.out/'actor_initialization.json').read_text())
            self.assertEqual(metadata['mode'], 'strict_resume' if resume else
                             'BC_actor_only_new_critics_and_optimizers')
            self.assertEqual(metadata['sha256'], digest(actor))
        return calls

    def test_actor_initialization_precedes_optimizer_construction(self):
        self.assertEqual(self.dispatch(), ['actor_transfer', 'optimizer_construction'])

    def test_strict_resume_pins_actor_without_overwriting_resumed_actor(self):
        self.assertEqual(self.dispatch(resume=True), ['optimizer_construction'])

    def test_interrupt_restores_all_private_patches(self):
        self.assertEqual(self.dispatch(failure=True), ['actor_transfer', 'optimizer_construction'])


if __name__ == '__main__': unittest.main()
