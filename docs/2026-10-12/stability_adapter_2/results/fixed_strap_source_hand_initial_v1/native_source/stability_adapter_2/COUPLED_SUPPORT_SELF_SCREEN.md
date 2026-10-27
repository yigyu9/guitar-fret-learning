# 같은 왼손 비인접 source 쌍 검사 보완

v1/v2의 source selfpair는 native filter가 충돌을 허용한 쌍과 양손 쌍을 검사했으나,
같은 왼손은 importer mask를 공유해 비인접 손가락 쌍이 빠졌다. 계획에서 참고한
near_contact_initial_audit의 source screen은 native mask와 무관하게 같은 왼손
graph거리>2를 검사한다. Native collision 정책은 그대로 두고 source검사만 보완한다.

v2소스/출력/로그/metadata를예상SHA대조후보존한다. 새 v3는LH/Wrist/Elbow 모든
source geom쌍을조회해 graph>2는기존증가screen에포함하고≤2는연결부진단으로기록한다.
기존 native허용쌍과같은geom쌍은중복추가하지않는다. v3실행전독립검수로코드범위를확인한다.
v2의t0제출PDbase/비선택63목표유지와wholepalm접근조건은그대로유지한다.

이 보완은 실제PhysX selfcollision 설정을바꾸거나source LP공통구반지름을
native penetration으로인증하지않는다. 추가물리실행0이고기존모든실패결과는보존한다.
