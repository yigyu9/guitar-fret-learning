# 정책·PPO·수집기 구현

`guitar_learning/policy.py`, `ppo.py`, `rollout.py` 및 대응 CPU 검사 3파일의 구현 기록이다. 기존 music_pipeline_v2 정책의 tanh Gaussian 계산·마스킹과 PPO의 GAE/분리 optimizer/KL 거래 복원을 선별 재사용했다. 원본은 수정하지 않았다. 신규 세 파일은 이전 활성 버전이 없으며 작업 전 환경 정본은 root 담당자가 `guitar_learning/archive/20261018_before_training_interface`에 보관했다.

정책은 상태 D→256→256, 공유 이벤트 24→128→128, 상태 query 128 attention, current/nearest strict deadline 두 우선 슬롯을 사용한다. 결합 입력 640에서 기본 512→512→256을 거친다. Actor와 Value의 encoder는 독립이고 두 critic은 value encoder를 공유한다. 왼손33/오른팔6 head와 log_std39는 정규화 목표 offset 행동을 내며 직접 토크를 출력하지 않는다. 초기 평균은 0, log_std=-3이다. running normalizer 없이 관측 생성기의 명시 고정 scale을 사용한다.

작은/기본/큰 fusion은 각각 256³, 512²→256, 1024²→512다. 예시 상태 450차원의 총 파라미터 수는 1,069,392 / 1,922,384 / 4,950,096이다. 실제 상태 차원은 생성자에서 명시한다. schema/observation/action/task/reward/termination 계약이 필수며 구조·규모·차원·normalization과 함께 checkpoint identity에 포함된다.

수집기는 단일 환경 N=1의 T,N buffer를 반환한다. 실제 termination은 다음 가치0, 시간제한 등 truncation은 reset 전 최종 관측으로 bootstrap한다. rollout 경계에서도 bootstrap하며 episode cost/length는 collect 사이에 유지한다. 예외나 잘못된 최종 episode는 collector를 invalid 처리하고 예외를 전달한다. 부분 batch는 반환하지 않는다.

PPO는 actor와 value 별도 optimizer, reward/cost GAE, analytic KL 재시도·초과시 actor와 optimizer 복원, 모든 update 오류시 전체 학습 상태 복원을 제공한다. checkpoint 저장은 기존 경로 덮어쓰기를 거부한다. 재개는 정책/optimizer/RNG만 복원하며 환경·collector는 새 episode로 시작한다. 환경 물리상태의 중간 재개는 구현 범위가 아니다.

검증은 rl38 CPU의 합성 자료만 사용했다. 인접 `cpu_tests.txt`에 정책 변화, critic 분리, padding/NaN masking, 규모·계약, GAE, KL 및 update 실패 복원, checkpoint 재개/RNG/덮어쓰기 거부, terminal/truncated/rollout 경계 bootstrap, episode 누적, 입력 누락·guard 오류의 검사 결과가 있다. GPU/native physics/PPO 실제 환경 학습은 실행하지 않았다.
