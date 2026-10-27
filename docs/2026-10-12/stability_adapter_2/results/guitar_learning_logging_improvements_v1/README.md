# 학습 로그 개선 적용 결과

2026-10-19. [기존 감사의 우선순위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_audit_v1/README.md)를 현행 학습 경로에 적용했다. 기존 학습 명령에 기본 적용되며 사용법은 [LOGGING.md](/home/ajou/yigyu/3/guitar_learning/LOGGING.md)에 정리했다.

보상·성공 판정·관측563/행동39·native0/정책7초·Root 고정·하체 유한 제어·자유 기타 조건은 유지한다. 코드/로그 개선 확인용 짧은 학습이며 음악 품질 개선·수렴을 검증한 실행은 아니다.

## 구현한 우선순위

1. **음악 목표별 요약:** 업데이트/에피소드/worker/목표/stage/시간창별 분모, timing-only/quality/joint 구분, 활성 손의 압현·해제 또는 타현·회복, 준비2초 행동을 기록한다. 완료0회는 성공률 `null`이다.
2. **실제240Hz 안전:** 네 물리 하위 표본의 기타·발·관절 극값, 접촉 이탈 점유와 최장 연속 이탈을 집계한다. 최초 clean 및 음 종료 후 최초 clear 표본도 기록한다.
3. **중단·회계:** 60 제어 tick마다 gzip member+fsync를 만들고 에피소드/업데이트/종료에서 추가 경계를 남긴다. sampled/logged/durable/committed/discarded를 분리한다. 처리된 예외에도 품질/준비 요약을 남기며 원 예외를 보존한다.
4. **장기 저장·메모리:** standard는 반복 config/중복 timing/매 tick의 상세 action/contact를 줄인다. 활성 손 판정 변화와 실패 주변 raw 근거는 남긴다. 누적 집계는 과거 episode 목록을 보관하지 않고 counter/group으로 유지하고 종료 보고서는 `episodes.jsonl`을 참조한다.
5. **PPO 진단:** 기존 last 지표를 명시하고 표본 가중 loss/norm, KL 거부 시도, 활성 std/latent entropy/포화, clip fraction, advantage와 비용 기여, critic EV/MSE를 기록한다. optimizer/RNG/identity 계약은 유지한다.
6. **최종 저장·평가:** 마지막 주기 checkpoint 중복을 만들지 않고 `final.pt`를 유지한다. 완전히 같은 PPO 상태는 hardlink로 재사용한다. 평가 로그는 학습과 모드·출처·분모를 분리하고 actor 이전의 과거 학습량을 상속하지 않는다.

자동 대시보드와 매 업데이트 자동 평가는 추가하지 않았다. 기존 evaluator를 필요할 때 실행하면 `evaluation_metrics.json`이 함께 생긴다. 기록 전용 시간은 제공하지만 속도 향상 주장은 하지 않는다.

## 검사와 실제 실행

- 최종 전체 CPU **335개 통과**, 151.200초: [전체 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/cpu_all_final_v1.txt).
- 원본 PPO와 동일 rollout/seed를 사용한 회귀에서 shared/LH/RH의 가중치·Adam 두 개·RNG·기존 스칼라가 CPU에서 정확히 일치했다. KL 거부·복원 경로도 포함했다.
- 잘린 gzip·CRC 오류·빈 실행·fsync 실패·원 예외 보존·다중 worker·업데이트를 넘는 에피소드·누적 품질·역할 분모·1000 episode 후 집계 메모리 보존을 검사했다.
- 첫 통합 검사에서 terminal 정보의 alias 때문에 상세 근거가 축약되는 문제를 발견·수정했다. 단독 실행 fixture의 torch 재import 문제도 고쳤다. 실패 로그는 삭제하지 않고 최종 통과 로그와 구분해 보존했다.
- 검수에서 기록 직후 fsync 오류의 마지막 행 누락, 전역 episode 목록 증가, 비활성 손 raw 선택, stream close와 부분 수집 회계 혼동을 발견·수정하고 회귀 검사를 추가했다.

| 실제 실행 | 설정과 범위 | 결과 |
| --- | --- | --- |
| [왼손 학습](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/left_native_train_v1/report.json) | 2환경×210tick×2업데이트 | 840전이, 완주2, 물리 실패0, 품질 성공0/2 |
| [오른손 학습](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/right_native_train_v1/report.json) | 1환경×420tick×1업데이트 | 420전이, 완주1, 물리 실패0, 품질 성공0/1 |
| [strict 재개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/left_native_resume_v1/report.json) | 왼손 final에서2환경×8tick×1업데이트 | 16전이, optimizer update2→3, 완료episode0/성공률null |
| [오른손 결정적 평가](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/right_native_eval_v1/evaluation_metrics.json) | 새 오른손 final, 1episode/7초 | 420제어tick, 물리 실패0, timing-only1/1·품질0/1 |

