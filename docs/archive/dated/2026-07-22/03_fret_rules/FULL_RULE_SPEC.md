# task_fret (왼손 압현) 설계 — §2 규칙 명세 (rule set)

> **상태: HISTORICAL FRET-V1 RULE SNAPSHOT.** 아래 33-action/341D 및 425D 안내는 현재
> Fret-v2 계약이 아니다. 현재 정본은 [`master_plan/03_fret.md`](../../../master_plan/03_fret.md)다.

> 역사 문서 안내 갱신: 2026-09-01. 원문은 2026-07-22의 33-action/341-observation 계약을 보존한다.
> 현재 구현은 `30 action / 425 observation / 6 reward-value`이며, `L_Thorax`는 초기 PD 자세로 유지한다. 운영 기준은
> [`tab2body/TRAINING.md`](../../../tab2body/TRAINING.md)다.

> 백지 재설계의 **작업 정본**. 왼손이 fingermapping을 보고 정해진 타이밍에 정확한 (줄,프렛)을
> 지정 손가락으로 누르고 떼는 것을 학습하기 위한 **규칙 명세**. 각 규칙은 실제로 `rewards/fret.py`·
> `tasks/task_fret.py`·`goals.py`·`base.py` 중 어디서 강제되는지까지 지정한다(= 그 파일들의 사양서).
> 구 `task_fret_plan.md`(Xu 이식안)는 참고 자료. 파일 지도는 `tab2body/STRUCTURE.md`.
> 원문 작성일 2026-07-22. 상태: 통합 규칙 R1~R29 + 메커니즘 M1~M3.
> 아래 5,000회 학습 수치는 당시 비교 기준이며 현재 공식 성능 지표가 아니다.

## 용어와 좌표 정본

- **기타 로컬 좌표**는 실제 에셋과 `to_guitar_frame()`을 따른다. `+x_g`는 6번줄(low-E)에서
  1번줄(high-e), `+y_g`는 브리지/바디에서 너트, `+z_g`는 지판 바깥쪽이다. 따라서 너트→브리지는
  `-y_g`다. 팀 초안의 축 이름은 이 프로젝트 축으로 변환해 사용한다.
- **Target**은 지정 손가락으로 눌러야 하는 줄·프렛, **Protected**는 울려야 하므로 누르면 안 되는 줄,
  **DONT_CARE**는 음향·정확도 판정만 자유인 줄이다. DONT_CARE도 관통·관절 안전·과압 규칙은 지킨다.
- **Fret cell**은 두 프렛 와이어 사이 나무 구간, **Target fretting region**은 그중 정상 압현으로
  인정하는 범위, **fingertip pad**는 끝마디 중심선과 유효 반지름으로 근사한 접촉 영역이다.
- 손가락 역할은 `press/hold/release/transit/hover/anchor/barre`로 표현한다. 현재 환경은 이를
  PRESS/NO_PRESS/DONT_CARE 타임라인과 룩어헤드로 대부분 암묵적으로 표현하며, 명시 역할 채널은 후속 항목이다.

## 0. 관통하는 프레임 — 누가 무엇을 책임지나

- **fingermapping = "규칙 엔진"**: 어느 손가락으로·어디를 누를지와 교차·스팬을 풀어 `presses`로
  넘긴다. 다만 이 결과를 무조건 신뢰하지 않고 S0 builder/loader가 에셋·손가락 점유 계약을 재검사한다.
- **학습 환경 = "모터 제어기"**: 그 목표를 **물리적으로 달성**하고 **사실적으로** 움직이게 한다.
- ⟹ goal loader는 6줄·22프렛·finger·시간축·바레 계약을 fail-fast로 확인하고, runtime env는
  **① 달성(정확히 누름/뗌)** · **② 사실성(자연스러운 손·팔 자세)** · **③ 안전(관통·이탈 금지)**를 다룬다.

## 1. 분류 체계 · 담당 파일

### 제어 관절 계약(2026-07-20 재정의)

- 정책 제어는 왼쪽 어깨 띠부터 손끝까지만 허용한다:
  `L_Thorax(3) + L_Shoulder(3) + L_Elbow(3) + L_Wrist(3) + LH:thumb(5) + 검지·중지·약지·소지(각 4)` = **33 actions**.
- `Torso/Spine/Chest` 9DOF와 머리·오른팔·오른손·하체는 seated init PD target에 고정한다.
- `L_Thorax`는 몸통 굽힘이 아니라 작은 범위의 쇄골·어깨 띠 움직임이므로 제어에 남긴다.
- 엄지는 프렛 음을 담당하지 않지만 R6 넥 뒤 지지를 직접 조절할 수 있도록 정책 제어에 포함한다.
- Actor는 잠재 diagonal Normal을 `tanh`로 변환하고 Jacobian을 보정하는 bounded policy
  `tanh_squashed_diagonal_gaussian.v1`이다. action scale=1.0, EMA α=0.5, 제어관절 reset hard-range
  inset=2%, 초기 policy std=.02를 함께 사용한다.
- 구 37-action checkpoint는 action head shape가 달라 호환되지 않으며 새 환경에서 처음부터 재학습한다.

| 분류 | 뜻 | 주 담당 파일 |
|---|---|---|
| **보상** | 잘할수록 오르는 연속 점수(손을 목표로 유도) | `env/rewards/fret.py` |
| **종료** | 성공 완료와 실패 종료를 구분하며 실패 종료에만 즉시 `−25` | `env/tasks/task_fret.py` |
| **목표** | 무엇을 향해 보상하나(언제·무엇을·어느 손가락) | `env/goals.py` |
| **관측** | 정책이 보는 입력(현재+미래 목표) | `env/goals.py`(observe) |
| **인프라** | 자동 유지(학습 대상 아님) | `env/base.py` |

## 2. 규칙 마스터 표

**사용자 제시 규칙 (R1~R15)**

