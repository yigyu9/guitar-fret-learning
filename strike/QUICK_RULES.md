# 오른손 strike 규칙 — 사람이 먼저 읽는 짧은 버전

> 갱신: 2026-09-07. 현재는 pick-only single과 ordered strum, phrase-planned down/up을
> `strike_plan.v4`와 Strike-v2 303D 정책으로 실행한다.

이 문서는 전체 규칙을 빠르게 이해하기 위한 요약이다. 구현 충돌이 생기면
[현재 구현 규칙 정본](RIGHT_HAND_RULES.md), [goal 계약](01_goal_contract/README.md),
[구현 판정표](IMPLEMENTATION_CHECKLIST.md)를 따른다.

Ordered strum과 protected traversal은 구현되어 있다. 왼손 `FretReady`와 공통 타이밍 gate는
Strike 정책 내부가 아니라 [`master_plan/05_synchronizer.md`](../master_plan/05_synchronizer.md)의
FullBody Synchronizer가 담당한다.

## 현재 pick-only 전제

현재 학습의 원본 입력은 이미 오른손 타현 대상으로 선택된 pick 사건
`[time, frame, string]`이다. 가까운 이종 줄 사건은 compiler가 strum으로 묶는다. `time`이 정본이고
`frame`은 60 Hz 일치 검사용이다.
원본에는 방향 필드를 추가하지 않는다. 결정론적 `phrase_dp_microtiming_v3`가 전체 phrase에서
down/up을 계획하고, 결과와 판단 근거를 `strike_plan.json`에 고정한다.
손가락 타현과 방향 입력은 schema를 확장할 때 추가한다.

## 1. 일반 확장에서는 음표가 생겼다고 항상 오른손으로 치는 것은 아니다

`notes.t_on`은 새 소리가 난 후보 시각이다. hammer-on, pull-off, slide처럼 오른손 타현 없이 생긴
소리일 수 있다. 그래서 입력을 다음 순서로 바꾼다.

```text
SourceNote → 오른손 공격 필요 여부 → StrikePlan → 60 Hz RuntimeGoal
```

StrikePlan은 어떤 줄을 언제 칠지만이 아니라 pick/손가락, down/up, single/strum, 타현 영역과 다음
동작의 관계를 미리 정한다. 현재 데이터에는 오른손 annotation이 없으므로 첫 구현은 명시적인
`pick_only_v1` 해법을 사용한다. 이것은 사람의 유일한 정답이 아니라 재현 가능한 첫 실행안이다.

## 2. pick S0에서 타현은 접촉 상태가 아니라 RELEASE 사건이다

현재 `RH:pick`은 검지에 붙은 질량·충돌·방향 없는 점 marker이고 줄도 비충돌 선분이다. 실제 현이
휘거나 피크에 힘을 저장하지 않으므로 CONTACT와 LOAD를 억지로 성공 phase로 만들지 않는다.

두 프레임 사이 pick-tip 경로가 실제 유한 string segment를 올바르게 가로지른 한 순간을
`RELEASE`로 기록한다. CONTACT/LOAD는 fingerstyle V2나 물리 pick V2에서 필요할 때만 하위 상태로
추가한다.

## 3. 현재 공개 운동은 세 단계다

```text
READY → APPROACH → RELEASE_RECOVER
```

- `READY`: 한 고정 자세가 아니라 다음 타현에 도달할 수 있는 편안한 준비 범위.
- `APPROACH`: 목표 줄, 방향, 진입측과 strike lane으로 이동.
- `RELEASE_RECOVER`: 유효 swept crossing의 한 순간과 짧은 follow-through/re-arm을
  하나의 공개 단계로 묶는다.

빠른 반복에서는 이전 회복과 다음 `APPROACH`가 겹칠 수 있다. 매 음마다 중립 자세로 돌아가지
않고 앞 동작의 끝을 다음 동작의 시작으로 연결한다.

## 4. 중복 방지는 별도 detector 상태가 맡는다

정책의 세 운동 phase와 물리 detector 상태를 섞지 않는다.

```text
ARMED → RELEASE pulse → WAIT_REARM → ARMED
```

현재 detector는 한 줄을 친 뒤 충분한 3-D separation과 최소 대기 frame을 모두 만족해야 같은
`(agent,string)`이 다시 ARMED가 된다. 새 goal이 생겼다는 이유만으로 re-arm하지 않는다. 향후
same-string alternate 확장에서는 직전 방향 이력까지 추가한다. 그래야 쉼 중 떨림과 반복 오타도
숨지 않는다.

## 5. 유효한 pick RELEASE의 조건

다음을 모두 만족해야 한다.

1. 이전→현재 pick 경로와 string이 평행하지 않고 실제로 교차한다.
2. 교차가 이번 frame 경로 안이고 실제 유한 string 양 끝 안이다.
3. down/up 방향과 최소 횡단 속도가 맞다.
4. 최소 depth를 만족하고 심한 기타 관통 shortcut이 아니다.
5. 해당 detector가 ARMED다.

