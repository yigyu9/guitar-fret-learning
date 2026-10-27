# 구현·계획 변경 위치

기존 frozen runner를 수정하지 않고 새 grip 실행과 후처리를 추가했다. source 시각화가 아닌 실제Gym 영상은 native 각 경로에 있다.

| 파일 | 실제 시작 줄 | 내용 |
|---|---:|---|
| [search_multi_face_grip.py](/home/ajou/yigyu/3/stability_adapter_2/search_multi_face_grip.py:27) | 27 | def left_fk |
| [audit_multi_face_grip_search.py](/home/ajou/yigyu/3/stability_adapter_2/audit_multi_face_grip_search.py:14) | 14 | def main |
| [multi_face_grip_audit.py](/home/ajou/yigyu/3/stability_adapter_2/multi_face_grip_audit.py:14) | 14 | def audit_initial |
| [run_multi_face_grip.py](/home/ajou/yigyu/3/stability_adapter_2/run_multi_face_grip.py:18) | 18 | def main |
| [analyze_multi_face_grip.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_multi_face_grip.py:23) | 23 | def main |
| [MULTI_FACE_GRIP_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/MULTI_FACE_GRIP_PLAN.md:1) | 1 |  |
| [MULTI_FACE_GRIP_REFINEMENT.md](/home/ajou/yigyu/3/stability_adapter_2/MULTI_FACE_GRIP_REFINEMENT.md:1) | 1 |  |
| [MULTI_FACE_GRIP_DIAGNOSTIC.md](/home/ajou/yigyu/3/stability_adapter_2/MULTI_FACE_GRIP_DIAGNOSTIC.md:1) | 1 |  |
| [MULTI_FACE_GRIP_PALM_REFINEMENT_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/MULTI_FACE_GRIP_PALM_REFINEMENT_PLAN.md:1) | 1 |  |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1277) | 1277 | 사용자 요청: 엄지 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:664) | 664 | 엄지 후면 |

`analysis_attempt_v1`/`v2`는 보완 이전 후처리 원문·결과·실행 로그다. 각 원문 SHA를 당시 입력목록과 exact 검증한 뒤 보존했다. 최종 summary/curves는 둘 모두와 exact이며 native 추가 실행은 없다.

v1/v2 source producer와 중단·실패 기록도 기존 경로에 보존했다. v1 계획 이후 v3 실제실행의 근거는 REFINEMENT/DIAGNOSTIC 문서를 따른다.
