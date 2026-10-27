"""Independent-reference fixtures only; no native simulation or GL."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
from scipy.spatial.transform import Rotation

SPEC = importlib.util.spec_from_file_location('pose_capture',Path(__file__).with_name('validate_pose_capture.py'))
tool = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(tool)
NAMES = ['human/LH:palm']+['human/LH:'+f+'1' for f in ('index','middle','ring','pinky')]
JOINTS = ['LH:'+f+'1_'+a for f in ('index','middle','ring','pinky') for a in ('x','z')]


class PoseReferenceTests(unittest.TestCase):
    def test_actual_y_rms_max_and_common_world_rotation_cancel(self):
        body = np.zeros((2,1,5,13)); target = np.zeros((2,1,8))
        palm = Rotation.from_rotvec([.2,-.1,.4])
        body[...,0,3:7] = palm.as_quat()
        for frame,angle in enumerate((.3,.4)):
            body[frame,:,1:,3:7] = (palm*Rotation.from_rotvec([0,angle,0])).as_quat()
        result = tool.reference_metrics(body,target,NAMES,JOINTS)
        for k in (tool.KEYS[0],tool.KEYS[2]): np.testing.assert_allclose(result[k],np.sqrt(.125),atol=1e-14)
        for k in (tool.KEYS[1],tool.KEYS[3]): np.testing.assert_allclose(result[k],.4,atol=1e-14)
        for k in tool.KEYS[4:]: np.testing.assert_allclose(result[k],0.,atol=1e-14)

    def test_zero_y_command_uses_target_and_xz_norm(self):
        body = np.zeros((2,1,5,13)); body[...,6] = 1
        target = np.tile([.3,.4],(2,1,4))
        result = tool.reference_metrics(body,target,NAMES,JOINTS)
        for k in tool.KEYS[:2]: np.testing.assert_allclose(result[k],0.)
        for k in tool.KEYS[2:]: np.testing.assert_allclose(result[k],.5,atol=1e-14)


if __name__=='__main__': unittest.main()
