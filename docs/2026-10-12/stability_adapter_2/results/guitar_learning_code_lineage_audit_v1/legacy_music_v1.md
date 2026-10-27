# 기존 fret·strike·음악 코드가 현재 경로로 이어지는 방식

현재 구현은 기존 fret/strike 환경·보상 전체를 가져와 연결한 구조가 아니다. **음악 목표 compiler는 실제로 재사용하고, 타현의 일부 기하 판정은 별도로 옮겨 구현했으며, 압현 판정·입력·학습 보상은 자유 기타 환경에 맞춰 새 경로로 구성했다.** 따라서 기존의 오압현 억제·준비·회복·뮤팅 관련 기능이 모두 현재 학습에도 작동한다고 설명하면 부정확하다.

이 문서는 현재 소스의 import·호출·수식을 비교한 읽기전용 감사다. Git 변경 이력이나 작성 당시의 복제 과정을 검증한 것은 아니다. “직접 재사용”은 실행 시 기존 모듈을 호출하는 경우, “의미·알고리즘 대응”은 별도 구현을 현재 코드로 확인한 경우를 뜻한다. 명시적 근거 없이 과거 파일을 복사했다고 단정하지 않는다. 코드·보상·학습·판정 기준을 변경하지 않았고 native 실험도 추가하지 않았다.

## 먼저 읽을 순서

1. **현재 실제 보상이 무엇인지:** [TimingEnvironment.step](/home/ajou/yigyu/3/guitar_learning/timing_environment.py:117) → [TimingLedger.update](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:118) → [ActionablePreparationEnvironment.step](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:53). 기존 보상에서 무엇을 버리고 무엇을 추가하는지 먼저 볼 수 있다.
2. **현재 압현·타현 성공의 근거:** [TaskMeasurement._contacts](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:62)와 [_observe](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:132) → [measure_sample](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:56) → [StrikeDetector.update](/home/ajou/yigyu/3/guitar_learning/strike.py:49).
3. **음악 목표가 어디서 오는지:** [ScoreTask.from_bundle](/home/ajou/yigyu/3/guitar_learning/music_task.py:78) → [load_music_task](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/events.py:164) → [_compiler](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/events.py:20) → [compile_song_bundle_events](/home/ajou/yigyu/3/tab2body/full/events.py:1004).
4. **기존에 있었으나 현재와 다른 기능:** [기존 fret 요구·금지 마스크](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:932), [기존 fret 오압현 veto](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:2275), [기존 StrikeTask 준비 판정](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3720), [기존 StrikeReward](/home/ajou/yigyu/3/tab2body/env/rewards/strike.py:368).
5. **현재 관측과 이전 시도들의 위치:** [ObservationBuilder](/home/ajou/yigyu/3/guitar_learning/observations.py:10), [SkillObservationBuilder](/home/ajou/yigyu/3/guitar_learning/skill_environment_v2.py:61), [TimingObservationBuilder](/home/ajou/yigyu/3/guitar_learning/timing_environment.py:33). dense/specialist/skill 경로는 아래 보상 표와 함께 읽으면 된다.

## 1. 실제 재사용과 별도 구현의 경계

| 항목 | 기존 위치 | 현재 위치·관계 | 판정 |
|---|---|---|---|
| 곡 bundle·현/프렛/손가락·press/release·방향·traversal 정본 | `tab2body/full/events.py`, `env/strike_goal_compiler.py` | `music_task.py` → `fresh_music_v1/events.py`가 기존 compiler 파일을 실제 로드·실행 | **실제 실행 코드 재사용** |
| 현재 학습 목표·토큰·매칭 이력 | 기존 canonical event·기존 task별 입력 | 새 `ScoreTarget`, `ScoreTask`, `MusicLedger`, `TaskMeasurement` | 정본 정보를 새 계약으로 투영·별도 판정 |
| 압현 | `tab2body/env/rewards/fret.py:FretReward` | `fretting_v1.measure_sample`의 native 접촉 feature 검사 | 기존 보상 클래스 호출 아님; 판정 방식도 다름 |
| 피크의 현 통과 | `env/strike_detector.py:swept_point_string_segments`, `PickStrikeDetector` | `guitar_learning/strike.py:StrikeDetector` | 주석에 명시된 NumPy transcription; 실행 시 기존 detector import 아님 |
| fret/strike 학습 보상 | `FretReward.compute`, `StrikeReward.compute` | `TrainingEnvironment`, dense/specialist/skill/timing/actionable 각 보상 | 기존 클래스 전체 이식 아님 |
| 고정 기타 환경 | `tab2body/env/base.py:GuitarEnvBase` | 기존 초기 자세 runtime의 native Scene/Controller를 사용하는 `NativeSession` | 고정 기타 base를 현재 환경으로 상속·재사용하지 않음 |

