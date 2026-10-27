"""Pure deadline codec/reward counterexamples; no native readiness claim."""
import unittest
import numpy as np
from .deadline_native_v1 import anchored_target, pilot_reward, PROFILE


class DeadlineNativeContracts(unittest.TestCase):
    def test_dynamic_anchor_endpoints(self):
        low=np.full(81,-2.); high=np.full(81,3.); anchor=np.linspace(-2.,3.,81)
        np.testing.assert_array_equal(anchored_target(np.zeros(81),anchor,low,high),anchor)
        np.testing.assert_allclose(anchored_target(np.ones(81),anchor,low,high),high)
        np.testing.assert_allclose(anchored_target(-np.ones(81),anchor,low,high),low)

    def test_bound_anchor_one_flat_side(self):
        low=np.zeros(81); high=np.ones(81)
        np.testing.assert_array_equal(anchored_target(-np.ones(81),low,low,high),low)
        np.testing.assert_array_equal(anchored_target(np.ones(81),high,low,high),high)

    def test_invalid_action_and_anchor(self):
        for action,anchor in ((np.full(81,1.01),np.zeros(81)),
                              (np.zeros(81),np.full(81,2.)),
                              (np.full(81,np.nan),np.zeros(81))):
            with self.assertRaises(ValueError):
                anchored_target(action,anchor,-np.ones(81),np.ones(81))

    def reward(self, **changes):
        kwargs=dict(position_outside=np.zeros(3),rotation_upper=0.,sounding_match=0.,
            fret_approach=0.,pick_approach=0.,body_excess=np.zeros(9),target_rate=np.zeros(81),
            accepted=0,wrong=0,success=0,miss=0,music_active=True)
        kwargs.update(changes)
        return pilot_reward(**kwargs)

    def test_inside_region_zero_and_prep_music_mask(self):
        self.assertEqual(self.reward()[0],0.)
        r,ledger=self.reward(sounding_match=1.,fret_approach=1.,pick_approach=1.,music_active=False)
        self.assertEqual(r,0.)
        self.assertEqual(ledger['sounding'],0.)

    def test_outside_monotonic_cost(self):
        costs=[self.reward(position_outside=np.array([x,0.,0.]),rotation_upper=x)[0]
               for x in (0.,.005,.05,.5)]
        self.assertTrue(all(a>b for a,b in zip(costs,costs[1:])))

    def test_rates_integrate_and_events_once(self):
        r,_=self.reward(sounding_match=1.,fret_approach=1.,pick_approach=1.)
        self.assertAlmostEqual(r*60,.9)
        r,ledger=self.reward(accepted=2,wrong=1,success=1,miss=2)
        self.assertAlmostEqual(r,1.75)
        self.assertAlmostEqual(ledger['fixed_event_deadlines'],0.)

    def test_unknown_measurement_abort_and_unqualified_profile(self):
        with self.assertRaises(ValueError): self.reward(rotation_upper=np.nan)
        self.assertFalse(PROFILE['production_reward_v4_certified'])
        self.assertIn('fatal_scheduled_tail',PROFILE['unimplemented_production_terms'])


if __name__=='__main__': unittest.main()
