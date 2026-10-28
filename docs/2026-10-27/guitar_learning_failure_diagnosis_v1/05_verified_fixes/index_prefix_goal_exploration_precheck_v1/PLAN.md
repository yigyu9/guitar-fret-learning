# 목표각 모델의 유한 탐색: native 사전 비교

2026-10-28. 원70e 모델은 deterministic 음악126/128·A해제73/128이다. 탐색분포 CPU 감사/독립검수(c13b6284...)에서 저장std .171171은 N자세 목표노이즈 RMS6.49~11.13도로 계산됐다. 실제각도 손실과 A우선순위 복사는 개선되지 않아 채택하지 않는다. 이번은 보상을 바꾸기 전 탐색단위만 확인하는 사전 비교다.

## 1. 최소 CPU 준비와 독립검수

- 원genuine GoalPolicy/원70e를 원계약으로 full strict load한다. 원fit exit1과 회복감사 근거를 그대로 보존한다. 다른계약으로 기존모델을 strict resume하지 않는다.
- 읽기전용 원모델을 불러온 뒤 실행 개입으로 선택4개 log_std만 공식후보 [.0081166123204,.0119162743986,.0125984570544,.0094416943864]의 log로 바꾼다. 실제값은 봉인된 exploration/results_v1에서 읽고 원공식을 확인한다. 원checkpoint 파일을 수정하거나 새학습모델을 저장하지 않는다.
- 이 변경을 별도 execution override/보고서에 명시한다. 다른35개 std·나머지72개 state tensor는 exact, 선택4개만 변경, 원관측에서 평균출력은 exact임을 검사한다. 원표본분포/모델과의 동일성으로 위장하지 않는다.
- deterministic과 stochastic 둘 다 같은 후보std·원평균/critic·관측/시간표·물리/기존9항이다. 두 모드의 차이는 실제 sampling뿐이며 source evaluator가 요청한 flag와 실제사용한 flag를 구분해 보고한다. stochastic을 deterministic이라고 보고하거나 RNG 불변을 요구하지 않는다.
- CPU에서 logp/latent/action→goal→physical의 의미, 변환1회·실제 mode/RNG·예외/alias복원·출력보호·metadata 경계를 확인한다. 기존collector/evaluator를 얇게 재사용하고 새시뮬레이터/일반framework를 만들지 않는다.

## 2. root 직렬 native 비교: 각128 첫시도

CPU/독립PASS·최종봉인 후 root만 deterministic128→stochastic128을 새출력에 한 번씩 실행한다. seed7을 각조건 시작에 설정하며 모델은 개입후 고정한다. PPO0/fit0/reference_calls0·첫tick NN 선택4축·단1GPU scene/105/90쌍/0.25Nm/full-native범위/4rad/s·원currentguard·원finite손목·비선택B/엄지035를 유지한다. 원N/Ref 목표를 선택NN출력 대신 주입하지 않는다.

전128 음악/해제/물리·손목실패/원장9항과 기존 bounded env0 raw/4env 관측을 남긴다. raw normalized goal·decoded goal·제출physical 요청·guard후 목표를 구분한다. stochastic에서는 seeded RNG의 실제전진과 모델불변을 검사한다. 후보의 표본상한을 실제변위/압력/잡음꼬리0으로 해석하지 않는다.

## 3. 실제 분석·독립검수 후 다음 판단

각조건의 원90% 음악·해제·AND 결과를 그대로 보고한다. deterministic은 원126/73과 대조하고 stochastic의 성능변화·clip/guard·안전성을 별도기록한다. 새후보는 단위상한 공식이며 학습 최적값이라고 부르지 않는다. 미달/실패를 분모에서 제외하지 않는다. 실제결과를 보지 않고 자동PPO·계수탐색·새fit·자유기타/J33/67음을 시작하지 않는다. 기존100PPO 유지검사 조건은 여전히 미충족이다. 후속 보상목적 대조는 두CPU 근거와 이번 native 결과 뒤 별도계획으로 정한다.

- [x] 최소CPU준비·정확한두명령·사전봉인. 독립검수/최종봉인 상태는 review.json·preparation_seal.json에 별도로기록하고 이계획은동결
- [ ] root deterministic128→stochastic128 실제실행
- [ ] 실제분석·독립검수·후속계획 판단
