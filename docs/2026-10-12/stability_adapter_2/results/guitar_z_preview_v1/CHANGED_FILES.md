# 이번 단위 변경 파일과 실제 줄 번호

2026-10-06 검증 시점의 절대 경로·1-based 줄 번호다. 이전 실험과 원자료는 보존했다.

| 파일 (절대 경로·줄 링크) | 역할 |
|---|---|
| [/home/ajou/yigyu/3/stability_adapter_2/README.md:10](/home/ajou/yigyu/3/stability_adapter_2/README.md:10) | 최신 범위와 기존 동일 p/q 원칙의 예외 |
| [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:542](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:542) | 접촉·PD 진단 및 사용자 제안 Z 비교 계획 |
| [/home/ajou/yigyu/3/stability_adapter_2/PHYSX_CONTACT_DIAGNOSTICS.md:1](/home/ajou/yigyu/3/stability_adapter_2/PHYSX_CONTACT_DIAGNOSTICS.md:1) | 240Hz 접촉 교정과 검증 체크리스트 |
| [/home/ajou/yigyu/3/stability_adapter_2/LOWER_BODY_DIAGNOSTICS.md:1](/home/ajou/yigyu/3/stability_adapter_2/LOWER_BODY_DIAGNOSTICS.md:1) | 승인된 PD/solver 진단과 미채택 결과 |
| [/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_PREVIEW.md:1](/home/ajou/yigyu/3/stability_adapter_2/GUITAR_Z_PREVIEW.md:1) | 정적 Z 비교와 목표 변경 확인 범위 |
| [/home/ajou/yigyu/3/stability_adapter_2/environment.py:37](/home/ajou/yigyu/3/stability_adapter_2/environment.py:37) | 진단 preset 및 물리 step 분리; 기본 동작 유지 |
| [/home/ajou/yigyu/3/stability_adapter_2/physics_presets.py:2](/home/ajou/yigyu/3/stability_adapter_2/physics_presets.py:2) | 14개 명시적 solver/하체 actuation 진단 조건 |
| [/home/ajou/yigyu/3/stability_adapter_2/native_contacts.py:6](/home/ajou/yigyu/3/stability_adapter_2/native_contacts.py:6) | native raw contact와 env body 이름 직렬화 |
| [/home/ajou/yigyu/3/stability_adapter_2/run_contact_calibration.py:10](/home/ajou/yigyu/3/stability_adapter_2/run_contact_calibration.py:10) | analytic box signed contact field 대조 |
| [/home/ajou/yigyu/3/stability_adapter_2/run_physx_contacts.py:19](/home/ajou/yigyu/3/stability_adapter_2/run_physx_contacts.py:19) | 각 physics step 실제 contact/state/strap/command 기록 |
| [/home/ajou/yigyu/3/stability_adapter_2/run_pose_hold_probe.py:12](/home/ajou/yigyu/3/stability_adapter_2/run_pose_hold_probe.py:12) | baseline hold/off isolated probe와 native readback 감사 |
| [/home/ajou/yigyu/3/stability_adapter_2/replay_contact_geometry.py:10](/home/ajou/yigyu/3/stability_adapter_2/replay_contact_geometry.py:10) | 저장 native pose의 source geometry 정적 재구성 |
| [/home/ajou/yigyu/3/stability_adapter_2/preview_guitar_z.py:14](/home/ajou/yigyu/3/stability_adapter_2/preview_guitar_z.py:14) | 기타만 Z 이동한 정적 형상 및 고정 L_A 경로 비교 |
| [/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:39](/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:39) | 추가 진단 runtime 의존성 hash 보존 |
| [/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contacts.py:7](/home/ajou/yigyu/3/stability_adapter_2/tests/test_native_contacts.py:7) | analytic box 접촉 부호/skin 및 raw 직렬화 검증 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_physx_contacts.py:17](/home/ajou/yigyu/3/stability_adapter_2/plot_physx_contacts.py:17) | H0 timeline 및 저장 source-shape 도해 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_lower_body_pd.py:1](/home/ajou/yigyu/3/stability_adapter_2/plot_lower_body_pd.py:1) | 14조건 원자료 비교 그림 생성 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_preview.py:1](/home/ajou/yigyu/3/stability_adapter_2/plot_guitar_z_preview.py:1) | Z 후보 정적 간격/route 비교 그림 생성 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:408](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:408) | 06 접촉·07 PD·08 Z 비교 이미지와 누적 설명 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/physx_contact_v1/README.md:1) | 접촉 v1 그림·실측·raw field·검증 범위 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_body_pd_v1/README.md:1) | 14조건 표·그림·isolated probe 분석 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_z_preview_v1/README.md:1) | 5개 정적 Z 후보 표·그림·권고 |

| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:212](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:212) | 후속 결과 인덱스와 현재 미검증 범위 |

기록 파일: 각 결과 디렉터리의 report/trace/states/contacts/leg_torques 및 로그·source snapshots, 신규 `comparison_all.json`, `preview.json`, `protected_validation.json`, `review.md`다. JSON 원자료는 표 대신 각 결과 README의 인덱스를 따른다. 모든 파일의 최초 줄은 1이다.

검증: native 포함 15 tests 통과, baseline의 과거 7 samples exact 재현, 14 preset readback·제어 범위 보존, isolated baseline hold/off 재현, 5개 정적 Z 비교 독립 재현, 보호 파일 87 metadata·49 SHA 불변. 이 검증은 물리 안정성 성공을 의미하지 않는다.

현재 native 기타 초기 목표와 기본 solver/하체 gain은 baseline 그대로다. 하체 초기각 보정 및 +5mm 실제 목표 변경은 적용하지 않았다. +5mm 실제 시험은 사용자 확인을 요청했다.
