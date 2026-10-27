# Stability Adapter REACH/GRIP training and render

## Goal

Train the revised functional-grip policy long enough to fit the nominal and
recovery demonstrations, render and evaluate the learned GRIP result, and
analyze the rollout with source/checkpoint/video provenance.

## Outputs

- Checkpoint and training report under
  `docs/2026-09-21/stability_adapter/grip/reach_grip_speedup_v1/checkpoints/`.
- Full WAIT→REACH→WRAP→GRIP teacher-reference video and summary sidecar under
  `docs/2026-09-21/stability_adapter/grip/reach_grip_speedup_v1/rollouts/`.
- Post-REACH learned-policy diagnostic videos and summary sidecars in the same
  directory. Per-frame raw traces are not retained by these recorders.
- Analysis summary beside the rollout.

## Checklist

- [x] Verify the current teacher reaches safe functional grip.
- [x] Train three 30,000-update BC variants with recovery rollouts.
- [x] Verify checkpoint identity, source hashes, and finite tensors.
- [x] Render failed learned-policy rollouts and a successful full WAIT→GRIP
  teacher reference.
- [x] Analyze phase duration, contact force, load, motion, and failure flags.
- [x] Run focused tests and independent change review.

## Success criteria

- The saved teacher demonstration has `training_success=true`.
- The learned rollout reaches functional grip without overload,
  environment failure, or policy failure.
- The video begins at WAIT and contains the visible REACH and GRIP motion.
- Every report records current environment, source, checkpoint, and video
  hashes.

## Result

The teacher criteria are satisfied, but the learned closed-loop success
criterion is not. The learned diagnostic videos begin at the validated
post-REACH snapshot; the successful teacher reference begins at WAIT and
records an explicit simulator/state replacement at the WAIT→REACH boundary.
See `ANALYSIS.md` in the output directory for the evidence and next action.
