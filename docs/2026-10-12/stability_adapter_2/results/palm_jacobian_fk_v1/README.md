# Palm Jacobian–fresh FK 좌표 대조

2026-10-07. 이 산출물은 12개의 왼팔 초기 관절 좌표 변화에 대한 saved native Jacobian과 fresh zero-step FK 차분의 오차를 요약한다. 10개 중앙 차분과 경계 one-sided 2개, baseline 1개로 총 23개 fresh 초기 query를 비교했다. 이 문서와 그림 생성에서는 추가 native query나 제어·설정 변경을 하지 않았다.

## 그림

![초기 왼팔 관절군별 raw 및 좌표 보정 오차](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1/artifacts_validated/palm_fk_coordinate_errors.png)

세 panel의 막대는 Thorax·Shoulder·Elbow·Wrist 각 관절군에서 x/y/z 차분 오차 norm의 최댓값이다. 위치 오차 JSON 단위 m/rad 값은 그림에서 mm/rad로 변환했고, 각도 오차는 rad/rad로 표시한다. 세로축은 로그 스케일이다. 왼쪽은 palm COM 위치 차분, 가운데는 각도 차분, 오른쪽은 source hull volume center 위치 차분을 나타낸다. 세 번째 panel은 expmap tangent를 적용한 뒤 선형 Jacobian의 기준점을 body origin으로 가정해 source center로 옮긴 경우와 COM 기준으로 옮긴 경우를 비교한다.

| 최대 오차 지표 | Raw native Jacobian | 보정 후 | 단위 |
|---|---:|---:|---|
| Palm COM 위치 | 0.215649087 | 0.000275001 | m/rad |
| 각도 | 0.678072945 | 0.000194957 | rad/rad |
| Source center: tangent 적용 후 body-origin 기준 | — | 0.042214636 | m/rad |
| Source center: tangent + COM 기준 이동 | — | 0.000274299 | m/rad |

좌표 기반 exponential-map 좌표의 left tangent를 native angular/linear Jacobian에 적용하면 이 초기 자세의 FK 차분과 오차가 크게 줄었다. 하지만 source-center 오차는 tangent 보정 후 선형 Jacobian의 기준점을 body origin으로 가정해 source center로 옮기면 최대 0.042214636 m/rad로 남는다. COM 기준 이동까지 반영한 값은 0.000274299 m/rad다. Source center는 source convex-hull의 체적 중심이며 표면 접촉점·해부학적 중심·native COM을 뜻하지 않는다.

Raw 비교 JSON의 6개 계약 검사와 12행별 검사가 모두 통과했고 embedded input 93개 SHA를 확인했다. 좌표 보정 JSON의 3개 검사와 embedded input 98개 SHA도 통과했다. 이 그림의 앞선 단위 표시 초안은 `artifacts/`와 `artifacts_v1/`에 보존했고, 해당 plotter source는 `source_plot_attempt/plot_palm_fk_coordinates.py`에 저장했다. 위치축을 JSON 값에 맞게 mm/rad로 고친 그림은 `artifacts_validated/`에 있다. 결과는 현재 초기 자세·선택한 좌표 변화에 대한 경험적 대조다. SDK 예제의 spherical position expmap 구현은 참고 근거일 뿐 이 프로젝트 importer 전체의 동작 증명은 아니다. 이 결과만으로 native DOF velocity 의미, 모든 자세에서의 Jacobian, runtime 제어, 안정성 또는 접촉을 인증하지 않는다.

## 재생성 및 입력 기록

```bash
python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_fk_coordinates.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_jacobian_fk_v1 \
  --out-dir /tmp/palm_jacobian_fk_reproduction
```

Plotter는 raw comparison과 `coordinate_comparison.json`의 전체 검사, 행 대응, 93/98개 embedded input SHA를 확인하고 비어 있지 않은 결과 폴더를 덮어쓰지 않는다. 입력·plotter·PNG SHA는 `artifacts_validated/plot_manifest.json`에 기록했다. 최종 canonical PNG와 새 `/tmp` 재생성본은 픽셀 단위로 일치했다. 최초 저장 시도와 serialization 오류 이력은 `failed_execution.json`, `native_execution.json`, `native_run.log`, `native_validated_run.log`, `source_attempt/`에 보존되어 있다. 계측 계획은 [PALM_JACOBIAN_FK_CHECK.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_JACOBIAN_FK_CHECK.md:1)에 있다.
