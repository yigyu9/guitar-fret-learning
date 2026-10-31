"""Phase/contact boundary checks and recorded-session wiring, not native success."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from guitar_learning.tool.experiments.transition.task import make_task
from guitar_learning.tool.experiments.transition.environment import build_environment as old_environment
from guitar_learning.tool.experiments.transition_refinement.environment import build_environment
from guitar_learning.tool.experiments.transition_refinement.reward import RewardLedger, metadata, TERMS
from guitar_learning.tests.test_transition_task import BUNDLE, config
from guitar_learning.tests.test_skill_environment import LongRecordedSession
from guitar_learning.tests.test_fretting_v1 import fixture
from guitar_learning.tests.test_fretting_quality import add_contact, quality


def sample(task, step, behavior=None, distance=.03):
    now = step/240.
    targets = {}
    for index, target in enumerate(task.targets):
        clean, positive = (False, False) if behavior is None else behavior(index, target, now)
        ids = [target.target_id+':contact'] if positive else []
        targets[target.target_id] = dict(candidate=clean, fretting_quality=dict(
            clean_target_candidate=clean, positive_target_candidate=positive,
            positive_evidence_ids=ids, status='correct' if clean else 'missing',
            higher_fret_evidence_ids=[], wrong_fret_evidence_ids=[],
            wrong_assignment=False, wrong_finger=False,
            wrong_finger_evidence_ids=[], wrong_assignment_evidence_ids=[]))
    return dict(task_time_s=now, physics_step=step, targets=targets,
        geometry={t.target_id:dict(delta=[distance, 0., 0.]) for t in task.targets})


class RefinementRewardTests(unittest.TestCase):
    def run_ledger(self, mode, behavior):
        task = make_task(BUNDLE, config(mode))
        ledger = RewardLedger(task, sample(task, 0, behavior), config(mode))
        terms = []
        for step in range(1, round(task.duration_s*240)+1):
            terms.append(ledger.update(sample(task, step, behavior)))
        return task, ledger, terms

    def test_press_zero_preparation_is_signed_progress_not_geometry_success(self):
        task = make_task(BUNDLE, config('single_a'))
        ledger = RewardLedger(task, sample(task, 0, distance=.03), config('single_a'))
        closer = ledger.update(sample(task, 1, distance=0.))
        farther = ledger.update(sample(task, 2, distance=.03))
        self.assertGreater(closer['refinement_prepare_progress'], 0.)
        self.assertLess(farther['refinement_prepare_progress'], 0.)
        self.assertAlmostEqual(closer['refinement_prepare_progress']+farther['refinement_prepare_progress'], 0.)
        self.assertEqual(closer['refinement_prepare_ready'], 0.)
        self.assertEqual(closer['refinement_hold_success'], 0.)
        self.assertFalse(ledger.summary()['native_success'])
        # Progress is active until onset, then vanishes even if geometry moves.
        for step in range(3, 481):
            ledger.update(sample(task, step, distance=.03 if step < 480 else 0.))
        after_onset = ledger.update(sample(task, 481, distance=.03))
        self.assertEqual(after_onset['refinement_prepare_progress'], 0.)

    def test_ready_reward_final_point_two_seconds_requires_both_native_endpoints(self):
        behavior = lambda i,t,now: (now != 1.9, now != 1.9)
        task = make_task(BUNDLE, config('single_a'))
        ledger = RewardLedger(task, sample(task, 0, behavior), config('single_a'))
        reward = 0.
        for step in range(1, 481):
            terms = ledger.update(sample(task, step, behavior))
            if step <= 432:
                self.assertEqual(terms['refinement_prepare_ready'], 0.)
            reward += terms['refinement_prepare_ready']
        # One missing native endpoint excludes both adjacent intervals.
        self.assertAlmostEqual(reward, .2-2/240.)
        self.assertAlmostEqual(ledger.summary()['per_target'][task.targets[0].target_id]['prepare_ready_s'], reward)

    def test_forty_percent_does_not_earn_ninety_percent_single_bonus(self):
        behavior = lambda i,t,now: (now <= t.onset_s+.2, now <= t.onset_s+.2)
        _, ledger, terms = self.run_ledger('single_a', behavior)
        self.assertAlmostEqual(next(iter(ledger.summary()['native']['per_target'].values()))['clean_hold_fraction'], .4)
        self.assertEqual(sum(row['refinement_hold_success'] for row in terms), 0.)
        self.assertEqual(sum(row['refinement_hold_missed'] for row in terms), -.5)
        self.assertFalse(ledger.summary(True)['native_success'])

    def test_ninety_percent_bonus_exactly_once_and_release_bonus_at_window_end(self):
        behavior = lambda i,t,now: (now <= t.onset_s+.45, now <= t.onset_s+.45)
        task, ledger, terms = self.run_ledger('single_a', behavior)
        self.assertEqual(sum(row['refinement_hold_success'] for row in terms), 1.)
        self.assertEqual(terms[round(2.45*240)-1]['refinement_hold_success'], 1.)
        self.assertEqual(sum(row['refinement_hold_missed'] for row in terms), 0.)
        self.assertEqual(sum(row['refinement_release_success'] for row in terms), .5)
        release_end = task.provenance['transition']['release_windows'][task.targets[0].target_id][1]
        self.assertEqual(terms[round(release_end*240)-1]['refinement_release_success'], .5)
        self.assertTrue(ledger.summary(True)['native_success'])

    def test_clean_loss_is_not_release_while_qualified_contact_remains(self):
        behavior = lambda i,t,now: (now < t.end_s, True)
        _, ledger, terms = self.run_ledger('single_a', behavior)
        self.assertEqual(sum(row['refinement_release_absent'] for row in terms), 0.)
        self.assertEqual(sum(row['refinement_release_success'] for row in terms), 0.)
        self.assertFalse(ledger.summary(True)['native_success'])

    def test_lower_preparation_uses_positive_with_clean_higher_but_keeps_wrong_veto(self):
        task = make_task(BUNDLE, config('overlap'))
        inputs = add_contact(fixture(finger='ring3', string=2, fret_body=7, y=.09),
            finger='index2', string=2, fret=5, y=.13)
        qualities = [quality(copy.deepcopy(inputs), t)[0] for t in task.targets]
        self.assertTrue(qualities[0]['clean_target_candidate'])
        self.assertTrue(qualities[1]['positive_target_candidate'])
        self.assertFalse(qualities[1]['clean_target_candidate'])
        def actual(step):
            row = sample(task, step)
            for target, q in zip(task.targets, qualities):
                row['targets'][target.target_id] = dict(candidate=q['clean_target_candidate'], fretting_quality=copy.deepcopy(q))
            return row
        ledger = RewardLedger(task, sample(task, 0), config('overlap'))
        for step in range(1, 674):
            ledger.update(actual(step))
        ready = ledger.update(actual(674))
        self.assertGreater(ready['refinement_prepare_ready'], 0.)
        wrong = actual(675)
        wrong['targets'][task.targets[1].target_id]['fretting_quality']['wrong_fret_evidence_ids'].append('unrelated-wrong')
        self.assertEqual(ledger.update(wrong)['refinement_prepare_ready'], 0.)
        self.assertEqual(ledger.update(actual(676))['refinement_prepare_ready'], 0.)
        missing_higher = actual(677)
        qa = missing_higher['targets'][task.targets[0].target_id]
        qa['candidate'] = qa['fretting_quality']['clean_target_candidate'] = False
        self.assertEqual(ledger.update(missing_higher)['refinement_prepare_ready'], 0.)

    def test_audible_wrong_and_missing_are_separate_no_preparation_penalty(self):
        task = make_task(BUNDLE, config('single_a'))
        first = sample(task, 0)
        first['targets'][task.targets[0].target_id]['fretting_quality']['status'] = 'wrong'
        ledger = RewardLedger(task, first, config('single_a'))
        for step in range(1, 481):
            row = sample(task, step)
            row['targets'][task.targets[0].target_id]['fretting_quality']['status'] = 'wrong'
            terms = ledger.update(row)
            self.assertEqual(terms['refinement_wrong_press'], 0.)
        wrong = sample(task, 481)
        wrong['targets'][task.targets[0].target_id]['fretting_quality']['status'] = 'wrong'
        self.assertAlmostEqual(ledger.update(wrong)['refinement_wrong_press'], -1/240.)
        transition = ledger.update(sample(task, 482))
        self.assertAlmostEqual(transition['refinement_wrong_press'], -.5/240.)
        self.assertAlmostEqual(transition['refinement_missing_press'], -.25/240.)

    def test_metadata_is_independent_of_measurement_and_pair_has_original_minimum(self):
        for mode in ('single_a', 'single_b', 'overlap', 'pair'):
            task = make_task(BUNDLE, config(mode))
            ledger = RewardLedger(task, sample(task, 0), config(mode))
            self.assertEqual(metadata(task, config(mode)), ledger.metadata())
            self.assertEqual(ledger.metadata()['hold_fraction'], .4 if mode == 'pair' else .9)
            self.assertEqual(ledger.metadata()['hold_minimum_s'], .05 if mode == 'pair' else None)
        bad = sample(task, 2)
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            ledger.update(bad)


class RefinementEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []

    def tearDown(self):
        for env in self.environments:
            env.close()
        self.folder.cleanup()

    def environment(self, old=False, role='left', **kwargs):
        sessions = []
        def factory(cfg, out):
            value = LongRecordedSession(cfg, out)
            sessions.append(value)
            return value
        env = (old_environment if old else build_environment)({},
            Path(self.folder.name)/str(len(self.environments)), bundle=BUNDLE,
            transition=config('single_a', role=role), session_factory=factory,
            contact_reader=lambda scene:copy.deepcopy(sessions[-1].row()['native_contacts']['contacts']), **kwargs)
        self.environments.append(env)
        return env, sessions

    def test_same_observation_native_contract_plus_explicit_refinement_only(self):
        env, _ = self.environment()
        old, _ = self.environment(old=True)
        obs, info = env.reset()
        old_obs, old_info = old.reset()
        expected = copy.deepcopy(old.contract)
        expected['reward']['refinement'] = metadata(env.task, config('single_a'))
        self.assertEqual(env.contract, expected)
        for name, value in obs.items():
            np.testing.assert_array_equal(value, old_obs[name])
        self.assertEqual(info['transition'], old_info['transition'])
        self.assertEqual(info['refinement']['native'], env.transition_ledger.summary(False))
        self.assertFalse(info['refinement']['successful'])

    def test_new_terms_replace_legacy_and_episode_total_matches(self):
        env, _ = self.environment(time_limit_s=1/60.)
        env.reset()
        original = env.refinement_ledger.update
        def update(row):
            value = original(row)
            value['refinement_prepare_progress'] += 1.
            return value
        with patch.object(env.refinement_ledger, 'update', side_effect=update):
            _, reward, _, truncated, info = env.step(np.zeros(39))
        self.assertTrue(truncated)
        self.assertEqual(set(info['reward_terms']), set(TERMS) | {'action_change', 'terminal_failure'})
        self.assertEqual(sorted(info['reward_terms']), env.contract['reward']['refinement']['active_reward_terms'])
        self.assertNotIn('song_left_success', info['reward_terms'])
        self.assertIn('song_left_success', info['legacy_reward_terms'])
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        self.assertAlmostEqual(reward, info['episode']['reward'])
        self.assertGreater(reward, 3.9)
        self.assertEqual(info['episode']['refinement'], info['refinement'])
        self.assertEqual(env.transition_ledger.summary(), env.refinement_ledger.native.summary())

    def test_unsafe_tick_suppresses_all_new_positive_reward_preserves_cost(self):
        env, sessions = self.environment()
        env.reset()
        sessions[0].unsafe_at = 4
        original = env.refinement_ledger.update
        def update(row):
            value = original(row)
            value['refinement_prepare_ready'] = 100.
            return value
        with patch.object(env.refinement_ledger, 'update', side_effect=update):
            _, reward, terminated, truncated, info = env.step(np.zeros(39))
        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertTrue(all(value <= 0. for value in info['reward_terms'].values()))
        self.assertTrue(all(row['refinement_reward_terms']['refinement_prepare_ready'] == 0.
            for row in info['physics_measurements']))
        expected_cost = sum(row['stability']['cost'] for row in info['physics_measurements'])+env.safety_config.failure_cost
        self.assertAlmostEqual(info['cost'], expected_cost)
        self.assertAlmostEqual(info['episode']['reward'], reward)
        self.assertTrue(info['refinement']['safety_invalidated'])
        self.assertFalse(info['refinement']['successful'])
        with self.assertRaisesRegex(RuntimeError, 'reset required'):
            env.step(np.zeros(39))
        self.assertEqual(sessions[0].scene.steps, 4)

    def test_joint_keeps_right_reward_terms_and_measurement_error_ends_episode(self):
        env, sessions = self.environment(role='joint')
        env.reset()
        _, reward, _, _, info = env.step(np.zeros(39))
        self.assertIn('song_right_progress', info['reward_terms'])
        self.assertNotIn('song_left_success', info['reward_terms'])
        self.assertEqual(sorted(info['reward_terms']), env.contract['reward']['refinement']['active_reward_terms'])
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        with patch.object(env.refinement_ledger, 'update', side_effect=ValueError('bad refinement')):
            with self.assertRaisesRegex(ValueError, 'bad refinement'):
                env.step(np.zeros(39))
        with self.assertRaisesRegex(RuntimeError, 'reset required'):
            env.step(np.zeros(39))
        self.assertEqual(sessions[0].scene.steps, 8)


if __name__ == '__main__':
    unittest.main()
