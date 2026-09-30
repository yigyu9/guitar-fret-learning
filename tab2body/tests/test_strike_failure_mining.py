from pathlib import Path
import sys

import torch


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tab2body.env.metrics import (
    bounded_failure_sampling_probabilities,
    event_failure_window_scores,
    event_predecessor_rehearsal_scores,
    event_mask_window_scores,
    update_event_failure_statistics,
)
from tab2body.learning.ppo import aggregate_episode_rows
from tab2body.learning.strike_curriculum import (
    S3_SONG_INTEGRATION,
    STRIKE_STAGES,
    StrikeCurriculum,
    StrikeCurriculumConfig,
)
from tab2body.strike_cfg import STRIKE


def curriculum_config():
    return StrikeCurriculumConfig(
        min_iterations={stage: 1 for stage in STRIKE_STAGES},
        max_iterations={stage: 5 for stage in STRIKE_STAGES},
        promotion_windows=1,
        terminal_evidence_episodes=1,
        s2_profiles=tuple(STRIKE["curriculum"]["s2_profiles"]),
        tempo_lambdas=tuple(STRIKE["curriculum"]["tempo_lambdas"]),
        s3_tempo_gates=tuple(STRIKE["curriculum"]["s3_tempo_gates"]),
        s3_uniform_curriculum_evidence_only=True,
    )


def evidence_row(f1, *, eligible):
    return {
        "strike_uniform_evidence_eligible": float(eligible),
        "strike_episode_f1": float(f1),
        "strike_true_positive_count": float(f1 > 0.5),
        "strike_false_positive_count": float(f1 <= 0.5),
        "strike_false_negative_count": float(f1 <= 0.5),
    }


def complete_curriculum_evidence(value):
    from tab2body.tests.test_strike_stage_curriculum import base

    row = base()
    row["strike_episode_f1"] = value
    if value < 1.0:
        row["strike_true_positive_count"] = value
        row["strike_false_positive_count"] = 1.0 - value
        row["strike_false_negative_count"] = 1.0 - value
    return row


def main():
    assert STRIKE["curriculum"]["stalled_hard_sample_fraction"] == 0.50
    assert STRIKE["curriculum"]["stalled_hard_rehearsal_events"] == 4
    assert STRIKE["curriculum"]["s3_upstroke_sample_fraction"] == 0.0
    failure = torch.zeros(4)
    exposure = torch.zeros(4)
    indices = torch.tensor([0] * 100 + [1])
    exposed = torch.ones(indices.numel(), dtype=torch.bool)
    failed = torch.ones_like(exposed)
    updated = update_event_failure_statistics(
        failure, exposure, indices, exposed, failed,
        decay=0.995, prior_exposure=16.0)
    assert torch.allclose(
        updated["score"][:2], torch.ones(2), atol=1e-6)
    assert updated["score"].max() <= 1.0
    assert updated["exposure_mass"].tolist() == [100.0, 1.0, 0.0, 0.0]

    indices = torch.tensor([0] * 100 + [1] * 100)
    failed = torch.tensor([True] * 100 + [False] * 100)
    contrasted = update_event_failure_statistics(
        torch.zeros(4), torch.zeros(4), indices,
        torch.ones(200, dtype=torch.bool), failed,
        decay=1.0, prior_exposure=16.0)
    assert contrasted["score"][0] > 0.90
    assert contrasted["score"][1] < 0.10

    window_scores = event_failure_window_scores(
        torch.tensor([0.0, 0.0, 1.0, 0.0, 0.0]), 2)
    probabilities = bounded_failure_sampling_probabilities(
        window_scores, 0.30)
    assert abs(float(probabilities.sum()) - 1.0) < 1e-6
    assert float(probabilities.max()) <= 0.300001
    assert bool((probabilities > 0.0).all())

    full_song_failure = torch.zeros(42)
    full_song_failure[23] = 1.0
    rehearsal_scores = event_predecessor_rehearsal_scores(
        full_song_failure, 4)
    assert rehearsal_scores.shape == (39,)
    assert int(rehearsal_scores.argmax()) == 22
    assert rehearsal_scores[22].item() == 1.0

    upstroke_windows = event_mask_window_scores(
        torch.tensor([False, True, False, False, True]), 2)
    assert upstroke_windows.tolist() == [1.0, 1.0, 0.0, 1.0]
    upstroke_probabilities = bounded_failure_sampling_probabilities(
        upstroke_windows, 0.40)
    assert upstroke_probabilities[2] == 0.0
    assert abs(float(upstroke_probabilities.sum()) - 1.0) < 1e-6

    production = StrikeCurriculum(curriculum_config())
    assert production.config.s3_episode_event_counts == (
        8, 16, 32, 42, 42, 42, 42, 42)
    production.stage = S3_SONG_INTEGRATION
    expected_gates = (0.96, 0.96, 0.97, 0.975, 0.98, 0.985, 0.987, 0.99)
    for level, (count, gate) in enumerate(zip(
            production.config.s3_episode_event_counts, expected_gates)):
        production.tempo_level = level
        assert production.song_events_per_episode == count
        assert production.current_strike_f1_gate == gate

    rows = [
        evidence_row(1.0, eligible=True),
        evidence_row(0.0, eligible=False),
    ]
    aggregated = aggregate_episode_rows(
        rows,
        (
            "strike_uniform_evidence_eligible",
            "strike_episode_f1",
            "strike_true_positive_count",
            "strike_false_positive_count",
            "strike_false_negative_count",
        ),
        ())
    assert aggregated["episodes"] == 2
    assert aggregated["uniform_evidence_episodes"] == 1
    assert aggregated["hard_evidence_excluded_episodes"] == 1
    assert aggregated["strike_episode_f1"] == 0.5
    assert aggregated["_uniform_evidence"]["strike_episode_f1"] == 1.0

    curriculum = StrikeCurriculum(curriculum_config())
    curriculum.stage = S3_SONG_INTEGRATION
    curriculum.stalled = True
    mixed = complete_curriculum_evidence(0.0)
    mixed["_uniform_evidence"] = complete_curriculum_evidence(1.0)
    evidence = curriculum._consume_evidence(mixed)
    assert evidence is not None
    assert evidence["strike_episode_f1"] == 1.0

    print("PASS: exposure-normalized bounded Strike failure mining")


if __name__ == "__main__":
    main()