기존 base는 기타 asset의 `fix_base_link=True`, `disable_gravity=True`를 설정한다. 현재 `NativeSession`은 이 base를 가져오지 않고 초기 자세 연구의 native Scene/Controller를 사용한다고 명시한다. [기존 asset 설정](/home/ajou/yigyu/3/tab2body/env/base.py:276), [현재 물리 경계](/home/ajou/yigyu/3/guitar_learning/native_session.py:13). 이는 이번 감사에서 자유 기타 물성을 새로 실험했다는 뜻은 아니다.

## 2. 음악 목표와 입력은 어떻게 바뀌었나

`ScoreTask.from_bundle`은 `load_music_task`를 직접 import한다. 그 함수의 `_compiler()`는 `tab2body/full/events.py`를 `importlib.util.spec_from_file_location`으로 실행한다. canonical compiler는 `tab2body.env.strike_goal_compiler`의 함수를 실제 import한다. 단순히 비슷한 JSON 형식을 새로 만든 관계가 아니다. [현재 import](/home/ajou/yigyu/3/guitar_learning/music_task.py:9), [실제 compiler 로드](/home/ajou/yigyu/3/stability_adapter_2/fresh_music_v1/events.py:20), [compiler 내부 import](/home/ajou/yigyu/3/tab2body/full/events.py:18).

원 bundle의 `mapping/fingering.json`, `training/fret_training.json`, `training/strike_plan.json`에서 정본 event를 만든다. fret의 dense 학습 frame을 곡 목표로 그대로 쓰는 것이 아니라 source-note identity가 맞는 press/release 시각을 사용한다. 현재는 선택한 event의 audible `string_targets`를 `ScoreTarget`으로 바꾸며 event ID·현·프렛·손가락·방향·onset/end/press·원시각·provenance를 보존한다. [정본 입력 파일](/home/ajou/yigyu/3/tab2body/full/events.py:1004), [현재 목표 투영](/home/ajou/yigyu/3/guitar_learning/music_task.py:100).

현재 policy가 raw audio를 받는 것은 아니다. 입력은 곡 bundle에서 만든 음악 목표와 현재 물리 상태다. `fresh_music_v1`의 별도186차원 encoder를 현재 정책 입력으로 그대로 쓰는 것도 아니다. `ScoreTask`가 새24필드 event token·최대64개·현재/가장 가까운 strict deadline의 우선 슬롯2개를 구성한다. `TaskMeasurement`는 현재 움직이는 기타 좌표계의 목표 차이·속도와 실제 접촉/타현 이력을 채운다. [토큰 계약과 구성](/home/ajou/yigyu/3/guitar_learning/music_task.py:11), [현재 event 입력](/home/ajou/yigyu/3/guitar_learning/music_task.py:130), [geometry 측정](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:101).

