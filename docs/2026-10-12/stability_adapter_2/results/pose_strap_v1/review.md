# 초기 상체·스트랩 조합 검수

2026-10-06, 별도 change-reviewer 검수. 요약 판정: **문제없음**.
현재 남은 Critical / Warning / Suggestion은 없다. 이번 초기 조합·후처리·산출물의
정확성에 대한 판정이며 실제 기타 유지 성공이나 최종 후보 채택을 뜻하지 않는다.

## 검수 범위와 보존 계약

- [입력 생성기](/home/ajou/yigyu/3/stability_adapter_2/pose_strap_inputs.py:54)는 C02 하체 초기각, 기타 +5mm 목표/회전, 몸통9 초기 목표, main66 범위와 native gain/limit을 유지한다. 스트랩 길이는 실행마다 정한 절대값이며 자세별 route 차이를 자동 상쇄하지 않는다.
- [초기 손 gate](/home/ajou/yigyu/3/stability_adapter_2/pose_strap_inputs.py:115)는 source 사람–기타 음수 pair 없음, 왼손 법선 proxy의 위쪽 반구 및 유효 국소 넥 단면 하단 이하 조건이다. 해부학적 법선 부호·native clearance·지지/운지 성공의 보증과 구분돼 있다.
- [비교 코드](/home/ajou/yigyu/3/stability_adapter_2/compare_pose_strap.py:27)는 실제 하체 운동·접촉을 남기고 하체 품질을 관찰용으로 기록한다. 하체 고정이나 collision 삭제를 도입하지 않았다. initial gate와 마지막 상태의 손 metrics를 별도로 기록한다.
- [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/POSE_STRAP_SEARCH.md:24), README·PLAN의 새 방향, comparison_v2.json과 33개 run 원자료, [plot 코드](/home/ajou/yigyu/3/stability_adapter_2/plot_pose_strap.py:52), 결과 README 및 VISUAL_REPORT 13절을 검수했다.

## 독립 검증

1. 스트랩 초기 입력 5개를 /tmp에 재생성해 저장된 strap_inputs.json 전체와 정확히 대조했다. 물리 step은 실행하지 않았으며 C02 초기각·gain/목표·read-only 검사와 자기/geometry helper/base/critical source SHA가 일치했다.
2. 33개 summary row의 초기/마지막 손 metrics와 초기 source query까지 다시 계산해 comparison_v2.json과 정확히 대조했다. 위치/회전 전체 최대·sample RMS·후반 RMS, main raw 편차 및 scalar-limit 위반을 별도 수식으로 계산해 일치했다. 모든 trace에서 absolute rest length가 고정돼 있었다.
3. 0.1초 5+17개, 0.5초 7개, 1초 4개 기록과 per-run 검사를 확인했다. C02 legacy 재현, 0N route-match reference 재현, long-run의 short prefix 검사도 통과했다. comparison_v1을 보존한 v2의 row 값은 contact key 이름 변경 외에 동일했다.
4. 1초 load_20n을 파일 저장 없이 240 physics steps로 독립 재현했다. 241개 native 상태/trace, 240개 contact 기록과 leg_torques 전체가 원자료와 정확히 일치했다. 새로운 설정이나 별도 물리 조건을 추가하지 않았다.
5. 두 PNG를 직접 확인하고 /tmp에 재생성했다. curve 2059×1902, source geometry 2489×1015 그림이 픽셀까지 동일했다. 기존 JSON/PNG의 SHA256·mtime은 검증 전후 불변이었다. 3개 geometry panel은 reference의 저장된 step0/120/240 pose와 해당 시점 strap route를 사용하고 world bounds/view를 공유한다.
6. [결과 표·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/README.md:13)을 원자료와 대조했다. source 재구성/native renderer 구분, 법선 proxy 한계, nonleg row 수/힘 구분 및 긴 구간 실패 설명이 정확하다.

## 해소된 문서·분류 지적

- 초기 계획의 연장 후보 수와 실제 7개/4개 연장 run의 차이는 [상체 후보 2개·스트랩 후보·기준 대조군의 구분과 연장 근거](/home/ajou/yigyu/3/stability_adapter_2/POSE_STRAP_SEARCH.md:41)로 명확해졌다. 새로운 관절/gain 범위를 추가한 것으로 해석하지 않는다.
- Pelvis를 포함하는 접촉 분류는 `upper` 대신 [nonleg](/home/ajou/yigyu/3/stability_adapter_2/compare_pose_strap.py:83)로 교정됐다. 기존 comparison.json은 남기고 comparison_v2.json을 별도로 생성했다. nonleg에는 pelvis/몸통/팔/손이 포함되며 raw contact row를 실측 지지 힘으로 해석하지 않는다.

## 실제 결과와 한계

0.1초의 route-match 최대 오차는 6.845mm/1.520°로 legacy 7.174mm/1.591°보다
작았지만, 작은 상체 변경의 영향은 제한적이었다. 0.5초 reference는 58.452mm/8.923°였고
20N preload는 51.079mm/8.618°였다. 1초 최대 오차는 legacy 218.603mm/36.360°,
reference 253.897mm/52.862°, 10N 241.875mm/61.609°, 20N 200.537mm/75.128°로
모두 지속 유지에 실패했다. 일부 위치 오차 감소로 회전 이탈을 숨기거나 성공을 선언하지 않는다.

초기 왼손 source palm 중심은 국소 넥 하단보다 82.533mm 낮았다. 초기 proxy gate를
통과해도 지지는 보장되지 않았다. 0.5초 이하 LH/RH 손 contact row가 없고,
1초 legacy의 RH:thumb3 65row 및 20N의 Pelvis 6row도 안정 지지 힘을 증명하지 않는다.
몸통 초기 목표 hold와 실제 drift는 구분돼 측정됐으며 하체는 물리에 남아 있다.
이번 결과는 feedback ON, 작은 연주 동작 안정성 또는 최종 유지 기준 통과 결과가 아니다.

이 검수는 pose_strap_v1에 한정한다. 이후 승인된 큰 초기각 손 탐색/거리 backend 문제는
별도 hand_support_v1 검수 대상이다. 최종 protected/source snapshot 정리는 부모 관리 증거다.
리뷰어는 요청된 이 review.md만 작성하고 구현·원자료·기존 결과를 수정하지 않았다.
