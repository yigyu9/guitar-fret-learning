# Isaac Gym native camera 결과 인덱스

이 단계는 기존 초기 상태를 물리 진행 없이 Isaac Gym native camera로 캡처하고 결과를 문서화했다. physics model, 설정, 이전 실행과 `self_collision_v1` 산출물은 수정하지 않았다.

## 산출물·검증

- [결과 설명과 native camera 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/README.md:1).
- 전신 [whole_body.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/whole_body.png), 손 visual geometry [hands.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/hands.png); collision camera [hands_collision.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/hands_collision.png)는 usable하지 않아 장면 이미지로 사용하지 않는다.
- [front/capture.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/capture.json): capture checks, mask audit, 73 input SHA, 3 output SHA.
- [front/attempt.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/attempt.json), [front.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/logs/front.log), [root verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/verification.json).
- 실행 당시 producer 사본: [front/producer.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/front/producer.py), [default/producer.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/default/producer.py); root verification은 두 사본의 SHA 일치를 확인했다.
- 첫 view 시도와 PNG는 [default/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/default/)에 보존했다. `front/`는 같은 초기 state의 전신/손 view와 색상 조정 기록이다.

## 구현·계획 링크

- [capture_isaac_gym_initial.py:14](/home/ajou/yigyu/3/stability_adapter_2/capture_isaac_gym_initial.py:14) graphics wrapper, [:25](/home/ajou/yigyu/3/stability_adapter_2/capture_isaac_gym_initial.py:25) camera scene, [:59](/home/ajou/yigyu/3/stability_adapter_2/capture_isaac_gym_initial.py:59) capture entry, [:88](/home/ajou/yigyu/3/stability_adapter_2/capture_isaac_gym_initial.py:88) native image write.
- [ISAAC_GYM_CAMERA_PLAN.md:1](/home/ajou/yigyu/3/stability_adapter_2/ISAAC_GYM_CAMERA_PLAN.md:1), [capture checklist:19](/home/ajou/yigyu/3/stability_adapter_2/ISAAC_GYM_CAMERA_PLAN.md:19), [project README:1](/home/ajou/yigyu/3/stability_adapter_2/README.md:1).
- [dated results index:323](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:323), [VISUAL_REPORT §54:988](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:988).

[독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/review.md:9)는 완료됐고 남은 지적사항은 없다.

최종 구현·문서 사본과 SHA는 [source_final_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/source_final_manifest.json)에, 결과 파일 목록은 [artifact_inventory.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/artifact_inventory.json)에 저장했다.
