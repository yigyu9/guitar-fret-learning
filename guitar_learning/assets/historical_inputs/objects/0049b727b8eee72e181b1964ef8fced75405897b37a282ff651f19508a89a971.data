"""Boundary/mapping regressions for teacher support nominal, CPU only."""
import unittest
import numpy as np
from .deadline_support_nominal_v1 import support_nominal

GROUPS = ['body']*9+['head']*6+['arm']*12+['finger']*21+['arm']*12+['finger']*21
NAMES = ['joint_%d'%i for i in range(81)]
NAMES[27:32] = ['LH:thumb1_x','LH:thumb1_y','LH:thumb1_z','LH:thumb2','LH:thumb3']


class SupportNominalTests(unittest.TestCase):
    def setUp(self):
        self.lo, self.hi, self.preload = np.full(81,-1.), np.full(81,1.), np.zeros(81)

    def guard(self, teacher, names=NAMES):
        return support_nominal(teacher,self.preload,self.lo,self.hi,GROUPS,names)

    def test_zero_preparation_preserved(self):
        self.assertTrue(np.array_equal(self.guard(self.preload),self.preload))

    def test_signed_arm_thumb_caps_other_channels_and_no_mutation(self):
        arm = np.array(GROUPS)=='arm'; thumb=np.array([n.startswith('LH:thumb') for n in NAMES])
        for sign in (-1,1):
            teacher=np.full(81,sign*.8); before=teacher.copy(); result=self.guard(teacher)
            self.assertTrue(np.all(result[arm]==sign*.15)); self.assertTrue(np.all(result[thumb]==sign*.10))
            self.assertTrue(np.array_equal(result[~(arm|thumb)],teacher[~(arm|thumb)]))
            self.assertTrue(np.array_equal(teacher,before)); self.assertTrue(np.array_equal(self.preload,np.zeros(81)))

    def test_native_limit_intersection(self):
        self.preload[15]=.98; self.preload[27]=-.98
        teacher=self.preload.copy();teacher[15]=1;teacher[27]=-1
        result=self.guard(teacher)
        self.assertEqual(result[15],1);self.assertEqual(result[27],-1)
        self.assertTrue(np.all(result>=self.lo));self.assertTrue(np.all(result<=self.hi))

    def test_missing_thumb_or_invalid_preload_rejected(self):
        with self.assertRaises(ValueError): self.guard(np.zeros(81),['joint_%d'%i for i in range(81)])
        self.preload[15]=1.1
        with self.assertRaises(ValueError): self.guard(np.zeros(81))


if __name__=='__main__':unittest.main()
