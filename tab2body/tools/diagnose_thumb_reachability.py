"""고정된 손 자세에서 엄지 관절 목표를 병렬 탐색한다."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import isaacgym  # noqa: F401
import torch

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.cfg import FRET
from tab2body.env.tasks import FretTask
from tab2body.learning import ActorCritic


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--goal", default=FRET["goal_path"])
    parser.add_argument("--hand-targets", default=FRET["hand_targets_path"])
    parser.add_argument("--num-envs", type=int, default=512)
    parser.add_argument("--warmup-frames", type=int, default=120)
    parser.add_argument("--settle-frames", type=int, default=60)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    env = FretTask(
        args.goal, args.hand_targets, num_envs=args.num_envs,
        device=FRET["device"], headless=True, seed=FRET["seed"],
        reset_noise=0.0, random_start=False,
        action_alpha=FRET["action_alpha"], action_scale=FRET["action_scale"],
        reset_soft_limit_fraction=FRET["reset_soft_limit_fraction"])
    init_action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
                   (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6))
    model = ActorCritic(
        env.num_obs, env.num_actions, env.value_dim,
        init_std=FRET["policy_init_std"],
        init_mean=init_action.clamp(-1.0, 1.0)).to(env.device)
    checkpoint = torch.load(
        args.checkpoint, map_location=env.device, weights_only=True)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    obs = env.reset()
    action = init_action.clamp(-1.0, 1.0).repeat(env.num_envs, 1)
    with torch.no_grad():
        for _ in range(args.warmup_frames):
            action, _, _ = model.act(obs, deterministic=True)
            obs, _, _, warmup_info = env.step(action)

        thumb_indices = torch.nonzero(
            env._action_finger_ids == 0, as_tuple=False).flatten()
        thumb_names = [
            env.dof_names[int(env.ctrl_idx[index])]
            for index in thumb_indices.cpu().tolist()]
        samples = 2.0 * torch.quasirandom.SobolEngine(
            len(thumb_names), scramble=True, seed=FRET["seed"]
        ).draw(env.num_envs).to(env.device) - 1.0
        samples[0] = action[0, thumb_indices]
        sweep_action = action.clone()
        sweep_action[:, thumb_indices] = samples

        alive = torch.ones(env.num_envs, dtype=torch.bool, device=env.device)
        min_distance = torch.full(
            (env.num_envs,), float("inf"), device=env.device)
        max_geometry = torch.zeros(env.num_envs, device=env.device)
        max_gap_quality = torch.zeros_like(max_geometry)
        geometry_sum = torch.zeros_like(max_geometry)
        valid_steps = torch.zeros_like(max_geometry)
        final_geometry = torch.zeros_like(max_geometry)
        contact = torch.zeros_like(alive)
        support = torch.zeros_like(alive)
        support_frames = torch.zeros_like(max_geometry)
        support_streak = torch.zeros(
            env.num_envs, dtype=torch.long, device=env.device)
        max_support_streak = torch.zeros_like(support_streak)
        penetration = torch.zeros_like(alive)
        finger_back = torch.zeros_like(alive)
        palm_down = torch.zeros_like(alive)
        thumb_overforce = torch.zeros_like(alive)
        wrist_safety = torch.zeros_like(alive)
        failure = torch.zeros_like(alive)
        max_penetration_depth = torch.zeros_like(max_geometry)
        penetration_point = torch.full(
            (env.num_envs,), -1, dtype=torch.long, device=env.device)
        penetration_solid = torch.full_like(penetration_point, -1)
        for _ in range(args.settle_frames):
            obs, _, done, info = env.step(sweep_action)
            valid = alive.clone()
            min_distance = torch.where(
                valid, torch.minimum(min_distance, info["thumb_distance"]),
                min_distance)
            max_geometry = torch.where(
                valid,
                torch.maximum(
                    max_geometry, info["thumb_geometric_support_quality"]),
                max_geometry)
            max_gap_quality = torch.where(
                valid, torch.maximum(max_gap_quality, info["thumb_gap_quality"]),
                max_gap_quality)
            geometry_sum += torch.where(
                valid, info["thumb_geometric_support_quality"],
                torch.zeros_like(max_geometry))
            valid_steps += valid.float()
            final_geometry = torch.where(
                valid, info["thumb_geometric_support_quality"], final_geometry)
            contact |= valid & info["thumb_contact"]
            support |= valid & info["thumb_support"]
            support_frames += (valid & info["thumb_support"]).float()
            support_now = valid & info["thumb_support"]
            support_streak = torch.where(
                support_now, support_streak + 1,
                torch.zeros_like(support_streak))
            max_support_streak = torch.maximum(
                max_support_streak, support_streak)
            deeper = valid & (
                info["guitar_penetration_depth"] > max_penetration_depth)
            max_penetration_depth = torch.where(
                deeper, info["guitar_penetration_depth"],
                max_penetration_depth)
            penetration_point = torch.where(
                deeper, info["guitar_penetration_point"], penetration_point)
            penetration_solid = torch.where(
                deeper, info["guitar_penetration_solid"], penetration_solid)
            penetration |= valid & info["guitar_penetration_termination"]
            finger_back |= valid & info["finger_back_termination"]
            palm_down |= valid & info["palm_down_termination"]
            thumb_overforce |= valid & info["thumb_overforce_termination"]
            wrist_safety |= valid & info["wrist_safety_termination"]
            failure |= valid & info["failure_termination"]
            alive &= ~done

    safe = ~failure
    mean_geometry = geometry_sum / valid_steps.clamp_min(1.0)
    support_rate = support_frames / valid_steps.clamp_min(1.0)
    rank_score = mean_geometry + 2.0 * support_rate + contact.float()
    safe_score = torch.where(
        safe, rank_score, torch.full_like(rank_score, -1.0))
    top = torch.topk(safe_score, k=min(20, env.num_envs)).indices
    rows = []
    for index in top.cpu().tolist():
        rows.append({
            "sample": index,
            "thumb_actions": {
                name: float(value) for name, value in zip(
                    thumb_names, samples[index].detach().cpu().tolist())},
            "min_distance_m": float(min_distance[index]),
            "max_geometric_quality": float(max_geometry[index]),
            "mean_geometric_quality": float(mean_geometry[index]),
            "final_geometric_quality": float(final_geometry[index]),
            "max_gap_quality": float(max_gap_quality[index]),
            "support_rate": float(support_rate[index]),
            "contact": bool(contact[index]),
            "support": bool(support[index]),
            "failure": bool(failure[index]),
        })
    result = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "collision_audit": dict(env.collision_audit),
        "num_samples": env.num_envs,
        "thumb_action_names": thumb_names,
        "baseline_thumb_actions": {
            name: float(value) for name, value in zip(
                thumb_names,
                action[0, thumb_indices].detach().cpu().tolist())},
        "baseline_thumb_distance_m": float(warmup_info["thumb_distance"][0]),
        "baseline_geometric_quality": float(
            warmup_info["thumb_geometric_support_quality"][0]),
        "baseline_contact": bool(warmup_info["thumb_contact"][0]),
        "baseline_support": bool(warmup_info["thumb_support"][0]),
        "safe_samples": int(safe.sum()),
        "contact_samples": int(contact.sum()),
        "support_samples": int(support.sum()),
        "safe_contact_samples": int((safe & contact).sum()),
        "safe_support_samples": int((safe & support).sum()),
        "stable_support_6_samples": int((max_support_streak >= 6).sum()),
        "safe_stable_support_6_samples": int(
            (safe & (max_support_streak >= 6)).sum()),
        "stable_support_12_samples": int((max_support_streak >= 12).sum()),
        "safe_stable_support_12_samples": int(
            (safe & (max_support_streak >= 12)).sum()),
        "support_without_guitar_penetration_samples": int(
            (support & ~penetration).sum()),
        "guitar_penetration_samples": int(penetration.sum()),
        "finger_back_samples": int(finger_back.sum()),
        "palm_down_samples": int(palm_down.sum()),
        "thumb_overforce_samples": int(thumb_overforce.sum()),
        "wrist_safety_samples": int(wrist_safety.sum()),
        "support_failure_reasons": {
            "guitar_penetration": int((support & penetration).sum()),
            "finger_back": int((support & finger_back).sum()),
            "palm_down": int((support & palm_down).sum()),
            "thumb_overforce": int((support & thumb_overforce).sum()),
            "wrist_safety": int((support & wrist_safety).sum()),
        },
        "minimum_distance_m": float(min_distance.min()),
        "maximum_geometric_quality": float(max_geometry.max()),
        "support_penetration_points": [
            int(value) for value in torch.unique(
                penetration_point[support & penetration]).cpu().tolist()],
        "support_penetration_solids": [
            int(value) for value in torch.unique(
                penetration_solid[support & penetration]).cpu().tolist()],
        "maximum_support_penetration_depth_m": float(
            max_penetration_depth[support].max()) if support.any() else 0.0,
        "best_safe_samples": rows,
    }
    env.close()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
