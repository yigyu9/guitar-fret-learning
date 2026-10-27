# tab2body 학습·평가 가이드

> 최종 갱신: 2026-09-07

이 문서는 현재 코드 기준의 Fret/Strike 실행 방법과 checkpoint 관리 규칙을 설명합니다.
기존 33-action Fret checkpoint와 과거 Strike checkpoint는 현재 계약으로 strict resume할 수
없습니다. 기본 Fret은 `L_Thorax`를 제외한 30-action/420-observation Fret-v2 정책을 처음부터 학습합니다.
현재 기본 Strike는 named block으로 구성된 `strike.observation.v2` 303D 계약입니다.
321D/327D actor는 v2로 resume하거나 초기화할 수 없으며, 입력 검수를 마친 canonical goal에서
fresh 학습합니다. 327D v1의 과거 S2 objective-transfer 규칙은 v1 호환 실행에만 적용됩니다.

학습 결과를 바탕으로 개선·구현·재학습할 때는
[`학습 개선 기록 운영 규칙`](../docs/TRAINING_IMPROVEMENT_PROCESS.md)을 따릅니다. 환경별 결정과
재시도 금지 항목은
[`Fret 실험 이력`](../docs/archive/dated/2026-08-24/FRET_EXPERIMENT_HISTORY.md)과
[`Strike 실험 이력`](../strike/03_training/EXPERIMENT_HISTORY.md)에 누적합니다.

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
│   ├── strike_training.json
│   └── strike_plan.json
├── preview/
└── manifest.json
```

곡 입력을 새로 만들거나 등록하는 절차는 [`data/song_bundles/README.md`](../data/song_bundles/README.md)를
참조합니다. runner에 `--song <song_id>`를 넘기면 해당 번들의 `training/` 파일을 자동으로 선택합니다.

## 3. 현재 task 계약

| 항목 | Fret | Strike |
|---|---:|---:|
| action | 30 | 30 |
| observation | 420 (v2 기본), 425 (v1 호환) | 303 (v2 기본), 327 (v1 호환) |
| reward/value | 6 / 6 | 1 / 1 |
| 기본 환경 수 | 1024 | 512 |
| 기본 iteration | 5000 | 50000 |
| PPO horizon | 32 | 32 |
| minibatch | 4096 | 2048 |
| checkpoint 주기 | 500 | 500 |

Strike의 30차원 출력 중 어깨·팔꿈치·손목 9차원은 기존 bounded joint target이고, 오른손 21차원은
`pick-grip-reference.json` 기준 residual이다. 엄지·검지는 `±0.08 rad`, 나머지 손가락은
`±0.22 rad` 범위다. 현재 goal compiler profile은 direction `phrase_dp_microtiming_v3`, transition
`entry_side_edge_gap_v2`다. Strike-v2는 관측 ABI와 모델 구조가 함께 바뀌었으므로 v1
checkpoint를 resume이나 `--initialize-from`에 사용하지 않는다.

Fret-v2 observation은 다음 named block으로 구성됩니다.

```text
proprio60 + arm_anchor18 + hand_geometry60 + current_event45
+ target_geometry24 + finger_transition52 + lookahead72
+ readiness_contact45 + phase12 + synchronizer2 + history30 = 420
```

Fret의 제어 순서는 `L_Shoulder`부터 시작한다. `L_Thorax` 3DOF는 정책 제어 없이 초기 PD
자세로 유지한다. 이 변경 전 checkpoint는 `--checkpoint`, `--initialize-from` 모두 사용하지 않는다.
Fret-v1 425D와 Fret-v2 420D도 서로 resume하거나 initialize하지 않는다.

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
  --curriculum-stage A0_PICK_GRIP \
  --smoke --num-envs 8 --run-name strike_a0_smoke
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
  --run-name fret_no_random_start_probe
```

`--no-random-start`는 시작 시점 무작위화만 끄며 손끝 접근 커리큘럼은 유지합니다.
커리큘럼까지 끄려면 `--no-curriculum`을 별도로 지정합니다.

## 6. Strike 학습

먼저 곡 bundle을 읽기 전용으로 감사합니다. `PASS`는 데이터 품질 검사를 통과한 상태,
`AMBIGUOUS`는 사람 검수가 필요한 상태, `INFEASIBLE`은 full-song 학습 금지 상태입니다.

```bash
python -m tab2body.tools.audit_strike_goal_quality \
  --all --format both \
  --out /tmp/strike_goal_quality_audit.txt --strict
```

source timing이나 grouping을 바꿔야 하면 canonical을 직접 덮어쓰지 않습니다. 근거·source event ID·
`merge|separate` 결정을 담은 review JSON으로 `*.proposed.json` 후보를 만들고, 오디오를 사람이 확인한
뒤에만 canonical로 승격합니다. 승격 후 같은 strict audit와 original-tempo preflight를 다시 통과해야
학습을 시작합니다.

