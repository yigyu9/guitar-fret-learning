"""생성된 실제 번들·A기준 FK·B 패드 후보 계약의 CPU 회귀검사."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import wave

import numpy as np
from scipy.spatial.transform import Rotation

import prepare_targets as prep


class PreparedTargetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = prep.ROOT/'data/song_bundles'/prep.SONG
        cls.result = json.loads((prep.BASE/'geometry/candidate_B.json').read_text())
        cls.catalog = json.loads((prep.ROOT/'guitar_learning/assets/natural_press_v3/catalog.json').read_text())
        cls.A = next(row for row in cls.catalog['goals'] if row['finger']=='middle')

    def test_actual_score_clock_and_source_string(self):
        from guitar_learning.song.task import make_task, load_anchor_track
        task = make_task(self.bundle)
        self.assertEqual([(t.string,t.fret,t.finger,t.onset_s,t.end_s) for t in task.targets],
                         [(2,f,2,3.+2*i,4.5+2*i) for i,f in enumerate((6,7,6,7))])
        self.assertEqual(task.episode_duration_s,11.)
        track = load_anchor_track(self.bundle)
        self.assertEqual([track['anchors'][120*i] for i in range(4)],[5.,6.,5.,6.])
        with wave.open(str(self.bundle/'source/audio.wav'),'rb') as audio:
            self.assertEqual(audio.getnframes()/audio.getframerate(),7.5)
            self.assertFalse(any(audio.readframes(audio.getnframes())))

    def test_arm_only_and_native_bounds(self):
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        q, a = np.array(self.result['q105']), np.array(self.A['q105'])
        ids = np.array(self.result['arm_native_indices']); mask=np.ones(105,dtype=bool); mask[ids]=False
        self.assertEqual(len(ids),12)
        np.testing.assert_array_equal(q[mask],a[mask])
        c=load_gpu_prepared_reset_contract('left');pd=c['initial']['native_PD_properties']
        self.assertTrue((q[ids]>=np.array(pd['lower'])[ids]).all())
        self.assertTrue((q[ids]<=np.array(pd['upper'])[ids]).all())
        hold=np.array(self.result['hold_target105']); ah=np.array(self.A['hold_target105'])
        np.testing.assert_array_equal(hold[mask],ah[mask]);np.testing.assert_array_equal(hold[ids],q[ids])

    def test_source_fk_snapshot_consistency(self):
        from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
        from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
        c=load_gpu_prepared_reset_contract('left');c=dict(c,state=copy.deepcopy(self.A['state']))
        s=SimpleNamespace(names=c['initial']['joint_names'],human_bodies=c['initial']['human_body_names'],q_ref=np.array(self.A['q105']))
        fk=full_fk(s,c['state']);q=np.array(self.result['q105'])
        state=prep.snapshot_for_q(c,q,fk)
        self.assertEqual(state,self.result['state'])
        for actor in ('guitar_body_states','chair_body_states'):
            self.assertEqual(state[actor],self.A['state'][actor])
        for name,body in zip(s.human_bodies,self.A['state']['human_body_states']):
            p,r=fk(np.array(self.A['q105']))[name]
            np.testing.assert_allclose(p,[body['pose']['p'][k]for k in 'xyz'],atol=1e-12)
            original=Rotation.from_quat([body['pose']['r'][k]for k in 'xyzw'])
            self.assertLess((original.inv()*r).magnitude(),1e-12)

    def test_same_point_cell_height_and_normal(self):
        row=self.result;k=row['selected_sample'];point=np.array(row['pad_points_G_m'][k]);m=row['geometry']
        self.assertTrue(row['candidate_valid']);self.assertFalse(row['native_verified'])
        self.assertLess(m['tangent_error_m'],.005)
        self.assertTrue(.010<=m['height_m']<=.014)
        self.assertTrue(m['cell_low_m']<=point[1]<=m['cell_high_m'])
        self.assertGreaterEqual(row['normal_cos'][k],.1)
        self.assertLess(row['wrist_rotation_change_deg'],.1)
        self.assertEqual(k,self.A['geometry']['selected_sample'])
        for name in ('index','ring','pinky'):
            self.assertEqual(row['other_distal_pad_clearance']['B']['distal_pads'][name][
                'finite_neck_string_height_facing_sample_count'],0)

    def test_provenance_and_guide_transition(self):
        for path,sha in self.result['source_sha256'].items():self.assertEqual(prep.digest(path),sha,path)
        manifest=json.loads((self.bundle/'manifest.json').read_text())
        self.assertEqual(manifest['provenance']['generator_source_sha256'][str(Path(prep.__file__).resolve())],prep.digest(prep.__file__))
        guide=self.result['wrist_guide_samples']
        self.assertEqual([guide[str(t)]['anchor_fret']for t in (3.,5.,7.,9.)],[5.,6.,5.,6.])
        delta=np.array(guide['5.0']['target_G_m'])-guide['3.0']['target_G_m']
        self.assertLess(delta[1],-.02);np.testing.assert_array_equal(delta[[0,2]],[0.,0.])

    def test_existing_bundle_is_not_overwritten(self):
        before=prep.digest(self.bundle/'manifest.json')
        with self.assertRaises(FileExistsError):prep.build_bundle()
        self.assertEqual(prep.digest(self.bundle/'manifest.json'),before)


if __name__=='__main__':
    unittest.main()
