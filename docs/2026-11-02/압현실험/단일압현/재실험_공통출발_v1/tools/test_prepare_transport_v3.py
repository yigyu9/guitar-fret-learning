"""공통 reset·운반 경유점·불변 입력 계약을 CPU에서 확인한다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('common_transport_v3',HERE/'prepare_transport_v3.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
import numpy as np


class TransportTest(unittest.TestCase):
    def test_joint_interpolation_bounds_and_non_arm_preservation(self):
        a=np.zeros(105);b=a.copy();b[[42,48]]=[.31,-.18]
        points=module.joint_path(a,b)
        np.testing.assert_equal(points[0],a);np.testing.assert_equal(points[-1],b)
        self.assertLessEqual(max(np.max(np.abs(y-x)) for x,y in zip(points,points[1:])),np.deg2rad(2)+1e-12)
        for point in points:
            self.assertTrue(np.all(point>=np.minimum(a,b)))
            self.assertTrue(np.all(point<=np.maximum(a,b)))
        with self.assertRaises(ValueError):module.joint_path(np.zeros(104),b)
        with self.assertRaises(ValueError):module.joint_path(a,b,0.)

    def test_input_tampering_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);asset=root/'asset';asset.write_text('original')
            catalog=root/'catalog.json';catalog.write_text('{"goals": []}')
            provenance=root/'provenance.json';provenance.write_text(json.dumps(dict(catalog_sha256=module.sha(catalog),active_physical_inputs={str(asset):module.sha(asset)})))
            module.verify_inputs(catalog,provenance)
            asset.write_text('modified')
            with self.assertRaises(ValueError):module.verify_inputs(catalog,provenance)

    def test_generated_common_start_and_sparse_commands(self):
        paths=list((HERE.parent/'inputs_v3_pinky').glob('*/catalog.json'))
        self.assertTrue(paths,'대표 후보를 먼저 생성해야 한다')
        for path in paths:
            catalog,provenance=module.verify_inputs(path,path.with_name('provenance.json'))
            self.assertFalse(catalog['native_verified'])
            self.assertEqual(len(catalog['goals']),1)
            row=catalog['goals'][0];arm=catalog['action_indices'][:12]
            initial=np.array(row['q105']);fixed=np.setdiff1d(np.arange(105),arm)
            self.assertFalse(row['native_verified'])
            self.assertEqual(row['q105'],catalog['initial_q105'])
            self.assertEqual(row['q105'],[r['pos'] for r in row['state']['human_dof_states']])
            commands=row['transport_waypoints'];dense=row['transport_validation_samples']
            self.assertTrue(2<=len(commands)<=4)
            self.assertGreaterEqual(sum(p['minimum_duration_s'] for p in commands),2.-1e-9)
            self.assertLessEqual(sum(p['minimum_duration_s'] for p in commands),6.+1e-9)
            self.assertEqual(commands[0]['q105'],row['q105'])
            self.assertEqual(commands[-1]['q105'],row['final_hover_q105'])
            for point in commands+dense:
                np.testing.assert_equal(np.array(point['q105'])[fixed],initial[fixed])
                self.assertFalse(point['native_verified'])
            for point in commands:
                self.assertAlmostEqual(np.linalg.norm(point['wrist_quaternion_G_xyzw']),1.,places=8)
            self.assertTrue(all(not p['command_waypoint'] for p in dense))


if __name__=='__main__':unittest.main()
