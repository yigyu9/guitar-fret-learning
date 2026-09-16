# Strike 학습 개선 이력

> **상태: APPEND-ONLY HISTORICAL RECORD.** 각 절의 “현재”는 해당 실험 시점 기준이다.
> 현행 실행 계약은 [`README.md`](README.md) 상단과 코드의 v14/303D 계약을 따른다.

> 최종 갱신: 2026-08-31
>
> 목적: 오른손 학습의 `학습 → 분석 → 개선안 → 구현 → 재학습`을 하나의 연속된
> 근거로 남기고, 이미 실패한 설계나 같은 구조의 병목을 반복하지 않는다.
>
> 공통 작성 절차: [`TRAINING_IMPROVEMENT_PROCESS.md`](../../docs/TRAINING_IMPROVEMENT_PROCESS.md)

## 사용 원칙

1. 새 구현을 시작하기 전에 이 문서의 `중복 방지 표`와 연결된 이전 실험을 확인한다.
2. 관측 사실, 원인 판단, 추론과 아직 모르는 것을 구분한다.
3. 구현 직후에는 성공이라고 쓰지 않고 `검증 전`으로 둔다.
4. 장기 run이 끝나면 같은 실험 항목에 대조 결과와 영상 판정을 추가한다.
5. traversal이나 `goal_finished`만으로 성공을 판단하지 않는다. completion, timing, zone,
   recovery, false positive와 안전 지표를 함께 본다.
6. 정책 입력·보상·stage 의미가 바뀌면 checkpoint 호환성을 명시한다.
7. 과거 결론은 삭제하지 않는다. 후속 실험 ID로 수정 근거를 연결한다.

상태는 `유지`, `폐기`, `보완 필요`, `검증 전` 네 가지를 사용한다.

## 중복 방지 표

| 방법 또는 설계 | 확인된 결과 | 현재 판단 |
|---|---|---|
| 가까운 사건에 고정 대칭 시간창 사용 | 복잡한 곡에서 사건 창이 겹쳐 goal 검증 단계에서 중단 | 폐기 |
| 가까운 서로 다른 줄을 독립 single로 강제 | 물리 re-arm 전에 다음 사건이 와서 실행 불가능 | 폐기 |
| 원본 시각을 덮어써 간격을 늘림 | 원곡 복원 여부를 검증할 수 없음 | 폐기 |
| phrase 안에서 strike lane을 이벤트마다 무작위 변경 | 타현 사이 불필요한 너트/브리지 방향 이동으로 A4 정체 | 폐기 |
| strum 전체 동안 첫 줄 entry만 접근 목표로 사용 | 첫 줄 이후 진행 방향을 알려주지 못해 completion 0 | 폐기 |
| 실제 2줄 단계의 내부 목표를 1줄로 시작 | 단계 이름·성공 지표와 실제 운동 계약이 불일치 | 폐기 |
| S1에서 timing을 완전히 끈 뒤 S2에서 timing·zone·microtiming을 동시에 적용 | 6줄 traversal은 0.994지만 약 990 iteration 동안 S2 성공률 0 | 폐기·재설계 필요 |
| 20/15 ms 지수 kernel만으로 큰 timing/duration 오차 교정 | 715/262 ms 오차에서 보상이 사실상 0 | 단독 사용 폐기 |
| 즉시 strum 진행 보상 뒤 시간창 종료 시 전량 환수 | 할인율 때문에 조기 strum이 이득일 가능성 | 보완 전 재사용 금지 |
| down/up 균형 연습과 방향별 별도 지표 | 한쪽 방향만 외우는 것을 방지하고 방향 성능을 분리 관찰 | 유지 |
| 목표 RELEASE 뒤 clean recovery reset/blocked 진단 | 왕복·중복 crossing 병목을 독립적으로 확인 가능 | 유지 |
| 넓은 tolerance 통과율만으로 다음 S2 profile 승급 | 목표창 앞쪽에 몰린 정책이 좁은 창에서 즉시 붕괴하고 T1↔T2 진동 | 폐기 |
| timed 실패를 물리 traversal 실패로도 중복 집계 | completion·recovery를 0으로 만들고 timing 표본을 성공 쪽으로 편향 | 폐기 |
| 새 S2 profile 진입 직후 rollback 판정 | 적응 전에 이전 profile로 되돌아가 정책 개선 시간을 주지 못함 | 폐기 |
| 정상 종료 시 최종 checkpoint 영상만 생성 | 조기 중단·코드 수정 뒤 중간 policy 동작을 복기할 영상이 없음 | 폐기 |
| 마지막 완료 영상에서 1,900 iteration 뒤 다음 저장 checkpoint를 두 view로 기록 | 약 2,000 간격 이력, 실패 재시도와 중단 checkpoint 복구를 GPU에서 확인 | 유지 |
| 모든 timed profile에서 고정 `approach_lead_s=0.25` 사용 | T1에서 approach가 열린 뒤 약 60 ms 만에 RELEASE하여 평균 약 186 ms 조기 타현으로 고착 | 폐기 |
| profile별 접근 lead와 강제 READY 대기 구간 사용 | 목표 중심으로 접근 시작점을 옮기되 물리 strum 기술은 유지하도록 설계 | 검증 전 |
| A0 뒤 grip 보상을 `0.003~0.005`로 약화하고 binary 성공률만 gate | S3에서 success 약 0.99여도 연속 quality와 영상 속 손 모양이 붕괴 | 폐기 |
| 엄지·검지/자유 손가락 residual 분리와 모든 단계 연속 grip gate | 피크 끝 운동학을 먼저 고정하고 후기 단계의 자세 우회를 차단 | 검증 전 |
| S3의 모든 사건에 고정 12-frame 회복을 요구 | 8-event episode에서 이론상 최대 약 0.773으로 recovery gate 0.95를 달성할 수 없음 | S3 승급 기준으로 폐기, 진단값으로 유지 |
| S3 full/handoff 회복 분리와 같은 줄 handoff 재무장 | 짧은 간격은 다음 접근까지 확보된 frame만 사용하고 충분한 간격·마지막 사건은 full 회복 보존 | 검증 전 |
| 노출 횟수를 보정하지 않은 raw failure count로 hard window 표집 | 이미 많이 뽑힌 구간이 더 큰 score를 얻고 다시 더 많이 뽑히는 자기강화 붕괴 발생 | 폐기 |
| hard episode를 S3 승급 evidence에 포함 | 학습 분포를 바꾸는 순간 승급 평가 분포도 함께 변하는 문제 발생 | 폐기 |
| deterministic 전체곡 평가 중 학습용 failure mining 상태 갱신 | 평가 1회의 동일 실패가 환경 수만큼 raw count로 누적되어 표집 분포를 오염 | 폐기 |
| 노출 보정 실패율 + hard 15% + window 확률 상한 10% + uniform-only 승급 evidence | hard 훈련과 전체곡 평가 분포를 분리하도록 구현 | 검증 전 |
| S2 전체 completion 평균만으로 양방향 획득 판단 | up 약 99.3%가 down 0.1% 미만을 가려 한쪽 끝줄 실패가 보이지 않음 | 폐기 |
| 마지막 줄의 물리 exit 목표 없이 timing tolerance·gate만 완화 | 마지막 줄을 지나게 하는 운동 목표가 없어 구조 병목을 해결하지 못함 | 폐기 |
| final-string→exit 방향대칭 목표 + 최대 투영 증가분 | down/up 동일 수식이고 후퇴·왕복으로 보상을 재수집하지 않음 | 검증 전 |
| 70/30 부족 방향 focus를 전체 승급 evidence에도 사용 | 학습 분포 변화가 승급 기준을 바꾸므로 금지; balanced holdout만 gate에 사용 | 폐기 |

## 실험 이력

### STRIKE-001 — 가까운 사건과 겹치지 않는 시간 계약

- 시기: 2026-08-10~12
- 분류: `DATA`, `GATE`
- 문제: `00_SS1-68-E_comp`처럼 타현 간격이 짧은 곡은 고정 허용창이 서로 겹쳐
  `strike goal event windows overlap`으로 학습을 시작할 수 없었다.
- 원인 판단: 물리적으로 하나의 stroke인 서로 다른 줄 사건까지 독립 single로 유지했고,
  전역 대칭 허용창이 인접 사건 간격을 고려하지 않았다.
- 구현:
  - 가까운 서로 다른 줄 사건을 하나의 strum과 연속 traversal로 컴파일한다.
  - 원본 시각은 보존하고 학습용 간격만 `tempo_lambda`로 넓힌다.
  - 성능 gate를 통과하며 `0→0.25→0.5→0.75→0.9→0.95→0.975→1`로 원곡 간격을 복원한다.
  - 각 사건의 허용창은 인접 간격의 45% 이하인 비대칭 창으로 제한한다.
- 결과: 176개 source event가 62 single과 43 strum, 총 105개 실행 gesture로 컴파일됐고
  겹치는 matcher window 없이 학습할 수 있게 됐다.
- 한계: 같은 줄의 빠른 재타현은 alternate-restrike 제어가 없어 지원하지 않는다.
- 재발 방지 결정: 원본 시각과 학습 시각을 분리하고 `tempo_lambda=1`에서 다시 통과하기 전에는
  원곡 성공으로 판정하지 않는다.
- 근거: [`README.md`](README.md)의 `가까운 사건·strum·원템포 커리큘럼`,
  [`PHRASE_DIRECTION_PLANNER.md`](../01_goal_contract/PHRASE_DIRECTION_PLANNER.md)
- 상태: `유지`

### STRIKE-002 — A2 이후 ready 기술 보존

- 시기: 2026-08-13
- 분류: `GATE`, `FORGETTING`, `REWARD`
- 문제: A1에서는 ready 성공률이 높았지만 A2 진입 뒤 약 0.16까지 떨어져 crossing만 수행하는
  정책이 됐다.
- 원인 판단: A2 이후 ready 보상과 승급 조건이 약해져 준비 자세 없이 줄을 통과해도 학습이
  진행될 수 있었다.
- 구현:
  - A2 이후에도 ready 획득 전 위치 품질과 ready pulse 보상을 유지한다.
  - 준비 전 crossing에는 성공 보상을 주지 않고 별도 penalty를 적용한다.
  - A2 이후 승급에도 ready 성공률을 공통 gate로 포함한다.
- 결과: 희소한 crossing 성공률만 보고 ready 망각을 놓치는 판정 경로를 제거했다.
- 재발 방지 결정: 후기 stage는 새 기술뿐 아니라 보존해야 할 선행 기술 gate도 명시한다.
- 근거: [`README.md`](README.md)의 `A2 ready 기술 보존`
- 상태: `유지`

### STRIKE-003 — 이벤트별 무작위 lane을 phrase lane으로 변경

- 시기: 2026-08-16
- 분류: `DATA`, `TRANSITION`, `CONTROL`
- 기준 run: `strike/training/runs/20260813_1233_00_SS1-68-E_comp`
- 문제와 관측 사실: A4 `tempo_lambda=0`에서 recall이 약 0.47로 정체됐다.
- 원인 판단: 입력에 없는 lane을 매 이벤트마다 다시 뽑아 연속 타현 중 불필요한 줄 길이 방향
  이동을 요구했다.
- 구현: episode 시작에 preferred 영역에서 lane을 한 번 뽑고 8-event phrase 동안 고정했다.
  `target_lane_shift_m`을 추가해 phrase 내부 변화가 0인지 확인한다.
- 재발 방지 결정: goal에 없는 자유 변수는 사건마다 무작위화하지 않는다. 사람 동작에서 유지되는
  문맥의 시간 단위와 randomization 단위를 맞춘다.
- 근거: [`README.md`](README.md)의 `A4 phrase lane 안정화`
- 상태: `유지`

### STRIKE-004 — single crossing에서 연속 strum으로 가는 bridge

- 시기: 2026-08-19
- 분류: `TRANSITION`, `REWARD`, `CONTROL`
- 문제: 첫 줄을 통과한 뒤에도 접근 목표가 첫 줄 entry에 남아 있었고, 전체 traversal 전에는
  양의 crossing 신호가 없어 strum completion이 0에 머물렀다.
- 구현:
  - 통과할 때마다 목표를 다음 traversal string으로 이동한다.
  - 마지막 줄 뒤에만 exit/recovery로 전환한다.
  - 새 줄을 올바른 순서·방향으로 통과할 때 `1 / 요구 줄 수` 진행 보상을 한 번 지급한다.
  - single과 strum을 같은 단계에서 경쟁시키지 않고 A0~A3, A4~S3로 나눴다.
  - S1에서 span을 3→4→5→6줄로 늘린다.
- 결과: 후속 v5 run의 S1 마지막 200 iteration에서 traversal recall 0.998,
  completion 0.998을 확인했다.
- 한계: untimed S1의 높은 completion은 timed S2 성공을 보장하지 않았다. 후속은 STRIKE-007이다.
- 재발 방지 결정: 여러 하위 목표를 가진 동작은 다음 하위 목표와 부분 진척을 observation과
  metric에 모두 노출한다.
- 근거: [`README.md`](README.md)의 `strum bridge v3`
- 상태: `유지`

### STRIKE-005 — 양방향·줄별 microtiming 계약

- 시기: 2026-08-20
- 분류: `DATA`, `METRIC`, `REWARD`
- 문제: 원곡 방향 분포만 사용하면 한 방향을 거의 보지 못할 수 있고, strum 완료 여부만으로는
  줄별 간격과 sweep 길이를 평가할 수 없었다.
- 구현:
  - S2까지 down/up 연습을 환경별로 균형 생성한다.
  - 방향에 맞춰 traversal 순서와 줄별 offset을 반전한다.
  - 줄별 timing RMS, sweep-duration MAE와 down/up completion을 별도 기록한다.
  - 부분 strum 실패 시 지급한 진행 보상을 환수한다.
- 결과: 방향·순서·줄 통과와 timing/duration 병목을 분리해서 볼 수 있게 됐다.
- 한계: 환수가 시간창 종료 때 지연되고 정밀 보상 kernel이 너무 좁아 큰 오차를 교정하지 못하는
  문제가 STRIKE-007에서 확인됐다.
- 근거: [`README.md`](README.md)의 `양방향 연습·strum 미세 타이밍 v4` 및 이 문서의 STRIKE-005 실행 기록
- 상태: `보완 필요`

### STRIKE-006 — clean recovery와 실제 2줄 S0

- 시기: 2026-08-24
- 분류: `GATE`, `CONTROL`, `METRIC`
- 기준 run: `strike/training/runs/20260824_1325_00_SS1-68-E_comp`
- 문제와 관측 사실: 기존 S0은 첫 줄 통과보다 고속 왕복, duplicate와 detector 재무장 전
  crossing이 병목이었다. 성공률 약 0.486, FP 약 0.502, duplicate 약 0.406이었다.
