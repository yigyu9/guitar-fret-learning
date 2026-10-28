# B 비용 head 초기0: seed17 재현 준비

## 목적과 고정 조건

seed7 B가 기존 연속2평가 기준을 통과했으므로, 원래 계획의 다음 단계인 독립 seed17 재현을 준비한다. seed7 B도300회에서65/128로 저하됐다. 이번 seed17은 B 자체의 재현이며 **seed17 대조군 없는 seed7 기준선과의 인과 비교가 아니다.**

- fresh B만 실행한다. 초기 비용 head의 weight/bias만0으로 만들고 나머지 초기 tensor·RNG를 같은 seed17의 정상 초기화와 대조한다. 모델 이전·resume·A gamma 변경·접촉 목표 제어 개입을 합치지 않는다.
- large128/H32/300, incremental, std0.1711710544767014, seed17, 원래 gamma/PBRS gamma0.99, 비용 계수1이다.
- 고정 기타·유한 팔 손목 teacher·엄지035·비선택 손가락 B·중지4축·원곡 target53의 원래 음 길이·onset-local3초를 유지한다. 561관측/9보상/물리 및 손목 종료/native 범위·속도·PD/엄격 loader는 기존 그대로다.
- 초기 policy/zero/random/reference128시도와50/100/150/200/250/300의 policy128시도: 학습1+평가10단계를 GPU에서 순차 수행한다. 모든 실패를 각128 분모에 포함한다.

## 재사용과 새 코드 범위

`run_replication.py`는 기존 `03_short_learning/support/run_short_comparison.py`의 `jobs(...,'incremental',17)`, `validate(...,'incremental',17)`, `run_child`, `analyze`를 재사용한다. 기존 v3 `support/variants.py`와 `support/run_variant.py`의 fresh B·strict 평가도 그대로 호출한다.

기존 `run_ablation.py`의 jobs/validate는 seed7에 고정되어 있어 수정하지 않는다. 새 child adapter는 기존 wrapper의 입력핀 목록에 이 새 orchestrator와 PLAN/CPU검사만 추가한다. 학습·평가 로직을 바꾸지 않는다. 실행 시 기존 frozen_sources 검증과 새 준비 seal을 함께 검증하며, 실행 도중에는 wrapper/PLAN/CPU검사도 child pin에 들어간다.

출력은 이 디렉터리의 `B_zero_cost_head_seed17/` 새 하위 경로다. 기본 명령은 dry-run이며 GPU를 실행하지 않는다. `--continue-evaluations`는 이미 완전 검증된 단계만 재사용하며 불완전 train을 재개하거나 덮어쓰지 않는다.

## 검증 체크리스트

- [x] 기존 동결 source/teacher/reference SHA 확인.
- [x] CPU dry-run: seed17 train1+eval10, B만 지정, 원래 checkpoint/128시도 계획 확인.
- [x] 같은 seed17 CPU 초기화에서73 tensor 중71 동일·비용 head2 정확0·RNG 동일 확인.
- [x] 평가 fresh=False에서 checkpoint 비용 head를 다시0으로 덮어쓰지 않으며 같은 계약 strict load/다른 계약 거부 확인.
- [ ] Python3.8 구문·독립 검수 통과 후 새 준비 seal 작성.
- [ ] root의 직렬 GPU 인계 후에만 실제300회+10평가 실행.
- [ ] 실제 initial checkpoint의 head0와 설정/핀을 CPU 재확인하고, 300행 비용 감사 및 전체10평가·scene 종료·outer 종료코드0 확인.
- [ ] 기존 acceptance 재계산과 간결한 seed17 재현 보고.

CPU 초기화 검사는 native 생성 initial checkpoint와 구분한다. 실제 GPU 성과·접촉력·자연스러움·자유 기타·전곡 성공은 준비 검사로 주장하지 않는다.

## 수용 기준과 인계 명령

달성≥80%, 유지≥70%, audible wrong≤10%, 물리 실패≤5%를 인접한 policy 평가2회에서 연속 충족해야 한다. 최종300회 수치와 손목/전체 실패도 그대로 보고하며 중간 최선만 고르지 않는다.

root가 다른 GPU 작업 종료를 확인하고 준비 seal/독립 검수를 확인한 뒤 실행한다.

```bash
python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/replication_cost_head_seed17/run_replication.py --execute
```

이 준비에서는 GPU를 실행하지 않는다. 기존 활성 소스·v3 support4개·seed7 결과는 보존한다.