| # | 규칙 | 분류 | 담당 파일 | 강제 방식(스케치) |
|---|---|---|---|---|
| R1 | 각 활성 손가락의 지정 역할에 따라 목표 (줄,프렛)을 실제로 누르거나 유지한다 | 보상+판정 | `rewards/fret.py` | 줄별 `0.30·접근거리 + 0.50·실제압현 + 0.20·위치품질`. 다른 손가락 대체 불인정 |
| R2 | 접근 목표와 압현 위치 품질을 분리한다 | 보상(기하) | `rewards/fret.py` | 목표 와이어 표면→이전 와이어 표면의 나무 구간을 `x=0..1`로 정의. 거리 목표 `x=0.20`, 위치 최적 `x=0.10..0.30`, 뒤로 밀린 화음 손가락도 압현 성공은 유지 |
| R3 | 줄·프렛별 압현 요구 상태: PRESS / NO_PRESS(Protected) / DONT_CARE | 보상+판정 | `rewards/fret.py` | 목표 f의 낮은 프렛=DC, f=PRESS, 높은 프렛=NP. goal=−1은 전 프렛 NP, 0은 전 프렛 DC. NP 오압현 시 해당 줄 task 점수 0 |
| R4 | DONT_CARE는 음향 판정만 자유이며 전역 안전 규칙은 그대로 적용한다 | 판정 | `rewards/fret.py` + `tasks/task_fret.py` | 이격 선호·정확도·all-correct에서는 제외하지만 관통·과압·관절·비정상 지지 규칙은 면제하지 않음 |
| R5 | 역할·릴리즈 타이밍에 따라 P/NP/DC를 전환한다 | 목표 | `tools/build_fret_training_data.py` | 같은 위치 재타현/anchor는 PRESS 병합, 다른 press로 이동하는 빈 구간은 NO_PRESS, 다음 press가 없으면 DONT_CARE. 급격한 release 모션 억제는 R10 |
| R6 | 엄지는 넥 뒷면의 허용 영역에서 유연하게 지지한다 | 보상+종료 | `rewards/thumb.py` + `rewards/fret.py` | 넥 뒤 접근 30% + 실제 접촉 70%. 접촉 점수는 목표 손끝이 80→25mm로 가까워질 때만 열리고, 과도한 순접촉력은 감점한다. raw 힘 5,000 초과가 3프레임 지속되면 종료하며 옆면/앞면 지지는 불인정 |
| R7 | 손목이 기타로컬 최소 안전 영역을 명백히 벗어나지 않는다 | 종료 | `tasks/task_fret.py` | 고정 박스 `(-.20,-.35,-.30)..(.30,.35,.25)m` 밖 3프레임 연속 시 종료 |
| R8 | 네 압현 손가락이 기타 뒤로 지나치게 넘어가지 않는다 | 종료 | `tasks/task_fret.py` | 구간당 5점 중 한 손가락의 25% 이상이 기타 로컬 `z<-50mm`에 3프레임 지속되면 종료. x/y와 무관하며 엄지는 제외 |
| R9 | 일반 압현은 아치형 손가락을 선호하되 각도로 일괄 실격시키지 않는다 | **보류** | — | MCP/PIP/DIP 굽힘은 선호하지만 단음·바레 차이 때문에 단일 임계값은 사용하지 않음. 옆줄 간섭이 관찰될 때 재검토 |
| R10 | 정상 이동·release는 허용하고 과속·떨림·튀어 오름만 억제한다 | **보류** | `rewards/fret.py` | 기본 가중치 0. 압현 안정 후 상태별 속도 자유구간+가속도/jerk 감점으로 교체 |
| R11 | 하체 잠금 | 인프라 | `base.py` | 리밋 핀칭+armature+매스텝 재주입(3중 잠금, 자동) |
| R12 | 손가락→손목→팔꿈치→어깨 순으로 움직임을 우선하고, 목표 없는 REST 구간에는 불필요한 움직임을 줄인다 | 보상 | `rewards/motion.py` + `rewards/fret.py` | 손목 목표에서 멀면 비용 0, 접근할수록 활성. 가동범위 정규화 속도 가중 `0.05/0.20/0.50/1.00`, 전체 보상 2%. R17의 idle 원칙을 흡수하되 별도 에너지 보상은 추가하지 않음 |
| R13 | 손바닥 안쪽이 바닥을 향하지 않는다 | 종료 | `tasks/task_fret.py` | 손바닥 안쪽 법선의 world-z<−0.3이 3프레임 지속되면 종료. 기타 자세와 무관한 세계 중력축 기준이며 소프트 보상 없음 |
| R14 | humanoid가 기타를 관통하지 않음 | 구현+종료 | `safety.py` + `tasks/task_fret.py` + `base.py` | 필터 1&2 물리 저항 + 넥/바디 해석 깊이와 swept 감시. 5mm×3프레임이면 종료 |
| R15 | 각 손가락은 현재·다음 목표와 역할 변화 타이밍을 안다 | 관측 | `goals.py`(observe) | 3시점 75D + 손가락별 13D×4 + 곡 진행률1 = goal128D. 준비 delay를 시간 채널에 반영하며 S0 다중 줄은 거부 |

**추가 규칙 (R16~R20, 실연주 도움)**

