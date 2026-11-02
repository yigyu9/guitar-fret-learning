"""격리 참조 진단의 시간창·연속 속도·native 호출 경로를 CPU에서 검사한다."""
import ast
import json
from pathlib import Path
import unittest
import numpy as np
from reference_motion_settle030 import BASE, keyframes, trajectory, quintic


class ReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference=json.loads((BASE/'geometry/reference_v1/reference_candidates.json').read_text())
        cls.candidates=cls.reference['candidates']

    def test_four_geometry_endpoints(self):
        self.assertTrue(all(v['cpu_candidate_valid'] for v in self.candidates.values()))
        self.assertFalse(self.reference['native_verified'])
        for name, fret in [('A_press',6),('B_press',8)]:
            self.assertEqual(self.candidates[name]['candidate_frets_geometry_only'],[fret])

    def test_physical_note_windows_unchanged(self):
        times,q,_=trajectory(self.candidates,.75)
        for start,end,label in [(3.,4.5,'A_press'),(5.25,6.75,'B_press')]:
            mask=(times>=start)&(times<=end)
            np.testing.assert_allclose(q[mask],np.tile(self.candidates[label]['q105'],(mask.sum(),1)),atol=1e-12)
        self.assertEqual(times[-1],7.25)
        self.assertTrue(np.isfinite(q).all())

    def test_continuous_rate(self):
        frames=keyframes(self.candidates,.75)
        indices=self.reference['native_indices']
        peak=np.max([1.875*np.abs(b[2][indices]-a[2][indices])/(b[0]-a[0])
            for a,b in zip(frames,frames[1:])],axis=0)
        bound=np.array([3.]*12+[4.]*4)
        self.assertTrue((peak<=bound+1e-8).all(),peak.tolist())
        self.assertEqual(len(indices),16)

    def test_native_no_teleport_or_clock_assignment(self):
        path=BASE/'tools/reference_native_settle030.py'; source=path.read_text(); tree=ast.parse(source)
        calls=[n.func.value.id+'.'+n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)]
        self.assertIn('env.begin_control',calls)
        self.assertIn('env.substep',calls)
        self.assertIn('env.end_control',calls)
        self.assertIn('env.invalidate_control',calls)
        self.assertNotIn('env._snapshot',calls)
        self.assertNotIn('scene.reset',calls)
        for n in ast.walk(tree):
            if isinstance(n,(ast.Assign,ast.AugAssign)):
                targets=n.targets if isinstance(n,ast.Assign) else [n.target]
                self.assertTrue(all("attr='clock'" not in ast.dump(v) for v in targets))
        self.assertNotIn('set_actor_dof',source)
        self.assertNotIn('score_time=',source)
        self.assertIn('virtual_middle_s3_f6_f8_AB_v1',source)

    def test_production_exposure_schedule_contract(self):
        from guitar_learning.training.finger_skill_runner import ExposureSchedule
        source=(BASE/'tools/reference_native_settle030.py').read_text()
        self.assertIn('planned_transitions=4,full_song_after=1',source)
        schedule=ExposureSchedule(4,1)
        self.assertEqual(schedule.config['full_song_after'],1)
        with self.assertRaises(ValueError):
            ExposureSchedule(2,1)

    def test_longer_settle_without_target_time_change(self):
        frames=keyframes(self.candidates,.75)
        arrivals=[time for time,label,_ in frames if label=='B_press']
        self.assertAlmostEqual(arrivals[0],4.95)
        self.assertIn(5.25,arrivals)
        self.assertIn(6.75,arrivals)
        source=(BASE/'tools/reference_native_settle030.py').read_text()
        self.assertIn('pins[str(motion_path)]=sha(motion_path)',source)

    def test_quintic_endpoints(self):
        np.testing.assert_equal(quintic(np.array([-1.,0.,1.,2.])),[0.,0.,1.,1.])


if __name__=='__main__':unittest.main()
