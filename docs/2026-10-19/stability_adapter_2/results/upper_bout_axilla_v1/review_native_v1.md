# native 및 지역 접촉 독립 검수

판정: **문제없음 — 기록·명령 검증 범위. 요청한 근위 상완/볼록부 접촉과 초기 자세 유지는 미달.** Critical 0 / Warning 2 / Suggestion 0. 저장 원자료와 코드를 읽고 CPU 수식을 재계산했으며 신규 물리·학습은 실행하지 않았다.

- [명령 분석:36](/home/ajou/yigyu/3/stability_adapter_2/analyze_upper_bout_axilla_v1.py:36): 약한 조건의 1200개 전완/상완 task, 자세 항, 기록된 gravity 합산과 모델 clip을 독립 재계산했다. 합산 최대 차이 1.78e−15Nm, float32 제출 exact, other69 노력 0이다. 초기 인간 기준점에서 전완 8mm/상완 2mm 목표도 재현했다. J·qdot와 기록 점 속도 오차 최대 0.000939/0.000136m/s이며, 300개 POSITION69 readback/state 검사와 물리당 단일 노력 제출 기록이 맞다. 전체 gravity/Jacobian의 독립 물리 인증은 수행하지 않았다.
- [요약:26](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/summarize_trials_v2.py:26): native2/3의 전체 초기 state JSON exact, 세 조건의 기타 초기 state exact를 직접 확인했다. 세 attempt 입력 872/872/878개 현재 SHA 불일치 0, native 영상 6개 SHA 일치. 각 1200 physics/300 control/5초·151프레임, 스트랩 force/정책/체크포인트/금지 API 호출 0 기록과 일치한다. 영상 길이 5.033333초와 물리 5초는 구분한다.
- [결과 요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/result_summary_v2.json): 바디 BB 중심 이동/SO3를 trace에서 재계산하여 강한 4° `303.680mm/113.813°`, 강한 6° `234.261mm/82.276°`, 약한 6° `59.465mm/53.935°`를 재현했다. 약한 조건 root 이동은 별도 `389.853mm`; 2→5초 BB 이동 `0.132568mm`/회전 `0.066829°`는 후기 정착이다. 목 G+Y 고도각 약 −13.709°는 SO3와 다른 지표다.
- [지역 판정:22](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analyze_contact_region_v2.py:22): localPos+offset를 body origin/world/G 좌표로 재변환하고 캡슐 축 투영을 재계산했다. 이전 비교 조건과 신규 세 조건 모두 근위 0~35%·Gx/Gy 볼록부 지역 접촉/양의 raw lambda 0/1200. 전체 자료 feature pair 최대 약 1.23e−7m/캡슐 반지름 차이 최대 0.219321mm를 재현했다. 약한 조건 전체 상완 1075/전완 1189/왼팔·손 0/Head 0 표본도 원자료와 일치하며, 실제 상완 접촉의 축 fraction 중앙값은 약 0.618373이다.

Warning 1 — [제어:81](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v6.py:81), [상완:107](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v6.py:107): 전완 방향과 상완 목표 거리·상한이 함께 달라졌다. 개선 원인을 개별 항으로 분리하지 않는다. 두 점 요청힘·raw lambda는 측정 접촉힘이나 지지 기여가 아니며, 관측 래치는 노력 명령 중단을 뜻하지 않는다.

Warning 2 — [지역 정의:29](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/analyze_contact_region_v2.py:29): 지역은 근위 구간과 Gx/Gy이며 mid-depth Gz 검사·해부학적 겨드랑이 인증은 포함하지 않는다. 240Hz endpoint 표본의 무접촉을 모든 solver 내부/연속시간의 무접촉으로 확대하지 않는다. 후기 정착·Head 회피는 초기 회전 유지나 연주 성공을 인증하지 않는다.

핵심 SHA256: summary2 `4e6f842ddc999a00c758f93f418e239a02319bc5c617eca014bca5f17e002df3`; contact_region2 `8cd5e2dd22db173820b7b3fd2448e60e0465588bfcc87938e99f704406904324`; analysis3 verification `de3193b01899b659d84ccc157ad7b5647fc945eebb344c1f4961a8a0bb6dc426`.

산출물 그림·최종 설명·봉인 검수는 후속 최종 리뷰에서 별도로 확인한다.
