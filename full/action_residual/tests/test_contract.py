"""Executable contract checks for ``full.action_residual``.

Run directly so the prototype does not depend on pytest being installed::

    python full/action_residual/tests/test_contract.py
"""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full.action_residual import (  # noqa: E402
    ActionResidualConfig,
    ActionResidualCoordinator,
    ActionResidualManifest,
    ActionSafetyMasks,
    CentralCriticConfig,
    CentralMultiHeadCritic,
    FrozenSourcePolicyAdapter,
    GoalScoreBatch,
    MaskedJointTanhNormal,
    RawSourceObservation,
    SourceProposal,
)
from tab2body.learning.models import ActorCritic  # noqa: E402


def _profile() -> tuple[
        ActionResidualManifest, tuple[str, ...], tuple[str, ...],
        tuple[str, ...], tuple[str, ...]]:
    axes = ("x", "y", "z")
    left_arm = tuple(
        f"L_{joint}_{axis}"
        for joint in ("Shoulder", "Elbow", "Wrist") for axis in axes)
    right_arm = tuple(
        f"R_{joint}_{axis}"
        for joint in ("Shoulder", "Elbow", "Wrist") for axis in axes)
    left_fingers = tuple(f"LH:finger_{index}" for index in range(21))
    right_fingers = tuple(f"RH:finger_{index}" for index in range(21))
    body = tuple(
        f"{joint}_{axis}"
        for joint in ("L_Thorax", "R_Thorax", "Torso", "Spine", "Chest")
        for axis in axes)
    fret = left_arm + left_fingers
    strike = right_arm + right_fingers

    # Deliberately do not concatenate the source groups in source order.  This
    # proves that composition follows names rather than fragile numeric slices.
    joint = body[:3] + fret + body[3:9] + strike + body[9:]
    neutral = tuple(-0.24 + index * 0.006 for index in range(len(joint)))
    residual_names = left_arm + right_arm + body
    caps = tuple(0.08 if "Wrist" in name else 0.12
                 for name in residual_names)
    manifest = ActionResidualManifest(
        joint_action_names=joint,
        fret_action_names=fret,
        strike_action_names=strike,
        arm_residual_names=left_arm + right_arm,
        body_residual_names=body,
        neutral_logits=neutral,
        residual_caps=caps,
        fret_checkpoint_sha256="a" * 64,
        strike_checkpoint_sha256="b" * 64,
    )
    return manifest, fret, strike, residual_names, body


def _inputs(
        config: ActionResidualConfig, batch: int = 4
        ) -> dict[str, torch.Tensor]:
    return {
        "goal_context": torch.randn(batch, config.goal_context_dim),
        "readiness_context": torch.randn(
            batch, config.readiness_context_dim),
        "joint_context": torch.randn(batch, config.joint_context_dim),
        "guitar_context": torch.randn(batch, config.guitar_context_dim),
    }


def _proposals(
        manifest: ActionResidualManifest, batch: int = 4,
        fret_mean: torch.Tensor | None = None,
        strike_mean: torch.Tensor | None = None,
        ) -> tuple[SourceProposal, SourceProposal]:
    fret_mean = (
        torch.randn(batch, manifest.fret_action_dim)
        if fret_mean is None else fret_mean)
    strike_mean = (
        torch.randn(batch, manifest.strike_action_dim)
        if strike_mean is None else strike_mean)
    return (
        SourceProposal(
            mean=fret_mean,
            log_std=torch.linspace(-3.0, -2.0, manifest.fret_action_dim),
            action_names=manifest.fret_action_names,
            checkpoint_sha256=manifest.fret_checkpoint_sha256,
        ),
        SourceProposal(
            mean=strike_mean,
            log_std=torch.linspace(-2.5, -1.5, manifest.strike_action_dim),
            action_names=manifest.strike_action_names,
            checkpoint_sha256=manifest.strike_checkpoint_sha256,
        ),
    )


