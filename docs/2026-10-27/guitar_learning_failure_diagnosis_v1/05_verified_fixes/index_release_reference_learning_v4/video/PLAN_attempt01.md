# Actual V4 NN native video preparation

- [x] Reuse frozen learn.evaluate/GoalPolicy, including the actual selected-teacher prohibition context and all128 quotas. Camera subclass records after physical NN step and before resets.
- [ ] Await the chosen checkpoint and matching completed deterministic evaluation. No checkpoint was loaded and no native/GPU replay was executed during preparation.
- [ ] Run stdlib preflight/prepare with explicit checkpoint/evaluation; seal parent master pins plus source evaluation, checkpoint and own inputs. Independent review PASS is required before execute.
- [ ] Root alone executes the sealed replay. Compare all128 episode rows, q/target/body/candidate/raw NN goals exactly against the selected source evaluation; compare native capture poses exactly to replay. Force differences are reported separately.
- [ ] Inspect env0 first-attempt hand/fullbody clips: 354 controls,177frames,1280×720,30fps,5.9s. Fullbody camera (-.10,3.4,1.1), target(-.15,-.10,.65); hand camera uses current helper.

API: `video.py preflight --checkpoint ABS --evaluation ABS`; `video.py prepare --checkpoint ABS --evaluation ABS`; after independent review, `video.py gate-check` and `video.py execute`. Run with actual rl38 Python. `cpu_check.py` uses mock native surfaces and never loads the checkpoint. This is actual V4 NN evaluation, with NN-only selected four axes and unchanged native support for the other axes. No policy, gate, source checkpoint or parent result is changed.
