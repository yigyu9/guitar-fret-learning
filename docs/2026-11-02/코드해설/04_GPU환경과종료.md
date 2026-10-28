# GPU 환경, 보상 정산, 에피소드 종료

[전체 읽기 안내](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md) · [해설한 소스 기준](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/소스기준.json)

이 문서는 `gpu/environment.py`와 `gpu/finger_skill_environment.py`를 해설한다. 정책이 행동을 낸 다음 **어떤 물리 자료를 읽고, 어떤 음의 기록을 바꾸며, 어느 시점에 보상과 종료를 반환하는가**가 중심이다. 두 파일은 물리 시뮬레이터 자체를 소유하지 않는다. 장면은 `GpuScene`, 관절 명령은 `BatchedController`, 그 결과를 평가하는 음악 환경은 이 두 파일이 맡는다.

추가 통합 후 곡·목표·손목 안내 자료형은 `song/task.py`, 공통 이벤트 시간선 검증과 `MusicTask`는 `score/canonical.py`, 표면·압현면·손목 영역 기하는 `gpu/contact.py`에서 찾는다. 회전·상대속도 연산은 `gpu/control.py`에 있다. 이번 파일 배치 변경으로 함수의 계산, 보상 계수, 종료 문턱이나 물리 설정을 바꾸지는 않았다.

## 먼저 구분할 두 클래스

실제 기본 인스턴스의 상속은 다음과 같다.

```text
TensorSongEnvironment                    environment.py
  └─ FingerSkillEnvironment              finger_skill_environment.py ← 현재 기본
```

`TensorSongEnvironment`는 공유 v22 측정·음별 원장·물리 실패·기본 관측의 몸체다. `FingerSkillEnvironment`가 이를 직접 상속하여 **구간 시계·목표 마스크·진단, 최종 9개 보상, 진행량에 따른 구간→전곡 전환, 손목 종료와 단일 실패 비용**을 한 클래스에서 결정한다. 현재 skill 계약은 `guitar_learning.finger_skill.v3`이고 J33 공동 학습만 지원한다. 따라서 부모의 `TERMS`나 `reward` 설명 문자열만 보고 현재 학습 보상을 판단하면 틀릴 수 있다. 마지막 오버라이드까지 따라가야 한다.

일반적으로 `super().__init__()` 안에서 `self._allocate()`나 `self._surface_potential()`을 호출해도 현재 객체의 가장 아래 구현이 선택된다. 부모 메서드 안의 `self.xxx()`는 부모 구현으로 고정되지 않는다는 점이 이 코드를 읽는 핵심이다.

공유 부모가 참조하는 단계 가중치도 이름을 구분해야 한다. `song/curriculum.py`의 [CPULeftCurriculum](/home/ajou/yigyu/3/guitar_learning/song/curriculum.py:29)은 CPU 전체 에피소드 지표용이고, [GPULeftCurriculum](/home/ajou/yigyu/3/guitar_learning/song/curriculum.py:137)은 GPU 손가락별 지표용이다. `environment.py`에서는 각각 `LegacyCurriculumState`, `CurriculumState`라는 지역 import 별칭으로 보인다. `_weights()`의 GPU 양성 항과 일부 옛 감점용 CPU 가중치 선택은 공유 부모의 동작이다. 현재 기본 `FingerSkillEnvironment`의 최종 9항은 이 단계 가중치를 제거하고 아래 고정 계수를 사용한다. 구간→전곡 전환의 `ExposureSchedule`도 이 두 성과 기반 단계 클래스와 별개의 진행량 일정이다.

## 공통 표기와 물리·정책 경계