2026-08-30에 사용자가 판정을 위임해 `00_SS1-68-E_comp`의 source event 147~149를 하나의 down
strum으로 병합한 후보를 `approved_user_delegated` 상태로 canonical에 승격했습니다. 수동 오디오
청취는 수행하지 않았고 source JAMS·symbolic chord·기존 `46.5 ms < 50 ms` 불가능 경계를 근거로
승인했습니다. 현재 canonical은 104 events(61 single/43 strum), direction v3/transition v2,
최소 edge gap `51.0 ms`, `INFEASIBLE=0`입니다. 전체 strict audit는 exit 0,
`PASS 2 / AMBIGUOUS 6 / INFEASIBLE 0`이며, 이 곡은 남은 source/grouping 경고 때문에
`AMBIGUOUS`지만 original-tempo preflight를 통과합니다. 아래 명령으로 303D v2 계약의 fresh A0 학습을
시작할 수 있습니다. 구 checkpoint의 exact resume은 금지하며, `--initialize-from`은 아래 §8의
감사된 S2 objective-transfer 조건을 만족할 때만 사용합니다.
이미 실행 중인 `20260828_2158_00_SS1-68-E_comp` 프로세스는 메모리에 로드한 구 goal/contract를
사용하므로 새 canonical은 다음 fresh run부터 적용됩니다. 구 입력은 promotion history의 SHA와 파일로
재현할 수 있습니다.

```bash
python -m tab2body.train \
  --task strike --song 00_SS1-68-E_comp \
  --num-envs 1024 --iterations 50000
```

특정 curriculum stage만 진단하려면 다음처럼 실행합니다.

```bash
python -m tab2body.train \
  --task strike --curriculum-stage S1_STRUM_SPAN \
  --num-envs 512 --iterations 500 \
  --run-name strike_s1_probe
```

현재 Strike는 A3 뒤에 실제 strum 문맥의 1줄 clean recovery를 학습하는 A4를 두고, S0에서 처음부터
실제 2줄 strum을 요구한다. 추가 RELEASE나 재무장 전 crossing은 recovery count를 초기화하며,
recovery completion/reset/blocked rate가 승급·평가에 포함된다. A0~S2에서는 down/up을 균형 연습하고,
S2/S3에서는 strum timing RMS와 sweep-duration 오차를 사용한다. 원곡 tempo는
`0→0.25→0.5→0.75→0.9→0.95→0.975→1`로 복원한다.

S2의 허용 오차는 iteration만으로 줄지 않는다. 내부 profile
`E0 endpoint→400→250→225→200→175→150→100→zone 100→67→50 ms`가 현재
completion·양방향·end-to-end recovery·timing pass·signed mean/tail·RMS·duration·보존 gate를
3회 연속 통과할 때만 이동한다.
새 profile의 첫 200 iteration은 적응 구간이며 이때는 rollback하지 않는다. Z0 전에는 lane을 soft
진단/보상으로만 사용하며, 이후 심한 성능 붕괴가 3회 연속이면 한 profile 후퇴한다. 물리 traversal
완료와 timing 성공은 별도 지표로 집계한다.

E0에서는 마지막 줄 하나만 남을 때 final-string→exit를 연속 운동 목표로 사용하고, 그 선분 투영의
최대 진행 증가분과 마지막 RELEASE physical-completion pulse를 timing과 독립적으로 보상한다.
down/up completed/event raw count를 각각 합쳐 낮은 방향 완주율을 gate하며, conditional recovery와
미완료 사건도 분모에 남기는 end-to-end recovery를 함께 본다. 최저 방향 완주율이 `0.60` 미만인
evidence가 3회 연속이면 부족한 방향을 70%로 집중한다. 강제로 바꾸지 않은 60%는 down/up 30/30
balanced holdout이고 승급에는 이 holdout만 사용한다. E0와 T0에서는 첫 9개 어깨·팔꿈치·손목
action의 정책 표준편차 하한을 `0.03`으로 유지한다.

S3는 tempo별 F1/wrong 종료/blocked gate를 사용하고 안전 실패는 항상 0을 요구한다. 정체되면
event별 실패·노출 EMA로 구한 노출 보정 실패율로 episode 시작의 15%를 hard
window에서 뽑고 85%는 전곡에서 균일하게 뽑는다. prior exposure는 16, decay는 0.995이고
하나의 hard window 표집 확률은 최대 10%다. hard episode도 PPO는 학습하지만 stalled S3의
승급 F1/rate는 uniform episode의 raw TP/FP/FN와 blocked/recovery count만 합쳐 계산한다.
주기 영상·deterministic 전체곡 평가 중에는 failure-mining 갱신을 끄고 통계 상태를
복원해 평가가 훈련 분포를 오염시키지 않는다. task generator RNG와 reset generation도 함께
복원하므로 평가용 reset이 이후 학습 표집 난수열을 바꾸지 않는다.

