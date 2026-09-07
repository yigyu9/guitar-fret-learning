# 문서 안내

현재 연구 구조의 최상위 정본은 [`master_plan`](../master_plan/README.md)이다. 실행 명령과
코드 계약은 [`tab2body/TRAINING.md`](../tab2body/TRAINING.md), Fret·Strike의 현재 허브는
각각 [`fret/README.md`](../fret/README.md), [`strike/README.md`](../strike/README.md)를 따른다.

## 문서 분류

- `2026-*`: 해당 날짜의 실험, 승인, 설계 상태를 보존한 역사 기록
- `plans/`: Master Plan 이전의 설계안과 체크리스트; 모두 역사 기록
- `related_work_analysis/`, `*-paper-ko.md`: 선행연구 내용과 비교 근거
- `TRAINING_IMPROVEMENT_PROCESS.md`: 현재 실험 변경 기록 규칙
- `guitar-basics-notes.md`: 기타 도메인 참고자료

날짜별 문서나 선행연구 문서의 “현재”는 그 문서가 작성된 시점을 의미한다. 현재 코드의
action/observation 차원, Synchronizer 책임, G0/G1/G2 구조를 판단할 때는 사용하지 않는다.

## 현재 핵심 계약

```text
Fret-v2       420D observation / 30D action
Strike-v2     303D observation / 30D action
Synchronizer  rule-based timing supervisor / no joint ownership
FullBody      named 105D ABI; G0는 60D active + 45D held
Strap         tension-only virtual constraint + separate visualization
```

## 현재 구현 경계

- Fret-v2와 Strike-v2의 독립 환경·학습·checkpoint 계약은 구현되어 있다. 현재 저장된
  checkpoint의 성능 승급 여부는 계약 구현과 별도로 판단한다.
- Canonical PlayEvent, rule Synchronizer, 105D action 조립과 source checkpoint 검증은 CPU
  계약 수준으로 구현되어 있다.
- 하나의 Isaac Gym simulator에서 두 source policy를 실제로 함께 실행하는 `FullG0Task`와
  G1/G2 StabilityAdapter 학습은 아직 구현 전이다.
- Strap은 독립 Isaac Gym probe에서 검증했으며 Full runtime 연결은 남아 있다.
