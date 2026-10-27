# V7 및 부분 timeline 분석기 사전검수

요약 판정: 수정 권장. V7 source 변경은 문제없음. 새 timeline 분석기는 부분 실행 시간 구간과 비교 길이를 보완한 뒤 실행한다. CPU/native 재실행 및 원본 수정은 하지 않았다.

Critical: 2

- [analyze_right_arm_wrap_timelines_v1.py:169](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v1.py:169): `nstep>=480`이면 실제 2~종료 시점 값을 `2_to_5s`로 저장한다. :170 회전과 :175의 `2p5_to_5s`도 같은 문제다. 실제3초(720steps)에서 현재 AST 식이 non-null을 출력함을 재현했다. **완전5초에만 해당 필드를 계산하거나 실제 관측 끝시간을 포함한 이름·구간 metadata로 바꾼다.**
- [analyze_right_arm_wrap_timelines_v1.py:193](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v1.py:193): 부분 wave와 완전 static 비교는 body/rotation 배열 길이가 달라 :195/:196에서 실패한다. 181×3과301×3 차감의 ValueError를 재현했다. 같은 짧은 partial끼리라면 :194의 `first2p5s_trace_exact=True`도 관측하지 않은2.5초를 인증한다. **공통 실제 관측 구간만 비교하고 종료시간·표본수를 저장하며,2.5초 prefix 도달 여부를 별도 기록한다.**

Warning: 1

- [analyze_right_arm_wrap_timelines_v1.py:139](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v1.py:139): 4.5~5초 slice는 4.5~5초 도중 중단된 경우 일부 행을 `last120`/`last_half_second`로 저장한다(:177~185 동일). :199의 “partial이면 late count0” 설명도 이 경우 성립하지 않는다. **5초 미도달이면 해당 완전구간 통계를 null로 두거나 관측 구간·행 수를 명시한다.** 현재 네 partial 모두2초 이전이어서 이 값은0이지만 일반 partial 지원에서는 확인이 필요하다.

Suggestion: 0

확인 근거:

- [search_right_arm_wrap_upright_v7.py:129](/home/ajou/yigyu/3/stability_adapter_2/search_right_arm_wrap_upright_v7.py:129): V6 수락식에서 axis-guide오차≤15mm만 제거했고 실제 full R_Shoulder20~100%·normal·trunk20/Chest30/forearm12·sourceclear/natural/waist/finger42/모델한계 gate는 유지됐다. guide4000 잔차와 오차 출력도 유지하고 :130의 soft-only 표기가 [계획:3](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_UPRIGHT_PLAN_V7.md:3)과 일치한다.
- [analyze_right_arm_wrap_timelines_v1.py:31](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v1.py:31): report의 실제 physics/control 수·240Hz 시계·완료 조건을 대조하며 :50부터 실제행 수 전체의 기존 명령 합성·bodyPD·33effort 소유권/cap·48position 검사를 유지한다.
- [analyze_right_arm_wrap_timelines_v1.py:165](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v1.py:165): Thorax cap을 두 reference 중 max로 오기하는 과거 문제를 `max_proximal_point_request_cap_N` 및 body별 cap/depth로 구분했다. full raw0~1/clamped 및Chest/trunk presence·positive raw lambda도 별도 출력한다. lambda를 Newton으로 바꾸지 않는다.
- [analyze_right_arm_wrap_timelines_v1.py:157](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v1.py:157): 실제 첫/마지막 physics frame과 MP4 실제 frame 수·30fps를 확인하며 영상 길이를5초로 가정하지 않는다.

두 Python AST 통과. V7 소비 입력 map의 source/계획 SHA가 현재 파일과 일치한다. 검수한 분석기는 미실행본이며 아래 SHA 기준이다. 수정 후 재검수 필요.

- V7 source SHA256: `aa8b3545be02ff013599093ed89edbb4cd8dd1acee034de13b80595b7d011003`
- V7 plan SHA256: `6ed9e80937c09752a75ff5b7e4573a7f3b4ef425707804e91b3c56d303ab1c7c`
- Timeline analyzer SHA256: `e07d9c77670d898aa940ab9ce84206e42fbe9401ac0656c9900615bb129d6a26`


# 새 V2 분석기 재검수 — 최신 판정

요약 판정: 문제없음. 위 V1의 발견 기록은 보존하며, 미실행 V1 대신 새 timelineV2/postureV2를 사용하면 앞선 지적은 해결된다. V7 source 검수도 통과다.

Critical: 0

Warning: 0

Suggestion: 0

- [timelineV2:169](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py:169): 2~5초/2.5~5초 값은 nstep1200에서만 계산한다. :139/:140 및 :177~185 후기 통계도 부분 실행에서는 null이다. 실제4.5833초에 해당하는1100steps의 AST 경계식으로 null을 확인했다.
- [timelineV2:191](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_timelines_v2.py:191): 부분 wave 비교는 available=false로 종료하며2.5초exact를 주장하지 않는다. 이 AST 분기를181행 partial로 실행해 확인했다. :193은 완전 static만 선택하므로 실제 같은301행끼리만 비교한다.
- [postureV2:90](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_arm_wrap_posture_v2.py:90): report의 실제 physicssteps와 endpoint행 수를 대조한다. :104~118에서 실제 raw0~100%, clamped전체, clamped최근접20% 이상과45% 부분집합을 구분하고, partial 후기45%값은 null이다. localZ proxy·부모상대회전·G39 초기 균일이동 검사는 소비된 이전 분석기 그대로 유지한다.
- V2들은 자기파일 및 실제 입력의 종료 SHA 검사를 유지하며 V1/소비된 V7를 수정하지 않았다. 두 V2 AST 통과. 이 검수에서는 분석기 전체/native를 실행하지 않았다. 명령·자세 원자료의 결과 검수는 실행 후 별도 수행한다.

- TimelineV2 SHA256: `15a69d65d1b8f8215ac41ae8f4299b701d7980b531951c232f7f82ec04d65704`
- PostureV2 SHA256: `3f25c2012da63d8f0f05357878a201e6efcf17fcd8ce95a3437793e2caa7de05`
