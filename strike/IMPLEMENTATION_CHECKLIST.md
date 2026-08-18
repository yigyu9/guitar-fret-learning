# task_strike 구현 판정표 — 규칙을 코드·진단·보류로 내리는 방법

> 최상위 실행 규칙은 [RIGHT_HAND_RULES.md](RIGHT_HAND_RULES.md), strum·양손 확장은
> [RIGHT_HAND_EXTENSIONS.md](RIGHT_HAND_EXTENSIONS.md)다. 이 표의 S/N 항목은 하위 상세 추적 ID다.

> **현재 상태 갱신 — 2026-07-27:** 이 표의 과거 S0/593D/4채널 항목은 역사 기록이다.
> 새 실행 정본은 최소 `[time,frame,string]`, 281D observation, scalar reward,
> `A0_PICK_GRIP→A4_ZONE_CONTROL`이다. 현재 파일별 판정은
> [status.md](02_physical_control/status.md)와 [학습 문서](03_training/README.md)를 우선한다.

새 재설계에서 완료한 구현 단위:

1. `[x]` 최소 goal schema/42-event builder/time authority/string conversion.
2. `[x]` finite swept detector, subframe time, direction/depth/speed, release/re-arm, zone quality.
3. `[x]` 30-DOF StrikeTask, 281D fixed observation, A0 arm mask, stale-reset 방지.
4. `[x]` pick-grip/ready/crossing/timing/zone stage-masked scalar reward.
5. `[x]` 성능 기반 A0~A4와 100→67→50 ms 저장·복원 curriculum.
6. `[x]` strike checkpoint schema, PPO 로그, 평가 gate, plot, 분석, remembered/current recorder.
7. `[x]` CPU tests, 실제 CUDA detector 동등성, A0~A4 GPU runtime audit, PPO smoke.
   - A0~A4 승급은 완료 episode의 exact 지표와 failure=0만 사용하고 no-evidence rollout은 streak을 보존한다.
   - timing p95는 tolerance/zone gate 전 target crossing 전체를 pooling한다.
   - A4 global zone과 sampled lane band의 attempt/hit 저장공간을 분리한다.
   - checkpoint 재평가의 saved PPO/task RNG 복원과 1600×900 이중 MP4를 GPU에서 재검증했다.
8. `[ ]` 새 환경 500회 학습 및 로그·두 영상 기반 수정.
9. `[ ]` 충분히 학습된 분포로 detector/안전/naturalness 후보 수치 재보정.
10. `[ ]` up/alternate, fingerstyle, hybrid 확장. down-strum은 2026-08-10 구현.

2026-08-10 빠른 사건 대응 구현:

1. `[x]` v1/v2 source를 immutable하게 읽는 capability-aware goal compiler.
2. `[x]` 가까운 이종 줄 사건과 동시 onset을 `audible/traversal/protected` mask의 down-strum으로 컴파일.
3. `[x]` strum의 부분 RELEASE 누적, traversal 완료 직후 hit, mask 밖/역방향 FP matcher.
4. `[x]` 인접 사건별 비대칭 timing window로 overlap 제거.
5. `[x]` easy timeline과 `tempo_lambda 0→0.25→0.5→0.75→0.9→1` A4 homotopy.
6. `[x]` original-tempo gate 전 curriculum 완료 금지, 전체곡 평가는 원본 시간 강제.
7. `[x]` `00_SS1-68-E_comp` v2 goal 생성: source 176, compiled 104, strum 43, unsupported 0.
8. `[x]` CPU strike 회귀 검사 전체 통과.
9. `[ ]` CUDA/Isaac Gym smoke와 새 checkpoint 학습. 현재 세션은 CUDA가 없어 preflight에서 중단됨.
10. `[ ]` same-string alternate restrike와 upstroke detector/controller.

2026-08-03 정리에서는 Strike 전용 중복 설정·학습 배관·recorder fallback을 합치고, 실제 RELEASE 기반
회복·A4 READY miss·중복 crossing·종료 시 회복 gate를 CPU 회귀로 다시 닫았다. 현재 CUDA device가 없어
위 7번의 과거 GPU 증거를 최신 코드 증거로 재사용하지 않는다. 변경 내역과 재검증 명령은
[`CODE_AUDIT_2026-08-03.md`](CODE_AUDIT_2026-08-03.md)에 있다.

