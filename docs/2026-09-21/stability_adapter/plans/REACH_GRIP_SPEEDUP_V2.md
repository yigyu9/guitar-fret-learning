# REACH·GRIP 시간 단축 구현 계획 v2

작성일: 2026-09-28  
대상: `stability_adapter/reach_*`, `grip_*`  
목표: WAIT 종료 후 functional GRIP까지의 시간을 현재 약 111초에서 12~18초 수준으로 단축

## 1. 전제와 범위

이번 작업은 성공 판정을 느슨하게 만들어 영상을 짧게 만드는 작업이 아니다. 다음 조건은 유지한다.

- 자유 기타, 중력 ON, 기존 `strapped-v1` 스트랩 유지
- 손바닥 위 방향과 넥 아래쪽 접근 provenance 유지
- 실제 thumb normal force와 최소 두 opposing digit force 요구
- 과압, proximal collision, strap failure, 기타 낙하 종료 조건 유지
- WAIT는 학습/가속 대상에서 제외
- Fret/Strike/Synchronizer handoff는 이번 범위에서 제외

현재 측정 기준:

| 구간 | 현재 frame | 현재 시간 |
|---|---:|---:|
| REACH | 1,077 | 17.95 s |
| WRAP | 909 | 15.15 s |
| GRIP_CLOSE | 4,668 | 77.80 s |
| REACH+GRIP | 6,654 | 110.90 s |
| thumb TOUCH | 3,675 | 61.25 s |

최대 병목은 학습 update 수가 아니라 엄지가 실제 접촉 없이 TOUCH/retry에 머무는 현상이다.
따라서 teacher가 실제 힘을 만들기 전에 learned policy를 다시 장기 학습하지 않는다.

## 2. 목표 성능과 승급 기준

### 2.1 1차 teacher 목표

WAIT terminal snapshot에서 seed 17 기준:

| 지표 | 목표 |
|---|---:|
| REACH | `<= 480 frame` / 8 s |
| WRAP | `<= 360 frame` / 6 s |
| GRIP_CLOSE | `<= 240 frame` / 4 s |
| REACH+GRIP | `<= 1,080 frame` / 18 s |
| thumb TOUCH 진입 후 실제 force 발생 | `<= 180 frame` |
| thumb distal normal force | `1~8 N` |
| 유효 opposing digit | 최소 2개 |
| opposing normal-force 합 | `1.5~16 N` |
| functional dwell | 8 frame 유지 |
| acquisition overload | 0 frame |
| environment failure | 0 |

### 2.2 반복 안정성 목표

단일 성공 후 바로 학습하지 않는다.

- 같은 초기환경 seed 17 반복 실행 10회 중 10회 functional GRIP
- 허용된 작은 초기 관절 perturbation을 넣은 20회 중 18회 이상 성공
- p95 REACH+GRIP 시간이 1,200 frame 이하
- thumb retry 평균 0.5회 이하, 최대 2회
- 접촉 형성 순간 conservative hand load `<= 40 N`
- 모든 성공에서 trace/video/report SHA와 controller source hash 저장

## 3. 전체 구현 순서

```text
P0 계측 기준선 고정
  -> P1 thumb collision-mesh proxy와 force-onset 교정
  -> P2 조건 기반 thumb TOUCH/재시도 단축
  -> P3 primary tripod WRAP/GRIP
  -> P4 REACH 3-zone 가속
  -> P5 deterministic teacher 반복 검증
  -> P6 stage-balanced residual 학습
  -> P7 WAIT-starting 전체 검증
```

P1이 통과하지 않으면 P2 이후로 진행하지 않는다. 실제 힘이 없는 상태에서 dwell과 timeout만
줄이면 성공 시간이 아니라 실패 시간만 짧아진다.

## 4. P0 — 계측 기준선 고정

### 4.1 목적

REACH 내부 phase와 GRIP 세부 stage별 시간이 현재 trace에 충분히 드러나지 않는다. 상수를 바꾸기
전에 어느 gate가 시간을 쓰는지 frame 단위로 고정한다.

### 4.2 구현

`reach_learning.py`:

