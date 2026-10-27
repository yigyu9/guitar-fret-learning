"""GPU integration check that R7/R8 monitor streaks drive FretTask.done."""
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


def _initial_action(env):
    action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
              (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6))
    return action.clamp(-1.0, 1.0).repeat(env.num_envs, 1)


def _assert_terminates_on_third_step(env, action, info_key):
    for step in range(3):
        _, reward, done, info = env.step(action)
        assert torch.isfinite(reward).all()
        expected = step == 2
        assert bool(info[info_key].item()) == expected, (step, info_key)
        assert bool(done.item()) == expected, (
            step, info_key, bool(info[info_key].item()),
            bool(info["palm_down_termination"].item()),
            bool(info["wrist_safety_termination"].item()),
            bool(info["finger_back_termination"].item()),
            bool(info["guitar_penetration_termination"].item()))


def main():
    env = FretTask(
        FRET["goal_path"], FRET["hand_targets_path"], num_envs=1,
        device=FRET["device"], headless=True, reset_noise=0.0,
        random_start=False, preparation_frames=60,
        palm_down_threshold=-1.0,
        wrist_safety_bounds_min=(-100.0, -100.0, -100.0),
        wrist_safety_bounds_max=(100.0, 100.0, 100.0),
        finger_back_limit_z=-100.0)
    try:
        action = _initial_action(env)
        env.reset()

        # Make only R7 impossible to satisfy. The task must end after its
        # configured three-frame debounce, including during preparation.
        env.wrist_safety_monitor.bounds_min = (10.0, 10.0, 10.0)
        env.wrist_safety_monitor.bounds_max = (11.0, 11.0, 11.0)
        _assert_terminates_on_third_step(
            env, action, "wrist_safety_termination")

        # Automatic reset has run. Restore R7 and make only R8 impossible.
        env.wrist_safety_monitor.bounds_min = (-100.0, -100.0, -100.0)
        env.wrist_safety_monitor.bounds_max = (100.0, 100.0, 100.0)
        env.finger_back_monitor.limit_z = 100.0
        _assert_terminates_on_third_step(
            env, action, "finger_back_termination")
    finally:
        env.close()
    print("PASS: R7 and R8 each drive FretTask.done on frame 3")


if __name__ == "__main__":
    main()
