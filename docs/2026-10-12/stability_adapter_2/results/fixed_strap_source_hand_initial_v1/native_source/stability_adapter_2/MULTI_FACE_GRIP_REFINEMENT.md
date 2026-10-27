# 다면 grip source 검색 보완

v1 세seed는 면거리/넥교차/손가락자기교차로 거절됐다. v2의 dense hull face-pair
soft penalty는 계산이 길어 Ctrl-C로 중단했다. 두 시도 모두 native초기화/step은0이다.
v2는 완료결과와 사전입력manifest가 없어 완료된 검증으로 해석하지 않는다.

v3는 초기 팔 탐색폭을 기준±.3rad와 native한계의 교집합으로 넓힌다.
엄지·네손가락은 서로 다른 넥길이 지점에 닿을 수 있으므로 기존50mm patch의
길이범위를 앞/뒤쪽으로 각50mm 확장하되 실제 neck1 안에 둔다.
손바닥의 파란 옆면patch/세계위쪽반구 조건은 유지한다.
전면높이는 실제source프렛/줄최외곽, 후면은명시−Z, fingertip은collisionfacet을쓴다.

soft search penalty만 local OBB를 사용해 줄이고 최종 판정은 원래 full source hull LP로 한다.
OBB penalty는 실제교차/접촉증거가 아니다. 세seed마다 최대30초 source계산을 허용하고
시간한계에 도달하면 측정된 최소cost q를 후보로 검토한다. fit 미수렴 사실을 보존한다.
각source시도는 입력manifest를 import 전에 파일로 저장하고 종료 후같은목록을재검증한다.
원본data/code/그림을 덮어쓰지 않는다. v1/v2를 보존하고 새v3 phase/trials에 저장한다.

최종 face gap3mm/사람–기타·양손·비인접LH source교차 없음/up>0 조건은 완화하지 않는다.
이 조건을 통과하면 fresh Gym초기FK와 source재검사를 하고 각physics조건의5초를 녹화한다。
후보가없으면 실제접촉한grip/5초성공을 주장하지 않고 거절원인과 배치그림을 남긴다.
