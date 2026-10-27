# 상체 공동 학습 구조 구현 1차 — 2026-10-12

## 범위와 판단

사용자가 승인 요청 없이 필요한 결정을 진행하도록 허용한 범위에서 구현한다. 기존 모델·물리·실험은 보존한다. 최종 목표는 자유 기타의 허용 영역 유지와 Fret/Strike 공동 수행이다. 현재 reward v4에는 SO(3) 허용집합 거리, 압현 pad 인증, 연속 유지/dropout, 물리 fatal 이후 고정 일정 정산이 미완료다. 이를 유효한 0으로 넣거나 기존 task done을 그대로 사용하는 학습은 하지 않는다.

이번 구현은 81출력 Actor/Critic(각 512→256), 표본 잠재행동 보존, PPO/GAE, 불변 체크포인트, 공통 음악 관측과 native 정책 실행까지다. 실제 환경 최적화는 별도 보상 계약의 미완료 조건을 명시적으로 막는다. CPU 합성 과제의 optimizer 검증은 기타 연주 학습으로 집계하지 않는다.

## 행동과 관측

하체/root 고정, 상체81 단일 소유권, body 목표 ±5°, 기존 그룹별 목표 변화율/PD를 유지한다. Gaussian 잠재행동 u와 tanh(u)를 저장하고, rate 제한 이후 목표로 로그확률을 역산하지 않는다. 초기 평균은 검증된 preload1.0 절대 목표다. 이를 정확하게 표현하려고 a=0을 anchor, a>0을 anchor→upper, a<0을 lower→anchor로 선형 대응한다. 이는 매 step 누적하는 residual이 아니다. anchor가 관절 경계인 경우 해당 방향의 목표가 평평해질 수 있으며 정보를 숨기지 않는다. 기존 계획의 mid/half 대응을 이번 ABI에서 대체하고 양끝·0·경계 반례로 검증한다.

학습 관측은 physical548 + 공동 음악28 + 현재 event의 목표별 timing6/required6 + 방향2 + event 시작/끝까지 시간2 + goal-independent press cells132 + pick detector state6/재무장 진행6/previous tip3 = 739D이다. 기존420/303 정책 history 및 교사 행동은 넣지 않는다. 명세 offset/입력 SHA/관절순서/목표 범위를 체크포인트 계약으로 봉인한다. 표적 음악 일정은 알려진 입력이며 미래 실제 성공 결과는 넣지 않는다. 이전 tip과 detector state는 240Hz 측정의 실제 상태다. 처음 tip은 현재 tip으로 초기화한 뒤 관측한다.

Actor 평균 head는 0으로 시작해 deterministic 정책이 preload1.0을 재현한다. log_std는 body/head -5, arm/finger -4에서 시작하고 학습 가능하다. 작은 탐색은 target span으로 변환되므로 실제 rad 분포도 로그로 기록한다. Critic은 scalar1이다. 관측 RMS는 rollout/PPO 동안 고정하고 갱신 뒤 다음 rollout부터 사용한다.

GAE는 terminal bootstrap과 reset 경계를 분리한다. terminated는 bootstrap0, truncated는 실제 종료 관측 value로 bootstrap하되 다음 episode로 trace를 잇지 않는다. PREP도 정책/critic 표본이며 music reward만 비활성화한다. 할인은 초 단위 half-life 10초, GAE trace half-life 1초로 명시한다(60Hz gamma≈0.998845, lambda≈0.988514). 최적값 인증이 아닌 시작값이다.

## 검증 순서

- [ ] 코드 구현 → 문법 검사, 81채널·초기 평균·경계 mapping·포화 logprob·GAE 종료/절단·계약 불일치/덮어쓰기 금지·PPO 실제 parameter 갱신 반례.
- [ ] native 실행 → 739D 실제 음악 측정, 81 정책의 5초 시작~종료 영상, 고정 하체/초기 상태/금지 API/원본 보존 검사. 정책 평균 실행이며 음악 성공을 의도적으로 보장하지 않는다.
- [ ] 별도 change-reviewer 검수 → 새 버전으로 수정/재검증, 실제 줄 번호와 한글 이미지/영상 문서, main4 append, 보존 감사.

결과 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/joint_learning_structure_v1/`.
후속 full PPO 시작 조건: reward v5의 측정·정산 계약과 fatal tail/discount 연결 검증. 기존 Fret/Strike checkpoint는 측정 설정 확인용이며 Actor 가중치/optimizer 자동 이식이나 교사 행동 강제 복사를 하지 않는다.
