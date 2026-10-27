# Palm Jacobian runtime cache–velocity 진단

2026-10-07. 동일 승인 PI 제어로 저장된 24 physics steps·25 Jacobian query를 요약한다. 좌우 palm row는 L17/R43, 각 query 행렬은 6×105 full-DOF Jacobian이다. 추가 제어나 native run 없이 `measurements/`와 `cache_comparison.json`만으로 그림을 생성했다. 기존 3초 run의 states, trace, controls 0.1초 prefix는 이번 run과 exact match다.

## 그림

![24-step 동안 좌우 palm Jacobian과 native velocity 잔차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1/artifacts_validated/palm_runtime_velocity_residuals.png)

그림은 step 1–24의 저장 query만 연결한다. `t=0` pre-refresh Jacobian buffer는 0이어서 표시하지 않았고, 초기 refresh 값은 직전 성공 초기 Jacobian과 exact match다. 매 후속 query의 pre-refresh Jacobian은 바로 앞 query에서 refresh한 값과 exact match였다. 이는 조회 시점/cache 동작 기록이며 모든 SDK/importer 또는 runtime control 의미를 일반 인증하지 않는다.

왼쪽 panel은 Jacobian cache의 pre-refresh와 refreshed 값을 full native DOF velocity에 곱해 COM 선속도를 예측한 residual, 가운데는 angular residual이다. 오른쪽은 refreshed Jacobian 예측과 native body linear velocity의 두 점 해석을 비교한다. COM 가설은 native linear velocity가 COM 속도라고 보고, origin 가설은 body-origin 속도로 해석해 `v_native + ω × (COM − origin)`으로 COM 속도로 옮긴 residual이다. 이는 Jacobian의 기준점을 바꿔 비교하는 것이 아니다. report에는 source-hull center 점의 residual도 별도 저장되어 있다. 이는 native body linear/angular velocity에서 rigid-point 식 `v + ω × (p_source − p_COM)`으로 계산한 대조값이지 source point velocity를 따로 native 측정한 것은 아니다. 이 도출값은 세 panel의 curve에는 포함하지 않았다.

| Palm | Jacobian 시점 | COM 선속도 오차 max (mm/s) | 각속도 오차 max (rad/s) | native velocity를 origin으로 해석 후 COM 변환한 선속도 오차 max (mm/s) |
|---|---|---:|---:|---:|
| LH | pre-refresh | 4.781572 | 0.002632 | 65.566518 |
| LH | refreshed | 1.500569 | 0.001591 | 68.134978 |
| RH | pre-refresh | 1.692057 | 0.006329 | 50.047692 |
| RH | refreshed | 1.371527 | 0.004354 | 49.273723 |

반복 조회 중 t=0 pre-refresh buffer는 zero였고 초기 refresh는 이전 저장 Jacobian과 같았다. 각 physics step 뒤 다음 refresh 전 cache 값은 직전 query의 refreshed 값이었다. 즉 query 전 refresh가 필요한 cache 동작이 관찰됐다. Refresh 후 오차도 0은 아니며, 이 0.1초 관찰은 full SDK Jacobian 계약, DOF velocity 의미 전반 또는 모든 실행 시점의 일치를 증명하지 않는다.

실행은 24 physics steps였고 `report.json`의 9 checks/71 embedded input SHA, `cache_comparison.json`의 3 checks/75 embedded input SHA가 모두 통과했다. 초기화·상태/target/PD 보존과 3초 run prefix 검사가 통과했지만 기타는 종료 위치 오차 6.874401 mm, 회전 오차 1.519676°로 목표에 남아 있다. 안정성 성공, 지속 지지, 신규 손 위치 controller 적합성을 인증하지 않는다. Palm source hull center는 접촉점이나 해부학적 점이 아니다.

## 재생성 및 provenance

```bash
python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_runtime.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_runtime_v1 \
  --out-dir /tmp/palm_jacobian_runtime_reproduction
```

Plotter는 raw report/cache checks, 71/75 embedded SHA, 25개 연속 query와 query 보존 상태를 확인하고 비어 있지 않은 출력 폴더를 덮어쓰지 않는다. `artifacts_validated/plot_manifest.json`에는 실제 소비 JSON, embedded input SHA, producer와 출력 PNG SHA가 따로 기록된다. 원자료는 `measurements/{report,queries,states,trace,controls}.json`, cache 대조는 `cache_comparison.json`, run 기록은 `native_execution.json` 및 `native_run.log`다. 계측 범위는 [PALM_JACOBIAN_RUNTIME_CHECK.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_JACOBIAN_RUNTIME_CHECK.md:1)에 있다.
