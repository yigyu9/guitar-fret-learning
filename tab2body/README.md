# tab2body

`tab2body`는 `data/song_bundles/<song_id>/training/`의 곡별 목표를 Isaac Gym 물리 환경과
PPO 학습으로 실행하는 패키지입니다. 현재 실행 가능한 태스크는 왼손 `fret`과 오른손
`strike`입니다.

## 구조

```text
tab2body/
├── train.py                 # --task fret|strike 공용 진입점
├── train_fret.py            # Fret runner
├── train_strike.py          # Strike runner
├── cfg.py                   # Fret 설정
├── strike_cfg.py            # Strike 설정
├── env/
│   ├── base.py              # Isaac Gym 공통 환경·PD·reset·관측
│   ├── goals.py             # Fret goal 로더·관측
│   ├── tasks/task_fret.py   # Fret task
│   └── tasks/task_strike.py # Strike task
├── learning/                # ActorCritic·PPO·curriculum·평가·checkpoint 계약
├── tools/                   # 데이터 생성·plot·rollout·runtime 감사
├── tests/                   # CPU/GPU 회귀 테스트
└── _gen/                    # 재생성 가능한 중간 산출물
```

정본 곡 입력은 `../data/song_bundles/`에 두고, `tab2body/_gen/`은 생성물·진단용으로만
사용합니다. 실행 결과는 `../fret/training/runs/` 또는 `../strike/training/runs/`에 저장됩니다.

## 실행 환경

프로젝트 루트에서 Isaac Gym의 Python 경로를 먼저 설정합니다.

```bash
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR="/tmp/torch_extensions_tab2body"
```

## 입력 데이터

곡별 입력은 다음 파일을 사용합니다.

```text
data/song_bundles/<song_id>/training/
├── fret_training.json
├── hand_position_targets.json
└── strike_training.json
```

`--song <song_id>`를 지정하면 해당 번들의 입력을 자동으로 선택합니다. 입력 생성·검수·등록은
[`data/song_bundles/README.md`](../data/song_bundles/README.md)를 참조합니다.

## 학습 실행

공용 진입점은 태스크를 먼저 선택한 뒤 해당 runner만 불러옵니다.

### Fret

현재 Fret 계약은 33 action, 353 observation, 6 reward/value입니다. 기본 설정은 1,024 환경,
5,000 iteration입니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

GPU 메모리가 부족하면 `--num-envs 512` 또는 더 낮은 값을 사용합니다.

### Strike

현재 Strike 계약은 30 action, 263 observation, scalar reward/value입니다. 기본 설정은 512 환경,
3,000 iteration입니다.

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 3000 \
  --run-name strike_main
```

### Smoke

`--smoke`는 장시간 성능 학습이 아니라 simulator·PPO·checkpoint·평가 저장 경로를 확인하는
배관 테스트입니다. 환경은 최대 8개, 1 iteration, horizon 4, PPO epoch 1, minibatch 32로
자동 축소되며 자동 영상은 만들지 않습니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name fret_smoke

python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name strike_smoke
```

## checkpoint와 평가

기본 checkpoint 저장 주기는 500 iteration이며 학습 종료 시 마지막 iteration도 저장합니다.

```text
fret/training/runs/<run-name>/checkpoints/fret_*.pt
strike/training/runs/<run-name>/checkpoints/strike_*.pt
```

학습 재개:

```bash
python -m tab2body.train \
  --task fret \
  --checkpoint ../fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 500
```

`--checkpoint`는 모델·optimizer·iteration·global step·curriculum 상태를 복원합니다. 현재
환경·곡·PPO·구현 계약과 호환되지 않는 checkpoint는 로드하지 않습니다.

평가:

```bash
python -m tab2body.train \
  --task fret --eval \
  --checkpoint ../fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 64 --eval-episodes 64
```

평가 결과는 checkpoint가 속한 실행 폴더의 `evaluations/`에 저장됩니다.

## 관련 문서

- [`TRAINING.md`](TRAINING.md): 학습·평가·재개 상세 절차
- [`STRUCTURE.md`](STRUCTURE.md): 모듈과 태스크 계약
- [`../fret/03_training/README.md`](../fret/03_training/README.md): Fret 문서
- [`../strike/03_training/README.md`](../strike/03_training/README.md): Strike 문서
