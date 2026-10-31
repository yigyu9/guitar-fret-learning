# V5 actual NN native video

- [x] Reuse frozen V4/video/video.py and cameras.py without copying the camera runtime or changing any parent source.
- [x] Bind the V5 experiment, settings and numerical imports only inside a scope; restore module aliases, reused globals and import paths on success or failure.
- [x] Selected completed deterministic final300 runs/ppo_eval_000300_det and exact runs/ppo/final.pt, last300 regardless of score as predeclared. Actual pair stdlib preflight PASS; checkpoint loads0/native replay0 during preparation.
- [ ] CPU-only preflight/prepare with explicit pair; source must be completed V5 schema, own checkpoint SHA frozen, checkpoint_updates300, full128 quotas and NN-only helper calls0. No selected-pair seal is created before those artifacts exist.
- [ ] Independent final preparation review PASS required; root alone may execute after sealing. No checkpoint is loaded and no native/GPU replay is run during this preparation.
- [ ] Verify full128 episode ledger and q/target/body/candidate/raw NN goals exactly against the selected deterministic evaluation. Native capture poses must equal replay poses. Force differences remain separately reported.
- [ ] Inspect native hand/fullbody clips: preselected env0 first attempt,354controls,177frames,5.9s,1280×720,30fps. Upright fullbody camera position(-.10,3.4,1.1), target(-.15,-.10,.65), unchanged frozen V4 helper.

API: actual rl38 `video.py preflight --checkpoint ABS --evaluation ABS`; then `video.py prepare --checkpoint ABS --evaluation ABS`; after independent review, `video.py gate-check` and `video.py execute`. The frozen V5 learner supplies its own reward settlement contract and the existing NN-only four-axis guard; no teacher blending or old-checkpoint compatibility is added. The wrapper does not assert success from release alone.

Selected V5 failure footage: all3=0/128, A0/128, B7 128/128, B8 127/128; A released105/128. Release without achievement is not success. Preliminary code review files are unchanged; final selected-pair preparation review remains required.
