# TRANSPORT pose-control v1

## Goal

Replace the 20 mm displacement-only gross success with a 50 mm pose step
toward the authored initial guitar pose.  The guitar must be position- and
rotation-controlled, dynamically settled, and retained by the functional grip.

## Implementation checklist

- [x] Relax L_Thorax-descendant arm step and target-error limits.
- [x] Use a time-based minimum-jerk guitar-pose trajectory; never advance the
  command from accidental measured displacement.
- [x] Keep the guitar-relative palm grasp transform during translation and
  rotation.
- [x] Continue the 6D palm servo during SETTLE instead of freezing the arm.
- [x] Relax absolute pressure limits and terminate only persistent/dynamic
  impact-like pressure.
- [x] Require position, rotation, linear speed, angular speed, and functional
  grip for a 60-frame success dwell.
- [x] Run deterministic teacher probe at 50 mm / up to 15 degrees.
- [x] Train a transport behavior-cloning checkpoint only from a successful
  teacher, unless a failed diagnostic is explicitly recorded as non-promotable.
- [x] Render clean acquisition-to-TRANSPORT teacher and learned-policy videos
  and verify their reports and SHA-256 values.
- [x] Run the 38 transport unit tests and Python syntax checks.
- [x] Complete independent change review and correct its dynamic-impact,
  terminal-reason, and timing findings.

## Initial acceptance gates

- Requested translation: 50 mm toward the authored initial position.
- Requested rotation: up to 15 degrees toward the authored initial rotation.
- Position error: at most 10 mm.
- Rotation error: at most 3 degrees for a full 15-degree request (20% adaptive
  tolerance, capped by the environment).
- Linear speed: at most 0.03 m/s.
- Angular speed: at most 0.15 rad/s.
- SETTLE dwell: 60 consecutive frames with retained grip.
- Persistent hard pressure is rejected, but a stable high-force grip is not
  rejected solely because of its absolute load.

## Implemented limits

- L_Thorax-descendant arm target window: `+/-0.02` -> `+/-0.15 rad`.
- Arm command step: `0.0002` -> `0.0015 rad/frame`.
- Transport trajectory: 600 frames with minimum-jerk interpolation.
- Soft thumb/finger/hand-load diagnostics: 80 / 60 / 150 N.
- Hard digit/hand thresholds: 120 / 250 N, with a 20-frame dwell.
- Dynamic impact detection remains active above 180 N when the load rises by
  more than 30 N/frame or relative speed exceeds 0.45 m/s. Persistent absolute
  force uses the 20-frame dwell; dynamic/deep-contact events use a leaky impact
  score that rejects two events separated by one clear frame while tolerating
  one isolated event.

## 2026-09-21 result

This iteration improves grip retention and removes the old false-positive
displacement-only success, but it does **not** pass the 50 mm pose gate.

- Deterministic teacher: 5,228 control steps at 60 Hz (87.13 s), with
  TRANSPORT entered at frame 3429 and active for 1,800 steps (30.0 s); no grip
  loss and no overload. The rendered 89.2 s includes a 2 s terminal freeze.
- Teacher translation error: 50.0 -> 41.275 mm (8.725 mm progress; minimum
  41.238 mm).
- Teacher rotation error: requested 15 degrees, final 12.599 degrees.
- Teacher terminal speeds: 0.0610 m/s linear, 0.6246 rad/s angular; therefore
  SETTLE was not entered.
- Teacher terminal hand load: 55.865 N.
- Behavior cloning: 1,768 MOVE samples, 12,000 updates, final loss
  `2.6450511541042943e-06`.
- Learned policy evaluation: no grip loss and no overload, but final position
  error 51.42 mm and rotation error 13.393 degrees. It did not reproduce the
  teacher's small translation improvement and is explicitly non-promotable.
- Tests: 38/38 transport tests and 83/83 no-fixture StabilityAdapter regression
  tests passed in the `rl38` Isaac Gym environment; syntax checks passed.

Artifacts are under `../transport/pose_50mm_v1/`. The teacher video is the
best current motion evidence; the learned video is retained as a negative
evaluation result rather than represented as a successful transport policy.
