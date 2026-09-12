# 10. 확정 결정 기록과 남은 미결정 사항

> 상태: **MIXED — DECISION LOG + OPEN QUESTIONS**

앞부분은 확정 결정의 append-only 기록이고, 마지막 주제별 목록만 아직 결정하지 않은 사항이다.
결정이 바뀌면 기존 항목을 삭제하지 않고 `SUPERSEDED BY MP-xxx`로 표시하며 관련 contract
version을 올린다.

## 확정된 결정

### MP-001 — 하체 action과 posture reward

```text
상태: DECIDED
결정일: 2026-09-05
```

- 최종 full-body action space에는 하체 전체를 포함한다.
- 하체는 G1부터 trainable하게 한다.
- G0에서는 하체 action slot을 예약하되 hold/mask한다.
- G1에서는 초기 자세 기준 bounded residual과 joint-angle dead-zone reward를 사용한다.
- G2에서는 하체 residual authority를 확대하고 artificial assist를 0으로 만든다.
- 하체 posture reward와 기타 stability reward는 분리한다.
- 평상시 하체가 초기 자세 근처에 머무는 것은 정상이며, 기타 tipping/slip/recovery 상황에서만 의미 있는 하체 보정을 허용한다.
- 논문상의 기본 표현은 `posture-constrained whole-body guitar controller`로 한다.

검증해야 할 비교:

```text
hard-lock lower body
vs.
hold-prior + trainable lower-body residual
```

주요 지표는 guitar stability, drop/slip, recovery time, Fret/Strike retention, lower-body action usage다.

### MP-002 — Neck/Head 포함과 look target

```text
상태: DECIDED
결정일: 2026-09-05
```

- 최종 full-body action ABI에 Neck/Head 6D를 포함한다.
- 현재 FullBody action profile은 105D named ABI로 둔다. zero-range fixed hold 8축을
  제외한 실질 가동 관절 차원은 97D로 집계한다.
- Neck/Head는 StabilityAdapter가 아니라 `GazeTarget/AttentionBranch`가 소유한다.
- GazeTarget의 기본 mode는 기타의 `strike_zone`으로 한다.
- strike zone은 개별 string이나 event마다 바꾸지 않고 기타에 부착된 안정적인 target으로 유지한다.
- 이후 `guitar_body`, `custom` target을 별도 ablation 또는 연주 형태에서 확장한다.
- Neck/Head는 G1부터 trainable하게 하되, neck limit·angular velocity·gaze switching jerk를 별도 제한한다.

105D 계산:

```text
Fret 30 + Strike 30 + Thorax/body 15 + Lower body 24 + Neck/Head 6 = 105
```

이 중 `L/R_Knee_y,z`와 `L/R_Toe_y,z` 8축은 zero-range fixed hold이므로 실질 가동
관절은 97D로 집계한다. 105D는 named ABI 호환성을 위해 유지한다.

실제 asset의 joint manifest가 이 숫자와 다르면 105D를 억지로 유지하지 않고 새 action ABI version을 만든다.

### MP-006 — 양팔 StabilityAdapter authority

```text
상태: DECIDED
결정일: 2026-09-05
```

- StabilityAdapter는 양쪽 shoulder/elbow residual을 제어할 수 있다.
- 왼쪽 shoulder/elbow는 neck 지지, 오른쪽 shoulder/elbow는 guitar body 지지에 사용할 수 있다.
- body/lower-body residual도 G1부터 trainable하게 한다.
- 양쪽 wrist는 초기에는 reserved로 둔다.
- 양손 finger residual은 StabilityAdapter에 허용하지 않는다.
- residual은 새 action dimension이 아니라 기존 named action 위에 적용한다.

초기 active mask:

```text
body/lower-body
L_Shoulder, L_Elbow
R_Shoulder, R_Elbow
```

초기 reserved mask:

```text
L_Wrist, R_Wrist
모든 Fret/Strike finger
```

### MP-007 — StabilityAdapter residual 적용 공간

```text
상태: DECIDED
결정일: 2026-09-05
```

- StabilityAdapter는 Fret·Strike source의 pre-tanh/logit을 직접 수정하지 않는다.
- Fret·Strike source-specific action transform을 먼저 적용한다.
- residual은 그 이후의 named joint target/action 공간에서 합성한다.
- residual cap은 실제 관절 단위로 정의하며 기본 단위는 radian이다.
- residual 합성 이후 total cap·safety filter를 통과시키고 common EMA/PD를 한 번만 적용한다.
- source의 mean/log_std, observation normalization, 확률 분포, 기존 checkpoint action contract는 유지한다.

### MP-008 — 기타 pose 안정성 종료와 soft constraint

```text
상태: DECIDED
결정일: 2026-09-05
```

- 초기 기타 pose에서 회복 불가능한 위치·회전 이탈, 과도한 slip, 필수 접촉 상실, drop, penetration, over-force는 hard failure로 처리한다.
- hard-failure envelope 내부에서는 기타 pose·속도·미끄러짐·support load·residual 크기를 soft reward로 평가한다.
- 단일 simulation step의 노이즈로 terminate하지 않고, 조건이 연속 control step 동안 유지되거나 회복 불가능한 사건이 발생할 때만 episode를 종료한다.
- hard-failure envelope 수치는 사용자가 임의로 고정하지 않고 G1 calibration, 고정 기타 기술 허용 오차, 접촉·기하 여유로 산출한다.
- Fret·Strike 성능 저하는 안정성 reward와 별도의 보존 지표로 기록한다.

### MP-009 — StabilityAdapter reference frame 우선순위

```text
상태: DECIDED
결정일: 2026-09-06
```

- 기타 지지와 초기 상대 pose 보존의 primary reference는 body frame `B`로 한다.
- world 전체 pose를 primary target으로 고정하지 않는다.
- world/gravity frame `W`는 중력 기준 기울기, 낙하 방향 속도, tipping/drop을 판정하는 secondary safety reference로 사용한다.
- Fret·Strike target geometry와 음악 event는 guitar frame `G`에서 유지한다.
- frame별 초기 reference와 valid rule을 observation/action contract에 명시한다.

### MP-010 — pelvis anchor와 hold 정책

```text
상태: DECIDED
결정일: 2026-09-06
```

- StabilityAdapter의 body frame `B` anchor는 pelvis다.
- G0에서는 pelvis hard-lock을 source equivalence, 초기 안정성 검증, `PelvisLocked` ablation baseline에 사용한다.
- G1·G2의 본 실험에서는 pelvis를 hard-lock하지 않고 강한 joint-angle hold로 유지한다.
- lower-body residual은 trainable하지만 기타 tipping/slip recovery에 필요한 제한된 이탈만 허용한다.
- pelvis hold 오차, joint-angle deviation, lower-body residual을 별도 metric으로 기록한다.

### MP-011 — StabilityAdapter 접촉 관측

```text
상태: DECIDED
결정일: 2026-09-06
```

- 접촉력(normal/tangential load)과 slip velocity를 주 관측으로 사용한다.
- contact/no-contact flag는 보조 관측으로 사용한다.
- 초기 support group은 `strap`, `body_contact`(torso/thigh), `arm_contact`(palm/forearm)의 세 가지로 단순화한다.
- 왼쪽·오른쪽 및 손가락별 contact 모델은 초기 범위에서 분리하지 않는다.
- 손가락 끝은 Fret·Strike 연주 접촉으로만 취급하고 support group에는 포함하지 않는다.

### MP-013 — 초기 support observation

```text
상태: DECIDED
결정일: 2026-09-06
```

