# GRIP palm-align pre-shape implementation and training

## Goal

Move all five digit chains visibly and safely while the palm is still aligning,
then acquire palm force before allowing thumb/finger wrapping and closure.

## Phase contract

1. `PALM_ALIGN_PRESHAPE`: align the palm while moving all digits to targets
   target offsets outside their assigned neck faces, and require a measured
   30 mm minimum gap with no digit contact before advancing.
2. `PALM_CONTACT`: retain the collision-free pre-shape and move only the arm
   through the final palm-side contact gap.
3. `WRAP_THUMB`: move all digits toward hover patches; thumb remains the gate.
4. `WRAP_FINGERS`: finish the four front-face hover latches.
5. `WRAP_SETTLE`: verify a low-force pre-grasp.
6. `GRIP_CLOSE`: close locally toward directional contact.
7. `GRIP_HOLD`: accumulate the 120-frame hold.
8. `ACQUISITION_GRIP_READY`.

Loss of palm pose returns to phase 1. Loss of palm force with pose retained
returns only to phase 2, preserving pre-shape instead of reopening the hand.

## Checklist

- [x] Add eight-phase observation and phase gates.
- [x] Add phase-0/1 five-digit pre-shape ownership and IK targets.
- [x] Add palm contact dwell and pose/force-specific rollback.
- [x] Update policy dimensions, tests, trainer, recorder, and provenance.
- [x] Run static/unit checks and GPU teacher validation.
- [x] Train the 20,000-update recovery BC policy.
- [x] Render and inspect main and hand-closeup videos.
- [x] Complete independent change review.

## Success criteria

- All five digit chains receive nonzero commanded motion in phase 0.
- The rendered policy visibly changes finger pose before palm force is acquired.
- Palm-force loss does not force the hand back to the fully open reference.
- No overload, non-finite state, or false success promotion is allowed.
- Until successful-pose pad calibration and full collider clearance exist,
  `PAD_CALIBRATION_VALIDATED=false` remains a hard promotion blocker.
