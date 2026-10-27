# 변경 파일과 실제 줄 번호

구현/계획은 `/home/ajou/yigyu/3/stability_adapter_2/`, 결과/검증/이미지/영상은 이번 결과 디렉터리에 저장했다. 기존 코드나 실험 산출물을 삭제하지 않았다. 아래 줄 번호는 이번 파일의 실제1-based 정의 위치다.

| 파일 | 위치와 내용 |
|---|---|
| [JOINT_LEARNING_IMPLEMENTATION_V1.md](/home/ajou/yigyu/3/stability_adapter_2/JOINT_LEARNING_IMPLEMENTATION_V1.md:1) | 1차 범위·행동/관측 변경·검증 계획. 소비된 계획은 유지하고 완료 체크는 main PLAN에 추가 |
| [joint_policy_v1.py](/home/ajou/yigyu/3/stability_adapter_2/joint_policy_v1.py:14) | 14: 절대 anchor codec, 50: Actor/Critic, 62: 표본 action/latent/logprob/value, 69: PPO likelihood 재평가 |
| [joint_ppo_v1.py](/home/ajou/yigyu/3/stability_adapter_2/joint_ppo_v1.py:14) | 14: 설정, 44: GAE, 64: JointPPO, 76: update, 130: 이어지는 rollout 수집, 156: 불변 저장, 178: 계약 검증/복원 |
| [joint_learning_observation_v1.py](/home/ajou/yigyu/3/stability_adapter_2/joint_learning_observation_v1.py:13) | 13:739D block순서, 19: 합성, 45: 실제 측정 연결, 92:240Hz 측정, 108: timestamp 관측, 117: 학습 미완료 gate |
| [run_joint_policy_v2.py](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v2.py:17) | 실제 native entry. 동일 ABI checkpoint 복원/81정책 제어/5초 녹화/부분 로그 보존 |
| [run_joint_policy_v1.py](/home/ajou/yigyu/3/stability_adapter_2/run_joint_policy_v1.py:17) | syntax 소비 이력으로 보존. native 실행에는v2 사용 |
| [test_joint_learning_v1.py](/home/ajou/yigyu/3/stability_adapter_2/test_joint_learning_v1.py:15) | CPU22검사. 실제 synthetic optimizer 갱신과 종료·메모리·checkpoint 반례 |
| [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:870) | append: 상체 공동 학습 구조 완료/남은 보상 계약 |
| [stability_adapter_2/README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1969) | 같은 결과 append |
| [결과 메인 README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:639) | 결과 연결 append |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:2419) | 구조도/영상 결과 연결 append |
| [이번 결과 README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/README.md:1) | 한글 설명·구조도·native 이미지/영상·검증·후속 항목 |
| [verify_native_outputs_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/verify_native_outputs_v1.py:1) | raw 결과 후처리/검증 producer. 시뮬레이션·학습 코드는 아님 |

최종 이미지: [구조도v4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/artifacts/joint_learning_architecture_v4.png), [native 몽타주v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/artifacts/mean_policy_native_montage_v2.png). `artifacts/`의 producer/metadata와 이전 그림 버전은 소비 이력으로 보존한다. 구현 검수와 물리 실행은 root/change-reviewer, 그림 산출물만 Luna가 맡았다.

`native_mean_v2/`와 `native_sample_resume_v2/`에 실제 초기값,739D ABI, 입력SHA, 원표본/최종목표 로그, trace,240Hz 음악 측정/정산, 초기 정책 checkpoint, 전신/양손 PNG와 MP4가 있다. 세부 파일/절대 경로/SHA 전체 목록은 마감 inventory에 기록한다. `source_attempt_v1/`, `source_attempt_v2/`는 소비 당시 코드이고 `source_final/`은 최종 참조 사본이다. 이후 기존 main4 append로 바뀐 원본은 검증된 pre-append snapshot과 비교한다.
