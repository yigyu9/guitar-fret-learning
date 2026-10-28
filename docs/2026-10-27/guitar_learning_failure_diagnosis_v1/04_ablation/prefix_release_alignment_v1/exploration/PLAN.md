# 목표각 탐색 단위 CPU 검사

상위 PLAN의2번만 담당한다. 상위계획/원70e/저장관측/활성source/설정/기존결과는 수정하지 않는다. 새native/GPU/fit/PPO/모델저장0, 직접사용파일SHA만 확인한다.

- 표본은 사전고정 CPU torch.Generator seed7, float64 표준정규100000×4개를 모든case·두sigma에서 공통 사용한다. N/Ref는 원schedule의 정확한각을 encode→atanh하여 고정평균으로 정하고, 원70e의 env0 phase0..5별 저장행 순서의 len//2(짝수면 뒤쪽중앙)을 선택한다. phase선택은 기존저장라벨이며 새시계/관측생성0.
- genuineGoalPolicy의6행 평균은 원float32모델에서 읽고 이후 고정μ·원native경계·decode산술을float64로 평가한다. CUDA/float32정책잡음 bitexact 재현을 주장하지 않는다. 원73tensor/관측 불변·원rawgoal 재현을 확인한다.
- Δθ=decode(tanh(μ+σ ε))−decode(tanh μ)의RMS/평균편향/1·5·50·95·99분위수/|Δθ|>4/60 비율을 계산한다. 이는 rateclip 전 목표각 변화다.
- nominal=(4/60)×원saved effective exp(clamp(log_std,-5,2)) std(약.171171), L=max(upper−035ref,035ref−lower), 후보σ_i=nominal/L_i만 계산한다. 모집단RMS≤nominal 증명과 유한표본RMS≤nominal×표본ε_RMS를 구분하고 점별Lipschitz/zero-noise/encode-decode·유한성 검사한다. nominal을 기존incremental의 정확한 유한잡음RMS로 부르지 않는다.
- [x] 최소CPU실행·표/작은그림·단위/불변 검사
- [x] 결과와 한계 기록. 독립통합검수 판정은새review.json에 별도기록하고 이계획은동결

후보를 checkpoint나설정에 적용하거나 표본성과로 선택/탐색하지 않는다. 분포는목표각의확률산술이고 실제관절움직임·힘·실제PPO효과를 예측하지 않는다.

최종동결 전 계산명확화: config상수로 계산한 첫 초안은 draft_config_std/에 보존했다. 최종은 원float32 policy와 동일한 clamp/exp로 직접 확인한 saved effective std를 사용하며, config와의1e−8내 차이는 반올림 차이로 기록한다. 후보미적용/표본·평균·범위·검사scope는 불변이다.