- 각 support group은 `normal_load`, `tangential_load`, `slip_speed`, `contact_flag`를 관측한다.
- strap에서는 `normal_load`를 tension으로 해석한다.
- 접촉점별 벡터와 세부 force attribution은 초기 범위에서 제외한다.

### MP-014 — StabilityAdapter 초기 residual 출력 범위

```text
상태: DECIDED
결정일: 2026-09-06
```

- 전체 105D를 재출력하지 않고 named action group에 sparse residual을 적용한다.
- active: `Thorax/body`, `Lower body`, `L/R Shoulder`, `L/R Elbow`
- reserved: `L/R Wrist`
- forbidden: Fret·Strike finger, Neck/Head
- 기타가 안정적일 때는 residual authority를 낮게 유지하고, slip·tipping 위험이 커질 때만 높인다.

### MP-015 — residual authority gate 소유권

```text
상태: DECIDED
결정일: 2026-09-06
```

- StabilityAdapter는 residual candidate와 support-need/confidence만 제안한다.
- 최종 `authority_gate`, hard cap, safety veto는 외부 Safety/Consistency layer가 결정한다.
- gate는 기타 pose/slip/contact, Fret·Strike 보존 위험, curriculum stage를 함께 고려한다.
- 정책이 자기 residual 권한을 직접 무제한 확대하지 못하도록 한다.

### MP-016 — 초기 authority gate 방식

```text
상태: DECIDED
결정일: 2026-09-06
```

- G0·G1 초기 gate는 규칙 기반으로만 구성한다.
- 규칙은 기타 pose, slip, contact, Fret·Strike 보존 조건을 사용한다.
- learned ConsistencyBranch는 초기 범위에서 사용하지 않고 후속 확장으로 미룬다.
- hard safety와 hard cap은 이후에도 규칙 기반으로 유지한다.

### MP-017 — 규칙 기반 gate 조건

```text
상태: DECIDED
결정일: 2026-09-06
```

- hard failure: pose 이탈, tipping/drop, 필수 접촉 상실, 위험 slip, penetration/over-force, strap 과장력, pelvis safety 이탈
- residual 감소·차단: Fret readiness·Strike timing 저하, residual cap/rate 반복 도달, 불안정한 contact force
- residual 증가: pose drift, 회전·속도 증가, slip 증가, friction 여유 감소, strap tension 증가
- 우선순위는 hard safety → Fret·Strike 보존 → 기타 pose 안정화 → residual 최소화로 한다.
- threshold와 지속 시간은 G1 calibration에서 정하고 hysteresis를 사용한다.

### MP-018 — authority gate 분할

```text
상태: DECIDED
결정일: 2026-09-06
```

- 공통 `global_safety_gate`와 group별 `body_gate`, `lower_body_gate`, `arm_support_gate`를 사용한다.
- 좌우 shoulder/elbow는 초기에는 하나의 `arm_support_gate`로 묶는다.
- hard failure에서는 global gate가 모든 residual을 차단한다.
- group gate는 Fret·Strike 위험과 각 support group의 안정화 필요도에 따라 독립적으로 조절한다.

### MP-019 — FullBodyPlayer 합성 구조

```text
상태: DECIDED
결정일: 2026-09-06
```

- FullBodyPlayer는 monolithic end-to-end policy가 아니라 modular runtime system으로 구성한다.
- Fret, Strike, Synchronizer, StabilityAdapter, Gaze/Attention은 named proposal만 생성한다.
- 중앙 `ActionArbiter`가 ownership, priority, mask, cap, safety를 적용해 최종 105D action을 만든다.
- 개별 모듈은 Isaac Gym actuator에 직접 action을 쓰지 않는다.
- common EMA/PD는 최종 합성 후 한 번만 적용한다.

### MP-020 — 초기 Synchronizer 방식

```text
상태: DECIDED
결정일: 2026-09-06
```

- 초기 Synchronizer는 규칙 기반 timing supervisor로 구현한다.
- 공통 Canonical PlayEvent timeline은 변경하지 않는다.
- readiness, strike window, 안정성 조건으로 실행 허용·대기·miss/skip만 결정한다.
- 관절 action은 출력하지 않는다.
- learned timing correction은 규칙 기반 기준선의 한계가 검증된 경우에만 후속 확장한다.

### MP-021 — 공통 음악 timeline 입력

```text
상태: DECIDED
결정일: 2026-09-06
```

- raw audio는 오프라인 전처리에서만 사용한다.
- Tablature, Finger Mapping, Picking Plan을 `Canonical PlayEvent`로 합친다.
- Runtime의 Fret, Strike, Synchronizer는 이 event timeline을 공유한다.
- Finger Mapping 하나만을 공통 시간축으로 사용하지 않는다.

### MP-022 — Fret·Strike 독립성

```text
상태: DECIDED
결정일: 2026-09-06
```

- Fret과 Strike는 최종 단계까지 독립된 skill prior로 유지한다.
- 별도 actor, checkpoint, observation/action contract를 사용한다.
- Synchronizer는 양손 사이의 event-level timing을 조정한다.
- 각 손 내부의 motor timing은 해당 skill prior가 담당한다.
- 기본 구조에는 joint Fret-Strike actor를 두지 않으며, 필요한 경우에만 일부 계층을 제한적으로 fine-tuning한다.

### MP-023 — G1 source 동결 원칙

```text
상태: DECIDED
결정일: 2026-09-06
```

- G1 초기에는 Fret·Strike source policy를 완전히 동결한다.
- StabilityAdapter와 허용된 full-body residual을 먼저 학습한다.
- 이 구성에서 안정화 실패가 지속된 것이 검증된 경우에만 source 일부를 제한적으로 해제한다.
- 실패 판정 기준과 정확한 해제 계층은 세부 설계 단계에서 정한다.
- finger 계층은 별도 필요성이 검증되지 않는 한 동결한다.

### MP-024 — G0/G1/G2 물리 curriculum

```text
상태: DECIDED
결정일: 2026-09-06
```

- G0: 기타를 고정하고 Fret·Strike·Synchronizer를 학습·검증한다.
- G1: 기타 고정을 해제하고 강한 artificial assist에서 시작해 점진적으로 줄인다.
- G2: 최종 자유 기타 물리를 사용하고 artificial assist는 0으로 한다.
- strap 제약의 G2 사용 여부는 MP-025에서 결정한다.

### MP-025 — 가상 strap 물리 제약과 시각화

```text
상태: DECIDED
결정일: 2026-09-07
```

- 실제 strap의 지지 효과는 두 strap button을 잇고 가슴 위쪽과 왼쪽 어깨를 감싸는 신체
  표면 guide를 지나는 준-비신축성 maximum-length cable **제약**으로 구현한다. rope/cloth
  오브젝트의 접촉을 직접 시뮬레이션하는 방식은 아니다.
- 설정 길이 이내에서는 느슨하게 휘고, 240 Hz 물리 갱신으로 초과 신장을 1% 이내로 유지한다.
- guide는 해당 신체 collision capsule 표면 가까이에 두고, 굽힘점 반력은 guide가 속한 rigid body에 적용한다.
- guide 사이의 모든 선분도 전체 humanoid collision capsule과 비교해 비관통을 검증한다.
- 초기 검증에서는 고정 guide를 사용하고, G1에서는 표면 재투영과 제한적 접선 미끄러짐을 검증한다.
- 시각화는 물리 계산과 동일한 외부 경로를 따라가며 humanoid를 관통하지 않아야 한다.
- rope/cloth contact simulation은 초기 범위에서 제외한다.
- G2 주 평가는 `strapped` profile로 하고 `unstrapped`는 추가 비교 조건으로 둔다.
- strap 제약과 G1 curriculum artificial assist는 별개이며, G2에서 artificial assist만 0으로 만든다.
- 이 strap을 G1·G2 메인 물리 흐름의 기본 장비 `strapped-v1`으로 사용한다. G0에서는 source 등가성을 위해 strap force를 비활성화한다.
- 메인 환경 연결 전 guitar-side exit guide와 guitar collision proxy를 추가하고, 버튼 주변의 허용 연결 구간을 제외한 모든 strap 선분에 대해 기타 비관통을 검증한다.

