# Stability GRIP safety training and evaluation

## Goal

Train the safety-gated GRIP residual policy from the current free-guitar,
strapped environment, render the full sequence from WAIT, and analyze the
resulting physical trace without promoting an unsuccessful checkpoint.

## Checklist

- [x] Run long teacher/recovery/DAgger training into a new output directory.
- [x] Validate checkpoint v5 metadata, source hashes, and rollout outcomes.
- [x] Render a clean full-sequence video from WAIT through terminal state.
- [x] Preserve frame-level JSONL diagnostics beside the video.
- [x] Analyze phase dwell, thumb acquisition, contact force, overload, and exit.
- [x] Record an evidence-backed result summary.
- [x] Complete independent change/artifact review.

## Success criteria

- Training runs to completion without overwriting earlier checkpoints.
- Video begins at WAIT and includes the terminal outcome.
- Analysis distinguishes optimization loss from physical grip success.
- Failed physical promotion remains closed and is reported explicitly.