2026-08-04에는 제공 R1~R28을 다시 판정해 R7·R8·R11~R16의 motion/safety 진단을 구현했다.
학습 종료 시 `motion_diagnostics.json`이 자동 저장되며, R16 오른팔 관통 monitor는 분포 보정 전까지
termination을 비활성으로 유지한다. R18~R28은 누락이 아니라 공통 event/full-task 선행조건이 있는
명시 보류다. 항목별 최종 판정은 [`RULE_TRACEABILITY.md`](RULE_TRACEABILITY.md)를 따른다.

> 아래 `0~5` 절은 2026-07-23 pilot의 역사적 판정표다. 현재 구현 여부는 위 1~10과
> `status.md`를 따른다.
>
> 과거 상태: 2026-07-27 pick-only S0 500회 pilot 완료. PPO 수집기의 reusable observation
> buffer 참조 결함은 수정·회귀검사했지만 RELEASE 0/F1 0으로 primitive 학습은 실패했다.
> 다음 실행 전 A0 dynamic-ready·성능 기반 승급·거리 진단·6줄×양방향 GPU probe가 필요하다.
> `S1~S60`을 규칙마다 검토하되, 함수와 reward는 의미가 같은 규칙끼리
> 합친다. `계약 동결 → CPU oracle → GPU probe → task smoke → 학습 배관 → PPO → 전체곡 평가`
> 순서를 따른다.

## 0. 2026-07-23 실행 결과

| 단위 | 결과 | 코드/증거 | 다음 판정 |
|---|---|---|---|
| U0 Source/Mapper | 구현·PASS | `strike_mapper.py`, builder, 실제 42-event plan, byte-identical 재생성 | 유지 |
| U1 Goal/Observation | 구현·PASS | exact 593D manifest, 4,096-env CPU tensor test 7.99ms | GPU profile 후 최적화 재확인 |
| U2 Detector/Re-arm | 구현·PASS | CPU oracle, down/up·depth·near-miss·6줄 순서·re-arm test | 후보 수치는 진단 유지 |
| U3 Matcher/Task/Metrics | matcher CPU PASS, 기본 GPU step PASS | 배타적 class와 miss-once test; 8-env 30-action/806-obs finite step | scripted trajectory 보류 |
| U4 Reward/Audit | CPU adversarial PASS | signed corridor potential, hit-only zone, event/timing/economy; exact 1.019 > hover .120 > do-nothing 0 | GPU audit 전 임시 |
| U5 Safety | 공통 bounded action/finite/velocity 재사용 | base 경로 사용 | 우손 penetration/wrist 분포 진단 미구현 |
| U6 Curriculum/Training | 배관 PASS, primitive FAIL | 512-env×500 iter, 8.19M sample, 두 카메라 자동 저장; PPO update 정상, RELEASE 0/F1 0 | A0 dynamic-ready·성능 기반 승급·거리 진단·GPU probe 뒤 재학습 |

비동기 reset에서 stale rigid-body 위치가 가짜 swept crossing을 만들지 않도록 S0는
`reset_noise=0`을 fail-fast하고, full reset에서 PhysX로 갱신된 pick/body snapshot을 partial reset
관측과 detector history에 재사용한다. noisy RSI는 matching FK body cache 이후의 후속 구현이다.

2026-07-23 사용자 결정으로 strike action의 시작 관절은 `R_Shoulder`다. `R_Thorax` 3 DOF는
제어하지 않고 초기 PD 자세로 유지한다. 따라서 control은 shoulder3+elbow3+wrist3+hand21=30,
observation은 base183+goal593+EMA30=806이다. checkpoint의 ordered DOF와 model shape가 달라지므로
구 33-action strike checkpoint가 생겼더라도 직접 resume할 수 없다.

S1~S60의 현재 결론은 다음처럼 읽는다.

- **구현 완료·CPU 검증**: S1~S4, S6~S7, S9~S12, S15~S18, S31, S37, S39~S41,
  S43~S47, S51, S53의 pick-single 범위.