- `SafeReachTeacher.phase`의 숫자값을 이름 있는 상수로 변경한다.
- 외부 진단용 `phase_name` property를 추가한다.
- 매 frame 다음 값을 노출한다.
  - `reach_teacher_phase`
  - palm-to-target 거리
  - below distance와 under/palm-up/heading cosine
  - relative/guitar speed
  - stage settle streak
  - contact offset
  - commanded joint-step max
  - phase 전환 reason

`record_reach_diagnostic.py`, `record_grip_teacher_full_sequence.py`:

- REACH trace에도 위 필드를 기록한다.
- phase별 frame count와 최초/최종 frame을 report에 집계한다.
- WAIT→REACH snapshot 전환은 기존처럼 별도 boundary event로 유지한다.

`grip_learning.py`, `record_grip_diagnostic.py`:

- 기존 thumb stage 외에 palm-align, palm-contact, primary wrap, auxiliary wrap, force-acquire 시간을
  별도 집계한다.
- retry 시작/종료/소진 frame과 당시 thumb3 calibrated contact gap을 기록한다.

### 4.3 검증

- 기존 teacher action과 state transition이 바뀌지 않아야 한다.
- 기존 seed 17 trace의 REACH/WRAP/TOUCH 총 frame 수가 계측 오버헤드 외에는 동일해야 한다.
- trace timing은 controller pre-step과 physics post-step을 명시적으로 구분한다.

## 5. P1 — thumb collision-mesh proxy와 force-onset 접점 교정

### 5.1 문제

현재 pad proxy gap은 0.30 mm까지 감소하지만 thumb normal force는 0 N이다. 가능한 원인은 다음과
같다.

- `PAD_BODY_LOCAL_M` 점이 실제 thumb collision 표면을 대표하지 않음
- rear-face plane과 cooked convex collider 면의 차이
- contact offset이 proxy gap에 포함되지 않음
- pad point는 patch 안이지만 cooked PhysX collider의 실제 접촉면은 proxy와 다름
- thumb3이 아니라 thumb1/2가 먼저 제한되거나 다른 물체와 접촉함

### 5.2 새 기하 진단

Isaac Gym은 runtime에서 cooked PhysX convex vertex를 직접 제공하지 않는다. 따라서 STL에서 계산한
점은 **cooked collider의 정확한 표면**이 아니라 authored collision-mesh proxy로 취급한다. 실제 접촉의 source of
truth는 GPU rollout의 측정 force onset이다.

`grip_env.py`에 실행 중 계산용 기하를 추가한다.

1. `thumb1_left.stl`, `thumb2_left.stl`, `thumb3_left.stl` vertex를 로드한다.
2. MJCF의 thumb mesh scale `1, 0.95, 0.95`를 적용한다.
3. 각 geom의 body-local pose를 적용한다. 특히 thumb2/3의 local offset을 누락하지 않는다.
4. rigid-body pose로 proxy vertex를 world frame으로 변환한다.
5. guitar root 역변환으로 guitar-local proxy vertex를 계산한다.
6. distal thumb3은 lateral/axial patch 안의 vertex에서 rear-face plane signed distance를 계산한다.
7. proximal thumb1/2는 별도 금지 영역까지의 clearance를 계산한다.
8. distal 접촉 gap과 proximal clearance를 절대 하나의 minimum으로 합치지 않는다.

새 진단 필드:

```text
thumb_pad_proxy_gap_m
thumb3_mesh_proxy_gap_m
thumb3_calibrated_contact_gap_m
thumb3_proxy_closest_point_guitar_local[3]
thumb3_proxy_closest_point_in_patch
thumb1_2_proxy_clearance_m[2]
thumb1_2_forbidden_region[2]
thumb_raw_force_n
thumb_normal_force_n
thumb_first_force_frame
```

실제 제어에는 아직 사용하지 않고 첫 단계에서는 관측만 한다.

### 5.3 저속 contact sweep

`tools/calibrate_grip_contact_surfaces.py`에 thumb rear-face sweep mode를 추가한다.

calibration 전에도 적용할 수 있는 절대 hard bound를 먼저 고정한다.

