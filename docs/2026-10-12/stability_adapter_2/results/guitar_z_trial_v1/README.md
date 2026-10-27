# Guitar initial Z +5 mm paired native diagnostic

작성일: 2026-10-06. 사용자가 승인한 기타 초기 world Z +5 mm를 baseline H0와 짝지어, 각 조건을 240 Hz에서 24 physics steps(0.1초) 실행한 결과를 비교한다. 사람 초기 각도/root, held joint targets와 PD/solver 설정, 기타 회전, 절대 strap rest length는 동일하다. +5 mm trial은 후보 목표 높이에 대한 기타 위치 오차와 공통 원본 H0 위치 목표에 대한 별도 오차를 모두 기록했다.

## 초기 source geometry와 native trace

| 초기 조건 | 초기 source negative pair (1,404 human–guitar pairs) | R_Hip gap (mm) | R_Elbow gap (mm) | 초기 route (m) | absolute rest length (m) |
|---|---:|---:|---:|---:|---:|
| H0 | 1 | −1.331165 | 7.154318 | 1.089185175 | 1.089185175 |
| 기타 Z +5 mm | 0 | +3.302684 | 4.208398 | 1.083374167 | 1.089185175 |

![초기 source collision shapes at saved t=0 poses: H0와 기타 Z +5 mm 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_source_geometry_t0.png)

그림은 saved native t=0 body pose를 CPU source collision geometry로 재구성했다. 회색은 humanoid, 파랑은 기타, 빨강은 source query에서 음수 gap이 포함된 형상이다. 이것은 Isaac Gym renderer나 PhysX cooked-mesh 그림이 아니다. source signed gap 음수 크기는 보정된 침투 깊이가 아니며 cooked clearance 또는 전체 장면 clearance를 인증하지 않는다. +5 mm에서 guitar-human source pair 음수가 없어도 발-바닥 겹침/접촉 후보는 별도로 남았다.

![paired H0와 기타 Z +5 mm native diagnostic의 위치·회전 오차 및 strap route 시계열](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_timeline.png)

| 지표 | H0 | 기타 Z +5 mm |
|---|---:|---:|
| 최대 위치 오차: 각 조건의 candidate goal 기준 (mm) | 65.315253 | 63.033062 |
| 최대 위치 오차: 공통 원본 H0 goal 기준 (mm) | 65.315253 | 65.348676 |
| 최대 회전 오차 (°) | 7.318146 | 7.320381 |
| 최대 하체 raw angle drift (°) | 107.804858 | 107.783636 |
| 최대 torso drift (°) | 1.092551 | 1.092557 |
| 초기 strap route (m) | 1.089185175 | 1.083374167 |
| absolute rest length (m) | 1.089185175 | 1.089185175 |
| 기록된 applied strap tension 최대값 (N) | 0 | 0 |

후보 goal 기준으로는 +5 mm run의 최대 위치 오차가 약 2.282 mm 낮았지만, 원본 H0 goal 기준 오차는 65.348676 mm로 H0의 65.315253 mm보다 약간 컸다. 최대 회전 오차도 +5 mm run이 0.002235° 높다. 위치 오차 곡선은 각 trial goal 기준과 공통 원본 H0 goal 기준을 분리해 보여준다. +5 mm의 초기 route는 공통 `L_A=1.0891851746440693 m`보다 5.811 mm 짧다. Strap feedback은 없고 기록된 applied tension은 두 run 모두 24 physics steps 동안 0 N이다.

Native contact 기록에서는 H0의 첫 completed step에서 `guitar/G:body × human/R_Hip` contact row가 있었고 +5 mm run의 첫 completed step에는 기타-human contact가 없었다. 그러나 두 조건 모두 0.05 s (step 12)에 raw body labels `guitar/guitar × human/L_Knee` contact가 기록됐다. 두 조건의 첫 completed step에는 동일한 발-바닥 raw feature gap도 있었다: R_Ankle −9.690888 mm, R_Toe −8.885874 mm. 이들은 native contact feature 값이며 calibrated penetration depth나 clearance가 아니다. 기타/R_Hip의 첫-step 접촉 감소는 전체 접촉 제거 또는 정지 안정 성공을 의미하지 않는다.

## 해석 범위와 원자료

이 paired trial에서 source query 음수 guitar-human pair 수는 1에서 0으로 줄었지만, native 목표 오차·회전 오차·하체 drift·무릎 contact가 남았다. 따라서 이 결과는 초기 배치/접촉 후보 개선이며 정지 안정성 성공이나 첫 policy model 선정을 뜻하지 않는다. 더 의미 있는 다음 단계는 +5 mm로 올린 후보 기타 목표를 고정하고 초기 발 겹침과 lower-pose hold를 먼저 다루며, 원본 공통 위치 목표에 대한 오차도 계속 기록하는 것이다. 기존 상체 66개와 몸통 9개 PD, root, solver, strap 길이는 유지한다. 하체 q 보정이나 joint 표현 변경은 별도 중요 결정 검토 전에는 적용하지 않는다.

원자료: [paired comparison JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/comparison.json), [H0 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/report.json), [+5 mm report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/report.json), [H0 초기 source query](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/initial_source_geometry.json), [+5 mm 초기 source query](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/initial_source_geometry.json), [보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/protected_validation.json), [17-test log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/tests.log). Comparison checks pass; H0 saved states, contacts, and all historical trace fields reproduce exactly.

Plot 재생성은 repository root에서 다음처럼 실행한다. 이는 JSON/저장 상태를 읽는 그림 작업이며 물리 trial을 실행하지 않는다.

```sh
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib MUJOCO_GL=disable MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib MPLBACKEND=Agg /home/ajou/miniconda3/envs/rl38/bin/python -m stability_adapter_2.plot_guitar_z_trial --results-root /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1 --output-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images
```

Run input `lower_kd0_h0.json`라는 파일명과 달리 H0 report의 diagnostic preset은 `baseline`이다. 파일명에서 하체 damping=0 trial로 오해하지 않는다. 이전 comparison 후처리는 historical `leg_torques.json` 부재로 한 번 실패했으며 [실패 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/comparison_failed_missing_historical_torques.log)에 보존했다. 이후 완성된 comparison 검사는 통과했다. 별도 change-reviewer 검수를 통과했다. 17개 테스트와 두 native run의 전체 상태·접촉·trace가 독립 재현됐고 두 그림도 픽셀까지 일치했다. 후처리 재시도의 기존 geometry 보존 검사도 통과했으며 남은 지적은 없다. [검수 기록](review.md), [변경 파일·실제 줄 번호](CHANGED_FILES.md).
