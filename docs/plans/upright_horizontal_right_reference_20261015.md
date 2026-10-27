# 오른팔의 기준 배치 추종 비교

static3는 4.8도 상체목표+Hip ramp로 neck최대6.65048도/Chest0/몸통5도초과였다. source4 및 static2 초기목표/원 controller14/즉시 Hip preload로 돌아간다. 초기 기타 좌우/수평은 바꾸지 않는다.

기존 오른팔10Hz IK의 목표는 매번 실제 기타 pose를 따라 움직인다. 이 구조에는 초기 수평배치로 회복시키는 위치/방향 기준이 없다. 이것이 흔들림의 원인이라는 확정은 하지 않는다. 새 비교는 그 IK 목표를 초기 기타 pose에서 계산한 world palm 및 upper arm 지점으로 유지한다. 실제 human q를 이용한 FK/원래 finite joint target/rate/cap/지원task를 유지한다. 기타에는 목표를 제출하지 않고 직접힘/부착/매step상태갱신을 사용하지 않는다. 이 조건은 사람의 오른팔로 초기 지지 자세를 유지하려는 제어이며 고정된 기타를 뜻하지 않는다.

controller_horizontal_v2는 controller_v14 복사에서 initial guitar p/r 저장 및 right IK reference만 변경한다. 하체/가상 지지 task/body목표/양손열린상태/원범위/zero8는 static2와 같다. 실행전 변경범위와 초기 IK오차를 확인하고 정지5초 native 전표본 neck3도/lateral20mm/body5도/right3도/1초후 ChestRShoulder동시95% 및 기존안전gate 판정. 실패를 숨기지 않고 전후모두 보존한다. 통과 전 release15/PPO 없음.

- [ ] source4/initialtarget 복원 및 right world reference 코드 확인
- [ ] native 정지5초 및 전표본 분석
- [ ] 실제 비교 영상·독립 검수·보존 감사
