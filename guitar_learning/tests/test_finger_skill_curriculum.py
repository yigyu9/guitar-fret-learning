"""Pure R/F/J accounting, evaluation scope and strict resume tests."""
import copy
import unittest

from guitar_learning.training.finger_skill_curriculum import FingerSkillCurriculum


def episode(phase='R', safe=True, wrist=1., counts=(16, 16, 16, 16), success=.5, steps=100):
    return dict(evaluation=True, valid=True, reason='timeline_complete' if safe else 'terminal_failure',
        steps=steps, song=dict(completed=safe),
        finger_skill_eval=dict(phase=phase, scope='full_song' if phase == 'J' else 'phrase',
                               wrist_inside_fraction=wrist),
        left_curriculum=dict(full_safe=safe, finger_metrics=[
            dict(target_count=count, success_fraction=success if count else 0.) for count in counts]))


class FingerSkillCurriculumTests(unittest.TestCase):
    def test_r_ready_from_safe_wrist_without_thumb_b_or_music_mastery(self):
        coordinator = FingerSkillCurriculum()
        rows = [episode(wrist=.9, success=0) for _ in range(9)]+[episode(safe=False, success=1)]
        result = coordinator.evaluate(rows)
        self.assertTrue(result['ready'])
        self.assertAlmostEqual(result['safe_fraction'], .9)
        self.assertAlmostEqual(result['wrist_inside_fraction'], .81)
        self.assertEqual(coordinator.evaluation_transitions, dict(R=1000, F=0, J=0))
        self.assertEqual(coordinator.next_phase(), 'F')
        self.assertFalse(coordinator.ready)

    def test_r_safety_and_wrist_are_independent_requirements(self):
        for rows in ([episode(wrist=.79) for _ in range(10)],
                     [episode() for _ in range(8)]+[episode(safe=False) for _ in range(2)]):
            coordinator = FingerSkillCurriculum()
            self.assertFalse(coordinator.evaluate(rows)['ready'])
            self.assertIsNone(coordinator.next_phase())

    def test_f_four_fingers_and_failed_tail_remain_in_denominator(self):
        coordinator = FingerSkillCurriculum(phase='F')
        rows = [episode('F', success=.25) for _ in range(9)]+[episode('F', safe=False, success=1)]
        result = coordinator.evaluate(rows)
        self.assertEqual(result['finger_opportunities'], [160]*4)
        self.assertEqual(result['finger_successes'], [36.]*4)
        self.assertEqual(result['finger_success_fractions'], [.225]*4)
        self.assertTrue(result['ready'])
        self.assertEqual(coordinator.next_phase(), 'J')
        self.assertIsNone(coordinator.next_phase())

    def test_f_cannot_advance_from_one_good_finger_or_insufficient_opportunities(self):
        for counts in ((64, 0, 0, 0), (64, 64, 64, 63)):
            coordinator = FingerSkillCurriculum(phase='F')
            self.assertFalse(coordinator.evaluate([episode('F', counts=counts, success=1)])['ready'])
        coordinator = FingerSkillCurriculum(phase='F')
        row = episode('F', counts=(64, 64, 64, 64), success=1)
        row['left_curriculum']['finger_metrics'][2]['success_fraction'] = .19
        self.assertFalse(coordinator.evaluate([row])['ready'])

    def test_partial_training_and_scope_mismatch_rejected_atomically(self):
        mutations = (
            lambda row: row.__setitem__('evaluation', False),
            lambda row: row.__setitem__('reason', 'rollout_cut'),
            lambda row: row['song'].__setitem__('completed', False),
            lambda row: row['finger_skill_eval'].__setitem__('phase', 'F'),
            lambda row: row['finger_skill_eval'].__setitem__('scope', 'full_song'),
            lambda row: row.__setitem__('valid', False),
        )
        for mutate in mutations:
            coordinator = FingerSkillCurriculum()
            before = coordinator.state_dict()
            bad = episode(); mutate(bad)
            with self.assertRaises(ValueError): coordinator.evaluate([episode(), bad])
            self.assertEqual(before, coordinator.state_dict())

    def test_budgets_never_force_advancement_and_commit_invalidates_old_readiness(self):
        coordinator = FingerSkillCurriculum(budgets=dict(R=10, F=20, J=30))
        self.assertTrue(coordinator.commit(12)['stalled'])
        self.assertIsNone(coordinator.next_phase())
        self.assertTrue(coordinator.evaluate([episode()])['ready'])
        self.assertFalse(coordinator.status()['stalled'])
        self.assertFalse(coordinator.commit(1)['ready'])
        self.assertIsNone(coordinator.next_phase())
        self.assertEqual(coordinator.training_transitions['R'], 13)
        for count in (-1, True, 1.5):
            with self.assertRaises(ValueError): coordinator.commit(count)

    def test_exact_resume_history_phase_and_config_rejection(self):
        coordinator = FingerSkillCurriculum(budgets=dict(R=100, F=200, J=300))
        coordinator.commit(13); coordinator.evaluate([episode()]); coordinator.next_phase()
        coordinator.commit(25); coordinator.evaluate([episode('F', counts=(64,)*4, success=.3)])
        restored = FingerSkillCurriculum(budgets=dict(R=100, F=200, J=300))
        restored.load_state_dict(coordinator.state_dict())
        self.assertEqual(restored.state_dict(), coordinator.state_dict())
        self.assertEqual(restored.next_phase(), coordinator.next_phase())
        self.assertEqual(restored.state_dict(), coordinator.state_dict())
        with self.assertRaises(ValueError): FingerSkillCurriculum().load_state_dict(coordinator.state_dict())
        before = restored.state_dict(); bad = copy.deepcopy(before)
        bad['evaluation_transitions']['R'] += 1
        with self.assertRaises(ValueError): restored.load_state_dict(bad)
        self.assertEqual(restored.state_dict(), before)
        bad = copy.deepcopy(before); bad['training_transitions']['F'] = -1
        with self.assertRaises(ValueError): restored.load_state_dict(bad)
        self.assertEqual(restored.state_dict(), before)

    def test_config_validation_and_native_diagnostic_wrist_fallback(self):
        for kwargs in (dict(phase='Q'), dict(budgets={'R': 1}), dict(thresholds={'safe_fraction': 1.1}),
                       dict(thresholds={'finger_opportunities': 0}), dict(thresholds={'unknown': .5})):
            with self.assertRaises(ValueError): FingerSkillCurriculum(**kwargs)
        row = episode(); del row['finger_skill_eval']['wrist_inside_fraction']
        row['left_episode_diagnostics'] = dict(wrist=dict(inside_fraction=.9))
        coordinator = FingerSkillCurriculum()
        self.assertTrue(coordinator.evaluate([row])['ready'])
        state = coordinator.state_dict(); state['config']['budgets']['R'] = 0
        self.assertNotEqual(state, coordinator.state_dict())


if __name__ == '__main__':
    unittest.main()
