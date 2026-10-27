# 후면을 향하는 엄지 source 면을 선택한 초기 자세 비교

## 현재 측정 근거

contact_footprint_v1은 실제 관측 feature에 가장 가까운 thumb3/palm 활성 source triangle을
선택했다. 목표점 오차는0.06mm 이내였지만 thumb/palm 형상이 넥과 교차해 두 후보를 거절했다.
V2는 whole-hull 분리 proxy를 탐색에 넣어 교차를 없앴으나 엄지 대표점이 요청 후면 패치
밖0.201/0.395mm에 남았다. 후면 내부 여유2mm 조건을 통과하지 못해 물리 실행은0이다.
선택한 엄지 triangle outward의 G방향은 약[.997,−.016,.077]/[.998,−.006,.064]로,
후면 접촉에 필요한 body→neck +GZ보다 넥 옆면의 +GX에 가깝다.
관측 접촉점의 동일성을 유지하려다 원하는 후면 지지 배치를 제한했으므로 anchor 선택을 바꾼다.

## 다음 실행 단위

- [ ] 동일 half 초기 상태의 thumb3 활성 source hull에서 초기 G+Z와 dot>.75인
  triangle을 찾고 면적이 큰 후보를 선택한다. 선택 좌표/면적/법선/기존 관측면과의 차이를
  저장한다. 해부학적 pad 또는 PhysX cooked 접촉면으로 인증하지 않는다.
- [ ] 엄지 대표점은 이 면의 중심으로 바꾸고 기존 native feature는 관측 지점으로만 남긴다.
  기존 palm anchor와 부드러운 면 방향 선호를 유지한다. Source thumb3 hull의 후면 방향
  support와 유한 rear patch witness를 함께 검사해 단순 옆면 접촉을 rear 지지로 세지 않는다.
- [ ] 먼저 팔12±.05rad·엄지5±.10rad의 같은 범위로 두 clearance 후보를 준비한다.
  실패하면 source 목표·교차·bounds 잔차를 읽고 엄지 범위를±.20rad까지 한 번 보완한다.
  Native/Aug19 제한과 기존 절대목표의 상대offset±.3rad 교집합 안에서 검사한다.
  나머지 손가락/몸통9/오른팔손/물리 고정 root하체/기타 초기p·q/원LA와gain은 유지한다.
- [ ] 후면/옆면 대표점 투영 내부와 여유2/3mm·source 간격.3~1mm·전체source 교차를
  검사한다. 간격 경계 후보는 QP primal witness뿐 아니라 support-plane dual 하한으로
  최적성 오차를 확인한다. 기존 최근점 계산을 실제 cooked 관통 gate로 바꾸지 않는다.
- [ ] Fresh native 초기 FK/target/입력 대조를 통과한 최대2후보만 실제5초를 실행하고,
  초기값·전신/손151frame 영상·원자료·p/q 오차·body 접촉/후면 feature 위치를 기록한다.
  실제 지원 면은 원자료/영상으로 따로 확인한다. 이 계획 작성 시 신규 물리 실행은0이다.

실행에 소비된 V1/V2와 검수는 보존한다. 기타 고정/강제 손 부착/지속 pose 덮어쓰기나
기타 목표힘을 사용하지 않는다. 최종 양쪽66 제어권을 유지한다. 초기복원·지속 세 면 지지·
연주 중 안정화와 제어권/학습 구조 결정은 미완료다.
