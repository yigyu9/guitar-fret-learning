# 변경 파일 인덱스 — palm_plane_alignment_v1

이번 산출물은 저장 자료를 읽어 만든 그림과 설명이며 native 실행·물리 step은 추가하지 않았다.

- [plot_palm_plane_alignment.py](/home/ajou/yigyu/3/stability_adapter_2/plot_palm_plane_alignment.py:26) — 검증 입력을 읽고 세 지표 그림 생성.
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/README.md:1) — 수치표, 측정 정의, 한계와 기존 native camera 이미지.
- [palm_plane_alignment.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/palm_plane_alignment.png) — OFF/bias/tracking 저장 관측 그림.
- [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/plot_manifest.json) 및 [plot_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/plot_execution.json) — 입력·producer·출력 SHA와 실행 환경.
- [plot_execution.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/plot_execution.log) — plotter 실행 로그.
- [검증된 측정 입력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/validated/measurements.json) 및 [verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/verification.json) — 3개 구조 검사, 0 native initialization, 0 physics step.
- 재사용한 [기존 Isaac Gym native camera frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/native_tracking/blue_front_024.png) — 새 camera capture 없음.
- [설계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_PLANE_ALIGNMENT_PLAN.md:1), [VISUAL_REPORT §58](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1050), [결과 README 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:339).

검수 완료: [독립 검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/review.md:9)에 미해결 지적사항은 없다.

- [저장 pose 면 측정 구현](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_plane_alignment.py:35)
- [프로젝트 현재 제안 요약](/home/ajou/yigyu/3/stability_adapter_2/README.md:538)

최종 현재 소스 사본은 `source_final_manifest.json`, 이번 phase 파일은 `artifact_inventory.json`에 SHA를 기록한다.
