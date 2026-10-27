"""Verify moving contact regions against the saved horizontal pose; no physics."""
import argparse
import hashlib
import json
from pathlib import Path
import unittest
import numpy as np
from scipy.spatial.transform import Rotation
from .underneck_contact_targets import moving_regions

ROOT = Path(__file__).resolve().parents[1]
POSE = ROOT/'docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/pose.json'
GEOMETRY = ROOT/'docs/2026-10-12/visualizations/grip_proposal/geometry.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=False)
    inputs = [POSE, GEOMETRY, Path(__file__).resolve(),
              ROOT/'stability_adapter_2/underneck_contact_targets.py',
              ROOT/'stability_adapter_2/tests/test_underneck_contact_targets.py',
              ROOT/'stability_adapter_2/LEFT_UNDERNECK_CONTACT_PLAN.md']
    hashes = {str(p): sha(p) for p in inputs}
    (out/'attempt.json').write_text(json.dumps({'input_sha256': hashes}, indent=2)+'\n')
    pose = json.loads(POSE.read_text())
    geometry = json.loads(GEOMETRY.read_text())
    regions = moving_regions(pose['position_W_m'], pose['quaternion_xyzw'], geometry['regions_G_m'])
    rotation = Rotation.from_quat(pose['quaternion_xyzw'])
    checks = {
        'neck_horizontal': abs(rotation.apply([0, 1, 0])[2]) < 1e-12,
        'strings_face_world_positive_Y': np.allclose(rotation.apply([0, 0, 1]), [0, 1, 0], atol=1e-12),
        'palm_target_faces_up': regions['palm']['desired_hand_normal_W'][2] > .99,
        'thumb_rear_front_opposed': np.allclose(regions['thumb']['outward_normal_W'], -regions['front']['outward_normal_W'], atol=1e-12)}
    suite = unittest.defaultTestLoader.loadTestsFromName('stability_adapter_2.tests.test_underneck_contact_targets')
    with (out/'tests.log').open('w') as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    checks['unit_tests_pass'] = result.wasSuccessful() and result.testsRun == 5
    checks['inputs_unchanged'] = all(sha(Path(p)) == h for p, h in hashes.items())
    checks = {key: bool(value) for key, value in checks.items()}
    serial = {role: {k: v.tolist() for k, v in row.items()} for role, row in regions.items()}
    report = {'scope': 'illustrative moving surface goals, not hand placement or PhysX contact',
              'position_W_m': pose['position_W_m'], 'quaternion_xyzw': pose['quaternion_xyzw'],
              'regions_W': serial, 'regions_G_m': geometry['regions_G_m'],
              'checks': checks, 'tests_run': result.testsRun, 'input_sha256': hashes,
              'native_initializations': 0, 'physics_steps': 0,
              'new_hand_pose_configured': False, 'contact_controller_implemented': False}
    (out/'verification.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'checks': checks, 'tests_run': result.testsRun}, indent=2))
    if not all(checks.values()):
        raise AssertionError(checks)


if __name__ == '__main__':
    main()
