# 세 면 half 초기 자세의 스트랩 여유 비교

## 근거와 결정

`three_face_arm_initial_target_v1`의 새2회5초/2400step에서 팔12 목표를 실제 초기각으로 일치시켰지만 최대 이동159.799114/157.516483mm, 종료159.795174/157.510653mm로 저장 기준 최대25.229274·종료21.912505mm보다 커졌다. 두 조건은 채택하지 않는다. 손바닥 양의 raw lambda 마지막 step90/99, index3는11/11이며 지속 세 면 지지는 확인되지 않았다. 두 실행의 passive strap 제출장력은 전체1200 controls에서0N이었고 법칙 재계산오차0이다. 이는 해당 물리 경로에서 장력이 생기지 않은 관측이며 strap 비활성화 또는 단독 원인이라는 뜻은 아니다.

다음에는 저장 reference의 half 초기81q와 이전 절대81 PD목표(`saved_finger_targets`)로 돌아가 초기 스트랩 여유만 비교한다. 현재 LA1.1018469719600776m, half 초기 route1.0868332051527874m이므로 여유15.0137668072902mm이다. 다른 seed2/full 초기 자세의 이전 taut 시험은 이동35.020211mm/회전7.542504°로 tradeoff였으므로 이번에도 개선을 가정하지 않는다. half 배치에서는 route와 손 source 간격이 달라 직접 새5초 비교한다.

## 새2조건과 검증 체크리스트

- [ ] 저장 완료된 `three_face_support_loss_v1/native/saved_finger_targets`를 기준으로 초기81q, 기타 p/q/속도, 이전 절대81 목표, 몸통9·오른팔손·물리 고정 root/하체, PD/solver/material/strap 법칙을 정확히 보존한다. 기준은 저장 실행이며 새 native 실행으로 세지 않는다.
- [ ] `half_slack`: LA=(기존 LA+현재 route)/2=1.0943400885564325m로 초기 여유7.5068834036451mm. `zero_slack`: LA=현재 route=1.0868332051527874m로 초기 여유0mm. 첫 초기 법칙 장력은 둘 다0N이며 이후 gravity/contact와 passive stretch/damping으로만 장력이 생긴다. 실제 초기 route를 재측정해 수치/부동소수 오차를 기록한다. 길이는 실행 중 변경하지 않는다.
- [ ] 소비된 prepare/runner/analyzer의 이전 SHA와 source snapshot을 대조한 뒤 새 이름으로 구현한다. 새 source/FK admission·손바닥 상향 proxy·초기 설정 범위와 목표 float32 exact를 검증한다. 초기 불합격이면 partial 초기값/로그/영상으로 보존하고 관절·기타 pose를 강제로 바꾸지 않는다.
- [ ] 신규2회 각각 실제5초(1200step), 초기값/target81/actual states·contacts·controls/strap law, Gym 손/전신0~5초151frame를 보존한다. 왼33 또는 팔12는 이번 진단 범위일 뿐 최종 양쪽66 제어권 제한이 아니다.
- [ ] 첫.1초/전체최대/종료/마지막1초 기타 위치·회전 오차, 손 body접촉 시점, 몸통 실제좌표편차, strap law tension/포화·rate와 고정 root/하체를 원자료로 비교한다. 두 오차와 유지 양상을 함께 보며 초기 잠깐의 개선만으로 채택하지 않는다. 결과 그림/설명·독립 검수·기존 자료 보존을 완료한다.

기타 고정·손 강제 부착·추가 기타 목표 힘·지속 pose 덮어쓰기는 사용하지 않는다. Source hull 근접/선택facet 방향/body raw lambda로 해부학적 손가락 pad·넥 후면/전면/옆면의 실제 접촉, PhysX cooked 관통 여부, 접촉력N 또는 연속 지지를 인증하지 않는다. 최종 초기 기타 p/q 복원·유지, 연주 중 안정화·학습 구조는 여전히 미완료다. 사용자의 자율 진행 지침에 따라 별도 승인 대기 없이 작은 단위로 진행한다.

계획/구현은 `stability_adapter_2/`, 결과는 `docs/2026-10-12/stability_adapter_2/results/three_face_half_strap_slack_v1/`에 저장한다. 이 계획은 아직 구현·실행하지 않았다.
