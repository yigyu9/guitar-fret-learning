from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_right_hand_motion_profile import build_motion_profile


def main():
    document = {
        "schema": "tab2body.right_hand_reference_motion.v1",
        "source_kind": "retargeted_human",
        "frames": [
            {
                "phase": "READY",
                "gesture": "single_pick",
                "confidence": 1.0,
                "joint_positions_rad": {
                    "R_Wrist_x": value,
                    "RH:index2": 0.5 + value,
                },
            }
            for value in (0.0, 0.1, 0.2)
        ],
    }
    profile = build_motion_profile(document, "abc")
    ready = profile["profiles"]["single_pick:READY"]
    assert ready["frames"] == 3
    assert ready["joints"]["R_Wrist_x"]["median_rad"] == 0.1
    assert profile["source_kind"] == "retargeted_human"
    print("PASS: right-hand motion profile schema and quantiles")


if __name__ == "__main__":
    main()
