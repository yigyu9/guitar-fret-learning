# 현재 학습 로그의 유효성 점검

분석일: 2026-10-18. 현행 `train_musical_quality`와 기존 실제 실행을 읽기 전용으로 조사했다. 새 학습·물리 실행·로깅 코드 변경·기존 기록 삭제는 하지 않았다.

현재 기록은 보상 계산, 물리 실패, 정책 업데이트와 재개를 확인하는 데 유효하다. 그러나 음악 목표별 개선을 학습 중 비교하기 어렵고, 상세 진단과 중복 정보가 매 제어 단계에 섞여 있다. **기록을 일괄 줄이기보다 역할별 학습 요약을 먼저 추가하고, 반복 상세 정보를 별도 진단 기록으로 옮기는 것이 적절하다.**

## 1. 확인한 실제 실행과 수치 일관성

기준은 [최신 품질 보완 실행](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_musical_quality_v1/README.md)의 `left_native_train_v2`와 `right_native_train_v1`이다. 각각 1환경·420전이·7초·PPO 1회다. `left_native_train_v1`은 native 장면 생성 전 Ninja 초기화 실패이며, 물리 실패나 학습 에피소드로 세지 않는다.

[자동 대조 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/metrics_audit_v1.json)에서 다음을 확인했다.

- 학습에 반영된 전이 수와 저장된 전이 수: 양쪽 모두 420으로 일치.
- 전이 보상과 세부 보상 합계의 최대 차이: 왼손 `5.42e-8`, 오른손 `4.69e-8`. 저장 보상의 float32 반올림 범위다.
- 에피소드 보상 합계 차이: 최대 `1.34e-15`. 비용 합계 차이: 0.
- 최종 품질 요약과 에피소드의 품질 기록, 중첩된 타이밍 기록이 일치.
- 60Hz 제어 시각과 단계당 4개의 240Hz 물리 진행이 일치.
- 점검에 사용한 핵심 소스 7개는 각 실행의 `inputs_before.json` SHA와 일치.

이는 이 두 실행의 기록 일관성 검사다. 장기 수렴·여러 목표·중간 실패의 모든 경우를 검증했다는 뜻은 아니다.

| 학습 중 마지막 에피소드 | 왼손 | 오른손 |
| --- | --- | --- |
| 실행 정상 완료 | True | True |
| 타이밍만의 기존 달성 | 1/1 | 1/1 |
| 현행 음악 품질 성공 | 0/1 | 0/1 |
| 로그로 확인되는 남은 문제 | 음 구간 clean 유지율 100%지만 해제하지 않음. 해제 유예 이후 접촉 잔류 2.5478초 | 목표 타현 1회 후 추가 타현 1회, 타이밍 판정의 wrong 통과 1회 |

따라서 실행 완료나 누적 보상이 높다는 사실만 보고 연주를 성공했다고 해석하면 안 된다. 오른손 실행의 왼손 `missing_press_s=0.2322`와 clean 유지율 0은 비활성 손의 진단이며, 오른손 학습의 압현 실패로 집계하지 않는다.

## 2. 유지해야 하는 기록

| 기록 | 판단과 용도 |
| --- | --- |
| `settings.json`, `training_contract.json`, 입력 SHA, 초기화/이전 기록 | 필수. 목표, 단계 허용치, 보상, 물리·관측·행동 계약과 모델 출처가 달라진 실행을 구분한다. |
| `update_*.json`의 KL, 최대 시도 KL, 재시도, 학습률, cost weight | 필수. 업데이트가 거부되거나 학습률이 줄어드는지를 확인한다. |
| 전이 보상 항목·비용·종료 원인 | 필수 근거. 어떤 행동에 보상/벌점이 실제 부여됐는지 검증할 수 있다. 일상 모니터링에는 업데이트별 합계도 필요하다. |
| 품질별 지속시간·이벤트 수·최종 성공 | 필수. 유지·해제·추가 타현 등 보상 합계만으로 보이지 않는 실패를 구분한다. |
| heartbeat, `status.json`, `resources.jsonl`, `events.jsonl` | 유지. 진행 정지, worker 대기, 메모리 부족과 단계를 구분한다. 현재 용량상 우선 축소 대상이 아니다. |
| 모델/optimizer/RNG 체크포인트와 실패 복구 정보 | 유지. 재개는 새 native 에피소드에서 시작하며 물리 궤적 중간부터의 exact 재현은 아니다. |
| 입력 무변경·금지 호출·sim 생성/종료 감사 | 유지. 자유 기타 조건과 시뮬레이터 재사용을 확인하는 별도 근거다. |

