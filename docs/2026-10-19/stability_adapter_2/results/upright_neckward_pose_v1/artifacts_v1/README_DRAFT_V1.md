# Upright neckward pose · 초기/정지 비교 자료

이 보관본은 이전 neckward torso yaw 12° native와 완료된 native 1–6의 whole-body/hands 영상 14개를 원본 바이트 그대로 보존합니다. 각 source/copy SHA와 ffprobe는 manifest에서 확인할 수 있습니다. native7은 별도 실행 중이므로 이 문서와 보관 범위에는 포함하지 않았습니다.

![이전 12° 기준과 새 19° 조건의 실제 native 초기 및 5초 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/native12_vs_native19_initial_and_5s.png)

위 그림은 기존 native12와 native6/static_neckyaw19의 실제 0초·5초 whole-body 캡처입니다. 두 실행은 같은 camera 종류를 사용하지만 초기 조건 및 torso posture 목표가 달라 정성적 비교이며 동일 초기상태 반복 비교는 아닙니다. G 초기 quaternion은 유지됩니다. Source yaw 목표, native Chest heading, actor/G 전체회전은 서로 다른 양입니다.

![이전 12° 기준과 새 19°의 전체 native 영상 비교 파생물](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/static12_vs_static19_whole_body_side_by_side.mp4)

이 side-by-side 파일은 위 두 원본 whole-body 영상에서 만든 시각 비교용 파생물입니다. 원본 영상은 손대지 않았습니다. 개별 원본은 [영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/INDEX_V1.md)에서 확인할 수 있습니다.

현재 승인된 정지 후보 기준: native6/static_neckyaw19의 actual forward inclination 39.846996° (이전 48.347770°), heading 27.986843° (이전 22.198890°), body bbox centre 9.548665 mm, whole actor rotation 2.995398°. Actor-root 이동 25.911055 mm는 bbox-centre 이동과 별도입니다. 최대 body-centre 이동 10.380810 mm, 최대 whole rotation 3.313974°. 접촉 표본은 upper 1173/1200, late upper 120/120, R_Hip1194/1200, head/left/distal0으로 요약됐습니다. 회전 gate 여유가 작아 반복 강건성은 미확인입니다. 이 한 차례 5초 정지 시험은 음악 성공, 자연스러움, 동작 중 유지, 반복성을 검증하지 않습니다.

이 자료는 source/native/actor-root/G 회전을 혼동하지 않으며, source 기하 검사는 PhysX cooked clearance 인증이 아닙니다. Strap OFF, left grip OFF, root/lower fixed, guitar free, guitar에 직접 힘 없음이라는 phase 조건 아래에서 수행됐습니다. 세부 결과는 [phase README](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/analysis_v6/static_neckyaw19/verification.json)에서 확인합니다.
