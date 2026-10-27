# Palm task local axis authority 요약

2026-10-07. Saved `authority.json`의 25개 연속 query 표본에서 계산된 왼손 위치 보정 필요량과 기존 관절 delta box의 독립 축별 선형 범위를 그렸다. 새 rate limit은 포함하지 않았으며, 이번 산출물 과정에서 native 실행이나 제어 변경은 하지 않았다.

## 그림

![0.1초 저장 query별 XYZ 요구 보정과 축별 선형 범위](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_task_authority_v1/artifacts_validated/palm_axis_authority.png)

빨간 선은 저장된 `p_goal − p_current` world displacement이고, 파란 band는 각 저장 시점의 `A(q_actual)`와 기존 delta box에서 얻은 독립 world-axis 선형 interval이다. 각 시점의 A는 3×12 위치 map이며, 선형화 기준은 local이지만 표시 좌표는 world XYZ다. 값은 m에서 mm로 변환했다. 세 panel은 동일 0–0.1초 run의 저장 시점을 연결한다.

| 축 | 필요한 보정 곡선 범위 (mm) | 시간별 band의 전체 envelope (mm) | 모든 표본에서 공통인 축별 interval (mm) |
|---|---:|---:|---:|
| X | −9.389475 … 0.000000 | −273.475625 … 257.189165 | −269.120600 … 252.855618 |
| Y | 0.000000 … 23.138609 | −122.555638 … 126.370631 | −117.793412 … 85.442164 |
| Z | 0.000000 … 41.648954 | −187.808828 … 168.858346 | −144.076931 … 141.586645 |

25개 모든 저장 시점에서 각 축의 필요값은 해당 시점의 독립축 interval 안에 있었다. Step 24의 singular values는 내림차순 `0.653877653 / 0.619258465 / 0.203808618 m/rad`다. 이 결과는 기존 delta box의 축별 선형 범위만으로 보정을 배제할 근거가 없다는 관찰이다. 축별 interval은 다른 축을 따로 계산한 범위이므로, 세 좌표를 한 delta 조합으로 동시에 만들 수 있다는 보증이 아니다. Full nonlinear FK, 관절 조합 도달성, 접촉, drive의 유효성, 기타 안정성도 검증하지 않는다.

계산은 각 저장 시점의 `q_actual`에서 구성한 왼팔 3×12 위치 map `A`를 사용하고, 기존 `±0.15 rad ∩ C02 ±0.3 rad ∩ native joint box`에서 좌표별 extremum을 산출했다. 새 변화율 제한은 적용하지 않았다. `authority.json`의 3개 check와 embedded input 76개 SHA는 통과했다. 이 그림은 위치 task/controller의 승인이나 구현, 성공 기준을 의미하지 않는다.

## 재생성 및 provenance

```bash
python /home/ajou/yigyu/3/stability_adapter_2/plot_palm_task_authority.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_task_authority_v1 \
  --out-dir /tmp/palm_task_authority_reproduction
```

Plotter는 3개 check, 25개 순서가 맞는 record, 76개 embedded SHA를 확인하고 비어 있지 않은 출력 폴더를 덮어쓰지 않는다. 축별 containment는 강제 입력 검사가 아니라 기록된 관찰값이며, 이번 자료에서는 25/25 시점이 각자의 interval 안에 있다. 최종 그림과 manifest는 `artifacts_validated/`에 있다. 첫 legend 배치 초안은 `artifacts/`, `artifacts_v1/`에 보존했다. 입력·producer·출력 SHA는 `artifacts_validated/plot_manifest.json`을 참조한다.

분석 범위와 결과는 [PALM_TASK_AUTHORITY.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_TASK_AUTHORITY.md:17), [PLAN.md §46](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:891), [프로젝트 요약](/home/ajou/yigyu/3/stability_adapter_2/README.md:159)에 있다. 다음 비교안은 [PALM_POSITION_COMPARISON.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_POSITION_COMPARISON.md:78)에 적혀 있지만 아직 별도 확인 전이며 controller는 구현되지 않았다.
