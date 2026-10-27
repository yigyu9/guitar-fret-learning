# 실제 교사·BC·왼손 정책 평가 증거 검수 v1

요약 판정: **문제없음**. finalized native 8개 실행, 양손 BC, 왼손 정책 평가·gate·별도 PPO 준비 설정 및 현재 코드 SHA 사이의 모순을 발견하지 않았다. 원 `review_v1.md`는 수정하지 않았다. 이 검수에서는 native/BC/PPO를 새로 실행하지 않았으며 실행 중인 프로세스도 변경하지 않았다. 기존 결과를 읽고 체크섬·모델 상태 및 순수 파일 기반 gate 검증만 수행했다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음.

## 실제 결과 대조

`left_native_probe_v2/result.json`과 `right_native_probe_v1/result.json`의 case 배열을 각 하위 `result.json`과 대조해 모두 동일함을 확인했다. 8개 모두 420tick·7초 완주, 물리 실패 없음, 원 물리 flags 정상, 금지 호출·missing source pin·cleanup 오류 없음, 소비 입력 SHA 불변이다. 각 손의 policy/zero 기준선은 품질 실패이며 나머지 두 후보는 해당 손 원 품질 성공이다.

| 교사 후보 | 개입 행 | 확인한 역할별 결과 |
| --- | --- | --- |
| LH return_reference | 158 | clean audible 1.0, release 완료, release_late_s 0.1873833333 |
| LH return_reference_open_flex | 158 | clean audible 1.0, release 완료, release_late_s 0.2540500000 |
| RH hold_last_command | 168 | accepted 1, extra/wrong/unprepared 0, recovered true |
| RH hold_applied_target | 168 | accepted 1, extra/wrong/unprepared 0, recovered true |

이는 소수 교사 후보의 실제 성공이며 학습 정책 성공과 합산하지 않는다.

양쪽 `*_bc_v1/report.json`의 fit과 실제 `actor_initialization.pt`의 training 기록·모델 SHA가 일치한다. 각 1000step, LR 0.0001, 그룹별 batch 120, PPO update 0이다. LH 국소/보존 행은 158/262, RH는 168/252다. 최종 국소 MSE는 각각 2.555494029e-5, 1.105551490e-7이며 phase README의 반올림 수치와 일치한다.

실제 BC 모델을 원 checkpoint와 비교했다. 각 모델에서 선택 손 actor의 16개 state 항목만 변경됐고 나머지 38개 항목(critic·비활성 actor·std·buffer 포함)은 정확히 동일하다. 자료 manifest·원 checkpoint SHA·전체 architecture도 일치한다. `checkpoint_000024.pt`라는 실행 내 파일명과 누적 optimizer counter는 별개이며, 실제 원 모델의 누적 `updates`는 LH 29/RH 27이다. BC 산출물은 명시적 `guitar_learning.local_skill_bc.v1` 형식으로 PPO 재개 모델과 구분된다.

## 왼손 정책 평가와 준비 설정

`left_policy_evaluation_v1/musical_quality_result.json`·`evaluation_metrics.json`·`local_skill_gate.json`·`left_gate_validation_v1.json`을 대조했다.

- 교사 없는 결정적 정책 4회가 각각 valid/timeline_complete·420tick·7초이며, 품질 성공 4/4·timing-only 성공 4/4·물리 실패 0이다.
- 네 실행 모두 clean audible fraction 1.0, release 완료, `release_late_s=0.1790500000`, 최종 release clear dwell 2.3666666667초다. timing의 safety_invalidated는 false다.
- 평가 모델 SHA는 `1ef3f6ba8e73941ded9864fe8b1c8ac85dfce1b880d21274bb1539d83dd8f697`이며 BC report·실제 BC 파일·gate·평가 지표에서 일치한다.
- gate의 세 실제 artifact SHA, dataset manifest의 모든 파일 SHA, 원 모델 SHA 및 BC 전체 계약 digest가 모두 일치한다. `passed=true`가 실제 결과에 뒷받침된다.
- `left_bc_evaluation_settings_v1.json`은 보존됐다. 별도 `left_bc_ppo_ready_settings_v1.json`의 차이는 gate 경로 추가와 device CPU→CUDA뿐이다. 역할·망·목표·타이밍·품질 계약·BC 파일은 동일하다.
- 검수자가 준비 설정을 현행 parser로 읽고 `train.validate_gate`를 독립적으로 실행해 통과 및 proof 4개를 확인했다. 이 함수는 파일 검증만 수행하며 native나 PPO를 시작하지 않는다.

이 결과는 동일 단음·동일 준비 시작의 결정적 반복 평가다. 다양한 음·초기 상태 일반화나 양손 결합, 실제 음향 성공을 인증하지 않는다.

## 소스·입력 보존

현재 파일과 보관본 SHA를 직접 다시 계산했다.

| 대상 | 검사 개수 | 불일치 |
| --- | --- | --- |
| learning_source_pins_v1.json | 11 | 0 |
| probe_inputs_v3.json의 코드 | 3 | 0 |
| LH native 소비 입력 | 1566 | 0 |
| RH native 소비 입력 | 1566 | 0 |
| LH 정책 평가 소비 입력 | 1658 | 0 |
| 기존 장기 실행 source pins | 169 | 0 |
| 기존 장기 실행 execution pins | 6 | 0 |
| 기존 curriculum execution pins | 15 | 0 |

검수 시점에 RH 정책 평가는 진행 중이며 최종 gate는 없었다. 새 PPO도 시작하지 않았다. phase README 초안의 LH 진행 중/RH 미실행 표시는 이전 시점 설명이므로 최종 문서에서는 실제 완료 파일에 맞춰 갱신할 예정이다. 이 기록은 이후 RH 결과나 후속 PPO 성과를 미리 인증하지 않는다.
