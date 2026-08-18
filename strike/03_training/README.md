# 3. 현재 strike 학습·검증 계약

> 최종 갱신: 2026-08-19. 2026-07-27 실행 기록은 historical reference이며 현재 소스와 checkpoint
> 계약이 다를 수 있다. 배관 검증은 현재 코드에서 `--smoke`로 다시 실행한다.

## 2026-08-19 실행 흐름·runner 정리

`train.py --task strike`부터 goal compile, Isaac Gym 환경, PPO iteration, checkpoint·평가, sim 종료,
자동 분석·진단·두 영상까지의 실제 호출 흐름과 각 모듈의 입력/출력을
[`docs/2026-08-19/STRIKE_TRAIN_EXECUTION_FLOW.md`](../../docs/2026-08-19/STRIKE_TRAIN_EXECUTION_FLOW.md)에
정리했다. runner의 전역 runtime 주입, 반복 subprocess/manifest 처리, 중복 curriculum 적용과 장기
history 보존을 제거했다. 환경 종료 뒤 학습 CUDA 객체를 해제하고 자동 산출물을 실행한다.

## 2026-08-18 dense event·ordered strum·오타현·관절 진단

가까운 사건의 easy/runtime gap 진단, subframe 순서 기반 strum matcher, single/strum 분리 평가,
후기 tempo 오타현 budget 종료와 오른손 joint-limit soft 진단을 구현했다. strum observation은 완료한
traversal mask와 다음 줄을 포함한다. 사람 reference motion은 검증 schema와 profile 생성기까지만
구현했으며 실제 데이터 전에는 보상으로 활성화하지 않는다. 상세 내용과 GPU 확인 명령은
[`docs/2026-08-18/STRIKE_DENSE_STRUM_NATURAL_MOTION_IMPLEMENTATION.md`](../../docs/2026-08-18/STRIKE_DENSE_STRUM_NATURAL_MOTION_IMPLEMENTATION.md)에 기록했다.

## 2026-08-10 가까운 사건·strum·원템포 커리큘럼

원본 `strike_training.v1/v2` 파일은 수정하지 않고 goal compiler가 학습용 제스처를 만든다.

- 물리 회복 한계보다 가까운 서로 다른 줄 사건은 한 번의 `strum`으로 묶는다.
- strum은 첫 줄에서 마지막 줄까지의 연속 `traversal_mask`를 완주해야 완료된다. 그 사이의
  비발음 줄도 물리적으로 통과해야 하며 `audible_mask`와는 별도로 보존한다.
- 가까운 같은 줄 재타현은 현재 down-only 제어로 거짓 학습하지 않고
  `alternate_restrike` 미지원 오류로 중단한다.
- A4의 초기 시간표는 인접 사건을 넓히되 원본 시각을 별도로 보존한다. 성능 gate를 통과할 때
  `tempo_lambda=0→0.25→0.5→0.75→0.9→1`로 진행하며, `1`에서 다시 통과해야만 curriculum이
  완료된다.
- 시간창은 사건마다 앞·뒤 간격의 45% 이하로 줄이는 비대칭 창을 사용한다. 따라서 가까운
  사건에서도 두 matcher 창이 겹치지 않는다.
- `tempo_lambda=1`에 도달한 checkpoint만 deterministic 전체곡 평가를 수행한다. 미완료 checkpoint는
  저장된 현재 tempo의 8-event phrase로 평가하여 학습 분포와 평가 분포를 일치시킨다.

`00_SS1-68-E_comp`의 동시 onset도 v2 입력으로 생성되며 176개 source event가
61개 single pick과 43개 strum, 총 104개 실행 제스처로 컴파일된다.

## 2026-08-13 A2 ready 기술 보존

A2 이후 ready 보상이 사라져 crossing만 수행하고 A1 ready 기술을 잃는 실패를 수정했다.
A2~A4는 ready 획득 전 위치 오차 페널티와 ready pulse 보너스를 유지하며, ready 이전 crossing은
물리 진단에는 남지만 crossing·timing·zone 보상을 받지 않고 별도 페널티를 받는다.
`curriculum_success_rate`도 A2 이후 ready 성공을 반드시 포함한다. 최대 stage iteration에서
`stalled`가 되면 checkpoint를 저장하고 자동 종료한다. 상세 근거와 재학습 기준은
[`docs/2026-08-13/STRIKE_A2_READY_RETENTION.md`](../../docs/2026-08-13/STRIKE_A2_READY_RETENTION.md)에 기록했다.

## 2026-08-16 A4 phrase lane 안정화

