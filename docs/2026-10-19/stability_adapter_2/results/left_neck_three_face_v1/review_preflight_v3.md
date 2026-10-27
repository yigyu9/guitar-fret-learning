# V5 여유·방향 가중치·hull 극점 변경 사전 검수

요약 판정: 문제없음. 요청한 surgical source 변경이며 공유 면 gate/native V2/초기48각·G·모델 조건을 바꾸지 않는다.

Critical: 0

## 확인 근거

- [V5 seed:19](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v5.py:19)는 V4 rejected station20의33각만 warmstart로 사용하고 새 search_v5/PLAN_V5로 기록한다. station20 한 후보만 탐색한다. V4의 LP/면 실패를 현재 판정으로 승계하지 않는다.
- [극점 선택:80](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v5.py:80): hand local mesh와 actual neck/fret G mesh의 ConvexHull vertex만 변환한다. 임의 선형 방향의 min/max는 전체 vertex와 convex hull 극점에서 동일하므로 support/AABB·단위 face-normal separation 정의를 유지한다. 이동 plane의 nG=R*n,dG=d−nG·origin 식도 그대로다. 자산이나 final whole LP의 원 mesh를 축소하는 변경은 아니다.
- [가중치:100](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v5.py:100)는 pinky normal만6→24,neck preference1.5→2.5mm/self .8→1.5mm와 두 penalty weight14000을 적용한다. fit max_nfev140 외 기존 초기 L33/model/thumb80·55/4arm160/frozen48·G 및 공유6면 조건은 그대로다.
- [최종 gate:122](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v5.py:122)는 fresh whole-source LP·frozen48·placement_pass·4arm norm160을 유지한다. source/plan diff와 V5 AST를 확인했다. source optimizer/LP/native를 재실행하지 않았고 원파일은 수정하지 않았다.

## Warning

- [penalty:107](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v5.py:107)의2.5mm/1.5mm는 최적화 선호이며 hard 수락 여유가 아니다. 최종 수락만으로 모든 neck/self pair가 그 최소거리를 확보했다고 인증하지 않는다. face-plane separation은 보수적 증거이며 완전 SAT/최단거리를 대신하지 않는다.
- hull 재구성/정렬의 부동소수점 차이는 가능하지만 기하학적 support는 동일하다. source final LP는 전체 원 mesh로 독립 확인하고 actual native 초기 cooking/접촉·6면 관계는 별도로 판정한다.
- 현재 V5 source/LP 최종 결과가 미확정이다. 이 문서는 결과 수락·종료 SHA/native 가능성을 인증하지 않는다. 완료 결과의 shared gate/whole LP/모델/입력 보존을 확인한 후보만 다음 단계로 진행한다.

## Suggestion

없음. 현재 새 diff에서 blocking 구현 오류를 발견하지 못했다.