| 입력/출력 계약 | 관련 코드 |
|---|---|
| 기존 fret-v2: 명시된420차원·제어 DOF30 계약 | [fret_v2_contract](/home/ajou/yigyu/3/tab2body/fret_v2_contract.py:17), [DOF 검사](/home/ajou/yigyu/3/tab2body/fret_v2_contract.py:83) |
| 기존 strike-v2: 명시된303차원·제어 DOF30 계약 | [strike_v2_contract](/home/ajou/yigyu/3/tab2body/strike_v2_contract.py:19), [DOF 검사](/home/ajou/yigyu/3/tab2body/strike_v2_contract.py:78) |
| 현재 기본 상태468: 실제105 DOF·기타/손 상대 상태·접촉·안전·음악·검출 이력 | [ObservationBuilder](/home/ajou/yigyu/3/guitar_learning/observations.py:22) |
| skill 상태505: 위468+명시적 skill 이력37 | [HISTORY_FIELDS](/home/ajou/yigyu/3/guitar_learning/skill_environment_v2.py:14) |
| 최신 timing/actionable 상태536: 앞505+timing 이력31 | [TimingObservationBuilder](/home/ajou/yigyu/3/guitar_learning/timing_environment.py:33) |
| 현재 행동39: LH33+RH elbow/wrist6. RH 파지·지지 관절 목표는 held | [JointTargetContract](/home/ajou/yigyu/3/guitar_learning/control.py:22) |

이 표의 기존 수치는 명시한 v2 계약 파일에 대한 값이며 과거 모든 버전이 같은 차원이었다는 뜻은 아니다. 현재 몸 전체105 DOF를 관측하는 것과105개를 모두 정책 출력으로 학습하는 것도 구분한다. 하체·몸통 지지는 별도 유한 native 제어가 담당한다.

`SkillScoreTask.tokens`는 음악 deadline 이후에도 선택 목표를 계속 보이게 한다. timing 경로는 기존 앞505의 시간 scale4/이력 count960을 유지한 채 timing31을 붙인다. actionable에서는 native 정착2초를 없애고 policy pre-roll을1→3초, 정책 horizon을5→7초로 바꾸었지만 절대 물리 목표시각과 총7초는 유지한다. 이 입력 시간·실제 시작상태의 변화가 행동 성능까지 보존한다는 뜻은 아니다. [항상 보이는 목표](/home/ajou/yigyu/3/guitar_learning/skill_environment.py:57), [실행 목표 시간 이동](/home/ajou/yigyu/3/guitar_learning/timing_environment.py:19), [actionable 계약](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:14).

## 3. 압현: 기존 오압현 억제를 그대로 가져오지 않았다

이전 `FretReward`는 손가락 segment의 기하 pad-depth+hysteresis로 현×손가락×프렛의 압현 상태를 만들었다. 목표보다 높은 프렛과 NO_PRESS 현의 금지 압현을 검사하고, 목표 압현이 있어도 wrong press가 있으면 성공을 무효화하며 별도 감점한다. 현재는 실제 native 접촉 쌍의 양성lambda·witness·지정 손가락2/3·최근접 목표 현·목표 fret cell±2mm를 검사한다. [이전 geometric press](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:1920), [이전 금지와 veto](/home/ajou/yigyu/3/tab2body/env/rewards/fret.py:932), [현재 접촉 조건](/home/ajou/yigyu/3/guitar_learning/fretting_v1.py:86).

현재 잘못된 feature의 `wrong_finger...`, `wrong_fret...`, `wrong_string...` 이유는 그 feature를 거절하는 기록이다. 전체 오압현 class나 오압현 패널티가 아니다. 목표 feature가 하나라도 유효하면 다른 잘못된 접촉이 함께 있어도 후보는 참이다. 직접 이식되지 않은 부분은 전현·전프렛의 금지 압현 veto, NO_PRESS 보상 균형, 오압현 회피·감점, 이전 finger-arch/thumb/다음 목표 관련 보상 전체다.

열린현은 일반 `TaskMeasurement`에 손가락 obstruction을 검사하는 분기가 있지만, 최신 actionable timing 환경은 단일 fretted target만 허용한다. 이전의 fret0=DONT_CARE와 현재 음악 fret0=열린현도 다르다. 목표 후보·오압현·미압현과 최신 실제 접촉 분모는 [압현 감사 최신 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/fret_audit_v2.md)에 정리했다.

