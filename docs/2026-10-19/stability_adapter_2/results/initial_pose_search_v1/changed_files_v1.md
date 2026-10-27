# 변경 파일·실제 줄 번호

이번 단계에서 새로 만든 소스/계획과 메인 문서 추가 위치다. 소비한 V1/V2 및 실패 출력은 보존했다. 이전 qualification 소스·공용 자산·기존 stability_adapter는 변경하지 않았다.

| 파일·줄 | 변경 내용 |
|---|---|
| [INITIAL_POSE_SEARCH_PLAN_V1.md:1](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_PLAN_V1.md:1) | 소단계 범위·판정·보호 조건 |
| [INITIAL_POSE_SEARCH_GEOMETRY_ADDENDUM_V1.md:1](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_GEOMETRY_ADDENDUM_V1.md:1) | 왼쪽 상완–몸통 자체겹침 회피 보완 |
| [search_initial_pose_v1.py:22](/home/ajou/yigyu/3/stability_adapter_2/search_initial_pose_v1.py:22) | 초기 source 시도·4탈락 partial 보존 |
| [search_initial_pose_v2.py:35](/home/ajou/yigyu/3/stability_adapter_2/search_initial_pose_v2.py:35) | 7변형·고정 기타좌표 손목/관절여유·형상 검사 |
| [run_initial_pose_search_v1.py:109](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v1.py:109) | 초기 wrapper 버전 보존 |
| [run_initial_pose_search_v2.py:109](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v2.py:109) | 중간 wrapper 버전 보존 |
| [run_initial_pose_search_v3.py:17](/home/ajou/yigyu/3/stability_adapter_2/run_initial_pose_search_v3.py:17) | 실제 9회 native 진입·초기값/전체경과/명령/접촉/보호 기록 |
| [render_initial_pose_search_v1.py:15](/home/ajou/yigyu/3/stability_adapter_2/render_initial_pose_search_v1.py:15) | 보호 종료 직전 camera 4~8tick 간격 검사 |
| [audit_initial_pose_search_240hz_v1.py:11](/home/ajou/yigyu/3/stability_adapter_2/audit_initial_pose_search_240hz_v1.py:11) | 실제 active33위치/81속도240Hz 보충 |
| [summarize_initial_pose_search_v1.py:12](/home/ajou/yigyu/3/stability_adapter_2/summarize_initial_pose_search_v1.py:12) | 9회 비교·정지초기값·81각도 CSV·재현 SHA |
| [INITIAL_POSE_SEARCH_COMPLETION_V1.md:1](/home/ajou/yigyu/3/stability_adapter_2/INITIAL_POSE_SEARCH_COMPLETION_V1.md:1) | 완료 체크리스트·사용 범위와 후속 소단계 |
| [README.md:2501](/home/ajou/yigyu/3/stability_adapter_2/README.md:2501) | 메인 설명에 결과 추가 |
| [PLAN.md:1417](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1417) | 메인 계획에 결과 추가 |

결과·초기값·영상 위치:

- [결과 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/README.md:1)
- [모든 비교/최대값·SHA](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/report.json:1)
- [정지 초기값JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_initial_values.json:1)
- [81관절각 CSV](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/comparison_v1/static_candidate_joint_angles.csv:1)
- [이미지/영상 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/README_final_v1.md:1)
- [영상 모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/initial_pose_search_v1/README_final_v1.md:1)