### MP-026 — 신체 support contact 물리 형태

```text
상태: DECIDED
결정일: 2026-09-07
```

- 허벅지·몸통·손바닥·전완의 기타 지지는 실제 충돌 기반의 단순 box/capsule support proxy로 구현한다.
- 초기 그룹은 `body_contact`(양쪽 허벅지·몸통)와 `arm_contact`(양쪽 손바닥·전완)로 유지한다.
- proxy는 해당 humanoid rigid body에 부착하며 기타와 실제 contact·friction force를 주고받는다.
- 기존 collision shape로 안정적인 접촉과 force attribution이 가능하면 재사용하고, 부족한 부위에만 최소한의 named proxy를 추가한다.
- 손가락 끝은 support proxy에서 제외하고 Fret·Strike 연주 접촉으로만 취급한다.
- G1과 G2는 동일한 support proxy를 사용한다. artificial assist는 별도 구성으로 두며 proxy 접촉으로 위장하지 않는다.
- 초기 관측은 접촉점별 raw vector가 아니라 `body_contact`, `arm_contact` 그룹별 load·slip·contact flag로 집계한다.
- 상세 mesh contact와 학습된 가상 지지력은 초기 범위에서 제외한다.

### MP-027 — 기타 줄과 Strike 판정의 물리 수준

```text
상태: DECIDED
결정일: 2026-09-07
```

- 기타 줄은 실제 deformable/rigid collision object가 아닌 가상 geometry로 유지한다.
- Strike 성공은 pick marker의 swept crossing을 사용하는 `KinematicStrikeDetector`가 판정한다.
- 실제 string 변형, string rigid-body dynamics, pick-string contact solver와 음향 합성은 메인 연구 범위에서 제외한다.
- 가상 줄은 기타 좌표계에 고정되며 기타가 움직이면 live guitar pose를 따라 이동한다.
- 이 결정은 기존 Strike skill prior와 checkpoint를 재사용하기 위한 기본 계약이다.
- 가상 crossing의 기타 충격 여부는 MP-028에서 별도로 결정한다.

### MP-028 — 가상 Strike crossing의 기타 충격

```text
상태: DECIDED
결정일: 2026-09-07
```

- 가상 줄 crossing은 음악 event만 생성하며 기타에 force, torque 또는 impulse를 적용하지 않는다.
- 올바른 crossing과 잘못된 crossing 모두 인공적인 물리 충격을 만들지 않는다.
- StabilityAdapter는 중력, 기타 관성, strap, 실제 신체 접촉 변화와 별도 외부 교란을 대상으로 학습한다.
- 연구 결과에서 physical pick-string reaction이나 타현 반력 대응을 주장하지 않는다.
- Strike 직후 settling은 가상 impulse 회복이 아니라 실제 팔·손 움직임과 support contact 변화 이후의 기타 안정성으로 해석한다.

### MP-029 — Strike source action 계약

```text
상태: DECIDED
결정일: 2026-09-07
```

- Strike source는 기존 `30D` 관절 action과 기존 PD target semantics를 유지한다.
- 관절 구성과 순서는 `R_Shoulder 3 + R_Elbow 3 + R_Wrist 3 + RH hand 21`로 유지한다.
- 기존 checkpoint의 action name/order, scaling, joint limit mapping, EMA와 PD gain을 source action 계약에 포함한다.
- Strike source 자체를 joint-target residual policy로 재설계하지 않는다.
- StabilityAdapter residual은 Strike의 30D 출력을 대체하지 않으며, 중앙 `ActionArbiter`가 허용된 named joint에만 제한적으로 합성한다.
- `strike-v2`에서 observation이나 event 표현을 바꿀 경우 action ABI는 그대로 두되 observation/checkpoint contract version은 별도로 올린다.
- 여러 grip profile을 하나의 actor가 지원할지는 이 결정에 포함하지 않고 후속 결정으로 남긴다.

### MP-030 — Strike 기본 피크 그립

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 연구에서는 하나의 canonical pick grip만 사용한다.
- 곡, 음표, 줄, up/down 방향에 따라 grip profile을 전환하지 않는다.
- Strike는 동일한 그립을 유지한 채 single picking과 strumming을 수행한다.
- 그립 reference와 허용 오차는 checkpoint 및 환경 manifest에 버전으로 기록한다.
- 여러 피크 그립, fingerstyle, grip switching은 메인 구조의 필수 기능이 아니라 후속 확장·ablation으로 분리한다.

### MP-031 — Single picking과 strumming의 정책 구성

```text
상태: DECIDED
결정일: 2026-09-07
```

- single picking과 strumming은 하나의 StrikeMotorPolicy가 담당한다.
- 별도의 picking actor와 strumming actor 또는 동작별 checkpoint를 기본 구조에 두지 않는다.
- 동작은 `target_traversal_mask`, up/down direction, string별 timing offset, sweep duration이 포함된 `StrikeEvent`로 구분한다.
- actor의 observation·action shape과 canonical pick grip은 두 동작에서 동일하게 유지한다.
- 학습은 single-string crossing을 먼저 안정화한 뒤 인접 줄, 다중 줄 strumming 순으로 확장한다.
- 동작별 성공률은 따로 보고하되, 최종 checkpoint는 두 동작을 모두 수행해야 통과한다.

### MP-032 — Strike-v2 actor observation

```text
상태: DECIDED
결정일: 2026-09-07
schema: strike.observation.v2
dimension: 303D
```

- Strike-v2 actor observation은 다음 named block을 순서대로 연결한 `303D`로 고정한다.

```text
O_proprio                  60
O_arm_anchor               18
O_hand_geometry            30
O_grip_safety               7
O_current_event            32
O_target_geometry          25
O_lookahead                52
O_phase_detector           29
O_recovery                 18
O_synchronizer              2
O_history                  30
-----------------------------
total                     303
```

- 위치·회전·속도 geometry는 guitar frame을 기준으로 표현한다.
- `O_arm_anchor`는 pelvis가 아니라 `R_Thorax`를 오른팔의 직접 기준점으로 사용한다.
- 기타 world pose/twist, strap 장력, support contact force와 slip은 Strike actor에 넣지 않는다.
- `O_synchronizer`에는 raw Fret 상태가 아니라 `release_enable`과 supervisor timing offset만 넣는다.
- `O_history`는 Strike proposal이 아니라 arbiter와 actuator transform을 거쳐 실제 실행된 Strike 30D slice다.
- 처음에는 보수적으로 모든 block을 포함하며, 이후 named-block ablation으로 중요도가 낮은 특성을 검증한다.
- field를 추가·삭제·재정렬하면 `strike.observation.v3`처럼 schema version과 normalization을 함께 변경한다.
- 기존 Strike-v1 `327D` checkpoint와는 observation contract가 다르므로 직접 resume할 수 없다.

### MP-033 — Fret policy와 readiness 판정 분리

```text
상태: DECIDED
결정일: 2026-09-07
```