- **코드 구현, GPU 증거 대기**: S19~S24의 최소 보상/공통제어, S30 curriculum, S38 zone,
  S54 metric/task 경로.
- **진단 산출물 완료, threshold 승격 금지**: S23, S38, S46의 일부. PNG 2개, MP4 1개,
  JSON 1개를 `strike/renders`, `strike/diagnostics`에 저장했다.
- **후속 구현 유지**: S8, S13~S14, S25~S28, S32~S34, S42, S48~S50, S52, S55~S57,
  S59~S60. GPU 정상/오류 분포 또는 선행 주법 primitive가 필요하다.
- **명시 보류/거부 유지**: S29, S35~S36, S58과 rest stroke, 물리 pick grasp,
  fingerstyle/hybrid/strum, 최종 human-like 선언.

“완료”는 전체 S 규칙 완료가 아니라 **pick-only single S0에서 해당 규칙의 실행 가능한 부분**을 뜻한다.
v1은 `multi_pluck/strum` enum을 예약하지만 validator가 실행 계획을 거부한다.

## 1. 처리 상태

| 상태 | 의미 | 허용되는 결과 |
|---|---|---|
| **즉시 구현** | 의미와 정답/오답이 명확하고 현재 에셋으로 검증 가능 | loader, detector, matcher, test, fail-fast |
| **후속 구현** | 계약은 확정됐지만 선행 primitive나 주법 단계가 필요 | schema는 지금 보존하고 해당 stage에서 활성화 |
| **공통 통합** | strike 전용으로 복제하지 않고 검증된 fret/base 인프라를 재사용 | 공용 helper 확장 또는 task 조립 |
| **진단 우선** | 정상 분포 없이 reward/종료 임계값을 정하면 오탐 위험 | info/JSON/영상만 기록, 정책 return과 done에는 영향 없음 |
| **보류** | 물리 에셋·annotation·reference가 없어 현재는 정직하게 구현 불가 | loader가 unsupported를 명시적으로 거부 |

보류는 묵시적 무시가 아니다. source가 보류 주법을 요구하면 fallback으로 일반 strike인 척하지 않고
loader가 중단한다.

## 2. 구현 과정 규칙 E1~E16

| ID | 규칙 |
|---|---|
| E1 | 하나의 의미에는 한 owner만 둔다. detector·matcher·reward가 같은 crossing을 각자 다시 계산하지 않는다 |
| E2 | `S 규칙 하나 = reward 항 하나`로 만들지 않는다. 여러 규칙이 하나의 상태기·검출기·검사기로 합쳐질 수 있다 |
| E3 | CPU 합성 oracle을 통과하지 않은 기하와 상태기는 GPU task에 넣지 않는다 |
| E4 | GPU scripted trajectory를 통과하지 않은 detector/re-arm 수치로 PPO를 시작하지 않는다 |
| E5 | 진단값은 정상·오류 분포 분리와 영상 대조 전 reward·종료·최종 gate로 승격하지 않는다 |
| E6 | unsupported agent/setup/stroke mode는 fail-fast한다. 조용한 default와 일반 주법 위장은 금지한다 |
| E7 | detector는 goal을 보지 않고 물리 사건만 만들며 matcher만 goal을 본다 |
| E8 | 음악 event FSM, 정책 motor phase, `(agent,string)` detector state, reward ledger를 서로 다른 상태로 유지한다 |
| E9 | core outcome은 one-shot이고 auxiliary는 event 적분 return으로 core보다 작은지 감사한다 |
| E10 | reward 변경 전후에 do-nothing·hover·jitter·전줄 sweep·zig-zag scripted return을 재검사한다 |
| E11 | 새 stage로 승급할 때 이전 stage의 정확도·안전·reward audit를 모두 다시 통과한다 |
| E12 | 구현 수치와 field 순서가 바뀌면 source/intent/plan/runtime/checkpoint schema version을 올린다 |
| E13 | strike 구현 때문에 검증된 fret/base 계약을 선제 리팩터링하지 않는다. 실제 중복이 생긴 helper만 테스트 후 공통화한다 |
| E14 | 자연스러움 항은 정확한 strike primitive가 안정된 뒤 켜고, 정확도 회귀가 생기면 다시 진단으로 내린다 |
| E15 | motion prior score 하나로 human-like를 선언하지 않고 feature 분포와 deterministic 영상을 함께 본다 |
| E16 | 각 완료 표시는 코드 경로, CPU test, GPU evidence, 산출물 위치 네 가지가 있을 때만 `[x]`로 바꾼다 |

