# Strike 영역 정의와 시각화

## 결론

strike 목표는 한 점이 아니라 각 실제 string segment 위의 **길이 있는 띠**다. 모든 agent가 공유하는
1차 위치 범위는 guitar local `y_g`로 정하고, x 중심은 각 줄의 실제 기울어진 중심선을 그대로 따른다.
이 띠는 `RELEASE`가 허용되는 위치 footprint이며, 준비부터 회복까지 손을 매 frame 중앙으로 끌어당기는
pose 목표가 아니다.

| 구간 | guitar local y | 길이 | 용도 |
|---|---:|---:|---|
| 기존 `G:pluck_range` | `[-0.414, -0.242] m` | 172 mm | 참조 box; 그대로 정답으로 사용하지 않음 |
| **허용 strike 영역** | `[-0.385, -0.255] m` | 130 mm | 22프렛 끝과 브리지에서 여유를 둔 넓은 타현 띠 |
| **선호 core 영역** | `[-0.355, -0.295] m` | 60 mm | position quality 1.0인 중앙부 |

각 줄의 띠는 실제 `G:stringN→G:stringN_end`를 위 y 범위로 clip하고 중심선 좌우 2 mm를 시각 폭으로
사용한다. 이 2 mm는 줄 선택용 target ribbon이지 손가락 pad 반경이 아니다.

## 이 범위의 근거

- 22프렛 bridge-side edge는 약 `y=-0.2312 m`다. 허용 영역의 nut 쪽 끝 `-0.255 m`는 여기서
  약 23.8 mm 떨어져 지판 끝 타격을 피한다.
- 6개 string bridge endpoint는 `y=-0.40345..-0.40905 m`다. 허용 영역의 bridge 쪽 끝
  `-0.385 m`는 약 18.5~24.1 mm 여유를 둔다.
- 기존 `G:pluck_range`의 중심은 `y=-0.328 m`이고, 새 선호 core가 이를 포함한다.
- 넓은 허용 영역 안에서 음색 위치를 바꿀 수 있게 하되, 학습 초기에는 중앙 core를 선호한다.

## position quality

- preferred 내부: `1.0`.
- allowed 경계에서 preferred까지: raised-cosine으로 `0→1`.
- allowed 밖: `0.0`.

현재 단계 적용은 다음처럼 분리한다.

- A2: quality를 기록하지만 성공 판정에는 사용하지 않는다.
- A3: quality를 기록하지만 시간·줄·방향만 성공 판정에 사용한다.
- A4: allowed 밖 crossing은 일반 false positive이며 zone/lane 진단값으로 구분하고,
  목표는 window close까지 남는다.
- 어느 단계에서도 영역 밖 crossing 자체를 안전 종료로 만들지 않는다.

## allowed 영역과 phrase lane

130 mm allowed 전체는 도달 가능성과 다양한 음색 위치를 허용하는 외곽 계약이다. A0~A3의
기본 lane은 `y=-0.325 m`다. A4에서는 preferred 안의 lane을 event마다 샘플링하고 그 위치를
ready/entry/exit vector로 actor에게 제공한다. preferred의 모든 위치는 lane 중심으로 샘플될
자격이 동일하므로 고정된 중앙 한 점 보상이 생기지 않는다. 한 event 안에서 preferred 전체가
정답인 것은 아니며, 아래 local band를 만족해야 한다. 향후 phrase-level 음색 입력이 생기면
이 샘플러를 구절 lane으로 대체한다.

샘플된 lane 자체도 한 점이 아니다.

| sampled lane 상대 오차 | 판정 |
|---:|---|
| `|y_cross-y_lane| ≤ 6 mm` | lane quality 1.0 |
| `6 mm < |error| ≤ 12.5 mm` | raised-cosine quality, 성공 허용 |
| `|error| > 12.5 mm` | A4 lane 실패 |

A4 성공은 global allowed 영역과 이 local lane band를 모두 만족해야 한다. zone success의 분모는
두 gate를 적용하기 전의 timing-valid target attempt를 별도 저장공간에 보존하므로, 영역 밖 실패가
분모에서 사라져 성공률이 항상 1이 되는 오류를 막는다.

## ribbon 밖의 phase 영역

