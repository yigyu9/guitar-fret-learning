# 스트랩 영상 표시 변경파일·실제 줄

| 파일 | 1-based 실제줄 |
|---|---:|
| [strap_trial_recording.py](/home/ajou/yigyu/3/stability_adapter_2/strap_trial_recording.py:47) | 47 |
| [run_strap_recorded_diagnostic.py](/home/ajou/yigyu/3/stability_adapter_2/run_strap_recorded_diagnostic.py:18) | 18 |
| [run_strap_recorded_trial.py](/home/ajou/yigyu/3/stability_adapter_2/run_strap_recorded_trial.py:18) | 18 |
| [verify_strap_video.py](/home/ajou/yigyu/3/stability_adapter_2/verify_strap_video.py:9) | 9 |
| [STRAP_VIDEO_VISUALIZATION_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/STRAP_VIDEO_VISUALIZATION_PLAN.md:1) | 1 |
| [EXPERIMENT_WORKFLOW.md](/home/ajou/yigyu/3/stability_adapter_2/EXPERIMENT_WORKFLOW.md:126) | 126 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:898) | 898 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1648) | 1648 |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1676) | 1676 |

- [결과/이미지설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/README.md:1)
- [실제초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/initial_values.json:1)
- [투영/깊이분기와기존loop대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/root_preflight.json:1)
- [원자료/영상15검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/verification.json:1)
- [실제전신영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/whole_body.mp4)
- [실제손영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_video_v1/native/hands.mp4)

기존frozen camera/녹화helper/runner/공용자산/과거영상은수정하지않았다. 표시영상은native camera에실제route를overlay했고rawPNG도분리보존했다. 이번새actualphysics집계는근접진단entry 1회1200step이다. 일반상수entry는문법과원loop AST대조이며독립실행0이다. 독립검수는도구thread limit으로보류했다.
