# 오른손 확장 규칙 — Strum과 양손 동기화

> 상태: **설계 정본, 현재 미구현**  
> 이 문서는 제공된 코드 스트로크·Protected String·FretReady 아이디어를 현재 물리 계약과 모순 없이
> 구현하기 위한 다음 단계 규칙이다. 현재 실행 가능 범위는 [RIGHT_HAND_RULES.md](RIGHT_HAND_RULES.md)를
> 따른다.

## 1. 확장 순서

```text
현재 pick single/down
→ pick down-strum
→ target/protected/muted string set
→ 왼손 고정 코드와 결합
→ 느린 코드 전환
→ 매 박 코드 전환
→ up/alternate rhythm
→ 물리 pick·탄성 string·음향
```

strum과 양손 동기화를 동시에 처음 도입하지 않는다. 먼저 오른손만으로 ordered multi-string RELEASE를
검증한 뒤 왼손 readiness를 결합한다.

## 2. Strike와 Stroke를 구분한다

- **strike**: `(agent,string)` 하나에서 발생한 RELEASE 하나.
- **stroke/strum**: 한 agent가 하나의 방향으로 여러 줄에 만든 ordered strike sequence 하나.
- **performance event**: 목표 시각, 왼손 목표, 오른손 stroke plan을 같은 `event_id`로 묶은 상위 사건.

strum의 소리 시작 시각은 첫 번째 **audible target RELEASE**다. 물리 접촉 시작이나 손의 approach 시작을
stroke time으로 사용하지 않는다.

시간 어휘는 다음처럼 분리한다.

```text
BeatTime                         # 악보/메트로놈 격자가 있을 때만
TargetAttackTime = BeatTime + microtiming_offset
ActualReleaseTime                # detector가 측정한 실제 RELEASE
```

현재 곡 입력의 `time`은 `TargetAttackTime` 역할이며 별도 beat grid가 없으면 BeatTime과 같다고 가정하지
않는다. strum은 첫 audible release를 event anchor로 쓰고 나머지 줄은 target별 offset으로 검사한다.

## 3. Strum v2 입력 계약

현재 `[time,frame,string]`은 여러 줄, 방향, muted traversal을 표현할 수 없다. 최소 입력은 다음과 같다.

```json
{
  "event_id": "bar12-beat3",
  "time": 8.250,
  "frame": 495,
  "kind": "strum",
  "agent": "pick",
  "direction": "down",
  "audible_mask":   [true, true, true, true, true, false],
  "traversal_mask": [true, true, true, true, true, false],
  "muted_mask":     [false, false, false, false, false, false],
  "protected_mask": [false, false, false, false, false, true],
  "target_offsets_s": [0.000, 0.008, 0.016, 0.024, 0.032, null],
  "early_s": 0.050,
  "late_s": 0.050,
  "max_span_s": 0.060,
  "zone": {"profile": "preferred_lane"},
  "fret_event_id": "bar12-beat3"
}
```

배열 순서는 Isaac `0=high-e … 5=low-E`다. 위 예시는 설명용이며 실제 down 순회는 index `5→0`
방향이다.

| ID | 수준 | 규칙 |
|---|---|---|
| RH-X01 | MUST | `audible_mask`는 실제로 소리 나야 하는 줄이다. |
| RH-X02 | MUST | `traversal_mask`는 피크 경로가 지나도록 허용된 줄이다. |
| RH-X03 | MUST | `muted_mask`는 traversal에는 포함되지만 audible 성공에는 포함되지 않는 줄이다. |
| RH-X04 | MUST | `protected_mask`는 crossing이 허용되지 않는 줄이며 traversal과 겹칠 수 없다. |
| RH-X05 | MUST | audible은 traversal의 부분집합이고 audible과 muted는 겹치지 않는다. |
| RH-X06 | MUST/PLAN | mute/span 정보 없는 비연속 audible set을 single-agent strum으로 추측하지 않는다. |
| RH-X07 | MUST | direction, 줄별 offset band와 전체 span을 모두 명시한다. |
| RH-X08 | MUST | source annotation → preset → mapper inference의 출처와 hash를 manifest에 남긴다. |

## 4. Strum 실행 규칙

