# 09. 학습·평가·승급

> 상태: **PROPOSED**

기본 물리 curriculum은 `G0 fixed guitar → G1 strapped + assisted free guitar → G2 strapped final free guitar`로 구성한다. 물리 효과를 갖는 tension-only 가상 strap constraint는 G1부터 계속 유지하고, 별개의 artificial assist만 점진적으로 줄여 G2에서 0으로 만든다.

## 1. 오프라인 데이터 검증

```text
P0 Audio confidence
P1 Tablature validity
P2 Finger mapping validity
P3 Picking/strum validity
P4 Canonical event consistency
```

통과 조건:

- 시간 순서가 단조 증가
- 모든 string/fret/finger가 유효
- Fret과 Strike projection이 같은 event id를 공유
- timing mode와 FPS가 명시됨
- confidence가 낮은 event가 별도 표시됨

Confidence가 낮다는 이유만으로 event를 학습에서 제외하거나 reward를 낮추지 않는다.
구조 계약을 통과한 Tablature 결과는 모두 사용하고 confidence는 subgroup 분석에만 쓴다.
실행 불가능한 string/fret 또는 깨진 시간 순서 같은 schema violation은 confidence 문제와
구분하여 validation failure로 처리한다.

## 2. Skill prior 학습

```text
Fret F0~F6
Strike A0~A4, S0~S3
```

각 곡의 Fret·Strike 주 학습은 기록된 random seed의 fresh initialization에서 시작한다.
다른 곡 checkpoint의 actor, observation normalization, critic 또는 optimizer state를
초기값으로 사용하지 않는다. 동일 곡·동일 계약 안의 resume와 동일 곡 source를 G0→G2에서
재사용하는 것은 허용한다.

각 source는 다음을 만족해야 한다.

- standalone event 성공
- 해당 곡의 전체 event와 transition subgroup 성공
- 같은 곡의 별도 evaluation rollout과 다양한 reset·physics seed 평가
- 안전·관절 제한 통과
- source checkpoint와 observation/action manifest 봉인

Fret checkpoint는 single-note, chord, sustain/release, 빠른 transition 및 short-lead
subgroup, 같은 곡의 evaluation rollout, joint/collision safety gate를 모두 통과해야 한다. 전체 평균
reward나 평균 press accuracy만으로 승급하지 않는다. 각 threshold는 micro-environment와
baseline 분포로 calibration한 뒤 계약에 봉인한다.

Song bundle 자체는 training용과 evaluation용으로 나누지 않는다. 각 곡의 전체 canonical
timeline을 학습과 평가에 모두 사용한다. 평가는 weight update가 없는 별도 rollout에서
같은 곡에 여러 seed·초기 상태·외란을 적용하지만 이를 unseen-song split으로 해석하지
않는다.

현재 Strike의 세부 단계와 metric은 [Strike training 문서](../strike/03_training/README.md)를 참고하되,
Master Plan에서는 unseen-song 일반화가 아니라 각 곡의 독립 성능, worst-event subgroup,
여러 seed·초기 상태·물리 외란에 대한 same-song robustness를 우선한다.

## 3. G0 composition

```text
G0.0 source frozen union
G0.1 common event replay
G0.2 rule-based timing supervisor
G0.3 learned timing model은 rule baseline 실패가 입증된 경우에만 선택적 검토
```

통과 조건:

- source observation, mean, action transform, EMA, PD target 동등성
- Fret/Strike 개별 지표가 baseline 대비 허용 범위
- 조기 strike가 허용되지 않음
- event cursor가 한 번만 진행됨

## 4. G1 stability learning

```text
G1a strong compliant assist
G1b reduced/random assist
G1c zero-assist probes
```

G1에서는 Fret·Strike·Synchronizer source를 동결한다. StabilityAdapter와 G1부터 활성화한 lower-body residual, Neck/Head Gaze/Attention branch는 trainable하게 둔다.

각 episode는 `reset → initial pelvis-relative guitar-pose stabilization → common pre-roll → score/audio frame 0` 순서로
시작한다. Stabilization 중에는 source 관절을 명시적 hold로 유지하고 score runtime을 step하지
않는다. 안정 gate가 연속 조건을 만족한 경우에만 pre-roll을 시작하며, timeout이면 오디오를
시작하지 않고 `preplay_stability_failure`로 종료한다.

G1a→G1b→G1c 전환은 iteration 수로 자동 진행하지 않는다. 각 assist level에서 stability,
source retention과 safety gate를 연속해서 통과해야 다음 level로 내려간다. 감소 후 성능이
지속적으로 rollback 기준을 벗어나면 한 단계 강한 assist로 복귀한다. Curriculum level,
연속 통과·실패 counter와 assist parameter는 checkpoint에 저장한다.

G1의 기타에는 `strapped-v1` 가상 strap constraint를 항상 적용한다. 강도 curriculum의 대상은 strap이 아니라 artificial hand/root assist이며, strap tension은 support observation과 안전 metric으로 계속 기록한다.

Source 해제는 기본 학습 절차가 아니다. StabilityAdapter와 허용된 residual만으로 안정화 실패가 지속된 것이 검증된 경우에만 제한적 fine-tuning 단계로 넘어간다.

