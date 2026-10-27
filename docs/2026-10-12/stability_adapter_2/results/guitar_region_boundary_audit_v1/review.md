# 독립 검수 — 기타 playable-region 경계 감사

판정: **문제없음(PASS)**. Critical / Warning / Suggestion: 남은 항목 없음. 분석 코드·summary·README와 저장된 네 조건의 실제 control/native pose를 읽기 전용으로 대조했다. 환경 import·native 초기화·physics 실행·원자료 및 조건 변경은 하지 않았다.

- Control의 `before_physics_step`과 trace의 `physics_step`을 결합하고 실제 `time_s`도 동일함을 확인했다. 중복 trace의 위치·회전 일치를 확인해 한 표본으로 집계한다. Rebase/free4/velocity/READY의 정확시각 표본 151/150/150/151, false 8/32/40/8이 일치한다. 결합되지 않은 control 149/150/150/149는 진단 범위 밖이다.
- 602개 결합 표본에서 원래 함수의 반환값을 재계산했다. 위치 box 실패 0, 저장 flag 불일치 0이다. False 88개는 특이점 분기가 아닌 일반 회전의 principal·alternate 두 Euler branch 모두 실패하며, 허용 pitch 안에서 roll/yaw 조건을 벗어난다. 두 branch 재구성 및 modulo 사용을 생략한 분석이 아니다.
- 초기 native 회전행렬의 +90° 특이점과 roll−yaw=−90° 통과를 확인했다. 공통 첫 false 시각 0.033333초의 작은 초기 대비 SO(3) 회전과 Euler 경계 이탈을 구분한 설명이 맞다. World x ±0.01°에서 false, y/z ±0.01°에서 true인 순수 회전 계산도 재확인했다. 이는 새 native 실험이나 threshold 변경이 아니다.
- 입력 27개 시작/종료 SHA와 현재 파일이 일치하고 Python 3.8 AST 문법을 확인했다. 코드의 numeric/source decode·parse는 SHA 및 byte-cache 대조 뒤에 수행된다. 실행 전 underneck 함수 위치 `rg` 탐색까지 사전 봉인으로 주장하지 않는 README 경계는 적절하다. 분석 코드 자체의 SHA는 별도 현재/기록 대조이며, 이전 전체 실행 이력을 새로 인증하지 않는다.

검수 SHA256: `analysis.py` `2fcb3e7f364581319076d467b1b9474abb142036890c9d6c35a3f1dddecb58c9`, `summary.json` `2c4a89f5222ba7942e5b33f03e8f8b9f93d713eb308aeceac8392b04361fd3a4`, `README.md` `3309b4491cc9169c71c2d014891cbe518090be3bb44490ba44463edec615800f`.

한계: 저장된 exact-match 표본과 원래 predicate의 분해만 검증했다. 표본 사이 상태·연속 최대 회전·접촉/제어 원인·연주 성공·box의 물리적 적합성은 판정하지 않았다. Root의 이후 최종 보존 감사·봉인 완료를 이 기록에서 주장하지 않는다.