| ID | 수준 | 규칙 |
|---|---|---|
| RH-X09 | TASK | down은 첫 traversal 줄부터 Isaac index가 단조롭게 `5→0` 방향으로 감소해야 한다. |
| RH-X10 | TASK | up은 `0→5` 방향이며 입력 방향 필드가 구현되기 전에는 활성화하지 않는다. |
| RH-X11 | TASK | 목표 줄을 건너뛰거나 반대로 되돌아가 채우는 zig-zag를 한 stroke로 인정하지 않는다. |
| RH-X12 | TASK | audible 줄은 offset window 안에서 정확히 한 RELEASE와 매칭되어야 한다. |
| RH-X13 | TASK | muted traversal은 audible hit가 아니며 별도 mute detector 없이 “음소거 성공”을 주장하지 않는다. |
| RH-X14 | TASK | protected 줄 RELEASE는 해당 stroke의 wrong/extra crossing이다. |
| RH-X15 | TASK | 마지막 target은 `max_span_s` 안에 끝나야 하며 너무 느린 sweep을 동일 onset chord로 인정하지 않는다. |
| RH-X16 | DIAG | 줄별 release 속도와 release 간격의 분산을 기록하되 정상 strum 자료 전에는 hard 범위를 두지 않는다. |
| RH-X17 | SOFT | 마지막 target 뒤 즉시 정지·역전하지 않고 stroke 폭과 세기에 맞는 follow-through를 둔다. |
| RH-X18 | TASK/SOFT | 연속 down의 return은 string field 바깥을 우회해 protected/reverse crossing을 만들지 않는다. |
| RH-X19 | SOFT | strum은 손목·전완을 중심으로 하고 넓은 span/강한 stroke에서 팔꿈치 기여를 점진적으로 허용한다. |
| RH-X20 | MUST | 한 frame의 복수 crossing은 analytic subframe `t` 순서로 정렬한다. |

접촉력이 없는 현재 줄에서는 “유의미한 변형”을 protected 판정에 쓸 수 없다. 모든 string correctness는
RELEASE crossing으로 판정하고, 힘·변형은 물리 string 단계로 미룬다.

## 5. 피크 시작, 깊이, 자세와 세기

| ID | 수준 | 규칙 |
|---|---|---|
| RH-X21 | TASK | stroke 전 pick은 첫 traversal 줄의 entry side 준비 영역에 있고 줄 안에서 대기하지 않는다. |
| RH-X22 | SOFT | 피크 자세는 현재 grip qpos와 tip 접근 경로로만 평가하며 피크 면 각도는 rigid geometry 이후로 미룬다. |
| RH-X23 | TASK/DIAG | 최소 depth는 RELEASE 조건이고 최대 depth는 body dive/걸림 proxy로 먼저 진단한다. |
| RH-X24 | TASK/DIAG | 최소 속도는 유효 sweep에 필요하지만 최대 속도와 목표 세기 mapping은 자료로 보정한다. |
| RH-X25 | DIAG | 한 stroke 안의 줄별 속도·간격 일관성을 기록하되 완전 동일 속도를 강제하지 않는다. |
| RH-X26 | DEFER | `F_pick` 최소/최대 보상은 물리 pick, collision string과 pair-specific force가 생긴 뒤 도입한다. |
| RH-X27 | PLAN | intensity가 없으면 neutral 값을 provenance와 함께 쓰며 오디오 amplitude를 곧바로 pick force로 바꾸지 않는다. |

## 6. 양손 공통 사건

양손은 같은 event index를 소비한다.

```text
PerformanceEvent e_n =
  (event_id, target_time, fret_goal_ref, stroke_plan_ref)
```

각 손은 독립 상태와 결과를 유지한다.

```text
왼손:  HOLD → RELEASE → TRANSIT → PRESS → STABLE_HOLD
오른손: RELEASE → RECOVER → READY/APPROACH → RELEASE
```

| ID | 수준 | 규칙 |
|---|---|---|
| RH-B01 | MUST | 왼손과 오른손 goal은 동일한 `event_id`와 target time을 참조한다. |
| RH-B02 | MUST | 왼손은 다음 오른손 첫 audible RELEASE 전에 목표 음을 안정적으로 준비한다. |
| RH-B03 | TASK | 현재 코드/음은 해당 stroke의 필요한 release span 동안 유효 압현을 유지한다. |
| RH-B04 | PLAN/SOFT | 다음 목표에도 쓰는 anchor finger를 유지하고 나머지 손가락은 release→pre-shape→press한다. |
| RH-B05 | TASK | `FretReady`는 목표 압현, 보호/open 줄 비방해, 안정화, 안전 조건을 모두 만족해야 한다. |
| RH-B06 | PLAN | 준비 완료 목표는 `t_first_release - delta_stabilize` 이전이며 delta는 fret runtime 분포로 보정한다. |
| RH-B07 | MUST | 오른손 detector는 `FretReady`와 관계없이 항상 RELEASE를 기록한다. |
| RH-B08 | MUST | 왼손 미준비가 오른손의 실제 on-time RELEASE를 timing miss로 바꾸거나 숨기지 않는다. |
| RH-B09 | MUST | 오른손 timing, 왼손 readiness, 결합 음 정확도를 서로 다른 metric으로 저장한다. |
| RH-B10 | PLAN | 두 손 모두 최소 다음 event와 남은 transition 시간을 관측한다. |