## 3. 규칙을 합칠 구현 단위

규칙 60개를 파일 60개로 만들지 않고 다음 7개 단위로 합친다.

| 단위 | 포함 규칙 | 권장 owner |
|---|---|---|
| U0 Source/Mapper | S1~S5, S31~S33, S39~S42, S48~S52 | `tab2body/strike_mapper.py`, `tools/build_strike_training_data.py` |
| U1 Goal/Observation | S2, S15~S17, S39~S43, S48~S51 | `env/strike_goals.py` 신규; 검증된 `goals.py` fret 경로는 유지 |
| U2 Detector/Re-arm | S6~S11, S18, S43~S47, S53 | `env/strike_detector.py` 신규 |
| U3 Matcher/Task/Metrics | S9, S12~S18, S34, S43~S45, S53~S54 | `tasks/task_strike.py`, `env/metrics.py` |
| U4 Reward/Audit | S19~S23, S38, S55~S57 | `rewards/strike.py`, `tools/audit_strike_reward.py` |
| U5 Safety | S24~S28, S37, S46 | 기존 `base.py`·`safety.py` 확장, `tools/probe_strike_runtime.py` |
| U6 Curriculum/Style/Eval | S30, S58~S60 | `curriculum.py`, `train.py`, checkpoint contract, rollout/audit 도구 |

`env/goals.py`는 현재 846줄의 fret 전용 검증 경로이고 학습 증거가 있다. strike를 억지로 그 안에 넣지
않고 `strike_goals.py`를 만든다. 양쪽에서 실제로 같은 시간/hash helper가 중복된 뒤에만 작은
`goal_common.py` 추출을 검토한다.

## 4. S1~S60 개별 판정

### S1~S10 — source와 기본 detector

| ID | 판정 | 구현/검증 제안 |
|---|---|---|
| S1 | 즉시 구현 | `notes[]` 전수 source화, `presses[].strikes`는 대조 보고서에만 사용; open-string 보존 test |
| S2 | 즉시 구현 | source/intent/plan/runtime 각 loader의 finite·ID·enum·hash fail-fast |
| S3 | 공통 통합 | CSV 0=low-E→Isaac 5=low-E 변환을 builder 경계 함수 하나로 두고 왕복 test |
| S4 | 즉시 구현 | source `either` 보존, `pick_only_v1` mapper가 실제 down/up을 결정하고 provenance 저장 |
| S5 | 즉시 구현 | audible 빈 줄 자동 채움 금지; traversal/muted 정보 없는 비연속 strum 거부 test |
| S6 | 즉시 구현 | agent detector registry를 만들되 첫 활성 agent는 pick만; 미지원 finger agent는 loader 오류 |
| S7 | 즉시 구현 | swept pick point×finite string의 `t/s/depth` CPU oracle과 endpoint/parallel/high-speed test |
| S8 | 후속 구현 | p/i/m/a/c swept capsule과 contact→load→release는 fingerstyle V2에서 활성화 |
| S9 | 즉시 구현 | matcher가 string뿐 아니라 plan agent를 검사; acoustic hit와 plan violation은 별도 metric |
| S10 | 즉시 구현 | goal-independent `(agent,string)` separation/time/direction re-arm; rest 반복 오타 test |

### S11~S20 — event와 actor 목적

