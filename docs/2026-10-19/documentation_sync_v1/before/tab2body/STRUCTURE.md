# tab2body 학습 코드 구조

> 최종 갱신: 2026-09-07

현재 실행 가능한 물리 RL 태스크는 왼손 fret과 새 pick-only 오른손 strike다. strike는 제거된
과거 pilot을 복원한 것이 아니라 최소 goal과 A0~A4/S0~S3 curriculum으로 다시 구현했으며 이전
checkpoint와 호환되지 않는다.

## 공용 학습 구조

```text
ActorCritic
    ↓ bounded action
BaseEnv + task-specific goal/reward
    ↓ observation, reward, done
PPOTrainer
    └─ policy/value update
```

- `env/base.py`: Isaac Gym 세계, action/PD/reset/물리·관측 공용 코어
- `env/goals.py`: fret goal
- `env/strike_goal_compiler.py`, `env/strike_goals.py`: strike 입력 검증, single/strum compile과 시간표
- `env/strike_detector.py`, `env/strike_events.py`: 물리 RELEASE 검출과 ordered event 상태 전이
- `env/rewards/fret.py`: fret 보상
- `env/rewards/strike.py`: stage별 strike 보상
- `env/tasks/task_fret.py`: 30-action/420-observation Fret-v2 조립과 425D v1 호환 모드
- `env/tasks/task_strike.py`: 30-action/303-observation Strike-v2 조립과 327D v1 호환 모드
- `strike_v2_contract.py`: 303D named-block 관측 ABI와 검증 packer
- `learning/strike_v2_model.py`: block encoder 기반 Strike-v2 actor/critic
- `fret_v2_contract.py`, `learning/fret_v2_model.py`: 420D named-block Fret-v2 ABI와 actor/critic
- `full/`: Canonical PlayEvent, one clock/cursor, rule Synchronizer, frozen source loader,
  source postprocessing, 105D named action bridge(실질 가동 97D)와 CPU runtime
- `learning/`: 모델, PPO, fret/strike curriculum·평가·checkpoint/run 계약
- `train.py`: fret/strike 학습과 full G0 조립 진입점 (`--task fret|strike|full`)
- `song_bundles.py`: `data/song_bundles/<song_id>` 정본 경로와 곡 ID 해석
- `cfg.py`, `strike_cfg.py`: 왼손 fret/오른손 strike 설정
- `train_fret.py`, `train_strike.py`: 공용 진입점에서 같은
  `build_parser()`·`main()` 계약으로 불러오는 태스크별 실행기
- `train_full.py`: 동일 곡 source checkpoint 조립과 CPU interface probe

공용 진입점은 Isaac Gym이나 태스크 구현을 먼저 import하지 않는다. 태스크를 고른 뒤 해당
실행기만 import하므로 fret 코드가 strike 학습의 선행 의존성이 되지 않는다. 이 구조 변경은
두 태스크의 구현 지문에 포함되므로 변경 전 checkpoint는 resume하지 않고 새 학습을 시작한다.

실행은 프로젝트 루트에서 Isaac Gym 경로를 설정한 뒤 수행한다.

```bash
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
```

공용 PPO에는 Isaac Gym의 재사용 관측 버퍼를 rollout 시점에 복사하는 수정이 남아 있다. 이는
strike 전용 기능이 아니라 모든 태스크의 과거 관측을 보존하는 공용 정확성 수정이다.

## 곡 입력 경계

`tab2fingermapping/_gen`은 전사 작업 공간이고 `tab2body/_gen`은 재생성 가능한 실험 산출물이다.
검수 후 환경이 읽는 정본은 [`data/song_bundles`](../data/song_bundles/) 하나로 통일한다.
각 곡은 `source/`, `mapping/`, `training/`, `preview/`, `manifest.json`을 가지며,
`cfg.py`와 `strike_cfg.py`의 기본 goal도 이 경로를 사용한다. runner의 `--song <song_id>`는
각각 `training/fret_training.json`과 `training/strike_plan.json`으로 해석된다.

## strike 상태

- 원본 입력: `tab2body.strike_training.v3`(v1/v2도 읽음), 필수 `[time,frame,string]`
- RL 입력: `tab2body.strike_plan.v4`, `[time,frame,gesture,strings,direction]`와 줄별 timing offset
- 방향: 줄 재통과까지 비용화한 곡 전체 계획 `phrase_dp_microtiming_v3`; 실행 중 정책이 방향을 바꾸지 않음
- 제어/관측/출력: 30 action, 기본 v2 303 observation, scalar value/reward. 손가락 21 action은
  엄지·검지 `±0.08 rad`, 자유 손가락 `±0.22 rad`의 기준 자세 residual
- 피크/줄: 질량 없는 `RH:pick` 기준점과 고정 유한 선분 6개
- 성공: 방향·속도·깊이를 만족한 swept crossing 직후 RELEASE
- 학습: A0 grip → A1 ready → A2 single crossing → A3 timed single → A4 strum-context clean recovery → S0 실제 2줄 → S1 3~6줄 → S2 `E0` 양방향 끝줄/exit 완주 후 timed strum → S3 song
- 시간: 성능 gate에 따라 100→67→50 ms
- 증거: A0~S3 grip mean/p05/group/bad-streak와 완료 episode exact 지표, 허용창 전 target crossing timing p95, strum traversal/order/direction, raw-count pooled down/up 최저 방향, conditional/end-to-end recovery completion/reset/blocked rate
- S2/S3 위치: preferred lane 중심, `±6 mm` 만점·`±12.5 mm` 성공
- 산출물: checkpoint/log/evaluation/analysis/plot/remembered+current MP4. S0~S2 주기 진단은
  down/up을 각각 강제한 두 방향 × 두 카메라의 짝 영상과 방향별 report를 저장한다.

진입부터 종료까지의 현재 호출 계약은 [`strike/RIGHT_HAND_RULES.md`](../strike/RIGHT_HAND_RULES.md)와
`strike_plan.v4` compiler를 기준으로 한다.

과거 806-observation/593D goal/iteration 강제 승급 계약과 그 checkpoint는 현행이 아니다.

Fret의 현재 기본 observation은 420D named-block Fret-v2다. 425D는 v1 호환 모드다.
`L_Thorax`는 초기 자세의 PD target으로 유지한다.
기존 33-action checkpoint는 action head와 actuator-state 관측이 달라 재사용하지 않는다.

배관 검증은 별도 legacy smoke 파일이 아니라 공용 진입점으로 실행한다.

```bash
python -m tab2body.train --task fret --smoke --num-envs 8 --run-name fret_smoke
python -m tab2body.train --task strike --smoke --num-envs 8 --run-name strike_smoke
```
