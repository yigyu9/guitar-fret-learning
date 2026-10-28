# 단일 proximal collision-pair 실제 A/B CPU 분석

소유권은 이 analysis/만이다. 활성 source·producer·준비봉인·원자료를 보존하고 GPU/native 실행은 하지 않는다. root의 두 실제 launcher 종료 통보 후만 분석한다.

- [x] 실제 두 launcher exit0, report/close/wrapper 1회 및 복원, before/after source pins를 확인한다. 원90 vs89 contract·전체1485 matrix에서 단일 pair 차이와 native shape readback 경로를 확인한다. 물리 자산/PD/범위/기준판정·일정 불변도 비교한다.
- [x] 각4환경 첫 시도, 전체8 시도의 원 evaluation/음원장/9보상·물리/손목실패를 재계산한다. 성공0/4만으로 proximal 하중 효과 유무를 판단하지 않는다.
- [x] env0 저장60Hz clock/선택4 target·actual/추종오차, index1/2/3 및 middle1의 force vector/resultant, 손목 목표 추종, candidate/wrong·nearest geometry를 비교한다. 기존 v3 index reference는 별도 실행임을 유지하며 exact 재현을 가정하지 않고 관찰된 차이를 기록한다.
- [x] 저장 snapshot을 원 CPU ShortEnvironment에 넣어 원 contact/wrong 함수를 재사용하고 저장 candidate/wrong·geometry와 일치를 검사한다. 이 재계산은60Hz geometry/load gate 검산이며 실제240Hz 원장 재생/추가음지급이 아니다. 실패 endpoint/이후는 성공·무실패 force 통계에서 제외하고 모든 시도 분모는 보존한다.
- [x] 최소 표/그림/한국어 RESULTS와 verification JSON을 만들고 기존 change-reviewer에 독립 검수를 요청한다. body resultant를 pair압력으로 해석하거나 mainJ33 원인·영구필터제거 채택으로 확대하지 않는다. 최종 검수 판정은 results_v1/review.json에 보존한다.

시간 구간은 ramp 0<t<2, post-ramp 음전 2≤t<3, 원 audible 3≤t≤local_end, after t>local_end다. 보간하지 않으며 시각이 실제로 같은 endpoint만 비교한다. 첫2초·실제팔teacher feedback은 원래대로이며 서로 다른 실제 상태가 이후 팔 요청을 바꿀 수 있다.