zone quality는 모든 RELEASE에 기록한다. A2와 S2 E0~T6에서는 진단이고, A3·S2 Z0~Z2·S3에서는
allowed/lane 밖 crossing을 목표 실패로 세며 진단값으로 원인을 구분한다.

detector는 goal을 보지 않고 모든 RELEASE를 기록한다. matcher만 시간·줄·agent·방향을 보고 목표 하나에
배정한다. 목표에 배정되지 않은 RELEASE는 쉼 중에도 false positive다.

## 6. 타현 위치는 점이 아니라 줄 위 영역이다

- allowed: guitar local `y=[-0.385,-0.255] m`
- preferred: `y=[-0.355,-0.295] m`

preferred 안의 모든 위치는 target lane 중심으로 뽑힐 자격이 동등하다. zone 단계는 이 구간에서
중심을 샘플링하므로 고정된 중앙 한 점만 외울 수 없다. 한 event의 정답은 sampled lane 주변
`±6 mm` 만점, `±12.5 mm` 성공 경계의 띠다. allowed 밖은 목표 불일치이지 안전 종료는 아니다.

## 7. 자연스러움은 정확도 위에 쌓는다

- 단현 attack은 주로 손목·전완, 큰 줄 이동은 팔꿈치·어깨가 미리 돕는다.
- release 직전의 큰 어깨 jerk와 매 음마다 home pose로 돌아가는 동작을 피한다.
- 줄 위 hover, 전 줄 sweep, 왕복 jitter, 과도한 침투로 reward를 얻지 못하게 한다.
- 피크를 쥔 grip은 처음부터 끝까지 유지한다. jerk와 추가 style prior만 정확한 타현·안전 근거 뒤 켠다.
- reference가 없는 주법은 “사람과 동일”이 아니라 “안전하고 운동학적으로 타당”하다고만 평가한다.

## 8. 기존 guitar 연구에서 가져오는 것과 버리는 것

가져오는 것은 `RH:pick` marker와 프레임 간 swept crossing 아이디어다. 그대로 복사하지 않는 것은
무한 string 연장선, 방향·zone·re-arm 부재, detector와 reward/goal 소비의 결합, 27-action checkpoint
직접 로드다. `scale/strum` 모션에는 pick-tip과 RELEASE 정답 라벨이 없으므로 자세·속도·style 참고로만
쓴다. 자세한 근거는 [legacy 분석](90_references/LEGACY_GUITAR_PICK_ANALYSIS.md)에 있다.

## 9. 현재 학습 순서

```text
A0_PICK_GRIP
→ A1_TIP_READY
→ A2_SINGLE_CROSSING
→ A3_TIMED_SINGLE (100→67→50 ms)
→ A4_STRUM_CONTEXT_RECOVERY (실제 strum 문맥 1줄 + clean recovery)
→ S0_TWO_STRING_STRUM (실제 2줄)
→ S1_STRUM_SPAN (3→4→5→6줄)
→ S2_TIMED_STRUM (E0 endpoint→400→250→225→200→175→150→100→zone 100→67→50 ms)
→ S3_SONG_INTEGRATION
```

각 승급은 최소 iteration과 연속 성능 gate가 모두 필요하다. A0~S2와 S3 마지막 사건은 목표 RELEASE
뒤 추가 RELEASE나 재무장 전 crossing이 생기면 12-frame full recovery를 처음부터 다시 센다. S3의
짧은 사건 간격은 다음 접근 전 확보 가능한 1~11 frame의 handoff recovery를 사용하며, 같은 줄 재타현은
재무장을 생략하지 않는다. scheduled/full/handoff completion, reset rate, blocked crossing rate는
별도 로그와 승급 gate로 남고, 고정 12-frame completion은 S3 진단으로 유지한다. 물리 pick, 실제 grasp/slip,
string 탄성, same-string alternate, fingerstyle와 hybrid는 별도 계약으로 다룬다.
시간 p95에는 허용창 밖의 올바른 target crossing도 포함하며, A0~A4는 완료 episode가 없는
rollout을 승급 성공이나 실패로 세지 않는다.
S2 E0에서는 마지막 줄만 남으면 final-string→exit를 목표로 연속 운동을 만들고, 최대 투영 증가분과
timing 독립 physical-completion pulse로 양방향 끝줄 완주를 먼저 학습한다. down/up raw count 중 낮은
완주율과 conditional/end-to-end recovery를 함께 gate한다. 한쪽이 3개 evidence window 연속 0.60
미만이면 그 방향을 70%로 학습하되 승급은 down/up 30/30 balanced holdout만 사용한다.
S3의 안전 실패는 항상 0이어야 한다. 음악적 wrong-crossing 종료와 blocked crossing은 tempo별
gate를 사용해 `0.75`에서 학습 가능한 범위를 허용한 뒤 원곡 속도에서 각각 `≤0.01`로 줄인다.
승급 F1과 rate는 episode 평균의 평균이 아니라 TP/FP/FN와 raw count를 합쳐 계산한다. S3가
정체되면 15%는 노출 보정 실패 구간, 85%는 전곡 균일 시작으로 학습하고 승급은 uniform evidence만
사용한다.
