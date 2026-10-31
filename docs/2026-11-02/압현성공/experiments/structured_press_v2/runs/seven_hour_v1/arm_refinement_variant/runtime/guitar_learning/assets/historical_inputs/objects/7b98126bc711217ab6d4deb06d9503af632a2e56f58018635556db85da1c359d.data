"""GPU check for R29 frozen goal clock and metric gating."""
from __future__ import annotations

from pathlib import Path
import sys

import isaacgym  # noqa: F401 -- must precede torch
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cfg import FRET
from env.tasks import FretTask


def main():
    env = FretTask(
        FRET["goal_path"], FRET["hand_targets_path"], num_envs=2,
        device=FRET["device"], headless=True, reset_noise=0.0,
        random_start=False, preparation_frames=60)
    action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
              (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    action = action.repeat(env.num_envs, 1)
    env.reset()
    minimum_finger_z = torch.full((4,), float("inf"), device=env.device)
    maximum_back_fraction = torch.zeros(4, device=env.device)
    for step in range(60):
        _, reward, done, info = env.step(action)
        minimum_finger_z = torch.minimum(
            minimum_finger_z, info["finger_back_min_local_z"].amin(dim=0))
        maximum_back_fraction = torch.maximum(
            maximum_back_fraction,
            info["finger_back_fraction_by_finger"].amax(dim=0))
        assert info["preparing"].all()
        assert not info["goal_metrics_enabled"].any()
        assert (env.goals.frame_idx == 0).all()
        assert torch.isfinite(reward).all() and not done.any(), {
            "step": step,
            "palm": info["palm_down_termination"].tolist(),
            "wrist": info["wrist_safety_termination"].tolist(),
            "finger_back": info["finger_back_termination"].tolist(),
            "finger_back_min_z": info["finger_back_min_local_z"].tolist(),
            "penetration": info["guitar_penetration_termination"].tolist(),
        }
    assert (env.preparation_remaining == 0).all()
    assert (env.metric_total == 0).all()
    _, reward, done, info = env.step(action)
    assert not info["preparing"].any()
    assert info["goal_metrics_enabled"].all()
    assert (env.goals.frame_idx == 1).all()
    assert torch.isfinite(reward).all() and not done.any()
    assert (env.metric_total > 0).all()
    assert (maximum_back_fraction < FRET["finger_back_min_fraction"]).all()
    print("R8 initial-pose minimum local z:", minimum_finger_z.tolist())
    print("R8 initial-pose max fraction behind plane:",
          maximum_back_fraction.tolist())
    env.close()
    print("PASS: R29 60-frame reward-enabled preparation and live metric gate")


if __name__ == "__main__":
    main()