| hard bound | 값 | 동작 |
|---|---:|---|
| thumb3 mesh-proxy plane penetration | 최대 0.5 mm | 즉시 hold/retreat |
| 기존 pad-proxy plane penetration | 최대 0.5 mm | 즉시 hold/retreat |
| sweep 시작점 이후 forward travel | 최대 5 mm | 실패 종료 |
| thumb distal force | 6 N | 즉시 retreat/abort |
| thumb1/2 proximal raw force | 0.05 N | 즉시 hold/retreat |
| thumb1/2 mesh-proxy clearance | 최소 1.0 mm | 전진 금지/retreat |

`0.05 N` proximal 기준은 현재 safety-release clear threshold와 같고, `6 N` distal 기준은 현재
thumb force abort와 같다. authored proxy가 cooked collider와 다를 수 있으므로 clearance와 measured
force 중 하나라도 위험이면 더 보수적인 동작을 선택한다.

- ALIGN/RAIL이 완료된 고정 자세에서 distal thumb target만 단계적으로 전진
- step당 authored-mesh proxy gap 감소량을 `0.1~0.2 mm`로 제한
- 각 step 후 최소 10 control frame의 저속 settle을 수행
- calibration sample은 마지막 5 frame이 아래 조건을 모두 만족할 때만 수락
  - guitar linear speed `<=0.006 m/s`
  - guitar angular speed `<=0.03 rad/s`
  - thumb-guitar relative speed `<=0.006 m/s`
  - 5-frame guitar displacement `<=0.5 mm`
- 최초 `0.2 N`, `0.5 N`, `1.0 N` force 발생 위치 기록
- proximal force, 다른 손가락 force, guitar displacement도 함께 기록
- thumb1/2 clearance가 `1.0 mm` 아래로 내려가면 distal sweep을 즉시 hold/retreat
- force가 발생하지 않으면 위 absolute penetration/forward-travel hard bound에서 중단하고 실패
  원인을 기록

### 5.4 목표점 재보정

sweep 결과에서 안정적인 `1~2 N` 접촉이 발생하는 pose를 새 acquisition calibration JSON에 저장한다.

- thumb target local point
- authored-mesh proxy closest point와 적용한 scale/geom pose
- pad normal
- rear-face plane
- force-onset으로 실측한 proxy-to-contact offset과 반복 분산
- raw proxy 기준 force-onset gap
- `calibrated_gap = raw_proxy_gap - force_onset_proxy_gap`
- `rail_exit_gap_raw = force_onset_proxy_gap + 4 mm`
- `contact_bias_gap_raw = force_onset_proxy_gap + 1 mm`
- asset/collision mesh SHA
- controller source SHA

`DIGIT_TARGET_LOCAL_M[0]`, `THUMB_HOVER_TARGET_LOCAL_M`을 코드에 임의로 직접 조정하지 않고 이
calibration 산출물에서 로드하도록 바꾼다. 기존 JSON과 schema가 다르면 환경 생성을 거부한다.

### 5.5 P1 통과 기준

- 저속 sweep 5회 모두 thumb normal force `>=1 N`
- proximal thumb1/2 force가 `0.05 N` 미만이고 proxy clearance가 `1.0 mm` 이상
- 수락한 calibration sample의 선속도 `<=0.006 m/s`, 각속도 `<=0.03 rad/s`
- 수락 window의 thumb-guitar relative speed `<=0.006 m/s`
- 수락 window의 guitar displacement `<=0.5 mm`
- 최대 conservative hand load `<=40 N`
- proxy gap과 실제 force onset의 차이를 설명하는 offset이 반복 실행에서 `<=0.5 mm` 변동

## 6. P2 — thumb TOUCH와 retry 단축

P1 통과 후 `GripTeacher`의 TOUCH 상태를 기존 단일 pad gap이 아니라, force sweep으로 검증한
distal `thumb3_calibrated_contact_gap_m` 중심으로 변경한다. 이 값은 cooked collider의 exact
distance가 아니라
authored-mesh proxy에 실측 force-onset offset을 적용한 제어용 거리다. 실제 force는 항상 최종
접촉 source of truth로 유지한다. thumb1/2 clearance는 진행값에 섞지 않고 독립 safety gate로
사용한다.

