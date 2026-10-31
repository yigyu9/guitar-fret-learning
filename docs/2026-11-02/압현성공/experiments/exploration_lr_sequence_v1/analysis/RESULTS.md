# 압현 개선 비교 연구 결과

실행 중에는 완료한 목표만 누적한다. 모든 조건은 fresh large/64/H32/100회이며 각 모델은 초기·최종32환경으로 평가한다.

| 조건 | 목표 | seed | 완료 | 달성 /32 | clean≥0.1초 /32 | 실패 /32 | 최소거리 중앙값 mm |
|---|---|---:|---|---:|---:|---:|---:|
| baseline | index_s3_f4 | 7 | 예 | 0 | 0 | 0 | 66.86 |
| baseline | middle_s3_f6 | 7 | 예 | 0 | 0 | 0 | 64.31 |
| baseline | ring_s2_f7 | 7 | 예 | 0 | 0 | 0 | 63.95 |
| baseline | pinky_s3_f9 | 7 | 예 | 0 | 0 | 0 | 56.65 |
| exploration | index_s3_f4 | 7 | 예 | 0 | 0 | 0 | 66.51 |
| exploration | middle_s3_f6 | 7 | 예 | 0 | 0 | 0 | 64.87 |
| exploration | ring_s2_f7 | 7 | 예 | 0 | 0 | 0 | 69.34 |
| exploration | pinky_s3_f9 | 7 | 예 | 0 | 0 | 0 | 52.63 |
| lr | index_s3_f4 | 7 | 예 | 0 | 0 | 0 | 79.76 |
| lr | middle_s3_f6 | 7 | 예 | 0 | 0 | 0 | 63.05 |
| lr | ring_s2_f7 | 7 | 예 | 0 | 0 | 0 | 73.14 |
| lr | pinky_s3_f9 | 7 | 예 | 0 | 0 | 0 | 47.09 |
| combined | index_s3_f4 | 7 | 예 | 0 | 0 | 0 | 71.21 |
| combined | middle_s3_f6 | 7 | 예 | 0 | 0 | 0 | 69.57 |
| combined | ring_s2_f7 | 7 | 예 | 0 | 0 | 0 | 87.72 |
| combined | pinky_s3_f9 | 7 | 예 | 0 | 0 | 32 | 21.02 |
| sequential | index_s3_f4 | 7 | 예 | 0 | 0 | 0 | 66.84 |
| sequential | middle_s3_f6 | 7 | 예 | 0 | 0 | 1 | 69.23 |
| sequential | ring_s2_f7 | 7 | 예 | 0 | 0 | 0 | 59.45 |
| sequential | pinky_s3_f9 | 7 | 예 | 0 | 0 | 0 | 54.71 |

후보 선택은 사전 고정한 PLAN.md 기준이며 병렬환경32개를 독립 학습seed 반복으로 해석하지 않는다. 생산 기본값은 변경하지 않는다.

선택·재확인 결과:

```json
{
  "screen_candidates": [],
  "confirmation_seed": 17,
  "confirmed": [],
  "default_changed": false,
  "reason": "no_condition_cleared_prespecified_screen"
}
```

## 실제 정책 영상

- baseline_pinky_s3_f9_s7: 촬영 에피소드 달성=False
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/baseline_pinky_s3_f9_s7/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/baseline_pinky_s3_f9_s7/fullbody.mp4)
- exploration_pinky_s3_f9_s7: 촬영 에피소드 달성=False
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/exploration_pinky_s3_f9_s7/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/exploration_pinky_s3_f9_s7/fullbody.mp4)
- lr_pinky_s3_f9_s7: 촬영 에피소드 달성=False
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/lr_pinky_s3_f9_s7/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/lr_pinky_s3_f9_s7/fullbody.mp4)
- combined_pinky_s3_f9_s7: 촬영 에피소드 달성=False
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/combined_pinky_s3_f9_s7/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/combined_pinky_s3_f9_s7/fullbody.mp4)
- sequential_pinky_s3_f9_s7: 촬영 에피소드 달성=False
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/sequential_pinky_s3_f9_s7/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/exploration_lr_sequence_v1/video/sequential_pinky_s3_f9_s7/fullbody.mp4)