# Stability GRIP gap-adaptive thumb TOUCH

## Scope

- Widen the thumb target/measured envelope only in free space.
- Taper the envelope before contact while retaining compliant hand stiffness.
- Pause forward progress when rear-face alignment is poor.
- Detect stalled gap progress and perform a local thumb retreat/retry.
- Expose target error, gap progress, and retry state in diagnostic traces.

## Checklist

- [x] Add pure gap/alignment envelope and stall-state helpers.
- [x] Integrate adaptive TOUCH routing without changing LOAD safety behavior.
- [x] Add local thumb retry with bounded retreat and retry count.
- [x] Add frame-level diagnostics for the new control state.
- [x] Add focused regression tests.
- [x] Run syntax and regression checks.
- [x] Run a short GPU teacher validation.
- [x] Complete independent change review.

## Success criteria

- Gap above 4 mm uses a wider target envelope than near-contact motion.
- Alignment below the recovery threshold cannot command further penetration.
- A stalled thumb performs a bounded local retry rather than remaining in TOUCH
  indefinitely.
- Existing safety release remains authoritative.
- GPU teacher reaches 1 mm gap or produces real thumb normal force without an
  overload; otherwise the exact remaining failure is recorded.

## Validation result

- 42 pure/regression tests passed.
- GPU teacher minimum TOUCH gap: 0.30 mm (previously 5.12 mm).
- Maximum thumb normal force: 0 N; overload frames: 0.
- Near-contact bias active for 378 frames; all three bounded retries ran and
  exhaustion terminated explicitly at frame 5,271.
- The geometric proximity criterion passed, but physical-contact promotion
  remains closed pending a thumb collider/contact-surface audit.