이전 감사의 정정도 유지한다. 거절 feature 하위집합에는 같은2번현의 더 높은 명목 cell 기록이0이었지만, 유효 여부를 제한하지 않은 전체 좁은 기하 필터에는 cell8의 유효 feature1,843개가 있었다. 접촉 body는 `G:fret7`이고 기존±2mm margin 안이므로 이것을 실제8프렛 음향 오류로 인증하지 않는다. 이번 문서는 동일1,680표본 trace를 다시 집계하지 않고 [정정 근거](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_pick_fret_audit_v1/correction_v2.json)를 재사용했다.

## 4. 타현: 기하 검출은 대응하지만 task·보상은 축소·변경되었다

현재 `strike.py`는 기존 swept point–finite string 검출의 NumPy transcription이라고 소스에 명시한다. 실제 import는 자체 geometry helper뿐이며 기존 Torch `PickStrikeDetector` 객체를 실행하지 않는다. 현재는 각 표본의 기타-root frame에서 이전/현재 피크를 표현하고 선형 상대 sweep을 계산한다. 이는 물리 구간 내 선형 근사이며 실제 현 충돌·진동·소리나 일반적인 연속 충돌 검출을 보장하지 않는다. [현재 명시적 출처 주석](/home/ajou/yigyu/3/guitar_learning/strike.py:1), [상대 좌표 sweep](/home/ajou/yigyu/3/guitar_learning/geometry_v1.py:97).

| 항목 | 기존 strike | 현재 |
|---|---|---|
| 통과 기하 | `swept_point_string_segments`: 유한 xy 교차·속도·최소 깊이. zone 품질/허용 여부는 별도 반환 | 별도 NumPy 구현. 최소속도.05m/s,깊이1~15mm,허용y−.385~−.255m,wait-rearm를 모두 eligible event 조건으로 사용 |
| 반복 검출 억제 | `PickStrikeDetector`: WAIT_REARM·최소 complete control frame 수·3D 분리거리. 막힌 통과를 `blocked_wait_rearm`로 반환 | 최소2 **240Hz physics step**와3mm 분리. 탈락은 `crossing_candidates`의 이유로 남고 eligible `crossings`와 분리 |
| 준비 상태 | 기존 task는 ready 위치+grip success의 latch 및 준비 후 접근 단계, prepared/unprepared hit 구분 | 별도 skill ready 경로는 있으나 최신 timing 성공은 ready latch/grip 획득을 필수로 요구하지 않음. 현재는 live guide 접근 보상 사용 |
| 여러 줄 순서 | 기존 task가 traversal mask·방향·통과 순서·중복·완료·strum timing/회복 검사 | 최신 timing은 단일 목표 현/방향/시간창의 유일한 통과. 이전 전체 ordered-strum task가 현재에 동등하게 작동하는 것은 아님 |
| 오타현 범위 | unplanned·wrong direction·order·duplicate·blocked wait-rearm·supervisor-blocked를 합쳐 wrong count | eligible 통과만 ledger에 들어감. 현재 시간창/방향/현 불일치와 추가 매칭 통과를 별도 감점. depth/zone/wait-rearm 탈락 자체에 이전과 같은 개별 감점은 없음 |

근거: [기존 detector 원리](/home/ajou/yigyu/3/tab2body/env/strike_detector.py:300), [기존 rearm](/home/ajou/yigyu/3/tab2body/env/strike_detector.py:489), [현재 event 조건](/home/ajou/yigyu/3/guitar_learning/strike.py:79), [현재 rearm](/home/ajou/yigyu/3/guitar_learning/strike.py:94), [기존 ready/grip latch](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3720), [기존 ordered release](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3830), [기존 wrong count](/home/ajou/yigyu/3/tab2body/env/tasks/task_strike.py:3985), [현재 완화 타현 매칭](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:154).

현재 두 개의 음악 판정도 구분해야 한다.

