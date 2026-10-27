# Strike 10,000 checkpoint 영상 및 로그 분석

- 분석 시점: 2026-09-21 09:09 KST 부근
- run: `strike/training/runs/20260920_Jazz1_sync_baseline`
- 곡: `02_Jazz1-200-B_solo` (42 single-pick, strum 없음)
- 영상 기준: `strike_010000.pt`

## 선택 이유

반복 평가상 절대 최고는 9,000 checkpoint이며 타이밍 p95가 5.519ms다.
10,000 checkpoint도 고정 64회 전체곡 평가에서 F1, recall, precision,
무오류 전체곡 비율이 모두 1.0이고 타이밍 p95는 5.628ms다.
학습이 다른 PC에서 계속 실행 중이므로 별도 simulator를 추가 실행하지 않고,
최신 저장본이면서 품질 기준을 모두 만족한 10,000 checkpoint의 자동 전체곡 영상을 복사했다.

## 학습 상태

- S3 진입: iteration 1,128
- 원곡 속도 도달: iteration 3,259
- curriculum 완료: iteration 3,559
- 완료 후 학습률 배율: 0.25
  - actor: `7.5e-7`
  - critic: `7.5e-5`
- 분석 중 로그는 약 iteration 10,082까지 계속 갱신됨
- 원곡 holdout F1: 1.0, 연속 통과 17회
- `quality=pending`인 개별 학습 행은 hard-window 표본이라 uniform evidence가 없는 경우다.
  원곡 holdout 실패나 정책 회복 필요를 뜻하지 않는다.

## 10,000 전체곡 반복 평가

| 지표 | 값 |
|---|---:|
| 평가 episode | 64 |
| F1 / recall / precision | 1.0 / 1.0 / 1.0 |
| 무오류 전체곡 비율 | 1.0 |
| 오타현률 | 0.0 |
| 타이밍 p95 | 5.628ms |
| grip quality mean | 0.998110 |
| 안전 / grip eligibility | 통과 / 통과 |

최근 9,500~9,999 학습 window 평균은 F1 0.9934, recall 0.9887,
오타현률 0.00163, 타이밍 p95 7.21ms, grip 0.99826이다.
학습 중 무작위·hard 표본은 deterministic 원곡 평가보다 어렵기 때문에 두 수치를 직접 같은
성공률로 해석하지 않는다. 직전 500-window보다 F1·recall·오타현·타이밍과 안전 종료가 모두
소폭 개선됐으며, 현재까지 완료 후 학습률 감소의 명확한 성능 붕괴는 보이지 않는다.

## 영상 검수 범위

두 영상은 같은 deterministic 전체곡 rollout을 remembered/current 카메라로 촬영한 것이다.
길이는 각각 14.8초이며 42개 계획 타현을 모두 완료했고 blocked/wrong crossing은 0이다.
수치 통과와 별개로 손목·손가락 자세, 피크가 목표 줄을 실제로 통과하는 방향,
회복 시 불필요한 왕복이 없는지는 사람이 두 카메라에서 확인해야 한다.

## 줄·피크 진단 오버레이

같은 10,000 checkpoint의 전체곡 rollout에 기타 줄과 피크 기준점을 겹쳐 표시한
remembered/current 영상도 생성했다. 두 영상은 440 frame, 30fps, 14.667초이며
42개 계획 타현이 끝날 때까지 중간 종료 없이 촬영됐다.

- 연회색: 여섯 기타 줄
- 연노랑: 현재 목표 줄
- 파랑: 허용 타현 영역
- 초록: 선호 타현 영역
- 주황/노랑: 현재 목표 lane의 외곽/중심
- 분홍 점과 꼬리: `RH:pick` 가상 기준점과 최근 이동 궤적

오버레이는 렌더 뒤에 투영한 진단 정보다. rigid pick이나 줄 충돌체를 추가하지 않으며
시뮬레이션 물리와 정책 입력에는 영향을 주지 않는다.

## 파일

- `strike_010000_full_song_remembered.mp4`
- `strike_010000_full_song_current.mp4`
- `strike_010000_full_song.json`
- `strike_010000.full_song.eval.json`
- `strike_010000_full_song_remembered_zone_pick.mp4`
- `strike_010000_full_song_current_zone_pick.mp4`
- `strike_010000_full_song_zone_pick.json`
