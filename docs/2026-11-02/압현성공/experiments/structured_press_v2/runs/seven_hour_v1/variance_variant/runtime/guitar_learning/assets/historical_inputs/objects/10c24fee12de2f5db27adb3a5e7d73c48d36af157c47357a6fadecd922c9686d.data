"""Quality snapshots and effective native-contact eligibility, without physics."""
import copy
import json
from pathlib import Path
import unittest
import numpy as np
from guitar_learning.core.geometry_v1 import geometry_snapshot
from guitar_learning.music_task import ScoreTask,ScoreTarget
from guitar_learning.core.task_measurement import TaskMeasurement
from guitar_learning.core.task_measurement_v2 import TaskMeasurementV2
from guitar_learning.tests import test_task_measurement as old
from guitar_learning.tests.test_fretting_quality import add_contact
from guitar_learning.tests.test_fretting_v1 import fixture


def sample(step,pick_x=.02,*,higher=False,lower_only=False):
    inputs=fixture(step,fret_body=4 if lower_only else 5,y=.15 if lower_only else .12)
    if higher:add_contact(inputs,fret=6,y=.11)
    native,human,guitar,contacts=inputs
    native['human_body_states'][human.index('RH:pick')]['pose']['p']=dict(x=pick_x,y=-.32,z=.008)
    return dict(native=native,geometry=geometry_snapshot(native,human,guitar),native_contacts=contacts),human,guitar


