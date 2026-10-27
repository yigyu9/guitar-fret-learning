# 기존 최선 실행의 전체 재생

2026-10-07. 54개 기존 1초 이상 실행 중 전체 구간 최대 기타 위치·회전 오차가 모두 가장 작은 실행을 골랐다. 선택 실행은 `left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125`이며, 최대 위치 오차 73.268255 mm, 최대 회전 오차 13.439339°다. 저장된 `states.json`과 `trace.json`의 241개 시점(0–240, 240 Hz)을 생략하거나 보간하지 않았다.

## 영상

- [0.25배속, 60 fps, 4.0167초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/videos/best_run_slow_0p25x.mp4)
- [실시간, 240 fps, 1.0042초 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/videos/best_run_realtime_1x.mp4)
- 미리보기: [시작](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/images/preview_step_000.png), [중간](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/images/preview_step_120.png), [종료](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/images/preview_step_240.png)

두 영상은 전신·기타와 손·기타 넥을 나란히 보여주며 저장 trace의 strap route를 주황색으로 표시한다. 인체는 회색, 기타는 파랑, 왼손은 초록, 오른손은 자홍색이다. 이는 저장된 native 자세를 source collision geometry에 적용한 재구성 영상이며 PhysX 렌더가 아니다. 프레임마다 source 형상만 갱신하고 `mj_forward`로 표시 상태를 계산했다. native simulation 초기화와 physics step은 없었다.

선정 실행의 기록된 `stability_success`는 false다. 종료 시에도 선속도 약 0.293 m/s, 각속도 약 1.192 rad/s로 움직임이 남아 있다. 따라서 영상은 기존 후보의 전체 움직임을 보여줄 뿐, 안정성이나 연주 성공을 인증하지 않는다.

## 재생성 및 provenance

실행 코드: [render_best_run_video.py](/home/ajou/yigyu/3/stability_adapter_2/render_best_run_video.py). 결과물·선정 입력·source geometry asset·helper의 SHA-256, camera, 241개 frame mapping, `mj_forward` 호출 구분, ffmpeg 명령과 ffprobe 결과는 [render manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/render_manifest.json)에 기록했다. 실행 명령·환경·종료 상태는 [실행 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/best_run_video_v1/render_v2/render_execution.json)에 있다. 첫 제작본은 보존했고, `render_v2/`가 수정된 producer와 일치하는 최종본이다.

[독립 검수](review.md:7)를 완료했다. 실제 MP4의 시작/중간/종료 decode와 두 영상241프레임·codec·SHA를 확인했다.
