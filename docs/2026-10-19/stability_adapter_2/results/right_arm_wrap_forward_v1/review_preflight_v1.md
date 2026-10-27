# 오른팔 소폭 전방 이동 V1 사전검수

요약 판정: source는 계획과 일치하나 현재 사용자 목적의 채택 후보로는 부적합하다. 소비 V1과 결과를 보존하고 새 V2로 보완한다. 원본 수정·CPU/native 재실행은 하지 않았다.

Critical: 0

Warning: 1

- [source:63](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v1.py:63): 수락 gate는 elbow 전방 이동만 요구하고 palm 이동은 출력만 한다. [5mm 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/search_v1/forward5mm_audit.json)의 elbow+4.483mm/palm−2.260mm로 손이 후퇴한다. **V1을 전체 오른팔 전방 이동 결과로 채택하지 않고 palm 양의 이동을 요구하는 새 V2를 사용한다.** root가 이 한계를 발견해 V1 native를 실행하지 않은 상태다.

Suggestion: 0

- [source:37](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v1.py:37): 앞판+G_Z를 world 수평에 투영한 단위방향은 `[0.000980074,0.999999520,0]`, human 전방과 내적0.999214다. 위치/화면축과 혼동하지 않는다.
- [source:40](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v1.py:40): 실제 Shoulder51~53 세DOF만 ±0.12rad/모델교집합으로 변경한다. q0가 이미 float32 roundtrip이고 후보의 frozen78 exact gate가 유지된다. gp/q는 seed 값을 그대로 승계한다.
- [source:52](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v1.py:52): 실제 FK에서 모든 capsule을 다시 계산하고 full upper/30/45/65 alias 및 R_Thorax/R_Elbow 등 runtime 필요 witness를 새 row로 교체한다. full상완/normal/최근접20%/전완12mm/Chest30mm/trunk20mm/natural/전체sourceclear/모델한계가 계획과 일치한다. waist profile 값은 기타와 hips 고정에 따라 유지된다.
- [source:21](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v1.py:21): anchors discovery→XML발견핀→전체입력핀→Contract/FK/거리 query 순서다. 실제 human37·활성 guitarXML69 및 manifest/XML union70 파일과 contract config/candidate/reference가978개 before-map에 포함됨을 확인했다. 종료SHA검사를 유지한다.
- [source:84](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v1.py:84): native 설정은 후보path/hash와 elbow static amplitude0만 교체하며 기존 Thorax10N4mm/상완20N8mm·body9effort 및 wrapperV2를 유지한다. aliases를 읽는 기존 controller의 실제 강체점 연결과 호환된다.

AST 통과, 소비 source/plan SHA 일치. source 수락과 cooked 접촉·유지 성공을 구분한다.

- Source SHA256: `3af3840f41e411ab436055f98b6f94636702fa0d598cd9b4fd229ca41ce6504d`
- Plan SHA256: `7227d6bef86c89f6a24a90ff3ec0aebf729e1a6e55c1b38c74d2a7c248dfa23c`
