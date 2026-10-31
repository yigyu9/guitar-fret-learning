# Stability GRIP long training and analysis

## Experiment

- Train from scratch with the current gap-adaptive TOUCH controller.
- Use 50,000 optimizer updates, two noisy recovery rollouts, and two DAgger
  rollouts so that the policy sees nominal, perturbed, and learner-visited
  states.
- Keep seed 17 and the validated initial-environment identity for comparable
  diagnostics.
- Store the checkpoint, complete WAIT-starting video, frame trace, and analysis
  under `docs/2026-09-21/stability_adapter/grip/gap_adaptive_touch_v1/long_training_v1`.

## Checklist

- [x] Confirm the current teacher and checkpoint contract.
- [x] Collect nominal/recovery/DAgger samples and train for 50,000 updates.
- [x] Render a WAIT-to-terminal learned-policy rollout.
- [x] Compare training loss, terminal reason, stage duration, proximity, force,
      retry, and overload metrics against the teacher diagnostic.
- [x] Record conclusions and the exact reproduction commands.
- [x] Complete independent change review.

## Success criteria

- The checkpoint is finite, source-bound, and reproducible.
- The full-sequence recorder accepts the checkpoint without contract bypasses.
- The learned rollout produces non-zero thumb normal force and opposing force,
  then reaches functional GRIP or TRANSPORT without overload.
- If it does not, the report must distinguish policy imitation error from the
  teacher/contact-geometry limitation.
