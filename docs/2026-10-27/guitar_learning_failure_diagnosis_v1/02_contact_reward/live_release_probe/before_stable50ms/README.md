# Native live short-contact / release diagnostic

Prepared only. No GPU run or new native evidence has been collected by this support tool.
This is finite reference control in the existing fixed-guitar, teacher-supported middle-row8 task, never policy performance or free-guitar success. The existing incremental seed7 retry2 initial checkpoint and reference are mandatory. Strict source, evidence, teacher, model architecture and configuration checks remain in the original evaluator. No package source is edited.

The fixed assignment is 16 conditions × 8 environment repetitions = 128 first attempts. Environment `i` receives condition `i % 16`, repetition `i // 16`, before any GPU scene exists. Every condition follows the sealed reference ramp for2s. Only the selected middle four actions switch to the original035 prepared target when the **next**60Hz endpoint reaches the assigned release time:

| Condition | Release requested at local seconds | First control endpoint tick |
| --- | --- | --- |
| 0 | Never; reference hold | Never |
| 1–5 | 2.90, 2.92, 2.94, 2.96, 2.98 | 174, 176, 177, 178, 179 |
| 6–10 | 3.00, 3.02, 3.04, 3.06, 3.08 | 180, 182, 183, 184, 185 |
| 11–15 | 3.12, 3.14, 3.16, 3.18, 3.22 | 188, 189, 190, 191, 194 |

Actual note window: local press2.9787s, onset3.0s, end3.1174s. Endpoint rounding means a requested3.12s release starts on the control ending3.133333s. Request time is not a claim about actual physical separation time.

## Implementation and evidence contract

- Reuse unchanged `runner.run`, `_evaluate`, strict trainer load and `ShortPool`. The docs subclass substitutes only selected4 actions using existing `trajectory_actions(max_speed=4)`. Original wrist guidance, other-finger B, thumb, right-hand zero, native bounds, PD, effort, rewards, predicates and termination run unchanged. No state, force or body pose is overwritten. Source hooks are process-local and restored in `finally`.
- Each original pool step still performs four actual240Hz physics steps. A read-only callback runs **after** original `environment.substep(snapshot)` has updated geometry and note accounting. It records all128 environments compactly, with per-environment first-attempt masks; subsequent attempts remain excluded even when the unchanged evaluator resets completed rows.
- `physics240.npz`: actual integer clock, local/source score time, first-attempt mask, selected candidate/wrong/positive, surface distance/height/alignment, original position/facing gates, assigned distal resultant force, selected distal and guitar body states, actual/target q4, actual selected note progress/clean/streak/achievement/released/release time, and wrong provenance flags/fret bounds when present. No all-body240Hz trace.
- `control60.npz`: first-attempt mask, release requests, selected requested/executed actions, actual reward/cost, all nine component increments and cumulative values. Cumulative endpoint values must never be summed as increments. The original evaluator additionally saves its normal env0 first-attempt60Hz trace.
- `first_attempt_episodes.json`: every original completed first-attempt episode, including physical/wrist/normal failures, full original note ledger, all nine actual reward totals, and selected raw note fields including `released`/`release_s` omitted from the original serialized ledger.
- `probe_report.json`: all completed cases and missing-case IDs; finite, clock, four-substep, strict-runner, lifecycle, source/model/update checks. `inputs_before.json`/`inputs_after.json` retain the original source/teacher/checkpoint/config pins plus this script and precommitted protocol bytes. Existing output directories are rejected; errors, partial traces and traceback are preserved.

A conservative short-only witness requires final `0 < contact_progress < 1`, no latched achievement, and actual progress in that interval during the original press..end window. Progress alone is not received reward; actual component values are retained, with no arbitrary zero-reward criterion. Missing witnesses remain missing.

Release evidence reports candidate loss, original pad position-geometry loss, native assigned-distal resultant below the original0.01N gate, and surface distance/height. The joint flag first requires an actual candidate true→false transition after release control starts, then geometry/candidate absence and low load in the same observed sample; its actual clock and distance are recorded. A never-contacting attempt cannot qualify. Physics samples record the actual control's release-request mask, including substeps before the assigned endpoint. This does not identify a contact pair or certify real string pressure. These conditions can fail to produce contact or separation; no promise is made that all negative cases, especially facing-negative poses, are covered. The original `released` flag additionally uses its original post-note timing rule; its absence does not by itself disprove an earlier physical separation.

## CPU verification and handoff

Use the existing `rl38` Python with project root on `PYTHONPATH`. CPU checks instantiate only the existing fake-scene controller fixture. They verify all fixed assignments and exact release endpoints, per-environment clock handling, selected-four-only action replacement, actual inverse-codec/controller native-rate/bounds, and no snapshot state mutation.

```bash
PYTHONPATH="$PWD" /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/live_release_probe/verify_cpu.py
PYTHONPATH="$PWD" /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/live_release_probe/probe.py precommit --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/live_release_probe/precommit.json
```

Precommit strictly checks the existing checkpoint and teacher/reference evidence on CPU, and records exact script/input hashes plus all assignments. Changing script/input/protocol bytes invalidates the handoff. Independent review is required before GPU execution. No GPU run is authorized by this README; wait for the root task's explicit handoff after position and gradient probes. Then, in the established Isaac environment with CPU0–13 affinity and `KMP_AFFINITY=disabled`, invoke the separate `run-gpu --precommit ABSOLUTE_PRECOMMIT --out NEW_ABSOLUTE_OUTPUT` command. No training, checkpoint save or policy update occurs.
