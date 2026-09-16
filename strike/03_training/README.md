# 3. 현재 strike 학습·검증 계약

> **현재 기본 계약 — 2026-09-11:** `strike.observation.v2` 303D, action 30D,
> scalar reward/value, checkpoint container v14, curriculum state schema v16,
> environment state v14다.
> 아래 327D와 v10~v13 절은 실험 변화의 역사 기록이며 현재 checkpoint 계약으로 사용하지 않는다.
> v1 327D와 v2 303D actor는 서로 resume하거나 initialize하지 않는다.

## 2026-09-12 완료 후 유지 학습·독립 비교 (STRIKE-022)

- `--maintenance-lr-scale 0.25`: 커리큘럼 완료 **이후** actor/critic 기준 학습률을
  각각 1/4로 적용한다. 기본 1.0은 대조군이며 기존 학습 강도와 같다. 매 iteration
  기준값에서 계산하므로 재개해도 중첩 감소하지 않는다. `actor_learning_rate`,
  `critic_learning_rate`, `strike_maintenance_lr_multiplier`를 기록한다. Fret에는 적용하지 않는다.
- 원곡 속도·50ms 최종 허용 오차·보상·update 횟수·탐색량은 바꾸지 않는다.
  완료 기록을 초기화하는 actor-only 전이는 S3를 다시 통과한 뒤 배율이 적용된다.
- 동일 평가 protocol에서 무오류율과 하위 F1의 최고 대비 차이·연속 하락을 기록한다.
  `case-quality=below-best`는 기본 3회 연속 최고 미만인 경우의 **진단**이다.
  `quality=passed`와 동시에 나올 수 있고, 통계적 유의성·새 승급 gate·자동 rollback을 뜻하지 않는다.
- full/handoff는 원시 완료 합계/발생 합계로 계산한다. 해당 사건이 없는 경우 -1(N/A),
  기존 평균값은 `_macro`로 보존한다.
- 사건 `miss`는 타이밍/영역 조건 거부를 포함하므로 FN과 다르다. 새 physical hit/miss 신호와
  `event_reconciliation`으로 실제 TP/FN 및 wrong-crossing FP를 대조한다. 타현 TP/FN은
  줄별 음 개수가 아닌 **gesture** 단위다. 미관측 사건을 임의로 FN에 더하지 않는다.
- hard sampling은 기존 4-event predecessor 연습과 일반 표본을 유지한다.
  stall 진단의 `transition_sampling_audit`는 checkpoint 설정으로 재구성한 조건부 선택 확률이며,
  앞뒤 전환의 실측 노출 횟수나 성공 여부를 뜻하지 않는다.

### 두 checkpoint를 추가 seed로 비교

아래 작업은 원본 run을 수정하지 않고 새 폴더에서 평가만 수행한다. 결과는 seed별
`comparison.json` 및 원곡 사례별 보고서로 남기며 학습을 시작하지 않는다.

```bash
cd /home/ajou/yigyu/3
python -m tab2body.tools.compare_strike_evaluations \
  --reference-checkpoint /home/ajou/yigyu/3/strike/training/runs/20260911_2235_02_Jazz1-200-B_solo/evaluations/checkpoints/strike_009500_4667d6243b4901ef.pt \
  --candidate-checkpoint /home/ajou/yigyu/3/strike/training/runs/20260911_2235_02_Jazz1-200-B_solo/checkpoints/strike_021000.pt \
  --song 02_Jazz1-200-B_solo \
  --policy-transfer-evaluation \
  --seeds 1729 2718 3141 \
  --episodes 64 --num-envs 64 \
  --out /home/ajou/yigyu/3/docs/2026-09-12/strike_multiseed_comparison
```

`--policy-transfer-evaluation`은 변경된 코드에서 이전 actor와 관측 정규화만 검증·복사해
현재 환경에서 비교하겠다는 명시적 선택이다. 이전 실행 환경의 정확한 재현은 아니다.
원본 해시·현재 goal/계약·허용 오차를 기록한다. 생략하면 기존 strict checkpoint 검증을
유지하며 호환되지 않는 checkpoint는 거부한다. 추가 seed는 초기 조건 다양화이지 새 곡 평가가 아니다.
출력 디렉터리는 존재하지 않는 경로를 지정해야 한다.

GPU 없이 기존 두 보고서만 비교하려면 `--reference-report`, `--candidate-report`,
`--out`을 사용한다. goal/실행 계약 정보가 없는 옛 보고서는 완전한 조건 검증이 불가능하다고
명시하며, 확인 가능한 seed/사례 수/초기 조건이 다르면 비교를 거부한다.

의미 계약은 `continuous_quality_maintenance_diagnostics.v16`, 지표 계약은
`pooled_recovery_physical_event_diagnostics.v3`이다. curriculum 저장 형식은 선택적 진단 필드가
추가된 v16을 유지하지만 구현 해시·PPO 설정이 달라 기존 exact resume은 불가하다.
관측 303D/action 30D·보상·자산·goal은 유지한다. 장기 효과는 추가 평가와 대조 학습 전에는 미확정이다.

## 2026-09-11 성공 판정·품질 유지·고정 조건 평가 (이력)

단일 줄만 포함한 S3 episode에는 strum 조건을 적용하지 않는다. strum이 있는 episode는
기존 순서·방향·시간 조건을 유지한다. `complete`/`ever_mastered`는 과거 달성 기록이며
완료 뒤에도 uniform 표본의 gate를 계속 검사한다. `current_quality_passed`는 현재 상태,
`quality_recovery_needed`는 회복 필요 **진단**이다. 자동 중단·강제 정책 되돌리기는 하지 않는다.

원곡 평가는 고정 seed 1729와 고정 환경 ID의 첫 episode를 각각 수집한다. 빨리 끝난
실패나 반복 episode가 다른 사례를 대체하지 않는다. 동일 환경 수·계약의 평가끼리 비교하며,
GPU 물리 시뮬레이션의 비트 단위 재현성까지 보장하는 것은 아니다. 각 사례의 초기 조건,
F1·원시 TP/FP/FN·실패 사유, 사건별 방향·줄·관측 여부·성공·miss·오타현을 report에 남긴다.

원곡 품질은 최종 절대 F1 기준과 최고 대비 하락 기준을 함께 검사한다. 기본 3회 연속 평가로
판정을 확정하고, 1,500 iteration보다 오래된 평가는 stale로 표시한다. 누락·오래됨·누적 중은
성공으로 간주하지 않는다. 원속도 최종 curriculum 완료도 신선한 통과 평가를 요구한다.

- `evaluations/best_evaluation.json`: 반복 평가의 안전·손 모양·무오류 연주율·하위 F1 등으로
  선정한다. 선정 당시 checkpoint를 `evaluations/checkpoints/`에 따로 보존한다.
- `evaluations/best_video.json`: 한 번의 영상 결과로 선정한다. 기존 `best_full_song.json`은
  호환용으로 유지한다. 새 포인터는 run 내부 상대 경로와 해시를 기록한다.
- `metrics.jsonl`: 상세 지표 정본. F1·recall·FP는 원시 개수 합산 기준이고 이전 비율 평균은
  `_macro`로 분리한다. `training.log`는 간결한 진행·품질·실패 원인만 기록한다.

`diagnose_strike_stall.py`는 반복 평가와 영상 평가를 구분하고 완료 후 퇴행·고정 사례별 사건
실패를 분석한다. 손상된 로그 행은 위치를 알려주며, 무시하고 진행하지 않는다. 특정 곡의
고정 event 23 대신 checkpoint에서 가장 높은 실패 점수의 사건을 기본 진단 대상으로 고른다.

```bash
python -m tab2body.tools.diagnose_strike_stall \
  --run /absolute/path/to/strike/run \
  --output /absolute/path/to/diagnosis.json
```

새 의미 계약은 `continuous_quality_fixed_evaluation.v15`, 지표 계약은
`pooled_outcomes_optional_strum.v2`다. 이전 checkpoint의 exact resume은 거부한다.
정책 입출력과 자산·goal이 동일한 actor-only 전이 또는 새 run을 사용한다. CPU 검증과
장기 GPU 효과는 별개이며 실험 STRIKE-021에 결과를 기록한다.

## 2026-09-07 Jazz1 S3 정체 보완 (이력)