| # | 규칙 | 분류 | 담당 파일 | 강제 방식(스케치) |
|---|---|---|---|---|
| R16 | **Protected·인접 줄 접촉 회피** | **보류** | `rewards/fret.py` | 단일 압현 단계에서는 R3 오압현 무효화만 사용. 목표 압현이 안정된 뒤 dyad·코드 단계에서 울려야 할 줄의 유의미한 접촉/뮤트만 감점 |
| R17 | **idle / 에너지 최소화** | **R12에 통합** | `rewards/motion.py` | REST 구간의 불필요한 움직임 억제 원칙을 R12에 흡수. 별도 전역 action-energy 보상은 필요한 이동을 방해할 수 있어 구현하지 않음 |
| R18 | **게으른 손떼기(hover)** | 약한 보상 | `rewards/fret.py` | 실제 PRESS에 성공한 뒤 현재 해제된 손가락만 적용. 가장 가까운 실제 string segment와 손끝 표면 간격 30mm까지 자유, 초과분은 40mm scale로 완만히 감쇠. 전체 0.5%, 종료 없음 |
| R19 | **손목 중립각 선호** | **R21에 통합** | `base.py` + 향후 soft-range 보상 | 손목만 별도 규제하지 않고 R21의 관절 soft range 대상에 포함. 넓은 자유구간을 두며 실제 압현 자세 분포를 확인하기 전에는 추가 보상을 켜지 않음 |
| R20 | **스티키 핑거(재타현 유지)** | 목표 | `goals.py` | 재타현 병합 구간은 같은 손가락이 압점 유지(fingermapping `presses`가 이미 표현) → env는 유지 목표를 R1로 보상 |

**팀 규칙 통합 및 후속 논의로 추가한 항목 (R21~R29)**

| # | 규칙 | 분류 | 담당 파일 | 강제 방식(스케치) |
|---|---|---|---|---|
| R21 | 모든 제어 관절은 hard limit 안에 있고 자연스러운 soft range를 선호한다 | **hard 완료 / soft 보류** | `base.py` + 향후 진단 | hard limit은 action/PD clamp로 항상 강제. R19를 흡수한 손목·손가락 soft range는 정상 압현 학습의 관절 분포를 확보한 뒤 결정하며 현재 임계값·보상 없음 |
| R22 | 손가락끼리 관통하거나 서로의 목표 압현을 방해하지 않는다 | **진단 구현 / 강제 보류** | `safety.py` + `tools/audit_r22_runtime.py` | 다섯 손가락의 3개 마디를 6mm capsule로 근사해 10개 손가락 쌍의 최소 표면 간격·관통 깊이·지속시간 기록. 2mm 초과 겹침만 표시하며 보상·종료·self-collision 없음 |
| R23 | PRESS/HOLD 동안 손끝의 접선 방향 미끄러짐을 억제한다 | **약한 감점 구현** | `rewards/fret.py` | 지정 손가락의 모든 목표 줄이 3프레임 연속 실제 PRESS에 성공하면 기타 로컬 x/y anchor 설정. 누적 2mm까지 자유, 초과분은 3mm scale로 감쇠하며 전체 0.5%. 목표 변경·접촉 실패·release 즉시 초기화 |
| R24 | 목표 손끝·엄지 외 부위의 비정상 지지와 불필요한 과압을 허용하지 않는다 | **진단 구현 / 보상·종료 보류** | `safety.py` + `tools/audit_r24_runtime.py` | distal/middle/proximal 5손가락, 손바닥·손목·팔꿈치 순접촉력과 33 제어관절 실제 토크·limit 비율 기록. 정상 압현 분포 전 임계값 없음 |
| R25 | 여러 손가락 목표는 타현 전 준비되고 ChordReady가 짧은 연속 구간 유지돼야 한다 | **보류** | 향후 `goals.py` + 평가 | 현재 S0는 단일 압현 중심이고 60Hz goal에 strike timing 채널이 없어 타현 전 준비를 정확히 평가할 수 없음. dyad·코드 단계에서 strike 래스터화 후 3프레임(50ms) 연속 유지 진단부터 추가 |
| R26 | 한 정책은 한 곡의 고정 goal을 반복 연습하며 부분구간 숙달에서 전체곡 연주로 통합한다 | **커리큘럼 구현** | `learning/curriculum.py` + `goals.py` | 모든 규칙과 원곡 goal은 유지. 1~1000 coverage(random start 100%) → 1001~2000 integration(100→0%) → 이후 full-song(frame 0). 다곡 혼합·zero-shot 목적 아님 |
| R27 | 목표 PRESS 구간을 순간 접촉이 아니라 안정적으로 지속한다 | **진단+최종 평가 구현** | `goals.py` + `metrics.py` + `train.py` | 줄별 동일 fret/finger 연속 구간을 이벤트로 묶음. 충분히 긴 이벤트는 시작·끝 3프레임(각 50ms)을 제외하고, 유지율≥90%이며 연속 이탈≤3프레임인 이벤트만 성공. 모든 이벤트 성공을 최종 gate에 추가하되 별도 reward는 없음 |
| R28 | 일반 MOVE에서는 압현 상태로 지판을 끌지 않고 기존 압현을 해제한 뒤 이동한다 | **진단 구현 / 강제 보류** | `metrics.py` + `rewards/fret.py` + `tools/audit_r28_runtime.py` | 이전 목표의 relation=MOVE에서 목표가 바뀐 뒤 다음 목표 PRESS 성공 전까지 추적. 같은 string/fret 압현 셀이 연속 제어 프레임에 유지된 접선 이동만 confirmed drag로 누적하고 3mm 초과 move를 표시. endpoint 접촉만 있는 경우 candidate로 분리. reward·종료 없음 |
| R29 | 곡 goal 시작 전에 첫 운지에 접근할 충분한 준비시간을 제공한다 | **환경 clock 구현** | `tasks/task_fret.py` + `train.py` + rollout 도구 | reset 뒤 60프레임 동안 goal frame은 고정하되 룩어헤드 dt·13D time-to에 남은 delay를 반영. 보상·안전은 유지하고 F1/R27은 끈 뒤 정상 진행 |

**메커니즘 (M1~M3, 규칙 실현 장치)**

