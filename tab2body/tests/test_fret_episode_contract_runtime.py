"""GPU integration checks for FretTask termination and auto-reset contracts."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

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


def _assert_reset_observation(env, obs):
    """The policy-facing observation must describe the already-reset episode."""
    ds = env.dof_state.view(env.num_envs, env.n_dof, 2)
    n = env.n_nonlocked
    assert torch.allclose(obs[:, :n], ds[:, env.nonlocked_idx, 0])
    assert torch.allclose(obs[:, n:2 * n], ds[:, env.nonlocked_idx, 1])
    assert torch.allclose(ds[:, :, 0], env._settled_reset_q, atol=2e-6)
    assert torch.allclose(obs[:, 2 * n:env.base_obs_dim],
                          env._settled_reset_body_obs)
    goal_end = env.base_obs_dim + env.goal_dim
    assert torch.allclose(
        obs[:, env.base_obs_dim:goal_end],
        env.goals.observe(env.preparation_remaining))
    action_end = goal_end + env.actuator_obs_dim
    assert action_end == env.thumb_obs_start
    assert torch.allclose(obs[:, goal_end:action_end], env.prev_action)
    thumb_end = env.thumb_obs_start + env.thumb_obs_dim
    assert thumb_end == env.future_context_obs_start
    assert torch.allclose(
        obs[:, env.thumb_obs_start:thumb_end],
        env._settled_reset_thumb_obs)
    assert torch.allclose(
        obs[:, env.future_context_obs_start:],
        env.goals.observe_future_context(
            env.future_context_lookahead,
            env.preparation_remaining))
    assert (env.goals.frame_idx == 0).all()
    assert (env.preparation_remaining == env.preparation_frames).all()


def _write_minimal_goal(path):
    frames = []
    for frame in range(4):
        frames.append({
            "frame": frame,
            "t": frame / 60.0,
            "fret_goal": [0, 0, 0, 0, 0, 0],
            "finger_goal": [0, 0, 0, 0, 0, 0],
            "barre_goal": [False, False, False, False, False, False],
            "hand_anchor_fret": 1,
            "hand_allowed_fret_range": [1, 4],
        })
    Path(path).write_text(json.dumps({
        "schema": "tab2body.fret_training.v1",
        "metadata": {"fps": 60},
        "frames": frames,
    }))


def _make_env(goal_path, num_envs=1, preparation_frames=60, reset_noise=0.0):
    return FretTask(
        goal_path, None, num_envs=num_envs,
        device=FRET["device"], headless=True, reset_noise=reset_noise,
        random_start=False, preparation_frames=preparation_frames,
        palm_down_threshold=-1.0,
        wrist_safety_bounds_min=(-100.0, -100.0, -100.0),
        wrist_safety_bounds_max=(100.0, 100.0, 100.0),
        finger_back_limit_z=-100.0)


def main():
    with tempfile.TemporaryDirectory(prefix="fret_episode_contract_") as tmp:
        goal_path = Path(tmp) / "minimal_goal.json"
        _write_minimal_goal(goal_path)
        env = _make_env(goal_path)
        try:
            action = _initial_action(env)
            env.reset()

            # Failure: R7 ends the episode, broadcasts M2=-25 and preserves the
            # terminal observation separately from the reset next observation.
            env.goals.frame_idx.fill_(1)
            env.wrist_safety_monitor.bounds_min = (10.0, 10.0, 10.0)
            env.wrist_safety_monitor.bounds_max = (11.0, 11.0, 11.0)
            for step in range(env.wrist_safety_monitor.frames):
                obs, reward, done, info = env.step(action)
            assert done.item() and info["failure_termination"].item()
            assert info["wrist_safety_termination"].item()
            assert not info["goal_finished"].item()
            assert torch.equal(reward, torch.full_like(reward, -25.0))
            assert info["episode_failure_termination"].tolist() == [True]
            assert info["episode_goal_finished"].tolist() == [False]
            assert info["terminal_observation"].shape == (1, env.num_obs)
            phase_idx = env.base_obs_dim + env.goal_dim - 1
            terminal_phase = info["terminal_observation"][0, phase_idx]
            assert terminal_phase > 0.0
            assert obs[0, phase_idx] == 0.0
            _assert_reset_observation(env, obs)

            # Success: the final goal frame is evaluated, but normal completion is
            # not overwritten by the failure penalty.
            env.wrist_safety_monitor.bounds_min = (-100.0, -100.0, -100.0)
            env.wrist_safety_monitor.bounds_max = (100.0, 100.0, 100.0)
            env.max_episode_length = 1
            env.preparation_remaining.zero_()
            env.goals.frame_idx.fill_(env.goals.n_frames - 1)
            obs, reward, done, info = env.step(action)
            assert done.item() and info["goal_finished"].item()
            assert info["timeout"].item()
            assert not info["early_timeout"].item()
            assert info["normal_termination"].item()
            assert info["successful_termination"].item()
            assert not info["failure_termination"].item()
            assert not torch.equal(reward, torch.full_like(reward, -25.0))
            assert info["episode_success"].tolist() == [True]
            _assert_reset_observation(env, obs)

            # A time limit before the final goal is a failure, while remaining
            # distinguishable from a task-safety termination for diagnostics.
            env.preparation_remaining.zero_()
            obs, reward, done, info = env.step(action)
            assert done.item() and info["timeout"].item()
            assert not info["goal_finished"].item()
            assert info["early_timeout"].item()
            assert not info["normal_termination"].item()
            assert info["failure_termination"].item()
            assert torch.equal(reward, torch.full_like(reward, -25.0))
            assert info["episode_timeout"].tolist() == [True]
            assert info["episode_early_timeout"].tolist() == [True]
            assert info["episode_success"].tolist() == [False]
            _assert_reset_observation(env, obs)

            # Invalid policy output is latched as a failure, never reaches PhysX,
            # and cannot leak a non-finite reward/next observation into PPO.
            env.max_episode_length = env.goals.n_frames + env.preparation_frames
            bad_action = action.clone()
            bad_action[0, 0] = float("nan")
            obs, reward, done, info = env.step(bad_action)
            assert done.item() and info["nonfinite"].item()
            assert info["nonfinite_action_state"].item()
            assert info["failure_termination"].item()
            assert torch.equal(reward, torch.full_like(reward, -25.0))
            assert torch.isfinite(obs).all()
            _assert_reset_observation(env, obs)
        finally:
            env.close()

        # A partial reset must not rewind or replace a still-live neighbour.
        env = _make_env(
            goal_path, num_envs=2, preparation_frames=0, reset_noise=0.02)
        try:
            action = _initial_action(env)
            env.reset()
            thumb_reward = env.reward_fn.thumb_reward
            thumb_reward._contact[:] = True
            thumb_reward.contact_off_force = -1.0
            env.goals.frame_idx[:] = torch.tensor(
                [env.goals.n_frames - 1, 0], device=env.device)
            obs, _, done, info = env.step(action)
            assert done.tolist() == [True, False]
            assert info["terminal_env_ids"].tolist() == [0]
            assert info["thumb_contact"].tolist() == [True, True]
            assert thumb_reward._contact.tolist() == [False, True]
            assert (info["thumb_contact"].data_ptr()
                    != thumb_reward._contact.data_ptr())
            assert env.goals.frame_idx.tolist() == [0, 1]
            assert env.progress_buf.tolist() == [0, 1]
            n = env.n_nonlocked
            ds = env.dof_state.view(env.num_envs, env.n_dof, 2)
            assert torch.allclose(obs[0, :n], ds[0, env.nonlocked_idx, 0])
            assert torch.allclose(obs[0, 2 * n:env.base_obs_dim],
                                  env._settled_reset_body_obs[0])
            current = env.compute_observations()
            assert torch.allclose(obs[1], current[1])
        finally:
            env.close()
    print("PASS: failure penalty, named reasons, terminal obs and auto-reset next obs")


if __name__ == "__main__":
    main()