기존 세부 기록은 이번 보상 합계·성공 판정 검증에 실제로 사용됐다. 과거 증거를 삭제할 이유는 없다.

## 3. 지표를 읽을 때 주의할 구체적인 의미

1. **완료·안전·성공은 서로 다르다.** `report.completed`는 실행/감사 완료다. 정상 wall budget 종료도 포함할 수 있다. 에피소드 `timeline_complete`는 악보 시간표 완주다. 현행 `musical_quality.stage_success`가 해당 손의 품질을 포함한 단계 성공이다. stage 자체도 완화된 기준이며 실제 압력·음향·전곡 성공을 뜻하지 않는다.
2. **매 행의 누적 지표를 더하지 않는다.** `wrong_press_s`, `missing_press_s`, `release_late_s`, 타현 counts 등은 에피소드 누적이다. 마지막 값 또는 같은 에피소드 내 차분을 사용한다. 예를 들어 왼손 `release_late_s`의 최종 값은 2.5478초인데 420행을 합하면 196.0134가 된다. 반면 `reward_terms`와 `cost`는 그 제어 단계의 증분이므로 합산한다.
3. **손별·단계별 분모를 고정한다.** 완료 에피소드, 안전 실패, 시간 제한, 미완료 수를 나눈다. 완료 0회면 성공률은 미정으로 표시한다. 상대 손과 joint 음악 점수는 별도다. stage0/1과 50/100ms 기준을 섞어 하나의 성공률로 만들지 않는다.
4. **일반 `music`와 현행 타이밍의 wrong 수는 다른 판정이다.** 실제 오른손 끝 값은 `music.wrong_crossings=2`, `timing.wrong_crossings=1`, quality extra=1이다. 서로 더해 오류 4회라고 할 수 없다. 이벤트 ID와 판정별 이유를 함께 사용한다.
5. **학습 전이 로그는 60Hz 요약이다.** 실제 음악 비용·품질 통합은 240Hz지만 `stability`와 순간 `fretting_state`는 제어 단계 끝 표본이다. 그 끝 표본들의 최대 편차/접촉률을 전체 240Hz 최대/접촉률이라고 부르면 안 된다. `failure_reasons`는 네 하위 물리 단계의 실패를 모으므로 마지막 표본에 원인이 없어도 종료 원인이 남을 수 있다. 필요한 극값·접촉 시간은 하위 표본에서 따로 축약해야 한다.
6. **현재 loss와 grad norm은 업데이트 전체 평균이 아니다.** [PPO 반환부](/home/ajou/yigyu/3/guitar_learning/ppo.py:195)는 마지막 최적화 미니배치의 actor/value loss와 actor grad norm을 반환한다. grad norm은 clipping 전 값이다. 큰 값만으로 적용된 업데이트가 컸다고 단정하지 않는다. analytic KL은 최종 전체 rollout 분포 차이이고 max attempted KL은 복원된 거부 시도도 포함한다.
7. **best 타이밍 오차는 정의를 함께 본다.** 왼손 값은 후보 접촉 표본 중 최소 오차라 최초 도착 오차가 아니다. 현재 오른손 타이밍에는 새 gate를 통과해 받아들여진 통과가 들어가므로 raw 추가 타현을 best 값에서 평가하지 못한다. 첫 수락 이벤트의 부호 있는 오차와 추가/오류 수를 함께 제시한다.
8. `goal_distance_m`는 손끝 기준의 기하 거리다. 접촉 clean 여부, 압력이나 타현 성공을 대신하지 않는다. raw 접촉 양성값도 보정된 힘 N으로 해석하지 않는다.

