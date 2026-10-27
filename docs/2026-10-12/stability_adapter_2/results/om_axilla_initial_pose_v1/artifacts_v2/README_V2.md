# OM 초기 겨드랑이 자세 비교 — 그림 캡션 정정 v2

v1의 설명문에 적힌 조건 단위는 맞았고, whole-body 패널 열 제목의 `후방 30°`만 잘못 표시되어 있었다. v1 그림과 산출물은 그대로 보존하고 v2 이미지를 새로 만들었다. 30은 기타의 뒤쪽 위치 이동 30 mm이며 회전 30°가 아니다. 추가 전경 18°는 source의 누적 world lean 목표각으로, 단일 scalar 관절 DOF의 18° 변경과 구분한다.

![수정된 native 전신 조건 패널: 0·2·5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v2/whole_body_conditions_0_2_5s_v2.png)

![수정된 세 조건 초기 여섯 현 화면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v2/initial_strings_conditions_v2.png)

![수정된 hold ON 초기 측면 화면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v2/hold_on_initial_axilla_side_v2.png)

hold ON 조건은 PI와 팔 target rate 1→3을 동시에 변경했으므로 PI 단독 효과로 해석할 수 없다. v1 본문의 수치·설명은 이 이미지 단위 정정을 위해 바꾸지 않았다. 기존 V의 여섯 원본-copy 영상 링크는 [영상 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/om_axilla_initial_pose_v1/INDEX.md)에서 확인한다.

이 수정은 이미 생성된 native 프레임의 캡션만 바로잡았다. native/물리 재실행 0회, 영상 재복사 0회다. [producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v2/make_panels_v2.py)와 [입력 및 출력 SHA provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_axilla_initial_pose_v1/artifacts_v2/provenance_v2.json)를 둔다.
