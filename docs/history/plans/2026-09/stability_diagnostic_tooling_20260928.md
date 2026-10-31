# Stability Adapter diagnostic tooling

## Goal

Add the missing diagnostics needed to separate policy, controller, oscillation,
restore-noise, and WAIT→REACH boundary failures before another long run.

## Checklist

- [x] Add identical-state controller/policy residual A/B diagnostic.
- [x] Add settle-gate streak, co-failure, and reset-window trace analyzer.
- [x] Add oscillation, energy, and signal-correlation trace analyzer.
- [x] Add per-environment snapshot restore/noise rejection profiler.
- [x] Add WAIT-terminal versus validated-REACH boundary comparator.
- [x] Add focused tests for simulator-independent analysis logic.
- [x] Run syntax/tests and focused GPU smoke diagnostics.
- [x] Request independent change review and document commands/outputs.

## Success criteria

- Every tool writes machine-readable JSON with input/source hashes.
- A/B modes begin from independently restored identical snapshots.
- Trace analyzers operate without Isaac Gym or a GPU.
- Restore profiling reports rejection reasons rather than only retry means.
- Boundary comparison reports state jumps and teacher outcomes for both starts.
- Existing training and render behavior remains unchanged.
