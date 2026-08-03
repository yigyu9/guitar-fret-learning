# PROJECT_CONTEXT — 오디오 기반 전신 기타 연주 모션 생성 (핸드오프 문서)

> **어떤 AI 어시스턴트든(Claude/Gemini/GPT/기타) 새 세션은 이 문서부터 읽는다.**
> 이 문서는 상태, 결정, 함정과 실행 방법을 모은 부트스트랩 문서다.
> 삭제된 과거 문서의 결정은 §3과 태스크별 문서가 승계한다.
> 코드 트랙 정본은 `tab2fingermapping/chordtrack/REPORT.md`와 `fingermapping/ALGORITHM.md`다.
> **작업 규칙: 의미 있는 변경 후에는 이 문서의 §2(상태)를 갱신할 것.**
> 최종 갱신: 2026-08-03

## 0. 새 세션 시작 프롬프트 (사용자용 템플릿)

```
프로젝트 루트의 연구를 이어간다.
1. README.md(디렉토리 지도) → PROJECT_CONTEXT.md 순서로 읽어라.
2. 오늘 작업: [§2의 '다음 작업'에서 지정].
3. 규칙: §3 결정 로그는 사용자 승인 없이 변경 금지, §4 함정 준수, 실측 검증 없이 완료 선언 금지.
4. 작업 후 이 문서 §2 상태 스냅샷 갱신.
```
웹 챗(파일 접근 없음): 이 문서 전문 + 관련 코드 조각을 붙여넣고 위 2~3번을 지정.
웹 챗은 설계 토론·리뷰용으로만 — 구현·검증은 실행 가능한 도구에서.

## 1. 연구 한 줄

