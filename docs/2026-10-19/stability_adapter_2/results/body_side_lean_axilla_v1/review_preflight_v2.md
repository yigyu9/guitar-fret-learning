# 바디 쪽4° 팔·기타 초기 보정 V2 사전 검수

요약 판정: **문제없음 — source 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 0 / Suggestion 0. 계획·source 두 seed 결과·runner/분석기 diff를 읽기 전용으로 검토했다. 새 물리 실행·학습은 하지 않았다.

[source V2](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v2.py:20)는 거절된 right4° 행의 초기81 q에서 body/head 기준을 유지하고, 승인된 natural 기준 right9만 새 범위로 탐색한다. 몸통·머리·손목·왼팔·손가락을 포함한 다른72개는 right4 기준과 exact로 검사한다. 두 seed 모두 같은 right4 몸통/머리를 사용하며 반대 방향의 이전 조합은 right9/Gdelta 시작값에만 사용한다. 이동한 기타 상태로 전체 source audit를 다시 수행하고 수락 행에만 새 candidate/config를 생성한다.

두 결과 모두 polygon source audit clear지만 **analytic Hip 최소 gap이 약−0.010997mm**다. [최종 gate](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v2.py:33)의 전체 capsule/Hip 최소0.05mm 조건에 미달해 [완료 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v2/search.json:1)는 selected=[]/native0이다. 근위 gap 약2.4915mm·전완0.3124mm·normal world Z0.999998·other72·팔 방향·손 위치39.102mm가 통과하더라도 Hip gate를 생략해 수락할 수 없다. 음수 gap은 source analytic 지표이며 cooked 관통 깊이 인증이 아니다.

기타 delta는 두 결과 모두 약[−30.000, −9.404, +21.830]mm로 선언한 box 안이다. source 0.1mm 목표와 shape contact offset 약0.1mm는 서로 다른 양이며 첫 physics 접촉·지지력·무관통을 보장하지 않는다. solver/contact offset/모델 질량 변경 코드는 추가하지 않았다. 입력590개 현재 SHA 불일치0개와 Python3.8 구문을 확인했다.

[runner](/home/ajou/yigyu/3/stability_adapter_2/run_body_side_lean_axilla_v1.py:116)는 기존 전완 controller 대비 phase/계획/search 경로만 바꾼다. human right12 EFFORT/other69 새 POSITION 목표·고정 초기-world 전완점·토크 cap/owner/상태 불변/Jacobian gate·기타 free/strapOFF 조건을 유지한다. 기타 직접 외력·부착·runtime pose 덮어쓰기를 추가하지 않는다.

[분석기](/home/ajou/yigyu/3/stability_adapter_2/analyze_body_side_lean_axilla_v1.py:19)는 강화된 config/candidate attempt pin·초기81 q/실제 q·G p·손목 고정 마스크·69 제출 및 model clip 검사를 유지한다. source 파일의 legacy docstring `player-left`는 실행 방향 계산에 사용되지 않으며 실제 기준은 right4 q와 player-right 행/계획이다. 소비된 원문을 고치지 않았다. 이 분석기는 현재 거절된 두 해의 native 결과를 인증한 기록이 아니다.

현재 단계에서 native를 진행할 후보는 없다. 후속 수정은 새 경로에서 같은 전체 source/모델/방향 gate를 통과한 후보를 다시 생성해야 한다. source 근접만으로 actual 겨드랑이 접촉이나 유지 성공을 채택할 수 없다.

검수 SHA256:

- 계획 V2: `c72e33b1cb998fba722a11051a2e7776220b553c5cde453d549dab03a389fc39`
- search V2: `45b869603a87d5ecad63afba3334372c8821a5f3591966ea9679f1d09842ba3c`
- runner V1: `c3ff71b687c56005efa1169e93e665c3b4e333a495bd5ffa89b68d08af62a5d2`
- 분석기 V1: `566b2261a73010cdc7607ee042cd3bc78ea1fe54f5300e4dfb6086a45f21acd7`
- 완료 search.json: `139bc328ec80fa79d0740219a36cfaaa8a599e34ae8f2ebeb1e9b41506fbb27c`

이 새 리뷰 외 기존 소스·결과·리뷰는 수정하지 않았다.