def _empty_goal_score(batch: int) -> GoalScoreBatch:
    event_shape = (batch, 4)
    string_shape = (batch, 4, 6)
    return GoalScoreBatch(
        song_progress=torch.linspace(0.0, 0.5, batch),
        beat_phase_radians=torch.zeros(batch),
        bar_phase_radians=torch.zeros(batch),
        tempo_ratio=torch.ones(batch),
        clock_running=torch.ones(batch, dtype=torch.bool),
        timeline_valid=torch.ones(batch, dtype=torch.bool),
        event_valid=torch.zeros(event_shape, dtype=torch.bool),
        event_times_seconds=torch.zeros(batch, 4, 5),
        string_state=torch.zeros(string_shape, dtype=torch.long),
        target_fret_normalized=torch.zeros(string_shape),
        finger_id=torch.zeros(string_shape, dtype=torch.long),
        audible_mask=torch.zeros(string_shape, dtype=torch.bool),
        traversal_mask=torch.zeros(string_shape, dtype=torch.bool),
        strike_direction=torch.zeros(event_shape, dtype=torch.long),
        strike_offsets_seconds=torch.zeros(string_shape),
        gesture=torch.zeros(event_shape, dtype=torch.long),
        atomic_event=torch.zeros(event_shape, dtype=torch.bool),
    )


def test_current_profile_and_zero_initialization() -> None:
    torch.manual_seed(7)
    manifest, fret, strike, residual_names, body = _profile()
    assert len(fret) == 30
    assert len(strike) == 30
    assert len(body) == 15
    assert manifest.joint_action_dim == 75
    assert manifest.residual_dim == 33
    assert len(manifest.protected_action_names) == 42

    config = ActionResidualConfig()
    model = ActionResidualCoordinator(manifest, config)
    fret_mean = torch.randn(4, 30)
    strike_mean = torch.randn(4, 30)
    fret_proposal, strike_proposal = _proposals(
        manifest, fret_mean=fret_mean, strike_mean=strike_mean)
    output = model(
        fret_proposal=fret_proposal,
        strike_proposal=strike_proposal,
        **_inputs(config),
    )
    assert output.joint_mean.shape == (4, 75)
    assert output.raw_residual.shape == (4, 33)
    assert torch.equal(output.raw_residual, torch.zeros_like(output.raw_residual))
    assert torch.equal(output.joint_mean, output.base_mean)

    for source, values in ((fret, fret_mean), (strike, strike_mean)):
        indices = manifest.indices(source)
        assert torch.equal(
            output.base_mean[:, indices], values)
    protected = manifest.indices(manifest.protected_action_names)
    assert torch.equal(
        output.joint_residual[:, protected],
        torch.zeros_like(output.joint_residual[:, protected]))
    assert tuple(manifest.residual_action_names) == residual_names


def test_residual_caps_authority_and_single_distribution() -> None:
    torch.manual_seed(11)
    manifest, _, _, _, _ = _profile()
    config = ActionResidualConfig()
    model = ActionResidualCoordinator(manifest, config)
    with torch.no_grad():
        model.arm_head[-1].bias.fill_(9.0)
        model.body_head[-1].bias.fill_(-9.0)

    authority = torch.ones(manifest.residual_dim, dtype=torch.bool)
    authority[0] = False
    cap_scale = torch.full((manifest.residual_dim,), 0.5)
    fret_mean = torch.randn(4, manifest.fret_action_dim)
    strike_mean = torch.randn(4, manifest.strike_action_dim)
    fret_proposal, strike_proposal = _proposals(
        manifest, fret_mean=fret_mean, strike_mean=strike_mean)
    output = model(
        fret_proposal=fret_proposal,
        strike_proposal=strike_proposal,
        authority_mask=authority,
        cap_scale=cap_scale,
        **_inputs(config),
    )
    caps = torch.tensor(manifest.residual_caps) * 0.5
    assert torch.equal(
        output.bounded_residual[:, 0],
        torch.zeros_like(output.bounded_residual[:, 0]))
    assert bool((output.bounded_residual.abs() <= caps + 1e-7).all())

    active = torch.ones(75, dtype=torch.bool)
    inactive_index = manifest.indices(manifest.body_residual_names)[0]
    active[inactive_index] = False
    distribution = model.distribution(
        output,
        fret_proposal=fret_proposal,
        strike_proposal=strike_proposal,
        active_action_mask=active,
    )
    composed = distribution.log_std[0]
    assert torch.equal(
        composed[list(manifest.indices(manifest.fret_action_names))],
        fret_proposal.log_std)
    assert torch.equal(
        composed[list(manifest.indices(manifest.strike_action_names))],
        strike_proposal.log_std)

    sample = distribution.sample(deterministic=False)
    assert sample.policy_action.shape == (4, 75)
    expected_neutral = torch.tanh(
        torch.tensor(manifest.neutral_logits[inactive_index]))
    assert torch.equal(
        sample.executed_action[:, inactive_index],
        expected_neutral.expand(4))
    assert torch.allclose(
        sample.log_prob,
        distribution.log_prob_from_latent(sample.latent),
        atol=2e-5,
        rtol=2e-5,
    )
    entropy = distribution.entropy()
    assert entropy.shape == (4,)
    assert bool(torch.isfinite(entropy).all())


