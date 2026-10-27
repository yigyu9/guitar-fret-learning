# 변경 파일과 실제 줄

기존소비파일을보존하고새실행버전·계획·결과만추가했다. 메인4문서는원문prefix를유지해추가기록했다.

| 파일 | 실제 위치·용도 |
|---|---|
| [DEADLINE_TRAINING_PILOT_V1.md](/home/ajou/yigyu/3/stability_adapter_2/DEADLINE_TRAINING_PILOT_V1.md:1) | 시험학습범위·미인증항목·계획 |
| [DEADLINE_EXECUTION_V3.md](/home/ajou/yigyu/3/stability_adapter_2/DEADLINE_EXECUTION_V3.md:13) | 마감·30분운영·중단한계 |
| [deadline_native_v1.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:97) | 실제native환경·두baseline·820관측·81owner |
| [pilot_reward](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v1.py:52) | 명시적시험보상ledger |
| [deadline_ppo_v1.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_ppo_v1.py:14) | CUDA최적화·CPU/CUDA RNG불변checkpoint |
| [run_deadline_training_v3.py](/home/ajou/yigyu/3/stability_adapter_2/run_deadline_training_v3.py:76) | 실제장기entry·checkpoint·전체평가 |
| [deadline_rotation_v3.py](/home/ajou/yigyu/3/stability_adapter_2/deadline_rotation_v3.py:20) | 회전집합membership·밖거리상하한proxy |
| [test_deadline_native_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_native_v1.py:1) | 7순수codec/reward반례 |
| [test_deadline_ppo_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_ppo_v1.py:1) | 실제CPU/CUDA갱신·복원·거절검사 |
| [test_deadline_rotation_v3.py](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_rotation_v3.py:1) | 회전8묶음반례 |
| [test_deadline_schedule_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_deadline_schedule_v1.py:1) | 제어진입deadline3반례 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:884) | 메인계획추가 |
| [A README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1983) | 구현진행추가 |
| [D README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:653) | 결과추가 |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2433) | 영상결과추가 |
| [GPU_DIAGNOSIS.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/GPU_DIAGNOSIS.md:1) | GPU재확인과최초판단정정 |
| [이미지·영상문서](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/artifacts_smoke_v2/README.md:19) | native이미지/4영상/실측비교 |

소비된중간버전deadline_rotation_v1/v2,test_deadline_rotation_v1/v2,run_deadline_training_v1/v2도보존했다.각실패·검증로그는같은phase의rotation_checks,runner_checks,smoke_v1/v2에있다.사용한소스사본은source_at_launch_v3,기존메인사본은main_before_long_run_v3에상대경로를보존해저장했다.소스SHA/목표rate·범위/보상합대조는smoke_verification_v1.json에기록했다.
