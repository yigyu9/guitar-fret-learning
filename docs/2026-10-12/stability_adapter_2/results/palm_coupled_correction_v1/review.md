# palm_coupled_correction_v1 독립 검수

검수일: 2026-10-07.
범위: fit·원producer 보존/캐시 refit·새 analyzer·세 native 조건·최종 plot/docs·미실행 관절 유지 관측 계획.
검수는 저장 자료 계산·SHA·이미지 확인만 수행했다. native 실행·코드·원자료 수정 없이 이 기록만 작성했다.

요약: 문제없음. 작은 상수 목표 보정의 수학·원자료·산출물 검증 완료; 지속 손바닥 지지·기타 안정화는 미달성이다.

판정: Critical 없음 / Warning 해소 / Suggestion 해소. 남은 actionable finding은 없다.

## 계산·실행 경계

- SLSQP의 s=δ/.001, 기타 위치/회전 기준 norm 정규화, 손 법선 soft .01·s² regularizer .0001 및 손 위치/기타 p/q 예상 norm 제약이 계획과 맞다. 독립 목적값은 2.01→1.8634408012960728이며 요청 δ는 축별 ±.001rad다.
- Quarter/half/full float32 목표는 독립 계산과 exact, 예상 출력 차이는 ≤4.34e−19였다. Float32 후 full 적용량 최대 .00100000203rad는 기록한 변환 허용오차 안이다. 이것은 모델 예측 검증이며 물리 성공 문턱이 아니다.
- Environment read가 종료 SHA 뒤였던 Warning을 해소했다. 현재 fit:53–54는 JSON을 먼저 캐시하고 종료 봉인한 뒤 :68에서 캐시를 쓴다. 원fit/producer/trial은 보존했고 검증 refit은 별도 경로에서 후처리만 실행했다(native0/physics0). 입력 SHA 목록 이외 11결과 필드 및 environment JSON은 exact이며 원producer SHA 연결도 맞다.
- 새 native는 세 조건 각24step, 총3init/72steps다. 기준은 이전 저장 결과를 재사용했다. 분석5계약·385입력 현재 SHA와 실제 float32 목표 24개 exact를 확인했다. 25시점 예측 재계산 차이는 0이다.
- Full 실제 종료 손바닥 추적점9.113399mm, 기타 최대5.099186mm/.972608°다. 예측-실제 block 차이는 손 .1270970769mm/.00971311093°, 기타 .10738914245mm/.01470554062°로 재계산과 일치한다. 신규 행렬을 feedback으로 넣지 않았다.

## 최종 미디어·다음 계획

- Canonical PNG를 직접 확인했다. 기타 설정 목표 오차·source normal gap·raw lambda의 단위와 범례·전체0~.1초 축이 맞다. Plotter의 시작/종료 봉인10입력·출력 SHA가 현재 파일과 일치하며 인덱스 파일/줄 링크가 유효하다. 과학 그래프를 native camera 장면으로 표현하지 않는다.
- 표의 양의 raw λ step/행은 baseline/quarter/half 2/2, full 2/1이며 모두 step2에 한정된다. source 간격을 cooked clearance, raw λ를 N 지지력, 작은 오차 감소를 지속 지지 인증으로 해석하지 않는 설명이 맞다.
- hold_observation_seed를 raw에서 대조했다. Baseline/full의 양의 pair는 R_Hip–G:body step1–24와 LH:palm–guitar step2뿐이다. Full L_Shoulder_x actual−target .3380126953125rad/SDK velocity .632681131362915rad/s가 맞으며 whole-joint SO(3) 각도·drive 포화·중력 원인을 뜻하지 않는다.
- PALM_HOLD_OBSERVATION_PLAN.md는 아직 미실행2init/48step observer 계획이다. 질량/property/total DOF force의 조회 부작용과 이전5배열 exact를 검증하도록 남겼고 gain·모델·feedback을 이미 변경했다고 주장하지 않는다.
- CLI 예시 Suggestion은 해소됐다. 결과 README:25가 `/tmp/stability2_coupled_correction_replot_01`로 구분됐고 새 출력 경로 안내를 유지한다. README:14도 실제 회전 표시를 world SO(3) rotvec norm→deg로 명확히 했다. Producer의 no-overwrite 동작은 의도대로다.

## 검수 소스 SHA-256

- fit_palm_coupled_correction.py: `371e6d4d4bbb677ba732d760e7a06f1850dcc7720c511d6414c705f30aeebecc`
- analyze_palm_coupled_correction.py: `abc2f04f4bbcfb7bbca97c6d01329a3b2f5c18eb2a171d265aab0beda2e9665f`
- plot_palm_coupled_correction.py: `97a64e4340caa0425c6b6a5eefec845399239aa097a9efa5e5ae88b403b5ebd0`

## 최종 범위와 한계

Full은 비교한 네 조건에서 오차가 작지만 종료 source gap9.048mm와 초기 step2의 일시적 양의 raw lambda만 남는다. 안정 자세·지속 지지·연주 성공으로 채택하지 않았다. 현재 코드·원자료·산출물 검수는 완료했고 남은 actionable finding 없이 본 기록을 최종 동결한다.
