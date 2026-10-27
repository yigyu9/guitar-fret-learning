# 후면 엄지 면 탐색 실행 계약

기존 THREE_FACE_REAR_FACET_PLAN.md를 따라 source 검색과 통과 후보 최대2개5초를 진행한다. 소비된 이전 검색과 산출물은 수정하지 않는다.

- 이전 검색 producer의 실행 SHA를 대조하고 새 phase에 exact 복사한 뒤 새 search_rear_thumb_facet.py를 만든다.
- 같은 half81 초기각의 thumb3 활성 source triangle 중 초기G+Z dot>.75를 골라 면적이 가장 큰 triangle 중심을 anchor로 쓴다. 관측 native 지점은 진단 자료로만 유지한다.
- 첫 팔12±.05/엄지5±.10rad의 두 clearance(.3/.7mm)를 검사한다. 둘 다 실패할 때만 엄지±.20rad로 같은 두 후보를 추가한다. Native/Aug19/C02/기존절대목표offset±.3의 교집합과 나머지64 초기각/목표81/G/LA/gain은 유지한다.
- 기존 손바닥 anchor, 다른 손가락 초기각과 부드러운 front 높이 선호를 유지한다. 대표점의 후면/옆면 내부여유2/3mm, 전체 source 교차, palm상향proxy와 float32 실제각을 직접 검사한다.
- 유한패치–hull 거리는 mm 중심화 QP의 witness상한과 분리평면 support하한을 함께 기록한다. [.3,1]mm 간격은 하한/상한으로 확인하며 미확정이면 거절한다. 단순 solver success를 최적성 인증으로 쓰지 않는다.
- thumb의 후면 지지는 hull-witness→patch 방향+GZ dot>.75와 witness가 rear plane 바깥인 조건으로 구별한다. Source facet 법선 정렬은 계속 부드러운 선호이며 해부학적 pad/PhysX cooked 접촉 인증이 아니다.
- Source통과 때만 새fresh native FK/입력검사 후 최대2개 실제5초/1200step과 초기값·전신/손151frame을 저장한다. 통과0이면 새physics0을 명시하고 실패잔차로 다음방향을 정한다.

최종양쪽66 제어권/root하체물리고정/몸통9 PD목표/자유기타·수동strap/selfcollisionON을 유지한다. 기타고정/손부착/pose덮어쓰기/G목표힘은 없다.