| # | 장치 | 분류 | 담당 파일 | 내용 |
|---|---|---|---|---|
| M1 | all-correct 보너스 | 보상 | `rewards/fret.py` | 볼록결합 `rew_final = 0.8·rew_base + 0.2·all_correct`(가산 아님). 모든 PRESS/NO_PRESS 요구가 정답일 때만 1, DONT_CARE와 요구 없는 프레임은 제외 |
| M2 | 실패 종료 벌점 broadcast | 인프라 | `tasks/task_fret.py` | 조기 timeout, finite 실패, 속도 폭주, R7·R8·R13 등 실패 종료의 여섯 보상 열만 `−25`. 정상 마지막 goal 완료에는 적용하지 않음 |
| M3 | press 검출(판정 전제) | 보상 | `rewards/fret.py` | 지정 손가락 pad의 기타 안쪽 signed depth≥1.0mm + 올바른 프렛 칸 + 목표 줄. 해제≤0.5mm hysteresis, 최고 프렛 승 |

**운지 데이터와 env가 이중 확인**: fingermapping은 손가락 교차·스팬을 해결하고, goal loader는 각 frame의
길이 6, 정수 fret `−1/0/1..22`, PRESS finger `1..4`, frame/timestamp 단조성을 다시 검사한다. S0
`allow_barre=false`에서는 같은 손가락의 다중 줄과 모든 명시적 바레 표식을 fail-fast로 거부한다.

## 3. 규칙별 상세 (그룹)

### 3-1. 압현 코어 (R1·R2·R3·R4·R9·M3)
왼손 goal은 매 스텝 **줄별 상태** `(press: goal>0 → 눌러라 fret f·finger k / no-press: goal=−1 → 누르지마 / don't-care: goal=0)`. 각 줄이 자기 상태에
따라 채점되어 **per-string 6채널 보상**(멀티크리틱)을 이룬다.
- **R1/R2 확정안(2026-07-20)**: 지정 손가락 압현의 줄별 점수는
  `r_fret = 0.30·r_distance + 0.50·r_press + 0.20·r_press·quality(x)`로 구성한다.
  접근, 실제 압현, 위치 품질을 분리하므로 공중 hovering은 최대 30%이고, 올바르게 눌렀지만 화음
  배치 때문에 뒤로 밀린 손가락은 약 80% 이상을 유지한다. 다른 손가락 대체는 `r_press=0`이다.
- **접근 거리 30%**: 프렛 `f`의 나무 구간은 `G:fret(f)`의 너트쪽 표면부터
  `G:fret(f-1)`(1프렛은 nut)의 브리지쪽 표면까지이며 이를 `x=0..1`로 정규화한다. 목표 줄의
  `x=0.20` 지점을 접근 목표 `p20`으로 둔다. 지정 손가락 pad와 `p20`의 지판 평면상 오차 및
  바깥쪽 간격만 거리로 쓰고, pad가 기타 안쪽으로 들어간 깊이는 `max(...,0)`으로 clamp하여 실제로
  누른 뒤 거리 보상이 다시 감소하지 않게 한다. 초기 커널은
  `0.7·exp(-(d/0.012)^2)+0.3·exp(-(d/0.060)^2)`.
- **실제 압현 50%**: 기타 바깥 법선은 guitar local `+z`, 안쪽은 `-z`를 live quaternion으로
  월드 변환한다. 일반 압현은 지정 손가락 끝마디(`finger3→finger_top`), 바레는 검지 여러 마디의
  pad 표면을 사용한다. pad는 중심축에서 유효 반지름(초기 6.3mm)만큼 안쪽으로 보정한다.
  지정 손가락·목표 줄·올바른 프렛 칸·최고 압현 프렛 일치 조건에서 signed depth≥1.0mm면 press on,
  ≤0.5mm면 off(hysteresis). 더 깊게 눌러도 추가 점수는 없고 과도한 깊이는 R14가 처리한다.
- **위치 품질 20%**: `r_press=1`일 때만 활성화한다. `x=0..0.10`은 0→1로 증가,
  `x=0.10..0.30`은 1, `x=0.30..0.85`는 1→0으로 완만히 감소, `x≥0.85`는 0이다.
  거리 목표는 20%로 명확하지만 성공 위치는 넓게 허용하여 같은 프렛의 여러 손가락이 앞뒤로
  어긋나는 실제 코드 폼을 수용한다.
- **구현 상태(2026-07-20)**: `rewards/fret.py`에 위 30/50/20 구성, live fret 표면 기반 x좌표,
  one-sided 접근 거리, 원통형 pad signed-depth, 1.0/0.5mm hysteresis, 최고 프렛 승을 반영했다.
  CPU 기하 단위검사와 8-env GPU PPO smoke를 통과했다. 구 거리 판정으로 학습한
  `fret_002000.pt`를 새 기준으로 재평가하면 press 성공률과 F1이 0이므로 재학습해야 한다.
- **보상 보강(2026-07-21)**: 500회 파일럿에서 손끝이 평균 11.4cm 밖에 머문 문제를 반영해
  12/60/150mm 다중 스케일 접근으로 바꿨다. 50% 실제압현 항은 최종 성공 기준 1mm를 그대로
  유지하면서 `−5mm→+1mm` 깊이 진행도 40%와 binary 성공 60%로 구성해 성공 직전에도 학습 신호를 준다.
- **줄·프렛별 요구 상태(R3, 2026-07-20 구현)**: 매 60Hz 제어·보상 시점에 줄별 scalar goal로
  1~22프렛 마스크를 파생한다. 목표 f는 `1..f-1=DC / f=PRESS / f+1..22=NP`, goal=−1은
  전 프렛 NP, goal=0은 전 프렛 DC다. 실제 `(N,6,4손가락,22프렛)` press와 비교하며 낮은 프렛은
  음에 영향이 없어 무시하고 높은 프렛 또는 전 프렛 NP 위반은 해당 줄 task 점수를 0으로 만든다.
  음수 페널티와 press 직전 회피 shaping은 `cfg.py`의 가중치가 0인 비활성 hook으로 준비했다.
