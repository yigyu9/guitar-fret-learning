"""Reward-v2 deterministic evaluation binds the new implementation transactionally."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch._dynamo
from guitar_learning.tool.experiments.song import evaluate as original, policy, transfer, worker
from guitar_learning.song import environment
from guitar_learning.tool.experiments.song_reward_v2 import evaluate, policy as revised_policy, transfer as revised_transfer, worker as revised_worker
from guitar_learning.song import reward_environment as revised_environment


class RewardEvaluationWrapperTests(unittest.TestCase):
    def bindings(self):
        return (environment.build_environment,policy.SongPolicy,transfer.validate_experts,
            transfer.apply_experts,worker.compact)

    def test_trained_checkpoint_dispatch_and_all_bindings_restored(self):
        previous=self.bindings();settings={'reward_revision':{'schema':'guitar_learning.song_reward.v2'}}
        args=SimpleNamespace(run=Path('/tmp/frozen_reward_v2_checkpoint'))
        expected=object()
        def execute(actual_settings,actual_args):
            self.assertIs(actual_settings,settings);self.assertIs(actual_args,args)
            self.assertEqual(self.bindings(),(revised_environment.build_environment,revised_policy.RewardPolicy,
                revised_transfer.validate_experts,revised_transfer.apply_experts,revised_worker.compact))
            return expected
        with patch.dict('sys.modules',{'isaacgym':SimpleNamespace()}),patch.object(original,'evaluate',side_effect=execute) as delegated:
            self.assertIs(evaluate.evaluate(settings,args),expected)
        delegated.assert_called_once_with(settings,args);self.assertEqual(self.bindings(),previous)

    def test_primary_evaluation_error_preserved_and_bindings_restored(self):
        previous=self.bindings();args=SimpleNamespace(run=Path('/tmp/frozen_reward_v2_checkpoint'))
        with patch.dict('sys.modules',{'isaacgym':SimpleNamespace()}), \
                patch.object(original,'evaluate',side_effect=ValueError('primary evaluator error')):
            with self.assertRaisesRegex(ValueError,'primary evaluator error'):evaluate.evaluate({},args)
        self.assertEqual(self.bindings(),previous)

    def test_untrained_initialization_is_rejected_before_delegation(self):
        previous=self.bindings()
        with patch.dict('sys.modules',{'isaacgym':SimpleNamespace()}),patch.object(original,'evaluate') as delegated:
            with self.assertRaisesRegex(ValueError,'trained checkpoint'):
                evaluate.evaluate({},SimpleNamespace(run=None))
        delegated.assert_not_called();self.assertEqual(self.bindings(),previous)


if __name__=='__main__':unittest.main()