| 표기 | 의미 |
| --- | --- |
| `N` | 병렬 환경 개수, 예를 들어 1024 |
| `M` | 원곡 전체 목표 음 개수, 기본 곡은 67 |
| `q`, `qd`, `target` | 각각 실제 관절 위치 rad, 관절 속도 rad/s, 요청 관절 위치 rad. 크기 `[N,105]` |
| `body_state` | `[N,B,13]`; 위치 xyz, 회전 xyzw, COM 선형속도 xyz, 각속도 xyz |
| `contact_force` | 몸체별 native 합력 `[N,B,3]`, N 단위 |
| `action` | 정책 출력 `[N,39]`, 각 값 −1~1. 왼손 학습에서는 마지막 오른손 6열은 0 |
| `onset`, `press`, `end` | 목표별 발음 시작, 압현 준비의 실제 압현 시작 경계, 발음 끝. 초 단위 `[M]` |
| G 좌표 | 현재 움직이는 기타의 로컬 좌표. 거리 m, 시간 s |

`clock`은 정수 물리 스텝 수다. 1/240초마다 1 증가하고 `_local_time()`이 `clock/240`을 반환한다. **한 정책 tick 1/60초는 실제 물리 끝점 4개**로 구성된다. PPO의 H32는 이 정책 tick을 32개 수집하는 경계이며, 곡 시계나 음별 원장 또는 손목 타이머를 초기화하는 경계가 아니다.

## 1. `gpu/environment.py`: 장면 결과를 음악 학습 자료로 바꾸는 공유 몸체

원문 진입점: [TensorSongEnvironment](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:98).

### 초기화: 변하지 않는 계약과 기하를 준비한다

`__init__()`는 우선 `metadata`의 관절·몸체 이름과 제어 계약을 검사한다. 정확히 105관절인지, 이름이 중복되지 않는지, 왼손 action codec과 설정이 일치하는지 확인한다. 이는 이름이 같은 것처럼 보여도 다른 배열 순서의 관절에 행동을 적용하는 사고를 막는다.

다음 `make_task()`로 곡을 읽고 열린현이나 시간이 잘못된 목표를 거부한다. 왼손 보상은 압현·발음 시간의 양수 길이를 분모로 쓰므로, `end <= press` 또는 `end <= onset`인 목표를 허용하지 않는다. 이벤트 토큰의 수용량도 시작 전에 검사한다.

관측의 필드·정규화 scale은 `ObservationBuilder`에서 받은 뒤 이 파일에서 확장한다. 현재 기본 557차원은 부모의 왼손 552차원에 `FingerSkillEnvironment`의 `SKILL_FIELDS` 1개(`finger_skill.remaining_s`)와 `WRIST_FIELDS` 4개를 더한 결과다. 이전 R/F/J one-hot 3열과 `planned_ticks` 1열은 제거했다. 이벤트는 음마다 24개 값이고 별도로 손가락별 tracking/next 8개 priority slot을 만든다. 상태와 이벤트는 서로 다른 입력이다.

정적 기하 로딩은 최초 한 번이다. 넥 압현 평면, 손목 영역 시계열, 검지~소지 끝마디 안쪽 패드 각 128점, 엄지 패드 128점과 유한 뒷면을 읽는다. 매 스텝 OBJ/STL을 다시 읽는 구조가 아니다. 곡별 시간·현·프렛·손가락 번호도 GPU 텐서로 캐시한다.

`required`는 한 음을 달성하기 위한 **끊기지 않은 clean 시간**이다.

```text
D = end - onset
required = min(D, max(0.05초, left_fraction × D))
```

따라서 `left_fraction=0.4`, 음 길이 0.5초라면 필요한 연속 clean은 0.2초다. 누적 0.1초 접촉 두 번 사이에 끊김이 있었다면 0.2초 달성으로 합치지 않는다.

### `_allocate()`: 환경별 원장을 만든다

원문: [_allocate](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:460).

최초 reset 때 `N`이 확정되면 영구 배치 상태를 할당한다. `note` 사전의 대부분은 `[N,M]`다. 같은 음이라도 환경마다 언제 접촉하고 실패했는지가 다르므로 환경 축과 목표 축을 모두 갖는다.

