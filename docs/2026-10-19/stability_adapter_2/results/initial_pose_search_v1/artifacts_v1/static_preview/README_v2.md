# 정적 조건 미리보기 — 4개 후보

네 개의 완료된 정적 5초 실행을 나란히 보는 미리보기다. 진행 중인 16초 왼손 스트레스 시험은 포함하지 않으며, 여기서 최종 후보를 선택하지 않는다.

| 조건 | 기타 BB 중심 최대 변화 | 최대 SO(3) 회전 | 왼팔·손 무접촉 표본 | 오른손목·손 접촉 표본 |
|---|---:|---:|---:|---:|
| 여유각 보정만 | 3.286739 mm | 0.819455° | 418/1200 | 0 |
| Roll −2° | 6.066885 mm | 2.352577° | 46/1200 | 0 |
| Roll +2° | 20.857204 mm | 4.727968° | 93/1200 | 0 |
| Torso +2° | 3.999468 mm | 1.159350° | 113/1200 | 0 |

각 조건은 240 Hz에서 1200개 표본으로 관측했다. 기타는 자유 상태, strap OFF, root·하체 고정, self-collision ON이며 유한한 인간 제어를 유지한다. 네 조건 모두 일부 표본에서 왼팔·손 접촉이 있으므로 독립 지지 성공으로 해석하지 않는다. 오른손목·손 접촉은 네 조건에서 각각 0/1200이다. BB 값은 기타 바디 중심 변위이며 회전은 SO(3) geodesic이다.

![2×2 조건 배치, 각 칸에 t=0초와 t=5초의 동일 축척 native 전면 프레임을 표시. 조건·시간 캡션은 영상 바깥에 있음.](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/static_front_2x2_v2.png)

영상의 채운 원 표식은 양의 raw lambda, 빈 원은 lambda=0이며 힘(N)이나 면적이 아니다. X-ray 표시는 가려진 접촉점도 보이게 한다. 사람 모델의 초록/분홍 영역은 재질 색이고 접촉표식이 아니다.

| 조건 | t=0 전면 | t=5 전면 |
|---|---|---|
| 여유각 보정만 | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/margin_only_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/margin_only_t5.png) |
| Roll −2° | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_m2_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_m2_t5.png) |
| Roll +2° | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_p2_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_p2_t5.png) |
| Torso +2° | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/torso_p2_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/torso_p2_t5.png) |

[before pin](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/preview_before_v2.json) · [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/preview_manifest_v2.json)
