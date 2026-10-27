# 현행 음악 품질 로그의 의미와 해석 제한

2026-10-18. 읽기 전용 감사다. 학습·보상·판정·기존 로그를 변경하거나 새 실험을 실행하지 않았다. 최신 `train_musical_quality` 경로의 실제 손별 1업데이트와 후속 결정적 평가를 기준으로 한다. 이 문서의 추가 기록 제안은 구현한 기능이 아니다.

## 실제 실행과 분모

유효 학습은 [LH train v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/report.json:1), [RH train v1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1/report.json:1)다. 각각 1환경×420전이×1업데이트, 7초의 확률적 행동 episode 1개다. `left_native_train_v1`은 Ninja 확장 초기화 실패로 0전이이므로 음악 성공률 분모에서 제외하고 인프라 실패로 보존한다. 후속 결정적 평가는 손별 각각 1 episode다. 학습 수집과 결정적 평가를 합쳐 동일 조건의 독립 성공률처럼 표현하지 않는다.

| 후속 결정적 평가 | LH | RH |
| --- | --- | --- |
| 데이터 유효·시간표 완주 | 1/1 | 1/1 |
| 물리 안전 무효화 | 없음 | 없음 |
| timing-only 단계 달성 | 1/1 | 1/1 |
| 새 음악 품질 단계 성공 | 0/1 | 0/1 |
| 담당 손 핵심 결과 | clean audible 100%, 해제 미완료, late 접촉 2.5478초 | 준비 후 목표 통과 1회, 추가 목표 통과 1회, 반대 방향 통과 1회 |
| joint strict matched50 / matched100 | 0 / 0 | 0 / 0 |

근거: [LH 평가 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_eval_v1/musical_quality_result.json:1), [RH 평가 원자료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_eval_v1/musical_quality_result.json:1). 같은 폴더의 `result.json`과 `musical_quality_result.json`은 같은 평가를 다른 wrapper schema로 기록한 것이므로 서로 다른 시행이 아니다. 단일 업데이트로 수렴·장기 개선·일반화를 판단할 수 없다.

## 성공이라는 이름을 분리해야 하는 이유

- `report.completed`는 정상 실행·감사 완료이며 요청한 업데이트 수 이전의 정상 wall budget 종료도 포함할 수 있다. episode `valid`는 수집 자료의 유효성이다. 음악 성공을 뜻하지 않는다. 수집기의 `completed_episodes`에는 reward/cost/길이/종료 이유만 있으며 손별 품질 성공이 없다. [수집 코드](/home/ajou/yigyu/3/guitar_learning/parallel.py:375).
- `timing.timing_only_stage_success`와 `musical_quality.timing_achievement`는 넓은 시간창의 기존 손별 달성이다. 새 환경은 `timing.stage_success`와 `specialist.stage_success`를 **품질 조건을 적용한 성공**으로 덮어쓴다. 따라서 현재 `timing_report.successful_episodes`도 timing-only 성공 수가 아니다. [환경](/home/ajou/yigyu/3/guitar_learning/musical_quality_environment.py:39), [보고서 집계](/home/ajou/yigyu/3/guitar_learning/train_timing.py:80).
- `musical_quality.stage_success`는 안전하게 전체 horizon을 마친 timing 달성에 손별 조건을 더한다. 현 stage1 LH는 audible clean 비율 40% 이상과 현재 해제 완료, RH는 accepted 통과·현재 회복과 unprepared/extra/기타 blocked/잘못된 통과 0을 요구한다. LH가 항상 audible 100%를 요구하는 단계는 아니다. 중간 tick의 `stage_success=False`는 아직 완주하지 않았다는 뜻일 수도 있어 provisional과 구분한다. [품질 성공식](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:149).
- `music.matched50/100`은 양손 조건이 필요한 joint 판정이다. 현재는 clean 압현과 준비 gate를 거친 타현이 입력되므로 frozen 옛 판정과 완전히 같은 측정이라고 설명하면 안 된다. 손별 전문가의 반대손 비활성을 감안해야 한다. [측정 교체](/home/ajou/yigyu/3/guitar_learning/task_measurement_v2.py:16).
- `specialist.skill.held/crossed/first_success`는 계승한 하위 과제 이력이다. 새 품질 성공이나 현재 음악 정밀도를 대체하지 않는다.