현재 `timing_report.successful_episodes`도 품질 gate가 반영된 `timing.stage_success`를 센다. 파일 이름만 보고 timing-only 성공률로 해석하지 않는다. timing-only 비교에는 명시적 `timing_only_stage_success`를 사용한다. 과거 skill의 held/crossed 목록과 first-success 기록 역시 현행 최종 품질 성공을 대체하지 않는다.

## 4. 줄이거나 진단용으로 옮길 기록

- 타이밍 설정·판정 설명·scope 문자열·타현 preparation 계약을 매 제어 단계 반복하기보다 실행 계약에 한 번 기록한다.
- `timing`과 `specialist.timing`의 같은 사본은 일상 기록에서 한 곳을 정본으로 정할 수 있다. 최종 에피소드에도 반복 사본이 있다. 기존 호환 보고서를 유지할 경우 파일 경로·SHA로 정본을 참조하도록 바꿀 수 있다.
- 모든 접촉 feature의 좌표·body 이름·이유·증거 ID를 매 tick 복사하는 것은 상세 진단이다. 일상 학습에는 correct/wrong/missing 및 시간·이벤트 수, 선택된 이유만 남기고, 전체 feature는 판정 전환·실패 주변 또는 별도 진단 에피소드에 남기는 편이 적절하다.
- 39축 전체 행동과 단순 min/max, PID·peak RSS를 매 tick 중복 저장하는 부분은 축소 가능하다. 일상 기록에는 활성 손 행동 크기/포화·변화 요약과 저주기 자원 기록을 남긴다. 실제 자세·목표 추종을 진단할 때만 관절별 상세 기록을 켠다.
- 최초 `rollout_first.pt`는 입력/likelihood 검증에 유용하나 매 장기 실행의 필수 상시 기록으로 볼 필요는 없다. 형식 검증 실행 또는 진단 모드에 적합하다.
- 마지막 주기 체크포인트와 `final.pt`는 실질 학습 상태가 중복될 수 있다. 최종 정본 하나와 이를 가리키는 manifest로 정리할 수 있다. optimizer/RNG가 포함된 복구용 체크포인트 자체는 없애지 않는다.
- 240Hz 전체 native 상태·접촉·관측을 담는 평가 trace는 재현/정밀 진단용으로 가치가 크다. 일반 학습 스칼라 로그와 저장 예산을 분리한다.

학습은 매 에피소드의 첫 제어 단계에 네 물리 표본을 담은 별도 raw 파일도 남긴다. 이번 각 420행 중 raw 참조는 1개다. 따라서 일반 전이 요약만으로 7초 전체의 원시 접촉을 복원할 수 없다.

현재 specialist → timing → preparation → quality의 종료 요약은 같은 전이 gzip을 각각 다시 읽는다. 하나의 스트리밍 집계로 줄일 여지는 있지만, 먼저 의미와 실패 처리 일관성을 보존해야 한다.

실측 저장량은 다음과 같다. 실행 디렉토리와 인접 터미널 로그를 합한 논리 파일 크기이며, MB는 1,000,000바이트다.

| 실행 | 전체 자료 | 학습 전이 gzip | 전이 gzip 해제 후 |
| --- | --- | --- | --- |
| 왼손 학습 420전이 | 72.92MB | 0.357MB | 5.206MB |
| 오른손 학습 420전이 | 72.69MB | 0.241MB | 4.935MB |
| 왼손 시작 실패 0전이 | 0.368MB | 43바이트·0행 | 0바이트 |

이 세 학습 자료의 **약 92.53%는 PPO 체크포인트**다. 양손 각각 마지막 `checkpoint_000000.pt`와 `final.pt`의 model·optimizer·RNG·identity·업데이트 수가 모두 같고 metadata만 다르다. 최종 사본 하나씩을 피하면 이 두 짧은 실행에서는 총 **55.58MB**를 줄일 수 있다. 기존 파일은 삭제하지 않았다.

반면 일반 학습 전이 gzip은 양손 합계 **0.597MB**다. 행 평균 해제 크기는 왼손 약 12.40KB, 오른손 약 11.75KB다. 반복 문자열/사본을 줄일 여지는 있지만 현재 저장 용량의 주원인은 아니다. `specialist.timing` 중복 사본만의 해제 값 크기는 양손 각각 약 0.586/0.646MB이며, 이 수치를 그대로 gzip 절감량으로 볼 수는 없다.

