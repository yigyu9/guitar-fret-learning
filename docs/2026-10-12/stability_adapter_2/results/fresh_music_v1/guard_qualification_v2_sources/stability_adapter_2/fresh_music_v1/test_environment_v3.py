"""Whole-frame candidate selection never mixes bodies or raises tolerances."""
import unittest
import numpy as np
from .environment_v3 import choose_validation_alignment,MusicGuitarEnvironment
from .environment import shell


class AlignmentTest(unittest.TestCase):
    def test_current_consistent_previous_false_positive(self):
        self.assertEqual(choose_validation_alignment(.0007789463,.0104187087),'current')

    def test_qualified_fallback_only_if_current_fails(self):
        self.assertEqual(choose_validation_alignment(.012,.004),'previous_k_minus_1')
        self.assertEqual(choose_validation_alignment(.004,.001),'current')

    def test_two_failed_candidates_and_invalid_numbers_reject(self):
        for errors in ((.011,.012),(np.nan,.001),(.001,np.inf),(-.001,.001)):
            with self.assertRaises(ValueError): choose_validation_alignment(*errors)

    def test_global_max_does_not_mix_bodywise_minimum(self):
        current,previous = [.012,.001],[.001,.012]
        with self.assertRaises(ValueError): choose_validation_alignment(max(current),max(previous))

    def test_new_abi_same_reward_and_physical_actions(self):
        env = MusicGuitarEnvironment(shell.ROOT/'data/song_bundles/00_SS1-68-E_comp')
        self.assertEqual(env.abi['version'],'fresh_music_native_v3')
        self.assertEqual(env.abi['reward_profile']['approach_scale_m'],.15)
        self.assertEqual(env.abi['velocity_validation']['threshold_m_s'],.01)
        self.assertEqual(env.action_dim,54)
        self.assertEqual(env.obs_dim,744)


if __name__=='__main__': unittest.main()
