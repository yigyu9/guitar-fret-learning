# 엄지 기저부 4조건 fresh native 초기 형상 검사

기존 손 초기 후보의 thumb1_x 또는 thumb1_y 한 축만 바꿔 fresh native 초기 pose를 직접 검사했다. 고정 LA는 1.1018469719600776 m이며, 다른 80개 초기값·목표, 기타 전체 초기 상태, PD와 나머지 조건은 유지했다. 아래 반경은 각 실제 native t=0 pose에서 계산한 `LH:thumb2`–기타 source LP 공통 내접반경이다. 동적 물리 변화나 PhysX 관통 깊이가 아니다.

| 조건 | 실제 thumb1 초기각 q (rad) | 실제 각 변화 (rad) | thumb2–기타 공통 내접반경 (mm) | 유일 실패 검사 |
|---|---:|---:|---:|---|
| 기준 pose | — | 0 | 4.288364821 | source human–guitar |
| thumb1_x −0.05 | 0.480243981 | −0.050000012 | 5.193222414 | source human–guitar |
| thumb1_y +0.05 | −0.854457200 | +0.050000012 | 5.015439809 | source human–guitar |
| thumb1_x −0.10 | 0.430243999 | −0.099999994 | 6.079508797 | source human–guitar |
| thumb1_y +0.10 | −0.804457188 | +0.100000024 | 5.789206663 | source human–guitar |

![기준 pose와 네 초기 조건의 thumb2–기타 source LP 반경](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/artifacts/thumb1_base_native_source_radius.png)

네 fresh native 초기화는 각각 15개 검사 중 source human–guitar 검사만 실패했고, self 1,188쌍·cross-hand 및 나머지 검사는 통과했다. 따라서 네 조건은 모두 0 physics step에서 끝났으며 후보를 선택하지 않았다. 네 조건의 thumb2–기타 source intersection 반경은 기준보다 0.727075–1.791144 mm 커졌다. 이 결과는 네 표본의 거절일 뿐 thumb1 또는 thumb2 전체 가동범위가 불가능하다는 결론이 아니다. 5초 유지성·자연스러움·연주 기능은 측정하지 않았다.

![thumb1_y +0.05 조건의 실제 Isaac Gym native t=0 raw 손 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/native/thumb1_y_plus005/raw/frames/hands/00000.png)

위 이미지는 해당 조건의 fresh native camera가 저장한 t=0 raw frame이다. 이 phase는 4조건 각각 손/전신 한 프레임씩, 총 8개의 30fps partial video도 보존했다. 각 영상은 한 프레임(0.033333초)이며 5초 실행을 의미하지 않는다. [영상 모음 v13 — 전체 152개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v13.md:1).

다음 [손목 clearance 계획](/home/ajou/yigyu/3/stability_adapter_2/SOURCE_HAND_WRIST_CLEARANCE_PLAN.md:1)은 실패한 thumb1 변화들을 이어받지 않고 기존 `fixed_strap_source_hand_initial_v1` baseline 손 자세로 돌아간다. L_Wrist x/y/z의 0, ±0.05, ±0.10 rad를 포함한 13개 source 조건을 조사한 뒤, 통과 후보가 있으면 한 번의 fresh native 검사와 같은 초기화의 5초 기록을 진행하도록 제안한다. 아직 미실행이다.

저장 분석은 35개 검사, 준비/완료 실행 기록과 네 native audit를 보존했다. 산출물 생성은 저장 자료만 읽었고 새 native/physics/actor/학습 실행은 0회다. [분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/analysis.json:1) · [native batch](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/source_hand_thumb_base_native_v1/native_batch.json:1) · [기준 pose 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_source_hand_initial_v1/native/initial_grip_audit.json:1).
