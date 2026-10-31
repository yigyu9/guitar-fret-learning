# Stability adapter — support-first implementation plan

## Objective

Replace the direct 5 mm TRANSPORT start with a gated curriculum:

1. 0 mm force-bearing SUPPORT HOLD
2. 1 mm translation
3. 3 mm translation
4. 5 mm translation

The policy may advance only after 64 completed episodes with at least 80%
coarse-stage success.  Deterministic evaluation must use the exact snapshot
and zero start noise.

## Success criteria

### Support hold

- Horizontal drift <= 3 mm
- Vertical drift <= 3 mm
- Rotation error <= 3 degrees
- Linear speed <= 0.03 m/s
- Angular speed <= 0.30 rad/s
- Current force-bearing grip valid
- 120 consecutive frames

### Translation

- Signed progress inside a bounded interval around the requested distance
- Horizontal/vertical drift <= 3 mm
- Rotation error <= 3 degrees
- Linear/angular speed and grip gates identical to support
- 60 consecutive frames

## Checklist

- [x] Add support-first curriculum and bounded success gates.
- [x] Add per-digit force feedback to the retained hand target.
- [x] Add horizontal/vertical displacement, velocity, strap, and force logs.
- [x] Add support-specific reward and PPO stability controls.
- [x] Add focused tests and run the test suite.
- [x] Run a deterministic pre-training controller probe.
- [x] Train sufficiently from a fresh checkpoint.
- [x] Render deterministic result video and analyze logs.
- [x] Complete an independent change review.

## Independent review disposition

The reviewer found one correctness issue outside the zero-noise run delivered
here: when reset noise is nonzero, the current restore path derives the 0 mm
target from the already perturbed guitar pose.  The 100-update training and all
deterministic evaluations used zero noise, so this does not change their
reported dynamics or conclusions.  Preserve the current source hashes for
checkpoint reproducibility; before re-enabling reset noise, separate the
unperturbed reference pose from the perturbed episode-start pose and add a
direct test for that contract.

The reviewer also noted that the checkpoint's descriptive configuration stores
the legacy 180-frame timeout while the support environment actually enforces
240 frames.  Runtime logs and success statistics use the 240-frame environment
value.  Correct this metadata together with the reset-noise fix before the next
fresh run.
