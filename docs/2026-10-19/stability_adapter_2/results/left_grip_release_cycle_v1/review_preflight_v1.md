# 독립 사전 검수 V1

요약 판정: **수정 권장**. Critical 0건이며 유한 사람 관절 제어 및 16초 진단 실행 구조에는 차단할 오류를 찾지 못했다. 실제 잡기·놓기 성공과 물리 안정성은 실행 후 원자료 분석이 필요하다.

## Critical

없음.

## Warning

- `/home/ajou/yigyu/3/stability_adapter_2/left_grip_release_cycle_v1.py:125`: 새 최종 벡터를 `left_cycle_efforts.json`에 저장하지만 상속 encode에서 `left_wrist_tracking_rows.json`은 여전히 pre-cycle 벡터를 final이라고 표시한다(`left_near_arm_effort_v3.py:68`). body 파일만 scope를 바꾸므로 분석자가 이전 벡터를 실제 제출값으로 오인할 수 있다. 새 wrapper에서 해당 상속 로그의 scope와 final 참조를 `left_cycle_efforts.json`으로 명확히 교체할 것을 권장한다.
- `/home/ajou/yigyu/3/stability_adapter_2/run_left_grip_release_cycle_v1.py:166`: `completed`는 예외·입력 변경·금지 호출 유무만 나타내며 잡기·놓기 성공 판정이 아니다. `left_grip_release_cycle_v1.py:90`의 raw 접촉 로그에서 엄지+다른 손가락 동시 양의 lambda, 접촉 없는 연속 놓기 구간을 별도로 집계한 뒤 사용자에게 동작 성공 여부를 보고해야 한다. 계획서 33–35행에 이 후속 검증이 명시돼 있으므로 실행을 막는 오류로 보지는 않는다.

## 확인한 사항

- 변경은 새 두 소스·leaf 계획·config로 한정해서 읽었다. git diff/staged diff는 해당 파일들이 untracked 디렉터리에 있어 비어 있으며, 광범위한 기존 변경은 검수 대상에서 제외했다.
- 새 IK는 왼팔12 scalar 모델 한계와 기준 ±0.8rad, ball norm160° 및 위치/회전 오차 gate를 적용한다. 손가락 목표는 모델 한계 내 clip하고 상속 contract가 arm3rad/s·finger1.5rad/s로 최종 목표를 제한한다. other48 target exact와 other69 effort exact를 검사한다.
- 새 손목 가상 힘25N·모멘트2Nm은 왼팔12 Jacobian-transpose 토크에만 들어가며 모델 effort cap으로 clip한다. 상속 guard가 사람81 벡터의 finite/cap/33관절 owner를 확인하고 guitar wrench/state-write 경로는 추가되지 않았다.
- 현재 +10mm native initial state 전체 exact equality, source overlap audit, root/하체 fixed, 실제 자산·PD·질량 대조 및 입력 SHA 검사가 있다. 독립 fresh_learning_v1은 넓은 pin 대상에서 제외돼 다른 승인 작업과 충돌하지 않는다.
- 960회 60Hz control로 3840회240Hz 물리(16초), physics_step0부터 마지막까지30fps capture하며 예외 시 부분 영상/실패 보고를 남긴다.
- 두 새 Python AST parse와 config strict JSON parse 통과. 사전 검수에서 실제 GPU/물리 실행은 하지 않았다.

## 검수 파일 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/left_grip_release_cycle_v1.py`: `3eeabc32d2af26ece030c7ca704e0344cee472cdb00d540a9f5cd8094a2cdcfe`
- `/home/ajou/yigyu/3/stability_adapter_2/run_left_grip_release_cycle_v1.py`: `126ea9a1e1dd6621781456fefadb863df8019ad07c555cf01b6e890768e77b80`
- `/home/ajou/yigyu/3/stability_adapter_2/LEFT_GRIP_RELEASE_CYCLE_PLAN_V1.md`: `8f07c54c6763633d75243f11791d1182d343d376339481023be318f169b8813c`
- `/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_grip_release_cycle_v1/config_v1.json`: `585ce83b94359b2275e40479bb14af9f3b584a4c61a5197427707089c5d2d88c`
