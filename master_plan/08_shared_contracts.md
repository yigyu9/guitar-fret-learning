# 08. 공통 계약

> 상태: **G0 CPU 계약 구현 — Isaac 물리 통합 전**

모듈이 달라도 다음 계약은 동일하게 사용한다. 계약이 바뀌면 checkpoint와 학습 결과의 호환성을 자동으로 가정하지 않는다.

## 1. 시간 계약

```text
score_time_s       : 음악 기준 시간
physics_time_s     : simulator 시간
event_time_s       : canonical event onset
execution_time_s   : 실제 press/release/crossing 시간
```

`score_time_s`는 단조 증가하며 Fret, Strike, Synchronizer가 공유한다. Runtime에는
Synchronizer가 소유한 cursor와 score clock을 각각 하나만 두며, source policy가 별도
cursor를 진행하거나 실패한 event 때문에 score clock을 뒤로 옮기지 않는다.

G1/G2 episode의 reset 직후에는 score runtime 자체를 아직 step하지 않는다. 초기 pelvis 대비 기타 pose를
목표로 하는 `STABILIZING` gate를 통과한 뒤 score를 `-common_preroll_frames`에서 시작하고,
frame 0에서 오디오 재생을 맞춘다. 이는 진행 중인 score를 pause하는 기능이 아니라 연주 runtime의
시작을 늦추는 별도 pre-play phase다. 안정화 timeout은 음악 event 누락과 구분한다.

Runtime은 raw audio를 직접 읽지 않는다. Tablature, Finger Mapping, Picking Plan을 하나의 `Canonical PlayEvent`로 컴파일한 뒤 이를 유일한 공통 event timeline으로 사용한다.

각 event는 다음 시간을 명시할 수 있다.

```text
target_time
press_start
ready_deadline
strike_window_open
strike_window_close
sustain_until
recovery_deadline
```

Strike release boundary는 event 중심 시각이 아니라 해당 gesture의 가장 이른 string
traversal crossing으로 정의한다. 다음 event 간격을 침범하지 않는 event별 safe cap과
configured 3-frame 상한 중 작은 값만 delay budget으로 사용한다. 따라서 실제 event별
허용치는 0~3 frame이며 3 frame은 60 Hz에서 50 ms다.

오디오에서 얻은 시간이 불확실한 경우에도 training용 조정값은 `timing_mode`와 함께 저장한다.

```text
original
quantized
easy_training
tempo_scaled
```

Fret과 Strike가 서로 다른 timing mode를 사용하면 같은 곡을 학습하는 것이 아니다.

## 2. 좌표계 계약

| 좌표계 | 용도 |
|---|---|
| `G` guitar frame | fret, string, pick lane, target geometry; Fret·Strike primary frame |
| `B` body frame | pelvis 기준 기타와 몸통·허벅지의 상대 위치·속도; StabilityAdapter primary frame |
| `W` world/gravity frame | 중력, 기울기, tipping/drop, 외란 safety; StabilityAdapter secondary frame |

각 field에는 반드시 다음 metadata가 있다.

```text
name, shape, dtype, unit, frame, scale, clip, valid_rule
```

같은 이름의 `position`이라도 frame이 다르면 호환되지 않는다.

`B` frame의 anchor는 pelvis다. G0에서는 pelvis hard-lock을 검증용으로 허용하지만, G1·G2의 본 계약은 pelvis strong hold와 제한적 trainable lower-body residual이다. pelvis hold 오차, joint-angle deviation, residual magnitude는 평가 로그에 포함한다.

## 3. Event 계약

```text
Canonical PlayEvent {
    event_id
    score_time_s
    chord_group
    string_targets[]
    fret_projection
    strike_projection
    sustain_until_s
    ready_deadline_s
    strike_window
    recovery_deadline_s
    schema_version
}
```

하나의 음악 onset group을 하나의 `Canonical PlayEvent`로 만든다. 단음은
`string_targets`가 하나이고 chord/strum은 여러 string target과 string별 timing offset을
같은 event 안에 가진다. 내부 string target별 결과를 기록하더라도 event cursor는 그룹
단위로 한 번만 진행한다. Onset grouping tolerance의 수치는 데이터 검증으로 정한다.

### Fret projection

```text
string_targets[] {
    string, fret, finger, press_start, release, sustain
}
```

### Strike projection

```text
gesture, traversal_mask, audible_mask, direction,
string_offset, sweep_duration, physical crossing constraints
```

두 projection은 서로 다른 action을 가지지만 event id와 score time은 공유한다.

## 4. Action 계약

모든 action은 의미 있는 joint name으로 정의한다.

```text
raw policy action
→ source-specific action transform
→ named joint target/action space
→ residual merge
→ authority mask
→ per-joint cap
→ total cap
→ rate limit
→ EMA
→ PD target
```

