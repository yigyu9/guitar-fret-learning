# 정적 조건 미리보기 — 4개 후보

이 자료는 네 개의 완료된 정적 5초 실행을 비교하는 미리보기다. 진행 중인 16초 왼손 스트레스 시험은 포함하지 않으며, 이 표만으로 최종 후보를 고르지 않는다.

| 조건 | 기타 BB 중심 최대 변화 | 최대 SO(3) 회전 | 왼팔·손 무접촉 표본 | 오른손목·손 접촉 표본 |
|---|---:|---:|---:|---:|
| 여유각 보정만 | 3.286739 mm | 0.819455° | 418/1200 | 0 |
| Roll −2° | 6.066885 mm | 2.352577° | 46/1200 | 0 |
| Roll +2° | 20.857204 mm | 4.727968° | 93/1200 | 0 |
| Torso +2° | 3.999468 mm | 1.159350° | 113/1200 | 0 |

네 실행 모두 1200개 240 Hz 표본의 정적 관측이다. 기타는 자유 상태, strap OFF, root·하체 고정, self-collision ON이며 유한한 인간 제어를 유지한다. 모든 조건에서 왼팔·손 접촉 없는 표본이 1200개 중 일부뿐이므로, 독립 지지 성공이나 최종 안정 자세로 부르지 않는다. 오른손목·손 접촉 표본은 각 조건 0이다. 최대 이동은 기타 BB 바디 중심 기준이며 SO(3) 회전은 정규화된 쿼터니언에서 계산됐다.

![각 후보의 시작·5초 전면 프레임. 각 case/time 표시는 영상 밖 제목에 있음.](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/static_front_2x2.png)

프레임의 채운 원 표식은 양의 raw lambda 접촉, 빈 원은 lambda=0을 뜻하며 힘(N)이나 접촉 면적이 아니다. X-ray 표시는 가려진 접촉점도 항상 보이게 한다. 인체의 초록/분홍 영역은 모델 재질 색이며 접촉표식이 아니다. 네 시야는 동일 전면 축척의 native annotated frames에서 가져왔다.

| 조건 | t=0 전면 PNG | t=5 전면 PNG |
|---|---|---|
| 여유각 보정만 | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/margin_only_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/margin_only_t5.png) |
| Roll −2° | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_m2_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_m2_t5.png) |
| Roll +2° | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_p2_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/roll_p2_t5.png) |
| Torso +2° | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/torso_p2_t0.png) | [PNG](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/front_frames/torso_p2_t5.png) |

분석 원자료: [margin only](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/analysis_margin_only_static_v1.json), [roll −2°](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/analysis_roll_m2_static_v1.json), [roll +2°](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/analysis_roll_p2_static_v1.json), [torso +2°](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/analysis_torso_p2_static_v1.json). Before pin: [preview_before_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/preview_before_v1.json). Source/copy hashes: [preview_manifest_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/initial_pose_search_v1/artifacts_v1/static_preview/preview_manifest_v1.json).