| 원장 값 | 읽는 방법 |
| --- | --- |
| `clean` | 발음 구간 안의 누적 clean 초. 끊겨도 누적값은 남음 |
| `clean_streak` | 현재 이어지고 있는 clean 초. 끊기면 0 |
| `best_clean_streak` | 에피소드 중 가장 길었던 연속 clean 초 |
| `left` | `clean_streak >= required`를 한 번 만족하면 True로 유지되는 달성 표지 |
| `contact_time` | `press..end` 안의 누적 candidate 접촉 시간 |
| `contact_streak`, `best_contact_streak` | 현재·최장 최초 접촉 연속시간 |
| `contact_progress` | `best_contact_streak/tau`를 0~1로 자른 값. 보상 예산을 얼마나 소비했는지 나타냄 |
| `wrong`, `missing` | 발음 구간의 오압현·접촉 없음 누적 초 |
| `near_time`, `surface_min` | 1cm 근접 시간과 노출 중 최소 패드 거리. 달성과 별개인 진단 |

`contact_progress=1`이 곧 그만큼의 보상을 실제 지급했다는 뜻은 아니다. 실패 tick에서는 양성 보상이 억제되어도 진행 원장은 앞으로 간다. 동일 접촉을 반복해서 처음 보상을 다시 받는 일을 막는다.

### `_snapshot()`와 `_contacts()`: 현재 장면을 기타 좌표로 측정한다

원문: [_snapshot](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:532), [_contacts](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:584).

`_snapshot()`은 배열 크기·장치·유한값을 확인하고 월드/환경 위치에서 기타 위치를 빼고 역회전한다. 그 결과 기타가 약간 움직여도 줄·프렛·손목의 상대 위치를 같은 G 좌표로 비교할 수 있다. 각 몸체의 `loaded`는 native 합력 크기가 0.01N 이상인지다.

`_contacts()`에는 서로 다른 표본 계열이 함께 나온다.

1. 엄지와 네 손가락의 2·3마디 전체 메시 지지 꼭짓점: 타 손가락이 목표현의 더 높은 프렛을 막는지, 원래 측정과 어떻게 다른지 검사한다.
2. 검지~소지의 끝마디 안쪽 패드 128점: 현재 왼손의 올바른 접촉과 목표 접근 거리를 검사한다.

패드 점과 법선은 현재 몸체 회전으로 옮긴다. 점 속도는 몸체 원점 속도에 `ω × 점 오프셋`을 더하고, 기타의 병진·회전에 의한 속도를 빼서 구한다. 최근접 표본 번호가 바뀌는 순간의 거리 차분을 속도로 쓰지 않는다.

압현 목표는 실제 현의 x/y를 유지한 채 넥 압현면에 투영한 선분이다. `pad_target_geometry()`가 프렛셀 안쪽 2mm 경계, 가로거리 3mm, 평면 높이 −1~3mm, 패드 방향 cosine≥0.1, 해당 끝마디의 하중을 검사한다. **거리에는 최근접 유효점 하나**, 접촉에는 **조건을 모두 함께 만족하는 패드점 하나 이상**을 사용한다. 두 점이 반드시 같을 필요는 없다. 오압현은 현재 기본 자식의 `_left_wrong_contacts()`가 다시 판정한다.

최종 `candidate`는 `positive & ~wrong`이다. 이미 오압현이 제외된 후보이므로 아래 clean 계산의 입력은 잘못된 접촉을 포함하지 않는다. 그렇더라도 candidate는 몸체 합력과 유한 표면의 기하 대리지표이며, 실제 줄에 걸린 압력이나 소리의 인증은 아니다.

### `reset()`: 선택된 행의 측정 상태만 되돌린다

원문: [reset](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:747).

장면 소유자가 먼저 실제 물리를 준비 자세로 복원한 뒤 이 함수를 호출한다. 환경 reset 자체는 native actor 상태를 쓰지 않는다. `indices`에 해당하는 시계·이전 행동·원장·실패·누적 보상·진단만 0으로 만든다. 다른 병렬 환경은 계속 진행한다.

