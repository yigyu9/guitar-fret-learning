# 왼쪽 몸통 기울임 — 사전 독립 검수

요약 판정: **문제없음 — 수락된 두 후보의 제한된 native 시각 진단에 코드 차단 없음.** Critical 0 / Warning 1 / Suggestion 0. 새 코드·완료 source 결과만 검토했으며 새 물리 실행·학습은 하지 않았다.

- [방향 정의](/home/ajou/yigyu/3/stability_adapter_2/search_left_lean_axilla_v1.py:21)는 양 어깨에서 수평 오른쪽 축을 구하고 `−cross(world_up,right)`를 회전축으로 사용한다. 기준 world up의 작은 회전은 연주자 왼쪽을 향하며 DOF suffix를 world 축으로 해석하지 않는다. 실제 Chest 회전 투영은 4° 후보3.99999991°, 8° 후보8.00000001°다. Torso/Spine/Chest 분배와 Head world 방향 보정 오차는 선언한 gate 안이다.
- 기타 초기 p/q는 기준과 exact이고 몸통9·Neck/Head6 외의 **66개 초기 scalar q는 직접 비교해 exact**였다. 0° 행은 몸통/머리 변화와 방향 오차0이다. 4°/8° 몸통 최대 scalar 변화1.321/2.641°, 머리1.817/3.628°로 각각 ±0.12/±0.15rad 및 모델 한계를 통과한다. 미세 float 경계 때문에 other66 동일성이 깨진 문제는 없었다.
- [source 수락 판정](/home/ajou/yigyu/3/stability_adapter_2/search_left_lean_axilla_v1.py:33)은 전체 source clear·모델 bounds·capsule 간격·팔 방향·몸통/머리 방향 오차를 확인한다. 완료 [search.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/search_v1/search.json:1)은 4°와8°를 선택하며 native 실행 수는0이다. 입력576개 현재 SHA 불일치0개였다. 근위65% 간격은 관측값이며 겨드랑이 접촉을 보장하는 수락 조건은 아니다.
- [runner](/home/ajou/yigyu/3/stability_adapter_2/run_left_lean_axilla_v1.py:116)는 기존 natural V7 대비 phase/PLAN/search 이름만 바꾼다. 고정 초기-world 전완 motor 목표·관절별 토크 이득·native cap/owner window·혼합69 POSITION/12 EFFORT·상태 불변/Jacobian gate는 유지한다. config 변경은 candidate 경로와 SHA뿐이며 contract의 q_ref는 각 새 후보와 exact다. 따라서 runtime POSITION69는 **새 몸통/머리 목표를 포함한 기준**이고, 이전 phase의 other69와 같다는 계약이 아니다. 기타 직접 외력·부착·상태 덮어쓰기를 추가하지 않는다.

## Warning

1. [search_left_lean_axilla_v1.py:32](/home/ajou/yigyu/3/stability_adapter_2/search_left_lean_axilla_v1.py:32): source 오른상완 전체 gap은0°/4°/8°에서0.466/27.126/53.611mm, 근위65%는18.523/42.256/65.897mm로 **커진다**. 전완 gap도1.315/12.402/28.496mm다. 같은 팔 scalar q라도 부모 몸통 회전 때문에 팔 world 위치는 바뀐다. 결과 설명은 이를 숨기지 말고, 초기66 scalar 보존을 팔 world pose 보존 또는 겨드랑이 접근 성공으로 표현하지 않아야 한다. 두 후보의 native 실제 접촉·유지 성능은 아직 확인하지 않았다.

검수는 source 방향·초기 상태 계약·실행용 diff의 범위다. source clear는 cooked collider 간격/관통 인증이 아니며, 이후 단순 접촉이나 후기 정착을 자유 기타 유지 성공으로 확대할 수 없다.

검수 SHA256:

- 계획 V1: `0caf34bd0549aa5ffa06858735b811ba8349cdca81d1146bfb0a07088e278337`
- source search V1: `221a5d97fa0ee8bd35253a47ad9614f239b95a3ff729159845ac690043d3504e`
- runner V1: `f9209ecaea02b2ec2e8293e8a85e07251aa38bd680cdc2f2adbfba61a80898bb`
- 완료 search.json: `0231a0748cf74a2fc6e5b214139478490fd97e02d0eee04e384816c272e8e3d6`

이 새 리뷰 파일 외 기존 소스·결과·리뷰는 수정하지 않았다.
