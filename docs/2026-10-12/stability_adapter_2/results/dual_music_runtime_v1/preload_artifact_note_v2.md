# Native preload 비교 결과

![세 조건 native whole-body frame 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_comparison_v2.png)

![60 Hz trace의 위치 변위와 회전 변화](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_curves_v2.png)

세 조건은 같은 초기 native 상태를 사용합니다. 중립 조건은 기존 neutral 저장 run을 재사용했고, `preload=0.5`와 `preload=1.0`은 각각 별도 5초 run입니다. 모든 run은 60 Hz control/trace, 240 Hz 물리, 1200 physics step을 기록했습니다. 그림의 실제 Isaac Gym native camera 프레임은 **frame 00000/step 0/t=0.0초, frame 00060/step 480/t=2.0초, frame 00150/step 1200/t=5.0초**이며 캡처 metadata의 PNG SHA-256과 대조했습니다. 영상은 30 fps로 저장되어 있지만, 표와 곡선의 시간축은 물리 시각입니다.

## 비교값

위치 변위는 기타 actor 위치의 초기값 대비 유클리드 거리(mm), 회전 변화는 초기 quaternion 대비 shortest-path geodesic 각도(deg)입니다. 위치 상자 초과값은 분석기가 보고한 **core actor-root position-box max outside norm (mm)**이고, 회전 허용 영역의 포함 판정은 이 수치에 포함되지 않습니다.

| 조건 | 최대 위치 변위 (mm) | 최종 위치 변위 (mm) | 최대 geodesic 회전 (°) | 최종 geodesic 회전 (°) | core position-box 최대 초과 (mm) | position-box 초과 표본 |
|---|---:|---:|---:|---:|---:|---:|
| 기준 중립 (preload 0) | 111.790 | 111.787 | 19.486 | 19.485 | 34.335 | 288/301 |
| preload 0.5 | 75.331 | 75.330 | 13.910 | 12.294 | 11.262 | 273/301 |
| preload 1.0 · 선택 | 46.306 | 46.298 | 9.179 | 7.626 | 0.000 | 0/301 |

진단 선택 조건은 `preload=1.0`입니다. 세 비교 중 core actor-root 위치 상자 초과가 0.000 mm였고, 초기 대비 기타 이동과 회전도 중립 기준보다 작았습니다. 이는 이 초기화에서 drift가 개선됐다는 뜻입니다. 최대 위치 변위 46.306 mm와 회전 변화 9.179°가 남아 있으며, 원 분석의 `stability_success=false`·`training_ready=false`를 바꾸지 않습니다. SO(3) 허용 영역 전체, 지지 접촉 인증, 음악 detector/이벤트, 두 음악 checkpoint 연결이나 연주 성능의 인증이 아닙니다.

## 실행 범위와 상태

입력 run은 Isaac Gym native camera, CPU PhysX, Vulkan software graphics, strap OFF, root/하체 fixed, 자유 기타 조건입니다. 새 preload 두 run은 각각 5.0 물리 초를 완료했고, 이 후처리에서 새 물리 실행·정책 추론·학습은 하지 않았습니다. 새 run 보고서의 `dual_checkpoints_connected=false`, `training_updates=0` 상태를 유지합니다.

## 원자료 및 실행물

- [preload 분석 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload_analysis_v2.json)
- [기준 neutral trace](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/trace.json)
- [preload 0.5 trace/report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload050_v2/trace.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload050_v2/report.json)
- [preload 1.0 trace/report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload100_v2/trace.json), [report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload100_v2/report.json)
- [기준 whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/media/whole_body.mp4)
- [preload 0.5 whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload050_v2/media/whole_body.mp4)
- [preload 1.0 whole-body 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/dual_music_runtime_v1/preload100_v2/media/whole_body.mp4)

그림 픽셀 크기: 비교 몽타주 1902×1250, 곡선 2400×1050.
