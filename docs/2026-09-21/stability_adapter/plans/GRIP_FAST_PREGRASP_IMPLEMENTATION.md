# Fast multi-digit pre-grasp implementation

## Problem statement

The hybrid hand policy removed whole-arm divergence, but the 6,000-frame
rollout still needed 100 seconds and stopped in `WRAP_FINGERS`. Final
thumb/index/middle errors were `1.695 / 2.693 / 5.841 cm`. The middle-finger
error is outside a reasonable local finger correction, while the controller
freezes the distal arm after thumb acquisition. More behavior-cloning updates
cannot fix this reachability conflict because the source teacher also fails.

## Control redesign

1. Preserve the proximal torso/thorax action and restrict any arm correction
   to the existing nine distal shoulder/elbow/wrist slots.
2. After thumb acquisition, move index and middle simultaneously instead of
   serially. Their latch eligibility depends on thumb, not on each other.
3. Keep the validated distal-arm contact pose during `WRAP_FINGERS`. Two GPU
   probes showed that shared pad-error arm correction removes palm contact and
   worsens finger alignment even when bounded; it is therefore rejected.
4. Retain the existing distal-only palm-force relief without exposing any
   torso/thorax action.
5. Use distance-adaptive finger IK and a larger collision-free hover rate;
   retain a low rate for near-surface closing.
6. Reduce geometric latch/settle dwell only after preserving motion, force,
   alignment, and retention gates.
7. Validate the deterministic teacher before training. A failed teacher may
   supply an explicitly non-promotable diagnostic BC dataset, but cannot
   produce a promotable checkpoint.
8. Train the existing 158→21 phase-masked hybrid hand policy with exact and
   noisy-recovery teacher rollouts, then render a learned closed-loop rollout.

## Target timing and safety

- Thumb hover: ≤ 2 seconds after the WRAP reset.
- Index and middle hover: simultaneous, ≤ 6 seconds total.
- Enter `GRIP_CLOSE`: ≤ 10 seconds total.
- Desired full diagnostic budget: 1,800 control frames (30 seconds), rather
  than the previous 6,000-frame/100-second timeout. The geometric pre-grasp
  itself must finish substantially earlier than the full close/hold budget.
- Preserve all existing overload, wrong-contact, guitar-motion, and
  ring/pinky exclusion gates.
- A teacher or learned checkpoint remains non-promotable unless the 120-frame
  physical hold criterion passes.

## Checklist

- [x] Add parallel index/middle ownership and latch logic.
- [x] Add adaptive hover/close action rates.
- [x] Probe and reject destabilizing multi-pad distal-arm correction.
- [x] Preserve the validated distal-only palm-force relief.
- [x] Add/update regression tests.
- [x] Run deterministic teacher probes and inspect phase/error/force.
- [x] Train the hybrid hand policy on the improved teacher and recovery data.
- [x] Render and verify the learned rollout and provenance.
- [x] Complete independent change review.

## Acceptance

- No torso/thorax command drift.
- No environment failure or overload.
- Faster than the prior 100-second rollout.
- Both index and middle errors improve materially; any unmet grip gate is
  reported explicitly rather than promoted.

## Result

- Teacher: thumb latch frame 192, middle 712, index 787, `GRIP_CLOSE` frame
  797 (13.3 seconds), with no environment failure or overload.
- The stretch timing targets (thumb ≤2 seconds, both fingers ≤6 seconds,
  close ≤10 seconds) were not met. Close entry nevertheless improved by about
  67% from the previous frame 2,390 result.
- Learned rollout: all three latches and `GRIP_CLOSE` within the 1,800-frame
  budget, no environment failure or overload.
- Middle contact and directional digit force remain absent. Physical grip and
  promotion therefore remain false.
