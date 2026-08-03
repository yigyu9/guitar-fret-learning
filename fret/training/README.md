# Fret 학습 실행 폴더

> 최종 갱신: 2026-08-03

실행 결과는 `runs/<run-name>/` 아래에서 학습·평가·checkpoint 단위로 분리합니다.
`runs/`는 학습 명령이 자동으로 만들며, 실행 기록이 있는 폴더에 새 학습을 덮어쓰지 않습니다.

## 실행

프로젝트 루트에서 다음 환경을 설정합니다.

```bash
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
```

Fret 학습:

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

배관 smoke:

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name fret_smoke
```

`--smoke`는 최대 8 환경, 1 iteration으로 실행되며 자동 영상을 생성하지 않습니다.

## 현재 환경 프로필

- 기본 병렬 환경: 1,024
- PPO horizon: 32
- rollout batch: 32,768
- minibatch: 4,096
- PPO epoch: 5
- checkpoint 저장: 500 iteration마다 및 종료 시 마지막 iteration
- resource guard: 최대 1,024 환경, 시작 시 여유 VRAM/RAM/디스크 확인

현재 Fret 계약은 33 action, 353 observation, 6 reward/value입니다.

```text
observation = base180 + goal128 + previous EMA action33 + thumb geometry12
```

구 37-action 또는 341-observation checkpoint는 현재 계약과 호환되지 않습니다.

## 산출물 구조

```text
fret/training/runs/<run-name>/
├── run_manifest.json
├── checkpoints/
│   └── fret_<iteration>.pt
├── logs/
│   ├── metrics.jsonl
│   ├── training.log
│   ├── artifacts.log
│   └── sessions.jsonl
├── evaluations/
├── videos/
└── plots/
```

`run_manifest.json`에는 song ID, goal·hand-target hash, 차원, checkpoint contract, 환경 수,
하드웨어 및 산출물 경로가 기록됩니다.

## 재개와 평가

재개:

```bash
python -m tab2body.train \
  --task fret \
  --checkpoint runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 500
```

평가:

```bash
python -m tab2body.train \
  --task fret --eval \
  --checkpoint runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 64 --eval-episodes 64
```

재개는 모델·optimizer·iteration·global step·curriculum 상태를 복원합니다. 현재 코드와 입력,
asset, PPO 설정의 contract가 checkpoint와 다르면 안전을 위해 중단합니다.

자동 영상을 끄려면 `--no-auto-video`를 사용합니다. 상세 옵션은
[`tab2body/TRAINING.md`](../../tab2body/TRAINING.md)를 참조합니다.
