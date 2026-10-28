import copy
import json
import unittest
import numpy as np
from .test_fretting_v1 import fixture
from guitar_learning.core.geometry import geometry_snapshot
from guitar_learning.song.task import ScoreTarget, ScoreTask
from guitar_learning.core.measurement import TaskMeasurement


def score(*,fret=5,finger=1,onset=1/240,end=3/240):
    return ScoreTask((ScoreTarget('a','e',0,fret,finger,1,onset,end,0.,onset,end),))


def sample(step,*,pick_x=.02,**kwargs):
    native,human,guitar,contacts=fixture(step,**kwargs)
    body=native['human_body_states'][human.index('RH:pick')]
    body['pose']['p']=dict(x=pick_x,y=-.32,z=.008)
    return dict(native=native,geometry=geometry_snapshot(native,human,guitar),native_contacts=contacts),human,guitar


class TaskTests(unittest.TestCase):
    def test_real_contact_matching_hold_release_and_state(self):
        s,h,g=sample(0); m=TaskMeasurement(score(),h,g)
        first=m.reset(s)
        self.assertEqual(len(first['detector_state']),18)
        s,_,_=sample(1,pick_x=.03)
        r=m.update(s)
        self.assertEqual(r['delta']['new_strict_matches'],1)
        self.assertEqual(r['delta']['new_lenient_only_matches'],0)
        self.assertAlmostEqual(r['summary']['held_total_s'],0.)
        for step in (2,3): r=m.update(sample(step,pick_x=.03)[0])
        self.assertAlmostEqual(r['summary']['hold_fractions']['a'],1.)
        r=m.update(sample(4,pick_x=.03,raw_lambda=0)[0])
        self.assertEqual(r['delta']['timely_releases'],1)
        self.assertEqual(r['contact_lost_target_ids'],['a'])
        json.dumps(r,allow_nan=False)
        self.assertEqual(m.update(sample(5,pick_x=.03,raw_lambda=0)[0])['delta']['timely_releases'],0)

    def test_wrong_finger_no_match_and_both_endpoint_requirement(self):
        for kwargs in ({'finger':'middle2'},{'string':2},{'fret_body':6},{'raw_lambda':0}):
            s,h,g=sample(0,**kwargs); m=TaskMeasurement(score(),h,g);m.reset(s)
            r=m.update(sample(1,pick_x=.03)[0])
            self.assertEqual(r['delta']['new_strict_matches'],0)
            self.assertEqual(r['delta']['wrong_crossings'],1)
            self.assertEqual(r['delta']['held_delta_s'],0)

    def test_open_obstruction_and_clear(self):
        for finger in ('index2','middle2','thumb3'):
            s,h,g=sample(0,finger=finger); m=TaskMeasurement(score(fret=0,finger=0),h,g)
            r=m.reset(s)
            self.assertFalse(r['targets']['a']['candidate'])
        s,h,g=sample(0,raw_lambda=0); m=TaskMeasurement(score(fret=0,finger=0),h,g)
        m.reset(s)
        r=m.update(sample(1,pick_x=.03,raw_lambda=0)[0])
        self.assertEqual(r['delta']['new_strict_matches'],1)

    def test_no_early_false_final_release_and_miss_once(self):
        s,h,g=sample(0);m=TaskMeasurement(score(onset=.1,end=.2),h,g);m.reset(s)
        r=m.update(sample(1,raw_lambda=0)[0])
        self.assertEqual(r['delta']['timely_releases'],0)
        total=0
        for step in range(2,53):
            r=m.update(sample(step,raw_lambda=0)[0]);total+=r['delta']['new_missed_strict']
        self.assertEqual(total,1)
        self.assertFalse(r['targets']['a']['final_release_measured'])

    def test_legato_no_mandatory_loss(self):
        a=score().targets[0]
        b=ScoreTarget('b','e2',0,5,1,1,a.end_s,a.end_s+.1,a.end_s,a.end_s,a.end_s+.1)
        s,h,g=sample(0);m=TaskMeasurement(ScoreTask((a,b)),h,g)
        r=m.reset(s)
        self.assertFalse(r['targets']['a']['release_required'])

    def test_recorded_native_samples_no_simulation(self):
        import gzip
        from pathlib import Path
        root=Path('docs/2026-10-12/stability_adapter_2/results/guitar_learning_short_preparation_v1/native_v1')
        with (root/'initial_values.json').open() as f: initial=json.load(f)
        with gzip.open(root/'measurements240.json.gz','rt') as f: rows=json.load(f)['rows']
        task=score(onset=.1,end=.9)
        m=TaskMeasurement(task,initial['human_body_names'],initial['guitar_body_names'])
        m.reset(rows[0])
        for row in rows[1:]: result=m.update(row)
        self.assertEqual(len(rows),241)
        self.assertAlmostEqual(result['summary']['hold_fractions']['a'],1.)
        self.assertEqual(result['summary']['matched50'],0)
        self.assertEqual(result['summary']['released_count'],0)
        self.assertEqual(result['summary']['missed_strict'],1)

    def test_missing_duplicate_gap_and_input_private(self):
        s,h,g=sample(5);m=TaskMeasurement(score(),h,g)
        with self.assertRaises(RuntimeError):m.update(s)
        before=copy.deepcopy(s);m.reset(s)
        np.testing.assert_array_equal(before['geometry']['pick_G_m'],s['geometry']['pick_G_m'])
        s['geometry']['pick_G_m'][:]=100
        self.assertFalse(np.any(m.previous['geometry']['pick_G_m']==100))
        for step in (5,7):
            with self.assertRaises(ValueError):m.update(sample(step)[0])
        bad=sample(6)[0];bad['native_contacts']['physics_step']=7
        with self.assertRaises(ValueError):m.update(bad)

if __name__=='__main__':unittest.main()
