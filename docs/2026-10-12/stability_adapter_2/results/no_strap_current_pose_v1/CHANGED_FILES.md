# 변경 파일과 입력 자료

## 결과 phase

- 한국어 비교 수치, 실제 native t0/t5 프레임과 두 영상: [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/README.md:1)
- strap-off 조건과 force API 기록: [no_strap_mode.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/no_strap_mode.json:1), [초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/initial_values.json:1)
- native 결과/영상 메타데이터: [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/report.json:1), [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/capture.json:1), [videos.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/videos.json:1), [hands.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/hands.mp4), [whole_body.mp4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/whole_body.mp4)
- 분석 검사와 종료 오류 기록: [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/analysis.json:1), [analysis_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/analysis_execution.json:1), [native execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/execution.json:1)
- 원 native 카메라 이미지: [손 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/hands), [전신 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/native/frames/whole_body)
- 저장 분석은 20개 초기필드 비교 exact를 기록한다. `all21_initial_fields_exact`는 분석 결과에 남아 있는 legacy check 이름이며 실제 비교 배열은20개다. [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/analysis.json:1)
- 이번 phase 전체 설정은 [NO_STRAP_VIDEO_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/NO_STRAP_VIDEO_PLAN.md:1), 현재 조건 runner는 [run_no_strap_current_pose.py](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_current_pose.py:44), 실행 runner는 [run_no_strap_video_phase.py](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_video_phase.py:22), 저장 분석기는 [analyze_no_strap_video.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_no_strap_video.py:20), 영상 수집기는 [collect_no_strap_videos.py](/home/ajou/yigyu/3/stability_adapter_2/collect_no_strap_videos.py:15), 후처리 runner는 [run_no_strap_postprocess.py](/home/ajou/yigyu/3/stability_adapter_2/run_no_strap_postprocess.py:21)다.
- strap-on 비교값은 [앞선 initial-middle3 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/initial_middle3_alignment_v1/README.md:1)에서 인용했다. 해당 자료는 별도 이전 실제 run이며 이번 실행에 합쳐 쓰지 않았다.

## 누적 경로

- 기존 140개를 보존하고 두 MP4를 더한 영상목록: [VIDEO_INDEX_v11.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v11.md:1), [video_collection_update_v10.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/video_collection_update_v10.json:1)
- root verification과 최종감사 지원 producer: [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/ROOT_VERIFICATION_NOTES.md:1), [root_final_audit_producer.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/root_final_audit_producer.py:17)
- root 누적 결과: [stability_adapter_2 README](/home/ajou/yigyu/3/stability_adapter_2/README.md:1110), [PLAN 체크포인트](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1931), [VISUAL_REPORT §111](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2024)에 append-only로 기록했다.

독립 검수는 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/no_strap_current_pose_v1/review.md:1), root 보존 감사는 봉인 단계의 별도 기록에 남긴다.