### 6.1 RAIL 종료

현재 `THUMB_RAIL_FRAMES=180`의 고정 시간을 다음 조건으로 대체한다.

```text
rail_ready =
    stage_frames >= 12
    and calibrated_contact_gap <= 4 mm
    and alignment >= 0.80
    and thumb1_2_clearance >= 1.0 mm
    and proximal_force < 0.05 N
```

- 정상 geometry면 즉시 TOUCH로 전이
- 최대 60 frame이 지나도 준비되지 않으면 ALIGN으로 rollback
- 60 frame을 채웠다는 이유만으로 TOUCH에 진입하지 않음

### 6.2 TOUCH 진행

거리 구간별 target/measured envelope은 유지하되 검증된 calibrated contact gap을 사용한다.

```text
gap > 4 mm: 0.8 deg
2~4 mm: linear taper
gap <= 2 mm: 0.3 deg
alignment < 0.75: normal advance 정지
alignment >= 0.80: normal advance 허용
```

contact bias는 다음 모든 조건에서만 활성화한다.

- calibrated contact gap `<=1 mm`
- alignment `>=0.80`
- closest point가 patch 내부
- thumb1/2 clearance `>=1.0 mm`
- thumb1/2 proximal force `<0.05 N`
- retry 중이 아님

force가 `0.2 N`을 넘으면 gap drive를 멈추고 LOAD force servo로 넘긴다.
thumb1/2 clearance가 1.0 mm 아래로 내려가거나 proximal force가 0.05 N 이상이면 distal gap과
무관하게 즉시 hold/retreat하며 contact bias를 금지한다. P1의 0.5 mm penetration, 5 mm travel,
6 N distal hard bound도 runtime TOUCH에서 그대로 유지한다.

### 6.3 stall/retry

초기 제안값:

| 항목 | 현재 | 변경 후보 |
|---|---:|---:|
| stall window | 300 | 60 frame |
| minimum progress | 0.5 mm | 0.25 mm |
| retry retreat | 2 mm | 1 mm |
| retry duration | 120 | 30 frame |
| max retry | 3 | 2 |

stall은 단순 gap 변화만으로 판정하지 않는다.

```text
stalled =
    no force onset
    and calibrated-contact-gap progress < 0.25 mm / 60 frame
    and target/measured error is inside active envelope
```

actuator가 아직 target을 추종 중이면 retry를 시작하지 않는다. retry 종료 후 TOUCH ramp와 anchor를
재설정한다. 2회 소진 시 teacher flag를 내고 collector가 실패로 종료한다.

### 6.4 검증

- 기존 safety-release가 retry보다 항상 우선한다.
- force가 생긴 뒤에는 retry가 시작되지 않는다.
- retry가 thumb 외 관절 target을 바꾸지 않는다.
- unit test에서 exact boundary frame과 최대 retry 소진을 확인한다.

## 7. P3 — primary tripod WRAP/GRIP

### 7.1 목적

functional transport에 필요한 최소 지지는 thumb와 opposing finger 2개다. ring/pinky hover 완료를
기다리느라 functional acquisition을 지연시키지 않는다.

### 7.2 phase 구조는 유지

checkpoint/observation schema 변경을 최소화하기 위해 `GRIP_PHASES` 8개와 8D one-hot은 유지한다.
새 phase를 추가하지 않고 phase 3/4의 gate만 primary 기준으로 바꾼다.

```text
primary digits   = thumb, index, middle
auxiliary digits = ring, pinky
```

### 7.3 WRAP_FINGERS 변경

현재 한 손가락씩 처리하는 `active_digit_mask()`를 다음처럼 변경한다.

- free-space pre-shape: index/middle을 동시에 이동
- 접촉 capture band 진입: index 먼저, middle 다음으로 순차 contact
- ring/pinky는 collision-free hover target까지만 이동
- phase 3 종료는 thumb/index/middle hover latch로 판정
- ring/pinky latch는 phase transition을 막지 않음

환경의 hover loss rollback도 primary와 auxiliary를 분리한다.

