# Native 연결 기록 최종 검수

**판정: 복구 기록과 물리 연결 결과의 제한된 해석에 문제없음.** 원 run_smoke_v6 프로세스는 최종 보고 단계에서 exit 1로 종료했다. 원 실행 전체를 정상 종료 성공으로 부르면 안 된다.

검수 범위는 `native_recovery_v1/{recover.py,report.json}`, `native_analysis_v1/{analyze_v3.py,result.json}`, 원 `native_smoke_v1` 상태/목표 자료와 `comparison.json`, 준비 상태 비교 및 runner v7 수정 diff다. 물리 실행·기존 CPU 테스트를 반복하지 않았다.

## 원자료 직접 확인

- baseline: 60 tick, 240개 표본, physics step 5281–5520 연속.
- 행동0: 60 tick, 240개 표본, physics step 5281–5520 연속.
- 작은 비영행동: 앞 행동0 뒤에 이어 60 tick, 240개 표본, physics step 5521–5760 연속.
- 정책 각 tick의 실제 표본4개/진행4 step, upper42 최종 목표 오차0, 금지 호출 목록 빈 배열을 확인했다.
- 두 독립 준비의22초 native 상태가 정확히 같았다. 기타 body index0은 실제 이름 `guitar`와 대응한다.

## 결과 의미와 한계

분석의 기타 이동량은 각 시행의 준비22초 root 위치에 대한 거리이며, 회전은 준비 자세에 대한 상대 SO(3) 각도다. 비영행동 구간도 자신의 시작23초가 아닌 준비22초를 기준으로 한다. 결과의 PD 속성 동일성 키는 실제 비교한 PD properties 범위로 제한되었고 행동 범위는 실행 attempt에서 읽는다. 기록된 작은 drift를 V3 전체 안정성이나 음악 수행 성공으로 해석하지 않는다.

복구 audit은 원 실행 전 pin1502개의 불변과 보존 원자료·영상 hash를 확인한다. 원 프로세스의 실제 사후 import 목록은 남아 있지 않아 `actual_post_import_closure_certified=false`다. 새 자료를 만들어 이 불확실성을 대체하지 않았으며 원 report 부재·exit1을 보존한다. 이 구분은 적절하다.

runner v7의 변경은 `__file__=None` namespace 모듈을 건너뛰고 실제 문자열 `.py` 경로만 모으는 것으로, 확인된 최종 보고 예외 원인을 처리한다. v7의 native 전체 실행은 이번 기록으로 인증되지 않는다.

음악 보상·실제 압현/타현 성공·PPO 학습·장기 지지 안정성은 미검증 상태다. 이 검수는 제한된 정책 목표 인계 및 물리 데이터 연결이 실제 실행되었다는 결론까지만 지지한다.
