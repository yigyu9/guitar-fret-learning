# 왼팔 강성 단독 비교

세 조건은 같은 초기 자세, 기타 초기 위치·회전, 절대 스트랩 길이 1.1018469719600776 m, 목표각을 사용했습니다. 왼팔 12축의 stiffness만 기준의 1/1.5/2배로 바꾸고 damping은 모두 기준값(1배)으로 유지했습니다. 각 조건은 240 Hz에서 1200 step(5초) 실행했고, 분석은 7개 검사를 모두 통과했습니다. 초기 0.1초와 전체 5초 값을 따로 비교합니다.

| 조건 (kp, kd 배율) | 첫 0.1초 기타 최대 위치/회전 오차 | 5초 최대 위치/회전 오차 | 5초 종료 위치/회전 오차 | 종료 손 추적점 오차 | 종료 source 법선 간격 | 양의 raw palm λ가 기록된 step |
|---|---:|---:|---:|---:|---:|---|
| 기준 (1, 1) | 5.099 mm / 0.973° | 82.047 mm / 10.831° | 80.435 mm / 10.564° | 100.688 mm | +65.863 mm | 2 |
| 1.5배 (1.5, 1) | 7.629 mm / 1.265° | 246.612 mm / 76.100° | 236.592 mm / 73.508° | 294.220 mm | −101.071 mm | 1–3 |
| 2배 (2, 1) | 10.972 mm / 1.660° | 241.007 mm / 74.383° | 240.967 mm / 73.437° | 297.269 mm | −100.750 mm | 1–4 |

![세 조건에서 저장된 기타 위치·회전 오차와 source 법선 간격의 5초 추이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/palm_stiffness_only_curves.png)

곡선은 analyzer가 저장 raw에서 계산한 값입니다. 법선 간격은 움직이는 유한 패치의 투영값이므로 음수를 실제 관통 깊이로 해석하지 않습니다. 양의 raw λ 기록은 지정 step의 원시 접촉 계측이며, λ를 N으로 환산하거나 지속 지지력으로 읽을 수 없습니다. 따라서 접촉 step이나 위쪽 방향 proxy 위반 0회만으로 지지·안정 성공을 판정하지 않습니다. 실제 torso drift 최대값은 조건별 4.227° / 4.400° / 4.457°였고, 9개 목표는 유지된 값이므로 실제 자세 변화와 구분합니다. 세 조건 모두 `stability_success=false`입니다.

아래 2×3 이미지는 실제 Isaac Gym 카메라의 저장 프레임입니다. 윗줄은 각 조건의 전신 t=0, 아랫줄은 손 근접 t=5초를 보여줍니다. source-shape 재구성이 아니며, 물리 시뮬레이션을 다시 실행해 만든 영상도 아닙니다.

![각 조건의 실제 Gym 카메라 초기 전신 및 5초 손 근접 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/palm_stiffness_only_camera.png)

[기준 전체 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1/whole_body.mp4) · [기준 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1/hands.mp4) · [kp 1.5× 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1p5/whole_body.mp4) · [kp 1.5× 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1p5/hands.mp4) · [kp 2× 전신 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_2/whole_body.mp4) · [kp 2× 손 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_2/hands.mp4)

각 영상은 151장의 실제 Gym 프레임(0–5.0초, 30 fps)으로 만들어져 컨테이너 길이는 5.033초입니다. 시뮬레이션 길이는 5.0초입니다. 영상은 녹화 결과이며 안정성 인증은 아닙니다.

강성만 올린 조건은 초기 0.1초부터 기타 오차가 더 컸고, 장기 최대·종료 오차도 크게 악화됐습니다. kp 증가는 채택하지 않고 kp=1, kd=1을 기준으로 유지합니다. kd를 고정해 kp 효과를 비교했으며, kd를 독립적으로 바꾼 효과는 검증하지 않았습니다. 지지 유지나 연주 성공을 입증하지 않습니다. 다음 단계의 초기 자세·스트랩 검토는 상위 계획에 따릅니다.

재생성은 저장 데이터만 읽으며 출력 경로는 비어 있거나 존재하지 않아야 합니다.

```bash
MPLCONFIGDIR=/tmp/palm_stiffness_only_reproduction MPLBACKEND=Agg \
  python stability_adapter_2/make_palm_stiffness_only_artifacts.py \
  --out-dir /tmp/palm_stiffness_only_reproduction/artifacts
```

입력·producer·이미지 SHA256과 실제 그림에 표시된 6개 프레임은 [artifact manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts/artifact_manifest.json)에 기록했습니다. 실행 경로 및 종료 상태는 [artifact 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifact_execution.json)에 있습니다. manifest에 표시되지 않은 추가 6개 프레임 검증 입력도 포함됩니다. 이전 producer와 산출물은 [attempt 보존본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/artifacts_attempt_v1/) 및 [producer 사본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/producer_attempt_v1.py)에 남겼습니다. 각 조건의 초기 설정은 [kp=1 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1/initial_values.json), [kp=1.5 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_1p5/initial_values.json), [kp=2 초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/kp_2/initial_values.json)에 기록했습니다. 분석 원자료는 [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_stiffness_only_v1/analysis.json)이며, 기존 설정/실행 계획은 [단계 계획](/home/ajou/yigyu/3/stability_adapter_2/PALM_STIFFNESS_ONLY_PLAN.md)에서 확인할 수 있습니다.
