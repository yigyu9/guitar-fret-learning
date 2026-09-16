# Fret 학습 문서

> 최종 갱신: 2026-09-07 — Fret-v2 기본 계약

Fret은 한 곡의 60Hz 운지 goal을 반복 최적화하는 왼손 물리 학습입니다. 현재 기본 실행 계약은
30 action, 420 observation, 6 reward/value이며, 곡을 섞은 범용 정책이 아니라 곡별 정책을
별도로 학습합니다.

## 입력

기본 곡은 `02_Jazz1-200-B_solo`입니다.

```text
data/song_bundles/02_Jazz1-200-B_solo/
├── source/audio.wav
├── mapping/fingering.json
└── training/
    ├── fret_training.json
    └── hand_position_targets.json
```

현재 S0 입력은 60Hz, 861 frame, 42개 단음, 4~7프렛, 바레 없음입니다. 각 줄의 목표는
`PRESS`, `NO_PRESS`, `DONT_CARE` 상태로 해석되며, 명시 바레와 같은 손가락의 다중 줄 목표는
현재 기본 계약에서 거부합니다.

## 현재 학습 계약

```text
action       = 30
observation  = 420 (fret.observation.v2)
reward/value = 6 / 6
observation  = proprio60 + arm_anchor18 + hand_geometry60 + current_event45
               + target_geometry24 + finger_transition52 + lookahead72
               + readiness_contact45 + phase12 + synchronizer2 + history30
```

Fret-v1 425D는 `--observation-contract fret.observation.v1`로만 선택하는 호환 baseline이다.
Fret-v1과 v2 checkpoint는 서로 resume하거나 actor-only 초기화하지 않는다.

Fret의 기본 설정은 1,024 병렬 환경, 5,000 iteration, horizon 32, minibatch 4,096입니다.
checkpoint는 기본 500 iteration마다 저장되고 학습 종료 시 마지막 iteration도 저장됩니다.

`L_Thorax`를 제어하던 기존 33-action 정책은 action head와 actuator-state 관측이 달라 재사용하지
않습니다. strict resume은 새 30-action 계약 hash와 goal·asset·구현 지문이 모두 일치해야 합니다.

## 실행

프로젝트 루트에서 환경을 설정합니다.

```bash
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export TORCH_EXTENSIONS_DIR="/tmp/torch_extensions_tab2body"
```

배관 확인:

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --smoke --num-envs 8 --run-name fret_smoke
```

파일럿:

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 500 \
  --run-name fret_s0_pilot
```

본 학습:

```bash
python -m tab2body.train \
  --task fret --song 02_Jazz1-200-B_solo \
  --num-envs 1024 --iterations 5000 \
  --run-name fret_s0
```

GPU 메모리가 부족하면 `--num-envs 512` 또는 `256`으로 낮춥니다. `--smoke`는 성능 학습이
아니라 최대 8 환경, 1 iteration의 실행 배관 검사입니다.

## checkpoint 재개·평가

재개:

```bash
python -m tab2body.train \
  --task fret \
  --checkpoint fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 1024 --iterations 500
```

평가:

```bash
python -m tab2body.train \
  --task fret --eval \
  --checkpoint fret/training/runs/fret_s0/checkpoints/fret_005000.pt \
  --num-envs 64 --eval-episodes 64
```

재개·평가 절차와 `--initialize-from`, curriculum 옵션은
[`tab2body/TRAINING.md`](../../tab2body/TRAINING.md)에 정리되어 있습니다.

## 과거 실행 기록

`fret/training/runs/20260803_*`는 이전 33-action 계약의 역사 기록입니다.

| 실행 | 설정 | 상태 |
|---|---|---|
| `20260803_1327_02_Jazz1-200-B_solo` | 1,024 env, 500 iteration | checkpoint·평가·영상 보존 |
| `20260803_1352_02_Jazz1-200-B_solo` | 1,024 env, 500 iteration | checkpoint·평가 보존 |

이 기록들은 현재 30-action 계약과 호환되지 않으며 재개·평가에 사용하지 않습니다. 새 학습은
처음부터 별도 run으로 생성합니다.

## 산출물 구조

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
```

학습 중 생성되는 run 산출물은 `.gitignore` 대상입니다. 정본 goal·설계 문서와 실행에 필요한
소스만 저장소에 포함하고, checkpoint·log·rollout은 별도로 보관합니다.
