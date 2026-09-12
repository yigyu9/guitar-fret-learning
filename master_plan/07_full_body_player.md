# 07. FullBodyPlayer

> 상태: **105D·G0 CPU 계약 구현 / one-simulator physics·G1/G2 미구현**

`105D`는 최종 named ABI 슬롯 수이며, zero-range 하체 보조축 8개를 제외한 실질 가동
관절 수는 97D다. 고정축은 ABI에 hold 슬롯으로 보존한다.

## 한 줄 정의

FullBodyPlayer는 Fret, Strike, Synchronizer, StabilityAdapter의 출력을 하나의 physics step에서 합성하여 실제 기타 연주를 실행하는 최종 runtime 시스템이다.

FullBodyPlayer는 별도의 monolithic policy가 아니다. 각 모듈은 named proposal만 생성하며, 중앙 `ActionArbiter`가 이를 하나의 최종 action으로 합성한다. 어떤 모듈도 Isaac Gym actuator에 직접 action을 쓰지 않는다.

Fret과 Strike는 최종 단계에서도 별도 actor·checkpoint·observation/action contract를 유지한다. Synchronizer는 양손 사이의 event-level timing만 조정하고, 각 손 내부의 motor timing은 해당 skill prior가 담당한다.

## 입력

```text
- Canonical PlayEvent current/next events
- current simulator state
- FretProposal
- StrikeProposal / StrikeIntent
- FretReadiness
- StrikeResult / detector state
- SyncCommand
- StabilityProposal
- stage/mode/action authority configuration
```

## 출력

```text
PlayerStepOutput {
    executed_action[full action ABI]
    pd_target
    event_trace
    fret_readiness
    strike_result
    stability_metrics
    safety_flags
}
```

FullBodyPlayer가 반환하는 event trace는 학습과 평가에서 동일하게 사용해야 한다.

## Module checkpoint bundle

Fret, Strike, StabilityAdapter와 trainable Gaze/Attention checkpoint는 각 모듈의 training directory에 독립적으로
저장한다. FullBody checkpoint가 source weight를 복제해 포함하지 않고, 하나의
`player_bundle.json`이 immutable checkpoint 경로와 identity를 참조한다.

```text
fret/training/runs/.../checkpoints/fret_xxxxxx.pt
strike/training/runs/.../checkpoints/strike_xxxxxx.pt
stability_adapter/training/runs/.../checkpoints/stability_xxxxxx.pt
gaze/training/runs/.../checkpoints/gaze_xxxxxx.pt
full/training/runs/.../player_bundle.json
```

Bundle의 각 module entry는 프로젝트 기준 상대경로, file SHA-256, checkpoint contract
hash와 module type/version을 포함한다. Loader는 이 값을 모두 확인하고 하나라도 다르면
실행을 중단한다. `latest`처럼 내용이 바뀔 수 있는 alias를 최종 bundle identity로
사용하지 않는다. Rule-based Synchronizer는 weight checkpoint 대신 config path/hash와
schema version을 기록한다.

## ActionArbiter

FullBodyPlayer의 핵심은 각 policy가 별도로 action을 실행하지 않는다는 점이다.

```text
Fret proposal
Strike proposal
Sync command
Stability residual
        ↓
named ownership / priority / mask / cap
        ↓
one final action
        ↓
one EMA
        ↓
PD target
```

초기 action 소유권은 다음과 같다.

| 관절군 | 기본 소유자 | Synchronizer | StabilityAdapter |
|---|---|---|---|
| 왼손 finger | Fret | 금지 | 금지 |
| 오른손 finger | Strike | 금지 | 금지 |
| 왼쪽 shoulder/elbow | Fret | 금지 | G1부터 residual |
| 왼쪽 wrist | Fret | 금지 | 초기 reserved |
| 오른쪽 shoulder/elbow | Strike | 직접 torque 금지 | G1부터 residual |
| 오른쪽 wrist | Strike | 직접 torque 금지 | 초기 reserved |
| Thorax/body | 없음 또는 hold | 금지 | 단계적 권한 |
| Lower body | hold prior | 금지 | G1부터 trainable residual |
| Neck/Head | Gaze/Attention branch | 금지 | 금지 |

같은 관절을 두 branch가 수정해야 할 경우에도 단순 합산으로 끝내지 않는다.

```text
candidate residual
→ consistency gate
→ per-source cap
→ total joint cap
→ phase authority mask
→ safety filter
```

## 우선순위

```text
hard safety
> source finger integrity
> valid fret/strike event
> timing quality
> posture comfort
```

안정성을 위해 event를 늦추는 것은 가능하지만, 안정성 reward를 얻기 위해 잘못된 타현을 성공으로 기록할 수는 없다.

## Runtime 순서

```text
1. simulator state refresh
2. Canonical EventStream 조회
3. Fret/Strike source observation projection
4. Fret/Strike proposal 생성
5. readiness·detector·stability 계산
6. Synchronizer command 계산
7. StabilityAdapter residual 계산
8. ActionArbiter 합성
9. common EMA/PD 적용
10. physics step
11. event/safety/reward 기록
12. event cursor와 phase 갱신
```

한 physics step에서 event cursor를 두 번 이상 전진시키지 않는다.

## G0/G1/G2

### G0 fixed guitar