def test_central_critic_and_frozen_source_adapter() -> None:
    torch.manual_seed(17)
    manifest, _, _, _, _ = _profile()
    config = ActionResidualConfig()
    critic = CentralMultiHeadCritic(manifest, config)
    fret_mean = torch.randn(4, 30)
    strike_mean = torch.randn(4, 30)
    fret_proposal, strike_proposal = _proposals(
        manifest, fret_mean=fret_mean, strike_mean=strike_mean)
    values = critic(
        fret_proposal=fret_proposal,
        strike_proposal=strike_proposal,
        privileged_context=torch.randn(
            4, critic.config.privileged_context_dim),
        **_inputs(config),
    )
    assert values.shape == (4, 11)
    assert critic.config.value_head_names[:6] == (
        "fret_high_e", "fret_B", "fret_G",
        "fret_D", "fret_A", "fret_low_E")

    policy = ActorCritic(obs_dim=13, action_dim=3, value_dim=2)
    adapter = FrozenSourcePolicyAdapter(
        policy,
        ("joint_a", "joint_b", "joint_c"),
        checkpoint_sha256="c" * 64,
        source_name="test_source",
    )
    adapter.train(True)
    assert not adapter.training
    assert not policy.training
    assert all(not parameter.requires_grad for parameter in policy.parameters())
    proposal = adapter(RawSourceObservation(
        value=torch.randn(4, 13),
        source_name="test_source",
        checkpoint_sha256="c" * 64,
    ))
    assert proposal.mean.shape == (4, 3)
    assert proposal.log_std.shape == (3,)
    assert proposal.action_names == ("joint_a", "joint_b", "joint_c")
    with torch.no_grad():
        next(policy.parameters()).add_(0.01)
    try:
        adapter.assert_frozen_integrity()
    except RuntimeError as error:
        assert "mutated" in str(error)
    else:
        raise AssertionError("mutated frozen source policy was accepted")


def test_structured_goal_paths_are_checkpointed() -> None:
    torch.manual_seed(19)
    manifest, _, _, _, _ = _profile()
    config = ActionResidualConfig()
    model = ActionResidualCoordinator(manifest, config)
    critic = CentralMultiHeadCritic(manifest, config)
    fret, strike = _proposals(manifest)
    contexts = _inputs(config)
    contexts.pop("goal_context")
    score = _empty_goal_score(batch=4)

    output = model.forward_structured_goal(
        fret_proposal=fret,
        strike_proposal=strike,
        goal_score=score,
        **contexts,
    )
    assert output.joint_mean.shape == (4, 75)
    assert torch.equal(output.joint_mean, output.base_mean)
    values = critic.forward_structured_goal(
        fret_proposal=fret,
        strike_proposal=strike,
        goal_score=score,
        privileged_context=torch.zeros(4, 128),
        **contexts,
    )
    assert values.shape == (4, 11)
    actor_schema = model.checkpoint_manifest()["goal_score_schema"]
    critic_schema = critic.checkpoint_manifest()["goal_score_schema"]
    assert actor_schema == critic_schema
    assert actor_schema["dimensions"]["output"] == 128


