# 18조합 결과

시작 2026-11-02T02:34:06+09:00 / 종료 2026-11-02T06:00:25+09:00

손목지원·목표손가락4축 독립 학습이다. 미실행/실패를 전체18조합 분모에서 제외하지 않는다.

|조합|상태|학습 회수|선택 평가 달성|clean|오압현 초|영상 성패|
|---|---|---:|---|---:|---:|---|
|index_s1_f1|passed|100|32/32|1.0|0.0|None|
|middle_s1_f1|budget_unresolved|100|0/16|0.0|0.0|None|
|ring_s3_f1|budget_unresolved|100|16/16|0.8354166666666667|0.0|None|
|pinky_s3_f1|budget_unresolved|100|16/16|0.7545138888888889|0.0|None|
|middle_s3_f22|initial_unresolved|0|None/None|None|None|None|
|middle_s3_f12|initial_unresolved|0|None/None|None|None|None|
|index_s6_f22|initial_unresolved|0|None/None|None|None|None|
|pinky_s1_f12|budget_unresolved|100|16/16|0.8461805555555555|0.0|None|
|middle_s1_f12|initial_unresolved|0|None/None|None|None|None|
|pinky_s6_f12|passed|100|32/32|0.9858506944444444|0.0|None|
|ring_s1_f22|initial_unresolved|0|None/None|None|None|None|
|ring_s6_f1|budget_unresolved|100|0/16|0.0|0.0|None|
|pinky_s3_f22|initial_unresolved|0|None/None|None|None|None|
|index_s3_f12|initial_unresolved|0|None/None|None|None|None|
|middle_s6_f22|initial_unresolved|0|None/None|None|None|None|
|index_s1_f22|initial_unresolved|0|None/None|None|None|None|
|index_s6_f1|budget_unresolved|100|0/16|0.0|0.0|None|
|ring_s6_f12|budget_unresolved|100|0/16|0.0|0.0|None|

## 분석

- 빠른 선별 통과: 2/18.
- 초기 상태 미확보/미실행: 9/18.
- 100회 예산 내 미달은 수렴 불가능이나 물리적 불가능의 증거가 아니다.
- 학습 중 확률적 성공과 고정 정책 평가를 구분한다. 동일 초기 반복은 독립 학습 난수가 아니다.
- 처음 통과한 경계와 선택 모델은 results.json의 history/confirmation에서 확인한다.
- 초기 배치 오류는 초기 후보의 native_endpoint_diagnostics.json, 실행 오류는 상태 원장의 errors와 stdout을 대조한다.