- 원 `MusicLedger.crossing`은 목표 현·방향·±50/100ms에 더해 앞뒤 유효 왼손 접촉을 요구한다. `TaskMeasurement`는 여기에 매칭되지 않은 eligible event를 원 wrong crossing으로 집계한다. [원 매칭](/home/ajou/yigyu/3/guitar_learning/music_task.py:233), [접촉조건 전달](/home/ajou/yigyu/3/guitar_learning/task_measurement.py:154).
- 최신 `TimingLedger`의 우손 단계는 왼손 성공과 독립이다. 현재 stage1의±.5초 안에 목표 현/방향이 한 번 지나면 성공 후보가 되고, 추가 창 안 매칭에는−.02, 창 밖/다른 현/반대 방향에는−.1, 기한까지 미달에는−.5다. 완주·물리 안전을 통과해야 최종 단계 성공이다. [현재 계수](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:25), [현재 crossing 처리](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:167), [최종 성공](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:225).

따라서 원 joint music의 wrong/miss 수치와 별도 손 단계의 wrong/miss 수치는 의미와 보상 경로가 다르다.

## 5. NO_STRIKE·준비·뮤팅은 어디에 남았나

검사한 기존 `StrikeTask`·`StrikeReward`·detector·goal compiler에서 독립적인 `NO_STRIKE` enum/class를 확인한 것은 아니다. 이전에는 계획에 없는 현/방향/순서의 통과, 준비 전 hit, 이른 release, timing wait, miss, recovery를 각각 처리했다. 그 기능이 모두 새로운 이름의 NO_STRIKE 보상으로 유지된 것은 아니다. [기존 준비·대기 보상](/home/ajou/yigyu/3/tab2body/env/rewards/strike.py:425), [기존 unprepared/wrong/miss/early 감점](/home/ajou/yigyu/3/tab2body/env/rewards/strike.py:539), [기존 recovery](/home/ajou/yigyu/3/tab2body/env/rewards/strike.py:517).

현재도 eligible 오타현을 벌하는 제한적인 억제는 있다. 하지만 명시적인 쉼표별 “타현하지 말아야 하는 시간/현” 목표 전체, 기존 준비 latch를 만족해야만 hit 인정하는 규칙, 순서가 있는 전체 strum/회복 계획을 동등하게 이식한 상태는 아니다. detector의 재무장과 task의 회복 동작 계획도 서로 다른 기능이다.

뮤팅은 특히 정보 보존과 행동 감독을 구분해야 한다. canonical compiler에는 `audible_strings`, `traversal_strings`, `protected_strings`가 구분되어 있고, **통과하지만 muted인 현은 audible `string_targets`에 포함되지 않는다.** 이전 `StrikeGoalSequence`는 audible/traversal mask를 각각 구성하고 task는 traversal 순서를 처리한다. [정본 audible 의미](/home/ajou/yigyu/3/tab2body/full/events.py:186), [정본 세 가지 현 목록](/home/ajou/yigyu/3/tab2body/full/events.py:305), [이전 mask 구성](/home/ajou/yigyu/3/tab2body/env/strike_goals.py:370).

현재 `ScoreTask.from_bundle`의 학습 대상은 이 audible `string_targets`의 투영이다. non-audible traversal/protected 현을 위한 별도 ScoreTarget·토큰·muting 성공 조건을 만들지 않는다. source hash/provenance·정본 timeline에 원 정보가 있다는 사실이 현재 정책이 같은 정보를 입력으로 받고 뮤팅을 학습한다는 뜻은 아니다. 현재 이 투영을 다중 줄 과제로 확장하면서 muted 중간 현을 단순 wrong crossing으로 다루면 의미가 어긋날 수 있지만, 그 변경·새 기준 설계는 이번 감사에서 하지 않았다.

일반 열린현 obstruction 진단이나 예전 fret의 NO_PRESS도 실제 음향 뮤팅의 인증과 같지 않다. 현 압력·진동·음향은 이전 코드와 현재 코드의 이번 정적 비교로 검증할 수 없다.

## 6. 현재 보상 경로별로 무엇이 누적·교체되는가

아래 경로를 모두 동시에 누적하는 구조가 아니다. `DenseTrainingEnvironment`와 `SpecialistTrainingEnvironment`는 별도 환경 경로이며, 최신 `TimingEnvironment`는 skill-v2를 상속한다. dense의 guide helper와 SpecialistLedger를 일부 사용한다고 그 환경 클래스의 모든 보상이 누적되는 것은 아니다.

