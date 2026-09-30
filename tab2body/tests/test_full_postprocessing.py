"""CPU contracts for source-exact G0 action postprocessing."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import tab2body.full.postprocessing as post  # noqa: E402
from tab2body.learning.checkpoint_contract import (  # noqa: E402
    CHECKPOINT_CONTRACT_SCHEMA,
    STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
    file_sha256,
    seal_checkpoint_contract,
)


MJCF = PROJECT_ROOT / "tab2body/assets/smpl_mpl_hands_body.xml"
FRET_PROFILE = PROJECT_ROOT / "tab2body/assets/fret_human_joint_profile.json"
GRIP_REFERENCE = PROJECT_ROOT / "strike/02_physical_control/pick-grip-reference.json"


def _fret_names():
    return (
        "L_Shoulder_x", "L_Shoulder_y", "L_Shoulder_z",
        "L_Elbow_x", "L_Elbow_y", "L_Elbow_z",
        "L_Wrist_x", "L_Wrist_y", "L_Wrist_z",
        "LH:thumb1_x", "LH:thumb1_y", "LH:thumb1_z",
        "LH:thumb2", "LH:thumb3",
        "LH:index1_x", "LH:index1_z", "LH:index2", "LH:index3",
        "LH:middle1_x", "LH:middle1_z", "LH:middle2", "LH:middle3",
        "LH:ring1_x", "LH:ring1_z", "LH:ring2", "LH:ring3",
        "LH:pinky1_x", "LH:pinky1_z", "LH:pinky2", "LH:pinky3",
    )


def _strike_names():
    return tuple(name.replace("L_", "R_").replace("LH:", "RH:")
                 for name in _fret_names())


def _asset_manifest():
    return [{
        "path": "assets/smpl_mpl_hands_body.xml",
        "bytes": MJCF.stat().st_size,
        "sha256": file_sha256(MJCF),
    }]


def _fret_contract():
    return seal_checkpoint_contract({
        "schema": CHECKPOINT_CONTRACT_SCHEMA,
        "task": "fret",
        "control": {
            "controlled_dof_names": list(_fret_names()),
            "action_scale": 1.0,
            "action_alpha": 0.5,
            "reset_soft_limit_fraction": 0.02,
        },
        "config": {"reward_safety": {
            "human_hard_limits_enabled": True,
            "human_hard_limit_profile_sha256": file_sha256(FRET_PROFILE),
            "finger_synergy_coefficients": [0.2, 0.3, 0.4],
            "finger_synergy_min_driver_delta_deg": 0.05,
            "finger_synergy_full_driver_delta_deg": 1.0,
            "finger_synergy_max_induced_delta_deg": 3.0,
        }},
        "fingerprints": {"asset": {"manifest": _asset_manifest()}},
    })


def _strike_contract():
    return seal_checkpoint_contract({
        "schema": STRIKE_CHECKPOINT_CONTRACT_SCHEMA,
        "task": "strike",
        "control": {
            "controlled_dof_names": list(_strike_names()),
            "action_scale": 1.0,
            "action_alpha": 0.5,
            "reset_soft_limit_fraction": 0.02,
        },
        "inputs": {"grip_reference_sha256": file_sha256(GRIP_REFERENCE)},
        "config": {"strike": {"grip_control": {
            "pinch_residual_rad": 0.08,
            "free_residual_rad": 0.22,
        }}},
        "fingerprints": {"asset": {"manifest": _asset_manifest()}},
    })


def _mapping(names, *, fret_profile=False):
    _, lower, upper = post._mjcf_control_limits(MJCF, names)
    if fret_profile:
        _, lower, upper = post._apply_fret_hard_limit_profile(
            FRET_PROFILE, names, lower, upper)
    midpoint = (0.5 * (lower + upper)).float()
    half = (0.5 * (upper - lower)).float()
    return midpoint, half


def _qualification(task, stage, qualified=True):
    return {
        "task": task,
        "curriculum_stage": stage,
        "qualified_for_g0": qualified,
        "reasons": [] if qualified else ["test_unqualified"],
        "evidence_sealed": True,
        "training_context_sha256": "a" * 64,
    }


def _build_fret(**overrides):
    names = _fret_names()
    mid, half = _mapping(names, fret_profile=True)
    values = {
        "checkpoint_contract": _fret_contract(),
        "backend_action_names": names,
        "backend_control_mid": mid,
        "backend_control_half_ranges": half,
        "backend_action_scale": 1.0,
        "backend_action_alpha": 0.5,
        "backend_reset_soft_limit_fraction": 0.02,
        "humanoid_mjcf_path": MJCF,
        "human_hard_limit_profile_path": FRET_PROFILE,
        "source_qualification": _qualification("fret", "full_song"),
        "source_checkpoint_sha256": "1" * 64,
    }
    values.update(overrides)
    return post.FretSynergyPostprocessor.from_checkpoint_contract(**values)


def _strike_reference_action(mid, half, names):
    document = json.loads(GRIP_REFERENCE.read_text(encoding="utf-8"))
    target = document["joint_targets_rad"]
    result = torch.zeros(1, len(names), dtype=mid.dtype)
    for index, name in enumerate(names):
        if name.startswith("RH:"):
            result[0, index] = (float(target[name]) - mid[index]) / half[index]
    return result


def _build_strike(**overrides):
    names = _strike_names()
    mid, half = _mapping(names)
    values = {
        "checkpoint_contract": _strike_contract(),
        "backend_action_names": names,
        "backend_control_mid": mid,
        "backend_control_half_ranges": half,
        "backend_action_scale": 1.0,
        "backend_action_alpha": 0.5,
        "backend_reset_soft_limit_fraction": 0.02,
        "humanoid_mjcf_path": MJCF,
        "reference_actions": _strike_reference_action(mid, half, names),
        "grip_reference_path": GRIP_REFERENCE,
        "source_qualification": _qualification(
            "strike", "S3_SONG_INTEGRATION"),
        "source_checkpoint_sha256": "2" * 64,
    }
    values.update(overrides)
    return post.StrikePickGripPostprocessor.from_checkpoint_contract(**values)


def test_fret_synergy_reuses_final_stage_transform():
    processor = _build_fret()
    assert processor.manifest["source_curriculum_stage"] == "full_song"
    assert processor.manifest["stage_specific_action_mask"] is False
    assert processor.manifest["actuator_handshake"]["limit_mode"] == (
        "fret_human_hard_limit_profile")

    actions = torch.zeros(1, 30)
    previous = torch.zeros_like(actions)
    index = {name: i for i, name in enumerate(processor.action_names)}
    ring_flexion = [index[name] for name in post.FRET_FLEXION_ACTION_NAMES[2]]
    middle_flexion = [index[name] for name in post.FRET_FLEXION_ACTION_NAMES[1]]
    pinky_flexion = [index[name] for name in post.FRET_FLEXION_ACTION_NAMES[3]]
    actions[:, ring_flexion] = 0.10
    active = torch.tensor([[False, False, True, False]])
    event = torch.zeros(1, 4, 13)
    event[0, 3, 8] = 1.0
    event[0, 3, 11] = 1.0
    follower = processor.prepare_step(
        current_finger_active=active, finger_event=event)
    assert follower.tolist() == [[True, True, False, False]]
    result = processor(actions, previous)
    assert torch.all(result[:, middle_flexion] > 0.0)
    assert torch.equal(result[:, ring_flexion], actions[:, ring_flexion])
    assert torch.equal(result[:, pinky_flexion], actions[:, pinky_flexion])
    assert processor.last_diagnostics.follower_gate.tolist() == [
        [False, True, False, False]]
    assert not processor.step_state_prepared
    try:
        processor(actions, previous)
    except RuntimeError as exc:
        assert "prepare Fret synergy state" in str(exc)
    else:
        raise AssertionError("stale Fret synergy state was reused")


def test_fret_rejects_nonfinal_source_and_mapping_drift():
    try:
        _build_fret(source_qualification=_qualification(
            "fret", "isolated_press", qualified=False))
    except ValueError as exc:
        assert "unqualified fret source" in str(exc)
    else:
        raise AssertionError("unqualified Fret source was accepted")

    try:
        _build_fret(source_qualification=_qualification(
            "fret", "isolated_press", qualified=True))
    except ValueError as exc:
        assert "full_song" in str(exc)
    else:
        raise AssertionError("non-final Fret action transform was accepted")

    names = _fret_names()
    mid, half = _mapping(names, fret_profile=True)
    half[0] += 0.01
    try:
        _build_fret(backend_control_mid=mid,
                    backend_control_half_ranges=half)
    except ValueError as exc:
        assert "normalized-to-joint mapping" in str(exc)
    else:
        raise AssertionError("Fret joint-range drift was accepted")

    reordered = list(names)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    try:
        _build_fret(backend_action_names=reordered)
    except ValueError as exc:
        assert "action-name order mismatch" in str(exc)
    else:
        raise AssertionError("reordered Fret backend actions were accepted")


def test_strike_grip_constraint_uses_physical_radian_spans():
    processor = _build_strike()
    assert processor.manifest["requires_qualified_source"] is True
    assert processor.manifest["actuator_handshake"]["limit_mode"] == (
        "authored_mjcf")
    action = torch.full((1, 30), 0.5)
    previous = torch.zeros_like(action)
    result = processor(action, previous)
    names = processor.action_names
    index = {name: i for i, name in enumerate(names)}
    hand = [index[name] for name in names if name.startswith("RH:")]
    arm = [index[name] for name in names if not name.startswith("RH:")]
    pinch = [index[name] for name in processor.pinch_action_names]
    free = [index[name] for name in processor.free_action_names]
    reference = processor.reference_actions
    half = processor.half_ranges
    physical_delta = (result - reference) * half[None]
    assert torch.allclose(
        physical_delta[:, pinch], torch.full((1, len(pinch)), 0.04),
        atol=1e-6)
    assert torch.allclose(
        physical_delta[:, free], torch.full((1, len(free)), 0.11),
        atol=1e-6)
    assert torch.equal(result[:, arm], action[:, arm])
    assert len(hand) == 21


def test_strike_rejects_grip_and_actuator_drift():
    try:
        _build_strike(source_qualification=_qualification(
            "strike", "S3_SONG_INTEGRATION", qualified=False))
    except ValueError as exc:
        assert "unqualified strike source" in str(exc)
    else:
        raise AssertionError("unqualified Strike source was accepted")

    names = _strike_names()
    mid, half = _mapping(names)
    reference = _strike_reference_action(mid, half, names)
    reference[0, 9] += 0.01
    try:
        _build_strike(reference_actions=reference)
    except ValueError as exc:
        assert "normalized Strike grip reference" in str(exc)
    else:
        raise AssertionError("incorrect normalized grip reference was accepted")

    try:
        _build_strike(backend_action_alpha=0.4)
    except ValueError as exc:
        assert "scalar contract mismatch" in str(exc)
    else:
        raise AssertionError("Strike actuator alpha drift was accepted")


def test_postprocessor_binding_mutation_and_dtype_are_fail_closed():
    strike = _build_strike()
    strike.reference_actions[0, 9] += .1
    try:
        strike(torch.zeros(1, 30), torch.zeros(1, 30))
    except RuntimeError as exc:
        assert "mutated" in str(exc)
    else:
        raise AssertionError("mutated Strike grip tensor changed behavior")

    fret = _build_fret()
    fret.half_ranges[0] += .1
    fret.prepare_follower_mask(torch.ones(1, 4, dtype=torch.bool))
    try:
        fret(torch.zeros(1, 30), torch.zeros(1, 30))
    except RuntimeError as exc:
        assert "mutated" in str(exc)
    else:
        raise AssertionError("mutated Fret range tensor changed behavior")

    names = _strike_names()
    mid, half = _mapping(names)
    try:
        _build_strike(
            backend_control_mid=mid.double(),
            backend_control_half_ranges=half.double(),
            reference_actions=_strike_reference_action(
                mid.double(), half.double(), names))
    except ValueError as exc:
        assert "float32" in str(exc)
    else:
        raise AssertionError("float64 postprocessor ABI was accepted")


def main():
    test_fret_synergy_reuses_final_stage_transform()
    test_fret_rejects_nonfinal_source_and_mapping_drift()
    test_strike_grip_constraint_uses_physical_radian_spans()
    test_strike_rejects_grip_and_actuator_drift()
    test_postprocessor_binding_mutation_and_dtype_are_fail_closed()
    print("PASS: G0 source action postprocessing is source-exact and fail-closed")


if __name__ == "__main__":
    main()
