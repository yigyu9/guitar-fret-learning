# Neckward torso turn · 실제 native 진단

새 neck-yaw static과 elbow-motion native는 초기 상태와 2.5초까지 trace가 정확히 같습니다. 이전 stable baseline은 다른 초기 상태이므로 이전/새 static 영상을 같은 초기조건 비교로 해석하지 않습니다. 세 native는 각 5초·1200 physics steps, 300 controls, 151 native frame으로 끝까지 계산했습니다. strap OFF, left grip 없음, 기타 direct force 없음, root/lower 고정이며 기존 human effort controller를 유지했습니다(상완 motor-point 10 N cap, 추가 forearm point force 0 N). Elbow motion은 단일 scalar R_Elbow_y target이며 world rotation axis가 아닙니다.

![이전 static 및 새 두 조건의 실제 native whole-body 0초·5초 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/native_wholebody_old_new_timeline.png)

![이전/새 static의 동일좌표 upper-body 2D crop](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/native_wholebody_samecrop_old_new.png)

![새 neck-yaw static의 actual initial native support view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/neck_yaw_static_initial_support_view.png)

## 실제 Chest–Neck 자세

![이전 및 새 static의 실제 몸통 자세 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/torso_posture_old_vs_neckyaw.png)

Source 목표와 native 측정 자세는 서로 다른 수치입니다. Search candidate source 요청은 body-right 6°, 추가 forward bend 2°, neck 방향 world-Z guitar yaw 12° 및 head yaw 7.2°(60% goal)였습니다. Actual native Chest–Neck basis 기준으로 이전 static→새 static은 forward inclination 53.575657°→48.347770° (−5.227887°), +Y에서 −X로 향하는 heading 12.643226°→22.198890° (+9.555664° toward neck), total inclination 53.590252°→48.762687°였습니다. Side inclination은 2.534570°→−10.951170°로 변했으므로 실제 torso가 source의 “body-right 6°” scalar 목표를 유지했다고 말하지 않습니다. 이들은 scalar q 목표나 source angle이 아니라 native Chest–Neck frame에서 계산한 실제 자세입니다.

## 작은 elbow-motion 비교

![새 neck-yaw 조건의 5° elbow command와 posture 측정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/neck_yaw_elbow_motion_response.png)

- 새 static: final body-bbox centre 3.944391 mm / total rotation 1.472679°.
- 새 elbow-motion: 3.876188 mm / 1.454971°.
- 2.5–5초 elbow 절대 moving q range 10.083668°; static-referenced incremental range 10.099138°.
- 최대 same-time guitar body-bbox-centre difference 0.099629 mm, rotation difference 0.053043°; incremental response RMSE 0.048544°, absolute q-vs-target RMSE 0.131056°.

모든 native physics는 1200 step 동안 계속 계산됐습니다. 새 elbow-motion 결과는 작은 elbow 영향 진단 1회이지, 전체 연주 안정성·반복성 인증이 아닙니다. 실제 contact endpoint 표본은 1200회 기준이며 upper-arm any-contact 1169, R_Hip 1193, Head/left arm/right distal arm 0입니다. Native declared support-region 분류는 0/1200입니다. Observed upper-arm fractions 0.3538–0.5089는 proximal 0–35% 목표 밖이며, 겨드랑이 해부학적 지지나 contact force share를 입증하지 않습니다. Raw lambda는 힘 측정값이 아닙니다.

Source-only geometry candidate는 proximal30 gap 2.279 mm, forearm 13.998 mm, thigh 0.199 mm, torso 32.929 mm를 기록했습니다. 이것은 source geometry 분석이고 cooked PhysX clearance가 아닙니다. Hands 영상은 왼손/기타 넥 쪽 카메라이므로 오른쪽 upper-arm contact evidence로 해석하지 않습니다. 전체 native physics는 중간에 멈추지 않았습니다.

## 영상

이전 static과 새 neck-yaw static native whole-body 영상은 나란히 볼 수 있습니다. 이전 조건은 다른 초기 상태입니다.

![이전 static과 새 neck-yaw static native whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/old_vs_neckturn_static.mp4)

새 motion 조건 native 전체 영상:

![새 neck-yaw elbow-motion native whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/neck_yaw_motion_whole_body.mp4)

[영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/INDEX_V1.md) · [복사 SHA-256 및 ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/manifest_v1.json)

- [결과 summary](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/result_summary_v1.json)
- [실제 몸통 자세 측정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/torso_posture_v2.json)
- [Elbow comparison 및 trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/elbow_comparison_v1.json) · [trace JSON](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/elbow_comparison_trace_v1.json)
- [Native contact-region 분류](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/contact_region_v1.json)
- [Search source candidates](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/search_v1/search.json)
