# 양손 병합 및 기타 안정화 시스템 설계 초안

> **상태: SUPERSEDED.** 75D action과 learned joint coordinator를 검토하던 역사 문서다. 현재 정본은 [`master_plan`](../../master_plan/README.md)과 [`03_implementation/README.md`](../03_implementation/README.md)다.

> 상태: **개념·계약 설계 중 — 모델과 수치는 아직 확정하지 않음**  
> 작성일: 2026-08-26  
> 목표: 학습된 Fret·Strike 정책을 보존하면서 양손 연주와 기타 안정화를 하나의 Full 시스템에서 수행한다.

## 1. 시스템이 수행해야 할 일

Full 시스템에는 서로 다른 세 가지 책임이 있다.

1. **왼손 연주**
   - 목표 프렛과 손가락으로 줄을 누른다.
   - 타현 전 준비와 타현 후 sustain을 유지한다.
2. **오른손 연주**
   - 목표 줄을 올바른 방향과 시각에 타현한다.
   - 타현 후 줄에서 빠져나와 다음 event를 준비한다.
3. **기타 안정화**
   - 기타의 위치·방향·선속도·각속도를 허용 범위에 유지한다.
   - 팔·손의 실제 접촉 변화와 외란에서 slip·낙하·과도한 접촉력을 막는다.
   - 손 보조 연결이 점차 사라져도 실제 접촉만으로 기타를 유지한다.

Fret과 Strike의 기본기는 다시 학습하지 않는다. 두 source 정책은 제안 행동을 만들고, Full 모델은 **이벤트 동기화와 물리적 지지에 필요한 최소 수정**만 학습한다.

---

## 2. 추가 모델이 필요한 이유

### 2.1 단순 동시 재생의 한계

Fret과 Strike가 같은 악보 시계를 사용해도 다음 문제가 남는다.

- Fret의 압현 성공 허용 window와 Strike의 타현 허용 window가 겹친다.
- 각각 허용 범위 안에서 성공해도 Strike가 Fret 준비보다 먼저 발생할 수 있다.
- 한쪽 팔의 움직임이 몸과 기타를 통해 반대쪽 손을 교란한다.
- 단일손 학습 중 반대편 손은 거의 고정되어 있어, 양손 live 상태는 source actor에 분포 밖 관측이 될 수 있다.
- 고정 기타에서 학습한 정책에는 기타의 낙하·회전·타현 반력을 제어한 경험이 없다.

따라서 학습 없는 병렬 실행은 반드시 측정할 baseline이지만 최종 구조로 충분하다고 가정하지 않는다.

### 2.2 규칙만으로 해결할 수 없는 부분

규칙은 다음과 같은 이산 조건에 적합하다.

- 왼손이 준비되기 전 타현 금지
- Deadline을 넘긴 event는 skip
- 기타가 위험 envelope에 들어가면 recovery 또는 종료
- Reserved 관절을 중립 자세로 유지

그러나 규칙만으로는 여러 관절의 연속적인 보정량을 결정하기 어렵다.

- 어느 어깨·팔꿈치로 얼마만큼 기타의 회전·미끄러짐을 억제할지
- 기타가 회전하기 전에 어떤 자세로 brace할지
- Fret 준비를 앞당길지 Strike를 늦출지
- Slip과 접촉력 사이에서 어느 방향으로 움직일지

따라서 **명시적 규칙 supervisor + 학습된 제한적 coordinator** 조합을 사용한다.

---

## 3. 현재 가장 유력한 모델 구조

현재 제1 후보는 분리형 `Latent Sync + Action Support` 구조다.

```text
                         Common score/event supervisor
                                      |
             +------------------------+-----------------------+
             |                                                |
Fret native observation                         Strike native observation
             |                                                |
     Frozen Fret actor                                 Frozen Strike actor
             |                                                |
             +------ source feature/action proposals --------+
                                      |
                       +--------------+--------------+
                       |                             |
                  SyncBranch                   SupportBranch
             양손 timing/latent 수정       기타 6DoF/action 수정
                       |                             |
                       +--------- Named Arbiter ----+
                                      |
                          one joint TanhNormal sample
                                      |
                         source action transforms
                                      |
                    inactive seated-hold action override
                                      |
                              common EMA + PD
```

