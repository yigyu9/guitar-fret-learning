# 두 체크포인트 연결 · 영상 색인 V2

manifest에 기록된 byte-exact 원본 복사본은 총 4개입니다: 새 checkpoint 연결 실행의 전신·손 영상 2개와 연결 직전 shoulder-forward-10-mm 정지 기준의 전신·손 영상 2개입니다. 이 가운데 이번 연결 물리 실행의 영상은 2개이며, 이전 기준 영상은 별도 사례입니다.

연결 실행은 물리 2.05초에 source terminal로 종료했고 영상은 63프레임 ÷ 30fps = 2.1초입니다. 이전 기준 사례는 물리 5.0초, 영상은 151프레임 ÷ 30fps = 5.033333초입니다. 영상은 재인코딩하지 않았습니다. SHA와 ffprobe는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/manifest_v1.json)에 있습니다.

## 새 연결 실행 · checkpoint_connection

- [전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/checkpoint_connection/whole_body.mp4) — 63프레임, 30/1fps, 재생 2.100000초; 물리 실행은 2.05초에서 종료
- [손·기타 넥 방향 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/checkpoint_connection/hands.mp4) — 63프레임, 30/1fps, 재생 2.100000초; 물리 실행은 2.05초에서 종료

## 이전 5초 정지 기준 · baseline_shoulder10mm

- [전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/baseline_shoulder10mm/whole_body.mp4) — 151프레임, 30/1fps, 재생 5.033333초; 이전 별도 기준 실행
- [손·기타 넥 방향 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/baseline_shoulder10mm/hands.mp4) — 151프레임, 30/1fps, 재생 5.033333초; 이전 별도 기준 실행

사본 수는 파일 수이며 독립된 실험 조건 수를 뜻하지 않습니다. [SHA-256 manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/dual_checkpoint_shoulder_v1/manifest_v1.json)