별도의 전체 240Hz 평가 trace는 왼손 **43.23MB**, 오른손 **42.84MB** gzip이며, 해제하면 각각 약 201.83/200.87MB다. 일반 학습 로그가 이 정도로 매번 저장된다고 혼동하면 안 된다.

[파일별 크기·의미적 중복 대조](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/storage_audit_v1.json)에 상세 근거가 있다. 이 자료는 현재 1업데이트 실행의 측정이며 긴 학습에서는 저장 간격과 에피소드 수에 따라 구성 비율이 달라진다. 압축 크기를 전이 수에 단순 비례시킨 장기 용량 보장은 하지 않는다.

## 5. 먼저 추가할 기록

| 우선순위 | 추가/정리 대상 | 구체적인 내용 |
| --- | --- | --- |
| 1 | 업데이트별 음악 학습 요약 | 활성 손·stage·시간창·목표 ID, 완료/실패/시간 제한/미완료 수, 누적 및 최근 구간 성공률, 에피소드 보상/비용, 보상 항목별 합계. 업데이트에 끝난 에피소드가 없으면 분모 0과 미완료 진행을 명시한다. |
| 1 | 왼손 품질 | audible clean 유지율, 오압현/미압현 시간과 각 적용 구간, dropout, 음 종료→해제 지연, 해제 완료율. 비활성 오른손 항목은 해당 없음으로 둔다. |
| 1 | 오른손 품질 | 첫 accepted 타현의 signed/absolute 오차(ms), 목표 누락, 잘못된 현/방향·시각, unprepared·extra·기타 blocked 이벤트를 중복 없이 집계, 최종 recovery. 비활성 왼손 missing은 성공 분모에서 제외한다. |
| 1 | 물리 안정성 요약 | 240Hz 하위 표본에서 기타 이동/회전·발 이동의 최대값, 양발과 전체 지지의 이탈 시간/최장 연속 이탈, 종료 이유별 수. 가슴 단독 접촉률은 진단이다. |
| 1 | 중단 후 품질 요약 | 예외/사용자 중단에도 유효하게 저장된 prefix의 품질·실패 원인·마지막 checkpoint를 요약한다. 수집/저장/업데이트 반영/버림 전이 수를 별도 표기한다. |
| 2 | PPO 상태를 해석하는 데 필요한 통계 | 미니배치 표본 가중 평균 loss, 최종 전체 rollout KL(기존 유지), 활성 행동만의 std/entropy·clip fraction, reward/cost critic explained variance와 value 오차. entropy는 latent Gaussian인지 변환 후 행동인지 정의한다. |
| 2 | 안정성의 학습 영향 | reward advantage와 cost advantage 및 `cost_weight × cost advantage`의 평균/표준편차, 활성 손 행동 포화율·목표 추종 오차. cost weight 하나만으로 안전 비용이 탐색을 억누른다고 판단하지 않는다. |
| 2 | 비교 가능한 정기 평가 | 고정된 평가 목표/seed, checkpoint의 누적 업데이트·전이, 결정적/확률적 실행 구분과 에피소드 수. 학습 보상과 평가 점수는 따로 그린다. 손별/목표별 분모 및 단계 변경점을 남긴다. |
| 3 | 성능·매체 진단 | 기록 serialization/gzip/write, checkpoint, 요약 스캔 시간·바이트, worker 대기 및 정책/물리 시간을 분리 계측. 대표/실패 영상과 손 파지 목표 추종 오차는 주기적 평가에서 기록한다. 파지 목표 유지가 물리적 피크 파지 성공을 인증하지는 않는다. |

현재 `update_*.json`과 진행 출력에는 음악 품질 요약이 없다. 수치는 전이 상세와 종료 후 보고서에서 추출할 수 있지만 학습 중 추세 판단이 어렵다. TensorBoard 같은 표시 도구는 이 스칼라 요약이 정리된 다음 연결하면 된다.

## 6. 기록 손실·실패 처리의 범위