- `FretMotorPolicy`는 왼팔·왼손의 30D action proposal을 생성한다.
- `FretReadinessEvaluator`는 policy와 분리된 규칙 기반 physics evaluator로 둔다.
- readiness는 policy의 자기 선언이 아니라 실제 fingertip 위치, 올바른 줄·프렛 압현,
  잘못된 압현, chord 동시 준비, dwell, sustain 상태로 판정한다.
- Evaluator는 `ready`, confidence와 준비 실패 이유를 출력하며 Synchronizer가 이를 사용한다.
- learned readiness head는 필요하면 auxiliary prediction으로 추가할 수 있지만 타현 허가의
  authoritative signal로 사용하지 않는다.
- readiness 규칙과 threshold는 별도 contract version으로 관리한다.

### MP-034 — Fret source action 계약

```text
상태: DECIDED
결정일: 2026-09-07
dimension: 30D
```

- Fret source action은 `L_Shoulder 3 + L_Elbow 3 + L_Wrist 3 + LH hand 21`의
  기존 30D named action을 유지한다.
- `L_Thorax`와 몸통 관절은 FretMotorPolicy가 직접 제어하지 않는다.
- 몸통은 FullBodyPlayer에서 StabilityAdapter proposal과 ActionArbiter가 관리한다.
- 기존 checkpoint의 action name/order, scaling, joint-limit mapping, EMA와 PD semantics를
  Fret source action 계약에 포함한다.
- StabilityAdapter가 왼쪽 shoulder/elbow에 residual을 제안하더라도 Fret의 source action을
  대체하지 않으며, 최종 합성은 named-joint cap과 보존 gate를 거친다.

### MP-035 — Fret 연주 형태별 정책 구성

```text
상태: DECIDED
결정일: 2026-09-07
```

- single-note press, chord press, sustain, release와 position transition을 하나의
  `FretMotorPolicy`가 담당한다.
- 연주 형태별 actor나 checkpoint를 기본 구조에 따로 두지 않는다.
- 동작 차이는 `FretEvent`의 target string/fret/finger mask, chord group, sustain와
  press/hold/release/transition phase 입력으로 표현한다.
- 동작별 성공 지표는 분리해서 보고하지만 최종 Fret prior checkpoint는 곡에 필요한
  모든 Fret event 유형을 처리해야 한다.
- 특정 event 유형의 학습 난이도는 별도 정책이 아니라 curriculum sampling과 reward mask로 조절한다.

### MP-036 — Fret-v2 observation 재설계

```text
상태: DECIDED
결정일: 2026-09-07
schema: fret.observation.v2
dimension: 420D
```

- 기존 425D observation은 `fret.observation.v1` baseline으로 보존한다.
- 최종 Fret prior에는 named block 기반의 `fret.observation.v2`를 새로 설계한다.
- v2는 `60+18+60+45+24+52+72+45+12+2+30=420D` named block 계약으로
  봉인한다. 세부 순서는 `tab2body/fret_v2_contract.py` manifest를 단일 기준으로 삼는다.
- 다음 두 event는 단순한 고정 frame 복제가 아니라 현재와 다른 canonical Fret 상태를
  기준으로 한다. 정적 습득 단계에서는 미래 event를 노출하지 않는다.
- actor/critic은 각 block을 따로 encode한 뒤 fusion MLP로 결합한다. 초기 버전에는
  GRU를 넣지 않으며 history ablation에서 필요성이 확인될 때만 검토한다.
- v1 checkpoint를 v2에서 직접 resume하지 않는다. 재사용이 필요하면 호환 가능한
  encoder block의 제한적 warm-start, teacher/distillation 또는 baseline 비교로 분리한다.
- observation field를 추가·삭제·재정렬하면 normalization과 checkpoint contract version을
  함께 변경한다.
- 2026-09-07 `02_Jazz1-200-B_solo`에서 8 env × 4 step × 1 PPO update smoke,
  checkpoint strict-load, Fret-v1 425D 회귀 smoke를 통과했다. 이는 배관 검증이며
  학습 성능이나 곡 일반화 통과를 의미하지 않는다.

### MP-037 — Fret readiness와 엄지 지지 분리

```text
상태: DECIDED
결정일: 2026-09-07
선택: B
```

- `fret_ready`의 hard condition은 올바른 sounding fret, 음악적으로 방해되는 오압현
  없음, chord 동시 준비와 최소 dwell로 한정한다.
- 엄지 지지는 `thumb_support_ready`와 `support_confidence`라는 별도 신호로 유지하며
  `fret_ready`를 직접 false로 만들지 않는다.
- G1/G2의 최종 타현 허가는 `fret_ready AND support_safe`로 계산한다.
- `support_safe`의 물리 판정은 StabilityAdapter 측 책임이며 Synchronizer는 두 결과를
  받아 timing gate만 적용한다.

### MP-038 — Finger Mapping `t_press` 기준과 short-lead 분류

```text
상태: DECIDED
결정일: 2026-09-07
```

- Finger Mapping의 `t_press = t_strike - 0.12s`는 손가락 이동 시작 시점이 아니라
  목표 물리 압현 시작 시점으로 해석한다.
- Fret은 lookahead를 이용해 `t_press`보다 먼저 손가락을 이동·정렬할 수 있다.
- Fret은 event별 `t_press`에 실제 올바른 압현을 완료하고, 오압현 없이 연결된 strike와
  필요한 `t_release`까지 유지한다.
- 0.12초는 음악적·물리적 제약이 허용될 때 Finger Mapping이 확보하려는 nominal
  lead이며, 모든 event에 강제하는 downstream hard deadline으로 사용하지 않는다.
- 사용 가능한 lead가 6 frame보다 짧은 이벤트는 `short_lead`라는 진단·난이도 tag로
  표시한다. Fret의 목표 timing은 바꾸지 않으며 전체 성공률과 함께 subgroup 성능을
  별도로 보고한다.
- Synchronizer는 연결된 press/strike event ID를 사용해 strike 시점의 실제 readiness를
  확인하며, 별도의 고정 pre-press 시간 이동을 다시 적용하지 않는다.

### MP-039 — Fret 미준비 시 Strike 최대 지연

```text
상태: SUPERSEDED BY MP-075
결정일: 2026-09-07
```

- 이 결정의 2-frame 상한은 MP-075의 3-frame 상한으로 대체되었다.
- 역사적 근거 보존을 위해 아래 기존 문구를 남기며 현재 계약으로 사용하지 않는다.
- Synchronizer는 예정된 strike frame에 Fret이 준비되지 않은 경우 60 Hz 기준 최대
  2 frame(약 33 ms)까지 strike를 지연할 수 있다.
- 예정 frame에 실행된 타현은 `on_time`, 1~2 frame 지연 후 성공은
  `delayed_rescue`, 2 frame 초과는 `timing_failure`로 기록한다.
- `on_time`과 `delayed_rescue`는 최종 지표에서 분리하며 평균·분위수 strike timing
  error를 함께 보고한다.
- 이 제한은 물리적 접촉 판정 오차를 흡수하기 위한 것이며, Fret 실패를 장시간의
  Strike 지연으로 숨기는 용도로 사용하지 않는다.

### MP-040 — 지연 한도 초과 시 타현 누락

```text
상태: DECIDED
결정일: 2026-09-07
```

- 단일 string event에서 최대 지연 안에도 Fret이 준비되지 않으면 잘못된 음을 강제로
  타현하지 않고 해당 strike를 실행하지 않는다.
- 해당 event는 `missed_note_due_fret_not_ready`로 기록하며 공통 음악 시간축과 다음
  event는 예정대로 계속 진행한다.
- 누락은 큰 실패로 강하게 평가한다. 누락률이 높으면 먼저 Fret의 lookahead, reward와
  정책 성능을 개선한다.
