# 파일 인덱스 — seed2_strap_initial_v1

그림 생성 단계에서는 artifact producer와 문서만 추가·수정했다. 실험 코드·설정·raw 결과는 수정하지 않았다; 이번 새 native 실행의 구현 경로는 [구현 인덱스](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/IMPLEMENTATION_FILES.md:1)에 정리돼 있다.

| 경로 | 내용 |
|---|---|
| [그림 producer](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_strap_initial_artifacts.py:47) | 저장 데이터 해시 확인, 세 조건 곡선·카메라 표 생성. 실행 진입점은 [main](/home/ajou/yigyu/3/stability_adapter_2/make_seed2_strap_initial_artifacts.py:57). |
| [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/README.md:1) | 표, 그림, 실행 범위와 한계. |
| [곡선 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_curves.png) | 5초 기타 오차 및 strap law 제출 scalar. |
| [카메라 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/seed2_strap_initial_hands_camera.png) | 실제 Gym 저장 프레임 2×3 비교. |
| [보존한 v2 이미지·manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v2/artifact_manifest.json) | v2 곡선·카메라 출력 및 manifest를 그대로 보존. |
| [v2 producer 보존 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v2/producer.py) | v2 manifest producer SHA와 exact 일치. v2 출력 및 manifest 보존. |
| [보존한 v1 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts/producer.py) | 파일 SHA가 v1 manifest의 producer SHA와 일치하는 원본 producer 사본. v1 이미지·manifest도 보존했다. |
| [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifacts_v3/artifact_manifest.json) | producer, 919개 입력, 두 출력의 SHA와 실행 요약. |
| [v3 artifact 실행 메타데이터](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifact_execution_v3.json) · [로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifact_execution_v3.log) | 최종 v3 producer의 실제 명령·환경·종료 코드. v1/v2 산출물은 보존했다; v1 producer 사본과 v2 producer 사본은 각 manifest SHA와 일치한다. |
| [검증 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/analysis.json) · [brief](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/artifact_brief.json) | Sol이 확정한 측정 요약과 그림 범위. |
| [current 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/current/report.json) · [taut 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/taut/report.json) · [preload 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/native/preload5n/report.json) | 각 1회 초기화/1200 physics step run의 보고서. 영상과 초기 설정은 각 run 하위 폴더에 있다. |
| [다음 계획](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STARTUP_TARGET_PLAN.md:1) | 아직 실행 전인 계획. |

v1/v2 산출물은 보존했다. 최종 v3은 세 축을 0–5 s로 표시하며 full-5s exact 재현 boolean은 관측값으로만 보존하고 그림 gate로 쓰지 않는다. 독립 검수 완료 — Critical/Warning/Suggestion 없음. [검수 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/seed2_strap_initial_v1/review.md:7).
