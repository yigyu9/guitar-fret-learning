# Upright neckward pose · 정지 후보 및 작은 동작 진단

새 초기자세 후보는 native6의 torso neckward yaw source goal 19°입니다. 이전 12° 기준의 실제 native 초기/5초 장면은 아래 그림에 포함되어 있습니다. native1–6 및 이전 기준의 전신·손 영상 14개는 먼저 byte-exact 보관했고, 완료된 native7 전신·손 영상 2개도 동일 방식으로 추가해 총 16개를 [manifest V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/manifest_v2.json)와 [색인 V2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/INDEX_V2.md)에 기록했습니다. V1 manifest/index/provenance는 보존했습니다.

![이전 12° 기준과 새 19° static의 초기 및 5초 실제 native 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/native12_vs_native19_initial_and_5s.png)

이전 12°와 새 19° 사이의 실제 native 정지 whole-body 비교 영상(파생 side-by-side):

![정지 비교 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/static12_vs_static19_whole_body_side_by_side.mp4)

## 정지 후보의 실제 자세 및 gate

새 native6/static_neckyaw19에서 실제 Chest–Neck world 기준 forward inclination은 39.846996°였고, 이전 native neckward12°의 48.347770°보다 8.500774° 작았습니다. 실제 world heading(+Y에서 −X)은 27.986843°(이전 22.198890°), source yaw goal은 19°입니다. 기타의 초기 quaternion은 이전 후보와 같게 설정했으며 이후 물리에서 자유롭게 회전했습니다. Source yaw, Chest heading, 전체 actor/G 회전은 다른 양입니다.

정지 종료에서 기타 body bounding-box 중심 이동은 9.548665 mm, root actor 이동은 25.911055 mm, 전체 SO(3) 회전은 2.995398°였습니다. 최종값을 검사하는 3° 미만 gate는 2.995398°로 0.004602° 여유를 두고 통과했습니다. 실행 중 최대치는 중심 10.380810 mm/회전 3.313974°였고 최종값 gate와 별도입니다. 상완 접촉은 1173/1200이고 후기 구간 120/120, R_Hip 1194/1200; head/left/distal은 0이었습니다. 5초 한 번의 정지 시험이며 반복 강건성은 확인하지 않았습니다.

## 같은 초기값의 작은 elbow-motion 진단

![새 19° static과 elbow-motion의 실제 native 0·2·5초 프레임](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/artifacts_v1/native19_static_vs_elbow_timeline_v2.png)

![native7 실제 elbow-motion 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/upright_neckward_pose_v1/native_v7/whole_body.mp4)

Native6 정지와 native7 motion은 같은 초기 상태이며 2.5초까지 trace가 exact하게 같습니다. 작은 동작 구간은 2.5–4.5초의 단일 R_Elbow_y scalar target입니다. Actor world rotation 축이 아닙니다. 실제 moving q 절대 왕복은 10.094022°, 정지 대비 incremental 응답은 10.092677°였습니다(상관 0.999946426, incremental RMSE 0.048328°, absolute target RMSE 0.098600°). 정지 대비 기타 추가 최대차는 중심 0.077660 mm, 전체 회전 0.042115°이며 종료 차이는 0.041240 mm / 0.042115°입니다.

정지 및 motion의 strict 35%+upper-rim 분류는 1117/1200이며, motion raw-positive 표본은 1113/1200입니다. 이전 native12 strict-region은 0/1200이었습니다. 이 분류는 겨드랑이 해부학적 지지나 힘 분담의 인증이 아니며, raw lambda는 힘 단위가 아닙니다. 이 5초 작은 동작 진단은 음악 연주, 장시간 유지, 자연스러움 또는 반복성을 검증하지 않습니다.

## 실행 및 해석 범위

각 native 1–7 실행은 5.0초/1200 physics step/300 control step, 영상 151 frames/30 fps/5.033333초였습니다. 이 영상은 멈춰있는 마지막 프레임의 반복이 아니라 실제 5초 계산 결과입니다. Strap OFF, left grip OFF, root/lower fixed, guitar free, guitar direct force 없음 조건입니다. 실패한 26°/30° 및 follow 진단들도 영상 색인에 원형 그대로 남겼으며, 최종 후보로 표시하지 않습니다. Source/초기 overlap 검사는 PhysX cooked clearance 인증과 다릅니다.

이번 선택은 19° 정지 초기자세의 단일 gate 통과와 별도의 작은 동작 진단에 한정됩니다. 연주·장기 안정·반복 성공은 미확인입니다. [정지 19° 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/analysis_v6/static_neckyaw19/verification.json) · [elbow motion 비교자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/elbow_comparison_v1.json) · [실제 Chest–Neck 자세 trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/torso_posture_v7.json) · [새 조건 실제 접촉영역 분류](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/upright_neckward_pose_v1/contact_region_v1.json) · [이전 12° 실제 접촉영역 분류](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/contact_region_v1.json)