| 경로 | 실제 보상 처리 | 읽을 위치 |
|---|---|---|
| `TrainingEnvironment` | strict1/lenient-only.25/wrong crossing−.25/strict miss−.5/audible hold2/s/timely release.25/거리 approach/action-change/물리 실패 | [기본 계수](/home/ajou/yigyu/3/guitar_learning/training_environment.py:12), [실제 합산](/home/ajou/yigyu/3/guitar_learning/training_environment.py:125) |
| `DenseTrainingEnvironment` | 기본 보상에 LH early distal-origin 접근·RH guide/방향 shaping을 **추가** | [shaping](/home/ajou/yigyu/3/guitar_learning/dense_environment.py:74), [추가 합산](/home/ajou/yigyu/3/guitar_learning/dense_environment.py:119) |
| `SpecialistTrainingEnvironment` | 손별 목표: LH 접촉/유지, RH 독립±50/100ms. 한 손 경로는 action-change/물리 실패만 남기고 **교체**. joint는 기본 보상 유지 | [독립 ledger](/home/ajou/yigyu/3/guitar_learning/specialist_environment.py:65), [경로 선택](/home/ajou/yigyu/3/guitar_learning/specialist_environment.py:250) |
| `SkillTrainingEnvironment` | LH reach/contact/hold/timed, RH ready/cross/timed. action-change/물리 실패만 남기고 **교체** | [단계 ledger](/home/ajou/yigyu/3/guitar_learning/skill_environment.py:125), [보상 교체](/home/ajou/yigyu/3/guitar_learning/skill_environment.py:297) |
| `SkillTrainingEnvironmentV2` | 위 의미를 유지하며 숨은 달성·유지 이력을 입력에 명시. 새로운 기존 fret 보상 import 아님 | [관측 이력](/home/ajou/yigyu/3/guitar_learning/skill_environment_v2.py:35) |
| `TimingEnvironment` | action-change/물리 실패만 남기고 고정 시간창의 획득·유지·성공·정밀도·miss·오타현·추가통과·RH guide로 **교체**. 원 music ledger는 측정용으로 유지 | [timing 처리](/home/ajou/yigyu/3/guitar_learning/timing_curriculum.py:118), [다시 교체](/home/ajou/yigyu/3/guitar_learning/timing_environment.py:131) |
| 최신 `ActionablePreparationEnvironment` | 위 timing 보상에 첫2초 LH 원 candidate의 이전/현재 연속 양성 구간×.2/s만 **추가**. 안전 실패 tick의 양성 추가량은0 | [최종 준비 접촉](/home/ajou/yigyu/3/guitar_learning/actionable_preparation_environment.py:53) |

최신 경로에는 이전 fret의 적극 오압현 패널티, 이전 strike의 grip/ready latch 기반 unprepared hit 감점, 전체 ordered strum/recovery 보상이 그대로 있지 않다. `release` 이력은 남아 있지만 최신 timing의 명시적 해제 보상은 없다. 왼손 stage1은 확장 press/end 창 안의 연속 유지 성공이며 전체 audible 구간·적절한 해제·다음 프렛 전환을 모두 강제하지 않는다. 실제 평가에서 audible coverage를 별도로 확인한 결과와 보상식 자체의 보장을 구분한다.

## 검증 자료와 한계

이번 감사는 소스의 함수·라인·AST import와 직전 압현 감사v2를 확인했다. 기존 파일의 SHA를 [legacy_music_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_code_lineage_audit_v1/legacy_music_v1.json)에 기록했다. direct import가 없는 점은 검사한 핵심 모듈에 대한 근거이며 모든 과거 파일·모든 실행 버전에서 존재하지 않았다는 역사적 주장은 아니다.

현재 연결이 의도와 다르게 보이는 기능은 미이식·축소·별도 측정 항목으로 구분했다. 자동으로 코드를 복원하거나 보상·성공 판정을 변경하지 않았다. 이번 감사만으로 새로운 학습 성과, 양손 동시 음악 성공, pressure/audio·뮤팅·일반화를 주장하지 않는다.
