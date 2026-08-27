# 2. 물리 타현 — 이벤트를 오른손 움직임으로 실행하기

## 핵심 정의

타현은 **현재 goal과 독립인 detector**가 찾아낸 단일 RELEASE 사건이고, matcher가 이를 goal에
배정한다. pick S0는 `RH:pick`의 유효한 swept crossing 자체에서 RELEASE를 검출한다. fingerstyle V2는
필요할 때 pad의 contact/load/release 내부 상태를 추가한다. 단순 근접, 줄 위 정지, 무한 연장선 교차,
같은 줄 주변 떨림, 지정하지 않은 손가락의 교차는 성공이 아니다.

현재 줄은 `contype=0` marker라 물리 접촉력이 생기지 않는다. 따라서 성공 판정은 기하로 하고,
기타 바디 접촉력은 안전·기대기 진단에만 사용한다.

## 타현 주체별 기하

- `pick`: `RH:pick`을 점 tip으로 보고 swept point segment를 사용한다.
- `thumb/index/middle/ring/pinky`: 각 `RH:*3→*_top` 끝마디의 tip 쪽 구간을 capsule pad로 보고,
  이전→현재 frame의 swept capsule을 사용한다. 마디 전체나 손바닥 접촉은 타현으로 인정하지 않는다.
- 모든 주체는 같은 string marker와 event matcher를 사용하지만, pad 반경·진입 깊이·re-arm 거리는
  주체별로 실측한다. 피크 상수를 손가락에 그대로 복사하지 않는다.

## 판정 순서

1. `present_agent_mask`의 모든 실제 agent 현재·직전 기하를 기타 로컬 좌표로 변환한다.
2. pick은 swept point, 손가락은 swept fingertip capsule과 6개 유한 string segment의 교차/최소거리를
   physics substep 또는 analytic swept interpolation에서 계산한다.
3. pick S0는 finite `t/s`, 깊이, 횡방향 속도, 방향과 `ARMED` 상태를 만족한 crossing만 RELEASE
   후보로 둔다. zone은 항상 기록한다. A2/A3에서는 진단만 하고, A4에서는 global allowed와
   sampled lane band를 목표 성공 gate로 사용한다. zone 실패 자체는 safety termination이 아니다.
   finger pad의 engagement 이력은 V2 detector에서 별도로 검사한다.
4. 한 프레임에 여러 줄을 건너면 궤적상의 `t` 순으로 정렬한다.
5. `(agent,string)` 쌍이 re-arm된 crossing만 새 사건으로 내보낸다.
6. detector 출력 전체를 eligible event에 시간·줄·agent·방향·순서 제약으로 일대일 매칭한다.
7. 남는 crossing은 wrong/extra strike, 남는 목표는 window 종료 때 miss가 된다.

`s∈[0,1]` 검사는 기존 참조 구현에 없던 필수 보강이다. 이것이 없으면 너트나 브리지 밖의 무한 연장선을
가로질러도 타현으로 오인한다.

## re-arm과 중복 방지

```text
ARMED → RELEASE pulse → WAIT_REARM → ARMED
```

한 agent가 한 줄을 친 뒤에는 다음을 모두 만족해야 같은 `(agent,string)`으로 다시 칠 수 있다.

- 픽이 줄 중심에서 re-arm 거리(초기 후보 3 mm) 이상 떨어짐.
- 최소 2 control frame이 지남.
- 이전 release 뒤 최소 시간과 올바른 물리 separation/방향 이력을 만족함.

re-arm에는 새 goal 존재를 넣지 않는다. 그렇지 않으면 rest 중 첫 오타 뒤 반복 오타가 검출되지 않는
허점이 생긴다. 다른 손가락의 독립적인 동시 타현까지 막지 않도록 상태는 줄만이 아니라
`(agent,string)`별로 관리한다. 이 규칙으로 줄 주변 왕복 떨림이 동일 event의 여러 성공이나 무료 보상이
되는 것을 막는다.
re-arm 거리와 frame 수는 주체별 synthetic test 후 GPU trajectory 분포로 확정한다.

## 단현·동시 손가락 타현·하이브리드

- `single`: 지정된 agent 하나가 지정 줄 하나를 친다.
- `multi_pluck`: 서로 다른 agent들이 각자 지정된 줄을 onset window 안에서 친다. 모든 target이
  채워져야 event 완료다.
