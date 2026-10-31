# 독립 검수

**요약 판정: 문제없음 — scoped PASS. 실제 해제 개선 및 원prepared 기반 전체 재실행은 미검증이다.**

Critical: 없음.

Warning — `analyze.py:67`: 원 준비계약의 외장 `prepared.json`, `initial_values.json`, `inputs_before.json` 3개가 현재 Errno5 EIO다. 123개 pin 중 읽힌120개는 SHA 일치·불일치0이다. 저장 `inputs_unchanged=true`는 실행 당시 결과이며 현재 전체 source integrity 통과를 뜻하지 않는다. 외장 입력 복구 후 기록 SHA와 native PD 범위를 확인하고 원결과를 보존하는 별도 출력에서 원prepared 경로를 재현해야 한다.

확인한 범위:

- 코드·PLAN·RESULTS·results·그림을 검수했다. 후보는 고정 PIP40°/DIP10° 한 개이며 검색·최적화가 없다. 자체검사 실행 통과. 결과에 pin된 PLAN SHA도 현재 일치하며 체크리스트 원문을 수정하지 않았다.
- 두조건 env0 full354 중 phase3 각26행을 확인했고, codec clock=trace time×240, 해제58행과 distal/guitar pose exact join을 확인했다. source-valid128점과 signed plane height를 사용하며 음수높이를 여유로 합치지 않는다.
- **독립 확인은 원prepared 보정/full_fk와 다른 경로다.** 각조건 첫 저장행의 actual parent-relative PIP/DIP offset·zero를 한 번만 구한 뒤 매 queried 행의 실측 index1을 anchor로 두 hinge를 직접 전파했다. 원prepared 로더/원full_fk를 실행하지 않았다. 독립 baseline 최대 표본오차0.000179/0.000127mm·회전6.54e−7/6.41e−7rad로 둘 다 감사 허용값 이내였다. 저장문서의 원prepared baseline 최대0.000150mm를 같은 경로로 재실행했다는 뜻은 아니다.
- 독립 후보 최소 signedheight는 reference7.558176719/noisy7.565354545mm다. 저장 per-row 후보와 최대차0.00000341/0.00000399mm로 수치가 일치하고 128점×26행 모두5mm 위다. 원표본 최소−0.270116/−0.275510mm도 저장값과 일치한다. 후보는 XML 범위 PIP[0,90.0002]°/DIP[−5,90.0002]° 안이다. 저장 reference N target에서4rad/s의 최소 목표시간은51.9115ms다.
- 그림은 단위·시간·5mm선·조건부 후보 표시가 맞으며 native replay로 오해하지 않도록 명시한다. 목표를 실행했을 때 실제index1/기타/부하/충돌/추종이 유지된다고 보증하지 않는다. 실제 해제 개선 전 paired finite replay가 필요하다는 제한이 적절하다.

Suggestion: 없음. 새native/GPU/PPO/fit/모델생성0이며 활성소스·원자료·gate·archive는 수정하지 않았다. 수치 근거와 검수 대상 SHA는 `review.json`에 있다.
