# 02. Tablature → Finger Mapping

> 상태: **규칙 기반 v0 구현 / Canonical PlayEvent 연결 계약 정리 중**

## 책임

Tablature에서 선택된 음·줄·프렛을 왼손 압현 계획으로 변환한다.

```text
음악 note
→ tablature의 string/fret 검증
→ 왼손 finger 선택
→ hand position과 transition 결정
→ FretEvent 생성
```

이 단계의 결과는 Fret 학습 목표이며, Strike의 관절 action은 아니다.

## 입력

```text
- TablatureSong
- guitar tuning and fretboard geometry
- finger reach and joint-limit constraints
- optional style/profile
- optional human-reviewed fingering hints
```

style/profile은 나중에 다음처럼 확장할 수 있다.

```text
standard
jazz_position_shift
legato_priority
minimal_motion
human_reference
```

## 출력

```text
FretEvent {
    event_id
    score_time_s
    sustain_until_s
    notes[] {
        string_index
        fret_index
        finger_id
        press_start_s
        release_s
        confidence
    }
    chord_group
    hand_position_target
    transition_cost
}
```

같은 onset group의 단음·화음·strum은 하나의 canonical event ID를 공유한다. 단음은
note target 하나, chord/strum은 여러 note target을 event 안에 가지며 release와 sustain은
각 target에 유지할 수 있다.

이 결과에서 `press_start_s`는 target onset보다 앞설 수 있다. 그러나 이 lead time은 임의로 왼손과 오른손이 따로 바꾸는 값이 아니라 공통 event compiler에 기록되어야 한다.

## 최적화 기준

finger mapping은 다음 항목을 함께 고려한다.

- 동일 chord에서 손가락 충돌 여부
- 손가락 reach와 관절 제한
- 인접 event 사이의 hand position 이동
- 불필요한 finger lift
- sustain 중 기존 압현 보존
- string crossing과 다음 event 준비 시간
- 스타일별 선호도

초기 버전은 곡마다 규칙 기반 탐색이 선택한 하나의 canonical mapping만 학습 입력으로
저장한다. 여러 후보 mapping 집합을 actor 입력이나 학습 sampling에 사용하지 않는다.
선택된 mapping의 cost, 생성 규칙과 provenance는 재현을 위해 보존한다. Canonical finger
identity는 학습 prior이지만 음악적 성공의 hard gate는 아니므로, Fret policy가 같은
sounding fret을 만드는 다른 유효 손가락을 사용하는 것은 허용한다.

## Strike와의 관계

Finger mapping은 오른손이 실제로 어느 줄을 칠지 완전히 결정하지 않는다. 따라서 다음 branch를 별도로 둔다.

```text
TablatureSong
    ├─ FingerMapping → FretEvent
    └─ Picking/Strum compiler → StrikeEvent
```

두 branch는 나중에 `Canonical PlayEvent`에서 같은 `event_id`, `score_time_s`, `chord_group`으로 합쳐진다.

## 검증

- 모든 FretEvent가 유효한 string/fret/finger를 가짐
- chord의 required finger가 중복되지 않음
- sustain과 release 순서가 일관됨
- event 시간 순서가 단조 증가함
- Fret 학습 환경의 string convention과 일치함
- mapping confidence와 fallback 이유가 기록됨
