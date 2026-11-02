"""점 내부 판정과 수직 절단을 해석 가능한 정육면체로 확인한다."""
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fret_point_access',HERE/'fret_access_range.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
import numpy as np
from scipy.spatial import ConvexHull
from itertools import product

class PointAccessTest(unittest.TestCase):
    def setUp(self):
        self.planes=ConvexHull(np.array(list(product((-1.,1.),repeat=3)))).equations
        self.shapes=[dict(name='cube',planes=self.planes)]
    def test_inside_boundary_and_outside_are_distinct(self):
        self.assertEqual(module.classify_point(np.array([0.,0.,0.]),self.shapes)['strict_inside_shapes'],['cube'])
        boundary=module.classify_point(np.array([1.,0.,0.]),self.shapes)
        self.assertFalse(boundary['strict_inside_shapes']);self.assertEqual(boundary['boundary_shapes'],['cube'])
        self.assertFalse(module.classify_point(np.array([1.1,0.,0.]),self.shapes)['strict_inside_shapes'])
    def test_vertical_section(self):
        np.testing.assert_allclose(module.vertical_interval(.3,-.2,self.planes),[-1.,1.])
        self.assertIsNone(module.vertical_interval(1.1,0.,self.planes))

if __name__=='__main__':unittest.main()