path-aware recovery는 직접 경로에 위험 줄이 있으면 lift와 elevated transfer를 먼저 수행한다. 첫
waypoint에서 다음 waypoint로 목표가 바뀔 때 reach-potential baseline을 reset하며, wrong/blocked가
발생한 event에는 timing·strum microtiming bonus를 지급하지 않는다.

현재 curriculum schema는 `v13`, environment state는 `v14`, Strike-v2 checkpoint contract는
`v14`다. 이전 321D/327D actor는 v2로 전이하지 않는다. 아래 327D S2 actor-only 경로는
`--observation-contract strike.observation.v1`을 명시한 역사적 v1 재현에만 해당한다.

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
Strike는 마지막 완료 영상 이후 1,900 iteration 이상 지난 다음 저장 checkpoint에서 remembered/current
영상을 만들므로 기본 설정에서는 대략 2,000 iteration 간격으로 중간 동작을 보존합니다. S0~S2에서는
down/up을 각각 강제한 두 방향 × 두 카메라의 네 영상을 만들고, S3에서는 계획된 곡 방향의 두 카메라를
만듭니다. 정상 종료나 사용자 중단 시 마지막 checkpoint도 같은 방식으로 생성합니다. 실제 선택·성공·실패 이력은
`logs/periodic_videos.jsonl`에 남습니다. 간격은 `--periodic-video-min-gap`으로 조정할 수 있습니다.

Strike의 deterministic 전체곡 report가 생성되면 안전·grip·F1·event/strum completion·
blocked·wrong·timing 순으로 이전 최고 결과와 비교하고
`evaluations/best_full_song.json`을 원자적으로 갱신합니다. 전체곡 F1이 최고 기준보다
0.01을 초과해 떨어지면 퇴행 경고를 남깁니다.

JSONL은 append pending journal로 내구화합니다. 강제 종료 뒤 저널로 검증되는
마지막 불완전 record만 복구하고 중간 손상·교체된 대상·검증할 수 없는 tail은
fail-closed 합니다.

영상 생성을 끄려면 다음 옵션을 사용합니다.

```bash
python -m tab2body.train --task fret \
  --num-envs 512 --iterations 500 \
  --no-auto-video --run-name fret_no_video
```

Strike는 같은 위치에 `--task strike --no-auto-video`를 사용합니다. 이 옵션은 학습 중 주기 영상과
종료 영상을 함께 끕니다. 자동 plot과 motion audit까지 끄려면 `--no-auto-artifacts`를 함께 지정합니다.

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

Strike의 일반 warm-start는 허용하지 않습니다. 다만 동일한 327D 관측·30 action·goal/grip/asset과
direction `phrase_dp_microtiming_v3`, transition `entry_side_edge_gap_v2`, recovery
`path_aware_clearance_handoff.v1` interface를 가진 S1 최종 또는 S2 진입 직후 checkpoint는 아래처럼
명시적 S2 objective transfer를 할 수 있습니다. source actor·observation normalizer·학습된 `log_std`만
복사하고 critic·optimizer·iteration·curriculum·환경 RNG를 초기화합니다.

```bash
python -m tab2body.train \
  --task strike \
  --song 00_SS1-68-E_comp \
  --initialize-from /home/ajou/yigyu/3/strike/training/runs/20260830_1928_00_SS1-68-E_comp/checkpoints/strike_003147.pt \
  --initialize-stage S2_TIMED_STRUM \
  --allow-policy-objective-transfer \
  --num-envs 1024 --iterations 50000
```

`strike_003147.pt`는 S2 `stage_iteration=0`, evidence 0인 기준 소스입니다. late/stalled S2나 6줄
학습이 확인되지 않은 source는 거부하며 이 경로는 exact resume이 아닙니다.

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

- `logs/metrics.jsonl`: 기본 10 iteration 간격과 단계 변경·checkpoint·종료 시점의 scalar 지표
- `logs/training.log`: 사람이 읽는 학습 진행 로그

압현 성공 통계는 비율과 분자·분모를 함께 기록한다.

- `sustain_event_success_total / sustain_event_total`: 성공한 압현 유지 이벤트 수
- `press_success_frames / press_target_frames`: 전체 목표 압현 프레임 판정
- `finger_N_press_success_frames / finger_N_press_target_frames`: 손가락별 프레임 판정
- `curriculum_success_episodes / curriculum_episode_total`: 커리큘럼 성공 episode 수
- `chord_set_S_success_episodes / chord_set_S_target_episodes`: 손가락 조합별 성공 episode 수
- `sustain_event_success_rate_pooled`, `press_success_rate`, `finger_N_press_success_rate`: 각 비율
- `logs/artifacts.log`: plot·evaluation·video 생성 로그
- `run_manifest.json`: 입력 hash, 계약 hash, 환경 수, 산출물 경로

checkpoint contract 검증 실패는 안전을 위해 즉시 중단되는 정상 동작입니다. 과거 실행 결과와
현재 실행 결과를 섞지 말고 새 `--run-name`을 사용합니다.
