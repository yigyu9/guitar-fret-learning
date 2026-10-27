# tab2body

`tab2body`는 `data/song_bundles/<song_id>/training/`의 곡별 목표를 Isaac Gym 물리 환경과
PPO 학습으로 실행하는 패키지입니다. 왼손 `fret`과 오른손 `strike`를 독립 학습하며,
`full`은 현재 두 checkpoint를 검증·조립하는 CPU-safe G0 계약 runner입니다.

StabilityAdapter는 재구성 중이며 현재 `tab2body`에 실행 가능한 task가 없다.

## 구조

```text
tab2body/
├── train.py                 # fret|strike|full 공용 진입점
├── train_fret.py            # Fret runner
├── train_strike.py          # Strike runner
├── train_full.py            # G0 checkpoint assembly/contract probe
├── cfg.py                   # Fret 설정
├── strike_cfg.py            # Strike 설정
├── env/
│   ├── base.py              # Isaac Gym 공통 환경·PD·reset·관측
│   ├── goals.py             # Fret goal 로더·관측
│   ├── tasks/task_fret.py   # Fret task
│   └── tasks/task_strike.py # Strike task
├── full/                    # canonical event, rule Sync, 105D named ABI / 97D effective DOF runtime 계약
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
├── strike_training.json
└── strike_plan.json
```

`strike_training.json`은 원본 `[time, frame, string]`, `strike_plan.json`은 곡 전체에서
single/strum과 down/up을 확정한 RL 입력입니다. `--song <song_id>`는 후자를 선택합니다. 입력 생성·검수·등록은
[`data/song_bundles/README.md`](../data/song_bundles/README.md)를 참조합니다.

## 학습 실행

공용 진입점은 태스크를 먼저 선택한 뒤 해당 runner만 불러옵니다.

### Fret

현재 기본 Fret-v2 계약은 30 action, 420 observation, 6 reward/value입니다. `L_Thorax`는 정책 행동에서
제외해 초기 자세의 PD target으로 유지합니다. 기본 설정은 1,024 환경,
5,000 iteration입니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

GPU 메모리가 부족하면 `--num-envs 512` 또는 더 낮은 값을 사용합니다.

### Strike

현재 기본 Strike-v2 계약은 30 action, 303 observation, scalar reward/value입니다. 기존
327D Strike-v1은 `--observation-contract strike.observation.v1`로만 선택하는 호환
baseline입니다. 기본 설정은 512 환경, 50,000 iteration입니다. S2는
`E0_BALANCED_ENDPOINT`에서 down/up 마지막 줄·exit 완주를 먼저
확보한 뒤 timing profile을 줄입니다.

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 50000 \
  --run-name strike_main
```

S0~S2의 주기 진단은 down/up 각각을 두 고정 카메라로 저장합니다. 이전 checkpoint의 exact resume과
제한된 S2 actor-only objective transfer 조건은 [`TRAINING.md`](TRAINING.md)를 따릅니다.

### Full G0 계약 조립

`full`은 PPO 학습 명령이 아니다. 같은 곡의 Fret-v2·Strike-v2 checkpoint를 strict-load하고
Canonical PlayEvent, rule Synchronizer, 105D named action manifest(실질 가동 97D)를 검증한다. 현재 probe는 Isaac Gym
물리 연주가 아니라 CPU tensor/contract integration 검사다.

```bash
python -m tab2body.train --task full \
  --song 02_Jazz1-200-B_solo \
  --fret-checkpoint /path/to/fret_checkpoint.pt \
  --strike-checkpoint /path/to/strike_checkpoint.pt \
  --output full/04_training/bundles/02_Jazz1-200-B_solo.g0.json
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
