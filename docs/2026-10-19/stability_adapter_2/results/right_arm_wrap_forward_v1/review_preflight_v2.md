# 오른팔·오른손 함께 전방 이동 V2 사전검수

요약 판정: 문제없음. V1→V2 변경과 유지 조건을 검수했다. 원본 수정·CPU/native 재실행은 하지 않았다.

Critical: 0

Warning: 0

Suggestion: 0

- [source:40](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v2.py:40): 실제51~56 Shoulder3+Elbow3만 ±0.12rad/모델교집합으로 변경한다. 나머지75각·body/head/left/Wrist/finger42/rootlower·기타초기p/q는 유지한다. Elbow_y 모델한계에 ±5° 여유를 추가했고 실제 bounds 교집합이 비어 있지 않음을 확인했다.
- [source:51](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v2.py:51), [source:67](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v2.py:67): elbow와 RH:palm 모두 동일한 +G_Z 수평방향으로5/10mm 목표를 fitting하고, 각각 전방>0·오차≤2mm·직교≤12mm를 수락조건으로 요구한다. V1의 손 후퇴를 차단하며 [계획:6](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_FORWARD_PLAN_V2.md:6)과 일치한다.
- [source:74](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v2.py:74): fresh `arm_forward`, arm6 delta/bounds와 frozen75 metadata로 바꿔 3각/78고정 설명을 승계하지 않는다. 모든 fresh capsule/full alias/runtime 필수 row와 실제 G 초기값 보존 구조는 그대로다.
- [source:63](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v2.py:63): full상완0.05~4mm·최근접20%이상·normal−G_X≥0.7, forearm≥12mm/Chest≥30mm/Torso·Spine≥20mm, 모든capsule≥0.05mm·sourceclear/natural/모델한계와 frozen75 exact를 유지한다. 영벡터 normal은 valid=false/null/거절이다. waist profile의 누적 기타이동 metadata는 이전 기준값으로 승계되며 이번 phase에서 새로운 기타이동을 뜻하지 않는다.
- [source:88](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_forward_v2.py:88): 새로운 출력/계획/소스로 분리하고 controller/gain/10N4mm·20N8mm 및 static amplitude0는 유지한다. 기존 read-only wrapperV2에 필요한 R_Thorax capsule/full상완30 alias/R_Elbow proposal을 제공한다.
- 입력979개에 config/candidate/reference/helper와 human37·활성기타XML69/union70을 포함하며 사전/종료SHA 구조가 유지됐다. 두 버전의 AST와 소비 source/계획 SHA 대조가 통과했다. 실제 native 초기검증·접촉·5초 결과는 후속 독립 검수 대상이다.

- Source SHA256: `2873326d57ef230b822b09b837af7a75f7353e9c4e73b443666047bc1fd662db`
- Plan SHA256: `7d24661bc493d1dd9a83bfcbaa995f8a9d5334908f78e78af95ef057a798d61f`


# 새 native 전방 변위 분석기 추가 사전검수

요약 판정: 문제없음.

Critical: 0

Warning: 0

Suggestion: 0

- [analyze_right_arm_wrap_forward_v1.py:24](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_forward_v1.py:24): baseline 실제 초기G회전의+Z를 world수평에 투영해 고정 단위축을 정의한다. :27~30의 초기위치차 투영/직교변위/SO3 차와 :39~45의 동일240Hz endpoint 위치차 투영 수학이 맞다. 변하는 기타기준 상대변위로 설명하지 않는 scope가 적절하다.
- [분석기:21](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_forward_v1.py:21): native 실제 초기75각 exact와 기타39body 전체state exact를 요구한다. 초기 elbow/palm 전방>0도 확인한다. source6각 delta와 실제native 초기변위를 구분해 기록한다.
- [분석기:34](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_forward_v1.py:34): 짧은 실제 공통행만 비교하고 같은physics_step을 대조한다. 최종비교값의 실제comparison_end_time_s를 남기므로 partial 종료값을5초로 설명하지 않는다.5초/128step 공통구간 및 투영·직교분해를 작은 in-memory 계산으로 확인했다.
- [분석기:12](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_forward_v1.py:12): 자기파일/helper와 각 실제 읽는 초기값/report/config/candidate/endpoint를 읽기 전에 SHA로 기록하고 종료에 대조한다. 읽기전용이며 source/config/native를 변경하지 않는다. AST 통과. 원자료가 닫힌 뒤 실제75각/G39와 시계·명령 감사는 결과 검수에서 다시 확인한다.

V2 source 실제 두행은5mm수락(elbow4.088mm/palm5.071mm),10mm거절(elbow오차2.314mm·직교13.186mm)로 위 hard gate와 맞다. native 결과를 source 성공으로 대신하지 않는다.

분석기 SHA256: `2551e4f9f7eb478aa5a2e15511a833238b686c91a7c1a1cf8d8f08090de7cd9e`.
