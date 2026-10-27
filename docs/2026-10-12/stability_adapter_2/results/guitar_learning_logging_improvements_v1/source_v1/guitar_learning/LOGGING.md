# 학습 로그 사용법

2026-10-19. 기존 `train_musical_quality` 명령과 학습 설정을 그대로 사용하면 새 기록이 적용된다. 정책·관측563·행동39·보상·성공식·물리 조건·strict resume 계약은 바꾸지 않았다. 앞2초 정책 준비와 전체7초도 유지한다.

## 먼저 볼 파일

| 파일 | 용도 |
| --- | --- |
| `learning_status.json` | 수집 중 최신 진행, worker별 마지막 품질, 전체 집계와 저장 상태. 60 제어 tick 및 업데이트/종료 시 교체한다. |
| `learning_metrics.jsonl` | 업데이트별 최근 구간/누적 성공 분모·품질·안전·보상/비용과 optimizer 업데이트 수. |
| `update_*.json` | 해당 업데이트의 PPO 상세 통계와 음악 요약 정본. `report.updates`는 가벼운 스칼라와 이 파일의 경로를 제공한다. |
| `episodes.jsonl` | 종료/미완료 에피소드별 worker·episode 번호, 원 종료 근거와 새 역할별·240Hz 요약. |
| `training_summary.json` | 전체 counter/group, 준비 구간, 중단 시 미완료 상태, 전이 회계, episode 파일 경로/SHA. 전체 episode를 다시 메모리에 읽지 않는다. |
| `musical_quality_report.json` | 담당 손의 품질 성공과 timing-only 달성 구분, 실패/중단, worker별 마지막 상태. |
| `report.json`, `events.jsonl`, `resources.jsonl`, `status.json` | 기존 실행·감사·시스템 진행/메모리 기록. `completed`는 음악 성공이 아니다. |

기본 standard 종료 보고서의 `episodes` 배열은 비워 두고 `episode_records`로 원자료를 참조한다. 완료 수·성공 수는 누적 counter에서 가져온다. 진단 모드/과거 로그 호환 경로는 상세 배열을 제공할 수 있다. `timing_report`의 단계 성공은 현행 품질 gate를 포함하며 `timing_only_successful_episodes`와 구분한다.

## 지표 의미

- 역할·stage·시간창·목표별 분모를 분리한다. 평가 에피소드 0회이면 성공률은 `null`이다. 비활성 손의 품질 요약은 `null`이다.
- 보상 항목과 cost는 전이 증분을 합한다. wrong/missing/late 시간 및 타현 횟수는 종료 시 누적값을 한 번만 집계한다.
- 왼손은 audible clean 비율·wrong/missing 시간·dropout·현재 해제 완료·late 접촉 점유를 기록한다. 별도의 `first_post_note_clear_delay_s/ms`는 240Hz에서 처음 관찰한 음 종료 후 목표현 접촉 해제 시각이며 연속 해제 완료나 물리적 현 압력이 아니다.
- 오른손은 최초 accepted 타현의 signed 오차(초), accepted ID, extra/unprepared/기타 blocked, wrong 통과와 현재 recovery를 구분한다. 이벤트 ID가 겹치는 blocked와 extra를 중복 오류로 더하지 않는다.
- `safety240`은 네 하위 물리 표본 전부의 극값·접촉 이탈 시간과 에피소드 경계를 넘지 않는 최장 연속 이탈이다. 기존 `stability`는 마지막 하위 표본이다. 가슴 단독/삼중 접촉은 진단이며 전체 지지·접지·이탈 기준을 대체하지 않는다.
- `actor_loss` 등 기존 최상위 loss와 norm은 호환을 위한 마지막 미니배치 값이다. `*_last`로 의미를 명시하고 `diagnostics.minibatches`에 표본 가중 평균·최대를 제공한다. KL 거부 시도는 별도다.
- `diagnostics.advantages`는 reward/cost 및 cost weight 적용 후 규모를, `post_update`는 전체 rollout ratio/clip fraction, 활성 손33/6채널의 std·latent Gaussian entropy·포화율, critic MSE/EV를 제공한다. entropy는 tanh 행동의 entropy가 아니다. target 분산0의 EV는 `null`이다.

## 저장 경계와 중단

