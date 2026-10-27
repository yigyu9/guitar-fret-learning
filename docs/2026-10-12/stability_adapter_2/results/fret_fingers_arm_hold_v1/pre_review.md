# 왼팔 지지 목표 유지 + 손가락 Fret 사전 검수

요약 판정: **문제없음 (사전 코드 검수 PASS)**.

Critical: 없음. Warning: 없음. Suggestion: 없음.

## 확인 근거

- [run_fret_fingers_arm_hold.py:93](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:93): 최초120 control의 준비 목표·제한·물리 적분 경로는 소비된 `run_fret_native_connection_v3.py`와 동일하다. 초기화 단계에 제어축 분류와 기록 필드만 추가됐다.
- [run_fret_fingers_arm_hold.py:103](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:103): 인계 시 실제 관절 상태를 덮어쓰지 않고 마지막 제출 LShoulder/Elbow/Wrist9 **목표**를 복사한다. PLAY의 실제 최종 제출 목표가 이 값과 동일한지 매 control 검증한다(124행).
- [fret_finger_target_ownership.py:7](/home/ajou/yigyu/3/stability_adapter_2/fret_finger_target_ownership.py:7): 초기81 목표에서 source30 요청을 넣은 뒤 L9를 준비 목표, support15를 bounded hold로 덮어써 Fret21/준비L9/hold15/초기36 소유권을 분리한다. 손가락21 요청 보존 검증과 runner의81축 분할 검증이 있다.
- [run_fret_fingers_arm_hold.py:120](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:120): 손가락21은 기존3.2rad/s 제한, 나머지는0.8rad/s 제한 및 native 한계를 통과한다. source의 pd_target과 prev_action은 실제 최종 제출 목표로 갱신되므로 적용하지 않은 actor L9 요청이 다음 EMA/history 상태로 남지 않는다. actor30 출력과 source30 요청도 별도로 기록한다(132행).
- [run_fret_fingers_arm_hold.py:133](/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py:133): 물리 적분은 기존 단일 native owner에서 한 번 실행하고 source 평가·done에 즉시 종료한다. 원본 실패/성공 조건과 영상 종료 처리는 변경되지 않았다.
- [fret_fingers_arm_hold_preserved_run.py:54](/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_arm_hold_preserved_run.py:54): wrapper 변경은 실행 모듈 이름뿐이다. 기존 입력 SHA·새 A 파일 snapshot·실행 후 불변 검증은 유지된다.

## 검증과 한계

세 새 Python 파일 AST 문법 검사 PASS. 물리 실행 전 검수이므로 실제 PREP camera/state 동일성, 관절 목표 유지 및 기타/운지 결과는 아직 검증하지 않았다. 후속 native 실행 기록으로 확인해야 한다. 기타 안정화나 운지 성공을 사전 코드 PASS로 판단하지 않는다.

## 검수 시 소스 SHA256

- `/home/ajou/yigyu/3/stability_adapter_2/FRET_FINGERS_ARM_HOLD_PLAN.md`: `a2b77ecaf7bb473816d316cb872df610175bbd282fc4488cb4de318c149482d8`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_finger_target_ownership.py`: `5b6d0f8408f3c92ad7104e5b309120dc89f12e54195bf2ce56c182fdfbf71dff`
- `/home/ajou/yigyu/3/stability_adapter_2/run_fret_fingers_arm_hold.py`: `1345e98dfef9246c1e93b49ae6f4cabfc7f54921ee92b373d9c16890c6f5232a`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_fingers_arm_hold_preserved_run.py`: `7baa7f562b6e44e760dc4af0e729bd96b20958280aecd944d73e52c32013364a`
- `/home/ajou/yigyu/3/stability_adapter_2/run_fret_native_connection_v3.py`: `2bc281e7079d36e244e0eaf91a4d32f37c03b77055b1fc8bba5119b98d2e93d6`
- `/home/ajou/yigyu/3/stability_adapter_2/fret_native_v3_preserved_run.py`: `7f140bac720c82cb179e5cbe7bdfe656a0cf0f005547669970df469f41dbe16c`
