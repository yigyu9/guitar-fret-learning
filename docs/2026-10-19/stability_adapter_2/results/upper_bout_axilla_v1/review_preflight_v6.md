# 약한 두 점 제어 사전 검수

판정: **문제없음 — 제한된 5초 진단 실행을 막는 사항 없음.** Critical 0 / Warning 1 / Suggestion 0. 소스 읽기, 이전 초기값·방향 수치 및 문법만 확인했으며 신규 native 실행·학습은 하지 않았다.

- [실행 코드:79](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v6.py:79): 전완 local 기준점 계산은 이전과 동일하고, 기존 저장 단위 normal을 현재 초기 기타 회전으로 world 변환하여 기준점에서 8mm 이동한다. normal norm=1, world 방향은 약 `(0.120796, 0.906364, 0.404861)`이다. 기록된 G 기준 목표도 실제 desired에서 역변환한다.
- [상완 제어:107](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v6.py:107): 초기 인간 기준점에서 2mm 목표, 요청 벡터 상한 5N을 사용한다. 두 점의 관절 노력 합산 후 모델 한계로 한 번 clip하며, [물리 제출:64](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v6.py:64)의 물리당 단일 actor 명령 및 right12/other69·owner window·상태/목표 readback guard가 유지된다. 기타 외력·부착·런타임 pose 쓰기 추가 없음.
- [수락 후보](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/search_v3/right6_upper35/candidate.json)의 81각은 이전 [native2 초기값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upper_bout_axilla_v1/native_v2/right6_upper35/initial_values.json)의 q_ref와 정확히 같다. runner는 같은 후보/config를 사용하며 새 source4/5 거절값을 채택하지 않는다. 외부 방향 JSON은 [attempt 입력:129](/home/ajou/yigyu/3/stability_adapter_2/run_upper_bout_axilla_v6.py:129)에 포함된다.

Warning 1 — [계획:7](/home/ajou/yigyu/3/stability_adapter_2/UPPER_BOUT_AXILLA_PLAN_V6.md:7): 전완 목표 방향, 상완 목표 거리와 상한이 함께 달라진 비교다. 각 변경의 효과를 분리하거나 5N을 측정 접촉힘으로 해석하지 않는다. `safety_stopped`는 관측 래치이며 토크 중단을 뜻하지 않는다. 근위 0~35% source 기준점은 해부학적 겨드랑이·실제 접촉점 인증이 아니다.

검수 SHA256: runner6 `6e9f5f0b4d08707504c2890ff5239c53eb849300fafe7f9afecbe4524f251f92`, PLAN6 `34972d1f26d089c59f998927b7d99731563b347a67cecd4dbdf3ad348762cf20`.