- 구현:
  - A3와 S0 사이에 실제 strum 문맥 한 줄과 회복만 다루는 A4를 추가했다.
  - S0은 내부 1줄 없이 처음부터 실제 2줄 traversal을 요구한다.
  - 추가 RELEASE나 blocked-before-rearm crossing이면 12-frame recovery를 0으로 되돌린다.
  - recovery progress/completion은 one-shot이고 0.20 m/s 초과 속도에 bounded penalty를 준다.
  - completion/reset/blocked 지표와 구체적인 gate failure 이름을 기록한다.
- 검증: CPU 회귀 검사와 당시 GPU smoke는 통과했다. 후속 장기 run은 S1까지 높은 completion으로
  진입했지만 S2에서 별도 timing 병목이 발생했다.
- checkpoint: 계약 v7/curriculum v5/environment v6로 변경되어 이전 checkpoint와 비호환이다.
- 재발 방지 결정: 단계 이름, 실제 요구 줄 수와 completion 분모를 일치시키고, 회복은 성공률에
  숨기지 않고 독립 지표로 유지한다.
- 근거: 이 문서의 STRIKE-006 실행 기록과 현재 [`README.md`](README.md)
- 상태: `유지`

### STRIKE-007 — S2 timed-strum 무신호 정체

- 시기: 2026-08-24, 학습 진행 중 snapshot
- 분류: `REWARD`, `DISCOUNT`, `TRANSITION`, `FORGETTING`, `METRIC`
- 연결된 이전 실험: STRIKE-004, STRIKE-005, STRIKE-006
- 기준 run: `strike/training/runs/20260824_1743_00_SS1-68-E_comp`
- 관측 사실:
  - S1→S2 전이는 iteration 4,686에서 발생했다.
  - S1 마지막 200 iteration의 curriculum 성공률은 0.986, completion은 0.998이었다.
  - S2 최근 300 iteration의 curriculum 성공률과 completion은 모두 0이었다.
  - 같은 구간의 traversal recall은 0.994, 순서 정확도 1.0, 방향 정확도 약 0.994였다.
  - timing p95 약 1,189 ms, 줄별 timing RMS 약 715 ms, sweep-duration MAE 약 262 ms였다.
  - zone success와 recovery event는 0이었다.
  - PPO는 iteration마다 80 update를 수행했고 KL early-stop, action saturation과 안전 종료는 없었다.
- 후속 관측 — 2026-08-24 22:52 KST, iteration 7,635 / S2 stage iteration 2,948:
  - curriculum success와 completion은 계속 0이고, 마지막으로 completion이 0보다 컸던 시점은
    iteration 4,906이었다.
  - traversal recall은 0.9996, 순서 정확도는 1.0이지만 방향 정확도는 0.9279로 떨어졌다.
  - timing MAE 889 ms, p95 1,228 ms, 줄별 RMS 766 ms로 초기 S2보다 악화됐다.
  - false-positive rate는 0.282로 증가했고 zone success와 recovery event는 계속 0이었다.
  - 반대로 평균 reward는 S2 첫 500 iteration 평균 0.0092에서 최근 약 0.031로 증가했다.
  - 따라서 현재 objective는 task 성공과 음의 상관을 보이며, 추가 iteration만으로 회복된다는
    근거가 없다.
- 원인 판단:
  - S1에서 6줄 운동은 배웠지만 timing을 완전히 비활성화해 A3의 시간 대기 기술을 보존하지 않았다.
  - S2에서 timing, 무작위 lane, microtiming과 duration을 동시에 켜 stage 전이가 너무 컸다.
  - 20 ms timing kernel과 15 ms duration kernel은 현재 오차에서 사실상 0이라 교정 방향을 주지 못한다.
  - crossing/timing/zone/recovery 보상은 hard timing gate 뒤에 있어 큰 초기 오차에서는 접근할 수 없다.
  - S2의 줄별 진행 보상은 timing과 무관하게 즉시 지급되지만, 누적 진행 환수와 miss penalty는
    0.75~1.50초 목표창이 닫힌 뒤 지급된다. `gamma=0.95`, `GAE lambda=0.95`, horizon 32에서는
    조기 진행과 지연 실패의 credit assignment가 분리되어 잘못된 빠른 sweep을 강화할 수 있다.
- 아직 추론인 부분:
  - 로그가 절대 오차만 저장하므로 타현이 목표보다 빠른지 늦은지는 확정할 수 없다. S1의 즉시
    strum을 유지했다는 동작 흐름상 조기 타현일 가능성이 높다.
  - 즉시 진행 보상과 나중의 clawback/miss penalty 사이 할인 차이가 조기 strum을 강화했을
    가능성이 있다. 보상 항목별 return 로그가 없어 현재는 구조적 위험 판단이다.
- 결정한 개선 방향:
  - S2를 넓은 timing 적응, lane 적응, 정밀 microtiming 순으로 분리한다.
  - 허용 범위는 큰 현재 오차에서 시작해 단계적으로 100/67/50 ms까지 줄인다.
  - hard gate와 독립된 bounded dense timing/zone 신호를 추가한다.
  - 너무 이른 물리 crossing은 시간창 종료를 기다리지 않고 즉시 처리한다.
  - 진행 보상은 목표 시간 근처에서만 활성화하거나 할인에 안전한 potential로 바꾼다.
  - S0/S1에 timed rehearsal을 섞거나 timing을 넓은 범위로 계속 활성화한다.
  - signed timing error와 보상 항목별 episode return을 추가한다.
- 구현: 아직 반영하지 않았다. 현재 run과 코드는 분석을 위해 그대로 유지했다.
- 사전 성공 기준:
  - 새 S2 첫 수준에서 completion과 timing sample이 동시에 0보다 커야 한다.
  - 최근 300 iteration의 signed/absolute timing error가 감소해야 한다.
  - traversal/order/direction이 각각 0.95/0.98/0.98 아래로 붕괴하지 않아야 한다.
  - 다음 timing 수준으로 넘어가기 전에 zone과 recovery 표본이 실제로 발생해야 한다.
- 재발 방지 결정:
  - stage 전이에서 새 난이도 축을 둘 이상 동시에 hard gate로 켜지 않는다.
  - 초기 예상 오차에서 reward 값을 수치로 계산하는 회귀 검사를 추가하기 전에는 재학습하지 않는다.
  - gate 전 raw 물리 지표와 gate 후 성공 지표를 항상 함께 저장한다.
- 다음 행동: 구현 후 과거 checkpoint resume이 아니라 호환성 판단에 따라 S1 직전 policy
  initialization 또는 fresh run으로 대조 학습한다.
- 진행 단계: 구현 전
- 상태: `보완 필요`

### STRIKE-008 — 성공 기반 S2 timing profile

- 시기: 2026-08-24
- 분류: `REWARD`, `DISCOUNT`, `TRANSITION`, `GATE`, `METRIC`
- 연결된 이전 실험: STRIKE-007
- 문제와 관측 사실: S2의 첫 100 ms level에서 success가 0인 동안 reward와 traversal만
  증가하고 timing, FP와 방향 정확도가 악화됐다.
- 개선 가설:
  - S2를 `400→250→150→100→zone 100→67→50 ms` profile로 나눈다.
  - 현재 profile을 실제로 성공한 뒤에만 tolerance와 reward core를 줄인다.
  - 조기 RELEASE를 즉시 실패 처리하고 진행 shaping을 potential 기반으로 바꾸면 지연
    clawback의 할인 exploit을 제거할 수 있다.
  - timing gate 전 signed error와 raw zone 품질을 기록하면 정체 원인을 분리할 수 있다.
- 기존 시도와 다른 점: 단순히 tolerance gate를 낮추거나 최대 iteration을 늘리지 않는다.
  timing, zone과 정밀 duration을 서로 다른 profile에서 활성화하고 성능 붕괴 시 한 단계 후퇴한다.
- 상세 구현 계획:
  이 문서의 STRIKE-007 상세 계획과 현재 [`README.md`](README.md)
- checkpoint: reward/curriculum/metric 의미가 바뀌므로 strict resume 비호환으로 계획한다.
- 구현:
  - `strike_cfg.py`와 `learning/strike_curriculum.py`에 7개 S2 profile, profile별 gate/core,
    3-window 승급·후퇴와 200-iteration cooldown을 추가했다.
  - `task_strike.py`에서 S2 timed READY, 즉시 premature miss, 동적 zone hard gate,
    per-string timing 품질과 raw zone 표본을 연결했다.
  - `env/rewards/strike.py`에서 지연 clawback을 제거하고 terminal potential shaping 및
    profile-adaptive rational timing/duration 품질로 교체했다.
  - `strike_metrics.py`, `learning/ppo.py`, `train_strike.py`와 plot/analysis에 signed timing,
    pass/early/late/premature, raw zone, 보상 return, profile/rollback 및 reward-alignment
    경고를 추가했다.
  - S2 coarse profile의 평가에서 zone을 적용하지 않고 현재 profile gate를 사용하도록
    `learning/strike_evaluation.py`를 수정했다.
  - curriculum/environment/checkpoint/evaluation schema를 v6/v7/v8/v4로 올렸다.
- 검증:
  - 전체 `test_strike_*.py` CPU 회귀 스크립트 14개가 통과했다.
  - checkpoint contract와 PPO actor-advantage 검사도 통과했다.
  - 성공률 0.69에서는 T0 400 ms가 유지되고 0.70 gate 통과 뒤 T1 250 ms로 이동하는
    경계 검사를 추가했다.
  - 심한 붕괴 3회 뒤 정확히 한 단계 후퇴하는 검사, premature 경계, rational quality,
    terminal potential과 reward-alignment 경고 검사를 추가했다.
  - 기존 run이 1024-env로 계속 실행 중이므로 GPU smoke는 간섭 방지를 위해 보류했다.
- 재학습 위치: 기존 schema v5 checkpoint strict resume은 금지하고 A0 fresh run으로 시작한다.
- 진행 단계: CPU 구현·회귀 검증 완료, GPU smoke·학습 결과 검증 전
- 사전 성공 기준:
  - T0에서 timing pass와 completion이 0보다 커지고 signed/absolute timing 오차가 감소한다.
  - profile 이동 후에도 traversal/order/direction 보존 gate를 유지한다.
  - 조기 전체 sweep의 discounted return이 정시 완주보다 낮다는 audit를 통과한다.
  - Z2를 3회 연속 통과한 뒤에만 S3로 이동한다.
- 실제 결과:
  - `20260824_2357_00_SS1-68-E_comp`는 T1 250 ms에서 목표창 안 통과율과 물리 strum은
    거의 1.0이었지만 signed timing mean이 약 `-170 ms`에 머물렀다.
  - T2 150 ms로 이동하면 timing pass 약 `0.58`, traversal 약 `0.66`까지 즉시 떨어졌고,
    7~10 iteration 안에 롤백했다. 같은 T1↔T2 왕복이 38회 반복됐으며 초기 10회와 마지막
    10회의 핵심 지표에는 개선 추세가 없었다.
  - PPO는 최근 구간에서 대체로 80 update를 수행해 optimizer 정지가 주원인은 아니었다.
- 후속: STRIKE-009에서 중심 타이밍 승급 gate, 완만한 profile, 전환 적응 기간과 물리/타이밍
  지표 분리를 구현한다.
- 상태: `보완 필요`

### STRIKE-009 — 중심 타이밍 전이와 물리/시간 판정 분리

- 시기: 2026-08-25
- 분류: `GATE`, `TRANSITION`, `REWARD`, `METRIC`
- 연결된 이전 실험: STRIKE-005, STRIKE-007, STRIKE-008
- 문제와 관측 사실:
  - 기준 run은 `strike/training/runs/20260824_2357_00_SS1-68-E_comp`이다.
  - T1 250 ms에서 timing pass·completion·traversal·order·direction은 거의 1.0이었지만
    signed timing mean은 약 `-170 ms`, strum RMS는 약 `140 ms`였다.
  - T2 150 ms 진입 뒤 timing pass 약 `0.58`, traversal 약 `0.66`으로 붕괴해 38회
    T1↔T2 전환이 반복됐다.
  - timed stage에서 너무 이른 첫 RELEASE는 부분 strum인데도 즉시 event miss로 확정됐고,
    너무 이른 전체 traversal은 물리 completion·release recall·recovery까지 실패로 집계됐다.
  - timing 표본은 premature mask 뒤에서 수집되어 실패 표본이 빠지는 survivor bias가 있었다.
- 원인 판단:
  - T1 승급은 넓은 창 안 pass만 보며 오차 분포가 목표 시점 중심에 모였는지 검사하지 않았다.
  - tolerance가 `250→150 ms`로 한 번에 줄었고 새 profile 진입 직후부터 rollback을 허용했다.
  - 시간 실패와 물리 traversal 실패를 같은 `target_hit`로 집계해 다음 gate가 실제 병목을
    구분하지 못했다.
- 아직 추론인 부분: 중심 gate와 보상 강화가 장기 학습에서 signed mean을 실제 0 쪽으로
  이동시키는지는 fresh GPU 학습으로 확인해야 한다.
- 개선 가설:
  - tolerance를 `400→250→225→200→175→150→100 ms`로 줄이고 각 profile의 signed mean과
    p10/p90 꼬리 gate를 통과해야만 다음 단계로 가게 한다.
  - profile 이동 뒤 200 iteration을 적응 기간으로 보장하면 즉시 rollback 진동을 막을 수 있다.
  - 물리 completion·recall·recovery와 timing pass를 독립 집계하고 모든 완료 traversal을 timing
    표본으로 남기면 정책 상태와 승급 실패 원인이 일치한다.
  - S2의 dense timing-progress 보상 가중치를 `0.25→1.0`으로 높이면 넓은 창 내부에서도
    목표 중심으로 이동할 유인이 커진다.
- 기존 시도와 다른 점: 단순히 tolerance나 gate를 느슨하게 하지 않는다. 다음 창에 들어갈 수
  있는 중심 분포를 먼저 요구하고, 전환 학습 시간과 지표 의미를 함께 수정한다.
- 구현:
  - `strike_cfg.py`, `strike_training_runtime.py`, `learning/strike_curriculum.py`에 10개 profile,
    signed mean/tail gate, 200-iteration adaptation state와 저장·복원을 추가했다.
  - `env/strike_events.py`, `env/tasks/task_strike.py`에서 완료 traversal의 early/late를 계산하고
    물리 성공/실패와 timing 성공/실패를 분리했다. 부분 early RELEASE는 전체 sweep을 끝낼 기회를
    유지하며, 완료된 early/late sweep은 즉시 timing miss로 해소한다.
  - `env/rewards/strike.py`에 stage별 `timing_progress_reward`를 추가해 S2 중심 교정 신호를
    `1.0`으로 강화했다.
  - `learning/strike_evaluation.py`, `train_strike.py`의 평가에도 signed mean/tail gate를 적용했다.
  - curriculum/environment/checkpoint/evaluation schema를 각각 `v7/v8/v9/v5`로 올렸다.
