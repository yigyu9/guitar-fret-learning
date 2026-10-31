# Stability adapter support-wrench v2 implementation plan

## Objective

Make the 0 mm SUPPORT target independent of reset noise and give the arm a
bounded deterministic way to oppose the routed strap wrench.  Preserve PPO as
a residual policy instead of asking it to discover the complete static load.

## Success criteria

- Nonzero episode-start noise never changes the unperturbed target pose.
- Arm commands expose separate pose-servo, wrench feed-forward, integrator,
  policy-residual, rate-limit, tracking-limit, and joint-limit diagnostics.
- Position integration runs only with a force-valid grip and uses anti-windup.
- Every success gate and settle-streak reset cause is present in frame traces.
- An A/B probe can compare controller-only combinations from the same snapshot.
- User-facing result recordings start at WAIT; snapshot recordings are labeled
  diagnostic-only.

## Checklist

- [x] Separate unperturbed target pose from the perturbed start pose.
- [x] Add bounded strap-wrench feed-forward and support-error integrator.
- [x] Remove conflicting implicit support target behavior.
- [x] Add controller authority and per-gate diagnostics.
- [x] Add same-snapshot A/B diagnostic runner.
- [x] Enforce diagnostic/full-sequence video labeling.
- [x] Add focused tests and run validation.
- [x] Complete an independent change review.