def test_physical_cap_and_three_mask_model_path() -> None:
    torch.manual_seed(23)
    manifest, _, _, _, _ = _profile()
    config = ActionResidualConfig()
    model = ActionResidualCoordinator(manifest, config)
    with torch.no_grad():
        model.arm_head[-1].bias.fill_(20.0)
        model.body_head[-1].bias.fill_(-20.0)

    fret, strike = _proposals(manifest)
    residual_indices = model.residual_indices.detach().clone()
    authority = torch.ones(manifest.residual_dim, dtype=torch.bool)
    source_indices = torch.tensor(manifest.indices(
        manifest.fret_action_names + manifest.strike_action_names))
    new_indices = torch.tensor(manifest.indices(manifest.new_action_names))
    masks = ActionSafetyMasks.for_current_profile(
        residual_authority_mask=authority,
        residual_joint_indices=residual_indices,
        source_joint_indices=source_indices,
        new_joint_indices=new_indices,
        joint_dim=manifest.joint_action_dim,
    )
    cap_rad = torch.full((manifest.residual_dim,), 0.025)
    output = model.forward_physical_caps(
        fret_proposal=fret,
        strike_proposal=strike,
        safety_masks=masks,
        cap_rad=cap_rad,
        ctrl_half=torch.ones(manifest.residual_dim),
        action_scale=1.0,
        **_inputs(config),
    )
    base_action = torch.tanh(
        output.base_mean.index_select(1, residual_indices))
    corrected_action = torch.tanh(
        output.joint_mean.index_select(1, residual_indices))
    assert bool(((corrected_action - base_action).abs()
                 <= cap_rad + 1e-6).all())
    assert output.directional_caps is not None

    distribution = model.distribution(
        output,
        fret_proposal=fret,
        strike_proposal=strike,
        safety_masks=masks,
    )
    protected = torch.tensor(
        manifest.indices(manifest.protected_action_names), dtype=torch.long)
    assert bool(distribution.stochastic_execution_mask[:, protected].all())
    assert not bool(distribution.ppo_credit_mask[:, protected].any())
    sample = distribution.sample()
    assert bool(torch.isfinite(sample.log_prob).all())

    # With all coordinator authority removed, the 15 genuinely new body slots
    # are deterministic seated-hold targets, while all 60 source slots retain
    # their frozen-source exploration.
    zero_masks = ActionSafetyMasks.for_current_profile(
        residual_authority_mask=torch.zeros_like(authority),
        residual_joint_indices=residual_indices,
        source_joint_indices=source_indices,
        new_joint_indices=new_indices,
        joint_dim=manifest.joint_action_dim,
    )
    zero_output = model.forward_physical_caps(
        fret_proposal=fret,
        strike_proposal=strike,
        safety_masks=zero_masks,
        cap_rad=cap_rad,
        ctrl_half=torch.ones(manifest.residual_dim),
        action_scale=1.0,
        **_inputs(config),
    )
    zero_distribution = model.distribution(
        zero_output,
        fret_proposal=fret,
        strike_proposal=strike,
        safety_masks=zero_masks,
    )
    zero_sample = zero_distribution.sample()
    expected_body = torch.tanh(model.neutral_logits[new_indices]).unsqueeze(0)
    assert torch.equal(
        zero_sample.executed_action[:, new_indices],
        expected_body.expand(zero_sample.executed_action.shape[0], -1),
    )


def test_manifest_rejects_ambiguous_source_ownership() -> None:
    manifest, fret, strike, _, body = _profile()
    try:
        ActionResidualManifest(
            joint_action_names=manifest.joint_action_names,
            fret_action_names=fret,
            strike_action_names=(fret[0],) + strike[1:],
            arm_residual_names=manifest.arm_residual_names,
            body_residual_names=body,
            neutral_logits=manifest.neutral_logits,
            residual_caps=manifest.residual_caps,
        )
    except ValueError as error:
        assert "disjoint" in str(error)
    else:
        raise AssertionError("overlapping source ownership was accepted")