- **DONT_CARE(R4 통합)**: 이격 선호를 제거하고 행동 독립 상수로 처리한다. PRESS/NO_PRESS 정확도와
  all-correct의 검사 대상에서는 제외하며, 검사할 줄이 하나도 없는 프레임에는 all-correct 보너스를 주지 않는다.
  단, R8/R13/R14/R21~R24의 물리·안전 규칙까지 자유라는 뜻은 아니다.
- **접촉·힘의 현재 의미**: 현은 변형되는 물리 줄이 아니라 위치 기준이며, 프렛 와이어 접촉력도 직접
  측정하지 않는다. 따라서 현 단계의 최소 압현 힘은 pad signed-depth+hysteresis로 대체한다. 실제 현 변형과
  힘 상·하한은 R24에서 접촉 분포를 확보한 뒤 도입한다.
- **아치형 손가락(R9, 보류)**: MCP/PIP/DIP가 굽은 자세는 선호하지만 단음과 바레를 같은 각도 임계로
  실격시키지 않는다. 실제 인접 줄 간섭이 반복될 때 자세/접촉 기반 규제로 재검토한다.
- **판정(M3)**: 보상 전에 각 줄에서 "눌렸는지"를 기하로 판정.

### 3-2. 타이밍·릴리즈 (R5·R18·R20)
- **누름 타이밍**: `presses`의 `t_press`(타현 0.12s 선행)부터 그 줄 목표가 press로 켜짐.
- **뗌 타이밍(R5, 2026-07-20 구현)**: `press_events`가 같은 위치 재타현을 병합한 경우 PRESS를
  연속 유지한다. 남아 있는 이벤트 경계는 의도적 release로 간주하고, 같은 줄에 다음 press가 있으면
  `t_release..next.t_press`를 줄 전체 NO_PRESS로 채운다. 다음 press가 시작되면 R3 마스크가 새 목표보다
  높은 옛 프렛을 NP, 낮은 옛 프렛을 DC로 자동 분류한다. 다음 이벤트가 없으면 release 뒤 DONT_CARE다.
- **게으른 손떼기(R18)**: 실제 PRESS에 성공했던 손가락이 해제되면 실제 줄에서 pad 표면 기준 30mm까지
  자유롭게 호버하고, 초과 이탈만 0.5%의 작은 보상으로 억제한다.
- **스티키 핑거(R20)**: 재타현이 병합된 구간은 손가락을 떼지 않고 유지(목표가 계속 press).
- **역할 상태**: 일반 이동은 `hover→approach→press→hold→release→transit`으로 해석하되 모든 상태를
  반드시 순서대로 강제하지 않는다. anchor는 hold를 유지하고, barre는 여러 줄 PRESS를 동시에 담당한다.

### 3-3. 손·손목 자세 사실성 (R6·R13·R19)
- **엄지(R6, 2026-07-20 구현)**: 기타 mesh의 local 넥 뒷면 `z=-8mm`, y 길이
  `-0.241803..0.217197m`, 반폭 `27.908..20.419mm` 테이퍼를 해석 기하로 사용한다.
  `LH:thumb3→thumb_top`을 반지름 7mm capsule로 샘플링해 듀얼스케일(15/120mm) 접근 보상 30%,
  `LH:thumb3` net contact force가 0.5N에서 ON·0.1N에서 OFF이고 샘플이 실제 넥 뒤 영역일 때
  접촉 후보가 된다. 목표 손끝 거리 80→25mm gate를 통과해야 접촉 점수가 열리며, raw 순접촉력
  100을 넘는 부분은 500 scale로 감쇠하고 별도 최대 10% 감점을 준다. 이 힘은 접촉 상대를 구분하지
  못하므로 물리적 기타 힘으로 해석하지 않는다. 옆면·지판 앞·기타 바디 접촉은 성공 불인정한다.
  전체 보상에서 R6 비중은 5%다.
  raw 순접촉력 5,000 초과가 3프레임 지속되면 편법 고정으로 보고 종료한다.
- **손바닥 방향(R13)**: `wrist→middle1`과 `pinky1→index1`의 고정 순서 교차곱으로 손바닥 안쪽
  법선을 만들고 세계 중력축과 비교한다. 기타가 어떻게 놓였는지와 무관하게 법선의 world-z가
  `-0.3`보다 작은 상태가 3프레임 지속되는 명백한 바닥 방향 반전만 종료한다. 정상 범위에는
  보상·페널티가 없다. 초기 자세 world-z=+0.871. [4방향 시각화](renders/palm_world_direction_multiview.png)
- **손목 중립(R19)**: 손목 관절 극단각 회피. R13과 함께 손목이 비현실적으로 꺾이는 것을 규제.

### 3-4. 팔 모션 규제 (R10·R12·R17)
- **부드러움(R10, 보류)**: 정확한 압현을 먼저 학습하기 위해 현재 가중치는 0이다. 추후 자연스러운
  모션 단계에서 정상 속도는 자유롭게 두고 과속과 가속도 기반 떨림만 감점하는 방식으로 추가한다.
- **근위 안정(R12, 2026-07-21 구현)**: 실제 관절 속도를 각 DOF 가동범위로 정규화하고
  손가락/손목/팔꿈치/어깨에 `0.05/0.20/0.50/1.00` 비용을 적용한다. 손목이 목표 반경보다
  10cm 이상 멀면 비용은 0이고, 10cm 전환 구간에서 smoothstep으로 켜져 목표 안에서 완전히
  활성화된다. 따라서 도달 중에는 팔 전체를 허용하고 도착 후에는 손가락을 우선한다. 전체 비중 2%.
- **idle(R17→R12 통합)**: 별도 전역 action-energy 비용 없이 R12의 기존 작은 움직임 비용으로 처리한다.
- **유지 미끄러짐(R23)**: 실제 PRESS 3프레임 뒤 pad의 기타 로컬 접선(x/y) anchor를 잡고 누적 2mm
  자유구간을 넘는 slip만 3mm scale·전체 0.5%로 감점한다.
- *(이 규칙들은 모션 정규화 가족이며 압현 핵심 규칙과 분리한다.)*