`20260813_1233_00_SS1-68-E_comp`는 A4의 `tempo_lambda=0`에서 recall 약 0.47로 정체됐다.
원인은 입력에 없는 lane 목표를 매 이벤트마다 다시 무작위 지정해 연속 타현 중 불필요한 줄 방향 이동을
요구한 것이었다. 이제 preferred 영역의 lane을 episode 시작에 한 번 표본화하고 8-event phrase 동안
고정한다. `target_lane_shift_m` 진단값은 phrase 내부에서 0이어야 한다. 평가·motion audit·일반 영상·
시각화 영상도 checkpoint가 저장한 tempo를 보존하며, 원래 tempo에 도달한 checkpoint만 전체 곡으로
전환한다. 상세 근거는
[`docs/2026-08-16/STRIKE_A4_PHRASE_LANE.md`](../../docs/2026-08-16/STRIKE_A4_PHRASE_LANE.md)에 기록했다.

2026-07-27 재설계판은 실행 가능한 상태였다. 과거 S0 환경과 checkpoint는 복원하지 않았으며,
새 코드는 다음 다섯 기술을 순서대로 습득한다.

```text
A0_PICK_GRIP
→ A1_TIP_READY
→ A2_FREE_CROSSING
→ A3_TIMED_CROSSING (±100 → ±67 → ±50 ms)
→ A4_ZONE_CONTROL (tempo λ: 0 → 0.25 → 0.5 → 0.75 → 0.9 → 1)
```

iteration 수만으로는 승급하지 않는다. 각 단계의 최소 iteration 이후 성능 gate를 연속 3회
통과해야 하며, 최대 iteration에 도달해도 자동 승급하지 않고 `stalled`로 남는다. A0~A4의
판정은 완료된 episode의 정확한 `strike_*` 지표만 사용한다. 한 PPO rollout 안에 완료 episode가
없으면 성공도 실패도 아닌 **no evidence**로 처리해 기존 연속 통과 횟수를 유지한다.

## 단계별 의미

| 단계 | 새로 학습하는 것 | 시간/영역 적용 |
|---|---|---|
| A0 | guitar 연구 frame 2227에서 얻은 피크 그립 자세 유지 | 타현 없음 |
| A1 | 6개 줄 각각의 downstroke 진입측 ready 위치 도달 | 타현은 모두 FP |
| A2 | 준비·접근 뒤 목표 줄을 유효하게 통과 | timing/zone은 진단만 |
| A3 | 0.75–1.5초에 배치한 6줄 균형 단일 타현 | 허용 오차 100→67→50 ms |
| A4 | 원래 `[time, frame, string]` 곡 사건 실행 | 50 ms, global zone과 sampled lane band 모두 만족 |

A4의 release 위치는 preferred 구간 안에서 episode마다 샘플링한다. 따라서 중앙 한 점을 외우는
정책이 아니라 허용된 영역의 여러 phrase lane을 학습하되, 한 phrase 안에서는 사람처럼 같은 타현
영역을 유지한다. 각 sampled lane은 점이 아니라 `±6 mm`에서 만점이고 `±12.5 mm`까지 성공 가능한
띠다.

## 승급 gate

모든 단계는 앞 단계 기술을 계속 만족해야 한다.

| 단계 | 완료 episode에서 읽는 지표 | 현재 curriculum gate |
|---|---|---|
| A0 | `strike_grip_success_rate`, `failure_termination` | grip success ≥ 0.90, failure = 0 |
| A1 | `strike_grip_success_rate`, `strike_tip_ready_success_rate` | grip ≥ 0.90, ready ≥ 0.85 |
| A2 | 위 지표 + `strike_release_recall`, `strike_false_positive_rate` | recall ≥ 0.80, FP rate ≤ 0.05 |
| A3 100 ms | 위 지표 + `strike_episode_f1`, `strike_timing_p95_ms` | F1 ≥ 0.80, p95 ≤ 100 ms |
| A3 67 ms | 동일 | F1 ≥ 0.90, p95 ≤ 67 ms |
| A3 50 ms | 동일 | F1 ≥ 0.95, p95 ≤ 50 ms |
| A4 완료 | 위 지표 + `strike_zone_success_rate` | F1 ≥ 0.98, zone ≥ 0.95, p95 ≤ 50 ms |

A1~A4도 표의 성능 지표와 함께 완료 episode의 `failure_termination=0`을 반드시 만족한다.

timing MAE/p95는 성공으로 인정된 타현만 모으지 않는다. 올바른 줄·방향을 실제로 통과한
모든 target attempt를 **시간 허용창과 zone gate 적용 전**에 기록한다. 따라서 너무 이르거나 늦은
타현도 timing tail에 남고 p95 gate를 우회할 수 없다. 내부 motor phase는 matcher hard gate가 아니며,
phase가 어긋난 RELEASE는 step의 `release_phase_violation`, PPO 로그의
`curriculum_release_phase_violation` 진단으로 따로 남긴다.
여러 완료 episode의 raw 절대 오차 표본을 합친 뒤 한 번의 global p95를 계산한다.

