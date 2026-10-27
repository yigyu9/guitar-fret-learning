# 사전 독립 검수 — Strike terminal retract v1

판정: **문제없음(PASS)**. Critical / Warning / Suggestion: 남은 항목 없음. 새 runner·wrapper·계획을 기존 frozen incremental-approach와 대조했다. Native 초기화·물리 실행·공유 코드 변경은 하지 않았다.

- 기존 `advance`의 AST가 동일하며 PREPARE/PLAY 목표·actor·source timing·detector·손가락 4개 residual·PD 일정은 유지된다. Wrapper는 호출 모듈 이름만 바뀌며 task import 전에 원래 입력 SHA·소스 사본을 보존한다.
- HOLD에서 첫 실제 pick의 기타 좌표 XY와 `max(actual_z, READY_z)+30 mm` anchor를 고정한다. 이후 현재 기타 pose로 world 목표를 만들며 위치 차분 −0.1초 보정은 최대 5 mm다. 순수 산술로 anchor와 보정 제한을 확인했다.
- 실제 q 주변 R9 local IK ±0.15 rad, 이전 제출 목표+2δ, native bounds와 최종 rate 제한을 사용한다. 나머지 72개는 첫 HOLD 제출 목표를 유지한다. HOLD에서 actor/source step을 실행하지 않고 제출 함수의 history 갱신을 생략하며 clock/progress/history 불변을 별도로 검사한다. 기타 pose·힘을 쓰지 않는다.
- HOLD의 POSITION baseline PD 복원 시 setter 반환값, 전체 native properties 및 실제 상태를 비교한다. 불일치 시 physics 전에 중단하고, 성공한 경우에만 record 저장과 restored flag 설정을 수행한다. `PD_switch_gate`/terminal metadata도 PLAY 일정과 HOLD 복원을 구분한다.
- 복원 record 저장 누락 및 readback/state 불일치 후 실행 지속 Warning 2건이 수정됐다. 수정 전 미실행 runner/wrapper/계획은 `source_before_PD_review_fix/manifest.json`의 3개 SHA와 정확히 일치한다. Python 3.8 AST 문법 검사도 통과했다.

검수 SHA256: runner `b0e551e292b042dd79a87fa0985d1782d01d04dac63e07ae85e8f8babd0404f6`, wrapper `8595f01480a0542d3eb71b747fefe4fd6cdf39704ce631a75c7982916657a886`, 계획 `be341cdaba0643db79cb7ba30542f20afb0d96f0aa3c4e882966011e2bf679c1`.

이 판정은 실행 전 구조·수학·보존 경계에 한정된다. 음악 prefix 실제 재현, HOLD 회수·접촉·기타 안정성 및 영상 결과는 아직 검증하지 않았다.
