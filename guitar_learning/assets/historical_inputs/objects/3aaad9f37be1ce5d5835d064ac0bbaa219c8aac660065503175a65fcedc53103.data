"""Fail-closed integrity checks for the reference-only G0 bundle."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.full.action import FullActionManifest, G0ActionArbiter  # noqa: E402
from tab2body.full.bundle import (  # noqa: E402
    build_g0_bundle_document,
    validate_g0_bundle_document,
)
from tab2body.full.events import compile_song_bundle_events  # noqa: E402
from tab2body.full.runtime import G0SynchronizationRuntime  # noqa: E402
from tab2body.full.source_policies import load_frozen_skill_pair  # noqa: E402
from tab2body.learning.checkpoint_contract import canonical_sha256  # noqa: E402


SONG = "02_Jazz1-200-B_solo"
FRET_CHECKPOINT = (
    PROJECT_ROOT
    / "fret/training/runs/20260909_2338_02_Jazz1-200-B_solo"
    / "checkpoints/fret_001500.pt")
STRIKE_CHECKPOINT = (
    PROJECT_ROOT
    / "strike/training/runs/20260909_2345_02_Jazz1-200-B_solo"
    / "checkpoints/strike_001500.pt")


def _document():
    song_root = PROJECT_ROOT / "data/song_bundles" / SONG
    pair = load_frozen_skill_pair(
        song_id=SONG, bundle_path=song_root,
        fret_checkpoint=FRET_CHECKPOINT,
        strike_checkpoint=STRIKE_CHECKPOINT,
        device="cpu")
    timeline = compile_song_bundle_events(song_root)
    manifest = FullActionManifest.from_mjcf(
        PROJECT_ROOT / "tab2body/assets/smpl_mpl_hands_body.xml",
        fret_action_names=pair.fret.action_names,
        strike_action_names=pair.strike.action_names)
    return pair, build_g0_bundle_document(
        pair, timeline, manifest, project_root=PROJECT_ROOT)


def _reseal(document):
    document["sha256"] = canonical_sha256(document["payload"])
    return document


def _must_fail(document, phrase):
    try:
        validate_g0_bundle_document(document, project_root=PROJECT_ROOT)
    except ValueError as exc:
        assert phrase in str(exc), str(exc)
    else:
        raise AssertionError("malformed G0 bundle was accepted")


def test_bundle_rejects_overlapping_ownership_and_forged_qualification():
    pair, document = _document()
    assert not pair.qualified_for_g0
    assert not pair.fret.qualification.evidence_sealed
    assert not pair.strike.qualification.evidence_sealed
    validate_g0_bundle_document(document, project_root=PROJECT_ROOT)

    overlapping = deepcopy(document)
    owner = overlapping["payload"]["action"]["ownership"]
    owner["strike_source"][0] = owner["fret_source"][0]
    overlapping["payload"]["action_manifest_sha256"] = canonical_sha256(
        overlapping["payload"]["action"])
    _must_fail(_reseal(overlapping), "partition")

    forged = deepcopy(document)
    for task in ("fret", "strike"):
        qualification = forged["payload"]["sources"][task]["qualification"]
        qualification["qualified_for_g0"] = True
    forged["payload"]["qualified_for_g0_evaluation"] = True
    _must_fail(_reseal(forged), "qualification")


def test_action_contract_rejects_clamping_and_prefers_explicit_entry_hold():
    pair, document = _document()
    action = document["payload"]["action"]
    ownership = action["ownership"]
    manifest = FullActionManifest(
        joint_names=tuple(action["joint_names"]),
        fret_action_names=tuple(ownership["fret_source"]),
        strike_action_names=tuple(ownership["strike_source"]),
        reserved_hold_names=tuple(ownership["reserved_hold"]),
        schema=action["schema"])
    arbiter = G0ActionArbiter(manifest)
    hold = torch.zeros(1, 105)
    left = torch.zeros(1, 30)
    right = torch.ones(1, 30) * .8
    previous = torch.ones(1, 30) * .4
    entry_hold = torch.ones(1, 30) * -.2
    merged = arbiter.merge(
        left, right, hold, hold_strike=torch.tensor([True]),
        previous_strike_action=previous,
        strike_entry_hold_action=entry_hold)
    assert torch.equal(merged.commanded_strike_action, entry_hold)

    invalid = right.clone()
    invalid[0, 0] = 1.1
    try:
        arbiter.merge(left, invalid, hold)
    except ValueError as exc:
        assert "[-1,1]" in str(exc)
    else:
        raise AssertionError("out-of-range normalized action was clamped")


def test_runtime_resume_is_weight_bound_strict_and_transactional():
    pair, document = _document()
    action = document["payload"]["action"]
    ownership = action["ownership"]
    manifest = FullActionManifest(
        joint_names=tuple(action["joint_names"]),
        fret_action_names=tuple(ownership["fret_source"]),
        strike_action_names=tuple(ownership["strike_source"]),
        reserved_hold_names=tuple(ownership["reserved_hold"]),
        schema=action["schema"])
    timeline = compile_song_bundle_events(
        PROJECT_ROOT / "data/song_bundles" / SONG)
    runtime = G0SynchronizationRuntime(
        pair, timeline, manifest, num_envs=1,
        common_preroll_frames=1,
        allow_identity_postprocessors=True)
    hold = torch.zeros(1, 105, dtype=torch.float32)
    runtime.reset(hold)
    state = runtime.checkpoint_state()

    wrong_weights = deepcopy(state)
    wrong_weights["source_checkpoint_sha256"]["fret"] = "0" * 64
    try:
        runtime.load_checkpoint_state(wrong_weights)
    except ValueError as exc:
        assert "weights mismatch" in str(exc)
    else:
        raise AssertionError("runtime state accepted different source weights")

    invalid_child = deepcopy(state)
    invalid_child["previous_fret_action"].fill_(.3)
    invalid_child["synchronizer"]["tensors"]["event_id"].fill_(999)
    try:
        runtime.load_checkpoint_state(invalid_child)
    except ValueError as exc:
        assert "outside the timeline" in str(exc)
    else:
        raise AssertionError("runtime state accepted an invalid event cursor")
    assert torch.equal(runtime.previous_fret_action, torch.zeros(1, 30))

    out_of_range = deepcopy(state)
    out_of_range["previous_strike_action"][0, 0] = 1.1
    try:
        runtime.load_checkpoint_state(out_of_range)
    except ValueError as exc:
        assert "normalized range" in str(exc)
    else:
        raise AssertionError("runtime state clamped an invalid action history")


def main():
    test_bundle_rejects_overlapping_ownership_and_forged_qualification()
    test_action_contract_rejects_clamping_and_prefers_explicit_entry_hold()
    test_runtime_resume_is_weight_bound_strict_and_transactional()
    print("PASS: Full G0 bundle and action integrity")


if __name__ == "__main__":
    main()
