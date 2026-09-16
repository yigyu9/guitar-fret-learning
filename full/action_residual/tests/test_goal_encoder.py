"""Executable tests for the semantic 128D goal/score encoder.

Run directly without a pytest dependency::

    python full/action_residual/tests/test_goal_encoder.py
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from full.action_residual.goal_encoder import (  # noqa: E402
    GoalScoreBatch,
    GoalScoreEncoder,
)


def _batch(batch_size: int = 3) -> GoalScoreBatch:
    slots = 4
    strings = 6
    event_valid = torch.tensor(
        [[True, True, False, False]], dtype=torch.bool).expand(
            batch_size, -1).clone()
    times = torch.zeros(batch_size, slots, 5)
    times[:, 0] = torch.tensor([-0.1, -0.05, 0.2, 0.7, 1.0])
    times[:, 1] = torch.tensor([0.3, 0.35, 0.5, 0.9, 1.2])

    states = torch.zeros(batch_size, slots, strings, dtype=torch.long)
    frets = torch.zeros(batch_size, slots, strings)
    fingers = torch.zeros(batch_size, slots, strings, dtype=torch.long)
    audible = torch.zeros(batch_size, slots, strings, dtype=torch.bool)
    traversal = torch.zeros(batch_size, slots, strings, dtype=torch.bool)
    offsets = torch.zeros(batch_size, slots, strings)

    states[:, 0, 1] = 2  # FRETTED with index finger.
    frets[:, 0, 1] = 0.25
    fingers[:, 0, 1] = 1
    traversal[:, 0, 1] = True
    audible[:, 0, 1] = True

    states[:, 1, 2] = 2  # Future two-string strum.
    states[:, 1, 3] = 2
    frets[:, 1, 2] = 0.4
    frets[:, 1, 3] = 0.6
    fingers[:, 1, 2] = 2
    fingers[:, 1, 3] = 3
    traversal[:, 1, 2:4] = True
    audible[:, 1, 2:4] = True
    offsets[:, 1, 3] = 0.04

    direction = torch.zeros(batch_size, slots, dtype=torch.long)
    direction[:, :2] = 1  # DOWN
    gesture = torch.zeros(batch_size, slots, dtype=torch.long)
    gesture[:, 1] = 1  # STRUM
    atomic = torch.zeros(batch_size, slots, dtype=torch.bool)
    atomic[:, 1] = True

    return GoalScoreBatch(
        song_progress=torch.linspace(0.1, 0.9, batch_size),
        beat_phase_radians=torch.linspace(0.0, 3.0, batch_size),
        bar_phase_radians=torch.linspace(0.2, 5.0, batch_size),
        tempo_ratio=torch.ones(batch_size),
        clock_running=torch.ones(batch_size, dtype=torch.bool),
        timeline_valid=torch.ones(batch_size, dtype=torch.bool),
        event_valid=event_valid,
        event_times_seconds=times,
        string_state=states,
        target_fret_normalized=frets,
        finger_id=fingers,
        audible_mask=audible,
        traversal_mask=traversal,
        strike_direction=direction,
        strike_offsets_seconds=offsets,
        gesture=gesture,
        atomic_event=atomic,
    )


def _assert_raises(error_type: type[BaseException], fragment: str,
                   function: object) -> None:
    try:
        function()  # type: ignore[operator]
    except error_type as error:
        assert fragment in str(error), str(error)
    else:
        raise AssertionError(f"expected {error_type.__name__}: {fragment}")


def test_layout_and_exact_invalid_zero() -> None:
    torch.manual_seed(31)
    encoder = GoalScoreEncoder()
    with torch.no_grad():
        for layer in encoder.event_token_encoder.network:
            if isinstance(layer, torch.nn.Linear):
                layer.bias.fill_(0.37)
    batch = _batch()
    encoded = encoder.encode(batch)

    assert encoded.context.shape == (3, 128)
    assert encoded.global_clock.shape == (3, 8)
    assert encoded.raw_events.shape == (3, 4, 85)
    assert encoded.event_tokens.shape == (3, 4, 30)
    assert torch.equal(encoded.context, encoder(batch))
    assert torch.equal(
        encoded.raw_events[:, 2:], torch.zeros_like(encoded.raw_events[:, 2:]))
    assert torch.equal(
        encoded.event_tokens[:, 2:],
        torch.zeros_like(encoded.event_tokens[:, 2:]))
    assert bool(torch.isfinite(encoded.context).all())

    # Global encoding is deterministic and tempo ratio 1.0 is centered at 0.
    assert torch.equal(encoded.global_clock[:, 0], batch.song_progress)
    assert torch.equal(
        encoded.global_clock[:, 5], torch.zeros(batch.song_progress.shape))
    assert torch.equal(encoded.global_clock[:, 6:], torch.ones(3, 2))


def test_shared_event_encoder_and_85d_field_offsets() -> None:
    torch.manual_seed(37)
    encoder = GoalScoreEncoder()
    batch = _batch(batch_size=1)

    # Make current and next-1 semantically identical.  Slot position is only
    # conveyed by concatenation order; the shared encoder must return the same
    # token for equal event records.
    duplicate = replace(
        batch,
        event_times_seconds=batch.event_times_seconds.clone(),
        string_state=batch.string_state.clone(),
        target_fret_normalized=batch.target_fret_normalized.clone(),
        finger_id=batch.finger_id.clone(),
        audible_mask=batch.audible_mask.clone(),
        traversal_mask=batch.traversal_mask.clone(),
        strike_direction=batch.strike_direction.clone(),
        strike_offsets_seconds=batch.strike_offsets_seconds.clone(),
        gesture=batch.gesture.clone(),
        atomic_event=batch.atomic_event.clone(),
    )
    for field in (
            "event_times_seconds", "string_state", "target_fret_normalized",
            "finger_id", "audible_mask", "traversal_mask",
            "strike_direction", "strike_offsets_seconds", "gesture",
            "atomic_event"):
        value = getattr(duplicate, field)
        value[:, 1] = value[:, 0]

    encoded = encoder.encode(duplicate)
    assert torch.equal(encoded.raw_events[:, 0], encoded.raw_events[:, 1])
    assert torch.equal(encoded.event_tokens[:, 0], encoded.event_tokens[:, 1])

    raw = encoded.raw_events[0, 0]
    # 1 valid + 5 time + 24 state + 6 fret + 24 finger + 6 audible
    # + 6 traversal + 3 direction + 6 offset + 3 gesture + 1 atomic.
    assert raw.numel() == 1 + 5 + 24 + 6 + 24 + 6 + 6 + 3 + 6 + 3 + 1
    assert raw[0].item() == 1.0
    assert torch.count_nonzero(raw[6:30]).item() == 6  # one state/string
    assert torch.count_nonzero(raw[30:36]).item() == 1
    assert torch.count_nonzero(raw[36:60]).item() > 0


def test_schema_is_checkpointed_and_enforced() -> None:
    torch.manual_seed(41)
    source = GoalScoreEncoder()
    expected = source(_batch(batch_size=1))
    state = deepcopy(source.state_dict())
    assert "_extra_state" in state
    schema = state["_extra_state"]
    assert schema["architecture_id"] == GoalScoreEncoder.ARCHITECTURE_ID
    assert schema["dimensions"]["output"] == 128
    assert schema["canonical_string_order"] == [
        "high_e", "B", "G", "D", "A", "low_E"]
    assert sum(field["size"] for field in schema["raw_event_layout"]) == 85
    assert len(schema["schema_sha256"]) == 64

    restored = GoalScoreEncoder()
    restored.load_state_dict(state, strict=True)
    assert torch.equal(expected, restored(_batch(batch_size=1)))

    damaged = deepcopy(state)
    damaged["_extra_state"]["schema_version"] = 99
    _assert_raises(
        RuntimeError,
        "checkpoint schema mismatch",
        lambda: GoalScoreEncoder().load_state_dict(damaged, strict=True),
    )


def test_strict_shape_range_finite_and_semantic_validation() -> None:
    encoder = GoalScoreEncoder()
    base = _batch(batch_size=1)

    _assert_raises(
        ValueError, "song_progress must be in [0, 1]",
        lambda: encoder(replace(base, song_progress=torch.tensor([1.1]))))
    _assert_raises(
        ValueError, "finger_id IDs must be in [0, 4]",
        lambda: encoder(replace(
            base, finger_id=torch.full_like(base.finger_id, 7))))
    _assert_raises(
        ValueError, "event_times_seconds must be finite",
        lambda: encoder(replace(
            base,
            event_times_seconds=base.event_times_seconds.clone().fill_(
                float("nan")))))
    _assert_raises(
        ValueError, "event_valid must have shape",
        lambda: encoder(replace(base, event_valid=base.event_valid[:, :3])))

    bad_padding = base.strike_direction.clone()
    bad_padding[:, 3] = 1
    _assert_raises(
        ValueError, "strike_direction must be zero/false",
        lambda: encoder(replace(base, strike_direction=bad_padding)))

    missing_finger = base.finger_id.clone()
    missing_finger[:, 0, 1] = 0
    _assert_raises(
        ValueError, "FRETTED string requires",
        lambda: encoder(replace(base, finger_id=missing_finger)))

    audible_without_crossing = base.traversal_mask.clone()
    audible_without_crossing[:, 0, 1] = False
    _assert_raises(
        ValueError, "audible_mask must be a subset",
        lambda: encoder(replace(base, traversal_mask=audible_without_crossing)))


def test_gradients_reach_anatomical_finger_embeddings_only() -> None:
    torch.manual_seed(43)
    encoder = GoalScoreEncoder()
    output = encoder(_batch(batch_size=2))
    output.square().mean().backward()
    gradient = encoder.finger_embedding.weight.grad
    assert gradient is not None
    assert torch.equal(gradient[0], torch.zeros_like(gradient[0]))
    assert bool((gradient[1:4].abs().sum(dim=-1) > 0).all())


def main() -> None:
    tests = (
        test_layout_and_exact_invalid_zero,
        test_shared_event_encoder_and_85d_field_offsets,
        test_schema_is_checkpointed_and_enforced,
        test_strict_shape_range_finite_and_semantic_validation,
        test_gradients_reach_anatomical_finger_embeddings_only,
    )
    for test in tests:
        test()
    print(f"{len(tests)} goal encoder tests passed")


if __name__ == "__main__":
    main()