- checkpoint 호환성·재시작 위치: reward·metric·curriculum 의미가 달라 이전 checkpoint는
  strict resume과 policy initialization 모두 사용하지 않는다. A0 fresh run으로 시작한다.
- 검증:
  - `test_strike_*.py` CPU 회귀 스크립트 14개가 모두 통과했다.
  - `test_checkpoint_contract.py`와 정적 compile 검사를 통과했다.
  - off-center `mean=-170 ms, p10=-200 ms`가 T1을 통과하지 못하고, 중심 표본만 T2 225 ms로
    승급하는 경계 검사를 추가했다.
  - 적응 기간 동안 severe 표본이 들어와도 rollback하지 않고, 적응 종료 뒤 3회 severe 증거에서
    한 단계 후퇴하는 검사를 추가했다.
  - timing 실패지만 물리 traversal을 완료한 사건이 physical hit로 유지되고 timing sample에도
    포함되는 회귀 검사를 추가했다.
  - `20260825_strike009_smoke`에서 8-env·1-iteration GPU PhysX smoke, checkpoint,
    evaluation v5, analysis, plot과 motion diagnostics 생성을 통과했다. Isaac Gym의 기존 visual
    geometry 경고는 발생했지만 환경 생성·학습·저장에는 영향을 주지 않았다.
  - `20260825_strike009_s2_smoke`에서 S2/T1 250 ms를 고정해 새 중심 gate가 로그·평가에
    `mean 110 ms`, `tail 190 ms`로 전달되고 timed-strum 학습·평가가 예외 없이 끝나는 것을 확인했다.
    초기 정책의 성능 gate 실패는 실행 검사의 예상 결과다.
  - 장기 학습 결과는 아직 확인하지 않았다.
- 사전 성공 기준:
  - T1 마지막 300 iteration의 signed mean 절댓값이 `110 ms` 이하, p10/p90이 `±190 ms`
    안에 들어온 뒤에만 T2로 간다.
  - T2 진입 후 200 iteration 동안 rollback이 없어야 하며 이후 timing pass·physical completion이
    각각 `0.78` 이상이어야 한다.
  - T2~T6에서 signed mean과 tail gate가 단계적으로 줄고 traversal/order/direction이
    `0.95/0.98/0.98` 아래로 붕괴하지 않아야 한다.
  - S3 원곡 속도에서 timing F1·오타현·박자 오차·위치와 두 카메라 영상을 최종 판정한다.
- 재발 방지 결정: 다음 tolerance로 승급할 때 현재 창의 pass rate만 보지 않고, 다음 창과 겹치는
  중심 분포 및 전환 후 최소 적응 시간을 계약에 포함한다. 물리 동작과 시간 정확도는 별도 지표로
  유지한다.
- 다음 행동: fresh A0 run을 시작해 T1 중심화 속도와 T2 진입 후 200~500 iteration 추이를
  STRIKE-008 기준 run과 비교한다.
- 상태: `검증 전`

### STRIKE-010 — 체크포인트 기반 주기 영상 보존

- 시기: 2026-08-25
- 분류: `METRIC`, `ARTIFACT`, `RECOVERY`
- 연결된 이전 실험: STRIKE-008, STRIKE-009
- 문제와 관측 사실:
  - 기존 자동 영상은 학습이 정상 종료된 마지막 checkpoint에만 생성된다.
  - 로그 분석 뒤 학습을 조기에 중단하고 코드를 수정하면 중간 checkpoint의 동작을 영상으로
    복기할 수 없다.
  - PPO checkpoint는 기본 500 iteration마다 저장되므로 모든 checkpoint를 영상화하면 학습
    중단 시간이 지나치게 커질 수 있다.
- 개선 가설:
  - 마지막 완료 영상 이후 1,900 iteration 이상 지난 상태에서 다음 checkpoint가 저장될 때만
    두 카메라 영상을 만들면 대략 2,000 iteration 간격을 유지하면서 curriculum 전환 checkpoint도
    놓치지 않는다.
  - 영상 실패 시 마지막 완료 시점을 갱신하지 않고 다음 checkpoint에서 재시도하면 일시적인
    인코딩 실패 때문에 이후 이력이 비는 것을 막을 수 있다.
  - 학습 중단 시 마지막 완료 iteration을 checkpoint로 저장하고 종료 산출물 경로를 실행하면
    계획보다 일찍 멈춘 run도 복기할 수 있다.
- 기존 시도와 다른 점: 정확한 2,000 배수에 의존하지 않고 실제 checkpoint 저장 사건과 마지막
  성공 영상 사이의 간격을 기준으로 한다.
- 구현:
  - `learning/periodic_checkpoint_video.py`에 완전한 두-view+report 묶음 검색, checkpoint iteration
    파싱과 최소 간격 scheduler를 추가했다.
  - `tools/record_strike_rollout.py`의 카메라·frame·인코딩 중복을 `LiveStrikeRolloutRecorder`로
    합쳐 standalone 최종 영상과 학습 중 영상이 같은 카메라·결정론적 rollout 구현을 사용한다.
  - `train_strike.py`는 저장된 checkpoint만 대상으로 scheduler를 호출하고, 현재 Isaac Gym을 잠시
    멈춰 영상을 만든 뒤 전체 환경과 PPO 관측을 새 episode로 reset한다. 별도 simulator subprocess를
    동시에 띄우지 않는다.
  - 성공·실패를 `logs/periodic_videos.jsonl`과 manifest에 checkpoint별로 기록한다. 실패 시 scheduler
    완료 시점을 갱신하지 않아 다음 저장 checkpoint에서 재시도한다.
  - `KeyboardInterrupt`를 받으면 마지막 완료 iteration을 즉시 저장하고 interruption JSON, 평가와
    최종 두 영상을 생성한다. 이미 완전한 주기 영상은 종료 후 다시 렌더하지 않는다.
  - 기본 간격은 1,900이며 `--periodic-video-min-gap`, 전체 비활성화는 `--no-auto-video`, GPU 경로
    검사는 `--smoke --smoke-video`로 노출했다.
  - 설정·계약 변경: 영상 산출물 설정만 추가하며 policy/environment 의미는 바꾸지 않는다.
  - checkpoint 호환성·재시작 위치: runtime semantic fingerprint와 schema를 바꾸지 않아 기존
    STRIKE-009 checkpoint와 호환을 유지한다. 새 학습을 다시 시작할 필요는 없다.
- 검증:
  - 15개 `test_strike_*.py`, checkpoint contract, PPO actor advantage, run layout와 train dispatch
    CPU 회귀 검사가 모두 통과했다.
  - `20260825_periodic_video_smoke`에서 GPU PhysX 8-env·1-iteration 학습 checkpoint 직후 실제
    paused-live 녹화를 수행했다. 1600×900, 30 fps, 2초 remembered/current H.264 두 영상과 v2 report,
    ledger·manifest 등록을 통과했고 종료 시 같은 영상을 재사용했다.
  - `20260825_periodic_video_interrupt_smoke`는 iteration 4 직후 `Ctrl-C`를 보내 checkpoint,
    interruption JSON, 평가, 분석과 최종 두 영상을 모두 생성했다.
  - 사전 성공 기준:
    - 기본 500-iteration checkpoint 간격에서 2,000, 4,000, 6,000 iteration 영상이 선택된다.
    - 1,900 iteration 이후 저장된 curriculum 전환 checkpoint는 즉시 영상 대상으로 선택된다.
    - 한 view나 report가 빠진 영상은 완료로 세지 않고 다음 checkpoint에서 재시도한다.
    - 중단된 학습도 마지막 완료 iteration checkpoint와 최종 두 카메라 영상을 남긴다.
- 재발 방지 결정: 중간 policy 동작의 판정 근거는 checkpoint만 남기지 않고 checkpoint·두 view·
  report의 완전한 묶음으로 기록한다.
- 다음 행동: 다음 장기 run에서 약 2,000·4,000 iteration 영상이 실제로 누적되는지 ledger와
  manifest로 확인하고, 녹화 중단 시간이 학습 운영에 과도하지 않은지 함께 측정한다.
- 상태: `유지`

### STRIKE-011 — 목표 시각 중심 접근 제어

- 시기: 2026-08-25
- 분류: `CONTROL`, `REWARD`, `TRANSITION`, `METRIC`
- 연결된 이전 실험: STRIKE-008, STRIKE-009, STRIKE-010
- 기준 run / checkpoint:
  `strike/training/runs/20260825_1551_00_SS1-68-E_comp/checkpoints/strike_005000.pt`
- 문제와 관측 사실:
  - T1 250 ms 최근 300 iteration의 물리 completion/traversal/order는 거의 `1.0`이고
    false positive는 약 `0.004`였다.
  - 같은 구간의 signed timing mean은 약 `-186 ms`, p10은 약 `-201 ms`로 중심 gate
    `|mean|≤110 ms`, `p10≥-190 ms`를 통과하지 못했다.
  - T1 진입 초기 300 iteration의 mean `-146 ms`보다 최근 구간이 더 빨라졌고 최근 500
    iteration 기울기는 사실상 0이라 추가 학습만으로 중심화될 근거가 약했다.
  - 보상은 거의 평탄했지만 timing return과 strum-progress return은 함께 악화되어 물리 안정성
    향상이 시간 정확도 악화를 가리고 있었다.
- 원인 판단:
  - 모든 timed profile이 목표 첫 줄 시각보다 `250 ms` 앞에서 APPROACH를 열었다.
  - 현재 정책은 APPROACH가 열린 뒤 약 `60 ms`에 RELEASE하므로 구조적으로 약 `190 ms` 이른
    타현이 자연스러운 해가 됐다.
  - 기존 premature penalty는 현재 tolerance 왼쪽 경계보다 더 이른 경우에만 작동해 창 안의
    `-186 ms` 해에는 비용이 없었다.
- 아직 추론인 부분:
  - profile별 접근 lead를 줄였을 때 기존 물리 strum을 유지하면서 목표 중심으로 이동하는지는
    fresh 장기 run으로 확인해야 한다.
- 개선 가설:
  - T0 `250 ms`에서 시작해 T1 `140 ms`, 최종 `70 ms`까지 profile별 접근 lead를 줄이면
    현재 정책의 약 60 ms 운동 지연을 감안해 RELEASE 중심이 허용 gate 안으로 이동한다.
  - READY를 획득한 뒤 접근 시작 전까지 작은 대기 보상을 주고, 접근은 정해진 시각에만 열면
    일찍 출발할 유인을 줄이면서 무기한 대기는 방지할 수 있다.
  - tolerance 안에서도 profile별 grace보다 이른 RELEASE에 즉시 bounded cost를 주고 기존
    대칭 timing 품질 가중치를 강화하면 중심화 신호를 물리 completion과 분리할 수 있다.
- 기존 시도와 다른 점: tolerance와 승급 gate를 다시 바꾸는 것이 아니라, 실제 운동 명령이
  열리는 시각과 창 내부의 조기 편향 비용을 직접 교정한다.
- 구현:
  - `strike_cfg.py`와 `learning/strike_curriculum.py`에 profile별 접근 lead, early grace/scale과
    동적 state/apply를 추가했다. T0 `250 ms`, T1 `140 ms`, 최종 Z2 `70 ms`로 단조 감소한다.
  - `env/strike_events.py`에 접근 시작 경계와 bounded 조기 타현 비용을 순수 tensor 규칙으로
    추가하고, `task_strike.py`의 모든 timed 첫 event READY 전이에 적용했다.
  - timed READY 대기 품질과 wait reward, grace 밖 early-center penalty를 reward와 episode/rollout
    로그에 연결하고 S2 timing-progress 가중치를 `1.0→2.0`으로 높였다.
  - reward alignment monitor는 reward가 오르지 않아도 평탄한 상태에서 signed mean 절댓값이
    `15 ms` 넘게 악화되면 경고한다. plot과 자동 분석에는 wait/early-center return을 추가했다.
  - recorder는 stage/tolerance뿐 아니라 profile, zone, reward core와 새 timed-approach 상태까지
    checkpoint 그대로 복원한다.
  - 변경 파일·함수: curriculum profile, timed READY 전이, strike reward, rollout/episode 지표,
    checkpoint 계약, recorder 복원, 정렬 경고와 plot을 함께 수정했다.
  - 설정·계약 변경: profile마다 `approach_lead_s`, `timing_early_grace_ms`,
    `timing_early_penalty_scale_ms`를 저장·복원하고 environment/curriculum/checkpoint/evaluation
    schema를 올린다.
  - checkpoint 호환성·재시작 위치: phase와 reward 의미가 바뀌므로 STRIKE-009 checkpoint의
    resume 및 policy initialization을 금지하고 A0 fresh run으로 시작한다.
- 검증:
  - profile 접근 lead 단조 감소, 접근 경계 전/후, grace 안·밖, late와 bounded early cost 검사를
    통과했다.
  - wait/early penalty stage mask, 동적 checkpoint 불일치와 reward-flat/timing-worse 경고 검사를
    통과했다.
  - Strike 전용 CPU 회귀 스크립트 15개와 checkpoint contract, PPO actor advantage, run layout,
    `train.py` task dispatch가 모두 통과했다.
  - `20260825_strike011_smoke_complete`에서 8-env·1-iteration GPU PhysX 학습, v10 checkpoint,
    v6 evaluation, 분석·plot·motion diagnostics 자동 생성을 끝까지 통과했다.
  - 최종 소스의 `20260825_strike011_t1_final_smoke`에서 S2/T1 250 ms를 고정해 실제 runtime
    로그와 checkpoint에
    `approach_lead=0.14 s`, early grace `75 ms`, scale `150 ms`가 전달되는 것을 확인했다.
    untrained 1-iteration 정책의 성능 gate 실패는 실행 검사의 예상 결과다.
  - fresh 장기 run의 timing 중심화 결과는 아직 확인하지 않았다.
- 사전 성공 기준:
  - T1 첫 300~500 iteration에서 signed mean 절댓값이 기존 `186 ms`보다 감소하고 `110 ms`
    이하로 들어오는 추세가 있어야 한다.
  - p10이 `-190 ms` 이상으로 회복되고 timing return이 strum-progress와 함께 개선되어야 한다.
  - 물리 completion/traversal/order/direction은 각각 `0.95/0.95/0.98/0.98` 이상을 유지한다.
  - T2 진입 뒤 200 iteration 적응 구간에서 즉시 rollback이나 물리 붕괴가 없어야 한다.
- 실제 결과: CPU 및 A0/S2 GPU 배관 검증 완료, fresh 장기 run 전.
- 영상 판정: 새 run의 약 2,000/4,000 checkpoint 두 view에서 READY 대기와 목표 근처 sweep을
  확인한다.
- 재발 방지 결정: timing gate가 실패하면 tolerance뿐 아니라 목표 시각 대비 제어 phase가
  언제 열리는지와 RELEASE까지의 운동 지연을 함께 기록한다.
- 다음 행동: 구현·CPU 회귀 후 A0 fresh run으로 T1 중심화 대조 학습을 시작한다.
- 상태: `검증 전`

