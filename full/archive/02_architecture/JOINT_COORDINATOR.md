# JointCoordinator 모델 구조

> **상태: SUPERSEDED.** Synchronizer가 관절 action을 출력하는 구조는 채택하지 않았다. 현재 Synchronizer는 규칙 기반 timing supervisor이며 관절 residual은 향후 StabilityAdapter 책임이다.

> 상태: 구조 검토 중. 아직 확정되지 않음.

세 후보의 간단한 선택 절차는 [`MODEL_SELECTION.md`](MODEL_SELECTION.md), 상세 비교와 저장소·checkpoint 제약은 [`MODEL_FUSION_STUDY.md`](MODEL_FUSION_STUDY.md)를 참조한다.

완전 자유 기타까지 포함한 현재 제1 가설은 다음 하이브리드다.

```text
explicit event supervisor
  + frozen Fret/Strike policy adapters
  + separate SyncBranch
  + separate bounded action-logit SupportBranch
  + phase-aware named-action arbiter
  + one joint TanhNormal
  + fixed-shape central 11-head critic
```

두 trainable branch는 trunk와 optimizer group을 분리한다. G0 fixed에서는 Support가 exact zero이고, G1 free-root+soft hand tether에서는 Sync를 동결한 채 Support만 학습하며, G2에서는 동일 free asset에서 tether를 0으로 만든다.

단, 고정 기타 matched ablation에서 단일 pre-tanh action residual이 latent Sync에 비열등이 아니면 SyncBranch는 더 단순한 그 구조를 선택한다. 기타 안정화의 물리·학습 계약은 [`GUITAR_STABILIZATION.md`](GUITAR_STABILIZATION.md)와 [`CURRICULUM.md`](../04_training/CURRICULUM.md)를 참조한다.
