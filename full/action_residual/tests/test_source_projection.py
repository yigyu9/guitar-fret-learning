"""Direct checks for the frozen source observation projector."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full.action_residual.source_projection import (  # noqa: E402
    FrozenSourceObservationProjector,
    SourceProjectionManifest,
)
from tab2body.learning.models import RunningMeanStd  # noqa: E402
from tab2body.learning.models import ActorCritic  # noqa: E402
from full.action_residual.source_adapter import (  # noqa: E402
    FrozenSourcePolicyAdapter,
)


def _projector() -> FrozenSourceObservationProjector:
    names = (
        "owned_q", "foreign_q", "owned_geometry", "foreign_qdot",
        "goal", "previous_executed_action",
    )
    mean = torch.tensor((0.2, -0.4, 0.6, -0.8, 1.0, -1.2))
    variance = torch.tensor((1.0, 4.0, 9.0, 16.0, 25.0, 36.0))
    rms_sha = FrozenSourceObservationProjector.rms_sha256(mean, variance)
    manifest = SourceProjectionManifest(
        source_name="fret",
        observation_names=names,
        replace_with_rms_mean_names=("foreign_q", "foreign_qdot"),
        checkpoint_sha256="a" * 64,
        rms_sha256=rms_sha,
    )
    return FrozenSourceObservationProjector(
        manifest, rms_mean=mean, rms_variance=variance)


def test_projection_precedes_frozen_normalization() -> None:
    projector = _projector()
    live = torch.tensor((
        (1.2, 100.0, 3.6, -100.0, 6.0, 4.8),
        (-0.8, 200.0, -2.4, 300.0, -4.0, -7.2),
    ))
    result = projector(live)
    replacement_indices = projector.manifest.replacement_indices
    assert torch.equal(
        result.normalized_audit[:, replacement_indices],
        torch.zeros_like(result.normalized_audit[:, replacement_indices]),
    )
    live_indices = (0, 2, 4, 5)
    assert torch.equal(
        result.raw_projected[:, live_indices], live[:, live_indices])
    assert projector.checkpoint_manifest()["projection_manifest_sha256"] == (
        projector.manifest.sha256())

    source_rms = RunningMeanStd(projector.manifest.observation_dim)
    with torch.no_grad():
        source_rms.mean.copy_(projector.rms_mean)
        source_rms.var.copy_(projector.rms_variance)
    assert torch.equal(
        result.normalized_audit, source_rms(result.raw_projected))


def test_projected_adapter_applies_source_rms_once() -> None:
    projector = _projector()
    live = torch.arange(12, dtype=torch.float32).reshape(2, 6)
    projected = projector(live)
    policy = ActorCritic(obs_dim=6, action_dim=3, value_dim=1)
    with torch.no_grad():
        policy.obs_rms.mean.copy_(projector.rms_mean)
        policy.obs_rms.var.copy_(projector.rms_variance)
    adapter = FrozenSourcePolicyAdapter(
        policy,
        ("joint_a", "joint_b", "joint_c"),
        checkpoint_sha256=projector.manifest.checkpoint_sha256,
        source_name="fret",
        projection_manifest=projector.manifest,
    )
    expected = policy.distribution(projected.raw_projected).mean.detach()
    proposal = adapter(projected)
    assert torch.equal(proposal.mean, expected)

    try:
        adapter(projected.normalized_audit)  # type: ignore[arg-type]
    except TypeError as error:
        assert "bare tensors are ambiguous" in str(error)
    else:
        raise AssertionError("untagged normalized source tensor was accepted")


def test_projection_fails_closed() -> None:
    projector = _projector()
    bad = torch.zeros(1, projector.manifest.observation_dim)
    bad[0, 0] = float("nan")
    try:
        projector(bad)
    except ValueError as error:
        assert "finite" in str(error)
    else:
        raise AssertionError("nonfinite source observation was accepted")

    try:
        SourceProjectionManifest(
            source_name="strike",
            observation_names=("a", "b"),
            replace_with_rms_mean_names=("missing",),
            checkpoint_sha256="b" * 64,
            rms_sha256="c" * 64,
        )
    except ValueError as error:
        assert "absent" in str(error)
    else:
        raise AssertionError("unknown replacement field was accepted")

    try:
        projector(torch.zeros(
            1, projector.manifest.observation_dim, dtype=torch.float16))
    except TypeError as error:
        assert "torch.float32" in str(error)
    else:
        raise AssertionError("low-precision source projection was accepted")


def test_projection_checkpoint_seals_field_order() -> None:
    source = _projector()
    names = list(source.manifest.observation_names)
    names[0], names[1] = names[1], names[0]
    target_manifest = SourceProjectionManifest(
        source_name=source.manifest.source_name,
        observation_names=tuple(names),
        replace_with_rms_mean_names=("foreign_q", "foreign_qdot"),
        checkpoint_sha256=source.manifest.checkpoint_sha256,
        rms_sha256=source.manifest.rms_sha256,
    )
    target = FrozenSourceObservationProjector(
        target_manifest,
        rms_mean=source.rms_mean,
        rms_variance=source.rms_variance,
    )
    try:
        target.load_state_dict(source.state_dict(), strict=True)
    except RuntimeError as error:
        assert "manifest mismatch" in str(error)
    else:
        raise AssertionError("same-shape reordered observation ABI was accepted")


def test_projection_rejects_low_precision_module_conversion() -> None:
    projector = _projector()
    try:
        projector.half()
    except TypeError as error:
        assert "must remain torch.float32" in str(error)
    else:
        raise AssertionError("FP16 source RMS conversion was accepted")
    assert projector.rms_mean.dtype == torch.float32
    assert projector.rms_variance.dtype == torch.float32
    result = projector(torch.zeros(1, projector.manifest.observation_dim))
    assert torch.isfinite(result.normalized_audit).all()


def main() -> None:
    tests = (
        test_projection_precedes_frozen_normalization,
        test_projected_adapter_applies_source_rms_once,
        test_projection_fails_closed,
        test_projection_checkpoint_seals_field_order,
        test_projection_rejects_low_precision_module_conversion,
    )
    for test in tests:
        test()
        print(f"PASS {test.__name__}")


if __name__ == "__main__":
    main()
