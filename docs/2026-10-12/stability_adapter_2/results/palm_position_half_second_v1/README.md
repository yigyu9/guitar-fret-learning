# 왼손 위치 task 0.5초 후속 비교

2026-10-07. 동일 승인 초기 설정의 PI, RATE_PI, PALM_RATE 각 120 physics steps(0.5초) 저장 결과를 비교한다. 기존 0.1초 prefix는 세 조건의 states/trace/controls/contacts/hands/queries/leg_torques가 모두 exact인 것으로 기록돼 있다. 그림 생성 과정에서 추가 native 실행·query나 설정 변경은 없었다.

## 비교 그림

![세 조건의 0.5초 source-goal 거리·기타 오차·팔 목표 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/artifacts/palm_position_half_second.png)

첫 panel은 매 query의 `left_source_world_m`와 `palm_goal_world_m` 간 world 거리, 가운데는 각 조건의 공유 +5 mm 기타 목표에 대한 위치·회전 오차, 마지막은 30개 `updated_before_step` 지점에서 전달된 팔 목표 변화다. 기타 위치·회전 곡선은 원자료 그대로 표시한다. 세 모드의 저장된 기타 상태 일치 여부는 비교 JSON에서 false로 기록됐으며, 곡선에 offset을 주지 않았다.

| 조건 | 0.5초 최대 왼손 source–goal 거리 (mm) | 최대 기타 위치오차 (mm) | 최대 기타 회전오차 (°) | 최대 팔 목표 변화/갱신 (rad) | 최대 실제 팔 관절 편차 (°) | 최대 native scalar-limit 초과 (°) | LH/RH contact 행 (120 completed steps) |
|---|---:|---:|---:|---:|---:|---:|---:|
| PI | 115.511587 | 35.481594 | 4.991597 | 0.023776919 | 12.576740 | 0.030300427 | 0 / 127 |
| RATE_PI | 115.675290 | 35.690658 | 5.005785 | 0.019999996 | 12.598617 | 0.030300427 | 0 / 97 |
| PALM_RATE | 90.540508 | 36.091149 | 4.761921 | 0.019999996 | 13.025394 | 0.030300427 | 0 / 135 |

PALM_RATE의 최대 source–goal 거리는 RATE_PI의 최대값보다 25.134781 mm 작았지만 90.540508 mm가 남았다. 같은 비교에서 기타 위치오차는 0.400491 mm 커지고 회전오차는 0.243864° 작아졌다. 이는 짧은 구간의 tradeoff이며 조건 채택이나 안정 연주 성공이 아니다. 접촉 행은 저장 completed-step contact records의 행 개수일 뿐 힘·접촉 원인·연속 지지 증거가 아니다.

모든 조건의 saved samples에서 upward-normal proxy 최솟값은 0.9268898이고 projection은 범위 내였다. 해부학적 방향, cooked clearance 또는 실제 지지를 인증하지 않는다. 실제 팔 좌표 변화는 최대 약 12.6–13.0°였고 native scalar-limit 초과 0.030300427°가 공통으로 남았다. 목표 변화율 제한은 실제 관절각 제한 통과를 뜻하지 않는다. 30회 target change는 매 60 Hz update의 실제 전달 벡터 변화이며 시간은 `(physics_step−1)/240`으로 표시했다. `controls.saturated`의 PI demand–applied mismatch는 active-bound count와 다른 값이다. RATE_PI와 PALM_RATE는 오른팔 제어 알고리즘은 같지만 기록된 전달 target vector는 최대 0.000629574 rad 달랐다.

0.5초 상태는 저장 당시 기타/관절 변화의 관측이다. 이 단계에서는 1초 실행을 하지 않았으며, 학습·연주 성공 판정이나 추가 조건 결정을 하지 않는다.

## 조건

PI는 기존 팔 관절 PI, RATE_PI는 양팔 final target에 update당 0.02 rad 제한, PALM_RATE는 왼팔 12관절 source-center 위치 task(배율 2, regularizer 0.05 m/rad)와 같은 오른팔 RATE_PI 알고리즘이다. 세 조건은 같은 초기 상태로 각 fresh 환경을 생성해 120 steps 실행했고, 첫 0.1초 원자료가 이전 결과와 같았다. 초기 q, strap rest length, PD/physics, root, 기타 목표를 유지했다. Torso9·finger42·C02 하체 PD 목표는 유지했지만 실제 자유 시뮬레이션 자세가 고정된 것은 아니다. 위치-task 계산 잔차는 저장된 실제 palm 이동과 별도로 해석한다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/palm_position_followup_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_position_followup.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1 \
  --out-dir /tmp/palm_position_half_second_reproduction
```

Plotter는 comparison의 6개 contract check, 21개 prior-prefix record, 138개 embedded SHA, 121개 states/trace/query/hands와 120개 control/contact records, 30개 update 시점을 확인한다. 기타 상태/trace 일치 여부는 raw data와 대조해 기록하는 관측이지 그림 통과 조건이 아니다. 이전 0.1초 producer와 output은 변경하지 않았다. Inputs, producer, output hashes 및 실행 기록은 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/artifacts/plot_manifest.json)와 [plot_execution_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_half_second_v1/plot_execution_v1.json)에 있다.