## 누적값과 구간값

| 필드 | 실제 의미와 올바른 집계 |
| --- | --- |
| tick reward, cost, reward_terms | 한 60Hz 제어 구간 안의 실제 240Hz 기여 합. episode 안에서 합산 가능 |
| wrong_press_s / missing_press_s / clean_audible_s / release_late_s / dropout·통과 횟수 | reset 후 누적값. episode 마지막 값 또는 같은 episode 안의 차분 사용 |
| release_clear_dwell_s / recovery_dwell_s | **현재** 연속 구간 길이. 재접촉·접근 시 감소/초기화 가능 |
| ready / ready_dwell_s | ready는 과거 획득 latch, dwell은 최장 준비 구간. 현재 준비 상태와 다름 |
| recovered / ever_recovered | 현재 회복 상태 / 과거 회복 이력 |
| fretting_state의 bool과 status | 마지막 측정 상태. episode 비율이나 오류 횟수가 아님 |
| best_abs_error_s | reset 후 최솟값. None은 유효한 오차 표본이 없다는 뜻이며 0으로 대체하면 안 됨 |

품질 시간은 실제 연속 240Hz를 검사한다. wrong은 정책 시작~음 종료의 wrong 상태 점유, missing은 audible 구간의 missing 점유, clean audible은 양 끝 표본이 모두 clean인 구간만 적분한다. `release_late_s`는 음 종료+grace 이후 목표현 접촉 점유 시간이며 첫 해제 시각까지의 단일 지연시간과 동치가 아니다. [적분식](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:81), [준비·회복 요약](/home/ajou/yigyu/3/guitar_learning/strike_quality.py:144).

실제 LH 학습의 terminal `release_late_s`는 **2.5478초**다. 이를 420개 transition에서 매번 더하면 **196.0134**가 된다. 후자는 같은 누적값을 반복 더한 오류다. episode 경계를 넘겨 차분하거나 여러 worker의 마지막 행을 하나의 episode로 취급하지 않는다.

## 담당 손·후보·시간 오차

RH 평가의 LH `missing_press_s=0.2322`, `clean_audible_fraction=0`은 비활성 왼손의 진단이다. RH 학습 실패 사유나 LH 학습 성공률 분모가 아니다. 반대로 LH 평가의 strike ready=False도 비활성 오른손 진단이다. 품질 벌점·성공식은 역할별로 적용한다. 비활성 손의 원자료는 보존하되 주 화면에서는 N/A로 명시하는 편이 맞다. [역할별 보상](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:128), [성공식](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:153).

`positive_target_candidate`는 원 접촉 후보, `clean_target_candidate`는 새 veto를 적용한 후보다. 현재 `music.targets[*].candidate`와 compact의 `fret_candidates`는 clean이다. 원 후보는 evidence와 품질 스냅샷에 남는다. `incidental_other_string=True`나 `uncertain=True`가 `status=correct`, clean=True와 공존할 수 있으며 이 두 진단을 오압현 횟수로 합산하면 안 된다. LH 평가 최종 상태가 실제 그 예다. [후보 교체](/home/ajou/yigyu/3/guitar_learning/task_measurement_v2.py:16), [compact](/home/ajou/yigyu/3/guitar_learning/parallel.py:53).

LH `best_abs_error_s=0`은 후보가 press 시각에 존재한 표본의 오차 최솟값이다. 일찍 접촉해 계속 유지해도 0이 되므로 **손의 도착 오차 0**이라는 뜻이 아니다. 현재 LH timing 첫 성공 시각 3.595833초도 완화된 dwell을 채운 시각이며 접촉 시작 시각이 아니다. [precision 호출](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:139).

