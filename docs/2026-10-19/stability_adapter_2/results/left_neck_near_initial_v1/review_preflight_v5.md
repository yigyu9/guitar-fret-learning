# 사전 검수 — 왼손 초기 후보 source5

요약 판정: **문제없음. Critical 0 / Warning 2 / Suggestion 0.** station20mm는 실제 native 초기 검증을 진행할 source 후보다. native 실행·유지·연주 성공을 인증하는 판정은 아니다.

- [source5:74](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v5.py:74)는 왼쪽 변경 geom과 나머지 human 사이에서 트리거리 >2인 쌍을 추가한다. [source5:101](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v5.py:101)의 hand 자기교차 벌점 25000 및 다른 human과의 1mm 벌점은 source 최적화 잔차다. 정적 MuJoCo query에서 움직이는 왼쪽 body의 world FK를 갱신하며, 고정 human은 원 초기 pose를 유지한다. coarse 단계는 제거했고 native PD·제어식·물성 변경은 없다.
- [source5:109](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_near_v5.py:109) 이후 native 모델 bounds 안에서 최적화한 q를 float32로 변환하고 FK와 지정면을 다시 계산한다. 최종 전체 convex mesh LP 감사와 frozen48/면 오차·방향 조건을 유지한다. 저장된 predicted_human_poses는 현재 q의 FK에서 생성한다.
- source4 두 후보는 거절로 보존되어 있다. source5 station20mm는 source_clear/accepted/frozen48 모두 true, station60mm는 source_clear여도 index signed gap −0.586264mm와 palm 점오차24.115821mm로 거절했다. 최종 LP만으로 지정면 성공을 선언하지 않았다.
- source5 입력 647개를 현재 파일 SHA와 대조해 불일치 0을 확인했다. 선택 후보의 실제 33개 왼쪽 채널/나머지48 exact, 기존 기타 position/quaternion exact를 확인했다. config는 initial_candidate 및 그 SHA만 변경되었다. source5와 실행 runner2의 Python AST도 통과했다.
- 실행 [runner2](/home/ajou/yigyu/3/stability_adapter_2/run_left_neck_near_v2.py:1)는 앞선 preflight3과 같은 SHA다. 실제 초기 FK·면 proxy·전체 source LP·PD/mass·고정48 및 기타 상태 검증과 읽기 전후 상태 불변 검사 범위를 유지한다. 해당 native 검증 결과는 아직 검토하지 않았다.

Warning 1 — [선택 후보](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_near_initial_v1/search_v5/station20mm/candidate.json:1)의 실제 signed plane gap은 thumb11.149787mm, palm12.568833mm, 앞 네 손가락4.931762/7.956312/10.292967/6.811469mm다. 5/8mm는 제안 목표이고, 모든 부위가 그 간격을 정확히 달성한 것은 아니다. 점오차도 최대9.123055mm다. 보고서에는 목표와 달성값을 구분해야 한다.

Warning 2 — 정적 source geom distance와 최종 LP는 PhysX cooked 형상 접촉·해부학적 pad·연속시간 비접촉 인증이 아니다. 인접 트리거리 ≤2 쌍은 기존 검사 규약대로 제외된다. native 초기 source proxy 재감사도 이 한계를 갖는다. 후속 실제 접촉·자세 이탈과 첫 정책 전환 결과를 따로 기록해야 한다.

검수는 변경 코드 diff·계획V5·저장된 source4/5 결과·선택 config/candidate·현재 입력 SHA에 한정했다. 추가 source 계산/native/추론/학습은 실행하지 않았으며 다른 담당 파일은 수정하지 않았다.

검수 SHA256:

- source5: `893a71fdac6693a21607176f5577c8fd59e040480a4ec6bd4857aa4445f8c11e`
- 계획V5: `6cb272c7930a87e0a4fe36bbce202670637fc8cef4bda48aa71a11c9a6b8f637`
- 실행 runner2: `1337e4a462be2e49331632198590096a8645f48d200703613f5d45780cae91cb`
- 선택 candidate: `5c9eb8fefa98aeccb491e08571bdf926857412d1dc9556da9ce3924c4d154a18`
- 선택 config: `2c37fc0f959817a8b4e535bfb1618fb78ce3e8b6287950214031ebcb1368eddf`
