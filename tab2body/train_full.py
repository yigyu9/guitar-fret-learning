"""Assemble and verify a fixed-guitar G0 Fret+Strike player.

The first Synchronizer is deterministic, so this entry point does not launch
PPO.  It strictly loads the two song-specific source checkpoints, compiles the
shared event timeline, seals the 105D action contract, and optionally writes a
reference bundle.  The built-in probe is CPU-safe and verifies tensor/runtime
interfaces only; it is not an Isaac Gym performance rollout.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from tab2body.full.action import FullActionManifest
from tab2body.full.bundle import (
    build_g0_bundle_document,
    validate_g0_bundle_document,
    write_g0_bundle,
)
from tab2body.full.events import compile_song_bundle_events
from tab2body.full.runtime import G0SynchronizationRuntime
from tab2body.full.source_policies import load_frozen_skill_pair
from tab2body.full.synchronizer import EventOutcome
from tab2body.song_bundles import DEFAULT_SONG_ID, bundle_path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HUMANOID_MJCF = PROJECT_ROOT / "tab2body/assets/smpl_mpl_hands_body.xml"
ASSEMBLY_REPORT_SCHEMA = "tab2body.g0_assembly_report.v2"


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "fixed-guitar Fret/Strike checkpoint assembly and rule "
            "Synchronizer verification"))
    parser.add_argument(
        "--song", default=DEFAULT_SONG_ID,
        help="data/song_bundles 아래의 song_id")
    parser.add_argument(
        "--fret-checkpoint", required=True,
        help="같은 곡으로 학습한 Fret-v2 checkpoint")
    parser.add_argument(
        "--strike-checkpoint", required=True,
        help="같은 곡으로 학습한 Strike-v2 checkpoint")
    parser.add_argument(
        "--device", default="cpu",
        help="checkpoint interface probe device (default: cpu)")
    parser.add_argument(
        "--output", default=None,
        help="검증된 G0 reference bundle JSON을 저장할 경로")
    parser.add_argument(
        "--require-qualified-sources", action="store_true",
        help="full-song/original-tempo 승급 조건을 못 채운 source를 거부")
    parser.add_argument(
        "--skip-interface-probe", action="store_true",
        help="strict load와 bundle 검증만 수행하고 actor tensor probe는 생략")
    return parser


def _interface_probe(pair, timeline, manifest, device):
    """Exercise one canonical event without claiming physical performance."""
    batch = 2
    runtime = G0SynchronizationRuntime(
        pair, timeline, manifest, num_envs=batch,
        common_preroll_frames=1,
        allow_identity_postprocessors=True)
    hold = torch.zeros(batch, 105, dtype=torch.float32, device=device)
    executed = hold.clone()
    runtime.reset(hold)
    fret_obs = torch.zeros(
        batch, pair.fret.obs_dim, dtype=torch.float32, device=device)
    strike_obs = torch.zeros(
        batch, pair.strike.obs_dim, dtype=torch.float32, device=device)
    strike_ready = torch.ones(batch, dtype=torch.bool, device=device)
    guitar_stable = torch.ones(batch, dtype=torch.bool, device=device)
    last_command = None
    last_result = None
    max_steps = (
        timeline.events[0].traversal_end_frame
        + timeline.events[0].effective_delay_cap_frames + 8)
    for _ in range(max(max_steps, 8)):
        event = runtime.clock.current()
        ready = event.audible_mask.clone()
        command = runtime.before_physics(
            fret_observation=fret_obs,
            strike_observation=strike_obs,
            hold_action=hold,
            fret_ready_mask=ready,
            strike_ready=strike_ready,
            guitar_stable=guitar_stable)
        # Emulate the single Full actuator's alpha=.5 EMA.  A real FullG0Task
        # obtains this exact value from GuitarEnvBase.prev_action instead.
        executed = 0.5 * executed + 0.5 * command.action.full_action
        runtime.commit_executed_action(executed)
        crossing = torch.where(
            command.decision.strike_permission[:, None],
            command.event.traversal_mask,
            torch.zeros_like(command.event.traversal_mask))
        crossing_subframe_t = torch.zeros(
            batch, 6, dtype=torch.float32, device=device)
        crossing_direction = torch.zeros(
            batch, 6, dtype=torch.int8, device=device)
        for row in range(batch):
            ordered = command.event.traversal_order[row]
            ordered = ordered[ordered >= 0]
            if command.decision.strike_permission[row] and ordered.numel():
                fractions = torch.arange(
                    1, ordered.numel() + 1, dtype=torch.float32,
                    device=device) / float(ordered.numel() + 1)
                crossing_subframe_t[row, ordered] = fractions
                crossing_direction[row, ordered] = (
                    command.event.strike_direction[row])
        result = runtime.after_physics(
            crossing_mask=crossing,
            crossing_subframe_t=crossing_subframe_t,
            crossing_direction=crossing_direction,
            fret_ready_mask=ready)
        last_command, last_result = command, result
        if bool(result.resolved_pulse.all().item()):
            break
    else:
        raise RuntimeError("G0 interface probe did not resolve its first event")

    fret_sync = last_command.actor_fret_observation[:, [
        pair.fret.observation_index["fret_v2.synchronizer.release_enable"],
        pair.fret.observation_index["fret_v2.synchronizer.timing_offset_s"],
    ]]
    strike_sync = last_command.actor_strike_observation[:, [
        pair.strike.observation_index[
            "strike_v2.synchronizer.release_enable"],
        pair.strike.observation_index[
            "strike_v2.synchronizer.timing_offset_s"],
    ]]
    expected_sync = torch.tensor(
        [1.0, 0.0], dtype=torch.float32, device=device).expand(batch, -1)
    if not torch.equal(fret_sync, expected_sync) or not torch.equal(
            strike_sync, expected_sync):
        raise RuntimeError("frozen source actor sync context changed")
    outcomes = sorted({
        EventOutcome(int(value)).name
        for value in last_result.outcome.detach().cpu().tolist()
    })
    saved_runtime = runtime.checkpoint_state()
    expected_cursor = runtime.clock.event_index.clone()
    expected_frame = runtime.clock.score_frame.clone()
    runtime.reset(hold)
    runtime.load_checkpoint_state(saved_runtime)
    if (not torch.equal(runtime.clock.event_index, expected_cursor)
            or not torch.equal(runtime.clock.score_frame, expected_frame)):
        raise RuntimeError("G0 runtime state did not resume exactly")
    pair.fret.assert_frozen_integrity()
    pair.strike.assert_frozen_integrity()
    return {
        "status": "passed",
        "scope": "tensor_and_contract_only",
        "isaac_physics_executed": False,
        "batch_size": batch,
        "first_event_index": int(last_result.event_id[0].item()),
        "outcomes": outcomes,
        "full_action_shape": list(last_command.action.full_action.shape),
        "actor_facing_sync_context": [1.0, 0.0],
        "post_ema_history_committed": True,
        "runtime_state_resume_exact": True,
        "source_parameters_remained_frozen": True,
    }


def main(argv=None):
    args = build_parser().parse_args(argv)
    requested_device = torch.device(args.device)
    if requested_device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit(
            f"CUDA device requested but unavailable: {requested_device}")
    song_root = bundle_path(args.song).resolve()
    timeline = compile_song_bundle_events(song_root)
    pair = load_frozen_skill_pair(
        song_id=args.song,
        bundle_path=song_root,
        fret_checkpoint=args.fret_checkpoint,
        strike_checkpoint=args.strike_checkpoint,
        device=requested_device)
    if args.require_qualified_sources and not pair.qualified_for_g0:
        reasons = (
            list(pair.fret.qualification.reasons)
            + list(pair.strike.qualification.reasons))
        raise SystemExit(
            "source checkpoints are contract-compatible but not qualified "
            f"for G0 evaluation: {reasons}")

    manifest = FullActionManifest.from_mjcf(
        HUMANOID_MJCF,
        fret_action_names=pair.fret.action_names,
        strike_action_names=pair.strike.action_names)
    document = build_g0_bundle_document(
        pair, timeline, manifest, project_root=PROJECT_ROOT)
    validate_g0_bundle_document(document, project_root=PROJECT_ROOT)
    output = None
    if args.output:
        output = write_g0_bundle(args.output, document)
        validate_g0_bundle_document(
            json.loads(output.read_text(encoding="utf-8")),
            project_root=PROJECT_ROOT)

    probe = None
    if not args.skip_interface_probe:
        probe = _interface_probe(
            pair, timeline, manifest, requested_device)
    warnings = []
    if not pair.qualified_for_g0:
        warnings.append(
            "The selected checkpoints are suitable for integration smoke only; "
            "they have not passed the source-skill promotion gates.")
    warnings.append(
        "No one-simulator Isaac FullG0Task rollout was performed by this "
        "assembly command.")
    report = {
        "schema": ASSEMBLY_REPORT_SCHEMA,
        "song_id": pair.song_id,
        "canonical_timeline": {
            "schema": timeline.schema,
            "sha256": timeline.content_sha256,
            "event_count": len(timeline.events),
            "fps": timeline.fps,
        },
        "sources": {
            "fret": pair.fret.to_reference_document(PROJECT_ROOT),
            "strike": pair.strike.to_reference_document(PROJECT_ROOT),
            "qualified_for_g0_evaluation": pair.qualified_for_g0,
        },
        "action": {
            "schema": manifest.schema,
            "dimension": 105,
            "active_source_dimensions": 60,
            "reserved_hold_dimensions": 45,
            "manifest_sha256": manifest.sha256,
        },
        "synchronizer": {
            "type": "deterministic_rule_supervisor",
            "owns_joint_actions": False,
            "score_clock_pauses": False,
            "maximum_delay_frames": 3,
            "fret_press_advance_frames": 3,
        },
        "interface_probe": probe,
        "bundle_output": None if output is None else str(output),
        "bundle_sha256": document["sha256"],
        "warnings": warnings,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    main()
