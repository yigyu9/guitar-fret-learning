# 휴머노이드

현재 학습은 [smpl_mpl_hands_body.xml](/home/ajou/yigyu/3/tab2body/assets/smpl_mpl_hands_body.xml)의105개 scalar 관절을 사용하고Root를고정한다. 하체24개 중 원 비영 가동범위16축은 유한한 자세 유지 제어를 받고 원 영범위8축은 보존한다. 전체 비영 범위는97축이다.

| 역할 | 채널 수 | 적용 |
|---|---:|---|
| 왼팔·왼손 |33|연주 정책 출력|
| 오른팔꿈치·손목 |6|타현 정책 출력|
| 몸통·오른근위부·머리·오른손 파지 |42|유한 유지 목표|
| 하체 |24|원범위와 유한 지지 제어|

관절 이름 suffix를 세계 좌표축으로 해석하지 않는다. 목표각·실제각·보고 속도는 서로 다른 측정이다. 유한 유지 목표는 관절을 잠그거나 매step 상태를 덮어쓰는 방식이 아니다.

[관절표](JOINT_SPECIFICATIONS.md) · [학습 기준 초기 상태](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/initial_values.json) · [현행 학습의 제어·관측](/home/ajou/yigyu/3/guitar_learning/README.md)
