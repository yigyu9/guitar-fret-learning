"""Executable contract checks for field-level context encoding.

Run directly so this package does not require pytest::

    python full/action_residual/tests/test_context_encoding.py
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys
from typing import Callable

import torch


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full.action_residual.context_encoding import (  # noqa: E402
    AggregateSupportEncodingInput,
    EncodingBlockManifest,
    EncodingField,
    ExactContactEncodingInput,
    ExactTetherEncodingInput,
    GUITAR_SUPPORT_MANIFEST,
    GuitarSupportEncodingInput,
    GuitarSupportPacker,
    JointHistoryEncodingInput,
    JointHistoryPacker,
    PRIVILEGED_MANIFEST,
    PrivilegedEncodingInput,
    PrivilegedPacker,
    READINESS_MANIFEST,
    ReadinessEncodingInput,
    ReadinessPacker,
    SUPPORT_SITE_KEYS,
    SupportSiteEncodingInput,
    TETHER_KEYS,
    TetherEncodingInput,
)
from full.action_residual.context_pipeline import (  # noqa: E402
    ActionResidualContextPacker,
)
from full.action_residual.tests.test_contract import _profile  # noqa: E402


def _raises(error_type: type[Exception], fn: Callable[[], object]) -> str:
    try:
        fn()
    except error_type as error:
        return str(error)
    raise AssertionError(f"expected {error_type.__name__}")


def _scalar(values: list[float]) -> torch.Tensor:
    return torch.tensor(values, dtype=torch.float32)


def _readiness() -> ReadinessEncodingInput:
    nan = float("nan")
    return ReadinessEncodingInput(
        phase=torch.tensor([[1, 0, 0, 0, 0], [0, 0, 1, 0, 0]]),
        fret_global_ready=_scalar([0, 1]),
        strike_ready=_scalar([0, 1]),
        guitar_stable=_scalar([0, 1]),
        strike_permission=_scalar([0, 1]),
        deadline_missed=_scalar([0, 0]),
        strike_window_open=_scalar([0, 1]),
        recovery_active=_scalar([0, 0]),
        action_history_valid=_scalar([0, 1]),
        dwell_fractions=torch.tensor([[0, 0, 0], [1, 0.8, 1.0]]),
        press_required=torch.ones(2, 6),
        measurement_valid=torch.tensor([[0] * 6, [1] * 6]),
        press_quality=torch.tensor([[nan] * 6, [0.75] * 6]),
        assigned_finger_correct=torch.tensor([[nan] * 6, [1] * 6]),
        ready_dwell_fraction=torch.tensor([[nan] * 6, [0.5] * 6]),
        pick_geometry_valid=_scalar([0, 1]),
        pick_to_entry_g=torch.tensor([[nan] * 3, [0.10, -0.10, 0.20]]),
        pick_to_exit_g=torch.tensor([[nan] * 3, [0.05, 0.0, -0.05]]),
        pick_relative_velocity_g=torch.tensor(
            [[nan] * 3, [1.0, -2.0, 0.5]]),
        target_lane_error=_scalar([nan, 0.015]),
        traversal_direction_speed=_scalar([nan, 1.0]),
        clearance_margin=_scalar([nan, 0.025]),
        detector_armed=torch.tensor([[0] * 6, [1, 0, 1, 0, 1, 0]]),
    )


def _support_site(valid_second_row: bool = True) -> SupportSiteEncodingInput:
    nan = float("nan")
    valid = 1.0 if valid_second_row else 0.0
    second3 = [0.10, -0.10, 0.20] if valid_second_row else [nan] * 3
    return SupportSiteEncodingInput(
        anchor_position_error_g=torch.tensor([[nan] * 3, second3]),
        relative_velocity_g=torch.tensor(
            [[nan] * 3, [0.25, -0.5, 0.1] if valid_second_row else [nan] * 3]),
        normal_load_proxy=_scalar([nan, 50.0 if valid_second_row else nan]),
        tangential_load_proxy=_scalar([nan, 20.0 if valid_second_row else nan]),
        slip_speed=_scalar([nan, 0.1 if valid_second_row else nan]),
        friction_reserve=_scalar([nan, 30.0 if valid_second_row else nan]),
        contact_on=_scalar([nan, valid if valid_second_row else nan]),
        kinematics_valid=_scalar([0, valid]),
        contact_valid=_scalar([0, valid]),
    )


def _aggregate() -> AggregateSupportEncodingInput:
    nan = float("nan")
    return AggregateSupportEncodingInput(
        contact_valid=_scalar([0, 1]),
        total_normal_load=_scalar([nan, 50]),
        net_tangential_force_g=torch.tensor([[nan] * 3, [10, 20, 30]]),
        net_contact_torque_g=torch.tensor([[nan] * 3, [2, 4, 6]]),
        center_of_pressure_xy_g=torch.tensor([[nan] * 2, [0.1, -0.1]]),
        support_polygon_margin=_scalar([nan, 0.05]),
        overforce_margin=_scalar([nan, 20]),
        global_slip_margin=_scalar([nan, 0.25]),
        guitar_stable_dwell_fraction=_scalar([0.0, 0.8]),
        post_impact_grace_fraction=_scalar([0.0, 0.4]),
    )


def _tether() -> TetherEncodingInput:
    nan = float("nan")
    return TetherEncodingInput(
        valid=_scalar([0, 1]),
        extension_g=torch.tensor([[nan] * 3, [0.05, 0.0, -0.05]]),
        relative_velocity_g=torch.tensor([[nan] * 3, [0.25, 0.0, -0.25]]),
        tension_cap_fraction=_scalar([nan, 0.5]),
        artificial_power_fraction=_scalar([nan, -0.25]),
    )


def _guitar() -> GuitarSupportEncodingInput:
    nan = float("nan")
    return GuitarSupportEncodingInput(
        pose_valid=_scalar([0, 1]),
        twist_valid=_scalar([0, 1]),
        position_error_b=torch.tensor([[nan] * 3, [0.10, -0.10, 0.20]]),
        orientation_error_6d_b=torch.tensor(
            [[nan] * 6, [1.0, -1.0, 2.0, -2.0, 0.0, 0.5]]),
        linear_velocity_b=torch.tensor([[nan] * 3, [0.25, -0.5, 0.1]]),
        angular_velocity_b=torch.tensor([[nan] * 3, [2.5, -5.0, 1.0]]),
        gravity_direction_g=torch.tensor([[nan] * 3, [0.0, 0.0, -1.0]]),
        safety_margins=torch.tensor([[nan] * 4, [0.8, 0.7, 0.6, 0.5]]),
        support_sites={name: _support_site() for name in SUPPORT_SITE_KEYS},
        aggregate=_aggregate(),
        guitar_mode=torch.tensor([[1, 0, 0], [0, 1, 0]]),
        assist_lambda=_scalar([nan, 0.5]),
        assist_transition_blend=_scalar([nan, 0.25]),
        assist_state_valid=_scalar([0, 1]),
        tethers={name: _tether() for name in TETHER_KEYS},
    )


def _exact_contact() -> ExactContactEncodingInput:
    nan = float("nan")
    return ExactContactEncodingInput(
        pair_valid=_scalar([0, 1]),
        point_g=torch.tensor([[nan] * 3, [0.1, -0.1, 0.2]]),
        force_g=torch.tensor([[nan] * 3, [10, 20, 30]]),
        relative_tangent_velocity_g=torch.tensor(
            [[nan] * 3, [0.1, -0.2, 0.3]]),
        penetration_depth=_scalar([nan, 0.005]),
        true_friction_utilization=_scalar([nan, 0.8]),
    )


def _exact_tether() -> ExactTetherEncodingInput:
    nan = float("nan")
    return ExactTetherEncodingInput(
        valid=_scalar([0, 1]),
        extension_g=torch.tensor([[nan] * 3, [0.05, 0.0, -0.05]]),
        force_g=torch.tensor([[nan] * 3, [10, 20, 30]]),
        torque_g=torch.tensor([[nan] * 3, [2, 4, 6]]),
        mechanical_work_rate=_scalar([nan, -25]),
        saturation_fraction=_scalar([nan, 0.5]),
    )


def _privileged() -> PrivilegedEncodingInput:
    return PrivilegedEncodingInput(
        log_guitar_mass_ratio=_scalar([0.0, 0.1]),
        center_of_mass_g=torch.zeros(2, 3),
        inertia_symmetric=torch.full((2, 6), 0.05),
        linear_damping=_scalar([1.0, 2.0]),
        angular_damping=_scalar([1.0, 2.0]),
        support_friction=torch.full((2, 5), 0.8),
        contact_stiffness=_scalar([50000, 60000]),
        contact_damping=_scalar([500, 600]),
        guitar_geometry_scale_xyz=torch.ones(2, 3),
        gravity_magnitude_ratio=torch.ones(2),
        restitution=_scalar([0.1, 0.2]),
        contacts={name: _exact_contact() for name in SUPPORT_SITE_KEYS},
        tethers={name: _exact_tether() for name in TETHER_KEYS},
        external_disturbance_force=torch.zeros(2, 3),
        external_disturbance_torque=torch.zeros(2, 3),
        reset_position_offset=torch.zeros(2, 3),
        reset_rotation_log=torch.zeros(2, 3),
        initial_linear_velocity=torch.zeros(2, 3),
        initial_angular_velocity=torch.zeros(2, 3),
        curriculum_difficulty=_scalar([0.0, 0.5]),
        assist_randomization_severity=_scalar([0.0, 0.25]),
    )


def test_manifest_dimensions_offsets_and_hashes() -> None:
    expected = (
        (READINESS_MANIFEST, 64,
         "6afadd45e346be152c32745372a1b2b55eb04da0549172d769ab802dbf121c18"),
        (GUITAR_SUPPORT_MANIFEST, 128,
         "35f2ee1a06302085e4dab79f1b73e28c3692f05d5f035697efb51049af19c964"),
        (PRIVILEGED_MANIFEST, 128,
         "7aaaaa1077c8412fc2e00672da78e864edf34c495152ad9d62ea10ad6b0109e4"),
    )
    for manifest, dimension, sealed_hash in expected:
        assert manifest.dimension == dimension
        assert manifest.fields[0].offset == 0
        assert manifest.fields[-1].stop == dimension
        assert len(manifest.sha256()) == 64
        assert manifest.sha256() == sealed_hash

    field = EncodingField("a", 1, 1, "1", "none")
    message = _raises(
        ValueError,
        lambda: EncodingBlockManifest("bad", 2, (field,)))
    assert "expected 0" in message

    changed = replace(
        READINESS_MANIFEST.fields[0], scale=(2.0,) * 5)
    changed_manifest = replace(
        READINESS_MANIFEST,
        fields=(changed,) + READINESS_MANIFEST.fields[1:])
    assert changed_manifest.sha256() != READINESS_MANIFEST.sha256()


def test_readiness_pack_and_invalid_zero_semantics() -> None:
    packer = ReadinessPacker()
    data = _readiness()
    encoded = packer.pack(data)
    assert encoded.shape == (2, 64)
    assert torch.isfinite(encoded).all()
    assert READINESS_MANIFEST.slice("phase") == slice(0, 5)
    assert READINESS_MANIFEST.slice(
        "string_high_e.press_required") == slice(15, 16)
    assert READINESS_MANIFEST.slice("pick_geometry_valid") == slice(45, 46)
    assert torch.equal(
        encoded[0, READINESS_MANIFEST.slice("string_high_e.press_quality")],
        torch.zeros(1))
    assert torch.equal(
        encoded[0, READINESS_MANIFEST.slice("pick_to_entry_G")],
        torch.zeros(3))
    assert torch.allclose(
        encoded[1, READINESS_MANIFEST.slice("pick_to_entry_G")],
        torch.tensor([0.5, -0.5, 1.0]))

    invalid_when_live = replace(
        data, measurement_valid=torch.ones(2, 6))
    assert "nonfinite" in _raises(
        ValueError, lambda: packer.pack(invalid_when_live))
    bad_permission = replace(data, strike_permission=_scalar([1, 1]))
    assert "strike_permission" in _raises(
        ValueError, lambda: packer.pack(bad_permission))
    bad_phase = replace(data, phase=torch.zeros(2, 5))
    assert "one-hot" in _raises(ValueError, lambda: packer.pack(bad_phase))
    closed_window = replace(data, strike_window_open=_scalar([0, 0]))
    assert "exactly equal" in _raises(
        ValueError, lambda: packer.pack(closed_window))
    missed_deadline = replace(data, deadline_missed=_scalar([0, 1]))
    assert "exactly equal" in _raises(
        ValueError, lambda: packer.pack(missed_deadline))
    suppressed_ready_strike = replace(
        data, strike_permission=_scalar([0, 0]))
    assert "exactly equal" in _raises(
        ValueError, lambda: packer.pack(suppressed_ready_strike))

    # Values within binary tolerance are canonicalized before semantic gates;
    # 1e-7 must not become False in the tensor but True through bool-casting.
    near_zero_measurement = data.measurement_valid.clone()
    near_zero_measurement[1] = 1e-7
    assert "unmeasured required string" in _raises(
        ValueError,
        lambda: packer.pack(replace(
            data, measurement_valid=near_zero_measurement)))


def test_joint_history_pack_is_joint_major_and_fail_closed() -> None:
    names = tuple(f"joint_{index}" for index in range(75))
    lower = [-2.0] * 75
    upper = [2.0] * 75
    velocity = [2.0] * 75
    packer = JointHistoryPacker(names, lower, upper, velocity)
    assert packer.manifest.sha256() == (
        "13b76029d990aa884b8f9e1c66d1bacba87ce4fd1584cacc0495080d8bbf2f41")
    data = JointHistoryEncodingInput(
        q=torch.zeros(2, 75),
        qdot=torch.ones(2, 75),
        previous_executed_action=torch.full((2, 75), 0.25),
        previous_residual_ratio=torch.full((2, 75), -0.25),
        residual_rate_ratio=torch.full((2, 75), 0.1),
        effective_authority=torch.full((2, 75), 0.5),
    )
    encoded = packer.pack(data)
    assert encoded.shape == (2, 600)
    assert torch.allclose(
        encoded[0, :8],
        torch.tensor([0.0, 0.5, 0.5, 0.5, 0.25, -0.25, 0.1, 0.5]))
    assert packer.manifest.slice("joint.joint_1.q") == slice(8, 9)

    outside = data.q.clone()
    outside[0, 0] = 3.0
    clipped = packer.pack(replace(data, q=outside))
    assert torch.equal(clipped[0, :4], torch.tensor([1.0, 0.5, 1.0, 0.0]))

    bad_action = data.previous_executed_action.clone()
    bad_action[0, 0] = 1.1
    assert "previous_executed_action" in _raises(
        ValueError,
        lambda: packer.pack(replace(data, previous_executed_action=bad_action)))
    bad_q = data.q.clone()
    bad_q[0, 0] = float("nan")
    assert "q must be finite" in _raises(
        ValueError, lambda: packer.pack(replace(data, q=bad_q)))
    assert "75 unique" in _raises(
        ValueError,
        lambda: JointHistoryPacker(names[:-1], lower[:-1], upper[:-1],
                                   velocity[:-1]))


def test_guitar_support_pack_and_optional_sensor_rules() -> None:
    packer = GuitarSupportPacker()
    data = _guitar()
    encoded = packer.pack(data)
    assert encoded.shape == (2, 128)
    assert torch.isfinite(encoded).all()
    assert torch.equal(
        encoded[0, GUITAR_SUPPORT_MANIFEST.slice("position_error_B")],
        torch.zeros(3))
    assert torch.equal(
        encoded[0, GUITAR_SUPPORT_MANIFEST.slice(
            "support.left_neck.normal_load_proxy")],
        torch.zeros(1))
    assert torch.equal(
        encoded[0, GUITAR_SUPPORT_MANIFEST.slice(
            "aggregate.total_normal_load")],
        torch.zeros(1))
    assert torch.allclose(
        encoded[1, GUITAR_SUPPORT_MANIFEST.slice("position_error_B")],
        torch.tensor([0.5, -0.5, 1.0]))
    assert torch.allclose(
        encoded[1, GUITAR_SUPPORT_MANIFEST.slice(
            "aggregate.total_normal_load")],
        torch.tensor([0.5]))

    live_nan = replace(data, pose_valid=torch.ones(2))
    assert "position_error_B" in _raises(
        ValueError, lambda: packer.pack(live_nan))
    missing_site = dict(data.support_sites)
    missing_site.pop(SUPPORT_SITE_KEYS[0])
    assert "support_sites keys" in _raises(
        ValueError,
        lambda: packer.pack(replace(data, support_sites=missing_site)))

    # Contact attribution may be unavailable while body-state kinematics are
    # still valid.  The anchor signal must survive independently.
    sites = dict(data.support_sites)
    site = sites["left_neck"]
    sites["left_neck"] = replace(
        site,
        contact_valid=_scalar([0, 0]),
        normal_load_proxy=_scalar([float("nan"), float("nan")]),
        tangential_load_proxy=_scalar([float("nan"), float("nan")]),
        slip_speed=_scalar([float("nan"), float("nan")]),
        friction_reserve=_scalar([float("nan"), float("nan")]),
        contact_on=_scalar([float("nan"), float("nan")]),
    )
    split_valid = packer.pack(replace(data, support_sites=sites))
    assert torch.allclose(
        split_valid[1, GUITAR_SUPPORT_MANIFEST.slice(
            "support.left_neck.anchor_position_error_G")],
        torch.tensor([0.5, -0.5, 1.0]),
    )
    assert torch.equal(
        split_valid[1, GUITAR_SUPPORT_MANIFEST.slice(
            "support.left_neck.normal_load_proxy")],
        torch.zeros(1),
    )


def test_privileged_pack_and_exact_contact_rules() -> None:
    packer = PrivilegedPacker()
    data = _privileged()
    encoded = packer.pack(data)
    assert encoded.shape == (2, 128)
    assert torch.isfinite(encoded).all()
    assert torch.equal(
        encoded[0, PRIVILEGED_MANIFEST.slice("contact.left_neck.force_G")],
        torch.zeros(3))
    assert torch.allclose(
        encoded[1, PRIVILEGED_MANIFEST.slice("contact.left_neck.force_G")],
        torch.tensor([0.1, 0.2, 0.3]))
    assert torch.equal(
        encoded[0, PRIVILEGED_MANIFEST.slice(
            "exact_tether.left.mechanical_work_rate")],
        torch.zeros(1))

    live_contacts = dict(data.contacts)
    contact = live_contacts["left_neck"]
    live_contacts["left_neck"] = replace(contact, pair_valid=torch.ones(2))
    assert "contact.left_neck.point_G" in _raises(
        ValueError,
        lambda: packer.pack(replace(data, contacts=live_contacts)))
    bad_mass = data.log_guitar_mass_ratio.clone()
    bad_mass[0] = float("nan")
    assert "physics.log_guitar_mass_ratio" in _raises(
        ValueError,
        lambda: packer.pack(replace(data, log_guitar_mass_ratio=bad_mass)))
    assert "physics.restitution" in _raises(
        ValueError,
        lambda: packer.pack(replace(data, restitution=_scalar([1.1, 0.2]))))
    bad_friction = data.support_friction.clone()
    bad_friction[0, 0] = -0.1
    assert "physics.support_friction" in _raises(
        ValueError,
        lambda: packer.pack(replace(data, support_friction=bad_friction)))


def test_combined_context_pipeline_manifest_and_batches() -> None:
    action_manifest, _, _, _, _ = _profile()
    packer = ActionResidualContextPacker(
        action_manifest,
        lower_limits=[-2.0] * 75,
        upper_limits=[2.0] * 75,
        velocity_scales=[2.0] * 75,
    )
    joint = JointHistoryEncodingInput(
        q=torch.zeros(2, 75),
        qdot=torch.zeros(2, 75),
        previous_executed_action=torch.zeros(2, 75),
        previous_residual_ratio=torch.zeros(2, 75),
        residual_rate_ratio=torch.zeros(2, 75),
        effective_authority=torch.zeros(2, 75),
    )
    actor = packer.pack_actor(
        readiness=_readiness(), joint=joint, guitar=_guitar())
    assert actor.readiness_context.shape == (2, 64)
    assert actor.joint_context.shape == (2, 600)
    assert actor.guitar_context.shape == (2, 128)
    critic = packer.pack_critic(actor=actor, privileged=_privileged())
    assert critic.privileged_context.shape == (2, 128)
    assert set(actor.as_kwargs()) == {
        "readiness_context", "joint_context", "guitar_context"}
    assert set(critic.as_kwargs()) == {
        "readiness_context", "joint_context", "guitar_context",
        "privileged_context"}

    checkpoint = packer.checkpoint_manifest()
    assert checkpoint["action_manifest_sha256"] == action_manifest.sha256()
    assert len(checkpoint["schema_sha256"]) == 64
    assert checkpoint == packer.checkpoint_manifest()

    protected_joint = action_manifest.indices(
        action_manifest.protected_action_names)[0]
    bad_authority = joint.effective_authority.clone()
    bad_authority[:, protected_joint] = 1.0
    assert "protected source fingers" in _raises(
        ValueError,
        lambda: packer.pack_actor(
            readiness=_readiness(),
            joint=replace(joint, effective_authority=bad_authority),
            guitar=_guitar(),
        ),
    )


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items())
             if name.startswith("test_") and callable(value)]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"PASS {len(tests)} context-encoding contract tests")