def test_runtime_rejects_wrong_source_identity_and_profile() -> None:
    manifest, _, _, _, _ = _profile()
    config = ActionResidualConfig()
    model = ActionResidualCoordinator(manifest, config)
    fret, strike = _proposals(manifest)
    wrong_order = SourceProposal(
        mean=fret.mean,
        log_std=fret.log_std,
        action_names=(fret.action_names[1], fret.action_names[0])
        + fret.action_names[2:],
        checkpoint_sha256=fret.checkpoint_sha256,
    )
    try:
        model(
            fret_proposal=wrong_order,
            strike_proposal=strike,
            **_inputs(config),
        )
    except ValueError as error:
        assert "names/order" in str(error)
    else:
        raise AssertionError("permuted source action names were accepted")

    wrong_hash = SourceProposal(
        mean=fret.mean,
        log_std=fret.log_std,
        action_names=fret.action_names,
        checkpoint_sha256="d" * 64,
    )
    try:
        model(
            fret_proposal=wrong_hash,
            strike_proposal=strike,
            **_inputs(config),
        )
    except ValueError as error:
        assert "SHA-256" in str(error)
    else:
        raise AssertionError("wrong source checkpoint hash was accepted")

    orphan_manifest = ActionResidualManifest(
        joint_action_names=manifest.joint_action_names + ("orphan_x",),
        fret_action_names=manifest.fret_action_names,
        strike_action_names=manifest.strike_action_names,
        arm_residual_names=manifest.arm_residual_names,
        body_residual_names=manifest.body_residual_names,
        neutral_logits=manifest.neutral_logits + (0.0,),
        residual_caps=manifest.residual_caps,
        fret_checkpoint_sha256=manifest.fret_checkpoint_sha256,
        strike_checkpoint_sha256=manifest.strike_checkpoint_sha256,
    )
    try:
        ActionResidualCoordinator(orphan_manifest, config)
    except ValueError as error:
        assert "75D profile" in str(error)
    else:
        raise AssertionError("orphan action profile was accepted")


def test_distribution_rejects_nonfinite_neutral() -> None:
    mean = torch.zeros(2, 3)
    try:
        MaskedJointTanhNormal(
            mean,
            torch.zeros(3),
            torch.ones(3, dtype=torch.bool),
            torch.tensor((0.0, float("nan"), 0.0)),
        )
    except ValueError as error:
        assert "finite" in str(error)
    else:
        raise AssertionError("non-finite neutral action was accepted")


def test_distribution_preserves_saturated_latent_log_prob() -> None:
    mean = torch.tensor(((8.0, 10.0, 12.0),), dtype=torch.float32)
    mask = torch.ones(3, dtype=torch.bool)
    distribution = MaskedJointTanhNormal(
        mean,
        torch.full((3,), -5.0, dtype=torch.float32),
        mask,
        torch.zeros(3, dtype=torch.float32),
    )
    sample = distribution.sample(deterministic=True)
    assert bool((sample.policy_action == 1.0).any())
    assert torch.equal(
        sample.log_prob,
        distribution.log_prob_from_latent(sample.latent),
    )

    # A squashed value at exactly 1 has lost its originating latent.  PPO must
    # fail closed instead of manufacturing a different value with clamp/atanh.
    try:
        distribution.log_prob(sample.policy_action)
    except ValueError as error:
        assert "pre-tanh latent" in str(error)
    else:
        raise AssertionError("saturated action inverse was accepted")

    try:
        MaskedJointTanhNormal(
            mean.to(torch.float16),
            torch.zeros(3, dtype=torch.float16),
            mask,
            torch.zeros(3, dtype=torch.float16),
        )
    except TypeError as error:
        assert "torch.float32" in str(error)
    else:
        raise AssertionError("low-precision policy distribution was accepted")