`transitions.jsonl.gz`는 표준 gzip으로 읽을 수 있는 연결된 gzip member다. 60개 제어 tick(시뮬레이션1초), 에피소드 종료, 수집 끝, 정상/처리된 예외 종료에서 member를 닫고 file flush/fsync한다. `logging_contract.json`과 gzip metadata sidecar에 형식을 기록한다.

`accounting`의 수치는 worker에서 완전한 batch로 부모에게 반환된 표본 기준이다.

- `sampled_transitions`: journal 기록 시도까지 도착한 표본.
- `logged_transitions`: JSON encode/gzip write가 성공한 표본.
- `durable_transitions`: 완결 member와 fsync 경계를 통과한 표본.
- `committed_transitions`: 성공한 PPO 업데이트에 반영된 표본.
- `discarded_transitions`: 이번 실행의 PPO에 반영되지 않고 폐기한 표본. 저장 파일에 근거가 남을 수 있다.

worker 내부에서 죽어 부모에게 반환되지 않은 일부 물리 표본 수는 이 회계로 확정하지 않는다. `partial_collection`과 실패 원인을 함께 본다. 처리된 중단에서는 품질/준비 요약도 `finally`에서 만들며 0전이·완료0회도 명시한다. 부차적 요약 오류는 원래 예외를 덮지 않는다.

강제 종료로 마지막 gzip member가 잘렸다면 새 디렉토리로 검증된 prefix를 추출한다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.recover_training_log \
  --run /absolute/path/to/run --out /absolute/path/to/new_recovery_directory
```

완결 member의 CRC를 통과한 prefix만 사용하고 오류 원인을 남긴다. 단일 member였던 과거 gzip이 잘리면 검증된 prefix가 0일 수 있다. 복구 요약은 PPO commit 수나 체크포인트 유효성을 추정하지 않는다. 원 로그·모델을 변경하거나 학습을 자동 재개하지 않는다.

## 상세도와 모델 보관

설정 JSON에 다음 선택 항목을 추가할 수 있다. 생략 시 아래 값이 기본이다.

```json
"logging": {"detail": "standard", "save_first_rollout": false}
```

`standard`는 반복 config/긴 설명/중복 timing 사본과 매 tick의 전체 action·contact feature를 줄인다. 원 계약은 `training_contract.json`, 실제 상세는 에피소드 첫 tick·활성 손 판정 변화·물리 실패의 `raw_sample_path`에서 확인한다. 상대 손 변화만으로 raw를 추가하지 않는다. `diagnostic`은 상세 compact를 유지한다. `save_first_rollout: true`는 첫 PPO rollout tensor도 저장한다. 평가 전체240Hz trace는 별도 근거 파일이다.

최종 업데이트에는 `final.pt`만 새로 저장한다. 중간 주기 checkpoint와 최종 상태가 model·optimizer·RNG·계약까지 정확히 같으면 같은 실제 파일을 hardlink로 참조한다. `final_checkpoint.json`에 정본 출처와 최종 metadata를 남긴다. hardlink에는 주기 checkpoint의 payload metadata가 유지되며 최종 metadata는 manifest가 정본이다. 모델·optimizer·RNG를 유지하므로 기존 strict resume가 가능하다. 과거 모델 파일은 삭제하지 않는다.

## 평가와 성능 해석

`evaluate_musical_quality`는 `evaluation_metrics.json`도 남겨 결정적 평가, 체크포인트 SHA·업데이트 수·역할·완료 분모를 기록한다. actor 이전 초기화의 과거 optimizer 업데이트를 새 정책의 학습량으로 상속하지 않는다. `configured_seed`는 설정 출처이고 evaluator가 이를 명시적으로 reseed했다는 뜻은 아니다. strict 평가에는 checkpoint RNG 복원이 적용된다. 평가를 매 학습 업데이트마다 자동 실행하지는 않는다.

기록 encode/gzip write/fsync 시간과 모델 저장 시간은 별도로 남긴다. 장치 수준 IO 시간이나 worker 전체 물리 계산만의 시간은 아니다. 새 기록이 빨라졌다고 단정하지 않는다.

## 구현·보관·검증

- 생산: `training_metrics.py`, `training_log_io.py`, `training_log_format.py`, `training_reports.py`, `ppo_diagnostics.py`와 기존 실행기 연결.
- 이전 코드157파일: `archive/20261019_before_logging_improvements/manifest.json`의 경로/SHA로 확인한다.
- 실제 검증 결과: [로그 개선 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/README.md).
