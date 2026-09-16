"""Direct checks for source-intent calibration and normalization."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full.action_residual.source_intent import (  # noqa: E402
    CALIBRATED,
    CALIBRATION_REQUIRED,
    SourceIntentCalibration,
    SourceIntentNormalizer,
    calibrate_source_intent,
)
from full.action_residual.tests.test_contract import _profile  # noqa: E402


def test_fallback_is_explicit_and_bounded() -> None:
    manifest, _, _, _, _ = _profile()
    calibration = SourceIntentCalibration.fallback(manifest)
    assert calibration.status == CALIBRATION_REQUIRED
    normalizer = SourceIntentNormalizer(manifest, calibration)
    fret = torch.linspace(-10.0, 10.0, 30).unsqueeze(0)
    strike = -fret
    encoded = normalizer(fret, strike)
    assert encoded.shape == (1, 60)
    assert bool((encoded.abs() <= 1.0).all())
    assert normalizer.calibration_required


def test_offline_robust_calibration_and_identity() -> None:
    torch.manual_seed(211)
    manifest, _, _, _, _ = _profile()
    fret = torch.randn(256, 30) * 2.0 + 1.0
    strike = torch.randn(256, 30) * 0.5 - 0.25
    calibration = calibrate_source_intent(
        manifest,
        fret_mean_samples=fret,
        strike_mean_samples=strike,
    )
    assert calibration.status == CALIBRATED
    assert len(calibration.sha256()) == 64
    normalizer = SourceIntentNormalizer(manifest, calibration)
    encoded = normalizer(fret[:8], strike[:8])
    assert encoded.shape == (8, 60)
    assert bool(torch.isfinite(encoded).all())
    assert bool((encoded.abs() <= 1.0).all())
    assert not normalizer.calibration_required
    assert normalizer.checkpoint_manifest()["calibration_sha256"] == (
        calibration.sha256())


def test_calibration_rejects_wrong_source_contract() -> None:
    manifest, _, _, _, _ = _profile()
    calibration = SourceIntentCalibration.fallback(manifest)
    wrong = SourceIntentCalibration(
        fret_action_names=(calibration.fret_action_names[1],
                           calibration.fret_action_names[0])
        + calibration.fret_action_names[2:],
        strike_action_names=calibration.strike_action_names,
        fret_checkpoint_sha256=calibration.fret_checkpoint_sha256,
        strike_checkpoint_sha256=calibration.strike_checkpoint_sha256,
        fret_center=calibration.fret_center,
        fret_scale=calibration.fret_scale,
        strike_center=calibration.strike_center,
        strike_scale=calibration.strike_scale,
        status=CALIBRATION_REQUIRED,
    )
    try:
        SourceIntentNormalizer(manifest, wrong)
    except ValueError as error:
        assert "names" in str(error)
    else:
        raise AssertionError("wrong action order was accepted")


def main() -> None:
    tests = (
        test_fallback_is_explicit_and_bounded,
        test_offline_robust_calibration_and_identity,
        test_calibration_rejects_wrong_source_contract,
    )
    for test in tests:
        test()
    print(f"{len(tests)} source-intent tests passed")


if __name__ == "__main__":
    main()