def test_checkpoint_rejects_same_shape_semantic_mismatch() -> None:
    manifest, _, _, _, _ = _profile()
    names = list(manifest.joint_action_names)
    names[0], names[1] = names[1], names[0]
    reordered = ActionResidualManifest(
        joint_action_names=tuple(names),
        fret_action_names=manifest.fret_action_names,
        strike_action_names=manifest.strike_action_names,
        arm_residual_names=manifest.arm_residual_names,
        body_residual_names=manifest.body_residual_names,
        neutral_logits=manifest.neutral_logits,
        residual_caps=manifest.residual_caps,
        fret_checkpoint_sha256=manifest.fret_checkpoint_sha256,
        strike_checkpoint_sha256=manifest.strike_checkpoint_sha256,
    )
    source_actor = ActionResidualCoordinator(manifest)
    target_actor = ActionResidualCoordinator(reordered)
    untouched = target_actor.arm_head[0].weight.detach().clone()
    try:
        target_actor.load_state_dict(source_actor.state_dict(), strict=True)
    except RuntimeError as error:
        assert "manifest mismatch" in str(error)
    else:
        raise AssertionError("same-shape reordered action ABI was accepted")
    assert torch.equal(target_actor.arm_head[0].weight, untouched)

    source_critic = CentralMultiHeadCritic(manifest)
    head_names = list(source_critic.config.value_head_names)
    head_names[0], head_names[1] = head_names[1], head_names[0]
    target_critic = CentralMultiHeadCritic(
        manifest,
        critic_config=CentralCriticConfig(
            value_head_names=tuple(head_names)),
    )
    try:
        target_critic.load_state_dict(source_critic.state_dict(), strict=True)
    except RuntimeError as error:
        assert "manifest mismatch" in str(error)
    else:
        raise AssertionError("same-shape reordered value heads were accepted")

    # Exact semantic round trips remain supported.
    actor_roundtrip = ActionResidualCoordinator(manifest)
    actor_roundtrip.load_state_dict(source_actor.state_dict(), strict=True)

    corrupt_state = source_actor.state_dict()
    tensor_key = next(
        key for key, value in corrupt_state.items()
        if isinstance(value, torch.Tensor) and value.is_floating_point())
    corrupt_state[tensor_key] = corrupt_state[tensor_key].clone()
    corrupt_state[tensor_key].reshape(-1)[0] = float("nan")
    before_corrupt_load = actor_roundtrip.arm_head[0].weight.detach().clone()
    try:
        actor_roundtrip.load_state_dict(corrupt_state, strict=True)
    except RuntimeError as error:
        assert "non-finite" in str(error)
    else:
        raise AssertionError("non-finite checkpoint tensor was accepted")
    assert torch.equal(actor_roundtrip.arm_head[0].weight, before_corrupt_load)


def test_v1_rejects_unsealed_shape_and_source_dtype() -> None:
    try:
        ActionResidualConfig(goal_context_dim=127)
    except ValueError as error:
        assert "network widths are fixed" in str(error)
    else:
        raise AssertionError("same-ID Goal width variant was accepted")

    try:
        SourceProposal(
            mean=torch.zeros(2, 3, dtype=torch.int64),
            log_std=torch.zeros(3, dtype=torch.float32),
            action_names=("a", "b", "c"),
            checkpoint_sha256="e" * 64,
        )
    except TypeError as error:
        assert "torch.float32" in str(error)
    else:
        raise AssertionError("integer source proposal was accepted")


def test_nested_source_adapter_reseals_after_exact_load() -> None:
    class Parent(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            policy = ActorCritic(obs_dim=7, action_dim=3, value_dim=1)
            self.source = FrozenSourcePolicyAdapter(
                policy,
                ("joint_a", "joint_b", "joint_c"),
                checkpoint_sha256="f" * 64,
                source_name="nested_source",
            )

    parent = Parent()
    parent.load_state_dict(parent.state_dict(), strict=True)
    proposal = parent.source(RawSourceObservation(
        value=torch.zeros(2, 7),
        source_name="nested_source",
        checkpoint_sha256="f" * 64,
    ))
    assert proposal.mean.shape == (2, 3)
    try:
        parent.source.half()
    except TypeError as error:
        assert "must remain torch.float32" in str(error)
    else:
        raise AssertionError("FP16 frozen source policy was accepted")
    assert all(parameter.dtype == torch.float32
               for parameter in parent.source.policy.parameters())


def main() -> None:
    tests = (
        test_current_profile_and_zero_initialization,
        test_residual_caps_authority_and_single_distribution,
        test_central_critic_and_frozen_source_adapter,
        test_structured_goal_paths_are_checkpointed,
        test_physical_cap_and_three_mask_model_path,
        test_manifest_rejects_ambiguous_source_ownership,
        test_runtime_rejects_wrong_source_identity_and_profile,
        test_distribution_rejects_nonfinite_neutral,
        test_distribution_preserves_saturated_latent_log_prob,
        test_checkpoint_rejects_same_shape_semantic_mismatch,
        test_v1_rejects_unsealed_shape_and_source_dtype,
        test_nested_source_adapter_reseals_after_exact_load,
    )
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    main()