StabilityAdapter의 초기 active mask는 body/lower-body와 양쪽 shoulder/elbow다. 양쪽 wrist는 reserved로 두고, 양손 finger에는 residual authority를 주지 않는다.

통과 조건:

- free guitar asset의 질량·관성·CoM이 유효
- reset과 contact가 결정적이고 안정적
- drop/penetration/over-force hard gate 통과
- guitar pose hard-failure envelope 이탈 없이 episode 완료
- envelope 내부에서는 pose·velocity·slip을 soft reward로 최적화
- Fret/Strike event 성능 유지
- assist work와 dependency가 감소

## 5. G2 final physics

```text
G2.0 short phrase
G2.1 full song
G2.2 repeated evaluation seeds
G2.3 외란·물리 parameter randomization
```

인공 assist는 정확히 0이어야 한다. 주 평가는 tension-only 가상 strap 제약을 포함한
`strapped` profile로 하고, `unstrapped`는 추가 비교 조건으로 둔다. 시각화 mesh는 물리력에
관여하지 않는다.

하체는 G1부터 trainable하게 한다. G1a에서는 초기 seated pose 기준의 joint-angle dead-zone reward와 bounded residual cap을 사용하고, G1b와 G2에서 authority를 점진적으로 늘린다.

기타 pose 안정성은 hard-failure envelope과 soft constraint를 함께 사용한다. envelope을 벗어나면 episode를 실패 종료하지만, 내부에서는 기타 pose 오차와 residual 크기를 연속 reward로 평가한다. 단발성 step 오차가 아니라 지속 조건 또는 drop·접촉 상실처럼 회복 불가능한 사건만 종료 원인으로 기록한다.

Neck/Head 6D도 최종 action ABI에 포함하고 G1부터 trainable하게 한다. 초기에는 기타에 부착된 `strike_zone` look target만 사용하며, GazeTarget alignment와 neck/head motion safety를 별도 metric으로 기록한다. 기본 학습 중 target switching은 허용하지 않는다.

## 6. 제한적 fine-tuning

다음 조건이 모두 충족될 때만 source 일부를 해제한다.

- residual cap saturation이 반복됨
- residual cap 확장만으로는 안전·성능 문제가 해결되지 않음
- adapter-off·authority-mask ablation에서 source adaptation 필요성이 확인됨
- G0 rehearsal 성능이 유지됨

해제 순서:

```text
observation adapter
→ proximal arm output rows
→ 마지막 hidden block
→ wrist
→ finger는 별도 승인
```

G0 teacher KL/BC, 낮은 learning rate, source normalization freeze, G0 rehearsal을 사용한다.

## 7. 평가 지표

각 곡은 별도 policy와 FullBody bundle로 평가하고 곡별 결과를 먼저 보고한다. 전체 요약은
각 곡에 동일 가중치를 주는 macro average와 worst-song 성능을 primary로 사용한다. 모든
event를 합친 micro average는 곡 길이·event 수가 많은 곡의 영향이 커지므로 보조 지표로만
보고한다.

FullBody paired baseline은 `B0 strap+source/no-adapter`, `B1 adapter+lower-body-lock`,
`B2 adapter+trainable-lower-body`의 세 조건으로 고정한다. 같은 곡, source checkpoint,
Synchronizer config, 초기 상태, seed와 외란을 사용해 B0→B1 adapter 효과와 B1→B2 하체
효과를 분리한다.

Synchronizer baseline은 고정 기타 G0에서 `S0 scheduled-strike/no-readiness-gate`와
`S1 rule-based Synchronizer`를 같은 source checkpoint와 event timeline으로 paired
비교한다. Premature strike, timing error, full/partial event와 miss를 보고한다.

### 개별 기술

- Fret press/no-press/wrong-press/sustain/chord-ready
- Strike precision/recall/F1
- Strike timing MAE/p95/signed bias
- strum order/direction/traversal
- recovery completion/reset

### 공동 연주

```text
joint_event_success =
    fret_ready_dwell
    AND valid strike
    AND timing window
    AND sustain/recovery
```

### 안정성

- guitar pose/twist RMS/p95
- linear/angular velocity
- settling time
- slip/drop
- contact load/friction reserve
- assistance force/work
- residual cap saturation

### 망각

- G0 source와 composition의 paired regression
- Fret/Strike action distribution drift
- 기존 event별 최악 성능
- 해당 곡의 반복 evaluation seed·외란 조건 성능

기술 보존의 승급 판단은 실제 Fret/Strike event metric을 primary로 사용한다. Source action
deviation과 residual norm/rate는 drift 진단 및 soft regularization이며, action이 다르다는
이유만으로 실제 음악 성공을 실패로 바꾸지 않는다.

## 8. 초기 승급 gate

실제 tolerance는 micro-environment에서 보정한 뒤 봉인한다. 초기 제안은 다음과 같다.

```text
G0 action/PD equivalence: max error ≤ 1e-6
핵심 source metric: baseline의 95% 이상, 절대 저하 2%p 이하
premature strike: 1% 이하
G2 artificial assist: 정확히 0
drop: 0
slip episode: 1% 이하
```

평균 reward가 아니라 모든 필수 gate의 AND로 checkpoint를 승급한다.
