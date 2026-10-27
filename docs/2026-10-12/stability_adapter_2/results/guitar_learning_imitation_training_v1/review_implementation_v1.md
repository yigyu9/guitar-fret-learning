# 교사 초기화·손별 PPO 구현 독립 검수

요약 판정: **문제없음**. 검수 범위에서 Critical·Warning 및 현재 BC/평가 연결을 차단할 결함을 발견하지 못했다. PPO 진행은 계획대로 **BC 정책의 실제 결정적2회 성취와 안전한 전체 horizon 완료·입력 불변**을 확인한 뒤 결정해야 한다. BC fit이나 evaluator의 `completed=true`만으로 기능 성공을 인증하지 않는다.

## 범위와 근거

`guitar_learning/AGENTS.md`와 `docs/plans/guitar_learning_imitation_training_20261018.md`를 읽고 신규 `imitation.py`, `imitation_environment.py`, `train_imitation_ppo.py`, `imitation_io.py`, `capture_imitation.py`, `train_imitation.py`, `evaluate_imitation.py` 및 두 신규 시험 파일을 읽기 전용으로 검수했다. 기존 runner·환경·SpecialistPolicy/PPO는 연결 계약만 대조했다. 소유한 이 보고서 외의 소스·시험·문서·원자료를 수정하지 않았다.

root가 실행한 정본 `cpu_tests_v1.log`에서 **201 tests, 83.197s, OK**를 확인했다. 신규 검사는12개이며 dataset 형식·행동/마스크·잘못된 계약 거부, 실제 Actor-only fit·초기화 roundtrip, 비선택 tensor 보존, 고정 profile/reset, PPO 전달 순서·strict resume·중단 시 일시 바인딩 복원을 다룬다. 검수자가 시험이나 native 실행을 다시 수행한 결과는 아니다.

## Critical / Warning

없음.

## 확인한 구현 계약