- delay budget은 실험 전에 고정하여 보고하며, 평가 도중 누락을 피하려고 임의로
  확장하지 않는다.

### MP-041 — 양손 공통 타현 허용 구간과 지연 원인

```text
상태: SUPERSEDED BY MP-075
결정일: 2026-09-07
```

- 아래 +2 frame 기준은 MP-075의 event별 0~3 frame 기준으로 대체되었다.
- Fret readiness와 Strike의 실제 타현 모두 예정 strike frame부터 +2 frame까지의
  동일한 공통 허용 구간을 사용한다.
- 허용 구간 내 지연은 `delayed_by_fret`, `delayed_by_strike`, `delayed_by_both`로
  원인을 분리해 기록한다.
- Fret은 준비됐지만 허용 구간 내 실제 타현 crossing이 발생하지 않으면
  `missed_note_due_strike_timing`으로 기록한다.
- 공통 음악 시간축은 지연이나 누락과 관계없이 계속 진행하며 다음 event를 연쇄적으로
  뒤로 밀지 않는다.

### MP-042 — Fret readiness 최소 확인 시간

```text
상태: DECIDED
결정일: 2026-09-07
```

- `fret_ready`는 필요한 모든 압현이 올바르고 오압현이 없는 상태가 타현 직전 최소
  1 control frame 동안 연속 확인되어야 true가 된다.
- 처음 correct contact가 발생한 바로 그 frame에는 strike를 허가하지 않고 다음
  control frame부터 허가한다.
- `short_lead`를 처리할 수 있도록 1 frame보다 긴 고정 dwell은 요구하지 않는다.
- 이 규칙은 순간적인 접촉 chatter를 ready로 오인하는 것을 막기 위한 최소 확인이며,
  실제 contact 안정성은 별도 연속성 지표로 보고할 수 있다.

### MP-043 — 올바른 압현의 위치·누름 결합 판정

```text
상태: DECIDED
결정일: 2026-09-07
```

- correct press는 손끝이 목표 string/fret cell 안에 있는 위치 조건과 실제 누름 상태를
  동시에 만족해야 한다.
- 목표 위치에 정렬됐지만 줄 위에 떠 있는 상태는 `approach_ready`로만 취급하고
  `press_ready` 또는 `fret_ready`로 인정하지 않는다.
- 줄은 가상이므로 누름 상태는 손끝이 원래 virtual string 위치보다 fretboard 방향으로
  들어간 깊이로 판정한다.
- 구체적인 위치·깊이 threshold는 임의로 확정하지 않고 단일 손가락 소규모 기하
  검증 환경에서 calibration한 뒤 계약에 봉인한다.

### MP-044 — 압현 readiness에서 접촉력 제외

```text
상태: DECIDED
결정일: 2026-09-07
```

- 실제 기타 줄은 fretboard 위에 떠 있으므로 올바른 압현을 위해 손끝이 fretboard에
  직접 닿을 필요는 없다.
- `correct_press`의 hard condition에는 fretboard 접촉 여부와 접촉력 threshold를
  포함하지 않는다.
- 누름은 목표 string/fret 위치와 virtual string의 원래 높이를 넘어 fretboard 방향으로
  이동한 geometric press depth로 판정한다.
- 기타·손가락 사이의 물리 접촉력은 충돌 안전이나 안정화 진단에 사용할 수 있지만
  Fret readiness를 직접 결정하지 않는다.

### MP-045 — 모든 가상 줄의 공통 press-depth 기준

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 Fret readiness는 여섯 가상 줄 모두에 동일한 하나의 press-depth threshold를
  적용한다.
- depth는 기타 좌표계에서 virtual string의 원래 위치로부터 fretboard 방향으로 측정한다.
- 줄별 threshold나 보정 계수는 초기 계약에 넣지 않는다.
- 이후 검증에서 특정 줄에만 지속적인 false-ready 또는 false-not-ready가 관찰될 때만
  줄별 보정을 후속 버전으로 추가한다.

### MP-046 — Press depth의 fingertip 표면 기준

```text
상태: DECIDED
결정일: 2026-09-07
```

- Press depth는 fingertip rigid body의 중심점이 아니라 virtual string 쪽을 향한
  fingertip 표면을 기준으로 측정한다.
- 손가락 자세와 기울기가 달라져도 실제 표면이 줄의 원래 위치보다 fretboard 방향으로
  들어갔는지를 판정한다.
- body center와 string plane 사이 거리만으로 `press_ready`를 판정하지 않는다.
- 표면 계산의 구체적 구현 방식은 MP-047의 고정 finger-pad marker를 따른다.

### MP-047 — 고정 finger-pad marker 사용

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 표면 위치 계산은 collision mesh의 매-frame closest point가 아니라 각 distal
  finger body에 고정한 `finger_pad_marker`를 사용한다.
- marker는 실제 손끝 pad 표면에 한 번 calibration하고, runtime에는 rigid-body transform으로
  기타 좌표계 위치를 계산한다.
- 이 marker로 목표 string/fret 위치 오차와 virtual string 기준 press depth를 함께 계산한다.
- mesh closest-point 방식은 marker 방식에서 자세별 체계적 오차가 확인될 때만 후속
  대안으로 검토한다.

### MP-048 — Fret 구간 내부의 균일 점수 영역

```text
상태: DECIDED
결정일: 2026-09-07
```

- 대상 fret 구간에서 nut 쪽 wire를 0, bridge 쪽 wire를 1로 정규화한 좌표
  `u_fret`을 사용한다.
- `0.1 <= u_fret <= 0.9`인 모든 위치에는 동일한 correct-position 점수를 준다.
- 구간 중앙이나 특정 fret wire 인접 위치에 추가 보너스를 주지 않는다.
- 양 끝의 0.1 margin은 fret wire 위 또는 인접 fret으로 넘어가는 경계 혼동을 줄이기
  위해 정답 영역에서 제외한다.

### MP-049 — String 영역의 5:5 분할

```text
상태: DECIDED
결정일: 2026-09-07
```

- 넥 폭 방향에서 인접한 두 virtual string 중심선 사이의 중점을 5:5 경계로 사용한다.
- neck width 전체를 여섯 string 영역으로 빈틈과 중첩 없이 분할한다.
- `finger_pad_marker`가 속한 영역의 string 하나를 누른 것으로 판정한다.
- 동일 string 영역 안에서는 중심선으로부터의 거리에 따른 추가 보너스나 감점을 두지
  않는다.

### MP-050 — 음악적으로 방해되는 추가 압현만 차단

```text
상태: DECIDED
결정일: 2026-09-07
```

- 추가 압현은 존재 자체로 `fret_ready`를 false로 만들지 않는다.
- 현재 타현될 각 string에서 활성 press 중 bridge에 가장 가까운 가장 높은 fret을
  `effective_sounding_fret`으로 계산하고 이것이 목표 fret과 같은지 판정한다.
- 목표보다 낮은 fret의 추가 press는 더 높은 목표 fret이 정상적으로 눌려 있다면 현재
  음높이를 바꾸지 않으므로 hard interference로 처리하지 않는다.
- 목표보다 높은 fret의 추가 press, 또는 개방현 목표 string의 fretted press는 실제
  음높이를 바꾸므로 hard interference다.
- 현재 event에서 타현되지 않는 string의 추가 press는 현재 음악 event의 hard failure가
  아니다. 필요한 경우 자세 효율이나 다음 전환을 위한 soft penalty로만 다룬다.

### MP-051 — 대체 손가락의 동일 fret 압현 허용

