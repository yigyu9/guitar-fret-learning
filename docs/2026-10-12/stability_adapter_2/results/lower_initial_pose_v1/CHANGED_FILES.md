# 변경 파일의 절대 경로와 실제 줄 번호

2026-10-06. 이번 승인 범위: +5mm 기타와 기존 root/상체/PD/solver/절대 L_A를 유지한 하체 초기각 기준 ±0.05rad 국소 탐색 및 개선 후보 최대 3개 native 비교. 초기 상태 한 번 적용 뒤 물리 step 중 재주입하지 않는다.

## 계획·구현·검증·문서

- [/home/ajou/yigyu/3/stability_adapter_2/LOWER_INITIAL_POSE.md:1](/home/ajou/yigyu/3/stability_adapter_2/LOWER_INITIAL_POSE.md:1)
- [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:582](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:582)
- [/home/ajou/yigyu/3/stability_adapter_2/README.md:10](/home/ajou/yigyu/3/stability_adapter_2/README.md:10)
- [/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_TRIAL.md:49](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_TRIAL.md:49)
- [/home/ajou/yigyu/3/stability_adapter_2/BATCH_EXPERIMENTS.md:9](/home/ajou/yigyu/3/stability_adapter_2/BATCH_EXPERIMENTS.md:9)
- [/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:35](/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:35)
- [/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:9](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:9)
- [/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:83](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:83)
- [/home/ajou/yigyu/3/stability_adapter_2/replay_contact_geometry.py:10](/home/ajou/yigyu/3/stability_adapter_2/replay_contact_geometry.py:10)
- [/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:12](/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:12)
- [/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:41](/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:41)
- [/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:73](/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:73)
- [/home/ajou/yigyu/3/stability_adapter_2/compare_lower_initial_pose.py:15](/home/ajou/yigyu/3/stability_adapter_2/compare_lower_initial_pose.py:15)
- [/home/ajou/yigyu/3/stability_adapter_2/plot_lower_initial_pose.py:12](/home/ajou/yigyu/3/stability_adapter_2/plot_lower_initial_pose.py:12)
- [/home/ajou/yigyu/3/stability_adapter_2/plot_lower_initial_pose.py:81](/home/ajou/yigyu/3/stability_adapter_2/plot_lower_initial_pose.py:81)
- [/home/ajou/yigyu/3/stability_adapter_2/tests/test_trial_settings.py:40](/home/ajou/yigyu/3/stability_adapter_2/tests/test_trial_settings.py:40)
- [/home/ajou/yigyu/3/stability_adapter_2/tests/test_initial_overlap.py:9](/home/ajou/yigyu/3/stability_adapter_2/tests/test_initial_overlap.py:9)
- [/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:12](/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:12)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/lower_initial_pose_c01.json:4](/home/ajou/yigyu/3/stability_adapter_2/trials/lower_initial_pose_c01.json:4)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/lower_initial_pose_c02.json:4](/home/ajou/yigyu/3/stability_adapter_2/trials/lower_initial_pose_c02.json:4)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/lower_initial_pose_c03.json:4](/home/ajou/yigyu/3/stability_adapter_2/trials/lower_initial_pose_c03.json:4)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:254](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:254)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:498](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:498)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/README.md:1)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/review.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/review.md:1)

## 새 원자료·로그

- [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/comparison.json:1)
- [search/search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/search/search.json:1)
- [search_verified/search.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/search_verified/search.json:1)
- [search_reproduction_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/search_reproduction_validation.json:1)
- [tests.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/tests.log:1)
- [protected_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/protected_validation.json:1)
- [source_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/source_manifest.json:1)
- [source_snapshot_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/source_snapshot_validation.json:1)
- [baseline/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/baseline/report.json:1)
- [baseline/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/baseline/trace.json:1)
- [baseline/states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/baseline/states.json:1)
- [baseline/contacts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/baseline/contacts.json:1)
- [baseline/leg_torques.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/baseline/leg_torques.json:1)
- [baseline/initial_source_geometry.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/baseline/initial_source_geometry.json:1)
- [c01/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c01/report.json:1)
- [c01/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c01/trace.json:1)
- [c01/states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c01/states.json:1)
- [c01/contacts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c01/contacts.json:1)
- [c01/leg_torques.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c01/leg_torques.json:1)
- [c01/initial_source_geometry.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c01/initial_source_geometry.json:1)
- [c02/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c02/report.json:1)
- [c02/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c02/trace.json:1)
- [c02/states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c02/states.json:1)
- [c02/contacts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c02/contacts.json:1)
- [c02/leg_torques.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c02/leg_torques.json:1)
- [c02/initial_source_geometry.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c02/initial_source_geometry.json:1)
- [c03/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c03/report.json:1)
- [c03/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c03/trace.json:1)
- [c03/states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c03/states.json:1)
- [c03/contacts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c03/contacts.json:1)
- [c03/leg_torques.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c03/leg_torques.json:1)
- [c03/initial_source_geometry.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/c03/initial_source_geometry.json:1)

실행 로그는 같은 결과 디렉터리에 있다. 최초 자기 SHA 누락 탐색 자료와 당시 source_used.py도 search/에 보존했다. 최종 구현 스냅샷은 source/이며 절대 원래 경로·SHA는 source_manifest.json에 기록했다. 이전 단계의 snapshot 검사는 당시 코드에 대한 기록이며 이후 승인된 소스 변경으로 대체하지 않는다.

## 이미지

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_c02_poses.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_c02_poses.png) — 바이너리 이미지로 줄 번호 없음.
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_comparison.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/images/lower_initial_pose_v1_comparison.png) — 바이너리 이미지로 줄 번호 없음.

다음 중요 결정의 아직 미실행 승인안: [LOWER_JOINT_REPRESENTATION_PROPOSAL.md:1](/home/ajou/yigyu/3/stability_adapter_2/LOWER_JOINT_REPRESENTATION_PROPOSAL.md:1). 이번 완료한 후보 실험과 분리한다.
