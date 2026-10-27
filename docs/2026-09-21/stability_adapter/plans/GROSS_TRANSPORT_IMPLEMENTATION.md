# Gross transport implementation

The precision T0.1 curriculum remains frozen.  This branch first proves that
the acquired grip can move the guitar a visible 20 mm.

## Success contract

- `LOAD_SETTLE -> PRELOAD -> BREAKAWAY -> CRUISE -> BRAKE -> HOLD`
- PRELOAD prefers measured palm-patch force. Because the current acquired
  pose often has zero palm-normal force, a transparent force-closure fallback
  is also accepted: thumb, at least two opposing fingers, and at least 12 N
  bounded total hand load. The 30-frame dwell begins only after PRELOAD entry.
- BREAKAWAY requires 2 mm projected travel or positive goal-direction speed.
- The commanded target remains 20 mm. CRUISE ends at 16 mm and the coarse
  acceptance boundary is 18 mm (90% of the command), avoiding unsafe extra
  force merely to gain the final precision millimetres.
- Success requires at least 18 mm projected travel with grip retained for 60
  frames. Strap oscillation speed is recorded but deliberately not gated in
  this displacement-first curriculum; damping and precision are owned by the
  next curriculum. The commanded and accepted distances are
  both written to diagnostics; a later precision curriculum owns the final
  2 mm.
- Pose precision is deliberately absent.  Rotation is only a 15 degree safety
  limit, not an optimization target.

## Checklist

- [x] Preserve precision transport v6 and introduce a separate environment.
- [x] Implement force-bearing preload and monotonic stage gates.
- [x] Reward projected travel; penalize lateral/backward motion and failures.
- [x] Implement the deterministic palm-preload/arm-transport teacher.
- [x] Add CPU tests for transition and metric contracts.
- [x] Run the complete unit suite (70 tests passed).
- [x] Run a GPU teacher smoke test and record measured displacement/forces.
- [x] Resolve independent change-review findings; final re-review is clean.

## Verified v6 result

- Commanded displacement: 20.0 mm
- Coarse acceptance boundary: 18.0 mm
- Final projected displacement: 19.149 mm
- Final lateral drift: 4.184 mm
- HOLD: 60 consecutive frames
- Final hand load: 40.47 N
- Final grip retained: yes
- Persistent overload termination: no
- Peak transient hand load: 236.682 N

The peak transient load means this is a displacement-feasibility result, not a
promotion-ready transport policy. The next iteration must reduce impulse and
strap oscillation before behavior cloning or residual RL is enabled.
