from isaacgym import gymapi  # noqa: F401

import torch

from tab2body.cfg import FRET
from tab2body.env.config import configured_kwargs
from tab2body.env.tasks.task_fret import FretTask


def main():
    if not torch.cuda.is_available():
        print("SKIP: CUDA is unavailable")
        return
    env = FretTask(**configured_kwargs(
        FretTask, FRET, reward_config=FRET,
        num_envs=8, device="cuda:0", headless=True,
        reset_noise=0.0, random_start=False, preparation_frames=0))
    try:
        env.reset()
        env.set_curriculum_stage(
            "static_chord", duration_frames=30, reset=True)
        for slot in range(env.goals.pose_slot_count):
            env._success_pose_valid[slot] = True
            env._success_pose_quality[slot] = 0.9
            env._success_pose_q[slot] = env._settled_reset_q[0]
            env._success_pose_body_obs[slot] = env._settled_reset_body_obs[0]
            env._success_pose_thumb_obs[slot] = env._settled_reset_thumb_obs[0]
        env.success_rsi_probability = 1.0
        ids = torch.arange(env.num_envs, device=env.device)
        env.reset_idx(ids)
        assert env.success_rsi_reset.all()
        terminal = env.compute_observations()
        reset_obs = env._compose_reset_observation(terminal, ids)
        assert torch.isfinite(reset_obs).all()
        state = env.curriculum_state_dict()
        assert state["success_rsi"]["valid"].all()
        env._success_pose_valid.zero_()
        env.load_curriculum_state_dict(state)
        assert env._success_pose_valid.all()
    finally:
        env.close()
    print("PASS: goal-conditioned success RSI GPU reset")


if __name__ == "__main__":
    main()
