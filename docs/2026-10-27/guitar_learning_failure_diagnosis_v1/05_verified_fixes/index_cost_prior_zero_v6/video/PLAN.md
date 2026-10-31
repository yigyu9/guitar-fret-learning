# V6 actual NN native video

- [x] Reuse immutable V4/video camera runtime and replay verification. No parent or historical source is copied or changed.
- [x] Bind the V6 experiment and execute through its actual local_modules(include_learn=True) context after all gates and Isaac import. Restore numerical aliases, camera alias, paths and reused globals on success/error.
- [ ] Await completed V6 last300 deterministic evaluation and exact own checkpoint. Last300 is selected regardless of score by the existing evaluation_schedule.json.
- [ ] Run CPU-only explicit-pair preflight/prepare. Require V6 schema, checkpoint_updates300, matching frozen checkpoint SHA, original128 quotas and NN-only helper calls0. Own selected_control must say actual V6 NN only and be correctly pinned.
- [ ] Independent final preparation PASS required before root executes. No selected-pair seal, checkpoint loading or native/GPU replay during this preparation.
- [ ] Verify full128 episode ledger plus q/target/body/candidate/raw NN goals exactly; native capture poses equal replay poses. Force differences are separately reported.
- [ ] Inspect env0 first-attempt hand/fullbody clips:354controls,177frames,5.9s,1280×720,30fps; frozen upright camera(-.10,3.4,1.1) targeting(-.15,-.10,.65).

API: actual rl38 `video.py preflight --checkpoint ABS --evaluation ABS`; `video.py prepare --checkpoint ABS --evaluation ABS`; after independent review, `video.py gate-check` and `video.py execute`. V6 retains V5 physics, actor, settlement and nine rewards; the only training initialization difference is the two zero-initialized learnable cost-head tensors. The wrapper never substitutes another reward contract or treats release alone as success.