## 7. FretReady와 결합 성공

`FretReady(n)`은 최소 다음을 포함한다.

1. 필요한 finger/string/fret 목표가 유효하게 눌림.
2. open 또는 release가 필요한 줄을 잘못 누르지 않음.
3. 목표 접촉과 fingertip 속도가 안정화됨.
4. 심각한 관통, hard limit, 비유한 상태가 없음.
5. stroke span 동안 필요한 압현이 유지됨.

결과를 하나로 뭉개지 않는다.

```text
RightHandSuccess(n) = ordered/timed/zone-correct stroke
LeftHandReady(n)    = FretReady before first audible RELEASE

CombinedPerformanceSuccess(n) =
    RightHandSuccess(n)
  ∧ LeftHandReady(n)
  ∧ FretHoldDuringStroke(n)
  ∧ SharedEventAligned(n)
  ∧ NoSafetyFailure(n)
```

## 8. Hard Gate와 Soft Gate의 처리

제공된 “초기 Hard Gate → 이후 Soft Gate”는 유용한 **비교 실험 후보**지만 현재 확정 규칙은 아니다.

- Hard Gate: 왼손 미준비 시 정책의 planned Attack/APPROACH를 보류할 수 있다.
- Soft Gate: 오른손은 target time을 지키고 왼손 미준비를 combined failure로 감점한다.
- Hard Gate도 master clock이나 target time을 뒤로 미루지 않는다. 준비되지 않으면 `blocked_miss`로 남긴다.
- 두 방식 모두 detector를 끄지 않는다.
- Hard Gate가 오른손 timing 학습을 망가뜨리거나 “안 쳐서 FP가 없는” 편법을 만들 수 있으므로
  독립 RH metric과 최종 Soft/ungated 평가를 반드시 유지한다.

최종 목표는 오른손이 늦게 왼손을 기다리는 것이 아니라, 왼손이 target time 전에 준비되는 것이다.

## 9. 양손 예시

```text
1박: C down
2박: C down
3박: G down
4박: G down
```

- 1·2박: 왼손 C를 유지하고 오른손은 각 target time에 down stroke.
- 2박 RELEASE 이후: 공통 finger는 유지하고 이동 finger가 G를 pre-shape/press.
- 3박 직전: `FretReady(G)=true`; 오른손은 첫 traversal 줄 entry side에 ready.
- 3박: 오른손 첫 audible RELEASE가 target time에 발생하고 왼손은 stroke span 동안 G를 유지.
- 3박 이후: 오른손 recovery는 다음 stroke entry와 연결되고 왼손은 다음 event를 준비.

왼손 release 시작 시각은 모든 곡에 같은 비율로 고정하지 않는다. 현재 sustain, 다음 목표 난이도,
tempo와 `delta_stabilize`를 고려해 plan에서 정한다.

## 10. 확장 커리큘럼

현재 A0→A4 단현 curriculum을 통과한 뒤 다음 순서를 사용한다.

| 단계 | 학습 내용 | 새 gate |
|---|---|---|
| X0 | 인접 2줄 down mini-strum | 순서, span, protected clear |
| X1 | 연속 3…6줄 down strum | audible/traversal/muted mask |
| X2 | 다양한 시작 줄과 protected 저음줄 | string-set precision/recall |
| B0 | 고정 왼손 코드 + 반복 down | FretReady와 stroke 동시 유지 |
| B1 | 두 코드, 2·4박마다 전환 | transition success, sustain |
| B2 | 매 박 코드 전환 | readiness deadline, timing |
| X3 | upstroke 단독 | 방향 입력·up recovery |
| X4 | down/up 리듬 패턴 | phrase direction consistency |

각 단계는 정확도·오타·timing·span·readiness를 완료 episode에서 평가한다. iteration 수만으로
승급하지 않는다.

## 11. 물리 모델 이후로 미루는 규칙

다음은 현재 marker 환경에서 구현 완료로 표시하지 않는다.

- 얇은 rigid pick과 엄지·검지의 실제 grasp/slip/회전.
- 탄성 string의 변형, load peak, release vibration과 실제 음향 onset.
- pair-specific pick-string 접촉력과 세기·음색 mapping.
- 실제 mute, palm mute, slap, tap, rasgueado.
- 손톱과 살의 별도 geometry 및 음색.