inactive action의 neutral은 숫자 0이 아니라 해당 관절의 seated-hold action으로 계산한다.

action manifest에는 다음을 봉인한다.

```text
joint name/order
ctrl_mid
ctrl_half
action_scale
joint limits
EMA coefficient
PD gains
neutral hold target
authority mask
```

현재 Master Plan의 full-body action ABI v1은 105D이다.

여기서 105D는 authored joint name/order를 보존하는 ABI 슬롯 수다. 실제 제어 자유도는
`L/R_Knee_y,z`, `L/R_Toe_y,z`의 zero-range 8축을 제외한 97D로 센다. 고정축은 물리적으로
움직이지 않으며 정책이 예측하지 않지만, 기존 named ABI와 checkpoint 매핑을 위해 슬롯은
삭제하지 않는다.

```text
Fret              30
Strike            30
Thorax/body       15
Lower body        24
Neck/Head          6
---------------------
합계             105D
```

G0에서도 임시 60D ABI를 만들지 않는다. Fret 30D와 Strike 30D만 source-active이고,
나머지 45개 named slot은 초기 seated-hold action으로 유지한다.

```text
G0 external action ABI = 60 source-active + 45 reserved-hold = 105D
```

숫자 `0`은 seated pose를 뜻하지 않으므로 reserved 45D에는 반드시 물리 환경이 계산한
명시적 hold action을 넣는다. G0 action bridge는 두 30D action을 관절 이름으로 scatter할
뿐이며, common EMA/PD는 향후 하나의 Isaac `FullG0Task`가 한 번만 적용한다.

`Neck/Head 6D`는 시선·머리 방향을 위한 action이며, 기타 support residual과 분리한다. lower-body 또는 Neck/Head joint 수가 실제 asset manifest와 다르면 105D를 자동으로 유지하지 않고 새 ABI version을 발행한다.

StabilityAdapter residual은 source pre-tanh/logit 공간이 아니라 source-specific action transform 이후의 named joint target/action 공간에서 적용한다. residual cap은 실제 joint 단위(기본 radian)로 봉인하며, 이후 total cap·safety filter와 common EMA/PD를 한 번만 적용한다.

StabilityAdapter actor는 full 105D masked tensor가 아니라 active joint만 포함한 compact
named residual을 출력한다. ActionArbiter는 action manifest의 joint name으로 이 값을
105D ABI에 scatter한다. 이름 누락·중복·순서 불일치는 fail closed하며 active set 변경은
새 adapter action/checkpoint contract를 요구한다.

## 4.1 Gaze target 계약

```text
GazeTarget {
    mode
    target_point_B
    event_id
    phase
    valid
}
```

가능한 mode는 초기에는 다음으로 제한한다.

```text
strike_zone
```

`strike_zone`은 기타의 **strike detection interval 중앙**에 부착된 안정적인 target이다. string 방향 좌표는 canonical 기타 3번 줄과 4번 줄 중심선의 중간으로 정의한다. 개별 string이나 event마다 target을 교체하지 않는다. 이후 `guitar_body`, `custom`을 추가할 수 있다.

desired gaze direction은 별도 orientation target을 저장하지 않고 다음처럼 계산한다.

```text
desired_gaze_direction_B = normalize(
    strike_zone_point_B - eye_or_head_proxy_position_B
)
```

현재 asset에 독립적인 eye joint가 없으면 head forward axis를 eye direction의 proxy로 사용한다. Neck/Head action은 현재 head forward axis를 desired gaze direction에 맞추는 방향으로 해석한다.

줄 번호는 사람이 읽는 canonical 번호와 simulator 내부 index를 구분한다.

```text
canonical string number
    → string-index conversion manifest
    → simulator marker/body index
```

strike zone 계산에서 3번·4번 줄을 사용할 때도 이 변환 manifest를 통해서만 접근한다. low-E/high-e 순서가 다른 artifact를 직접 섞지 않는다.

## 5. Observation 계약

관측은 flat tensor가 아니라 named block의 concat으로 정의한다.

```text
ObservationManifest {
    block_name
    field_name
    offset
    size
    unit
    frame
    scale
    clip
    valid_rule
}
```

Fret-v1 425D와 Strike-v1 327D는 기존 baseline 계약이다. Strike-v2는 MP-032의
`strike.observation.v2/303D`, Fret-v2는 MP-036의 `fret.observation.v2/420D`를
사용한다. block 또는 field가 바뀌면 새 `schema_version`과 새 normalization을
사용한다.

현재 frozen Fret-v2·Strike-v2 actor에 전달하는 Synchronizer 2D block은 학습 때와 같은
`(strike_permission, timing_correction)=(1, 0)`으로 고정한다. 실제 readiness gate,
permission과 action hold는 이 2D block을 바꾸지 않고 외부 Synchronizer와 105D action
bridge에서 집행한다. Delay 시 Strike의 기존 native timing field만 명시적으로 shift한다.
이 상수를 향후 실제 supervisor state로 바꾸려면 source policy를 새 observation contract로
다시 학습하거나 제한적으로 fine-tuning해야 한다.