오디오 단독 입력 → Conformer 전사(tablature) → 물리 RL(Isaac Gym) → **전신** 기타 연주 모션.
노벨티 = 전신 + 물리 시뮬레이션 + 오디오 단독의 조합(선행: Xu SA'24=손만, ELGAR=물리 없음).
스타일은 참조 모션 추적이 아니라 discriminator 분포 모방(AMP/ICCGAN) — `docs/style-learning-explained.md`.

## 2. 현재 상태 스냅샷 (2026-08-03)

- **[2026-08-03] Fret 현재 호환 계약·실행**: 현재 정책은 **33 action / 353 observation / 6 reward-value**다.
  관측은 `base 180 + goal 128 + prev_action 33 + thumb geometry 12`로 구성한다. 호환 실행은
  `fret/training/runs/20260803_1327_02_Jazz1-200-B_solo`와
  `fret/training/runs/20260803_1352_02_Jazz1-200-B_solo`이며 각각 1,024 환경·500 iteration이다.
  구 `341 observation`·`37-action` checkpoint는 재개·평가하지 않는다. 현재 실행·smoke·평가 명령은
  `tab2body/TRAINING.md`와 `fret/training/README.md`를 정본으로 삼는다.

- **[2026-07-27] 새 strike A0~A4 환경 구현·검증**:
  입력 정본은 `tab2body.strike_training.v1`의 `[time, frame, string]`이며 time을 기준으로
  60 fps frame을 ±0.5 frame 안에서 검증한다. 제어는 우측 어깨 3+팔꿈치 3+손목 3+
  오른손 21 = **30 DOF**, actor 관측은 **263차원**으로 봉인했다. 줄은 기타 body marker에서
  읽은 고정 선분이고, 피크는 `RH:pick`에 고정된 질량 없는 기준점이다. 성공은 접촉이 아니라
  유한 선분을 올바른 방향·속도·깊이로 통과한 직후의 one-shot RELEASE 사건이다.
  학습은 `A0_PICK_GRIP → A1_TIP_READY → A2_FREE_CROSSING → A3_TIMED_CROSSING →
  A4_ZONE_CONTROL` 순서이며, A3 timing tolerance는 성능 gate를 연속 통과할 때
  **100→67→50 ms**로 줄어든다. A4는 전체 goal 시간축과
  allowed y `[-0.385,-0.255]m`, preferred y `[-0.355,-0.295]m` 안의 lane sampling을 쓴다.
  sampled lane은 `±6mm` 만점·`±12.5mm` 성공 경계의 띠다. A1~A4 승급은 완료 episode의
  exact 지표만 쓰고, 무episode rollout은 streak을 유지한다. timing p95에는 tolerance/zone gate
  전의 유효 target crossing 전체가 들어간다. 전체곡은 첫 event 30 frame 전부터 시작한다.
  GPU runtime audit는 6환경·5단계에서 finite action/observation/reward와 기타 충돌 필터,
  6줄 간격·영역을 통과했다. 학습/평가 코드는 checkpoint contract·resume curriculum state,
  task RNG, JSONL log·평가 JSON·분석 MD·학습 plot·remembered/current 두 MP4를 저장한다.
  최종 8-env PPO→checkpoint→재평가와 1600×900 이중 영상 생성까지 실제로 통과했다.
  정본 설명은 `strike/README.md`, `strike/03_training/README.md`; fret/strike 공용 실행
  진입점은 `python -m tab2body.train --task strike`다. 공용 진입점은 태스크만 선택하며
  `train_fret.py`와 `train_strike.py`가 동일한 `build_parser()`·`main()` runner 계약을
  구현한다. 이 구조 변경 전 checkpoint는 구현 지문 불일치로 resume하지 않는다.
- **[2026-07-29] guitar reference 기반 A0_PICK_GRIP 자세 선정·Isaac 렌더**:
  `related_work/guitar/assets/motions/scale.json`의 실제 대표 frame 2227에서 오른손
  local quaternion과 현재 21-DOF 축 target을 추출했다. 새 strike의 첫 단계는 타현 전
  엄지·검지 pinch-like pose와 나머지 손가락의 자연스러운 굽힘을 만드는
  `A0_PICK_GRIP`으로 제안한다. 정본 수치·보상 계약은
  `docs/2026-07-29/pick_grip_pose_from_guitar_research.txt`에 기록했다.
  `tab2body/tools/render_pick_grip_pose.py`는 seated 기본자세의 나머지 84 DOF를 유지하고
  `RH:*` 21 DOF만 교체해 GPU PhysX/GPU pipeline에서 렌더한다. 결과는 같은 문서 폴더의
  `pick_grip_pose_isaac_gym_{remembered,current}.png`와 검증 JSON이다. 오른손 target
  최대 오차는 6.08e-6 rad, 비-RH 기본자세 최대 변화는 0.001926 rad였다.
- **[2026-07-27, 역사] 기존 strike 환경 제거 후 새 설계로 전환**:
  사용자 결정으로 `train_strike.py`, StrikeTask, strike goal/detector/reward/mapper, 설정,
  registry, 관련 도구·검사, 생성 contract/manifest/diagnostics, checkpoint/eval/plot을 제거했다.
  규칙·연구 문서와 500회 pilot의 `logs/`, 두 결과 `videos/`만 보존한다. 공용 PPO의 reusable
  observation buffer snapshot 수정은 fret에도 필요한 정확성 수정이라 유지한다. 아래의 strike
  구현·카메라·smoke 기록은 삭제 전 역사이며, 바로 위의 새 A0~A4 계약이 현재 정본이다.
- **[2026-07-27] strike 카메라 2개 동결 및 자동 이중 녹화**:
  사용자 선택 기준은 `remembered`(0.7m, world direction `[0.15,0.85,0.62]`)와
  `current`(같은 목표점·거리·높이에서 오른쪽 70도, `[-0.7474,0.4317,0.62]`) 두 개뿐이다.
  실행 정본은 `tab2body/tools/record_strike_rollout.py`의 동결 상수이며, 자세 정본 이미지는
  `docs/2026-07-29/pick_grip_pose_isaac_gym_{remembered,current}.png` 두 개뿐이다.
  strike 학습 정상 종료 시 동일 deterministic rollout을
  `*_rollout_remembered.mp4`, `*_rollout_current.mp4`로 자동 저장하고 eval/final artifact JSON에
  두 경로와 카메라 계약을 기록한다. 최종 8-env×1-iteration, 4-step GPU smoke checkpoint를
  다시 평가해 두 H.264 1600×900@30fps, 60-frame MP4와 manifest 등록을 확인했다.
- **[2026-07-23] `tab2body/tools` 정리**: 실행 명령과 회귀 검사가 섞여 있던 구조를 정리해
  30개 `test_*.py`를 `tab2body/tests/`로 이동하고 README 인덱스를 각각 추가했다. 재생성 가능한
  `tools/__pycache__`를 제거했다. 실제 Isaac `render_strike_zone_isaac.py`가 승계한 비-Isaac
  `render_strike_zone_environment.py`와 그 PNG/JSON, 현재 R13 world-direction 진단으로 승계되어
  산출물도 없던 `render_palm_neck_direction.py`를 제거했다. 데이터 builder, 학습 plot/recorder,
  현재 환경 renderer, runtime audit와 회귀 검사는 asset·threshold·checkpoint 변경 시 다시 필요하므로
  유지했다.
- **[2026-07-23] strike 학습 종료 자동 산출물 + 8-env GPU PPO smoke PASS**:
  `train_strike.py`의 package import와 `cfg.STRIKE.reset_noise` 계약을 수정해
  RTX 4070 Ti / GPU PhysX / GPU pipeline에서 8환경×1 iteration(32 samples)을 실행했다.
  30 action, 806 observation과 finite rollout/update, `strike_000001.pt` 저장을 확인했다.
  PPO `metrics.jsonl`에는 target hit/wrong/miss/RELEASE 수와 hit timing, release speed/depth/zone
  분포를 추가했다. 정상 학습 종료 뒤 `plot_strike_training.py`와
  `record_strike_rollout.py`가 자동으로 training curve PNG, live strike overlay가 있는 deterministic
  Isaac MP4, TP/FP/FN·F1·종료·운동분포 eval JSON, 사람이 읽는 analysis MD를 만들고
  `final_artifacts.json`에 전 경로/오류를 기록한다. smoke는 12-step cap이라 F1=0이며 성능 증거가
  아니라 저장 배관 증거다. resume과 scripted 6줄·양방향 GPU detector probe, 장시간 PPO는 남아 있다.
- **[2026-07-23] 기타 기준 strike 영역을 실제 Isaac Gym StrikeTask에서 시각화**:
  `render_strike_zone_isaac.py`가 1-env `StrikeTask`를 cuda:0 GPU PhysX/GPU pipeline으로 실행하고
  Isaac camera sensor 장면을 캡처했다. `strike_visualization.py`는 캡처 프레임의 라이브
  `G:string1..6`/`G:string*_end` rigid body, `guitar_frame()`, `RH:pick`을 읽어 allowed/preferred
  ribbon을 투영한다. 결과는 `strike/renders/strike_zone_isaac_gym.png`, 라이브 월드 좌표·camera
  extrinsic 보고서는 `strike/diagnostics/strike_zone_isaac_gym.json`이다. 앞서 만든 비-Isaac
  Matplotlib 환경 대체 도식과 생성기는 tools 정리 때 제거했다. allowed
  `y_g=[-0.385,-0.255] m`(130mm), preferred
  `[-0.355,-0.295] m`(60mm)는 실제 현에 맞췄고, x 반폭 2mm·z 접근 3~25mm·pick depth 1mm는 후보로
  유지한다.
- **[2026-07-23] strike 제어 범위를 오른쪽 어깨 이하로 확정**: 사용자 결정에 따라 strike action에서
  `R_Thorax` 3 DOF를 제외하고 `R_Shoulder/R_Elbow/R_Wrist` 9 + `RH:*` 21 = **30 action**으로
  변경했다. `R_Thorax`는 seated init PD로 유지한다. base183과 goal593은 그대로이고 actuator
  observation이 33→30으로 줄어 전체 observation은 **806**이다. `StrikeTask`가 30/806을 fail-fast하며
  `test_strike_control_contract.py`가 실제 MJCF에서 shoulder3+elbow3+wrist3+hand21과
  `R_Thorax` 제외를 검사한다. checkpoint ordered DOF/model shape가 바뀌므로 이전 33-action strike
  checkpoint와는 호환하지 않는다.
- **[2026-07-23] strike S0 K-1~K3 1차 구현·CPU 검증 완료, 기본 GPU smoke PASS**:
  `strike_contract.py`가 `tab2body.strike-plan.v1`과 exact 593D RuntimeGoal manifest를 봉인했다.
  current/+0.10s/+0.25s/next1~3, agent·phase·detector state를 포함하며 4,096환경 CPU tensor
  rasterization은 1회 약 7.99ms였다. `strike_mapper.py`와 builder는 fingering `notes[]` 전수를
  SourceNote→Intent→Plan으로 바꾸고 CSV 0=low-E를 Isaac 5=low-E로 한 번만 변환한다. unknown attack은
  명시 `assume_attack_for_unknown` 없이는 실패하고, 합성 open-string/legato fixture와 실제 Jazz
  42-note 입력을 통과했다. 실제 plan을 두 번 생성한 파일 SHA-256은
  `50706e1bf8238d2c958131eb0011b50d08197f0f02307bfbd5809cb36a6fba94`로 동일하다.
  `env/strike_detector.py`는 finite swept crossing, 속도/깊이, zone quality와
  ARMED/WAIT_REARM을 구현했고, `strike_goals.py`는 one-shot matcher와 배타적 오류 class를 구현했다.
  CPU 검사는 mapper/detector/contract 모두 Python 3.8과 기본 환경에서 PASS했다.
  `StrikeTask`는 `R_Shoulder` 이하 우측 30 DOF, 806 observation(base183+goal593+EMA30),
  `RH:pick`, 실제 6 string
  marker, GPU tensor detector,
  event/timing/corridor/economy 4-value reward를 연결했다. corridor는 frame마다 양의 quality를 주지
  않고 signed potential 변화량을 써 hover 누적을 막고, zone은 정확한 hit에서만 one-shot 지급한다.
  CPU adversarial audit은 exact 1.019 > hover .120 > do-nothing 0, jitter −.068, wrong-only −.193을
  통과했으며 결과는 `strike/diagnostics/k3_reward_adversarial_audit.json`이다. `cfg.STRIKE`와
  `train_strike.py`는 single_release→alternate_pair→phrase→full_song curriculum과 strike checkpoint
  계약/이름을 제공한다. `strike/renders/k2_release_detector.png`,
  `k2_real_plan_timeline.png`, `k2_release_rearm.mp4`와
  `strike/diagnostics/k2_synthetic_detector.json`을 생성했으며 애니메이션은 S2 down/up을 각각 한 번
  검출했다. 기본 sandbox에서는 CUDA/NVML이 보이지 않지만 승인된 GPU 실행과 Guitar 환경 Ninja로
  task step, 8-env PPO smoke, checkpoint save와 자동 deterministic recording을 통과했다.
  checkpoint resume은 미검증이다. speed 0.05m/s, depth 1mm, re-arm 3mm/2frame,
  zone 값은 GPU 분포 전까지 후보 진단값이다. async reset의 stale body로 생기는 가짜 crossing을 막기
  위해 S0는 `reset_noise=0`을 강제하고 settled pick/body snapshot을 재사용한다. noisy RSI는 matching
  FK cache 이후로 보류한다. v1은 single만 실행하고 strum/multi/fingerstyle/hybrid는 fail-fast 또는
  보류한다.
- **[2026-07-23] strike phase 단순화·legacy guitar 감사·구현 전 gate 보강**: marker 기반 pick S0의
  정책 운동 phase를 `READY→APPROACH→RELEASE→RECOVER` 네 단계로 줄였다. 중복 방지 물리 detector는
  별도 `(agent,string)` 상태인 `ARMED→RELEASE pulse→WAIT_REARM→ARMED`로 관리한다. 탄성이 없는
  `RH:pick`/string marker에서는 CONTACT/LOAD를 성공 조건으로 요구하지 않고 signed-gap 진단 또는
  fingerstyle/물리 pick 후속 계약으로만 보존한다. `related_work/guitar`를 소스까지 감사한 결과 기존
  연구도 index2 아래의 질량·geom·독립 DOF 없는 pick marker와 이전→현재 swept crossing을 썼음을
  확인했다. 이 아이디어는 채택하되 finite string `s` 경계, 방향, 최소 횡속도, zone, re-arm,
  detector/matcher 분리를 보강한다. legacy의 free-wrist 6+손 21=27 action checkpoint는 현재 우팔/손
  30-action 정책에 직접 로드하지 않고 retarget된 trajectory teacher·hand-pose seed로만 검토한다.
  scale/strum 모션은 pick-tip/crossing/onset/RELEASE 라벨이 없어 detector oracle로 쓰지 않는다.
  구현 순서 앞에 StrikePlan schema·RuntimeGoal tensor·matcher/error precedence·detector fixture를 봉인하는
  K-1을, task smoke 뒤에는 strike cfg/registry/checkpoint/evaluator를 잇는 K3.5를 추가했다. 상세 근거는
  `strike/90_references/LEGACY_GUITAR_PICK_ANALYSIS.md`다. 사람이 먼저 읽는 축약본은
  `strike/QUICK_RULES.md`에 둔다.
- **[2026-07-22] 오른손 strike 규칙 v3 — raw/intent/plan 분리와 사람다운 운동 계약 확장**: 기존 Xu
  이식 초안을 구현 정본으로 바로 쓰지 않고 `SourceNote → StrikeIntent → phrase-level StrikePlan →
  RuntimeGoal`로 분리했다. `notes.t_on`은 sound-onset 후보이며 항상 오른손 공격은 아니다.
  tied/hammer/pull 등의 `requires_rh_attack=false`와 정보 부족 `unknown`을 구분하고, 개방현을 누락하는
  `presses[].strikes`는 fretted-note 감사 projection으로만 쓴다. 정책에는 raw를 직접 넣지 않고 mapper가
  `plectrum/fingerstyle/hybrid` setup, target별 `pick/thumb/index/middle/ring/pinky`, 방향, free stroke,
  audible/traversal/muted mask, microtiming, phrase lane과 다음 event 관계를 해결한 plan을 준다. pick을 쥔
  thumb/index의 동시 finger target과 transition 없는 regrip은 금지한다. 음악 event FSM과 별도로
  `READY→APPROACH→RELEASE→RECOVER` 정책 phase를 두고, detector는 goal과 무관하게 모든
  release/crossing을 낸 뒤 matcher가 일대일 배정한다. re-arm은 `(agent,string)`별
  `ARMED→RELEASE pulse→WAIT_REARM→ARMED`와 물리 separation/time으로만 결정해 rest 오타가 숨지 않게
  했다. pick은 swept point, 손가락은 후속 V2의 `*3→*_top` swept fingertip pad와
  **유한** string segment로 판정한다. strike 위치는 실제 6개 string을 guitar-local y로 clip한 ribbon이며,
  allowed `[-0.385,-0.255]m`(130mm), preferred `[-0.355,-0.295]m`(60mm)다.
  `strike/renders/strike_zone_reference.png`로 실제 asset endpoint·기존 box·position-quality를 시각화했다.
  6줄 보상은 진단/critic 후보로 남기고 event-normalized actor와 primitive ablation 후 봉인한다. 모든
  auxiliary는 event 적분 return으로 core보다 작은지 do-nothing/hover/jitter/전줄 sweep/zig-zag 등
  adversarial audit를 통과해야 한다. Xu RH scale/strum prior는 pick/strum 시작점일 뿐 전신 팔과
  fingerstyle 인간 분포의 증거가 아니므로, reference가 없는 주법은 “안전하고 운동학적으로 타당한 virtual
  strike”까지만 주장한다. 이 문서 작성 당시 Python task 파일은 빈 스텁이었고, 현재 구현 상태는 바로
  위 2026-07-23 S0 구현 항목이 승계한다. detector 수치·우손 안전 박스·actor reward
  variant·technique별 reference는 여전히 GPU 실측 대상으로 남는다.
- **[2026-07-22] strike 규칙별 구현 판정표 작성**: `strike/IMPLEMENTATION_CHECKLIST.md`에서 S1~S60을
  즉시 구현·후속 구현·공통 통합·진단 우선·보류로 하나씩 분류했다. 규칙마다 reward를 만들지 않고
  Source/Mapper, Goal/Observation, Detector/Re-arm, Matcher/Task/Metrics, Reward/Audit, Safety,
  Curriculum/Style의 7개 구현 단위로 합친다. 검증된 846줄 fret `goals.py`에 strike를 덧붙이지 않고
  `strike_goals.py`를 별도로 만들며, 실제 중복 helper만 나중에 공통화한다. 첫 범위는
  `pick_only_v1 + alternate_v1 + single pick`이고 style/motion reward는 0이다. K-1 contract freeze →
  K0 source/compiler → K1 CPU detector/matcher → K2 GPU kinematic probe → K3 task smoke/reward audit →
  K3.5 strike 학습 배관을 모두 통과하기 전 PPO를 시작하지 않는다. 이후 K4 pick single, K5 strum,
  K6 fingerstyle, K7 hybrid/style 순서다. 진단값은
  CPU/GPU 분리·3 seed rollout·정확도 무회귀·adversarial return 감사를 통과한 뒤에만 soft/hard 규칙으로
  승격한다.
- **[2026-07-22] 과거 5,000회 fret 학습**: 당시 1,024환경·163,840,000 samples에서 F1 0.598,
  압현 성공률 0.432, NO_PRESS 0.915, 오압현율 0.0536을 기록했다. 실행 산출물은 정리되어
  현재 경로로 제공되지 않으며, 이 수치는 353D 계약의 공식 성능이 아닌 역사적 비교 기준이다.
- **[2026-07-22] fret 학습 코드 무동작변경 정리**: `env/rewards/fret.py`에서 사용되지 않던
  점-선분 기하 함수 2개를 제거하고, 지정 손가락 표본 선택·손끝/바레 허용 표본·압현 hysteresis의
  중복 계산을 공용 경로로 합쳤다. `env/tasks/task_fret.py`에서는 이미 모든 태스크가 제공하는
  `termination_reasons()`의 구버전 호환 분기를 제거하고, 활성 줄 진단 평균 계산을 하나로 통합했다.
  두 파일은 합계 65줄 줄었으며 보상·판정·관측 계약은 유지된다. 관련 CPU 단위검사 11종과
  GPU PhysX episode/auto-reset 통합검사를 통과했다.
- **[2026-07-21] R7/R8 최소 안전 종료 구현**: R7은 손목 중심이 기타 로컬 고정 박스
  `(-.20,-.35,-.30)..(.30,.35,.25)m` 밖에, R8은 비엄지 네 손가락 중심선 샘플의 25% 이상이
  `z<-50mm` 뒤에 각각 3프레임 연속 있을 때 조기 종료한다. R8의 25% 조건은 정상 초기 소지의 단일
  끝점 돌출(최대 샘플 비율 13.3%) 오탐을 막으면서 평면은 유지한다. CPU 경계 검사, 각 조건 강제 GPU
  `done=True`, 정상 1초 준비 자세, 8-env PPO smoke가 모두 통과했다. 이 과정에서 `reset_idx()`가
  반환 직전 `done`을 함께 0으로 지우던 기존 alias 문제도 수정해 모든 태스크 종료가 PPO에 보존된다.
- **[2026-07-21] R29 첫 goal 1초 준비 clock 구현**: reset 후 선택된 시작 goal(frame0 또는 RSI frame)을
  60프레임 동안 고정한다. 정책은 당시 341D 관측과 R1/R2·손목·엄지 등 전체 보상을 받아 실제로 접근하고
  압현할 수 있지만 F1·NO_PRESS·R27 성공 통계와 goal frame 진행은 준비 종료 뒤 시작한다. 관통·손바닥
  등 안전규칙은 준비 중에도 유지한다. 마지막 원곡 frame을 빠뜨리던 종료 off-by-one도 함께 수정해
  episode는 준비60+원곡861=921 control frame이다. checkpoint에 준비 길이를 저장하고 다른 길이 resume를
  거부하며, rollout 영상의 오디오는 준비시간만큼 offset한다. 2-env 전용 clock 검사, 8-env PPO smoke,
  1-env 921프레임 전체 평가 배관 PASS; 평가 JSON에 준비 60프레임/1초가 기록됨을 확인했다.
- **[2026-07-21] R28 MOVE 중 pressed-drag 진단 구현**: 이전 목표 relation이 MOVE이고 손가락
  mask/fret이 바뀐 뒤 다음 목표 PRESS 성공 전까지 fingertip 기타 로컬 x/y 이동을 추적한다. 같은
  실제 string/fret 압현 셀이 연속 제어 프레임에서 유지된 이동만 confirmed distance로 누적하며,
  양 끝의 임의 접촉만 확인되는 경우는 lift/repress 가능성이 있어 candidate로 분리한다. move 시작·완료,
  두 거리·프레임·confirmed 누적 3mm 초과 pulse를 info와 `tools/audit_r28_runtime.py`에 기록한다.
  CPU 압현-drag/정상 lift 분리 검사, 8-env GPU PPO smoke, 8-env×120프레임 진단 도구 실행 PASS.
  초기 자세 유지 실행은 MOVE 시작 검출 index8/ring16, 실제 압현이 없어 candidate/confirmed 0으로
  예상대로 나왔다. 보상·종료·최종 통과조건에는 영향이 없다.
- **[2026-07-21] R27 PRESS 이벤트 지속 안정성 구현**: 동일 줄에서 fret·지정 손가락이 유지되는
  연속 PRESS run을 이벤트로 래스터화한다. 충분히 긴 음은 attack/release 각 3프레임(50ms)을 평가에서
  제외하고 짧은 음은 전체를 보존한다. 이벤트별 유지율·최장 연속 성공·최장 이탈·중단 횟수를 GPU에서
  누적하며, 유지율≥90%이고 연속 이탈≤3프레임이어야 성공이다. 모든 이벤트 성공을 최종 `passed`에
  포함하되 기존 프레임 보상과 중복되는 새 reward는 추가하지 않았다.
- **[2026-07-21] 연구 방향·R26을 곡별 반복 최적화로 교정**: 목표는 여러 곡으로 범용 정책을 사전학습해
  새 곡을 zero-shot 생성하는 것이 아니다. 곡 하나의 tablature/finger mapping/60Hz goal에 정책 하나를
  귀속시키고, 동일 곡을 많은 episode 동안 반복해 정확하고 자연스러운 모션을 얻는다. 모든 규칙과 원곡
  goal은 처음부터 유지하며, reset 시작 분포만 coverage 1,000회(random 100%) → integration 1,000회
  (100→0%) → full-song(frame 0)으로 바꾸는 `learning/curriculum.py`를 구현했다. 곡 ID·goal SHA-256·
  hand target·단계를 checkpoint에 저장하고 다른 곡 resume를 거부한다. custom goal은 같은 이름 hand
  target과 곡별 output dir를 자동 탐색한다. 데이터 builder도 실제 guitar fret y에서 곡별 wrist target을
  함께 생성한다. 반복되는 동일 운지 구간을 MLP가 구분하도록 정규화 곡 진행률 1D를 추가했다. 현재 계약은
  당시 `base=180, goal=128, actuator(prev_action)=33, obs=341`이었다. 이후 thumb geometry 12D가 추가되어
  현재 `obs=353`이다. 체크포인트는 goal·hand-target뿐 아니라
  모델/제어/보상/PPO/자산/구현 전체 계약을 봉인하며 legacy 또는 불일치 재개를 거부한다.
  CPU schedule/timeline/phase 검사와 당시 8-env GPU PPO(`obs=341`) 및 전체곡 평가 배관 PASS.
- **[2026-07-21] 전체곡 평가를 정확도·최소안전·자연스러움 진단으로 분리**: `passed`는 더 이상 F1만
  보지 않고 F1≥0.9와 관통 임계, tunneling·초기 overlap·관통/손바닥/손목 비정상 종료 0을 함께 요구한다.
  R18 hover, R23 slip, R22 손가락 겹침, R24 접촉력·토크 분포도 평가 JSON에 집계한다. 이 네 진단은
  정상 학습 정책 분포로 임계값을 보정하기 전까지 통과조건으로 꾸미지 않고
  `naturalness_review_required=true`와 rollout 영상 검토를 명시한다.
- **[2026-07-21] R24 과압·비정상 지지 진단 구현**: 보상·종료 없이 다섯 손가락 distal/middle/proximal,
  손바닥·손목·팔꿈치의 rigid-body net force, target/inactive distal 힘, 33 제어관절 실제 적용 토크와 cap
  비율을 info에 기록한다. net force는 접촉 상대를 식별하지 못한다는 caveat를 보고서에 명시한다.
  `tools/audit_r24_runtime.py`는 선택적 checkpoint rollout의 평균·p50/p95/p99/max와 body/DOF 순서를
  JSON으로 출력·저장한다. 초기 자세 8-env×120스텝에서 접촉력 0, 모든 값 finite, 최대 토크 cap 비율
  0.732였으며 이를 과압 임계값으로 쓰지 않는다.
- **[2026-07-21] R23 PRESS/HOLD 접선 slip 약한 감점 구현**: 같은 손가락의 string mask·fret이 유지되고
  지정된 모든 줄의 실제 PRESS가 3프레임 연속 성공하면 fingertip의 기타 로컬 x/y anchor를 잡는다.
  누적 2mm는 자유, 초과분은 3mm scale Gaussian으로 낮추며 전체 0.5%다. 목표 변경·접촉 실패·release는
  anchor를 즉시 초기화해 MOVE를 방해하지 않는다. 순간/누적 slip·gate·streak info를 추가했고 CPU 경계
  검사와 8-env GPU PPO smoke(곡 진행률 추가 전 `obs=307`) PASS.
- **[2026-07-21] R22 손가락 상호관통 진단 구현**: self-collision이나 보상/종료는 켜지 않고, 엄지를
  포함한 다섯 손가락의 3개 마디를 6mm capsule로 근사해 10개 쌍의 정확한 segment distance를 매 프레임
  계산한다. 2mm 초과 proxy 겹침의 쌍별 깊이·표면 간격·쌍 수·streak·초기겹침을 info에 기록하고
  `tools/audit_r22_runtime.py`로 집계한다. CPU 교차/평행/끝점/배치 검사 PASS. 초기 자세 8-env×120스텝은
  전 쌍 관통 0, 초기겹침 0이며 정상 학습 rollout 분포 전까지 진단 전용이다.
- **[2026-07-21] R18 약한 release-hover 보상 구현**: 실제 PRESS에 성공한 뒤 현재 비활성인 손가락만
  추적한다. fingertip pad 표면에서 가장 가까운 실제 string segment까지 30mm는 자유, 초과분은 40mm
  scale Gaussian으로 완만히 낮추며 전체 보상 0.5%다. 현재 압현/미사용 손가락은 제외하고 lateral MOVE와
  종료에는 관여하지 않는다. CPU 경계 사례와 8-env GPU PPO smoke(곡 진행률 추가 전 `obs=307`) PASS.
- **[2026-07-21] R15 손가락별 13D next-goal 관측 구현·전수 검증**: raw event가 아니라 정제된 60Hz
  `fret_goal/finger_goal`에서 각 손가락의 `[next_string_mask(6),next_fret,dt_next_goal,next_valid,
  dt_current_change,KEEP,MOVE,REST]`를 만든다. 동일 프렛의 겹친 줄은 mask로 합쳐 바레 확장을 지원하고,
  한 손가락의 동시 다중 프렛은 즉시 오류로 막는다. 4손가락 52D를 기존 goal75D에 붙여 goal127D,
  전체 obs307D다. S0 861프레임×4손가락=3,444개 벡터(44,772값)를 전수 검사해 finite·binary mask·
  valid·시간 범위·관계 one-hot을 모두 통과했다. 다중 줄은 105 finger-frame(전부 동일 프렛·연속 줄,
  현 데이터에서는 암묵 바레)이며 모호한 다중 프렛은 0이다. 합성 전환 검사와 8-env GPU PPO smoke
  당시 `obs=307`도 통과했다. 이후 곡 진행률 1D와 EMA actuator state 33D를 더해 당시 obs는 341이었으며,
  이 관측 변경들은 기존 checkpoint 입력층과 호환되지 않는다.
- **[2026-07-21] 왼손 fret 규칙 통합(R1~R29)**: 팀원 기타 규칙에서 왼손 압현에 해당하는 내용만
  기존 정본 `docs/plans/task_fret_design.md`에 병합했다. PRESS/NO_PRESS/DONT_CARE, 압점, 엄지,
  손목·손바닥, 근위 관절 우선순위, 타이밍, 관통은 기존 규칙에 흡수했다. 새 항목은 R21 전 관절
  hard/soft range, R22 손가락 상호관통·방해, R23 HOLD 접선 slip, R24 과압·비정상 지지,
  R25 ChordReady 연속 유지, R26 단계별 커리큘럼이며 후속 R27은 PRESS 이벤트 지속 평가다.
  새 자연스러움/접촉 규칙은 정상 정책 분포가
  없으므로 보류·진단으로 분류했다. 팀 초안의 좌표축은 실제 에셋과 달라 프로젝트 정본을
  `+x=6번줄→1번줄, +y=브리지→너트, +z=지판 바깥쪽`으로 명시했다.
- **[2026-07-21] R11 상체 붕괴 단기 점검**: 현재 33-action 설정으로 8환경×5 일반 PPO update
  (1,280 samples)를 새로 학습하고 861 simulation frame(14.37초) 전체 곡을 상체 시점으로 녹화했다.
  `fret/renders/r11_upperbody_probe_5iter.mp4`와 3초 간격 contact sheet에서 뒤로 꺾이는 누적 붕괴는
  관찰되지 않았다. 비제어 몸통·머리 DOF 최대 2.25°/RMS 0.93°, 우측 최대 1.32°/RMS 0.27°,
  제어 L_Thorax 최대 3.68°/RMS 1.49°, early reset 0. Torso body drift는 사실상 0,
  Chest 최대 9.5mm·Head 42.6mm·R_Wrist 37.7mm(연쇄 관절의 작은 각도 편차 누적)였다.
  이는 구조적 단기 PASS이며 충분히 학습된 정책의 장시간 안정성 보증은 아니다.
- **[2026-07-21] R12 goal-aware 근위 관절 우선순위 구현**: `env/rewards/motion.py`가 실제 DOF
  속도를 가동범위로 정규화하고 finger/wrist/elbow/shoulder에 0.05/0.20/0.50/1.00 비용을 준다.
  wrist goal 반경보다 10cm 이상 멀면 gate=0, 전환 구간은 smoothstep, 목표 안은 gate=1이므로
  도달할 때는 팔 전체를 쓰고 도착 후 손가락을 우선한다. 전체 reward 2%(core78). 그룹별 motion,
  gate, reward를 info/eval에 기록한다. CPU 계층 검사와 8-env GPU PPO smoke PASS. 미학습 1ep는
  wrist distance 22.9cm라 gate=0/reward=1로 도달을 방해하지 않음을 확인했다. 당시 smoke 진단
  산출물은 이후 현재 환경과의 호환성 정리 과정에서 삭제했다.
- **[2026-07-21] R13 손바닥-바닥 방향 종료 구현·시각화**: 손가락이 현 쪽으로 굽을 수 없는 명백한
  뒤집힘만 잡기 위해 기타 상대 방향 대신 세계 좌표의 바닥 방향을 사용한다. 손바닥 안쪽 법선은
  `cross(wrist→middle1, pinky1→index1)`의 고정 점 순서로 구성하며 현재 자세에 따라 부호를
  뒤집지 않는다. 법선의 world-z `<−0.3`이 3 제어 프레임 연속이면 조기 종료하며 정상 범위에는
  보상·페널티가 없다. 초기 자세 world-z=`+0.8708`을 확인했다. 초록=손바닥 안쪽, 파랑=world +z,
  빨강=바닥(world −z), 반투명 파랑=수평면인 `fret/renders/palm_world_direction_multiview.png`와
  방향별 PNG 4장을 생성했다. 이전 넥 상대 이미지는 비교 기록으로만 남긴다. `env/safety.py`의
  공용 법선·연속 판정 함수를 시각화와 `FretTask`가 함께 사용하고, 무효 법선은 streak을 초기화한다.
  info에 world-z/valid/streak/종료 원인을 기록하며 CPU 단위 검사와 8-env GPU PPO smoke를 통과했다.
- **[2026-07-21] R14 관통 안전 1단계 구현**: 런타임 시작 시 휴머노이드 54 shape(filter 1), 기타
  27 shape(filter 2), `contact_offset=0.1mm`, `1&2=0`을 감사해 충돌 비활성화를 즉시 실패시킨다.
  기타 로컬 테이퍼 넥·바디 박스·상판 박스의 해석적 내부 깊이를 왼팔/손가락 다점 표본에 적용하고,
  현재 깊이·9점 시간 보간 swept 깊이·양 끝이 밖인 터널링·reset 직후 겹침을 info에 기록한다.
  후보는 5mm/3프레임이지만 정상 압현 rollout 보정 전까지 `penetration_termination=False`로 진단만 한다.
  공통 ±300Nm 상한은 finger20/wrist60/elbow100/shoulder·thorax150/기타300Nm로 세분화했다.
  초기 자세 8env×12step과 실제 reset noise 0.02의 512env×2step에서 현재/swept/초기겹침/터널링
  모두 0, PPO smoke와 CPU 기하 검사를 통과했다.

- **[2026-07-20] 왼손 운지 문서 허브 `fret/` 신설·가독성 재구성**: 여러 디렉터리에 있는 정본은
  중복 복사하지 않고 연결하되, 사람이 `운지 결정 → 물리 압현 → 학습·검증` 순으로 읽도록 3단계
  디렉터리와 단계별 해설 README를 추가했다. 루트 `fret/README.md`는 전체 흐름·현재 상태·필수 규약과
  문서 판단 우선순위를 한 화면에 제공한다.
- **[2026-07-20] task_fret R1/R2 재검토 + 실제 프렛 시각화**: R1 규칙(지정 손가락이 목표
  줄·프렛을 누름)은 유지하되, 접근과 실제 press 성공을 분리했다. `tools/fretboard_visualization.py`가
  live `G:fretN` 기하를 카메라에 투영하고,
  `tools/render_fretboard_reference.py`로 `fret/renders/fretboard_reference.png`(1600×900)를 생성·육안 검증했다.
  `record_fret_rollout.py --show-frets`도 같은 오버레이를 사용한다. 자홍선=x20 접근점,
  노랑=x10~30 최적, 초록=x30~85 감점, 청록=실제 와이어이며 물리에는 영향이 없다.
- **[2026-07-20] task_fret R1/R2 구현·기본 검증 완료**: 줄별 압현 점수는 `30% 접근거리 + 50% 실제
  지정손가락 press + 20% 위치품질`. 접근 목표는 fret wire 표면 기준 나무 구간 x=20%, 실제 press는
  guitar local -z 방향 pad signed depth on/off=1.0/0.5mm + 올바른 프렛 칸 + 최고 프렛 일치,
  위치품질은 x=10~30% 만점·30~85% 완만 감점으로 확정했다. 같은 프렛 다중 손가락은 위치가 달라도
  press 성공을 유지한다. `rewards/fret.py`와 평가 지표에 구현했고 CPU 기하 단위검사 및 8-env GPU
  PPO smoke를 통과했다. 구 모델 `fret_002000.pt`의 새 기준 재평가는 F1=0, press 성공률=0%, 평균
  signed depth=-6.38mm로, 접근만 배운 기존 checkpoint는 폐기하고 새 보상으로 재학습해야 한다.
- **[2026-07-20] R3/R4 통합 구현 — 줄·프렛별 PRESS/NO_PRESS/DONT_CARE**: 매 60Hz frame에
  scalar goal로 6줄×22프렛 요구 마스크를 파생하고 실제 `(N,6,4,22)` 압현과 비교한다. 목표보다
  낮은 프렛은 DC, 목표는 지정손가락 PRESS, 높은 프렛은 NP이며 NP 오압현은 해당 줄 task 점수를 0으로
  무효화한다. goal=−1은 전 프렛 NP, 0은 전 프렛 DC다. `no_press_accuracy`·`wrong_press_rate`를
  평가에 추가했고, 추가 음수 페널티와 연속 회피 shaping은 cfg 기본 0으로 배관만 준비했다.
  CPU 사례검사(낮은 프렛 허용/높은 프렛 실패/전줄 NP/DC)와 8-env GPU PPO smoke PASS.
- **[2026-07-20] R5 release goal 정제 구현**: `build_fret_training_data.py`가 upstream에서 이미
  병합된 같은 위치 재타현은 PRESS로 유지하고, 남은 이벤트 경계에서 같은 줄의 다음 press가 있으면
  `t_release..next.t_press`를 NO_PRESS, 마지막 release 뒤는 DONT_CARE로 만든다. S0 goal을 재생성해
  24 press 이벤트·14 release window·861 frame, 줄-프레임 기준 P=1,213/NP=834/DC=3,119를 확인했다.
  CPU 타임라인 검사와 새 goal 기반 8-env GPU PPO smoke PASS.
- **[2026-07-20] fret 제어 관절 37→33 재정의**: 이상한 몸통 뒤꺾임을 막기 위해
  `Torso/Spine/Chest` 9DOF를 action에서 제거해 init PD로 고정하고, R6 넥 뒤 지지를 위해 엄지 5DOF를
  추가했다. 현재 정책 제어는 `L_Thorax/L_Shoulder/L_Elbow/L_Wrist` 12 + 왼손 다섯 손가락 21 = 33.
  `L_Thorax`는 작은 범위의 어깨 띠이므로 유지한다. 당시 obs255였고 R15 이벤트 관측 추가 후 307,
  곡 진행률 추가 후 308이었다. actuator state 33D까지 관측해 당시 341이었고, 이후 thumb geometry
  12D를 추가해 현재는 353이다. 당시 runtime assert와 8-env GPU PPO에서
  `actions=33, obs=341, reward/value=6`을 재검증했다.
  구 37-action checkpoint와 action head가 호환되지 않아 새 학습만 허용한다.
- **[2026-07-20] R6 엄지 넥 뒤 실제 접촉 보상 구현**: 새 `env/rewards/thumb.py`가 기타 mesh의
  tapered back plane(local z=-8mm, y=-0.241803..0.217197m, 반폭 27.908..20.419mm)을 사용한다.
  `LH:thumb3→thumb_top` 7mm capsule의 듀얼스케일 15/120mm 접근 30% + `thumb3` GPU net contact
  force가 on/off=0.5/0.1N이고 넥 뒤 영역일 때 접촉 70%; 전체 reward 비중 5%. 현 조합은
  core78/wrist15/thumb5/R12-proximal2이며 R10 smooth는 보류해 0.
  옆·앞·바디 접촉은 무효, 힘을 더 줘도 추가점수 없음. 거리/갭/힘/support/wrong-contact 지표를 평가에
  추가했다. CPU 기하+hysteresis 검사와 8-env GPU PPO smoke PASS. 초기 미학습 자세는 평균 넥 거리
  약 10.1cm·접촉력0이며 듀얼스케일 후 평균 thumb reward 0.0447로 0이 아닌 접근 신호를 확인했다
  (`tab2body/_gen/diagnostics/fret_thumb_r6_initial_1ep.json`). 실제 접촉 분포 기반
  힘 임계값 보정과 지속 과이탈 종료는 후속.
- **[2026-07-20] fret 시각 산출물 위치 확정**: 왼손 운지·압현 작업에서 새로 생성하는 이미지·영상은
  `fret/renders/`에 저장한다. checkpoint·평가 JSON·원본 데이터는 시각 산출물이 아니므로 기존
  `tab2body/_gen/` 위치를 유지한다. 프렛 캡처 생성 도구의 기본 출력도 이 경로로 변경했다.
- **[2026-07-20] 프렛보드 6줄 오버레이 추가**: `render_fretboard_reference.py --show-strings`가
  live `G:string1~6` 중심선을 서로 다른 색으로 투영하고 1 high-e~6 low-E 라벨을 붙인다. 기존
  `fretboard_reference.png`는 보존하고 새 캡처를 `fret/renders/fretboard_reference_with_strings.png`로 저장했다.
- **[2026-07-20] R7 손목 안전 영역 후보 시각화**: 움직이는 wrist goal 대신 기타 로컬의 넓은
  고정 박스를 최소 안전 종료 조건으로 쓰는 방향을 검토 중이다. 후보 경계
  `min=(-.20,-.35,-.30)m`, `max=(.30,.35,.25)m`를 실제 장면 위 반투명 직육면체로 표시한
  `fret/renders/wrist_safety_envelope_preview.png`를 생성했다. 현재 그림상 상체·무릎 일부까지
  포함할 만큼 느슨하며, 이는 **구현 확정값이 아니라 시각 검토용 후보**다. 추가로 기타 로컬
  `±X/±Y/±Z` 여섯 방향의 개별 PNG와 비교 모음
  `fret/renders/wrist_safety_envelope_multiview.png`를 생성했다.
- **[2026-07-21] R8 비엄지 손가락 기타 뒤 이탈 규칙 재정의·시각화**: 검지·중지·약지·소지의
  마디 중심선을 다점 샘플링하고 기타 로컬 `z<-50mm`를 넘으면 위반으로 한다. 실제 넥 뒷면
  `z=-8mm`에서 42mm 여유가 있으며, 손이 너무 뒤로 간 상태를 잡는 목적이므로 넥 테이퍼의 x/y
  범위는 검사하지 않는다. 엄지는 R6으로 분리해 제외하고 연속 2~3프레임 수는 구현 때 확정한다.
  구 빨간 테이퍼 부피 PNG 7장은 삭제했으며, 한 장의 경계 평면과 금지 `-Z` 화살표만 표시한
  `fret/renders/finger_back_limit_plane_multiview.png` 및 방향별 PNG 4장으로 교체했다.
- **[2026-07-21] fret 보류 항목 분리**: `fret/04_deferred/README.md`에 R3 추가 오압현
  페널티·회피 보상, R6 접촉력 보정·엄지 과이탈 종료, R9 손가락 각도 강제, R10 빠른 이동·떨림
  억제를 모았다. R9는
  단음과 바레의 정상 각도가 달라 하드 실격을 적용하지 않고 실제 자세 문제가 관찰될 때 재검토한다.
  R10은 압현 핵심 학습 뒤 자연스러운 모션 단계로 넘기고 `smooth_weight=0`으로 비활성화했다.
  R12 구현 후 보상 조합은 core78%+wrist15%+thumb5%+proximal2%다. 기존 단순 smooth 계산 코드는 hook으로 남긴다.
- **[2026-07-19] task_fret S0 데이터 파일럿 생성**: GuitarSet의 오디오 매핑 GT JAMS 후보를
  난이도 분석해 `02_Jazz1-200-B_solo`(42음, 단음, 4~7프렛, 3줄, 바레 없음)를 선정.
  `tab2body/tools/build_fret_training_data.py`가 annotation→명시 운지→60Hz 학습 JSON을 재현한다.
  산출물 `_gen/fret_training/02_Jazz1-200-B_solo.fret_training.json` = press 24개·861프레임,
  진단/위반 0. frame goal은 Isaac 줄 순서로 반전 완료하며 hand position은 6프렛 soft band +
  0.25초 선행 보간. 원본과 시각자료는 같은 경로의 `02_Jazz1-200-B_solo_bundle/`에 묶음.
  번들 내 `02_Jazz1-200-B_solo.isaac_fingering.mp4`는 Isaac Gym 기타 위 운지 목표를 손가락별
  색 구체로 표시한 오디오 포함 영상(1280×720, 30fps, 14.35초; H.264/AAC 검증).
  추가 `*.isaac_hand_position.mp4`는 6프렛 band·보간 anchor·넥 기하 기반 손목 중심·4cm soft
  range를 표시하고, 동일 430프레임의 기타 로컬 좌표를 `*.hand_position_targets.json`으로 저장.
  ⚠️ 손목 목표는 초기 기하 prior이며 휴머노이드 IK/reach·관통 검증 후 학습 보상에 채택한다.
  이 데이터 파일럿은 아래 S0 학습 코드에 연결 완료.
- **[2026-07-19] task_fret S0 학습 코드 구현 + 실행 배관 PASS**: 빈 스텁이던 `env/goals.py`,
  `env/rewards/fret.py`, `env/tasks/task_fret.py`, `learning/{models,ppo}.py`, `cfg.py`, `train.py` 구현.
  당시 계약 = 37 actions(몸통9+좌팔12+네 손가락16, 엄지 고정; 07-20부터 현행 33으로 폐기), obs 255(base180+goal75),
  reward/value 6줄. 실제 기타 압점↔지정 손가락 3세그먼트 듀얼스케일 보상 + free/don't-care +
  hand 4cm soft prior + smoothness, 0/0.1/0.25s 룩어헤드, 단일프레임 MLP, 줄별 GAE PPO.
  GPU PhysX 배관 smoke 후 **512env·2,500회 checkpoint=40,960,000 samples 본 학습**.
  checkpoint 비교(같은 S0 곡, deterministic 64 episode): F1 500회 0.1667 → 1,000회 0.7237 →
  1,500회 0.9020 → **2,000회 0.9175(구 기준 최선)** → 2,500회 0.9108. 당시 선택
  `_gen/checkpoints/fret_s0_pilot/fret_002000.pt`, 상세 `RESULTS.md`. resume는 iteration/global step을
  연속 복원하고 평가는 target/wrist 거리도 JSON에 기록한다. 선택 정책 영상 도구는
  `tab2body/tools/record_fret_rollout.py`; 선택 모델 영상 `fret_002000_rollout.mp4` 생성·재생 검증.
  ⚠️ 이 checkpoint는 07-20 signed-depth 기준에서 F1=0으로 효력이 끝났다. 새 보상 재학습 전이며,
  해당 곡 전체 롤아웃의 관통·limit·비제어 부위·목표 영상 대조 전에는 최종 물리 성공 미선언.

- ✅ 전제 P1~P8 전부 실측 해소 (research-flow §7)
- ✅ 에셋 확정: `tab2body/assets/` (휴머노이드 65바디/105DOF + 독립 기타 + 정본 좌식 자세 seated_pose.json)
- ✅ 검증 완료: 좌식 자세(관통 0), 프렛 도달 34/36(굽힌 운지), 스트라이크 6/6, GPU 512env
- ✅ **`tab2body/env/base.py` 마감 완료 + 전 검증 PASS** — 참조연구(guitar/DIGIT/GPS) 종합 기반. 두 축:
  - **초기자세 안정**: 하체 furniture 3중 잠금(pinch+armature+매스텝 재주입) → 드리프트 **0.0000°/50s**(verify_stability). 능동 상체 제어 중에도 0°. 발은 평평·바닥위~1cm(발 접지 시 잠금-접촉 떨림 트레이드오프 회피, §4).
  - **RL 루프**: reset/RSI · 액션 EMA(0.5)+2×스케일 · step(자동리셋) · 종료(timeout/NaN/blow) · **기타-상대 관측**(quat 버그 회피) · 접촉텐서 · 버퍼. 당시 공용 task smoke PASS.
  - **설계 문서** `tab2body/env/README.md`(왜 이렇게 구성됐나, 근거 태깅) + 원자료 `docs/base-env-research.md`.
- **[07-13] 디렉토리 재구성 + 루트 README.md(디렉토리 안내서) 신설**: guitar/GPS/ELGAR → `related_work/` 하위로, conformer_v2 → `tabtrans/conformer_v2/`로 이동(이동으로 깨진 config.py 경로 앵커 수리·임포트 검증 완료 — conformer_v2 실행은 tabtrans/에서 `python -m conformer_v2.<모듈>`). 새 세션은 README.md → 이 문서 순서로 부트스트랩.
- 🔶 **현재 다음 작업(strike 순서)**: 새 A0~A4 구현의 최종 GPU 스모크·checkpoint 재로딩·
  두 카메라 녹화 재검증은 완료했다. 이제 새 run에서 500 iteration 학습을 시작한다.
  단계 전환·100→67→50 ms 축소,
  6줄별 recall/FP/F1/타이밍/zone 분포와 두 시점 영상을 함께 보고 reward·gate 수치를 조정한다.
- 🔶 **병행 fret 작업**: 선택 곡을 새 R1/R2 보상과 곡별 R26 커리큘럼으로 재학습 →
  전체곡 pad 깊이·위치품질·F1 확인 → 관통·손가락 상호관통·R24 접촉/토크·비제어 부위 감사 → 영상 검수.
  다른 곡은 일반화 평가가 아니라 별도 정책으로 같은 절차를 반복한다.
- **[07-16] task_fret 설계·구현 계획 확정 = `docs/plans/task_fret_plan.md`**. 당시 계획서만 저장·구현 보류였으며 07-19 S0 경로가 착수됨. 이식원본(guitar env.py fret 보상 1471-1687·goal 1045-1432)+GPS+DIGIT 안티패턴 정밀 분석 종합. **사용자 결정(신규, §3 #12): 운지 감독 = 처음부터 명시(explicit)** — Xu 암묵 윈도 마스크 대신 우리 fingermapping의 finger id로 특정 손가락 감독(Xu Fig13 선행운지 한계=우리 노벨티). 현 S0 구현은 6줄 reward/value와 MLP-PPO 계약을 확정했으며, 암묵 폴백·20곡 변환·PopArt/AMP는 후속.
- 학습 아키텍처: 태스크 분해(fret ∥ strike 개별 학습) → G0 결합 → 같은 정책 G1 이어학습(기타 자유화)
- **[07-13] 코드(chord) 트랙 신설**: 설계 정본 = `docs/chord-module-design.md`(결정 D1~D8). 구현 = `tabtrans/conformer_v2/`(v1 불변, 인코더 공유+코드 헤드 37클래스). 라벨은 moum GT XML에서 유도(감사 88/88=100%; 파일명 `E1-Major 05`=E폼 5프렛 이동 의미론 발견). 비교 실험 완료: v2_stageA(동결 프로브) acc 0.76/mF1 0.24 vs **v3_joint acc 0.91/mF1 0.50, 탭 frame F1 0.75→0.91·note 0.70→0.86**(moum val — 단 도메인 파인튜닝 교락, 원 벤치마크 회귀 측정 전 채택 금지). **[07-13 밤] 손실 가중 스윕(w_chord 0/0.3/1/3) 완료 — 교락 moum 내 해소: 탭 개선은 전부 도메인 적응, 코드 손실은 탭 단조 하락(w0 탭 0.956 > w1 0.907), 코드 지표는 단조 상승(w3: mF1 0.536, τ0.7 P 0.96/R 0.24로 w1 지배). 권고 = 코드 채널 전용(탭 v1 유지)이면 w_chord=3, 겸용이면 0.3~1. 상세 tabtrans/conformer_v2/README 검증로그.** **[07-13 심야] 반전: 규칙 디코딩(예측 탭→match_pcset)이 학습 헤드 전부를 압도 — v1 무수정 탭→규칙 acc 0.937/mF1 0.708, wc00 탭→규칙 0.980/0.827(R/P 0.95/0.95). 코드 헤드 무용 가능성 — 경로 B→규칙 디코딩 전환은 사용자 결정 대기(README 검증로그 표 참조).** 도메인 기초 = `docs/guitar-basics-notes.md`(+지판 지도 PNG, 20곡 프렛 통계: 1~12프렛 91.8%·개방 20.9%).
- **[07-15] 코드(chord) 소스 확정 — 학습 헤드 은퇴 → 외부 ACE 도입 → 실측 후 "탭→규칙 1차 + ACE 2차"로 최종** (아래 4항목이 하루의 결정 흐름):
  - **conformer_v2 은퇴** → `tabtrans/legacy/conformer_v2/` 보존(07-13 심야 대기 건 사용자 확정 — 탭은 v1만 사용). ACE 조사 1순위 = **consonance-ACE**(ISMIR 2025·Conformer·170클래스·MIT·ckpt 동봉, github.com/andreamust/consonance-ACE; 예비 = BTC ISMIR 2019).
  - **consonance-ACE 클론·스모크 OK** → 현 `tab2fingermapping/ace/`. 로컬 패치 2건(패키지 임포트·enum.verify py3.10 폴백 — 재클론 시 재적용, `SETUP.md` §4). rock3 comp(Bb)에서 I-V-vi-iii-IV 정확 검출. ⚠️lab 끝 zero-pad N은 실길이로 클립, 내부 43.07fps→.lab 구간 출력.
  - **ACE 정량 평가 — 게이트 불통과**(`ace_eval/REPORT.md`): moum 코드88+단음156, 37클래스 top-1 완화 세트(τ0.3·minDur0.25) **0.65**(게이트 0.9 ✗)·루트 0.80·멜로디 N 오탐 5.9%. 실패 모드 = 감쇠 고립 코드의 3도 소실(`E:(5)`) — 연속 컴핑은 정확. v1 탭→규칙(0.937)이 압도 → ACE 2차 강등(결정 #11 수정 반영).
  - **코드 트랙 모듈 구현 + 게이트 통과** = `tab2fingermapping/chordtrack/`(`REPORT.md`): 1차 탭→규칙(match_pcset) + 시간 필터(mode9·N틈메움0.35s·최소지속0.25s) + 2차 ACE 게이팅(합의 conf=3/불일치 conf=1/N구간은 pcset 부분집합 검증 후 구제). moum 4변형: **탭→규칙 top-1 1.000·오탐 0%**(✓✓), 필터 +5.1%p, ACE 융합 +0.5%p. rock3: 합의 68%/불일치 20%(X:5 vs X:maj — 운지 관점 탭이 옳음)/구제 2.7%. ⚠️moum 1.000은 낙관 상한(고립 코드·v1 학습중복 가능).
- **[07-15] finger mapping 설계 + v0 구현 완료**: 설계 정본 = `docs/finger-mapping-design.md`(규칙 1~3=정책, 4~5=물리 마스크, 제안 6~10, 로드맵 M1~M4), 구현 = `tab2fingermapping/fingermapping/`(grips.py 그립 사전 + assign.py 빔서치 K20 + run_fingering.py, **설명서 = ALGORITHM.md**, 파이프라인 4단계 → `*.fingering.json`). 핵심: 그립 사전(오픈8종+CAGED바레+파워, GRIP_BONUS로 관례 폼 우선)·앵커 보너스(Am↔C 검지·중지 유지 재현)·지속음∪새배치 합집합 규칙4·5 검사·충돌은 조기 리프트(`t_cut`) 비용 해소(잘림=전사오류 후보 신호). 검증: 단위 6케이스 통과(교본 운지·F바레·하강겹침 선행계획 창발 등), rock3 218노트 **위반 0**, 멜로디 릭 2포지션 고정 재현. **[07-15 추가] 일반 바레 솔버**(후보 3층, `_barre_candidates` — 최저 프렛 2줄+ 공유 시 검지 바레 가정, W_BARRE 비용으로 필요할 때만 선택) → rock3 배정 불가 2건 구제(**전 노트 배정**, 잘림 17→14). 운지 시각화 = `fingermapping/render_timeline.py`(fingering.json→PNG, 산출 예 = `_gen/rock3_fingering_timeline.png`). **[07-15 추가] 누름(press) 타임라인**: 소리(t_on=타현)와 왼손 누름을 분리 — 선행 누름 0.12s(물리 클램프)·재타현 병합 1.5s(금지조건: 손가락 이동/사이에 낮은 프렛·개방 음)·**스티키 핑거**(같은 자리 재타현=같은 손가락 보너스, 병합 가능성 확보) → fingering.json `presses` 배열 = 왼손 goal, notes t_on = 타현 goal (task_fret∥task_strike 대응). rock3: 타현 218 → **누름 이벤트 103**(최장 유지 2.6s). **조기 릴리즈**(차단 앞 음을 최대 80ms 앞당겨 끊어 리드 확보, 최소 울림 50ms) → 리드<30ms 36→5개·평균 리드 0.104s. 타임라인 이미지 = 막대(누름)+검은 틱(타현).
- **[07-15] Stage1 재구성 → `tab2fingermapping/` 신설 + conda 환경**: 구 tabtrans 활성 컴포넌트 이동(conformer v1→`conformer/`, ACE→`ace/`, chordtrack·ace_eval·csv_to_notejson) + **통합 컨트롤러 `pipeline.py`**(v1 추론 1회 공유, 오디오→notes.csv+.lab+chords.json+fingering.json+notes.json 원커맨드). tabtrans는 아카이브(legacy·examples)로 존치, legacy config 경로 앵커 재수리. 실행 환경 = **conda `tab2fm`**(venv는 이동에 취약해 폐기; guitar_eval 클론+ACE 의존성, torch 2.5.1+cu121·py3.10) — 셋업·검증·트러블슈팅 정본 = **`tab2fingermapping/SETUP.md`**. 검증: rock3 end-to-end 기존 체인과 비트 동일(218노트→105이벤트, qerr 21.9ms).
- **[07-15] Isaac Gym 운지 시각화 데모** = `fingerviz/`(자체 README): wav→fingering.json→기타 지판 위 손가락별 색 구체(줄당 1개, 충돌 OFF·시각화 전용)→mp4(오디오 먹싱). 프렛/줄 좌표는 기타 액터 바디(G:fret*·G:string*) 월드 위치에서 런타임 계산, 에셋은 tab2body에서 복사(원본 불변). 산출 = `fingerviz/_gen/rock3_fingering_viz.mp4`(32.8s). ⚠️줄 매핑 가정: CSV s0(low-E)→G:string6 — goals.py "JSON↔G:string 매핑 확정" 때 재검증.
- **[07-15 밤] 전사 v2 재학습 착수 (onset+frame / HCQT / freq-attn) = `tab2fingermapping/transcribe_v2/`** (사용자 결정: 구조=듀얼헤드+HCQT / 규모=애블레이션 1~2일 / 목표=균형 note-onset F1). SOTA 조사 워크플로 종합(`_gen/research_synthesis.md`) → 설계 정본 `DESIGN.md`. v1 불변, guitar_v3 학습코드도 불변, 별도 디렉토리. 구조: HCQT 6하모닉 빈-롤 + 주파수축 어텐션 프런트엔드(hFT, 옥타브 유령음 핵심) + 6층 Conformer + Onset&Frame 듀얼 sigmoid 헤드(6현×21fret) + 지역최대 note-forming 디코드(재타현 분리 단위검증 ✓). GuitarSet player-held-out(train 0-3/val 4/test 5). **★R0 핵심 발견**: v1 mir_eval 재평가로 **"0.596"=융합 test113의 string-DEPENDENT note-F1 확정**(agnostic 0.695). GuitarSet 단독 0.87은 player5 학습 누수+깨끗한 단일기타. 융합 TDR 0.758은 **GuitarTechs 현-반전 라벨버그**(정방향51%↔반전98%) — v2 데이터셋이 정규화로 수정. 또 **재타현 병합 상당부분은 median smoothing(--smooth3)이 자초** — smoothing 없이 v1 recall 높음. **★학습 안정화 3종 해결**(DESIGN §11): ①출력 bias 사전확률 초기화(RetinaNet)=붕괴 해결의 핵심(sparse 타깃 전부-0 자명해 방지) ②스레드 제한(OMP/torch=2)=numpy/torch 상태오염 랜덤크래시 해결 ③스텝·아이템 예외 격리. 애블레이션 R0~R4 큐 **백그라운드 실행 중**(각 ~1분/epoch, 조기종료, 총 ~3-5h) → 완료 시 `RESULTS.md`. R0 baseline 정상 상승 확인(ep5 sdep 0.49↑). 목표선 sdep>0.506·sag>0.664·frame-tab>0.781·TDR>0.918. **새 세션은 RESULTS.md·DESIGN.md 확인.**
- **[07-16→07-17] guitar_v3 심볼릭 → 실제 복사(자립화)**: 07-16 심볼릭 링크였으나 **07-17 실제 디렉토리로 복사**(data/moum 4.6G 포함, 학습 ckpt 이력 947M 제외; 외부 `~/yigyu/guitar_v3` 원본 무결). 하드코딩 절대경로도 **프로젝트 상대경로로 패치**(`guitar_v3/{train,inference}.py`·`codes/dataset.py`·`tab2fingermapping/transcribe_v2/{train,evaluate}.py`, `__file__` 기준) → 프로젝트만 옮겨도 학습·추론 자립(윈도우 이식 가능). 상세=`conformer_reference/README.md §5`.
- **[07-16] 파일 정리 → `legacy/` 신설**: 현 파이프라인이 임포트 안 하는 것들을 최상위 `legacy/`로 이동 — ①최상위 ACE/(conformer-acr 클론 134M, 미채택 후보) ②`ace_eval/`(ACE 게이트 불통과 평가) ③`onset_split/`(무학습 onset분리 실험, transcribe_v2로 대체) ④`tabtrans/examples/`(구 체인검증 산출물). **살아있는 의존성은 원위치 유지**(tabtrans/legacy/conformer_v2 ← chordtrack, ace/ ← pipeline). 목록·되살리기 = `legacy/README.md`. findings는 각 REPORT+이 문서에 이미 기록. 학습·임포트 무영향 확인.
- **[07-15] 전사 recall 진단 + onset 분리 실험 — 재학습 불필요 판정**: rock3 comp GT(GuitarSet .jams, audio_mono-mic 360곡 전부 GT 보유) 대조에서 note R 0.32(509 vs 218) — 원인 = 연속 스트럼 재타현을 frame run-length가 병합(표현의 구조적 한계, frame F1 0.835는 양호). 무학습 후처리(오디오 onset에서 울리는 예측 노트 절단, **CQT band-gate**로 오절단 방지) 실험 = `tab2fingermapping/onset_split/`(REPORT.md): **전수 360파일 확정: note F1 0.793→0.857**(comp 0.705→0.807, solo 0.881→0.906; R +0.104에 P −0.010), 게이트(0.7) 통과 → **onset 헤드 재학습 보류, v1 무수정 유지**. 파이프라인 통합은 승인 대기.
- 🔶 **Stage1 다음 작업(순서)**: ①✅ S0 fingering→tab2body goal 연결 완료 ②아르페지오·실곡에서 chordtrack ARPEGGIO 경로·finger mapping 검증(dataset3·youtube) ③모티프 일관성·lazy lift 후처리(ALGORITHM.md §6) ④비용 가중치 20곡 통계 튜닝 ⑤`t_cut`·`finger=None` 진단 → 탭 교정 피드백(경로 C).

## 3. 핵심 결정 로그 (전부 사용자 확정, 뒤집으려면 사용자 승인 필요)

1. **EDGE(diffusion) 완전 폐기** — Xu 구현 분석으로 "참조 모션 필수" 전제가 틀림을 확인. 논문 제목 "Diffusion-based" 재작성 필요.
2. **베이스 = guitar/ (Pei Xu SA'24) 이식** — DIGIT 실패 원인 4가지(자유기타·단일보상·급경사보상·약한 disc) 각각에 검증된 해법 보유.
3. **기타도 최종 제어 대상** — G0(고정)→G1(스트랩 spring-damper)→G2(자유) 스테이징. 기타 안정성은 독립 태스크가 아니라 결합 정책의 G1 fine-tune.
4. **단일 env 금지** — tasks/{fret,strike,full} 분리 학습 후 결합(주입 네트워크, AdaptNet 방식). 몸통 공유가 Xu에 없던 난제.
5. **하체 잠금**(리밋 핀칭 lower==upper) + root 고정 — 자유 root는 3초 내 전도(실측).
6. **sit_guitar 영상 모션(유튜브+MediaPipe)**: 초기자세 시드(완료) / 몸통 한정 disc 실험(T6) / sway 통계 후퇴선. **팔·손 부위 사용 전면 금지**(머리 위 손·미러).
7. **학습·평가 주 데이터 = 큐레이션 탭 20곡**(guitar/assets/notes/), 전사는 데모·별도평가(note F1 0.596라 혼합 금지).
8. 디렉토리 위생: 최종 파일(assets/)과 생성물(_gen/)·렌더(renders/) 분리 — 모든 작업 공통.
9. **[07-13] RL 알고리즘 = PPO** (Isaac Gym 병렬+판별자+멀티크리틱 = Xu 상속. GPS의 DroQ는 CPU·소수 env 셋업의 산물이라 미채택).
10. **[07-13] 코드 정보 = goal의 옵셔널 채널**(상태 아님·비면 현행 동작·학습 시 채널 드롭아웃·채택은 S2/S3 A/B로 판정). base.py에는 goal_dim 가변성만 — 코드 의미론은 goals.py 관할. 연주가능성 보정은 모델 밖 제약 디코딩.
11. **[07-15] 코드(chord) 소스 = 외부 ACE 채택** — conformer_v2 학습 코드 헤드 은퇴(`tabtrans/legacy/`에 보존), 탭 전사는 v1 단독 유지. **[07-15 수정, 사용자 지시]** ACE 정량 평가 게이트 불통과(0.65)로 역할 조정: **1차 = 탭→규칙 디코딩, 2차 = ACE 게이팅**(신뢰도·N 구제·불일치 플래그) — 구현 = `tab2fingermapping/chordtrack/`.
12. **[07-16] task_fret 운지 감독 = 처음부터 명시(explicit)** — Xu의 암묵 순서형 손가락-윈도 마스크 대신, 우리 fingermapping이 배정한 finger id로 특정 손가락을 감독. 근거: Xu·GPS 공통 한계인 "선행적 운지 계획 부재"(Xu Fig13)를 우리 fingermapping(빔서치·앵커핑거·바레·`presses`)이 해결 → 감독 신호로 쓰면 그것이 노벨티. 데이터는 20곡→fingermapping→finger 라벨. 계획 = `docs/plans/task_fret_plan.md`. (암묵 경로는 진단 구간 폴백·A/B용으로 코드에 상시 공존.)

## 4. 함정 목록 (전부 실측으로 밟은 것 — 재발 시 여기부터 의심)

1. **MuJoCo↔Isaac 멀티힌지 회전 합성 불일치**: 같은 관절각 → 손목 세계좌표 8.4cm 차이. MuJoCo/poselib 저작 각도·mocap을 Isaac에 넣을 땐 반드시 Isaac FK 재검증. → seated_pose.json은 `joints`(MuJoCo용)/`joints_isaac`(Isaac용) 이중 표현. **Isaac 도구는 joints_isaac 사용.**
2. **Isaac create_actor 충돌 필터**: 두 액터의 filter 비트가 겹치면 **액터 간 충돌도 꺼짐**. 규약: humanoid=1, guitar=2, chair=0. (이걸 몰라 관통 검사가 한 번 무효였음)
3. **Isaac 네이티브 position drive의 D6 왜곡**: 멀티힌지 관절(어깨 등)에서 kp 무관 동일 오답 수렴(~20°). → base.py는 **하이브리드 PD**(감쇠=drive damping[암시적], 강성=명시 토크 τ=kp(q*−q)). 순수 명시 PD는 감쇠 0이면 bang-bang 발산(팔꿈치 235° 실측).
4. **PhysX 기본 contact_offset 2cm** → 가짜 접촉으로 관절 밀림. per-shape 0.0001 강제(업스트림 레시피).
5. **Isaac은 드라이브 없는 관절을 임포트된 스프링이 0도로 당김** — 자유 시뮬/이완 설계 시 상쇄 필요.
6. MJCF 게인은 XML 직파싱 금지(default 클래스 상속 누락) → 정본 = `tab2body/_gen/mjcf_gains.json`(MuJoCo 해석값).
7. env 여러 개 만들 때 **액터 생성은 env별로 순차**(env1 액터 전부 → env2 생성).
8. 접촉-인지 IK류 옵티마이저는 진동 → **최적 상태 추적 반환** + 이중 재시작(q_pre/웜) 필수.
9. MPL 손가락 굽힘 부호 = **양수**(리밋 비대칭 [~0,+1.57]로 판정; 팁-손바닥 거리 탐침은 신전 상태에서 판별 불능).
10. **잠긴 발 + 바닥 접촉 = 떨림/드리프트 딜레마**(2026-07-09 실측 `tools/hold_compare.py`, 5전략 비교): 핀칭락(하드)이 바닥에 닿으면 리밋-접촉 싸움으로 떨림, 소프트로 풀면 26° 드리프트(스모크 FAIL). **해법 = 발을 바닥에서 ~1cm 띄우고(접촉 제거) 하체를 3중 잠금**: ①pinch(±1e-4) ②armature=10(서브스텝 떨림 0.10°→0.0015°) ③매스텝 init 재주입(느린 정착 제거). → 드리프트 0.0000°/50s. 부수: SMPL 좌우 다리 bind 비대칭으로 두 발 자연 접지 높이 4cm 차이(coplanar 접지 불가). 발 각도 solve = `tools/foot_settle.py`(무릎 스윕+발목 레벨링, 뉴턴은 좌우 비대칭에 발산—스윕 필수).

## 5. 파일 지도

```
README.md                    ← 디렉토리 안내서 (새 세션 부트스트랩 1순위, 구성 변경 시에만 갱신)
strike/                     ← 오른손 규칙·물리 계약·A0~A4 학습 설명 + 과거 pilot logs/videos
docs/  (research-flow.md·chord-learning.md 07-13 삭제, chord-module-design.md 07-15 삭제 — 승계는 헤더 노트)
  base-env-research.md       ← base.py 설계 원자료(4레퍼런스 분석)
  finger-mapping-design.md   ← 왼손 운지 알고리즘 설계 정본 (07-15, 규칙 1~10 — 구현은 tab2fingermapping/fingermapping)
  guitar-basics-notes.md     ← 기타 도메인 기초(운지·코드·통계·연구 매핑) + fretboard-24fret-map.png
  GPS-paper-ko.md / guitar-paper-ko.md ← 논문 국문 정리본 (PDF 5종 동봉)
tab2body/                    ← 신규 구현 패키지 (README에 구조)
  assets/                    ← 최종 에셋만: smpl_mpl_hands_body.xml, guitar_asset.xml(앵커는 XML에 없음—seated_pose.json이 정본), mesh/37, seated_pose.json
  env/                       ← base.py + fret/strike goal·detector·reward·task
  tools/                     ← 현재 fret 생성·plot·rollout·runtime 감사 + README
  tests/                     ← fret·base·공용 학습 회귀 검사 + README
  _gen/                      ← 재생성물(리포트·씬·게인), renders/ ← 이미지·영상
tab2fingermapping/           ← Stage1 통합 (07-15 신설): pipeline.py = 오디오→탭CSV+코드트랙+운지(+noteJSON) 원커맨드 (환경 = conda tab2fm, SETUP.md)
  conformer/                 ← v1 전사 (transcribe.py·conformer 패키지·ckpt — 구 tabtrans에서 이동)
  ace/                       ← consonance-ACE 클론 (로컬 패치 2건 = SETUP.md §4)
  chordtrack/                ← 코드 트랙: 탭→규칙 1차 + ACE 게이팅 (REPORT.md에 게이트 통과 근거)
  fingermapping/             ← 왼손 운지 배정: 그립 사전+빔서치 (ALGORITHM.md = 구현 설명·가중치·한계)
  transcribe_v2/             ← 전사 v2 재학습 (onset+frame/HCQT/freq-attn, DESIGN.md·RESULTS.md)
  csv_to_notejson.py         ← 탭 CSV→note JSON (tab2body goal 입력)
tabtrans/                    ← legacy/conformer_v2만 존치 (chordtrack이 37클래스 어휘 임포트 — 살아있는 의존성)
legacy/                      ← [07-16] 현 파이프라인 미사용 보관: ACE후보클론·ace_eval·onset_split·구 examples (README.md)
related_work/                ← 관련 구현 3종 (동결, 수정 금지 — 이식은 tab2body로 복사 후)
  guitar/                    ← Pei Xu SA'24 원본 (⚠️활성 의존: env.py 보상·goal·main.py 학습루프 이식 소스, assets/motions 손 mocap, notes/ 20곡=주 학습 데이터)
  GPS/                       ← CGF'24 로봇손 (프렛 수식·기타 메시(미터 단위)·어블레이션 참조)
  ELGAR/                     ← SIGGRAPH'25 첼로, 물리 없는 diffusion (노벨티 비교축)
DIGIT/                       ← 과거 AMP 기반 실패 구현 (newvec 브랜치에 온전, summary.md=실패일지, sit_guitar mocap 5클립=동일 190.4s 테이크 가공 5종)
isaacgym/                    ← Isaac Gym Preview 4 설치본 (분석 불필요)
```

## 6. 실행 환경 (이 머신: RTX 4070 Ti 12GB)

```bash
# Isaac Gym 계열:
cd /path/to/yigyu/3
conda activate rl38
export PROJECT_ROOT="$PWD"
export PYTHONPATH="$PROJECT_ROOT/isaacgym/python:$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"
python -m tab2body.train --task fret --smoke
# 주의: import isaacgym이 torch보다 먼저. 프로젝트 루트에서 실행한다.

# 오디오→탭+코드 (Stage1): conda env tab2fm — 셋업·검증 = tab2fingermapping/SETUP.md
conda activate tab2fm
python tab2fingermapping/pipeline.py <wav> --bpm N
```

## 7. 규약 (틀리기 쉬운 것)

- **현 인덱스 3종 주의**: note JSON `frets[5]`=low-E(bass) / Conformer CSV string 0=low-E / **G:string6=low-E(=frets[5]) 채택 규약**(MEMORY 07-13 감사 4단 근거 + fingerviz 가정 일치) — goals.py 이식 시 스모크로 1회 검증
- note JSON: -1=안 침, 0=개방현 침(좌손은 뮤트 회피), f>0=프렛. 이펙트는 값+100 패킹.
- 쿼터니언: MJCF/우리 JSON = wxyz, Isaac gymapi.Quat = xyzw.
- 압현 위치 좌표 = 목표 `G:fretN` 와이어의 너트쪽 표면부터 이전 와이어의 브리지쪽 표면까지의
  나무 구간 `x=0..1`. 접근 목표 x=20%, 위치품질 만점 x=10~30%, x=85%까지 완만 감점.
  실제 press 성공은 위치점수가 아니라 기타 안쪽 signed depth와 올바른 프렛 칸으로 판정한다.
- 기타 앵커 포즈는 env config(seated_pose.json의 guitar_pos/quat_computed)에서 주입 — XML에 굽지 않음.
- 좌표: 몸은 +y를 봄(모델 identity는 -y향, yaw 180°), 기타 로컬 +y=넥→너트, +z=사운드보드 법선.

## 8. 참고 문서 인덱스

| 문서 | 내용 |
|---|---|
| docs/plans/ | 태스크별 규칙·계획·검증 체크리스트 |
| tab2body/env/README.md | env 모듈 구조, 하이브리드 PD 근거, 제어방식 3사 비교 |
| tab2body/assets/README.md | 에셋 출처·재생성·주의 |
| DIGIT/isaacgymenvs/summary.md | 과거 실패 18차 보상수정 일지 (안티패턴 목록) |
