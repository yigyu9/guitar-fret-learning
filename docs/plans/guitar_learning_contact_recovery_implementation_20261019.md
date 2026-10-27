# 접촉 회복 첫 구현 묶음

사용자가 개선 계획의 구현을 승인했다. 첫 범위는 평가 seed/초기화 진단과 회복 자료 수집이다. R1/R2 보상·새 학습·전곡은 다음 대조 실험으로 구분한다.

1. [x] 현행 지침·내부화·기존 계획 확인, 원본 probe/audit 계보 보관.
2. [x] 새 평가 seed/초기상태 비교·교란/실제240Hz회복 ledger·native 실행 경로 구현.
3. [x] 교란 행을 제외하는 독립 원자료 감사·자료 내보내기, 의미 있는 CPU 검사. 최종64개 통과, sidecar SHA·실제 float64 codec replay 보완 완료.
4. [x] 동결된 현재 소스에서 실제 native 평가/수집 연결 검사. 교사 수집3회·독립정책평가5회가 원 왼손 단음/안전 통과. 실제 원자료 v2 감사와0행내보내기거절 확인. 실패·부족한 시연은 보존하고 회복 성공으로 승격하지 않았다.
5. [x] 독립 change-reviewer 검수와 사용법·결과·남은 작업 기록. 잔여 actionable finding 없음; 결과는 docs/2026-10-12/stability_adapter_2/results/guitar_learning_contact_recovery_v1/README.md, verification.json.

기존 보상·원 관측/행동·Root/하체/자유기타·원 gain/제한/안전을 유지한다. 다른 작업자의 변경은 되돌리지 않는다. 기존 consumed source는 수정하지 않고 새 guitar_learning/contact_recovery와 하위 tests로 분리한다.

검수 기록: native 의존 import 오류를 수정하고 회귀 검사를 추가했다. v1 사전 검사는 초기 상태/조건 sidecar의 SHA 감사 누락을 보완하기 위해 native 수집 전에 명시적으로 중단했다. 로그·중단 이유·당시 소스는 결과 폴더에 보존했다. 보완 후 v2 실행으로 진행한다.

실제 수집3회는 원 음악·안전을 통과했다. 그중1회는 교란3tick이 실제 적용됐으나 상실0이라 회복자료를 발행하지 않았다. v2 감사로 실제 원자료/교사/보상/codec/회복 재현과0행내보내기거절을 확인했다. 기존 strict loader는 내부화 전 source provenance가 달라진 원본B32를 올바르게 거부했다. 고정 원본SHA·동일 원계약·소스 원문·완전한 명목capture 감사에 한해 출처 목록만 이관한 별도 평가 모델을 만들었고 반복reset2/2·새프로세스1/1·탐색2/2의 새 native 연결 검사를 통과했다. 원 strict load는 변경하지 않았다. 원본10파일/보관본·동결소스25파일 SHA 불일치0, 모든 완료 실행 입력 재해시 일치. 새PPO업데이트0·회복학습자료0건이다.
