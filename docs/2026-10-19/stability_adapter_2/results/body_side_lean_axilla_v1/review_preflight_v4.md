# 바디 쪽4° 오른허벅지 목표 V4 사전 검수

요약 판정: **문제없음 — V4 source 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 0 / Suggestion 0. 새 계획/source/runner 변경과 완료 결과를 읽기 전용으로 검토했다. 새 물리 실행·학습은 하지 않았다.

[source V4](/home/ajou/yigyu/3/stability_adapter_2/search_body_side_lean_axilla_v4.py:26)는 Hip soft 목표를 R_Hip으로 바꾸고 양Hip 각각의 양수 간격 hinge 비용을 유지한다. 수락 조건도 R_Hip<3mm를 직접 확인한다. 기타 X box만±40mm, R_Elbow_y scalar만 natural 기준±0.35rad로 확대하며 나머지 팔 범위·몸통/머리4°·Wrist/left/fingers·기타 회전은 보존한다. scalar 각도를 world 축 회전이나 해부학적 flexion으로 해석하지 않는다.

완료 해는 source clear, 전체 capsule 최소0.123462mm, R_Shoulder0.123462mm, L_Hip0.131361mm, R_Hip1.782223mm, 전완0.168742mm로 양수 gate를 통과한다. 그러나 **근위0~65% 최소 gap4.313937mm가3mm 조건을 초과**한다. [원결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/search_v4/search.json:1)의 selected=[]/native0 거절이 맞다. normal world Z0.999734, 손 위치30.483mm·방향 변화5.762°, 팔 방향 및 other72 조건만으로 근위 gate를 생략할 수 없다. 입력594개 현재 SHA 불일치0개를 확인했다.

[runner V3](/home/ajou/yigyu/3/stability_adapter_2/run_body_side_lean_axilla_v3.py:116)는 V2와 PLAN/search 경로만 다르다. 기존 전완 human effort·gravity/posture·native cap/owner/mixed69/상태 불변/Jacobian 가드, 자유 기타·strapOFF 조건을 유지한다. 기타 직접 외력·부착·런타임 pose 쓰기를 추가하지 않는다. source 거리·normal은 실제 cooked 접촉이나 유지 성공 인증이 아니다. Python3.8 구문은 정상이다.

검수 SHA256:

- 계획 V4: `c10ff91c9448257efa955a4d0af9976369a4311d9d50c2bf132e6d68110df370`
- search V4: `3aa33b8a4b01e7e383f45d27cc129ffac459fc6a51af9ca138ed7201c5f6d0bb`
- runner V3: `8635e0aca89ad2704c740a44372e0b37910daec9f4e488709048f4a194c4095a`
- 완료 search.json: `6bd5eb543753e4db4364c036e87444bc7300b23193153979370928b553103585`

이 새 리뷰 외 원본·기존 결과·이전 리뷰는 수정하지 않았다.