- `pick+middle`, `pick+ring`처럼 피크와 손가락을 섞는 hybrid picking도 같은 `multi_pluck`이다.
- hybrid에서는 엄지·검지가 pick grip에 쓰이므로 기본 target agent는 pick+m/a/(명시 c)다.
- 한 손가락이 다른 손가락 target을 대신하면 `wrong_agent`, 비목표 줄을 치면 `wrong_string`이다.
- 엄지는 저음줄, i/m/a는 고음줄을 맡는 관례를 prior나 curriculum으로 사용할 수 있지만 hard rule은
  아니다. goal에 명시된 배정을 정답으로 삼는다.

## 스트럼

스트럼은 pick·thumb·index 등 **하나의 agent**가 짧은 시간에 만드는 순서 있는 crossing들의 묶음이다.

- 첫 target crossing이 strum clock을 시작한다.
- 이후 crossing은 궤적 `t`와 실제 frame 순서로 누적한다.
- 목표 mask를 정확히 한 번씩 채우고 `max_span_frames` 안에 끝나야 성공이다.
- 순서가 명시된 event는 순서 위반을 실패로 기록한다.
- 목표 사이의 비목표 줄 crossing은 upstream이 span을 허용한 경우가 아니면 extra strike다.
- 반대 방향으로 되돌아가 남은 줄을 채우는 zig-zag는 하나의 strum으로 인정하지 않는다.
- 들리는 `audible_mask`, 실제 경로의 `traversal_mask`, 음소거 `muted_mask`를 분리한다. 음표 사이 빈 줄은
  자동 audible target이 아니지만 물리 sweep이 지나가는 muted string일 수 있다.
- target별 onset offset band와 전체 span을 모두 검사해 한 frame 고속 sweep을 사람다운 strum으로
  인정하지 않는다.

## 보상 원칙

- 희소 핵심: 올바른 event-string-agent crossing 완료.
- shaping: 각 활성 agent에서 다음 목표 string segment까지 거리, 타현면 위 안전한 접근, 예상 방향 정렬.
- 감점: wrong-string, wrong-agent, extra/duplicate crossing, window miss, strum 순서·방향 위반.
- 작은 자연스러움 항: 목표 근처에 도착한 뒤에만 근위 관절 속도와 jerk를 억제한다.
- 쉼에는 gap 길이와 다음 event에 맞는 ready **manifold**를 사용한다. 단일 고정 pose와 매음 home 복귀를
  보상하지 않고 recovery를 다음 entry gate로 연결한다.

보상 core는 target 수로 정규화한 event-level objective다. 줄별 6채널은 원인 진단과 critic 후보로
보존하되 actor 정본으로 미리 확정하지 않는다. event scalar와 정규화 6채널을 primitive에서 ablation하고,
strum/chord target 수가 task return 크기를 바꾸거나 non-target FP가 채널 밖으로 사라지는 설계는 거부한다.
모든 보조항은 프레임 비율이 아니라 event 적분 return으로 core보다 작은지 감사한다.

## 자세와 안전

- action은 오른쪽 어깨·팔꿈치·손목 9 + 우손 21 = 30을 기준으로 한다. `R_Thorax`는 고정한다.
- 모든 DOF hard limit은 base의 bounded action/PD clamp로 강제한다.
- 손목 작업영역, 손·팔의 기타 관통, 비유한 상태, 속도 폭주는 실패 종료 후보다.
- 정상 줄 통과는 비충돌 marker 교차이므로 기타 바디 관통 종료와 혼동하지 않는다.
- `G:pluck_range` net force는 접촉 상대·점·정확한 압력을 알려주지 않으므로 먼저 진단 분포를 모은다.
- humanoid self-collision이 꺼져 있어 엄지-검지 net contact로 “픽 그립”을 판정할 수 없다. pick mode는 초기
  파지 자세와 상대 위치/회전 진단을 사용하고, 별도 물리 pick asset 도입 전에는 접촉 보상을 쓰지 않는다.
- finger mode에서는 비활성 손가락이 줄을 우발적으로 가로지르는 경우를 false positive로 기록한다.
  단, 근접만으로 뮤트라고 판정하지 않으며 실제 crossing/engagement가 있어야 한다.

현재 강제 범위는 [오른손 구현 규칙 정본](../RIGHT_HAND_RULES.md), 상세 상태와 수치 후보는
[rules.md](rules.md), 구현 우선순위와 gate는
[학습·평가 계획](../03_training/README.md)을 따른다.

타현 위치는 점이 아니라 실제 줄 위 영역으로 정의한다. 허용·선호 구간과 에셋 기반 그림은
[Strike 영역 정의와 시각화](strike-zone.md)를 따른다.
