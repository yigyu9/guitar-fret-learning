import unittest
import numpy as np

from stability_adapter_2.trial_settings import validate_settings, initial_targets


class SettingsTests(unittest.TestCase):
    def test_invalid_numeric_and_schema_inputs(self):
        for value in ([0]*33, {'pose':[]}, {'joint_angles_rad':[]},
                      {'joint_angles_rad':{'R_Elbow_x':True}},
                      {'joint_angles_rad':{'R_Elbow_x':float('nan')}},
                      {'strap_rest_length_m':False}, {'strap_rest_length_m':0},
                      {'strap_rest_length_m':float('inf')}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_settings(value)
        with self.assertRaises(ValueError):
            validate_settings({}, require_length=True)

    def test_only_approved_guitar_z_offsets_are_allowed(self):
        self.assertEqual(validate_settings({})['guitar_initial_z_offset_m'],0.)
        self.assertEqual(validate_settings({'guitar_initial_z_offset_m':.005})['guitar_initial_z_offset_m'],.005)
        for offset in (True,None,'0.005',float('nan'),float('inf'),-.005,.002,.015):
            with self.subTest(offset=offset),self.assertRaises(ValueError):
                validate_settings({'guitar_initial_z_offset_m':offset})

    def test_explicit_main_angles_preserve_other_targets(self):
        base = np.array([.1,.2,.3],dtype=np.float32)
        names = ['Chest_x','R_Elbow_x','R_Hip_x']
        lower, upper = np.full(3,-1.),np.full(3,1.)
        settings = validate_settings({'joint_angles_rad':{'R_Elbow_x':.4}})
        target = initial_targets(base,names,[1],lower,upper,settings)
        np.testing.assert_array_equal(target[[0,2]],base[[0,2]])
        np.testing.assert_array_equal(base,np.array([.1,.2,.3],dtype=np.float32))
        self.assertAlmostEqual(float(target[1]),.4)
        for name, value in [('Chest_x',.2),('R_Hip_x',.4),('unknown',0),('R_Elbow_x',1.1)]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                initial_targets(base,names,[1],lower,upper,
                    validate_settings({'joint_angles_rad':{name:value}}))


if __name__ == '__main__':
    unittest.main()
