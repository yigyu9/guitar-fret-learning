"""Reference-only bundle manifest for a song-specific G0 player."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

import torch

from tab2body.learning.checkpoint_contract import (
    canonical_sha256,
    file_sha256,
    validate_contract_document,
)

from .action import FullActionManifest, humanoid_joint_names
from .events import CANONICAL_PLAY_EVENT_SCHEMA, compile_song_bundle_events
from .source_policies import (
    SOURCE_EXECUTION_CONTEXT_SCHEMA,
    FrozenSkillPair,
    inspect_source_checkpoint_metadata,
)
from .synchronizer import SYNCHRONIZER_SCHEMA


G0_BUNDLE_SCHEMA = "tab2body.g0_player_bundle.v2"


def build_g0_bundle_document(
        source_pair: FrozenSkillPair, timeline,
        action_manifest: FullActionManifest, *, project_root,
        common_preroll_frames=60, max_delay_frames=3,
        readiness_dwell_frames=1):
    """Seal references without copying either source policy's weights."""
    if source_pair.song_id != timeline.song_id:
        raise ValueError("source pair and canonical timeline song_id disagree")
    if int(timeline.fps) != int(source_pair.fps):
        raise ValueError("source pair and canonical timeline FPS disagree")
    if tuple(action_manifest.fret_action_names) != tuple(
            source_pair.fret.action_names):
        raise ValueError("bundle action manifest disagrees with Fret source")
    if tuple(action_manifest.strike_action_names) != tuple(
            source_pair.strike.action_names):
        raise ValueError("bundle action manifest disagrees with Strike source")
    common_preroll_frames = int(common_preroll_frames)
    max_delay_frames = int(max_delay_frames)
    readiness_dwell_frames = int(readiness_dwell_frames)
    if common_preroll_frames < 0:
        raise ValueError("common_preroll_frames must be non-negative")
    if max_delay_frames < 0 or readiness_dwell_frames < 0:
        raise ValueError("Synchronizer frame counts must be non-negative")
    root = Path(project_root).resolve()
    payload = {
        "schema": G0_BUNDLE_SCHEMA,
        "song_id": source_pair.song_id,
        "stage": "G0_FIXED_GUITAR",
        "physics": {
            "guitar_fixed": True,
            "sim_hz": source_pair.fps,
            "sim_substeps": source_pair.sim_substeps,
            "common_preroll_frames": common_preroll_frames,
            "physics_steps_per_control_step": 1,
        },
        "canonical_timeline": {
            "schema": timeline.schema,
            "content_sha256": timeline.content_sha256,
            "event_count": len(timeline.events),
            "source_files": [
                source.to_document() for source in timeline.source_files],
        },
        "sources": {
            "fret": source_pair.fret.to_reference_document(root),
            "strike": source_pair.strike.to_reference_document(root),
        },
        "source_action_postprocessing": {
            "fret": "checkpoint_matched_adjacent_finger_synergy_required",
            "strike": "checkpoint_matched_pick_grip_constraint_required",
            "applied_before_common_ema": True,
        },
        "synchronizer": {
            "schema": SYNCHRONIZER_SCHEMA,
            "type": "deterministic_rule_supervisor",
            "readiness_dwell_frames": readiness_dwell_frames,
            "configured_max_delay_frames": max_delay_frames,
            "effective_delay": (
                "min(configured_max, floor(outgoing_transition_slack*fps))"),
            "release_boundary": "event_center_plus_min_traversal_offset",
            "score_clock_pauses": False,
            "actor_facing_sync_context": {
                "release_enable": 1.0,
                "timing_offset_s": 0.0,
                "reason": "frozen source checkpoints observed only this constant",
            },
        },
        "action": action_manifest.to_document(),
        "action_manifest_sha256": action_manifest.sha256,
        "qualified_for_g0_evaluation": source_pair.qualified_for_g0,
    }
    return {"payload": payload, "sha256": canonical_sha256(payload)}