현재 S3는 8-event 구간을 계속 반복하지 않고 tempo와 함께 `8→16→32→42 events`로 늘린다.
실패 증거가 생기면 실패율 상위 연속 구간 50%와 uniform 구간 50%를 자동으로 사용하되, 승급 판단은
uniform 표본만 사용한다. 방향별 실패도 같은 실패율에 포함하므로 별도 fraction 인자는 필요 없다.
초기 F1 gate는 `0.96/0.96/0.97`이며 원곡 속도에서 `0.99`까지
점진적으로 강화된다. S3 miss penalty는 1.50, timing-progress reward는 0.75로 설정해 timing 수 ms
개선보다 event recall을 우선한다.

기준 run의 원곡 전체 F1은 iteration 4,000에서 `0.8831`로 최고였고 8,000에서 `0.4324`로
하락했다. event 23 물리 replay는 쉬운 tempo에서 단독 성공·22→23 전이 실패, 원곡 tempo에서
단독 실패를 보여 transition과 tempo를 별도 병목으로 확정했다. 상세 근거와 재학습 명령은
`EXPERIMENT_HISTORY.md`의 STRIKE-019를 따른다.

`--initialize-from`은 그 자체로 actor-only 전이를 명시하므로 별도의
`--allow-policy-objective-transfer`가 필요 없다. 시작 tempo는 자동으로 `0.0`이다. 콘솔의 매 iteration
값은 `window-F1`, 시작 직후와 500 iteration마다 수행하는 deterministic 원곡 평가는
`full-song-F1`로 구분해 출력한다.

S3가 낮은 tempo에서 최대 체류에 도달하면 같은 짧은 사건 분포를 무한히 반복하지 않는다.
새 계약에서는 마지막 원곡 tempo로 전환하고, `s3_original_tempo_rehearsal_active`가 켜진 동안
실제 goal의 전체 이벤트 수를 episode quota로 사용한다. 주기적 원곡 평가의 F1·recall·FP·
end-to-end recovery·reset은 curriculum holdout으로 저장되며 최고 F1 대비 0.05보다 큰 하락은
`original_tempo_retention` gate failure로 기록된다. 이 전환은 자동 종료가 아니며 요청한 iteration까지
계속 학습한다. curriculum schema는 v15이고 semantic checkpoint contract는
`direction_conditional_endpoint_recovery.v14`이다. 구 checkpoint는 exact resume 대신 새 계약에
맞는 actor-only transfer 또는 fresh run을 사용한다.

> 최종 갱신: 2026-08-31. 2026-07-27 실행 기록은 historical reference이며 현재 소스와 checkpoint
> 계약이 다를 수 있다. 배관 검증은 현재 코드에서 `--smoke`로 다시 실행한다.