### STRIKE-012 — S3 원곡 전체 평가 영상 분리

- 시기: 2026-08-26
- 분류: `ARTIFACT`, `EVALUATION`, `RECOVERY`
- 연결된 이전 실험: STRIKE-009, STRIKE-010, STRIKE-011
- 기준 run / checkpoint:
  `strike/training/runs/20260825_2020_00_SS1-68-E_comp`
- 문제와 관측 사실:
  - 기존 주기 영상은 현재 curriculum episode를 첫 `done`까지만 녹화한다.
  - 실제 저장된 S1/S2 영상은 약 6.0/1.67/1.40초이며, 원곡 41.94초 전체 평가 영상이 아니다.
  - `artifact_max_steps=900`은 최대 상한일 뿐이고 S2 episode가 먼저 끝나므로 영상 길이를
    보장하지 않는다.
- 원인 판단:
  - 학습 중 복기용 현재-stage 영상과 S3 최종 판정용 전체곡 영상이 하나의 파일 이름과 녹화
    절차를 공유했다.
  - S3에 전체곡 모드를 적용하지 않으면 stage horizon 또는 첫 episode 종료에서 녹화가 끝난다.
- 아직 추론인 부분:
  - S3 정책이 원곡 전체 타임라인을 실제로 완주할지는 S3 checkpoint가 생성된 뒤 확인해야 한다.
- 개선 가설:
  - S3 checkpoint에서 현재-stage 짧은 영상과 별도로 원곡 속도 전체곡 모드를 켜고 환경이 계산한
    전체곡 horizon까지 두 카메라를 녹화하면 약 42초의 연속 평가 근거를 남길 수 있다.
  - 중간 `done`을 무시해 reset된 episode를 이어 붙이지 않고, 최종 timeline 완료와 안전 실패를
    report에 구분하면 영상 길이와 평가 의미가 일치한다.
- 기존 시도와 다른 점: 주기 영상을 무조건 길게 늘리지 않고 S3에서만 이름·report가 분리된
  원곡 전체 평가 묶음을 추가한다.
- 구현:
  - `learning/run_layout.py`, `learning/periodic_checkpoint_video.py`에 일반 rollout과 충돌하지 않는
    S3 전체곡 두-view/report 경로, 원곡 길이 계약과 의미 기반 완료 판정을 추가했다.
  - `tools/record_strike_rollout.py`는 episode 종료 사유, simulation/video 초, reset 뒤 이어 붙이지
    않았다는 상태를 report에 남긴다. `--full-song`은 S3 checkpoint만 허용하고 원곡 속도와 환경이
    계산한 전체곡 horizon을 사용한다.
  - `train_strike.py`는 S3 주기 checkpoint에서 기존 현재-stage 영상과 별도로 전체곡 영상을
    녹화하고, 최종 S3 checkpoint에는 주기 간격과 관계없이 전체곡 묶음을 보장한다.
  - 전체곡 녹화 동안 wrong-crossing 조기 종료는 진단값으로만 남기고 종료 조건에서는 제외한다.
    non-finite와 속도 폭주 같은 복구 불가능한 안전 종료는 유지하며, 첫 `done` 뒤 다른 episode를
    이어 붙이지 않는다.
  - 녹화 전 stage/tolerance/tempo/strum/profile/zone/reward-core/approach 상태를 저장하고 종료 뒤
    같은 값과 새 PPO observation으로 복원한다.
  - 설정·계약 변경: policy/environment 의미와 checkpoint schema는 유지하고 영상 산출물 계약만
    `tab2body.strike_full_song_rollout.v1`로 확장했다.
  - checkpoint 호환성·재시작 위치: runtime semantic fingerprint 파일은 바꾸지 않아 기존
    STRIKE-011 checkpoint와 호환을 유지한다. 실행 중인 Python 프로세스는 코드를 다시 읽지 않으므로
    다음 재시작/재개부터 자동 전체곡 녹화가 적용된다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - Python 3.8에서 Strike 전용 CPU 회귀 15개, checkpoint contract, PPO actor advantage,
      run layout, `train.py` task dispatch와 정적 compile을 통과했다.
    - 41.9439초·105-event fixture에서 원곡 구간 최소 2,548 step 판정과 조기 종료/완료 경계를
      검사했다.
    - runtime 전체 상태가 full-song 전환 뒤 동일하게 복원되는 회귀 검사를 추가했다.
    - `20260826_strike012_s3_smoke_t2`는 실제 GPU PhysX에서 S3 1-iteration 학습과 v10 checkpoint
      생성까지 통과했다. 당시 별도의 fret 장기 학습 두 개가 GPU를 점유하고 있어 최종 S3 평가가
      장시간 대기했고, 기존 학습을 방해하지 않도록 전체곡 렌더 전에 smoke를 중단했다.
  - 학습 조건과 대조 run: S3 checkpoint에서만 별도 전체곡 묶음이 생성되는지 확인한다.
  - 사전 성공 기준:
    - S0~S2 checkpoint에는 기존 remembered/current/report만 생성된다.
    - S3 checkpoint에는 `_full_song_remembered.mp4`, `_full_song_current.mp4`,
      `_full_song.json`이 추가된다.
    - 전체곡 report는 원곡 속도, 예상/실제 step·초, 최종 timeline 완료와 조기 안전 종료 여부를
      명시한다.
    - 완료된 전체곡은 한 episode이고 두 영상 길이가 환경의 전체곡 horizon과 한 frame 이내로
      일치한다.
    - 녹화 뒤 학습 stage·tempo·PPO 관측이 원상 복구된다.
  - 실제 결과: CPU 계약과 실제 S3 환경/checkpoint 생성까지 검증했으며, 42초 MP4 실측은 GPU가
    비는 시점에 남아 있다.
  - 영상 판정: remembered/current 두 시점에서 전체 105 gesture의 방향·통과 줄·정지/회복을
    확인한다.
- 재발 방지 결정: 현재 curriculum 동작 복기 영상과 전체곡 최종 평가 영상을 파일·report·완료
  조건 모두에서 구분한다.
- 다음 행동: 다음 S3 checkpoint에서 자동 생성된 report의 `captured_original_song_duration=true`,
  `stitched_after_episode_reset=false`, 실제 약 42초 두 영상을 확인한다.
- 상태: `검증 전`

### STRIKE-013 — 피크 파지 운동학의 전 단계 보존

- 시기: 2026-08-26
- 분류: `CONTROL`, `FORGETTING`, `REWARD`, `GATE`, `METRIC`
- 연결된 이전 실험: STRIKE-002, STRIKE-011, STRIKE-012
- 문제와 관측 사실:
  - 기준 run `strike/training/runs/20260825_2020_00_SS1-68-E_comp`의 S3 영상에서 손 모양이
    눈에 띄게 풀렸다.
  - iteration 20,462의 binary `strike_grip_success_rate`는 약 `0.989`로 gate를 통과했지만
    rollout `curriculum_grip_quality`는 약 `0.897`이었다.
  - 원곡 속도 전체곡 영상의 마지막 grip quality는 약 `0.820`까지 낮아졌다.
  - A0 grip 가중치 `1.0`에 비해 S3 가중치는 `0.003`뿐이고, 기존 gate는 엄지·검지와 자유
    손가락 RMS가 각각 약 12/15도 안인 frame 비율만 사용했다.
- 원인 판단:
  - 후기 stage의 타현·timing 보상이 손 모양 비용보다 훨씬 커서 검지를 풀어 피크 궤적을 만드는
    우회가 가능했다.
  - `RH:pick`은 `RH:index2`에 붙어 있으므로 검지 자세가 풀리면 피크 끝의 위치와 방향도 바뀐다.
    뒤늦은 자세 교정은 이미 학습한 팔·손목 궤적의 목표 운동학을 바꾸게 된다.
  - binary frame 비율은 평균 품질, 긴 연속 붕괴와 곡 후반 최악 구간을 숨길 수 있었다.
- 아직 추론인 부분:
  - 새 residual 범위 `0.08/0.22 rad`가 strum 표현력과 자연스러움 사이의 최적 절충인지는 장기
    run과 영상 비교 전에는 확정할 수 없다.
- 개선 가설:
  - 엄지·검지는 작은 residual, 중지·약지·소지는 더 넓은 residual로 제어하고 같은 계약을
    A0~S3에서 유지하면 피크 끝 운동학이 먼저 고정된다.
  - 연속 quality와 tail/streak gate를 승급과 전체곡 평가에 함께 적용하면 평균 성공률로 자세
    붕괴를 숨길 수 없다.
- 기존 시도와 다른 점:
  - S3 보상만 사후에 키우지 않는다. action이 표현할 수 있는 손 자세 범위, frame reward,
    curriculum, 최종 평가와 영상 report를 동시에 바꾼다.
  - 손 전체를 고정하지 않고 엄지·검지와 자유 손가락의 허용 범위를 분리한다.
- 구현:
  - `strike_cfg.py`, `env/rewards/strike.py`, `env/tasks/task_strike.py`에서 손가락 action을 기준
    자세 residual로 변환한다. 엄지·검지는 `±0.08 rad`, 자유 손가락은 `±0.22 rad`다.
  - 모델의 초기 평균과 runtime audit 명령도 새 action 의미에 맞춰 손가락 residual `0`,
    팔·손목 초기 자세 명령으로 구성한다.
  - A1 grip 가중치는 `0.10`, A2~S3는 `0.02`로 유지한다.
  - episode별 grip mean/p05/min, pinch/free mean, quality `<0.85` frame 비율과 최대 연속 frame을
    저장한다. curriculum은 각각 `0.92/0.85/0.95/0.85/0.05/12` gate를 모든 단계에 적용한다.
  - `learning/ppo.py`는 raw frame quality를 모아 iteration p05/min을 다시 계산하고 최대 streak를
    평균내지 않는다.
  - `learning/strike_evaluation.py`, `train_strike.py`는 같은 지표를 최종 gate와 `ANALYSIS.md`에
    적용한다.
  - `tools/record_strike_rollout.py`는 전체 rollout의 grip 요약과 `passed`를 JSON의
    `grip_preservation`에 기록한다.
  - 설정·계약 변경: curriculum/environment/checkpoint/evaluation schema는
    `v9/v10/v11/v7`이다.
  - checkpoint 호환성·재시작 위치: action 의미가 바뀌었으므로 STRIKE-012 이전 checkpoint의
    resume과 initialization을 모두 금지하고 A0 fresh run으로 시작한다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - 정적 compile, Strike 전용 CPU 회귀 15개, checkpoint contract와 PPO actor advantage 검사가
      모두 통과했다.
    - 현재 Codex 실행 환경에서는 CUDA driver가 노출되지 않아 `rl38` GPU smoke는 환경 생성 전
      resource preflight에서 중단됐다. 코드 실패로 판정하지 않고 실제 CUDA 셸에서 재검증한다.
  - 학습 조건과 대조 run: 기존 S3 run은 진단 기준선으로만 보존하고 fresh A0 run과 비교한다.
  - 사전 성공 기준:
    - A0~S3 모든 단계에서 grip mean/p05와 두 관절군 quality gate를 통과한다.
    - bad-frame rate가 5% 이하이고 12 frame을 넘는 연속 붕괴가 없다.
    - S2/S3 strum completion·timing이 기존 목표를 만족하면서 엄지·검지 RMS와 영상 파지가
      유지된다.
    - S3 원곡 전체 report의 `grip_preservation.passed=true`이고 곡 후반 영상에서도 피크가
      손에서 풀려 보이지 않는다.
  - 실제 결과: CPU 구현·회귀 검증 완료, GPU smoke와 fresh 장기 run은 검증 전이다.
  - 영상 판정: remembered/current 두 view에서 엄지·검지 파지, 자유 손가락 자세, 피크 끝과
    줄의 상대 위치를 곡 처음·중간·끝에서 비교한다.
- 재발 방지 결정: 피크 끝의 기준 운동학에 영향을 주는 grip은 초기 자세 보상이 아니라 모든
  후기 단계의 보존 기술로 취급한다. binary 성공률만으로 human-like grip을 주장하지 않는다.
- 다음 행동: CUDA 환경에서 fresh smoke 뒤 A0부터 새 장기 학습을 시작한다.
- 상태: `검증 전`

### STRIKE-014 — S3 full/handoff dual recovery

- 시기: 2026-08-27
- 분류: `RECOVERY`, `CURRICULUM`, `GATE`, `METRIC`, `CHECKPOINT`
- 연결된 이전 실험: STRIKE-006, STRIKE-012, STRIKE-013
- 기준 run / checkpoint:
  `strike/training/runs/20260826_1237_00_SS1-68-E_comp/checkpoints/strike_027500.pt`
- 문제와 관측 사실:
  - 기준 run은 iteration `27,746`, S3 stage iteration `21,870`에서 tempo lambda `0.0`에 정체됐다.
  - 최근 1,000 iteration의 F1 `0.989`, strum completion `0.983`, direction `0.998`, timing
    MAE `6.71 ms`, grip mean/p05 `0.993/0.986`은 양호했지만 recovery completion은 약 `0.777`로
    gate `0.95`를 통과하지 못했다.
  - 기존 full recovery는 `12 frame=0.20 s`, 다음 접근 lead는 `0.07 s`이므로 사건 간격이 최소
    `0.27 s`여야 했다. tempo 0 timeline의 104개 간격 중 27개는 이보다 짧았다.
  - 8-event episode의 마지막 사건만 항상 full recovery가 가능하다고 보면 고정 기준의 이론상
    최대는 `(1 + 7×77/104) / 8 = 0.7728`이며 실제 `0.777`과 일치한다.
- 원인 판단:
  - 정책 실패가 아니라 곡의 사건 간격과 고정 12-frame 성공 분모가 모순이었다.
  - 모든 사건에서 직전 줄 detector 재무장을 기다리면 서로 다른 다음 줄로 자연스럽게 이어지는
    빠른 phrase도 불필요하게 막힌다.
- 아직 추론인 부분:
  - 1 frame까지 허용한 handoff가 영상에서 충분한 follow-through로 보이는지, 새 critic으로 전이한
    정책이 초기 S3에서 안정적으로 유지되는지는 장기 run 전에는 확정할 수 없다.
  - 같은 줄 handoff 비율과 실제 원곡 tempo에서 필요한 최소 separation은 새 로그로 확인해야 한다.
- 개선 가설:
  - A0~S2와 마지막 사건은 기존 full recovery를 보존하고, S3의 짧은 중간 간격만 다음 접근 전
    확보 가능한 길이로 줄이면 이전 기술을 바꾸지 않고 물리적으로 가능한 gate를 만들 수 있다.
  - 서로 다른 줄 handoff만 직전 줄 재무장을 생략하고 같은 줄은 재무장을 유지하면 detector 중복
    방지와 빠른 phrase 실행을 동시에 만족한다.