RH 평가의 accepted `1010:2`는 policy 4.2051353157초, 목표 대비 **+85.135316ms**다. `first_success_s=4.2083333333`은 240Hz 표본 끝의 달성 stamp이므로 정확한 선분 교차 시각과 다르다. 현재 best도 이 accepted 통과의 오차다. extra `1354:2`는 준비 gate 이후 blocked되어 timing.crossings/best에 들어가지 않는다. 반대 방향 `1071:2`는 timing.wrong_crossings=1로 남는다. 따라서 timing.crossings만 보면 추가 타현을 놓친다. 이 accepted 기하 오차는 독립 100ms 조건에는 들지만 50ms에는 들지 않으며, joint matched100=0은 비활성 LH 조건까지 포함한 별도 판정이다. [타이밍 ledger](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:167), [추가 통과 gate](/home/ajou/yigyu/3/guitar_learning/strike_quality.py:116).

## 표본 빈도와 보상 해석

학습 compact의 stability는 각 제어 tick에서 **마지막 substep의** `last_safety`만 기록한다. 그 60Hz 열의 최대값·접촉률을 모든 240Hz 표본의 최대값·접촉률이라고 부르면 안 된다. 반면 cost 및 품질 누적은 실제 240Hz 기여를 포함한다. 현재 학습은 episode 첫 tick의 raw 4개 표본만 저장하며, 결정적 평가는 모든 tick의 physics 측정을 저장한다. 학습 endpoint 자료로 보이지 않는 substep 극값을 복원할 수 없다. [compact](/home/ajou/yigyu/3/guitar_learning/parallel.py:45), [raw 저장 조건](/home/ajou/yigyu/3/guitar_learning/parallel.py:137), [평가 저장](/home/ajou/yigyu/3/guitar_learning/evaluate_timing.py:58).

보상 항은 보정까지 묶어 해석해야 한다. 실제 LH 학습의 timing_hold는 +2.7044, post-note 보정은 −1이므로 순 hold는 +1.7044다. timing_success +1은 correction −1로 상쇄되고 audible_success +1이 대체한다. 따라서 양성 항만 모아 “성공 보너스 2회”라고 설명하면 틀린다. post-note hold는 상쇄하지만 pre-onset 준비 접촉 보상은 남으므로 이 총보상으로 정확한 연주 시간 준수를 증명할 수 없다. [보정식](/home/ajou/yigyu/3/guitar_learning/musical_quality_environment.py:65), [실제 항별 합](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/musical_quality_report.json:1).

추가 타현의 blocked ID와 extra/unprepared 집합은 중복될 수 있다. 서로 다른 오류의 수를 내려면 ID와 reason을 기준으로 구분한다. 실제 RH 평가에서는 extra `1354:2` 한 건이 blocked에도 나타난 것이며, 별개의 반대 방향 `1071:2` 한 건과 구분한다.

## 실제 PPO 진단의 의미

| 업데이트 0 | LH | RH |
| --- | --- | --- |
| 최종 analytic KL | 0.0138914 | 0.0175723 |
| 최대 시도 KL | 1.1593204 | 0.0434493 |
| retry 수 | 2 | 1 |
| 설정 actor LR → 실제 LR | 1e-5 → 6.25e-7 | 1e-5 → 2.5e-6 |
| 기록 actor_grad_norm | 359.9896 | 72.3015 |
| collection / update 초 | 65.9102 / 0.1585 | 68.8437 / 0.1603 |

근거: [LH update](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/update_000000.json:1), [RH update](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1/update_000000.json:1). LR 축소·큰 KL 시도는 실제 기록이나 한 번의 업데이트만으로 원인이나 장기 학습 실패를 확정할 수 없다. collection 시간에는 시뮬레이션뿐 아니라 추론·통신·기록·reset 등이 포함되며 물리 연산만의 시간은 아니다.