A3의 miss는 시간창이 닫히면 즉시 episode를 끝낸다. hit는 12-frame
`RELEASE_RECOVER` 뒤 끝난다. A4의 마지막 hit도 같은 12-frame 회복을 보존한다.
기본 A4 학습 episode는 임의 시작점에서 연속 8개 event를 사용하고 첫 목표 30 frame 전부터
준비한다. deterministic 평가는 전체 42개 event를 사용한다.

위 표는 curriculum 진행 기준이다. 최종 deterministic A4 평가는 더 엄격한
precision/recall/F1/zone `0.99`, false-positive rate `≤0.01`, timing p95 `≤50 ms`를 사용하고,
수치 통과 뒤에도 영상의 사람 검토를 요구한다.

## 실행

기본 3,000 iteration:

```bash
python -m tab2body.train \
  --task strike --run-name strike_main
```

500 iteration:

```bash
python -m tab2body.train \
  --task strike --iterations 500 \
  --run-name strike_500
```

500 iteration은 새 보상과 동작을 확인하는 첫 진단 실행이다. 모든 gate를 매 iteration 완벽하게
통과한다고 가정해도 현재 최소 단계 길이와 연속 3회 조건상 A4 진입은 가장 빨라도 약 506
iteration, A4 완료 판정은 약 806 iteration이다. 실제 학습은 이보다 더 오래 걸릴 수 있으므로
전체 curriculum 검증에는 기본 3,000 iteration을 사용한다.

영상 인코딩을 제외한 학습/checkpoint/평가/분석/plot 배관을 먼저 짧게 검사:

```bash
python -m tab2body.train \
  --task strike --smoke \
  --run-name strike_smoke
```

한 단계만 고정해서 진단할 수도 있다.

```bash
python -m tab2body.train \
  --task strike --curriculum-stage A3_TIMED_CROSSING \
  --timing-tolerance-ms 100 \
  --iterations 500 \
  --run-name strike_a3_100ms
```

## 학습 종료 후 자동 산출물

```text
strike/training/runs/<run>/
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
  # opt-in 진단 replay
  videos/strike_<iteration>_rollout_remembered_zone_pick.mp4
  videos/strike_<iteration>_rollout_current_zone_pick.mp4
  videos/strike_<iteration>_rollout_zone_pick.json
  ANALYSIS.md
  run_manifest.json
```

- checkpoint에는 30개 관절의 정확한 이름·순서, 281D observation manifest, goal/grip hash,
  detector·zone·오른팔 관통 진단·보상·PPO 설정, policy 초기 표준편차, model/optimizer, iteration/global step,
  asset/구현 지문, curriculum stage/tolerance/streak/complete와 환경 상태가 저장된다.
- resume은 optimizer/counter/curriculum과 `StrikeTask` 전용 generator RNG/reset generation을
  복원한다. 전역 Torch CPU/CUDA RNG까지 저장하는 bitwise stochastic resume은 아직 아니다.
- 평가에서는 checkpoint의 PPO 설정과 policy 초기 표준편차로 모델을 재구성한 뒤 계약을 검증한다.
  training context와 environment의 stage/tolerance가 다르면 로드 전에 중단한다.
- 서로 다른 계약의 checkpoint는 resume·평가·영상 기록 전에 거부한다.
- 마지막 정책은 해당 단계에 맞게 deterministic 평가한다. A4 전체곡 평가는 첫 사건보다
  30 frame 앞에서 시작해 ready/approach 시간을 확보하며, 현재 42-event 곡의 최대 길이는
  894 simulation frame이다.
- 자동 motion 진단은 RELEASE depth/횡속도, tip speed, grip RMS, phase별
  shoulder/elbow/wrist/hand 속도·가속도·jerk, action saturation, recovery corridor·역방향 RELEASE,
  오른팔/손 기타 관통 분포를 JSON으로 저장한다. 이 값은 관찰용이며 성공/실패 분포가 분리되기 전에는
  보상이나 종료 임계값으로 사용하지 않는다.
- 평가는 checkpoint의 policy 초기 표준편차/PPO 설정, curriculum stage/tolerance와
  `StrikeTask` generator RNG를 복원한다. 영상 recorder는 저장된 stage/tolerance를 적용하고
  고정 seed로 deterministic rollout을 새로 만든다. 학습 재개는 현재 설정과 완전히 같을 때만 허용한다.
