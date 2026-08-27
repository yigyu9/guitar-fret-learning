# tab2body 학습 코드 구조

> 최종 갱신: 2026-08-19

현재 실행 가능한 물리 RL 태스크는 왼손 fret과 새 pick-only 오른손 strike다. strike는 제거된
과거 pilot을 복원한 것이 아니라 최소 goal과 A0~A4 curriculum으로 다시 구현했으며 이전
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
- `env/tasks/task_fret.py`: 33-action/428-observation fret 조립
- `env/tasks/task_strike.py`: 30-action/281-observation strike 조립
- `learning/`: 모델, PPO, fret/strike curriculum·평가·checkpoint/run 계약
- `train.py`: fret/strike 공용 학습 진입점 (`--task fret|strike`)
- `song_bundles.py`: `data/song_bundles/<song_id>` 정본 경로와 곡 ID 해석
- `cfg.py`, `strike_cfg.py`: 왼손 fret/오른손 strike 설정
- `train_fret.py`, `train_strike.py`: 공용 진입점에서 같은
  `build_parser()`·`main()` 계약으로 불러오는 태스크별 실행기

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
각각 `training/fret_training.json`과 `training/strike_training.json`으로 해석된다.

## strike 상태

- 입력: `tab2body.strike_training.v1/v2`, 필수 `[time,frame,string]`
- 제어/관측/출력: 30 action, 281 observation, scalar value/reward
- 피크/줄: 질량 없는 `RH:pick` 기준점과 고정 유한 선분 6개
- 성공: 방향·속도·깊이를 만족한 swept crossing 직후 RELEASE
- 학습: A0 grip → A1 ready → A2 crossing → A3 timing → A4 zone
- 시간: 성능 gate에 따라 100→67→50 ms
- 증거: A1~A4 완료 episode exact 지표, 허용창 전 target crossing timing p95
- A4 위치: preferred lane 중심, `±6 mm` 만점·`±12.5 mm` 성공
- 산출물: checkpoint/log/evaluation/analysis/plot/remembered+current MP4

진입부터 종료까지의 모듈별 실제 호출 계약은
[`docs/2026-08-19/STRIKE_TRAIN_EXECUTION_FLOW.md`](../docs/2026-08-19/STRIKE_TRAIN_EXECUTION_FLOW.md)를
기준으로 한다.

과거 806-observation/593D goal/iteration 강제 승급 계약과 그 checkpoint는 현행이 아니다.

Fret의 현재 observation은 기본 180 + goal 128 + 이전 action 33 + thumb geometry 12 +
미래 goal 문맥 75로 총 428차원이다. 이전 353차원 정책은 `--initialize-from`으로만 확장하며,
구 341-observation 또는 37-action checkpoint는 현재 계약으로 strict resume하지 않는다.

배관 검증은 별도 legacy smoke 파일이 아니라 공용 진입점으로 실행한다.

```bash
python -m tab2body.train --task fret --smoke --num-envs 8 --run-name fret_smoke
python -m tab2body.train --task strike --smoke --num-envs 8 --run-name strike_smoke
```