### 3.1 Frozen source adapters

- Fret과 Strike actor, source `obs_rms`, source action transform을 보존한다.
- 각 source가 학습할 때 사용한 native observation을 정확히 재구성한다.
- 반대편 손의 OOD 채널은 초기에는 source RMS 평균으로 가린다.
- 움직이는 기타에 대한 **자기 손의 guitar-relative geometry는 live**로 유지한다.
- Source checkpoint와 observation/action 계약 hash를 Full checkpoint에 저장한다.

### 3.2 SyncBranch

입력:

- Fret·Strike source feature
- 현재 event, target onset, remaining time
- Fret-ready 상태와 dwell
- 다음 Strike 줄·방향·시각

출력:

- Fret·Strike latent 또는 제한된 timing residual

역할:

- Fret 준비를 조금 앞당기거나 유지한다.
- 너무 빠른 Strike를 억제한다.
- 늦은 Strike와 양손 recovery를 조정한다.

마지막 layer는 zero-init해 초기 행동이 두 source의 병렬 실행과 같게 만든다.

### 3.3 SupportBranch

입력:

- Guitar pose relative to Chest/Pelvis
- Guitar linear/angular velocity와 gravity direction
- 손·팔뚝·허벅지 support geometry와 contact/slip margin
- Assist mode, tether 강도 `λ`, extension과 tension
- 다음 Strike의 시각·방향과 source proposed action
- 이전 support residual과 executed action

출력:

- 75D action 공간에 대한 bounded pre-tanh residual

역할:

- 타현 동작 전에 기타 지지를 방해하지 않는 자세를 준비한다.
- 팔·손 접촉 변화 후 기타를 허용 envelope로 복귀시킨다.
- `R_Thorax`와 필요한 proximal·몸통 관절을 사용해 slip과 낙하를 막는다.

Sync와 Support는 trainable trunk와 optimizer group을 분리한다. G1 안정화 학습이 G0에서 배운 timing을 망가뜨리지 않게 각각 동결할 수 있어야 한다.

### 3.4 Named Arbiter와 공동 행동 분포

두 branch가 같은 어깨·팔꿈치를 수정할 수 있으므로 다음 규칙을 적용한다.

1. 관절별 source owner와 branch authority mask 적용
2. Sync와 Support residual에 각각 cap 적용
3. 두 residual을 합친 뒤 관절별 총 cap 적용
4. 최종 mean/std를 구성
5. Joint TanhNormal에서 한 번만 sample

Fret, Strike, Support action을 각각 sample한 뒤 더하지 않는다. 그래야 PPO log-prob이 명확하고 하나의 공동 정책으로 학습할 수 있다.

### 3.5 Central multi-head critic

초기 후보는 11개 value/reward head다.

```text
Fret strings                 6
Strike                       1
Joint event                  1
Guitar pose/twist            1
Physical support/safety      1
Assist dependence/action     1
total                       11
```

이 shape은 G0부터 유지한다. 고정 기타에서는 물리 head를 diagnostic 또는 reward weight 0으로 두고, G1부터 활성화한다.

---

## 4. Action 병합 계약

### 4.1 75D 장기 ABI 후보

```text
Fret source                    30
Strike source                  30
L_Thorax + R_Thorax             6
reserved Torso/Spine/Chest      9
total                          75
```

- G0에서는 source 60개만 active다.
- G1에서 먼저 `R_Thorax`, 이후 필요하면 `L_Thorax`를 단계적으로 연다.
- 중앙 몸통 9개는 shape만 예약하고 필요성이 입증될 때까지 inactive다.
- Neck/Head와 하체는 현재 action 계약에서 제외한다.
- Guitar root를 직접 action으로 움직이지 않는다.

