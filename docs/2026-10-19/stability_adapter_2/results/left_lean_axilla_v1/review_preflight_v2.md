# 왼쪽4° 팔·기타 초기 배치 V2 사전 검수

요약 판정: **수정 권장 — source 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 1 / Suggestion 0. V2 계획/source/runner 및 미소비 분석기 변경을 검토했다. 새 물리 실행·학습은 하지 않았다.

[source 수락 코드](/home/ajou/yigyu/3/stability_adapter_2/search_left_lean_axilla_v2.py:32)는 근위65% 상완 gap0.2~6mm를 요구한다. 실제7.967442mm로 미달해 [완료 search.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_lean_axilla_v1/search_v2/search.json:1)의 선택은 비어 있고 native 수는0이다. 전체 source clear, 상완 전체 gap0.453716mm, Hip 최소0.664341mm, 근위 normal world Z0.997698은 통과했다. 이것을 겨드랑이 실제 접촉이나 유지 성공으로 해석하지 않는다.

기타 초기 이동은 world [−22.351, −37.818, +20.000]mm로 선언한 범위 안이다. 오른Thorax3 ±0.05rad, Shoulder/Elbow6 ±0.20rad만 탐색하고 나머지72는 left4 초기 기준과 exact로 검사한다. 손목·몸통/머리는 그72에 포함된다. 팔 외측267.590mm·아래45.908mm·손목 안쪽90.317mm, 손 위치 오차34.227mm다. 손 방향8.419° 변화는 soft 목표의 결과이며 엄격한 방향 보존 인증이 아니다. 입력579개 현재 SHA 불일치0개를 확인했다.

[runner V2](/home/ajou/yigyu/3/stability_adapter_2/run_left_lean_axilla_v2.py:116)는 V1 대비 계획/search 경로만 변경한다. human right12 유한 EFFORT, 다른69의 새 q_ref POSITION 목표, 초기-world 전완점 제어, 기존 cap/owner/readback/상태 불변/Jacobian gate를 유지한다. 기타 초기 배치 보정은 생성 단계이며 runtime pose 덮어쓰기·직접 기타 외력·부착을 추가하지 않는다.

## Warning

1. [analyze_left_lean_axilla_v1.py:25](/home/ajou/yigyu/3/stability_adapter_2/analyze_left_lean_axilla_v1.py:25): 초기 불변 마스크가 body/head15와 right12 전체를 제외해54개만 비교한다. V2의 오른손목3 보존은 이 분석기 마스크만으로 확인되지 않는다. native 결과에 대해 손목3을 별도 비교하거나 실제 initial q 전체를 해당 candidate q와 대조해야 한다. source의 other72 검사는 손목을 포함하므로 현재 거절 결과에는 영향이 없다. 분석기는 아직 실행 검증한 것이 아니다.

분석기의 혼합69 목표/명령/접촉 재계산은 기존 natural 분석기와 같고, 이전 body/head/right 초기값 변경을 허용하는 부분만 달라졌다. 기존 natural 기준 other69 exact와 새 초기 기준 runtime POSITION69 exact를 혼동하지 않는다. 전체 중력보상·힘 기여·cooked 무관통은 인증 대상이 아니다. 3차 범위 확대와 후속 실제 시험은 이번 검수에 포함하지 않는다.

검수 SHA256:

- 계획 V2: `f733921b6689653ca82934c3af3d1dcc1cc6caea6675016c33eacfc554984ac5`
- search V2: `9d030a16e5380121ac918b2469748b2d3a8ebacf42923677007c0237a483c28d`
- runner V2: `c8f67d5f1705e44cd0d5b033f485ca266565f0758838805687eac359d14cf58e`
- 분석기 V1: `4b9635e8fdcb584741a9ff320f29b31a2bb66252423a908de517bbec9194b3fe`
- 완료 search.json: `965d9222209b0e6e6423c58a6982ec68d5c146665cbcd914923bad3157ff984f`

이 새 리뷰 외 기존 소스·결과·리뷰는 수정하지 않았다.