### 3-5. 안전·종료 (R7·R8·R14 + M2)
- **손목 박스(R7, 구현)**: 자세 유도 보상이 아니라 명백한 이탈만 막는 최소 안전 규칙이다. 기타 로컬 고정 박스 `min=(-0.20,-0.35,-0.30)m`, `max=(0.30,0.35,0.25)m` 밖에 손목 중심이 3프레임 연속 있으면 종료한다. 경계 자체와 박스 내부에는 감점이 없다. [시각화](renders/wrist_safety_envelope_preview.png)
- **손가락 지판 뒤(R8, 구현)**: 검지·중지·약지·소지만 검사하고 엄지는 R6으로 분리한다. 각 손가락의 세 마디 중심선을 구간당 5점 샘플링한다. 한 손가락 샘플 중 25% 이상이 기타 로컬 `z<-50mm` 평면 뒤에 3프레임 연속 있으면 종료한다. 실제 넥 뒷면 `z=-8mm`보다 42mm 여유가 있고, 단일 끝점의 미세 돌출은 오탐으로 제외한다. x/y 범위와 무관하게 손이 기타 뒤로 지나치게 간 상태를 막는다. [평면 예시](renders/finger_back_limit_plane_multiview.png)
- **관통 금지(R14)**: **접촉(정상 압현)과 관통을 구분**해야 함 — 압현은 손끝이 줄/지판에 닿는 것(침투≈0)이고,
  손·팔이 넥/바디를 뚫고 지나가는 것만 실패. 충돌 필터 감사가 1차 저항을 보장하고, 기타 로컬 테이퍼
  넥·바디·상판의 해석적 내부 깊이를 왼팔/손가락 중심선 다점에서 계산한다. 이전→현재 위치는 9점
  시간 보간해 양 끝이 밖이어도 중간에 통과한 터널링을 기록한다. 현재 5mm×3프레임 후보와 reset 직후
  겹침을 info에 기록하지만 정상 압현 분포 확인 전까지 종료는 꺼 둔다. 접촉 힘은 종료 기준으로 쓰지 않는다.
- 조기 timeout·비유한 값·속도 폭주·R7/R8/R13 같은 **실패 종료만** M2로 −25 broadcast한다.
  마지막 goal을 실패 없이 마친 정상 종료는 벌점을 받지 않는다. R14 종료는 현재 꺼져 있다.

### 3-6. 관측 (R15)
- 기존 현재/0.1s/0.25s 줄별 75D 룩어헤드 뒤에 네 손가락의 13D 이벤트 벡터를 붙인다.
  `13D=[next_string_mask(6), next_fret/22, clamp(dt_next_goal,0,1s), next_valid,
  clamp(dt_current_change,0,1s), KEEP, MOVE, REST]`에 정규화 곡 진행률 1D를 더해 총 goal128D,
  여기에 actuator state인 직전 EMA action33을 붙여 당시 전체 obs341D였다. 진행률은 반복되는 동일 운지
  문맥을, prev_action은 같은 물리 자세에서 서로 다른 PD/EMA 상태를 정책이 구분하기 위한 값이다.
- raw event 대신 매 60Hz 프레임의 최종 `fret_goal/finger_goal`에서 상태 구간을 만든다. 현재 S0는
  같은 손가락이 한 프레임에 여러 줄을 맡으면 같은 프렛이어도 로딩을 중단한다. 6줄 mask는 이후
  `allow_barre=true`에서 동일 fret·연속 줄·명시적 검지 바레만 표현하도록 남겨 둔다.
- 바로 이어진 상태가 같은 프렛에서 하나 이상의 줄 접촉을 공유하면 KEEP, release 공백이나 다른 목표는 MOVE,
  이후 목표가 없으면 REST다. 재생성한 S0 861프레임은 암묵 다중 줄 finger-frame이 105→0이며,
  fret 범위·정수성·mask·valid·시간·관계 one-hot 계약을 통과한다. 합성 전환 검사와 곡 진행률을 포함한
  당시 배관은 action33, base180D, goal128D, prev_action33D, 전체 obs341D, value6이었다. 현재 thumb
  geometry 12D를 추가해 전체 obs는 353D다.

### 3-7. 인프라 (R11)
- 하체 잠금·우팔 좌식 유지는 base.py가 자동 처리(학습 대상 아님).
- reset noise 뒤 모든 DOF를 hard limit으로 clamp하고, 제어관절은 각 hard range 안쪽 2%에 둔 뒤
  action EMA를 reset PD target의 역변환 값으로 초기화한다. 자동 reset step은 다음 episode obs를
  반환하고, 직전 terminal obs와 reason은 info에 보존한다.
- action/PD/torque, DOF 위치·속도, root/body/contact, reward·observation의 NaN/Inf를 이름 있는 finite
  실패 원인으로 기록하고 유한화한 뒤 실패 종료하므로 PPO 통계로 전파되지 않는다. reward 계산 뒤
  goal128D와 EMA33을 붙여 만든 파생 관측도 같은 step에서 다시 검사해 즉시 `nonfinite_observation`으로
  종료한다.

### 3-8. 추가 안전·코드 준비·커리큘럼·지속 평가 (R21~R29)
- **관절 범위(R21)**: 물리 hard limit은 항상 강제한다. soft range는 현재 보류하며, 정상 압현에 성공한
  rollout에서 손목·손가락·팔꿈치·어깨별 관절 위치 분포를 확보한 뒤에만 자유구간과 가중치를 결정한다.
  분포가 없을 때 임의의 중립각이나 대칭 범위를 가정하지 않는다.
