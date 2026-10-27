# GRIP sequential-latch implementation

## Goal

Prevent the arm from continuously loading the neck while requiring three
simultaneous hover poses. Acquire thumb, index, and middle in order, preserve
each acquired pad target, then enter contact closure only after a quiet settle.

## Checklist

- [x] Add ordered per-pad hover dwell and relaxed retention gates.
- [x] Make the teacher command only the first unlatched digit.
- [x] Freeze torso/thorax/arm targets after thumb hover acquisition.
- [x] Replace the unreachable global `0.80` arm-freeze alignment gate with
  calibration-based signed thresholds.
- [x] Add force-aware palm retreat and a sustained palm-overload cutoff.
- [x] Extend the episode budget to 6,000 frames for sequential acquisition.
- [x] Preserve previous diagnostic artifacts under a legacy directory.
- [x] Fail closed unless `num_envs=1` and seal validation source hashes.
- [x] Run the teacher safety probe and record phase/latch progress.
- [x] Run the user-requested 20,000-update diagnostic BC training and video.
- [x] Complete independent change review (P0/P1 none).

## Acceptance

- `WRAP_THUMB` does not require index or middle hover.
- The teacher reaches at least `WRAP_FINGERS` without exceeding the palm-force
  cutoff.
- A lost pad is reacquired before closure; elapsed time never substitutes for
  geometry or force.
- Training remains blocked until the teacher exposes later phases safely.

## Result

The teacher now reaches `GRIP_CLOSE` without overload. Thumb, index, and middle
latched at frames 351, 1,401, and 2,330; close began at frame 2,390. At frame
6,000 all three guide points occupied their geometric contact patches, with
thumb force `4.460 N` and palm force `2.068 N`. Recorded index and middle chain
force remained `0 N`, so promotion training remains blocked. The next task is
to calibrate against the cooked PhysX collision surface rather than the visual
STL triangle surface.

The later user-requested diagnostic behavior cloning used all 6,000 teacher
samples for 20,000 updates (`8.8371e-7` final MSE). Its standalone rollout
failed in `WRAP_THUMB` at frame 694 with no latched pads and guitar speed
`1.0296 m/s`; it remains explicitly non-promotable.
