"""The second crossing changes only timing, including continuous hold boundaries."""
import unittest
import numpy as np
from guitar_learning.tool.experiments.right_strike.native_probe import trajectory as baseline
from guitar_learning.tool.experiments.right_strike_protocol_v3 import trajectory


class TimingComparisonTests(unittest.TestCase):
    def test_only_crossing_interval_is_compressed(self):
        initial = np.zeros(6); points = [np.full(6, i) for i in (1., 2., 3.)]
        for t in (0., .5, 1., 2.6, 2.89, 3.31, 3.8, 5.):
            np.testing.assert_array_equal(trajectory(t, initial, points), baseline(t, initial, points))
        for t, value in ((2.94, 1.), (3., 1.5), (3.06, 2.)):
            np.testing.assert_allclose(trajectory(t, initial, points), value, atol=1e-12)
        path = np.array([trajectory(t, initial, points) for t in np.linspace(0, 5, 1001)])
        self.assertTrue((np.diff(path[:, 0]) >= -1e-12).all())
        for t in (float('nan'), float('inf'), -.1, 5.1):
            with self.assertRaises(ValueError):
                trajectory(t, initial, points)


if __name__ == '__main__':
    unittest.main()
