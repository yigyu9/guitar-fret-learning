"""Record an explicitly non-qualified dual-hand G0 integration preview.

The displayed Fret simulator owns the one visible humanoid.  A hidden Strike
simulator supplies the still-unextracted Strike-v2 observation/detector view.
The rule Synchronizer owns the common event cursor and arbitrates both frozen
source actions; the hidden simulator's executed right-hand command is injected
by name into the displayed humanoid before its single visible physics step.

This is a wiring/video artifact, not the final one-simulator FullG0 evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def parser():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fret-checkpoint", type=Path, required=True)
    ap.add_argument("--strike-checkpoint", type=Path, required=True)
    ap.add_argument("--song", default="02_Jazz1-200-B_solo")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--strike-shadow", type=Path, required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=600)
    ap.add_argument("--fps", type=int, default=30, choices=(30, 60))
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    return ap


def _first(value, *, width=None, default=0.0):
    if value is None:
        return default
    value = value.detach()
    if width is None:
        return value.reshape(-1)[0]
    return value.reshape(-1, width)[0:1]


def _encode(frames, output, fps):
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    label = "INCOMPLETE G0 PREVIEW - RULE SYNCHRONIZER / SHADOW STRIKE VIEW"
    command = [
        ffmpeg, "-y", "-loglevel", "error", "-framerate", str(fps),
        "-i", str(frames / "%05d.png"),
        "-vf", (
            "drawbox=x=0:y=0:w=iw:h=48:color=black@0.65:t=fill,"
            "drawtext=text='{}':fontcolor=white:fontsize=24:x=18:y=12"
        ).format(label),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output),
    ]
    subprocess.run(command, check=True)


def main(argv=None):
    args = parser().parse_args(argv)
    if args.steps < 1:
        raise ValueError("steps must be positive")
    if 60 % args.fps:
        raise ValueError("fps must divide 60 Hz")

    # Isaac Gym must precede torch in this process.
    import isaacgym  # noqa: F401
    from isaacgym import gymapi
    import torch

    from tab2body.cfg import FRET
    from tab2body.env.config import configured_kwargs
    from tab2body.env.tasks import FretTask
    from tab2body.full import compile_song_bundle_events, load_frozen_skill_pair
    from tab2body.full.action import FullActionManifest
    from tab2body.full.runtime import G0SynchronizationRuntime
    from tab2body.song_bundles import (
        bundle_path, fret_goal_path, hand_targets_path, strike_goal_path,
    )
    from tab2body.strike_cfg import STRIKE
    from tab2body.tools.record_fret_rollout import upper_body_camera

    bundle = bundle_path(args.song)
    fret_goal = fret_goal_path(args.song)
    strike_goal = strike_goal_path(args.song)
    hand_targets = hand_targets_path(args.song)
    sources = load_frozen_skill_pair(
        song_id=args.song, bundle_path=bundle,
        fret_checkpoint=args.fret_checkpoint,
        strike_checkpoint=args.strike_checkpoint, device=args.device)
    timeline = compile_song_bundle_events(bundle)
    manifest = FullActionManifest.from_mjcf(
        PACKAGE_ROOT / "assets" / "smpl_mpl_hands_body.xml",
        fret_action_names=sources.fret.action_names,
        strike_action_names=sources.strike.action_names)

    common_preroll = 30
    fret_env = FretTask(**configured_kwargs(
        FretTask, FRET, reward_config=FRET, goal_path=str(fret_goal),
        hand_targets_path=str(hand_targets), num_envs=1, device=args.device,
        headless=True, seed=42, reset_noise=0.0, random_start=False,
        preparation_frames=common_preroll))
    shadow = torch.load(str(args.strike_shadow), map_location=args.device)
    if (shadow.get("schema") != "tab2body.strike_shadow_trace.v1"
            or shadow.get("song_id") != args.song
            or shadow.get("strike_checkpoint")
            != str(args.strike_checkpoint.resolve())):
        raise ValueError("Strike shadow trace does not match this preview")
    try:
        fret_env.set_curriculum_stage("full_song", reset=False)
        fret_obs = fret_env.reset()
        strike_obs = shadow["observations"][0:1]

        if tuple(fret_env.dof_names) != tuple(manifest.joint_names):
            raise RuntimeError("visible humanoid DOF order differs from Full 105D ABI")
        right_idx = torch.tensor(
            [fret_env.dof_names.index(name)
             for name in sources.strike.action_names],
            dtype=torch.long, device=args.device)
        left_full_idx = torch.tensor(
            manifest.fret_indices, dtype=torch.long, device=args.device)
        right_full_idx = torch.tensor(
            manifest.strike_indices, dtype=torch.long, device=args.device)

        lo = fret_env.dof_lower.view(1, fret_env.n_dof)
        hi = fret_env.dof_upper.view(1, fret_env.n_dof)
        mid = 0.5 * (lo + hi)
        half = 0.5 * (hi - lo)
        hold = torch.zeros(1, 105, dtype=torch.float32, device=args.device)
        movable = half > 1e-5
        hold[movable] = ((fret_env.init_pose[None] - mid)[movable]
                         / half[movable]).clamp(-1.0, 1.0)

        runtime = G0SynchronizationRuntime(
            sources, timeline, manifest, num_envs=1,
            common_preroll_frames=common_preroll,
            allow_identity_postprocessors=True)
        runtime.reset(hold)

        pending_right = hold[:, right_full_idx].clone()
        original_apply = fret_env.apply_actions

        def combined_apply(left_action):
            original_apply(left_action)
            target = (mid[:, right_idx]
                      + fret_env.action_scale * pending_right
                      * half[:, right_idx]).clamp(
                          lo[:, right_idx], hi[:, right_idx])
            fret_env.pd_target.view(1, fret_env.n_dof)[:, right_idx] = target

        fret_env.apply_actions = combined_apply

        cp = gymapi.CameraProperties()
        cp.width, cp.height = args.width, args.height
        cp.horizontal_fov = 55.0
        camera = fret_env.gym.create_camera_sensor(fret_env.envs[0], cp)
        spec = upper_body_camera(fret_env, args.width, args.height, 55.0)
        fret_env.gym.set_camera_location(
            camera, fret_env.envs[0], gymapi.Vec3(*spec.eye),
            gymapi.Vec3(*spec.target))

        stride = 60 // args.fps
        written = 0
        resolutions = {"full": 0, "partial": 0, "miss": 0}
        usable_steps = min(args.steps, int(shadow["observations"].shape[0]))
        with tempfile.TemporaryDirectory(prefix="sync_preview_") as tmp:
            frames = Path(tmp)
            for frame in range(usable_steps):
                if bool(runtime.clock.finished[0].item()):
                    break
                if frame % stride == 0:
                    fret_env.gym.step_graphics(fret_env.sim)
                    fret_env.gym.render_all_camera_sensors(fret_env.sim)
                    fret_env.gym.write_camera_image_to_file(
                        fret_env.sim, fret_env.envs[0], camera,
                        gymapi.IMAGE_COLOR, str(frames / f"{written:05d}.png"))
                    written += 1

                measurement = fret_env.reward_fn.observe_fret_v2_state(
                    fret_env.goals.current())
                fret_ready = measurement["ready"].to(torch.bool)
                strike_obs = shadow["observations"][frame:frame + 1]
                strike_ready = shadow["entry_ready"][frame:frame + 1].to(
                    torch.bool)

                advanced_fret_obs = fret_env.compute_synchronizer_observation(3)
                command = runtime.before_physics(
                    fret_observation=advanced_fret_obs,
                    strike_observation=strike_obs,
                    hold_action=hold,
                    fret_ready_mask=fret_ready,
                    strike_ready=strike_ready,
                    guitar_stable=torch.ones(
                        1, dtype=torch.bool, device=args.device))

                pending_right = (
                    0.5 * pending_right
                    + 0.5 * command.action.commanded_strike_action)
                fret_obs, _fr, _fd, _finfo = fret_env.step(
                    command.action.commanded_fret_action)

                executed = hold.clone()
                executed[:, left_full_idx] = fret_env.prev_action
                executed[:, right_full_idx] = pending_right
                runtime.commit_executed_action(executed.clamp(-1.0, 1.0))
                crossing = shadow["release_mask"][frame:frame + 1].to(
                    torch.bool)
                # A replayed crossing is not allowed to bypass the live rule gate.
                crossing &= command.decision.strike_permission[:, None]
                subframe = shadow["release_subframe_t"][frame:frame + 1].to(
                    torch.float32)
                direction = shadow["release_direction"][frame:frame + 1].to(
                    torch.int8)
                result = runtime.after_physics(
                    crossing_mask=crossing.to(torch.bool),
                    crossing_subframe_t=subframe.to(torch.float32),
                    crossing_direction=direction.to(torch.int8),
                    fret_ready_mask=fret_ready)
                if bool(result.resolved_pulse[0].item()):
                    code = int(result.outcome[0].item())
                    if code == 1:
                        resolutions["full"] += 1
                    elif code == 2:
                        resolutions["partial"] += 1
                    else:
                        resolutions["miss"] += 1

            if not written:
                raise RuntimeError("no preview frames were captured")
            _encode(frames, args.out.resolve(), args.fps)

        report = {
            "schema": "tab2body.synchronizer_shadow_preview.v1",
            "qualification": "integration_preview_only",
            "limitation": (
                "one visible humanoid; Strike observation/detector is replayed "
                "from a separately captured shadow trace until FullG0Task is extracted"),
            "song_id": args.song,
            "fret_checkpoint": str(args.fret_checkpoint.resolve()),
            "strike_checkpoint": str(args.strike_checkpoint.resolve()),
            "timeline_sha256": timeline.content_sha256,
            "video": str(args.out.resolve()),
            "simulation_steps": frame + 1,
            "video_frames": written,
            "resolutions": resolutions,
            "fret_press_advance_frames": 3,
            "configured_strike_delay_frames": 3,
        }
        report_path = args.out.resolve().with_suffix(".json")
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print(json.dumps(report, indent=2, ensure_ascii=False))
    finally:
        fret_env.close()


if __name__ == "__main__":
    main()
