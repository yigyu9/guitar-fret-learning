# 고려 중인 Full 모델 구조

> **상태: SUPERSEDED.** 모델 선택은 완료되었다. 75D joint coordinator 후보 대신 rule timing supervisor와 별도 StabilityAdapter를 사용한다.

> 상태: **선택 전 — 현재 1순위는 후보 A**

모든 후보는 Frozen Fret·Strike, 관절 이름 기반 75D action ABI 후보, 단일 joint TanhNormal, central critic을 공통으로 사용한다.

## 후보 A — Latent Sync + Action Support

```text
Fret/Strike hidden feature
        ↓
분리된 SyncBranch ──────┐
                       ├─ Named Arbiter → joint action
Guitar/support state    │
        ↓               │
분리된 SupportBranch ───┘
```

- `SyncBranch`: Fret 준비와 Strike 타이밍 수정
- `SupportBranch`: 기타 pose·속도·접촉 안정화

장점:

- 타이밍과 안정화 역할이 명확히 분리된다.
- G0에서는 Sync, G1에서는 Support를 따로 학습·동결할 수 있다.
- 기존 단일손 기술을 보존하면서 새 몸통 action을 만들 수 있다.

단점:

- Source actor의 hidden 구조에 의존한다.
- Branch 간 관절 권한과 residual 충돌을 관리해야 한다.

판단: **현재 가장 추천하는 구조**

## 후보 B — 단일 Action Residual

```text
Fret/Strike proposal + event + guitar state
                    ↓
              Coordinator MLP
                    ↓
          bounded action residual[75]
                    ↓
               joint action
```

장점:

- 가장 단순하고 구현·검증이 쉽다.
- Source actor 내부 구조에 대한 의존성이 작다.
- 신규 안정화 관절을 직접 제어할 수 있다.

단점:

- 타이밍과 안정화 gradient가 한 모델에서 충돌할 수 있다.
- 보정 원인이 Sync인지 Support인지 구분하기 어렵다.

판단: **후보 A와 반드시 비교할 단순 baseline**

## 후보 C — Temporal Support 모델

```text
현재 event/source intent → 빠른 Sync MLP

최근 guitar/support history → causal TCN → Support correction

두 결과 → Named Arbiter → joint action
```

장점:

- Slip, 접촉 변화, 마찰처럼 시간 이력이 필요한 현상에 대응할 수 있다.
- 완전 자유 기타와 물성 변화에 가장 강할 가능성이 있다.

단점:

- History·reset·checkpoint 계약이 복잡하다.
- 학습과 디버깅 비용이 가장 크다.
- 현재 상태만으로 충분하면 불필요한 과설계다.

판단: **A/B의 시간 정보 부족이 확인될 때만 검토**

## 간단 비교

| 기준 | 후보 A | 후보 B | 후보 C |
|---|---|---|---|
| 양손 타이밍 | 매우 높음 | 중간~높음 | 매우 높음 |
| 기타 안정화 | 높음 | 높음 | 매우 높음 |
| Source 보존 | 매우 높음 | 매우 높음 | 높음 |
| 구현 복잡도 | 중간 | 낮음 | 높음 |
| 현재 순위 | 1 | 2 | 3 |

## 선택 원칙

```text
A가 timing·source 보존에서 우세 → A 선택
A와 B의 성능이 비슷함          → 단순한 B 선택
A/B가 시간 이력 부족으로 실패   → C 추가 검증
```

상세 비교와 실험 기준은 [`MODEL_FUSION_STUDY.md`](MODEL_FUSION_STUDY.md)를 참조한다.