- 기존 시도와 다른 점:
  - recovery gate를 단순히 `0.77`로 낮추지 않는다. 곡이 요구한 회복 종류를 event마다 명시하고
    scheduled/full/handoff 성능을 별도 분모로 검증한다.
  - 고정 12-frame 지표를 삭제하지 않고 구조적 한계를 확인하는 진단값으로 보존한다.
- 구현:
  - `env/strike_events.py`에 다음 사건 시각, approach lead와 60 Hz clock으로 available/required
    frame을 계산하는 dual-recovery plan, 전환 조건과 one-shot progress 함수를 추가했다.
  - `env/tasks/task_strike.py`는 성공한 event마다 full 또는 handoff를 고정한다. 충분한 간격과 마지막
    사건은 12 frame+재무장, 짧은 서로 다른 줄은 1~11 frame 뒤 접근, 짧은 같은 줄은 해당 frame과
    재무장을 모두 요구한다.
  - A0~S2의 기존 보상·완료 조건은 그대로 두고 S3 보상만 scheduled recovery 진척과 완료 pulse를
    사용한다. 마지막 timeline 완료는 계속 12-frame full recovery를 요구한다.
  - episode/PPO/plot/video report에 fixed diagnostic, scheduled, full, handoff completion과 event 수,
    handoff 평균 요구 frame, same-string 여부를 추가했다.
  - curriculum과 deterministic evaluation은 S3에서 scheduled/full/handoff를 각각 gate하고 A0~S2는
    기존 fixed recovery gate를 사용한다.
  - `--initialize-from`은 이전 checkpoint의 actor, `log_std`, observation normalization만 가져오고
    critic, optimizer, iteration과 curriculum evidence는 초기화해 S3 tempo 0 새 run을 만든다.
    goal, grip, 관측 manifest, 제어 관절, action 의미, simulation rate와 asset이 다르면 거부한다.
  - 설정·계약 변경: curriculum/environment/checkpoint/evaluation schema는 `v10/v11/v12/v8`이다.
  - checkpoint 호환성·재시작 위치: v11 checkpoint의 일반 `--checkpoint` resume은 거부한다.
    STRIKE-013과 동일한 정책 인터페이스의 checkpoint만 `--initialize-from`으로 S3 전이할 수 있으며,
    그렇지 않으면 A0 fresh run을 사용한다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - dual plan의 12/9/1 frame 경계, 서로 다른 줄 handoff, 같은 줄 재무장, final full recovery와
      one-shot completion을 CPU 단위 검사했다.
    - Strike 전용 CPU 회귀 스크립트 15개, checkpoint contract와 정적 compile을 모두 통과했다.
    - 기존 A0~S2 fixed recovery gate가 유지되고 S3에서 fixed `0.77`만으로 실패하지 않으며
      scheduled/full/handoff 중 하나가 부족하면 명시적으로 실패하는 것을 검사했다.
    - `00_SS1-68-E_comp`의 104개 사건 간격은 모든 tempo 수준에서 full 77개, handoff 27개로
      분류됐고 handoff 중 6개는 같은 줄 재무장을 요구한다. 평균 요구 frame은 tempo 0의
      `11.31`에서 원곡 tempo의 `10.13`으로 자연스럽게 줄었다.
    - 현재 Codex 실행 환경에서는 CUDA가 노출되지 않아 실제 smoke는 환경 생성 전 resource
      preflight에서 중단됐다. 실제 CUDA 셸에서 재검증해야 한다.
  - 학습 조건과 대조 run: 기준 v11 actor를 `--initialize-from`으로 옮긴 S3 tempo 0 run과 A0 fresh
    run을 구분해 기록한다. 이전 run의 fixed recovery `0.777`은 진단 기준선으로 보존한다.
  - 사전 성공 기준:
    - S3 scheduled recovery `≥0.95`, full `≥0.95`, handoff `≥0.95`를 동시에 만족한다.
    - fixed 12-frame diagnostic은 짧은 간격 비율에 따라 낮아도 승급을 막지 않는다.
    - reset/blocked rate가 각각 stage gate 이하이고 같은 줄 handoff에서 재무장 전 중복 crossing이 없다.
    - tempo `0→1` 전 과정에서 F1, strum, timing과 grip 지표가 STRIKE-013 기준보다 악화되지 않는다.
  - 실제 결과: 구현과 CPU 계약 검증 완료, GPU smoke와 장기 S3 재학습은 검증 전이다.
  - 영상 판정: 짧은 간격에서 직전 stroke의 follow-through가 다음 entry로 이어지는지, 피크가 불필요한
    home pose 왕복을 하지 않는지, 같은 줄 재타현은 분리·재무장되는지 두 view에서 확인한다.
- 재발 방지 결정: 곡 구조상 달성 불가능한 고정 길이 행동을 성공 분모로 두지 않는다. 낮은 비율을
  gate 완화로 숨기지 말고 event별 물리 가용 시간과 실제 요구 행동을 함께 로그로 남긴다.
- 다음 행동: CUDA 환경에서 기준 checkpoint 정책 전이 smoke를 실행한 뒤 S3 tempo 0부터 재학습하고,
  첫 500~1,000 iteration의 scheduled/full/handoff와 grip/timing을 비교한다.
- 상태: `검증 전`

### STRIKE-015 — S3 0.75 정체의 원인별 판정과 실패 구간 재학습

- 시기: 2026-08-28
- 분류: `S3`, `TERMINATION`, `GATE`, `FAILURE_MINING`, `LOG_INTEGRITY`, `EVALUATION`
- 연결된 이전 실험: STRIKE-012, STRIKE-013, STRIKE-014
- 기준 run / checkpoint:
  `strike/training/runs/20260827_1246_00_SS1-68-E_comp/checkpoints/strike_026000.pt`
- 문제와 관측 사실:
  - 기준 run은 S3 tempo `0.75`에서 약 12,000 iteration 동안 정체됐다.
  - 정상 파싱되는 최근 구간의 F1 `0.9783`, blocked crossing `0.0190`, wrong-crossing 종료
    `0.0609`, scheduled/full/handoff recovery `0.9922/0.9933/0.9597`, strum completion
    `0.9743`, timing p95 `16.43 ms`, grip mean/p05 `0.9864/0.9762`였다.
  - 이벤트별 FP 약 `1.7%`라도 8-event episode의 초반 4개 사건 안에서 하나 이상 발생할 확률은
    약 `6.6%`다. 기존 `minimum_resolved_events=4`, `max_rate=0.20`은 네 번째 사건의 첫 오류를
    즉시 `1/4=25%`로 보아 종료시켰고 실제 종료율 `6.1%`와 일치했다.
  - `logs/metrics.jsonl`은 iteration 약 `26002`부터 여러 JSON object가 한 줄 안에서 섞여
    파싱할 수 없었다. 기존 append는 run writer 소유권과 record lock을 보장하지 않았다.
- 원인 판단:
  - 물리 traversal·timing·grip 전체가 붕괴한 것이 아니라, 이벤트 수준 오차를 짧은 episode의
    비율 종료로 확대하는 판정과 모든 tempo에 동일한 zero-failure gate를 사용한 것이 1차 병목이었다.
  - 정체 뒤에도 시작 구간을 균일 표본화했으므로 blocked/rearm이 반복되는 소수 구간에 충분한
    update가 집중되지 않았다.
  - episode 평균 F1을 다시 평균하면 사건 수가 다른 episode의 증거가 왜곡될 수 있었다.
- 아직 추론인 부분:
  - 실패 구간 30% 표본화가 0.75 이후 tempo에서도 충분한지, handoff completion을 유지한 채
    blocked crossing을 `1%` 이하로 내릴 수 있는지는 새 장기 run으로 확인해야 한다.
  - 기준 actor를 tempo `0.5`에서 전이하는 것이 fresh A0보다 빠른지는 대조 run 전에는 확정할 수 없다.
- 개선 가설:
  - 오타현 비율은 해결된 사건에서만 계산하고 진단으로 유지하며, 즉시 종료는 누적 4회 또는
    연속 3-event 같은 반복적·치명적 오류에만 적용한다.
  - 안전 실패는 모든 tempo에서 0을 요구하되 음악적 wrong 종료는 tempo `0.75`에서 관측 가능한
    범위를 허용하고 원곡 속도로 갈수록 다시 엄격하게 줄인다.
  - 정체 전부터 event별 실패 score를 모으고 정체 시 30% hard window + 70% 전곡 uniform으로
    표본화하면 어려운 구간을 보완하면서 기존 기술을 rehearsal할 수 있다.
- 기존 시도와 다른 점:
  - 전체 failure gate를 임의로 낮추지 않는다. non-finite·관통 등 안전 실패와 wrong-crossing 기반
    성능 실패를 분리한다.
  - 평균 성공률 대신 TP/FP/FN와 blocked/recovery raw count를 합친 뒤 precision/recall/F1/rate를
    한 번 계산한다.
  - 원곡 전체 영상에 frame별 실제 crossing과 event별 계획·성공·miss·blocked·timing을 함께
    저장해 높은 episode F1만으로 성공을 주장하지 않는다.
- 구현:
  - `env/metrics.py`와 `env/tasks/task_strike.py`는 rate 초과를 event resolution에서만 판정하며,
    rate는 기본적으로 종료시키지 않는다. count/consecutive 원인을 별도 로그로 보존한다.
  - `learning/strike_curriculum.py`는 safety failure를 항상 fail-closed로 검사하고 S3 tempo별
    F1/wrong 종료/blocked gate를 사용한다. raw TP/FP/FN와 blocked count를 pooled evidence로
    재계산한다.
  - tempo gate `(F1, wrong 종료, blocked)`는 `0.75=(0.975,0.08,0.025)`에서 시작해
    `1.0=(0.99,0.01,0.01)`로 엄격해진다.
  - event failure score와 정체 hard-window sampler를 checkpoint에 저장한다. 실패 score가 없는
    경우에는 자동으로 균일 표본으로 돌아간다.
  - `learning/run_io.py`는 run별 단일 writer lease, lock 기반 한 줄 append, 시작 시 JSONL 전수
    검증을 수행한다. 손상된 기존 metrics에는 더 쓰지 않고 정확한 줄 번호로 중단한다.
  - `tools/record_strike_rollout.py`의 원곡 report schema v2는 105개 계획 event와 실제 crossing
    trace, TP/FP/FN, completion, blocked, wrong, signed timing/p95를 저장한다.
  - `--initialize-from`의 기본 시작 tempo를 `0.5`로 바꿨고 `--initialize-tempo`로 명시할 수 있다.
    actor·분산·관측 정규화만 가져오며 critic·optimizer·iteration·curriculum은 초기화한다.
  - curriculum/environment semantic contract는 각각 `v11`, `v12`,
    `tempo_gated_failure_mining.v11`이다. 이전 checkpoint의 일반 resume은 허용하지 않는다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - rate가 미해결 frame에서 종료되지 않고 해결 event에서만 진단되는 계약, rate 종료 비활성,
      tempo별 gate, raw-count pooled F1, writer 동시 append/lease/손상 감지, event trace 집계를
      CPU 검사했다.
    - Strike curriculum/runtime/artifact/periodic-video 계약과 정적 compile을 통과했다.
    - Isaac Gym GPU smoke와 장기 정책 개선은 아직 검증 전이다.
  - 학습 조건과 대조 run: 기준 `strike_026000.pt` actor를 새 run의 tempo `0.5`에서 전이하고,
    fresh A0 run과 구분해 기록한다. 손상된 기준 run의 metrics는 복구·덮어쓰기하지 않는다.
  - 사전 성공 기준:
    - tempo `0.75`에서 safety failure `0`, F1 `≥0.975`, wrong 종료 `≤0.08`, blocked `≤0.025`를
      3개 evidence window 연속 통과한다.
    - tempo가 올라갈수록 설정된 gate가 엄격해지고 `1.0`에서 F1 `≥0.99`, wrong 종료·blocked
      각각 `≤0.01`을 만족한다.
    - hard sample 비율이 약 0.30이며 전곡 uniform 0.70이 유지되고, 특정 event만 반복하는 collapse가 없다.
    - 원곡 전체 report의 event trace로 strum 순서·방향·통과 줄과 오차 위치를 재현할 수 있다.
  - 실제 결과:
    - 초기 코드·CPU 계약 검증을 통과한 뒤
      `strike/training/runs/20260828_1109_00_SS1-68-E_comp`에서 재학습했다.
    - iteration `8,500`의 deterministic 전체곡 F1은 `0.99746`이었지만
      `10,500`에서 `0.96429`로 떨어졌고 FP/FN은 `1/0`에서 `7/7`로
      악화됐다. iteration `11,000`에서 event 86의 raw failure score가 `334.824`로
      특정 구간에 표집이 붕괴했다.
    - 따라서 30% raw-count mining을 유지하지 않고 STRIKE-016으로 보완한다.
  - 영상 판정: hard failure 상위 구간의 blocked/rearm crossing이 줄고, 곡 후반까지 grip과
    down/up 방향 및 strum sweep이 유지되는지 두 view와 event trace를 함께 본다.
- 재발 방지 결정: 사건 수가 적은 episode의 순간 비율을 즉시 종료 근거로 쓰지 않는다. 안전 실패,
  성능 종료, 품질 진단을 분리하고 pooled raw count와 원곡 event trace를 보존한다. 하나의 run에는
  한 trainer만 metrics를 쓸 수 있어야 한다.
- 다음 행동: 실제 CUDA 셸에서 `strike_026000.pt` actor를 tempo `0.5`로 전이해 smoke 후 장기 학습하고,
  `0.5→0.75` 전환 전후 1,000 iteration의 pooled gate와 hard-sample 분포를 비교한다.
- 후속: 위 재학습에서 raw-count failure mining 붕괴가 확인돼 STRIKE-016으로 보완한다.
- 상태: `보완 필요`

### STRIKE-016 — S3 실패 표집 붕괴와 전곡 성능 망각 방지

- 시기: 2026-08-28
- 분류: `S3`, `FAILURE_MINING`, `EVIDENCE`, `FORGETTING`, `LOG_INTEGRITY`,
  `EVALUATION`, `ARTIFACT`
- 연결된 이전 실험: STRIKE-012, STRIKE-013, STRIKE-014, STRIKE-015
- 기준 run / checkpoint:
  - run: `strike/training/runs/20260828_1109_00_SS1-68-E_comp`
  - 가장 좋은 전체곡 기준: `checkpoints/strike_008500.pt`
  - 전원 종료 전 마지막 저장본: `checkpoints/strike_011000.pt`
