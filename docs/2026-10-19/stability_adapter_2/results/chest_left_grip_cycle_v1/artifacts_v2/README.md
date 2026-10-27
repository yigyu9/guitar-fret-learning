# 왼손 기타 사이클 — 정규화된 자세 계산

이 요약은 [native cycle 측정](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/analysis_v1.json>)과 실제 native 영상·프레임을 설명한다. 16초, 3,840 physics step 실행은 완료됐고 기타는 자유 동역학이었다. 이전 V1 CSV/그래프는 native quaternion을 단위화하지 않고 회전을 계산해 pointwise 자세값에 오차가 있었다. V2에서는 SciPy `Rotation.from_quat`으로 모든 endpoint quaternion을 정규화한 뒤 `center_W = actor_position_W + rotation.apply(guitar_centre_G)` 및 `SO(3) = (R0.inv() * Ri).magnitude()`로 재계산했다. [새 CSV](./motion_samples_240Hz_v2.csv)의 3,841개 시점을 SciPy 기준과 각각 비교했고 최대 pointwise 오차는 0이다. 최대 BB 중심 변위는 37.2875096278 mm, 최대 SO(3)는 14.5157322932°로 분석기 결과와 일치한다.

비교 그림과 세 native 영상은 바이트가 보존된 기존 산출물을 직접 연결한다: [네 시점 손 프레임](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v1/hands_cycle_four_moments_v1.png>), [전신 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/whole_body.mp4>), [손 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/hands.mp4>), [가슴·팔 확대 영상](</home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/chest_left_grip_cycle_v1/chest_arm_close.mp4>).

![SciPy quaternion 정규화로 재계산한 240 Hz 기타 BB 중심 변위와 SO(3)](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/chest_left_grip_cycle_v1/artifacts_v2/guitar_motion_240Hz_v2.png)

V1 그래프·CSV는 이 quaternion 정규화 오류 범위에서 superseded 처리한다. native 물리 실행, endpoint 원자료, 16초 영상과 접촉분석은 변경되지 않았다. 입력·도구 SHA 및 pointwise 검사 결과는 [V2 manifest](./copy_manifest_v2.json)에 기록했다.