세 실행에서 sampled=logged=durable=committed였고 discarded=0이다. 왼손 첫 업데이트는 에피소드 완료0회·성공률null·미완료worker2개였고, 다음 업데이트에서 완료2회·품질 성공률0을 기록했다. 에피소드를 업데이트 경계에서 잘못 분리하거나 미완료를 성공으로 세지 않았다.

왼손 두 에피소드는 clean audible100%지만 해제 미완료·late 접촉2.5478초다. 오른손 학습은 accepted `1032:2`, 오차 **+177.248588ms**, extra1/wrong1/recovered=True다. 모두 타이밍만의 완화 달성과 품질 실패를 구분해 남겼다. 이는 동일 단음의 짧은 검증 결과다.

### 기록 시간과 파일

| 실행 | 전이 gzip | JSON encode | gzip create/write/finish | flush/fsync |
| --- | --- | --- | --- | --- |
| 왼손840전이 | 320,443B | 0.0730초 | 0.0827초 | 0.0966초 |
| 오른손420전이 | 219,078B | 0.0414초 | 0.0536초 | 0.0818초 |
| 재개16전이 | 8,071B | 0.0017초 | 0.0018초 | 0.0123초 |

이는 이번 실행의 부모 journal 계측이며 metadata 직렬화, worker의 raw 기록, 물리/통신 전체와 장치 IO 시간을 포함한 값이 아니다. 이전 실행과 환경 수·수집/업데이트 경계·정책이 달라 전후 속도나 압축률 비교로 해석하지 않는다. 왼손 중간 update1의 주기 모델과 update2 최종 모델은 서로 다른 학습 상태이므로 둘 다 유지하며, 오른손 최종은 중복 주기 모델 없이 저장했다.

### 실제 잘린 꼬리 복구

완료된 왼손 전이 파일을 **새 fixture로 복사한 뒤** 마지막8바이트를 제거했다. [복구 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/prefix_recovery_v1/recovered_summary.json)는 CRC 검증된 **390행·780전이**를 읽고 마지막 미완성 member를 EOF 오류로 명시했다. 원본 로그는 그대로다. 완료 episode와 PPO commit은 추정하지 않았다.

## 코드와 보존

- [실행기 연결](/home/ajou/yigyu/3/guitar_learning/train_parallel.py), [240Hz/역할별 집계](/home/ajou/yigyu/3/guitar_learning/training_metrics.py), [저장/복구·모델 게시](/home/ajou/yigyu/3/guitar_learning/training_log_io.py).
- [기록 상세도](/home/ajou/yigyu/3/guitar_learning/training_log_format.py), [요약 공통 근거](/home/ajou/yigyu/3/guitar_learning/training_reports.py), [PPO 진단](/home/ajou/yigyu/3/guitar_learning/ppo_diagnostics.py), [prefix 복구 실행기](/home/ajou/yigyu/3/guitar_learning/recover_training_log.py).
- 변경 전157파일의 [보관 경로/SHA](/home/ajou/yigyu/3/guitar_learning/archive/20261019_before_logging_improvements/manifest.json).
- 실제 실행 전169파일의 [봉인 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/sources_before_native_v1.json)와 [실제 소스 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/source_v1).
- 과거 실행/감사270개 artifact의 [보존 기준 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/preserved_results_before_v1.json). 과거 code/input/result/checkpoint는 삭제하거나 덮어쓰지 않았다.

## 최종 수치 대조

[독립 대조 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/native_verification_v1.json)는 완료다. [생산 스크립트](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/verify_native_v1.py)는 기존 결과를 읽기만 하고 새 버전 JSON을 작성한다.

- 실제 학습/재개1276전이·5104물리표본, 별도 평가420제어tick·1680물리표본이다. 실행·모델·원 입력 감사가 모두 통과했다.
- 전이 보상과 항목 합의 최대 차이는 왼손 `4.82e-8`, 오른손 `4.70e-8` 이내로 float32 저장 반올림 범위다. 종료 요약의 항목 합·분모·에피소드 파일 SHA가 일치한다.
- 실제 raw 근거가 남은12개 제어tick의48물리표본에서 안전 극값을 독립 계산해 기록과 대조했다. 모든 tick의 원시 궤적을 따로 저장하거나 전체240Hz 원자료를 재감사했다는 주장은 아니다. 별도의 합성 검사로 tick 경계의 연속 이탈도 확인했다.
- 평가에서는 accepted `1010:2`, 오차 **+85.135316ms**와 extra1/wrong1을 기록했다. 학습의 +177.248588ms와 다른 실행이며 혼합하지 않는다. 평가 `completed=True`, `source_unchanged=True`다.
- 봉인한 현행169파일, 보관한 이전157파일, 기존 결과/감사270파일의 SHA 변경0을 확인했다. 기존 입력·실패 근거·모델 파일을 제거하지 않았다.

검증 목표는 학습 판단에 필요한 기록을 정확하게 생산하는 것이다. 왼손0/2·오른손0/1의 품질 성공은 현재 모델의 남은 음악 수행 문제를 숨기지 않고 기록한 결과이며, 이번 로그 변경으로 장기 학습이 개선됐다고 해석하지 않는다.
