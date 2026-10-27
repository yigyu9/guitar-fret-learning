# Thorax 40N/16mm 사전 검수

요약 판정: **문제없음 — 제한된 5초 진단의 실행 차단 없음.** Critical 0건, Warning 2건, Suggestion 0건.

직전 버전과 코드·설정을 대조했다. 변경은 [가상점 설정 허용 tuple](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:30), body helper/runner의 새 버전 import, [Thorax 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/config_v1/static_Thorax40.json:31)이다. Thorax만 30N/12mm→40N/16mm이며 Shoulder 10N/4mm는 유지된다. 초기 조건·몸통 150/1·33 EFFORT/48 POSITION·현재 기타 목표점/속도·최종 모델 한계·단일 81 제출·상태 가드의 로직 변경은 없다. 새 Python 3파일 AST 검사를 통과했다.

## Warning

- [계획 V9:3](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_NATIVE_PLAN_V9.md:3), [가상점 제어식](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:52): 이전 종료 analytic 간격 0.549085mm는 실제 cooked 접촉이나 지지력의 인증이 아니다. 16mm는 인간 모터점 목표 오프셋, 40N은 가상점 요청 상한이다. 두 설정을 함께 바꾸므로 결과의 원인을 각각 분리할 수 없다. 실제 접촉력·관통깊이로 확대하지 않는 계획의 제한을 유지한다.
- [계획 V9:5](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_NATIVE_PLAN_V9.md:5): 법선 차이 28.88°인 같은 측면의 근접 구조는 수동 force closure를 증명하지 않는다. 이번 근위 0~30% 측정과 병행 제안된 0~65% 기하 검토를 구분하고, 몸통 실제각·두 부위 실제 접촉·오른 distal 비접촉을 확인한 뒤 동일 조건의 제한된 팔꿈치 동작을 판단해야 한다. 왼 thumb 및 허벅지의 힘/모멘트 기여와 반복 강건성·연주 성능은 별도 미검증이다.

## 검수 시 SHA-256

| 파일 | SHA-256 |
|---|---|
| RIGHT_BLOCK_CRADLE_NATIVE_PLAN_V9.md | ea73fc32a221b7188dd19d22f186cf26f2b2d901034899a142cf6a8e6b0ecf44 |
| right_block_effort_v6.py | 57f36af4f5df535440488097319cf53dbf85c74fd71d82fcb6fb6194e3ec1620 |
| right_block_body_effort_v5.py | 6e3c9928b11e0bd46d59a7276ecc9158439d24fe22ed1fc3758f2e2649fb7201 |
| run_right_block_cradle_v9.py | c9111d623b47e8e0f8119ff9cd5349a65ff5360de08bcc0040b13ee223654f10 |
| static_Thorax40.json | dd7352d3325de2e458a88cd5f4ca0f94d4b5709292747b6c9a4a05497f6b8f1a |

읽기 전용 사전 검수이며 새 native 결과 인증이나 과거 원자료 전체 감사는 하지 않았다. 새 물리 실행·소스/기존 결과/기존 리뷰 수정은 없다.
