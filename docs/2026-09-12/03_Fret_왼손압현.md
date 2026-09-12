# 3. Fret-v2: 왼손 압현 기술

## 3.1 Fret이 해결하는 문제

Fret은 기타 왼손이 필요한 프렛을 정확히 누르고, 음이 울리는 동안 유지하며, 다음 목표로 이동하도록 학습하는 **왼손 skill prior**입니다.

Fret이 책임지는 것:

- 왼쪽 어깨·팔꿈치·손목의 접근
- 손가락의 위치와 압현
- chord 형태와 finger assignment를 고려한 hand pose
- 현재 음을 유지하면서 다음 음으로 이동하는 transition

Fret이 책임지지 않는 것:

- 오른손 pick/strum
- 기타 전체를 몸으로 지지하는 안정성
- 타현 permission과 event cursor
- 최종 전신의 모든 관절

따라서 Fret의 출력은 “이번 순간의 왼손 관절 목표 제안”이지 “이 음은 반드시 지금 재생하라”는 명령이 아닙니다.

## 3.2 Fret의 한 step 입력과 출력

```text
현재 물리 상태 q, qdot
현재 Fret event
다음 event와 hand-position 목표
손가락/프렛 geometry
이전 실행 action과 phase
          │
          ▼
       Fret-v2 policy
          │
          ▼
왼쪽 어깨·팔꿈치·손목·손의 30D action
```

관찰에는 크게 다음 정보가 들어갑니다.

- 왼팔과 왼손의 proprioception
- 몸 기준의 arm anchor
- 기타 기준 손목·손가락 geometry
- 현재 event의 줄·프렛·손가락·press/release/sustain
- 다음 목표의 geometry와 transition
- 현재 접촉·readiness·phase
- Synchronizer context와 짧은 action history

정책은 observation을 보고 각 관절의 normalized target/action을 `[-1, 1]` 범위로 냅니다. 이후 실제 환경에서 smoothing과 PD가 적용됩니다.

## 3.3 Action 30차원

```text
L_Shoulder  3
L_Elbow     3
L_Wrist     3
LH hand    21  (손가락 관절 묶음)
----------------
합계         30
```

`L_Thorax`와 그 밖의 관절은 Fret policy가 소유하지 않습니다. G0에서는 이런 축을 seated pose 또는 현재 hold로 유지합니다. G1/G2에서도 안정화 계층과 source policy의 소유권을 섞지 않는 것이 기본 방향입니다.

## 3.4 Observation 420차원 계약

현재 Fret-v2는 block을 정해진 순서로 이어 붙여 420차원 벡터를 만듭니다.

| 블록 | 크기 | 의미 |
|---|---:|---|
| `O_proprio` | 60 | 왼팔·왼손의 관절 상태, 속도 등 |
| `O_arm_anchor` | 18 | 몸과 기타 기준의 팔 anchor 정보 |
| `O_hand_geometry` | 60 | 손목·손가락·기타 geometry |
| `O_current_event` | 45 | 현재 event의 줄·프렛·손가락·시간·유지 정보 |
| `O_target_geometry` | 24 | 현재/목표 프렛 위치와 상대 geometry |
| `O_finger_transition` | 52 | 현재 손 모양에서 다음 손 모양으로의 전환 정보 |
| `O_lookahead` | 72 | 뒤에 올 event들을 압축한 정보 |
| `O_readiness_contact` | 45 | 압현·접촉·준비 상태 |
| `O_phase` | 12 | 접근·압현·유지·전환 phase |
| `O_synchronizer` | 2 | source policy용 동기화 context |
| `O_history` | 30 | 이전 action 또는 실행 문맥 |
| **합계** | **420** | `fret.observation.v2` |

이 순서는 단순한 설명용 순서가 아니라 contract입니다. block 하나를 추가하거나 순서를 바꾸면 checkpoint와 loader가 호환되지 않을 수 있습니다.

## 3.5 모델 구조

각 block은 별도의 작은 Linear+ELU encoder를 통과합니다. encoder 출력들을 합쳐 공통 MLP에 넣고 actor와 critic head를 만듭니다.

```text
11개 observation block
  → block encoder들
  → concat 640D
  → MLP 512 → 256
      ├─ Actor: 30D mean + learned log_std
      └─ Critic: 6D value head
```

현재 architecture 이름은 `fret.block_encoder_mlp.v1`입니다. Fret critic은 scalar 하나가 아니라 6개의 reward/value 관련 출력을 사용합니다. Gaussian policy의 action은 bounded 형태로 샘플링되며, actor 마지막 출력은 작은 gain으로 시작하도록 구성되어 있습니다.