| ID | 판정 | 구현/검증 제안 |
|---|---|---|
| S11 | 즉시 구현 | 한 control step의 복수 crossing을 swept `t`로 정렬하고 6→1/1→6 순서 test |
| S12 | 즉시 구현 | pick single event의 one-shot complete/miss/extra 상태 전이 |
| S13 | 후속 구현 | 서로 다른 finger detector가 준비된 V2 multi-pluck stage에서 활성화 |
| S14 | 후속 구현 | pick single·restrike 통과 뒤 V1.1 strum으로 활성화; monotone/order/span 검사 |
| S15 | 즉시 구현 | event별 early/late window와 target별 offset band를 plan/runtime에 보존 |
| S16 | 즉시 구현 | window 밖 physical release는 detector에는 남고 matcher에서 FP |
| S17 | 즉시 구현 | window close에서 miss/FN을 정확히 한 번 ledger에 기록 |
| S18 | 즉시 구현 | detector output과 goal match 분리; 새 event 없이도 crossing 검출 유지 |
| S19 | 즉시 구현(2차) | sparse core가 먼저 통과한 뒤 potential-based approach를 추가하고 왕복/hover audit |
| S20 | 진단·실험 | 첫 smoke는 event-normalized scalar actor로 시작; 정규화 6채널과 primitive ablation 후 봉인 |

### S21~S30 — reward·안전·curriculum

| ID | 판정 | 구현/검증 제안 |
|---|---|---|
| S21 | 즉시 구현 | event reward ledger에 core/complete/prep/motion/style 절대 누적량을 각각 저장 |
| S22 | 즉시 구현+진단 | next entry gate를 포함한 ready manifold/idle mode는 관측·metric부터; 상수 ready reward 금지 |
| S23 | 진단 우선 | phase·tempo·technique별 qdot/accel/jerk 분포만 기록; 초기 strike reward weight=0 |
| S24 | 공통 통합 | base의 bounded action, EMA, PD clamp, hard joint limit, finite/velocity 종료 그대로 사용 |
| S25 | 진단 우선 | 우손 6줄 reach/strum scripted trajectory로 wrist envelope를 산출한 뒤 hysteresis 후보 결정 |
| S26 | 공통 통합+진단 | `safety.py` 기타 local penetration/swept proxy를 우팔 body list로 확장; 정상 marker crossing whitelist |
| S27 | 진단 우선 | thumb-index 상대 pose·index curl·pick marker drift 기록, grip force reward는 금지 |
| S28 | 진단 우선 | palm/wrist/forearm contact force와 support streak 기록; `G:pluck_range` net force 단독 판정 금지 |
| S29 | 보류 | strike 단독에서는 RH timing만 평가; 좌손 chord-ready 결합은 `task_full.py` 단계로 넘김 |
| S30 | 공통 통합 | fret의 성능기반 curriculum/checkpoint 상태기를 재사용하되 strike stage와 subgroup gate는 별도 정의 |

### S31~S40 — intent·agent·영역·4층 입력

| ID | 판정 | 구현/검증 제안 |
|---|---|---|
| S31 | 즉시 구현 | `requires_rh_attack=unknown`과 `agent=unspecified`를 별도 resolver로 처리하고 provenance 강제 |
| S32 | 후속 구현 | p/i/m/a 역할은 fingerstyle mapper의 soft transition cost로만 사용; hard string 표 금지 |
| S33 | 즉시 구현 | explicit annotation 없는 pinky target을 loader가 거부 |
| S34 | 즉시 구현+후속 | 두 mask 구조는 지금 구현; 실제 손가락 FP는 해당 fingertip detector가 들어오는 V2부터 활성화 |
| S35 | 보류 | hybrid V3 전까지 schema만 보존하고 runtime target은 거부; pick+thumb/index는 영구 invalid |
| S36 | 보류 | nail/flesh는 metadata만 보존; palm mute/slap/tap/rasgueado 입력은 unsupported 오류 |
| S37 | 즉시 구현 | `strike-zone.json`의 finite ribbon과 phrase lane을 detector/mapper의 단일 정본으로 로드 |
| S38 | 진단 우선 | allowed/preferred position quality 기록; GPU 정상 release 분포 전 reward·wrong-zone gate 금지 |
| S39 | 즉시 구현 | SourceNote→Intent→Plan→Runtime 산출물과 각 SHA를 실제 파일로 생성 |
| S40 | 즉시 구현 | attack=false는 target 0개, unknown은 profile 없이 build 실패; false/unknown unit test |

### S41~S50 — setup·motor phase·strum 의미

