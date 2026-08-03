# tab2body 학습·평가 가이드

> 최종 갱신: 2026-08-03

이 문서는 현재 코드 기준의 Fret/Strike 실행 방법과 checkpoint 관리 규칙을 설명합니다.
과거 37-action·341-observation Fret checkpoint와 과거 Strike checkpoint는 현재 계약과 호환되지
않습니다.

## 1. 환경 준비

모든 학습은 프로젝트 루트에서 실행합니다.

```bash
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR="/tmp/torch_extensions_tab2body"
```

공용 진입점은 `python -m tab2body.train`입니다. `--task fret` 또는 `--task strike`로 runner를
선택합니다.

## 2. 입력 데이터

곡별 정본은 다음 위치에 있습니다.

```text
data/song_bundles/<song_id>/
├── source/
├── mapping/
├── training/
│   ├── fret_training.json
│   ├── hand_position_targets.json
│   └── strike_training.json
├── preview/
└── manifest.json
```

곡 입력을 새로 만들거나 등록하는 절차는 [`data/song_bundles/README.md`](../data/song_bundles/README.md)를
참조합니다. runner에 `--song <song_id>`를 넘기면 해당 번들의 `training/` 파일을 자동으로 선택합니다.

## 3. 현재 task 계약

| 항목 | Fret | Strike |
|---|---:|---:|
| action | 33 | 30 |
| observation | 353 | 263 |
| reward/value | 6 / 6 | 1 / 1 |
| 기본 환경 수 | 1024 | 512 |
| 기본 iteration | 5000 | 3000 |
| PPO horizon | 32 | 32 |
| minibatch | 4096 | 2048 |
| checkpoint 주기 | 500 | 500 |

Fret observation은 다음 블록으로 구성됩니다.

```text
base 180 + goal 128 + previous EMA action 33 + thumb geometry 12 = 353
```

## 4. Smoke 배관 테스트

`--smoke`는 모델 성능을 판단하는 학습이 아니라 환경 생성, PPO update, checkpoint 저장, 평가·로그
생성을 확인하는 짧은 테스트입니다.

자동 축소 설정:

- 최대 8 환경
- 1 iteration
- horizon 4
- PPO epoch 1
- minibatch 32
- 자동 영상 비활성화

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name fret_smoke

python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name strike_smoke
```

정상 종료 후 실행 폴더의 `checkpoints/`, `logs/`, `evaluations/`가 생성되는지 확인합니다.
과거 smoke 결과 파일은 보존하지 않으며, 필요할 때 현재 코드로 다시 생성합니다.

## 5. Fret 학습

### 파일럿

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 500 \
  --run-name fret_s0_pilot
```

### 본 학습

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

GPU 메모리가 부족하면 `--num-envs 512`, `256`처럼 낮춥니다. 현재 resource guard의 검증 상한은
1,024 환경이며, 실행 시작 시 여유 VRAM·RAM·디스크를 확인합니다.

커리큘럼을 특정 단계로 고정하거나 random start를 끄는 옵션은 다음과 같습니다.

```bash
python -m tab2body.train \
  --task fret --curriculum-stage coarse_reach \
  --num-envs 512 --iterations 500 \
  --run-name fret_coarse_probe

python -m tab2body.train \
  --task fret --no-random-start \
  --num-envs 512 --iterations 500 \
  --run-name fret_full_start_probe
```

## 6. Strike 학습

```bash
python -m tab2body.train \
  --task strike --song 02_Jazz1-200-B_solo \
  --num-envs 512 --iterations 3000 \
  --run-name strike_main
```

특정 curriculum stage만 진단하려면 다음처럼 실행합니다.

```bash
python -m tab2body.train \
  --task strike --curriculum-stage A3_TIMED_CROSSING \
  --timing-tolerance-ms 100 \
  --num-envs 512 --iterations 500 \
  --run-name strike_a3_100ms
```

## 7. 실행 산출물

```text
fret/training/runs/<run-name>/
├── run_manifest.json
├── checkpoints/fret_*.pt
├── logs/metrics.jsonl
├── logs/training.log
├── logs/artifacts.log
├── evaluations/
├── videos/
└── plots/

strike/training/runs/<run-name>/
├── run_manifest.json
├── checkpoints/strike_*.pt
├── logs/metrics.jsonl
├── logs/training.log
├── logs/artifacts.log
├── evaluations/
├── videos/
└── plots/
```

기본 checkpoint 저장 주기는 500 iteration이고, 학습 종료 시 마지막 iteration을 별도로 저장합니다.
Fret 자동 영상 주기는 1,000 iteration, Strike 자동 영상 주기는 500 iteration입니다.

영상 생성을 끄려면 다음 옵션을 사용합니다.

```bash
python -m tab2body.train --task fret \
  --num-envs 512 --iterations 500 \
  --no-auto-video --run-name fret_no_video
```

## 8. 학습 재개와 warm-start

`--checkpoint`는 model, optimizer, iteration, global step, curriculum 상태를 복원하는 정식 resume입니다.
`--iterations`는 checkpoint 이후 추가할 iteration 수입니다.

```bash
python -m tab2body.train \
  --task fret \
  --checkpoint ../fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 500
```

`--run-name`을 생략하면 checkpoint가 속한 실행 폴더에 이어 기록합니다. 현재 환경·곡·PPO·asset·구현
지문이 checkpoint 계약과 다르면 resume을 거부합니다.

Fret 정책 가중치만 새 실행에 가져오려면 `--initialize-from`을 사용합니다.

```bash
python -m tab2body.train \
  --task fret \
  --initialize-from ../fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_warmstart
```

이는 새 계약으로 시작하며 optimizer는 기본적으로 새로 초기화합니다. 호환되는 optimizer까지
가져오려면 `--initialize-optimizer`를 추가합니다.

## 9. checkpoint 평가

평가는 `--eval`과 `--checkpoint`를 함께 사용합니다. random start와 reset noise를 끄고 deterministic
rollout을 수행합니다.

```bash
python -m tab2body.train \
  --task fret --eval \
  --checkpoint ../fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 64 --eval-episodes 64

python -m tab2body.train \
  --task strike --eval \
  --checkpoint ../strike/training/runs/strike_main/checkpoints/strike_003000.pt \
  --num-envs 64 --eval-episodes 64
```

평가 JSON은 해당 run의 `evaluations/`에 저장됩니다.

## 10. 로그 확인

- `logs/metrics.jsonl`: PPO·reward·task 지표
- `logs/training.log`: 사람이 읽는 학습 진행 로그
- `logs/artifacts.log`: plot·evaluation·video 생성 로그
- `run_manifest.json`: 입력 hash, 계약 hash, 환경 수, 산출물 경로

checkpoint contract 검증 실패는 안전을 위해 즉시 중단되는 정상 동작입니다. 과거 실행 결과와
현재 실행 결과를 섞지 말고 새 `--run-name`을 사용합니다.
