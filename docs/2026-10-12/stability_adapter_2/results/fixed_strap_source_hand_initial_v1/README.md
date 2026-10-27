# 고정 스트랩 손 초기값 후보: 실제 0-step 형상 거절

기존 `initial_middle3_alignment_v1` 자세와 고정 LA 1.1018469719600776 m 기준에서 왼손 다섯 관절 초기값과 유지 목표를 source/native/normalized 범위 교집합 안의 값으로 바꿔 검증했다. 준비 단계 9개 검사는 모두 통과했고, 나머지 76개 초기값·목표와 기타 전체 초기 상태, PD, 몸통 목표, 스트랩 길이는 유지됐다.

| 관절 | 이전 초기각 → 후보 초기각 (rad) | 초기각 변경 (deg) | 이전 목표 → 후보 목표 (rad) |
|---|---:|---:|---:|
| LH thumb1_x | 0.697449 → 0.530244 | −9.580139 | 0.625016 → 0.530244 |
| LH thumb1_y | −1.565726 → −0.904457 | +37.887913 | −1.522105 → −0.904457 |
| LH thumb3 | 0.989964 → 0.387397 | −34.524579 | 0.892722 → 0.387397 |
| LH index1_x | 0.922862 → 0.753953 | −9.677739 | 0.958665 → 0.753953 |
| LH ring1_x | 1.003438 → 0.861938 | −8.107339 | 1.068293 → 0.861938 |

후보는 실제 native 초기화에서 거절됐다. 15개 직접 검사 중 `source_human_guitar_clear`만 실패했고, 충돌 쌍은 `LH:thumb2`–기타였다. 저장된 source LP의 공통 내접 반경은 0.004288365 m (4.288365 mm)다. 이 값은 PhysX 관통 깊이나 동적 접촉 측정값이 아니다. 양손 교차와 humanoid self-screen 1,188쌍, palm-up proxy, 초기 기타·PD·root/lower 조건 등 나머지 14개 검사는 통과했다.

이 실행은 초기화 1회와 0 physics step에서 종료됐다. `report.json`의 `completed=false`와 `native_execution.json`의 `exit_code=1`은 예상된 초기 source-geometry gate 거절이며, 실행 오류를 감춘 성공 판정이 아니다. 후보를 채택하지 않았고 5초 기타 안정성, 자연스러움, 연주 기능은 측정하지 않았다. 범위 안의 관절값만으로 겹침 없는 초기 형상이 보장되지 않는다는 결과다. actor 추론과 학습은 0회다.

![실제 Isaac Gym native t=0 손 프레임; 저장된 스트랩 경로 표시 포함](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/hands/00000.png)

![실제 Isaac Gym native t=0 전신 프레임; 저장된 스트랩 경로 표시 포함](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/frames/whole_body/00000.png)

두 영상은 각각 한 프레임만 담은 30 fps partial 기록이며 길이는 0.033333초다. 5초 영상이 아니며, 그림의 주황 경로는 스트랩 시각화이지 천 형상이나 추가 물리 효과가 아니다.

![한 프레임 partial 손 영상 — 0.033333초, 5초 실행 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/hands.mp4)

![한 프레임 partial 전신 영상 — 0.033333초, 5초 실행 아님](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/whole_body.mp4)

다음 진단은 [엄지2 여유 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_THUMB2_CLEARANCE_PLAN.md:1)에 적힌 7개 CPU source 조건(thumb2 오프셋 0, ±0.05, ±0.1, ±0.2 rad)이다. 아직 실행하지 않았다. 검증된 scalar FK만 사용해 zero-identity와 source-clear 조건을 만족하는 최소 변경 후보를 찾은 뒤, fresh native gate를 통과하면 같은 초기화에서 5초를 기록할 예정이다. 고정 LA와 현재 기준 자세는 유지한다.

원자료는 [초기값](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_values.json:1), [준비 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/preparation.json:1), [초기 형상 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_grip_audit.json:1), [native report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/report.json:1), [영상 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/videos.json:1)에 보존했다.
