# Strike 학습 실행 흐름과 모듈 계약

> 기준 소스: 2026-08-19  
> 기준 명령: `python train.py --task strike ...` 또는 프로젝트 루트에서
> `python -m tab2body.train --task strike ...`

이 문서는 명령을 입력한 시점부터 환경 종료와 자동 산출물 생성까지 실제 호출되는 코드만
설명한다. 숫자나 파일 위치보다 checkpoint의 observation manifest와 run manifest가 최종
권위이며, 현재 정적 계약은 오른팔 30 action, 281 observation, scalar reward/value다.

## 1. 전체 호출 순서

```text
train.py
└─ resolve_task(argv)                         --task strike 선택
   └─ load_runner("strike")                  tab2body.train_strike 지연 import
      └─ train_strike.main(runner_argv)
         ├─ CLI·곡·출력 경로 해석
         ├─ Isaac Gym → Torch 순서로 runtime import
         ├─ goal/config/resource 사전 검증
         ├─ StrikeTask 생성
         │  ├─ GuitarEnvBase: Isaac Gym scene·actor·tensor
         │  ├─ StrikeGoalSequence: 입력 검증·gesture compile
         │  ├─ PickGripReference: 오른손 초기 자세
         │  └─ detector/reward/state/observation 구성
         ├─ ActorCritic + PPOTrainer 생성
         ├─ checkpoint contract 생성·resume 검증
         ├─ StrikeCurriculumRuntime 적용
         ├─ PPOTrainer.learn
         │  └─ iteration마다 collect → StrikeTask.step → update → save
         ├─ deterministic 평가 및 eval JSON 저장
         ├─ StrikeTask.close로 Isaac Gym sim 종료
         ├─ 학습 CUDA 객체·cache 해제
         └─ 분석·plot·motion audit·두 카메라 영상 생성
```

## 2. 진입점과 인자 전달

### `tab2body/train.py`

| 구분 | 내용 |
|---|---|
| 입력 | 원본 CLI 문자열 배열 |
| 처리 | `parse_known_args`로 `--task`만 읽고, `runner_argv`가 `--task` 토큰만 제거한다. `load_runner`가 선택한 runner의 `build_parser/main` 계약을 확인한다. |
| 출력 | strike 전용 인자 배열을 `tab2body.train_strike.main`에 전달한 반환값 |

이 모듈은 Torch, Isaac Gym, StrikeTask를 import하지 않는다. 따라서 `--help`와 task dispatch가
GPU runtime 초기화보다 먼저 안전하게 동작한다. 기본 task는 하위 호환을 위해 `fret`이다.

### `tab2body/train_strike.py: build_parser/main`

| 입력 | `--song` 또는 `--goal`, grip reference, 환경 수, device, iteration, checkpoint, curriculum/eval/산출물 옵션 |
| 처리 | 상호 배타 인자와 파일 존재 여부를 검사하고 절대 경로로 정규화한다. `--song`은 곡 번들의 `training/strike_training.json`으로 변환한다. |
| 출력 | 학습 종료 시 생성된 artifact 경로 사전. 실패 시 원인을 보존한 예외 |

`--task`는 이미 공용 진입점에서 제거되므로 strike parser에는 존재하지 않는다. `--song`과 명시적
`--goal`은 동시에 사용할 수 없다. `--eval`은 반드시 `--checkpoint`를 요구한다.

## 3. 입력과 실행 폴더 결정

### `tab2body/song_bundles.py`

| 입력 | `song_id` 또는 training JSON 절대 경로 |
| 처리 | 디렉터리 탈출을 막는 song ID 검증, 정본 번들 경로 생성, training 파일에서 song ID 역추출 |
| 출력 | `data/song_bundles/<song_id>/training/strike_training.json`, 정규화된 song ID |

### `tab2body/learning/run_layout.py`

