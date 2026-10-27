# 상체 자세와 strap parameter native diagnostic

작성일: 2026-10-06. 부모 Sol의 raw-log 분석 결과를 시각화·정리한 33 native-run 비교다. 이 작업은 결과 해석을 새로 선택하거나 후보를 채택하지 않는다. 사용 원자료는 `comparison_v2.json`이며 이전 v1 comparison의 contact group 의미 모호성을 바로잡은 후속 파일이다. `plot_manifest.json`은 플롯 코드·헬퍼·mesh/assets·comparison 및 읽은 trace/state 입력의 SHA-256을 기록한다.

## 범위와 공통 조건

모든 trial에서 하체 초기 자세 및 하체 물리는 그대로 실행했다. 표와 이번 비교 목적에서 하체는 관찰 전용으로 두고 평가 점수에서 제외했으며, 상체/손과 strap의 변화를 본다. guitar target, humanoid root, torso9 목표 및 PD/solver 등 나머지 허용 조건은 비교 입력 audit로 고정됐다. 별도 active strap, feedback, 하체 변경은 없다.

비교는 0.1 s strap 조건 5개, 0.1 s upper-joint set 17개(reference 1개와 ±0.025 rad perturbation 16개), 0.5 s 유지 7개, 1.0 s 유지 4개다. 33개 run의 per-run invariant/runtime audit가 모두 통과했다. 비교 검증에서 legacy가 c02를 exact 재현, 0 N route-match reference가 exact 재현됐고 long-run prefix가 short-run과 재현 일치했다. 이는 setup과 후처리의 consistency를 뜻하며 물리적 성공을 뜻하지 않는다.

0.1 s 기준 route-match는 초기 계산 strap route 1.0833741669597394 m와 동일한 absolute rest length다. legacy는 1.0891851746440693 m를 유지한다. 20 N preload 조건의 오차는 short run에서 오히려 더 컸다. 단위 없는 별도 승압 또는 활성제어는 하지 않았다.

## 0.1 s strap 조건 (5 runs)

각 오차는 저장 trace 전체에서의 최대값이다. strap tension은 trace의 기록된 applied value다.

|Run / horizon|Condition|Rest L (m)|Max position error (mm)|Max rotation error (°)|Max applied tension (N)|
|---|---|---|---|---|---|
|0.1 s · legacy|legacy LA=1.089185 m|1.089185|7.174|1.591|0.000|
|0.1 s · load_00n|route-match LA=1.083374 m|1.083374|6.845|1.520|8.017|
|0.1 s · load_05n|preload 5 N, LA=1.082541 m|1.082541|6.817|1.581|8.791|
|0.1 s · load_10n|preload 10 N, LA=1.081708 m|1.081708|6.970|1.731|10.000|
|0.1 s · load_20n|preload 20 N, LA=1.080041 m|1.080041|7.821|2.226|20.000|

## 0.1 s upper-joint set (17 runs)

모든 조건은 route-match length 1.0833741669597394 m였다. 기준 reference 1개와 baseline 대비 상체 단일 관절만 ±0.025 rad 바꾼 16개 조건이다.

