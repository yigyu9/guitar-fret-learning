"""참조 경로의 유지·순서·요청각 의미를 확인한다. 물리 성공 검사가 아니다."""
import ast
import json
import importlib.util
from pathlib import Path
import unittest
import numpy as np

spec=importlib.util.spec_from_file_location('reference_motion',Path(__file__).with_name('reference_motion.py'))
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class ReferenceTrajectoryTests(unittest.TestCase):
    def setUp(self):
        self.candidates={key:dict(q105=np.full(105,i).tolist()) for i,key in enumerate(
            ('A_press','A_hover','B_press','B_hover'))}

    def test_all_requested_gaps_and_holds_are_preserved(self):
        for gap in (.5,.75,1.):
            ts,qs,frames=module.trajectory(self.candidates,gap)
            np.testing.assert_array_equal(qs[ts<=1.5],np.zeros((sum(ts<=1.5),105)))
            b=(ts>=1.5+gap)&(ts<=3.+gap)
            np.testing.assert_array_equal(qs[b],np.full((sum(b),105),2.))
            a=ts>=3.+2*gap
            np.testing.assert_array_equal(qs[a],np.zeros((sum(a),105)))
            self.assertAlmostEqual(ts[-1],4.5+2*gap)
            self.assertEqual([name for _,name in frames],['A_press','A_press','A_hover','B_hover',
                'B_press','B_press','B_press','B_hover','A_hover','A_press','A_press','A_press'])

    def test_settle_preserves_previous_note_and_completes_descent_early(self):
        for gap in (.5,.75,1.):
            ts,qs,frames=module.trajectory(self.candidates,gap)
            for start,end,value in ((1.5+gap-.2,1.5+gap,2.),(3.+2*gap-.2,3.+2*gap,0.)):
                mask=(ts>=start-1e-10)&(ts<=end+1e-10)
                np.testing.assert_allclose(qs[mask],value,atol=1e-10,rtol=0)
            self.assertEqual(frames[1][0],1.5)

    def test_no_unsupported_schedule_silently_accepted(self):
        with self.assertRaises(ValueError): module.trajectory(self.candidates,.2)

    def test_native_note_output_accepts_numpy_streak(self):
        # 실제 native 출력 정리 코드를 추출하여 GPU 없이 회귀를 확인한다.
        path=Path(__file__).with_name('reference_native.py')
        tree=ast.parse(path.read_text())
        loop=next(n for n in ast.walk(tree) if isinstance(n,ast.For) and
            isinstance(n.target,ast.Name) and n.target.id=='row' and
            isinstance(n.iter,ast.Name) and n.iter.id=='note')
        row=dict(best_streak_s=np.float64(1.5),clean_s=1.5,observed_s=1.5,first_clean_s=3.+1/240.,start_s=3.)
        code=compile(ast.Module(body=loop.body,type_ignores=[]),str(path),'exec')
        exec(code,{'row':row})
        self.assertIs(type(row['best_streak_s']),float)
        json.dumps(row,allow_nan=False)
        for key in ('diagnostic_hold_100ms','hold_90percent','full_hold_observed','entire_hold_clean'):
            self.assertIs(type(row[key]),bool)

    def test_quintic_endpoints_have_zero_slope(self):
        self.assertEqual(module.quintic(0.),0.)
        self.assertEqual(module.quintic(1.),1.)
        self.assertLess(module.quintic(1e-5)/1e-5,1e-7)
        self.assertLess((1-module.quintic(1-1e-5))/1e-5,1e-7)


if __name__=='__main__': unittest.main()