| ID | 판정 | 구현/검증 제안 |
|---|---|---|
| S41 | 즉시 구현 | episode/phrase `hand_setup=plectrum`을 v1에 봉인; event별 setup 변경 금지 |
| S42 | 즉시 구현+보류 | transition 없는 setup 변경 거부는 지금 구현; 실제 pick regrip motion은 보류 |
| S43 | 즉시 구현 | event FSM, 3-state policy phase, detector state를 서로 다른 tensor/state object로 유지 |
| S44 | 즉시 구현 | pick의 `READY→APPROACH→RELEASE_RECOVER` 전이와 illegal transition metric |
| S45 | 즉시 구현 | 유효 swept crossing의 RELEASE pulse만 matcher에 전달; CONTACT/LOAD는 S0 gate가 아님 |
| S46 | 진단 우선 | ready/approach/release/recovery 3D 영역을 기록하고 contact/load overlay는 후속 진단으로 둠 |
| S47 | 즉시 구현 | control-frame analytic swept interpolation으로 RELEASE를 검출; contact/load 복원은 finger V2 |
| S48 | 후속 구현 | schema/loader mask invariant는 지금 구현, 실제 audible/traversal/muted strum matcher는 V1.1 |
| S49 | 즉시 구현 | mute/span 없는 비연속 single-agent strum은 build/load fail-fast |
| S50 | 후속 구현 | target offset field·검사는 지금 보존, microtiming reward/gate는 strum/multi stage에서 활성화 |

### S51~S60 — coarticulation·감사·사람다움

| ID | 판정 | 구현/검증 제안 |
|---|---|---|
| S51 | 즉시 구현 | phrase lane과 time horizon+next 3 event obs를 v1에 제공; next4~5는 coverage 보고 뒤 결정 |
| S52 | 즉시 구현+보류 | pick/free와 finger free schema는 허용; rest stroke runtime은 landing annotation 전 거부 |
| S53 | 즉시 구현 | detector API에 goal tensor를 전달하지 않는 구조 test; unmatched release는 항상 FP |
| S54 | 즉시 구현 | exclusive physical class와 acoustic/plan confusion matrix를 episode metric에 저장 |
| S55 | 즉시 구현 | potential reset·event 적분 보조항·timestep subdivision invariance audit |
| S56 | 진단 우선 | scripted return dominance와 실제 rollout reward decomposition이 통과할 때만 보조 가중치 유지 |
| S57 | 즉시 구현 | `audit_strike_reward.py`를 PPO 필수 선행 gate로 두고 adversarial trajectory 전수 실행 |
| S58 | 보류 | 정확도 primitive 전에는 Xu motion discriminator 비활성; legacy 27-action checkpoint 직접 로드 금지, 이후 trajectory retarget/phase coverage 감사부터 |
| S59 | 진단 우선 | phase/path/coordination/strum/idle feature를 JSON과 영상 overlay로 저장, 임계값은 reference 뒤 결정 |
| S60 | 공통 통합 | evaluator가 `task_passed`, `kinematic_passed`, `human_like_review_required`를 분리 보고 |

## 5. 첫 구현 범위 — Strike S0

첫 버전에서 모든 주법을 동시에 구현하지 않는다.

```text
profile: pick_only_v1
hand_setup: plectrum
supported event: single pick
direction policy: alternate_v1 — phrase 첫 음 down, 이후 attack event마다 up/down 교대
stroke position: allowed ribbon + phrase lane
detector: swept finite pick crossing and physical re-arm
policy phase: READY→APPROACH→RELEASE_RECOVER
detector state: ARMED→RELEASE pulse→WAIT_REARM→ARMED
optional diagnostics: signed gap/contact-band/depth
reward: normalized one-shot hit/FP/FN + 검증된 뒤의 approach potential
style/motion reward: 0
```

`alternate_v1`은 phrase 시작을 down으로 두고 attack event마다 교대한다. phrase 경계는 explicit annotation
또는 versioned rest threshold로만 만들며, 빌드 때 사용한 threshold를 plan provenance에 저장한다.