| 입력 | workspace, song ID, `--out`, `--run-name`, checkpoint |
| 처리 | 새 run, 명시 경로, 기존 checkpoint run 재개의 우선순위를 적용한다. 기존 metrics/checkpoint가 있는 새 run 덮어쓰기를 차단한다. |
| 출력 | `RunLayout`: checkpoints/logs/evaluations/videos/plots/manifest 경로 |

run name을 생략한 새 학습은 로컬 시각 `YYYYMMDD_HHMM_<song_id>`를 사용한다. checkpoint만
지정하고 run name을 생략하면 기존 run에 이어 쓴다.

## 4. runtime import와 사전 검증

### `train_strike._load_strike_support_runtime`

| 입력 | 로컬 프로젝트 위치 |
| 처리 | 로컬 Isaac Gym Python 경로를 추가하고 `isaacgym`을 먼저, `torch`를 다음에 import한다. |
| 출력 | Torch 모듈 |

Isaac Gym의 torch bridge 등록 순서 때문에 이 순서를 바꾸지 않는다. 파일 layout, run I/O,
checkpoint hash 도구는 Torch 비의존 모듈이므로 일반 import로 정리되어 있다.

### `tab2body/strike_training_runtime.validate_strike_goal_for_training`

| 입력 | goal 경로, `STRIKE` config, A4 필요 여부 |
| 처리 | schema/gesture, detector re-arm, recovery, episode horizon, timing window, safety 설정의 실행 가능성을 CPU에서 검사한다. |
| 출력 | goal validation metadata |

### `tab2body/learning/run_io.training_resource_preflight`

| 입력 | CUDA device, 환경 수, 출력 위치, resource limit |
| 처리 | 환경 수 상한, CUDA 사용 가능 여부, 여유 VRAM/RAM/disk를 실제 allocation 전에 확인한다. |
| 출력 | 시작 시점 resource snapshot; 부족하면 즉시 예외 |

run layout은 이 검사 전에는 경로만 계산하고 디렉터리를 만들지 않는다. 따라서 CUDA나 자원이
부족한 사전 검증 실패가 빈 run 폴더를 남기지 않는다. 검사를 통과한 뒤에만 실제 하위 폴더를 만든다.

## 5. goal 변환

### `tab2body/env/strike_goals.py`

| 입력 | `strike_training.v1/v2` JSON의 `metadata.fps`와 `[time, frame, string]` event |
| 처리 | 60 Hz, time/frame 오차, string 0..5, 사건 순서와 ID를 검증한다. `time`이 시간 권위다. |
| 출력 | `StrikeGoalSequence`의 GPU/CPU tensor: original/easy time, gesture, direction, audible/traversal/protected mask |

### `tab2body/env/strike_goal_compiler.py`

| 입력 | 검증된 source events, detector·recovery 간격, 초기 timing tolerance |
| 처리 | 가까운 서로 다른 줄 사건을 ordered strum으로 묶고, 같은 줄의 불가능한 빠른 재타현은 `alternate_restrike`로 표시한다. 물리 최소 간격에 맞춘 easy timeline을 만든다. |
| 출력 | `CompiledStrikeGoal`: 원본/쉬운 시간표, single/strum 사건, adaptive event windows |

A4에서 `tempo_lambda=0`은 easy timeline, `1`은 원곡 시간이다. 중간값은 두 시간표의 선형 보간이며,
성능 gate가 통과될 때만 `0 → 0.25 → 0.5 → 0.75 → 0.9 → 1`로 진행한다. 원본 JSON은 수정하지
않는다.

## 6. 환경 생성

### `train_strike._create_task`와 `tab2body/env/config.py`

| 입력 | CLI override와 `STRIKE` 설정 |
| 처리 | `configured_kwargs`가 `StrikeTask.__init__` 서명에 있는 설정만 전달하고 누락/오타를 드러낸다. |
| 출력 | `StrikeTask` |

### `tab2body/env/base.py: GuitarEnvBase`

| 입력 | 환경 수, 제어 DOF prefix, 장치, reset/action 설정, 관측 body |
| 처리 | Isaac Gym sim, 사람·기타 actor, DOF/rigid-body/contact tensor, PD target, 공용 reset·관측·안전 판정을 만든다. |
| 출력 | 벡터화된 물리 상태와 공용 observation/reward 기반 |

