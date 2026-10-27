# 이번 소단계 변경 파일

기존 `stability_adapter/`와 이전 결과는 보존했다. 아래 구현은 `stability_adapter_2/`에 새로 추가한 파일이다. 실행에 쓰인 시점별 원본은 각 실행의 `source_before/`에, 마감 시점 사본은 `source_final/`에 구분해 보관한다. posture 분석기 v1/v2는 미실행 초안이며 최종 네 조건 분석은 posture v3이다. 접촉추종 분석기 v1과 그 세 조건 결과도 실행 기록으로 보존했다.

| 파일 (절대 경로·실제 시작 줄) | 역할 |
|---|---|
| [PALM_THUMB_POSTURE_SUPPORT_V1_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_POSTURE_SUPPORT_V1_PLAN.md:1) | 소단계 계획 |
| [PALM_THUMB_SUPPORT_V1_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_SUPPORT_V1_PLAN.md:1) | 소단계 계획 |
| [PALM_THUMB_SUPPORT_V2_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_SUPPORT_V2_PLAN.md:1) | 소단계 계획 |
| [PALM_THUMB_SUPPORT_V3_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_THUMB_SUPPORT_V3_PLAN.md:1) | 소단계 계획 |
| [analyze_palm_thumb_posture_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_posture_support_v1.py:14) | 후처리 비교 분석 |
| [analyze_palm_thumb_posture_support_v2.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_posture_support_v2.py:14) | 후처리 비교 분석 |
| [analyze_palm_thumb_posture_support_v3.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_posture_support_v3.py:14) | 후처리 비교 분석 |
| [analyze_palm_thumb_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:14) | 후처리 비교 분석 |
| [palm_thumb_posture_preserved_v1.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_posture_preserved_v1.py:12) | 실행 전후 입력 보존 |
| [palm_thumb_posture_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_posture_support_v1.py:6) | 단일 PD 목표의 제한된 지지 보정 |
| [palm_thumb_support_preserved_v1.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_preserved_v1.py:12) | 실행 전후 입력 보존 |
| [palm_thumb_support_preserved_v2.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_preserved_v2.py:12) | 실행 전후 입력 보존 |
| [palm_thumb_support_preserved_v3.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_preserved_v3.py:12) | 실행 전후 입력 보존 |
| [palm_thumb_support_search_v1.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_search_v1.py:15) | 정적 초기각 탐색 |
| [palm_thumb_support_search_v2.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_search_v2.py:15) | 정적 초기각 탐색 |
| [palm_thumb_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_support_v1.py:6) | 단일 PD 목표의 제한된 지지 보정 |
| [run_palm_thumb_posture_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_posture_support_v1.py:15) | native 시뮬레이션·기록 |
| [run_palm_thumb_posture_support_v1.sh](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_posture_support_v1.sh:1) | 실행 환경 진입점 |
| [run_palm_thumb_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v1.py:15) | native 시뮬레이션·기록 |
| [run_palm_thumb_support_v1.sh](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v1.sh:1) | 실행 환경 진입점 |
| [run_palm_thumb_support_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v2.py:15) | native 시뮬레이션·기록 |
| [run_palm_thumb_support_v2.sh](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v2.sh:1) | 실행 환경 진입점 |
| [run_palm_thumb_support_v3.py](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v3.py:15) | native 시뮬레이션·기록 |
| [run_palm_thumb_support_v3.sh](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_support_v3.sh:1) | 실행 환경 진입점 |
| [test_palm_thumb_posture_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_palm_thumb_posture_support_v1.py:12) | 수치 계약 검사 |
| [test_palm_thumb_support_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_palm_thumb_support_v1.py:12) | 수치 계약 검사 |

## 갱신한 메인 문서

- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:694)
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1892)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:587)
- [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2335)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/README.md:1)
- [FILE_INDEX.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/FILE_INDEX.md:1)

## 결과·검수·검증

- [이미지·초기값·영상 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/FILE_INDEX.md:1)
- [독립 최종 검토](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/review_final.md:1)
- [최종 검사 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/final_verification.json:1)
- [마감 파일 SHA 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/artifact_inventory.json:1)

`baseline_v3`는 5초 물리 실행 후 입력 SHA 실패로 제외된 기록이다. 카메라 SIGSEGV 세 실행은 부분 영상이며, 정식 비교는 `analysis_final/`의 네 완료 조건이다.