- 영상은 같은 rollout을 `remembered`와 `current` 두 고정 카메라로 저장한다.
- `record_strike_visualized_rollout.py`를 별도로 실행하면 기존 영상을 보존한 채 실제 6개 줄,
  allowed/preferred/current lane, geometry-less `RH:pick`과 짧은 이동 궤적을 두 영상에 표시한다.
  오버레이는 카메라 PNG 위의 X-ray 진단 투영이며 물리나 충돌 판정에는 참여하지 않는다.
- `--smoke`는 시간을 줄이기 위해 자동 영상을 끈다. 이중 영상 경로는 저장된 checkpoint를
  `--eval`로 다시 열거나 recorder를 직접 실행해 확인한다.
- 평가나 후처리 하나가 실패해도 이미 생성된 checkpoint/log 경로와 오류 종류를 manifest에 남긴다.
- 수치 gate를 통과해도 `human_like_review_required=true`다. 두 영상을 사람이 확인해야 한다.

## 현재 검증 결과

`tab2body/tools/audit_strike_runtime.py`를 RTX 4070 Ti의 GPU PhysX/GPU pipeline에서 실행했다.

- action: 30 (`R_Shoulder/Elbow/Wrist` 9 + `RH:*` 21)
- 2026-07-29 당시 observation: 263. 현재 gesture/tempo/mask 추가 후 정적 계약은 281이며 CUDA 재검증 대기
- `R_Thorax`: action 제외
- `G:pluck_range`: 해당 1개 shape만 사람과 충돌하지 않게 비활성, 나머지 기타 충돌 유지
- 실제 6개 string marker 좌표 finite
- 최소 인접 줄 간격 9.639 mm, 최대 stroke across offset 3 mm
- A0~A4 hold probe에서 finite observation/reward, 실패 종료 0
- A3 target time 0.75–1.5초, 6개 줄 균형
- A4 lane은 preferred `[-0.355,-0.295] m` 안, core `±6 mm`, outer `±12.5 mm`
- 전체곡 시작 `-0.4769 s`, 첫 사건까지 30-frame pre-roll, 최대 894 frame
- 당시 8-env PPO/checkpoint/evaluation smoke와 checkpoint 재로딩 통과
- 동일 120-step rollout에서 1600×900, 30 fps, 60-frame H.264 영상 두 개 생성·manifest 등록

2026-07-29 GPU audit JSON은 역사 산출물로 정리되어 현재 저장하지 않는다. 현재 GPU 배관은 위의
공용 `--smoke` 명령으로 재생성하며, 산출물은 해당 실행 폴더의 `run_manifest.json`·로그·평가 JSON을
기준으로 확인한다.

과거 버전의 smoke 실행 산출물은 현재 환경 계약과 호환되지 않아 보존하지 않는다. 배관 검증이
필요하면 위 실행 명령의 `--smoke` 옵션으로 현재 코드에서 새로 생성한다.

## 5,000 iteration 실제 학습

2026-07-27에 수정된 A1 계약으로 5,000 iteration, 81,920,000 samples 학습을 완료했다.
이 절의 결과와 checkpoint는 당시 실행의 historical record이며 현재 코드의 공식 성능 결과로
사용하지 않는다. 현재 장시간 재학습 결과는 아직 확정하지 않았다.
커리큘럼은 iteration 3,027에서 A4까지 완료했으며, 최종 checkpoint와 로그·평가·그래프·
remembered/current 영상이 모두 정상 저장됐다.

엄격한 42-event deterministic 최종 평가는 grip/ready/zone/timing/safety를 통과했지만
precision `0.906`, recall `0.963`, false-positive rate `0.090`, F1 `0.934`로 전체 task
gate는 아직 통과하지 못했다. 상세한 실행 이력, 체크포인트 비교, 산출물, 다음 개선 우선순위는
[STRIKE_5000_20260727.md](STRIKE_5000_20260727.md)에 기록했다.

## 아직 주장하지 않는 것

- 1 mm depth, 0.05 m/s 횡속도, 3 mm·2 frame re-arm은 실행 가능한 초기값이며 충분히
  학습된 정상/오류 rollout 분포로 재보정해야 한다.
- 현재 외부 입력에는 방향이 없으므로 v1은 명시적인 `down_only_v1`이다.
- 실제 피크 geometry, 물리 grasp/slip, 줄 탄성·소리, fingerstyle, up/alternate, hybrid는 보류다.
- runtime smoke 통과는 장시간 학습 성능을 뜻하지 않는다. 장시간 학습의 실제 성능은
  5,000-iteration 결과 문서와 로그·평가·영상으로 판단한다.

과거 500회 실패 실험은 비교 자료로
[STRIKE_S0_PILOT_500_20260727.md](STRIKE_S0_PILOT_500_20260727.md)에만 남긴다.
