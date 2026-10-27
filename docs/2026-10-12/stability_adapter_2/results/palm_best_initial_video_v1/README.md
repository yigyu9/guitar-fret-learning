# Isaac Gym에서 다시 녹화한 시작 자세

[영상 보기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/best_initial_state_isaac_gym.mp4)

최근 12축 비교에서 손과 기타 지표가 함께 낮고 양의 손바닥 접촉 반응도 관찰된 `axis_00` 조건을 골랐다. 같은 seed의 L_Thorax_x PD 목표에 +0.005 rad를 요청했다. 이는 새 초기 관절 배치가 아니라 동일한 초기 배치에 대한 작은 목표각 보정 비교다. α=.45 기준 대비 0.1초 기타 최대 오차는 위치 5.341201→5.163317 mm, 회전 1.006166→0.979721°로 줄었고 손 끝점 오차는 9.288558→9.170356 mm로 줄었다. 양의 palm raw λ는 2 physics step의 두 contact 행뿐이어서 지속 지지는 아니다.

영상은 실제 Isaac Gym/PhysX 카메라의 front·side 두 시점을 0–0.1초 동안 녹화했다. 저장 pose만 그린 영상이 아니다. 14개 카메라 정지화면은 7개 동기화된 시점(front/side 쌍)으로 합쳐져 15fps로 재생된다(대략 0.25배속). 녹화 재생 검사는 모두 통과했다: `commands_preserve_states`, `render_preserves_states`, `camera_five_raw_exact`, `inputs_unchanged`, `images_14`.

[실제 카메라 캡처와 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/isaac_gym_capture/report.json), [ffprobe·인코더·입력/출력 SHA](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/video_execution.json). 첫 인코딩은 합성 시점 수 검사를 통과하지 못해 [시도 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/artifacts_attempt_v1/)에 별도 보존했다.

## 요청한 5초 front-view 영상

[앞에서 본 5초 영상 보기](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/front_view_5s_slowmotion.mp4)

이 파일은 검증된 0.1초 Isaac Gym 원본 7개 시점을 약0.02배속으로 표시해 길이를5초로 맞춘 front-view slow-motion이다. 매끄럽게 보이도록 새 포즈를 만들어내지 않았으며, 7개 실제 렌더 시점을 반복 표시한다. **이는5초 물리 실행 영상이 아니다.** 동일 목표로 별도5초(1200step) PhysX 시뮬레이션도 시도했다. 실제 352step(1.467초)를 진행했으나 다음 step에서 SIGSEGV로 종료됐고, 1초 시점에는 기타 위치오차85.33mm/회전오차11.59°였다. [실패한 장기 실행과 partial camera 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/five_second_physx_attempt.json).

[5초 영상 재생·프레임·입력 SHA/ffprobe](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_best_initial_video_v1/front_view_5s_execution.json).
