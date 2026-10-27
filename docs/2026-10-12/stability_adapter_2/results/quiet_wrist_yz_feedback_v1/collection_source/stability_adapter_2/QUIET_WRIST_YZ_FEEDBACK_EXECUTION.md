# Y/Z 기타 오차 feedback OFF/ON 실행 단위

[제어 설계](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_YZ_FEEDBACK_PLAN.md:1)를 구현한다. 기존 Z 응답 phase를 먼저 독립 검수·보존 감사로 마무리한 뒤 새 `quiet_wrist_yz_feedback_v1`에서 진행한다.

1. 기타 world 위치와 xyzw 방향에서 `goal-current` 위치 오차 및 `Log(R_goal R_current^-1)` 회전 오차를 계산하는 작은 helper를 추가한다. 저장된 6×2 응답과 고정 κ를 쓰며 60Hz 업데이트마다 두 보정각을 적분한다. 실제로 적용한 오차·gradient·요청 rate·포화 후 유효 rate·보정 전/후 각도를 저장한다.
2. 기존 quiet 녹화 runner를 새 파일로 복사하고, 두 보정각을 기존 66관절 offset에 한 번 합성한다. OFF는 보정각0, ON은 command_time>2초에서만 갱신한다. 나머지79관절·모든 손가락·기존 Wrist_x 파형과 PD/LA/초기값을 유지한다. 관절 state setter나 기타 force를 추가하지 않는다.
3. 새 봉인 runner는 재사용 local import closure·자산·baseline·Y/Z 비교 결과와 그 inventory·두 계획을 실행 전에 해시 및 사본으로 보존한다. 기존 출력이 있으면 거절하고 각 OFF/ON은 ONE 초기화만 허용한다. 로그를 닫은 뒤 exit code와 전후 입력 SHA를 기록한다. 자동 재시도는 없다.
4. 실행 전 독립 계산으로 world 회전 오차 부호·quaternion 부호 불변성·0오차·오차 반전·rate/각도 제한·포화 복귀·첫484 전체 목표·다른79/손가락 목표를 검산한다. 별도 change-reviewer 검수 후 두 실제5초·151frame·각 손/전신 스트랩 영상을 기록한다. 이 단위에서 actor 추론·학습은 없다.

저장 결과 분석은 새 phase에서 수행한다. OFF와 기존 baseline 전체 경로, ON의 공통 prefix 및 현재 오차→목표 기록을 대조하고 초기 p/q 오차와 후기 변화를 나누어 보고한다. 검사를 통과하는 것과 자연스러운 연주·폐루프 안정성 인증을 구분한다. 제약 위반과 native 실패는 부분 결과로 보존한다.

- [ ] helper·runner·봉인 runner 구현 및 독립 수학/목표 검산
- [ ] 독립 사전 검수
- [ ] OFF/ON 각 ONE 실제5초와 초기값/영상 보존
- [ ] 원자료 분석·Luna 산출물·독립 최종 검수
