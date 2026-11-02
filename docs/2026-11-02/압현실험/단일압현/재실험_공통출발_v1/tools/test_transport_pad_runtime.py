"""고정 패드 점의 Jacobian·표본 매핑·실행 봉인을 CPU로 확인한다."""
import os
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import numpy as np
from scipy.spatial.transform import Rotation
import torch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pad_transport_tested',HERE/'transport_pad_runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)


class PadFeedbackTest(unittest.TestCase):
    def test_point_jacobian_matches_rigid_offset_finite_difference(self):
        rng=np.random.RandomState(17)
        linear=rng.normal(size=(3,12));angular=rng.normal(size=(3,12))
        offset=np.array([.025,-.04,.03]);direction=rng.normal(size=12)
        old=np.vstack((linear,.1*angular))
        _,jac=runtime.replace_point_feedback(torch.zeros(1,6,dtype=torch.float64),
            torch.tensor(old)[None],torch.tensor(offset)[None],torch.zeros(1,3,dtype=torch.float64),torch.tensor([False]))
        epsilon=1e-7
        displacement=epsilon*(linear@direction)+(Rotation.from_rotvec(epsilon*(angular@direction)).apply(offset)-offset)
        np.testing.assert_allclose(jac[0,:3].numpy()@direction,displacement/epsilon,rtol=1e-6,atol=1e-6)
        np.testing.assert_allclose(jac[0,3:].numpy(),.01*angular,atol=1e-12)

    def test_orientation_scale_and_reset_rows(self):
        error=torch.ones(2,6);jac=torch.ones(2,6,12);offset=torch.zeros(2,3)
        changed,changed_jac=runtime.replace_point_feedback(error,jac,offset,torch.full((2,3),2.),torch.tensor([False,True]))
        torch.testing.assert_close(changed[0,:3],torch.full((3,),2.))
        torch.testing.assert_close(changed[0,3:],torch.full((3,),.1))
        self.assertFalse(bool(changed[1].any()));self.assertFalse(bool(changed_jac[1].any()))

    def test_actual_pad_mapping_and_pre_pin_metadata(self):
        folder=HERE.parent/'inputs_v2/middle_s3_f12'
        catalog,row,_=runtime.base.load_inputs(folder/'catalog.json',folder/'provenance.json','middle_s3_f12')
        point=runtime.point_specification(catalog,row)
        from guitar_learning.gpu.contact import load_fingertip_pad
        pad=load_fingertip_pad();ids=np.flatnonzero(pad['valid'][point['finger_id']-1])
        self.assertEqual(int(ids[point['selected_compact_valid_index']]),point['selected_full_sample_index'])
        self.assertEqual(point['body_name'],'LH:middle3')
        original=runtime.base.wrist_error_and_jacobian
        with tempfile.TemporaryDirectory() as directory:
            with runtime.pad_runtime(catalog,row) as contract:
                settings=Path(directory)/'settings.json'
                runtime.base.write(settings,dict(condition='C',runtime_sha256='base'))
                value=json.loads(settings.read_text())
                self.assertEqual(value['condition'],'D')
                self.assertEqual(value['schema'],runtime.SCHEMA)
                self.assertFalse(value['feedback']['policy_press_feedback'])
                self.assertEqual(value['feedback']['orientation_scale_m_per_rad'],.01)
                _,_,pins=runtime.base.load_inputs(folder/'catalog.json',folder/'provenance.json','middle_s3_f12')
                self.assertEqual(pins[str(HERE/'transport_pad_runtime.py')],runtime.digest(HERE/'transport_pad_runtime.py'))
                self.assertEqual(pins[str(HERE/'transport_runtime.py')],runtime.BASE_SHA256)
            self.assertIs(runtime.base.wrist_error_and_jacobian,original)

    def test_base_hash_mismatch_is_rejected(self):
        with mock.patch.object(runtime,'digest',return_value='incorrect'):
            with self.assertRaises(ValueError):runtime.load_base()


if __name__=='__main__':unittest.main()
