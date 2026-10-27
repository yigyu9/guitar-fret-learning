# V5 변경 사전검수

요약 판정: 문제없음. V4→V5 변경만 검수했으며 CPU/native 재실행 및 원본 변경은 하지 않았다.

Critical: 0

Warning: 0

Suggestion: 1

- [stability_adapter_2/analyze_right_arm_wrap_upright_v3.py:103](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_upright_v3.py:103): 기존 `upper45_*`는 실제 45% 부분집합 통계다. 후속 native의 전체 상완 유지 판정은 전체 raw 접촉과 축분율을 함께 보고하고, 이 값을 전체 0~100% 통계로 설명하지 않는다. 현재 source 사전검수의 차단 사유는 아니다.

확인 근거:

- [source:90](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v5.py:90), [source:110](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v5.py:110), [source:129](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v5.py:129): 탐색·최종 witness 모두 범위 1.0이고 full/30/45/65 키는 같은 witness다. [runtime:24](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:24)는 30 alias의 실제 점을 R_Shoulder 강체에 연결하며 범위를 다시 30%로 제한하지 않는다. 운동학적 영향과 동적 유지 성공을 분리한 [계획:6](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_UPRIGHT_PLAN_V5.md:6)과 일치한다.
- [source:124](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v5.py:124): zero-normal은 valid=false/null로 저장되고 수락식을 단락 평가하여 거절된다. 해당 AST를 추출해 zero-vector와 `allow_nan=False` JSON 저장을 확인했다. V4의 NaN 저장 경고가 새 버전에서 해결됐다.
- [source:128](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v5.py:128): 최근접 20~100%, 정상 −G_X≥0.7, 축오차≤15mm와 Torso/Spine≥20mm, Chest≥30mm, 전완>12mm, 전체 source 비겹침·waist·natural·finger42·모델한계 gate가 유지된다. 상완 음수간격 잔차 100000은 CPU fitting 가중치이며 runtime gain 변경이 아니다.
- [source:133](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v5.py:133): 상완20N/8mm·Thorax10N/4mm는 [기존 구현:30](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:30)의 허용 쌍이다. 입력 핀과 종료 SHA 검사 구조는 유지됐다.

문법 AST 통과. 소비된 `search_v5/inputs_before.json`의 source/계획 SHA와 현재 파일이 일치한다. 형상 결과 및 native 성공 판정은 이 기록의 범위 밖이다.

- Source SHA256: `8224cb1af11536a0a3a06c60daafad230ece9694549fa72e08c4b00b1d582b38`
- Plan SHA256: `9b88eedbcf78a219af9fbb2fc59a1238cc7e5d21ec78dfc0ac6a43b66425b1c7`
