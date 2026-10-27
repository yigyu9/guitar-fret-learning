# V14: 현재 접촉 간격의 normal 복원과 world tangent 유지

V13은 상완 world preload4→2mm에서 상완 접촉이0.104167초 이후 사라졌고 기타 회전이8.495°에 도달했다. 실패한2mm world 설정은 채택하지 않는다. 현재 목표 전달·관절 한계 오류로 설명할 근거는 없다.

## 확인한 제어 결손

V13 종료의 오른상완 source gap은5.680mm인데, 고정 material point의 world 목표 오차를 현재 접촉 normal에 투영하면−0.225mm/인체 접근 요청0.446N뿐이다. 0.2초에는 gap1.032mm인데 요청이 오히려 바깥쪽0.533N이었다. 고정 world material 목표의 normal 성분이 실제 기타와의 간격을 표현하지 못했다. 반면 world palm/material IK와 tangent 유지가 기타의 전체 움직임을 제한한 이전 효과는 보존할 필요가 있다.

새 후보는 정상 방향만 현재 source 접촉면을 따르는 unilateral gap PD, 접선은 기존 초기 world material anchor 복원을 사용한다. 전체 IK를 현재 기타에 따라 움직이는 과거 방식으로 복구하지 않는다. 이는 실제 결손을 겨냥한 미검증 제어기이며 성공한 설정으로 설명하지 않는다.

## 제어 정의

- 초기 source4·target2·affine human goal·world palm/material IK·유한 하체와 발·Root/cube·Gfree/gravityON/strapOFF는 그대로다.
- 현재 RShoulder capsule/실제 native pose와 G convex source에서 nearest normal/skin witness를 구한다. normal 목표 깊이2mm, K2000/D30은 기존 task gain과 같다. 접근 힘만 허용한다.
- normal은 현재 skin witness의 Jacobian과 실제 rigidbody 속도를 사용한다. 움직이는 feature 좌표의 차분을 속도로 쓰지 않는다. tangent는 고정 material point의 Jacobian과 world anchor·실제 속도를 사용한다.
- 두 힘의 합 벡터 norm을 원20N cap으로 제한하고 같은 비율로 각 힘을 줄인다. 각각의 human 작용점에서 Jᵀ로 기존15개 상체 채널에만 매핑한다. 기존 world Rtask 성분을 정확히 제거한 뒤 새 두 성분을 더하고 원 관절 cap으로 재제한한다. 하체 명령·zero8·POS48은 바꾸지 않는다.
- 고정4mm world task reference는 진단용 legacy 값으로 표시하고 실제 사용한 normal goal과 world tangent anchor를 따로 기록한다. 기타에 직접 force/state/attachment를 적용하지 않는다.

V13의 native net-contact tensor는 raw normal 합과 scale≈1/오차≈10⁻⁷로 일치하지만 전체 Newton RMS24.31N이다. substeps1/±1step 정렬로도 해결되지 않아 마찰 누락 가능성이 크다. 이 값을 전체 접촉 하중이나 Hip 보상에 사용하지 않는다. 새16에서는 기존 raw 접촉·원자료와 실제 제어량으로 판정하며, 실패한 센서 자료는 보존한다.

1. runtime/run/analyzer16과 `static5_v14.json`을 준비한다. actual schema와 normal 부호·투영·combinedcap·두 Jacobian·lower 보존을 CPU에서 검증하고 독립 검수를 받는다.
2. `native_static_v14`5초에서 기존18개 기준과 새 제어 정합을 판정한다. G회전5°/이동30mm/넥3°/좌우20mm, Torso/Chest/Spine5°·right3°,1..5초 가슴+상완95%/양발95%,last1 네 발 기준을 완화하지 않는다.
3. 실패 시 현재 접촉 frame/force와 실제 geometry 변화를 먼저 기록한다. 성공하면 같은 설정 재현 후 압현·타현, 이어 왼손 해제15초를 검증한다. PPO는0으로 유지한다.

- [ ] 신규 제어·source/force/frame 정합 검증과 검수
- [ ] 실제 정지5초 전체 판정
- [ ] 통과 재현→압현/타현→왼손 해제

소비한 소스와 이 leaf는 수정하지 않고 결과는 새 진행 기록에 남긴다.