|Run / horizon|Condition|Max position error (mm)|Max rotation error (°)|Max applied tension (N)|nonleg guitar contact rows|
|---|---|---|---|---|---|
|0.1 s · L_Elbow_x_minus|L_Elbow_x −0.025 rad|6.840|1.519|8.008|0|
|0.1 s · L_Elbow_x_plus|L_Elbow_x +0.025 rad|6.846|1.520|8.027|0|
|0.1 s · L_Shoulder_x_minus|L_Shoulder_x −0.025 rad|6.842|1.519|7.940|0|
|0.1 s · L_Shoulder_x_plus|L_Shoulder_x +0.025 rad|6.838|1.519|8.093|0|
|0.1 s · L_Thorax_y_minus|L_Thorax_y −0.025 rad|6.825|1.595|8.970|0|
|0.1 s · L_Thorax_y_plus|L_Thorax_y +0.025 rad|6.950|1.533|18.174|0|
|0.1 s · L_Wrist_y_minus|L_Wrist_y −0.025 rad|6.842|1.520|8.016|0|
|0.1 s · L_Wrist_y_plus|L_Wrist_y +0.025 rad|6.840|1.519|8.019|0|
|0.1 s · R_Elbow_x_minus|R_Elbow_x −0.025 rad|6.849|1.521|8.004|0|
|0.1 s · R_Elbow_x_plus|R_Elbow_x +0.025 rad|6.839|1.519|8.030|0|
|0.1 s · R_Shoulder_x_minus|R_Shoulder_x −0.025 rad|6.843|1.519|7.977|0|
|0.1 s · R_Shoulder_x_plus|R_Shoulder_x +0.025 rad|6.841|1.520|8.058|1|
|0.1 s · R_Thorax_y_minus|R_Thorax_y −0.025 rad|6.838|1.519|8.081|0|
|0.1 s · R_Thorax_y_plus|R_Thorax_y +0.025 rad|6.843|1.519|7.954|0|
|0.1 s · R_Wrist_y_minus|R_Wrist_y −0.025 rad|6.849|1.521|8.018|0|
|0.1 s · R_Wrist_y_plus|R_Wrist_y +0.025 rad|6.849|1.521|8.016|0|
|0.1 s · reference|route-match reference|6.845|1.520|8.017|0|

`nonleg_guitar_contact_row_count`는 다리 이외의 모든 body 접촉 row를 포함하며 pelvis/torso와 양팔·손을 포함한다. 이는 접촉 힘이 아니며 상체/손 지지를 판정하지 않는다. 17개 run의 max position error 범위는 6.825–6.950 mm, 회전 error는 1.519–1.595°였다. 이 제한된 0.1 s 구간에서 개별 상체 관절 변경 효과는 작았다. `nonleg` contact row 한 건은 R_Shoulder_x +0.025 rad 조건에서 기록됐다. 이는 접촉 힘이나 안정적인 손 지지를 증명하지 않는다.

## 장시간 유지 결과

|Run / horizon|Condition|Rest L (m)|Max position error (mm)|Max rotation error (°)|Max applied tension (N)|nonleg guitar contact rows|
|---|---|---|---|---|---|---|
|0.5 s · L_Shoulder_x_minus|L_Shoulder_x −0.025 rad|1.083374|58.591|8.919|15.216|0|
|0.5 s · L_Shoulder_x_plus|L_Shoulder_x +0.025 rad|1.083374|58.305|8.926|15.507|0|
|0.5 s · legacy|legacy LA=1.089185 m|1.089185|64.915|9.175|23.394|0|
|0.5 s · load_05n|preload 5 N, LA=1.082541 m|1.082541|56.796|8.797|14.546|0|
|0.5 s · load_10n|preload 10 N, LA=1.081708 m|1.081708|55.221|8.754|14.955|0|
|0.5 s · load_20n|preload 20 N, LA=1.080041 m|1.080041|51.079|8.618|20.173|0|
|0.5 s · reference|route-match reference|1.083374|58.452|8.923|15.379|0|

0.5 s reference는 58.452 mm/8.923°였고, legacy는 64.915 mm/9.175°였다. L_Shoulder_x +0.025/−0.025 rad 조건은 각각 58.305/8.926°와 58.591/8.919°였다. preload 20 N은 51.079 mm/8.618°로 이 구간의 위치/회전 오차를 줄였지만 유지 성공 판정은 아니다. 0.5 s hold 7개 모두 nonleg guitar contact row는 0이었다. 0.1 s upper-joint set에서는 R_Shoulder_x +0.025 rad 한 조건에서 R_Elbow row 1건이 있었다. 0.5 s 이하에서 LH/RH 손 body contact row는 없었다. 고정 torso9 목표의 실제 raw drift는 0.1 s set에서 1.090–1.095°, 0.5 s set에서 2.663–2.668°, 1.0 s set에서 3.477–3.580°였으며 기타/손 평가와 별도로 관찰했다.

