# 오른팔 construction PD 사전 검수

판정: **문제없음**. Critical 0 / Warning 1 / Suggestion 0. 검수 범위는 V8 계획·v7 실행 코드·새 config/reference·사전 입력 SHA 및 관련 constructor/저장 체인의 읽기 전용 검토이다. 추가 native 실행·학습은 수행하지 않았다.

- [실행 코드:13](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v7.py:13): 기존 scene 구성을 먼저 실행하고 초기 구성 단계에서 오른 Thorax/Shoulder/Elbow/Wrist 12개 stiffness×4·damping×2를 적용한다. 변경 전후 전체 구조화 속성 readback을 비교하며 effort와 나머지 69개 속성은 유지한다. 모의 PD 검사에서 추가 setter 1회와 float32 기대값 일치를 확인했다.
- [LearningScene:34](/home/ajou/yigyu/3/stability_adapter_2/learning_scene_v2.py:34): 위 구성 이후 constructor가 새 reference와 실제 PD를 비교한다. [guard:10](/home/ajou/yigyu/3/stability_adapter_2/environment_guard_v2.py:10)는 초기화 완료 후 PD 변경을 거절한다. 새 reference는 원본 대비 오른팔 stiffness/damping만 변경됐고, config는 reference 경로·SHA만 변경됐다. 순수 CPU 81D 계약 생성도 통과했다.
- [저장 체인:28](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v7.py:28): v7 final_save→v6 final_save→보존된 원 저장 함수로 이어진다. 실제 함수 AST를 연결한 모의 호출에서 저장 1회·재귀 없음·기존 preload/PI 표기와 새 PD 표기·V8 입력 SHA 보존을 확인했다. strapOFF factory와 단일 목표 제출 경로를 재사용한다.

Warning 1 — [실행 코드:26](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v7.py:26)의 `construction_override_calls=1`은 이 진단 코드의 추가 setter 횟수이다. 기존 초기 PD 설정까지 포함한 총 호출 수나 native 적용 증거로 해석하지 말고, 실제 시험의 before/applied readback과 runtime 금지 호출 기록을 함께 확인해야 한다. 접촉·왼팔 비접촉·기타 유지 성공 및 실물 근력은 이번 사전 검수로 인증하지 않는다.

확인한 사전 SHA-256은 다음과 같으며 [입력 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/right_hold_preflight_inputs_v1.json)과 일치한다. 원본 reference의 기록 SHA도 현재 원본과 일치한다.

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v7.py | a0f779db3972b24012a4a039e1ac1af7e827e47892e433b19bfce2e4c2b94b90 |
| OM_NO_STRAP_UPPER_ARM_PLAN_V8.md | 6af4d090d980e53f90796b99dea280ca9e4cd9ac3afec5b73c6f606eeb199a7b |
| right_hold_config_v1.json | be6097c64061fb134748a2a618f0a8adbdaa913d73446f93d64dd082bff8b72b |
| right_hold_reference_v1.json | 7869a41181310d13e6dfde54412ee3451ba3b9b6d4b223f1b35e1363e2afa56f |

오른팔 강도만 높이는 제한 진단이다. 기존 몸통 목표와 실제 몸통 자세 사이의 오차, 움직이는 기타에 대한 피드백 부재는 그대로 남는다. 지정한 이 새 리뷰 파일 외에는 수정하지 않았다.
