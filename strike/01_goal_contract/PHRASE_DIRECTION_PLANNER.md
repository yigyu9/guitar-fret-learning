# Phrase 방향 계획기 v1

## 실행 계약

```text
strike_training.json
[time, frame, string]
        ↓ 물리 최소 간격 내 사건 묶기
single_pick / strum
        ↓ 전체 곡 2-state 동적 계획
strike_plan.json
[time, frame, gesture, strings, direction]
        ↓
RL이 고정된 방향으로 READY → APPROACH → RELEASE_RECOVER 수행
```

원본은 음향 추출 결과이므로 수정하지 않는다. 파생 plan은 재현 가능한 실행 해법이며
`tab2body.strike_plan.v4`, 방향 profile은 `phrase_dp_microtiming_v3`다. checkpoint에는 plan 파일 해시와
profile이 봉인된다. v5 이전 strike checkpoint와는 호환하지 않는다.

## 묶음 규칙

- detector의 re-arm/follow-through로 계산한 물리 최소 간격보다 가까운 사건을 한 후보군으로 묶는다.
- 한 줄이면 `single_pick`, 서로 다른 두 줄 이상이면 `strum`이다.
- audible 줄 사이의 줄도 피크가 실제로 지나가므로 `traversal_strings`에 포함한다.
- 그중 음향 목표가 아닌 줄은 `protected_strings`로 기록한다.
- 동일 후보군 안에 같은 줄이 반복되면 `alternate_restrike`로 표시하고 현재 학습은 중단한다.
- 첫 사건부터 마지막 사건까지 50ms를 넘으면 인접 간격이 짧아도 새 묶음으로 나눈다.

## Strum micro-timing

- plan의 `time`은 첫 onset이 아니라 source onset의 평균이다.
- 방향 순서의 첫 traversal 줄은 중심보다 빠르고 마지막 줄은 중심보다 늦다.
- 관측 시각을 방향 순위에 회귀한 줄 간격을 4~12ms 범위로 제한한다.
- 관측 순서가 방향과 반대거나 동시 onset이면 기본 7ms 간격을 사용한다.
- `source_times_s`, `traversal_offsets_s`, `sweep_duration_s`, `timing_fit_rms_s`를 plan에 보존한다.
- 성공 timing은 첫 줄 하나가 아니라 모든 traversal 줄과 sweep duration을 진단한다.

## 방향 비용

각 사건은 down/up 두 후보를 가지며 곡 전체 누적 비용이 가장 작은 경로를 고른다.

- 시간차가 충분한 strum의 단조 줄 순서와 반대인 방향의 비용
- 짧은 간격에서 같은 방향으로 다시 준비해야 하는 비용
- 직전 통과 종료 줄에서 다음 통과 시작 줄까지의 거리
- 여유가 큰 구간의 불필요한 방향 반전 비용
- 정보가 동률일 때 적용되는 약한 down prior

결과에는 `direction_source`와 `direction_confidence`를 남긴다. confidence는 음향 방향의 정답
확률이 아니라, 현재 비용 모델에서 반대 방향보다 얼마나 우세했는지를 나타낸다.

## RL 적용 범위

- 현재 사건의 방향은 준비점, 진입점, 줄 통과 순서, 종료점, detector 정답에 모두 동일하게 사용한다.
- single 연습 단계도 곡 plan에서 뽑은 down/up을 모두 학습한다.
- S3에서는 다음 두 사건의 traversal과 방향을 lookahead로 제공해 회복 동작을 미리 연결한다.
- 정책 출력에는 방향 선택 head가 없다. plan과 다른 방향의 RELEASE는 오타현으로 판정한다.

## 생성과 검증

```bash
python tab2body/tools/build_strike_plan.py \
  data/song_bundles/<song_id>/training/strike_training.json \
  --out data/song_bundles/<song_id>/training/strike_plan.json

python tab2body/tests/test_strike_direction_planner.py
```

compiler의 re-arm, follow-through, 초기 timing tolerance가 바뀌면 plan을 다시 생성해야 한다.
