# Soft orientation 사전 독립 검수

요약 판정: **문제없음 / 사전 PASS**. 남은 Critical·Warning·Suggestion 없음. 물리 실행 없이 소스 차이·수학·계획을 검수했다.

- `run_strike_soft_orientation.py:150`의 actual pick 회전과 baseline FK 회전 anchor, `:178`의 Chest-conjugated 회전 예측은 현재 관절값에서 실제 회전을 재현한다. 순수 NumPy/SciPy 100개 회전 사례에서 anchor 및 world 회전 일관성 오차 최대 1.262497375036826e−15 rad를 확인했다. 저장된 `rotation_anchor_check.json`의 입력 SHA도 일치한다.
- 기존 POSITION timed-wait-rebase와 비교해 PLAY IK에 방향 5 mm/rad soft residual과 기록 필드를 추가했다. 위치 1000 m→mm 및 관절규제 3의 공동 가중합이며, 기존 native·관절 offset·rate 제한은 유지한다. PREPARE 방향 기준을 공유하되 물리적 정렬이나 접촉을 강제하지 않는다.
- phase0/open1의 policy+PI, closed1의 actual-angle IK와 I 유지, RECOVER의 이전 목표+2δ, 손가락21·왼팔·native PD schedule·source clock·검출기·성공 조건은 기존 소스와 동일하다. 새 force/state 쓰기와 actor 변경은 없다.
- wrapper의 실행 모듈 연결과 입력 SHA/복구 구조, 두 Python 파일의 Python 3.8 AST를 확인했다. 계획 `:5`의 우선순위처럼 읽힐 수 있던 표현은 공동 soft cost와 hard bounds로 정정되어 Suggestion을 해소했다.

확인 SHA256: runner `54b393fb5cf610e2c79f1e99070499974a2d75f80a31ebd516d8da6640ac6978`, wrapper `d8f22a8c61b017707a86752611c6d10130c2a770598d0cfd8e456861b71b0bbf`, 계획 `74fc1d03c675fd6895c72e16c0d19fd1e49a32c6cc4716ed1e38a24da7520fab`.

이 판정은 실행 전 구현·수학 범위다. 실제 추적 정확도·타현·회복·접촉 지지·전체 안정성 및 source/native CPU/GPU 동등성을 인증하지 않는다. 검수 중 native 초기화·물리 실행은 0회다.
