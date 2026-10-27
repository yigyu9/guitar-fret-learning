# GRIP force-closure iteration

## Diagnosis

- The v25 teacher reaches all five hover latches, but only the index and pinky
  ever generate distal normal force.
- At the end of `GRIP_CLOSE`, middle/ring PIP joints are flexed to 72.73/66.94
  degrees while their DIP joints remain at 5.27/7.10 degrees.  The thumb's
  second flexion joint falls to 3.20 degrees.
- The phase-5 Cartesian controller therefore preserves the guide point while
  opening the joints that must create normal force.  More behavior-cloning
  updates cannot repair this teacher target.

## Implementation

- [x] Replace phase-5 Cartesian closure with sequential force-seeking joint
  closure: index, middle, ring, thumb, then distal-first pinky.
- [x] Use per-segment force to retreat on proximal collision, hold a valid
  distal contact, and relieve overload.
- [x] Keep palm re-acquisition active once all digit support exists.
- [x] Add unit tests for closure ownership and contact/overload behavior.
- [x] Run short teacher probes and retain only a safer improvement.
- [x] Rebuild the contact contract, train, render, and verify artifacts.
- [x] Run independent change review and resolve all warnings.

## Success gates

- Every distal digit produces at least 0.5 N; thumb produces at least 2 N.
- Palm produces 0.5--8 N after opposing finger contact exists.
- No proximal digit body exceeds 0.2 N and no digit exceeds its force ceiling.
- The strict 120-frame hold and calibration blockers remain unchanged.

## Progress log

- 2026-09-20: v25 trace isolated missing DIP/thumb flexion as the next teacher
  bottleneck; selected force-seeking joint closure instead of longer training.
- 2026-09-20: v26 produced index/pinky force, but middle remained 4.5 mm off
  the front face at its 48-degree DIP target.  Increased distal-flexion reach,
  extended the diagnostic horizon to 3,600 frames, and lowered the controller
  pressure-relief threshold to 2.5 N per finger.
- 2026-09-20: v27 reached middle contact, proving the collider and filter are
  active, but terminated at 10.9 N middle / 11.2 N pinky overload.  Reduced
  final joint-target velocity from 0.15 to 0.05 degree per control frame.
- 2026-09-20: v28 still overloaded because palm re-acquisition pushed the free
  guitar into already closed index/pinky targets.  Added measured-state PD
  pressure release and delayed palm re-acquisition until all digit support
  forces exist.
- 2026-09-20: v29 completed 3,200 frames without overload and simultaneously
  held index/middle/ring at 0.986/0.678/0.768 N with near-zero guitar motion.
  Pinky had not completed its approach, so raised the now-compliant close rate
  from 0.05 to 0.08 degree per control frame for the full 3,600-frame probe.
- 2026-09-20: v30 held index/middle/ring at 1.081/0.720/0.845 N and brought
  pinky to 0.350 N without overload.  Extended the horizon to 4,800 frames so
  pinky, thumb, then palm re-acquisition can execute in order.
- 2026-09-20: v31 reached all four opposing-finger minima, but index pressure
  relief blocked thumb ownership.  Decoupled parallel over-pressure relief
  from the sequential missing-contact owner.
- 2026-09-20: v32 ended with all four opposing fingers above their minima but
  their intermittent force prevented simultaneous sequential ownership from
  reaching the thumb; the thumb joints remained at the hover pose.  Added a
  five-frame demonstrated-contact latch so completed fingers maintain force
  in parallel while closure progresses to the next digit.  Physical success
  thresholds remain unchanged and still require simultaneous force.
- 2026-09-20: v34 exposed the remaining sequencing block: index, middle, and
  ring latched at frames 1,033/1,674/2,276, while pinky distal force exceeded
  0.5 N but a simultaneous proximal brush prevented its latch.  Restricted
  the progress latch to demonstrated distal force; proximal contact still
  triggers immediate pressure release and remains forbidden for success.
- 2026-09-20: v35 proved the displayed pinky load was not usable distal
  normal force: its pad remained 15.5 mm lateral to the configured patch and
  the distal-contact latch stayed false.  Re-centred the pinky acquisition
  target on the reachable stable-close pose (x=10 mm, y=34 mm) and added
  separate distal-normal/per-segment force fields to every diagnostic trace.
