# v9 초기 자세와 대기 MCP 허용 범위 반영

GPU 왼손의 기본 초기 상태와 행동0 유지목표를 v9로 바꿨다. 학습·평가·영상·GPU진단의 GpuScene이 같은 자산을 사용한다. 원본035/v14와 오른손·CPU 과거실행은 보존한다. 학습기본에 쓰는 자산은 guitar_learning/assets/prepared_reset_v1/left_standby_v9.json이며 docs 없이도 로드한다. 자산은 원후보바이트를 그대로 복사해 diagnostic_only 기록도 원문에 남아있지만 실제 채택상태·SHA는 runtime/scene 계약에 명시한다.

대기 보상은 기존 B 중심을 유지하면서 MCP±30도/PIP·DIP±15도 안에서 같은 최대품질을 준다. 바깥30도 척도 감쇠, 손가락별 gate, 보상률.02/초, 준비·압현 보호, 엄지/벌림 제외, 움직임 비용0은 유지한다. 가동범위 제한이나 대기자세 자동복귀를 추가하지 않았다. 준비보상계약은v6이며 새 초기자세 자산도 input SHA에 봉인한다. 이전체크포인트 재개 검증을 완화하지 않는다.

## 확인한 결과

- CPU 핵심60개 통과: 초기상태/변조거부/관절별 보상범위/제어/이식성/환경/충돌 검사.
- 함께 실행한 preparation_B 포함59개 중58개 통과, 구형v22 checkpoint 검사1개는 실패했다. test_v22_checkpoint_roundtrip_rejects_legacy_v20_without_state_mutation의 현재 정책 생성 단계에서 엄지 관측v2 요구와 현행v3 계약이 불일치한다. 이번 변경의 MCP 계산·초기로더와 무관한 legacy 계약 검사이며 우회하거나 정책 검증을 완화하지 않았다. 원로그는 cpu_all_requested.log, 핵심통과로그는 cpu_core.log에 있다.
- 실제GPU 기본4환경에서 초기q오차0, 행동0 reference 일치,1200step/5초 유한상태, 환경1·3 부분reset 및0·2 행보존 통과. 기본로더를 교체하는 monkeypatch 없이 검사했다.
- large8환경/H32의 신규2업데이트·512전이 완료. final.pt와 초기모델,2줄학습지표 저장. 입력봉인에 v9 자산 포함, training_contract에30/15/15 기록을 확인했다. 짧은 실행 연결 검사이며 압현 학습 성능 개선을 입증한 결과는 아니다.
- change-reviewer 독립검수: Critical/Warning 없음. 이전 원문과 비교해 자산/SHA/이식성/초기복원/대기gate/strictresume 확인.

[기본GPU검사](default_reset_verification.json) · [짧은학습결과](training_smoke/report.json) · [학습계약](training_smoke/J/training_contract.json) · [보상문서](../../../../2026-10-26/왼손보상구조/04_손가락추종과자세.md)

변경 전 원문·SHA는 guitar_learning/archive/20261030_before_left_standby_v9/manifest.json에 보관했다. 기존035/v14 원자료와 v9 시각화 결과는 수정하지 않았다.
