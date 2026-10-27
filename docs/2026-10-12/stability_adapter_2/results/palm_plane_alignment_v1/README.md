# 손바닥·파란 측면의 source 평면 정렬 측정

이 그림은 검증된 `validated/measurements.json`의 0–0.1초 저장 관측을 표시한다. 입력 파일에는 OFF, bias, tracking 각 25개 샘플, 세 구조 검사, 0 native initialization / 0 physics step이 기록돼 있다. 별도의 실행이나 camera capture는 추가하지 않았다.

| 조건 | 시작 법선 대향각 (°) | 시작 signed point-to-plane 간격 (mm) | 종료 법선 대향각 (°) | 종료 signed 간격 (mm) | 종료 접선 거리 (mm) |
|---|---:|---:|---:|---:|---:|
| OFF | 0.00001123 | 0.050075 | 8.937354 | 56.503250 | 44.542511 |
| Bias | 0.00001123 | 0.050075 | 5.134797 | 41.415924 | 27.124028 |
| Tracking | 0.00001123 | 0.050075 | 4.750409 | 40.495078 | 26.445653 |

첫 열의 angle은 저장 pose로 변환한 source facet 법선들의 대향각이다. 전체 SO(3) 자세 차이가 아니다. signed gap은 선택된 source point에서 target plane까지의 법선 방향 거리이고, 접선 거리는 target patch 중심까지의 평면 내 거리다. 시작 signed gap 0.050075 mm는 이전 단계의 closest hull–patch 거리 0.049807 mm와 측정 정의가 다르므로 같은 값처럼 비교하지 않는다. source facet은 cooked collision surface도, 해부학적으로 보정된 손바닥 면도 아니다. 이 측정은 접촉력·접촉 성공·힘 한계를 나타내지 않는다.

![0–0.1초 OFF, bias, tracking의 source 평면 정렬 지표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/palm_plane_alignment.png)

현재 손바닥 추적은 full initial palm–guitar relative rotation을 유지한다. 측정은 법선 방향과 유한 patch 내 위치를 함께 보는 것이 유용함을 보여준다. 평행한 두 면만으로는 접촉이 보장되지 않는다. 향후 설계 검토에서는 면의 outward normal을 서로 마주 보게 하고 법선 간격과 finite patch 내 점 위치를 함께 다루며, 법선 둘레 회전은 자유도로 남기는 방안을 검토할 수 있다. normal-only 제어기는 구현하거나 시험하지 않았다. 상세 설계는 [PALM_PLANE_ALIGNMENT_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_PLANE_ALIGNMENT_PLAN.md)를 따른다.

기존 장면 예시로, 같은 palm-side 단계에서 저장한 Isaac Gym native camera frame을 표시한다. 기존 capture를 재사용했으며 이번 측정에서 camera run을 추가하지 않았다.

![기존 palm-side tracking 실행의 Isaac Gym native camera frame, physics step 24](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_side_feedback_v1/native_tracking/blue_front_024.png)

producer, 입력·출력 SHA, 실행 환경은 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/CHANGED_FILES.md)와 [`plot_manifest.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/plot_manifest.json), [`plot_execution.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/artifacts/plot_execution.json)에 기록했다.

[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_plane_alignment_v1/review.md:9)를 완료했고 미해결 지적사항은 없다.
