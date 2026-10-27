"""CPU integration with recorded bodies/synthetic evidence, not native dynamics."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning import training_environment, actionable_preparation_environment
from guitar_learning.music_task import ScoreTask, ScoreTarget
from guitar_learning.task_measurement import TaskMeasurement
from guitar_learning.task_measurement_v2 import TaskMeasurementV2
from guitar_learning.musical_quality import QualityLedger, QualityConfig, HISTORY_FIELDS
from guitar_learning.musical_quality_environment import build_environment, MusicalQualityEnvironment
from guitar_learning.strike_quality import StrikeQualityDetector
from guitar_learning.tests.test_skill_environment import LongRecordedSession


def fretting(status='missing', *, contact=None):
    clean = status == 'correct'
    if contact is None: contact = status != 'missing'
    return dict(positive_target_candidate=clean, clean_target_candidate=clean,
        status=status, wrong_assignment=False, higher_fret=status == 'wrong',
        incidental_other_string=False, uncertain=False,
        target_string_contact_evidence_ids=['contact'] if contact else [])


def strike(**kwargs):
    return dict(ready=False, ready_dwell_s=0., accepted_crossing_ids=[],
        unprepared_count=0, extra_count=0, recovered=False, recovery_dwell_s=0., **kwargs)


def measured(tick, status='missing', *, contact=None, quality=None):
    return dict(physics_step=tick, task_time_s=tick/240.,
        targets={'t':dict(fretting_quality=fretting(status, contact=contact))},
        strike_quality=strike() if quality is None else quality)


class QualityLedgerTests(unittest.TestCase):
    def task(self, onset=2/240., end=8/240.):
        return ScoreTask((ScoreTarget('t','e',1,5,1,1,onset,end,0.,onset,end),))

    def test_clipped_occupancy_clean_intervals_dropout_and_other_hand_zero(self):
        task = self.task(onset=2.5/240.,end=8.5/240.)
        left = QualityLedger(task, measured(0,'wrong'), 'left', .4)
        right = QualityLedger(task, measured(0,'wrong'), 'right', .4)
        for tick,status in ((1,'wrong'),(2,'correct'),(3,'correct'),(4,'missing')):
            row=measured(tick,status)
            terms=left.update(row); other=right.update(row)
            self.assertTrue(all(other[name] == 0. for name in (
                'quality_wrong_press','quality_missing_press','quality_dropout','quality_late_release','quality_release')))
        # Wrong occupancy: full0..1 plus half1..2. Audible clean starts midway2..3.
        self.assertAlmostEqual(left.wrong_press_s,1.5/240.)
        self.assertAlmostEqual(left.clean_audible_s,.5/240.)
        self.assertAlmostEqual(left.missing_press_s,.5/240.)
        self.assertEqual(left.dropouts,1)
        self.assertEqual(terms['quality_dropout'],-.1)
        self.assertAlmostEqual(terms['quality_missing_press'],-.5*.5/240.)
        with self.assertRaisesRegex(ValueError,'consecutive'): left.update(measured(4))

    def test_release_requires_clear_target_string_and_bonus_is_one_shot(self):
        task=self.task();cfg=QualityConfig(release_dwell_s=2/240.,release_grace_s=1/240.)
        ledger=QualityLedger(task,measured(0,'correct'),'left',.4,cfg)
        for tick in range(1,9):ledger.update(measured(tick,'correct'))
        # Missing assigned finger with a lower-fret target-string contact is not release.
        for tick in (9,10):ledger.update(measured(tick,'missing',contact=True))
        self.assertFalse(ledger.release_complete)
        self.assertGreater(ledger.release_late_s,0.)
        self.assertEqual(ledger.update(measured(11))['quality_release'],0.)
        self.assertEqual(ledger.update(measured(12))['quality_release'],0.)
        self.assertEqual(ledger.update(measured(13))['quality_release'],.25)
        self.assertTrue(ledger.release_complete)
        ledger.update(measured(14,'missing',contact=True))
        self.assertFalse(ledger.release_complete)
        for tick in (15,16,17):self.assertEqual(ledger.update(measured(tick))['quality_release'],0.)
        self.assertTrue(ledger.release_complete)

    def test_strike_penalties_delta_recovery_one_shot_and_final_current_gate(self):
        task=self.task();ledger=QualityLedger(task,measured(0),'right',.4)
        q=strike();q.update(ready=True,accepted_crossing_ids=['s'],recovered=True,recovery_dwell_s=1/240.)
        terms=ledger.update(measured(1,quality=q))
        self.assertEqual(terms['quality_recovery'],.1)
        q.update(unprepared_count=1,extra_count=1)
        terms=ledger.update(measured(2,quality=copy.deepcopy(q)))
        self.assertEqual(terms['quality_unprepared'],-.1)
        self.assertEqual(terms['quality_extra_strike'],-.1)
        self.assertEqual(terms['quality_recovery'],0.)
        self.assertTrue(all(v==0. for v in ledger.update(measured(3,quality=copy.deepcopy(q))).values()))
        q.update(recovered=False,recovery_dwell_s=0.)
        ledger.update(measured(4,quality=copy.deepcopy(q)))
        timing=dict(stage_success=True,provisional_success=True,wrong_crossings=0)
        self.assertFalse(ledger.summary(timing)['stage_success'])
        q.update(recovered=True,recovery_dwell_s=1/240.)
        self.assertEqual(ledger.update(measured(5,quality=q))['quality_recovery'],0.)
        history=dict(zip(HISTORY_FIELDS,ledger.history()))
        self.assertEqual(history['unprepared_count'],1.)
        self.assertEqual(history['extra_count'],1.)
        self.assertEqual(history['recovery_awarded'],1.)


class MusicalQualityEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.environments=[]

    def tearDown(self):
        for env in self.environments:env.close()
        self.folder.cleanup()

    def environment(self,role='left',**kwargs):
        sessions=[]
        def factory(config,out):
            session=LongRecordedSession(config,out);sessions.append(session);return session
        def contacts(scene):return copy.deepcopy(sessions[-1].row()['native_contacts']['contacts'])
        binding=training_environment.ContactEnvironment
        original=actionable_preparation_environment.ActionablePreparationEnvironment
        env=build_environment({},Path(self.folder.name)/str(len(self.environments)),role=role,
            bundle='data/song_bundles/05_BN2-131-B_solo',session_factory=factory,contact_reader=contacts,**kwargs)
        self.assertIs(training_environment.ContactEnvironment,binding)
        self.assertIs(actionable_preparation_environment.ActionablePreparationEnvironment,original)
        self.environments.append(env)
        return env

    @staticmethod
    def synthetic_contacts(measurement,sample):
        # Keep actual recorded contact queries; inject clearly labelled quality
        # evidence to exercise downstream ledger/reward/observation integration.
        evidence,_=TaskMeasurement._contacts(measurement,sample)
        measurement.fretting_quality={t.target_id:fretting('wrong') for t in measurement.task.targets}
        return evidence,set()

    @staticmethod
    def synthetic_strike(detector):
        q=strike();step=detector.last_step or 0
        q.update(ready=step>=1,ready_dwell_s=1/240. if step>=1 else 0.,
            accepted_crossing_ids=['synthetic'] if step>=2 else [],
            unprepared_count=int(step>=2),extra_count=int(step>=3),
            recovered=step>=3,recovery_dwell_s=1/240. if step>=3 else 0.)
        return q

    def test_actual_measurement_binding_shape_native_zero_and_first_action_samples(self):
        env=self.environment(time_limit_s=1/60.)
        binding=training_environment.TaskMeasurement
        observation,reset=env.reset()
        self.assertIs(training_environment.TaskMeasurement,binding)
        self.assertIsInstance(env.measurement,TaskMeasurementV2)
        self.assertIsInstance(env.measurement.detector,StrikeQualityDetector)
        self.assertEqual(observation['state'].shape,(536+len(HISTORY_FIELDS),))
        self.assertEqual(reset['training_contract']['observation']['dimension'],len(observation['state']))
        self.assertEqual(reset['preparation_seconds'],0.)
        self.assertEqual(env.control.session.scene.steps,0)
        self.assertEqual(env.task.duration_s,7.)
        self.assertEqual(reset['training_contract']['action']['dimension'],39)
        self.assertEqual(len(env.control.session.scene.names),105)
        _,reward,terminated,truncated,info=env.step(np.r_[np.full(33,.1),np.zeros(6)])
        self.assertFalse(terminated);self.assertTrue(truncated)
        self.assertEqual([r['physics_step'] for r in info['physics_measurements']],[1,2,3,4])
        self.assertEqual(env.control.session.preparation_calls,0)
        self.assertEqual(env.control.session.policy_calls,1)
        self.assertTrue(all('fretting_quality' in r['music'] and 'strike_quality' in r['music'] for r in info['physics_measurements']))
        self.assertAlmostEqual(reward,sum(info['reward_terms'].values()))
        self.assertAlmostEqual(info['episode']['reward'],reward)
        self.assertEqual(info['episode']['musical_quality'],info['musical_quality'])

    def test_last_substep_history_penalties_and_fresh_persistent_reset(self):
        env=self.environment()
        with patch.object(TaskMeasurementV2,'_contacts',self.synthetic_contacts),patch.object(StrikeQualityDetector,'summary',self.synthetic_strike):
            first,_=env.reset();session=env.control.session
            observation,reward,_,_,info=env.step(np.zeros(39))
            self.assertAlmostEqual(info['reward_terms']['quality_wrong_press'],-1/60.)
            self.assertEqual(info['reward_terms']['quality_unprepared'],0.)  # LH other-hand reward zero
            self.assertEqual(info['reward_terms']['quality_extra_strike'],0.)
            fields=env.contract['observation']['fields']
            self.assertEqual(observation['state'][fields.index('quality_history.higher_fret')],1.)
            self.assertAlmostEqual(observation['state'][fields.index('quality_history.wrong_press_s')],1/60./7.,places=8)
            self.assertAlmostEqual(observation['state'][fields.index('quality_history.extra_count')],1/1680.,places=9)
            self.assertEqual(observation['state'][fields.index('quality_history.strike_recovered')],1.)
            self.assertAlmostEqual(reward,sum(info['reward_terms'].values()))
            again,_=env.reset()
            self.assertIs(env.control.session,session)
            self.assertEqual(session.reset_calls,1)
            self.assertEqual(session.scene.steps,0)
            self.assertEqual(env.total_reward,0.)
            self.assertEqual(env.quality_ledger.extra_count,0)
            for key in first:np.testing.assert_array_equal(first[key],again[key])

    def test_transient_failed_tick_suppresses_positive_quality_preserving_actual_cost(self):
        with patch.object(StrikeQualityDetector,'summary',self.synthetic_strike):
            normal=self.environment('right',time_limit_s=1/60.);normal.reset()
            _,_,_,_,baseline=normal.step(np.zeros(39))
            self.assertEqual(baseline['reward_terms']['quality_recovery'],.1)
            unsafe=self.environment('right');unsafe.reset();unsafe.control.session.unsafe_at=1
            _,reward,terminated,_,info=unsafe.step(np.zeros(39))
        self.assertTrue(terminated)
        self.assertTrue(info['failure_reasons'])
        self.assertEqual(info['reward_terms']['quality_recovery'],0.)
        self.assertTrue(all(value<=0. for row in info['physics_measurements'] for value in row['musical_quality_terms'].values()))
        expected=sum(row['stability']['cost'] for row in info['physics_measurements'])+unsafe.safety_config.failure_cost
        self.assertAlmostEqual(info['cost'],expected)
        self.assertAlmostEqual(info['episode']['cost'],expected)
        self.assertAlmostEqual(reward,sum(info['reward_terms'].values()))
        self.assertAlmostEqual(info['episode']['reward'],reward)
        self.assertFalse(info['musical_quality']['stage_success'])

    def test_quality_failure_gates_final_success_consistently_without_hiding_timing_achievement(self):
        env=self.environment()
        env.reset()
        # Seed a timing achievement, then verify missing audible quality/final
        # release cannot inherit success at actual seven-second completion.
        env.timing_ledger.achieved=True
        for _ in range(420):observation,reward,terminated,truncated,info=env.step(np.zeros(39))
        self.assertTrue(terminated);self.assertFalse(truncated)
        self.assertEqual(info['task_time_s'],7.)
        self.assertTrue(info['timing']['timing_only_stage_success'])
        self.assertFalse(info['musical_quality']['stage_success'])
        self.assertFalse(info['timing']['stage_success'])
        self.assertEqual(info['specialist']['timing'],info['timing'])
        self.assertEqual(info['episode']['timing'],info['timing'])
        self.assertEqual(info['episode']['specialist'],info['specialist'])
        self.assertEqual(info['episode']['musical_quality'],info['musical_quality'])


if __name__=='__main__':unittest.main()