`actor_loss`, reward/cost value loss는 각각 마지막 minibatch 값이다. `actor_grad_norm`도 마지막 actor minibatch의 **clip 전** norm이며 현재 전체 업데이트 평균이나 clip 후 norm이 아니다. analytic KL은 최종 full rollout 평가, max_attempted_kl은 거절된 시도를 포함한다. 현재 critic은 MSE이며 value clipping은 구현되어 있지 않다. [PPO](/home/ajou/yigyu/3/guitar_learning/ppo.py:152).

업데이트 파일에는 품질별 episode 진단이 들어가지 않는다. `musical_quality_report.json`은 run 종료 뒤 전체 compact 로그를 읽어 만든다. `last_measured_quality`는 마지막으로 순회한 worker의 측정이며 다중 worker 평균이 아니다. 현재 N1에서는 혼동이 적지만 미래 N>1 통합에 주의해야 한다. 첫 rollout tensor는 처음 업데이트만 저장한다. [종료 후 집계](/home/ajou/yigyu/3/guitar_learning/train_musical_quality.py:62), [업데이트 저장](/home/ajou/yigyu/3/guitar_learning/train_parallel.py:169).

## 추가·축소 권고의 우선순위

**P0 — 현재 의미를 정확하게 표시.** 실행 완료/물리 안전/timing-only/품질 성공/joint strict를 별도 열로 둔다. 역할·episode 수·시간 구간·240Hz 적분 또는 60Hz endpoint 여부·후보 버전을 함께 표시한다. 누적값은 terminal 집계하고 reward 보정은 순항으로 설명한다. 이것은 새 실험 없이 현재 로그 해석부터 바로 적용할 수 있다.

**P1 — 학습 원인을 판단할 때 필요한 추가 요약.** 업데이트별 담당 손의 실패 이유·audible clean·wrong/missing 시간·해제 지연 점유/실제 첫 clear·accepted 첫 signed 오차·extra/wrong/recovery를 보상·비용과 같이 기록하는 것이 우선이다. LH 도착 시각은 best=0 대신 별도 첫 접촉/연속 접촉 시각을 사용한다. RH는 native eligible·prepared accepted·extra를 별개 ID로 남긴다.

**P1 — 최적화 진단.** ratio clip fraction, 활성 채널 entropy/std와 tanh 포화율, 보상/비용 advantage의 결합·정규화 전 규모, reward/cost critic의 target/value 범위와 explained variance·TD 오차가 현재 누락되어 있다. minibatch loss/norm의 평균·최대와 clip 후 norm도 마지막 값만 보는 제한을 줄인다. cost target 분산이 거의 0이면 explained variance는 N/A로 표시해야 한다. 현재 objective에 없는 value-clip 비율은 제안하지 않는다. 비활성 채널은 0행동·고정 log_std placeholder이므로 활성 LH33/RH6 채널만으로 행동 통계를 낸다. [활성 분포](/home/ajou/yigyu/3/guitar_learning/specialist_policy.py:80), [advantage 결합](/home/ajou/yigyu/3/guitar_learning/ppo.py:146).

**P2 — 화면 중복 축소, 감사 원자료 보존.** specialist/timing/quality에 반복된 성공과 긴 feature_diagnostics를 매 tick 주요 진행표에 전부 노출할 필요는 없다. 원자료는 보존하고 실패/변화 시점의 상세 근거를 연결한다. `goal_distance_m`은 손가락 body 원점의 거리 proxy이며 압력·실제 clean·음향 성공을 대체하지 않는다. 전체105축의 min/max도 활성 관절 추종 오차를 대체하지 않는다. 코드·보상·학습 변경은 이 감사 범위가 아니다.

## 확인한 입력 SHA256

아래는 이번 감사에서 읽은 핵심 파일의 해시다. 문서 작성 전후 이 파일들의 SHA 변화는 0이다. 기존 자료의 모든 파일을 전수 해시한 주장은 아니다.

