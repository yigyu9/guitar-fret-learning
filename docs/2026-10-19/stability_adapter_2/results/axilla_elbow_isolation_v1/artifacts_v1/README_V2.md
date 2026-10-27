# 겨드랑이 지지 자세: 팔꿈치 영향 격리 진단

> V2 보완본: 그래프 범례를 plotting area 밖에 두고, 실제 초기 support view 및 동일 전신 카메라 상체 crop을 추가했습니다. V1과 기존 원본 미디어는 변경하지 않았습니다.

세 native 실행(static cradle, R_Elbow_y 2° 구동, R_Elbow_y 5° 구동)은 초기 native 상태와 2.5초까지 trace가 일치합니다. 각 조건은 5초 완료, 1200 physics step입니다. strap은 OFF, 왼손 그립 없음, 기타에 직접 가한 힘 없음, root/lower body 고정입니다. 사람 상완점은 10 N cap으로 제어했고 전완점은 추가 motor force 0입니다.

![세 조건 실제 native 전신 캡처 0·2.5·5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/native_whole_body_timeline.png)

![세 조건 실제 native 손 캡처 0·2.5·5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/native_hands_timeline.png)

## 5° 구동 비교

![5도 팔꿈치 명령·실제 응답과 동시점 자세 차이](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/elbow_5deg_response_and_body_delta_v2.png)

아래 영상은 static 기준과 5° 구동 조건의 실제 native whole-body 영상을 나란히 재생하는 파생 비교본입니다. 원본 영상은 별도로 보존했고 재인코딩하지 않았습니다. 노란 안내는 명령 변화 구간(2.5–4.5초)을 표시합니다.

![정적 기준과 팔꿈치 5도 구동 native 영상 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/static_vs_elbow_motion5_side_by_side.mp4)

최종 5° 조건의 native 영상 원본도 함께 제공합니다.

![5도 팔꿈치 구동 조건 native 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/elbow_motion5_whole_body.mp4)

| 확인 항목 | 실제 관측 |
|---|---:|
| 2° 명령 대비 elbow incremental 응답 peak-to-peak | 4.03339° |
| 5° 명령 대비 elbow incremental 응답 peak-to-peak | 10.08300° |
| 5° 조건 elbow 변화 tracking RMSE¹ | 0.042524° |
| 5° 조건 absolute moving q 대 target RMSE | 0.108712° |
| 최대 same-time body-bbox 중심 차이 | 0.027241 mm |
| 최대 same-time 전체 회전 차이 | 0.009348° |

¹ moving-minus-static 실제 scalar response와 명령 변화 간 오차입니다. 절대 moving q 대 target RMSE는 별도로 0.108712°입니다. 전신과 기타의 physics는 중간 종료 없이 각 1200 step 내내 계산됐습니다. 2.5–5초의 동시점 자세 차이는 작지만 이 결과는 작은 elbow 영향 진단 1회이며, 전체 연주 성능이나 반복성을 입증하지 않습니다. 상완 native 공간분류는 0–35% 구간에서 1171/1200 표본입니다. 이는 source 후보 목표 구간 0–30% 자체가 native 접촉으로 확인됐다는 뜻이 아니며, cooked contact 보증이나 해부학적 겨드랑이 지지 증거도 아닙니다. 오른쪽 허벅지에 해당하는 R_Hip는 1196/1200, 머리·왼팔·원위 오른팔은 0/1200 endpoint 표본입니다. raw lambda는 힘 측정값이 아닙니다.

Search의 source 2bend8 후보에는 proximal30 gap 1.313 mm, forearm 16.88 mm, thigh 0.183 mm, torso 27.511 mm로 기록됐습니다. 이는 source analytic 평가이며 PhysX cooked clearance 인증은 아닙니다. 각 영상은 151프레임·30fps(인코딩 5.033초), 물리 구간 5초입니다.

## 영상 원본

[영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/INDEX_V1.md) · [SHA-256 및 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/axilla_elbow_isolation_v1/manifest_v1.json)

- [native 비교 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/elbow_comparison_v2.json)
- [native 비교 trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/elbow_comparison_trace_v2.json)
- [native 검증: static](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/analysis_v3/static_cradle/verification.json) · [2°](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/analysis_v4/elbow_motion/verification.json) · [5°](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/analysis_v5/elbow_motion5/verification.json)


## 오른쪽 상완 시점 보완

![5° 조건의 실제 native 초기 support view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/native5deg_initial_support_detail.png)

위 support view는 native_v4/elbow_motion5의 실제 초기 native 렌더입니다. 아래 두 장은 같은 native whole-body 카메라 프레임의 같은 픽셀 좌표를 잘라 확대한 2D crop이며, 별도의 native camera나 접촉 측정이 아닙니다.

![동일 전신 카메라의 0초·5초 상체 2D crop](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/axilla_elbow_isolation_v1/artifacts_v1/native5deg_upperbody_samecrop_0_5s.png)

앞의 hands timeline은 기타 넥/왼손 쪽을 보는 카메라입니다. 이 시점으로 오른쪽 상완 contact 여부를 판정하지 않습니다.
