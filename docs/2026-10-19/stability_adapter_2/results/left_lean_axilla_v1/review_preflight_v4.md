# 왼쪽 기울임 두 human motor 점 V4 사전 검수

요약 판정: **문제없음 — 제한된 비교 실행에 코드 차단 없음.** Critical 0 / Warning 1 / Suggestion 0. runner V3→V4 및 분석기 V2→V3 변경을 읽기 전용으로 대조했다. 새 물리 실행·학습은 하지 않았다.

[상완 기준점 구성](/home/ajou/yigyu/3/stability_adapter_2/run_left_lean_axilla_v4.py:106)은 같은 source3 후보의 근위65% witness를 R_Shoulder local motor 점으로 변환하고, 초기 기타 surface에서 normal 반대6mm 위치를 고정 world 목표로 사용한다. K2000/D30/요청 cap30N이며 측정 접촉점·접촉력·실제6mm 관통을 뜻하지 않는다. 초기 source3 candidate SHA와 기존 source 입력은 보존됐다.

[combined_control](/home/ajou/yigyu/3/stability_adapter_2/run_left_lean_axilla_v4.py:109)은 기존 전완 `control()`의 **미clip 요청**에 상완 `JᵀF`의 right12 성분만 더하고 native 모델 cap으로 최종 clip한다. 기존 control은 힘 API를 호출하지 않는다. 실제 API 호출은 유지된 `step_physics`의 한 번뿐이며, 중력보상/자세 항을 중복 합산하지 않는다. other69 effort0·새 POSITION q_ref·owner window/상태 불변/readback/Jacobian gate와 기타 free/strapOFF 조건을 유지한다. 기타 직접 외력·부착·pose 덮어쓰기를 추가하지 않는다.

상완 점은 native COM/origin 보정 후보 중 실제 점속도와 맞는 프레임을 선택하고 오차0.01m/s 초과를 거부한다. 기존 전완 control이 먼저 같은 physics 상태의 Jacobian을 refresh하고 finite 검사한다. 추가 계산 중 물리 적분은 없으며 새 점 계산도 상태 불변을 검사한다. 두 요청 벡터는 **각각**30N 상한으로, 합계 요청 벡터의30N 상한은 아니다. 최종 관절 effort의 모델 상한은 합산 뒤 적용한다.

[분석기 V3](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_lean_axilla_v3.py:34)는 상완1200행 cadence·endpoint 기반 점 위치/속도·고정 world 목표·힘 공식/상한·Jacobian 속도·right task를 확인하고, 전완+상완+gravity+posture 합산 및 최종 clip을 재계산한다. 초기81 q/candidate/config pin과 손목 초기 보존 검사는 유지한다. 각 점 힘 요청과 raw 접촉 lambda는 실제 측정 N이 아니며, 전체 gravity/Jacobian 또는 지지 기여의 독립 인증은 아니다. 실제 새 두 점 제어의 결과 검증은 후속 범위다. Python3.8 구문은 정상이다.

## Warning

1. [LEFT_LEAN_AXILLA_PLAN_V4.md:15](/home/ajou/yigyu/3/stability_adapter_2/LEFT_LEAN_AXILLA_PLAN_V4.md:15): 비교 기준도 기존 전완 점·gravity·posture의 human actuator 토크를 사용한다. 따라서 조건 전체를 **순수 수동 지지 대 능동 누름** 비교로 설명하면 부정확하다. 기존 능동 전완 제어에 상완 점 하나를 추가한 비교로 한정해야 한다. 접촉 발생이나 후기 정착만으로 유지 성공을 주장할 수 없다.

검수 SHA256:

- 계획 V4: `01f2fb03922e1709056901871bd3c72a3fd4514ac139279e32452a66b6e63a19`
- runner V4: `2c75a69792e884655682c938a9c678cb0399352263a15feaa67933763a342b52`
- 분석기 V3: `62b6923eb6fcf547837aa13ead8026122e2572afd2936861896ffc7408678705`
- source3 초기 candidate: `9fbe35820e4f21877806885687eb442c1153a117e85836d93dada66c0e821364`

이 새 리뷰 외 원본 코드·실험·이전 리뷰는 수정하지 않았다.