| 파일 | SHA256 |
| --- | --- |
| [guitar_learning/train_musical_quality.py](/home/ajou/yigyu/3/guitar_learning/train_musical_quality.py) | `d6b4a00e2e375e9b7bd52c4d957101d20a7c864c10841271eb0b83072c9a1c7a` |
| [guitar_learning/musical_quality_environment.py](/home/ajou/yigyu/3/guitar_learning/musical_quality_environment.py) | `2a795bc35a738746eea58529b3e8d207646f6a5ce739214c5505318714b19009` |
| [guitar_learning/musical_quality.py](/home/ajou/yigyu/3/guitar_learning/musical_quality.py) | `44bd74c25dadd066c3fbf9683181def683e1bfc4d71ac77ddafb5ac7b036c344` |
| [guitar_learning/task_measurement_v2.py](/home/ajou/yigyu/3/guitar_learning/task_measurement_v2.py) | `a35299c72bacdd3514d7c66ddfdacccf1124a4fc6f3d050c3a33e63321efbc15` |
| [guitar_learning/timing_curriculum.py](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py) | `1e221cc05f7ab80e9b56a95b076a3b79c6a23e1bbc8204e7c91bf7e336236806` |
| [guitar_learning/strike_quality.py](/home/ajou/yigyu/3/guitar_learning/strike_quality.py) | `34419e36125110bee157f6188f9183f4204423acd7b037c8954a0e3368a218b5` |
| [guitar_learning/parallel.py](/home/ajou/yigyu/3/guitar_learning/parallel.py) | `a267340e7b75c3e93a752de2a8c57aeaf4e16559d820ec686d232a6232514d14` |
| [guitar_learning/ppo.py](/home/ajou/yigyu/3/guitar_learning/ppo.py) | `5f834698e88baaae45de616d9681fe82bbcce2dbdd1ec957be9328f5e8065735` |
| [guitar_learning/train_parallel.py](/home/ajou/yigyu/3/guitar_learning/train_parallel.py) | `b6eb831ef91bb1a5dac605e42d40bf27b070081233f5e0d5952a74a62a147c01` |
| [guitar_learning/train_timing.py](/home/ajou/yigyu/3/guitar_learning/train_timing.py) | `6822fdbd1a05755fc67fbd1a23b6a297f97e44514184930f1b66c90e80bb836c` |
| [guitar_learning/evaluate_timing.py](/home/ajou/yigyu/3/guitar_learning/evaluate_timing.py) | `e958f7b9af2b41d09a704784c4e957a762038d0c5381f5172c28be09618ff936` |
| [guitar_learning/specialist_policy.py](/home/ajou/yigyu/3/guitar_learning/specialist_policy.py) | `e71b8444b0ff8ab902ab57acebb9eb8933f130bca8932fdfa0668d81b6d4c03d` |
| [docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/update_000000.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/update_000000.json) | `908d360bbf28ba0cf7ee1cb18eeeadae79a03ed4820c32b935e29df912a85b94` |
| [docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1/update_000000.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1/update_000000.json) | `39695331f288b5590e9150835124deaffca7baddfc52ab88f8007d8bbb45c536` |
| [docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/musical_quality_report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_train_v2/musical_quality_report.json) | `1c950599a4e194d84d75f1a9756bd6d489a76d8629308a1c0e02a858b8f0377d` |
| [docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1/musical_quality_report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_train_v1/musical_quality_report.json) | `8efda19b908735f6c9a88f59f004b23c2c464cde4cf1f6c0defb27eafc3a398c` |
| [docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_eval_v1/musical_quality_result.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/left_native_eval_v1/musical_quality_result.json) | `53d16b3a75d781533f92716ed2288fb13aa906a685feed05cd411a27bf28e960` |
| [docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_eval_v1/musical_quality_result.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/right_native_eval_v1/musical_quality_result.json) | `05434e90b99bb5a572b1b51c8a4ffa791cdaaeb975e7810414aebd0c3b34949d` |
