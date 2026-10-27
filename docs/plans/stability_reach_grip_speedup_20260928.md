# Stability Adapter REACH/GRIP speed-up

## Goal

Reduce REACH and functional-GRIP acquisition time without weakening overload
or contact-region safety, and determine whether the right arm is an obstacle
or a required part of the initial free-guitar equilibrium.

## Checklist

- [x] Test right-arm/guitar and right-arm/neck collision isolation on GPU.
- [x] Reject isolation after it prevents the source WAIT equilibrium.
- [x] Reorder force closure around the actual transport-entry contract.
- [x] Use gap-dependent fast/mid/near hand target rates.
- [x] Expose functional grip as the training success signal and reward it.
- [x] Shorten redundant REACH settle/hold dwell without enlarging unsafe steps.
- [x] Fix the thumb-path support gate and below-minimum LOAD pressure deadlock.
- [x] Add focused CPU tests and run GPU REACH/GRIP A/B smoke checks.
- [x] Request independent change review.

## Success criteria

- Right-hand support remains enabled because removing it prevents WAIT settle;
  the right hand is not treated as the cause of the REACH/GRIP delay.
- Functional acquisition prioritizes index, middle, then thumb.
- Near-contact rate and all overload termination limits remain unchanged.
- Teacher rollout reaches functional grip faster than the 3,429-frame baseline.
- REACH prerequisite is faster than the 1,199-frame baseline.
- Existing source environment, strap route, and Synchronizer assets are not
  changed.

## Verified result

- REACH prerequisite: 1,077 frames (baseline 1,199, 10.2% reduction).
- Functional GRIP: success at 2,712 frames (baseline still unsuccessful at
  3,429 frames).
- Functional support set: thumb + index + middle, 8-frame dwell.
- Final conservative hand load: 4.99 N; no overload, policy failure, or
  environment failure.
- Evidence: `docs/2026-09-21/stability_adapter/diagnostics/reach_grip_speedup_smoke_v1.json`.
- Independent change review: PASS, no remaining blocker or major finding.
