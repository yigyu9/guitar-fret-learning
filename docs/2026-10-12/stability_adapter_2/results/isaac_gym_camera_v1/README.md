# Isaac Gym native camera: 초기 장면

2026-10-07. 사용자가 요청한 Isaac Gym 카메라 캡처다. 앞선 `self_collision_v1` 이미지와 영상은 저장된 native 자세를 MuJoCo에서 source geometry로 재구성한 결과였다. 아래 `front/` PNG는 Isaac Gym camera sensor가 직접 저장했다.

## 캡처 장면

`front/`는 self-collision ON의 `near2µm` 초기 상태다. `capture.json`에 `physics_steps=0`, `initial_state_exact=true`, `render_preserves_state=true`, `zero_physics_steps=true`, `inputs_unchanged=true`가 기록됐다. 이 이미지는 step 0의 장면이지 rollout이나 충돌 성공을 보여주지 않는다. strap은 Isaac Gym native scene에 렌더 형상이 없어 화면에 나타나지 않는다.

상태 비교는 body/DOF full-state와 collision-mask audit를 포함한다. 관절 목표 getter를 읽어 native target 전달값까지 대조한 검사는 아니다.

![Isaac Gym native camera의 전신 시야, 초기 step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/whole_body.png)

![Isaac Gym native camera의 손 visual geometry, 초기 step 0](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/hands.png)

`hands_collision.png`도 보존했다. 검증 결과 이 파일은 `hands.png`와 byte-identical이므로 별도 collision geometry 장면을 확인할 수 없고, collision camera는 usable하지 않다. 두 파일이 같은 이유는 확인되지 않았다.

## 실행·검증 범위

캡처는 `graphics_device_id=0`을 사용했고 로그에는 PhysX CPU device와 GPU pipeline 비활성화가 기록됐다. 이는 GPU 실행이나 특정 Vulkan backend, Lavapipe 사용을 확인한 결과가 아니다. 로그의 CUDA/visual-geometry 경고도 보존했다. `front/capture.json`의 73개 입력과 PNG 3개 출력 SHA는 현재 파일과 일치하고 캡처 state/zero-step/input checks 및 mask audit가 통과했다. 루트 검증 기록은 default/front 두 캡처에서 초기 상태가 정확히 일치하고 physics step이 0이라고 확인한다.

실행 producer 사본은 [`front/producer.py`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/producer.py)와 [`default/producer.py`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/default/producer.py)에 보존했다. root verification은 두 producer 사본이 각각의 source hash와 일치한다고 기록한다.

촬영 당시 producer의 입력 SHA 목록에는 이전 ON `report.json` 자체가 포함되지 않았다. 최종 [audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/verification.json)에서 해당 report SHA를 보존된 이전 실험 inventory와 연결해 일치를 확인했다. 실행 당시 producer 사본은 그대로 보존했다. [원본·이전 산출물 보존 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/preservation_verification.json)도 통과했다.

이 카메라 이미지는 초기 시점의 시각 자료이며 접촉력, 충돌 성공, cooked collision geometry, 안정성의 증거가 아니다. capture 구현은 [capture_isaac_gym_initial.py](/home/ajou/yigyu/3/stability_adapter_2/capture_isaac_gym_initial.py:1), 절차는 [ISAAC_GYM_CAMERA_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/ISAAC_GYM_CAMERA_PLAN.md:1)에 있다. 원본 카메라 로그는 [`front.log`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/logs/front.log), 결과 검사는 [`verification.json`](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/verification.json), 파일·줄 인덱스는 [CHANGED_FILES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/CHANGED_FILES.md:1)에 기록했다.

[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/review.md:9)는 완료됐고 남은 지적사항은 없다.