초기 snapshot으로 기타·발의 기준 자세를 저장하고, reset 뒤 현재 candidate를 `previous_candidate`에도 넣는다. 첫 물리 구간에서 존재하지 않는 과거 표본을 임의의 False와 연결하지 않기 위해서다. 최초 B 자세 품질과 실제/요청 손가락 각도 범위도 reset 표본으로 기록한다. 진행 중인 control의 중간에는 reset을 거부한다.

### 한 tick의 처리: `begin_control → substep × 4 → end_control`

원문: [begin_control](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:861), [substep](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1031), [end_control](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1241).

`begin_control(actions)`는 유한한 `[N,39]` 행동과 비활성 손 0을 확인한다. tick 임시 보상·비용·실패를 비우고, **행동 전 접근 potential Φ**를 저장한다. 손가락이 이미 target 한계에 있는데 더 밖으로 누적하려는 행동도 진단용으로 표시한다.

각 `substep(snapshot)`은 실제 연속한 물리 스텝인지 확인하고 시계를 1 증가시킨다. 이어 새 장면을 측정하고, 직전 끝점과 현재 끝점 사이에서 목표 시간창과 겹치는 시간을 계산한다.

```text
audible_dt = max(0, min(now,end) - max(before,onset))
press_dt   = max(0, min(now,end) - max(before,press))
both       = previous_candidate AND candidate
clean_dt   = audible_dt × both
wrong_dt   = audible_dt × (previous_wrong + wrong)/2
missing_dt = audible_dt × (previous_absent + absent)/2
```

여기서 absent는 candidate도 wrong도 아닌 상태다. clean은 양 끝점 모두 유효해야 인정하는 보수적 구간이고, wrong/missing은 끝점 사다리꼴 적분이다. 예를 들어 1/240초 구간의 한쪽 끝점만 wrong이면 약 1/480초의 wrong 시간이 쌓인다. 이 방식은 정확한 접촉 시작 시각을 엔진에서 받은 것과는 다르다.

그다음 누적 clean·현재/최장 streak·달성 표지·최초 접촉 진행·오압현 출처 시간을 갱신한다. 보상률을 주는 B 대기·엄지 안내는 매 240Hz 표본에서 `/240`으로 적분한다. 선택적 tracking/shape와 구형 손목항 계산도 부모에 남지만, **현재 최종 합산은 자식이 걸러낸다**. `_safety()`가 각 표본의 물리·손목 실패를 누적한 다음 previous 값을 새 끝점으로 옮긴다.

`end_control()`은 정확히 4개의 물리 표본이 왔는지 확인한다. 수행 부족 정산→실패 고정→접근 potential 정산→실패 tick 양성 억제→행동 변화→단일 비용→최종 9항 합산→종료 보고 순서다. 반환값은 다음 구조다.

```text
(observation, reward[N], cost[N], terminated[N], truncated[N], completed_episodes)
```

이 환경은 `truncated`를 모두 False로 돌려준다. H32 수집 경계는 environment terminal이 아니며 수집기가 이어지는 관측으로 bootstrap한다. 종료한 환경만 `completed_episodes`의 CPU 사전으로 변환한다.

### 관측과 진단을 읽는 법

원문: [_events](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1367), [observation](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1437), [_episode](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1532).

`observation()`은 q−준비 q, qd, target−q, 이전 action, 기타의 골반 상대 자세·속도, 손/신체 proxy, 지지 flag, 기타·발 변위, 곡 이력 등을 이어 붙인다. 왼손에는 손목 영역 오차, 실제 MCP/PIP/DIP sin/cos, 손가락별 유효성·대기 gate, 엄지 안내를 더한다. 자식이 로컬 잔여 시간 1열과 종료 타이머 4열을 덧붙인 뒤 scale로 나누고 −10~10으로 자른다. 각 숫자가 SI 원값 그대로 들어간다고 생각하면 안 된다.