- 2026-09-20: v36 placed pinky x/y within roughly 0.1/0.3 mm of the new guide,
  but simultaneous PIP/DIP flexion loaded the middle phalanx to 5.9 N while
  the distal pad was still 7.8 mm above the face, causing overload.  Changed
  pinky closure to distal-first (DIP to 60 degrees, then PIP) and extended the
  diagnostic horizon to 6,000 frames for this safer articulated path.
- 2026-09-20: v37 latched pinky distal contact at frame 2,594 and moved the
  thumb flexion joints through their full target range, but flexion alone
  displaced the thumb pad about 24/25 mm in x/y and produced zero rear-face
  normal force.  Switched only the thumb contact step to full thumb Jacobian
  position/normal control and allowed low-rate palm contact restoration after
  all four opposing pads have demonstrated force.
- 2026-09-20: v38 reduced the thumb rear-face gap from 9.65 mm to -1.03 mm and
  improved alignment to 0.872, but the pad converged 24 mm below the old
  y=130 mm guide.  Early palm restoration also drove pinky2 to 16.7 N.
  Re-centred the thumb target on the reachable aligned pose (x=-18 mm,
  y=106 mm) and restored the five-digit requirement for palm re-acquisition.
- 2026-09-20: v39 revealed that replacing the thumb guide globally also moved
  the validated WRAP hover target, causing phase 2/3 retention rollback.
  Split the target contract: retain x=-8/y=130 mm for collision-free hover,
  then switch to x=-18/y=106 mm only after entering `GRIP_CLOSE`.
- 2026-09-20: v40 restored the full phase chain, but force flicker made
  already-latched fingers return to their maximum closure targets, producing
  13.5 N middle-tip and 11.9 N pinky-proximal impact spikes.  Replaced that
  maintenance behavior with a measured-state 0.25-degree re-contact bias;
  first-time owner closure remains sequential and slow.
- 2026-09-20: v41 prevented the prior multi-finger spike, but pinky2 reached
  21.5 N while the thumb still had 10.6 mm of rear-face clearance.  Reordered
  force closure to index, middle, ring, thumb, then pinky so the opposing
  thumb supports the free guitar before the short pinky completes its wrap.
- 2026-09-20: v42 completed 5,200 frames without overload and retained stable
  index/middle/ring normal force, but the x=-18 mm thumb guide sent the
  redundant IK to the opposite x=+37.6 mm local solution.  Re-centred the
  contact guide on the earlier arm-fixed Cartesian basin (x=0, y=116 mm),
  keeping the transition close to the validated hover pose.
- 2026-09-20: v43/teacher video completed 5,200 frames without overload and
  showed substantial hand motion, but still no thumb normal force.  The first
  30k BC checkpoint then left the demonstrated state distribution after a
  phase rollback and terminated at frame 3,349 with extreme contact load.
  Added a 0.05 normalized-action trust region around the live teacher target;
  inactive digits and all arm joints remain exactly teacher-controlled.
- 2026-09-20: trust-region v4 removed the v3 physical blow-up and completed
  5,200 frames without overload or environment failure, but +/-0.05 remained
  too wide for hover dwell and the policy repeatedly rolled back before
  `GRIP_CLOSE`.  Tightened the execution trust region to +/-0.01 for the final
  checkpoint; this preserves learned corrections while enforcing the staged
  teacher's contact-safe basin.
- 2026-09-20: the +/-0.01 v5 policy was less robust: small systematic bias
  accumulated during `WRAP_FINGERS` and produced a 179.7 N index impact at
  frame 1,574.  Rejected v5 and restored the +/-0.05 v4 runtime, which is the
  only learned rollout in this iteration to complete 5,200 frames with both
  overload and environment failure false.  It remains a failed acquisition
  candidate because it does not reach `GRIP_CLOSE`.
