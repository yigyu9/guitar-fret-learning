# 고정 Elbow의 기타 6현 radial reach bound 분석

![저장된 native pose의 geometry에서 계산한 radial reach bound 두 패널](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/artifacts_v1/radial_reach_bound_v1.png)

**저장된 native pose의 기하학적 분석 그래프, 시뮬레이션 렌더/타현 성공 아님.** 이 그림은 [radial_bound_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/radial_bound_v1.json)의 실제 배열만 그렸다. elbow-to-string 거리와 radial 위치오차 하한은 입력의 meter 단위 field를 mm로 변환했다. 보간이나 pose 합성은 없다.

고정된 Elbow에서 준비 자세의 손가락을 유지할 때 가능한 최대 pick 반경은 forearm 0.249810 m + wrist-to-pick 0.138315 m = 0.388125 m다. 왼쪽 패널은 t=0에서 실제 27 lane 각각의 Elbow-to-string 거리 6개를 보여 주며, 점선 수평선은 이 상한이다. 오른쪽 패널은 저장된 t=0/2/5초 pose별로 각 lane의 여섯 실제 string 위치오차 lower bound 중 최댓값을 표시한다. string index 1–6은 JSON 배열 순서이며, 현의 음높이나 순서를 별도로 추정하지 않았다.

음영은 선호 기타 lane Y 구간 −0.355…−0.295 m이고, 세로 점선은 default lane −0.325 m다. default lane에서 여섯 string의 위치오차 하한 범위는 t=0에서 10.67–30.32 mm, t=2에서 6.53–27.11 mm, t=5에서 6.75–27.35 mm다.

이 하한은 triangle inequality의 radial 필요조건이다. 반경 안쪽이라고 관절 한계, 자세 도달성, 충돌 회피, 실제 현 접촉이나 타현 성공이 보장되지 않는다. t=2/5 값은 정지 reference의 실제 proximal/guitar pose에서 계산했으며, wrist-to-pick 길이는 reference 손가락 준비 자세를 유지한다고 둔다. 실제 손가락 compliance 범위는 평가하지 않았다.

[실행 전 source·font·producer SHA pin](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/artifacts_v1/preflight_pin_v1.json) · [입력 전후 SHA 및 출력 PNG SHA](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/artifacts_v1/provenance_v1.json) · [단일 PNG producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1/artifacts_v1/build_radial_plot_v1.py)