학습 결과를 분석해 코드를 바꾸기 전에는
[`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md)의 중복 방지 표와 연결된 실험을 먼저 확인한다.
구현 직후에는 장기 효과를 확정하지 않고 `검증 전`으로 기록하며, 재학습 결과를 같은 실험 항목에
추가한다. Fret과 공유하는 작성 절차는
[`TRAINING_IMPROVEMENT_PROCESS.md`](../../docs/TRAINING_IMPROVEMENT_PROCESS.md)를 따른다.

## 2026-08-31 S2 양방향 끝줄·exit 완주 계약 v13

`20260830_1928_00_SS1-68-E_comp`는 S1에서 down/up이 모두 약 `99.4%`였지만 S2 진입 뒤
up completion은 약 `99.3%`, down completion은 `0.1%` 미만으로 갈라졌다. down trace는 대부분
`5→4→3→2→1`까지 통과하고 마지막 `0`번 줄을 남겼다. 전체 평균이나 up 성능만으로는 이 병목이
숨으며, S2의 timing 허용 오차를 넓히거나 gate를 낮춰도 마지막 줄을 지나가게 하는 물리 목표가
생기지 않는다.

현재 S2는 다음 순서로 물리 완주와 timing을 분리한다.

1. 마지막 줄 하나만 남으면 `APPROACH` 목표를 방향별 final-string→exit 선분의 exit로 바꾼다.
2. 선분 투영의 지금까지 최대값 증가분만 bounded terminal-progress 보상으로 지급한다. down/up은
   같은 수식을 쓰며 후퇴·왕복은 보상을 다시 만들지 못한다.
3. 마지막 올바른 RELEASE 직후 timing gate와 독립된 physical-completion pulse를 one-shot으로
   지급한다. 시간창 밖 완주도 물리 획득 증거에는 남고 timing 성공으로는 세지 않는다.
4. 새 첫 profile `E0_BALANCED_ENDPOINT`에서 양방향 완주를 회복한 뒤 `T0_400MS`로 이동해 기존
   중심 timing 커리큘럼을 시작한다. 지연 clawback은 다시 사용하지 않는다.

승급은 완료 episode 비율을 평균하지 않는다. down/up completed/event raw count를 각각 합친 뒤
둘 중 낮은 `strike_worst_direction_completion_rate`를 검사한다. recovery도 물리 완료 뒤만 보는
conditional completion과, 미완료 사건까지 분모에 남기는 end-to-end completion을 동시에 gate한다.
E0 기준은 completion `≥0.80`, 최저 방향 `≥0.75`, end-to-end recovery `≥0.75`이며 기존 grip,
ready, recall, FP, conditional recovery, reset/blocked, traversal/order/direction gate도 보존한다.
E0에서는 timing mean/tail/RMS/duration/zone을 승급 조건으로 사용하지 않는다.

최저 방향 완주율이 `0.60` 미만인 evidence가 3회 연속이면 endpoint recovery가 켜진다. 부족한 방향을
전체 표본의 `70%`, 반대 방향을 `30%`로 연습하되, 강제로 바꾸지 않은 `60%` 표본은 down/up
`30/30` balanced holdout으로 남긴다. focus 표본은 PPO 학습에는 들어가지만 승급 evidence에서
제외하고 holdout raw count만 사용한다. E0와 T0 동안 정책 탐색이 너무 일찍 수축하지 않도록
어깨·팔꿈치·손목 첫 9개 action의 표준편차를 최소 `0.03`으로 clamp한다.

현재 checkpoint semantic contract는 `v14`, curriculum state schema는 `v15`, environment state는 `v14`다. 구 상태의
`--checkpoint` exact resume은 허용하지 않는다. 동일한 327D 관측·30 action·goal/grip/asset과
direction/transition/recovery interface를 가진 S1 최종 또는 S2 진입 직후 checkpoint만, 사용자가
objective 변경을 명시적으로 승인할 때 actor·observation normalizer·source `log_std`를 새 S2 run으로
전이할 수 있다. critic·optimizer·iteration·curriculum·환경 RNG는 초기화한다. 기준 소스는
`20260830_1928_00_SS1-68-E_comp/checkpoints/strike_003147.pt`이며 이 checkpoint는 S2
`stage_iteration=0`, evidence 0이다.

```bash
python train.py \
  --task strike \
  --song 00_SS1-68-E_comp \
  --initialize-from /home/ajou/yigyu/3/strike/training/runs/20260830_1928_00_SS1-68-E_comp/checkpoints/strike_003147.pt \
  --initialize-stage S2_TIMED_STRUM \
  --allow-policy-objective-transfer \
  --iterations 50000 \
  --num-envs 1024
```

이 명령은 resume이 아니라 새 run이다. source가 late S2, stalled, 6줄 미학습, S1 미통과이거나 정책
interface가 다르면 fail-closed 한다. S0~S2의 주기 영상은 같은 checkpoint에서 down/up을 각각
강제해 `down|up × remembered|current` 네 MP4와 방향별 report를 저장하며, capture 전후 runtime과
task RNG를 복원한다.

## 2026-08-30 입력 품질·path-aware clearance 계약 v12 (기반 계약)

full-song 학습은 이제 사건 중심 간격이 아니라 이전 traversal의 마지막 줄 offset부터 다음
traversal의 첫 줄 offset까지 남은 시간을 검사한다. 원속도에서 detector/follow-through 최소 간격을
만족하지 못하면 GPU 환경을 만들기 전에 중단한다. `audit_strike_goal_quality.py`는 전체 bundle의
fingering/raw/JAMS 정합성, 묶음 경계, 실제 edge gap과 방향 반전 재통과를
`PASS/AMBIGUOUS/INFEASIBLE`로 분류한다.

현재 compiler profile은 direction `phrase_dp_microtiming_v3`, transition
`entry_side_edge_gap_v2`다. v3 방향 planner는 phrase 전체의 microtiming과 다음 recovery 경로 비용을
함께 보고 down/up을 고정하며, v2 transition은 exit-side→entry-side 직접 경로가 가로지르는 줄과
clearance/re-arm 필요 여부를 plan에 봉인한다.

```bash
python tab2body/tools/audit_strike_goal_quality.py \
  --all --format human --strict
```

일반 입력 감사 절차는 다음과 같다.

1. canonical bundle을 읽기 전용으로 감사한다. `PASS`는 통과, `AMBIGUOUS`는 사람 검수 대기,
   `INFEASIBLE`은 full-song 학습 금지다.
2. 문제가 source timing/grouping이면 canonical을 직접 수정하지 않는다. source event ID,
   `merge|separate`, 이유와 evidence가 있는 review JSON으로 `*.proposed.json` 후보를 만든다.
3. 오디오를 사람이 판정한다. 승인 전 후보 상태는 `proposed_pending_audio_review`이며 reviewed 정본이나
   학습 입력이 아니다.
4. 승인된 후보만 canonical로 원자 교체하고 strict audit와 original-tempo preflight를 다시 수행한다.
   `INFEASIBLE=0`을 확인한 뒤 fresh 학습을 시작한다.

다른 줄 handoff도 exit-side→next-entry-side 경로가 방금 친 줄을 가로지르면 re-arm을 생략하지 않는다.
정책은 `release lift → elevated transfer → approach`를 수행해야 한다. 관측에는 이전 recovery 방향,
현재 음악 방향, clearance required/reached 6개가 추가돼 전체 observation은 기존 321에서 327로
변경됐다. 첫 lift waypoint에서 elevated-transfer waypoint로 목표가 바뀔 때 reach potential baseline을
초기화해 올바른 lift가 목표 전환 때문에 음의 shaping을 받지 않게 한다. wrong/blocked 이력이 생긴
event에는 timing·strum microtiming bonus를 지급하지 않는다.

따라서 321D였던 v11 이하 checkpoint는 일반 resume뿐 아니라 `--initialize-from` actor 전이도
입력층 크기가 달라 사용할 수 없다. path-aware v12의 327D checkpoint도 exact resume은 불가하며,
현재 허용되는 예외는 위에서 정의한 S1 최종/S2 진입 직후의 명시적 S2 actor-only 전이뿐이다.
그 외에는 fresh A0부터 학습한다. 2026-08-30에 사용자가 판정을 위임해 source
event 147~149를 하나의 down strum으로 병합한 후보를 `approved_user_delegated` 상태로 canonical에
승격했다. 수동 오디오 청취는 수행하지 않았고 source JAMS·symbolic chord·기존 `46.5 ms < 50 ms`
불가능 경계를 근거로 승인했다. 현재 canonical은 raw v3, plan v4, direction
`phrase_dp_microtiming_v3`, transition `entry_side_edge_gap_v2`이며 104 events(61 single/43 strum),
최소 edge gap `51.0 ms`, `INFEASIBLE=0`이다. strict 전체 감사는 exit 0,
`PASS 2 / AMBIGUOUS 6 / INFEASIBLE 0`이다. 이 곡 자체는 남은 source/grouping 경고 때문에
`AMBIGUOUS`지만 full-song preflight는 통과하며 fresh 학습 입력으로 사용할 수 있다. 승격 이력은
`data/song_bundles/00_SS1-68-E_comp/training/history/20260830_user_delegated_strum_merge/`에 보존한다.
이미 실행 중인 `20260828_2158_00_SS1-68-E_comp`는 메모리에 로드된 구 goal/contract로 계속 동작하며
새 canonical은 다음 fresh run부터 적용된다. 구 입력의 SHA와 파일은 위 history로 재현할 수 있다.

아래 v12 이하 절과 `--initialize-from` 명령은 당시 계약의 이력이다. 현재 실행에는 위의 제한된
S2 objective-transfer 명령 또는 fresh 학습 명령만 사용한다.

## 2026-08-28 S3 노출 보정 실패 표집·전체곡 퇴행 방지 v12 (이력)

S3가 `stalled`에 들어가면 event별 raw 실패 횟수가 아니라 실패 mass와 노출
mass의 EMA로 계산한 노출 보정 실패율로 hard window를 고른다. 전역 실패율에
prior exposure `16`을 적용하고 EMA decay는 `0.995`다. episode 시작의 `15%`만 hard
window에서 뽑고, 하나의 window가 갖는 표집 확률은 최대 `10%`로 제한한다.
실패 score가 없으면 균일 표집으로 돌아간다.

hard episode도 PPO update에는 포함해 어려운 구간을 학습한다. 다만 S3 stalled
승급 gate는 곡 전체에서 균일하게 뽑힌 episode의 pooled TP/FP/FN·blocked·recovery
evidence만 사용한다. 로그의 `uniform_evidence_episodes`,
`hard_evidence_excluded_episodes`, `uniform_evidence_fraction`으로 학습 표본과 승급
표본이 분리됐는지 확인한다.

주기 영상과 deterministic 전체곡 평가 중에는 failure-mining 갱신을 끄고 기존
mass/exposure/score 상태를 복원한다. 따라서 평가 실패가 훈련 표집 분포를
바꾸지 않는다. 전체곡 report는 안전·grip·F1·event/strum completion·blocked·wrong·
timing 순으로 비교하며 현재 run의 최고 결과를 `evaluations/best_full_song.json`에
기록한다. 현재 전체곡 F1이 최고 기준보다 `0.01`을 초과해 떨어지면
퇴행 경고를 남긴다. S3 reward-alignment 감시도 uniform evidence를 기준으로
reward 상승과 F1·blocked·wrong 악화가 같이 나타나는지 본다.

JSONL append는 pending journal을 먼저 내구화한 뒤 정확한 offset에 record를 쓴다.
강제 종료 뒤에도 저널로 검증되는 불완전한 마지막 record만 복구하고, 중간 손상·
교체된 대상·검증할 수 없는 tail은 더 쓰지 않고 멈춘다.

curriculum schema는 `v12`, environment state는 `v13`, semantic contract는
`exposure_normalized_failure_mining.v12`다. 구 checkpoint의 일반 `--checkpoint` resume은
허용하지 않는다. 동일한 정책 입출력의 actor는 `--initialize-from`으로만 가져오며
critic·optimizer·iteration·curriculum evidence는 새로 시작한다. STRIKE-016의 첫 비교는
iteration 8,500 actor를 tempo `0.95`에서 전이하고 `0.975`를 짧은 대조로 비교한다.

```bash
python train.py \
  --task strike \
  --song 00_SS1-68-E_comp \
  --initialize-from /path/to/strike_008500.pt \
  --initialize-tempo 0.95 \
  --iterations 50000 \
  --num-envs 1024
```

## 2026-08-28 S3 tempo gate와 실패 구간 재학습 v11 (이력)

S3는 모든 속도에 `failure=0` 하나를 적용하지 않는다. non-finite·비정상 관통 같은 안전 실패는
항상 0이어야 하지만, 음악적 wrong-crossing 종료와 blocked/rearm 품질은 tempo마다 별도 gate를
사용한다. `0.75`에서는 `(F1≥0.975, wrong 종료≤0.08, blocked≤0.025)`를 적용하고 속도를 올릴수록
엄격하게 줄여 원곡 속도에서는 `(F1≥0.99, wrong 종료≤0.01, blocked≤0.01)`을 요구한다.
오타현 비율은 해결된 event에서만 평가하며 진단으로 남긴다. 즉시 종료는 누적 4회 또는 연속
3-event 오류에만 사용한다.

승급 evidence는 episode F1 평균의 평균이 아니다. 완료 episode의 TP/FP/FN와 blocked/recovery
raw count를 모두 합친 뒤 F1과 rate를 한 번 계산한다. S3가 최대 체류를 넘기면 이전부터 누적한
event failure score를 이용해 episode의 30%를 어려운 연속 구간에서, 70%를 곡 전체에서 균일하게
시작했다. 이 raw-count 30% 표집은 STRIKE-015 실행에서 특정 window 자기강화와
전체곡 성능 퇴행을 발생시켜 현재 v12의 노출 보정 15% 표집으로 대체됐다.

한 run에는 한 trainer만 쓸 수 있다. metrics/training/periodic-video JSONL은 record lock으로 한 줄씩
저장하고 resume 전에 전체 파일을 검증한다. 원곡 전체 report v2에는 계획 event별 실제 crossing,
accepted/blocked, miss, wrong count와 timing을 저장한다.

기존 checkpoint는 일반 resume하지 않는다. 동일한 정책 인터페이스의 actor를 가져올 때는 critic,
optimizer와 curriculum을 초기화하고 기본 tempo `0.5`에서 시작한다.

```bash
python train.py \
  --task strike \
  --song 00_SS1-68-E_comp \
  --initialize-from /path/to/strike_026000.pt \
  --initialize-tempo 0.5 \
  --iterations 50000 \
  --num-envs 1024
```

## 2026-08-27 S3 dual recovery v10 (이력)

A0~S2의 운동 기술과 S3의 마지막 사건은 기존처럼 `12 frame + detector 재무장`의 full recovery를
사용한다. S3에서 다음 사건의 접근 시작까지 12 frame을 확보할 수 없을 때만 handoff recovery를
사용한다. 필요한 길이는 `floor((다음 목표 시각 - 현재 RELEASE 시각 - approach lead) × 60)`으로
계산하고 `1~12 frame`으로 제한한다. 서로 다른 줄로 이어지는 handoff는 직전 줄의 재무장을 기다리지
않지만 같은 줄 재타현은 반드시 재무장을 기다린다. 따라서 짧은 간격을 수행하기 위해 매번 중립
자세로 돌아가지는 않으면서, 같은 줄 중복 RELEASE 방지는 유지한다.

보상과 S3 승급은 실제 스케줄에 맞는 `strike_scheduled_recovery_completion_rate`를 사용한다.
full/handoff의 event 수와 completion을 별도로 gate하며, 기존 고정 12-frame
`strike_recovery_completion_rate`는 회귀 진단으로 남긴다. 마지막 사건은 항상 full recovery이므로
전체곡 완료 의미는 바뀌지 않는다. curriculum/environment/checkpoint/evaluation 계약은
`v10/v11/v12/v8`이다.

기존 v11 checkpoint는 그대로 resume하지 않는다. 같은 곡·관측·제어·asset 계약을 가진 정책은
actor, 탐색 분산과 관측 정규화만 가져오고 critic·optimizer·iteration을 초기화해 S3 tempo 0에서
새 run으로 시작할 수 있다.

```bash
python train.py \
  --task strike \
  --song 00_SS1-68-E_comp \
  --initialize-from /path/to/strike_027500.pt \
  --iterations 50000 \
  --num-envs 1024
```

## 2026-08-26 지속형 pick-grip 제어 v9

피크를 쥔 손 모양은 A0에서만 학습하고 버리는 준비 기술이 아니라 모든 strike 단계의 제어 계약이다.
정책의 30차원 action과 오른손 21관절 제어는 유지하지만, 손가락 action은 기준 자세에 대한 residual로
해석한다. 엄지·검지 9관절은 기준에서 `±0.08 rad`, 중지·약지·소지 12관절은 `±0.22 rad`만
움직일 수 있다. 어깨·팔꿈치·손목은 기존 범위를 유지한다. 따라서 피크 끝의 큰 이동은 손을 풀어서
만들지 않고 오른팔과 손목 궤적으로 학습해야 한다.

A1~S3의 grip 보상 가중치는 기존 `0.003~0.005`에서 `0.02`, A1은 `0.10`으로 올렸다. 승급은 기존
binary grip success `≥0.90` 외에도 모든 단계에서 아래 조건을 동시에 요구한다.

- 전체 frame grip quality 평균 `≥0.92`, 하위 5% `≥0.85`
- 엄지·검지 평균 quality `≥0.95`, 자유 손가락 평균 quality `≥0.85`
- quality `<0.85`인 frame 비율 `≤0.05`
- 낮은 quality가 연속되는 구간 `≤12 frame`

로그와 최종 평가에는 평균·하위 5%·최솟값, 두 관절군 quality, bad-frame 비율과 최대 연속 길이가
저장된다. S3 원곡 전체 영상 report에도 `grip_preservation` 요약과 통과 여부를 저장해 곡 후반의
자세 붕괴를 마지막 frame 하나로 판단하지 않는다. 이 임계값은 구조적으로 적용됐지만 장기 run의
학습 가능성과 영상 자연스러움은 아직 검증 전이다.

action 의미와 curriculum/environment/checkpoint/evaluation 계약은 각각
residual-grip/v9/v10/v11/v7로 바뀌었다. 기존 checkpoint의 resume과 policy initialization은
허용하지 않으며 A0 fresh run으로 다시 시작한다.

## 2026-08-25 목표 시각 중심 접근 제어 v8

공개 stage는 `S2_TIMED_STRUM`으로 유지한다. 이때 도입한 내부 timing profile은
`T0 400→T1 250→T2 225→T3 200→T4 175→T5 150→T6 100→Z0 100→Z1 67→Z2 50 ms`
순서였고, 현재 계약은 이 앞에 `E0_BALANCED_ENDPOINT`를 추가한다. 각 timing profile의 completion,
timing pass, RMS, duration과 보존 gate에 더해 signed timing
mean과 p10/p90 꼬리가 목표 시점 중심으로 모여야 다음 profile로 간다. profile 전환 뒤 200 iteration은
적응 기간으로 보장하며 이 기간에는 rollback하지 않는다. 이후 심한 붕괴가 3회 연속이면 한 단계
후퇴하고 200 iteration 동안 재승급하지 않는다. iteration 수만으로 tolerance를 줄이지 않는다.

T0에서는 첫 줄 목표 `250 ms` 전부터 접근하되 T1부터
`140→130→120→110→100→90→90→80→70 ms`로 접근 시작을 목표 쪽으로 옮긴다. A3는
기본 `250 ms` lead를 사용한다. 모든 timed stage의 첫 event는 profile의 접근 시작 시각 전까지
READY를 유지하고, 그동안 준비 자세 품질에 작은 wait 보상을 받는다. 접근 시각이 되면 강제로
APPROACH가 열리므로 wait 보상을 위해 무기한 멈출 수는 없다. 일부 줄이 현재 허용창보다 일찍 RELEASE되어도
부분 strum을 즉시 끝내지 않고 전체 sweep을 완주할 기회를 준다. 완료된 sweep이 허용창 밖이면
그 step에서 timing miss를 확정한다. 부분 진행의 지연 clawback은 제거했고,
timing 품질을 포함한 gamma-correct potential shaping을 사용한다. timing/duration 품질은 profile별
rational core를 사용해 큰 초기 오차에서도 0이 되지 않는다. S2 timing-progress 가중치는 `2.0`이며
profile별 grace보다 이른 RELEASE에는 즉시 bounded early-center penalty를 적용한다. 따라서 넓은
허용창 안의 조기 타현도 timing pass와 별개로 목표 중심보다 낮은 return을 받는다. Z0 전에는 lane을 soft 보상·raw
진단으로만 사용하고 hard zone gate는 적용하지 않는다.

물리적으로 올바른 줄을 완주했는지와 정해진 시간 안에 완주했는지는 독립적으로 집계한다. early/late
sweep도 physical completion·release recall·recovery에는 성공으로 남고 timing pass에서만 실패한다.
모든 완료 traversal은 timing 표본에 포함되므로 실패 표본이 통계에서 빠지지 않는다.

로그에는 signed timing 분포, timing pass/early/late/premature, 접근 open/lead/남은 시간,
wait 품질, early-center cost, hard gate 전 raw zone, timing/wait/progress/penalty return,
profile/rollback과 `reward_alignment_warning`을 저장한다. reward가 평평해도 signed mean 절댓값이
악화되면 정렬 경고가 켜진다. 당시 상세 설계 파일은 현재 저장소에 없으며, 구현 상태와
재시도 결정은 [`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md)의 STRIKE-011에 보존한다.
curriculum/environment/checkpoint/evaluation 계약은 v8/v9/v10/v6이며 기존 checkpoint의 resume과
policy initialization은
허용하지 않는다.