### `tab2body/env/tasks/task_strike.py: StrikeTask.__init__`

| 입력 | goal, grip reference, zone/trajectory/detector/safety/reward/episode 설정 |
| 처리 | 오른쪽 어깨 3 + 팔꿈치 3 + 손목 3 + 오른손 21 DOF를 정확히 검사한다. `R_Thorax`는 고정한다. 줄 선분, pick tip, grip pose, detector, reward, penetration monitor, curriculum state, metric buffer, 281D observation manifest를 구성한다. |
| 출력 | `num_actions=30`, `num_obs=281`, `value_dim=1`, 초기 관측 |

### `tab2body/env/rewards/strike.py`

| 입력 | 손 관절 자세와 단계별 grip/ready/release/timing/zone/오타현 신호 |
| 처리 | 현재 단계에서 획득해야 하거나 보존해야 하는 보상만 합성한다. joint-limit soft penalty는 task에서 마지막에 더한다. |
| 출력 | 환경별 scalar reward와 항목별 진단값 |

## 7. 모델, checkpoint 계약, curriculum

### `tab2body/learning/models.py: ActorCritic`

| 입력 | 281D observation, 초기 평균 action, 초기 표준편차 |
| 처리 | RunningMeanStd 정규화 뒤 MLP actor/critic을 계산한다. actor는 tanh-squashed Gaussian으로 `[-1,1]` 내부 action을 만든다. |
| 출력 | 30D action, log probability, scalar value |

### `tab2body/strike_checkpoint.py`

| 입력 | live env/model, goal/grip hash, semantic config, PPO config, asset·구현 파일 |
| 처리 | action 순서, observation manifest, 물리/보상/goal/PPO 의미와 구현 지문을 canonical JSON hash로 봉인한다. |
| 출력 | checkpoint contract payload와 SHA-256 |

resume/eval은 model tensor를 바꾸기 전에 live contract와 저장 contract를 비교한다. 의미가 다른
checkpoint는 shape이 같아도 거부한다.

### `tab2body/learning/strike_curriculum.py`와 `strike_training_runtime.py`

| 입력 | 완료 episode 지표, stage별 최소/최대 iteration, promotion window, timing/tempo schedule |
| 처리 | A0 grip → A1 ready → A2 crossing → A3 timing → A4 zone 순으로 성능 기반 승급한다. stage/tolerance/tempo 변경을 환경에 적용하고 reset observation을 trainer에 전달한다. |
| 출력 | checkpoint에 저장되는 curriculum state와 전이 record |

최대 iteration은 강제 승급 조건이 아니다. gate를 통과하지 못한 채 최대치에 도달하면 `stalled`를
기록하고 최신 checkpoint를 저장한 뒤 정상적인 평가·산출물 단계로 이동한다.

## 8. PPO iteration 내부

### `tab2body/learning/ppo.py: PPOTrainer.learn`

한 iteration은 다음 순서다.

1. `iteration_callback`: 현재 curriculum을 환경에 적용한다.
2. `collect`: 기본 32 simulation step을 수집한다.
3. `advantages`: scalar reward/value로 GAE와 정규화 actor advantage를 계산한다.
4. `update`: clipped PPO policy/value loss, entropy, 선택적 action regularization으로 갱신한다.
5. `iteration_result_callback`: 완료 episode 통계를 curriculum에 전달한다.
6. metrics/log/checkpoint를 주기에 따라 저장한다.
7. `post_iteration_callback`: curriculum 전이 JSON과 stalled checkpoint를 저장한다.

Strike runner는 전체 iteration history를 메모리에 보존하지 않는다. 마지막 iteration 통계만 별도
보존해 `ANALYSIS.md`에 사용하고, 상세 이력의 권위는 `logs/metrics.jsonl`이다.

### `PPOTrainer.collect`

