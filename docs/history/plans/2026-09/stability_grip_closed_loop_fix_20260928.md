# Stability GRIP closed-loop correction

## Assumptions

- Keep the validated WAIT, REACH, WRAP teacher and functional-grip thresholds.
- Represent CONTACT_ACQUIRE/FORCE_BUILD as a GRIP_CLOSE subphase so existing
  phase indices and observation dimensions remain stable.
- Existing v3 checkpoints remain evidence only; changed controller sources
  intentionally prevent silently loading them as current checkpoints.

## Checklist

- [x] Add explicit GRIP_CLOSE subphase and failed-gate diagnostics.
- [x] Restrict learned residuals to the currently active force-closure digit.
- [x] Add learner-state DAgger collection and v4 checkpoint provenance.
- [x] Persist per-frame action/contact trace in diagnostic rollouts.
- [x] Add focused unit tests and run syntax/tests.
- [x] Run a short GPU smoke validation.
- [x] Complete independent change review.

## Success criteria

- Pre-GRIP_CLOSE and inactive digit actions remain exactly on the reference.
- CONTACT_ACQUIRE and FORCE_BUILD are observable without changing the existing
  eight-phase environment contract.
- DAgger samples come from actions executed by the learner, with the teacher
  target evaluated at the same pre-step state.
- Every diagnostic rollout writes a parseable per-frame JSONL trace containing
  reference/applied actions, active residual digits, subphase, and failed gates.

## Verification

- 43 focused GRIP/REACH tests passed.
- GPU DAgger smoke: 1,802 teacher samples plus 216 learner-state samples,
  schema-v4 checkpoint saved with matching current source hashes.
- GPU recorder smoke: v4 checkpoint loaded and a JSONL trace with explicit
  pre-step action ownership and post-step diagnostic fields was hash-verified.
- Independent review: PASS, no remaining Blocker/Major findings.
