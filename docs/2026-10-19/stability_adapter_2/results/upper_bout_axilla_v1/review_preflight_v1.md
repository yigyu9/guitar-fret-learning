# 위 볼록 외곽·상완0~35% V1 사전 검수

요약 판정: **문제없음 — source 거절 유지, native 후보 없음.** Critical 0 / Warning 1 / Suggestion 0. 새 계획/source/runner/분석기를 읽기 전용으로 검토했다. 새 물리 실행은 하지 않았다.

[source V1](/home/ajou/yigyu/3/stability_adapter_2/search_upper_bout_axilla_v1.py:24)의4°/6°는 원 natural 기준의 추가 world Chest 회전이며 현재4°에 다시 더하는 값이 아니다. 기타 초기 p/q를 유지하고 body/head/right9만 탐색한다. 모델·선언 각도·고정57 scalar·Head world 방향·전체 source/capsule·G 위외곽 영역 조건을 검사한다. 기타 높이·gain·solver·형상을 바꾸지 않는다.

두 해는 source clear지만 근위0~35% 최소 gap5.669/5.029mm가4mm 조건을 초과하고 팔꿈치 하강17.057/17.896mm가20mm 조건에 미달한다. [완료 search](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/search_v1/search.json:1)는 selected=[]/native0이며 입력599개 현재 SHA 불일치0개다. 전체 R_Shoulder gap은0.154/0.160mm, 근위 closest fraction은 두 해 모두0.35다. 원자료를 native 수락값으로 사용하지 않는다.

runner는 검수된 두 점 제어 대비 phase/PLAN/search만 바꾼다. 호환키65에 실제35 witness를 담고 row에 그 의미를 명시한다. human right12 토크 합산/모델 cap/한 번 제출/other69 POSITION·effort0/owner·state·Jacobian gate를 유지한다. 새 분석기는 case/config/out resolve로 이전 상대 CLI 문제를 해소했다. Python3.8 구문은 정상이다.

## Warning

1. [analyze_upper_bout_axilla_v1.py:48](/home/ajou/yigyu/3/stability_adapter_2/analyze_upper_bout_axilla_v1.py:48): 접촉 집계는 전체 R_Shoulder–G:body 단위다. source35 목표를 썼다는 이유만으로 실제 접촉을 근위0~35%/지정 볼록부로 인증할 수 없다. native contact 위치의 local/world·캡슐 표면·구간/영역 검증 전에는 전체 상완 접촉 표본으로만 설명해야 한다.

검수 SHA256:

- 계획 V1: `c3d5f394ab41287ea0c3245527052b354cb887e74d47dcc8e22a73f44b3a7b2f`
- search V1: `cf03dd7452fe88f88fb5fbba634200b3f4b1ee27cabae43a916a84fec913c3a5`
- runner V1: `b57400262603ed2074918c51ba56c10deb099cd7da72212601a680cc3d27d87a`
- 분석기 V1: `a243c4b47e5ed6a6108c956c359099b36b62f7d8f519ae1e5be31546845bad85`
- search 결과: `0a0994527e2a8a466ee2c063732ecf6ad3ef4c0da2fd21f99b6a62f5ce39de29`

이 새 리뷰 외 기존 파일은 수정하지 않았다.
