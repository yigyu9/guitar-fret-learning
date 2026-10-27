# waist flank source4 사전 검수

판정: **문제없음 — CPU 탐색 실행 차단 없음.** 현재 Critical 0건(직전 발견1 해결), Warning 2건, Suggestion 0건.

새 [helper2:21](/home/ajou/yigyu/3/stability_adapter_2/left_arm_clearance_source_v2.py:21)은 `local=geom_centre+corners*half_size`를 만든 뒤 body rotation/translation을 적용한다. 실제 Pelvis 정점을 독립 행렬식으로 대조한 최대오차는1.13e−16m였다. 현재 native 기준 forearm↔Pelvis box 간격은 Pelvis-local box의 별도1차원 거리 최소화와4.16e−17m 오차로 일치했고, segment 교차·평행·끝점3사례도 통과했다. helper1/source3은 보존하며 source3 fitting/native는 실행하지 않았다.

source4는 source3에서 helper2 import·PLAN4·새 search_v4 경로만 바꾼다. actual human mesh37개/config/원GXML/거절 numeric seed SHA, 모델과 교차한 초기각 범위·Elbow_y ±5° 여유·frozen42/G회전 보존, 최종6caps/전체 LP·왼 wrist5mm/방향1°·자연 팔 조건을 유지한다. body9/right12 fit와 왼팔 보상 후 최종 float32 q로 다시 검사하고 genuine predicted human poses·새 기타 전체 상태를 저장한다. helper/source AST를 통과했다.

## Warning

- [PLAN_V4의 곡면 걸침 설명](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_THIGH_WAIST_PLAN_V4.md:26): 수락 영역은 최소 반폭+15mm flank이고 +5mm core는 참고다. region 확대를 기존 core 충족이나 실제 허벅지 걸침/힘 분담으로 설명하지 않는다. native의 접촉점·기타 변위와 왼손/기존 상완 기여를 따로 확인한다.
- [helper2:27](/home/ajou/yigyu/3/stability_adapter_2/left_arm_clearance_source_v2.py:27): 두 analytic 간격의3mm 조건은 soft 선호다. 한정된 두 부위의 proxy가 모든 자기충돌·cooked geometry를 인증하지 않는다. 최종 전체 LP/6caps/model gate와 후속 실제 초기 상태 검사를 유지한다. body 초기 범위와 runtime 실제 움직임 기준도 별개다.

검수 SHA-256: helper2 `88acee125b4a8c2f4a8e7b0e4d558850e0d8e682bebe9ff6aeef11b28013ae37`, source4 `ddf03f1018f8962593ec55e68121e66efc5341ab65f555ed91453dcaf5e258e2`, PLAN_V4 `df5874d55c035100c23e98413180e898f2cf9ef6f60c3e70d5fb43d57d3594dc`.

새 fitting/native/학습을 실행하거나 다른 소스·원자료·기존 리뷰를 수정하지 않았다. CPU 결과 수락·실제 cooked 상태·최종 봉인은 이 사전 기록에서 선인증하지 않는다.
