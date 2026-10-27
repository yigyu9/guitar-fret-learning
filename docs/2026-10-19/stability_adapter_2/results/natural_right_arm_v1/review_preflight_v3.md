# 자연 오른팔 V5 사전 검수

요약 판정: **문제없음 — V5 거절 유지, native 진행 후보 없음.** Critical 0 / Warning 0 / Suggestion 1. V5 계획·변경 코드와 완료 source 결과만 검토했다. 새 물리 실행·학습은 하지 않았다.

[탐색 변경](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v5.py:35)은 V3 저장값을 seed로 쓰고 기타 초기 world Y 이동 한계를 90→120mm로 늘린다. 팔꿈치 하강·외측 및 손목 안쪽의 soft 잔차 가중치를 1000→300으로 낮추지만, [최종 수락 조건](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v5.py:42)은 유지한다. 움직인 기타 상태로 전체 source audit를 수행하며, 기타 회전과 다른 69개 초기 관절값은 유지한다.

두 후보 모두 전체 source clear지만 팔꿈치 하강은 44.598/64.051mm로 80mm 조건에 미달한다. 전완 gap은 1.266/1.315mm, 손 목표 오차는 14.336/14.010mm다. 완료된 [search.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/search_v5/search.json)의 선택 목록은 비어 있고 native 수는 0이다. 입력 SHA 571개 현재 불일치 0개를 확인했다. source 거절을 실제 자연스러움이나 해당 범위 전체의 불가능성 판정으로 확대하지 않는다.

[runner V5](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v5.py:113)는 V4 대비 계획/search 경로만 바뀐다. 초기 world 전완 motor 목표·유한 human 토크·POSITION69/EFFORT12 가드·기타 자유 상태·strap OFF를 유지한다. 계획은 이탈 감지 래치가 토크 차단이나 종료가 아님을 명시한다. 제어 후보를 실제 실행한 검증은 아니다.

## Suggestion

1. [search_natural_right_arm_v5.py:30](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v5.py:30): `seed_res`와 32행의 `least_squares` 결과는 37행에서 V3 저장값을 시작점으로 사용하면서 더 이상 쓰이지 않는다. 이후 새 버전에서 이 불필요한 최적화만 제거할 수 있다. 소비된 V5는 보존한다.

검수 SHA256:

- 계획 V5: `2ee281748ebc15334803f345f42d371472c6120264234297e03e2e95a02bf29f`
- search V5: `aea085c59c396f4b2621fe604a63d54aa786ca459b998a06aa8951cda2754535`
- runner V5: `00d7cb23f9de49dcbd67b74c3c60de3980da810b7ca200944643729b3c7bd685`
- 완료 search.json: `1149e68166c64cd2b830f3a8484095c54101bd7c153f2381d7fae214f1933fe4`

기존 리뷰·소스·원자료는 수정하지 않았다.
