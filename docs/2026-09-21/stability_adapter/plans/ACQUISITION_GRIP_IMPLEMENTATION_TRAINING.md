# Acquisition-centred GRIP implementation and training

## Goal

Apply the v2 acquisition-centred contact contract to the live StabilityAdapter
WRAP/GRIP environment, train the hybrid hand policy, and render an independent
evaluation rollout under `grip/acquisition_centered/`.

## Checklist

- [x] Load acquisition-centred palm/thumb/four-finger patches in `GripEnv`.
- [x] Add palm-side alignment before digit wrapping.
- [x] Calibrate and control all four distal finger colliders.
- [x] Update phase gates, reward, observations, tests, trainer, and recorder.
- [x] Run CPU/static checks and a GPU teacher diagnostic.
- [x] Train and save a provenance-sealed checkpoint.
- [x] Render and inspect the learned-policy video and metrics.
- [x] Complete independent change review.

## Success criteria

- The mean four-finger axial target equals acquisition G and all live targets
  remain on their assigned surface patches.
- The teacher visibly moves the palm toward the floor-facing side and moves all
  five digit chains toward the acquisition-centred targets.
- Training and evaluation complete without non-finite state or overload.
- Physical success requires palm, thumb, and four-finger directional contact
  held for 120 frames; otherwise the output is explicitly marked diagnostic.

## Outcome

The implementation, 20,000-update training run, and independent video rollout
completed. The rollout is explicitly diagnostic: it reached accurate palm-side
geometry and visibly moved all five digit chains, but lost physical palm force
and did not complete the thumb/back-face or 120-frame five-digit hold gates.
Review findings were applied for palm-retention rollback, stale teacher-hold
reset, provenance sealing, non-finite checkpoint rejection, and diagnostic
labelling. Full collider-surface clearance and successful-pose distal-pad
calibration remain promotion blockers and are enforced by
`PAD_CALIBRATION_VALIDATED=false`.
