"""Contact attribution tests with explicit synthetic native feature fixtures."""
import copy
from dataclasses import replace
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.quality.fretting_quality import classify_fretting
from guitar_learning.core.measurement import FretTarget
from guitar_learning.core.measurement import FretContract
from guitar_learning.core.measurement import measure_sample
from guitar_learning.core.geometry import frame
from guitar_learning.core.geometry import geometry_snapshot
from guitar_learning.song.task import ScoreTarget
from guitar_learning.tests.test_fretting_v1 import fixture

TARGET=ScoreTarget('a','e',0,5,1,1,1.,1.2,.8,1.,1.2)
CONTRACT=FretContract(minimum_dwell_s=.05)


def add_contact(inputs,*,finger='middle2',string=1,fret=6,y=.11,height=-.001,raw_lambda=1.):
    state,humans,guitars,contacts=inputs
    geometry=geometry_snapshot(state,humans,guitars)
    a,b=geometry['starts_G_m'][string-1],geometry['ends_G_m'][string-1]
    fraction=(y-a[1])/(b[1]-a[1]);point=a+fraction*(b-a);point[2]+=height
    gp,gr=frame(state['guitar_body_states'][guitars.index('guitar')]);world=gp+gr.apply(point)
    guitar_name='guitar' if fret=='root' else 'G:fret'+str(fret)
    names=('guitar/'+guitar_name,'human/LH:'+finger)
    bodies=(state['guitar_body_states'][guitars.index(guitar_name)],state['human_body_states'][humans.index('LH:'+finger)])
    raw=dict(body0_name=names[0],body1_name=names[1],**{'lambda':raw_lambda})
    for i,body in enumerate(bodies):
        pos,rot=frame(body);raw['localPos'+str(i)]=dict(zip('xyz',rot.inv().apply(world-pos).tolist()))
    contacts['contacts'].append(raw)
    return inputs


def quality(inputs=None,target=TARGET):
    inputs=fixture() if inputs is None else inputs
    evidence=measure_sample(*inputs,FretTarget(target.string+1,target.fret,dict(zip(range(1,5),('index','middle','ring','pinky')))[target.finger]),CONTRACT)
    geometry=geometry_snapshot(inputs[0],inputs[1],inputs[2])
    return classify_fretting(geometry,target,evidence,CONTRACT),evidence,geometry


