"""Explicit timing migration preserves actor behavior and rejects unsafe changes."""
import copy
from pathlib import Path
import torch
import unittest
from unittest.mock import patch
from guitar_learning.imitation.imitation import SCHEMA
from guitar_learning.imitation.imitation_environment import ImitationEnvironment, profile_settings
from guitar_learning.skills.skill_environment_v2 import SkillTrainingEnvironmentV2
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOConfig, PPOTrainer
from guitar_learning.timing.timing_curriculum import TimingConfig
from guitar_learning.timing.timing_transfer import apply_actor_initialization, validate_contracts
from guitar_learning.tests import test_timing_environment as fixtures


class TimingTransferTests(unittest.TestCase):
    def setUp(self):
        fixtures.TimingEnvironmentTests.setUp(self)
        self.threads = torch.get_num_threads(); torch.set_num_threads(1)

    def tearDown(self):
        fixtures.TimingEnvironmentTests.tearDown(self)
        torch.set_num_threads(self.threads)

    def contract(self, role='left', legacy=False, stage=0):
        if legacy:
            def construct(*args, task, role, **kwargs):
                kwargs.pop('timing', None)
                skill = 'hold' if role == 'left' else 'cross'
                skill_config, guide_config, profile = profile_settings(role, skill)
                env = SkillTrainingEnvironmentV2(*args, task=task, role=role, skill=skill,
                    skill_config=skill_config, guide_config=guide_config, **kwargs)
                return ImitationEnvironment(env, profile)
            with patch.object(fixtures, 'TimingEnvironment', construct):
                env = fixtures.TimingEnvironmentTests.environment(self, role)
        else:
            env = fixtures.TimingEnvironmentTests.environment(self, role, timing=TimingConfig(stage_index=stage))
        env.reset()
        return copy.deepcopy(env.contract)

    def model(self, contract, role='left'):
        return SpecialistPolicy(contract['observation']['dimension'], size='small',
            role=role, frozen_partner=False, contract=contract)

    def payload(self, source, kind):
        if kind == 'bc':
            return dict(schema=SCHEMA, role=source.role, architecture=copy.deepcopy(source.architecture),
                dataset_manifest={'synthetic CPU fixture': 'not native evidence'}, training={'steps': 1},
                model=copy.deepcopy(source.state_dict()))
        trainer = PPOTrainer(source)
        return dict(identity=trainer._identity(), updates=1, model=copy.deepcopy(source.state_dict()))

    def save(self, payload, name='source.pt'):
        path = Path(self.folder.name)/name
        torch.save(payload, path)
        return path

    def test_bc_and_ppo_expand_only_active_actor_input_and_preserve_behavior(self):
        for role, kind in (('left', 'bc'), ('right', 'ppo')):
            source = self.model(self.contract(role, legacy=True), role)
            target = self.model(self.contract(role), role)
            with torch.no_grad():
                source.actor_heads[role].weight.normal_(0., .05)
                source.actor_heads[role].bias.normal_(0., .05)
                source.log_std.fill_(-4.)
            before = copy.deepcopy(target.state_dict())
            payload = self.payload(source, kind)
            result = apply_actor_initialization(target, self.save(payload, role+'.pt'), kind=kind)
            self.assertEqual(len(result['expanded']), 1)
            first = 'actor_encoders.'+role+'.state.0.weight'
            self.assertTrue(torch.equal(target.state_dict()[first][:, :505], source.state_dict()[first]))
            self.assertEqual(torch.count_nonzero(target.state_dict()[first][:, 505:]), 0)
            for key, value in target.state_dict().items():
                if key.startswith(('actor_encoders.'+role+'.', 'actor_heads.'+role+'.')):
                    if key != first: self.assertTrue(torch.equal(value, source.state_dict()[key]), key)
                elif key != 'log_std':
                    self.assertTrue(torch.equal(value, before[key]), key)
            old_inputs = (torch.randn(3, 505), torch.randn(3, 64, 24), torch.ones(3, 64, dtype=torch.bool),
                torch.randn(3, 2, 24), torch.ones(3, 2, dtype=torch.bool))
            new_inputs = (torch.cat((old_inputs[0], torch.randn(3, 31)), dim=1), *old_inputs[1:])
            old_action = source.act(*old_inputs, deterministic=True)['action']
            new_action = target.act(*new_inputs, deterministic=True)['action']
            self.assertTrue(torch.allclose(old_action, new_action, atol=1e-6, rtol=1e-6))
            selection = target.role_slices[role]
            self.assertTrue(torch.equal(target.log_std[selection], source.log_std[selection]))

    def test_timing_stage_warm_start_preserves_learned_history_but_strict_resume_rejects(self):
        source = self.model(self.contract(stage=0))
        target = self.model(self.contract(stage=1))
        with torch.no_grad(): source.actor_encoders['left'].state[0].weight[:, 505:].fill_(.125)
        path = self.save(self.payload(source, 'ppo'))
        result = apply_actor_initialization(target, path, kind='ppo')
        self.assertEqual(result['expanded'], [])
        self.assertTrue(torch.equal(target.actor_encoders['left'].state[0].weight,
                                    source.actor_encoders['left'].state[0].weight))
        trainer = PPOTrainer(source); saved = Path(self.folder.name)/'strict.pt'; trainer.save(saved)
        with self.assertRaisesRegex(ValueError, 'mismatch'): PPOTrainer(target).load(saved)

    def test_contract_physics_safety_goal_and_prefix_changes_reject_before_mutation(self):
        source = self.model(self.contract(legacy=True))
        good = self.payload(source, 'bc')
        target = self.model(self.contract())
        variants = []
        for field in ('action', 'termination'):
            bad = copy.deepcopy(good); bad['architecture']['contract'][field]['unexpected'] = 1
            variants.append(bad)
        for key, index, value in (('fields', 0, 'different_joint'), ('scales', 0, 2.)):
            bad = copy.deepcopy(good); bad['architecture']['contract']['observation'][key][index] = value
            variants.append(bad)
        bad = copy.deepcopy(good); bad['architecture']['contract']['task']['targets'][0]['finger'] = 2
        variants.append(bad)
        bad = copy.deepcopy(good); bad['model']['actor_heads.left.bias'][0] = float('nan')
        variants.append(bad)
        bad = copy.deepcopy(good); bad['architecture']['role'] = 'right'; variants.append(bad)
        bad = copy.deepcopy(good); bad['model']['reward_critic.weight'] = torch.zeros(2, 256)
        variants.append(bad)
        before = copy.deepcopy(target.state_dict())
        for index, payload in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(ValueError):
                apply_actor_initialization(target, self.save(payload), kind='bc')
            for key, value in target.state_dict().items(): self.assertTrue(torch.equal(value, before[key]), key)
        bad_target = copy.deepcopy(target.architecture['contract'])
        bad_target['observation']['fields'][-1] = 'hidden_or_reordered_state'
        with self.assertRaises(ValueError): validate_contracts(source.architecture['contract'], bad_target, 'left')


if __name__ == '__main__': unittest.main()