`_events()`는 선택 음의 시간·현·프렛·손가락·현재 candidate/wrong·현재 clean streak·최초 접촉 진행·패드 오차/속도·법선을 24값으로 만든다. priority 8slot은 `finger_target_indices()`의 손가락별 tracking/next 순서를 따른다. 목표가 없는 슬롯은 mask=False와 0값이다.

`_record_finger_motion()`은 60Hz 완료 끝점의 실제·요청 범위, target−q RMS, 한계 도달 비율, 행동 부호 뒤집힘, 손바닥 상대 기저 회전을 누적한다. 240Hz 최댓값과 혼동하지 않는다. 손가락이 안 움직일 때 `action_mean_abs`도 작은지, target만 움직이고 actual이 못 따라가는지, actual이 움직여도 올바른 패드가 접근하지 않는지를 나눠 볼 수 있다.

오른손 `_strike()`, strict50/100ms 기록과 일부 옛 항은 공유 코드에 있다. 현재 왼손 기본은 오른손 행동 0이고 오른손 음악항을 최종 9항에 합치지 않는다. 코드를 지우지 않았다고 현재 학습 목표라는 뜻은 아니다.

## 2. `gpu/finger_skill_environment.py`: 현재 학습 범위와 최종 기준

### `FingerSkillEnvironment`: 원곡을 복사하지 않고 보는 범위만 바꾼다

원문: [FingerSkillEnvironment](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:48).

이 클래스 하나가 J·independent·K1·scheduled 계약을 받는다. 생성 시 v3 schema와 고정 J 메타데이터, 계획 전이 수와 25% 전환 문턱을 확인한다. 이전 R/F 부모와 별도 Simplified 자식은 없으며 `TensorSongEnvironment`를 직접 상속한다. 매 정책 tick(1/60초)에 새 행동을 내고 실제 물리 4표본을 처리한다.

구간 선택의 핵심 상태는 다음과 같다.

| 상태 | 의미 |
| --- | --- |
| `score_offset[N]` | 원곡 시계 = local 시계 + offset |
| `duration_ticks[N]` | 선택 구간의 로컬 길이, 60Hz 정수 |
| `focus_mask[N,M]` | 이 에피소드에서 수행·보상·성공 분모에 포함하는 원래 음 |
| `recovery_mask[N,M]` | B 회복 경계 계산에 쓰는 범위. focus 다음 같은 손가락 음을 추가할 수 있음 |
| `view_first/last` | 손목 안내를 구간 밖으로 진행시키지 않기 위한 원곡 경계 |
| `phrase_ids` | 종료 결과를 어느 원곡 구간과 연결할지 나타내는 ID |

`_reset_scope()`는 reset 행마다 균형 sampler에서 구간을 하나 고른다. 원곡 target 배열은 그대로 두고 마스크만 바꾼다. 선택되지 않은 과거 음이 즉시 미달성으로 집계되는 일을 막고, 다음 미선택 음의 준비 경계는 recovery에 남겨 구간 말미를 인공적인 완전 휴식처럼 만들지 않는다.

보상 균형계수는 선택된 음 기준으로 다시 계산한다.

```text
b_i = 선택 음 수 / (선택 범위에 등장한 손가락 수 × 그 손가락의 선택 음 수)
```

선택 음이 8개이고 검지 6개·약지 2개라면 검지 음은 8/(2×6), 약지 음은 8/(2×2)다. 각 손가락이 맡은 전체 음의 총 가중치가 같아진다. 모든 손가락의 음 하나당 점수를 같게 하는 방식은 아니다.

`_score_time()`의 offset은 음별 onset/press/end 비교용이다. `_local_time()`은 reset 후 실제 물리 시간이고 손목 유예·잔여 에피소드 시간에 사용한다. 이 둘을 섞으면 구간 시작 직후 이미 유예가 끝난 것처럼 판단하거나, 원곡 15초 음을 local 3초에 찾지 못하게 된다.

