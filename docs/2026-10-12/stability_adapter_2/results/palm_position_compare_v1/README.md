# 왼손 위치 task 0.1초 저장 결과 비교

2026-10-07. 사용자가 승인한 세 조건을 각 24 physics steps(0.1초) 실행한 저장 데이터를 읽어 비교했다. 그림과 표는 `comparison.json` 및 mode별 `trace.json`, `queries.json`, `controls.json`, `report.json`을 사용한다. 이 산출물 생성 과정에서 추가 native 실행·query는 하지 않았다.

## 비교 그림

![PI, RATE_PI, PALM_RATE의 왼손 위치 오차·기타 오차·최종 팔 목표 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1/artifacts/palm_position_compare.png)

첫 panel은 같은 query의 `left_source_world_m`와 `palm_goal_world_m` 간 거리, 두 번째와 세 번째는 trace의 기타 위치·회전 오차다. 마지막 panel은 6개 `updated_before_step` control에서 직전 전달 팔 목표 벡터 대비 현재 `final_arm_targets_rad`의 최대 절대 성분 변화를 표시한다. 첫 변화 기준은 `initial_joint_targets_rad[arm_indices]`이고 표본 시간은 `(physics_step−1)/240`이다. 기타 위치·회전 오차 trace는 세 조건에서 저장값이 정확히 같아 그림에서도 같은 선을 겹쳐 그렸으며 시각 offset을 주지 않았다.

| 조건 | 0.1초 최대 왼손 source–goal 거리 (mm) | 기타 위치오차 (mm) | 기타 회전오차 (°) | 최대 팔 목표 변화/갱신 (rad) | 6회 갱신의 active-bound 축 수 |
|---|---:|---:|---:|---:|---|
| PI | 48.561228 | 6.874401 | 1.519676 | 0.023776919 | 2, 0, 1, 1, 0, 0 |
| RATE_PI | 48.835811 | 6.874401 | 1.519676 | 0.019999996 | 2, 1, 3, 2, 0, 0 |
| PALM_RATE | 47.473935 | 6.874401 | 1.519676 | 0.019999996 | 2, 1, 3, 2, 1, 1 |

PALM_RATE의 최대 source–goal 거리는 RATE_PI보다 1.361875 mm 작았지만 0.1초 뒤에도 47.473935 mm였다. 기타 위치·회전 오차는 세 저장 trace에서 정확히 동일해 이 진단에서 기타 유지 개선은 관찰되지 않았다. 24-step 로그의 왼손·오른손 contact 행은 각각 세 조건 모두 0이다. 접촉 행 수는 지지력·접촉 원인·지속 지지를 나타내지 않는다.

세 조건 모두 saved samples 전체에서 upward-normal proxy의 최솟값은 0.9268898이었고, proxy 기준 위쪽 값이 유지됐다. 이 normal의 해부학적 부호는 검증되지 않았다. 실제 팔 관절 최대 좌표 편차는 PI/RATE_PI/PALM_RATE 순으로 5.832434°/5.881556°/5.942037°이고 native scalar limit 초과는 세 조건 모두 최대 0.030300427° 남았다. 이 수치들은 제어 출력과 관절 상태 기록이지 연주 안정성 인증이 아니다.

## 조건과 해석 범위

PI는 기존 팔 관절 PI다. RATE_PI는 양팔의 최종 목표를 60 Hz update마다 최대 0.02 rad씩 제한한다. PALM_RATE는 RATE_PI와 같은 오른팔 제어 알고리즘에 왼팔 12관절 source-center 위치 task를 더한다(위치 배율 2, regularizer 0.05 m/rad). 두 모드의 오른팔 target vector 자체가 같다는 뜻은 아니다. 공통 초기 q, strap rest length, native PD, 기타 목표와 physics 설정을 유지했고 humanoid root는 고정했다. Torso9, finger42, C02 하체의 PD 목표도 유지했으며 자유 시뮬레이션 중 실제 자세가 고정됐다는 뜻은 아니다. 표시된 target change는 실제 전달된 팔 목표의 갱신 간 차이며 `controls.saturated`의 PI demand–applied mismatch와 구분된다. active-bound 축 수는 표의 별도 comparison 필드다.

PALM_RATE의 위치 task 계산 잔차는 마지막 갱신에서 약 0.689 mm였지만 저장된 실제 source-center–goal 최대 거리는 47.473935 mm였다. 선형 목표 계산 잔차는 실제 물리 응답과 구별하며, 차이를 drive 원인으로 단정하지 않는다. 결과는 승인된 초기 0.1초 세 조건의 비교다. contact, 물리 지지, 기타 유지 성공, 안정 연주를 입증하지 않는다. 비교 설계와 제한은 [PALM_POSITION_COMPARISON.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_COMPARISON.md:1) 및 [PLAN.md §48](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:910)에 기록한다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/palm_position_compare_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_position_compare.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1 \
  --out-dir /tmp/palm_position_compare_reproduction
```

Plotter는 comparison의 5개 check와 103개 embedded SHA를 확인하고 기록된 guitar-state coincidence boolean을 raw states와 대조한다. Trace coincidence는 관측으로 manifest에 남기며, 값이 달라도 raw curves를 그린다. 비어 있지 않은 output directory는 덮어쓰지 않는다. Inputs, producer, output hashes는 [plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_position_compare_v1/artifacts/plot_manifest.json)에 기록했다.