```text
상태: DECIDED
결정일: 2026-09-07
```

- Finger Mapping에 지정된 손가락과 다른 손가락이 동일 string의 동일 목표 fret을
  눌러도 해당 string의 음악적 성공으로 인정한다.
- `fret_ready`의 hard gate는 finger identity가 아니라 타현 대상 string별
  `effective_sounding_fret` 일치로 결정한다.
- 대체에 사용된 손가락이 동시에 담당해야 할 다른 target을 누르지 못하면 그 target
  string의 readiness 실패와 reward penalty가 발생한다.
- 계획된 손가락 배정 일치율은 hard gate가 아닌 별도 `fingering_adherence` 진단 지표로
  보고한다.

### MP-052 — 부분 준비 chord/strum의 타현 실행

```text
상태: SUPERSEDED BY MP-075
결정일: 2026-09-07
```

- 아래 +2 frame 기준은 MP-075의 event별 0~3 frame 기준으로 대체되었다.
- 여러 string을 묶어 타현하는 chord/strum event는 일부 target string이 준비되지
  않았다는 이유로 전체 event를 누락하지 않는다.
- 예정 frame부터 최대 +2 frame까지는 모든 target string의 준비를 기다릴 수 있다.
- deadline에도 일부 string이 미준비면 타현을 실행하고 `partial_chord` 또는
  `partial_strum`으로 기록한다.
- deadline에 준비된 target string이 하나도 없으면 타현하지 않고 `missed_chord` 또는
  `missed_strum`으로 기록한다.
- 결과는 string별 effective sounding fret의 정답·오답·누락으로 평가하며, 전체 event
  성공률과 정확한 string 비율을 함께 보고한다.
- 단일 string event의 미준비 시 누락 규칙은 그대로 유지한다.

### MP-053 — Multi-string event의 full·partial 성공 분리

```text
상태: DECIDED
결정일: 2026-09-07
```

- Chord/strum은 모든 target string의 effective sounding fret이 정답일 때만 전체 event
  성공으로 센다.
- 일부 target string만 정답이면 `partial_success`로 기록하고 전체 event 성공률에는
  포함하지 않는다.
- Partial reward는 `correct_target_strings / total_target_strings` 비율을 기준으로 준다.
- 정답 target string이 하나도 없으면 `missed_event`이며 partial reward는 0이다.
- 보고 시 full-event success rate와 target-string accuracy를 항상 분리한다.

### MP-054 — 실제 시뮬레이션 압현 시각화 도구

```text
상태: DECIDED
결정일: 2026-09-07
```

- `FretPressVisualizer`는 Finger Mapping 목표와 실제 시뮬레이션 압현을 string/fret cell
  단위로 동시에 표시한다.
- 실제 표시는 finger ID, 검출 string/fret, press depth, string별 effective sounding fret,
  correct·harmless-extra·interfering 상태를 포함한다.
- 기본 색은 목표 윤곽=파랑, 올바른 압현=초록, 무해한 추가 압현=노랑, 방해 압현=빨강으로
  한다.
- viewer overlay, frame별 machine-readable trace와 녹화 영상 overlay를 지원한다.
- 시각화는 `FretReadinessEvaluator`의 동일한 authoritative snapshot을 사용하며 별도
  판정 로직을 복제하지 않고 학습 reward나 action에도 영향을 주지 않는다.

### MP-055 — 압현 해제 시점의 비대칭 판정

```text
상태: DECIDED
결정일: 2026-09-07
```

- `t_release` 이전에 손가락을 떼어 필요한 sustain을 끊으면 early-release failure로
  처리한다.
- `t_release` 이후의 늦은 해제는 존재 자체로 hard failure나 고정 penalty를 주지 않는다.
- 늦은 해제가 다음 타현의 개방현·더 낮은 fret을 방해하면 sounding-fret interference로
  처리한다.
- 늦게 유지한 손가락이 다음 assignment로 이동하지 못하면 해당 후속 target의 readiness
  failure로 처리한다.
- 즉, 음악이나 다음 동작에 실제 영향을 주지 않는 late hold는 허용한다.

### MP-056 — 초기 Fret-v2에서 바레 제외

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 Fret-v2는 single-finger/single-string 압현과 여러 손가락 chord를 지원하지만
  한 손가락으로 여러 string을 누르는 barre는 지원하지 않는다.
- 현재 song bundle에는 `barre=true` event가 없으므로 초기 검증 범위에는 영향이 없다.
- Finger Mapping과 Canonical PlayEvent의 `barre` field는 미래 확장을 위해 보존한다.
- `barre=true` 입력은 일반 chord로 자동 변환하지 않고 capability validation에서
  unsupported error로 명확히 보고한다.
- Barre는 기본 Fret 검증 후 여러 index-pad marker와 별도 readiness 판정을 갖는 후속
  단계에서 추가하며, 판정 의미가 바뀌면 readiness/checkpoint contract version을 올린다.

### MP-057 — 초기 연구에서 특수 주법 제외

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 연구는 일반 fretted/open note와 이를 사용하는 picking·strum만 다룬다.
- Hammer-on, pull-off, slide, bend 등 별도의 왼손 onset·연속 pitch 모델이 필요한 특수
  주법은 현재 범위에서 고려하지 않는다.
- Technique label이 있는 입력을 일반 press/strike event로 조용히 변환하지 않고
  capability validation에서 unsupported로 보고한다.
- 특수 주법 지원은 현재 master plan의 필수 완료 조건이나 평가 범위에 포함하지 않는다.

### MP-058 — Fret reward의 음악 결과 우선 계층

```text
상태: DECIDED
결정일: 2026-09-07
```

- Fret reward의 1순위는 strike 시점의 string별 effective sounding fret 정확성, chord
  완성도와 miss 여부다.
- 2순위는 sustain 유지, early release와 다음 event interference다.
- 3순위는 fingertip 접근·press depth·계획 운지·thumb support·동작 smoothness shaping이다.
- 하위 tier reward의 최대 합이 wrong sounding fret 또는 missed target의 손실을
  상쇄하지 못하도록 reward 범위를 제한한다.
- 평균 scalar reward만으로 성공을 판정하지 않고 음악 event outcome과 각 reward tier를
  별도로 기록한다.

### MP-059 — Fret checkpoint의 AND 승급 gate

```text
상태: DECIDED
결정일: 2026-09-07
```

- Fret checkpoint는 single-note 정확성, chord 완성도, sustain/release, 빠른 transition,
  short-lead subgroup, 같은 곡의 evaluation rollout과 joint/collision safety를 모두 통과해야 승급한다.
- 전체 평균 reward나 평균 press accuracy 하나로 승급하지 않는다.
- 각 필수 gate의 결과와 최악 subgroup 성능을 checkpoint 평가 기록에 포함한다.
- 구체적인 수치 threshold는 지금 임의로 정하지 않고 micro-environment 및 baseline
  분포로 calibration한 뒤 봉인한다.

### MP-060 — Tablature 결과의 전량 학습 사용

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기에는 confidence 수준과 관계없이 schema validation을 통과한 Tablature event를
  모두 학습에 사용한다.
- 낮은 confidence를 이유로 event를 제외하거나 reward weight를 낮추지 않는다.
- confidence, source와 review status는 오류 분석 및 subgroup 평가용 metadata로 보존한다.
- 음수·역전 duration, 유효 범위 밖 string/fret, 비단조 시간처럼 실행 불가능한 구조
  오류는 confidence와 구분하여 validation failure로 처리한다.

