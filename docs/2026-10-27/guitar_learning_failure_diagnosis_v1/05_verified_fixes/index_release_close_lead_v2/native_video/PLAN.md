# V2 native camera replay preparation

- [x] Reuse V2 execution_scope/reference_raw and V1 run/Pool; camera-only subclass records after native step and before reset.
- [x] Keep full current source pins, baseline reuse metadata, noNN gates and original 128-attempt ledger.
- [x] V2 candidate/report.json completed128 and current input SHA audit verified; preflight PASS.
- [x] CPU-only `prepare` copied sealed source inputs and baseline files after headless completion.
- [ ] Independently review this folder and set its preparation_seal/review.json using the unchanged V1 gate contract.
- [ ] Root alone may run `execute` after review. No GPU/native/NN run was performed during preparation.
- [ ] Check video_verification.json, both FFmpeg clips and native_capture.npz: env0 first attempt fixed before execution; 354 controls, 177 frames, 1280×720 at 30fps, 5.9s.

Commands (from project root, using the same Python/environment as the V2 native candidate):

```
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_close_lead_v2/native_video/cpu_check.py
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_close_lead_v2/native_video/render.py preflight
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_close_lead_v2/native_video/render.py prepare
# Independent review and SHA seal required before this last command:
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/index_release_close_lead_v2/native_video/render.py execute
```

This is scripted-reference diagnostic footage, not a trained policy or checkpoint. It records the existing noNN V2 action path with native cameras. Fullbody camera position (-.10,3.4,1.1), target (-.15,-.10,.65); hand camera uses the current render helper. The graphics acquisition hook is restored immediately after Pool construction. V2 module aliases are restored by execution_scope, including failure paths. Camera/encoder failures preserve the original exception while Pool cleanup saves partial capture and reports encoder errors. Native capture poses must equal replay trace, and replay q/target/body/candidate plus all 128 episode rows must equal the original headless V2 results bit for bit. A mismatch writes failed video_verification.json and raises; the original source report is never modified.
