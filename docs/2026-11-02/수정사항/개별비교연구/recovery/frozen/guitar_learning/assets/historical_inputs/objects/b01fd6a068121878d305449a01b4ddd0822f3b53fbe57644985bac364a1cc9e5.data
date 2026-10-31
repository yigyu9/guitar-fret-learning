"""Regression checks for exploitable legacy rewards and blocked rearm passages."""
import copy
import unittest
from unittest.mock import patch
import numpy as np
from guitar_learning.musical_quality import QualityLedger
from guitar_learning.task_measurement import TaskMeasurement
from guitar_learning.task_measurement_v2 import TaskMeasurementV2
from guitar_learning.timing_curriculum import TimingConfig
from guitar_learning.tests import test_musical_quality_environment as fixtures
from guitar_learning.tests.test_musical_quality_environment import measured, strike, fretting


class QualityEdgeTests(unittest.TestCase):
    def test_wait_rearm_not_double_charged_and_blocks_success(self):
        task=fixtures.QualityLedgerTests().task()
        ledger=QualityLedger(task,measured(0),'right',.4)
        s=strike();s.update(ready=True,accepted_crossing_ids=['ok'],recovered=True,
            blocked_event_ids=['unprepared','extra','wait'],unprepared_crossing_ids=['unprepared'],
            extra_crossing_ids=['extra'],unprepared_count=1,extra_count=1)
        terms=ledger.update(measured(1,quality=copy.deepcopy(s)))
        self.assertEqual(terms['quality_other_blocked'],-.1)
        self.assertEqual(terms['quality_extra_strike'],-.1)
        self.assertEqual(terms['quality_unprepared'],-.1)
        self.assertEqual(ledger.other_blocked_count,1)
        terms=ledger.update(measured(2,quality=copy.deepcopy(s)))
        self.assertEqual(terms['quality_other_blocked'],0.)
        self.assertFalse(ledger.summary(dict(stage_success=True,provisional_success=True,wrong_crossings=0))['stage_success'])

    def test_post_note_hold_is_not_rewarded_and_only_audible_success_pays(self):
        helper=fixtures.MusicalQualityEnvironmentTests()
        helper.setUp()
        def contacts(measurement,sample):
            evidence,_=TaskMeasurement._contacts(measurement,sample)
            measurement.fretting_quality={t.target_id:fretting('correct') for t in measurement.task.targets}
            return evidence,set(measurement.fretting_quality)
        try:
            env=helper.environment(role='left',timing=TimingConfig(stage_index=1,pre_roll_s=3.))
            totals={}
            with patch.object(TaskMeasurementV2,'_contacts',contacts):
                env.reset()
                for tick in range(420):
                    _,reward,done,_,info=env.step(np.zeros(39))
                    self.assertAlmostEqual(reward,sum(info['reward_terms'].values()))
                    for key,value in info['reward_terms'].items():totals[key]=totals.get(key,0.)+value
                    if info['task_time_s']<env.task.targets[0].onset_s:
                        self.assertEqual(totals.get('quality_audible_success',0.),0.)
            self.assertTrue(done)
            self.assertAlmostEqual(totals['timing_success']+totals['quality_timing_success_correction'],0.)
            self.assertAlmostEqual(totals['quality_audible_success'],1.)
            self.assertAlmostEqual(totals['quality_post_note_hold_correction'],-1.)
            self.assertFalse(info['musical_quality']['release_complete'])
            self.assertFalse(info['timing']['stage_success'])
        finally:helper.tearDown()


if __name__=='__main__':unittest.main()
