"""Synthetic musical evidence and recorded bodies, not native skill validation."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning import training_environment
from guitar_learning.music_task import ScoreTask, ScoreTarget
from guitar_learning.persistent_environment import PersistentContactEnvironment
from guitar_learning.specialist_environment import (SpecialistLedger, SpecialistRewardConfig,
    SpecialistTrainingEnvironment, build_specialist_environment)
from guitar_learning.task_measurement import TaskMeasurement
from guitar_learning.training_environment import TrainingEnvironment
from guitar_learning.tests.test_persistent_environment import ReusableRecordedSession

BUNDLE = 'data/song_bundles/05_BN2-131-B_solo'


def task(onset=.1, end=.2, press=0.):
    return ScoreTask((ScoreTarget('t', 'e', 1, 7, 3, 1, onset, end, press, onset, end),),
                     provenance={'source':'synthetic_cpu_specialist_fixture'})


def measurement(tick, candidate=False, crossings=()):
    return dict(physics_step=480+tick, task_time_s=tick/240.,
        targets={'t':dict(candidate=candidate)}, geometry={'t':dict(delta=[.02,0.,0.])},
        crossings=list(crossings))


def crossing(identity='strike', *, at=.1, string=2, direction=1):
    return dict(crossing_id=identity, task_time_s=at, string_number=string, direction=direction)


class SpecialistLedgerTests(unittest.TestCase):
    def test_left_dwell_independent_of_strikes_and_loss_resets_continuity(self):
        ledger = SpecialistLedger(task(), measurement(0))
        for tick in range(1,9): ledger.update(measurement(tick, True))
        self.assertFalse(ledger.summary('left', False)['provisional_success'])
        ledger.update(measurement(9, False))
        self.assertEqual(ledger.left['t']['dwell_s'], 0.)
        for tick in range(10,23): ledger.update(measurement(tick, True))
        summary = ledger.summary('left', False)
        self.assertTrue(summary['provisional_success'])
        self.assertFalse(summary['stage_success'])
        self.assertEqual(summary['left']['acquisitions'], 2)
        self.assertEqual(summary['left']['releases'], 1)
        self.assertAlmostEqual(summary['left']['longest_dwell_s'], .05)
        self.assertEqual(summary['right']['matched50'], 0)
        self.assertTrue(ledger.summary('left', False, completed=True)['stage_success'])
        ledger.invalidate(['guitar_displacement'])
        failed = ledger.summary('left', False, completed=True)
        self.assertFalse(failed['stage_success'])
        self.assertFalse(failed['provisional_success'])
        self.assertEqual(failed['left']['valid_dwell_targets'], [])
        self.assertEqual(failed['left']['dwell_targets'], ['t'])

    def test_no_contact_dwell_outside_declared_window_or_short_candidate(self):
        ledger = SpecialistLedger(task(onset=.05, end=.075, press=.05), measurement(0, True))
        total = 0.
        for tick in range(1,50):
            terms = ledger.update(measurement(tick, True))
            total += terms['left_dwell_success']
        self.assertEqual(total, 0.)
        self.assertLessEqual(ledger.left['t']['valid_s'], .025+1e-12)
        self.assertFalse(ledger.summary('left', False, completed=True)['stage_success'])
        self.assertEqual(ledger.left['t']['dwell_s'], 0.)

    def test_right_unique_string_direction_time_matches_without_left_contact(self):
        ledger = SpecialistLedger(task(), measurement(0))
        rewards = []
        for tick in range(1,25):
            events = [crossing()] if tick == 24 else []
            rewards.append(ledger.update(measurement(tick, False, events)))
        summary = ledger.summary('right', False, completed=True)
        self.assertTrue(summary['stage_success'])
        self.assertEqual(summary['right']['matched50'], 1)
        self.assertEqual(summary['right']['matched100'], 1)
        self.assertEqual(summary['left']['valid_s'], 0.)
        self.assertEqual(sum(x['right_strict_match'] for x in rewards), 1.)
        duplicate = ledger.update(measurement(25, False, [crossing()]))
        self.assertEqual(duplicate['right_strict_match'], 0.)
        self.assertEqual(duplicate['right_wrong_crossing'], 0.)
        extra = ledger.update(measurement(26, False, [crossing('extra', at=26/240.)]))
        self.assertEqual(extra['right_strict_match'], 0.)
        self.assertEqual(ledger.summary('right', False)['right']['matched50'], 1)
        self.assertEqual(ledger.duplicate_crossings, 1)

    def test_wrong_crossings_and_lenient_match_do_not_become_strict_success(self):
        ledger = SpecialistLedger(task(), measurement(0))
        for tick in range(1,45):
            events = {24:[crossing('wrong_string', at=.1, string=3)],
                      25:[crossing('wrong_direction', at=25/240., direction=-1)],
                      42:[crossing('late', at=.175)]}.get(tick, [])
            ledger.update(measurement(tick, False, events))
        summary = ledger.summary('right', False, completed=True)
        self.assertEqual(summary['right']['geometric_crossings'], 3)
        self.assertEqual(summary['right']['wrong_crossings'], 2)
        self.assertEqual(summary['right']['matched50'], 0)
        self.assertEqual(summary['right']['matched100'], 1)
        self.assertFalse(summary['stage_success'])
        with self.assertRaisesRegex(ValueError, 'consecutive'):
            ledger.update(measurement(44))
        with self.assertRaisesRegex(ValueError, 'valid measured'):
            ledger.update(measurement(45, False, [crossing('future', at=1.)]))


class ShiftedRecordedSession(ReusableRecordedSession):
    def native(self):
        native = super().native()
        if self.scene.steps == getattr(self, 'unsafe_at', None):
            for body in native['guitar_body_states']:
                body['pose']['p']['x'] += .1
        return native


class SpecialistEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.environments = []
        self.sessions = []

    def tearDown(self):
        for env in self.environments: env.close()
        self.folder.cleanup()

    def environment(self, role='left', *, ordinary=False, **kwargs):
        sessions = []
        def factory(config, out):
            session = ShiftedRecordedSession(config, out)
            sessions.append(session); self.sessions.append(session)
            return session
        def contacts(scene): return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        cls = TrainingEnvironment if ordinary else SpecialistTrainingEnvironment
        if not ordinary: kwargs['role'] = role
        with patch.object(training_environment, 'ContactEnvironment', PersistentContactEnvironment):
            env = cls({}, Path(self.folder.name)/str(len(self.environments)),
                task=kwargs.pop('task', task()), session_factory=factory, contact_reader=contacts, **kwargs)
        self.environments.append(env)
        return env

    @staticmethod
    def candidates(measurement, sample):
        return ({t.target_id: dict(fretting_contact_candidate=True) for t in measurement.task.targets},
                {t.target_id for t in measurement.task.targets})

    def test_inactive_actions_rejected_before_physics_and_frozen_partner_allowed(self):
        for role, inactive in (('left', 33), ('right', 0)):
            env = self.environment(role)
            env.reset(); action = np.zeros(39); action[inactive] = .1
            session = env.control.session
            with self.assertRaisesRegex(ValueError, 'inactive'): env.step(action)
            self.assertEqual(session.scene.steps, 480)
            self.assertEqual(session.policy_calls, 0)
            allowed = self.environment(role, frozen_partner=True)
            allowed.reset(); allowed.step(action)
            self.assertEqual(allowed.control.session.scene.steps, 484)
        for invalid in (np.zeros(38), np.full(39, np.nan), np.full(39, 1.01)):
            with self.assertRaises(ValueError): env.step(invalid)

    def test_left_native_candidate_dwell_without_right_match_and_reset_clears(self):
        env = self.environment('left')
        with patch.object(TaskMeasurement, '_contacts', self.candidates):
            first, reset = env.reset()
            for _ in range(19):
                _, reward, terminated, truncated, info = env.step(np.zeros(39))
            self.assertTrue(terminated)
            self.assertFalse(truncated)
            self.assertTrue(info['specialist']['stage_success'])
            self.assertEqual(info['music']['matched50'], 0)
            self.assertNotIn('missed_strict', info['reward_terms'])
            self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
            self.assertEqual(info['episode']['specialist'], info['specialist'])
            session = env.control.session
            observation, reset2 = env.reset()
        self.assertIs(env.control.session, session)
        self.assertEqual(reset2['specialist']['left']['valid_s'], 0.)
        self.assertFalse(reset2['specialist']['provisional_success'])
        self.assertEqual(reset2['specialist']['right']['matched50'], 0)
        self.assertEqual(reset2['training_contract'], reset['training_contract'])
        for key in first: np.testing.assert_array_equal(first[key], observation[key])

    def test_right_measured_geometry_matching_without_left_contact(self):
        env = self.environment('right', task=task(onset=.0125))
        env.reset()
        self.assertFalse(env.last_measured['targets']['t']['candidate'])
        detector = env.measurement.detector
        def detect(previous, current):
            events = [dict(crossing_id='483:2', string_number=2, direction=1,
                           physics_step_fraction=483.)] if current['physics_step'] == 483 else []
            return dict(events=events, candidates=[])
        with patch.object(detector, 'update', side_effect=detect):
            _, reward, _, _, info = env.step(np.zeros(39))
        self.assertEqual(info['music']['matched50'], 0)
        self.assertEqual(info['specialist']['right']['matched50'], 1)
        self.assertEqual(info['specialist']['left']['valid_s'], 0.)
        self.assertTrue(info['specialist']['provisional_success'])
        self.assertFalse(info['specialist']['stage_success'])
        self.assertEqual(info['reward_terms']['right_strict_match'], 1.)
        self.assertAlmostEqual(reward, sum(info['reward_terms'].values()))
        self.assertEqual(info['pick_guide']['physics_step'], 484)
        self.assertTrue(np.isfinite(info['pick_guide']['distance_m']))

    def test_safety_failure_invalidates_success_and_preserves_base_cost_termination(self):
        specialist = self.environment('left')
        baseline = self.environment(ordinary=True)
        with patch.object(TaskMeasurement, '_contacts', self.candidates):
            specialist.reset(); baseline.reset()
            specialist.control.session.unsafe_at = baseline.control.session.unsafe_at = 493
            for _ in range(3):
                specialist.step(np.zeros(39)); baseline.step(np.zeros(39))
            self.assertTrue(specialist.specialist_ledger.summary('left', False)['provisional_success'])
            stage = specialist.step(np.zeros(39))
            base = baseline.step(np.zeros(39))
        self.assertEqual(stage[2:4], base[2:4])
        for name in ('cost', 'termination_reason', 'failure_reasons', 'music'):
            self.assertEqual(stage[4][name], base[4][name])
        self.assertEqual(stage[4]['termination_reason'], 'terminal_failure')
        self.assertFalse(stage[4]['specialist']['provisional_success'])
        self.assertFalse(stage[4]['specialist']['stage_success'])
        self.assertTrue(stage[4]['specialist']['safety_invalidated'])
        self.assertEqual(stage[4]['reward_terms']['terminal_failure'], -2.)
        self.assertEqual(stage[4]['specialist']['left']['valid_dwell_targets'], [])
        self.assertTrue(all(value <= 0 for key, value in stage[4]['reward_terms'].items() if key.startswith('left_')))
        self.assertEqual(stage[4]['episode']['reward'], specialist.total_reward)

    def test_joint_retains_base_reward_music_observation_action_and_termination_contract(self):
        baseline = self.environment(ordinary=True, time_limit_s=2/60)
        contracts = []
        for role in ('left', 'right', 'joint'):
            env = self.environment(role, time_limit_s=2/60)
            obs, reset = env.reset()
            contracts.append(copy.deepcopy(env.contract))
            for key in ('observation', 'action', 'termination'):
                self.assertEqual(contracts[-1][key], contracts[0][key])
            self.assertEqual(obs['state'].shape, (468,))
            if role == 'joint':
                base_obs, base_reset = baseline.reset()
                for key in ('observation', 'action', 'termination'):
                    self.assertEqual(reset['training_contract'][key], base_reset['training_contract'][key])
                for _ in range(2):
                    actual = env.step(np.zeros(39)); expected = baseline.step(np.zeros(39))
                    self.assertEqual(actual[1:4], expected[1:4])
                    for name in ('cost','music','reward_terms','termination_reason'):
                        self.assertEqual(actual[4][name], expected[4][name])
                    for key in actual[0]: np.testing.assert_array_equal(actual[0][key], expected[0][key])

    def test_builder_rejects_unsupported_modes_and_restores_construction_binding(self):
        original = training_environment.ContactEnvironment
        common = dict(bundle=BUNDLE, start_event_index=0)
        for config in (dict(stage='C'), dict(music={'reward_mode':'dense_v2'}),
                       dict(music={'goal_event_indices':[0]}), dict(music={'typo':True})):
            with self.assertRaises(ValueError):
                build_specialist_environment({}, self.folder.name, **common, **config)
        with self.assertRaises(ValueError):
            build_specialist_environment({}, self.folder.name, role='invalid', **common)
        self.assertIs(training_environment.ContactEnvironment, original)
        self.assertEqual(self.sessions, [])
        for config in (dict(minimum_dwell_s=0), dict(left_missed=1), dict(left_hold_second=-1)):
            with self.assertRaises(ValueError): SpecialistRewardConfig(**config)


if __name__ == '__main__': unittest.main()
