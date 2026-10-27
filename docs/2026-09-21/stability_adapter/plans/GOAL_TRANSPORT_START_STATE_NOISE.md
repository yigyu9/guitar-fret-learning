# Goal-conditioned TRANSPORT start-state noise

## Goal

Prevent the arm policy from overfitting to one serialized functional-grip
state while keeping the contact-sensitive hand and strap boundary valid.

## Contract

- Sample per episode and per environment with the environment's seeded torch
  generator.
- Guitar root position: independent uniform noise within +/-2 mm per world
  axis.
- Guitar root orientation: random-axis rotation with angle within +/-0.5 deg.
- Controlled arm state: independent uniform noise within +/-0.5 deg on the
  nine distal L_Thorax-descendant slots only.
- Keep proximal torso/thorax state, all hand DOFs/targets, root velocities,
  and strap state unchanged.
- Rebuild contact for eight held-action physics frames and require three
  consecutive valid terminal frames.  Resample only invalid environments at
  decreasing noise scales; retain valid environments.  The last scale is the
  exact snapshot, so large vector batches fail closed to a valid grip instead
  of discarding noise from every environment.

## Verification

- [x] Pure noise-bound and seeded-reproducibility tests.
- [x] Existing goal-transport tests.
- [x] Existing GRIP/REACH compatibility tests.
- [x] Eight-environment noisy restore probe.
- [x] Collision-filter setup executes once across repeated noise retries.
- [x] Two-environment noisy restore and PPO smoke.
- [x] Cached-snapshot smoke.
- [x] Independent change review.
