# 변경 파일과 실제 줄 번호

기존 모델·실험은 보존하고 아래 새 구현을 추가했다. 소비된 중간 버전은 수정하거나 삭제하지 않는다.

## 현재 구현

- [search_right_thigh_waist_v5.py](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v5.py:22)
- [run_right_thigh_waist_v3.py](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v3.py:8)
- [analyze_right_thigh_waist_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:12)
- [left_arm_clearance_source_v2.py](/home/ajou/yigyu/3/stability_adapter_2/left_arm_clearance_source_v2.py:17)
- [RIGHT_THIGH_WAIST_COMPLETION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_COMPLETION_V1.md:1)

## 단계별 계획과 보존 버전

source3/helper1은 box 검수 실패로 fitting/native에 사용하지 않았다. run1은 source 입력에 소비됐으나 native는 미실행이고 run2의 첫 native는 중단 이력이다.

- [RIGHT_THIGH_WAIST_ELBOW_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_ELBOW_PLAN_V1.md:1)
- [RIGHT_THIGH_WAIST_PLAN_V1.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V1.md:1)
- [RIGHT_THIGH_WAIST_PLAN_V2.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V2.md:1)
- [RIGHT_THIGH_WAIST_PLAN_V3.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V3.md:1)
- [RIGHT_THIGH_WAIST_PLAN_V4.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V4.md:1)
- [RIGHT_THIGH_WAIST_PLAN_V5.md](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V5.md:1)
- [left_arm_clearance_source_v1.py](/home/ajou/yigyu/3/stability_adapter_2/left_arm_clearance_source_v1.py:1)
- [run_right_thigh_waist_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v1.py:1)
- [run_right_thigh_waist_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v2.py:1)
- [search_right_thigh_waist_v1.py](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v1.py:1)
- [search_right_thigh_waist_v2.py](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v2.py:1)
- [search_right_thigh_waist_v3.py](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v3.py:1)
- [search_right_thigh_waist_v4.py](/home/ajou/yigyu/3/stability_adapter_2/search_right_thigh_waist_v4.py:1)

## 결과와 재현 입력

- [결과 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/README.md:1)
- [초기 후보/81각](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/search_v5/shift95_front30_roll-5/candidate.json:1)
- [실제 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/native_elbow5_v1/initial_values.json:1)
- [팔꿈치 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/config_v1/elbow5_roll5.json:1)
- [완료 조건 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/analysis_final_v1/analysis.json:1)
- [부분 중단 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/partial_analysis_v1.json:1)
- [부분 분석 재현](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/audit_partial_v1.py:1)

## 현재 설명·시각화와 메인 계획 반영

- [메인 계획 추가](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1201)
- [작업 인계 추가](/home/ajou/yigyu/3/stability_adapter_2/README.md:2293)
- [결과 색인 추가](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/README.md:126)
- [형상 입력 검사 지침 보완](/home/ajou/yigyu/3/stability_adapter_2/AGENTS.md:19)
- [최종 이미지·영상 설명 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/README_V3.md:1)
- [정정 시각화 생성 코드 V3](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/artifacts_v1/build_artifacts_v3.py:1)
- [영상 전체 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_thigh_waist_v1/INDEX_V1.md:1)
- [실제 실행 독립 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/review_native_v1.md:1)
- [최종 독립 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/review_final_v1.md:1)
- [보존·입력·영상 최종 확인 코드](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/seal_outputs_v1.py:1)

V1/V2 도식은 오류 이력으로 보존하고 V3 설명을 현재 참조로 사용한다. 위 메인 문서 네 개는 원문을 보존한 추가이며, 변경 전 snapshot과 SHA 기록은 navigation_update_v1.json 및 workflow_update_v1.json에 있다.
