# 바디 쪽4° 양수 간격 보정 V3 사전 검수

요약 판정: **문제없음 — source 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 0 / Suggestion 0. 새 계획·source V2→V3·runner V1→V2 diff와 완료 source 결과를 읽기 전용으로 검토했다. 새 물리 실행·학습은 하지 않았다.

[source V3](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v3.py:26)은 V2 첫 해를 seed로 사용하고 상완 전체/Hip의0.15mm hinge 비용, 전완/Hip0.2mm·근위 상완2mm soft 목표로 조정한다. finite soft 비용은 강제 거리 보장이 아니며 최종 gate가 별도로 판단한다. 관절·기타 위치 범위와 [수락 조건](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v3.py:33)은 V2와 동일하다.

완료 해는 전체 source clear이고 최소 capsule gap+0.129640mm, 전완+0.370637mm, Hip 최소+0.148674mm, 근위 normal world Z0.999768이다. 그러나 **근위0~65% gap3.632320mm가 필수3mm 미만 조건을 초과**하여 [search.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v3/search.json:1)의 selected=[]/native0을 유지한다. 양수 거리와 팔 방향·손 위치33.674mm·other72 exact만으로 이 gate를 생략할 수 없다. 입력592개 현재 SHA 불일치0개를 확인했다.

현재 Hip 목표/판정은 `min(L_Hip,R_Hip)`이며 실제 L_Hip0.148674mm, R_Hip2.441700mm다. 최소값을 오른허벅지 거리로 표시하거나 source 근접을 실제 지지력으로 해석하지 않는다. 기타 delta는 world[−30.000, +0.512, +20.954]mm로 같은 box 안이다. body/head4°·Wrist/left/fingers를 포함한 다른72는 right4 초기 기준을 유지한다. source docstring의 방향은 새 파일에서 player-right로 바로잡았고 기존 소비본은 보존한다.

[runner V2](/home/ajou/yigyu/3/stability_adapter_2/run_body_side_lean_axilla_v2.py:116)는 V1 대비 PLAN/search 경로만 변경한다. 기존 전완 human actuator·gravity/posture·모델 cap/owner/혼합69 POSITION/12 EFFORT·상태 불변/Jacobian gate와 free 기타/strapOFF 조건을 유지한다. 기타 직접 외력·고정·부착·runtime pose 쓰기를 추가하지 않는다. source clear는 cooked clearance/접촉 또는 기타 유지 성공 인증이 아니다.

오른Hip 목표로 바꾸는 다음 source4 및 그 범위 확대는 이번 검수 대상이 아니다. 다음 후보는 새 source/계획에서 다시 모든 gate를 통과해야 한다. 현재 원자료는 native 후보로 사용하지 않는다. Python3.8 구문은 정상이다.

검수 SHA256:

- 계획 V3: `71b8183ced7daecb29f8255d60f6cb21c62e64b048d8509f176f90e1d4db7320`
- search V3: `ca3049ecf1a7a2eec442f5261e9b16a41f3f44fa138df42bc33e22e1d813e287`
- runner V2: `1e664e8f3759caabaaf0a21b6f3d67b5e90f8c83b2c4be5eb2d598be6f062ca7`
- 완료 search.json: `999808a9e0cd60f8a6fa45ad18f3f718be52704f35cac46606a53477117b2a05`

이 새 리뷰 외 기존 소스·결과·리뷰는 수정하지 않았다.