[학습 핵심](/home/ajou/yigyu/3/guitar_learning/train_parallel.py:189)은 예외와 부분 수집, 복구 가능 checkpoint 및 worker 상태를 `finally`에서 기록한다. 실제 시작 실패도 error/report/events에 남는다. 시작 실패에서는 초기화된 trainer가 없으므로 복구 checkpoint가 없는 것이 정상이다.

반면 [품질 요약](/home/ajou/yigyu/3/guitar_learning/train_musical_quality.py:55)과 [준비 요약](/home/ajou/yigyu/3/guitar_learning/train_actionable_preparation.py:73)은 하위 실행의 정상 반환 뒤에만 생성된다. 중간 예외에서는 유효한 기존 전이가 있어도 이 요약이 누락될 수 있다. 현재 실패 예시는 0전이라 음악 품질을 잃은 사례는 아니지만, 코드 경로상 누락 가능성은 명확하다. 해결 시 원래 예외를 덮지 않도록 해야 한다.

전이 gzip은 정상 종료/처리된 예외에서 닫힌다. 주기적인 내구성 경계는 구현되어 있지 않으므로 강제 종료·프로세스 중단·전원 손실에서 마지막 행과 gzip trailer가 보존된다고 가정하지 않는다. 파일 분할 또는 명시적 주기 저장과 prefix 판독 정책은 추후 구현 대상이다. 체크포인트는 임시 파일을 완성해 link로 게시하지만 전원 손실까지 보장하는 fsync 구현은 아니다.

stdout/stderr의 `.log` 파일은 실행한 쪽의 출력 리다이렉션에 의존한다. 구조화 기록은 실행기가 쓰지만 터미널 출력 전체를 자동으로 같은 디렉토리에 복제하지는 않는다.

## 7. 권장 기록 구성과 적용 순서

- 항상: 실행 계약·출처, 업데이트별 스칼라 요약, 에피소드별 역할/목표/성공·실패 근거, 중요 이벤트, 저주기 자원 상태, 복구 checkpoint.
- 진단 선택: 상세 행동·관절·contact feature, 최초 rollout, 오류 주변 표본. 상세를 끄더라도 이벤트 수·지속시간·실패 원인과 원본 입력 참조는 유지한다.
- 정밀 평가 선택: 240Hz 전체 native trace, 원시 접촉, 대표 영상. 일반 학습과 별도 파일/보관 주기로 운영한다.

적용은 ①역할별 실시간 요약과 분모 정의 → ②예외 시 요약·전이 커밋 경계 → ③중복 상세/최종 모델 저장 축소 → ④필요 시 대시보드·시간 계측 순서가 적절하다. 현재 로그가 학습을 느리게 만드는 주원인인지는 기록 전용 시간 계측이 없으므로 결론 내리지 않았다.

## 근거 코드와 점검 산출물

- [전이 기록과 업데이트 저장](/home/ajou/yigyu/3/guitar_learning/train_parallel.py:140), [60Hz 기본 compact](/home/ajou/yigyu/3/guitar_learning/parallel.py:45), [episode 집계](/home/ajou/yigyu/3/guitar_learning/parallel.py:346).
- [현행 품질 로그 연결·종료 집계](/home/ajou/yigyu/3/guitar_learning/train_musical_quality.py:26), [품질 summary](/home/ajou/yigyu/3/guitar_learning/musical_quality.py:149), [단계 성공 동기화](/home/ajou/yigyu/3/guitar_learning/musical_quality_environment.py:39).
- [240Hz 비용·종료 통합](/home/ajou/yigyu/3/guitar_learning/training_environment.py:118), [안전 수치 정의](/home/ajou/yigyu/3/guitar_learning/safety.py:75), [자원/상태 모니터](/home/ajou/yigyu/3/guitar_learning/monitoring.py:111).
- [점검 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_logging_audit_20261018.md), [읽기 전용 수치 대조 스크립트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/verify_metrics_v1.py), [수치 대조 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/metrics_audit_v1.json).
- [저장량 점검 스크립트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/storage_audit_v1.py), [저장량 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/storage_audit_v1.json).
- [지표별 의미와 학습/평가 구분 상세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/metrics_semantics_v1.md).
- [독립 검수: 문제없음](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/review_v1.md). 수치 재현·실제 파일 크기·checkpoint 중복·근거 링크 확인을 완료했다.