|Run / horizon|Condition|Rest L (m)|Max position error (mm)|Max rotation error (°)|Max applied tension (N)|nonleg guitar contact rows|
|---|---|---|---|---|---|---|
|1 s · legacy|legacy LA=1.089185 m|1.089185|218.603|36.360|23.394|65|
|1 s · load_10n|preload 10 N, LA=1.081708 m|1.081708|241.875|61.609|14.955|0|
|1 s · load_20n|preload 20 N, LA=1.080041 m|1.080041|200.537|75.128|23.796|6|
|1 s · reference|route-match reference|1.083374|253.897|52.862|15.379|0|

1 s에서 route-match reference는 253.897 mm/52.862°, legacy는 218.603 mm/36.360°, 10 N preload는 241.875 mm/61.609°, 20 N preload는 200.537 mm/75.128°였다. 위치 오차가 일부 낮아진 조건도 회전 오차가 매우 커졌고 모든 조건은 지속 유지에 실패했다. 1초 comparison의 nonleg contact rows는 legacy의 RH:thumb3 65건, preload20의 Pelvis 6건이며 route-match/10N은 0건이었다. 이 row 수는 힘이나 손의 안정 지지를 나타내지 않는다.

## 손·기타·strap geometry 그림

![strap short traces와 0.5/1초 유지 trace의 기타 위치·회전오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/images/pose_strap_v1_native_curves_v2.png)

![reference의 t=0, 0.5, 1.0초 저장 pose에서 기타, 양손, strap route 및 palm-normal proxy](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/images/pose_strap_v1_reference_geometry_v2.png)

geometry panels는 reference run의 저장된 native state (step 0/120/240)에서 CPU source convex collision shape를 재구성했다. 파랑은 기타, 초록/자홍은 왼손/오른손 source hand shape, 회색은 나머지 humanoid, 점선은 저장 native trace의 strap route다. 화살표는 손가락/wrist vector에서 계산한 palm normal proxy이며 anatomical sign은 검증되지 않았다. 이는 Isaac Gym/PhysX renderer가 아니고 cooked mesh clearance나 실제 손 지지 판정도 아니다. route와 geometry는 저장 pose에서 설명용으로 배치한 것이다.

초기 LH palm convex-hull centroid는 해당 넥 단면 하단보다 82.533 mm 아래였고 normal proxy `palm_up_dot=0.869692`였다. 초기 source human-guitar query 음수 pair는 0이었다. 이 proxy와 초기 query는 hand-on-guitar 접촉 또는 하중 지지를 의미하지 않는다. 0.5 s까지 양손/guitar native contact row가 없으며, 1 s의 thumb/pelvis contact rows 역시 안정적인 지지나 지속 hold를 입증하지 않는다. torso9의 실제 drift는 계속 별도 측정됐다.

그림은 저장 comparison/trace/state와 source collision geometry만 읽어 생성했다. 재생성은 새 출력 경로로 실행한다. plotter는 기존 output 또는 manifest를 덮어쓰지 않고 오류로 중단한다.

```bash
cd /home/ajou/yigyu/3
PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3 \
LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib MUJOCO_GL=disable \
MPLCONFIGDIR=/tmp/stability_adapter_2_matplotlib MPLBACKEND=Agg \
/home/ajou/miniconda3/envs/rl38/bin/python stability_adapter_2/plot_pose_strap.py \
  --comparison docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/comparison_v2.json \
  --results-dir docs/2026-10-12/stability_adapter_2/results/pose_strap_v1 \
  --curve-output /tmp/pose_strap_curves_fresh.png \
  --geometry-output /tmp/pose_strap_geometry_fresh.png \
  --manifest /tmp/pose_strap_manifest_fresh.json
```

이번 결과는 긴 시간에서 오차가 증가해 지속 안정/최종채택으로 볼 수 없다. 이 문서는 요청된 산출물 단위이며, 다음 탐색 승인이나 후보 선택은 포함하지 않는다.
