# 현재 기타 상대 목표 사전 검수

판정: **문제없음**. Critical 0 / Warning 1 / Suggestion 0. V9 계획·v8 코드·사전 입력 기록을 읽기 전용으로 검토했다. 기존 v6 preload/PI와 v7 construction PD를 대조했으며, 추가 native 실행·학습·원본 수정은 하지 않았다.

- [상대 IK:55](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v8.py:55): 매 control 실제 기타 p/q와 human q/body pose로 목표점과 FK를 다시 구성한다. 오른팔 12개만 q_ref±.4rad∩모델 한계에서 최적화하고, optimizer 성공과 motor 점 오차 5mm 미만을 모두 만족할 때 목표를 채택한다. 실패 시 마지막 채택 목표를 유지한다.
- [PI·제한:65](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v8.py:65): 오른팔 적분·잔차 ±.4rad, 최종 요청 q_ref±.8rad∩모델 한계를 유지한다. 나머지 69개 목표는 q_ref이며 기존 단일 codec/rate 제출 경로를 사용한다. 기존 monitor 반환값은 버리고 상태 기록을 위해 한 번만 호출한다.
- [구성·저장:74](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v8.py:74): 검수된 construction PD 변경과 strapOFF factory, 읽기 전용 endpoint 기록을 재사용한다. AST로 기존 metadata→v8 final_save→원 저장 함수를 연결한 모의 검사에서 저장 1회·재귀 없음·최신 상대 제어 설명·V8/V9 입력 SHA 보존을 확인했다.

순수 CPU에서 직전 저장 native 초기 상태로 실제 제어 함수를 실행했다. 초기 상대 IK 채택, 실패 IK 목표 유지, 나머지69 요청 불변, 요청 한계, control당 monitor 1회, 상태 불변을 확인했다. 합성 기타 이동/회전으로 15cm 및 25° 초과 시 latch와 원위치 복귀 후 재무장되지 않음을 각각 확인했다. 이 검사는 실제 물리 전이나 native IK 예측 정확도 검증이 아니다.

Warning 1 — [중단 및 PI:55](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v8.py:55): latch는 **IK 목표 갱신만** 중단한다. PI 적분·잔차와 rate 제한은 계속 동작하므로 실제 제출 target까지 고정된다는 뜻으로 보고하지 않아야 한다. 현재 계획의 마지막 목표 유지 의미와 일치한다. motor 기준점 추종·관절 한계 만족은 실제 접촉, 무겹침, 지지력 또는 초기 기타 유지 성공을 인증하지 않는다.

[사전 입력 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/relative_preflight_inputs_v1.json)의 4개 SHA와 현재 파일이 일치한다.

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v8.py | 9dad59d6c1618ba34cb45df7fd559f83f24baaf16074190f81c7da0284e12efe |
| OM_NO_STRAP_UPPER_ARM_PLAN_V9.md | 8bc1e98b6ac375a2902058979afdfce357ca4b685e044a44d01a136ecde99b1b |
| right_hold_config_v1.json | be6097c64061fb134748a2a618f0a8adbdaa913d73446f93d64dd082bff8b72b |
| right_hold_reference_v1.json | 7869a41181310d13e6dfde54412ee3451ba3b9b6d4b223f1b35e1363e2afa56f |

실행 차단 사항은 발견하지 않았다. 실제 기타 변화·왼팔 비접촉·상완 접촉·제출 목표·runtime 금지 호출은 계획된 다음 native 시험에서 별도로 확인해야 한다. 지정한 새 리뷰 파일만 작성했다.