StabilityAdapter의 초기 support observation block은 다음과 같다.

```text
SupportContactBlock[group]
    normal_load
    tangential_load
    slip_speed
    contact_flag
```

`group`은 `strap`, `body_contact`, `arm_contact`이며, strap에서는 `normal_load`를 tension으로 해석한다.

StabilityAdapter의 task-preservation 입력은 Fret 420D와 Strike 303D raw actor observation이
아니라 별도 `FretTaskSummary`, `StrikeTaskSummary`, `ActionContext` 계약을 사용한다.
Summary는 readiness evaluator, strike detector와 phase machine의 authoritative state로
생성하며 source observation의 내부 offset을 참조하지 않는다.

현재 `stability.observation.v2`는 264D이며 기타15, support12, Fret summary11, Strike
summary8, active-joint proprio86, action context129, phase3의 named block으로 구성한다.
StabilityAdapter action은 43D로 body15, 가동 가능한 lower-body16, 양쪽 shoulder/elbow12만
소유한다. `L/R_Knee_y,z`와 `L/R_Toe_y,z`는 zero-range이므로 초기 자세로 hold하지만,
최종 FullBody 105D ABI의 named slot에서는 제거하지 않는다.
손목·손가락·Neck/Head는 이 action manifest에 들어가지 않는다.

## Physics runtime 계약

관측과 reward가 접촉력을 사용하는 경우 asset hash만으로는 checkpoint
호환성을 판정할 수 없다. 최소한 `dt`, control frequency, substep 수,
solver iteration, contact/rest offset, contact collection mode, max depenetration velocity를
physics runtime profile에 넣고 hash를 봉인한다.

현재 Fret G0 프로필은 60 Hz, 4 substep, `CC_LAST_SUBSTEP`,
`max_depenetration_velocity=10.0 m/s`다. `CC_ALL_SUBSTEPS`로 학습한 기존
checkpoint는 같은 자세 궤적이라도 net-contact observation/reward의 의미가 다르므로
암묵적으로 resume하지 않고 명시적 contract migration 후 재학습한다.

## 6. Checkpoint 계약

각 checkpoint는 다음 hash를 포함한다.

```text
skill checkpoint hash
observation manifest hash
action manifest hash
event schema hash
timeline/content hash
physics asset hash
support hardware profile/strap route hash
pre-play stability config/reference mode hash
normalization hash
reward/value manifest hash
stage and authority mask
parent checkpoint hash
```

FullBody는 module weight를 하나의 monolithic checkpoint로 복사하지 않고 module별
checkpoint reference를 가진 bundle manifest로 저장한다. 각 reference는 프로젝트 기준
상대경로, file SHA-256와 checkpoint contract hash를 함께 가진다. 경로가 존재하더라도
hash 또는 contract가 다르면 fail closed한다. 제한적 fine-tuning은 기존 source를
덮어쓰지 않고 새 module checkpoint와 parent hash를 생성한 뒤 새 bundle이 이를 참조한다.
Bundle은 `song_id`와 canonical timeline/content hash도 봉인하며, Fret·Strike와 FullBody
bundle의 곡 identity가 다르면 직접 로드를 거부한다.

독립 skill의 `training_context`는 실행 당시 stage·tempo·tolerance를 재현하는 진단 정보로
hash를 계산해 bundle에 보존한다. 그러나 이 변경 가능한 필드만으로 G0 승급을 승인하지
않는다. Physical G0 평가 자격은 context hash, 최종 stage, 원속도, 독립 평가 통과 여부가
checkpoint contract 내부의 qualification으로 함께 봉인된 경우에만 참이다. 기존 봉인 없는
checkpoint는 ABI integration smoke에만 사용한다. Runtime resume은 contract hash뿐 아니라
실제 checkpoint file SHA-256도 동일해야 한다.

다음은 자동 호환으로 간주하지 않는다.

- observation field 추가·삭제·순서 변경
- action name 또는 순서 변경
- EMA/PD/action scale 변경
- fixed guitar와 free guitar asset 변경
- `strapped-v1` route, button/exit guide, stiffness·damping 또는 collision proxy 변경
- detector의 성공 의미 변경
- kinematic strike와 physical strike의 변경
- 105D joint set·이름·순서 또는 action ABI 차원 변경

## 7. Source policy 계약

Fret/Strike source를 재사용할 때 다음이 동일해야 한다.

```text
actor architecture
native observation manifest
obs normalization
action name/order
source action transform
log_std interpretation
deployment EMA/PD
```

source actor에 새 stability observation을 조용히 추가하지 않는다. 필요하면 `SourceObservationBridge`와 별도 major version을 만든다.
