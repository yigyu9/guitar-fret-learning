"""학습된 fret 정책의 deterministic 전체 곡 close-up rollout을 MP4로 기록한다.

Isaac Gym은 torch보다 먼저 import해야 한다. 예:
  python tools/record_fret_rollout.py \
    --checkpoint ../fret/training/runs/jazz1_pilot/checkpoints/fret_002000.pt \
    --audio ../data/song_bundles/02_Jazz1-200-B_solo/source/audio.wav
"""
from __future__ import annotations

import argparse
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
from isaacgym import gymapi
import torch

from tab2body.cfg import FRET
from tab2body.env.config import configured_kwargs
from tab2body.env.tasks import FretTask
from tab2body.learning import ActorCritic
from tab2body.learning.run_layout import default_video_path
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
                    default=FRET["preparation_frames"] / 60.0)
    return ap


def main(argv=None):
    args = parser().parse_args(argv)
    if 60 % args.fps:
        raise ValueError("fps must divide the 60 Hz simulation clock")
    if args.preparation_seconds < 0.0:
        raise ValueError("preparation seconds must be non-negative")
    if args.camera_distance_scale <= 0.0:
        raise ValueError("camera distance scale must be positive")
    preparation_frames = int(round(args.preparation_seconds * 60.0))

    env = FretTask(**configured_kwargs(
        FretTask, FRET,
        goal_path=args.goal,
        hand_targets_path=args.hand_targets or None,
        num_envs=1,
        device=args.device,
        headless=True,
        seed=FRET["seed"],
        reset_noise=0.0,
        random_start=False,
        preparation_frames=preparation_frames,
    ))
    init_action = ((env.init_pose[env.ctrl_idx] - env.ctrl_mid[0]) /
                   (env.action_scale * env.ctrl_half[0]).clamp_min(1e-6)).clamp(-1.0, 1.0)
    model = ActorCritic(env.num_obs, env.num_actions, env.value_dim,
                        init_std=FRET["policy_init_std"],
                        init_mean=init_action).to(args.device)
    checkpoint = torch.load(
        args.checkpoint, map_location=args.device, weights_only=True)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    obs = env.reset()
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
    out.parent.mkdir(parents=True, exist_ok=True)
    frames_dir = out.with_suffix("") / "frames"
    if frames_dir.exists():
        shutil.rmtree(frames_dir)
    frames_dir.mkdir(parents=True)

    stride = 60 // args.fps
    written = 0
    torso_prefixes = ("Torso", "Spine", "Chest", "Neck", "Head")
    right_prefixes = ("R_Thorax", "R_Shoulder", "R_Elbow", "R_Wrist", "RH:")
    groups = {
        "torso_head_noncontrolled": torch.tensor(
            [i for i, name in enumerate(env.dof_names)
             if name.startswith(torso_prefixes)], device=env.device),
        "right_side_noncontrolled": torch.tensor(
            [i for i, name in enumerate(env.dof_names)
             if name.startswith(right_prefixes)], device=env.device),
        "left_thorax_controlled": torch.tensor(
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
    try:
        total_sim_frames = env.preparation_frames + env.goals.n_frames
        for sim_frame in range(total_sim_frames):
            sample_stability()
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
                action, _, _ = model.act(obs, deterministic=True)
            obs, _reward, done, info = env.step(action)
            live = info["goal_metrics_enabled"]
            live_count = int(live.sum().item())
            if live_count:
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
            reset_count += int(done.sum().item())
    finally:
        env.close()

    cmd = ["ffmpeg", "-y", "-framerate", str(args.fps),
           "-i", str(frames_dir / "%05d.png")]
    if args.audio:
        cmd += ["-itsoffset", f"{env.preparation_frames / 60.0:.6f}",
                "-i", args.audio, "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", str(out)]
    subprocess.run(cmd, check=True, capture_output=True)
    stability = {
        "checkpoint": str(Path(args.checkpoint).resolve()),
        "video": str(out.resolve()),
        "view": args.view,
        "camera_distance_scale": args.camera_distance_scale,
        "frames_simulated": total_sim_frames,
        "preparation_frames": env.preparation_frames,
        "preparation_seconds": env.preparation_frames / 60.0,
        "audio_start_seconds": env.preparation_frames / 60.0,
        "early_resets": reset_count,
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
        },
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
    print(f"frames removed: {frames_dir}")


if __name__ == "__main__":
    main()