`plan_decisions()`와 `decision_observation()`은 삭제했다. 행동을 여러 tick 유지하거나 계획 길이를 관측에 다시 쓰지 않으며, `remaining_s`는 실제 로컬 종료까지 남은 시간만 나타낸다. 이벤트 토큰의 시간 비교와 접촉 적분은 원래 60/240Hz 경계를 그대로 따른다.

`_episode()`는 부모의 전곡 집계를 선택 마스크의 분모로 보정한다. `completed`는 선택 타임라인 끝까지 갔는지, `stage_success`는 안전 완주와 모든 선택 음 달성을 함께 만족하는지다. 원곡 67음과 구간 4음의 평균 달성을 같은 분모로 읽지 않도록 `selected_target_count`와 `scope`를 확인한다.

### 같은 클래스에서 보상·노출·종료 계약을 확정한다

원문: [FingerSkillEnvironment.__init__](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:55).

생성자는 v3·phase J·independent·hold_ticks1·scheduled를 검사하고 `full_song_after == planned_transitions//4`를 요구한다. phase·탐색·유지 길이는 선택 분기가 없는 고정 메타데이터다. 현재 보상 이름은 `REWARD_TERMS`의 9개이며 기존 계수·접촉 기하·물리 설정을 유지한다. R/F 보상 필터와 단계 이전은 없다.

`set_training_progress(committed)`는 실제 optimizer에 반영된 raw 전이 수를 단조롭게 받는다. `_reset_scope()`는 문턱에 도달한 뒤 **새로 reset되는 환경부터** 전곡으로 바꾼다. 진행 중 구간을 중간에 잘라 전곡으로 교체하지 않는다. 최초 reset은 명시적으로 구간이다. 따라서 planned budget의 25%라는 문턱과 실제 구간 전이 비율은 정확히 같은 개념이 아니다.

### 현재 9개 보상의 계산 소유자

최종 선택은 [_reward_components](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:342)다. 아래의 `b`는 앞의 선택 음 균형계수, `D`는 음 길이다.

| 항목 | 실제 처리와 시점 |
| --- | --- |
| 목표 패드 접근 | 자식 `_surface_potential()`을 부모 begin/end에서 차분. 매 60Hz `γΦ(next)−Φ(before)` |
| 최초 접촉 | 부모 240Hz 최장 contact 진행 증가량의 raw `0.5b`에 자식 0.5배. 한 음 총 상한 `0.25b` |
| 압현 유지 | 부모 clean 적분의 raw `2b×clean_dt/D`에 자식 0.5배. 완전 유지 예산 `1b` |
| 압현 달성 | 부모 연속 clean 문턱 통과 raw `0.5b`에 자식 0.5배. 한 번 `0.25b` |
| 오압현 | 부모 wrong 적분 `−b×wrong_dt/D`에 자식 0.15배. 전체 음 오압현 시 `−0.15b` |
| 음 수행 부족 | 자식 정산 함수가 누락·최장 clean 부족을 합침. 한 음 최대 `−0.10b` |
| 대기 자세 | 공유 B 회복률을 240Hz 적분한 raw 항을 그대로 선택. 기본 전체 네 손가락 합 최대 0.02/초 |
| 엄지 안내 | 공유 엄지 기하/접촉률의 240Hz 적분을 그대로 선택. 최대 0.02/초 |
| 행동 변화 | LH21 계수 0, 왼손목 계수 0.0025/초, 나머지 0.01/초의 명령 변화 감점 |

행동 변화의 실제 한 tick 식은 `−sum(c_i × max(abs(a_i−previous_a_i)−0.05, 0)^2) / 39 / 60`이다. 0.05 안의 작은 변화는 감점하지 않고, 초과분을 제곱하며39축 분모와60Hz 시간 적분을 적용한다. 예를 들어 계수0.01인 한 축만0.15 변하면 초과분은0.10이고 해당 tick의 기여는 약−4.27×10⁻⁸이다. LH21은 `c_i=0`이어서 이 식의 움직임 비용을 받지 않는다.

