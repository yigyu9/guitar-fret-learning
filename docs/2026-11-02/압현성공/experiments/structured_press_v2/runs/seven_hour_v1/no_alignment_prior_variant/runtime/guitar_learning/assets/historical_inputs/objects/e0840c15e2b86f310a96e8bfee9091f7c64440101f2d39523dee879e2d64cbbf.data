import json
import math
import tempfile
from pathlib import Path

import numpy as np

from tab2body.env.joint_limits import apply_joint_limit_profile


def _profile(path, joints):
    path.write_text(json.dumps({
        "schema": "tab2body.fret-human-joint-profile.v1",
        "joints": joints,
    }))


def test_profile_narrows_only_named_joint():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "limits.json"
        _profile(path, {"joint_a": {"lower_deg": -30, "upper_deg": 40}})
        lower, upper, audit = apply_joint_limit_profile(
            ["joint_a", "joint_b"],
            np.radians([-90, -20]), np.radians([90, 20]), path)
        assert np.allclose(np.degrees(lower), [-30, -20], atol=1e-4)
        assert np.allclose(np.degrees(upper), [40, 20], atol=1e-4)
        assert audit["applied_joint_count"] == 1


def test_profile_cannot_expand_authored_limit():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "limits.json"
        _profile(path, {"joint_a": {"lower_deg": -100, "upper_deg": 40}})
        try:
            apply_joint_limit_profile(
                ["joint_a"], np.radians([-90]), np.radians([90]), path)
        except ValueError as exc:
            assert "넓힌다" in str(exc)
        else:
            raise AssertionError("expanded hard limit was accepted")


if __name__ == "__main__":
    test_profile_narrows_only_named_joint()
    test_profile_cannot_expand_authored_limit()
    print("joint limit profile tests passed")