- primary 손실: 기존처럼 이전 phase rollback
- auxiliary 손실: diagnostic만 기록하고 acquisition은 계속
- auxiliary proximal/overforce: 해당 digit만 measured hold로 release

### 7.4 GRIP_CLOSE 변경

필수 force owner 순서:

```text
index -> middle -> thumb
```

thumb가 force band에 들어오고 functional candidate가 8 frame 유지되면 acquisition 완료로 판정한다.
ring/pinky는 이후 background 보강 대상으로 남기되 TRANSPORT 진입을 막지 않는다.

strict all-five success는 제거하지 않는다. strict promotion 경로는 기존대로 다섯 손가락과 pad/pair
검증을 요구하고, 빠른 runtime 경로만 functional boundary를 사용한다. 환경은
`primary_functional_ready`와 `all_five_ready`를 별도 상태로 유지한다. runtime은 전자에서
TRANSPORT로 넘어갈 수 있고, strict 진단 모드는 계속 실행하여 ring/pinky 보강과 후자를 확인한다.

### 7.5 기대 시간

- palm align/contact: 120~180 frame
- primary wrap: 120~180 frame
- primary force acquire: 60~120 frame
- 총 WRAP+GRIP: 300~480 frame, 5~8초

## 8. P4 — REACH 3-zone 가속

P0 trace로 실제 병목 phase를 확인한 뒤 거리별 step 제한을 조정한다.

### 8.1 제어 구간

```text
FAR:      palm-target distance > 12 cm
APPROACH: 4~12 cm
CONTACT:  <=4 cm 또는 contact candidate 발생
```

초기 후보값:

| 구간 | joint step | action delta | 목적 |
|---|---:|---:|---|
| FAR | 0.018 rad | 0.035 | 빠른 아래쪽 staging |
| APPROACH | 0.010 rad | 0.018 | moving-neck 추적 |
| CONTACT | 0.002~0.003 rad | 0.003~0.005 | 현재 compliance 유지 |

현재 FAR `0.012`, staging `0.006`, contact `0.002~0.003`보다 먼 구간만 가속한다. 접촉 구간은
속도를 올리지 않는다.

### 8.2 안전한 가속 조건

FAR/APPROACH 가속은 다음 조건을 모두 만족할 때만 사용한다.

- palm이 underside corridor 안에 있음
- guard radius 밖이거나 올바른 아래쪽 provenance가 이미 확인됨
- palm/digit contact force가 noise floor 이하
- 기타 속도가 hard safety 범위 안
- DLS condition diagnostic이 유효
- Torso/L_Thorax excursion budget 안

조건이 깨지면 즉시 기존 보수 step으로 fallback한다.

### 8.3 settle dwell

`REACH_STAGE_SETTLE_DWELL=45`를 무조건 줄이지 않는다. 다음 adaptive dwell을 사용한다.

- 최소 15 frame 연속으로 현재 velocity gate 만족
- 기타 선·각속도가 threshold의 절반 이하이면 15 frame에서 통과
- threshold의 절반~상한이면 최대 45 frame 유지
- 한 frame이라도 상한 초과 시 streak 0
- 최종 REACH capture hold 60 frame은 유지

### 8.4 IK target

FAR 구간에서는 seed 17 기준 collision-free below-neck joint target을 초기 seed로 사용할 수 있지만,
live guitar pose 오차는 task-space DLS가 계속 보정한다. 고정 world joint trajectory만 replay하지 않는다.

### 8.5 환경 manifest 재봉인

`INITIAL_ENVIRONMENT.json`은 `reach_env.py` SHA를 검증하므로 P4 코드 변경과 manifest 갱신은 같은
작업 단위로 처리한다.

1. 변경 후 `reach_env.py` SHA-256 계산
2. `INITIAL_ENVIRONMENT.json.runtime.environment_impl_sha256` 갱신
3. `load_initial_environment_profile(verify_files=True)` 통과 확인
4. release factory와 reach-boundary factory를 각각 생성·종료하는 smoke 실행
5. 새 environment identity를 teacher report와 이후 checkpoint에 기록