- 2026-09-20: archived the previous `current` fast-parallel pilot, promoted v4
  only as the current *diagnostic* candidate, and copied its checkpoint,
  teacher video, learned video, reports, and v43 teacher trace into `current`.
  Both videos passed ffprobe as H.264 960x540 at 15 fps for 88.667 seconds.
- 2026-09-20: independent review found that the progress latch accepted an
  out-of-patch or over-limit distal force.  Restricted latching to the correct
  pad patch and the per-digit operating force interval, added dwell/flicker/
  over-force regression tests, and moved the evaluator's default output from
  legacy `preshape_v1` into this iteration's `contact_force_fix` directory.
- 2026-09-20: post-review v44 reproduced the 5,200-frame teacher trajectory
  without overload while leaving only correctly placed index/middle/ring
  contacts latched.  Retrained v6 for 30,000 updates on 11,601 samples and
  regenerated both videos against the current source hashes.  The v6 policy
  again completed 5,200 frames without overload/environment failure but did
  not advance past the hover phases, so it remains non-promotable.
- 2026-09-20: thumb-path v1 replaced the direct hover/contact target switch
  with CLEAR, ALIGN, RAIL, TOUCH, LOAD, and HOLD substages.  GPU probes rejected
  coupled wrist assistance because it repeatedly drove the unclosed pinky
  proximal link into the neck.  The accepted v12 teacher instead used only the
  five thumb joints, froze the valid rail tangential point during touch, found
  the physical distal-collider contact depth, and reached HOLD at frame 3,561.
  Its maximum thumb distal normal force was 3.89 N, maximum thumb proximal
  force was 0.0 N, and neither overload nor environment failure occurred.
- 2026-09-20: trained the thumb-path teacher for 30,000 masked-BC updates on
  11,643 samples with one recovery rollout.  Final loss was 9.491e-05.  The
  learned rollout remained physically safe but rolled back during hover and
  never reached GRIP_CLOSE, so the checkpoint and policy video are explicitly
  retained as non-promotable diagnostics under `grip/thumb_path_v1/`.
- 2026-09-20: independent review rejected the v1 HOLD claim.  The v12 trace
  entered the labelled HOLD state using a historical five-frame latch while
  current force was below the 2 N operating minimum; actual 2--4 N continuity
  was insufficient.  Marked v1 rejected, removed the force substitution,
  added real LOAD/HOLD dwell and rollback gates, and added thumb substage plus
  route/force features to the policy observation for the v2 rerun.
- 2026-09-20: thumb-path v2 reached a later-rejected HOLD label from filtered force
  at frame 3,438 and retained it for 16 frames with 2.724 N peak filtered
  normal force and zero proximal thumb force.  It then correctly rolled back
  to LOAD after pressure loss; later pinky proximal overload terminated the
  teacher at frame 3,797, so the run remains a diagnostic rather than a full
  grip success.
- 2026-09-20: trained the v3/175D stage-conditioned policy for 30,000 updates
  on 9,774 samples (final MSE 1.781e-05) and rendered teacher and learned-policy
  videos.  The learned policy stayed in PALM_ALIGN_PRESHAPE/CLEAR for 4,000
  frames and is explicitly non-promotable.  All v2 artifacts are isolated
  under `grip/thumb_path_v2/`.
- 2026-09-20: final review rejected the v2 HOLD label because its LOAD/HOLD
  gate used EMA-filtered force, which remained in band across instantaneous
  zero-force frames.  Marked v2 rejected, switched the gate to raw distal
  normal force, added proximal-abort and 175D observation-schema regression
  tests, and separated three-frame TOUCH confirmation from ten-frame LOAD
  pressure dwell.
- 2026-09-20: raw-force v3 demonstrated ten consecutive 2--4 N LOAD frames
  (3.570, 3.491, 3.480, 3.503, 2.314, 3.097, 2.776, 3.528, 2.776, 2.525 N),
  then entered HOLD and correctly rolled back after pressure loss.  Retrained
  for 30,000 updates on 11,889 samples (final MSE 5.134e-05) and regenerated
  both videos.  The teacher remained overload-free for 4,000 frames but did
  not finish the five-digit hold.  The learned policy failed in palm alignment
  at frame 2,824 with overload, so the checkpoint is non-promotable.