현재 사람 root와 하체는 고정되어 있으므로 `완전 자유`는 우선 기타 root가 자유롭다는 의미다. 사람의 균형까지 풀 경우 별도 단계와 ABI 검토가 필요하다.

### 4.2 관절별 소유권

| 관절군 | 기본 소유자 | Sync | Support |
|---|---|---|---|
| 왼손 finger | Fret | 금지 | 금지 |
| 오른손 finger | Strike | 금지 | 금지 |
| 양 wrist | Source | 제한된 timing | 초기 금지 |
| 양 shoulder/elbow | Source | 제한 허용 | 단계적으로 허용 |
| `L_Thorax` | Reserved | 금지 | 후기 후보 |
| `R_Thorax` | Support | 금지 | 첫 신규 권한 |
| 중앙 몸통 9 | Reserved | 금지 | G2 후기 후보 |

Finger residual은 마지막까지 source 독점으로 두는 것이 기본 원칙이다.

### 4.3 Reserved action의 중립값

Inactive action을 숫자 `0`으로 덮으면 안 된다. 현재 normalized action 0은 관절 hard range의 midpoint이므로 seated pose가 변할 수 있다.

```text
hold_action[joint] = actions_for_pd_targets(init_pose[joint])
```

- Inactive slot은 관절별 seated-hold action으로 override한다.
- 해당 slot은 PPO log-prob과 entropy에서 mask한다.
- Neutral action 값과 계산 버전을 checkpoint manifest에 저장한다.

---

## 5. 한 control step의 병합 순서

```text
1. 공통 score cursor에서 current/future event window 생성
2. Fret·Strike native observation 각각 구성
3. Frozen source actor에서 feature, mean, std 계산
4. SyncBranch에서 양손 timing correction 계산
5. SupportBranch에서 기타 안정화 correction 계산
6. Named Arbiter에서 ownership, phase mask, total cap 적용
7. 최종 joint distribution에서 raw action 한 번 sample
8. Fret·Strike source action transform을 각 slice에 적용
9. 관절 이름으로 75D full action 조립
10. Inactive slot을 seated-hold action으로 override
11. Common EMA와 PD target 적용
12. Physics step 후 event·접촉·기타 안정화 결과 판정
```

Rollout에는 joint distribution에서 sample한 raw action과 그 log-prob을 저장한다. Environment transform과 safety gate는 deterministic 실행 변환으로 별도 기록한다.

---

## 6. 양손 병합 규칙

### 6.1 하나의 악보 시계

Fret과 Strike compiler는 다음을 공유한다.

- Event ID
- Onset, duration, deadline
- Fret target과 담당 finger
- Strike target string과 direction
- Tie, hammer-on, pull-off처럼 Strike가 없어야 하는 event
- Chord/strum cluster의 원자성

각 compiler가 독립적으로 시간을 반올림하면 coordinator가 정책 오차가 아니라 데이터 clock 오차를 학습하므로 금지한다.

### 6.2 Fret 준비 조건

```text
fret_ready(event, t) =
  target strings/frets/fingers correct
  AND required pressure/contact satisfied
  AND minimum ready dwell satisfied
  AND no penetration/over-force failure
```

한 프레임의 우연한 접촉을 준비 완료로 인정하지 않는다. Chord/strum은 필요한 줄 전체가 동시에 준비되어야 한다.

### 6.3 기타 안정 조건

```text
guitar_stable(t) =
  pose error within envelope
  AND linear/angular velocity within envelope
  AND support/slip margin valid
  AND minimum stable dwell satisfied
```

타현 직전과 직후에는 event phase에 맞는 서로 다른 envelope를 사용할 수 있다. Strike 직후의 정상 충격을 즉시 실패로 판단하지 않고 짧은 recovery window 후 settling을 측정한다.

### 6.4 타현 허용 조건

```text
strike_permission(event, t) =
  event requires strike
  AND strike approach/direction valid
  AND fret_ready(event, t)
  AND guitar_stable(t)
  AND t is inside strike window
```

