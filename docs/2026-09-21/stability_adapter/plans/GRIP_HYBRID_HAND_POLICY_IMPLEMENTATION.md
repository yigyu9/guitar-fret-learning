# GRIP hybrid hand-policy implementation

## Goal

Prevent autoregressive whole-arm drift by retaining deterministic arm control
and learning only phase-masked left-hand targets around the WRAP reference.

## Checklist

- [x] Add latch and active-digit state to the observation contract.
- [x] Change the policy contract from 152→36 to 158→21.
- [x] Use WRAP-reference hand residuals instead of previous-action residuals.
- [x] Apply per-phase thumb/index/middle action masks at runtime and in loss.
- [x] Clamp normalized observations and raise the standard-deviation floor.
- [x] Add a bounded noisy teacher rollout for recovery-state samples.
- [x] Archive the incompatible whole-body BC checkpoint and video.
- [x] Train 20,000 updates and render the learned hybrid rollout.
- [x] Verify source/checkpoint/video hashes and complete independent review.

## Acceptance

- The learned rollout keeps deterministic arm ownership.
- No learned output can move an inactive digit chain.
- The policy reaches thumb hover without the previous upward arm divergence.
- Failed physical grip remains explicitly non-promotable.

## Result

- 20,000 updates, 11,940 active-chain samples, final masked MSE
  `1.01354794423969e-6`.
- The learned rollout completed 6,000 frames without environment failure and
  latched thumb hover.
- It stalled in `WRAP_FINGERS`; index and middle were not latched and physical
  grip did not succeed. This artifact remains non-promotable.