### MP-061 — 곡별 단일 canonical Finger Mapping

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 Finger Mapping은 곡마다 하나의 canonical fingering plan만 학습 입력으로 저장한다.
- 여러 후보 mapping을 actor observation이나 training sampling에 넣지 않는다.
- 선택된 mapping의 cost, 생성 규칙과 provenance는 재현 및 사후 분석을 위해 보존한다.
- Canonical finger identity는 기술 prior이지만 음악적 성공의 hard gate는 아니다. 정책이
  같은 sounding fret을 만드는 다른 유효 손가락을 선택하는 것은 허용한다.
- 다중 후보 mapping은 단일 mapping 편향이 실제 일반화 문제로 확인될 때만 후속 확장한다.

### MP-062 — Onset group 단위 Canonical PlayEvent

```text
상태: DECIDED
결정일: 2026-09-07
```

- 같은 음악 onset에 속한 단음·화음·strum을 하나의 `Canonical PlayEvent`로 묶는다.
- 단음 event는 string target 하나, chord/strum event는 여러 string target과 줄별 timing
  offset을 가진다.
- Fret release와 sustain은 event 내부 string target별로 유지할 수 있다.
- Partial chord/strum 평가는 내부 string target별로 기록하지만 공통 event cursor는
  onset group 단위로 한 번만 진행한다.
- Onset을 같은 그룹으로 묶는 구체 tolerance는 데이터 분포를 확인한 뒤 calibration한다.

### MP-063 — 독립 module checkpoint와 FullBody bundle manifest

```text
상태: DECIDED
결정일: 2026-09-07
```

- Fret, Strike와 StabilityAdapter checkpoint는 각 모듈의 training directory에 독립적으로
  저장한다.
- FullBody는 source weight를 복사한 monolithic checkpoint가 아니라 module reference를
  가진 `player_bundle.json`으로 구성한다.
- 각 reference는 프로젝트 기준 상대경로, file SHA-256, checkpoint contract hash와 module
  type/version을 포함한다.
- Loader는 경로·hash·contract를 모두 검증하고 하나라도 다르면 fail closed한다.
- Rule-based Synchronizer는 weight 대신 config path/hash와 schema version을 기록한다.
- Fine-tuning 결과는 기존 source를 덮어쓰지 않고 parent hash를 가진 새 module checkpoint로
  저장한 뒤 새 FullBody bundle에서 참조한다.
- FullBody bundle은 `song_id`와 canonical timeline/content hash를 포함하며 모든 source
  checkpoint의 곡 identity가 일치해야 한다.

### MP-064 — 성능 기반 G1 assist curriculum

```text
상태: DECIDED
결정일: 2026-09-07
```

- G1 artificial assist는 고정 iteration마다 감소하지 않고 performance-gated staircase로
  줄인다.
- 현재 level에서 guitar stability, Fret·Strike retention과 safety gate를 연속 평가 구간
  동안 통과해야 assist를 한 단계 감소시킨다.
- 감소 후 성능이 rollback threshold를 지속적으로 벗어나면 한 단계 강한 assist level로
  복귀할 수 있다.
- 승급·복귀 threshold 사이에 hysteresis를 두어 level oscillation을 막는다.
- 현재 assist level, 물리 parameter와 연속 통과·실패 counter를 checkpoint에 저장한다.
- 구체 threshold와 평가 구간 길이는 G1 calibration으로 봉인한다.

### MP-065 — 곡별 독립 policy checkpoint

```text
상태: DECIDED
결정일: 2026-09-07
```

- Fret와 Strike는 곡별로 각각 학습하고 곡별 checkpoint를 저장한다.
- 한 곡에서 학습한 checkpoint는 다른 곡의 완성 policy로 직접 resume/evaluate하지 않는다.
- 각 checkpoint와 FullBody bundle은 `song_id`, goal SHA-256와 canonical timeline/content
  hash를 봉인하며 서로 다르면 fail closed한다.
- 재사용 대상은 곡 사이의 동일 weight가 아니라 model architecture, observation/action
  contract, compiler와 curriculum 절차다.
- 다른 곡 checkpoint를 초기값으로 사용하는 transfer는 필수 경로가 아니다. 이후 허용할
  수 있는 확장으로만 남기며 현재 주 실험에서는 사용하지 않는다.
- Song bundle을 train/test 곡으로 나누지 않고 각 곡의 전체 timeline을 학습과 평가에
  모두 사용한다.

### MP-066 — Song bundle의 학습·평가 곡 분할 없음

```text
상태: DECIDED
결정일: 2026-09-07
```

- 곡별 policy를 학습하므로 song bundle을 training song과 evaluation song으로 분리하지
  않는다.
- 각 곡의 전체 canonical timeline을 해당 곡 policy의 학습과 최종 평가에 모두 사용한다.
- 평가는 weight update가 없는 별도 rollout에서 같은 곡의 여러 seed·초기 상태·외란을
  적용한다. 이는 song data split이나 unseen-song 평가가 아니다.
- 논문 결과는 song-specific performance로 기술하며 unseen-song generalization을
  주장하지 않는다.

### MP-067 — StabilityAdapter의 task-summary 입력

```text
상태: DECIDED
결정일: 2026-09-07
```

- StabilityAdapter는 Fret 420D와 Strike 303D actor observation 전체를 입력으로 받지 않는다.
- `FretTaskSummary`는 string별 readiness, fingertip/press error summary와 다음 event까지
  남은 시간을 제공한다.
- `StrikeTaskSummary`는 motor phase, approach/recovery state, pick-lane error summary와 다음
  strike까지 남은 시간을 제공한다.
- `ActionContext`는 StabilityAdapter가 수정할 권한이 있는 joint의 source proposal과 직전
  executed action/residual을 제공한다.
- Summary는 policy self-report가 아니라 authoritative evaluator/detector state에서 만들며
  별도 named contract로 version 관리한다.

### MP-068 — 단일 StabilityAdapter actor와 외부 rule gate

```text
상태: DECIDED
결정일: 2026-09-07
```

- 초기 StabilityAdapter는 여러 learned policy로 나누지 않고 하나의 actor로 구성한다.
- GuitarState, SupportState, TaskSummary와 ActionContext는 각각 encoder를 거쳐 shared
  fusion trunk에서 결합한다.
- Actor는 bounded named residual과 support-need/confidence를 출력한다.
- Fret·Strike consistency, authority cap과 hard safety veto는 actor 외부의 규칙 기반
  gate가 최종 결정한다.
- Learned ConsistencyBranch는 초기 범위에서 제외하고 rule baseline의 한계가 검증된
  경우에만 후속 확장한다.

### MP-069 — Compact named StabilityAdapter residual

```text
상태: DECIDED
결정일: 2026-09-07
```

- StabilityAdapter actor는 full 105D를 출력한 뒤 mask하지 않고 authority가 있는 joint만
  포함한 compact residual을 출력한다.
- ActionArbiter는 action manifest의 joint name으로 compact residual을 최종 105D action
  slot에 배치한다.
- Joint 이름의 누락·중복·순서 불일치는 fail closed한다.
- Wrist 등 새로운 joint group을 활성화하면 StabilityAdapter action contract와 checkpoint
  version을 올리며 기존 checkpoint와 자동 호환하지 않는다.

### MP-070 — 실제 task 결과 우선의 기술 보존

```text
상태: DECIDED
결정일: 2026-09-07
```

- StabilityAdapter의 Fret·Strike 보존 여부는 source action과의 수치적 동일성이 아니라
  실제 sounding-fret·sustain·strike crossing·timing 결과를 primary 기준으로 판단한다.
- 실제 음악 결과가 유지되면 기타 안정화를 위한 shoulder/elbow/body action 변화는
  허용한다.
