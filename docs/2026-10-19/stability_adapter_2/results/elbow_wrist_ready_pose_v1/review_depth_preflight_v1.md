# V4 깊이 보정 사전 검수

요약 판정: 수정 권장. V4 코드/계획의 읽기 정합성은 문제없으나 ±6mm source envelope가 거절됐다. 현재 V4 native 실행 단계로 진행하지 않는다.

Critical: 0

## 확인 근거

- [V4 보정:40](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v4.py:40): 현재 실제 pick을 현재 기타 G로 변환하고 time≥2.6s부터 Gz만 `.8*(desired−actual)`/±6mm로 보정한다. XY 목표와75 요청 q_ref는 유지한다. 실제 pick이 얕으면 음수 보정으로 목표를 더 깊게 넣는 부호가 일치한다.
- `max(target_z+correction,.0023)` floor는 고정 source manifest front 최대 −.001700m +4mm와 일치한다. 현재 원 crossing Z=.00929993m이므로 −6mm envelope 최저 .00329993m에서도 floor는 작동하지 않는다. 이 floor는 pick 목표에 대한 것이며 손 전체의 안전 여유를 보장하지 않는다.
- V3→V4 diff는 관측 깊이 보정과 로그 필드 추가뿐이다. 요청 finite/error≤2mm/모델/±1rad/norm<160 및 rate 적용 최종 norm의 물리 전 gate, 원 step 후 최종81/75 exact 확인을 유지한다. force/state setter·PD/gain/cap·33EFFORT/48POSITION·원guard 변경이 없다.
- [depth audit:22](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_depth_v1.py:22)는 crossing 양끝과 중점 각각±6mm, 총6점의 fresh whole source audit를 수행했다. 최대 위치오차 .000252817mm이며 norm도 모두160° 미만이다. 현재 입력1026개 SHA가 모두 일치하고 V4/audit AST를 확인했다. native/solver를 재실행하지 않았다.

## Warning

- [depth_audit_v1/report.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/depth_audit_v1/report.json:1): sample0(Gx−.0324452/Gy−.325/Gz .00329993m)의 `RH:ring3↔G:body` source 겹침 common radius는1.14823mm/.451019mm다. 나머지5점은 clear이나 전체 accepted_for_native=False다. [DEPTH_PLAN:7](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_DEPTH_PLAN_V1.md:7)의 envelope 통과 후 native 기준을 지켜 현재 V4 실행은 보류하고, 보정 범위/준비 자세를 새 버전에서 보완한 뒤 다시 source 검증한다. 이 source 수치를 실제 PhysX 관통 깊이로 부르지 않는다.
- [depth audit scope:27](/home/ajou/yigyu/3/stability_adapter_2/audit_elbow_wrist_ready_depth_v1.py:27): 6점은 초기 proximal/G 조건의 일부 envelope 표본이며 이동 중 기타·접근/회복 전체·연속 clearance를 인증하지 않는다. 향후 source 통과 후에도 실제 접촉/깊이/RELEASE와 드리프트를 별도로 판정해야 한다.
- [V4 로그](/home/ajou/yigyu/3/stability_adapter_2/run_elbow_wrist_ready_v4.py:59)의 `depth_correction_m`은 floor 적용 전 clipped 보정량이다. floor가 작동하는 경우 실제 Z 변경량은 `corrected_pick_G_m[2]−desired_pick_G_m[2]`로 분석한다. 현재 envelope에서는 floor가 비활성이다.

## Suggestion

없음. 이전 V3 down/up 실제 결과 검수는 이번 보정 코드 사전 검수와 별도 범위다.
