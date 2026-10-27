# 손바닥·검지 지지 소실의 실제 자세 진단

## 현재 근거

같은 half 초기81q에서 finger21 목표를 새초기값으로 유지하면 첫.1초 오차는4.718710mm/.936405°에서3.933977mm/.872048°로 줄었지만, 최대이동25.229274→26.111870mm와 종료21.912505mm/7.091529°→26.047250mm/7.714785°는 커졌다. 검지 양λ 고유step은23→33, 마지막step81→106이며 손바닥은30→50이나 마지막step123으로 같았다. 손가락 목표 변경을 채택하지 않고 half/saved_finger_targets를 진단 기준으로 보존한다. 이 기준도 안정화 성공은 아니다.

## 다음 작은 단위

1. 새 두 실행의 actual body poses와 기타 poses를 저장 원자료에서 읽어 step0/24/60/120/240/1200, 즉0/.1/.25/.5/1/5초를 비교한다. joint좌표로 종료bodypose를 다시 만드는 대신 저장된 실제 bodypose를 CPU source 형상에 배치한다. 물리 시뮬레이션을 재생하거나 state/pose를 native에 덮어쓰지 않는다.
2. 기존 기타 local rear/front/side 패치를 매 시점 실제 기타 pose로 변환하여 여섯 손 부위 source hull 거리와 지정 collision-facet inward alignment, 손바닥 상향proxy를 측정한다. 선택facet의 해부학적 손가락 pad 정체성, source형상과 PhysX cooked 차이는 미확인으로 유지한다. native body접촉시점과 대조하되 source거리로 면별접촉을 인증하지 않는다.
3. 동일 시점의 actual-minus-submitted 목표 오차를 손가락21/왼팔12/몸통9로 분리한다. 관절 scalar좌표 오차를 SO(3) 몸체 회전오차라고 부르지 않는다. 현재 종료 left Shoulder_x 목표오차는 두조건 .378943/.379285rad이며 이 차이나 크기만으로 접촉 소실 원인을 단정하지 않는다. 관측 위치/회전과 목표추종 관계를 먼저 확인한다.
4. 이어 같은 saved_finger_targets 설정을 새로1회5초 기록하며 초기 rigid-shape 물성(frictions/contact/rest offsets/filter)과 body/shape mapping을 SDK에서 읽기만 한다. 읽기전후 native state/PD/Python target 동일을 검사한다. 기존 raw contact의 friction 필드만으로 실제 material을 단정하지 않는다. 값 읽기에 맞춘 새 최소runner를 만들고 기존runner/공용assets는 보존한다. 초기각/Gp·q/LA/PD/solver/target를 변경하지 않는다. 전신/손0~5초151frame 영상 및 초기값을 저장한다.
5. 지지거리/법선과 실제 target오차, shape물성을 함께 본 뒤 다음 손/팔 초기값·보정 방향을 Sol이 결정한다. 진단 전에 gain·friction·strap·몸통 목표·학습구조를 바꾸지 않는다. 원자료·기하진단·실제 영상은 구분해 문서화한다.

기타자유/중력/수동strap·root하체물리고정·selfcollisionON·초기몸통9목표와 최종66제어권을 유지한다. 고정기타/강제손부착/목표기타힘/상태덮어쓰기는 없다. 예측 원인이나 성공을 먼저 확정하지 않는다. 이 계획은 아직 구현/실행하지 않았다.