## 3.6 압현 목표와 readiness

Fret에서 중요한 것은 단순히 손가락 중심점이 프렛보드 근처에 있는지가 아닙니다. 현재 설계는 기타 geometry와 실제 fingertip pad marker를 사용해 다음을 봅니다.

- 목표 string의 sounding fret이 맞는가?
- 목표 음을 방해하는 추가 press가 없는가?
- 목표 press가 최소 한 control frame 동안 확인되었는가?
- chord의 필요한 줄들이 함께 준비되었는가?
- sustain 중에 압현이 유지되는가?
- thumb support가 안전한가?

현재 hard `fret_ready`는 음악적 압현 판정입니다. thumb support와 전체 기타 안정성은 별도의 조건입니다. G1/G2에서 타현을 허용하려면 대략 다음이 모두 필요합니다.

```text
strike permission
  = fret_ready
    AND support_safe
    AND Strike ready
    AND guitar stable
```

프렛 위치는 fret cell 안의 normalized position으로 평가하며, 현재 geometry contract에서는 대략 중앙 80% 영역을 유효 영역으로 사용합니다. 실제 소리가 나는 프렛은 한 줄에서 눌린 음들 중 가장 높은 유효 프렛으로 해석합니다. 따라서 손가락 번호가 예상과 다르다고 곧바로 음악적 실패로 처리하는 것과, 실제 sounding fret이 틀린 것을 구분해야 합니다.

## 3.7 시간과 lookahead

운지는 타현 순간에 시작하면 늦습니다. mapping에 기록된 nominal `t_press`는 보통 타현 시점보다 약 0.12초 앞선 압현 완료 기준입니다. 이것은 팔을 움직이기 시작하는 시점과 같지 않습니다.

정책은 lookahead로 다음 정보를 보고 더 일찍 움직일 수 있습니다.

- 다음 event까지 남은 시간
- 현재 손 모양과 다음 손 모양의 거리
- 같은 손가락을 유지할지 바꿀지
- chord 전환 비용
- 짧은 lead time인지 여부

즉, `press_start`, `t_press`, `strike_time`은 서로 다른 개념입니다.

## 3.8 보상은 무엇을 좋아하는가

Fret reward는 하나의 성공 flag만으로 구성되지 않습니다. 현재 설계는 다음 요소를 여러 reward channel로 나누어 학습합니다.

- 목표 위치에 접근하는 정확도
- 압현 위치와 contact/press quality
- 음을 유지하는 sustain 품질
- chord의 bottleneck 음이 준비되었는지
- thumb support와 자세 안전성
- 다음 목표로의 이동과 transition
- 불필요한 움직임, 큰 속도, 안전 위반에 대한 penalty

6개의 reward/value channel은 어떤 부분이 좋아졌고 어떤 부분이 막혀 있는지 분석하기 위한 것입니다. 평균 reward 하나만 보고 “연주 가능”이라고 판단하지 않고, readiness·sustain·chord·transition 지표를 함께 봅니다.

## 3.9 Curriculum

Fret curriculum은 쉬운 동작에서 긴 음악 구간으로 올라갑니다.

```text
coarse_reach
 → fine_reach
 → isolated_press
 → integrated_press
 → chord_reach / chord_fine_reach
 → static_chord
 → frozen_context
 → goal_pair
 → transition_window
 → coverage
 → integration
 → full_song
```

각 단계는 observation/action shape를 바꾸는 것이 아니라, 목표 분포·난이도·reward mask·평가 기준을 바꾸는 방식입니다. 작은 도달/압현 성공이 곧 full-song source 승급을 의미하지 않습니다.

## 3.10 코드 읽기 지도

- contract와 block 순서: `../../tab2body/fret_v2_contract.py`
- 모델: `../../tab2body/learning/fret_v2_model.py`
- task와 물리 reward: `../../tab2body/env/tasks/task_fret.py`
- 설정: `../../tab2body/cfg.py`
- 학습 진입점: `../../tab2body/train_fret.py`
- 상위 개념: `../../master_plan/03_fret.md`

## 3.11 현재 상태와 주의점

Fret-v2의 420D 계약과 학습 파이프라인은 구현되어 있고, 개별 손가락·압현·전환을 개선하는 실험이 진행되었습니다. 하지만 정식 source policy로 full-song 승급되었다고 가정하면 안 됩니다. 특히 짧은 구간의 손가락 성공, chord readiness, 긴 구간 전환 성공률을 따로 확인해야 합니다.

과거 문서에는 Fret observation/action 차원을 다르게 적은 기록이 있습니다. 신규 실험은 `fret.observation.v2`와 현재 checkpoint manifest를 기준으로 시작합니다.

