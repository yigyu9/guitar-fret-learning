"""CPU checks for immutable035/v14 annotation geometry and song boundaries."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fixed_song_guides',HERE/'render.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class FixedGuideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepared,cls.geometry,cls.scene,cls.pins=tool.build_geometry('05_BN2-131-B_solo')

    def test_complete_original_song_and_clock(self):
        s=self.scene
        self.assertEqual(s['target_count'],67)
        self.assertEqual(s['control_ticks'],1969)
        self.assertEqual(len(s['wrist_target_G_m']),1970)
        self.assertAlmostEqual(s['duration_s'],1969/60)
        self.assertEqual(len({t['target_id'] for t in s['targets']}),67)

    def test_each_cell_uses_two_neighboring_actual_markers(self):
        self.assertEqual(len(self.scene['cells']),22)
        wires=self.geometry['fret_markers_G_m']
        for c in self.scene['cells']:
            p=np.array(c['quad_G_m']);f=c['fret']
            np.testing.assert_allclose(p[:2,1],wires[f-1,1],atol=1e-12)
            np.testing.assert_allclose(p[2:,1],wires[f,1],atol=1e-12)
            self.assertGreater(p[1,0],p[0,0])

    def test_target_segments_use_correct_string_plane_and_inward_margin(self):
        plane=np.array(self.scene['press_plane']['plane_G'])
        starts=self.geometry['starts_G_m'];ends=self.geometry['ends_G_m'];wires=self.geometry['fret_markers_G_m']
        for t in self.scene['targets']:
            p=np.array(t['segment_G_m']);f=t['fret'];string=t['string']-1
            np.testing.assert_allclose(p@plane[:3]+plane[3],0,atol=1e-12)
            lo,hi=sorted([wires[f-1,1],wires[f,1]])
            np.testing.assert_allclose(p[:,1],[lo+.002,hi-.002],atol=1e-12)
            expected_x=starts[string,0]+(p[:,1]-starts[string,1])/(ends[string,1]-starts[string,1])*(ends[string,0]-starts[string,0])
            np.testing.assert_allclose(p[:,0],expected_x,atol=1e-12)

    def test_wrist_reference_preserves_xz_and_only_moves_along_neck(self):
        target=np.array(self.scene['wrist_target_G_m']);ref=np.array(self.scene['wrist_G_m'])
        np.testing.assert_allclose(target[:,0],ref[0],atol=1e-7)
        np.testing.assert_allclose(target[:,2],ref[2],atol=1e-7)
        self.assertLess(self.scene['guide_formula_max_error_m'],2e-6)
        self.assertGreater(np.ptp(target[:,1]),.1)

    def test_audible_onset_inclusive_end_exclusive_and_preparation_separate(self):
        # Real 240Hz/60Hz samples rarely hit score decimal boundaries exactly.
        # Use an exact integral frame target to check the boundary convention.
        sample=dict(self.scene)
        sample['targets']=[dict(index=0,onset_s=1.,end_s=2.)]
        sample['tracking']=[[0] for _ in range(121)]
        sample['tracking_valid']=[[True] for _ in range(121)]
        self.assertEqual(tool.active(sample,59),([],[0]))
        self.assertEqual(tool.active(sample,60),([0],[]))
        self.assertEqual(tool.active(sample,119),([0],[]))
        # Production selector invalidates end; mirror that validity at the endpoint.
        sample['tracking_valid'][120]=[False]
        self.assertEqual(tool.active(sample,120),([],[]))

    def test_tracking_is_assigned_and_preparing_is_future(self):
        for tick in range(1970):
            audible,prep=tool.active(self.scene,tick);now=tick/60
            for slot,(i,valid) in enumerate(zip(self.scene['tracking'][tick],self.scene['tracking_valid'][tick])):
                if valid:self.assertEqual(self.scene['targets'][i]['finger'],slot+1)
            for i in prep:
                t=self.scene['targets'][i]
                self.assertLessEqual(t['press_s']-2,now)
                self.assertLess(now,t['onset_s'])
                self.assertNotIn(i,audible)

    def test_neck_camera_screen_up_agrees_with_world_up(self):
        i=self.prepared['initial'];state=self.prepared['state']
        _,rotation=tool.frame(state['guitar_body_states'][i['guitar_body_names'].index('guitar')])
        up=rotation.apply(tool.NECK_CAMERA_AXES_G[:,1])
        self.assertGreater(up[2],.99)
        self.assertAlmostEqual(np.linalg.det(tool.NECK_CAMERA_AXES_G),1.)

    def test_press_surface_sources_are_pinned(self):
        for path,expected in self.scene['press_plane']['source_sha256'].items():
            self.assertEqual(self.pins[path],expected)
            self.assertEqual(tool.sha(path),expected)


if __name__=='__main__':unittest.main(verbosity=2)
