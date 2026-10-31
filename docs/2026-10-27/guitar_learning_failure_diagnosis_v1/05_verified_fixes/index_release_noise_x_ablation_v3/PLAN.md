# V3 single-axis applied noise ablation

Parent authorized CPU preparation within the diagnostic plan. This is a noNN scripted reference experiment, with no policy/checkpoint/PPO. The baseline and deterministic V2 candidate below are copied evidence, not new native runs.

- [x] Preserve the V2 schedule/goals, all four Normal draws at seed7 and original noise hash; zero only applied noise column0 (selected action17, index1_x).
- [x] Freeze original V1 run source in input pins and require exactly three guarded AST edits: clone/mask after original hash, change only addition RHS, save applied_noise beside original scaled_noise.
- [x] CPU arithmetic checks: all39 exact with zero mask; only action17 can change; other3 draws and RNG state exact; exception restores V2 aliases.
- [x] Copy V2 baseline and deterministic candidate report/evaluation with explicit provenance; preserve full 488-pin current source chain plus noisy evidence and own input seal.
- [ ] Independent reviewer must seal PASS review.json through the unchanged base.gate.
- [ ] Root alone executes one new noisy_candidate native128 experiment after review. No native/GPU execution during preparation.
- [ ] Inspect completed128/all128 denominator, nine reward components, unchanged PD/guard/action-range gates, original noise hash, saved original draws and applied_noise, partial/error preservation and inputs_after.

Commands, from project root with the existing diagnostic environment:

```
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_noise_x_ablation_v3/probe.py prepare
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_noise_x_ablation_v3/probe.py gate-check
# Only after independent review, root may execute:
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_noise_x_ablation_v3/probe.py execute
```

No sigma, target schedule, angle, reward, controller, physical state or failure-threshold tuning. Original base.run's first-attempt quotas, 128 denominator, guard audits, seed boundary, lifecycle/error handling and partial files stay intact. Original scaled_noise and original full128 draw hash remain intact; applied_noise is separately logged for the same first4 streams. No archived implementation or checkpoint is imported.

Actual runtime compatibility: Python3.8.20 rl38 CPU354 arithmetic, source preflight and syntax PASS. Initial system-Python-only preparation and unsupported ast.unparse source are preserved in preparation_failures/attempt01; exact ast.dump template matching now supports the real runtime. Own review remains pending; no GPU execution.
