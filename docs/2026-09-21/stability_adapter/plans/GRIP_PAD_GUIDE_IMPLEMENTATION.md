# GRIP pad-guide implementation

## Goal

Replace fingertip-body-origin guidance with explicit distal-pad contact regions
for thumb, index, and middle, then retrain and render the result.

## Checklist

- [x] Calibrate fixed distal-pad points from the authored collider meshes.
- [x] Define thumb underside and index/middle top-face guide patches.
- [x] Use pad-to-patch distance, approach normal, and raw contact in phase gates.
- [x] Require signed pad alignment and distal-body signed normal force.
- [x] Remove the elapsed-time fallback from the thumb-close gate.
- [x] Expose pad deltas/alignment to the policy without changing unrelated state.
- [x] Render target patches and measured pad points in the diagnostic video.
- [x] Run safety probe and 20,000-update behavior cloning.
- [x] Render teacher and learner-only videos and verify provenance.
- [x] Complete independent change review (P0/P1 none; documentation P2 fixed).

## Acceptance

- Arm targets remain frozen after pre-pinch entry.
- Index and middle each enter their own hover patch before closing.
- Thumb closes only after an opposing finger contact is measured.
- Active contact forces remain inside configured safety limits.
- Checkpoint and video metadata match the exact controller source hashes.

## Result

The implementation and artifact checks are complete, but the physical
acceptance criteria are not. With signed alignment enabled, the teacher stayed
in `WRAP_THUMB` and failed the overload gate at frame 3,615 before any distal
pad established normal force. The learned policy failed at frame 140. All
outputs therefore remain explicitly non-promotable diagnostics.
