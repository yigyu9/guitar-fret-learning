# 교정된 엄지 기하에서의 fresh 기준선과 시간척도 비교

이 폴더는 thumb rear support v3 / episode diagnostics v6 교정 후의 별도 CPU 준비본이다. 상위 time_credit_ablation의 기존 support·frozen_sources·cpu_inputs·active_source_before·review 및 기하 수정 전 thumb A/B 봉인은 변경하지 않는다. 원래 도구 4개의 수정 전 사본과 SHA는 `before_path_adjustment/`와 `before_path_adjustment.json`에 있다. `variants.py`는 원본과 바이트까지 동일하다. 새 도구는 중첩 경로·봉인 검사·CPU 기하/입력 호환성 검사만 추가하며 A/B 수학과 초기화 의미를 유지한다.

순서는 현재 생산 native 회귀 완료 → root의 직렬 GPU 인계 → **현재 기하의 fresh 원래 gamma baseline** → **같은 기하의 A** → 필요하면 B다. GPU 인계는 팀 내부 자원 조정이며 추가 사용자 승인 요청을 뜻하지 않는다. 이 준비에서는 GPU/학습/평가를 실행하지 않았다. 과거 기하의 baseline과 새 A 사이 차이를 gamma 효과라고 판단하지 않는다. 이전 모델·optimizer를 이식하거나 strict resume를 완화하지 않는다.

세 조건 모두 incremental/large/128환경/H32/300회/seed7/std .1711710544767014·중지 row8·원래 2초 손목 teacher·동일 finite 제어다. baseline은 원래 gamma .99와 원래 cost head를 사용한다. A는 reward/PBRS gamma만 `exp(-1/1800)`으로 맞춘다. B는 원래 gamma .99에서 fresh cost head의 weight/bias 두 텐서만 0으로 초기화한다. B 평가 load에는 재초기화를 적용하지 않는다. 두 변경을 합치지 않는다.

각 조건은 fresh train 1개 + 초기 policy/zero/random/reference 4개 + 50/100/150/200/250/300 정책 평가 6개 = 11개 직렬 job이다. 평가마다 원래 128환경 첫 시도와 모든 실패를 분모에 보존한다. reference는 손가락까지 유한 제어하는 대조군이며 학습 성과가 아니다. 수용 기준(달성≥80%, clean≥70%, wrong≤10%, 물리실패≤5%, 연속2개 정책평가), 손목/전체실패 보고, seed17/27 후속 확인과 자유 기타/67음 미검증 한계는 원래 계획 그대로다.

## root 실행 명령

프로젝트 루트에서 아래 명령은 계획만 출력한다. 생산 native 회귀 완료와 root GPU 인계 뒤 해당 명령에만 `--execute`를 추가한다. baseline은 기존 실행기를 그대로 사용하며 새 출력 폴더를 명시한다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/03_short_learning/support/run_short_comparison.py --mode incremental --seed 7 --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/baseline_original_gamma_seed7

/home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/support/run_ablation.py --variant A_time_discount_30s

/home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/support/run_ablation.py --variant B_zero_cost_head
```

baseline 직전에도 새 CPU 봉인 검사를 실행한다. A/B orchestrator와 child는 native import/새 출력 작성 전에 이를 자동 확인한다. baseline은 원래 orchestrator의 실행 중/종료 후 소스 검사를 그대로 쓴다. 모든 실행 동안 봉인 대상 문서를 수정하지 않는다.

```bash
PYTHONPATH=docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/corrected_source_v3/support python -c 'from run_variant import validate_freeze; validate_freeze()'
```

`cpu_self_test.json`은 실제 large 모델·production GAE·strict loader로 A tensor/RNG 동일성, B 두 head 텐서만 변경, reward encoder 갱신 후 zero-cost GAE=0, 양의 비용 head 학습 가능, 같은 계약 3개 허용/교차 6개 거부를 확인한다. baseline/A/B 모두 원래 teacher evidence/reference를 읽었고 현재 rear plane `[0,0,-1,-.008]` 및 v3/v6 계약을 확인했다. 합성 비용의 감소는 실제 실패 비용 학습 성능이 아니다. `dry_run_baseline.json`, `dry_run_A.json`, `dry_run_B.json`과 새 `frozen_sources.json`·`cpu_verification.json`이 별도 준비 근거다. CPU 확인만으로 native 학습 결과를 주장하지 않는다.
