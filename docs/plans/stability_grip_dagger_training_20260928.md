# Stability GRIP DAgger long training

## Configuration

- Final optimization: 50,000 updates.
- Teacher data: one nominal and one noisy recovery rollout.
- Closed-loop data: one full learner-state DAgger rollout.
- Output: `docs/2026-09-21/stability_adapter/grip/closed_loop_dagger_v1/`.

## Checklist

- [x] Train and save the schema-v4 checkpoint with source hashes.
- [x] Verify finite tensors and checkpoint/report hash identity.
- [x] Run a closed-loop learned-policy diagnostic rollout.
- [x] Verify video/JSONL trace hashes and frame counts.
- [x] Analyze phase/subphase duration, force, motion, active owner, and gates.
- [x] Run focused regression tests and independent review.

## Success criteria

- The learner reaches `training_success=true` without environment failure,
  overload, or timeout.
- The final support has a valid thumb plus at least two opposing fingers and
  completes the functional dwell.
- If the rollout fails, the report identifies the dominant failed gate and
  owner/subphase where progress stopped; no checkpoint is promoted.