- **손가락 상호 간섭(R22)**: 현재 좌식 안정성을 위해 humanoid self-collision은 꺼 둔다. 엄지를 포함한
  다섯 손가락의 각 3개 중심선 마디를 6mm capsule로 근사하고, 서로 다른 손가락 10쌍의 3×3 정확한
  segment distance에서 표면 간격과 관통량을 구한다. 2mm를 넘는 proxy 겹침의 쌍별 tensor, 최대 깊이,
  쌍 수, 연속 프레임, 초기 겹침을 `info`로 기록한다. 보상·종료 효과는 없으며 정상 학습 rollout에서
  반복 관통이 확인될 때만 소프트 벌점이나 제한적 self-collision을 검토한다. 보정 전에는 최종 평가
  gate에도 포함하지 않는다. 초기자세 8-env×120스텝은 10쌍 모두 관통·초기겹침 0이었다.
- **비정상 지지·과압(R24)**: 엄지를 포함한 다섯 손가락의 distal/middle/proximal, 손바닥·손목·팔꿈치
  rigid body 순접촉력을 매 프레임 기록한다. 네 압현 손가락은 현재 목표 활성 여부에 따라 target/inactive
  distal 힘도 분리한다. 정책 제어 33관절에는 실제 적용 토크와 안전 cap 대비 비율을 함께 기록한다.
  Isaac의 net contact force는 접촉 상대를 식별하지 못하므로 기타 접촉으로 단정하지 않으며,
  `audit_r24_runtime.py`가 선택적 checkpoint rollout의 평균·p50/p95/p99/max를 JSON으로 집계한다.
  엄지 과압만 500회 파일럿의 편법이 확인돼 R6에서 소프트 감점한다. 나머지 부위는 보상·종료
  임계값 없이 정상 압현 분포와 영상에서 편법이 확인된 뒤에만 개입한다.
- **압현 중 slip(R23)**: 같은 손가락의 줄 mask와 프렛이 유지되고 지정된 모든 줄의 실제 PRESS가 3프레임
  연속 성공하면 현재 fingertip의 기타 로컬 x/y를 anchor로 저장한다. 누적 접선 이동 2mm까지 자유이며,
  초과분만 3mm scale Gaussian과 전체 0.5%로 반영한다. 순간 이동과 누적 이동, gate, streak를 info에
  기록한다. 목표 변경·접촉 실패·release에서는 anchor를 즉시 폐기하므로 MOVE를 방해하지 않는다.
- **ChordReady(R25, 보류)**: 여러 PRESS가 필요한 목표에서는 `all_correct`가 한 프레임만 켜지는 것으로는
  부족하지만, 현재 S0는 단일 압현 중심이고 60Hz 환경 goal에 `strike_now/time_to_next_strike`가 없다.
  지금 streak만 추가하면 실제 타현 전 준비와 무관한 구간도 성공으로 셀 수 있으므로 구현하지 않는다.
  dyad·코드 커리큘럼 전에 finger mapping의 `strikes`를 goal로 래스터화한 뒤, 타현 직전 3프레임(50ms)
  ChordReady 유지율을 우선 평가 지표로 추가하고 보상은 결과를 본 뒤 결정한다.
- **곡별 반복 커리큘럼(R26)**: 정책과 체크포인트는 한 곡의 goal SHA-256에 귀속된다. 다른 곡이나
  합성 목표를 섞지 않고 모든 물리 규칙·보상·안전 진단도 처음부터 유지한다. 초기 coverage 1,000회는
  같은 곡 내부에서 시작 프레임을 무작위로 골라 모든 운지를 고르게 반복한다. 다음 integration 1,000회는
  무작위 시작 확률을 1→0으로 선형 감소시켜 부분 동작을 곡 흐름으로 연결한다. 이후 full-song 단계는
  모든 episode를 frame 0에서 시작한다. 횟수는 설정/CLI로 변경 가능하고 checkpoint에 곡 hash·단계·확률을
  저장한다. 또한 ordered DOF, observation/action/value shape, action/reset, reward·safety·PPO와 actor
  objective, goal/hand, 자산·핵심 구현 지문을 strict contract로 봉인한다. 재개·평가는 전체 계약이
  일치해야 하며 계약 없는 legacy checkpoint도 거부한다. 최종 평가는 항상 원곡 처음부터 deterministic
  전체곡이다.
- **압현 지속 안정성(R27)**: 줄별로 동일 fret·지정 손가락이 이어지는 최대 PRESS run을 하나의 이벤트로
  만든다. 9프레임 이상인 이벤트는 attack/release 각 3프레임을 평가에서 제외하고, 더 짧은 이벤트는
  삭제하지 않고 전체를 평가한다. 이벤트마다 유효 압현 프레임 비율, 최장 연속 성공, 최장 연속 이탈,
  접촉 중단 횟수를 누적한다. 유지율 90% 이상이고 최장 이탈이 3프레임 이하인 이벤트만 성공이며,
  전체곡의 모든 이벤트가 성공해야 `sustain_passed`다. R1이 이미 매 프레임 보상하므로 R27 보상은
  추가하지 않고 최종 평가 gate로만 사용한다.
- **최종 learned-song gate**: 적용 가능한 PRESS F1≥0.90·NO_PRESS 정확도≥0.99·오압현율≤0.01,
  모든 episode 전체곡 완료·실패 종료 0, R27 예상 이벤트 전수 coverage·유지율≥0.90·성공률100%·최장
  이탈≤3프레임을 각각 요구한다. 여기에 해석 관통≤5mm·swept/초기겹침 0·R7/R8/R13 종료 0을
  proxy safety gate로 결합한다. R22 capsule 겹침은 별도 진단으로만 기록한다.
  `hard_safety_passed`는 exact mesh 안전이 아닌 하위 호환 alias이며 R14 termination은 여전히 비활성이다.