- 조건이 만족되지 않으면 조기 타현에 성공 reward를 주지 않는다.
- 음악 clock은 멈추지 않는다.
- Deadline까지 준비되지 않으면 늦게 치지 않고 miss/skip한다.
- Ready gate가 영원히 닫혀 학습 신호가 사라지지 않도록 curriculum 또는 제한된 escape를 둔다.

### 6.5 Sustain과 recovery

- Strike 후 Fret은 note duration 동안 필요한 압현을 유지한다.
- 오른손은 줄과 기타 body를 불필요하게 계속 누르지 않고 recovery zone으로 이동한다.
- 기타는 strike 동작과 실제 support contact 변화 후 정해진 시간 안에 pose/twist envelope로 복귀한다.
- 다음 event 준비가 현재 sustain을 지나치게 깨지 않도록 overlap rule을 명시한다.

---

## 7. 기타 고정 해제와 안정화 규칙

### 7.1 단계

| 단계 | 기타 물리 | 인공 보조 | 학습 모듈 |
|---|---|---|---|
| G0 | Fixed root, gravity off | 없음 | Sync만 |
| G1a | Free root, gravity on | 강한 soft hand tether | Support만, Sync freeze |
| G1b | 동일 free asset | 약한/random tether + zero probe | Support, 후기 joint refine |
| G2 | 동일 free asset | 정확히 0 | 최소 joint fine-tune |

G0→G1은 asset load 설정이 바뀌므로 별도 환경과 stage promotion으로 처리한다. G1→G2는 같은 free asset에서 tether 강도 `λ`만 0으로 낮춘다.

### 7.2 손 보조 연결 규칙

Hard weld는 사용하지 않는다.

- Fret fingertip과 pick을 기타에 직접 묶지 않는다.
- 왼쪽 palm/thumb-side와 neck support anchor를 연결한다.
- 오른쪽 wrist/forearm-side와 guitar body support anchor를 연결한다.
- 연주 진행 방향에는 slack을 크게 두고 분리·낙하 방향에는 더 큰 stiffness를 둔다.
- Spring-damper force에 dead-zone, force cap, torque cap, rate limit을 둔다.
- 가능하면 기타와 사람에게 equal-and-opposite force를 적용한다.
- Reset 직후 live body state가 유효해질 때까지 tether를 최소 한 physics frame 비활성화한다.

### 7.3 Tether 의존 방지

- Assist level `λ`는 actor와 critic이 관측한다.
- 한 episode 안에서는 `λ`를 고정한다.
- Tether force·torque·impulse·work를 기록한다.
- 약한 assist 단계부터 exact-zero-tether episode를 섞는다.
- 평균 assist return이 아니라 zero-tether 성공률로 G2 진입을 결정한다.

### 7.4 안정화 reward 원칙

- 정확한 한 pose가 아니라 허용 pose/orientation dead-zone을 사용한다.
- Contact force 크기 최대화 대신 `[Fmin,Fmax]` 지지 band와 slip margin을 보상한다.
- Strike 직후에는 짧은 velocity grace를 주고 이후 settling을 평가한다.
- Drop, penetration, over-force, body collision을 별도 safety 지표로 유지한다.
- 안정화 reward가 Fret·Strike 실패를 상쇄하지 못하도록 음악 지표를 별도 acceptance gate로 둔다.

---

## 8. 안전과 실패 처리 우선순위

```text
hard drop/over-force safety
  > source finger integrity
  > event timing
  > posture comfort
```

### Recoverable 상태

- Guitar pose/twist가 정상 envelope를 벗어났지만 복구 가능한 상태
- 제한된 recovery window 동안 Support authority를 사용
- 해당 구간 Strike는 skip할 수 있지만 score clock은 계속 진행

### Terminal 상태

- Guitar drop/floor contact
- Pose·velocity runaway
- Tether extension/force/solver impulse 초과
- 손·기타 penetration 또는 over-force
- Nonfinite state/action/contact
- Human joint/velocity hard safety 위반

Hysteresis와 dwell을 사용해 한 프레임 접촉 spike를 실제 실패와 구분한다.

---

## 9. 학습 순서