## 2026-08-24 A4 clean-recovery 전이와 실제 S0 2줄 계약 v5

기존 S0은 첫 줄 타현보다 타현 뒤 고속 왕복, duplicate, detector 재무장 전 crossing이 병목이었다.
이를 해결하기 위해 A3와 S0 사이에 실제 strum 문맥의 입구 한 줄과 깨끗한 회복만 학습하는
`A4_STRUM_CONTEXT_RECOVERY`를 추가했다. S0은 더 이상 내부 1줄 수준을 갖지 않고 처음부터 실제 2줄
연속 traversal을 요구한다.

목표 RELEASE 뒤 추가 물리 RELEASE나 재무장 전 crossing이 생기면 12-frame recovery count를 0으로
되돌린다. recovery 진행·완료 보상은 최대 진척 기준 one-shot이고, 회복 중 0.20 m/s를 넘는 tip 속도에는
bounded penalty를 적용한다. `blocked_wait_rearm`은 FP와 wrong penalty에도 포함된다.

로그·승급·평가에는 recovery completion/reset 및 blocked crossing rate를 독립적으로 기록한다.
승급 실패 원인은 `curriculum_last_gate_failures`에 직접 남는다. 최종 평가는 clean recovery 100%,
reset 0, blocked crossing 0을 요구한다. 당시 별도 재설계 파일은 현재 저장소에 없고,
근거는 [`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md)에 보존한다. 이전 checkpoint와
호환되지 않으므로 A0부터 다시 학습한다.

## 2026-08-20 양방향 연습·strum 미세 타이밍 v4 (이력)

- A0~A4 single→strum-context와 S0~S2 strum 연습은 원곡의 방향 빈도와 분리해 down/up을 환경별로 정확히
  절반씩 생성한다. 반대 방향에서는 시작 줄, traversal 순서와 줄별 목표 offset도 함께 반전한다.
  S3만 `strike_plan.v4`에 고정된 원곡 방향을 그대로 수행한다.
- 당시 S2/S3는 실패 시 진행도를 나중에 회수했지만, 이 지연 clawback은 STRIKE-008에서
  terminal potential shaping으로 교체됐다.
- 완료된 strum마다 줄별 timing RMS와 계획 대비 sweep-duration 절대 오차를 저장한다. curriculum
  gate는 각각 `≤35 ms`, `≤30 ms`, 최종 평가는 `≤25 ms`, `≤20 ms`를 요구한다.
- down/up별 event count와 completion rate를 분리 저장하고 학습 plot과 `ANALYSIS.md`에 표시한다.
- S3 원곡 복원은 `0→0.25→0.5→0.75→0.9→0.95→0.975→1`로 진행해 마지막 간격 축소를
  완만하게 만든다.
- 어깨·팔꿈치·손목 9개 action에는 threshold `0.90`, weight `0.002`의 약한 saturation
  regularization을 적용한다. 속도·가속도·jerk는 사람 기준 분포가 생길 때까지 진단으로 유지한다.
- `protected crossing`이라는 모호한 matcher 이름은 traversal 밖의 통과를 뜻하는
  `unplanned crossing`으로 정정했다. traversal 안의 비발음 `protected_strings`와는 다른 개념이다.

관측 의미, 보상, curriculum/environment state와 checkpoint 계약이 바뀌었으므로 v4 이전 Strike
checkpoint는 사용하지 않고 A0부터 새로 학습한다.

## 2026-08-19 실행 흐름·runner 정리

`train.py --task strike`부터 goal compile, Isaac Gym 환경, PPO iteration, checkpoint·평가, sim 종료,
자동 분석·진단·두 영상까지의 모듈 흐름과 strum-v2 변경을
[`tab2body/TRAINING.md`](../../tab2body/TRAINING.md)와
[`tab2body/STRUCTURE.md`](../../tab2body/STRUCTURE.md)에 정리했다. 환경 종료 뒤 학습 CUDA 객체를
해제하고 자동 산출물을 실행한다.

## 2026-08-19 strum bridge v3

strum은 single pick과 동일한 `준비→통과→회복` 구조를 사용하되 통과 구간 안에 여러 줄의
연속 하위 목표를 가진다. 이전 구현은 첫 줄을 통과한 뒤에도 approach 위치 보상이 첫 줄의
entry를 향하고, 전체 traversal을 끝내기 전에는 양의 crossing 보상이 없어서 이전 A4에서
single F1만 높고 strum 완료율은 0에 머물렀다.

현재 구현은 다음 계약을 사용한다.

- 첫 줄을 통과하면 approach 목표를 즉시 `next_traversal_string`으로 옮긴다. 마지막 줄 하나만 남으면
  final-string→exit의 exit를 직접 향해 마지막 RELEASE를 유도하고, 그 뒤에만 recovery로 전환한다.
- 올바른 순서·방향의 새 줄은 ordered progress를 늘리지만 실제 보상은 현재 timing 품질을 포함한
  gamma-correct potential 차분이다. 중복 RELEASE와 ready 이전 통과에는 진행 보상을 지급하지 않는다.
- S0의 접근 구간에는 다음 통과 지점까지의 거리-potential 진전을 조밀하게 보상한다. 왕복으로
  반복 수집할 수 없는 gamma-correct 차분을 사용하며, 접근 속도 품질은 진단값으로만 기록한다. 초기 strum의
  오타현·미준비·miss 비용은 낮추고, S1~S3에서 정확도 요구와 함께 단계적으로 원래 크기로 복원한다.
- single과 strum을 한 단계에서 경쟁시키지 않는다. A0~A3에서 single을 확보한 뒤 S0~S3에서
  strum을 독립적으로 습득하고 마지막에 곡으로 통합한다.
- A4는 실제 strum 사건의 진입측 1줄로 A3 단일 통과와 clean recovery를 재확인한다. S0은 처음부터
  2줄 연속 통과를 요구하고 S1은 같은 조건에서 span을 `3→4→5→6`으로 늘린다.
- S2는 E0에서 양방향 끝줄·exit 완주를 먼저 확보한 뒤 전체 span strum을
  `400→250→225→200→175→150→100→zone 100→67→50 ms` 중심·성공 기반 profile로 줄인다.
- S3에서 처음으로 single/strum이 섞인 phrase를 사용하고 `tempo_lambda=0→0.25→0.5→0.75→0.9→0.95→0.975→1`
  순서로 원곡 사건 간격을 복원한다.
- PPO 로그에는 `curriculum_strum_progress`, `curriculum_strum_max_strings`, 기존 completion/traversal/
  order/direction 지표와 `curriculum_approach_motion_quality`가 함께 저장된다.

관측 앞 8칸은 상호 배타적인 stage one-hot이 아니라 grip/ready/crossing/strum/timing/zone/span/song의
공유 기술 descriptor다. A3→S0에서 이미 배운 기술 입력이 사라지지 않는다. 관측 의미, 환경 상태 schema,
보상과 curriculum 계약이 모두 바뀌었으므로 과거 checkpoint는
재개하거나 초기화에 사용하지 않는다. 새 학습은 A0부터 시작한다.

## 2026-08-18 dense event·ordered strum·오타현·관절 진단

가까운 사건의 easy/runtime gap 진단, subframe 순서 기반 strum matcher, single/strum 분리 평가,
후기 tempo 오타현 budget 종료와 오른손 joint-limit soft 진단을 구현했다. strum observation은 완료한
traversal mask와 다음 줄을 포함한다. 사람 reference motion은 검증 schema와 profile 생성기까지만
구현했으며 실제 데이터 전에는 보상으로 활성화하지 않는다. 재시도 금지 결정과 후속 결과는
[`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md)에 누적한다.

