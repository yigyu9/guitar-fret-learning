# 팔12·손가락6 연동 source 검증 실행 단위

직전 −4mm actual 비교는 회전 개선/후기 변화 증가를 확인한 progress다.
추가 LA 단축 대신 −2mm 저장 actual 상태에서 PALM_FINGER_COUPLED_SOURCE_PLAN의
첫 두 단계를 수행한다. 원본/이전 source·코드·계획·체크포인트는 보존한다.

1. 새 coupled_support_source.py에 현재 Chest로 이동한 팔12 FK delta와
   measured palm-relative finger 계층을 합성한다. LH:thumb2/3,index2/3,middle2/3
   단일축의 상대 회전만 추가하고 실패한 finger1 q→pose 모델은 쓰지 않는다.
   qdelta0의 모든 body/mesh identity, 각 축 차분과 실제 저장24시점의 arm/조건부hinge
   예측을 확인한다. 실제 simulator를 만들거나 상태를 쓰지 않는다.
2. 새 search_coupled_support_source.py에서 t0/0.1/0.5/5초의 measured source geometry로
   palm 요청옆면·thumb후면·index/middle전면을 함께 본 bounded least-squares 제안을 만든다.
   팔±0.05rad/finger±0.10rad와 native/손한계 및 원본PDbase+delta의±0.3rad 초기offset
   경계를 교차한다. 현재 손목 파형에 대응하는 저장 최종target을base로 보존한다.
   Finger1 등 비선택 관절 및 torso/하체/root/G/LA는 변경하지 않는다.
3. Fraction1/0.5/0.25를 원범위 안에서 조회한다. Whole source hull LP 공통구반지름의
   새/증가교차(기존10µm source 증가 screen), 유한patch witness 상/하한, palmar+Z와
   soft normal preference를 함께 기록한다. 연결graph거리≤2 제외는 기존기준을 유지하되
   제외쌍 진단도 보존한다. Source screen은 cooked 접촉/관통 인증이 아니다.
4. 유효한 방향/예측 모델이 있어야 다음 물리 실행 계약을 작성한다. 이번 단위의 기본은
   저장자료 검사이며 native초기화/physics/학습0이다. 다음 실제 trial은 동일초기값과
   0~5초의 스트랩 포함 두 영상을 저장한다. 추가 candidate 불가시 실패원인을 기록한다.

- [ ] 24저장시점 arm/조건부hinge 검증과0변화 identity/18축 차분
- [ ] 4시점 bounded 제안과 fraction screen, 전체쌍/patch/상향/PD 경계
- [ ] 수치·그림·독립검수·보존 감사, 다음 작은 실행 단위 결정

18축은 지지 보정의 임시 탐색 범위이며 최종 주요66 제어권을 제한하지 않는다.
기타의 초기 world p/q 복원·유지가 최종 목적이고, 현재 G frame의 손 오차 감소는 그 수단이다.
하나의 연주+공동residual 최종PD목표 구조를 유지하고 필수 WAIT나 손 부착,
기타 고정/목표 견인힘/지속pose 덮어쓰기를 도입하지 않는다.
