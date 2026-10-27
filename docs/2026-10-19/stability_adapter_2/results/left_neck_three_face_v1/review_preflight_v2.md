# V4 형상 separation·공유 면 gate·native V2 사전 검수

요약 판정: 문제없음. 새 source/native의 공유 gate와 초기 왼33 허용·비왼48 보존·읽기 관측 변경이 계획과 일치한다. source V4 최종 수락/LP 결과는 검수 시점 미완료이며 별도 확인 후 실행한다.

Critical: 0

## 확인 근거

- [공유 geometry:12](/home/ajou/yigyu/3/stability_adapter_2/left_neck_three_face_geometry_v1.py:12)는 앞4finger y offset±.03/±.01m 및 해당 width를 재계산하고,palm10mm/엄지·finger8mm 목표를 만든다. outward/반대방향 facet alignment/worldpalmup 부호는 앞선 frame 정의를 유지한다. [공유 gate:23](/home/ajou/yigyu/3/stability_adapter_2/left_neck_three_face_geometry_v1.py:23)는 전체 point 오차<12mm/plane gap2..16mm/alignment>.3 및 palm worldup를 요구한다. source와 native가 같은 두 함수를 사용한다.
- [source 변환:104](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v4.py:104)의 local convex plane 변환은 nG=R*nLocal,dG=dLocal−nG·origin으로 올바르다. unit face-normal projection 또는 AABB 양수 gap은 보수적인 분리 증거이며 [penalty:107](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v4.py:107)는 hand↔실제 neck/fret 1.5mm 및 비인접 hand↔hand .8mm를 선호한다. capsule/raw mj_geomDistance를 최적화에 쓰지 않는다. 전체 팔/인체/기타 source LP는 [최종:122](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v4.py:122)에서 fresh 예측 상태로 별도 수행한다.
- [초기 범위:59](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v4.py:59)는 왼33 모델 교집합과 thumb2≤80/thumb3 0..55를 유지하며 수락에 frozen48/shared gate/4arm ballnorm<160°를 요구한다. V3 rejected station20 row는 warmstart33각만 공급하고 현재 판정을 승계하지 않는다. source pin은 anchor→XML discovery→전체mesh/candidate/reference→contract/FK 순서다. 기존 소비 V1~V3은 변경하지 않는다.
- [native 초기 검사:49](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_three_face_v2.py:49)는 왼33/비왼48 count를 확인하고 비왼48 raw DOF state·기타39 raw state를 현재 left-thumb baseline과 exact 비교한다. 이전 finger37 대신 right21을 legacy reference와 비교하며 전체 q_ref/model·root/lower·PD/mass·native 초기 FK/source LP를 유지한다.
- [native 공유 초기 gate:115](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_three_face_v2.py:115)는 실제 초기 pose/currentG에서6면을 측정해 원 물리 루프 전 통과를 요구한다. 이후 afterphysics callback은 원 observer 이후6body rawpose/currentG face metrics/pass만 endpoint에 추가하고 native state 보존을 검사한다. 카메라3view 및 기존 V7 rightEW6·LEFT wrist taskOFF·finite33EFFORT/48POSITION·rate/cap/단일human81 제출은 그대로다. 새 force/state setter가 없다.
- source V4/shared geometry/native V2 AST를 확인했다. 이번 검수는 읽기·수식 검토이며 optimizer/shape LP/native를 재실행하지 않았다.

## Warning

- [separating_gap:29](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v4.py:29)는 AABB와 두 hull face-normal 축만 사용한다. 모든 edge-cross 축을 포함한 완전3D SAT/최단거리가 아니므로 분리된 일부 edge-edge 배치에도 보수적 penalty를 줄 수 있다. 최적화 실패는 전역 불가능 증명이 아니며 최종 LP·모델·면 gate를 대신하지 않는다.
- 공유2..16mm는 앞선2..12mm보다 넓힌 초기 준비 간격이다. source/native가 이 새 조건으로 함께 판정한다는 것을 기록하며, 작은 gap/point-target 오차는 실제 finite face의 최소거리·완전 containment/접촉·압현/anatomical pad 인증이 아니다. actual0/2/5초 및 전체240Hz face 관계·영상·접촉으로 재검증한다.
- source V4 `search.json`이 아직 닫히지 않아 후보 수락·전체 LP·종료SHA를 인증하지 않는다. 수락 후보가 없으면 native0을 유지한다. 이후 새 파일이 생겨도 이 기록 자체가 source 수락 증거가 되지 않는다.
- native observer는 후기 면 이탈을 기록하며 물리 자세를 강제 복구하지 않는다. 실제 기타 추종/접촉/G drift/원 detector 성공은 후속 원자료 범위다. 기존 후보의 left_thumb_natural 등 nested metadata는 과거 이력이며 이번 초기 수락은 새 left_neck_near/shared actual face gate로 판정한다.

## Suggestion

없음. 완료 source 수락/LP·입력 보존을 확인한 후보만 native 진단으로 진행한다.
