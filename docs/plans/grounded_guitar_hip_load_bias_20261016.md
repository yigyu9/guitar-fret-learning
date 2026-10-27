# 관측된 오른쪽 고관절 부하의 유한 보상

V14 실제 정지 시험(native_static_v14)은 상완 접촉을 회복했으나 기타 회전5.7696°와 Spine 기울기5.0955°로 실패했다. 채택하지 않는다. 다음 비교의 기준은 기타 회전1.493°였던 runtime14/native_static_v12이며 가슴 접촉은 아직 실패 상태다.

실제 기준 시험 마지막240개 lower_stable_pd 기록에서 submitted−human gravity의 R_Hip3 평균은 [-0.218509675222, 0.937492792878, -1.597839927853] Nm, norm1.865404Nm이다. 이는 전체 접촉력을 관측하지 못한 net-contact tensor와 무관한 native generalized torque다. 마지막 실제 Hip 자세를 유한 목표로 옮기는 source 계산은 기타 접촉면 방향으로 약1mm 접근을 예측했으나 실제 동적 접촉 유지와 발 접지는 미검증이다.

가설은 이 관측 부하를 상쇄하면 목표와 실제 Hip의 차이가 줄어 가슴 지지도 개선된다는 것이다. 초기105각·기타·Root·cube·upper target·world right anchors는 기준과 같다. 기타를 직접 이동하거나 힘을 주지 않는다.

1. 새 producer/spec과 runtime17/analyzer17/run17을 만든다. 세 Hip 축에만 smoothstep 0.15..0.75초로 bias를 올린다. 기존 stable-PD의 gravity 인자에 bias를 더해 raw 단계에서 보상하고 원300Nm cap을 그대로 적용한다. implicit RHS, K300/D75, 원 human gravity 진단, zero8, 나머지 하체, 발 IK는 유지한다. component/norm2Nm 이하와 입력 SHA·1200개 실제 기록 재구성을 검증하고 독립 검수를 받는다.
2. native_static_v15에서 실제 정지5초를 판정한다. 기타 이동30mm/회전5°/넥3°/좌우20mm, Torso·Chest·Spine5°와 right3°,1..5초 Chest+상완95%/양발95%,last1 네 발 기준을 완화하지 않는다. 부하 보상은 정적 부하가 작은 자세 변화에도 비슷하다는 가정이며 실제 반력과 기타 회전을 바꿀 수 있다.
3. 전체 통과 시 동일 입력 재현을 먼저 하고 압현·타현, 이어 왼손 해제15초를 검증한다. 실패하면 목표·실제 Hip와 접촉·기타 움직임을 기록하고 원자료에서 다음 원인을 찾는다. PPO는 시작하지 않는다.

- [ ] 새 소스·spec 인증과 독립 검수
- [ ] 실제 정지5초 모든 기준 판정
- [ ] 통과 재현 → 압현·타현 → 왼손 해제

소비한 이 계획과 모든 실험 파일은 수정하지 않는다. 결과는 grounded_guitar_support_v1의 새 진행 기록에 남긴다.
