"""학습된 fret 정책의 deterministic 전체 곡 close-up rollout을 MP4로 기록한다.

Isaac Gym은 torch보다 먼저 import해야 한다. 예:
  python -m tab2body.tools.record_fret_rollout \
    --checkpoint fret/training/runs/jazz1_pilot/checkpoints/fret_002000.pt \
    --audio data/song_bundles/02_Jazz1-200-B_solo/source/audio.wav
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
LOCAL_ISAACGYM_PYTHON = PROJECT_ROOT / "isaacgym" / "python"
if (LOCAL_ISAACGYM_PYTHON / "isaacgym" / "__init__.py").is_file():
    sys.path.insert(0, str(LOCAL_ISAACGYM_PYTHON))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import isaacgym  # noqa: F401
from isaacgym import gymapi, gymtorch
import torch

from tab2body.cfg import FRET
from tab2body.fret_v2_contract import FRET_V2_BLOCK_SLICES
from tab2body.env.config import configured_kwargs
from tab2body.env.metrics import (
    adjacent_finger_motion_correlations,
    summarize_joint_trajectory,
)
from tab2body.env.tasks import FretTask
from tab2body.learning.fret_v2_model import fret_actor_critic_class
from tab2body.learning.checkpoint_contract import canonical_sha256, file_sha256
from tab2body.learning.run_layout import default_video_path
from tab2body.tools.fret_rollout_contract import (
    EventEvidence, rollout_configuration, verify_rollout_model,
)
from tab2body.tools.fretboard_visualization import (
    CameraSpec,
    camera_from_guitar,
    draw_fretboard_overlay,
)


def scale_camera_distance(camera, scale):
    """Keep the framing direction and pull the camera away from its target."""
    if scale <= 0.0:
        raise ValueError("camera distance scale must be positive")
    eye = torch.tensor(camera.eye, dtype=torch.float64)
    target = torch.tensor(camera.target, dtype=torch.float64)
    pulled_eye = target + scale * (eye - target)
    return CameraSpec(
        tuple(float(x) for x in pulled_eye), camera.target,
        camera.width, camera.height, camera.horizontal_fov_deg)


def upper_body_camera(env, width, height, horizontal_fov_deg=55.0):
    """Pull the familiar guitar camera back to include pelvis, head and both arms."""
    points = torch.stack([
        env.hbody_pos("Pelvis")[0], env.hbody_pos("Head")[0],
        env.hbody_pos("L_Wrist")[0], env.hbody_pos("R_Wrist")[0],
        env.gbody_pos("G:fret12")[0],
    ]).detach().cpu()
    center = points.mean(dim=0)
    close = camera_from_guitar(env, width, height, horizontal_fov_deg)
    view = torch.tensor(close.eye) - torch.tensor(close.target)
    view = view / view.norm().clamp_min(1e-8)
    radius = (points - center).norm(dim=-1).max().item()
    vertical_fov = 2.0 * math.atan(
        (height / width) * math.tan(math.radians(horizontal_fov_deg) / 2.0))
    half_fov = min(math.radians(horizontal_fov_deg) / 2.0, vertical_fov / 2.0)
    distance = 1.35 * radius / max(math.sin(half_fov), 1e-8)
    eye = center + distance * view
    return CameraSpec(tuple(float(x) for x in eye), tuple(float(x) for x in center),
                      width, height, horizontal_fov_deg)


def parser():
    ap = argparse.ArgumentParser(description="record a trained fret policy")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--action-mode", choices=("mean", "sample"), default="mean")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--start-frame", type=int, default=0,
                    help="진단용 시작 song frame; 이후 원래 곡 순서를 유지")
    ap.add_argument("--initial-pose", choices=("default", "cached"), default="default")
    ap.add_argument("--hold-preparation-pose", action="store_true",
                    help="진단용: 준비 중 정책 대신 초기 PD 목표를 유지")
    ap.add_argument("--cached-preparation-action", action="store_true",
                    help="캐시 자세에서 준비 중 저장된 EMA 상태와 행동을 함께 복원")
    ap.add_argument("--restore-source-state", action="store_true",
                    help="출처가 있는 캐시의 전체 q/속도/root/PD를 진단 환경에 복원")
    ap.add_argument("--diagnostic-probe", action="store_true",
                    help="최고 캐시 대신 별도 저장한 최초 전체목표 성공 표본 사용")
    ap.add_argument("--extra-preparation-frames", type=int, default=0,
                    help="진단용 추가 접근 시간; 60 frame = 1초")
    ap.add_argument("--goal", default=FRET["goal_path"])
    ap.add_argument("--hand-targets", default=FRET["hand_targets_path"])
    ap.add_argument("--audio", default=None)
    ap.add_argument("--out", default=None,
                    help="기본값: 해당 run의 videos/<checkpoint>_rollout.mp4")
    ap.add_argument("--device", default=FRET["device"])
    ap.add_argument("--fps", type=int, default=30, choices=(30, 60))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--show-frets", action="store_true",
                    help="overlay actual fret wires, x=20%% target and position quality bands")
    ap.add_argument("--max-fret", type=int, default=12)
    ap.add_argument("--view", choices=("closeup", "upper-body"), default="closeup",
                    help="upper-body includes the torso, head and both arms for stability review")
    ap.add_argument("--camera-distance-scale", type=float, default=1.0,
                    help="1보다 크면 같은 구도를 유지하며 카메라를 뒤로 이동")
    ap.add_argument("--preparation-seconds", type=float,
                    default=None, help="기본값: checkpoint에 저장된 준비 시간")
    ap.add_argument(
        "--no-human-hard-limits", action="store_true",
        help="원본 XML 관절 범위로 렌더링")
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    if args.restore_source_state and not args.cached_preparation_action:
        raise ValueError("source-state restore requires cached-preparation-action")
    if args.diagnostic_probe and not args.restore_source_state:
        raise ValueError("diagnostic-probe requires restore-source-state")
    if args.cached_preparation_action and (
            args.initial_pose != "cached" or args.hold_preparation_pose):
        raise ValueError("cached preparation action requires cached pose and no hold-preparation-pose")
    if args.start_frame < 0 or args.extra_preparation_frames < 0:
        raise ValueError("diagnostic frame counts must be non-negative")
    diagnostic = (args.start_frame != 0 or args.initial_pose != "default"
                  or args.extra_preparation_frames != 0 or args.hold_preparation_pose)
    if diagnostic and args.audio:
        raise ValueError("segment diagnostics do not support audio alignment")
    if 60 % args.fps:
        raise ValueError("fps must divide the 60 Hz simulation clock")
    if args.preparation_seconds is not None and args.preparation_seconds < 0.0:
        raise ValueError("preparation seconds must be non-negative")
    if args.camera_distance_scale <= 0.0:
        raise ValueError("camera distance scale must be positive")
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    config, payload = rollout_configuration(
        checkpoint, FRET, goal=args.goal, hand_targets=args.hand_targets or None,
        root=PACKAGE_ROOT)
    implementation_changes = [
        entry["path"]
        for entry in payload["fingerprints"]["implementation"]["manifest"]
        if not (PACKAGE_ROOT / entry["path"]).is_file()
        or file_sha256(PACKAGE_ROOT / entry["path"]) != entry["sha256"]]
    preparation_frames = config["preparation_frames"]
    if args.preparation_seconds is not None:
        requested_frames = int(round(args.preparation_seconds * 60.0))
        if requested_frames != preparation_frames:
            raise ValueError("preparation time differs from checkpoint contract")
    if args.no_human_hard_limits and config["human_hard_limits_enabled"]:
        raise ValueError("cannot disable hard limits saved in checkpoint contract")

    evaluation_seed = config["seed"] if args.seed is None else args.seed
    torch.manual_seed(evaluation_seed)
    env = FretTask(**configured_kwargs(
        FretTask, config,
        reward_config=config,
        goal_path=args.goal,
        hand_targets_path=args.hand_targets or None,
        num_envs=1,
        device=args.device,
        headless=True,
        seed=evaluation_seed,
        reset_noise=0.0,
        human_hard_limits_enabled=(
            config["human_hard_limits_enabled"]
            and not args.no_human_hard_limits),
        random_start=False,
        preparation_frames=preparation_frames,
    ))
    init_action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
                   (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    try:
        ModelType = fret_actor_critic_class(env.observation_contract)
        model = ModelType(env.num_obs, env.num_actions, env.value_dim,
                         init_std=payload["model"]["policy_init_std"],
                         init_mean=init_action).to(args.device)
        verify_rollout_model(env, model, payload)
        model.load_state_dict(checkpoint["model"])
    except Exception:
        env.close()
        raise
    model.eval()

    if args.start_frame >= env.goals.n_frames:
        env.close()
        raise ValueError("start frame is outside the song")
    original_pose = env.init_pose.clone()
    original_reset_lo = env.reset_ctrl_lo.clone()
    original_reset_hi = env.reset_ctrl_hi.clone()
    cache_slot = None
    if args.initial_pose == "cached":
        cache_slot = int(env.goals.frame_pose_slot[args.start_frame].item())
        cache = (checkpoint.get("environment_state") or {}).get("success_rsi", {})
        if args.diagnostic_probe:
            cache = deepcopy(cache)
            probe = cache.get("diagnostic_probes", {}).get(str(cache_slot))
            if probe is None:
                env.close()
                raise ValueError("no diagnostic success probe for target")
            cache["q"][cache_slot] = torch.tensor(probe["q"])
            cache["action"][cache_slot] = torch.tensor(probe["action"])
            cache["valid"][cache_slot] = True
            cache.setdefault("source_metadata", {})[str(cache_slot)] = probe["metadata"]
        if cache_slot < 0 or "valid" not in cache or not bool(cache["valid"][cache_slot]):
            env.close()
            raise ValueError("no successful cached pose for this target")
        cached_q = cache["q"][cache_slot].to(env.device)
        if cached_q.shape != env.init_pose.shape or not torch.isfinite(cached_q).all():
            env.close()
            raise ValueError("invalid cached pose")
        env.init_pose[env.ctrl_idx] = cached_q[env.ctrl_idx]
        env.reset_ctrl_lo.copy_(env.dof_lower.view(1, env.n_dof)[:, env.ctrl_idx])
        env.reset_ctrl_hi.copy_(env.dof_upper.view(1, env.n_dof)[:, env.ctrl_idx])
    try:
        obs = env.reset()
    finally:
        env.init_pose.copy_(original_pose)
        env.reset_ctrl_lo.copy_(original_reset_lo)
        env.reset_ctrl_hi.copy_(original_reset_hi)
    if diagnostic:
        reset_obs = obs.clone()
        env.goals.frame_idx[:] = args.start_frame
        env.preparation_frames += args.extra_preparation_frames
        env.max_episode_length += args.extra_preparation_frames
        env.preparation_remaining[:] = env.preparation_frames
        obs = env.compute_observations()
        if hasattr(env, "_settled_reset_v2_blocks"):
            for name in ("O_arm_anchor", "O_hand_geometry"):
                obs[:, FRET_V2_BLOCK_SLICES[name]] = reset_obs[:, FRET_V2_BLOCK_SLICES[name]]
            env.obs_buf.copy_(obs)
    if args.restore_source_state:
        metadata = cache.get("source_metadata", {}).get(str(cache_slot))
        if not metadata or metadata["source_frame"] != args.start_frame:
            env.close()
            raise ValueError("source metadata missing or start frame does not match")
        if metadata["effective_active"] != [x > 0 for x in metadata["source_fret"]]:
            env.close()
            raise ValueError("source target was masked; full-context replay is not equivalent")
        roots = torch.tensor(metadata["actor_root_state"], device=env.device)
        target_roots = env.root_state.view(1, -1, 13)[0]
        if roots.shape != target_roots.shape or not torch.isfinite(roots).all():
            env.close()
            raise ValueError("source root state mismatch")
        roots[:, :3] += target_roots[1, :3] - roots[1, :3].clone()
        target_roots.copy_(roots)
        ds = env.dof_state.view(1, env.n_dof, 2)
        ds[0, :, 0] = cached_q
        ds[0, :, 1] = torch.tensor(metadata["dof_velocity"], device=env.device)
        env.pd_target.view(1, env.n_dof)[0] = torch.tensor(metadata["pd_target"], device=env.device)
        env.prev_action[0] = cache["action"][cache_slot].to(env.device)
        env.gym.set_actor_root_state_tensor(env.sim, gymtorch.unwrap_tensor(env.root_state))
        env.gym.set_dof_state_tensor(env.sim, gymtorch.unwrap_tensor(env.dof_state))
        # PhysX는 상태 대입만으로 link transform을 갱신하지 않는다.
        env.step_physics()
        env.refresh()
        obs = env.compute_observations()
    cp = gymapi.CameraProperties()
    cp.width, cp.height = args.width, args.height
    cp.horizontal_fov = 55.0
    camera = env.gym.create_camera_sensor(env.envs[0], cp)
    camera_spec = (upper_body_camera(env, args.width, args.height, cp.horizontal_fov)
                   if args.view == "upper-body" else
                   camera_from_guitar(env, args.width, args.height, cp.horizontal_fov))
    camera_spec = scale_camera_distance(camera_spec, args.camera_distance_scale)
    env.gym.set_camera_location(camera, env.envs[0],
                                gymapi.Vec3(*camera_spec.eye), gymapi.Vec3(*camera_spec.target))

    out = (Path(args.out).resolve() if args.out else
           default_video_path(args.checkpoint))
    if args.out is None and (args.action_mode != "mean" or args.seed is not None):
        out = out.with_name(f"{out.stem}_{args.action_mode}_seed{evaluation_seed}{out.suffix}")
    if args.out is None and diagnostic:
        out = out.with_name(f"{out.stem}_from{args.start_frame}_{args.initial_pose}"
                            f"_extra{args.extra_preparation_frames}{out.suffix}")
        if args.hold_preparation_pose:
            out = out.with_name(f"{out.stem}_holdprep{out.suffix}")
        if args.cached_preparation_action:
            out = out.with_name(f"{out.stem}_cacheaction{out.suffix}")
        if args.restore_source_state:
            out = out.with_name(f"{out.stem}_source{out.suffix}")
        if args.diagnostic_probe:
            out = out.with_name(f"{out.stem}_probe{out.suffix}")
    out.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = out.with_suffix("") / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    stride = 60 // args.fps
    written = 0
    controlled_joint_names = [
        env.dof_names[index]
        for index in env.ctrl_idx.detach().cpu().tolist()]
    if len(controlled_joint_names) != 30:
        raise RuntimeError(
            "fret rollout requires the 30-DOF shoulder-to-fingertip contract; "
            f"got {len(controlled_joint_names)} controlled DOFs")
    controlled_thorax = [
        name for name in controlled_joint_names
        if name.startswith("L_Thorax")]
    if controlled_thorax:
        raise RuntimeError(
            "L_Thorax must remain held outside fret policy control: "
            f"{controlled_thorax}")
    torso_prefixes = ("Torso", "Spine", "Chest", "Neck", "Head")
    right_prefixes = ("R_Thorax", "R_Shoulder", "R_Elbow", "R_Wrist", "RH:")
    groups = {
        "torso_head_noncontrolled": torch.tensor(
            [i for i, name in enumerate(env.dof_names)
             if name.startswith(torso_prefixes)], device=env.device),
        "right_side_noncontrolled": torch.tensor(
            [i for i, name in enumerate(env.dof_names)
             if name.startswith(right_prefixes)], device=env.device),
        "left_thorax_noncontrolled": torch.tensor(
            [i for i, name in enumerate(env.dof_names)
             if name.startswith("L_Thorax")], device=env.device),
    }
    group_max = {name: 0.0 for name in groups}
    group_sum_sq = {name: 0.0 for name in groups}
    group_samples = {name: 0 for name in groups}
    tracked_bodies = ("Torso", "Chest", "Head", "R_Wrist")
    body_initial = {name: env.hbody_pos(name)[0].detach().clone()
                    for name in tracked_bodies}
    body_max_drift = {name: 0.0 for name in tracked_bodies}
    reset_count = 0
    diagnostic_frames = 0
    thumb_distance_sum = 0.0
    thumb_support_frames = 0
    thumb_wrong_contact_frames = 0
    synergy_active_sum = 0.0
    synergy_induced_sum = 0.0
    finger_back_soft_sum = 0.0
    min_finger_local_z = float("inf")
    min_finger_proximal_local_z = float("inf")
    min_finger_distal_local_z = float("inf")
    controlled_lower = env.ctrl_lo[0].detach().cpu()
    controlled_upper = env.ctrl_hi[0].detach().cpu()
    finger_flexion_indices = torch.tensor([
        [env.dof_names.index(f"LH:{finger}1_x"),
         env.dof_names.index(f"LH:{finger}2"),
         env.dof_names.index(f"LH:{finger}3")]
        for finger in ("index", "middle", "ring", "pinky")
    ], dtype=torch.long, device=env.device)
    controlled_joint_samples = []
    finger_flexion_samples = []
    event_evidence = EventEvidence()
    completed = False
    termination_reasons = []
    episode_metrics = {}

    def sample_stability():
        dof_pos = env.dof_state.view(env.num_envs, env.n_dof, 2)[0, :, 0]
        error = dof_pos - env.init_pose
        for name, indices in groups.items():
            values = error[indices]
            group_max[name] = max(group_max[name], float(values.abs().max().cpu()))
            group_sum_sq[name] += float(values.square().sum().cpu())
            group_samples[name] += int(values.numel())
        for name in tracked_bodies:
            drift = (env.hbody_pos(name)[0] - body_initial[name]).norm()
            body_max_drift[name] = max(body_max_drift[name], float(drift.cpu()))
    preparation_trace = []
    reset_q = env.dof_state.view(env.num_envs, env.n_dof, 2)[0, :, 0].clone()
    hold_action = env.actions_for_pd_targets(reset_q[env.ctrl_idx][None])
    cached_action = None
    if args.cached_preparation_action:
        cached_action = cache["action"][cache_slot].to(env.device)[None]
        if (cached_action.shape != hold_action.shape
                or not torch.isfinite(cached_action).all()
                or (cached_action.abs() > 1.00001).any()):
            env.close()
            raise ValueError("invalid cached EMA action")
    cache_reset_error_deg = (float(torch.rad2deg(
        (reset_q[env.ctrl_idx] - cached_q[env.ctrl_idx]).abs().max()).item())
        if args.initial_pose == "cached" else None)
    cache_restore_audit = None
    if args.initial_pose == "cached":
        controlled = set(env.ctrl_idx.cpu().tolist())
        cache_restore_audit = {
            "available_fields": sorted(cache),
            "source_metadata": cache.get("source_metadata", {}).get(str(cache_slot)),
            "joint_differences": [
                {"name": name, "controlled": i in controlled,
                 "cached_rad": float(cached_q[i].item()),
                 "reset_rad": float(reset_q[i].item()),
                 "difference_deg": float(torch.rad2deg(reset_q[i] - cached_q[i]).item())}
                for i, name in enumerate(env.dof_names)],
        }
    try:
        total_sim_frames = env.preparation_frames + env.goals.n_frames - args.start_frame
        for sim_frame in range(total_sim_frames):
            sample_stability()
            if int(env.preparation_remaining[0].item()) == 0:
                dof_position = env.dof_state.view(
                    env.num_envs, env.n_dof, 2)[0, :, 0]
                controlled_joint_samples.append(
                    dof_position[env.ctrl_idx].detach().cpu())
                finger_flexion_samples.append(
                    dof_position[finger_flexion_indices].detach().cpu())
            if sim_frame % stride == 0:
                env.gym.step_graphics(env.sim)
                env.gym.render_all_camera_sensors(env.sim)
                env.gym.write_camera_image_to_file(
                    env.sim, env.envs[0], camera, gymapi.IMAGE_COLOR,
                    str(frames_dir / f"{written:05d}.png"))
                if args.show_frets:
                    active = env.goals.current()["fret"][0]
                    active = active[active > 0].detach().cpu().tolist()
                    draw_fretboard_overlay(frames_dir / f"{written:05d}.png", env,
                                           camera_spec, max_fret=args.max_fret,
                                           active_frets=active)
                written += 1
            with torch.no_grad():
                action, _, _ = model.act(obs, deterministic=args.action_mode == "mean")
            prep_before = int(env.preparation_remaining[0].item())
            if args.hold_preparation_pose and prep_before > 0:
                action = hold_action.clone()
            if cached_action is not None and prep_before > 0:
                env.prev_action.copy_(cached_action)
                action = cached_action.clone()
            goal_frame = int(env.goals.frame_idx[0].item())
            diagnostic_goal = {
                key: value[0].detach().cpu().tolist()
                for key, value in env.goals.current().items()
                if key in ("fret", "finger", "sustain_event_id", "sustain_eligible")}
            obs, _reward, done, info = env.step(action)
            if diagnostic and sim_frame < env.preparation_frames + 20:
                current_q = env.dof_state.view(env.num_envs, env.n_dof, 2)[0, :, 0]
                preparation_trace.append({
                    "sim_frame": sim_frame, "goal_frame": goal_frame,
                    "preparation_remaining_before_step": prep_before,
                    "done": bool(done[0].item()),
                    "cached_ema_error": (float((env.prev_action - cached_action).abs().max().item())
                        if cached_action is not None and prep_before > 0 and not bool(done[0].item())
                        else None),
                    "max_controlled_deviation_from_reset_deg": (None if bool(done[0].item())
                        else float(torch.rad2deg(
                            (current_q[env.ctrl_idx] - reset_q[env.ctrl_idx]).abs().max()).item())),
                    "metrics": {key: value.item() for key, value in info.items()
                                if key.startswith("finger_") and value.numel() == 1},
                })
            if bool((info["policy_teacher_weight"] > 0).any().item()):
                raise RuntimeError("full-song evaluation unexpectedly activated a policy teacher")
            live = info["goal_metrics_enabled"]
            live_count = int(live.sum().item())
            if live_count:
                event_evidence.update(goal_frame, diagnostic_goal, {
                    key: value[0].item() for key, value in info.items()
                    if key.startswith("finger_") and value.numel() == 1})
                live_f = live.float()
                diagnostic_frames += live_count
                thumb_distance_sum += float(
                    (info["thumb_distance"] * live_f).sum().cpu())
                thumb_support_frames += int(
                    (info["thumb_support"] & live).sum().cpu())
                thumb_wrong_contact_frames += int(
                    (info["thumb_wrong_contact"] & live).sum().cpu())
                synergy_active_sum += float(
                    (info["finger_synergy_active_rate"] * live_f).sum().cpu())
                synergy_induced_sum += float(
                    (info["finger_synergy_induced_deg"] * live_f).sum().cpu())
                finger_back_soft_sum += float(
                    (info["finger_back_soft_penalty"] * live_f).sum().cpu())
                min_finger_local_z = min(
                    min_finger_local_z,
                    float(info["finger_back_min_local_z"][live].min().cpu()))
                min_finger_proximal_local_z = min(
                    min_finger_proximal_local_z,
                    float(info[
                        "finger_back_proximal_min_local_z"
                    ][live].min().cpu()))
                min_finger_distal_local_z = min(
                    min_finger_distal_local_z,
                    float(info[
                        "finger_back_distal_min_local_z"
                    ][live].min().cpu()))
            reset_count += int(done.sum().item())
            if bool(done[0].item()):
                completed = bool(info.get("goal_finished", torch.tensor([False]))[0].item())
                summary_keys = (
                    "accuracy_l", "precision_l", "recall_l", "f1_l",
                    "no_press_accuracy", "wrong_press_rate", "chord_ready_rate",
                    "press_dropout_rate", "sustain_event_count",
                    "sustain_event_success_count", "sustain_event_success_rate",
                    "sustain_hold_rate",
                )
                episode_metrics = {
                    key: value.item() for key, value in info.items()
                    if (key in summary_keys or key.startswith("press_finger_"))
                    and value.numel() == 1}
                termination_reasons = [
                    key for key, value in info.items()
                    if key.endswith("_termination") and value.numel() == 1
                    and bool(value.item())]
                break
    finally:
        env.close()

    events_report = out.with_suffix(".events.json")
    events_report.write_text(json.dumps({
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "checkpoint_contract_sha256": checkpoint["checkpoint_contract"]["sha256"],
        "goal": str(Path(args.goal).resolve()),
        "input_hashes": payload["inputs"],
        "implementation_files_changed_since_checkpoint": implementation_changes,
        "evaluation_mode": ("deterministic_full_song_no_curriculum_teacher"
                            if args.action_mode == "mean" else
                            "sampled_full_song_no_curriculum_teacher"),
        "evaluation_seed": evaluation_seed,
        "start_frame": args.start_frame,
        "initial_pose": args.initial_pose,
        "cached_pose_slot": cache_slot,
        "extra_preparation_frames": args.extra_preparation_frames,
        "hold_preparation_pose": args.hold_preparation_pose,
        "cached_preparation_action": args.cached_preparation_action,
        "restore_source_state": args.restore_source_state,
        "diagnostic_probe": args.diagnostic_probe,
        "source_restore_refresh_physics_steps": int(args.restore_source_state),
        "cached_to_settled_reset_max_controlled_error_deg": cache_reset_error_deg,
        "cache_restore_audit": cache_restore_audit,
        "preparation_trace": preparation_trace,
        "evaluation_scope": "song_suffix" if diagnostic else "full_song",
        "preparation_frames": env.preparation_frames,
        "evaluation_contract_sha256": canonical_sha256({
            "config": payload["config"], "control": payload["control"],
            "observation": payload["observation"], "model": payload["model"],
            "implementation": {
                entry["path"]: (file_sha256(PACKAGE_ROOT / entry["path"])
                                if (PACKAGE_ROOT / entry["path"]).is_file() else None)
                for entry in payload["fingerprints"]["implementation"]["manifest"]},
            "recorder": file_sha256(__file__),
        }),
        "sim_hz": env.SIM_HZ,
        "goal_finished": completed,
        "termination_reasons": termination_reasons,
        "episode_metrics": episode_metrics,
        "frames_simulated": sim_frame + 1,
        "expected_song_frames": env.goals.n_frames,
        "evidence_notes": [
            "Frame indices are zero-based song frames; seconds = frame / sim_hz.",
            "String indices follow goal storage order (zero-based).",
            "Means include event boundary frames; eligible_frames reports grace-filtered exposure.",
            "Per-finger metrics are attributed only for unique single-string assignments.",
            "Precision checks and axis qualities are evidence, not physical contact-cause labels.",
            "Stops at the first episode end; unobserved events are not scored as successes.",
        ],
        "events": event_evidence.report(),
    }, indent=2, ensure_ascii=False, allow_nan=False))

    cmd = ["ffmpeg", "-y", "-framerate", str(args.fps),
           "-i", str(frames_dir / "%05d.png")]
    if args.audio:
        cmd += ["-itsoffset", f"{env.preparation_frames / 60.0:.6f}",
                "-i", args.audio, "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    joint_trajectory = (
        torch.stack(controlled_joint_samples)
        if controlled_joint_samples else None)
    flexion_trajectory = (
        torch.stack(finger_flexion_samples)
        if finger_flexion_samples else None)
    stability = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "video": str(out.resolve()),
        "view": args.view,
        "camera_distance_scale": args.camera_distance_scale,
        "frames_simulated": sim_frame + 1,
        "preparation_frames": env.preparation_frames,
        "preparation_seconds": env.preparation_frames / 60.0,
        "audio_start_seconds": env.preparation_frames / 60.0,
        "early_resets": reset_count - int(completed),
        "goal_finished": completed,
        "joint_groups": {
            name: {
                "max_abs_deviation_deg": math.degrees(group_max[name]),
                "rms_deviation_deg": math.degrees(math.sqrt(
                    group_sum_sq[name] / max(group_samples[name], 1))),
            }
            for name in groups
        },
        "body_max_position_drift_m": body_max_drift,
        "left_hand_diagnostics": {
            "frames": diagnostic_frames,
            "mean_thumb_distance_m":
                thumb_distance_sum / max(diagnostic_frames, 1),
            "thumb_support_rate":
                thumb_support_frames / max(diagnostic_frames, 1),
            "thumb_wrong_contact_rate":
                thumb_wrong_contact_frames / max(diagnostic_frames, 1),
            "finger_synergy_active_rate":
                synergy_active_sum / max(diagnostic_frames, 1),
            "mean_finger_synergy_induced_deg":
                synergy_induced_sum / max(diagnostic_frames, 1),
            "mean_finger_back_soft_penalty":
                finger_back_soft_sum / max(diagnostic_frames, 1),
            "minimum_finger_local_z_m":
                min_finger_local_z if diagnostic_frames else None,
            "minimum_finger_proximal_local_z_m":
                min_finger_proximal_local_z if diagnostic_frames else None,
            "minimum_finger_distal_local_z_m":
                min_finger_distal_local_z if diagnostic_frames else None,
            "adjacent_finger_motion_correlation": (
                adjacent_finger_motion_correlations(flexion_trajectory)
                if flexion_trajectory is not None else {}),
        },
        "controlled_joint_distribution": (
            summarize_joint_trajectory(
                joint_trajectory, controlled_lower, controlled_upper,
                controlled_joint_names)
            if joint_trajectory is not None else {}),
    }
    report = out.with_suffix(".stability.json")
    report.write_text(json.dumps(stability, indent=2, ensure_ascii=False))
    shutil.rmtree(frames_dir)
    try:
        frames_dir.parent.rmdir()
    except OSError:
        pass
    print(f"rollout: {written} frames -> {out}")
    print(f"stability: {report}")
    print(f"events: {events_report}")
    print(f"frames removed: {frames_dir}")


if __name__ == "__main__":
    main()
