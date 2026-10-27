# Neckward torso turn · 보정본 V2

이 문서는 V1을 보존한 채 잘못된 yaw 대상 표현과 측정 좌표 설명을 바로잡습니다. V1의 “guitar yaw 12°”는 잘못된 표기였습니다. source 목표는 몸통(Chest/Torso) world-Z yaw 12°를 neck 방향으로 요청한 것이며, 기타 quaternion은 초기값 그대로 유지됐습니다. 추가 forward bend는 2°이고, body-right 6°는 yaw 적용 전 몸통 world-goal 성분입니다. 이 source 목표값들은 scalar 관절 q가 아닙니다.

![이전 기준과 새 static의 실제 native world 자세 시간 trace](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/torso_posture_old_new_traces_v2.png)

위 그래프는 `torso_posture_v2.json`의 1201개 시점을 직접 그렸습니다. forward inclination은 native Chest frame의 원래 Chest–Neck 축을 transport해 얻은 world +Y 전방 기준 각도이고, heading은 world +Y에서 −X로 향하는 각도입니다. 따라서 이는 native world 자세 측정이지 scalar q, native frame 축 각도, 또는 source 목표값이 아닙니다. 이전 static과 새 static은 초기 상태가 달라 직접적인 동일 초기조건 비교가 아닙니다. 새 static과 elbow-motion은 초기값과 2.5초까지 exact하게 일치합니다.

실제 final measured values (이전 static → 새 static): forward inclination 53.575657° → 48.347770°; heading 12.643226° → 22.198890° toward neck; total inclination 53.590252° → 48.762687°; side inclination 2.534570° → −10.951170°. 따라서 실제 자세가 “body-right 6°” 목표를 유지했다고 해석하지 않습니다.

## 기존 캡처와 영상

V1에서 검수된 캡처와 요약 그래프는 변경 없이 그대로 연결합니다.

![이전 static 및 새 조건의 whole-body native 캡처](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/native_wholebody_old_new_timeline.png)

![새 static의 초기 support view](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/neck_yaw_static_initial_support_view.png)

![Elbow-motion 측정 그래프](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/neck_yaw_elbow_motion_response.png)

![이전 static과 새 static 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/old_vs_neckturn_static.mp4)

![새 elbow-motion 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/neck_yaw_motion_whole_body.mp4)

Hands 영상은 왼손/넥 방향 카메라라 오른쪽 상완 접촉의 증거가 아닙니다. 세 native 모두 5초/1200 physics step을 완료했습니다. 아래 접촉 수치는 새 두 실행(static_neckyaw12 및 elbow_neckyaw12)에 해당합니다: 상완 any-contact 1169/1200, R_Hip 1193/1200, Head/왼팔/오른쪽 distal arm 0/1200, declared support-region 0/1200. 이전 static_cradle 기준은 상완 1187/1200, R_Hip 1196/1200, proximal-35% 분류 1171/1200입니다. Source geometry 간격은 PhysX cooked clearance 인증이 아니며 raw lambda는 힘 측정이 아닙니다. 이는 각 조건의 단일 5초 진단이며 자연스러운 연주, 음악 성공, 반복성을 보증하지 않습니다.

[이전 V1 문서(보존)](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/artifacts_v1/README_V1.md) · [trace 원자료](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/neckward_torso_turn_v1/torso_posture_v2.json) · [복사 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/neckward_torso_turn_v1/INDEX_V1.md)
