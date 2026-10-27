# Changed files — three_face_support_loss_v1 artifacts

| File | Contents / source reference |
|---|---|
| [make_three_face_support_loss_artifacts.py](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_support_loss_artifacts.py:27) | Frozen original producer; `main()`. Initial font lookup failure is preserved in `artifact_attempt_v1`. |
| [make_three_face_support_loss_artifacts_v2.py](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_support_loss_artifacts_v2.py:27) | Frozen v2 producer; render passed, layout was rejected in visual QA and preserved under `artifact_layout_v2`. |
| [make_three_face_support_loss_artifacts_v3.py](/home/ajou/yigyu/3/stability_adapter_2/make_three_face_support_loss_artifacts_v3.py:27) | Final frozen producer; `main()`. Provenance and two final PNG hashes are in `artifacts_v3/artifact_manifest.json`. |
| [run_three_face_shape_readback.py](/home/ajou/yigyu/3/stability_adapter_2/run_three_face_shape_readback.py:18) · [실행본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/runner_source.py:18) | New preserved runner source; `read_native_shapes()` line 18 and `main()` line 42. |
| [analyze_three_face_support_loss.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_three_face_support_loss.py:24) · [실행본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/analysis_source.py:24) | New preserved analyzer source; `main()`. |
| [THREE_FACE_ARM_INITIAL_TARGET_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_ARM_INITIAL_TARGET_PLAN.md:1) | New next diagnostic plan; unexecuted. |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1502) | Updated main experiment plan reference. |
| [stability_adapter_2 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:839) | Updated project README reference. |
| [dated stability_adapter_2 index](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:507) | Updated dated result index reference. |
| [VISUAL_REPORT.md §80](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1500) | Appended §80 only. Figure 114 heading is line 1513; figure 115 heading is line 1519. Sections 1–79 are unchanged. |
| [phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/README.md:1>) | Scope, measurements, artifact captions, native media, provenance, and limitations. |
| [CHANGED_FILES.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/CHANGED_FILES.md:1>) | This source and file index. |
| [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/review.md:1>) | Independent review record. |
| [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/final_verification.json:1>) | Final preservation and SHA verification record. |

| Artifact attempt | Result and preserved record |
|---|---|
| v1 | Exit 1 at font-family lookup, native calls 0; [artifact_attempt_v1](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_attempt_v1/>). |
| v2 | Exit 0 in 11.918461 s, native calls 0; rendered but layout rejected; [artifact_layout_v2](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_layout_v2/>). |
| v3 | Exit 0 in 11.23134584305808 s, native calls 0; accepted two-PNG layout, 10,679 input hashes equal before and after; [execution](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifact_execution_v3.json>), [manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_support_loss_v1/artifacts_v3/artifact_manifest.json>). |