부모의 단계별 `groups`·`weights` 계산은 호출되지만 자식이 **가중된 components 대신 raw terms에서 위 9항을 새로 구성**한다. 구형 단계 계수가 현재 보상에 한 번 더 곱해지는 구조가 아니다. `song_finger_tracking`, `song_finger_coordination`, `song_wrist_position`, `song_missing_press`, `song_left_missed`, `terminal_failure`는 현재 합산에서 제외된다.

### 목표 패드 접근: 가까이 서 있기만 해서 계속 양성을 받는 항이 아니다

원문: [_surface_potential](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:283).

각 손가락 tracking slot 0에서 유효한 목표 하나를 고르고 다음을 합한다.

```text
near = clamp(1 - distance/0.02, 0, 1)
direction = 1 - 0.2 × near × (1-clamp(alignment,0,1))
Φ = Σ b × valid × tracking_weight × exp(-distance/0.03) × direction
r = 0.99 × Φ_after - Φ_before
```

거리 3cm의 거리계수는 `exp(-1)≈0.368`, 0cm는 1이다. 방향 불일치는 2cm 안에서만 최대 20% 줄인다. 완전 대기 회복 중에는 `tracking_weight=0`이므로 그 손가락의 접근 potential은 없다. 후보 접촉 여부나 행동·속도 비용을 이 potential에 별도 가산하지 않는다.

실제 종료는 실패든 정상 끝이든 `Φ_after=0`으로 정산한다. 반면 H32와 목표 교체에서는 생략하거나 Φ를 초기화하지 않는다. 예를 들어 직전 Φ=0.7에서 종료하면 접근항은 −0.7이다. 이 음수가 반드시 접근 실패라는 뜻은 아니다. potential 보상의 끝값을 회수하는 정상적인 terminal 정산일 수 있다. reward 그래프는 terminal·비terminal을 구분해서 읽어야 한다.

### 음 수행 부족: 두 감점을 합산하지 않고 큰 부족 하나로 정산한다

원문: [performance_settlement](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:29), [_prepare_control_end](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:317).

음이 진행 중이면 `missing/D`가 증가한 만큼 `0.1b` 예산에서 조금씩 지급한다. 음 끝에서는 아래 비율 중 큰 값으로 최종 due를 정한다.

```text
누락 비율 = clamp(missing/D,0,1)
연속 유지 부족 = clamp(1-best_clean_streak/required,0,1)
최종 부족 = max(누락 비율, 연속 유지 부족)
추가 감점 = max(0, 0.1b×부족 - 이미 지급한 감점)
```

누락 비율 0.6, 연속 부족 0.8, b=1이면 최종 0.08이다. 이미 0.06을 지불했다면 음 끝에 0.02만 더 감점한다. 0.06+0.08로 중복 감점하지 않는다. `performance_paid`, `performance_settled`는 `[N,M]`이며 선택 reset 때만 0이 된다.

### 물리·손목 실패와 비용

기존 물리 판정은 부모 [_safety](/home/ajou/yigyu/3/guitar_learning/gpu/environment.py:1223)에 있다.

| 실패 | 문턱 |
| --- | --- |
| 기타 기준 위치 이탈 | 거리 > 0.08m |
| 기타 기준 회전 이탈 | 회전벡터 크기 > 0.35rad |
| 발 기준 위치 이탈 | 두 발 중 거리 > 0.04m |
| 가슴·오른쪽 어깨·오른쪽 힙 지지 flag가 모두 소실 | 셋 중 하나라도 남으면 유지. 전부 없는 상태가0.25초 초과 |
| 양발 중 접지 flag 소실 | 0.25초 초과 |
| 관절 속도 과대 | 어느 관절이든 절댓값 > 50rad/s |
| 유한 지지 제어의 법선 무정의 | control invalid flag |

지지 flag는 몸체 합력이며 상대 접촉쌍 인증이 아니다. 이 기준은 실제 압현 성공을 대신하지 않고 장면의 실패를 검출한다.

