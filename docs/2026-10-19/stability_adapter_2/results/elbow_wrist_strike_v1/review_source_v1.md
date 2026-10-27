# Elbow·Wrist 도달 소스 독립 검수

요약 판정: 문제없음. 현재 7경로 모두 거절하고 native로 진행하지 않는 판단은 근거와 일치한다.

Critical: 0

## 확인 근거

- [V2 소스:25](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_strike_source_v2.py:25): 실제 저장 초기 상태로 FK를 보정하고 Elbow/Wrist6만 최적화한다. 저장된 48표본의 위치오차와 capsule–body 간격을 별도로 재계산한 차이는 각각 최대 2.67e−16m/1.12e−16m였다. frozen75, 모델 범위 및 초기±1rad를 확인했다.
- [V2 수락 조건:42](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_strike_source_v2.py:42): 세 경로의 최대 위치오차는 24.109/21.419/28.852mm, 최소 전완 간격은 −.0869/−.0722/−.1104mm다. 모두 도달/간격 조건을 통과하지 못해 전체 overlap 감사 배열도 비어 있다. 수락0은 정상이다.
- [길이 계산:13](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_reach_bound_v1.py:13): 실제 초기 Elbow→Wrist .249809751m와 Wrist→pick .138315429m의 합 .388125180m를 독립 검산했다. XML [Wrist offset:259](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:259)의 길이 .249809587m와 native 차이는 .164µm다. pick은 [index2 하위 marker:297](/home/ajou/yigyu/3/stability_adapter_2/assets/humanoid_fixed_lower.xml:297)이며 Wrist→palm→index1→index2→pick 체인과 고정 손가락 자세가 반경의 조건이다.
- [radial 계산:15](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_reach_bound_v1.py:15): 저장 초기/실제 정지2초/5초의 81행 거리와 하한 재계산은 최대 1.67e−16m 차이다. 기본 lane의 하한은 초기10.665–30.316mm, 2초6.530–27.109mm, 5초6.747–27.345mm다.
- source V1/V2 입력 맵 1012/1014개와 discovery/기타 XML 핀의 현재 SHA가 일치한다. XML에서 참조하는 human37/guitar69 mesh 및 manifest 입력을 포함한다. 해당 세 분석 소스 AST를 확인했다. solver/native 재실행은 하지 않았다.

## Warning

- [경로 생성:33](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_strike_source_v1.py:33): `single`은 ±12mm로 인접줄을 포함한 약3줄 sweep다. 또한 up 구간 24mm/.55s=.04364m/s는 원 detector .05m/s보다 낮다. 향후 단현/down-up 시험에서는 폭과 실제 속도를 별도로 설계해야 한다. 현재 전 경로 거절이므로 실제 타현 성공 주장에는 사용하지 않는다.
- [V1 raw query 및 V2 baseline:29](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_strike_source_v2.py:29): 동일 초기 raw −14.355mm와 analytic +.425mm가 불일치한다. raw 음수를 실제 PhysX 관통으로 인증하지 않는다. V2 source 간격도 cooked/native 접촉 인증이 아니다.
- [전체 source 감사:44](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_strike_source_v2.py:44): 통과 시에도 일부 표본만 감사하는 구조다. 현재는 그 단계에 진입하지 않았으므로 손·손가락 전체 clearance, 연속 경로 및 실제 RELEASE를 검증한 것으로 쓰면 안 된다.
- [필요조건 scope:22](/home/ajou/yigyu/3/stability_adapter_2/elbow_wrist_reach_bound_v1.py:22): 반경은 고정 proximal 축과 기준 손가락 자세의 필요조건이다. active PD의 실제 compliance나 다른 준비 자세를 포함한 전역 불가능 증명은 아니다. optimizer 실패도 전역 불가능 증명이 아니다.

## Suggestion

없음. 수락0/native0으로 이번 점검을 닫고 준비 자세 변경은 별도 단계로 다루는 것이 적절하다.