1. **동일한 물리 profile — `imitation_environment.py:14`, `:34`, `:41`.** LH hold의 distal-origin 접근 계수만0으로 하고 RH cross의 guide를 y−0.36m/depth0.004m/반폭0.008m로 고정한다. 원래 240Hz 접촉·기하 통과·성공·안전 및 기존39행동 codec을 바꾸지 않는다. 역할/단계와 profile을 매 reset의 task 계약에 붙이며 다른 skill·첫 event/tempo 변경·profile override를 거부한다. wrapper의 step/close는 기존 환경에 연결된다.
2. **실제 새 profile 재수집 — `capture_imitation.py:23–49`.** 과거505 교사 자료의 역할·형식·성공 기록을 검사한 뒤 행동만 새 profile에서 재생한다. 행동 직전 관측과39행동을 짝짓고 후속 네 물리 표본을 따로 저장한다. 새 성취 flag는 새 환경에서 측정한다. 과거 성공 flag를 새 결과로 복사하지 않는다. root의 닫힌 `left_capture_v1`/`right_capture_v1` 결과에서 각각 `success=true`,240 ticks·505차원·입력 불변을 확인했다. 이는 scripted 재생이며 BC 정책 성공이 아니다.
3. **데이터·계약 검사 — `imitation.py:68–92`.** 자체 capture의 success·240행·505차원, single-hand task 계약과 정확한 NPZ field/shape, bool mask, 유한 floating 입력/행동, 정규화 범위와 비활성 손의 정확한0을 검사한다. dataset 세 파일의 SHA를 기록하고 읽는 동안 변화가 없는지 확인한다. 이 loader가 native 접촉을 재계산하거나 report의 진실성을 새로 인증하는 것은 아니므로 실제 재수집 결과·보존 감사를 함께 사용해야 한다.
4. **선택 Actor만 BC 학습 — `imitation.py:105–159`, `train_imitation.py:39–57`.** 선택 encoder/head만 별도 Adam에 넣고 `tanh` 정규화 행동 MSE를 학습한다. Critic·상대 손·std는 BC optimizer에 포함하지 않는다. 초기 std.02는 명시 설정이며 전후 model key 비교로 비선택 변경을 거부한다. 전체240행 오차를100 step 간격과 마지막 budget에서 측정하여 stopping/fit 결과를 기록한다. `training_mse`, 최대 절댓값 오차, `converged`는 학습 자료 fit이고 native 성공·일반화 지표가 아니다.
5. **PPO와 분리된 초기화 형식 — `imitation.py:171–214`.** BC payload는 `guitar_learning.imitation.v1`이며 PPO identity·updates·optimizer를 만들지 않는다. atomic no-overwrite 저장을 사용한다. 적용 전 schema·역할·전체 architecture/계약과 유한 model key/shape/dtype·파일 불변을 확인하고, 실제 복사는 선택 encoder/head 및 선택 std만 수행한다. payload에 저장된 무작위 Critic·상대 손은 PPO 모델에 전달하지 않는다.
6. **fresh PPO 순서·strict resume — `train_imitation_ppo.py:53–91`.** 초기화 파일을 실행 입력에 pin하고 예상 SHA를 재검사한다. 새 실행은 BC Actor/std를 적용한 뒤 기존 PPO trainer의 새 optimizer를 생성한다. Critic과 업데이트 카운터는 fresh 모델/기존 trainer의 초기값이다. 기존 specialist checkpoint 전달을 동시에 받지 않는다. `--resume`에서는 BC 적용을 건너뛰고 기존 PPO strict load가 모델·optimizer/RNG를 복원한다. 일시 Pool/trainer/pin 바인딩은 정상 종료·중단 때 복원된다. BC를 PPO 업데이트로 위장하지 않는다.
7. **구분된 실제 정책 평가 — `evaluate_imitation.py:34–77`.** BC 모드에는 자체 Actor 초기화 검증, PPO 모드에는 기존 전체 identity strict load를 사용한다. 같은 profile 환경과 `parallel.FIELDS` 순서·deterministic action으로 실행하고 매 행동 직전 입력/행동 및 원240Hz 측정을 남긴다. 다음 reset에서도 계약을 대조한다. `completed`는 요청한 episode 수가 끝났다는 뜻이므로 physical failure·stage success·timeline reason을 별도로 확인해야 한다. 두 동일 prepared-start 반복은 새 분포·곡의 일반화 검사가 아니다.
8. **확장된 입력 보존 — `imitation_io.py:10–24`.** 기존 prepared 입력, 활성 G Python·stability Python, song bundle 전부와 `tab2body/full/events.py`, 명시 dataset/초기화/checkpoint를 pin한다. 종료 전 변화는 예외로 처리한다. 앞선 작은 probe pin 목록을 이번 범위와 같다고 설명하지 않는다. 최종 native lifecycle·기존 파일/봉인 보존 감사는 별도로 필요하다.

## 결과 해석과 진행 조건

- BC의 `report.completed`와 `ppo_updates=0`는 BC 예산 실행의 완료다. fit이 목표 MSE에 도달했는지는 `fit.converged`에서 읽고, 실제 기능은 native 평가로 판단한다.
- 현재 구현은 LH 실제 contact/50ms hold와 RH 지정 현·방향의 기하 cross를 다룬다. LH 하중 비의존·상완 지지/V3 정밀 요구, 악보 타이밍·음향·사람 motion 유사성·다른 목표 일반화·양손 결합은 별도다.
- PPO는 root가 BC native 성취를 확인한 손에서만 진행하고, 마지막 policy가 기능을 잃으면 그 실패를 보존해야 한다. 비용1·actor_lr1e−5·N2/H240·최대24업데이트/soft wall1800초는 이번 명시 예산이며 수렴을 보장하지 않는다.
- 본 보고서는 BC 초기화/실제 정책 평가/PPO 완료 또는 최종 source seal의 성과 판정까지 포함하지 않는다. 이후 실제 결과를 정량적으로 검수해야 한다.