| 입력 | 현재 observation과 action mask |
| 처리 | policy action을 만들고 reusable Isaac observation buffer를 step 전에 복사한다. episode 완료 metric과 rollout diagnostic을 모은다. non-finite tensor는 optimizer 진입 전에 거부한다. |
| 출력 | `[horizon, num_envs, ...]` rollout과 완료 episode 행 |

### `StrikeTask.step`

한 physics frame의 순서는 다음과 같다.

1. 현재 motor phase를 보존하고 30D action을 PD target에 적용한다.
2. PhysX를 진행하고 tensor를 refresh한다.
3. `RH:pick`의 이전→현재 swept segment와 고정 기타 줄 6개를 비교한다.
4. `PickStrikeDetector`가 깊이·횡속도·방향·finite-segment 조건을 만족한 RELEASE를 만든다.
5. ordered matcher가 목표 traversal 순서, 중복, 보호/비목표 줄, 방향을 판정한다.
6. ready/timing/zone gate, miss, event 완료, recovery와 다음 event 전이를 갱신한다.
7. reward와 joint-limit penalty를 계산한다.
8. timeout, non-finite, velocity blowup, recovery timeout, 기타 관통, 후기 오타현 종료를 합친다.
9. terminal observation·episode metric·reason을 만든 뒤 완료 env만 reset한다.
10. 다음 observation, reward, done, info를 반환한다.

`step` 출력 계약은 다음과 같다.

| 출력 | shape/의미 |
|---|---|
| observation | `[N,281]`, 완료 env는 reset 상태가 합성됨 |
| reward | `[N,1]` |
| done | `[N]` bool |
| info | live 진단, RELEASE mask, target/progress, 종료 이유, 완료 episode metric |

## 9. 저장, 평가, 종료

### checkpoint 저장

`PPOTrainer.save`는 model, optimizer, iteration/global step, curriculum training context, 환경 RNG/reset
generation, checkpoint contract를 임시 파일에 쓴 뒤 같은 filesystem에서 원자적으로 교체한다.

### deterministic 평가

`train_strike.evaluate_strike`는 현재 stage를 보존한다. A4이면서 `tempo_lambda=1`인 경우에만 원곡
전체를 평가하고, 그 전에는 현재 tempo의 training phrase를 평가한다. deterministic action으로 지정된
episode 수를 모아 single/strum/timing/zone/safety gate를 계산하고
`evaluations/strike_<iteration>.eval.json`에 저장한다.

### 환경 종료와 자동 산출물

평가 성공·실패와 관계없이 `finally`에서 `StrikeTask.close`가 sim을 파괴한다. 정상 평가 뒤에는
부모 프로세스의 env/model/trainer/checkpoint 참조와 비사용 CUDA cache를 해제한 다음 별도 프로세스로
다음을 만든다.

```text
run_manifest.json
checkpoints/strike_<iteration>.pt
logs/metrics.jsonl
logs/training.log
logs/artifacts.log
logs/sessions.jsonl
evaluations/strike_<iteration>.eval.json
evaluations/strike_<iteration>.motion_diagnostics.json
plots/strike_training_curves.png
videos/strike_<iteration>_rollout_remembered.mp4
videos/strike_<iteration>_rollout_current.mp4
videos/strike_<iteration>_rollout.json
ANALYSIS.md
```

plot, motion audit, 영상 실행은 공통 `_run_logged_tool`을 사용한다. 모든 stdout/stderr는
`artifacts.log`에 남고, 기대 파일이 실제 생성되지 않으면 성공으로 기록하지 않는다. 일부 후처리가
실패해도 checkpoint와 성공 산출물, 실패 종류는 manifest에 남는다. 단, CLI는 불완전한 자동 산출물을
성공으로 오인하지 않도록 마지막에 non-zero 예외를 반환한다.

## 10. 종료 경로