- **MOVE 중 pressed drag(R28, 진단 전용)**: 이전 손가락 목표가 MOVE 관계이고 mask/fret이 바뀐
  프레임부터 다음 목표가 실제 PRESS에 성공할 때까지 추적한다. 손끝 기타 로컬 x/y 이동을 사용하되,
  같은 실제 string/fret 압현 셀이 이전·현재 제어 프레임 양쪽에서 유지된 경우만 confirmed drag로
  누적한다. 양 끝에서 어떤 압현이 있었다는 사실만으로는 한 스텝 사이의 정상 lift/repress를 배제할 수
  없어 candidate 채널로 별도 기록한다. confirmed 누적 3mm 초과를 표시하지만 보상·종료·최종 gate에는
  연결하지 않는다. slide·bend·vibrato가 도입되면 주법 goal에 따라 진단 gate를 끄는 확장이 필요하다.
- **첫 goal 준비시간(R29)**: 모든 reset 뒤 60제어 프레임(1초) 동안 선택된 시작 frame을 고정한다.
  정책 관측에는 해당 fret/finger, 손목·hand anchor, next-goal이 그대로 보이고 R1/R2 접근·압현 보상도
  정상 계산되므로 첫 음에 충분히 접근할 수 있다. 이 구간은 F1·NO_PRESS·R27 지속 통계에서는 제외하지만
  룩어헤드 dt와 손가락별 time-to에는 남은 준비 delay를 더해 countdown을 관측하게 한다. 관통·손바닥·
  손목을 포함한 안전규칙과 물리 진단은 유지한다. 1초 뒤 goal clock과 곡 평가를 시작한다.
  random-start coverage도 선택된 frame에서 같은 준비시간을 받는다. rollout 영상은 준비 동작을 포함하고
  오디오는 정확히 1초 offset으로 시작한다.
- **해제 후 hover(R18)**: 에피소드 중 실제 PRESS에 한 번이라도 성공한 손가락이 현재 비활성일 때만 켠다.
  여섯 실제 string segment 중 가장 가까운 곳과 fingertip pad 표면의 거리를 사용하며 30mm 이내는 완전히
  자유다. 초과 거리는 40mm scale의 Gaussian으로 부드럽게 낮추고 0.5%만 반영한다. 현재 압현 중인
  손가락과 아직 목표를 받지 않은 손가락에는 적용하지 않으며, 프렛 방향 이동이나 종료 조건에는 관여하지 않는다.

## 4. 규칙 간 관계 · 잠재 충돌

- **R1/R2(30/50/20) ↔ R9(아치형 선호) ↔ M3(signed depth)**: 거리만으로 공중 접근을 성공 처리하지
  않고 실제 signed-depth press에서만 50% press와 20% 위치 점수를 연다. R9는 각도로 일괄 실격시키지 않는다.
- **R6/R13/R21(R19 통합 손 자세) ↔ R1(압현 달성)**: 자세 규제가 너무 강하면 압현 도달을 방해할 수 있음 →
  정상 범위 선호는 **소프트(작은 가중)**로 두고, R13처럼 명백한 안전 위반만 종료한다.
- **R12(모션 우선순위·R17 통합) ↔ 빠른 곡 압현**: 이동 벌점이 과하면 빠른 프렛 이동을 못 함 →
  별도 전역 에너지 비용은 두지 않고 기존 작은 가중만 유지한다.
- **R14(관통 금지) ↔ 정상 접촉**: 접촉과 관통 구분 실패 시 정상 압현이 벌점/종료될 위험(가장 주의).

## 5. 구현 시 확정 필요 (기하·임계값 미해결)

- **손바닥 법선축(R13)**: body 로컬축 대신 wrist·index1·middle1·pinky1 점으로 고정 부호 법선을
  구성했고 초기 자세 world-z=+0.871임을 4방향 시각화로 확인했다. `-0.3`, 3 제어 프레임 종료와
  무효 법선 제외, streak reset, info 진단을 구현했으며 장시간 학습 자세 분포로 임계값만 재보정한다.
- **R6 임계값 보정**: 초기 contact on/off=0.5/0.1N은 실제 접촉 rollout 분포로 재조정. 과이탈 종료는 보류.
- **관통 metric(R14)**: 접촉힘이 아닌 해석적 내부 깊이로 확정. 현재 5mm×3프레임 후보이며 학습된 정상
  압현 rollout에서 current/swept 깊이 분포를 확인한 뒤 종료를 활성화한다. 충돌 프록시 확대는 오탐 시에만 검토.
- **세로 손가락 각도 임계(R9)**: 정상 단음·코드·바레 자세 분포를 확보한 뒤 재확인.
- **각 소프트 규칙 가중치**: R6·R10·R12·R18·R21의 상대 가중(압현 R1을 방해 않는 선에서).
- **R1/R2 코드 반영**: 30/50/20 분해, `x=20%` 접근점, signed depth+hysteresis, 위치 quality를 구현.
- **초기 수치 보정**: pad 유효 반지름 6.3mm, press on/off 1.0/0.5mm, 거리 scale 12/60mm를
  정답·hover·오프셋 대조 자세로 보정하고 기존 checkpoint를 새 press F1로 재평가.

## 6. 다른 섹션 (예정)

- **§1 학습환경(PPO·네트워크)**: 현재 S0 기본값은 num_envs512·horizon32·γ=λ=0.95·Actor lr
  1e-5·Critic lr 3e-4·entropy 0.001·멀티크리틱(value_dim=6)이며 PopArt는 후속이다. 6열 GAE는 곡의
  활성 줄 가중치를 먼저 적용해 합산하고 scalar actor advantage를 한 번 정규화한다. minibatch KL이
  0.03을 이미 넘으면 optimizer step 전에 차단해 초과를 확인한 뒤 한 번 더 갱신하는 문제를 막는다.
  Actor는 tanh-squashed bounded policy v1이며 초기 std=.02다.
  (γ=λ=0.95이므로 곱 GAMMA_LAMBDA=γλ=0.9025.)
- **§3 입출력(type·shape)**: action `(N,33)`, 보상/value `(N,6)`, base obs180 + goal128 +
  actuator-state(prev_action)33 = observation `(N,341)`으로 당시 확정했다. 현재 observation은 `(N,353)`다.