사람다운 한 번의 stroke는 release ribbon만으로 정의되지 않는다. 각 줄의 tangent, across-string 방향,
soundboard normal로 local stroke frame을 만들고 다음 3D 영역을 agent·stroke mode별로 보정한다.

```text
ready shell → approach corridor / entry gate
            → release ribbon
            → exit / next-event recovery corridor
```

- `ready/approach/entry`: 아직 타현 성공이 아니며 올바른 접근측과 기타 바디 clearance를 만든다.
- `release ribbon`: 시간·줄·agent·zone이 맞을 때만 one-shot 사건을 낸다.
- `exit/recovery`: 즉시 역전과 이웃 줄 오타 없이 빠져나와 다음 event를 준비한다.

contact/load tube는 marker pick S0의 필수 geometry나 성공 gate가 아니다. signed gap과 virtual load가
필요한 fingerstyle/물리 pick 후속 연구에서만 선택적 diagnostic overlay로 추가한다.

현재 실행 정본 `tab2body/strike_cfg.py`와 checkpoint contract가 확정한 영역값은 y footprint와
sampled lane 폭이다. x/z의 3D gate 크기와 agent별 attack angle은 합성 trajectory와 GPU replay에서
정상/오류 분포가 분리된 뒤 schema version을 올려 추가한다. 자세한 phase 규칙은
[NATURAL_MOTION_RULES.md](NATURAL_MOTION_RULES.md#phase별-3d-영역)를 따른다.

## z와 agent별 차이

공통 접근 높이 후보는 string 중심보다 `3..25 mm` 위다. pick valid depth 1 mm는 기존 참조에서 가져온
후보일 뿐이다. thumb/index/middle/ring/pinky는 pad 크기와 궤적이 다르므로 hit corridor와 release/re-arm
거리를 각각 실측한다. 즉 **공통 y 영역 + agent별 x/z detector**가 최종 구조다.

## Isaac Gym 실측 기록

아래 수치는 2026-07-27 historical runtime audit 기록이다. 현재 코드와 checkpoint 계약이 바뀌었으므로
현재 학습 결과로 해석하지 않고, 필요하면 `python -m tab2body.train --task strike --smoke`로 재검증한다.

`tab2body/tools/audit_strike_runtime.py`가 실제 GPU PhysX 환경의
`G:string1..6`/`G:string*_end` body를 기타 로컬 좌표로 읽는다. 2026-07-27 결과:

- 6개 시작점과 끝점 모두 asset 값과 일치하고 finite
- `y=-0.325 m`에서 최소 인접 줄 간격 `9.639 mm`
- ready/exit across offset `3 mm`는 인접 간격 절반보다 작아 다른 줄을 먼저 넘지 않음
- A4에서 6개 env의 sampled lane `[-0.3473,-0.2957] m`, 모두 preferred 내부
- 넓은 역사적 `G:pluck_range` box의 사람 충돌만 비활성화하고 실제 기타 body/neck 충돌은 유지

좌표 전체는 2026-07-29 GPU audit JSON에 기록했던 역사 자료다. 해당 JSON은 정리되어 현재 저장하지
않으며, 2026-07-28에 `record_strike_visualized_rollout.py`와
`strike_visualization.py`를 추가했다. 이 진단 도구는 각 실제 줄 선분을 위 y 범위로 정확히
clip하고, allowed/preferred/current lane 및 `RH:pick` 가상점을 remembered/current 카메라 PNG에
투영한다. Isaac Gym 물리·충돌 geometry는 추가하지 않으며 기존 기본 영상도 덮어쓰지 않는다.

5,000-iteration 정책의 실제 결과는 다음 두 영상과 별도 metadata에 있다.

- [remembered zone/pick 영상](../training/runs/strike_5000_20260727_v2_fixed_a1/videos/strike_005000_rollout_remembered_zone_pick.mp4)
- [current zone/pick 영상](../training/runs/strike_5000_20260727_v2_fixed_a1/videos/strike_005000_rollout_current_zone_pick.mp4)
- [zone/pick metadata](../training/runs/strike_5000_20260727_v2_fixed_a1/videos/strike_005000_rollout_zone_pick.json)