- 문제와 관측 사실:
  - 정책은 iteration `2,322`에서 원곡 속도에 도달했고 `8,322`에서 S3 최대 체류를 넘어
    hard-window 표집을 시작했다.
  - deterministic 전체곡 traversal F1은 iteration `8,500`의 `0.99746`에서 `10,500`의
    `0.96429`로 하락했다. FP/FN은 `1/0`에서 `7/7`, blocked/wrong은 `1/1`에서 `4/7`로
    증가했지만 timing p95는 `15.56 ms`에서 `13.81 ms`로 좋아졌다.
  - iteration `11,000`의 event failure score는 event 86이 `334.824`, 다음 event가
    `9.924`였고 105개 중 104개 event에 0보다 큰 score가 남았다. event 86을 포함하는
    시작 window 79~86이 hard 표집 질량을 사실상 독점했다.
  - hard 표집 뒤 학습 표본의 F1은 약 `0.982`에서 `0.970`, blocked rate는 약 `0.016`에서
    `0.043`으로 악화됐다. hard 표본 frame은 약 25%였다.
  - `logs/metrics.jsonl`은 물리 line 3부터 JSON record가 중간에서 끊기고 다음 record가
    이어졌다. 마지막 전원 종료만으로 설명할 수 없는 실행 중 무결성 문제다.
  - 전체곡 report는 schema v2로 정상 완주했지만 완료 확인 함수가 v1만 허용해 일부 산출물을
    실패로 기록했다.
- 원인 판단:
  - failure score가 event별 노출 횟수로 정규화되지 않은 raw 실패 횟수라서, 한 번 많이 뽑힌
    구간이 더 큰 score를 얻고 다시 더 많이 뽑히는 양의 피드백이 생겼다.
  - 학습용 1,024개 환경을 그대로 쓰는 deterministic 영상·전체곡 평가에서도
    failure score 갱신이 켜져 있었다. 평가의 동일 실패 한 번이 환경 수만큼
    bincount에 더해져 event 86 score 폭증을 일으킨 직접 오염 경로였다.
  - hard episode와 uniform episode를 합친 동일한 분포로 curriculum gate를 계산해, 정체 뒤
    학습 분포가 바뀌는 순간 승급 평가 분포도 함께 바뀌었다.
  - S3 reward-alignment 감시가 없어서 reward와 timing이 좋아지는 동안 전곡 F1·blocked가
    악화되는 목적 불일치를 경고하지 못했다.
- 아직 추론인 부분:
  - 15% hard 표집과 window 확률 상한이 event 86의 blocked/rearm을 줄이면서 전체곡 rehearsal을
    충분히 보존하는지는 새 장기 run 전에는 확정할 수 없다.
  - iteration 8,500 actor를 어느 tempo에서 전이하는 것이 가장 안정적인지는 `0.95/0.975`
    짧은 대조가 필요하다.
- 개선 가설:
  - event별 실패/노출 EMA로 실패율을 만들고 window별 최대 표집 확률을 제한하면 특정 사건의
    자기강화 붕괴를 막을 수 있다.
  - PPO 학습에는 hard episode를 포함하되 curriculum evidence는 uniform episode만 사용하면
    어려운 구간 보완과 고정 분포 승급 판정을 분리할 수 있다.
  - S3 reward-alignment와 deterministic 전체곡 최고 성능을 별도로 기록하면 timing 보상만
    좋아지는 퇴행을 조기에 발견할 수 있다.
- 기존 시도와 다른 점:
  - hard 표집을 제거하지 않는다. raw count를 노출 보정 실패율로 바꾸고 hard 비율·window 확률을
    동시에 제한한다.
  - gate를 완화하지 않는다. 학습 분포와 평가 분포를 분리해 기존 원곡 gate의 의미를 보존한다.
- 구현:
  - `env/metrics.py`와 `env/tasks/task_strike.py`에 event별 실패 mass와 exposure mass의
    EMA, 전역 사전분포로 보정한 노출 정규화 실패율, bounded window sampler를
    추가했다. prior exposure는 `16`, hard episode 비율은 `0.15`, 하나의 window가
    갖는 최대 표집 확률은 `0.10`이다.
  - hard episode도 PPO update에는 포함하지만 `learning/ppo.py`에서 uniform episode의
    pooled evidence를 별도로 계산한다. `learning/strike_curriculum.py`는 S3 stalled 승급
    gate에 이 uniform evidence만 사용하며 hard 표본 수와 제외 비율을 로그로 남긴다.
  - `train_strike.py`는 주기 영상과 deterministic 전체곡 평가 동안 failure-mining
    갱신을 끄고 기존 mass/exposure/score를 복원한다. 전체곡 report의 안전·grip·
    F1·completion·blocked·wrong·timing 순서로 최고 정책을 고르고
    `evaluations/best_full_song.json`에 경로를 기록하며 F1이 0.01보다 더 하락하면
    퇴행 경고를 남긴다. S3 reward-alignment 감시도 uniform evidence를 사용한다.
  - `learning/run_io.py`는 append 전 pending journal에 offset·payload hash·prefix hash·target
    identity를 fsync한다. 강제 종료 뒤에도 저널과 일치하는 마지막 record만
    정확히 복구하고 중간 손상·대상 교체·검증할 수 없는 tail은 fail-closed 한다.
  - 설정·계약 변경: hard 표집 `0.15`, decay `0.995`, prior exposure `16`,
    window 확률 상한 `0.10`, S3 uniform-only evidence를 기본값으로 사용한다.
    curriculum schema는 `v12`, environment state는 `v13`, semantic contract는
    `exposure_normalized_failure_mining.v12`로 변경했다.
  - checkpoint 호환성·재시작 위치: 정책 입출력은 유지하지만 failure 통계 상태가 달라 일반
    resume은 허용하지 않는다. iteration 8,500 actor를 `--initialize-from`으로 전이한다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - Strike 전용 CPU 회귀 스크립트 17개와 run I/O, PPO actor-advantage,
      checkpoint/full contract, action-saturation 검사를 통과했다.
    - 실패율의 노출 정규화, window 10% 상한, uniform-only 승급 evidence,
      S3 reward-alignment, environment state 복원, report v2 완주 판정, 최고 전체곡
      선택·퇴행 경고, append journal 정상·손상 경계를 회귀 검사로 고정했다.
    - policy-transfer `--smoke`를 실행했지만 현재 셸에서 CUDA가 노출되지 않아 resource
      preflight가 `CUDA is unavailable`로 안전하게 중단했다. 빈 run 디렉터리는 남지 않았다.
      Isaac Gym 환경 생성과 장기 재학습은 CUDA 복구 뒤 검증해야 한다.
  - 학습 조건과 대조 run: iteration 8,500 actor를 새 run으로 전이하고 기존 10,500 전체곡
    report를 퇴행 기준선으로 보존한다.
  - 사전 성공 기준:
    - hard episode 비율이 목표 범위이고 한 window의 표집 확률이 설정 상한을 넘지 않는다.
    - curriculum evidence에는 hard episode가 포함되지 않으며 uniform 표본 수가 로그에 남는다.
    - 원곡 전체 traversal F1이 8,500 기준에서 0.01 이상 하락하면 개선 성공으로 판정하지 않는다.
    - 원곡 속도에서 F1 `>=0.99`, wrong 종료·blocked 각각 `<=0.01`, safety failure `0`을 유지한다.
    - metrics JSONL은 강제 종료 뒤 불완전한 마지막 record만 명시적으로 복구할 수 있고 중간
      손상은 정확한 위치에서 fail-closed 한다.
    - schema v2 전체곡 완주는 실패 산출물로 잘못 분류되지 않는다.
  - 실제 결과: 구현·CPU 계약 검증과 CUDA 부재 fail-fast까지 확인했다. 실제 GPU smoke·장기
    재학습은 검증 전이다.
  - 영상 판정: event 79~86의 up-pick rearm과 사건 8·11·28의 망각 여부를 두 view에서 비교한다.
- 재발 방지 결정: hard-example mining의 점수는 반드시 exposure로 정규화하고, 학습 분포를 바꾼
  표본을 동일한 curriculum 승급 증거로 사용하지 않는다.
- 다음 행동: GPU policy-transfer smoke 뒤 iteration 8,500 actor를 새 S3 run으로 전이한다.
- 상태: `검증 전`

### STRIKE-017 — 입력 불확실성과 방향 반전 recovery를 분리한 일반 품질 계약

- 시기: 2026-08-30
- 분류: `INPUT_QUALITY`, `STRIKE_PLAN`, `PHYSICAL_FEASIBILITY`, `RECOVERY`,
  `OBSERVATION`, `REWARD_ALIGNMENT`, `DATASET_AUDIT`, `RNG_ISOLATION`
- 연결된 이전 실험: STRIKE-014, STRIKE-015, STRIKE-016
- 기준 run / checkpoint:
  - run: `strike/training/runs/20260828_2158_00_SS1-68-E_comp`
  - 진단 시 최신 저장본: `checkpoints/strike_048500.pt`
  - deterministic 전체곡 최고 기록: iteration `36,000`, traversal F1 `0.997455`
- 문제와 관측 사실:
  - stochastic uniform S3 evidence는 F1 약 `0.985`, blocked 약 `0.016`에서 정체되어
    원속도 gate `F1 >= 0.99`, blocked `<= 0.01`을 동시에 통과하지 못했다.
  - 2k~48k 전체곡 report 24개에서 plan event 86은 목표 B현을 `24/24` 맞혔다. 그러나 앞의
    event 85가 성공한 22개 report에서는 high-e를 되돌아가며 `blocked_wait_rearm`을 `22/22`
    발생시켰다. 둘이 함께 clean인 report는 `0/24`였다.
  - event 85의 마지막 high-e traversal 시각에서 event 86의 첫 B현 시각까지는 `46.5 ms`로,
    detector/follow-through가 요구하는 `50 ms`보다 짧다. 사건 중심 시각만 검사하던 기존 validator는
    이 경계를 놓쳤다.
  - fingering source 147~149는 `35.2595/35.2943/35.3408 s`로 `81.3 ms`에 퍼졌지만 JAMS
    note onset은 `35.277968/35.280145/35.283048 s`의 `5.08 ms` 묶음이고 symbolic notes도
    하나의 chord로 표현했다. 사용자가 판단을 위임해 이를 하나의 down strum으로 승인했다.
- 원인 판단:
  - 1차 원인은 PPO 표집량이 아니라 불확실한 upstream onset을 고정 `50 ms` 묶음 규칙으로 바로
    물리 goal로 바꾸고, traversal 끝 offset을 고려하지 않은 입력/plan 계약이다.
  - 2차 원인은 다른 줄 handoff면 detector re-arm을 생략하던 recovery 규칙이다. 다음 up 경로가
    직전 high-e를 다시 지나는데도 exit 아래에서 다음 entry 아래로 직접 이동했다.
  - S3 timing shaping이 dirty event에도 지급돼 빠른 blocked 경로가 늦지만 clean한 경로보다 유리할
    수 있었다. failure mining은 event 86을 정상적으로 찾았지만 구조적으로 불가능한 목표는 해결할
    수 없다.
- 아직 추론인 부분:
  - 수동 오디오 청취는 수행하지 않았다. source JAMS·symbolic mapping·물리 불가능 경계를 근거로
    사용자가 위임한 판정을 적용했으므로, 실제 음향 attack에 대한 직접 청취 증거는 여전히 없다.
  - 새 lift-clearance 경로가 `51.0/51.1 ms`의 근접하지만 feasible한 전이를 원속도에서 얼마나
    안정적으로 수행하는지는 GPU 재학습과 영상 검수가 필요하다.
- 개선 가설:
  - raw onset을 증거로 보존하고 JAMS/provenance·묶음 경계·traversal edge를 학습 전에 감사하면
    데이터 오류와 제어 실패를 분리할 수 있다.
  - 방향 반전의 실제 exit-side→entry-side 선분이 방금 친 줄을 가로지르면 lift와 elevated transfer,
    detector re-arm을 모두 요구해야 오타현 없는 경로가 학습 가능하다.
  - wrong/blocked가 한 번이라도 생긴 event의 timing/microtiming bonus를 0으로 만들면 정확도를
    timing보다 우선할 수 있다.
- 기존 시도와 다른 점:
  - 특정 곡이나 event 86을 코드에 예외 처리하지 않는다. 모든 bundle과 모든 인접 plan event에 같은
    source/edge/path 검사를 적용한다.
  - gate나 detector 허용치를 낮추지 않는다. `AMBIGUOUS`는 검수 대상으로 보존하고
    `INFEASIBLE`만 full-song 시작 전에 fail-closed 한다.
  - 원본 시간을 조용히 변경하지 않는다. 보정은 연속 source ID, `merge|separate`, 이유와 근거가
    모두 있는 reviewed override로만 수행하며 plan에 함께 봉인한다.