환경 identity가 바뀌므로 과거 REACH/GRIP checkpoint를 그대로 평가하지 않는다. P4 이후의 teacher
기준선과 P6 학습 checkpoint는 모두 새 identity로 다시 생성한다.

## 9. P5 — deterministic teacher 검증

학습 전에 다음 세 종류를 순서대로 실행한다.

### A. 고정 REACH snapshot

- 가장 재현성 높은 경계에서 controller 자체 성능 검증
- 10회 반복
- phase별 p50/p95 frame 기록

### B. perturbation recovery

- distal arm `±0.5°`
- thumb/index/middle action `±0.01 normalized`
- guitar pose는 snapshot 계약 범위 안에서 작은 perturbation
- 20회 실행

### C. WAIT-starting diagnostic

- release부터 WAIT를 실제 실행
- 현재는 snapshot 전환을 report에 명시
- 별도로 live WAIT terminal을 그대로 이어가는 REACH도 실행해 boundary gap을 측정
- snapshot 경로가 성공해도 live boundary가 실패하면 official end-to-end 성공으로 표기하지 않음

각 실행은 full trace, stage timing, force onset, retry, overload, terminal reason을 보존한다.

## 10. P6 — 빠른 teacher를 학습 정책으로 distill

teacher가 반복 성공한 뒤에만 수행한다.

### 10.1 데이터 구성

REACH와 GRIP은 서로 다른 관측·action·policy를 사용하므로 dataset과 optimizer도 합치지 않는다.
각 trainer 안에서 stage-balanced sampler를 사용한다.

REACH dataset:

| stage | 목표 batch 비율 |
|---|---:|
| FAR | 30% |
| APPROACH/CONTACT | 50% |
| contact hold/recovery | 20% |

GRIP dataset:

| stage | 목표 batch 비율 |
|---|---:|
| index/middle force-owner acquisition | 40% |
| thumb TOUCH | 35% |
| thumb LOAD/HOLD recovery | 25% |

PALM, WRAP, thumb CLEAR/ALIGN/RAIL은 현재 `learned_residual_action_mask()`가 의도적으로 소유권을
주지 않는 deterministic 구간이다. v1에서는 이 mask를 풀지 않으며 dataset에도 넣지 않는다.
이 구간의 속도는 teacher 개선으로만 얻는다. 향후 pre-GRIP policy가 필요하면 action ownership,
teacher target, safety fallback을 별도 schema로 설계한다.

성공 궤적뿐 아니라 다음 recovery 상태를 수집한다.

- TOUCH 진입 직후 alignment가 0.75 부근인 상태
- thumb3 calibrated contact gap 1~5 mm
- index/middle contact 한쪽이 순간적으로 끊긴 상태
- target/measured error envelope 경계
- 1회 retry 직후 상태

### 10.2 정책 구조

첫 구현은 복잡한 recurrent network를 추가하지 않는다.

- ReachPolicy와 GripPolicy는 현재처럼 별도 checkpoint로 유지
- ReachPolicy는 현재 계약대로 `prev_action + scale * model(obs)`인 순수 bounded residual로 실행
- Reach checkpoint 실행 중에는 `SafeReachTeacher.action()`이나 teacher phase를 사용하지 않음
- REACH의 성공 gate, wrong-side/contact failure, timeout과 종료 안전은 환경이 소유
- GripPolicy는 현재처럼 매 frame `GripTeacher.action()`으로 reference와 내부 phase를 갱신한 뒤,
  policy-owned hand slot에만 residual을 합성하는 hybrid 실행을 유지
- 현재 GripPolicy MLP와 stage one-hot 유지
- stage-balanced sampling
- stage별 loss weight
- GripPolicy의 현재 21D hand-action output과 masked action MSE를 유지
- GripPolicy에는 teacher reference 주변 trust region을 유지하고, ReachPolicy에는 기존 bounded residual
  scale과 action clamp를 유지

보조 예측 loss는 v1 범위에서 제외한다. 필요하면 다음 버전에서 auxiliary head, target 생성 시점,
loss weight, checkpoint schema와 runtime 소비 여부를 함께 설계한다. MLP가 반복 실패할 때만 GRU
또는 stage별 head를 검토한다.

### 10.3 runtime fallback

