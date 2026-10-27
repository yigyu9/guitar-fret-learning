# Goal-conditioned TRANSPORT PPO implementation

## Goal

Replace failed-teacher behavior cloning as the primary TRANSPORT learning path
with direct 9-DoF arm control from a reusable functional-grip snapshot.

## Assumptions

- The deterministic acquisition controller remains responsible only for
  producing and validating the initial functional-grip snapshot.
- During TRANSPORT, the 21 hand targets and the six proximal torso/base arm
  targets remain fixed.  The hand target adds a bounded regrip impedance bias
  to the measured grip pose so a restored simulator can reconstruct contact
  force instead of depending on a non-serialized PhysX contact manifold.
- The learned policy owns only the nine distal L_Thorax-descendant arm targets.
- Existing strap, collision, TRANSPORT overload, grip-loss, and pose-success
  contracts remain authoritative.  GRIP's acquisition-only 40 N whole-hand
  ceiling remains diagnostic after the boundary; stable high load is allowed,
  while persistent 120 N digit/250 N hand load and dynamic impact stay terminal.

## Success criteria

- [x] Capture and restore a functional-grip physics/control snapshot without
  replaying WAIT, REACH, or GRIP for every episode.
- [x] Accept a bounded 9D joint-target delta without a teacher action.
- [x] Use dense position and rotation progress rewards, goal-local settling,
  grip retention, and hard safety termination.
- [x] Provide a 5, 10, 20, and 50 mm curriculum with 0, 0, 5, and 15 degree
  rotation steps.
- [x] Add a GPU-parallel PPO trainer with checkpoint provenance and no
  failed-teacher imitation loss.
- [x] Add pure unit tests and a short GPU smoke test.
- [x] Complete independent change review.

## Non-goals

- Do not delete or silently promote the existing diagnostic BC checkpoints.
- Do not train the hand policy jointly with TRANSPORT in this iteration.
- Do not connect an unverified checkpoint to Synchronizer or MAINTAIN.