## 2026-08-10 가까운 사건·strum·원템포 커리큘럼

원본 `strike_training.v1/v2` 파일은 수정하지 않고 goal compiler가 학습용 제스처를 만든다.

- 물리 회복 한계보다 가까운 서로 다른 줄 사건은 한 번의 `strum`으로 묶는다.
- strum은 첫 줄에서 마지막 줄까지의 연속 `traversal_mask`를 완주해야 완료된다. 그 사이의
  비발음 줄도 물리적으로 통과해야 하며 `audible_mask`와는 별도로 보존한다.
- 가까운 같은 줄 재타현은 현재 alternate same-string 제어가 없는 상태에서 거짓 학습하지 않고
  `alternate_restrike` 미지원 오류로 중단한다.
- A4의 초기 시간표는 인접 사건을 넓히되 원본 시각을 별도로 보존한다. 성능 gate를 통과할 때
  `tempo_lambda=0→0.25→0.5→0.75→0.9→0.95→0.975→1`로 진행하며, `1`에서 다시 통과해야만 curriculum이
  완료된다.
- 시간창은 사건마다 앞·뒤 간격의 45% 이하로 줄이는 비대칭 창을 사용한다. 따라서 가까운
  사건에서도 두 matcher 창이 겹치지 않는다.
- `tempo_lambda=1`에 도달한 checkpoint만 deterministic 전체곡 평가를 수행한다. 미완료 checkpoint는
  저장된 현재 tempo의 8-event phrase로 평가하여 학습 분포와 평가 분포를 일치시킨다.

`00_SS1-68-E_comp`의 동시 onset은 raw v3 입력으로 생성되며 176개 source event가
61개 single pick과 43개 strum, 총 104개 실행 제스처로 컴파일된다.

## 2026-08-13 A2 ready 기술 보존