- 구현:
  - `env/strike_goals.py`의 raw v3는 필수 `[time,frame,string]`을 유지하면서 선택적
    `event_id/source_time/time_uncertainty_s/source_ref`와 reviewed override를 지원한다. v1/v2는
    계속 읽는다.
  - `env/strike_goal_compiler.py`의 현재 profile은 direction `phrase_dp_microtiming_v3`, transition
    `entry_side_edge_gap_v2`다. 방향 v3 planner는 phrase 전체의 microtiming과 같은 방향 recovery,
    clearance urgency를 비용으로 함께 최적화한다. transition v2는 이전 traversal 마지막 줄 시각과
    다음 첫 줄 시각, 방향·entry side, 직접 경로의 재통과 줄, clearance 필요 여부와 bridge-split
    후보를 계산한다. 구 `strike_plan.v4`도 진단을 파생하며 새 plan은 `transitions[]`를 저장·검증한다.
  - `strike_training_runtime.py`는 full-song에서 원속도 infeasible transition을 GPU 생성 전에
    거부하고 clearance 설정도 fail-fast 검증한다.
  - `env/strike_events.py`와 `env/tasks/task_strike.py`는 path-aware handoff에서
    `release lift → elevated next-entry transfer → approach`를 강제한다. recovery 방향, 현재 음악 방향,
    clearance required/reached 6개 관측을 추가했다. 첫 lift waypoint 도달로 목표가 elevated
    next-entry로 바뀔 때 reach potential baseline/validity를 초기화해 올바른 lift에 목표 전환 음수
    shaping이 붙지 않게 했다.
  - `env/rewards/strike.py`는 wrong/blocked 이력이 있는 event의 timing·strum microtiming 보상을
    차단한다. crossing·recovery 기술과 기존 안전 penalty는 유지한다.
  - `train_strike.py`의 학습 중 평가·주기 영상은 failure-mining 상태와 함께 task generator RNG,
    reset generation을 snapshot/restore한다. 평가용 reset이 이후 hard-window 표집과 학습 reset
    난수열을 바꾸지 않는다. 전역 Torch CPU/CUDA RNG까지 포함한 bitwise resume 계약은 아니다.
  - `tools/audit_strike_goal_quality.py`는 한 곡/전체 bundle을 읽기 전용으로 검사해
    `PASS/AMBIGUOUS/INFEASIBLE` JSON·사람용 보고서를 저장하고 strict 모드에서 infeasible을 exit 2로
    반환한다. 일반 절차는 `canonical read-only audit → evidence가 있는 *.proposed.json → 수동 오디오
    판정 → 승인된 canonical 원자 교체 → strict audit/preflight 재실행`이며, `AMBIGUOUS`나 pending
    후보를 자동 정본화하지 않는다.
  - 사용자가 source 147~149를 하나의 down strum으로 묶는 판단을 위임했고, 후보를
    `approved_user_delegated` 상태로 canonical에 원자 승격했다. 수동 오디오 청취는 수행하지 않았다.
    canonical SHA-256은 raw v3
    `4fa5659f5220eb28ade714842d98fa4a81d90d242e42c2a99acdb93f87cac096`, plan v4
    `efab30028c60e1d2e9c412a6cb36ad1cd84154996b1d1a39c4fe5483bb9ee85f`, review
    `67fe86945199c63cd5135d38ba24631ea02ffff531c6b7aebf82fc20992dcc5f`다.
  - 승격 뒤 `00_SS1` plan은 104 events(61 single/43 strum), direction v3/transition v2,
    최소 edge gap `51.0 ms`, infeasible transition `0`이다. 승격 전 정본·후보·promotion record는
    `data/song_bundles/00_SS1-68-E_comp/training/history/20260830_user_delegated_strum_merge/`에 보존했다.
  - 현재 전체 8개 bundle strict audit는 exit 0,
    `PASS 2 / AMBIGUOUS 6 / INFEASIBLE 0`이다. `00_SS1`은 승인 override가 적용됐지만 다른
    source/grouping/provenance 경고 때문에 곡 단위로는 `AMBIGUOUS`다. 결과는
    `docs/archive/dated/2026-08-30/strike_goal_quality_audit.*`에 저장했다.
  - 설정·계약 변경: clearance height `10 mm`, waypoint 도달 거리 `4 mm`, strike observation
    `321→327`; semantic checkpoint v12에 direction v3/transition v2,
    path-aware recovery/correctness-first timing 계약을 추가했다. curriculum schema는 `v12`, environment
    state는 `v13`이다.
  - checkpoint 호환성·재시작 위치: observation 입력층이 달라 기존 checkpoint의 일반 resume과
    `--initialize-from` actor 전이를 모두 허용하지 않는다. 새 환경은 fresh run으로 시작한다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - compiler transition/override roundtrip, goal timing/direction/microtiming, path-aware re-arm,
      clearance gate, dirty-event timing 차단, runtime preflight, artifact 계약과 전체 bundle 감사를 CPU로
      검사했다.
    - 승격된 canonical plan은 direction v3/transition v2, 104 events, infeasible 0으로 strict audit와
      original-tempo preflight를 통과한다. 전체 감사는 다른 bundle의 ambiguity를 보존하면서 exit 0이다.
    - current path-aware 계약의 최종 CPU 회귀는 `26/26 PASS`다. 현재 호스트는 NVIDIA driver를 사용할 수
      없어 Isaac Gym GPU 환경 생성·PPO update·영상 smoke를 실행하지 못했다.
  - 학습 조건과 대조 run:
    - 승인·canonical 승격·strict audit가 완료됐으므로 새 observation 계약으로 fresh A0부터 학습한다.
      구 36k 전체곡 report는 행동 비교 기준으로만 보존한다.
  - 사전 성공 기준:
    - dataset strict audit의 `INFEASIBLE=0`; 모든 override에 source ID·이유·근거가 남는다.
    - S3 원속도 uniform F1 `>=0.99`, blocked `<=0.01`, wrong 종료 `<=0.01`, safety failure `0`을
      3개 evidence window 연속 통과한다.
    - event별 deterministic trace에서 target hit 전 재통과 blocked가 없고, near-edge 전이의
      clearance required/reached가 영상·로그와 일치한다.
    - grip mean/p05와 strum 43개 방향·순서·완주 성능이 이전 best에서 퇴행하지 않는다.
  - 실제 결과: 코드·CPU 계약, 사용자 위임 승인, canonical 승격과 strict data audit까지 완료했다.
    기존 `20260828_2158_00_SS1-68-E_comp` run은 2026-08-30 19:16 KST에도 iteration 53,221로
    실행 중이지만 메모리에 로드된 구 goal/contract를 사용한다. 새 canonical의 GPU 재학습 결과는
    아직 없으며 다음 fresh run부터 적용된다. 구 canonical SHA와 파일은 promotion history로 재현한다.
  - 영상 판정: 방향 반전에서 피크가 줄 아래로 직선 복귀하지 않고 위로 이탈한 뒤 다음 entry 쪽으로
    이동하는지, 82→84 근접 전이와 보정된 35.28초 chord를 두 카메라에서 확인한다.
- 재발 방지 결정: 학습 정체를 PPO 문제로 판단하기 전에 source→raw→plan 정합성과 실제 traversal-edge
  가능성을 일반 audit workflow로 검사한다. `INFEASIBLE` goal은 tempo curriculum이나 hard mining으로
  우회하지 않으며, `AMBIGUOUS`/pending proposed artifact도 사람 승인 없이 학습 정본으로 승격하지 않는다.
- 다음 행동: GPU driver가 사용 가능한 환경에서 canonical 입력의 fresh A0 smoke와 학습을 실행한다.
  영상에서는 보정된 35.28초 down strum과 near-edge clearance를 확인한다.
- 상태: `검증 전` — 입력 승인·strict audit는 완료, GPU 학습 효과는 미검증

### STRIKE-018 — S2 양방향 마지막 줄·exit 완주와 독립 timing 전이

- 시기: 2026-08-31
- 분류: `CONTROL`, `REWARD`, `METRIC`, `CURRICULUM`, `EXPLORATION`,
  `POLICY_TRANSFER`, `VIDEO`
- 연결된 이전 실험: STRIKE-004, STRIKE-005, STRIKE-008, STRIKE-009, STRIKE-010,
  STRIKE-017
- 기준 run / checkpoint:
  - run: `strike/training/runs/20260830_1928_00_SS1-68-E_comp`
  - 정책 전이 기준: `checkpoints/strike_003147.pt`
  - source 상태: S2 진입 직후, `stage_iteration=0`, S2 evidence 0, 6줄 span
- 문제와 관측 사실:
  - S1의 down/up completion은 각각 약 `99.4%`였지만 S2 진입 뒤 up completion은 약
    `99.3%`, down completion은 `0.1%` 미만으로 갈라졌다.
  - down trace는 대부분 `5→4→3→2→1`까지 계획 순서로 통과한 뒤 마지막 high-e인 `0`번 줄을
    남겼다. up은 반대 방향 전체 traversal을 완주했다.
  - 성공한 S2 timing 표본은 목표보다 약 `194 ms` 빨랐지만, down에는 마지막 RELEASE 자체가 거의
    없어 timing 정렬 전에 물리 endpoint 획득이 병목이었다.
- 원인 판단:
  - 기존 APPROACH는 다음 줄의 entry를 향했고 exit는 physical completion 뒤에야 활성화됐다.
    중간 줄은 다음 목표로 이동하는 운동이 관성을 제공하지만 마지막 줄에는 그 너머의 downstream
    목표가 없어 경계 직전에서 멈출 수 있었다.
  - 전체 completion 평균과 조건부 recovery는 up 성공 또는 이미 물리 완료한 표본만 반영해 마지막
    down 줄 실패를 숨길 수 있었다. finger mapping이나 방향 planner보다 S2 endpoint/reward/gate
    계약의 구조 문제다.
- 아직 추론인 부분:
  - 새 exit target이 실제 GPU에서 down 완주를 up 수준까지 회복하는지는 장기 run 전에는 확정할 수
    없다. 구현·CPU 계약 통과는 학습 효과의 증거가 아니다.
  - 물리 완주 회복 뒤에도 약 `-194 ms` signed timing 편향은 별도 T0 이후 최적화가 필요할 수 있다.
- 개선 가설:
  - 마지막 줄만 남은 동안 final-string→exit를 직접 목표로 하고 최대 투영 증가분만 보상하면
    방향별 코드 분기 없이 경계 밖까지 이어지는 sweep을 학습할 수 있다.
  - 마지막 RELEASE physical-completion pulse를 timing 성공과 분리하면 물리 기술을 먼저 획득한 뒤
    기존 centered-timing profile을 좁힐 수 있다.
  - down/up raw count와 미완료 사건을 포함한 end-to-end recovery를 gate하면 한쪽 방향·조건부
    분모의 성공 착시를 막을 수 있다.
- 기존 시도와 다른 점:
  - timing 허용 오차나 승급 임계값만 낮추지 않는다. timing보다 앞선 물리 endpoint 목표와 증거를
    추가한다.
  - STRIKE-008에서 제거한 지연 clawback을 되살리지 않는다. terminal shaping은 최대 투영 증가분만
    지급해 cycle-safe이고, physical pulse는 one-shot이다.
  - 부족 방향을 더 학습하되 focus 표본으로 승급하지 않는다. 별도의 balanced holdout을 고정한다.
- 구현:
  - `env/strike_events.py`, `env/tasks/task_strike.py`, `env/rewards/strike.py`에 방향대칭
    final-string→exit 목표, monotone terminal progress, timing 독립 physical-completion pulse와
    끝줄/exit 진단을 추가했다.
  - `strike_metrics.py`, `learning/ppo.py`, `train_strike.py`에서 down/up completed/event,
    scheduled-recovery completed/event raw count를 먼저 합친 뒤 전체 completion, 최저 방향,
    conditional/end-to-end recovery rate를 한 번 계산한다.
  - `strike_cfg.py`, `learning/strike_curriculum.py`에 첫 S2 profile
    `E0_BALANCED_ENDPOINT`를 추가했다. E0은 completion `0.80`, worst-direction `0.75`,
    end-to-end recovery `0.75`를 요구하고 timing/zone 정밀 gate는 T0 이후로 미룬다.
  - 최저 방향 completion이 `0.60` 미만인 evidence가 3회 연속이면 그 방향을 70%로 focus한다.
    강제 focus가 아닌 60% 표본은 down/up 30/30 balanced holdout이며 승급은 holdout raw evidence만
    사용한다. holdout이 없으면 fail-closed 한다.
  - PPO는 E0/T0에서 첫 9개 어깨·팔꿈치·손목 action의 탐색 표준편차를 `0.03` 이상으로 유지한다.
  - `learning/checkpoint_contract.py`와 `train_strike.py`에 명시적 actor-only S2 objective transfer를
    추가했다. 같은 327D/30-action goal·grip·asset·profile·recovery interface의 S1 최종 또는
    S2 진입 직후만 actor, observation normalizer와 source `log_std`를 복사한다. critic·optimizer·
    iteration·curriculum·환경 상태/RNG는 초기화한다.
  - S0~S2 주기 영상은 같은 checkpoint에서 down/up을 각각 강제해 두 방향 × remembered/current
    카메라와 방향별 report를 저장하고 runtime/RNG 복원을 검증한다.
  - 설정·계약 변경: timing reward `physical_endpoint_then_centered_timing.v2`, strum motion
    `direction_symmetric_terminal_exit_progress.v1`, metric `raw_count_direction_and_recovery.v1`,
    curriculum `direction_conditional_endpoint_recovery.v13`; checkpoint schema `v13`, curriculum
    schema `v13`, environment state `v14`다.
  - checkpoint 호환성·재시작 위치: v12 상태의 exact resume은 불가하다. 기준 `strike_003147.pt`를
    `--initialize-stage S2_TIMED_STRUM --allow-policy-objective-transfer`로 새 run에 전이한다.
- 검증:
  - 회귀 검사 / GPU smoke:
    - down/up 공통 terminal projection, monotone/cycle-safe 증가, physical/timing pulse 분리,
      raw-count pooling, 최저 방향/e2e gate, 3-window focus와 balanced holdout, std floor,
      source-stage가 제한된 actor-only transfer, paired 영상 report/RNG 복원 검사를 추가했다.
    - 문서와 lazy runner semantic expectation은 checkpoint/curriculum/environment v13/v13/v14 및 새
      reward/motion/metric 계약을 고정한다.
    - runner-lazy, event, curriculum, reward, checkpoint, artifact, paired-video, runtime, PPO의 선택된
      CPU 회귀 스크립트 9개가 모두 통과했다.
    - 현재 호스트의 GPU 장기 학습과 새 영상 동작 검수는 아직 수행하지 않았다.
  - 학습 조건과 대조 run: `strike_003147.pt`의 actor를 새 E0 S2 run으로 전이하고, 구 S2의
    down/up/끝줄 miss와 같은 raw count·paired 영상으로 비교한다.
  - 사전 성공 기준:
    - E0 balanced holdout에서 down/up 양쪽 event가 존재하고 최저 방향 completion `>=0.75`, 전체
      completion `>=0.80`, conditional recovery `>=0.95`, end-to-end recovery `>=0.75`를 3회
      연속 통과한다.
    - down final-string miss와 remaining count가 감소하고 exit distance가 방향별로 함께 줄어든다.
    - traversal/order/direction, grip mean/p05, FP, reset/blocked와 safety가 이전 S1 기준에서
      붕괴하지 않는다.
    - E0 통과 전 timing 수치가 좋아졌다는 이유만으로 T0로 승급하지 않는다. T0 이후 signed timing
      mean/tail과 RMS/duration을 기존 기준으로 다시 검사한다.
  - 실제 결과: 코드와 회귀 계약은 구현됐고 GPU 재학습 효과는 검증 전이다.
  - 영상 판정: paired down 영상에서 피크가 `5→0`을 모두 지나 exit 쪽으로 계속 이동하는지,
    up 영상에서 반대 순서와 동일한 follow-through가 유지되는지 확인한다.
- 재발 방지 결정: strum 평균 성공률 하나로 양방향 획득을 주장하지 않는다. timing 조정 전에
  방향별 마지막 줄과 end-to-end recovery를 raw 분자·분모로 확인하며, focus 학습 표본을 승급
  evidence로 재사용하지 않는다.
- 다음 행동: 기준 actor-only S2 run을 시작해 E0 paired 영상과 raw down/up/끝줄 진단을 먼저 검수한
  뒤, E0를 실제 통과했을 때만 T0 timing 학습을 평가한다.
- 상태: `검증 전`

### STRIKE-019 — 짧은 구간 과적합과 원곡 tempo 망각 보완

- 시기: 2026-09-07
- 분류: `S3`, `CURRICULUM`, `FAILURE_MINING`, `REWARD`, `DIAGNOSTIC`
- 기준 run / checkpoint:
  - run: `strike/training/runs/20260907_0439_02_Jazz1-200-B_solo`
  - 정책 전이 기준: `checkpoints/strike_004000.pt`
  - 원인 분석 기준: `checkpoints/strike_009500.pt`
