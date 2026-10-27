# 변경 파일 및 구현 경로

## 이번 단계 산출물

| 파일 | 변경 및 참조 |
|---|---|
| [Phase README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/README.md:1>) | 한국어 결과, 단위·비교 한계, 6-body source gap, 실제 영상·초기값 링크, producer 시도 이력 및 provenance. |
| [VISUAL_REPORT.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1432>) | 기존 §1–77 뒤에 §78과 그림 110–111만 추가했다. 앞부분은 수정하지 않았다. |
| [저장 분석](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/analysis.json>) | 7개 분석 check, 3 initialization/3600 steps, trial별 5초 trace와 요약. |
| [승인 산출 brief](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifact_brief.json>) | 표기할 field·단위 및 Sol 승인 비교 범위. |
| [오류 후처리 보존본](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifact_attempt_v1>) | Python 3.8의 `str.removeprefix` 호환 오류 실행본·로그·metadata를 보존했다(native_calls 0). |
| [성공 산출 실행 기록](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifact_execution.json>) · [성공 manifest](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/artifact_manifest.json>) | exit 0, 약 0.866초, 저장 입력 19개 전후 SHA 동일, native_calls 0, 두 PNG 출력 SHA 기록. |
| [그림 producer](</home/ajou/yigyu/3/stability_adapter_2/make_three_face_same_target_artifacts.py:139>) | `main()`에서 sealed saved-data 입력으로 PNG 2개와 manifest를 생성한다. 성공 실행 소비 후 producer는 수정하지 않았다. |
| [곡선 및 6-body 비교 그림](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/three_face_same_target_curves.png>) · [hands montage](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/artifacts/three_face_same_target_hands.png>) | 저장된 240 Hz 기타 오차, 세 trial × 여섯 초기 source gap, 실제 Gym hands 카메라 step 0/1200 montage. |

## 실험 구현 및 계획 참조

| 구현·계획 | 관련 코드 위치 |
|---|---|
| [Seed 2 source warmstart 준비](</home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_warmstart_trials.py:18>) | `main()`은 초기 left33 source 후보 계산 단계다. |
| [Projected support warmstart 준비](</home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_projected_warmstart_trials.py:18>) | `main()`은 별도 projected 후보의 source 검사 단계다. |
| [이번 three-face 후보 준비](</home/ajou/yigyu/3/stability_adapter_2/prepare_three_face_same_target_trials.py:18>) | `main()`에서 같은 목표 비교용 admitted trial을 준비한다. |
| [기록 실행기](</home/ajou/yigyu/3/stability_adapter_2/run_seed2_support_warmstart.py:18>) | `main()`에서 새 native 실행과 실제 5초 카메라 기록을 수행한다. |
| [66축 목표 compose helper](</home/ajou/yigyu/3/stability_adapter_2/warmstart_targets.py:5>) | `compose()`는 66 relative offset과 bounds를 검사한다. |
| [저장자료 분석기](</home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_support_warmstart.py:20>) | `main()`은 raw trace/contact/video와 run contracts를 재검증한다(native 재실행 없음). |
| [초기 관측각 실행 설계](</home/ajou/yigyu/3/stability_adapter_2/SEED2_SUPPORT_WARMSTART_EXECUTION.md:1>) · [투영 후보 계획](</home/ajou/yigyu/3/stability_adapter_2/SEED2_PROJECTED_SUPPORT_WARMSTART_PLAN.md:1>) | native0으로 거절한 source-only 준비 분기의 설계와 범위. |
| [이번 source 준비 계획](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_INITIAL_SAME_TARGET_PLAN.md:1>) · [다음 미실행 계획](</home/ajou/yigyu/3/stability_adapter_2/THREE_FACE_FINGER_TARGET_HOLD_PLAN.md:1>) | 현재 비교 조건과 이후 finger-target hold 방향. 다음 계획은 아직 실행하지 않았다. |

## Root 소유 기준 문서

- [주요 계획](</home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1466>), [프로젝트 README](</home/ajou/yigyu/3/stability_adapter_2/README.md:821>), [날짜별 README](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:497>)는 root가 관리한다.
- 최종 독립 검수와 입력·출력 대조 결과는 [review.md](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/review.md>) 및 [final_verification.json](</home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/three_face_initial_same_target_v1/final_verification.json>)에 기록한다.
- 산출물 정리 에이전트는 이전 native 자료·§1–77·root 소유 README/계획을 수정하지 않았다. root의 새 계획/README 변경은 위 링크에 기록했다.
