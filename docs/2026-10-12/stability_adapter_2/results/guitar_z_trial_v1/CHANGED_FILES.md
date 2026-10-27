# 이번 소단계 변경 파일과 실제 줄 번호

2026-10-06. 기타 초기 Z +5mm 승인 시험만 구현·검증했다. 기존 dirty 파일과 기존 stability_adapter 관련 코드/산출물은 수정하지 않았다. 링크는 절대 경로와 현재 실제 one-based 시작 줄이다.

## 계획·구현·검증 및 결과 문서

- [/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_TRIAL.md:1](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_TRIAL.md:1)
- [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:571](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:571)
- [/home/ajou/yigyu/3/stability_adapter_2/README.md:10](/home/ajou/yigyu/3/stability_adapter_2/README.md:10)
- [/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:23](/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:23)
- [/home/ajou/yigyu/3/stability_adapter_2/environment.py:46](/home/ajou/yigyu/3/stability_adapter_2/environment.py:46)
- [/home/ajou/yigyu/3/stability_adapter_2/run_initialization.py:21](/home/ajou/yigyu/3/stability_adapter_2/run_initialization.py:21)
- [/home/ajou/yigyu/3/stability_adapter_2/run_trial.py:51](/home/ajou/yigyu/3/stability_adapter_2/run_trial.py:51)
- [/home/ajou/yigyu/3/stability_adapter_2/run_physx_contacts.py:55](/home/ajou/yigyu/3/stability_adapter_2/run_physx_contacts.py:55)
- [/home/ajou/yigyu/3/stability_adapter_2/compare_guitar_z_trial.py:15](/home/ajou/yigyu/3/stability_adapter_2/compare_guitar_z_trial.py:15)
- [/home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_trial.py:18](/home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_trial.py:18)
- [/home/ajou/yigyu/3/stability_adapter_2/trials/guitar_z_5mm.json:4](/home/ajou/yigyu/3/stability_adapter_2/trials/guitar_z_5mm.json:4)
- [/home/ajou/yigyu/3/stability_adapter_2/tests/test_trial_settings.py:19](/home/ajou/yigyu/3/stability_adapter_2/tests/test_trial_settings.py:19)
- [/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:12](/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contract.py:12)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:245](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:245)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:484](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:484)
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/README.md:1)

## 새 원자료·로그

- [comparison.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/comparison.json:1)
- [tests.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/tests.log:1)
- [protected_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/protected_validation.json:1)
- [comparison_retry_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/comparison_retry_validation.json:1)
- [source_manifest.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/source_manifest.json:1)
- [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/review.md:1)
- [h0/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/report.json:1)
- [h0/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/trace.json:1)
- [h0/states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/states.json:1)
- [h0/contacts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/contacts.json:1)
- [h0/leg_torques.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/leg_torques.json:1)
- [h0/initial_source_geometry.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/h0/initial_source_geometry.json:1)
- [z5/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/report.json:1)
- [z5/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/trace.json:1)
- [z5/states.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/states.json:1)
- [z5/contacts.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/contacts.json:1)
- [z5/leg_torques.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/leg_torques.json:1)
- [z5/initial_source_geometry.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5/initial_source_geometry.json:1)
- [z5_input_contract/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5_input_contract/report.json:1)
- [z5_input_contract/trace.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/z5_input_contract/trace.json:1)

Native 실행/후처리 로그는 같은 결과 디렉터리에 있다. 최초 후처리 실패 로그도 보존했다. 구현 스냅샷은 `source/` 아래 상대 구조대로 저장했으며 source_manifest.json에 원래 절대 경로와 SHA-256을 기록했다.

## 이미지

- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_source_geometry_t0.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_source_geometry_t0.png) — 바이너리 이미지로 줄 번호 없음.
- [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_timeline.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/images/guitar_z_trial_v1_timeline.png) — 바이너리 이미지로 줄 번호 없음.

최종 소스 스냅샷 SHA와 두 run runtime SHA는 [source_snapshot_validation.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_trial_v1/source_snapshot_validation.json:1)에 기록했다. 다음 미승인 소단계의 구체 범위는 [GUITAR_Z_TRIAL.md:49](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_TRIAL.md:49)에 있다.