| 종료 원인 | 동작 |
|---|---|
| 정상 iteration 완료 | 마지막 checkpoint 저장 → 평가 → sim 종료 → 자동 산출물 |
| curriculum stalled | 해당 iteration checkpoint 저장 → learn 중단 → 현재 단계 평가 → 자동 산출물 |
| `--eval` | 학습 없이 contract 검증·checkpoint 복원 → deterministic 평가 → 자동 산출물 |
| 사전 검증 실패 | sim 생성 전 중단 |
| StrikeTask 생성 뒤 model/PPO/evaluation 실패 | `finally`에서 sim 종료 후 예외 전파 |
| plot/audit/video 실패 | manifest에 artifact error 기록 후 모든 후처리 종료 시 요약 예외 |

## 11. 2026-08-19 정리·개선 내용

- Torch 비의존 run/checkpoint I/O를 일반 import로 이동하고, runtime loader의 전역 변수 주입을 제거했다.
- simulator/model class loader는 전역 상태를 수정하지 않고 명시적으로 class tuple을 반환한다.
- plot, motion audit, dual-video의 중복 subprocess·파일 확인 코드를 `_run_logged_tool` 하나로 합쳤다.
- 분석/plot/audit/video의 반복적인 성공·오류 manifest 처리를 `_attempt_artifact`로 합쳤다.
- 학습 종료 전의 중복 curriculum 적용을 제거하고 runtime wrapper만 단일 권위로 유지했다.
- curriculum 전이와 stalled가 같은 iteration에 발생할 때 동일 checkpoint를 두 번 쓰지 않는다.
- 장기 학습에서 모든 iteration dict를 RAM에 쌓지 않고 마지막 통계만 보존한다. stalled 예외에서도
  마지막 통계가 `ANALYSIS.md`에서 사라지지 않는다.
- sim 종료 후 GPU 모델과 checkpoint 참조를 해제하고 cache를 비워 자동 audit/video의 OOM 위험을
  줄였다.
- resource preflight를 통과한 뒤 run 디렉터리를 생성하도록 순서를 바꿔 실패한 실행의 빈 폴더를
  남기지 않는다.
- strike 설정 파일에 남아 있던 불필요한 연속 공백을 제거했다.
- checkpoint runtime 상수를 runner에서 test 용도로 재노출하던 불필요한 결합을 제거했다.

## 12. 남은 구조적 개선 후보

- `StrikeTask.step`은 물리 검출, event state machine, metric, 종료 판정을 한 메서드에 조립한다.
  tensor clone과 호출 순서가 성능·정확성 계약이므로 GPU golden rollout 없이 성급하게 분리하지 않는다.
  다음 분리는 detector output→matcher input과 reward/termination snapshot을 golden fixture로 고정한 뒤 한다.
- `PPOTrainer`는 fret/strike 공용이라 진단 key별 특수 aggregation이 함께 있다. 새 task가 추가될 때는
  task별 diagnostic reducer 인터페이스를 두는 것이 적절하다.
- Python/Isaac 객체 삭제와 `empty_cache`는 allocator의 비사용 block을 반환하지만 CUDA context 자체를
  종료하지는 않는다. 자동 영상의 최대 안정성이 필요하면 장기적으로 학습 자체도 parent launcher의
  하위 프로세스로 격리할 수 있다.

## 13. 검증 명령

CPU 계약:

```bash
python tab2body/tests/test_train_task_dispatch.py
python tab2body/tests/test_strike_runner_lazy_import.py
python tab2body/tests/test_strike_training_runtime.py
python tab2body/tests/test_strike_goal_timing.py
python tab2body/tests/test_strike_event_logic.py
python tab2body/tests/test_strike_evaluation_gates.py
python tab2body/tests/test_ppo_actor_advantage.py
```

GPU 전체 배관:

```bash
python train.py --task strike \
  --song 00_SS1-68-E_comp \
  --smoke --num-envs 8 \
  --run-name strike_flow_smoke_20260819
```

smoke는 1 iteration·horizon 4로 줄이고 자동 영상은 끈다. checkpoint/log/evaluation까지 확인한 뒤,
영상 경로는 저장된 checkpoint의 `--eval` 실행 또는 recorder로 별도 검증한다.