두 정책의 현재 실행 계약이 다르므로 fallback을 합치지 않는다.

REACH:

- 환경의 wrong-side/contact/safety gate가 action과 무관하게 매 step 판정
- unsafe termination이면 즉시 episode를 실패 종료하고 teacher로 몰래 전환하지 않음
- non-terminal stall은 trace에 기록하고 `prev_action` 기준 bounded residual을 계속 사용
- 후속 버전에서 hybrid REACH가 필요하면 teacher state update, action blending, recorder parity를 별도
  wrapper와 테스트로 먼저 구현

GRIP learned residual은 다음 조건에서 0으로 만든다.

- 적용 후 측정된 alignment가 0.75 아래로 내려감
- 측정된 thumb3 calibrated gap이 30 frame 동안 진전하지 않음
- proximal force 또는 overload 경고
- retry 시작

GRIP의 조건이 관측된 다음 frame부터 recovery dwell 동안 residual을 0으로 하고, 이미 매 frame
갱신되는 `GripTeacher` reference action만 실행한다. GripPolicy는 phase 전환과 safety gate를 소유하지
않는다. 이는 counterfactual 예측기가 아니라 post-step watchdog이다.

### 10.4 학습 승급 기준

- teacher 성공률 기준을 그대로 통과
- learned p95 시간이 teacher의 120% 이하
- learned 최소 calibrated contact gap이 teacher보다 0.5 mm 이상 악화되지 않음
- force onset frame이 teacher보다 60 frame 이상 늦지 않음
- GRIP fallback 사용률 10% 이하
- checkpoint에 source/environment/calibration hash 기록

## 11. P7 — WAIT부터 전체 시퀀스 검증

최종 평가는 중간 snapshot에서 시작한 짧은 클립이 아니라 release 직전부터 시작한다. 영상과 로그는
같은 rollout에서 생성한다.

1. 기존 `strapped-v1` 환경에서 기타 고정 해제
2. WAIT가 기타 속도 gate와 dwell을 실제로 통과
3. 학습된 ReachPolicy를 순수 bounded-residual 모드로 실행하고 gate/safety는 환경이 소유
4. 환경 `done`이나 strict success를 기다리지 않고, `reach_capture_ready(info)`가 true인
   contact-acquired hold boundary에서 GripPolicy로 handoff
5. `primary_functional_ready`가 8 frame 유지되면 GRIP 성공
6. 최소 120 frame을 더 유지하여 순간 접촉이 아님을 확인
7. 선택적으로 TRANSPORT 진입 직전까지 기록하되, TRANSPORT 성공으로 오표기하지 않음

평가 세트는 고정 seed 10개와 허용 perturbation seed 20개를 별도로 둔다. teacher-only와
learner-enabled를 동일 seed로 비교하고 다음을 보고한다.

- WAIT, REACH, WRAP, GRIP_CLOSE별 p50/p95 frame
- 실제 force onset, functional-ready, hold 완료 frame
- retry/fallback 횟수와 실패 terminal reason
- thumb 및 opposing digit force 범위, conservative hand load
- guitar 선·각속도, strap 상태, Torso/L_Thorax excursion
- teacher 대비 learner 성공률과 시간 변화

영상은 전체 성공 rollout 하나만 골라 자막 없는 MP4로 만들고, 판정 수치는 별도 JSON/README에
보존한다. 실패 rollout도 trace에서는 제외하지 않는다.

## 12. 파일별 변경 범위

| 파일 | 변경 내용 |
|---|---|
| `reach_learning.py` | named phase, 3-zone 속도, adaptive settle, diagnostics |
| `reach_env.py` | 필요한 corridor/DLS/speed 진단 노출, 안전 gate 유지 |
| `INITIAL_ENVIRONMENT.json` | 변경된 `reach_env.py` SHA와 runtime identity 재봉인 |
| `grip_env.py` | thumb mesh proxy/force-onset geometry, primary/auxiliary gate 분리 |
| `grip_learning.py` | geometry-based RAIL/TOUCH, 짧은 retry, tripod force order |
| `train_reach_pilot.py` | REACH stage-balanced sampling과 closed-loop 평가 |
| `train_grip_pilot.py` | stage-balanced sampling, stage metric, fallback 결과 저장 |
| `record_reach_diagnostic.py` | REACH phase timing trace |
| `record_grip_diagnostic.py` | calibrated gap/force onset/primary timing trace |
| `record_grip_teacher_full_sequence.py` | 전체 timing summary와 boundary 표시 |
| `calibrate_grip_contact_surfaces.py` | 저속 thumb mesh-proxy/force sweep와 calibration 출력 |
| `policy.py` | v1 구조 변경 없음 |

