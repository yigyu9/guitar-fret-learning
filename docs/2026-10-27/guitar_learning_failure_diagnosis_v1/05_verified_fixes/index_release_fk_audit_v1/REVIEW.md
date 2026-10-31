# 독립 검수

**요약 판정: 문제없음 — scoped PASS. 원prepared 기반 전체 재실행은 미검증이다.**

Critical: 없음.

Warning — `analyze.py:232`: 원 준비계약의 외장 `prepared.json`, `initial_values.json`, `inputs_before.json`이 현재 모두 Errno5 EIO다. 125개 pin 중 읽힌122개는 SHA 일치·불일치0이며, 저장된 실행 당시 before/after125개는 같다. 현재 전체 source integrity 통과로 읽으면 안 된다. 외장 입력 복구 후 SHA 대조와 별도 출력의 재실행이 필요하다. 원결과·gate·archive는 보존한다.

확인한 범위:

- 코드·PLAN·RESULTS·results·series·그림을 검수했다. 두 코드 자체검사 실행 통과. 원CAS SHA와 현 `full_fk` AST 동일성을 독립 확인했다. FK PLAN은 원125개 pin에 포함되지 않았고 검수 중 수정하지 않았다.
- 두조건 env0 full354/해제58행의 시계·local/source time 및 distal/guitar pose를 원NPZ에서 직접 exact join했다. series의 모든 world 위치/회전 통계가 저장 results와 일치한다. 그림의 단위·시간창·legend와 자료 범위가 맞는다.
- native palm→index1 회전 log의 xz−actual q 최대는 reference2.1487221e−7/noisy2.0173705e−7rad다. log y 최대2.714860565/2.784835007°와 전체 추이가 series와 직접 일치한다. XML 두 노출축은 x,z다. 이 현상의 물리 원인은 확정하지 않았다.
- native PIP/DIP parent-relative 회전을 XML x축 exp(actual q)와 직접 비교한 최대오차는6.70e−7rad 미만, XML offset과 native offset 차이는0.000200mm 미만이다. 이는 저장된 downstream hinge 관계의 독립 검산이며 원prepared 보정 `full_fk` 전체 재실행은 아니다.
- 저장 원FK의 palm-relative 회전은 허용1e−4rad를 크게 초과하고 `fk_accuracy_gate=false`다. 프로그램 완료와 FK 정확성 실패를 구분한 결론이 적절하다. 저장 원FK world/표본 오차 수치의 원prepared 기반 재계산은 외장EIO로 확인하지 못했다.

Suggestion: 없음. 새native/GPU/PPO 실행0이며 활성소스·원자료·gate·archive는 수정하지 않았다. 수치 근거와 검수 대상 SHA는 `review.json`에 있다.
