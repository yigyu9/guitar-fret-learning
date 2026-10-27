# G0 Synchronizer 구현

현재 구현은 고정 기타에서 song-specific Fret-v2와 Strike-v2를 하나의 공통 음악
시간축으로 조합하는 단계다. 첫 기준선은 learned joint controller가 아니라 deterministic
timing supervisor다.

## 실행 흐름

```text
song bundle
  -> Canonical PlayEvent timeline / one score clock / one event cursor

shared physical state
  -> Fret-v2 native view (420D)   -> frozen Fret actor   -> 30D
  -> Strike-v2 native view (303D) -> frozen Strike actor -> 30D

physical readiness + detector state
  -> RuleBasedSynchronizer
  -> execute / bounded wait / partial / skip

source-specific action transforms
  -> joint-name scatter into 105D named ABI (97D effective movable + 8D fixed hold;
     G0는 60 source-active + 45 seated-hold)
  -> one common EMA / PD / physics step
  -> post-EMA local actions return to both source history blocks
```

## 구현된 코드

- `tab2body/full/events.py`: song bundle 검증과 canonical event compiler
- `tab2body/full/clock.py`: 단일 score clock과 exactly-once cursor
- `tab2body/full/readiness.py`: effective sounding-fret와 Strike readiness
- `tab2body/full/synchronizer.py`: 최대 3-frame, 실제 event별 0~3-frame safe delay를 갖는 rule supervisor
- `tab2body/full/source_policies.py`: Fret/Strike checkpoint strict loader와 frozen inference
- `tab2body/full/postprocessing.py`: source actuator 범위 handshake, Fret synergy, Strike grip
- `tab2body/full/action.py`: named 105D action manifest와 G0 arbiter
- `tab2body/full/runtime.py`: 위 구성요소의 batched transaction runtime
- `tab2body/env/tasks/task_full.py`: one-simulator backend가 지켜야 할 one-step bridge
- `tab2body/train_full.py`: checkpoint assembly와 CPU tensor/contract probe

## 현재 checkpoint 조립 예시

```bash
python -m tab2body.train --task full \
  --song 02_Jazz1-200-B_solo \
  --fret-checkpoint fret/training/runs/20260909_2338_02_Jazz1-200-B_solo/checkpoints/fret_001500.pt \
  --strike-checkpoint strike/training/runs/20260909_2345_02_Jazz1-200-B_solo/checkpoints/strike_001500.pt \
  --output full/04_training/bundles/02_Jazz1-200-B_solo.g0.json
```

이 조합은 ABI·hash·shape integration smoke에는 사용할 수 있지만 물리 성능 평가용 source는
아니다. Fret checkpoint는 `isolated_press`, Strike checkpoint는 원속도 승급 전
`S3_SONG_INTEGRATION` 상태다. 실제 physical G0는 final-stage 독립 승급을 통과한 두 source와
정확한 source action postprocessor만 허용해야 한다.

Source 승급 판정은 변경 가능한 `training_context` 값만 믿지 않는다. 최종 physical G0
평가에는 그 context hash와 독립 평가 통과 여부가 checkpoint contract 안에 함께 봉인된
qualification이 필요하다. 기존 checkpoint는 이 봉인이 없으므로 integration smoke 전용이다.

## 아직 남은 물리 연결

`FretTask`와 `StrikeTask`를 각각 생성해 두 simulator를 나란히 실행하면 안 된다. 다음
단계에서는 하나의 `GuitarEnvBase`에서 60개 source 관절을 함께 활성화하고 다음 view를
추출해야 한다.

1. 같은 humanoid/기타 tensor에서 Fret-v2 420D view와 press-cell snapshot 생성
2. 같은 tensor에서 Strike-v2 303D view, motor phase와 crossing detector 생성
3. merged collision setup과 source별 normalized-action joint range 검증
4. signed pre-side readiness와 current-pose EMA 역산 hold로 closed permission의
   entry-side phase boundary 집행
5. common EMA/PD와 simulator step을 각각 정확히 한 번 실행
6. crossing의 subframe 시각·방향·canonical traversal 순서 검증

따라서 현재 CPU probe 통과를 실제 기타 연주 성공이나 Isaac Gym rollout 성공으로 해석하지
않는다.
