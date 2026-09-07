# 과거 설계 문서 안내

이 디렉터리는 초기 구현 과정에서 작성한 설계안과 체크리스트를 보존하는 역사 기록이다.

현재 연구 구조와 모듈 책임의 정본은 [`master_plan`](../../master_plan/README.md)이다. 이 디렉터리의 수치, action/observation 차원, 네트워크 구조, G0/G1/G2 책임을 현재 구현 계약으로 사용하지 않는다.

## 문서 상태

| 문서 | 상태 | 보존 이유 |
|---|---|---|
| `learning_env_design.md` | SUPERSEDED | 초기 PPO·멀티크리틱·75D Full 구조의 근거 기록 |
| `task_fret_plan.md` | HISTORICAL | Fret 최초 구현 계획과 선택 근거 |
| `task_fret_design.md` | SUPERSEDED | Fret-v1 계열 규칙과 과거 관측 계약 기록 |
| `task_fret_checklist.md` | SUPERSEDED | 과거 Fret 구현 검증 내역 |
| `task_strike_design.md` | SUPERSEDED | Xu 기반 Strike 초기 이식 설계 기록 |
| `task_full_design.md` | SUPERSEDED | AdaptNet 기반 양손 결합안 기록 |
| `task_hold_design.md` | SUPERSEDED | 단일 Full 정책을 직접 fine-tuning하던 초기 안정화안 기록 |

## 현재 설계와 달라진 핵심

- Fret-v2는 420D observation과 30D action을 사용한다.
- Strike-v2는 303D observation과 30D action을 사용한다.
- 최종 FullBody action ABI는 이름과 순서가 고정된 105D다.
- Fret과 Strike는 최종 Full 정책의 일부를 처음부터 공동 학습하는 것이 아니라 재사용 가능한 기술 prior다.
- Synchronizer는 AdaptNet이나 관절 residual 정책이 아니라 공통 음악 시간축과 readiness를 관리하는 규칙 기반 timing supervisor다.
- 기타 안정화는 기존 Full 정책 전체를 바로 fine-tuning하는 방식이 아니라 별도 StabilityAdapter가 residual 보정을 수행한다.
- G1부터 하체, 몸통, 양손 인접 관절을 포함한 전신 action을 활성화하되 기존 Fret·Strike 기술 보존을 우선한다.
- 스트랩은 충돌 가능한 천/줄 모델이 아니라 물리 효과를 갖는 tension-only 가상 제약이며, 시각화는 별도다.
- Full 실행에서는 하나의 Canonical PlayEvent cursor와 공통 score clock을 사용한다.

## 사용 규칙

- 과거 결정의 이유를 추적할 때만 이 디렉터리를 참조한다.
- 새로운 구현이나 checkpoint 계약은 `master_plan`, 현재 코드, 각 모듈의 최신 실행 문서를 기준으로 한다.
- 과거 내용이 현재 설계와 충돌하면 `master_plan`을 우선한다.
- 역사적 문서의 숫자를 최신 값으로 부분 수정하지 않는다. 부분 수정은 서로 다른 세대의 계약을 한 문서에 섞을 수 있다.

