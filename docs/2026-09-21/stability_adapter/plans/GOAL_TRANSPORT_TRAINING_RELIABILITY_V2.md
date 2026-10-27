# Goal-conditioned TRANSPORT training reliability v2

## Objective

Make teacher-free TRANSPORT PPO produce diagnosable, resumable training runs
without allowing one failed parallel environment to truncate every other
trajectory.  Remove the positive idle-policy reward before spending more GPU
time.

## Scope

- Preserve the existing functional-grip snapshot and physical environment.
- Keep synchronized snapshot warmup, because warmup advances the shared
  simulator.
- Replace immediate `done.any()` batch resets with an active-environment cycle.
- Persist metrics on every update and make checkpoints resumable.
- Add termination, grip, progress, action, and restore diagnostics.
- Do not connect this policy to Synchronizer or MAINTAIN in this change.

## Checklist

- [x] Add masked GAE and active-environment lifecycle helpers with CPU tests.
- [x] Keep successful/failed environments inactive until a safe synchronized
      cycle reset while healthy environments continue.
- [x] Remove the positive per-frame grip survival reward and make zero-action
      idling negative.
- [x] Save the first update, write JSONL/status files atomically, and support
      policy-state resume.
- [x] Record valid sample counts, completion reasons, movement errors, grip
      validity, action saturation, and update timing.
- [x] Preserve legacy functional-grip snapshot compatibility across trainer-only
      changes.
- [x] Run unit/compatibility tests and a GPU smoke run.
- [x] Request an independent change review and resolve findings.
- [x] Update the training README and provide the new minimal command.

## Acceptance criteria

1. A done row no longer marks healthy rows as PPO boundaries or resets their
   episode returns.
2. Post-terminal inactive samples contribute neither GAE nor PPO loss.
3. The all-idle, valid-grip reward is negative before timeout.
4. Update 1 creates a checkpoint and one durable JSONL metric row.
5. Resume restores model, optimizer, normalizer, curriculum, counters, and RNG
   state, then starts a fresh synchronized physical cycle.
6. A short GPU run completes at least two updates, writes artifacts, and can
   resume for another update.
