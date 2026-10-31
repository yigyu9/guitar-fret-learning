"""Export a deterministic Strike-v2 shadow trace for the G0 preview."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = PACKAGE_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--fret-checkpoint", type=Path, required=True)
    ap.add_argument("--strike-checkpoint", type=Path, required=True)
    ap.add_argument("--song", default="02_Jazz1-200-B_solo")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--steps", type=int, default=600)
    args = ap.parse_args(argv)

    import isaacgym  # noqa: F401
    import torch
    from tab2body.env.config import configured_kwargs
    from tab2body.env.tasks import StrikeTask
    from tab2body.full import load_frozen_skill_pair
    from tab2body.song_bundles import bundle_path, strike_goal_path
    from tab2body.strike_cfg import STRIKE
    from tab2body.tools.record_strike_rollout import (
        _load_checkpoint, _restore_task, restore_stage_and_tolerance,
    )

    sources = load_frozen_skill_pair(
        song_id=args.song, bundle_path=bundle_path(args.song),
        fret_checkpoint=args.fret_checkpoint,
        strike_checkpoint=args.strike_checkpoint, device=args.device)
    env = StrikeTask(**configured_kwargs(
        StrikeTask, STRIKE, goal_path=str(strike_goal_path(args.song)),
        grip_reference_path=str(STRIKE["grip_reference_path"]), num_envs=1,
        device=args.device, headless=True, seed=42, reset_noise=0.0,
        random_start=False))
    try:
        checkpoint = _load_checkpoint(torch, args.strike_checkpoint, args.device)
        obs = _restore_task(
            env, *restore_stage_and_tolerance(checkpoint), full_song=True)
        env.wrong_crossing_termination_enabled = False
        trace = {key: [] for key in (
            "observations", "entry_ready", "release_mask",
            "release_subframe_t", "release_direction")}
        for _ in range(args.steps):
            trace["observations"].append(obs[0].detach().cpu())
            native = sources.strike.prepare_observation(
                obs, previous_executed_action=env.prev_action)
            action = sources.strike.deterministic_action(native)
            obs, _reward, done, info = env.step(action)
            trace["entry_ready"].append(
                info.get("entry_ready", torch.ones(1, device=args.device))[0]
                .detach().cpu())
            for key, dtype in (("release_mask", torch.bool),
                               ("release_subframe_t", torch.float32),
                               ("release_direction", torch.int8)):
                default = torch.zeros(1, 6, dtype=dtype, device=args.device)
                trace[key].append(info.get(key, default)[0].detach().cpu())
            if bool(done[0].item()):
                break
        payload = {key: torch.stack(value) for key, value in trace.items()}
        payload.update({
            "schema": "tab2body.strike_shadow_trace.v1",
            "song_id": args.song,
            "strike_checkpoint": str(args.strike_checkpoint.resolve()),
        })
        args.out.parent.mkdir(parents=True, exist_ok=True)
        torch.save(payload, args.out)
        print("strike shadow frames: {} -> {}".format(
            payload["observations"].shape[0], args.out.resolve()))
    finally:
        env.close()


if __name__ == "__main__":
    main()
