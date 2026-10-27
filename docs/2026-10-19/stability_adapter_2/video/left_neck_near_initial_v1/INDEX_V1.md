# 왼손 넥 근접 초기 배치 · 영상 색인 V1

기존 native 실행에서 만든 MP4 10개를 재인코딩 없이 byte-exact 복사했습니다. hold_v2는 1.833초 안전 중단으로 짧은 부분 영상이며, 나머지 hold_v1/v3/v4는 5초 관찰, pair_v1은 2.433초의 source 종료 영상입니다. 재생 길이는 30fps 영상 프레임 기준이며 물리 경과 시간과 다를 수 있습니다. source/copy SHA-256 및 ffprobe는 [manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/manifest_v1.json)에 기록했습니다.

## hold_v1 · 기본 위치 제어

물리 경과 5.000000초, 1200 step, 완료=true, 종료=`five_second_observation`.

- [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v1/whole_body.mp4) — 151프레임, 30/1fps, 재생 5.033333초
- [왼손·기타 넥 방향 확대 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v1/hands.mp4) — 151프레임, 30/1fps, 재생 5.033333초

## hold_v2 · 높은 위치 제어 게인

물리 경과 1.833333초, 440 step, 완료=false, 종료=`None`.
속도 안전 검사에서 중단된 부분 실행이며 5초 결과가 아닙니다.

- [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v2/whole_body.mp4) — 56프레임, 30/1fps, 재생 1.866667초
- [왼손·기타 넥 방향 확대 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v2/hands.mp4) — 56프레임, 30/1fps, 재생 1.866667초

## hold_v3 · 낮춘 명시 게인

물리 경과 5.000000초, 1200 step, 완료=true, 종료=`five_second_observation`.

- [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v3/whole_body.mp4) — 151프레임, 30/1fps, 재생 5.033333초
- [왼손·기타 넥 방향 확대 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v3/hands.mp4) — 151프레임, 30/1fps, 재생 5.033333초

## hold_v4 · 손목 준비 과제 포함

물리 경과 5.000000초, 1200 step, 완료=true, 종료=`five_second_observation`.

- [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v4/whole_body.mp4) — 151프레임, 30/1fps, 재생 5.033333초
- [왼손·기타 넥 방향 확대 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/hold_v4/hands.mp4) — 151프레임, 30/1fps, 재생 5.033333초

## pair_v1 · 두 체크포인트 연결

물리 경과 2.433333초, 584 step, 완료=true, 종료=`first_source_terminal`.
두 체크포인트 연결 뒤 첫 source 종료 조건에서 끝났으며 곡 완주가 아닙니다.

- [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/pair_v1/whole_body.mp4) — 74프레임, 30/1fps, 재생 2.466667초
- [왼손·기타 넥 방향 확대 MP4](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/left_neck_near_initial_v1/pair_v1/hands.mp4) — 74프레임, 30/1fps, 재생 2.466667초

