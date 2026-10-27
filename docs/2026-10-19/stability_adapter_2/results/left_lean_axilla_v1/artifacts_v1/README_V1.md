# Left-lean axilla · source 분석과 native 비교

이번 보관본은 확정된 source 비교와 완료된 native1/native2 두 조건만 다룹니다. 추가 native3 조건은 이 문서에서 평가하거나 결론 내리지 않습니다.

![초기 native 장면 3조건 정성 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/initial_pose_three_conditions.png)

![source analytic capsule 간격 그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/source_gap_comparison.png)

## Source 간격과 해석

Source search의 0°·4°·8° 추가 Chest 좌측 world 회전 비교에서 R_Shoulder capsule gap은 0.466·27.126·53.611 mm, upper arm 근위 65% witness gap은 18.523·42.256·65.897 mm, R_Elbow/전완 capsule gap은 1.315·12.402·28.496 mm였습니다. 이는 source analytic capsule와 convex 기타 표면 사이 간격이며 cooked native 접촉, 관통 여유, 겨드랑이 지지의 증거가 아닙니다. 66개 관절 scalar 값이 유지돼도 body의 world 회전으로 팔 world 위치는 변합니다.

초기 native 장면 세 장은 카메라와 기타 초기 위치가 다르므로 정성 비교입니다. pure left4°와 coupled 조건의 기타 초기 변위도 서로 다릅니다.

## 완료된 native 조건

![두 완료 native의 실제 0·2·5초 전신 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/artifacts_v1/native_timeline_comparison.png)

| 결과 | pure left4° · native1 | left4_nearbody · native2 |
|---|---:|---:|
| body bbox 중심 이동 | 187.876 mm | 205.134 mm |
| actor-root 이동 | 258.387 mm | 323.030 mm |
| 초기 대비 전체 SO(3) 회전 | 73.904° | 50.178° |
| 2→5초 body 중심 이동 / 회전 변화 | 0.614 mm / 0.237° | 35.083 mm / 13.212° |
| R_Shoulder 접촉 표본 | 0/1200 | 0/1200 |
| R_Forearm 접촉 표본 | 173/1200 | 346/1200 |
| Head 접촉 표본 | 782/1200 | 0/1200 |
| 왼팔·손 접촉 표본 | 0/1200 | 0/1200 |

두 조건은 각각 1200 physics step, 300 control, 5초 완료, strap OFF, policy/music 0입니다. 접촉 표본은 240 Hz endpoint count이며 force가 아닙니다. native1은 Head 접촉으로 거절됐습니다. native2는 Head 접촉과 왼팔 접촉은 없지만 R_Shoulder 접촉은 0/1200이고 기타 이동·회전도 커 유지에 실패했습니다. 작은 2→5초 변화만으로 목표 자세 유지라고 해석하지 않습니다.

영상의 6현은 실제 native camera 장면에 추가된 depth-tested 시각 overlay이며 물리 현이나 진동 모델이 아닙니다. [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/INDEX.md) · [SHA/ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_lean_axilla_v1/manifest_v1.json)

## 근거 자료

- [source search v1](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/search_v1/search.json)
- [native1 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v2/verification.json) · [native2 verification](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/analysis_v3/verification.json)
- [native1 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v1/left4deg/report.json) · [native2 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/native_v2/left4_nearbody/report.json)
