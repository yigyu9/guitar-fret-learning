# fret S0 학습 결과 — 2026-07-19

> **주의(2026-07-20)**: 아래 표는 접근 거리로 press 성공을 판정하던 구 R1/R2의 역사적 결과다.
> 실제 pad signed-depth를 쓰는 현 보상으로 `fret_002000.pt`를 재평가한 결과는 F1 0,
> press 성공률 0%, 평균 signed depth -6.38mm다. 새 환경에서는 이 checkpoint를 이어 쓰지 말고 재학습한다.
> 재평가 JSON: `eval_002000_r1r2_signed_depth.json`.
> R3/R4 3상태 지표 배관 1-episode 진단: `eval_002000_tristate_pipe_1ep.json`
> (`wrong_press_rate=0.00907`; 이 곡은 개방현 NO_PRESS 표본 없음).
> R5 release NO_PRESS goal 포함 1-episode 배관 진단:
> `eval_002000_tristate_r5_pipe_1ep.json` (`no_press_accuracy=0.3741`,
> `wrong_press_rate=0.2716`; 구 정책의 미학습 진단값).

입력은 `02_Jazz1-200-B_solo` 한 곡이다. 512개 병렬 환경, random start, 32-step PPO로
2,500회 checkpoint(40,960,000 environment samples)까지 학습했다. 중단 요청 시점까지
`metrics.jsonl`에는 2,521회/41,304,064 samples가 기록됐다.

## 최종 선택

- checkpoint: `fret_002000.pt`
- 선택 근거: 동일 조건으로 평가한 checkpoint 중 deterministic 전체 곡 F1 최고
- 평가: F1 **0.917510**, precision 0.996473, recall/accuracy 0.850460
- 평균 지정 압점 거리: 0.007165m
- 평균 손목 prior 거리: 0.067946m
- all-correct frame 비율: 0.813899
- 정량 게이트 F1≥0.9: PASS

## checkpoint 비교

| iteration | samples | F1 | precision | recall | 평균 압점 거리 | 판정 |
|---:|---:|---:|---:|---:|---:|:---:|
| 500 | 8,192,000 | 0.166728 | 1.000000 | 0.091942 | 20.53mm | FAIL |
| 1,000 | 16,384,000 | 0.723669 | 1.000000 | 0.580885 | 12.17mm | FAIL |
| 1,500 | 24,576,000 | 0.902015 | 0.997753 | 0.823765 | 8.01mm | PASS |
| **2,000** | **32,768,000** | **0.917510** | **0.996473** | **0.850460** | **7.17mm** | **PASS/선택** |
| 2,500 | 40,960,000 | 0.910773 | 0.999877 | 0.836369 | 7.12mm | PASS |

각 행은 random start와 reset noise를 끄고, 곡 처음부터 deterministic action으로 64개 환경을
동시에 완주한 평균이다. JSON 원본은 `eval_*.json`, 학습 곡선은 `training_curves.png`다.

## 영상

`fret_002000_rollout.mp4`는 선택 정책을 곡 처음부터 deterministic으로 재생한 지판 close-up이다.
1280×720, H.264/AAC, 30fps, 14.374초, 431프레임으로 검증했다. 목표만 표시한 번들의
`02_Jazz1-200-B_solo.isaac_fingering.mp4`와 같은 시각에서 비교한다. 영상은 정성 확인용이며
관통 깊이와 관절 limit은 별도 수치 감사로 판정해야 한다.

## 해석과 남은 게이트

F1은 학습 전 0에서 0.9175까지 올랐고, 압점 거리도 20.53mm에서 7.17mm로 줄었다. 2,500회는
압점 거리만 소폭 줄고 F1은 낮아져 2,000회 모델을 선택했다. 이는 학습에 사용한 같은 곡의
S0 정량 성공이며 일반화 성공은 아니다. 다음 검증은 학습 정책 rollout 영상, 기타 관통 0,
손가락 limit 위반 0, 비제어 우팔·하체 안정, held-out 단음곡 F1이다.
