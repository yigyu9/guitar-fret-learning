# Stability Adapter support-wrench v2 long training

## Goal

Train a fresh goal-transport PPO checkpoint against the current support-wrench
environment, render an official result video from the authored WAIT boundary,
and analyze both training and rollout diagnostics.

## Success criteria

- [x] Complete a fresh 200-update PPO run without source/snapshot contract
  errors (4-env completion after the 8-env restore failures were preserved).
- [x] Preserve the training metrics and final checkpoint under
  `docs/2026-09-21/stability_adapter/transport/goal_ppo_v1/runs/20260927_support_wrench_v2_env4/`.
- [x] Evaluate the final checkpoint deterministically and record phase, grip,
  guitar-displacement, target-error, controller-saturation, and termination data.
- [ ] Render the official continuous video from WAIT through acquisition and
  transport. The live WAIT→REACH path failed; the saved full-phase video is
  explicitly marked diagnostic because it contains a validated snapshot boundary.
- [x] Summarize the observed bottleneck and the next concrete change, without
  claiming success from reward alone.

## Execution

1. Run 200 PPO updates (8 environments, 256-step rollout) from scratch.
2. Build/verify a full-sequence recorder that starts at the authored release.
3. Render the deterministic final rollout and write a machine-readable trace.
4. Analyze the JSONL training log and rollout trace; update the result note.
5. Run focused tests and request an independent change review for any new code.
