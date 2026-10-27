# OM 겨드랑이 초기 자세 사전 검수

판정: **문제없음 — source 통과 후보의 제한된 native 진단을 막는 Critical은 발견하지 않았다.** Critical 0건, Warning 1건, Suggestion 0건. 이는 겨드랑이 끼움·몸통 지지 성공 승인이 아니다. 코드·정적 저장 결과를 읽기 전용 검수하고 순수 거리 정답만 확인했으며 추가 native·학습·원본 수정은 수행하지 않았다.

[거리 계산 v2:9](/home/ajou/yigyu/3/stability_adapter_2/om_axilla_source_geometry_v2.py:9)의 centred-metre segment–convex QP 목적함수·gradient·plane offset 변환·segment t 한계·실패 거부를 확인했다. 서로 떨어진/관통하는/대각선 box 정답 거리 1/0/√2의 독립 순수 검사가 통과했다. [AABB pruning:40](/home/ajou/yigyu/3/stability_adapter_2/om_axilla_source_geometry_v2.py:40)은 segment AABB와 piece AABB 거리에서 radius를 빼는 하한이므로 최근접 후보를 잘못 제거하는 조건을 발견하지 않았다. 음수 gap은 교차 지표이며 물리 관통깊이가 아니다. 소비된 v1 실패본·기록은 보존되어 있다.

[검색:29](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v1.py:29)의 0/6/12/18° 추가 world 전경, Torso/Spine/Chest 누적 목표, 초기 몸통±8°와 머리·양팔±0.3rad의 native 교집합을 확인했다. 왼손 palm world pose와 Head world 방향은 최종 오차 gate를 사용하며 손가락·기타 초기 p/q는 변경하지 않는다. 오른손목 pose는 soft 선호이고 오른손 palm world pose를 강제로 보존하는 계약은 아니다. [최종 수락:57](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v1.py:57)은 전체 다각형 source audit와 지정 6 capsule–63piece 간격≥0.2mm, 상완 간격<10mm 및 자세 오차를 검사한다. 이는 PhysX cooked clearance 인증이 아니다.

Warning 1건:

- [검색:47](/home/ajou/yigyu/3/stability_adapter_2/search_om_axilla_initial_v1.py:47): 접촉 영역·최근접 segment 위치 선호는 soft 비용이며 수락에 ‘겨드랑이/기타 윗부분’ hard gate 또는 Chest 접촉 gate는 없다. 저장 후보의 상완 최근접 segment_fraction은 0전경 1.0, 12/18° 약 0.8이며 기타 로컬 Y≈−0.464~−0.470m로 하단 쪽이다. Chest 간격도 0/12/18°에서 약 71.1/45.3/33.1mm다. 현재 후보를 상완 접근·몸통 굽힘으로 설명하고 native 상완/몸통 접촉과 실제 위치를 별도로 판정해야 한다. 겨드랑이 끼움이 필수 수락 조건이면 후속 새 검색 버전에서 영역 조건을 추가한다. 소비된 현재 검색 결과를 수정하지 않는다.

Critical: 없음. Suggestion: 없음. 초기 source 검사·고정 q_ref PD 진단과 실제 지지·접촉력·연주 중 자유를 구분한다. 실제 native 초기화·쿡된 형상·몸통/팔 접촉 및 5초 초기 위치 유지는 후속 검증 범위다.
