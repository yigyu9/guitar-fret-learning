import unittest
import numpy as np
from guitar_learning.core.measurement import StrikeDetector


def geometry(step,pick):
    starts=np.array([[i*.01,-.4,0.] for i in range(6)])
    ends=starts.copy(); ends[:,1]=-.2
    return dict(physics_step=step,starts_G_m=starts,ends_G_m=ends,pick_G_m=np.array(pick,dtype=float))


class StrikeTests(unittest.TestCase):
    def test_six_subframe_crossings(self):
        d=StrikeDetector(); r=d.update(geometry(0,[-.01,-.32,-.002]),geometry(1,[.06,-.32,-.002]))
        self.assertEqual([e['string_number'] for e in r['events']],list(range(1,7)))
        self.assertTrue(all(e['direction']==1 for e in r['events']))
        self.assertTrue(all(0<e['subframe_fraction']<1 for e in r['events']))
        self.assertEqual(len(d.update(geometry(1,[.06,-.32,-.002]),geometry(2,[-.01,-.32,-.002]))['events']),0)

    def test_zone_depth_finite_direction(self):
        for y,z in ((-.1,-.002),(-.32,-.1),(-.32,.01)):
            r=StrikeDetector().update(geometry(0,[-.01,y,z]),geometry(1,[.06,y,z]))
            self.assertFalse(r['events'])
        r=StrikeDetector().update(geometry(0,[.06,-.32,-.002]),geometry(1,[-.01,-.32,-.002]))
        self.assertTrue(all(e['direction']==-1 for e in r['events']))

    def test_common_rigid_motion_and_discontinuity(self):
        # Frames are independently transformed to G; common SE3 motion therefore
        # leaves identical local inputs rather than a swept world-space chord.
        d=StrikeDetector(); a=geometry(0,[.025,-.32,-.002]); b=geometry(1,[.025,-.32,-.002])
        self.assertFalse(d.update(a,b)['events'])
        with self.assertRaises(ValueError): d.update(a,b)
        with self.assertRaises(ValueError): StrikeDetector().update(a,geometry(3,[.03,-.32,-.002]))

if __name__=='__main__': unittest.main()
