"""The visible previous target defines smoothing with no additional filter state."""
import unittest
import numpy as np
from .environment_v5 import smooth_target


class TargetSmoothingTests(unittest.TestCase):
    def test_known_step_and_observed_state_only(self):
        previous = np.zeros(81,dtype=np.float32)
        request = np.r_[np.full(54,.08),np.zeros(27)]
        result = smooth_target(request,previous,.2)
        np.testing.assert_allclose(result[:54],.016)
        np.testing.assert_array_equal(result[54:],previous[54:])
        np.testing.assert_array_equal(previous,np.zeros(81))

    def test_convex_bounds_and_persistent_authority(self):
        request = np.linspace(-.08,.08,81)
        previous = np.zeros(81)
        for _ in range(100):
            next_target = smooth_target(request,previous,.2)
            self.assertTrue(np.all(next_target>=np.minimum(previous,request)))
            self.assertTrue(np.all(next_target<=np.maximum(previous,request)))
            previous = next_target
        np.testing.assert_allclose(previous,request,atol=2e-11)

    def test_no_smoothing_and_invalid_alpha(self):
        np.testing.assert_array_equal(smooth_target(np.ones(81),np.zeros(81),1),np.ones(81))
        for alpha in (0,-.2,1.01,float('nan')):
            with self.assertRaises(ValueError): smooth_target(np.ones(81),np.zeros(81),alpha)


if __name__=='__main__': unittest.main()