def validate_g0_bundle_document(document, *, project_root=None):
    if not isinstance(document, Mapping) or set(document) != {
            "payload", "sha256"}:
        raise ValueError("G0 bundle must contain only payload and sha256")
    payload = document["payload"]
    if not isinstance(payload, Mapping) or payload.get("schema") != G0_BUNDLE_SCHEMA:
        raise ValueError("unsupported G0 player bundle schema")
    actual = canonical_sha256(payload)
    if document.get("sha256") != actual:
        raise ValueError("G0 bundle payload SHA-256 mismatch")
    if payload.get("stage") != "G0_FIXED_GUITAR":
        raise ValueError("G0 bundle stage mismatch")
    song_id = payload.get("song_id")
    if not isinstance(song_id, str) or not song_id:
        raise ValueError("G0 bundle song_id must be non-empty")
    physics = payload.get("physics")
    if not isinstance(physics, Mapping) or physics.get("guitar_fixed") is not True:
        raise ValueError("G0 bundle must seal a fixed guitar")
    if (int(physics.get("sim_hz", -1)) != 60
            or int(physics.get("sim_substeps", -1)) != 4
            or int(physics.get("common_preroll_frames", -1)) < 0):
        raise ValueError("G0 bundle physics clock contract is invalid")
    if int(physics.get("physics_steps_per_control_step", -1)) != 1:
        raise ValueError("G0 bundle must use exactly one physics step per command")
    action = payload.get("action")
    if (not isinstance(action, Mapping)
            or set(action) != {"schema", "dimension", "joint_names", "ownership"}
            or action.get("dimension") != 105):
        raise ValueError("G0 bundle must preserve the final 105D action ABI")
    if payload.get("action_manifest_sha256") != canonical_sha256(action):
        raise ValueError("G0 action manifest SHA-256 mismatch")
    ownership = action.get("ownership")
    if not isinstance(ownership, Mapping) or set(ownership) != {
            "fret_source", "strike_source", "reserved_hold"}:
        raise ValueError("G0 action ownership fields are invalid")
    try:
        validated_action_manifest = FullActionManifest(
            joint_names=tuple(action.get("joint_names", ())),
            fret_action_names=tuple(ownership.get("fret_source", ())),
            strike_action_names=tuple(ownership.get("strike_source", ())),
            reserved_hold_names=tuple(ownership.get("reserved_hold", ())),
            schema=action.get("schema"))
    except (TypeError, ValueError) as exc:
        raise ValueError("G0 action ownership is not a 30+30+45 partition") from exc
    if validated_action_manifest.to_document() != dict(action):
        raise ValueError("G0 action manifest is not canonical")
    timeline_ref = payload.get("canonical_timeline")
    if (not isinstance(timeline_ref, Mapping)
            or timeline_ref.get("schema") != CANONICAL_PLAY_EVENT_SCHEMA
            or int(timeline_ref.get("event_count", 0)) < 1):
        raise ValueError("G0 canonical timeline reference is invalid")
    synchronizer = payload.get("synchronizer")
    actor_context = (
        synchronizer.get("actor_facing_sync_context")
        if isinstance(synchronizer, Mapping) else None)
    if (not isinstance(synchronizer, Mapping)
            or synchronizer.get("schema") != SYNCHRONIZER_SCHEMA
            or synchronizer.get("type") != "deterministic_rule_supervisor"
            or synchronizer.get("score_clock_pauses") is not False
            or int(synchronizer.get("configured_max_delay_frames", -1)) != 3
            or int(synchronizer.get("readiness_dwell_frames", -1)) != 1
            or synchronizer.get("release_boundary")
                != "event_center_plus_min_traversal_offset"
            or not isinstance(actor_context, Mapping)
            or float(actor_context.get("release_enable", -1.0)) != 1.0
            or float(actor_context.get("timing_offset_s", 1.0)) != 0.0):
        raise ValueError("G0 Synchronizer contract is invalid")
    postprocessing = payload.get("source_action_postprocessing")
    if (not isinstance(postprocessing, Mapping)
            or postprocessing.get("applied_before_common_ema") is not True
            or postprocessing.get("fret")
                != "checkpoint_matched_adjacent_finger_synergy_required"
            or postprocessing.get("strike")
                != "checkpoint_matched_pick_grip_constraint_required"):
        raise ValueError("G0 source action postprocessing contract is missing")

    sources = payload.get("sources")
    if not isinstance(sources, Mapping) or set(sources) != {"fret", "strike"}:
        raise ValueError("G0 bundle lacks source references")
    qualification = []
    for task, owner in (("fret", "fret_source"),
                        ("strike", "strike_source")):
        reference = sources.get(task)
        if not isinstance(reference, Mapping):
            raise ValueError(f"G0 bundle lacks {task} source reference")
        if (not isinstance(reference.get("path"), str)
                or not reference.get("path")
                or not isinstance(reference.get("file_sha256"), str)
                or len(reference["file_sha256"]) != 64
                or not isinstance(
                    reference.get("checkpoint_contract_sha256"), str)
                or len(reference["checkpoint_contract_sha256"]) != 64):
            raise ValueError(f"G0 {task} source hashes/path are invalid")
        if (reference.get("task") != task
                or tuple(reference.get("action_names", ()))
                    != tuple(ownership[owner])
                or int(reference.get("observation_dimension", -1))
                    != (420 if task == "fret" else 303)):
            raise ValueError(f"G0 {task} source interface reference is invalid")
        source_qualification = reference.get("qualification")
        if (not isinstance(source_qualification, Mapping)
                or source_qualification.get("task") != task
                or not isinstance(
                    source_qualification.get("qualified_for_g0"), bool)
                or not isinstance(
                    source_qualification.get("evidence_sealed"), bool)
                or not isinstance(
                    source_qualification.get("training_context_sha256"), str)
                or len(source_qualification["training_context_sha256"]) != 64
                or (source_qualification.get("qualified_for_g0") is True
                    and source_qualification.get("evidence_sealed") is not True)):
            raise ValueError(f"G0 {task} source qualification is invalid")
        execution_context = reference.get("execution_context")
        if (not isinstance(execution_context, Mapping)
                or execution_context.get("schema")
                    != SOURCE_EXECUTION_CONTEXT_SCHEMA
                or execution_context.get("task") != task
                or execution_context.get("training_context_sha256")
                    != source_qualification.get("training_context_sha256")):
            raise ValueError(f"G0 {task} execution context is invalid")
        qualification.append(source_qualification["qualified_for_g0"])
    expected_qualified = all(qualification)
    if payload.get("qualified_for_g0_evaluation") is not expected_qualified:
        raise ValueError("G0 aggregate source qualification is inconsistent")

    if project_root is not None:
        root = Path(project_root).resolve()
        live_joint_names = humanoid_joint_names(
            root / "tab2body/assets/smpl_mpl_hands_body.xml")
        if tuple(action.get("joint_names", ())) != live_joint_names:
            raise ValueError("G0 action joint order differs from the live MJCF")
        live_timeline = compile_song_bundle_events(
            root / "data/song_bundles" / song_id)
        if (live_timeline.content_sha256
                != timeline_ref.get("content_sha256")
                or len(live_timeline.events)
                != int(timeline_ref.get("event_count"))):
            raise ValueError("G0 canonical timeline reference changed")
        for task in ("fret", "strike"):
            reference = sources.get(task)
            if not isinstance(reference, Mapping):
                raise ValueError(f"G0 bundle lacks {task} source reference")
            path = (root / str(reference.get("path", ""))).resolve()
            try:
                path.relative_to(root)
            except ValueError as exc:
                raise ValueError(
                    f"G0 {task} checkpoint reference escapes project root") from exc
            if not path.is_file() or file_sha256(path) != reference.get(
                    "file_sha256"):
                raise ValueError(f"G0 {task} checkpoint reference changed")
            checkpoint = torch.load(
                str(path), map_location="cpu", weights_only=True)
            if not isinstance(checkpoint, Mapping) or (
                    "checkpoint_contract" not in checkpoint):
                raise ValueError(f"G0 {task} checkpoint contract is missing")
            contract = validate_contract_document(
                checkpoint["checkpoint_contract"])
            if contract["sha256"] != reference.get(
                    "checkpoint_contract_sha256"):
                raise ValueError(f"G0 {task} checkpoint contract changed")
            if contract["payload"].get("task") != task:
                raise ValueError(f"G0 {task} checkpoint task changed")
            control = contract["payload"].get("control")
            model = contract["payload"].get("model")
            if (not isinstance(control, Mapping)
                    or tuple(control.get("controlled_dof_names", ()))
                        != tuple(reference.get("action_names", ()))
                    or not isinstance(model, Mapping)
                    or int(model.get("num_obs", -1))
                        != int(reference.get("observation_dimension", -2))):
                raise ValueError(f"G0 {task} source interface changed")
            live_qualification, live_execution_context = (
                inspect_source_checkpoint_metadata(task, checkpoint, contract))
            if reference.get("qualification") != (
                    live_qualification.to_document()):
                raise ValueError(f"G0 {task} source qualification changed")
            if reference.get("execution_context") != live_execution_context:
                raise ValueError(f"G0 {task} execution context changed")
    return {"payload": dict(payload), "sha256": actual}


def write_g0_bundle(path, document):
    """Write an already validated, deterministic reference manifest."""
    validated = validate_g0_bundle_document(document)
    destination = Path(path).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(
        json.dumps(validated, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    temporary.replace(destination)
    return destination


def read_g0_bundle(path, *, project_root=None):
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_g0_bundle_document(
        document, project_root=project_root)


__all__ = [
    "G0_BUNDLE_SCHEMA",
    "build_g0_bundle_document",
    "read_g0_bundle",
    "validate_g0_bundle_document",
    "write_g0_bundle",
]
