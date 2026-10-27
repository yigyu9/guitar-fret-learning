"""CPU contracts; recorded body fixtures do not certify native dynamics."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning import training_environment
from guitar_learning.training_environment import TrainingEnvironment
from guitar_learning.persistent_environment import PersistentContactEnvironment
from guitar_learning.skill_environment import (SkillConfig, SkillScoreTask,
    SkillLedger, SkillTrainingEnvironment, build_skill_environment, skill_pick_guide)
from guitar_learning.music_task import MusicLedger
from guitar_learning.task_measurement import TaskMeasurement
from guitar_learning.tests.test_specialist_environment import task, measurement, crossing, ShiftedRecordedSession


class SkillLedgerTests(unittest.TestCase):
    def ledger(self, role, skill):
        return SkillLedger(task(), measurement(0), role, skill, SkillConfig())

    def test_anytime_contact_and_hold_after_original_deadline_keep_timed_failure(self):
        contact = self.ledger('left', 'contact')
        hold = self.ledger('left', 'hold')
        for tick in range(1,110):
            candidate = tick >= 96
            for ledger in (contact, hold):
                ledger.update(measurement(tick, candidate))
        self.assertTrue(contact.summary(completed=True)['stage_success'])
        self.assertTrue(hold.summary(completed=True)['stage_success'])
        self.assertEqual(hold.summary()['left']['dwell_targets'], [])
        self.assertEqual(hold.summary()['skill']['held_targets'], ['t'])
        self.assertAlmostEqual(hold.longest['t'], 13/240.)
        self.assertEqual(contact.first_success_s, .4)
        hold.invalidate(['guitar_displacement'])
        failed = hold.summary(completed=True)
        self.assertFalse(failed['stage_success'])
        self.assertEqual(failed['skill']['held_targets'], ['t'])

    def test_hold_requires_contiguous_intervals_and_ready_is_only_proxy(self):
        hold = self.ledger('left', 'hold')
        ready = self.ledger('right', 'ready')
        guide = dict(target_id='t', distance_m=.005)
        for tick in range(1,24):
            candidate = tick != 10
            hold.update(measurement(tick, candidate))
            ready.update(measurement(tick), guide if tick != 10 else dict(guide, distance_m=.02))
            if tick == 22:
                self.assertFalse(hold.provisional())
                self.assertFalse(ready.provisional())
        self.assertTrue(hold.provisional())
        self.assertTrue(ready.provisional())
        self.assertEqual(ready.summary()['skill']['contact_targets'], [])
        self.assertEqual(ready.summary()['skill']['crossed_targets'], [])
        self.assertIn('preparation proxy', ready.summary()['success_criterion'])

    def test_anytime_crossing_unique_and_no_left_prerequisite_or_false_timed_match(self):
        ledger = self.ledger('right', 'cross')
        for tick in range(1,98):
            events = [crossing(at=.4)] if tick in (96,97) else []
            ledger.update(measurement(tick, False, events))
        result = ledger.summary(completed=True)
        self.assertTrue(result['stage_success'])
        self.assertEqual(result['right']['matched50'], 0)
        self.assertEqual(result['skill']['contact_targets'], [])
        self.assertEqual(result['skill']['geometric_crossings'], 1)
        self.assertEqual(result['skill']['duplicate_crossings'], 1)
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            ledger.update(measurement(97))

    def test_wrong_direction_cannot_satisfy_crossing_and_timed_remains_timed(self):
        cross = self.ledger('right', 'cross')
        timed = self.ledger('right', 'timed')
        for tick in range(1,97):
            events = [crossing(at=.4, direction=-1)] if tick == 96 else []
            for ledger in (cross, timed): ledger.update(measurement(tick, False, events))
        self.assertFalse(cross.provisional())
        self.assertFalse(timed.provisional())

    def test_horizon_extension_preserves_target_times_and_original_token_fields(self):
        original = task()
        extended = SkillScoreTask(original.targets, provenance=original.provenance)
        original_ledger, ledger = MusicLedger(original), MusicLedger(extended)
        geometry = {'t':dict(delta=[.01, 0., 0.], velocity=[0., 0., 0.])}
        self.assertEqual(original.tokens(.1, geometry, original_ledger), extended.tokens(.1, geometry, ledger))
        tokens, mask, ids = extended.tokens(3., geometry, ledger)
        self.assertTrue(mask[0]); self.assertEqual(ids[0], 't')
        self.assertEqual(tokens[0][7:9], (0., 0.))
        self.assertEqual(extended.targets, original.targets)
        self.assertEqual(extended.duration_s, 4.)
        self.assertEqual(extended.state(3., ledger)[0], 1.)
        for cfg in (dict(horizon_s=.1), dict(horizon_s=4.001), dict(dwell_s=0), dict(success_bonus=-1)):
            with self.assertRaises(ValueError):
                settings = SkillConfig(**cfg)
                SkillScoreTask(original.targets, horizon_s=settings.horizon_s)


class LongRecordedSession(ShiftedRecordedSession):
    def row(self):
        # Explicitly static extension for interface-only tests, not simulation.
        return self.rows[min(max(0, self.scene.steps-480), len(self.rows)-1)]


class SkillEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []

    def tearDown(self):
        for env in self.environments: env.close()
        self.folder.cleanup()

    def environment(self, role='left', skill='reach', ordinary=False, **kwargs):
        sessions = []
        def factory(config, out):
            session = LongRecordedSession(config, out); sessions.append(session)
            return session
        def contacts(scene): return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        if ordinary:
            cls = TrainingEnvironment
            score = SkillScoreTask(task().targets)
        else:
            cls, score = SkillTrainingEnvironment, task()
            kwargs.update(role=role, skill=skill)
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            env = cls({}, Path(self.folder.name)/str(len(self.environments)), task=score,
                session_factory=factory, contact_reader=contacts, **kwargs)
        self.environments.append(env)
        return env

    def test_all_skill_observation_action_termination_and_base_task_contracts_identical(self):
        contracts = []
        for role, skills in (('left', ('reach', 'contact', 'hold', 'timed')),
                            ('right', ('ready', 'cross', 'timed'))):
            for skill in skills:
                env = self.environment(role, skill)
                obs, reset = env.reset()
                contract = copy.deepcopy(reset['training_contract'])
                contract['task'].pop('specialist')
                contracts.append(contract)
                self.assertEqual(obs['state'].shape, (468,))
                for name in ('observation', 'action', 'termination', 'task'):
                    self.assertEqual(contract[name], contracts[0][name])
                self.assertEqual(env.control.session.scene.steps, 480)
                action = np.zeros(39); action[33 if role == 'left' else 0] = .01
                with self.assertRaisesRegex(ValueError, 'inactive'): env.step(action)
                self.assertEqual(env.control.session.scene.steps, 480)

    def test_longer_episode_survives_original_end_and_closes_only_at_four_seconds(self):
        env = self.environment()
        env.reset()
        with patch.object(TaskMeasurement, '_contacts', return_value=({'t': {}}, set())):
            for index in range(240):
                obs, reward, terminated, truncated, info = env.step(np.zeros(39))
                self.assertEqual(terminated, index == 239)
                self.assertFalse(truncated)
        self.assertEqual(info['task_time_s'], 4.)
        self.assertEqual(info['termination_reason'], 'timeline_complete')
        self.assertTrue(obs['mask'][0])
        self.assertEqual(info['music']['matched50'], 0)
        self.assertFalse(info['specialist']['stage_success'])
        self.assertEqual(info['episode']['reward'], env.total_reward)

    def test_failure_cost_and_music_equal_base_no_positive_skill_credit(self):
        env, base = self.environment(), self.environment(ordinary=True)
        env.reset(); base.reset()
        env.control.session.unsafe_at = base.control.session.unsafe_at = 481
        actual, expected = env.step(np.zeros(39)), base.step(np.zeros(39))
        self.assertEqual(actual[2:4], expected[2:4])
        for key in ('cost', 'failure_reasons', 'termination_reason', 'music'):
            self.assertEqual(actual[4][key], expected[4][key])
        self.assertTrue(actual[4]['specialist']['safety_invalidated'])
        self.assertFalse(actual[4]['specialist']['stage_success'])
        self.assertTrue(all(v <= 0 for v in actual[4]['reward_terms'].values()))
        truncated = self.environment(time_limit_s=1/60)
        truncated.reset()
        self.assertFalse(truncated.step(np.zeros(39))[4]['specialist']['stage_success'])

    def test_static_front_and_rear_guides_are_distinct_and_clock_independent(self):
        env = self.environment('right', 'ready'); env.reset()
        front = skill_pick_guide(env.task, env.last_sample, 0., 'ready')
        later = skill_pick_guide(env.task, env.last_sample, 3., 'ready')
        rear = skill_pick_guide(env.task, env.last_sample, 0., 'cross')
        np.testing.assert_allclose(front['goal_G_m'], later['goal_G_m'])
        delta = np.asarray(rear['goal_G_m'])-front['goal_G_m']
        self.assertAlmostEqual(np.linalg.norm(delta), .012)
        self.assertGreater(np.dot(delta[:2], front['normal_G_xy'])*front['direction'], 0.)

    def test_builder_rejects_modes_without_constructing_native_session(self):
        original = training_environment.ContactEnvironment
        for kwargs in (dict(role='joint', skill='hold'), dict(role='left', skill='cross'),
                       dict(role='left', skill='reach', stage='C'),
                       dict(role='left', skill='reach', music={'reward_mode':'dense_v2'})):
            with self.assertRaises(ValueError):
                build_skill_environment({}, self.folder.name,
                    bundle='data/song_bundles/05_BN2-131-B_solo', **kwargs)
        self.assertIs(training_environment.ContactEnvironment, original)


if __name__ == '__main__': unittest.main()
