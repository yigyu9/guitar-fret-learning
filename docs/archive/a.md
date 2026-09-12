# Fret 20,000-iteration 학습 분석 — 2026-08-04

> **상태: HISTORICAL EXPERIMENT REPORT.** 당시 Fret 계약과 run을 분석한 기록이며 현재
> Fret-v2 420D 정책의 성능 보고서가 아니다.

결론부터 말하면, 20,000 iteration 학습은 정상 완료됐지만 최종 정책을 성공으로 판단하기는 어렵습니다. 정적 압현과 엄지 지지는 크게 개선됐지만, 커리큘럼이 중간 단계에 고착됐고 마지막 구간에서 오압현·엄지 과압·관통이 증가했습니다.

### 학습 개요

- 곡: `02_Jazz1-200-B_solo`
- 환경: 1,024개
- 학습: 20,000 epoch, 총 655,360,000 sample
- 순수 학습 시간: 약 13시간 52분
- 초기 checkpoint 없이 새로 학습
- checkpoint 500 epoch, 영상 1,000 epoch 간격으로 정상 저장

전체 설정은 [run_manifest.json](/home/ajou/yigyu/3/fret/training/runs/20260804_0037_02_Jazz1-200-B_solo/run_manifest.json), 추이는 [training_curves.png](/home/ajou/yigyu/3/fret/training/runs/20260804_0037_02_Jazz1-200-B_solo/plots/training_curves.png)와 [fingertip_curriculum.png](/home/ajou/yigyu/3/fret/training/runs/20260804_0037_02_Jazz1-200-B_solo/plots/fingertip_curriculum.png)에서 볼 수 있습니다.

### 커리큘럼 결과

```text
coarse_reach       1 ~   295
fine_reach       296 ~   610
isolated_press   611 ~ 1,233
integrated_press 1,234 ~ 1,533
chord_reach      1,534 ~ 1,833
chord_fine       1,834 ~ 4,141
static_chord     4,142 ~ 4,607
frozen_context   4,608 ~ 7,107
goal_pair        7,108 ~ 20,000
```

가장 큰 문제는 전체 학습의 64.5%를 `goal_pair/retention`에서 보냈다는 점입니다.

- `mixed`, 실제 전환 학습, 연속 구간 학습에 한 번도 진입하지 못했습니다.
- `sequence_probability=0`이므로 곡의 실제 목표 간 이동은 학습되지 않았습니다.
- 2번 손가락 focus가 약 11,780 epoch 지속됐습니다.
- 18,894 epoch 이후 다른 손가락으로 focus가 바뀌기 시작했지만, focus가 바뀔 때마다 evidence가 초기화되어 손가락끼리 번갈아 망각했습니다.

설정상 `goal_pair_max_iterations=2000`이지만 [cfg.py](/home/ajou/yigyu/3/tab2body/cfg.py:231), 현재 hard-timeout은 `goal_pair`가 최종 난이도까지 도달해야 작동합니다. 따라서 retention에서 막히면 timeout으로도 빠져나오지 못합니다. 관련 처리는 [curriculum.py](/home/ajou/yigyu/3/tab2body/learning/curriculum.py:2241)에 있습니다.

### 마지막 구간의 성능 변화

신뢰도가 높은 4,096 episode 누적 창을 비교하면 다음과 같습니다.

| 지표 | goal_pair 진입 | 최종 | 판단 |
|---|---:|---:|---|
| F1 | 90.68% | 91.27% | 소폭 개선 |
| 최약 손가락 압현 | 73.83% | 81.96% | 개선 |
| NO_PRESS 정확도 | 99.48% | 85.70% | 크게 악화 |
| 오압현률 | 0.26% | 6.59% | 크게 악화 |
| 압현 유지율 | 90.03% | 87.28% | 악화 |
| 이벤트 성공률 | 80.95% | 47.94% | 크게 악화 |
| dropout | 1.20% | 11.92% | 크게 악화 |
| 실패 종료율 | 0.02% | 5.39% | 크게 악화 |

즉, 마지막에는 손가락을 어떻게든 누르는 능력은 좋아졌지만, 누르면 안 되는 곳까지 누르고 압현 유지와 안전을 희생했습니다.

마지막 1,000 epoch의 실패 종료 5,299건은 주로 다음과 같습니다.

- 엄지 과압: 4,003건, 약 3.1%
- 기타 관통: 1,236건, 약 1.0%
- 손가락 후면 침범: 58건
- 속도 발산: 2건

PPO 자체는 NaN이나 수치 발산 없이 안정적이었습니다. 따라서 학습 알고리즘보다 커리큘럼과 보상 균형 문제입니다.

### 모션 분석

좋아진 부분:

- 엄지 거리는 1 epoch 영상의 26.4mm에서 최종 1.72mm로 감소했습니다.
- 최종 단일 rollout의 엄지 지지율은 78.5%입니다.
- release 자세 오차는 마지막 구간 평균 약 5.4°까지 감소했습니다.
- 최종 영상은 중간 reset 없이 곡을 완주했습니다.

남은 문제:

- 훈련 중 엄지 지지는 높지만 과도하게 세게 미는 방향으로 학습됐습니다.
- 이웃 손가락 연동은 최종 영상에서도 평균 0.10°에 불과하여 사실상 보이지 않습니다.
- 비엄지 손가락의 기타 로컬 z가 최종 영상에서 `-55mm`까지 내려갑니다. 근위 마디 종료 한계 `-60mm`에 매우 가깝습니다.
- 현재 후면 감점은 distal 영역 위주라 근위 마디가 넥 아래로 감기는 동작을 충분히 막지 못합니다. 구현은 [safety.py](/home/ajou/yigyu/3/tab2body/env/safety.py:219)에서 확인됩니다.
- 왼쪽 상체 제어 관절 RMS가 1.91°에서 15.78°로 증가했고, 머리 위치 이동도 약 9.2cm까지 커졌습니다. 상체 붕괴는 아니지만 어깨·상체 보상이 늘었습니다.

최종 영상은 [fret_020000_rollout.mp4](/home/ajou/yigyu/3/fret/training/runs/20260804_0037_02_Jazz1-200-B_solo/videos/fret_020000_rollout.mp4)입니다.

### 종합 판단

- 단일 영상 결과는 20,000 epoch가 가장 좋습니다.
- 그러나 통계적으로는 최종 checkpoint가 가장 안전하거나 정확한 모델은 아닙니다.
- 6,000~7,000 epoch가 정적 압현, NO_PRESS, sustain, 안전성의 균형은 가장 좋았습니다.
- 18,000 epoch는 goal-pair 재학습 출발점 후보입니다.
- 현재 코드 그대로 추가 학습하면 같은 retention 고착과 공격적 압현이 반복될 가능성이 높습니다.
- 독립적인 다중 seed 평가는 아직 없어 최종 일반화 성능은 확정할 수 없습니다.

다음 개선 우선순위는 `goal_pair deadlock 해소 → mastered-finger replay → PRESS/NO_PRESS 동시 통과 조건 → 엄지 과압 억제 → 근위 손가락 후면 감점 보강` 순서가 적절합니다.
