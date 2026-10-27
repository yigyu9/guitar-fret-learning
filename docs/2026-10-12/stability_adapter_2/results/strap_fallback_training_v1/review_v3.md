# 초기 비교 산출물 v2 보완 검수

요약 판정: **수정 권장 — 외부 범례와 절대 링크 보완은 확인했으며 설명의 장력 시점 한 문장은 정정이 필요하다.** native/code/수치 차단 오류는 없다. 기존 [검수 v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v2.md:1)와 소비 산출물은 수정하지 않았다. 검수자는 이 보완 기록만 생성했다.

Critical 없음.

Warning: [v2 설명:23](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/README.md:23)의 `last_applied_tension_n`을 “다음 적분 직전에 적용하도록 기록된”이라고 설명한 문장은 시점이 다르다. [native3:155](/home/ajou/yigyu/3/stability_adapter_2/deadline_native_v3.py:155)는 직전 물리 step의 적용 index를 기록한 뒤 simulate/steps 증가를 수행하고, 제어 끝 관측이 그 값을 읽는다. **정확한 정의는 제어 endpoint에서 읽은 ‘직전 물리 적분에 제출된 계산 케이블 장력 명령’이며, 다음 적분의 현재 후보 계산값이나 센서값이 아니다.** 소비본은 보존하고 root의 새 마감 설명에 이 시점 정정을 명시할 것을 권장했다. 그림의 pre-integration 표기와 원자료는 맞다.

[보완 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/measured_traces_external_legend.png)를 실제로 열었다. 범례는 세 axes 밖의 아래 여백에 있으며 표본/평탄선을 가리지 않는다. OFF실선/ON점선과 position norm/mm·초기 SO(3)회전/degree·60Hz 명령 장력/N·물리 시간축은 원자료와 일치한다. [v2 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/README.md:1)의 근거 링크는 절대 경로다. 이에 따라 검수 v2의 기존 범례·상대 링크 Warning은 새 보완본에서 해결됐다.

[입력 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/input_hashes.json:1)의5입력은 전후/현재 SHA가 일치한다. [producer 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/producer_execution.json:1)의 producer/font SHA도 대조했다. v1 producer·영상/원자료의 앞선 검수 SHA는 그대로이며 새 native/학습·영상 재인코딩은0이다. 이번 보완은 초기 비교 그래프 QA이며 smoke 이후 장기 학습 실행 완료·음악 성공·최종 정오 마감을 인증하지 않는다.
