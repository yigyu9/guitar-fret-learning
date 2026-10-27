# 변경 파일·입력 색인

## 신규 producer와 계획

- [render_best_run_video.py:1](/home/ajou/yigyu/3/stability_adapter_2/render_best_run_video.py:1): 저장 자세의 source-geometry 영상 producer.
- [render_best_run_video.py:140](/home/ajou/yigyu/3/stability_adapter_2/render_best_run_video.py:140): 입력·output guard, source probe 및 저장 자세 재생.
- [render_best_run_video.py:180](/home/ajou/yigyu/3/stability_adapter_2/render_best_run_video.py:180): 두 fps 인코딩, ffprobe 검증, 해시 manifest.
- [replay_contact_geometry.py:10](/home/ajou/yigyu/3/stability_adapter_2/replay_contact_geometry.py:10)와 [initial_overlap.py:9](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:9): 기존 source probe 경로 재사용.
- [plot_joint_hold.py:172](/home/ajou/yigyu/3/stability_adapter_2/plot_joint_hold.py:172): 기존 geometry asset 열거 helper 재사용.
- [BEST_RUN_VIDEO_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/BEST_RUN_VIDEO_PLAN.md:1) 및 [PLAN.md §57:1038](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1038): 작업 계획과 선택 근거.

## 선택 입력과 저장 결과

- [selection.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/selection.json:1), [full_run_candidates.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/full_run_candidates.json:1), [selection_inputs_manifest.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/selection_inputs_manifest.json:1): 54개 기존 전체 실행 비교 및 입력 SHA.
- 선택 원자료: [report.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125/report.json:1), [states.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125/states.json:1), [trace.json:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125/trace.json:1).
- [OSMesa probe log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/osmesa_probe.log)와 [EGL probe log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/egl_probe.log): 기존 렌더러 확인 이력.
- 최종 producer-aligned output: [render_v2/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/), [manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/render_manifest.json), [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/render_execution.json), [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/render_execution.log).
- [README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/README.md:1) 및 [VISUAL_REPORT.md §49:926](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:926): 영상 링크, 조건과 한계.

[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/review.md:7)를 완료했다. 기존 첫 제작본과 원자료는 보존했다.

- [자율결정 운영 지침](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:18)과 [프로젝트 README 기록](/home/ajou/yigyu/3/stability_adapter_2/README.md:477): 사용자 새 지침을 반영했다.
