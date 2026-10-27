# 학습 로그 사용법

## 현재 기본 GPU 실행

2026-10-24 저장 형식을 유지한다. 2026-10-26 현재 GPU왼손은 보상v22·552상태·선별 손가락 충돌·B복귀/추종 동기화·엄지 안내를 사용한다. 최초접촉 원장v7·이벤트v5와 아래 정본/체크포인트 구조는 유지한다. 기존 CPU·전문 경로의 파일 목록과 계약을 GPU에 그대로 적용하지 않는다. [현행 결과](/home/ajou/yigyu/3/docs/2026-10-26/guitar_learning_hand_contact_v22/README.md)를 따른다.

| 파일 | 저장 내용 |
| --- | --- |
| `initial.pt`, `checkpoint_*.pt`, `final.pt` | 모델·두 optimizer·난수·curriculum. 기본 추가 저장 간격250회. 초기·최종은 별도 저장하므로2,000회 실행은9개다. 명시한 `--checkpoint-every`가 우선한다. |
| `checkpoint_manifest.jsonl` | 초기·중간·최종·생성된 복구 파일의 이름·학습 횟수·크기·SHA·저장 시간. `report.checkpoints`와 `timers.checkpoint_s`는 전체 성공 저장을 집계한다. 해시·manifest 쓰기 시간은 모델 저장 시간과 구분한다. |
| `learning_metrics.jsonl` | 업데이트당 한 줄의 PPO·보상 성분·단계·처리시간·에피소드 요약과 정본 ID. 중복 `update_*.json`은 생성하지 않는다. |
| `episodes.jsonl` | 종료 에피소드의 상세 원장·동작·진단 정본. 다른 로그는 이 정본의 ID를 참조한다. |
| `episode_metadata.json` | 첫 에피소드 발생 때 한 번 저장하는 공통 schema·계약·설명·목표/관절 이름 등. 실행 중 값이 바뀌면 오류로 처리한다. |
| `transitions.jsonl.gz` | 원래 reward/cost/terminated/truncated 배열·에피소드 참조. gzip CRC와 sampled/logged/durable/committed/discarded 회계를 유지한다. |
| `settings.json`, `training_contract.json`, `inputs_before.json` | 설정·학습 계약·입력 해시. |
| `report.json`, `song_report.json`, `status.json`, `events.jsonl`, `resources.jsonl` | 완료·오류·원곡 종료 집계·진행·자원 감시. |

기본100회처럼 저장 간격보다 짧은 실행은 초기·최종만 남는다. 실패 복구 파일은 기존 유효 optimizer 경계에서만 생성한다. 평가 결과의 최고 모델은 이미 저장된 파일 경로로 지정하며 같은 모델을 별도로 복사할 필요가 없다. 최고 모델은 학습 보상만으로 정하지 않는다.


### v19 최초접촉 원장과 진단

GPU왼손 `surface_note_ledger.v7`에 현재 `contact_streak`, 최장 `best_contact_streak`, `contact_progress`를 기록한다. progress=min(best/min(.05,end−press),1)는 소진한 원시 예산 진행률이다. 실제 받은 금액이 아니며 실패tick 양성 억제·단계 가중 후 지급액은 `reward_components.song_left_contact`와 update의 component 평균에서 확인한다. 음별 원시 예산 상한은0.5b이고 같은 길이의 짧은 접촉 반복은 추가 예산이 없다. 누적contact_time·clean/held·best_clean_streak·contact_done/left 지표를 유지한다. 부분접촉 진행을 최초접촉 완료나 audible 음 달성으로 세지 않는다.

관측 events.v5는 GPU왼손 토큰12/13을 현재 접촉 진행률/소진 예산 진행률로 사용한다. 토큰에서 누적held 관측을 교체했지만 원장과 보고서의 누적held는 보존한다. 진단 도구의 정적목표·고정/자유 대조는 일반 학습 episodes와 구분하며, 240Hz 원시와60Hz 자세는 사전 지정 대표환경만 저장한다. [구현·검증 범위](/home/ajou/yigyu/3/docs/2026-10-25/guitar_learning_press_acquisition_v1/README.md)를 따른다.

### 새 로그 읽기와 검증

```bash
python -m guitar_learning.tool.inspect_gpu_training_log --run /absolute/path/to/run
```

`guitar_learning.training.gpu_log_records`의 `iter_episode_rows`, `iter_learning_metrics`, `iter_gpu_transitions`는 스트리밍으로 새 정본·공통 메타데이터·ID 참조를 복원하고 과거 GPU 형식도 읽는다. PPO에는 압축 전 원래 에피소드가 전달된다. 문서 결과 폴더 안의 과거 검증·분석 스크립트는 당시 동결된 파일 배치 전용이므로 새 실행에는 사용하지 않는다.

