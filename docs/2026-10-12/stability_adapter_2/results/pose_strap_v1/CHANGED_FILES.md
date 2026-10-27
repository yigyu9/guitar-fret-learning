# 변경 파일·절대 경로·실제 줄 번호

2026-10-06. 이 소단계의 신규 구현/입력/산출물과 갱신한 메인 안내를 정리한다.
기존 stability_adapter·공용 자산·2026-08-19 자료는 수정하지 않았다.

## 메인 계획과 구현

- [POSE_STRAP_SEARCH.md](/home/ajou/yigyu/3/stability_adapter_2/POSE_STRAP_SEARCH.md:1)
- [pose_strap_inputs.py](/home/ajou/yigyu/3/stability_adapter_2/pose_strap_inputs.py:1)
- [compare_pose_strap.py](/home/ajou/yigyu/3/stability_adapter_2/compare_pose_strap.py:1)
- [plot_pose_strap.py](/home/ajou/yigyu/3/stability_adapter_2/plot_pose_strap.py:1)
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:10)
- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:593)

## 초기 설정 입력

- [L_Elbow_x_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Elbow_x_minus.json:1)
- [L_Elbow_x_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Elbow_x_plus.json:1)
- [L_Shoulder_x_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Shoulder_x_minus.json:1)
- [L_Shoulder_x_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Shoulder_x_plus.json:1)
- [L_Thorax_y_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Thorax_y_minus.json:1)
- [L_Thorax_y_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Thorax_y_plus.json:1)
- [L_Wrist_y_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Wrist_y_minus.json:1)
- [L_Wrist_y_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/L_Wrist_y_plus.json:1)
- [R_Elbow_x_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Elbow_x_minus.json:1)
- [R_Elbow_x_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Elbow_x_plus.json:1)
- [R_Shoulder_x_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Shoulder_x_minus.json:1)
- [R_Shoulder_x_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Shoulder_x_plus.json:1)
- [R_Thorax_y_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Thorax_y_minus.json:1)
- [R_Thorax_y_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Thorax_y_plus.json:1)
- [R_Wrist_y_minus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Wrist_y_minus.json:1)
- [R_Wrist_y_plus.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/R_Wrist_y_plus.json:1)
- [reference.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/pose/reference.json:1)
- [legacy.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/strap/legacy.json:1)
- [load_00n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/strap/load_00n.json:1)
- [load_05n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/strap/load_05n.json:1)
- [load_10n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/strap/load_10n.json:1)
- [load_20n.json](/home/ajou/yigyu/3/stability_adapter_2/trials/pose_strap_v1/strap/load_20n.json:1)

## 결과·그림 설명·검수

- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/README.md:1)
- [comparison_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/comparison_v2.json:1)
- [decision.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/decision.json:1)
- [plot_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/plot_manifest.json:1)
- [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/review.md:1)
- [source_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/source_manifest.json:1)
- [source_snapshot_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/source_snapshot_validation.json:1)
- [protected_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/protected_validation.json:1)
- [input_contract_tests.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/pose_strap_v1/input_contract_tests.log:1)
- [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:514)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:264)

PNG는 이 결과 폴더 images에, 원자료 report/trace/states/contacts 및 실행 로그는 각 run에 있다.
그림은 저장 native pose의 source 형상 재구성이며 Isaac/PhysX renderer·clearance 인증이 아니다.
기존 원자료를 보존하고 새 경로로 후처리한 이력을 함께 남겼다.
