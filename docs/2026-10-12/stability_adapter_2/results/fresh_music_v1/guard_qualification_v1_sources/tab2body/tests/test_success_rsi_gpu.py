from isaacgym import gymapi  # noqa: F401

import torch

from tab2body.cfg import FRET
from tab2body.env.config import configured_kwargs
from tab2body.env.tasks.task_fret import FRET_POLICY_ACTION_DIM, FretTask


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
        assert env.num_actions == FRET_POLICY_ACTION_DIM == 30
        controlled_names = [
            env.dof_names[index]
            for index in env.ctrl_idx.detach().cpu().tolist()]
        assert controlled_names[0].startswith("L_Shoulder")
        assert not any(name.startswith("L_Thorax")
                       for name in controlled_names)
        env.set_curriculum_stage(
            "static_chord", duration_frames=30, reset=True)
        thorax_indices = env._thorax_dof_indices
        corrupted_thorax = env.init_pose[thorax_indices] + 0.03
        for slot in range(env.goals.pose_slot_count):
            env._success_pose_valid[slot] = True
            env._success_pose_quality[slot] = 0.9
            env._success_pose_q[slot] = env._settled_reset_q[0]
            env._success_pose_q[slot, thorax_indices] = corrupted_thorax
            env._success_pose_body_obs[slot] = env._settled_reset_body_obs[0]
            env._success_pose_thumb_obs[slot] = env._settled_reset_thumb_obs[0]
        env.success_rsi_probability = 1.0
        ids = torch.arange(env.num_envs, device=env.device)
        env.reset_idx(ids)
        assert env.success_rsi_reset.all()
        ds = env.dof_state.view(env.num_envs, env.n_dof, 2)
        expected_thorax = env.init_pose[thorax_indices][None].expand(
            env.num_envs, -1)
        assert torch.allclose(
            ds[:, thorax_indices, 0], expected_thorax, atol=1e-6)
        assert not ds[:, thorax_indices, 1].any()
        assert torch.allclose(
            env.pd_target.view(env.num_envs, env.n_dof)[
                :, thorax_indices],
            expected_thorax, atol=1e-6)
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
