# B 압현 단계 팔 제한 단일 요인 진단

집계: 2026-10-31T00:13:37.784700+00:00

같은 저장 B정책·16축·aligned/reset4242에서 press 팔 clamp만 제거; free33/v9 전환 아님

| 조건 | 실행 | 상태 | 안전 성공/분모 | clean초 | wrong예산 보상 | cost |
|---|---|---|---|---|---|---|
| pinky_B0 | control | completed | 30/32 | 2.34375 | -0.009375007823109627 | 0.0 |
| pinky_B0 | unclamped | completed | 30/32 | 2.34375 | -0.009375007823109627 | 0.0 |
| pinky_B100 | control | completed | 21/32 | 1.640625 | -0.05156254302710295 | 0.0 |
| pinky_B100 | unclamped | completed | 21/32 | 1.640625 | -0.05156254302710295 | 0.0 |
| index_B0 | control | completed | 32/32 | 2.433854166666667 | 0.0 | 0.0 |
| index_B0 | unclamped | completed | 32/32 | 2.4361979166666665 | 0.0 | 0.0 |
| index_B100 | control | completed | 32/32 | 1.888671875 | 0.0 | 0.0 |
| index_B100 | unclamped | completed | 32/32 | 1.8970052083333333 | 0.0 | 0.0 |

전체 비교 준비: True

네 대응 진단 비교 가능; 공식 B 승급·일반화 주장이 아님

실제 초기 대응: `{"pinky_B0": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}, "pinky_B100": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "ddb9a415af0bcd45eaa7f678dac861f59b114b916d200ba10cefae7777dbcf62"}, "index_B0": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}, "index_B100": {"verified": true, "count": 32, "exact_initial_conditions_sha256": "57a7b84458298b1236c80c881c39d9f78c62b89fe8f64d3531d61b3ebe74669b"}}`

원본 strict source·평균 정책·관측 단계·초기 분포·활성축·물리·보상·native rate/smoothing은 유지한다. 실패도 첫32 episode 분모에 포함하고, 9항과 비용·실제 초기 q/hold는 JSON 원시 증거로 확인한다. free33/v9 성공과 B 실패의 차이를 이 진단 이전에 clamp 원인으로 확정하지 않는다.
