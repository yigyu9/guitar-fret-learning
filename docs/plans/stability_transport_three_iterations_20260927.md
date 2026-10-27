# Stability Adapter TRANSPORT — three-iteration plan

## Baseline

- Run: `20260927_training_v7`
- Deterministic peak: 3.374 mm of the requested 5 mm at frame 37
- Deterministic final: -0.678 mm at frame 180
- Main failure: the controller reaches useful displacement, disables its
  servo, and does not reject the guitar's lateral/downward momentum.

## Success criteria

Each iteration must produce a fresh checkpoint, metrics JSONL, deterministic
zero-noise rollout video, and analysis.  A rollout is successful only when the
environment's support, pose, velocity, and 30-frame dwell gates all pass.
Peak displacement alone is diagnostic evidence, not success.

## Checklist

- [x] Implement profiles 1–3 behind one source version and add tests.
- [x] Profile 1: active goal-pose retention and world-velocity damping.
- [x] Train/render/analyze profile 1.
- [x] Profile 2: profile 1 plus direction-aware progress/lateral reward.
- [x] Train/render/analyze profile 2.
- [x] Profile 3: profile 2 plus reduced post-target residual and short timeout.
- [x] Train/render/analyze profile 3.
- [x] Compare all three against v7 and record the next recommendation.
- [x] Run focused tests and independent change review.

## Fixed evaluation condition

- Curriculum stage 0: 5 mm translation, 0 degree rotation
- Exact captured grip snapshot
- Zero start position/rotation/arm noise
- Deterministic actor action
- 180 simulation frames unless terminated earlier
