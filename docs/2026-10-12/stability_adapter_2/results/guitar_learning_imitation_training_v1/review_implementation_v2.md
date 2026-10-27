# BC 계약 표현 호환 수정 독립 검수 v2

요약 판정: **문제없음**. 기존 BC 초기화의 JSON list와 native tuple 표현 차이를 contract 내부 비교에서만 정규화한다. Critical·Warning 및 현재 hand별 PPO 연결을 막는 구현 결함은 발견하지 못했다. 실제 v2 BC 평가도 LH/RH 각각2/2 성취·안전한 전체 horizon 완료·입력 불변으로 끝났다. 이는 이번 단일 목표/동일 prepared start의 결과이며 PPO 후 기능 유지를 보장하지 않는다.

## 범위와 실패 기록

신규 `guitar_learning/imitation_v2.py`, `train_imitation_ppo_v2.py`, `evaluate_imitation_v2.py` 및 `tests/test_imitation_contract_v2.py`, `tests/test_imitation_ppo_v2.py`를 읽기 전용으로 검수했다. 기존 evaluator와의 diff, 실제 BC checkpoint·capture/eval reset 계약 및 닫힌 v2 평가 결과도 확인했다. 소유한 이 보고서 외의 파일은 수정하거나 실행하지 않았다.

v1 BC는 양손 각각2,000step을 수행했지만 첫 native 평가는 정책 행동 실행 전에 초기화 계약 비교에서 거부됐다는 root 보고를 확인했다. BC 모델을 만든 capture JSON에는 list가 저장되고 native 환경 계약에는 tuple이 포함돼 있어 기존 Python dictionary exact 비교가 달라졌다. 이는 기존 BC 초기화 로더의 실행 시 호환성 결함이며 v1의 실제 정책 성취로 기록하면 안 된다. 당시 실패·BC fit·소비된 소스는 보존한다. 새 로더가 BC를 다시 학습하거나 기존 payload를 덮어쓰지는 않는다.

`archive/20261018_before_imitation_contract_v2/manifest.json`의5개 기존 파일은 현재 원본과 보관본 모두 기록 SHA와 일치함을 독립 확인했다.

## Critical / Warning

없음.

## 수정 범위와 엄격성

1. **contract만 정규화 — `imitation_v2.py:13–45`.** 재귀적으로 문자열 key를 요구하고 `allow_nan=False`인 JSON roundtrip을 사용한다. tuple/list의 순서와 값은 유지되고, 값·필드·범위·역할/목적·안전 조건을 제외하거나 재작성하지 않는다. source/target architecture는 각각 deepcopy한 뒤 그 안의 `contract`만 바꿔 비교하므로 원 target architecture와 raw container는 그대로 남는다. outer `roles` tuple 같은 architecture 차이를 JSON으로 우회하지 않는다.
2. **복사 전 검증·Actor만 적용 — `imitation_v2.py:30–61`.** 기존 별도 BC schema·역할·metadata 요구, PPO identity/updates 거부, 전체 model key/shape/dtype/유한값과 초기화 파일 불변 검증을 유지한다. 검증을 모두 마친 뒤 선택 Actor encoder/head와 선택 std만 복사한다. Critic·상대 손·optimizer·PPO 카운터를 가져오는 경로는 없다.
3. **PPO entrypoint의 좁은 교체 — `train_imitation_ppo_v2.py:7–13`.** 기존 runner 호출 동안 BC initializer 바인딩만 일시 교체한다. fresh 실행의 Actor 전달→기존 fresh PPO optimizer 생성 순서는 그대로다. strict resume는 BC 전달을 건너뛰고 기존 전체 identity load를 사용한다. 새 canonical 비교로 PPO checkpoint의 strict identity를 완화하지 않는다. 정상/중단 때 바인딩을 복원한다.
4. **평가 경로 — `evaluate_imitation_v2.py:26`.** v1 evaluator와의 차이는 BC initializer import 한 줄이다. profile·505입력·`parallel.FIELDS`·deterministic action·원240Hz 측정/행동 직전 기록·PPO strict load는 바꾸지 않는다.

## 시험과 실제 계약 확인

정본 `cpu_tests_v2.log`에서 root가 실행한 전체 **207 tests, 85.743s, OK**를 확인했다. 신규6개 검사는 container 표현 동등성·target metadata 무변경·Actor/std만 복사, 실제 값/범위/size/skill/역할/outer container/NaN 차이 거부, 비문자열 key/비유한 계약 거부, 기존 runner 전달·strict resume·중단 복원을 다룬다. 검수자가 해당 소스를 실행하거나 시험을 재수행한 결과는 아니다.

새 tuple/list 회귀 fixture는 **합성 계약**이다. 실제 native 전체계약 fixture를 시험에 넣었다고 표현하지 않는다. 실제 데이터에 대해서는 두 BC checkpoint의 저장 계약을 직접 읽어, 각각 원 capture와 v2 eval의 `reset_00.json` 계약 값·필드가 exact 일치함을 독립 확인했다. 실제 raw tuple 표현을 잃는 JSON 자료 대조만으로 native 로드 통과를 주장하지 않고, 아래의 실제 평가 결과도 함께 확인했다.

## 실제 v2 BC 평가와 해석

- `left_bc_eval_v2/result.json`, `right_bc_eval_v2/result.json` 모두 `completed=true`, `source_unchanged=true`,2개 episode의 `stage_success=true`와 `reason=timeline_complete`다. 두 손 모두 container 비교를 넘어 정책 행동을 실제 실행했다는 근거다.
- BC report의 `ppo_updates`는0이고 payload schema는 `guitar_learning.imitation.v1`이다. BC fit을 PPO 업데이트로 세지 않는다.
- 두 BC fit은2,000step에서 LH MSE **2.480236253e−5**, RH **5.431588943e−5**로, 목표1e−6에 대한 `converged=false`다. 이를 목표 오차 수렴으로 바꾸지 않는다. 실제 native2/2 성취와 학습 자료 오차 목표는 별도 판정이다.
- 이번 기능 성취는 LH 올바른 contact/50ms hold와 RH 지정 현·방향의 기하 cross다. 음악 시각·음향·하중 비의존·V3 정밀 조건·다른 초기 분포/곡·양손 결합을 인증하지 않는다.

현재 계획의 native gate는 양손에서 통과했다. 이후 PPO의 실제 유효 업데이트 수·입력/수명 감사·마지막 결정적 기능 유지와 실패는 별도 결과 검수가 필요하다. 이 수정이 앞으로의 PPO 학습 성과나 최종 봉인까지 승인하는 것은 아니다.
