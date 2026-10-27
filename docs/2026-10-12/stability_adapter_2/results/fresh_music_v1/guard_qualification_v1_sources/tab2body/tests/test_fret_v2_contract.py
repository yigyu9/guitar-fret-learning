"""CPU contracts for the 420D Fret-v2 observation and block policy."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.fret_v2_contract import (  # noqa: E402
    FRET_V1_OBSERVATION_CONTRACT,
    FRET_V2_BLOCK_SIZES,
    FRET_V2_BLOCK_SLICES,
    FRET_V2_OBSERVATION_CONTRACT,
    FRET_V2_OBSERVATION_DIM,
    fret_v2_block_manifest,
    pack_fret_v2_blocks,
)
from tab2body.learning.fret_v2_model import (  # noqa: E402
    FRET_V2_ENCODER_WIDTHS,
    FRET_V2_MODEL_ARCHITECTURE,
    FretV2ActorCritic,
    fret_actor_critic_class,
)
from tab2body.learning.models import ActorCritic  # noqa: E402


def expect_error(fragment, callback, error_type=ValueError):
    try:
        callback()
    except error_type as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(
            f"expected {error_type.__name__} containing {fragment!r}")


def main():
    names = tuple(f"left_joint_{index:02d}" for index in range(30))
    manifest = fret_v2_block_manifest(names)
    assert tuple(manifest) == tuple(FRET_V2_BLOCK_SIZES)
    assert sum(map(len, manifest.values())) == FRET_V2_OBSERVATION_DIM == 420
    assert len({field for block in manifest.values() for field in block}) == 420
    assert FRET_V2_BLOCK_SLICES["O_proprio"] == slice(0, 60)
    assert FRET_V2_BLOCK_SLICES["O_history"] == slice(390, 420)

    blocks = {
        name: torch.full((4, size), float(index + 1))
        for index, (name, size) in enumerate(FRET_V2_BLOCK_SIZES.items())
    }
    observation = pack_fret_v2_blocks(blocks)
    assert observation.shape == (4, 420)
    for index, name in enumerate(FRET_V2_BLOCK_SIZES):
        assert torch.all(
            observation[:, FRET_V2_BLOCK_SLICES[name]] == float(index + 1))

    missing = dict(blocks)
    missing.pop("O_readiness_contact")
    expect_error("missing", lambda: pack_fret_v2_blocks(missing))
    wrong = dict(blocks)
    wrong["O_phase"] = torch.zeros(4, 11)
    expect_error("[N,12]", lambda: pack_fret_v2_blocks(wrong))
    nonfinite = dict(blocks)
    nonfinite["O_synchronizer"] = torch.tensor(
        [[1.0, float("nan")]]).repeat(4, 1)
    expect_error(
        "NaN or Inf", lambda: pack_fret_v2_blocks(nonfinite),
        FloatingPointError)

    assert fret_actor_critic_class(FRET_V1_OBSERVATION_CONTRACT) is ActorCritic
    assert fret_actor_critic_class(
        FRET_V2_OBSERVATION_CONTRACT) is FretV2ActorCritic
    expect_error(
        "unsupported", lambda: fret_actor_critic_class("fret.unknown"))

    neutral = torch.linspace(-0.5, 0.5, 30)
    model = FretV2ActorCritic(
        420, 30, value_dim=6, init_std=0.04, init_mean=neutral)
    assert model.MODEL_ARCHITECTURE_VERSION == FRET_V2_MODEL_ARCHITECTURE
    assert tuple(model.actor.encoders) == tuple(FRET_V2_BLOCK_SIZES)
    assert tuple(FRET_V2_ENCODER_WIDTHS) == tuple(FRET_V2_BLOCK_SIZES)
    action, log_prob, value = model.act(
        torch.zeros(5, 420), deterministic=True)
    assert action.shape == (5, 30)
    assert log_prob.shape == (5,)
    assert value.shape == (5, 6)
    assert torch.isfinite(action).all()
    assert torch.isfinite(log_prob).all()
    assert torch.isfinite(value).all()
    assert torch.allclose(action[0], neutral, atol=1e-6, rtol=1e-6)
    expect_error(
        "obs_dim=420", lambda: FretV2ActorCritic(419, 30))

    print("PASS: Fret-v2 420D ABI and block-encoded policy")


if __name__ == "__main__":
    main()