현재 자식 [_safety](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:296)는 여기에 손목을 추가한다. 먼저 안내 상자의 최근접점까지의 축별 오차 중 최대 절댓값 `excess=max(abs(delta))`를 구한다. 유클리드 거리 문턱이 아니다.

* local 3초 뒤 normal 검사 활성. 상자 밖 **추가 3cm 초과**면 active가 되고 elapsed에 1/240초씩 더한다.
* active 상태에서 추가 2~3cm로 돌아오면 elapsed를 같은 속도로 줄인다. 추가 2cm 이하로 들어오면 active와 elapsed를 0으로 만든다.
* elapsed≥1.5초면 normal 손목 실패. 이는 경계 밖 net 누적시간으로, 회복대에서도 계속 누적하는 방식이 아니다.
* 추가 10cm 이상이 연속 0.10초면 severe 실패. 이 조건은 최초 3초 유예 중에도 적용한다.

예를 들어 3cm 초과 1.0초 뒤 2~3cm 회복대에 0.4초 머물렀다면 elapsed는 0.6초다. 음 목표가 바뀌거나 H32에 도달했다고 이 시간을 지우지 않는다. 선택 에피소드 reset에서만 타이머와 failure latch를 모두 지운다.

[_apply_failure_cost](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:327)는 물리·손목을 합친 `failed & ~failure_paid`에 한 번만 비용을 매긴다.

```text
cost = 5 + 2×남은 local 에피소드 초
       + 선택·미정산 음의 미관측 wrong 상한 및 미지급 수행 부족 상한
```

남은 음 예산은 [remaining_negative_budget](/home/ajou/yigyu/3/guitar_learning/gpu/finger_skill_environment.py:41)의 `0.15b×남은 발음 비율 + max(0,0.1b-performance_paid)` 합이다. 이미 관측해 지불한 감점을 다시 전액 더하지 않는다. 구형 running physics cost 함수는 자식에서 비워 두며, 구형 보상 −2 `terminal_failure`도 9항에 포함하지 않는다. 실패 비용은 `reward`와 별도인 `cost` 출력이며 PPO가 두 가치를 결합해 최적화한다.

실패 tick의 최초 접촉·유지·달성·대기·엄지 양성은 억제한다. 오압현, 수행 부족과 terminal 접근 정산 같은 음성은 남긴다. 물리와 손목이 같은 tick에 실패해도 비용 2회를 청구하지 않는다.

### 이 파일부터 코드를 볼 때의 순서

먼저 `FingerSkillEnvironment.__init__`의 계약과 `_reward_components`를 읽어 현재 사용 항을 고정한다. 다음 `_surface_potential`, `performance_settlement`, `_safety`, `_apply_failure_cost`를 읽는다. 그 뒤 부모 `begin_control/substep/end_control`을 읽으면 raw 계산과 최종 선택이 연결된다. 마지막으로 scope/reset/observation/episode를 읽어 어느 값이 에피소드 동안 유지되는지 확인한다.

특히 `observation()`은 원장을 진전시키지 않는다. 관측을 여러 번 요청했다고 보상을 더 받거나 손목 시간이 늘지 않는다. 시간·접촉 적분은 실제 `substep()`과 `end_control()`의 소유다.


### 새 관측과 이전 checkpoint의 관계

`_observation_state()`는 부모의 552열 뒤에 로컬 잔여 시간과 손목 종료 타이머 4열을 붙여 557열을 만든다. remaining의 scale은 원곡 task 길이이고, 타이머의 scale은 순서대로 1·1.5초·3초·0.1초다. 정책은 마지막 5개 필드명과 순서까지 확인한다.

이전 561열 checkpoint와 R/F/J 계약은 지원하지 않는다. 과거 557열도 phase/계획 tick을 포함하던 다른 관측이므로 새 557열에 쓸 수 없다. 새로운 v3 환경·정책 v2로 학습하고, 같은 전체 계약·소스에서 저장한 checkpoint만 엄격 재개한다.
