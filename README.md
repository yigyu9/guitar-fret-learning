# github_publish

오디오 입력을 기타 탭·운지 데이터로 변환하고, 이를 Isaac Gym 기반의 왼손 `fret` 및 오른손
`strike` 물리 학습으로 연결하는 프로젝트입니다.

## 프로젝트 구조

```text
.
├── data/                  # 곡별 오디오·annotation·학습 입력
│   └── song_bundles/      # 검수된 곡 단위 입력과 목표 데이터
├── docs/                  # 설계·검증·사용 문서
├── fret/                  # 왼손 fret 학습 문서와 실행 결과 위치
├── strike/                # 오른손 strike 학습 문서와 실행 결과 위치
├── isaacgym/              # NVIDIA Isaac Gym Preview 4 런타임
├── tab2body/              # 물리 환경·reward·PPO·평가·학습 코드
├── tab2fingermapping/     # 오디오→탭·코드·운지 Stage1 파이프라인
├── PROJECT_CONTEXT.md     # 프로젝트 전체 상태와 결정 기록
├── .gitignore
└── .gitattributes
```

| 경로 | 용도 |
|---|---|
| `data/song_bundles/` | 학습에 사용하는 곡별 입력과 목표 데이터 |
| `tab2fingermapping/` | 오디오에서 탭·코드·왼손 운지 생성 |
| `tab2body/` | Isaac Gym 환경, PPO 학습, checkpoint·평가 도구 |
| `fret/` | 왼손 압현 학습 문서와 결과 관리 |
| `strike/` | 오른손 타현 학습 문서와 결과 관리 |
| `docs/` | 공통 설계·검증·실행 문서 |
| `isaacgym/` | 물리 시뮬레이션 런타임 |

`tab2fingering`이라는 폴더는 없으며, 실제 폴더명은 `tab2fingermapping`입니다.
`related_work/`와 `DIGIT/`은 참고·보관용 디렉토리이며 현재 실행에 필수는 아닙니다.

## 처리 흐름

```text
오디오
  → tab2fingermapping
  → data/song_bundles/<song_id>/
  → tab2body + Isaac Gym
  → fret 또는 strike 학습·평가
```

## 실행 환경

물리 학습은 CUDA GPU와 Isaac Gym Preview 4가 설치된 `rl38` conda 환경에서 실행합니다.
오디오 변환 Stage1은 별도의 `tab2fm` 환경을 사용합니다.

물리 학습 환경:

```bash
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR="/tmp/torch_extensions_tab2body"
```

Stage1 환경 설정과 ACE 관련 의존성은 [`tab2fingermapping/SETUP.md`](tab2fingermapping/SETUP.md)를
참조합니다.

## 사용 방법

### 1. 오디오에서 탭·운지 입력 생성

```bash
conda activate tab2fm
cd tab2fingermapping
python pipeline.py /path/to/audio.wav --bpm 117
```

생성 결과를 검수한 뒤 `data/song_bundles/<song_id>/`에 등록합니다.

### 2. 물리 학습 배관 확인

`--smoke`는 전체 시뮬레이터·PPO·checkpoint·평가 저장 경로를 짧게 확인합니다.
최대 8개 환경, 1 iteration으로 실행되며 자동 영상은 생성하지 않습니다.

Fret:

```bash
conda activate rl38
cd "$PROJECT_ROOT"
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name fret_smoke
```

Strike:

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name strike_smoke
```

### 3. Fret 학습 시작

기본 설정은 1,024개 병렬 환경, 5,000 iteration입니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

GPU 메모리가 부족하면 환경 수를 낮춥니다.

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 5000 \
  --run-name fret_s0_512env
```

### 4. Strike 학습 시작

기본 설정은 512개 병렬 환경, 3,000 iteration입니다.

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 3000 \
  --run-name strike_main
```

### 5. 학습 설정과 결과 위치

| 항목 | Fret | Strike |
|---|---:|---:|
| 기본 환경 수 | `1024` | `512` |
| 기본 iteration | `5000` | `3000` |
| PPO horizon | `32` | `32` |
| minibatch 크기 | `4096` | `2048` |
| PPO epoch | `5` | `5` |
| checkpoint 주기 | 500 iteration | 500 iteration |
| 자동 영상 주기 | 1000 iteration | 500 iteration |

실행 결과는 `--run-name`에 따라 다음 위치에 저장됩니다.

```text
fret/training/runs/<run-name>/
├── checkpoints/fret_*.pt
├── logs/metrics.jsonl
├── logs/training.log
├── evaluations/
├── videos/
└── plots/

strike/training/runs/<run-name>/
├── checkpoints/strike_*.pt
├── logs/metrics.jsonl
├── logs/training.log
├── evaluations/
├── videos/
└── plots/
```

checkpoint는 기본적으로 500 iteration마다 저장되며, 학습 종료 시 마지막 iteration도 저장됩니다.
실행 폴더에 이미 학습 기록이 있으면 덮어쓰지 않으므로 새 실험에는 다른 `--run-name`을 사용합니다.

자동 영상이 필요하지 않으면 다음 옵션을 사용합니다.

```bash
python -m tab2body.train --task fret \
  --num-envs 1024 --iterations 500 \
  --no-auto-video --run-name fret_no_video
```

### 6. checkpoint 재개

`--checkpoint`는 모델, optimizer, iteration, global step, curriculum 상태를 복원합니다.
`--iterations`는 checkpoint 이후에 추가로 실행할 iteration 수입니다.

```bash
python -m tab2body.train \
  --task fret \
  --checkpoint fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 500
```

위 명령은 같은 실행 폴더에서 학습을 이어갑니다. 현재 코드와 checkpoint의 학습 계약이 다르면
안전하게 실행을 중단합니다.

정책 가중치만 가져와 새 실행을 시작하려면 Fret에서 `--initialize-from`을 사용합니다.

```bash
python -m tab2body.train \
  --task fret \
  --initialize-from fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_warmstart
```

### 7. checkpoint 평가

`--eval`과 `--checkpoint`를 함께 사용합니다.

```bash
python -m tab2body.train \
  --task fret --eval \
  --checkpoint fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 64 --eval-episodes 64
```

평가 결과는 해당 실행 폴더의 `evaluations/`에 저장됩니다.

## 상세 문서

- [`tab2body/TRAINING.md`](tab2body/TRAINING.md): 물리 학습·평가·checkpoint 상세 사용법
- [`fret/03_training/README.md`](fret/03_training/README.md): Fret 학습 문서
- [`strike/03_training/README.md`](strike/03_training/README.md): Strike 학습 문서
- [`tab2fingermapping/SETUP.md`](tab2fingermapping/SETUP.md): Stage1 설치와 실행 환경
- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md): 프로젝트 전체 상태와 결정 기록

Isaac Gym, ACE, 오디오, annotation, checkpoint를 외부에 배포할 때는 각 구성요소의 라이선스와
재배포 조건을 확인해야 합니다.
