# 시간 할인과 비용 critic 초기화의 분리 대조

[승인된 계획](../INTERVENTION_PLAN.md)의 실행기와 CPU 검증을 준비했다. **GPU 학습은 아직 실행하지 않았다.** 활성 `guitar_learning`과 기존 `docs03/support/run_short_comparison.py`는 수정하지 않았다.

| 대조 | 변경 | 유지 |
| --- | --- | --- |
| A `A_time_discount_30s` | PPO gamma와 PBRS gamma를 모두 `exp(-1/(60×30)) = 0.9994445987368581`로 설정 | 원래 비용 head 초기값, cost gamma1, lambda.98 및 나머지 설정 |
| B `B_zero_cost_head` | fresh 정책의 `cost_critic.weight`, `cost_critic.bias`만0 초기화 | reward/PBRS gamma.99, actor·reward critic·value encoder·std·RNG 및 나머지 설정 |

A와 B는 별도 태그·별도 출력·별도 실행이다. 두 변경을 합치는 옵션이 없다. B의 초기화는 train에서 새 정책을 생성할 때만 적용한다. evaluate에서는 원래 strict loader로 저장된 head를 읽고 **재초기화하지 않는다**. 태그는 `settings.song.short_learning.ablation`에 들어가며 정책 architecture의 task 계약에도 보존된다. 같은 계약의 저장본만 strict load할 수 있다.

기존 CLI·runner·ShortPolicy·DecisionPPOTrainer·학습/평가/분석 함수를 재사용한다. 문서 아래 wrapper가 해당 프로세스의 생성 함수만 연결하고 종료 시 복구한다. 디스크의 활성 소스나 기존 실행기를 편집하지 않는다. 두 비교 모두 incremental/large/128환경/H32/300회/seed7/std.1711710544767014/중지row8 고정 손목 teacher 조건이다.

## 순서와 명령

A부터 실행·분석하고 필요하면 B를 별도로 실행한다. 현재 seed17 작업이 끝나 GPU를 인계받기 전에는 `--execute`를 사용하지 않는다. 기본 명령은 실행 계획 JSON만 출력하고 반환하며 Isaac Gym·Torch·하위 프로세스를 시작하지 않는다.

```bash
taskset -c 0-13 /home/ajou/miniconda3/envs/rl38/bin/python \
  /home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/04_ablation/time_credit_ablation/support/run_ablation.py \
  --variant A_time_discount_30s
```

GPU 인계 후 같은 명령에 `--execute`를 붙인다. 기본 출력은 이 디렉토리의 `A_time_discount_30s_seed7`이다. B는 variant를 `B_zero_cost_head`로 바꾸며 `B_zero_cost_head_seed7`에 저장된다. 기존 경로를 덮어쓰지 않는다. 중단 후 `--continue-evaluations`는 **완료·봉인 검증을 통과한 단계만** 재사용한다. 미완료 학습을 resume하는 기능은 없다.

각 실행은300회 fresh 학습, 초기 policy/zero/random/reference4대조, 50·100·150·200·250·300회의 policy6평가를 직렬 수행한다. 평가마다128환경의 첫 시도를 포함하며 실패를 분모에서 빼지 않는다. reference는 선택 손가락도 스크립트로 움직인 대조군이고 학습 성과가 아니다.

기존 보상·성과·관절 그림과 함께 `analysis/acceptance.json`을 저장한다. 통과 기준은 달성≥80%·clean≥70%·wrong≤10%·물리실패≤5%를 **연속 두 개의 학습 후 policy 평가**에서 만족하는 것이다. 손목·전체 실패도 함께 보고한다. seed7 통과가 채택이나 자유 기타·전곡 성공을 뜻하지 않는다. 예산이나 문턱을 결과에 맞춰 바꾸지 않는다.

## 소스 봉인과 CPU 확인

자체 wrapper·variant/helper·orchestrator·재사용 실행기, teacher/reference와 해당 evidence, 승인 계획을 모든 child 입력 SHA에 넣는다. child 실행 전 입력 manifest가 생기기 전에도 같은 파일을 감시한다. 기존 `run_child`의30초 감시와 child의 전후 봉인 검증을 유지한다. 따라서 GPU 실행을 시작한 뒤에는 이 support의 Python 파일과 감시 대상 문서를 편집하면 안 된다.

[CPU 결과](cpu_self_test.json)는 실제 **large** 모델과 production GAE·strict loader를 사용했다. GPU 장치를 숨긴 상태에서 다음을 확인했다.

- A의 설정 diff는 두 gamma와 계약 태그뿐이며, 실제 환경 PBRS gamma가 일치한다. 초기 모델 텐서와 RNG도 원래와 같다.
- B의 상태 텐서는 비용 head 두 개만 달라졌다. actor·reward critic·value encoder·std 및 생성 후 RNG가 동일하다.
- reward 학습으로 shared value encoder를 바꾼 뒤에도 비용 예측과 zero-cost GAE는0이다.
- 합성 양의 비용 target을 주면 원래 optimizer가 cost head를 학습한다. 한 번의 CPU 검사에서 loss가1에서 약0.99021로 감소했다. 이는 실제 자유 기타 실패 비용 학습의 성능 증거는 아니다.
- 같은 variant3경우는 strict load를 수용했고 baseline/A/B 사이6개 교차 로드는 거부했다. 학습된 비영 비용 head는 evaluate 구성·load 후에도 유지됐다.

`active_source_before.json`의518개는 **활성 Python517개와 재사용 실행기1개**를 합친 수다. 새 활성 Python 파일을 추가한 것이 아니다. 최종 [CPU 검증](cpu_verification.json)과 `frozen_sources.json`에서 분모와 SHA를 구분한다. A/B의 실제 native 학습·평가 결과는 GPU 실행 후 별도로 검증해야 한다.
