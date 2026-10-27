"""CPU reward checks for the native-measured long approach distance."""
import unittest
from unittest.mock import patch
import numpy as np

from .environment_v2 import (MusicGuitarEnvironment,PreviousEnvironment,
                             dense_approach_quality,confirmed_release_quality)


class DenseApproachTest(unittest.TestCase):
    def test_measured_baseline_has_useful_distance_sensitivity(self):
        far,near = .154,.144
        qfar,qnear = dense_approach_quality([far,near])
        self.assertGreater(qfar,.3)
        self.assertGreater(qnear-qfar,.02)
        self.assertLess(np.exp(-(far/.025)**2),1e-15)
        self.assertEqual(dense_approach_quality(0),1)
        self.assertGreater(dense_approach_quality(.01),dense_approach_quality(.1))
        self.assertGreater(dense_approach_quality(.1),dense_approach_quality(.2))

    def test_invalid_distances_rejected(self):
        for value in (-.01,np.nan,np.inf):
            with self.assertRaises(ValueError): dense_approach_quality(value)

    def test_never_pressed_hand_gets_no_release_credit(self):
        row = dict(released_after_hold=False,assigned_contact_geometric_seconds=0)
        self.assertEqual(confirmed_release_quality([row]),0)
        row['released_after_hold'] = True
        self.assertEqual(confirmed_release_quality([row]),0)
        row['assigned_contact_geometric_seconds'] = .15
        self.assertEqual(confirmed_release_quality([row]),1)
        row['released_after_hold'] = False
        self.assertEqual(confirmed_release_quality([row]),0)

    def test_v2_only_replaces_approach_and_confirmed_release(self):
        old = dict(fret_rows=[dict(distance_m=.154,required=True,anticipatory_approach=False),
                             dict(distance_m=.001,required=False,anticipatory_approach=False)],
                   approach_quality=1e-17,release_quality=1.,
                   press_hold_release=[dict(released_after_hold=False,assigned_contact_geometric_seconds=0)],
                   accepted_crossings=2,force_verified_press=False)
        env = MusicGuitarEnvironment.__new__(MusicGuitarEnvironment)
        with patch.object(PreviousEnvironment,'_measure_music',return_value=old):
            result = env._measure_music(1.)
        self.assertAlmostEqual(result['approach_quality'],float(np.exp(-.154/.15)))
        self.assertEqual(result['active_approach_distances_m'],[.154])
        self.assertEqual(result['release_quality'],0)
        self.assertEqual(result['accepted_crossings'],2)
        self.assertFalse(result['force_verified_press'])
        self.assertEqual(result['approach_quality_v1_diagnostic'],1e-17)


if __name__=='__main__': unittest.main()