```text
S0 source equivalence 검증
→ S1 fixed frozen union baseline
→ S2 fixed A/B Sync 모델 비교
→ S3 free + strong soft tether, Support-only
→ S4 weak/random tether + zero-assist probe
→ S5 fully free, short phrase → full song
→ S6 held-out song/tempo/physics
```

핵심 원칙:

- Fret·Strike release checkpoint 전에는 긴 Full 학습을 시작하지 않는다.
- Source 두 정책은 모든 단계에서 frozen이다.
- G1 초기는 Sync를 freeze하고 Support만 학습한다.
- 현재 단계뿐 아니라 이전 단계의 회귀 평가도 통과한 checkpoint만 승급한다.
- Temporal TCN/GRU는 current-state 모델의 시간 정보 부족이 입증된 뒤에만 추가한다.

---

## 10. 단계 전환 평가 항목

### 연주

- Fret accuracy, sustain, thumb support
- Strike string, direction, timing, recovery
- Fret-ready→Strike signed offset
- Premature strike, deadline miss/skip
- Joint event precision/recall/F1

### 기타

- Position/orientation RMS와 p95
- Linear/angular velocity RMS와 p95
- Drop/slip/recovery rate
- Strike 후 settling time
- Support distribution, over-force, penetration
- Tether assistance fraction과 exact-zero 성능

### 모델 개입

- Sync/Support residual norm
- Per-joint cap saturation
- Branch conflict와 head-off 성능
- Source mean/action drift
- Action rate, jerk, saturation

승급 수치는 G0와 source release checkpoint의 실측 분포를 얻은 뒤 확정한다.

---

## 11. 구현 전 필수 조건

1. Fret·Strike source checkpoint와 observation/action transform을 release 상태로 확정한다.
2. Free guitar의 target mass, inertia, center of mass를 명시한다.
3. Guitar rigid-body name/order와 marker lookup을 load-time audit한다.
4. Fret thumb-support와 Strike pluck-range를 함께 처리하는 Full 전용 atomic collision profile을 만든다.
5. `strapped-v1`을 이식하고 humanoid·guitar 양쪽의 전체 선분 비관통 gate를 통과시킨다.
6. Guitar pose/velocity, strap tension, tether/support slot을 G0부터 고정 observation shape에 넣는다.
7. 75D reserved 관절의 seated-hold neutral action을 계산한다.
8. Source zero-residual equivalence test와 one-joint-distribution PPO test를 만든다.
9. G2 평가에서 artificial force가 정확히 0이고 physical strap은 활성 상태인지 assertion한다.

---

## 12. 아직 결정할 항목

- 75D action ABI 최종 확정
- SyncBranch를 latent 방식으로 할지 단일 action residual로 할지
- 양쪽 hand support anchor의 정확한 body/point
- 중앙 몸통 9개를 어느 단계에서 실제로 해제할지
- SupportBranch에 temporal history가 필요한지

현재 모델 후보 선택 과정은 [`MODEL_SELECTION.md`](02_architecture/MODEL_SELECTION.md), 상세 근거는 [`MODEL_FUSION_STUDY.md`](02_architecture/MODEL_FUSION_STUDY.md), 기타 물리 설계는 [`GUITAR_STABILIZATION.md`](02_architecture/GUITAR_STABILIZATION.md), 학습 단계는 [`CURRICULUM.md`](CURRICULUM.md)를 참조한다.

---

## 13. 요약

```text
규칙은
  공통 시계, 준비·안정 gate, deadline, 안전을 담당한다.

SyncBranch는
  두 학습 정책 사이의 타이밍 오차를 최소 수정한다.

SupportBranch는
  손 보조가 줄어들어도 기타가 안정되도록 몸의 행동을 수정한다.

Frozen source policies는
  이미 학습한 Fret·Strike 기본기를 제공한다.
```

최종 목표는 두 source를 다시 학습하는 하나의 거대 정책이 아니라, **기존 기술을 보존하면서 양손 event 성공과 자유 기타 지지를 추가하는 제한적 Full coordinator**다.