현재 source effect가 부족해 `assume_attack_for_unknown=true`를 쓸 수는 있지만 이는 mechanics baseline
가정이다. 사람다운 최종곡 정답으로 승격하지 않는다. S0 곡은 builder coverage report에서 다음 조건을
만족하는 곡을 선택한다.

- open string을 포함해 모든 source note가 보존됨.
- 동시 onset/비연속 chord/unsupported effect가 없거나 명시적으로 제외된 연습 구간.
- 같은 줄 restrike, 인접 이동, string leap가 각각 평가 가능한 수만큼 존재.
- mapper unresolved event 0.

## 6. 구현 단계와 중단 gate

### K-1 — 실행 계약 동결

산출물:

- 이름이 하나뿐인 `StrikePlan` schema와 valid/invalid JSON fixture.
- ordered `RuntimeGoal` field manifest: 의미, shape, normalization, valid mask, 정확한 차원.
- pick S0 detector 수식·경계와 release record, `ARMED/WAIT_REARM` 전이 fixture.
- 겹친 window의 결정론적 일대일 matcher 및 배타적 error precedence fixture.

gate:

- `stroke_direction/free/window_early_frames/...` 등 canonical key가 모든 문서와 fixture에서 동일.
- target마다 `onset_offset_s` 또는 `onset_offset_band_s`가 정확히 하나이고,
  `ordered_targets`는 non-strum `null`/strum 순열로 고정.
- legacy 별칭을 조용히 받지 않고 unknown field/enum을 fail-fast.
- 같은 crossing/event 배열이 언제나 같은 match와 오류 class를 생성.
- CONTACT/LOAD 이력 없이도 S0 조건을 만족한 finite crossing은 RELEASE이고, 근접/hover는 RELEASE가 아님.
- schema와 tensor manifest hash를 checkpoint 계약에 저장할 수 있음.

### K0 — source/compiler

산출물:

- `tab2body/strike_mapper.py`
- `tab2body/tools/build_strike_training_data.py`
- `tab2body/tests/test_strike_contract.py`
- `tab2body/tests/test_strike_mapper.py`

gate:

- note 손실·중복 0, open string 손실 0.
- canonical unit fixture에는 실제 곡 포함 여부와 무관하게 `fret=0` open-string note를 최소 하나 포함.
- upstream ID가 없는 입력도 canonical 원본 순서로 안정적인 `source_note_id`를 만들고 source index를 보존.
- true/false/unknown 전수 보고, 실행 bundle unresolved 0.
- 같은 input/version/config의 plan hash 동일.
- unsupported group/setup/effect가 조용히 통과하지 않음.

### K1 — CPU detector와 matcher

산출물:

- `tab2body/env/strike_detector.py`
- `tab2body/env/strike_goals.py`
- `tab2body/tests/test_strike_detector.py`
- `tab2body/tests/test_strike_contract.py`

gate:

- finite segment 내부/외부, endpoint, parallel, hover, jitter, high-speed sweep 전수 정답.
- goal 유무와 detector output이 동일.
- `ARMED→RELEASE pulse→WAIT_REARM→ARMED` 전이가 정확하고 pulse는 crossing당 한 번뿐.
- CONTACT/LOAD 없이 valid pick crossing 성공, signed-gap 진단 유무에 따른 detector 결과 불변.
- re-arm 전 duplicate 0, re-arm 뒤 restrike 보존.
- 한 crossing 한 class, 한 target 한 crossing.

### K2 — GPU kinematic probe와 안전 진단

산출물:

- `tab2body/tools/probe_strike_runtime.py`
- agent/string/direction/zone별 JSON과 target/actual overlay 이미지 또는 영상.

gate:

- pick×6줄×양방향 positive 100%, scripted negative FP 0.
- control-step/swept interpolation에서 crossing time·order 안정.
- reset overlap·기타 current/swept 관통·nonfinite 0.
- wrist/zone/gate 수치는 이 단계 결과 전에는 hard-coded final 값으로 봉인하지 않음.

### K3 — StrikeTask smoke와 reward audit

산출물:

- `rewards/strike.py`, `tasks/task_strike.py`
- `tests/test_strike_control_contract.py`
- `tools/audit_strike_reward.py`

gate:

- exact RH control DOF 이름/순서와 action count 봉인.
- 폐기된 pilot 당시 obs field 순서, event FSM·4-state policy phase·detector state의 독립성,
  terminal info, auto-reset PASS. 현재 실행 정본은 3-state policy phase다.
- exact hit가 do-nothing/hover/jitter/wrong+correct/전줄 sweep보다 높은 event return.
- rest 길이·target 수·timestep 변화에 event 최대 return 안정.
- 이 gate 전에는 PPO 금지.

### K3.5 — strike 학습 배관 통합

산출물:

- strike cfg와 task registry/train 분기.
- task-aware run/checkpoint naming, evaluator와 rollout recorder.
- strike curriculum state 및 checkpoint contract 검사.

gate:

- `task=strike`, 우측 30 DOF 이름/순서, StrikePlan/RuntimeGoal manifest와 reward variant가 저장됨.
- fret run/checkpoint/output과 경로가 섞이지 않고 legacy 27-action RH checkpoint 직접 로드를 거부.
- 새 strike checkpoint save와 deterministic evaluation/recording smoke PASS; resume은 별도 검사 대기.
- 이 gate 전에는 장시간 PPO 금지.

### K4 — pick single PPO

순서:

```text
dynamic ready/reach → untimed release → timed single → same-string restrike
→ adjacent/leap transition → source-song coverage → integration → full song
```

각 승급에서 줄·방향·IOI subgroup recall, FP/duplicate, timing, 안전을 따로 본다. 평균만 통과하고 특정 줄이나
방향이 실패하면 승급하지 않는다.

### K5 — pick strum

audible/traversal/muted mask, target별 microtiming, monotone sweep와 field 밖 reversal을 활성화한다. single과
restrike gate를 다시 통과해야 한다.

### K6 — fingerstyle

p/i/m/a detector를 한 agent씩 추가해 single→교대→multi-pluck 순서로 진행한다. free stroke만 지원하고
rest stroke·rasgueado는 계속 거부한다.

### K7 — hybrid와 style

pick+m/a를 추가하고 정확도·간섭 gate를 통과한 뒤에만 technique-conditioned style prior를 실험한다.
Xu reference는 scale/strum seed일 뿐 fingerstyle·전신 팔의 최종 human-like 기준이 아니다.

## 7. 진단값 승격 규칙

`진단 → soft reward → task/hard gate` 승격에는 다음 증거가 모두 필요하다.

1. CPU scripted positive/negative 분리.
2. GPU 정상/오류 trajectory의 분포 margin.
3. 정상 정책 3 seed에서 p95/p99와 영상 일치.
4. soft reward를 켜도 core 정확도·timing·안전 회귀 없음.
5. adversarial return audit 통과.
6. 문서·config·checkpoint contract version 갱신.

손목 box·zone edge·jerk·pick grip·support force·3D corridor·자연스러움 feature는 이 절차 전에는 hard
종료나 최종 통과조건으로 사용하지 않는다.

## 8. 지금 보류하는 항목

- 실제 pick grasp force·pick blade orientation·edge/slant.
- nail/flesh 음색과 실제 string force/진동.
- rest stroke, palm mute, slap, tap, rasgueado.
- phrase 중 pick을 잡거나 놓는 regrip motion.
- full의 좌손 chord-ready/음향 동시성.
- 정확도 primitive 전 style discriminator.
- 전신·fingerstyle reference 없는 human-like 최종 선언.

## 9. 다음 착수 제안

다음 작업은 K-1 계약 동결만 수행한다. `task_strike.py`나 PPO부터 만들지 않는다.

1. StrikePlan key/enum/schedule을 하나의 schema와 valid/invalid fixture로 봉인한다.
2. RuntimeGoal field 순서·정규화·정확한 차원 manifest를 봉인한다.
3. swept RELEASE/re-arm과 겹친 window matcher/error precedence fixture를 확정한다.
4. 그 계약을 사람이 읽는 예시로 확인한 뒤 K0 source/compiler로 넘어간다.

이 순서가 fret에서 `presses → goal contract → 기하 판정 → GPU probe → PPO`로 진행하며 얻은 가장 중요한
교훈을 strike에 그대로 적용한 형태다.
