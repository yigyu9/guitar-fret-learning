# Isaac Gym 조기 종료 원인과 5초 재생 영상

## 결론

앞선 갑작스러운 종료는 humanoid와 기타가 실제로 부딪혀 물리 엔진이 종료된 것이 아니라, Isaac Gym 네이티브 코드에서 발생한 SIGSEGV(잘못된 메모리 접근에 의한 프로세스 충돌)입니다. PhysX 접촉 기록에는 기타·인체·의자·바닥 사이 접촉이 있지만, 통제된 5초 실행은 이 접촉을 포함한 채 유한한 상태로 1200스텝을 마쳤습니다. 따라서 접촉 자체가 종료 원인이라는 증거는 없습니다.

정확한 네이티브 원인은 아직 특정할 수 없습니다. 초기 실패들은 물리 진행 중 카메라 렌더링이 섞인 경우에 나왔지만, 후속 대조에서는 렌더 한 번 뒤 5초 물리와 정상 종료가 성공했고, 두 번 렌더하는 재시험도 `step_graphics`, `render_all_camera_sensors`, 이미지 저장, 시뮬레이터 닫기까지 모두 성공했습니다. 즉 렌더링과 연관된 간헐적 런타임 충돌 가능성은 남지만, 반복 렌더만으로 재현되는 문제라고 단정할 수 없습니다.

실행 로그는 PhysX CPU, GPU pipeline 비활성 상태이며 그래픽 CUDA context 생성 실패와 visual geom 누락을 보고합니다. 이 환경 구성이 그래픽 경로 불안정에 기여했을 가능성은 있으나, 인과관계는 확인되지 않았습니다. GDB는 host의 ptrace 제한으로 붙지 못해 네이티브 backtrace도 확보하지 못했습니다.

## 실제 Isaac Gym 물리 실행 영상

![Isaac Gym PhysX 실제 5초 실행, 정면 전신](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_crash_diagnosis_v1/front_fullbody_physx_video_v1/front_fullbody_physx_5s.mp4)

영상은 Isaac Gym PhysX에서 같은 axis_00 시작 상태와 저장된 팔 목표를 재생해 만들었습니다. 0초부터 5초까지 0.25초 간격의 21개 시점 각각을 별도의 새 시뮬레이터에서 재생하고, 각 환경에서 카메라 프레임을 한 번 렌더했습니다. 이 방식은 영상 프레임을 물리 상태에서 직접 얻으면서 한 프로세스 안의 반복 렌더링을 피합니다. 모든 프레임의 관절·기타 상태 표본은 기준 1201개 상태 trace와 정확히 일치합니다. MP4는 4fps라 5.25초 길이이며, 마지막 프레임은 물리 시각 5.0초입니다. 정면 전신이 보이도록 원본의 검은 하늘 여백만 잘랐습니다.

![5초 종료 시점의 전신 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_crash_diagnosis_v1/front_fullbody_physx_video_v1/preview_final_cropped.png)

단, 영상의 최종 기타 위치 오차는 242.5mm, 회전 오차는 73.38도입니다. 즉 실제 시뮬레이션 영상은 제공되지만, 현재 저장된 팔 제어 목표만으로 기타를 안정화하지 못한 결과입니다. 물리 안정성 실패와 네이티브 프로세스 충돌은 별개의 문제입니다.

## 진단 파일

- `diagnosis_summary.json`: 실패·대조 실행 및 근거를 구조화한 요약
- `run_result.json`, `trace.jsonl`, `contact_summary.jsonl`: 카메라 없는 5초 CPU PhysX 실행과 접촉 기록
- `single_sensor_no_render_v1/`: 센서를 시작 전 만들고 5초 후 한 번만 렌더한 실행
- `one_midrun_single_render_v1/`: 0.5초에 한 번 렌더 후 나머지 물리 진행과 닫기까지 성공한 실행
- `one_midrun_render_v1/attempt_failure.json`: 두 번째 렌더 단계에서 발생한 초기 간헐 실패 및 후속 재시험 기록
- `second_render_stage_probe_v1/runner.log`: 두 렌더와 닫기 각 단계의 재시험 로그
- `front_fullbody_physx_video_v1/`: 21개 원본 Isaac Gym 프레임, 프레임별 trace 일치 검증, MP4와 캡처 스크립트
- `gdb_run.log`: ptrace 제한으로 backtrace를 얻지 못한 기록