class FrettingQualityTests(unittest.TestCase):
    def test_correct_target_read_only_and_explicit_evidence(self):
        inputs=fixture();before=copy.deepcopy(inputs)
        q,e,g=quality(inputs)
        self.assertEqual(q['status'],'correct');self.assertTrue(q['clean_target_candidate'])
        self.assertEqual(q['positive_evidence_ids'],e['valid_evidence_ids'])
        self.assertEqual(q['target_string_contact_evidence_ids'],e['valid_evidence_ids'])
        self.assertEqual(inputs,before)

    def test_target_plus_higher_same_string_blocks_clean_but_preserves_positive(self):
        q,e,_=quality(add_contact(fixture(),fret=6,y=.11))
        self.assertTrue(e['fretting_contact_candidate']);self.assertTrue(q['positive_target_candidate'])
        self.assertFalse(q['clean_target_candidate']);self.assertTrue(q['higher_fret'])
        self.assertTrue(q['wrong_fret']);self.assertEqual(q['status'],'wrong')
        self.assertEqual(len(q['target_string_contact_evidence_ids']),2)

    def test_lower_contact_allowed_only_with_actual_target(self):
        q,_,_=quality(add_contact(fixture(),fret=4,y=.15))
        self.assertTrue(q['clean_target_candidate']);self.assertFalse(q['wrong_fret'])
        self.assertTrue(q['allowed_lower_fret_evidence_ids'])
        q,_,_=quality(fixture(fret_body=4,y=.15))
        self.assertEqual(q['status'],'wrong');self.assertTrue(q['wrong_fret'])

    def test_wrong_finger_only_on_goal_is_assignment_error_but_extra_same_goal_not_veto(self):
        q,_,_=quality(fixture(finger='middle2'))
        self.assertTrue(q['wrong_finger']);self.assertTrue(q['wrong_assignment'])
        self.assertEqual(q['status'],'wrong')
        q,_,_=quality(add_contact(fixture(),fret=5,y=.13))
        self.assertTrue(q['clean_target_candidate']);self.assertFalse(q['wrong_assignment'])

    def test_other_string_is_diagnostic_and_not_blanket_penalty(self):
        q,_,_=quality(add_contact(fixture(),fret=6,y=.11,string=2))
        self.assertTrue(q['incidental_other_string']);self.assertTrue(q['clean_target_candidate'])
        self.assertFalse(q['higher_fret']);self.assertFalse(q['wrong_fret'])
        q,_,_=quality(fixture(string=2))
        self.assertEqual(q['status'],'missing');self.assertTrue(q['incidental_other_string'])

    def test_named_target_body_margin_and_root_margin_not_nominal_higher_error(self):
        for body in (5,'guitar'):
            with self.subTest(body=body):
                q,_,_=quality(fixture(fret_body=body,y=.1193))
                self.assertTrue(q['clean_target_candidate']);self.assertFalse(q['higher_fret'])
                self.assertEqual(q['feature_diagnostics'][0]['geometric_cells'],[6])
                self.assertEqual(q['feature_diagnostics'][0]['assigned_fret'],5)

    def test_unlabelled_interior_higher_and_uncertain_wire_do_not_conflate(self):
        q,_,_=quality(add_contact(fixture(),fret='root',y=.11))
        self.assertTrue(q['higher_fret'])
        q,_,_=quality(add_contact(fixture(),fret='root',y=.0995))
        self.assertTrue(q['uncertain']);self.assertTrue(q['clean_target_candidate'])
        self.assertIn(q['uncertain_evidence_ids'][0],q['target_string_contact_evidence_ids'])

    def test_body_geometry_disagreement_and_unaligned_witness_are_uncertain(self):
        inputs=add_contact(fixture(),fret=9,y=.11)
        q,_,_=quality(inputs)
        self.assertTrue(q['uncertain']);self.assertFalse(q['wrong_fret']);self.assertTrue(q['clean_target_candidate'])
        inputs=add_contact(fixture(),fret=6,y=.11)
        inputs[3]['contacts'][-1]['localPos1']['x']+=.001
        q,_,_=quality(inputs)
        self.assertTrue(q['uncertain']);self.assertTrue(q['clean_target_candidate'])

    def test_nonpositive_contact_and_support_bodies_do_not_become_wrong_press(self):
        q,_,_=quality(fixture(raw_lambda=0))
        self.assertEqual(q['status'],'missing');self.assertFalse(q['uncertain'])
        # Support rejection is already represented by the existing evidence;
        # classification never counts this body as a fretting error.
        q,e,g=quality()
        bad=copy.deepcopy(e);bad['contact_evidence'][0]['human_body']='human/R_Hip'
        bad['contact_evidence'][0]['valid']=False;bad['valid_evidence_ids']=[];bad['fretting_contact_candidate']=False
        out=classify_fretting(g,TARGET,bad,CONTRACT)
        self.assertEqual(out['status'],'missing');self.assertFalse(out['wrong_finger'])

    def test_live_translated_rotated_nonparallel_strings_keep_classification(self):
        ref=quality(add_contact(fixture(),fret=6,y=.11))[0]
        transformed=quality(add_contact(fixture(translation=(.3,-.5,.8),rotation=Rotation.from_euler('xyz',(.2,-.4,.7))),fret=6,y=.11))[0]
        for name in ('status','positive_target_candidate','clean_target_candidate','higher_fret','wrong_fret'):
            self.assertEqual(ref[name],transformed[name])
        self.assertEqual(ref['higher_fret_evidence_ids'],transformed['higher_fret_evidence_ids'])

    def test_open_bad_target_or_nonfinite_geometry_rejected(self):
        q,e,g=quality()
        for target in (replace(TARGET,fret=0,finger=0),replace(TARGET,string=6)):
            with self.assertRaises(ValueError):classify_fretting(g,target,e,CONTRACT)
        g=copy.deepcopy(g);g['starts_G_m'][0,0]=float('nan')
        with self.assertRaises(ValueError):classify_fretting(g,TARGET,e,CONTRACT)


if __name__=='__main__':unittest.main()
