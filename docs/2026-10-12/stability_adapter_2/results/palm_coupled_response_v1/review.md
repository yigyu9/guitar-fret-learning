# palm_coupled_response_v1 독립 검수

검수일: 2026-10-07.
범위: probe 생성기·새 analyzer·14조건 저장 자료·최종 plotter/그림/설명 및 다음 보정 계획의 미실행 범위.
검수에서는 native 실행·원자료·코드 변경을 하지 않았으며 이 검수 기록만 작성했다.

요약: 문제없음. 실제 float32 목표 기반 결합 응답·heldout·산출물 검증 완료; 지지/기타 안정화 성공은 미달성이다.

판정: Critical 없음 / Warning 없음 / Suggestion 해소. 남은 actionable finding은 없다.

## 원자료·수학 검증

- 14init/336steps·6분석 계약·352입력 현재 SHA를 확인했다. 같은 초기 상태, initial±.3rad∩native 목표 범위와 동결 runner를 유지한다. 단축 .005rad 및 조합 .001rad는 요청량이며 계산은 실제 float32 전달 목표 차이를 사용한다.
- 독립 NumPy/SciPy 재계산에서 14조건 float32 목표는 exact였다. 기타 WORLD actual-minus-configured-goal 곡선 차이 ≤1.71e−16, 25×12×12 응답 행렬 차이 ≤5.59e−14였다. 행렬은 `(probe−baseline)/applied_delta`이며 손 출력은 desired-minus-actual, 기타 출력은 actual-minus-configured-goal로 부호를 구분한다.
- Heldout 예측 차이는 손 위치 0.0300361527mm/법선 회전벡터 0.00252476154°, 기타 위치 0.02473378246mm/world 회전벡터 0.00364702757°로 저장값과 일치한다. Hand 회전 0.08m/rad 환산을 기타 rad 성분에 적용하지 않는다.
- Baseline states/trace/tasks/contacts/controls 다섯 배열은 이전 alpha .45와 exact다. Report는 새 경로·producer 메타가 달라 실행계약으로 별도 검사한다. 원 계획의 '6raw 비교' 의미를 실제 exact 검증 범위와 구분하라는 Suggestion은 결과 README·메인 PLAN·VISUAL §65에 반영됐다.
- 실제 연산 helper/data 봉인을 확인했다. 혼합 단위 SVD를 conditioning 인증으로 해석하지 않으며 이 단계에는 fit·새 feedback이 없다.

## 최종 미디어·계획

- Canonical PNG를 직접 확인했다. 손 종료 추적점 오차와 기타 .1초 최대 오차, 관절명·관측 범위 확대·heldout block별 mm/° 표시가 맞는다. Plot 58입력·출력 SHA와 변경 인덱스 파일/줄 링크가 일치하며 source/camera 장면으로 표현하지 않는다.
- 결과 표의 요청 목표와 실제 전달 목표 구분, raw lambda 시점/행수 및 지속 지지 미달성 설명이 원자료와 맞는다. 표에서 모든 probe 요청이 +.005rad인 것은 이번 실제 생성 조건이며 일반 모델 범위에 대한 주장이 아니다.
- PALM_COUPLED_CORRECTION_PLAN.md의 초기 ±.001rad∩기존 box, 실제 float32 예상값 재계산, 세 constant-target 검증(계획3init/72steps)은 아직 미실행이다. Soft 법선 항 계수는 fit 전에 기록하도록 남겼고 새 실시간 feedback·gain·strap·finger 변경을 포함하지 않는다.

## 검수 소스 SHA-256

- generate_palm_coupled_probes.py: `4e87bb2aed3a5b6dec64bdd385f67fad2e043cff9553243456388de8c692bdad`
- analyze_palm_coupled_response.py: `ac4745e3564c3950fcf56e349ad8ef75c3693edc9a366860b0f6fc69166cbf14`
- plot_palm_coupled_response.py: `3d4822ab09d728fa86134369408b0b2a257beeea741cc0826063daefdc5e4a5e`

## 최종 범위와 한계

L_Elbow_y probe의 손/기타 오차 감소에는 양의 palm raw lambda 소실이 동반된다. 다른 조건도 양의 값은 초기 step2뿐이며 힘(N)·지속 지지 인증이 아니다. 이 행렬은 고정 초기 상태의 .1초 국소 목표 응답으로 FK·실시간 feedback Jacobian·장기 안정성으로 확대하지 않는다. 새 후보 채택 없이 식별·산출물 검수를 완료했고 본 기록을 동결한다.

## 역사적 plot producer 추가 확인

`artifacts_attempt_v1/plot_palm_coupled_response.py`의 복원 SHA `ea4ba4a2ea00db0bd90a5c941fb378ef28eda383d26d92c7dc3830d5d824ea21`는 당시 manifest와 exact다. 현재 canonical `artifacts/`의 별도 source/input/output 검증은 그대로 유지된다. 이전 경계 phase의 초안 producer 한 버전 미보관 한계를 이 phase의 현재 producer exact 검증으로 소급 보완했다고 주장하지 않는다. 추가 확인을 포함해 기록을 최종 동결한다.