class QualityMeasurementTests(unittest.TestCase):
    def task(self):return old.score(onset=2/240.,end=5/240.)

    def test_higher_contact_preserves_raw_positive_but_blocks_effective_matching(self):
        s,h,g=sample(0,higher=True);before=copy.deepcopy(s)
        measurement=TaskMeasurementV2(self.task(),h,g);legacy=TaskMeasurement(self.task(),h,g)
        first=measurement.reset(s);prior=legacy.reset(s)
        self.assertEqual(s['native'],before['native'])
        self.assertEqual(s['native_contacts'],before['native_contacts'])
        for name in s['geometry']:
            np.testing.assert_equal(s['geometry'][name],before['geometry'][name])
        target=first['targets']['a']
        self.assertTrue(target['positive_target_candidate']);self.assertTrue(target['evidence']['fretting_contact_candidate'])
        self.assertFalse(target['candidate']);self.assertFalse(target['clean_target_candidate'])
        self.assertTrue(prior['targets']['a']['candidate'])
        self.assertEqual(target['evidence'],prior['targets']['a']['evidence'])
        for step,x in ((1,.02),(2,.03)):
            s=sample(step,x,higher=True)[0];result=measurement.update(s);old_result=legacy.update(s)
        self.assertEqual(result['summary']['matched50'],0)
        self.assertEqual(old_result['summary']['matched50'],1)
        self.assertEqual(result['strike_quality']['accepted_crossing_ids'],['2:1'])
        self.assertTrue(result['fretting_quality']['a']['higher_fret'])
        self.assertEqual(result['schema'],'guitar_learning.task_measurement.v2')
        json.dumps(result,allow_nan=False)

    def test_clean_contact_both_endpoint_hold_and_separate_actual_string_clear(self):
        s,h,g=sample(0,higher=True);measurement=TaskMeasurementV2(self.task(),h,g);measurement.reset(s)
        r=measurement.update(sample(1)[0])
        self.assertTrue(r['targets']['a']['candidate']);self.assertEqual(r['delta']['held_delta_s'],0.)
        r=measurement.update(sample(2)[0])
        self.assertEqual(r['delta']['held_delta_s'],0.)
        r=measurement.update(sample(3)[0])
        self.assertAlmostEqual(r['delta']['held_delta_s'],1/240.)
        r=measurement.update(sample(4,lower_only=True)[0])
        self.assertFalse(r['targets']['a']['candidate'])
        self.assertTrue(r['fretting_quality']['a']['target_string_contact_evidence_ids'])
        self.assertTrue(r['fretting_quality']['a']['wrong_fret'])
        self.assertTrue(r['targets']['a']['measured_contact_lost'])

    def test_ready_gate_changes_joint_matching_but_retains_native_candidate(self):
        s,h,g=sample(0);m=TaskMeasurementV2(self.task(),h,g);m.reset(s)
        r=m.update(sample(1,.03)[0])
        self.assertEqual(r['summary']['matched50'],0)
        self.assertEqual(r['crossings'],[])
        self.assertTrue(r['crossing_candidates'][0]['valid'])
        self.assertEqual(r['strike_quality']['unprepared_count'],1)
        self.assertEqual(r['strike_quality']['blocked_reasons'],{'1:1':['unprepared_matching_crossing']})

    def test_reset_private_snapshots_and_clock_errors(self):
        s,h,g=sample(0,higher=True);m=TaskMeasurementV2(self.task(),h,g);r=m.reset(s)
        r['fretting_quality']['a']['higher_fret_evidence_ids'].clear()
        self.assertTrue(m.fretting_quality['a']['higher_fret_evidence_ids'])
        self.assertTrue(r['targets']['a']['fretting_quality']['higher_fret_evidence_ids'])
        r=m.reset(sample(10)[0])
        self.assertEqual(r['task_time_s'],0.)
        self.assertTrue(r['fretting_quality']['a']['clean_target_candidate'])
        self.assertFalse(r['strike_quality']['ready'])
        self.assertFalse(r['strike_quality']['blocked_event_ids'])
        for step in (10,12):
            with self.assertRaises(ValueError):m.update(sample(step)[0])
        self.assertTrue(m.fretting_quality['a']['clean_target_candidate'])

    def test_single_fretted_scope_and_same_original_task(self):
        s,h,g=sample(0);task=self.task();before=copy.deepcopy(task)
        TaskMeasurementV2(task,h,g).reset(s)
        self.assertEqual(task,before)
        for unsupported in (old.score(fret=0,finger=0),ScoreTask((task.targets[0],ScoreTarget('b','e2',1,5,1,1,1.,1.2,.8,1.,1.2)))):
            with self.assertRaises(ValueError):TaskMeasurementV2(unsupported,h,g)

    def test_saved_native_boundary_feature_is_not_false_higher_fret_error(self):
        from guitar_learning.quality.fretting_quality import classify_fretting
        from guitar_learning.core.fretting_v1 import FretContract
        root=Path('docs/2026-10-12/stability_adapter_2/results')
        c=json.loads((root/'guitar_learning_pick_fret_audit_v1/correction_v2.json').read_text())['first_record']
        r=json.loads((root/'guitar_learning_actionable_preparation_v1/left_ppo_eval_v1/reset_00.json').read_text())
        names=json.loads((root/'guitar_learning_short_preparation_v1/native_v1/initial_values.json').read_text())
        geometry=geometry_snapshot(r['prepared_reset']['actual_initial_state'],names['human_body_names'],names['guitar_body_names'])
        target=ScoreTarget(**r['training_contract']['task']['targets'][0])
        contract=FretContract(minimum_dwell_s=.05)
        from dataclasses import asdict
        evidence=dict(target=dict(string_number=2,musical_fret=7,finger='ring'),contract=asdict(contract),
            fretting_contact_candidate=True,valid_evidence_ids=[c['evidence']['evidence_id']],contact_evidence=[c['evidence']])
        quality=classify_fretting(geometry,target,evidence,contract)
        self.assertTrue(quality['clean_target_candidate']);self.assertFalse(quality['higher_fret'])
        self.assertEqual(quality['feature_diagnostics'][0]['geometric_cells'],[8])
        self.assertEqual(quality['feature_diagnostics'][0]['assigned_fret'],7)


if __name__=='__main__':unittest.main()
