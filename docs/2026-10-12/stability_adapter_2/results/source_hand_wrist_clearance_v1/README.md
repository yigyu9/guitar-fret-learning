# 손목 13조건 source 교차 지도 — 겹침은 모두 남음

저장된 conditional source query의 기준 pose와 12개 손목 변화에서 보고된 human–guitar LP 공통 내접반경을 그렸다. 파랑은 `LH:thumb2`–기타, 주황은 그 밖에 보고된 human–guitar 쌍 중 가장 큰 반경이다. 도표는 정적 source 조건만 나타내며 이번 조건으로 새 Gym 렌더나 동역학을 실행하지 않았다.

| 조건 | 보고된 HG 쌍 수 | thumb2–기타 반경 (mm) | 다른 쌍 최대반경 (mm)¹ | palm-up proxy z |
|---|---:|---:|---:|---:|
| 기준 pose | 1 | 4.288365 | 해당 없음 | 0.956547 |
| L_Wrist_x −0.05 | 2 | 4.080276 | 1.104381 | 0.966780 |
| L_Wrist_x +0.05 | 2 | 4.528466 | 0.174537 | 0.943977 |
| L_Wrist_x −0.10 | 4 | 3.904457 | 2.259860 | 0.974651 |
| L_Wrist_x +0.10 | 2 | 4.799441 | 0.387612 | 0.929101 |
| L_Wrist_y −0.05 | 3 | 2.573466 | 1.027937 | 0.948744 |
| L_Wrist_y +0.05 | 1 | 5.966854 | 해당 없음 | 0.963266 |
| L_Wrist_y −0.10 | 6 | 0.815476 | 2.076522 | 0.939887 |
| L_Wrist_y +0.10 | 2 | 7.521130 | 0.483138 | 0.968873 |
| L_Wrist_z −0.05 | 1 | 5.771217 | 해당 없음 | 0.961274 |
| L_Wrist_z +0.05 | 6 | 2.780306 | 1.694364 | 0.950884 |
| L_Wrist_z −0.10 | 3 | 7.018256 | 1.506921 | 0.965054 |
| L_Wrist_z +0.10 | 8 | 1.266417 | 3.480137 | 0.944299 |

¹ `해당 없음`은 다른 쌍이 1e−7 m LP 보고 임계값을 넘지 않았다는 뜻이다. 거리가 0이라는 뜻은 아니다.

![기준 및 12개 손목 조건의 두 human–guitar source 반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/artifacts/wrist_source_clearance_radii.png)

13개 조건 모두 thumb2–기타 source 교차가 남았다. Wrist_y −0.10 rad에서는 thumb2 반경이 0.815476 mm로 줄었지만 palm–기타 반경 2.076522 mm와 추가 손가락/fret 쌍 등 총 6개 HG 쌍이 보고됐다. 반경은 LP 공통 내접반경이며 PhysX 관통 깊이나 동적 접촉 인증이 아니다. Cross-hand/self 1,188쌍은 모두 clear하고 palm-up proxy도 양수지만, source clearance 후보는 없고 5초 안정성은 측정하지 않았다. 추가 native/physics/actor/학습 실행은 0회이며 영상 모음 152개는 바꾸지 않았다.

![이전 fixed-strap 실제 실행의 t=0 손 프레임 재사용 — 이번 source 조건의 새 Gym 렌더가 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png)

위 이미지는 기존 실제 native 프레임을 설명용으로 재사용했다. 이번 13개 source 조건에서 촬영한 장면이 아니다.

다음 [팔 위치 조정 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_ARM_POSITION_PLAN.md:1)은 기존 손가락 상대 자세와 held offset을 보존하고, 원 baseline 및 Wrist_y −0.10 source 가설의 두 seed에서 Thorax/Shoulder/Elbow 작은 한 축 변화를 비교한다. 총 74 source 조건 뒤 최소 후보 하나를 fresh native에서 확인하는 단계이며 아직 실행하지 않았다. Source 교차 검사는 물리 성공 판정이 아니다.

원자료 [search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/search.json:1) · [69-input search 실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/search_execution.json:1) · [search source manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_wrist_clearance_v1/search_source_manifest.json:1).
