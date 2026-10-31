"""무접촉 실험의 시간순 정산·초기화·평가 격리를 CPU에서 검사한다."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import torch

from termination_runtime import environment_class, update_streak, policy_class, termination_spec


class FakeEnvironment:
    """GPU 장면 없이 실제 자식 훅의 호출·비용 경로를 검사하는 최소 부모다."""
    def __init__(self, metadata, **kwargs):
        self.device = 'cpu'
        self.initialized = False
        self.end = torch.tensor([3., 4., 4., 5., 6., 7., 8., 9.], dtype=torch.float64)
        self.contract = dict(observation=dict(fields=['x'], scales=[1.], dimension=1),
            termination=dict(additional_failure_reasons=[]))
        self.evaluation = False
        self.now = torch.tensor([9., 9.], dtype=torch.float64)

    def _tensor(self, values):
        return torch.tensor(values)

    def _allocate(self, count):
        self.N = count
        self.note = {'clean': torch.zeros(count, len(self.end))}
        self.focus_mask = torch.ones_like(self.note['clean'], dtype=torch.bool)
        self.score_offset = torch.zeros(count, dtype=torch.float64)
        self.existing_failure = torch.zeros(count, dtype=torch.bool)
        self.cost = torch.zeros(count)
        self.paid = torch.zeros(count, dtype=torch.bool)

    def reset(self, indices, snapshot):
        if not self.initialized:
            self._allocate(2)
            self.initialized = True
        self.note['clean'][indices] = 0
        return self._observation_state(torch.zeros(2, 1))

    def _control_failures(self):
        return self.existing_failure

    def _score_time(self):
        return self.now+self.score_offset

    def _local_time(self):
        return self.now

    def _observation_state(self, state):
        return state

    def end_control(self):
        # 실환경과 같은 순서: 실패 훅 -> 한 번의 통합 비용 -> 반환.
        failed = self._control_failures()
        self.cost += 5*(failed & ~self.paid)
        self.paid |= failed
        return failed

    def _episode(self, index, failed):
        return dict(failure_reasons=[], termination=dict(
            physical_failure=bool(self.existing_failure[index]), wrist_failure=False,
            primary_reason='physical_failure' if self.existing_failure[index] else 'timeline_complete'))


class StreakTests(unittest.TestCase):
    def test_order_empty_and_repeated_calls(self):
        initial = torch.tensor([2, 4])
        opportunities = torch.tensor([[1, 0, 1, 1, 1], [0, 0, 0, 0, 0]], dtype=torch.bool)
        contacted = torch.tensor([[0, 0, 1, 0, 0], [0, 0, 0, 0, 0]], dtype=torch.bool)
        final, maximum = update_streak(initial, opportunities, contacted)
        self.assertEqual(final.tolist(), [2, 4])
        self.assertEqual(maximum.tolist(), [3, 4])
        empty = torch.zeros(2, 0, dtype=torch.bool)
        self.assertEqual(update_streak(initial, empty, empty)[0].tolist(), [2, 4])

    def test_vectorized_order_matches_scalar_reference(self):
        generator = torch.Generator().manual_seed(17)
        initial = torch.randint(0, 8, (37,), generator=generator)
        opportunities = torch.rand(37, 19, generator=generator) > .3
        contacted = torch.rand(37, 19, generator=generator) > .6
        final, maximum = update_streak(initial, opportunities, contacted)
        for row in range(37):
            streak = peak = int(initial[row])
            for opportunity, contact in zip(opportunities[row], contacted[row]):
                if opportunity:
                    streak = 0 if contact else streak+1
                    peak = max(peak, streak)
            self.assertEqual((int(final[row]), int(maximum[row])), (streak, peak))

    def environment(self, threshold=5):
        env = environment_class(FakeEnvironment, threshold)({})
        env.reset([0, 1], None)
        return env

    def test_same_end_group_contact_resets_and_repeated_hook_is_idempotent(self):
        env = self.environment()
        env.note['clean'][0, 1] = 1/240.
        failed = env.end_control()
        self.assertEqual(env.no_contact_opportunities.tolist(), [6, 6])
        self.assertEqual(env.no_contact_streak.tolist(), [5, 6])
        self.assertEqual(failed.tolist(), [True, True])
        env.end_control()
        self.assertEqual(env.cost.tolist(), [5., 5.])
        self.assertEqual(env.no_contact_opportunities.tolist(), [6, 6])

    def test_selected_only_preparation_and_unfinished_excluded(self):
        env = self.environment(3)
        env.now[:] = 5.
        env.focus_mask[:, 3] = False  # 5초 음은 미선택.
        env.note['clean'][:, 0] = 1.  # 준비 경계 음은 기회가 아니다.
        self.assertFalse(env.end_control().any())
        self.assertEqual(env.no_contact_opportunities.tolist(), [1, 1])
        self.assertEqual(env.no_contact_streak.tolist(), [1, 1])
        env.now[:] = 2.99
        self.assertFalse(env.end_control().any())
        self.assertEqual(env.no_contact_opportunities.tolist(), [1, 1])

    def test_evaluation_counts_but_keeps_original_failures_and_no_new_cost(self):
        env = self.environment(3)
        env.evaluation = True
        env.existing_failure[1] = True
        self.assertEqual(env.end_control().tolist(), [False, True])
        self.assertEqual(env.cost.tolist(), [0., 5.])
        self.assertEqual(env.no_contact_streak.tolist(), [6, 6])
        row = env._episode(0, False)
        self.assertFalse(row['termination']['no_contact_failure'])
        self.assertTrue(row['no_contact_termination']['evaluation_disabled'])

    def test_baseline_same_dimensions_no_new_failure_and_contract(self):
        env = self.environment(0)
        self.assertFalse(env.end_control().any())
        state = env._observation_state(torch.zeros(2, 1))/env.scales
        self.assertEqual(state.shape, (2, env.contract['observation']['dimension']))
        self.assertEqual(state[:, -2:].tolist(), [[1., 0.], [1., 0.]])
        self.assertEqual(env.contract['termination']['no_contact_experiment']['threshold'], 0)
        self.assertEqual(len(env.contract['termination']['no_contact_experiment']['module_sha256']), 64)

    def test_partial_reset_clears_before_return_observation(self):
        env = self.environment()
        env.end_control()
        observation = env.reset([0], None)
        self.assertEqual(observation[0, -2:].tolist(), [0., 5.])
        self.assertEqual(env.no_contact_streak.tolist(), [0, 6])
        self.assertFalse(env.no_contact_seen[0].any())
        self.assertFalse(env.no_contact_crossed[0])
        self.assertTrue(env.no_contact_crossed[1])

    def test_primary_reason_preserves_physical_priority(self):
        env = self.environment(3)
        env.existing_failure[1] = True
        env.end_control()
        self.assertEqual(env._episode(0, True)['termination']['primary_reason'], 'no_contact')
        self.assertEqual(env._episode(1, True)['termination']['primary_reason'], 'physical_failure')
        self.assertIn('no_contact', env._episode(1, True)['failure_reasons'])


class PolicyTests(unittest.TestCase):
    def test_actual_frozen_policy_forward_checkpoint_and_strict_contract(self):
        root = Path(__file__).resolve().parent.parent/'개별비교연구'
        sys.path.insert(0, str(root/'recovery/frozen'))
        from guitar_learning.tool.experiments.finger_ablation_learning import LearningPolicy, LearningTrainer
        contract = json.loads((root/'runs/baseline_s7/train/J/training_contract.json').read_text())
        flags = contract['reward']['finger_ablation']['flags']
        original = LearningPolicy(557, size='small', contract=contract, research_config=flags)
        expanded = copy.deepcopy(contract)
        expanded['observation']['fields'] += ['no_contact.streak', 'no_contact.threshold']
        expanded['observation']['scales'] += [5., 5.]
        expanded['observation']['dimension'] = 559
        expanded['termination']['no_contact_experiment'] = termination_spec(5)
        expanded['termination']['additional_failure_reasons'] += ['no_contact']
        cls = policy_class(LearningPolicy, 5)
        policy = cls(559, size='small', contract=expanded, research_config=flags)
        inputs = (torch.zeros(2, 559), torch.zeros(2, 3, 24), torch.ones(2, 3, dtype=torch.bool),
            torch.zeros(2, 8, 24), torch.ones(2, 8, dtype=torch.bool))
        with torch.no_grad():
            output = policy(*inputs)
        self.assertTrue(all(torch.isfinite(value).all() for value in output.values()))
        self.assertEqual(policy.finger_encoder.state[0].in_features, 559)
        self.assertEqual(policy.value_encoder.state[0].in_features, 559)
        self.assertEqual(policy.architecture['state_dim'], 559)
        self.assertEqual(policy.architecture['contract'], expanded)
        self.assertEqual(policy.architecture['support_fields'][-2:], ['no_contact.streak', 'no_contact.threshold'])
        trainer = LearningTrainer(policy, research_config=flags)
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory)/'policy.pt'
            trainer.save(checkpoint)
            restored = cls(559, size='small', contract=expanded, research_config=flags)
            LearningTrainer(restored, research_config=flags).load(checkpoint)
            with torch.no_grad():
                actual = restored(*inputs)
            for key in output:
                self.assertTrue(torch.equal(output[key], actual[key]))
            wrong_threshold = copy.deepcopy(expanded)
            wrong_threshold['termination']['no_contact_experiment'] = termination_spec(3)
            mismatch = policy_class(LearningPolicy, 3)(559, size='small',
                contract=wrong_threshold, research_config=flags)
            with self.assertRaisesRegex(ValueError, 'own schema/architecture'):
                LearningTrainer(mismatch, research_config=flags).load(checkpoint)
        for field in ('source', 'base_fields', 'action', 'dimension'):
            invalid = copy.deepcopy(expanded)
            if field == 'source':
                invalid['termination']['no_contact_experiment']['module_sha256'] = '0'*64
            elif field == 'base_fields':
                invalid['observation']['fields'][-3] = 'incorrect_original_wrist_field'
            elif field == 'action':
                invalid['action']['names'].reverse()
            else:
                invalid['observation']['dimension'] = 557
            with self.assertRaises(ValueError):
                cls(559, size='small', contract=invalid, research_config=flags)


if __name__ == '__main__':
    unittest.main()
