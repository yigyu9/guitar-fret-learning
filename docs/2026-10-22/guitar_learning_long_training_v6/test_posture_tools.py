"""Known quaternion/role/empty-denominator CPU fixtures, no actual analysis main."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
from scipy.spatial.transform import Rotation

PHASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('analyze_posture',PHASE/'analyze_posture.py')
analysis=importlib.util.module_from_spec(spec);spec.loader.exec_module(analysis)


def poses(angles):
    angles=np.asarray(angles,dtype=float)
    n=len(angles);palm=Rotation.from_euler('xyz',np.tile([20,-35,17],(n,1)),degrees=True)
    result=np.empty((n,4,3,4))
    for f in range(4):
        parent=palm
        for j in range(3):
            parent=parent*Rotation.from_rotvec(np.c_[angles[:,f,j]*np.pi/180,np.zeros((n,2))])
            result[:,f,j]=parent.as_quat()
    return palm.as_quat(),result


class PostureToolsTests(unittest.TestCase):
    def test_known_signed_flexions_and_qualities_under_rotated_palm(self):
        triples=np.array([[0,0,90],[40,55,35],[30,30,15],[-30,0,70]])
        angles=np.broadcast_to(triples[None],(2,4,3)).copy()
        palm,segments=poses(angles)
        result=analysis.measure([0,1],[],palm,segments)
        np.testing.assert_allclose(result['angles']*analysis.DEG,angles,atol=1e-12)
        np.testing.assert_array_equal(result['valid'],True)
        np.testing.assert_array_equal(result['idle_weight'],1)
        np.testing.assert_array_equal(result['roles'],0)
        self.assertLess(result['oracle_max_error_deg'],1e-10)
        expected=np.exp(-np.array([70**2+30**2,0,0,50**2+40**2+10**2])/30**2)
        np.testing.assert_allclose(result['coordination_quality'][0],expected,atol=1e-14)

    def test_nonplanar_base_full_quaternion_oracle_and_invalid_projection(self):
        palm,segments=poses(np.zeros((1,4,3)))
        relative=Rotation.from_rotvec(np.deg2rad([35,25,15]))
        parent=Rotation.from_quat(palm[0])
        segments[0,0]=np.repeat((parent*relative).as_quat()[None],3,axis=0)
        direction=relative.apply([0,-1,0])
        expected=np.arctan2(-direction[2],-direction[1])
        result=analysis.measure([0],[],palm,segments)
        self.assertAlmostEqual(result['angles'][0,0,0],expected,places=13)
        self.assertGreater(abs(expected*analysis.DEG-35),1)
        segments[0,1]=np.repeat((parent*Rotation.from_euler('z',90,degrees=True)).as_quat()[None],3,axis=0)
        result=analysis.measure([0],[],palm,segments)
        self.assertFalse(result['valid'][0,1,0]);self.assertEqual(result['coordination_quality'][0,1],0)

    def test_endpoint_roles_fade_absent_finger_and_zero_denominators(self):
        times=np.array([-.25,-.125,0.,1.,2.,3.,3.125,3.25])
        targets=[dict(onset_s=1.,end_s=3.,press_s=2.,finger=1)]
        palm,segments=poses(np.tile(np.array([30,30,15]),(len(times),4,1)))
        result=analysis.measure(times,targets,palm,segments)
        np.testing.assert_allclose(result['idle_weight'][:,0],[1,.5,0,0,0,0,.5,1],atol=1e-14)
        np.testing.assert_array_equal(result['roles'][:,0],[0,0,1,2,2,0,0,0])
        np.testing.assert_array_equal(result['idle_weight'][:,1:],1)
        q=np.tile(np.deg2rad([30,0,30,15]),(len(times),1))
        row=analysis.summarize_finger(result,1,q,q,np.zeros_like(q),np.ones(4)*-2,np.ones(4)*2)
        self.assertEqual(row['audible']['endpoint_samples'],0)
        self.assertIsNone(row['audible']['angles_deg'][1]['mean'])
        self.assertIsNone(row['audible']['violation_fraction']['fully_straight'])
        self.assertEqual(row['idle_full']['usable_triplets'],len(times))
        empty=analysis.pooled([])
        self.assertEqual(empty['safe']['captures'],0)
        self.assertIsNone(empty['failed']['fingers']['index']['all']['pip_mean_deg'])

    def test_soft_violation_allocation_and_endpoint_weighted_safety_pool(self):
        angles=np.tile(np.array([0,0,90]),(3,4,1));palm,segments=poses(angles)
        measured=analysis.measure([1,2,3],[],palm,segments)
        q=np.tile(np.deg2rad([0,0,0,90]),(3,1))
        roles=analysis.summarize_finger(measured,0,q,q,np.zeros_like(q),np.zeros(4),np.ones(4)*np.pi/2)
        row=roles['all'];self.assertEqual(row['violation_counts']['distal_over_pip20'],3)
        self.assertEqual(row['violation_counts']['pip_straight_distal_bent'],3)
        np.testing.assert_allclose(row['mean_positive_flexion_share'],[0,0,1],atol=1e-15)
        record=dict(full_safe=True,endpoint_samples=3,fingers={f:dict(roles=roles) for f in analysis.FINGERS})
        pooled=analysis.pooled([record]);self.assertEqual(pooled['safe']['endpoint_samples'],3)
        self.assertEqual(pooled['safe']['fingers']['index']['all']['violation_fraction']['distal_over_pip20'],1)
        self.assertIsNone(pooled['failed']['fingers']['index']['idle_full']['standby_quality_mean'])


if __name__=='__main__':unittest.main()
