# GRIP thumb contact and opposing-force fix

## Goal

Validate the thumb acquisition point against the authored neck collision
surface, explain why the four fingers do not generate opposing force, then
implement and train a load-bearing acquisition grip.

## Assumptions

- Thumb pad contacts the neck back face.
- Index, middle, ring, and pinky pads contact the front face.
- Palm remains on the floor-facing side surface.
- This task stops at a sustained acquisition grip; transport is not included.

## Checklist

- [x] Audit thumb target, pad point, face normal, and reachable approach path.
- [x] Diagnose force loss per digit from the latest teacher and learner traces.
- [x] Define measurable contact, opposition, force, slip, and hold gates.
- [x] Implement the minimum target/controller/environment changes.
- [x] Add regression tests and run teacher probes.
- [x] Re-seal the diagnostic contact contract and train the policy.
- [x] Render and inspect learner-only main and close-up videos.
- [x] Verify hashes, reports, decoding, and independent change review.

## Outcome

The teacher and the learned v2 policy both reach five-pad hover latch and
`GRIP_CLOSE`, but neither produces the required palm-plus-thumb-plus-four-finger
force hold.  The learner finishes with 0.874 N on the index only.  Both remain
failed diagnostics; promotion blockers stay closed.

## Success criteria

- Thumb distal pad is inside its back-face patch with positive inward normal
  force; all four finger distal pads are inside their front-face patches.
- Thumb and summed finger force vectors oppose by at least 150 degrees.
- Thumb force is 2–8 N; every finger is 0.5–5 N; summed opposing finger force
  is 2–16 N.
- Palm pose/contact and guitar motion gates remain valid for 120 consecutive
  frames without overload, non-finite state, or environment failure.
- A successful-pose pad calibration must exist before promotion; otherwise the
  result remains a diagnostic candidate even if the raw hold gate passes.
