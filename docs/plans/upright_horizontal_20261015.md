# 사용자 교정: 기타 좌우 위치 복원·수평 넥 유지

직전 upright_chest_support_v1은 그대로 보존한다. 사용자 지적은 기타 몸통이 humanoid 왼쪽으로 너무 이동했고 넥이 수평에서 벗어났다는 것이다. 이번 단계는 이 두 조건을 자세/접촉보다 먼저 고정한다.

## 기준과 허용치

- 기타 몸통 기준점: 원 G:body convex 전체의 source AABB 중심(local G=[0,-.4,-.05593798]m). 기타 root/손/넥 끝을 몸통 중심으로 혼동하지 않는다.
- humanoid 오른쪽: 초기 horizontal(RHip−LHip) 정규화, 기준점은 고정 Pelvis. 이전 하체 안정화 초기의 몸통 중심 우측 오프셋 +150.035mm로 되돌린다. 직전 raised 후보 −53.689mm여서 약203.724mm 왼쪽으로 이동했다.
- source: 그 우측 좌표를 고정하고 neck local+Y의 world-Z 성분0(수평)으로 parameterize한다. 기타 앞뒤 이동±100mm/높이0~+80mm/넥축 주위 앞뒤기울기−.6~+.2rad/수평yaw±5°만 탐색한다. 좌우 이동·넥 상향으로 접촉문제를 우회하지 않는다.
- native 전체 5초: neck angle 절대3°이내/몸통 좌우 좌표는 기준±20mm, Torso/Chest total5°/옆3°,1초후Chest·RShoulder 동시 positive contact95%이상과 기존 모든 safety gate. 초기 형상 통과와 실제 유지 성공은 별개다.

## 순서

1. [ ] source9의 직립 body/Head/lower24를 보존하고 guitar 배치와 양팔을 맞춘다. 팔/손 재배치를 허용하되 이전 guitar-local palm 오차와 실제 native 추종을 기록한다.
2. [ ] 원범위/zero8/105·97/feet/capsule·BOX·chair·ground/손도달 검사.
3. [ ] 통과 후보만 원 finite controller14/scene8, upper target는 새 초기 qref(직전 기하에서 얻은 bias6를 전용하지 않음)로 정지5초.
4. [ ] 실제 기타 위치/수평/각도/접촉 전체 표본 판정과 native 비교 영상. 통과 전 왼손15초/PPO 금지.

Root/의자고정,하체16 유효축 finite stablePD,명목0축8 원범위유지,105입력,기타자유강체/중력ON/strapOFF/직접힘·부착·상태덮어쓰기금지 유지. 기존 code/input/output/leaf계획은 수정하지 않으며 새 phase에 실패도 보존한다.
