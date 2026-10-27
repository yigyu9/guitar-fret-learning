# Quiet 손목 Y 목표 응답 실행 leaf

기존 [손목 계획](/home/ajou/yigyu/3/stability_adapter_2/QUIET_WRIST_SUPPORT_AUTHORITY_PLAN.md:1)에 따라 L_Wrist_y만 ±0.005 rad 보정한다. 원 quiet 기준 trial과 초기 81각, 원 스트랩 LA 1.1018469719600776 m, 자유 기타 초기 fullstate, root/하체 고정, 몸통9 PD ×2/√2, 기존 L_Wrist_x ±0.005 rad·1 Hz 파형을 그대로 둔다. 검지 추가 보정은 0이며 다른 80목표는 저장 baseline과 1200명령 전체를 대조한다.

- [ ] 새 runner·compact runtime closure·명령 독립 검산·독립 사전 검수
- [ ] plus/minus 각 한 초기화, fresh 15검사 뒤 같은 초기화에서 실제 0~5초·두151frame 영상
- [ ] 저장 분석·그림·초기값/영상 문서와 독립 최종 검수

명령은 60 Hz, 물리는 240 Hz다. 2초까지 추가 보정0, 2~2.5초 선형 ramp, 2.5~5초 일정 목표다. Float64 초기각+상대목표를 float32로 변환하고 기존 compose가 66offset ±0.3rad 및 native 목표 한계를 검사한다. Clip·gain 변경·기타 인위적 복원력·강제 손 부착·시작 후 state/pose 쓰기는 없다. 전체66 가용성을 유지한다.

두 조건 모두 원 quiet trial을 직접 읽으며 새 출력경로 quiet_wrist_support_authority_v1/native/{plus,minus}를 쓴다. 최대 두 실제 초기화이며 자동 재시작은 없다. 물리/API 오류는 원자료/partial로 보존하고 별도 진단 뒤 다음 행동을 결정한다. 원 index3 세 시도 및 감사32검사/3990파일 기록은 보존한다. 2초 이전 동일 prefix, 새 Wrist_y 유한응답, 실제 PD 추종·접촉·손바닥 상향·실제 한계 초과량을 측정하며 큰 각도나 feedback gain으로 외삽하지 않는다.

이 시험은 초기 상태 오차를 보정할 수 있는 실제 물리 제어권을 찾는 단계다. 이번에는 actor/checkpoint 로드·추론·학습을 하지 않는다. 원 Fret/Strike 코드는 현재 guitar frame으로 관측하며 기본 action은 정규화된 절대 PD 목표, Strike 손은 grip-reference residual이다. Source bounds는 checkpoint 출력 경험통계가 아니라 authored/profile/정규화 표현범위다. 초기 실제각의 source 범위 일치와 previous PD/history의 정확한 bridge 역변환 조건을 구분하며 향후 전환설계에서 검증한다. 이 조건을 완화했다고 연주 성공으로 취급하지 않는다.

구현 진입점: /home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_support.py:19
실행 봉인기: /home/ajou/yigyu/3/stability_adapter_2/run_quiet_wrist_support_phase.py:23
