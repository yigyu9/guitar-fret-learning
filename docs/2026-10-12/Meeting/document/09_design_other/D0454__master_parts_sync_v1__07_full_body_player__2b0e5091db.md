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

Fret, Strike와 향후 추가할 모듈 checkpoint는 각 모듈의 training directory에 독립적으로
저장한다. FullBody checkpoint가 source weight를 복제해 포함하지 않고, 하나의
`player_bundle.json`이 immutable checkpoint 경로와 identity를 참조한다.

```text
fret/training/runs/.../checkpoints/fret_xxxxxx.pt
strike/training/runs/.../checkpoints/strike_xxxxxx.pt
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

현재 구현된 G0 action 소유권은 다음과 같다. StabilityAdapter의 active joint, residual 범위와
공유 관절 정책은 새 환경 계약에서 정하며 아래 표로 미리 고정하지 않는다.

| 관절군 | G0 소유자 | Synchronizer |
|---|---|---|
| 왼손 action | Fret | 직접 action 금지 |
| 오른손 action | Strike | 직접 action 금지 |
| 나머지 named slot | seated hold | 직접 action 금지 |

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
5. readiness·detector 계산
6. Synchronizer command 계산
7. ActionArbiter 합성
8. common EMA/PD 적용
9. physics step
10. event/safety/reward 기록
11. event cursor와 phase 갱신
```

StabilityAdapter가 다시 구현되면 residual 계산 위치와 실패 처리를 새 통합 계약으로 추가한다.

한 physics step에서 event cursor를 두 번 이상 전진시키지 않는다.

## G0/G1/G2

### G0 fixed guitar

- guitar root fixed
- guitar gravity off
- source equivalence와 Synchronizer 검증

### G1 assisted free guitar

환경, trainable joint와 assist curriculum은 새 StabilityAdapter 환경 계약에서 다시 정의한다.
스트랩은 원본 `strapped-v1` 계약만 보존했으며, 새 환경의 물리 검증 전에는 실행 계약이
확정된 것으로 보지 않는다. 자세한 내용은
[StabilityAdapter 실행 계획](../docs/2026-10-12/plans/LEAN_STABILITY_ADAPTER_EXECUTION_PLAN.md)을 따른다.

### G2 final free guitar

G2의 최종 물리 조건과 평가 profile은 G1 환경 계약과 검증 결과가 확정된 뒤 정의한다.

현재 human root와 하체가 고정되어 있으므로 구현 범위는 seated upper-body player다. 자유기타,
사람 balance, StabilityAdapter의 관절 소유권과 action 합성 순서는 새 physics/action 계약에서
함께 정의한다. 확정 전에는 G0의 105D named ABI나 source policy 계약을 자동 승계하지 않는다.

## 현재 G0 action manifest

현재 G0 runtime은 다음 105D named ABI를 사용한다.

```text
Fret              30
Strike            30
Thorax/body       15
Lower body        24
Neck/Head          6
---------------------
합계             105D
```

현재 lower-body 24D와 Neck/Head 6D는 reserved hold다. G1/G2의 최종 joint manifest,
Neck/Head 소유권, gaze target·reward와 checkpoint 분리는 새 FullBody action 계약에서 정하며
현재 105D 구성을 자동 승계하지 않는다.

## 최종 성공 정의

```text
Fret-ready dwell 완료
AND Strike event 정확
AND timing window 통과
AND sustain/recovery 통과
AND 정의된 모듈의 안전·안정성 gate 통과
AND safety gate 통과
```

평균 episode reward가 높아도 이 조건 중 하나라도 반복적으로 실패하면 FullBodyPlayer release로 승격하지 않는다.

## FullBody baseline

현재 baseline은 G0 source equivalence와 Synchronizer 검증만 포함한다. 자유기타 support 조건,
하체 권한과 StabilityAdapter ablation은 새 환경·평가 계약이 확정된 뒤 정의한다.
