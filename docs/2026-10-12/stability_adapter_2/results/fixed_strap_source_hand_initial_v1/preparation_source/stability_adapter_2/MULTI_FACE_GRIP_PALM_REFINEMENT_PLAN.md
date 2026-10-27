# 감싸기 seed2의 손바닥 지지 보완 — 다음 소단계

현재 결과는 `docs/2026-10-12/stability_adapter_2/results/multi_face_grip_v3/analysis.json`이다.
seed2는 기준 대비 기타 최대 이동·회전을 줄였지만 세면 동시 초기 지지가 아니며,
손바닥의 양의 raw lambda는 step121까지만 기록됐다. 정적 marker 하나를 맞추는 것보다
전체 collision hull과 유한 넥 면 사이의 거리를 함께 확인해야 한다.

1. seed2 초기값을 기준으로 왼팔12를 각 ±0.03rad, 왼손21을 각 ±0.10rad 안에서
   작은 source 후보를 찾는다. 기존 baseline 팔 ±0.3rad와 native 손가락 한계도 함께 적용한다.
   목표는 palm측면·thumb후면·나머지 distal전면의 전체 hull gap을 함께 줄이는 것이다.
   기존 finite면 범위/정의는 유지하고 평행성은 부드러운 선호로 남긴다.
2. source 사람–기타·양손·비인접 왼손 교차 금지, palm-up proxy>0을 유지한다.
   기존 seed2보다 세면 거리 최대값이 작아진 최대2후보만 fresh Gym t0 FK/실제 q 범위를 확인한다.
   source 형상 안전성은 cooked clearance 인증으로 설명하지 않는다.
3. 통과 후보를 실제Gym에서 각5초 실행하고 초기값·두뷰영상·연속원자료를 저장한다.
   기존 seed2의 저장 결과와 비교하며 새 실행 수를 별도로 기록한다.
   초기 세면3mm 접근 달성과 실제 접촉 유지·기타 p/q 오차 개선을 각각 판정한다.

root/하체고정, 기타 초기 p/q, 오른팔·오른손, 몸통9 목표, 기존 LA/PD/startupoffset
법칙을 유지한다. 강제 부착·기타고정·지속 pose 쓰기는 사용하지 않는다.
seed2를 최종 안정 자세로 채택하거나 학습을 시작하지 않는다.

- [ ] source 국소 후보와 hard 검사 기록
- [ ] 최대2후보 fresh native 초기 검사 및5초 기록
- [ ] 결과 분석·산출물·독립 검수와 보존

이 계획은 아직 실행하지 않았다. 사용자 요청의 반복 탐색에서 다음에 사용할 기준을 남긴다.
