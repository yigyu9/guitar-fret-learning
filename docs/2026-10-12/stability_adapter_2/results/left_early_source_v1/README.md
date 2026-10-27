# 초기 왼손–기타 근접 저장 자료

2026-10-07. 기존 3초 실행에서 저장된 7개 시점(0–0.1초)의 JSON 측정값과 step 0/24 source triangle snapshots를 그렸다. 이 산출물을 위해 native 실행이나 제어 변경은 추가하지 않았다.

## 측정 그림

![초기 왼손 source 거리, 별도 signed query, normal proxy 및 neck 높이](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/left_early_source_measurements.png)

| 저장 step | 시간 (s) | unsigned source-hull 거리 (mm) | backend signed query (mm) | palm normal world-Z proxy | local neck 아래 상대 높이 (mm) |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.000000 | 0.545306 | 0.167218 | 0.926890 | −24.728 |
| 1 | 0.004167 | 0.610046 | 0.269675 | 0.927441 | −25.007 |
| 2 | 0.008333 | 5.109051 | 5.104413 | 0.929119 | −29.862 |
| 4 | 0.016667 | 6.983490 | 6.983615 | 0.933804 | −32.433 |
| 8 | 0.033333 | 13.071000 | 13.055504 | 0.943814 | −39.468 |
| 12 | 0.050000 | 19.216691 | 19.216794 | 0.952457 | −46.303 |
| 24 | 0.100000 | 29.787930 | 20.000000* | 0.965232 | −57.601 |

`source_hull_distance_m`는 source convex-hull의 unsigned witness 거리다. `backend_signed_gap_20mm_cutoff_m`는 별도 backend query이며 마지막 20 mm 값은 cutoff에 걸려 기록된 값이지 측정된 실제 간격이 아니다. 두 query는 처음부터 값이 다르고, 마지막 표본에서도 같은 척도의 수치처럼 등치할 수 없다. 음수 크기를 cooked 관통 깊이로 해석하지 않는다.

저장된 hull 간격은 초기 표본 뒤 빠르게 커졌고, normal-Z proxy는 0.926890에서 0.965232로 증가했다. 손바닥 중심은 선택된 local neck lower section보다 모든 표본에서 아래에 있었다. 이는 source query 및 landmark proxy의 관측이다. normal proxy의 해부학적 방향 부호는 검증하지 않았으며, 초기 clearance, cooked PhysX 접촉, 지지력 또는 원인을 인증하지 않는다. step 0의 `native_LH_contact_rows`는 `null`(해당 초기 query 없음)이고, step 1/2/4/8/12/24 완료-step 기록은 모두 빈 목록이다. 이 기록은 source pose query와 동시 측정된 접촉이 아니며 힘이나 지속 지지를 뜻하지 않는다.

## 저장 형상 그림

![0초와 0.1초 native 저장 pose의 source triangles 재구성](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/left_early_source_geometry.png)

두 panel은 같은 world bounds와 camera를 사용한다. 파란색은 기타, 초록색은 왼손 source shapes, 회색은 팔꿈치·손목이다. 주황 선/점은 저장된 source-hull witness 쌍을 형상 위에 읽기 쉽게 덧그린 annotation이다. 특히 초기 0.545 mm 간격은 표시 overlay이지 surface depth, 실제 가시성, cooked mesh 또는 PhysX clearance 판정이 아니다. geometry는 저장 pose에서 source triangles를 CPU로 재구성했으며 native renderer가 아니다. 금색 화살표는 크기를 60 mm로 표시한 normal proxy로, 해부학적 부호는 확인되지 않았다.

## 재생성 및 provenance

```bash
MPLCONFIGDIR=/tmp/left_early_source_mpl python /home/ajou/yigyu/3/stability_adapter_2/plot_left_early_source.py \
  --results-dir /home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1 \
  --out-dir /tmp/left_early_source_reproduction
```

Plotter는 analysis의 4개 check, 7개 지정 step, geometry의 step 0/24 및 embedded source 68개 SHA를 확인하며 기존 output directory를 덮어쓰지 않는다. [Plot manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/left_early_source_v1/artifacts/plot_manifest.json)는 JSON 입력, producer, 산출 이미지와 embedded input SHA를 기록한다. 새 위치 task/controller는 검증·승인·구현되지 않았다.
