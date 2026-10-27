# 환경 기반(native) 관측·제어 경로 점검

## 결과 그림

![중립 목표와 작은 목표 움직임의 실제 native 시뮬레이션 frame 00000/00150 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/initial_final_montage.png)

그림은 원본 `whole_body`·`hands` 카메라의 PNG frame 00000(physics step 0, 0초)과 00150(step 1200, 물리 5.000초)을 직접 사용했습니다. 각 이미지 SHA-256은 해당 실행의 `capture.json` 프레임 기록과 일치합니다. 장면에는 체크보드 바닥, 회색/흰색 휴머노이드, 파란 기타가 보입니다. 재생 파일은 151 frame, 30 fps로 인코딩되어 표시 길이가 5.0333초입니다. 이는 물리 적분 5.000초와 구분됩니다.

## 설정과 검증 범위

이번 점검은 CPU PhysX와 Vulkan software graphics를 사용하는 native Isaac Gym 환경에서 실행됐습니다. 기타는 자유 물체이며 스트랩은 꺼져 있고, root와 하체는 고정했습니다. 상체 정책 입력·목표 경로는 81 DOF이고, 중립 목표와 작은 목표 움직임의 두 실행은 같은 초기 native 상태에서 시작했습니다. 제어는 60 Hz, 물리 적분은 240 Hz로 5초 동안 진행했습니다. 관측은 음악 조건을 뺀 기반 548차원이고, 81차원 native 목표 제출 경로를 확인한 것입니다.

아래의 목표 변화량은 명령한 관절 목표의 최대 차이이고, 실제 변화량은 시뮬레이션에서 초기 q로부터 관찰된 native 관절 q 차이입니다. 두 값은 서로 다른 양입니다. 작은 목표 변화가 작더라도 환경의 실제 관절 움직임이나 기타 지지 안정성을 보장하지 않습니다.

| 관절 그룹 | 작은 목표 최대 변화량 (rad) | 중립 실행 실제 최대 Δq (deg) | 작은 목표 실행 실제 최대 Δq (deg) |
|---|---:|---:|---:|
| 몸통 | 0.0100 | 2.492 | 2.518 |
| 머리 | 0.0200 | 1.492 | 1.531 |
| 팔 | 0.0200 | 16.417 | 16.497 |
| 손가락 | 0.0300 | 6.771 | 6.776 |

기타 최대 위치 변위는 중립 목표에서 111.790 mm, 작은 목표 움직임에서 113.778 mm였습니다. 두 실행 모두 기타 위치 허용 상자 밖으로 벗어난 표본이 301개 중 288개였고, 최대 회전 변화 진단값은 각각 19.486°와 19.888°였습니다. 이 위치 이탈과 큰 자세 변화 때문에 초기 지지 조건은 안정성 성공으로 판정되지 않았습니다.

왼손바닥–기타 접촉은 각 실행 301개 평가 표본 중 284개에서 기록됐습니다. 이는 `LH:palm`과 기타의 어떤 body 사이 접촉 여부이며, 넥을 지지하거나 하중을 견뎠다는 인증이 아닙니다. 따라서 접촉 횟수만으로 지지 성공을 주장하지 않습니다.

## 범위와 한계

두 실행 모두 물리 초기화, 기반 548D 관측, 81D 목표 제출의 smoke test입니다. 보고서의 `training_ready`와 `stability_success`는 모두 `false`이며, 새 학습·PPO 실행은 없었습니다. 음악 이벤트를 포함한 최종 관측 차원, 음악 조건, 보상 및 종료 조건은 아직 확정·검증되지 않았습니다. 이 결과는 학습 준비 완료나 음악 연주 성능의 근거가 아닙니다.

![중립 목표 전체 몸체 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/media/whole_body.mp4)

![중립 목표 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/media/hands.mp4)

![작은 목표 움직임 전체 몸체 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_small_motion_v2/media/whole_body.mp4)

![작은 목표 움직임 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_small_motion_v2/media/hands.mp4)

## 원자료

- 변경 파일 색인: [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/CHANGED_FILES.md)
- 분석 결과: [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/analysis.json)
- 중립 실행 보고서·프레임 기록: [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/report.json), [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_neutral_v2/media/capture.json)
- 작은 목표 실행 보고서·프레임 기록: [report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_small_motion_v2/report.json), [capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/environment_foundation_v1/native_small_motion_v2/media/capture.json)
- 실행 조건: [environment_foundation_v1.json](/home/ajou/yigyu/3/stability_adapter_2/environment_foundation_v1.json)
