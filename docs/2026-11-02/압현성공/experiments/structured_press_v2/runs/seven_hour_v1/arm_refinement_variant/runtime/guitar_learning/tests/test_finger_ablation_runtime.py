"""연구용 factory의 설정 격리와 원래 J 제약 검증을 CPU에서 확인한다."""
import copy
import unittest
from guitar_learning.tool.experiments.finger_ablation import flags, make_settings, research_runtime
from guitar_learning.training import finger_skill_runner as runner
from guitar_learning.training import rollout, ppo


class ResearchRuntimeTests(unittest.TestCase):
    def test_exact_factors_and_single_setting_difference(self):
        original = make_settings(flags(), num_envs=8)
        for factor in flags():
            variant = make_settings(flags([factor]), num_envs=8)
            difference = copy.deepcopy(variant)
            difference['finger_ablation'] = original['finger_ablation']
            if factor == 'separate':
                difference['ppo']['advantage_normalization'] = 'joint'
            self.assertEqual(original, difference)
        with self.assertRaises(ValueError): flags(['unknown'])

    def test_scoped_factories_restore_even_on_error(self):
        original = (runner._validate_joint_settings, runner._policy, rollout.GpuPool, ppo.DecisionPPOTrainer)
        config = flags(['separate'])
        settings = make_settings(config, num_envs=8)
        with research_runtime(config):
            runner._validate_joint_settings(settings)
            wrong = copy.deepcopy(settings)
            wrong['finger_skill']['hold_ticks'] = 2
            with self.assertRaises(ValueError): runner._validate_joint_settings(wrong)
            wrong = copy.deepcopy(settings)
            wrong['ppo']['cost_weight'] = 0.
            with self.assertRaises(ValueError): runner._validate_joint_settings(wrong)
            with self.assertRaises(ValueError): runner._validate_joint_settings(make_settings(flags(), num_envs=8))
        self.assertEqual(original, (runner._validate_joint_settings, runner._policy,
                                   rollout.GpuPool, ppo.DecisionPPOTrainer))
        with self.assertRaisesRegex(RuntimeError, 'intentional'):
            with research_runtime(config): raise RuntimeError('intentional')
        self.assertEqual(original, (runner._validate_joint_settings, runner._policy,
                                   rollout.GpuPool, ppo.DecisionPPOTrainer))