- Source action deviation과 residual magnitude/rate는 과도한 개입을 줄이는 bounded soft
  regularization 및 drift 진단으로 사용한다.
- Action consistency 점수가 실제 음악 실패를 상쇄하거나 유효한 안정화를 hard reject하지
  않도록 한다.

### MP-071 — 곡별 평가와 macro·worst-song 집계

```text
상태: DECIDED
결정일: 2026-09-07
```

- 각 곡은 해당 곡의 독립 policy/FullBody bundle로 평가하고 곡별 결과를 먼저 보고한다.
- 전체 대표값은 각 곡에 동일 가중치를 주는 macro average를 primary로 사용한다.
- 특정 곡에서의 실패가 평균에 가려지지 않도록 worst-song 성능을 함께 primary 결과로
  보고한다.
- 모든 event를 합친 micro average는 긴 곡이나 event가 많은 곡의 영향이 커지므로 보조
  지표로만 사용한다.

### MP-072 — FullBody의 세 가지 필수 paired baseline

```text
상태: DECIDED
결정일: 2026-09-07
```

- `B0`: free guitar + tension-only virtual strap constraint + source Fret/Strike,
  StabilityAdapter 없음.
- `B1`: StabilityAdapter 사용, lower body hard-lock.
- `B2`: StabilityAdapter 사용, lower body trainable residual.
- 세 조건은 같은 곡, source checkpoint, Synchronizer config, 초기 상태, physics seed와
  외란을 사용해 paired evaluation한다.
- B0→B1 차이는 StabilityAdapter 효과, B1→B2 차이는 trainable lower body의 추가 효과로
  해석한다.

### MP-073 — Synchronizer readiness-gate baseline

```text
상태: DECIDED
결정일: 2026-09-07
```

- 고정 기타 G0에서 `S0 scheduled strike/no Fret-readiness gate`와 `S1 rule-based
  Synchronizer`를 paired 비교한다.
- 두 조건은 같은 곡, Canonical PlayEvent, Fret·Strike checkpoint와 initial seed를 사용한다.
- Premature strike, strike timing error, full/partial event success와 missed event를
  primary 비교 지표로 사용한다.
- 이 baseline은 StabilityAdapter와 free-guitar physics를 제외해 timing supervisor 자체의
  기여를 분리한다.

### MP-074 — 각 곡의 fresh initialization 학습

```text
상태: DECIDED
결정일: 2026-09-07
```

- 각 곡의 Fret·Strike 주 학습은 다른 곡 checkpoint 없이 fresh initialization에서
  시작한다.
- 다른 곡의 actor weight, observation normalization, critic과 optimizer state를
  warm-start 또는 distillation에 사용하지 않는다.
- 초기 random seed와 model initialization contract를 run manifest에 기록한다.
- 동일 곡·동일 계약 checkpoint의 resume와 동일 곡 source checkpoint를 G0→G2에서
  재사용하는 것은 허용한다.
- Cross-song transfer는 현재 연구 범위와 필수 실험에서 제외한다.

### MP-003 — 기본 시선 목표

```text
상태: DECIDED
결정일: 2026-09-05
```

- 기본 GazeTarget은 기타의 `strike_zone`으로 한다.
- strike zone은 strike detector의 유효 crossing interval 중앙에 고정된 body-relative target이다.
- string 방향 위치는 canonical 기타 3번 줄과 4번 줄 중심선의 중간으로 둔다.
- 일반 연주 중에는 event별·string별 시선 전환을 하지 않는다.
- Neck/Head는 target을 부드럽게 추적하며 angular velocity와 switching jerk를 제한한다.
- `guitar_body`와 `custom` target은 이후 별도 실험에서 확장한다.

### MP-005 — Head direction as gaze proxy

```text
상태: DECIDED
결정일: 2026-09-05
```

- 별도의 eye joint가 없는 현재 모델에서는 head forward axis를 gaze direction의 proxy로 사용한다.
- `strike_zone`은 위치 target이고, 별도 orientation target은 저장하지 않는다.
- desired gaze direction은 head/eye proxy 위치에서 strike zone을 향하는 벡터로 계산한다.
- Neck/Head policy는 head forward vector와 desired gaze direction의 차이를 줄인다.
- head roll, neck limit, angular velocity, gaze switching jerk는 별도 safety/reward 항목으로 제한한다.

### MP-004 — Strike zone anchor

```text
상태: DECIDED
결정일: 2026-09-05
```

- strike zone의 crossing 방향 위치는 strike detector의 유효 detection interval 중앙으로 한다.
- string 방향 위치는 canonical 기타 3번 줄과 4번 줄의 중심선 중간으로 한다.
- target은 개별 string/event를 따라 이동하지 않는다.
- canonical string 번호와 simulator index는 conversion manifest를 통해서만 연결한다.

### MP-075 — Synchronizer 3-frame 상한과 Fret press advance

```text
상태: DECIDED
결정일: 2026-09-07
대체: MP-039, MP-041, MP-052의 2-frame 부분
```

- Strike late rescue의 configured 상한은 60 Hz 기준 3 frame, 즉 50 ms다.
- 각 event의 실제 허용치는 다음 event의 traversal·rearm 여유를 침범하지 않도록
  `min(3, floor(outgoing_transition_slack * 60))`으로 계산하므로 0~3 frame이다.
- 이 보정은 Strike detector의 최종 50 ms 허용 오차를 추가로 넓히지 않는다.
- Fret actor용 목표 view는 현재 string이 비압현일 때만 미래 PRESS를 최대 3 frame
  앞당겨 제공할 수 있다. 현재 활성 fret과 release 시점은 변경하지 않는다.
- readiness는 실제 crossing이 발생할 때까지 매 frame 다시 확인한다. crossing 전에
  목표 압현이 풀리면 permission을 닫고, crossing 이후 `t_release`까지의 유지는 별도
  sustain 지표로 평가한다.
- 예정 시각 성공과 지연 구조 성공은 각각 `on_time`, `delayed_rescue`로 분리해 보고한다.

## 1. 입력 파이프라인

- Audio Analysis가 생성하는 note/chord의 최종 schema
- tablature 생성 시 허용할 수동 annotation 범위
- 낮은 confidence event 사용 방식: MP-060에서 전량 사용으로 결정
- tempo map과 timing mode의 기준

Raw audio는 offline 입력으로만 사용하고 confidence는 MP-060에 따라 진단 metadata로만
보존한다.

## 2. Finger Mapping

- mapping 후보 수: MP-061에서 단일 canonical mapping으로 결정
- 손가락 번호와 hand position을 같은 artifact에 저장할지
- 스타일별 mapping profile을 언제 도입할지

## 4. Action 계약

Strike source action은 MP-029, 기본 피크 그립은 MP-030을 따른다.

## 5. Support contact 세부 설정

- 부위별 proxy 크기와 local pose
- 기타 body·neck 중 각 support site가 접촉할 수 있는 영역
- friction·contact offset의 초기 범위
- 그룹별 force attribution과 slip 계산 방식
- 연주 접촉과 support 접촉이 겹칠 때의 우선순위

## 6. Source checkpoint migration

- 기존 Fret-v1/Strike-v1을 teacher로만 사용할지
- v2 observation을 새로 학습할지
- source distillation을 허용할지
- 새 주 실험에는 기존 다른 곡 checkpoint를 전이하지 않으며 곡별 fresh initialization 사용

## 결정 기록 양식

```text
Decision ID:
Date:
Question:
Options:
Chosen option:
Reason:
Affected contracts:
Required experiments:
Rollback condition:
```
