# 같은 추가 예산의 reference-only / corrective 비교

**두 조건 모두 음악·해제·AND 기준 미달이다.** 기존 warmstart all3 91/128과 달리 둘 다 0/128이며, 추가100PPO는 진행하지 않는다. 상세 근거는 [INTERPRETATION.md](INTERPRETATION.md)와 비교 그림에 기록했다.

| 조건 | A/B7/B8 달성률 | all3 | A release | 음악/해제/AND | 물리/손목 실패 |
|---|---|---:|---:|---|---|
| reference_only | 0.210938,0.054688,0.085938 | 0.000000 | 0.406250 | False/False/False | 0/0 |
| corrective_mixed | 0.398438,0.593750,0.593750 | 0.000000 | 0.007812 | False/False/False | 0/0 |

각 조건128시도·384음과 실패를 모두 보존했다. 원 reference/기존 warmstart는 비교 출처이며 새 NN 성과와 합치지 않는다. 두 조건 모두 같은 추가1000×192 예산이다. A 달성/해제 교차표, 원9항, offline6구간, env0 기하·손목·순힘과 실제각은 comparison.json에 기록했다.

body 순힘은 접촉쌍 압력이 아니며 상세 관찰은 env0 60Hz에 한정한다. CPU 모델 재현은 native strict CUDA 복원의 대체가 아니다. 예산·문턱·후속PPO 자동 확장 없음.