- guitar root fixed
- guitar gravity off
- source equivalence와 Synchronizer 검증

### G1 assisted free guitar

- G2와 동일한 free guitar asset
- gravity on
- tension-only 가상 strap constraint는 항상 활성화
- 별도의 artificial hand assist를 강하게 시작해 점진적으로 감소
- Fret·Strike·Synchronizer source는 동결
- StabilityAdapter, lower-body residual, Gaze/Attention branch는 trainable

### G2 final free guitar

- artificial assist λ=0
- 가상 strap constraint는 유지하며 기본 profile을 `strapped-v1`으로 명시
- `unstrapped`는 구조 비교용 보조 평가 profile
- 짧은 phrase에서 해당 곡의 full song과 다양한 evaluation seed·외란 조건으로 확장

현재 human root와 하체가 고정되어 있다면 이 시스템은 엄밀히 말해 seated upper-body player다. 사람 전신 balance를 포함하는 단계는 별도 physics/action 계약으로 분리한다.

최종 목표에서는 하체 action slot을 제거하지 않는다. 평상시에는 초기 seated 자세 근처에서 동작하고, 기타 tipping/slip 또는 외란 recovery가 필요할 때만 작은 보정을 사용하도록 한다.

StabilityAdapter는 양쪽 shoulder/elbow까지 residual authority를 가질 수 있다. 왼쪽은 neck 지지, 오른쪽은 guitar body 지지를 담당할 수 있다. 양쪽 wrist는 초기에는 reserved로 두고, 양손 finger는 Fret/Strike source가 독점한다. 이 residual은 별도 action dimension이 아니라 기존 named action 위에 적용된다.

최종 action 합성 순서는 다음과 같다.

```text
Fret/Strike source action
    → source-specific action transform
    → named joint target/action space
    → StabilityAdapter residual
    → total joint cap + safety filter
    → common EMA/PD
```

이 순서를 사용하면 StabilityAdapter는 실제 관절 단위로 보정량을 제한하면서도 source policy의 pre-tanh/logit 및 확률 계약을 건드리지 않는다.

## Neck/Head와 look target

최종 FullBody action manifest는 다음 105D를 사용한다.

```text
Fret              30
Strike            30
Thorax/body       15
Lower body        24
Neck/Head          6
---------------------
합계             105D
```

이는 현재 lower-body 24D, Neck/Head 6D 가정에 따른 값이며 최종 joint manifest에서 이름과 순서를 다시 봉인한다.

Neck/Head는 StabilityAdapter가 소유하지 않는다. 기타 지지가 아니라 시선과 머리 방향의 task behavior이므로 별도의 `GazeTarget/AttentionBranch`가 target을 만들고, FullBodyPlayer가 6D action을 합성한다. G1부터 이 branch를 학습한다면 가중치는 별도 gaze checkpoint로 저장하고 player bundle이 참조한다.

```text
GazeTarget {
    mode              # strike_zone / guitar_body / custom
    target_point_B
    valid
}
```

초기 기본값은 `strike_zone`이다. 이는 개별 string이나 event를 따라 빠르게 이동하는 점이 아니라, 기타의 **strike detection interval 중앙**에 붙은 안정적인 기준점이다. string 방향으로는 canonical 기타 3번 줄과 4번 줄의 중심선 사이를 사용한다. 기타가 몸통에 대해 움직이면 target도 기타와 함께 body frame에서 이동한다.

target point에서 현재 head/eye proxy까지의 방향 벡터를 desired gaze direction으로 계산한다. 별도의 eye joint가 없는 현재 모델에서는 head forward axis를 gaze direction의 proxy로 사용한다. actor는 target point 자체를 action으로 받는 것이 아니라, 현재 head forward vector와 desired gaze direction의 오차를 보고 Neck/Head action을 출력한다. target 변경은 낮은 빈도로만 허용하고, 기본 연주 중에는 `strike_zone`을 유지한다.

권장 reward는 다음과 같다.

```text
r_gaze =
    target_alignment
  - neck_angle_limit_penalty
  - head_angular_velocity_penalty
  - gaze_switch_jerk_penalty
  - head_roll_penalty
```

초기에는 `strike_zone` 하나만 사용하고, `guitar_body`·`custom` target은 이후 ablation 또는 별도 연주 형태에서 확장한다.

## 최종 성공 정의

```text
Fret-ready dwell 완료
AND Strike event 정확
AND timing window 통과
AND sustain/recovery 통과
AND guitar stability envelope 통과
AND safety gate 통과
```

평균 episode reward가 높아도 이 조건 중 하나라도 반복적으로 실패하면 FullBodyPlayer release로 승격하지 않는다.

## 필수 FullBody baseline

최종 free-guitar 조건에서는 다음 세 구성을 같은 곡, 초기 상태, physics seed와 외란으로
paired evaluation한다.

```text
B0: strap + source Fret/Strike, StabilityAdapter 없음
B1: StabilityAdapter 사용, lower body hard-lock
B2: StabilityAdapter 사용, lower body trainable residual
```

`B0→B1`은 StabilityAdapter의 효과, `B1→B2`는 posture-constrained whole-body control에서
trainable lower body의 추가 효과를 측정한다. 세 조건은 동일한 source checkpoint와
Synchronizer config를 사용한다.