- 문제와 관측 사실:
  - 8-event 학습 구간의 uniform F1은 약 `0.962`에서 정체됐고, S3 최대 체류를 넘겨
    `stalled=true`가 됐다. 이는 프로세스 정지가 아니라 승급 실패 상태다.
  - 원곡 속도 deterministic 전체곡 F1은 iteration 4,000의 `0.8831`이 최고였고,
    iteration 8,000에는 `0.4324`로 하락했다. timing MAE와 평균 reward는 계속 좋아져
    짧은 구간 보상과 전체곡 성공이 정렬되지 않았다.
  - event failure score는 upstroke 12개 중 11개가 `0.05`를 넘었고, downstroke에서는
    event 23이 `0.831`로 독보적으로 높았다.
  - checkpoint 9,500의 실제 Isaac Gym 재생에서 쉬운 tempo의 event 23 단독은 F1 `1.0`이지만
    22→23은 event 23을 놓쳐 F1 `0.6667`이었다. 22→23→24에서는 22와 24를 성공해
    event 23의 고정 geometry보다 incoming recovery/transition이 병목임을 확인했다.
  - 원곡 tempo에서는 event 23 단독도 실패했다. 따라서 transition 획득과 tempo 일반화는
    서로 다른 두 문제다.
- 구현:
  - S3 episode 길이를 tempo 수준에 따라 `8→16→32→42`로 늘리고 이후에는 전체 42 events를
    유지한다. 긴 시간 credit assignment와 곡 후반 상태 분포를 단계적으로 노출한다.
  - 실패 증거가 생긴 즉시 노출 보정 hard-window 50%와 uniform window 50%를 자동 표본화한다.
    방향별 실패는 같은 score에 포함하며 별도의 upstroke fraction은 사용하지 않는다. hard 표본은
    PPO에는 사용하지만 uniform 승급 evidence에서는 제외한다.
  - 초기 tempo gate F1을 `0.96, 0.96, 0.97`로 두고 이후
    `0.975→0.98→0.985→0.987→0.99`로 강화한다.
  - S3 miss penalty를 `0.50→1.50`, timing-progress reward를 `1.50→0.75`로 바꿔
    몇 ms의 timing 개선보다 event 누락 방지를 우선한다.
  - `diagnose_strike_stall.py`와 event-window 물리 replay 옵션을 추가해 단일 event,
    incoming transition, incoming+outgoing transition을 tempo 0/1에서 같은 checkpoint로 비교한다.
  - reward/curriculum 의미가 바뀌므로 exact resume은 금지하고 actor·log_std·observation
    normalization만 4,000 checkpoint에서 전이한다. `--initialize-from` 자체를 이 전이의 명시적
    승인으로 사용하고 시작 tempo는 인자 없이 `0.0`이다. critic, optimizer, environment와
    curriculum은 초기화한다.
  - 콘솔의 짧은 episode 수치는 `window-F1`, deterministic 원곡 전체 수치는 `full-song-F1`로
    분리한다. 원곡 평가는 S3 시작 직후와 500 iteration마다 영상 없이 실행하며, 영상은 기존
    주기 설정을 유지한다.
- 검증:
  - Strike CPU 회귀 스크립트 전체가 통과했다.
  - 1,024 environments, 실제 GPU PhysX에서 actor-only 전이 후 PPO iteration 1회와 checkpoint
    생성을 통과했다. 검증 run은 `strike_stall_fix_validation_20260907`이다.
  - 장기 학습에서 16/32/42-event 단계의 전체곡 F1 회복 여부는 아직 검증 전이다.
- 사전 성공 기준:
  - 각 tempo 단계에서 uniform pooled gate를 통과하고 hard/upstroke 표본을 승급 증거로 섞지 않는다.
  - event 23 단독과 22→23→24가 tempo 0과 1에서 모두 완료된다.
  - 원곡 속도 전체곡 F1이 먼저 기존 최고 `0.8831`을 회복하고, 최종 `>=0.99`를 3개 evidence
    window 연속 만족한다.
  - grip, blocked/wrong crossing, timing tail이 기존 최고 checkpoint보다 퇴행하지 않는다.
- 다음 행동: 아래 actor-only 전이 명령으로 장기 run을 시작하고 3,000 iteration마다 전체곡 report와
  event 23 전이 진단을 함께 비교한다.
- 상태: `검증 전` — 코드·CPU·GPU 1 iteration 검증 완료, 장기 효과 미확정

```bash
python -m tab2body.train \
  --task strike \
  --song 02_Jazz1-200-B_solo \
  --initialize-from /home/ajou/yigyu/3/strike/training/runs/20260907_0439_02_Jazz1-200-B_solo/checkpoints/strike_004000.pt
```

## 다음 실험 등록 양식

```text
### STRIKE-NNN — 짧은 이름

- 시기:
- 분류:
- 연결된 이전 실험:
- 문제와 관측 사실:
- 기준 run / checkpoint:
- 원인 판단:
- 아직 추론인 부분:
- 개선 가설:
- 기존 시도와 다른 점:
- 구현:
  - 변경 파일·함수:
  - 설정·계약 변경:
  - checkpoint 호환성·재시작 위치:
- 검증:
  - 회귀 검사 / GPU smoke:
  - 학습 조건과 대조 run:
  - 사전 성공 기준:
  - 실제 결과:
  - 영상 판정:
- 재발 방지 결정:
- 다음 행동:
- 상태: 유지 / 폐기 / 보완 필요 / 검증 전
```

## 다음 반복의 기준선

다음 작업은 STRIKE-017에서 승격한 canonical plan과 327D 정책 interface를 유지하면서,
STRIKE-018의 기준 actor를 새 E0 S2 objective에 전이한 GPU smoke와 대조 학습이다.
STRIKE-013의 grip 보존, STRIKE-014의 recovery 분리,
STRIKE-016의 exposure-normalized failure-mining 기준은 그대로 유지한다. 고정 recovery gate나
원속도 feasibility 기준을 낮춰 성공 수치를 만드는 실험은 하지 않고
아래 순서로 판정한다.

```text
grip mean/p05와 pinch/free 품질이 모든 단계에서 유지되는가
  → 12 frame을 넘는 연속 grip 붕괴가 없는가
  → 물리 traversal 표본이 존재하는가
  → signed timing이 목표 방향으로 줄어드는가
  → timing gate 전 lane 품질도 개선되는가
  → completion·recovery event가 생기는가
  → scheduled/full/handoff recovery가 각각 gate를 통과하는가
  → 6줄 순서·방향을 유지하는가
  → E0에서 down/up 마지막 줄·exit와 end-to-end recovery를 balanced holdout으로 통과하는가
  → 400→250→225→200→175→150→100→zone 100→67→50 ms를 중심·성공 기반으로 통과하는가
  → S3 원곡 tempo에서 유지되는가
```

## STRIKE-020 — S3 원곡 속도 rehearsal과 retention gate

- 시기: 2026-09-10
- 번호 정정: 기존 STRIKE-019(2026-09-07)와 중복되어 2026-09-11에 STRIKE-020으로 정리했다.
- 연결된 문제: 낮은 tempo의 짧은 사건 window에서는 물리 지표가 좋아도 원곡 전체
  속도 평가가 뒤늦게 붕괴할 수 있었다. 기존 full-song 평가는 진단만 하고 학습 분포나
  승급 판단에 반영하지 않았다.
- 구현:
  - `learning/strike_curriculum.py`에 S3 stalled recovery와 원곡 holdout 상태를 추가했다.
  - S3가 마지막 tempo가 아닌 상태에서 최대 체류에 도달하면 마지막 원곡 tempo로 전환하고,
    song goal의 전체 이벤트 수를 episode quota로 사용한다. 이 구간은
    `s3_original_tempo_rehearsal_active`로 기록된다.
  - 주기적 원곡 full-song 평가의 F1, recall, false positive, end-to-end recovery,
    reset rate를 curriculum 상태에 저장하고, 최고 F1 대비 하락이 0.05를 넘으면
    `original_tempo_retention` gate를 실패시킨다.
  - 콘솔에는 rehearsal 활성과 retention warning을 별도로 표시한다.
  - curriculum schema는 v15, checkpoint semantic contract는
    `direction_conditional_endpoint_recovery.v14`로 올렸다. 기존 exact resume은
    의도적으로 거부되며 actor-only transfer 또는 새 A0 run을 사용한다.
- 검증:
  - Strike curriculum, runtime, runner, checkpoint 및 전체 `test_strike_*.py` 회귀 통과.
  - fake goal 123-event 환경에서 rehearsal이 실제 episode quota 123을 전달하는지 확인했다.
  - CUDA 장기 run에서의 원곡 retention 개선 효과는 아직 검증 전이다.
- 재발 방지 결정: 원곡 평가 수치를 단순 영상/보고서로 남기지 않고 다음 iteration의
  curriculum 상태·checkpoint·gate에 연결한다. 다만 reward 계수는 이번 단계에서 바꾸지
  않아 물리 completion을 timing 보상 변경으로 다시 흔드는 위험을 피한다.
- 정책 observation/action interface는 현재 설정을 그대로 유지했으며, 의미 변경으로
  기존 exact resume이 거부되는 semantic contract만 갱신했다.
- 상태: 구현 완료 / GPU 장기 검증 전

## STRIKE-021 — 완료 이후 품질 감시와 반복 평가 정합성

- 시기: 2026-09-11. 연결: STRIKE-018~020.
- 기준 run: `20260910_1916_02_Jazz1-200-B_solo`.
- 관측: 약 3,578 iteration에 완료, 이후 gate count 532 고정. single-only 곡인데 success=0.
  22,000 checkpoint 단일 영상 F1=1.0, 64회 평가 F1=0.9776. 원곡 rehearsal은 이 run에서
  한 번도 활성화되지 않아 STRIKE-020의 효과로 성공을 단정할 수 없다.
- 구현: 없는 strum 조건 제외, 완료 후 uniform gate 계속 검사, 과거 달성/현재 품질 분리,
  원곡 절대·상대 F1 및 연속 증거/유효기간, 고정 평가 사례·사건별 실패 기록, 반복 평가 기반
  best_evaluation과 불변 checkpoint 사본, best_video 분리 및 상대 경로, 원시 개수 합산 F1,
  중복 텍스트 로그 축소, 기존 진단 도구 확장·손상 로그 명시 오류.
- 계약: 303D/30D 및 보상 유지. curriculum state v16, 의미 계약
  `continuous_quality_fixed_evaluation.v15`, 지표 `pooled_outcomes_optional_strum.v2`.
  exact resume 비호환; 이전 run은 보존하고 검증된 actor-only 전이 또는 fresh run 사용.
- 재발 방지: `complete`를 현재 품질로 해석하지 않으며, 영상 한 번의 결과를 반복 성능과
  혼용하지 않는다. `quality_recovery_needed`는 진단이며 자동 policy rollback은 아니다.
- 검증: Strike 23개·공통 4개 테스트 스크립트 및 독립 검수 통과. 최종 보완된
  품질 보고·반복 평가·curriculum·runtime 테스트는 학습용 Python 3.8에서도 통과했다.
  수정 모듈 문법 검사와 기존 기준 run 진단 실행을 완료했다. NVIDIA 드라이버에
  연결되지 않아 GPU smoke는 수행하지 못했으며, 장기 학습 효과는 대조 실험 전에는 미확정이다.
- 상태: 구현·CPU 검증 완료 / GPU 검증 전.

## STRIKE-022 — 완료 후 학습 강도와 전체곡 일관성 진단

- 시기: 2026-09-12. 연결: STRIKE-016, 019, 021.
- 기준 run: `20260911_2235_02_Jazz1-200-B_solo`, checkpoint 9500 / 21000.
- 관측: 고정 64회 원곡 평가에서 F1 1.0 / 0.998323, 무오류 연주율 1.0 / 0.921875.
  21000 타이밍 p95는 4.84ms로 9500의 5.32ms보다 작다. handoff 콘솔 집계와
  사건별 miss 합계가 실제 원시 분자·분모와 다른 문제도 발견했다.
- 추론: 후기 정책 갱신이 일관성을 떨어뜨릴 가능성. 추가 seed 비교 전 인과는 확정하지 않는다.
- 구현 범위: full/handoff 원시 횟수 집계, 타이밍 거부와 물리 누락 구분,
  동일 조건 추가 seed 비교, 완료 후 선택적 학습률 감소, 무오류·하위 성능 진단,
  기존 hard-window 전환 노출 감사.
- 실험 변수: 완료 후 학습률 배율 1.0(대조) / 0.25(실험). 보상, update 횟수,
  허용 오차, 관측·제어, 자동 종료 정책은 바꾸지 않는다.
- 사전 성공 기준: 독립 추가 seed의 전체곡 무오류율·하위 F1 개선과 누락 감소,
  손 모양·안전·타이밍 유지. 고정 64회 최고값만으로 성공을 주장하지 않는다.
- 원인 확인: raw `miss`에는 물리 통과 후 타이밍/영역 거부가 포함된다. 기존 10개 raw miss와
  9개 FN은 집계 오류의 직접 증거가 아니며, 물리 신호를 분리해 의미를 명시했다.
- 구현 결과:
  - `strike_metrics.py`: full/handoff 원시 개수 pooling과 `_macro` 분리.
  - `task_strike.py`, `strike_repeat_evaluation.py`: 물리 hit/miss 신호와 관측 상태·개수 대조.
  - `train_strike.py`, `compare_strike_evaluations.py`: 추가 seed paired 평가, actor-only 명시적
    평가 전이, 기존 보고서 비교와 goal/runtime/tolerance 정합성 및 구형 보고서 한계 표시.
  - `ppo.py`: 완료 이후 기준 학습률에 지정 배율 적용. `--maintenance-lr-scale` 기본 1.0,
    실험 0.25. 실제 LR 기록, Fret 및 완료 전 학습에는 적용하지 않는다.
  - `strike_curriculum.py`, `strike_training_runtime.py`: 동일 protocol의 무오류율·하위 F1
    최고 대비 하락 진단과 상태 복원. 신규 강제 gate/자동 rollback 없음.
  - `diagnose_strike_stall.py`: 기존 4-event predecessor 표집의 전환 포함 확률 재구성.
    실측 전환 노출량은 아니며 표집 비중은 변경하지 않았다.
- 계약: observation303/action30 및 보상 유지. 의미 계약
  `continuous_quality_maintenance_diagnostics.v16`, 지표
  `pooled_recovery_physical_event_diagnostics.v3`. 저장 schema16은 선택적 진단 추가로 유지.
  구현/PPO 해시 변경으로 exact resume 비호환. 정책 전이는 기존 ABI 검증 후에만 허용한다.
- 검증: CPU 테스트 30개 및 독립 검수 통과. 주요 신규 테스트는 학습용 Python3.8에서도 통과.
  기존 9500/21000 보고서 CPU 비교와 checkpoint 기반 표집 감사 실행 완료.
  GPU driver 연결 불가로 추가 seed의 실제 PhysX 평가 및 새 학습 효과는 미검증이다.
- 재발 방지: highest F1 또는 몇 ms의 timing 향상만으로 무오류 연주 일관성을 주장하지 않는다.
  구형 보고서의 누락 정보를 추측하지 않고 비교 한계를 표시한다.
- 상태: 구현·CPU 검증 완료 / GPU 장기 효과 검증 전.
