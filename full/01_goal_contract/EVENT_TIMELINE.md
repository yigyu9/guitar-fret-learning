# 공통 이벤트 타임라인

> 상태: **CPU compiler 구현 완료 — physical FullG0Task 연결 전**

`Canonical PlayEvent`는 Fret과 Strike를 하나의 음악 사건으로 연결하는 runtime 정본이다.
구현은 `tab2body/full/events.py`, 공통 clock과 cursor는 `tab2body/full/clock.py`에 있다.

## 입력

- `mapping/fingering.json`: 실제 sounding note의 string·fret·finger와 source event ID
- `training/fret_training.json`: Fret actor에 제공할 60 Hz dense goal
- `training/strike_training.json`: 원본 strike 사건과 시각
- `training/strike_plan.json`: gesture, 방향, traversal order·offset·mask

실제 sounding fret은 strike frame의 dense Fret raster에서 추론하지 않는다. 겹치는 press
window 때문에 raster가 `DONT_CARE`이거나 다른 fret일 수 있으므로, strike의
`source_event_ids`를 `fingering.json` note에 연결해 만든다.

## 핵심 필드

```text
event_id, onset_group, source_event_ids
event_time/frame
release_boundary_time/frame
execution_deadline_time/frame
effective_delay_cap_frames
audible string targets
traversal mask/order/offsets/direction
unsupported diagnostics
```

Readiness 분모에는 실제로 울려야 하는 `audible_mask`만 포함한다. 피크 경로 보호를 위한
`traversal_mask`는 운동 기하이며 sounding target으로 해석하지 않는다. Strum의 release
boundary는 event center가 아니라 `event_time + min(traversal_offsets)`다.

configured 지연 상한은 3 frame이지만 다음 event의 traversal·rearm 여유를 보존해 실제
event별 상한을 0~3 frame으로 줄인다. Score clock은 지연이나 누락 때문에 이동하지 않는다.

지원되지 않는 barre, 특수 주법, finger가 없는 fretted note, 지원되지 않는 strike gesture는
정상 실행에서 fail closed한다. 분석 모드에서는 진단 상태를 남길 수 있다. Timeline과 입력
파일의 schema·SHA-256은 G0 bundle에 봉인한다.
