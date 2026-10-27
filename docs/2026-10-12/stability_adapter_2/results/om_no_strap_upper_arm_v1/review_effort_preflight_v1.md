# 오른팔 actuator effort 사전 검수

판정: **문제없음**. Critical 0 / Warning 1 / Suggestion 0. 원 v10/V11과 최종 실행용 v11/V12, effort config/reference·사전 입력 기록을 읽기 전용으로 검토했다. 지정한 리뷰 외 파일 수정·추가 native 실행·학습은 하지 않았다.

- [effort guard:19](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v11.py:19): human actor·동일 env·81D finite·오른12 외0·native effort cap·physics owner/window를 함께 제한한다. 실제 guard를 CPU에서 실행해 정상 제출1회와 actor/env/shape/finite/mask/cap/owner/window 위반8개 거절, runtime PD 변경 거절을 확인했다. OM의 construction guard가 이 하위 클래스로 교체되고 기존 StrapForceGuard가 감싸는 계층을 유지한다. 다른 force/state/runtime property 권한을 열지 않는다.
- [construction:32](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v11.py:32): 기존 scene 구성 뒤 오른12만 EFFORT·stiffness/damping0으로 변경한다. 새 reference는 그 세 필드만 달라지고 초기 q, 나머지69, effort cap·모델 한계는 같다. 81D 계약 생성이 통과했다. 기존 LearningScene constructor의 actual PD/reference 비교는 이 변경 뒤 실행된다.
- [physics 순서:45](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v11.py:45): 매 physics tick 제어 계산→제한 window의 actuator effort1회→원 strapOFF 적분 순서다. 실제 factory 함수를 모의 parent와 연결해1200회 순서·counter·window 종료를 확인했다. root/하체와 다른69 POSITION 목표 경로를 재사용하며 기타 직접 외력은 없다.
- [Jacobian·토크:65](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v11.py:65): 고정 root의 link index−1과 tensor shape를 검사한다. 점 Jacobian은 `Jv−skew(world offset)·Jw`, 속도는 COM 기준 회전 오프셋을 포함한다. 중력 보상은 `−Jcomᵀ·mg`, task torque는 `Jpointᵀ·force`로 부호가 맞는다. force는 초기 희망점 방향으로 spring/damper를 적용하고 norm40N으로 제한하며, 최종 오른 토크는 native effort cap으로 제한한다. 순수 합성 Jacobian에서 COM 점속도 일치·10mm/s 초과 중단·40N 요청cap·나머지69 torque0을 확인했다.
- [관측 및 저장:84](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v11.py:84): 기존 endpoint callback이 먼저 행을 추가한 뒤 Head–기타 관측을 덧붙인다. 전체 point J와 qdot, 상태 불변 검사가 추가됐고 기존 torque 식은 같다. 실제 metadata 함수들을 AST로 연결한 검사에서 attempt/report 각1회·재귀 없음·최신 EFFORT 설명·오른 POSITION target은 제출되지만 무시됨·기존 계획 SHA 보존을 확인했다.

Warning 1 — [해석 선택:75](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v11.py:75): 초기 zero velocity에서는 COM/origin 후보를 구분할 수 없어 COM을 가정한다. 이후 상완 한 점의 `J@qdot` 오차 검사는 관측된 운동에서의 제한 검증이며 전체 Jacobian 열·모든 body의 중력 보상 정확성을 인증하지 않는다. 실제 실행 후 저장된 전체J/qdot·point velocity로 오차와 선택 모드를 재확인해야 한다. 요청40N과 제출 토크는 측정 접촉력·구동력 또는 실물 근력으로 표현하지 않아야 한다.

[기존 사전 입력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/effort_preflight_inputs_v1.json) 4개와 [실행용 관측 보완 입력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/effort_observation_preflight_inputs_v1.json) 2개의 SHA가 현재 파일과 일치한다. reference가 기록한 원본 SHA도 일치한다.

| 최종 실행 입력 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v11.py | 6e9b7af9aabcaffb9a7bedc39a559e4b1076996bd51803c60ce0e418f1794473 |
| OM_NO_STRAP_UPPER_ARM_PLAN_V12.md | 6b609890a3aeefe36997d5bf14ddb09c46ec22c7a19dfd81c1c80c3875ba4649 |
| right_effort_config_v1.json | b0134dda53a1db8865b7a28bfc3b26a54d9b799f3a70178f49cbfab50124b537 |
| right_effort_reference_v1.json | 747b3fa6a80b20a6e0b005be658cc6cb5cb9fdbf767fdb879cc853cfa27ca619 |

실행 차단 사항은 발견하지 않았다. native API 지원·실제 effort 적용·속도 관계·접촉·왼팔 비접촉·Head 접촉 부재·기타 자세 유지는 다음 실제 시험의 검증 대상이다. 이번 검수는 유한한 관절 토크 진단의 사전 코드/수식 범위이며, source motor 기준점이나 후기 정착을 실제 지지 성공으로 인증하지 않는다.