A2 이후 ready 보상이 사라져 crossing만 수행하고 A1 ready 기술을 잃는 실패를 수정했다.
A2~A4는 ready 획득 전 위치 오차 페널티와 ready pulse 보너스를 유지하며, ready 이전 crossing은
물리 진단에는 남지만 crossing·timing·zone 보상을 받지 않고 별도 페널티를 받는다.
`curriculum_success_rate`도 A2 이후 ready 성공을 반드시 포함한다. 최대 stage iteration에서
당시에는 `stalled`에서 자동 종료했지만 2026-08-19부터 이 종료 동작은 제거했다. 상세 근거와 재학습 기준은
[`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md)의 STRIKE-002에 기록했다.

## 2026-08-16 A4 phrase lane 안정화

`20260813_1233_00_SS1-68-E_comp`는 A4의 `tempo_lambda=0`에서 recall 약 0.47로 정체됐다.
원인은 입력에 없는 lane 목표를 매 이벤트마다 다시 무작위 지정해 연속 타현 중 불필요한 줄 방향 이동을
요구한 것이었다. 이제 preferred 영역의 lane을 episode 시작에 한 번 표본화하고 8-event phrase 동안
고정한다. `target_lane_shift_m` 진단값은 phrase 내부에서 0이어야 한다. 평가·motion audit·일반 영상·
시각화 영상도 checkpoint가 저장한 tempo를 보존하며, 원래 tempo에 도달한 checkpoint만 전체 곡으로
전환한다. 상세 근거는 [`EXPERIMENT_HISTORY.md`](EXPERIMENT_HISTORY.md)의 STRIKE-003에 기록했다.

2026-07-27 재설계판은 실행 가능한 상태였다. 과거 S0 환경과 checkpoint는 복원하지 않았으며,
새 코드는 single 네 단계와 strum 네 단계를 순서대로 습득한다.

```text
A0_PICK_GRIP
→ A1_TIP_READY
→ A2_SINGLE_CROSSING
→ A3_TIMED_SINGLE (100 → 67 → 50 ms)
→ A4_STRUM_CONTEXT_RECOVERY (실제 strum 문맥 1줄 + clean recovery)
→ S0_TWO_STRING_STRUM
→ S1_STRUM_SPAN (3 → 4 → 5 → 6줄)
→ S2_TIMED_STRUM (E0 endpoint → 400 → 250 → 225 → 200 → 175 → 150 → 100 → zone 100 → 67 → 50 ms)
→ S3_SONG_INTEGRATION (tempo λ: 0 → 0.25 → 0.5 → 0.75 → 0.9 → 0.95 → 0.975 → 1)
```

iteration 수만으로는 승급하지 않는다. 각 단계의 최소 iteration 이후 성능 gate를 연속 3회
통과해야 하며, 최대 iteration에 도달해도 자동 승급하지 않고 `stalled` 진단을 남긴다. 학습은
중단하지 않고 명령의 `--iterations`까지 계속되며, 이후 gate를 통과하면 stalled가 해제된다. 모든 단계의
판정은 완료된 episode의 정확한 `strike_*` 지표만 사용한다. 한 PPO rollout 안에 완료 episode가
없으면 성공도 실패도 아닌 **no evidence**로 처리해 기존 연속 통과 횟수를 유지한다.

## 단계별 의미

| 단계 | 새로 학습하는 것 | 시간/영역 적용 |
|---|---|---|
| A0 | guitar 연구 frame 2227에서 얻은 피크 그립 자세 유지 | 타현 없음 |
| A1 | 6개 줄 각각의 down/up 진입측 ready 위치 도달 | 타현은 모두 FP |
| A2 | 준비·접근 뒤 목표 줄을 유효하게 통과 | timing/zone은 진단만 |
| A3 | 0.75–1.5초에 배치한 6줄 균형 단일 타현 | 허용 오차 100→67→50 ms |
| A4 | 실제 strum 방향·진입 문맥의 첫 줄 통과 뒤 고속 왕복 없이 12-frame 회복 | timing/zone 없음 |
| S0 | 실제 2줄 strum의 올바른 방향·순서·연속 궤적 완주 | timing/zone 없음 |
| S1 | 같은 연속 궤적의 폭을 3→4→5→6줄로 확대 | timing/zone 없음 |
| S2 | 먼저 양방향 마지막 줄·exit 완주를 회복하고, 다음에 6줄 timing과 strike 영역을 추가 | E0 endpoint→400→250→225→200→175→150→100 ms, 이후 zone+100→67→50 ms |
| S3 | 원래 `[time, frame, string]` 곡의 single/strum을 혼합 실행 | 50 ms, sampled lane, tempo λ를 0→1로 복원 |

S3의 release 위치는 preferred 구간 안에서 episode마다 샘플링한다. 따라서 중앙 한 점을 외우는
정책이 아니라 허용된 영역의 여러 phrase lane을 학습하되, 한 phrase 안에서는 사람처럼 같은 타현
영역을 유지한다. 각 sampled lane은 점이 아니라 `±6 mm`에서 만점이고 `±12.5 mm`까지 성공 가능한
띠다.

## 승급 gate

모든 단계는 앞 단계 기술을 계속 만족해야 한다.

| 단계 | 완료 episode에서 읽는 지표 | 현재 curriculum gate |
|---|---|---|
| A0 | binary/연속 grip 지표, `failure_termination` | success ≥ 0.90, mean/p05 ≥ 0.92/0.85, pinch/free ≥ 0.95/0.85, bad rate/streak ≤ 0.05/12, failure = 0 |
| A1 | 위 grip 지표 + `strike_tip_ready_success_rate` | 공통 grip gate, ready ≥ 0.85 |
| A2 | 위 지표 + `strike_release_recall`, `strike_false_positive_rate` | recall ≥ 0.80, FP rate ≤ 0.05 |
| A3 100 ms | 위 지표 + `strike_episode_f1`, `strike_timing_p95_ms` | F1 ≥ 0.80, p95 ≤ 100 ms |
| A3 67 ms | 동일 | F1 ≥ 0.90, p95 ≤ 67 ms |
| A3 50 ms | 동일 | F1 ≥ 0.95, p95 ≤ 50 ms |
| A4 | strum 문맥 1줄 지표 + recovery completion/reset/blocked rate | completion ≥ 0.90, direction ≥ 0.95, recovery ≥ 0.95, reset/blocked ≤ 0.05 |
| S0 | 실제 2줄 completion, traversal/order/direction + recovery | completion ≥ 0.90, traversal ≥ 0.95, order ≥ 0.98, direction ≥ 0.95, recovery ≥ 0.95, reset/blocked ≤ 0.08 |
| S1 각 폭 | S0와 동일; 현재 폭 이상인 실제 strum만 표본화 | 동일 gate를 통과하면 다음 폭으로 확대 |
| S2 E0 endpoint | 양방향 raw completion + conditional/end-to-end recovery; timing은 진단 | completion ≥ 0.80, worst direction/end-to-end ≥ 0.75 |
| S2 T0 400 ms | strum gate + 양방향/end-to-end + timing 중심·microtiming | pass/completion/worst direction/end-to-end ≥ 0.70, mean ≤ 180 ms, tail ±300 ms, RMS ≤ 300 ms, duration ≤ 200 ms |
| S2 T1 250 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.75, mean ≤ 110 ms, tail ±190 ms, RMS ≤ 200 ms, duration ≤ 150 ms |
| S2 T2 225 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.78, mean ≤ 95 ms, tail ±170 ms, RMS ≤ 180 ms, duration ≤ 140 ms |
| S2 T3 200 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.80, mean ≤ 80 ms, tail ±150 ms, RMS ≤ 165 ms, duration ≤ 130 ms |
| S2 T4 175 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.82, mean ≤ 70 ms, tail ±130 ms, RMS ≤ 145 ms, duration ≤ 115 ms |
| S2 T5 150 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.85, mean ≤ 55 ms, tail ±110 ms, RMS ≤ 120 ms, duration ≤ 100 ms |
| S2 T6 100 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.88, mean ≤ 35 ms, tail ±75 ms, RMS ≤ 80 ms, duration ≤ 70 ms |
| S2 Z0 100 ms | 위 지표 + zone | T6 gate + worst direction/end-to-end ≥ 0.88, zone ≥ 0.80 |
| S2 Z1 67 ms | 동일 | pass/completion/worst direction/end-to-end ≥ 0.90, mean ≤ 25 ms, tail ±50 ms, zone ≥ 0.90, RMS ≤ 50 ms, duration ≤ 45 ms |
| S2 Z2 50 ms | 동일 | pass ≥ 0.95, completion/worst direction/end-to-end ≥ 0.90, mean ≤ 18 ms, tail ±35 ms, zone ≥ 0.95, RMS ≤ 35 ms, duration ≤ 30 ms |
| S3 tempo 0~0.5 | single F1 + strum/timing/zone/microtiming + 원인별 failure | F1 ≥ 0.98, safety failure=0, wrong 종료=0, blocked ≤ 0.02 |
| S3 tempo 0.75 | 동일 | F1 ≥ 0.975, wrong 종료 ≤ 0.08, blocked ≤ 0.025 |
| S3 tempo 0.9→1.0 | 동일 | 단계적으로 강화; 원곡에서 F1 ≥ 0.99, wrong 종료/blocked ≤ 0.01 |

A1~S2는 표의 성능 지표와 함께 완료 episode의 `failure_termination=0`을 요구한다. S3는 안전 실패
`0`을 유지하면서 tempo별 wrong-crossing 종료 gate를 적용한다.

모든 S2 profile은 conditional recovery completion `≥0.95`도 별도로 요구한다. down/up completion,
전체 strum completion과 두 recovery rate는 raw 분자·분모를 먼저 합친 뒤 한 번 계산한다. endpoint
focus가 켜진 동안 승급에는 `s2_focus_sampled=0`인 balanced holdout만 들어가며, 해당 evidence가
없으면 fail-closed 한다.

timing MAE/p95는 성공으로 인정된 타현만 모으지 않는다. 올바른 줄·방향을 실제로 통과한
모든 target attempt를 **시간 허용창과 zone gate 적용 전**에 기록한다. 따라서 너무 이르거나 늦은
타현도 timing tail에 남고 p95 gate를 우회할 수 없다. 내부 motor phase는 matcher hard gate가 아니며,
phase가 어긋난 RELEASE는 step의 `release_phase_violation`, PPO 로그의
`curriculum_release_phase_violation` 진단으로 따로 남긴다.
여러 완료 episode의 raw 절대 오차 표본을 합친 뒤 한 번의 global p95를 계산한다.

A3/S2의 no-release miss는 시간창이 닫히면 episode를 끝낸다. 허용창 밖에서 완료된 traversal은
같은 step에 timing miss가 되지만, 일부 줄만 이른 부분 strum은 전체 traversal을 계속한다. 물리적으로
완료한 early/late traversal은 timing 실패와 별개로 현재 단계가 요구하는 `RELEASE_RECOVER` 뒤
끝난다. A3/S2와 S3의 마지막 hit는 12-frame full recovery를 보존하고, S3의 짧은 중간 간격만
다음 접근까지 확보 가능한 handoff recovery를 사용한다.
기본 S3 학습 episode는 임의 시작점에서 연속 8개 event를 사용하고 첫 목표 30 frame 전부터
준비한다. deterministic 평가는 전체 104개 실행 gesture를 사용한다.

위 표는 curriculum 진행 기준이다. 최종 deterministic S3 평가는 더 엄격한
precision/recall/F1/zone `0.99`, false-positive rate `≤0.01`, timing p95 `≤50 ms`,
strum RMS `≤25 ms`, sweep-duration MAE `≤20 ms`를 사용하고,
scheduled/full/handoff recovery completion을 각각 `1.0`, recovery reset `0`,
blocked-before-rearm crossing `0`을 요구하며,
수치 통과 뒤에도 영상의 사람 검토를 요구한다.

## 실행

기본 진단 실행:

```bash
python -m tab2body.train \
  --task strike --iterations 3000 --run-name strike_diagnostic
```

새 strum-v2 전체 학습:

```bash
python train.py \
  --task strike \
  --song 00_SS1-68-E_comp \
  --iterations 50000 \
  --num-envs 1024 \
  --run-name 20260824_clean_recovery_v5
```

500 iteration:

```bash
python -m tab2body.train \
  --task strike --iterations 500 \
  --run-name strike_500
```

500 iteration은 새 보상과 single 기초 동작을 확인하는 첫 진단 실행이다. S1에는 폭별 최소 체류,
S2에는 tolerance별 최소 체류, S3에는 tempo별 최소 체류가 각각 적용되므로 전체 계약 검증에는
50,000 iteration 실행을 권장한다.

영상 인코딩을 제외한 학습/checkpoint/평가/분석/plot 배관을 먼저 짧게 검사:

```bash
python -m tab2body.train \
  --task strike --smoke \
  --run-name strike_smoke
```

한 단계만 고정해서 진단할 수도 있다.

```bash
python -m tab2body.train \
  --task strike --curriculum-stage A3_TIMED_SINGLE \
  --timing-tolerance-ms 100 \
  --iterations 500 \
  --run-name strike_a3_100ms
```

## 학습 중·종료 후 자동 산출물

```text
strike/training/runs/<run>/
  checkpoints/strike_<iteration>.pt
  logs/metrics.jsonl
  logs/training.log
  logs/artifacts.log
  logs/sessions.jsonl
  logs/periodic_videos.jsonl
  evaluations/strike_<iteration>.eval.json
  evaluations/strike_<iteration>.motion_diagnostics.json
  plots/strike_training_curves.png
  videos/strike_<iteration>_rollout_remembered.mp4
  videos/strike_<iteration>_rollout_current.mp4
  videos/strike_<iteration>_rollout.json
  videos/strike_<iteration>_rollout_down_remembered.mp4  # S0~S2
  videos/strike_<iteration>_rollout_down_current.mp4     # S0~S2
  videos/strike_<iteration>_rollout_down.json            # S0~S2
  videos/strike_<iteration>_rollout_up_remembered.mp4    # S0~S2
  videos/strike_<iteration>_rollout_up_current.mp4       # S0~S2
  videos/strike_<iteration>_rollout_up.json               # S0~S2
  videos/strike_<iteration>_full_song_remembered.mp4  # S3 전용
  videos/strike_<iteration>_full_song_current.mp4     # S3 전용
  videos/strike_<iteration>_full_song.json            # S3 전용
  # opt-in 진단 replay
  videos/strike_<iteration>_rollout_remembered_zone_pick.mp4
  videos/strike_<iteration>_rollout_current_zone_pick.mp4
  videos/strike_<iteration>_rollout_zone_pick.json
  ANALYSIS.md
  run_manifest.json
```

- checkpoint에는 30개 관절의 정확한 이름·순서, 현재 9-stage curriculum과 observation manifest, goal/grip hash,
  detector·zone·오른팔 관통 진단·보상·PPO 설정, policy 초기 표준편차, model/optimizer, iteration/global step,
  asset/구현 지문, curriculum stage/tolerance/streak/complete와 환경 상태가 저장된다.
- resume은 optimizer/counter/curriculum과 `StrikeTask` 전용 generator RNG/reset generation을
  복원한다. 전역 Torch CPU/CUDA RNG까지 저장하는 bitwise stochastic resume은 아직 아니다.
- 평가에서는 checkpoint의 PPO 설정과 policy 초기 표준편차로 모델을 재구성한 뒤 계약을 검증한다.
  training context와 environment의 stage/tolerance/tempo/span이 다르면 로드 전에 중단한다.
- 서로 다른 계약의 checkpoint는 resume·평가·영상 기록 전에 거부한다.
- 마지막 정책은 해당 단계에 맞게 deterministic 평가한다. S3 전체곡 평가는 첫 사건보다
  30 frame 앞에서 시작해 ready/approach 시간을 확보하며, source 176개가 컴파일된 104개
  실행 제스처 전체를 평가한다.
- 자동 motion 진단은 RELEASE depth/횡속도, tip speed, grip RMS, phase별
  shoulder/elbow/wrist/hand 속도·가속도·jerk, action saturation, recovery corridor·역방향 RELEASE,
  오른팔/손 기타 관통 분포를 JSON으로 저장한다. 이 값은 관찰용이며 성공/실패 분포가 분리되기 전에는
  보상이나 종료 임계값으로 사용하지 않는다.
- 평가는 checkpoint의 policy 초기 표준편차/PPO 설정, curriculum stage/tolerance와
  `StrikeTask` generator RNG를 복원한다. 영상 recorder는 저장된 stage/tolerance를 적용하고
  고정 seed로 deterministic rollout을 새로 만든다. 학습 재개는 현재 설정과 완전히 같을 때만 허용한다.
- 학습 도중 평가·주기 영상을 만들 때는 failure-mining 상태, task generator RNG, reset generation을
  함께 snapshot한다. 녹화 뒤 이를 먼저 복원하고 새 학습 observation을 reset하므로 산출물 생성이
  이후 hard-window 선택이나 reset 난수열을 바꾸지 않는다.
- 영상은 `remembered`와 `current` 두 고정 카메라로 저장한다. S0~S2는 같은 checkpoint에서
  down/up을 각각 강제한 두 rollout을 기록하고 실제 `practice_direction`, 두 방향 완주와
  runtime/RNG 복원을 방향별 report로 검증한다. S3는 계획된 곡 방향을 바꾸지 않는다.
- 일반 `_rollout_*` 영상은 현재 curriculum episode를 첫 종료까지 기록하는 짧은 복기 자료다.
  S3 checkpoint에는 이 파일들과 별도로 원곡 속도 약 42초의 `_full_song_*` 두 영상과 report를
  저장한다. 전체곡 녹화는 첫 사건 30 frame 전부터 시작하고 104개 실행 gesture의 마지막 시각을
  지난 뒤 끝난다.
- S3 전체곡 녹화에서는 wrong-crossing 임계값을 조기 종료로 사용하지 않고 진단값으로 계속
  집계한다. non-finite·속도 폭주 같은 복구 불가능한 안전 종료는 유지한다. recorder는 첫 `done`
  뒤 reset된 곡을 이어 붙이지 않으며 report의 `captured_original_song_duration`,
  `completed_full_timeline`, `ended_before_original_song_end`, `stitched_after_episode_reset`으로
  길이와 종료 의미를 구분한다. report v2의 `event_trace`와 `event_trace_summary`에는 계획 event별
  실제 통과 줄, accepted/blocked, miss, wrong count, timing과 전체 TP/FP/FN가 함께 저장된다.
- 학습 중에는 마지막으로 두 영상과 report가 모두 완성된 iteration에서 1,900 iteration 이상 지난
  상태로 다음 checkpoint가 저장되면 현재 정책의 deterministic rollout을 두 카메라로 기록한다.
  기본 500-iteration checkpoint 주기에서는 보통 2,000 iteration 간격이다. curriculum 전환
  checkpoint가 1,900 이후 먼저 저장되면 그 checkpoint를 사용한다.
- 중간 녹화는 현재 Isaac Gym을 잠시 멈추고 수행하며, 별도 simulator를 띄우지 않는다. 녹화 뒤에는
  모든 학습 환경을 새 episode로 reset하고 PPO 관측도 교체한다. 성공·실패와 실제 선택 iteration은
  `logs/periodic_videos.jsonl`과 `run_manifest.json`에 기록한다. 생성 실패는 학습을 중단하지 않고
  마지막 완료 iteration을 유지해 다음 checkpoint에서 다시 시도한다.
- `Ctrl-C`로 학습을 중단하면 마지막으로 완료된 iteration을 checkpoint로 저장한 뒤 최종 평가와
  두 카메라 산출물 생성을 계속한다. 산출물 처리까지 즉시 중단하려면 다시 중단 신호를 보내야 한다.
- 간격은 `--periodic-video-min-gap`으로 바꿀 수 있고 `--no-auto-video`는 중간·최종 영상을 모두 끈다.
- S3 checkpoint의 전체곡 영상만 다시 만들 때는 아래처럼 실행한다.

```bash
python -m tab2body.tools.record_strike_rollout \
  --checkpoint strike/training/runs/<run>/checkpoints/strike_<iteration>.pt \
  --goal data/song_bundles/<song_id>/training/strike_plan.json \
  --grip-reference strike/02_physical_control/pick-grip-reference.json \
  --full-song
```
- `record_strike_visualized_rollout.py`를 별도로 실행하면 기존 영상을 보존한 채 실제 6개 줄,
  allowed/preferred/current lane, geometry-less `RH:pick`과 짧은 이동 궤적을 두 영상에 표시한다.
  오버레이는 카메라 PNG 위의 X-ray 진단 투영이며 물리나 충돌 판정에는 참여하지 않는다.
- `--smoke`는 시간을 줄이기 위해 자동 영상을 끈다. 이중 영상 경로는 저장된 checkpoint를
  `--eval`로 다시 열거나 recorder를 직접 실행해 확인한다. 중간 녹화 경로 자체를 GPU에서 검사할
  때만 `--smoke --smoke-video --periodic-video-min-gap 1`을 사용한다.
- 평가나 후처리 하나가 실패해도 이미 생성된 checkpoint/log 경로와 오류 종류를 manifest에 남긴다.
- 수치 gate를 통과해도 `human_like_review_required=true`다. 두 영상을 사람이 확인해야 한다.

## 현재 검증 결과

`tab2body/tools/audit_strike_runtime.py`를 RTX 4070 Ti의 GPU PhysX/GPU pipeline에서 실행했다.

2026-08-30 path-aware 기반 계약의 CPU 회귀는 `27/27 PASS`였다. 2026-08-31 endpoint 계약은
방향대칭 terminal progress, physical/timing 판정 분리, raw-count pooling, E0와 방향 집중/holdout,
첫 9 action std floor, 제한된 S2 policy transfer, S0~S2 paired video를 독립 회귀 검사로 고정했다.
runner-lazy/event/curriculum/reward/checkpoint/artifact/paired-video/runtime/PPO의 선택된 CPU 스크립트
9개는 모두 통과했다.
현재 호스트에서는 NVIDIA driver를 사용할 수 없어 이 계약의 Isaac Gym GPU smoke와 장기 학습 효과는
검증하지 못했다. 아래 GPU 결과는 이전 계약의 역사적 배관 증거이며 327D 정책의 현재 성능이나
호환성을 뜻하지 않는다.

- action: 30 (`R_Shoulder/Elbow/Wrist` 9 + `RH:*` 21)
- 2026-07-29 당시 observation: 263, 2026-08-19 balanced-direction 계약: 321. 현재
  path-aware clearance 계약은 recovery/music 방향과 clearance 상태 6개가 늘어난 327이며 CPU
  manifest 검증은 통과했지만 Isaac Gym CUDA smoke는 driver unavailable로 미실행이다.
- `R_Thorax`: action 제외
- `G:pluck_range`: 해당 1개 shape만 사람과 충돌하지 않게 비활성, 나머지 기타 충돌 유지
- 실제 6개 string marker 좌표 finite
- 최소 인접 줄 간격 9.639 mm, 최대 stroke across offset 3 mm
- 과거 A0~A4 hold probe에서 finite observation/reward, 실패 종료 0; 당시 v3는 A0 PPO update와
  checkpoint schema/관측 manifest까지 CUDA smoke 검증 완료
- A3 target time 0.75–1.5초, 6개 줄 균형
- S2/S3 lane은 preferred `[-0.355,-0.295] m` 안, core `±6 mm`, outer `±12.5 mm`
- 전체곡 시작 `-0.4769 s`, 첫 사건까지 30-frame pre-roll, 최대 894 frame
- 당시 8-env PPO/checkpoint/evaluation smoke와 checkpoint 재로딩 통과
- 2026-08-25 v7 계약은 `20260825_strike009_smoke`에서 8-env·1-iteration GPU PhysX 학습,
  checkpoint v9, evaluation v5, 분석·plot·motion diagnostics 자동 생성을 통과
- `20260825_strike009_s2_smoke`에서 S2/T1 250 ms 고정 실행과 center mean/tail gate의
  학습 로그·평가 전달을 확인
- v8 profile별 timed-approach, READY wait, early-center penalty와 v10 checkpoint 계약은 Strike
  전용 15개 CPU 회귀 및 checkpoint·PPO·진입 검사를 통과했다.
- `20260825_strike011_smoke_complete`의 GPU PhysX A0 전체 배관과 최종 소스의
  `20260825_strike011_t1_final_smoke` S2/T1 고정 runtime도 통과했으며 장기 학습 효과는 검증 전
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
[STRIKE_5000_20260727.md](../archive/STRIKE_5000_20260727.md)에 기록했다.

## 아직 주장하지 않는 것

- 1 mm depth, 0.05 m/s 횡속도, 3 mm·2 frame re-arm은 실행 가능한 초기값이며 충분히
  학습된 정상/오류 rollout 분포로 재보정해야 한다.
- 원본 입력에는 방향이 없고 `phrase_dp_microtiming_v3`가 전체 곡의 방향·줄별 시각과 이동 중 재통과 비용을 미리 확정한다.
  현재 사건과 두 개 lookahead의 방향을 관측하며 정책이 실행 중 방향을 변경하지 않는다.
- 실제 피크 geometry, 물리 grasp/slip, 줄 탄성·소리, fingerstyle, up/alternate, hybrid는 보류다.
- runtime smoke 통과는 장시간 학습 성능을 뜻하지 않는다. 장시간 학습의 실제 성능은
  5,000-iteration 결과 문서와 로그·평가·영상으로 판단한다.

과거 500회 실패 실험은 비교 자료로
[STRIKE_S0_PILOT_500_20260727.md](../archive/STRIKE_S0_PILOT_500_20260727.md)에만 남긴다.
