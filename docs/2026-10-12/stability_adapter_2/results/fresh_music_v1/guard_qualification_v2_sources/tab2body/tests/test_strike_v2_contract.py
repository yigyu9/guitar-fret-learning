"""CPU contracts for the 303D Strike-v2 observation and block policy."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tab2body.learning.strike_v2_model import (  # noqa: E402
    STRIKE_V2_ENCODER_WIDTHS,
    STRIKE_V2_MODEL_ARCHITECTURE,
    StrikeV2ActorCritic,
    strike_actor_critic_class,
)
from tab2body.learning.models import ActorCritic  # noqa: E402
from tab2body.strike_v2_contract import (  # noqa: E402
    STRIKE_V1_OBSERVATION_CONTRACT,
    STRIKE_V2_BLOCK_SIZES,
    STRIKE_V2_BLOCK_SLICES,
    STRIKE_V2_OBSERVATION_CONTRACT,
    STRIKE_V2_OBSERVATION_DIM,
    pack_strike_v2_blocks,
    strike_v2_block_manifest,
)


def expect_error(fragment, callback, error_type=ValueError):
    try:
        callback()
    except error_type as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError(
            f"expected {error_type.__name__} containing {fragment!r}")


def main():
    names = tuple(f"joint_{index:02d}" for index in range(30))
    manifest = strike_v2_block_manifest(names)
    assert tuple(manifest) == tuple(STRIKE_V2_BLOCK_SIZES)
    assert sum(map(len, manifest.values())) == STRIKE_V2_OBSERVATION_DIM == 303
    assert len({field for block in manifest.values() for field in block}) == 303
    assert STRIKE_V2_BLOCK_SLICES["O_proprio"] == slice(0, 60)
    assert STRIKE_V2_BLOCK_SLICES["O_history"] == slice(273, 303)

    blocks = {
        name: torch.full((4, size), float(index + 1))
        for index, (name, size) in enumerate(STRIKE_V2_BLOCK_SIZES.items())
    }
    observation = pack_strike_v2_blocks(blocks)
    assert observation.shape == (4, 303)
    for index, name in enumerate(STRIKE_V2_BLOCK_SIZES):
        assert torch.all(
            observation[:, STRIKE_V2_BLOCK_SLICES[name]] == float(index + 1))

    missing = dict(blocks)
    missing.pop("O_recovery")
    expect_error("missing", lambda: pack_strike_v2_blocks(missing))
    wrong = dict(blocks)
    wrong["O_synchronizer"] = torch.zeros(4, 3)
    expect_error("[N,2]", lambda: pack_strike_v2_blocks(wrong))
    nonfinite = dict(blocks)
    nonfinite["O_synchronizer"] = torch.tensor(
        [[1.0, float("nan")]]).repeat(4, 1)
    expect_error(
        "NaN or Inf", lambda: pack_strike_v2_blocks(nonfinite),
        FloatingPointError)

    assert strike_actor_critic_class(
        STRIKE_V1_OBSERVATION_CONTRACT) is ActorCritic
    assert strike_actor_critic_class(
        STRIKE_V2_OBSERVATION_CONTRACT) is StrikeV2ActorCritic
    expect_error(
        "unsupported", lambda: strike_actor_critic_class("strike.unknown"))

    neutral = torch.linspace(-0.5, 0.5, 30)
    model = StrikeV2ActorCritic(
        303, 30, value_dim=1, init_std=0.04, init_mean=neutral)
    assert model.MODEL_ARCHITECTURE_VERSION == STRIKE_V2_MODEL_ARCHITECTURE
    assert tuple(model.actor.encoders) == tuple(STRIKE_V2_BLOCK_SIZES)
    assert tuple(STRIKE_V2_ENCODER_WIDTHS) == tuple(STRIKE_V2_BLOCK_SIZES)
    action, log_prob, value = model.act(
        torch.zeros(5, 303), deterministic=True)
    assert action.shape == (5, 30)
    assert log_prob.shape == (5,)
    assert value.shape == (5, 1)
    assert torch.isfinite(action).all()
    assert torch.isfinite(log_prob).all()
    assert torch.isfinite(value).all()
    # Zero observation reaches zero hidden activations, so the seeded output
    # bias must reproduce the requested neutral physical action.
    assert torch.allclose(action[0], neutral, atol=1e-6, rtol=1e-6)
    expect_error(
        "obs_dim=303", lambda: StrikeV2ActorCritic(302, 30))

    print("PASS: Strike-v2 303D ABI and block-encoded policy")


if __name__ == "__main__":
    main()
