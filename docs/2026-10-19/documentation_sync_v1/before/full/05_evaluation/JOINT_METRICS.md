# 양손 공동 평가 지표

> 상태: **G0 평가 계약 — physical baseline 측정 전**

## 음악 사건 결과

- `full_event_rate`: 모든 audible target이 올바르게 준비되고 계획된 traversal이 실행된 비율
- `partial_event_rate`: multi-string event에서 일부만 성공한 비율
- `missed_fret/strike/both/stability_rate`: 실패 원인별 비율
- `audible_string_accuracy`: audible target string 단위 정답 비율
- `ordered_traversal_accuracy`: 방향·순서·계획 밖 crossing까지 포함한 Strike 실행 정확도

## Timing

- `on_time_rate`와 `delayed_rescue_rate`를 분리
- signed/absolute crossing timing error의 mean, p50, p95
- 실제 delay frame과 `delayed_by_fret/strike/both`
- event별 safe cap 때문에 구조적으로 지연할 수 없었던 사건 수

## Fret 유지

- readiness 획득률과 crossing 시점 readiness 유지율
- crossing 전에 press가 풀린 횟수
- crossing 이후 `t_release`까지 sustain 비율
- `effective_sounding_fret` 정확도와 별도 `fingering_adherence`

## 물리·계약 안전

- permission이 닫힌 상태의 crossing 수
- wrong-direction, order-violation, unplanned crossing 수
- source checkpoint hash·observation/action manifest 일치 여부
- 105D action의 ownership 위반, cap, non-finite 발생 수

G0 결과는 독립 Fret·Strike 평가와 반드시 함께 제시한다. 현재 CPU interface probe는 위
물리 성능의 증거가 아니며, 하나의 Isaac Gym simulator에서 실행한 FullG0Task 결과만 physical
G0 수치로 인정한다.