기존에 새 구현과 충돌하는 pad-proxy-only stall 판정, all-five WRAP blocking gate, 고정 180-frame
RAIL은 대체 시 제거한다. historical strict all-five 판정과 안전 종료는 제거하지 않는다.

## 13. 테스트 계획

### 순수 단위 테스트

- scaled/offset mesh-proxy vertex transform과 plane signed distance
- thumb3 contact gap과 thumb1/2 clearance가 섞이지 않음
- patch 내부 최근접점 선택
- contact offset 적용
- geometry-based RAIL transition
- stall이 actuator lag 중에는 발생하지 않음
- 2회 retry 정확한 소진
- primary latch는 auxiliary 없이 phase를 통과
- auxiliary 손실은 primary rollback을 유발하지 않음
- strict all-five gate는 그대로 유지
- adaptive REACH zone과 fallback 경계
- adaptive settle streak reset

### GPU smoke

1. thumb sweep 300~600 frame
2. GripTeacher 최대 1,200 frame
3. ReachTeacher 최대 600 frame
4. REACH→GRIP 최대 1,500 frame
5. WAIT-starting 전체 진단

### 회귀 검사

- strap tension/extension 결과가 기준선에서 벗어나지 않음
- Torso/L_Thorax excursion 증가 없음
- non-neck contact와 proximal force 증가 없음
- 기존 contact/transport unit test 통과
- report/video/trace SHA 일치

## 14. 산출물 구조

```text
docs/2026-09-21/stability_adapter/
  reach_grip_speedup_v2/
    calibration/
      thumb_mesh_proxy_force_sweep_v1.json
      thumb_contact_calibration_v2.json
      thumb_contact_visualization_v2.png
    teacher_trials/
      reach_profile_v1.jsonl
      tripod_grip_v1.jsonl
      repeated_validation_v1.json
    checkpoints/
      reach_speedup_residual_v1.pt
      reach_speedup_residual_v1.json
      grip_speedup_residual_v1.pt
      grip_speedup_residual_v1.json
    rollouts/
      wait_to_grip_teacher_v1.mp4
      wait_to_grip_policy_v1.mp4
      *.json
      *.trace.jsonl
    README.md
```

README에는 채택한 상수뿐 아니라 폐기한 후보와 이유도 기록한다.

## 15. 중단·rollback 조건

다음 중 하나라도 발생하면 속도 상향을 중단하고 직전 단계로 돌아간다.

- 새 calibrated contact 목표에서도 thumb force가 0 N
- thumb1/2 proximal force가 distal force보다 먼저 증가
- guitar velocity 또는 hand load peak가 기준선의 1.5배 초과
- palm/neck 이외 접촉 증가
- REACH의 wrong-side/approach violation 발생
- tripod 변경 후 transport entry support가 기존 proxy보다 약화
- learned policy가 teacher보다 성공률 5%p 이상 하락

rollback은 threshold를 임의 완화하는 것이 아니라 해당 단계의 controller/calibration만 되돌린다.

## 16. 예상 작업 단위

1. P0 계측과 기준 trace
2. P1 mesh-proxy/force-onset audit 및 calibration
3. P2 thumb state-machine 단축
4. P3 tripod acquisition
5. P4 REACH 가속
6. P5 반복 teacher 검증
7. P6 학습과 learned 검증
8. P7 전체 영상·로그·분석

각 단위는 코드 수정 → 순수 테스트 → 짧은 GPU smoke → 로그 판정 순서로 닫는다. 한 단계가 통과하지
않으면 다음 단계의 속도 상향이나 장기 학습을 진행하지 않는다.