메타데이터와 에피소드 정본을 먼저 동기화한 뒤 이를 참조하는 전이 member와 PPO commit을 확정한다. 중단된 실행에서 로그가 남았다는 이유로 PPO 반영이나 음악 성공을 추정하지 않는다. 손상된 JSON 끝줄·누락 참조·gzip CRC 오류는 조용히 생략하지 않는다.

### GPU 왼손 에피소드 진단 v5

left_episode_diagnostics에는 모든 환경의 작은 요약만 기록하고 매tick 원시자세를 모두 덤프하지 않는다. 원시240Hz·60Hz영상/자세는 사전에 지정한 대표환경만 별도 진단도구로 저장한다.

- B: 실제240Hz gate 적용시간·준비/비유한거리/무효각도 제외시간·gate가중품질·원시/단계가중 실제보상을 기록한다. v22에서 stale candidate/wrong와4cm근접veto는없으며 호환필드가0인것을 접촉없음으로 해석하지 않는다. 준비시간은 press..end합집합·해제.05초/양끝.1초fade·gap별복귀를 따른다.
- 자세: 실제source-frame MCP/PIP/DIP의 gate가중 idle와본인press..end구간 평균·극값·유효시간을분리한다. 해부학적관절각인증이아니다. 검지형 MCP과신전/PIP·DIP굽힘, 소지형 MCP·PIP굽힘/DIP폄, DIP−PIP편중의노출을 전체/idle/press조건별로기록한다. 이진단은추가관절벌점이아니다.
- 회복창: 악보로 고정한 이전end+.05초해제+1초잠정복귀예산~다음press−.35초(초기1.05초·마지막곡끝)에서실제B대역체류를기록한다. 완전관측된길이≥.5초창만계획시간중80%criterion으로평가한다. 짧은창·초기부터대역안·초기무효를구분하고 정책의gate로분모를바꾸지않는다. 1초를검증된최대복귀시간으로표현하지않는다.
- 손목: 기타좌표Gx/Gy/Gz영역초과평균/최대와영역체류를240Hz에기록한다.
- 엄지 새240Hz: 공유thumb_support helper의선택thumb3패치 동일점gap·normal cosine·영역초과·유효/무효·기하근접시간·음수gap/−1mm이하시간·quality적분·원시잠재 .01*Q+.01*Q*candidate(상한.02/s)보상·실제지급을기록한다. 실제지급에는명시OFF/ON계수와실패controltick양성억제를적용한다. 엄지3 native몸체합력의유효시간·평균/최대와기타좌표뒷면바깥법선하중·그유효시간을별도로기록한다. candidate시간·near_unloaded시간을구분하며후자는near_geometry이면서합력유효·법선하중<.01N일때만센다. 비유한힘은제외하며힘증가보너스는없다.
- 엄지 기존60Hz: thumb2/3 유한source지지정점과넥뒷면유한삼각형사이거리/뒷면쪽근접비율을남긴다. 법선없는127지지점의기존진단을새128패치240Hz와같은접촉률로합치거나직접대조하지않는다.

reset준비상태자체는물리표본이아니다. H32에서원장·누적목표·진단을지우지않고종료환경선택reset만초기화한다. 관측조회는보상원장을갱신하지않는다. body netforce·source표면gap은실제넥접촉쌍/현압력/음향/PhysX cooked관통깊이인증이아니다. reward_components와update평균은19개공용키이며왼손합산은14슬롯(coordination기본0)이다.

### 이전 로그 삭제 기록

사용자 요청으로 이전 버전의 큰 원시 로그 일부를 삭제했다. [삭제 목록·크기·SHA](/home/ajou/yigyu/3/docs/2026-10-24/guitar_learning_compact_logging_v1/cleanup_manifest.json)에 정확한 범위를 남겼다. 체크포인트·영상·분석 보고서·계약과 당시 최신이던 v17 실행은 보존했다. 과거 보고서는 당시 검증 결과이며 삭제된 원시 로그를 재검사했다는 뜻이 아니다.

## 기존 CPU·전문 음악 품질 경로


2026-10-19. `guitar_learning.tool.training.train_musical_quality` 명령과 기존 학습 설정을 사용하면 기록이 적용된다. 정책·관측563·행동39·보상·성공식·물리 조건·strict resume 계약은 바꾸지 않았다. 앞2초 정책 준비와 전체7초도 유지한다.

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
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.tool.recover_training_log \
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

- 생산: `guitar_learning/training/training_metrics.py`, `guitar_learning/training/training_log_io.py`, `guitar_learning/training/training_log_format.py`, `guitar_learning/training/training_reports.py`, `guitar_learning/training/ppo_diagnostics.py`와 기존 실행기 연결.
- 이전 코드157파일: `archive/20261019_before_logging_improvements/manifest.json`의 경로/SHA로 확인한다.
- 실제 검증 결과: [로그 개선 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_logging_improvements_v1/README.md).
