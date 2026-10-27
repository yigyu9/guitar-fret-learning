# Thumb LOAD recovery v1

## Goal

Keep a force-bearing thumb through `GRIP -> TRANSPORT` without storing a stale
compressed PD target that produces a delayed overload.

## Assumptions

- Transport acquisition remains functional: thumb plus at least two of
  index/middle/ring. Pinky is not a transport-entry prerequisite.
- The strict five-digit/palm-contact GRIP result remains diagnostic until its
  collider-pair and pad calibration gates are validated.
- Seed 17 is the first deterministic acceptance case.

## Checklist

- [x] Add unit coverage for the bounded thumb pressure correction.
- [x] Limit accumulated pressure trim to 0.20 degrees around LOAD origin.
- [x] Recenter the LOAD origin on measured pose after overpressure (anti-windup).
- [x] Preserve proximal-contact and immediate overpressure release behavior.
- [x] Probe the full GRIP-to-TRANSPORT teacher and record entry latency.
- [x] Train a new grip behavior-cloning checkpoint from the revised teacher.
- [x] Add continuous acquisition recording to the transport renderer.
- [x] Render a clean continuous GRIP-to-TRANSPORT rollout.
- [x] Record metrics, limitations and artifact hashes.

## Acceptance gates

- Thumb force-bearing support and two non-pinky opponents for 30 consecutive
  frames before transport entry.
- No environment failure or hard overload before entry.
- Transport starts no later than the verified 3,429-frame baseline.
- Reach at least 18 mm projected displacement and hold it for 60 frames.

## Verified teacher result

- Final post-review probe:
  `transport/thumb_load_recovery_v1/gross_probe_v8_post_review.json`
- Transport entry: frame 3,429 (baseline preserved)
- Terminal: success at frame 3,741
- Final projected displacement: 19.173 mm
- Final conservative hand load: 41.256 N
- Hold dwell: 60 frames
- Terminal hard-overload failure: false
- Transient dangerous-pressure flag: 26 frames in 18 runs, longest run 5
  frames (below the 6-frame hard termination dwell)
- Peak conservative hand load: 209.975 N; this transient remains a safety
  limitation even though the controller released and completed transport

The rejected v6 probe reached only 15.988 mm and terminated on overload after
the accumulated pressure trim kept returning to a stale compressed LOAD
origin. Re-centering that origin on the measured release pose removed the
failure while retaining low-force recovery.

## Training and render artifacts

- Checkpoint: `grip/thumb_load_recovery_v1/checkpoints/grip_thumb_load_recovery_bc_12000_v1.pt`
- Training: 12,000 updates, 11,297 masked samples, final loss
  `5.636255446006544e-05`, thumb final stage `HOLD`
- Limitation: strict five-digit 120-frame hold was not completed, so the
  checkpoint is recorded but is not promotion eligible. The verified rollout
  uses the deterministic teacher controller.
- Limitation: the successful rollout still contains short dangerous-pressure
  transients. It demonstrates recovery rather than pressure-safe deployment;
  the checkpoint and teacher must not be promoted as a final safety policy.
- Clean continuous video:
  `grip/thumb_load_recovery_v1/videos/grip_to_transport_clean_v1.mp4`
- Video: 960x540 H.264, 10 fps, 64.4 seconds, acquisition included
- Video SHA-256:
  `e6340541bde2b6f291248c9422d00226255b4995f4bd70f57830a11fc2b707cb`
- Checkpoint SHA-256:
  `317927eccc3b46b7a3fb61d1749865fb495789cc53d3c614b9e20b73a27d0bc5`
