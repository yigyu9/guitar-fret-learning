# 실제 학습 환경의 가상 단음 압현 결과

실행 상태: complete. 평가 완료 목표: 16/16.

large·64환경·H32·100회·seed 7, 목표마다 새 정책으로 학습했다. 목표는 3.0~5.5초이며 기존 기준인 연속 clean 1.0초를 달성해야 한다. 기존 J33 보상·제어·조기 종료를 유지했다. 각 모델은 16환경에서 평가했다.

성공 횟수는 음 달성과 물리·손목 실패가 없는 평가 에피소드 수이다. 이는 1개 seed의 짧은 학습이며 실패가 곧 물리적 도달 불가능을 뜻하지 않는다.

| 목표 | 초기→최종 성공 /16 | 최종 최장 clean (초) | 평균 보상 초기→최종 |
|---|---:|---:|---:|
| index_s3_f6 | 0 → 0 | 0.000 | -0.291 → -0.154 |
| index_s3_f4 | 0 → 0 | 0.000 | -0.249 → -0.106 |
| index_s3_f9 | 0 → 0 | 0.000 | -0.070 → -0.082 |
| index_s2_f7 | 0 → 0 | 0.000 | -0.218 → -0.156 |
| middle_s3_f6 | 0 → 0 | 0.000 | -0.285 → -0.111 |
| middle_s1_f10 | 0 → 0 | 0.000 | -0.067 → -0.063 |
| middle_s3_f7 | 0 → 0 | 0.000 | -0.284 → -0.162 |
| middle_s2_f8 | 0 → 0 | 0.000 | -0.204 → -0.138 |
| ring_s3_f7 | 0 → 0 | 0.000 | -0.322 → -0.127 |
| ring_s2_f7 | 0 → 0 | 0.000 | -0.310 → -0.115 |
| ring_s4_f11 | 0 → 0 | 0.000 | -0.082 → -0.075 |
| ring_s4_f9 | 0 → 0 | 0.000 | -0.232 → -0.205 |
| pinky_s4_f11 | 0 → 0 | 0.000 | -0.175 → -0.154 |
| pinky_s3_f9 | 0 → 0 | 0.000 | -0.375 → -0.223 |
| pinky_s4_f12 | 0 → 0 | 0.000 | -0.104 → -0.102 |
| pinky_s2_f10 | 0 → 0 | 0.000 | -0.270 → -0.181 |

## 실제 정책 영상

영상은 별도 재평가의 환경 0을 촬영했다. 평가에서 성공한 목표라도 이 촬영 에피소드의 성공 여부는 아래에 따로 표시한다.

- index_s3_f9: 촬영 에피소드 미달성
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/index_s3_f9/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/index_s3_f9/fullbody.mp4)

- middle_s1_f10: 촬영 에피소드 미달성
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/middle_s1_f10/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/middle_s1_f10/fullbody.mp4)

- ring_s4_f11: 촬영 에피소드 미달성
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/ring_s4_f11/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/ring_s4_f11/fullbody.mp4)

- pinky_s4_f12: 촬영 에피소드 미달성
  - [hand](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/pinky_s4_f12/hand.mp4)
  - [fullbody](/home/ajou/yigyu/3/docs/2026-11-02/압현성공/video/learning/pinky_s4_f12/fullbody.mp4)

과거 기하 후보 재생 결과는 상위 디렉토리에 별도로 보존했다. 본 표와 video/learning만 실제 PPO 학습 결과이다.
