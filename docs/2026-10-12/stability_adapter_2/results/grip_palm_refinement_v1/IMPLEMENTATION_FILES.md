# 구현·계획 실제 줄 인덱스

기존 multi_face_grip_v3 source와 raw는 동결 보존하고 다음 파일을 추가했다. 초기각만 바꾼 새두실행과 저장된 seed2 비교를 구분한다.

| 파일 | 실제 시작 줄 | 역할 |
|---|---:|---|
| [search_grip_palm_refinement.py](/home/ajou/yigyu/3/stability_adapter_2/search_grip_palm_refinement.py:12) | 12 | def main |
| [run_grip_palm_refinement.py](/home/ajou/yigyu/3/stability_adapter_2/run_grip_palm_refinement.py:18) | 18 | def main |
| [analyze_grip_palm_refinement.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_grip_palm_refinement.py:24) | 24 | def main |
| [GRIP_PALM_REFINEMENT_EXECUTION.md](/home/ajou/yigyu/3/stability_adapter_2/GRIP_PALM_REFINEMENT_EXECUTION.md:1) | 1 |  |
| [GRIP_PALM_REFINEMENT_SELECTION.md](/home/ajou/yigyu/3/stability_adapter_2/GRIP_PALM_REFINEMENT_SELECTION.md:1) | 1 |  |
| [SEED2_STRAP_INITIAL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/SEED2_STRAP_INITIAL_PLAN.md:1) | 1 |  |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1296) | 1296 | seed2 손바닥 초기 |
| [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:678) | 678 | seed2 손바닥 접근 |

앞선 손바닥 보완 계획은 원본과 이전 source_final snapshot을 보존하며 완료 체크는 현재 main PLAN에 남긴다. 다음 strap 계획은 아직 미실행이다.
