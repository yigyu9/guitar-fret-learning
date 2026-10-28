# 기존 distal 표본의 해제·이동 여유 측정

2026-10-28. 원 reference는 음악/해제128/128이지만 N은035 준비자세이며 충분한 이격 여유가 검증된 목표가 아니다. 같은 후보 목표각 잡음에서 reference도 세음 전체2/128로 감소했다(실제분석 독립PASS). 저장된 env0에는 해제 latch 뒤 A candidate 재출현이 있었다. 다음은 원인 분리를 위한 **읽기 전용 새 측정**이며 목표각·분포·보상 변경이 아니다.

## 1. 최소 도구와 CPU 검증

- 원 GoalPool/reference/noisy-reference/평가를 재사용한다. `super().step()` 후 원 after 콜백 앞에서 native 끝점 상태를 읽고, 원 before에 복사한 first mask를 쓴다. 원 after·부분reset·장면종료·원오류 보존과 RNG 소비는 유지한다. 환경의 `_snapshot/_contacts`를 다시 실행해 상태를 갱신하지 않는다.
- 원 `fingertip_pad`의 검지 slot0/index3 굽힘 안쪽128표본·법선·valid mask와 원 body→world→guitar 변환을 사용한다. body1/2·손가락3마디 전체·전체 피부가 아니다. 손등이나 전방향 support vertex를 섞지 않는다.
- A 원 string/fret·유한 셀·plane을 그대로 사용한다. 표본축을 batch로 펼쳐 P=1로 원 `pad_target_geometry`를 재사용하며, 원 P=128 aggregate와 nearest/any-sample witness를 교차검산한다. sourcevalid를 현재 facing mask로 덮지 않는다. nearest 표본의 법선과 contact witness를 구분한다.
- 3D 유한 셀 거리, 별도 signed plane height, normal cosine, lateral/셀 내부 여부·원 geometric/load/candidate 관계를 표본별로 기록한다. 음수 높이의 관통·잘못된 방향·무하중을 단순히 '분리 여유'로 합치지 않는다. 새 성공/clearance 임계값은 만들지 않는다.
- 검증은 원 finite-cell inset·회전 plane·same-sample/nearest≠witness·입력불변 테스트를 재사용한다. P=1 펼침과 P=128 aggregate의 동등성, 올바른 검지/시간창/first endpoint 선택, 원상태/다른콜백/RNG 불변을 최소 fixture로 확인한다. 모델 생성/load/학습은0이다.

## 2. 사전 지정 수집 두 조건

실제 자료에 없는 표본별 값이 필요하므로 원무잡음 reference와 같은 후보std noisy-reference를 새 장면에서 각각 한 번 수집한다. 기존 helper/128환경 evaluator와 계약을 유지해 새 제어·작은장면 경로를 만들지 않고, 상세 저장은 **env0..3 첫시도·A 원press부터 B7 sharedpress를 처음 넘는60Hz 끝점까지만(clock692..920 inclusive, 환경당최대58행)**으로 제한한다. 128성공률을 다시 확인하는 것이 실행 목적이 아니며 기존 성과는 원출처를 유지한다. 추가128표본·새seed·std/관절각 탐색은 하지 않는다.

각 조건은 새 출력·정확한 명령·독립검수/최종봉인 후 root가 직렬로 실행한다. 원 K1/60Hz·4substep/240Hz·기타 고정·유한 손목·다른손가락B·엄지035·비엄지0.25Nm·원105/90쌍·DIP보호·9보상·성공/해제·종료는 그대로다. 잡음 조건은 기존 분포/shape/seed 규칙을 그대로 쓰며 무잡음은 원 raw reference를 그대로 반환한다.

## 3. 실제 검산과 판단

원 body/plane/점·법선/유한 셀 좌표의 유한성, 매시점 P=128 aggregate와 펼친 표본의 일치, 실제 first/실패 endpoint·시계 및 동일 source 표본ID를 검증한다. 기존 원9항·128원장·장면종료를 보존하고 새신호를 별도 NPZ/요약으로 저장한다. 도구가 원 요청/평균/분포/물리에 개입하지 않았는지 원 callback·RNG/변환 감사를 유지한다.

해제 latch, 같은 A의 candidate 재등장, 실제 distal 무하중, 유효 이산 표본들의 거리·방향을 분리한 타임라인/작은 그림을 만든다. 이 훅은60Hz이며 미저장240Hz 최초사건·연속 무접촉·전체피부/접촉쌍·현 압력은 인증하지 않는다. 데이터로 부족한 이격 여유와 탐색 단위 문제를 먼저 구분한 뒤 **한 가지 수정대상만** 결정한다. 새 목표각·std·K·상관·보상 변경이나 PPO/fit는 이 작업에 포함하지 않는다.

- [ ] 최소 CPU 구현·독립검수·최종봉인
- [ ] root 두 조건의 제한된 표본별 native 수집
- [ ] 실제자료 검산·독립검수·수정대상 판단
