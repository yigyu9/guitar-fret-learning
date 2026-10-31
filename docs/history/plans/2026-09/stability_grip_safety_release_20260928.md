# Stability GRIP safety release implementation

## Scope

- Make safety release authoritative over learned residuals.
- Bound thumb TOUCH targets around measured joint positions.
- Recenter all thumb targets on first/unsafe contact.
- Persist optimization history and per-rollout terminal outcomes.

## Checklist

- [x] Add per-digit safety-release latch and hysteresis.
- [x] Disable residuals during safety release and unsafe thumb routing stages.
- [x] Limit TOUCH target compression and recenter on raw contact.
- [x] Persist loss history and terminal outcome metadata.
- [x] Add focused regression tests.
- [x] Run GPU teacher/policy smoke validation.
- [x] Complete independent change review.

## Success criteria

- Unsafe contact immediately returns the affected digit's full action target to
  its measured state.
- The learned action mask is empty while release is latched and remains empty
  until a safe dwell completes.
- Thumb TOUCH cannot accumulate more than the configured target/measured error.
- New checkpoints preserve enough loss and rollout outcome data for audit.

## Validation result

- Pure logic regression suite: 38 tests passed, including the teacher-action
  safe-dwell integration regression.
- GPU PhysX nominal teacher, pre-fix: overload at frame 3036 with an 83.887 N
  conservative hand-load estimate.
- GPU PhysX nominal teacher, final safety settings: no overload through frame
  6000, but terminated by `environment_timeout` in thumb `TOUCH` with no
  functional-grip dwell.
- The safety-release implementation is therefore validated for the observed
  overload regression. Grip promotion remains correctly closed; thumb contact
  path/IK acquisition requires a separate geometry recalibration before long
  DAgger training.
