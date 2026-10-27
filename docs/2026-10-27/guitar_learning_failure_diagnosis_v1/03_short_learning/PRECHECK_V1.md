# 고정 팔 목표각 사전검사: 학습 진입 보류

large·4환경·H32의 GPU 수집/PPO1회·저장 및 strict 초기모델 로드는 두 목표에서 통과했다. 이는 과제 학습 성과가 아니라 구현 smoke다. 원래 음 길이를 유지한 reference 대조의 결과는 다음과 같다.

| 실제 원곡 단일 목표 | 달성 / 시도 | 평균 clean | audible wrong | 물리/손목 실패 |
| --- | ---: | ---: | ---: | ---: |
| 중지 row8, 길이0.1174초 | 0/4 | 0% | 0% | 0/4 |
| 중지 row9, 길이0.2322초 | 0/4 | 0% | 100% | 0/4 |

팔12축·선정4축 모두 source 접촉 순간의 목표각까지3초 유한 ramp로 움직였다. 학습 정책이 압현한 것이 아니다. row8은3.6초에도 목표 패드 거리가 약19.2mm, 평면 높이가 약8.7mm였고 row9는 오압현이 유지됐다. 두 목표 모두 사전 진입 기준을 통과하지 못했으므로300회 비교는 시작하지 않았다.

원본 접촉 순간의 **실제각과 제어 목표각은 다르다.** source FK를 저장된 native 손목 pose와 비교한 오차는 최대2.10µm/9.60e−7rad로 작았다. 다른 실제각은 유지하고 팔12축만 source 목표각으로 바꿔 계산하면 손목 위치/방향이 row8에서56.57mm/23.50도, row9에서57.59mm/13.47도 달랐다. 따라서 그 순간의 목표각을 정적인 접촉 자세로 취급할 수 없다. [원본 actual/target 및 FK 검산](../02_contact_reward/wrist_pose_proposal_readonly.json)

다음 보정은 선택 손가락이나 패드 오차를 추종하지 않고, 팔12축만 source의 **실제 손목 위치·방향**을 유지하는 별도 진단 조건이다. 배치 ramp2초·원래 audible onset3초로 구분하고, 첫 tick부터 모든 전이를 수집한다. native 범위/PD/힘/속도·접촉/보상·종료 문턱은 유지한다. 이 조건도 실제 GPU 사전검사를 통과해야 하며 아직 학습 준비가 됐다고 판단하지 않는다.

[그래프](precheck_joint_targets.png) · [수치](precheck_joint_targets.json) · [row8 원결과](smoke_inc_row8_reference/evaluation.json) · [row9 원결과](smoke_inc_row9_reference/evaluation.json)
