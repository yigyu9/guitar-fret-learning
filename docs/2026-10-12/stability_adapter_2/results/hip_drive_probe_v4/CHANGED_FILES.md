# 독립 hip/하체 PD 후속 단위 변경 파일

아래 절대 경로와 1-based 줄 번호는 실제 저장된 파일에서 확인했다. 원본 실험·공용 자산·이전 결과는 보존했다.

| 파일·실제 줄 번호 | 변경 역할 |
|---|---|
| [/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:559](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:559) | 독립 PD 진단의 범위와 미채택 상태 |
| [/home/ajou/yigyu/3/stability_adapter_2/HIP_DRIVE_PROBE.md:1](/home/ajou/yigyu/3/stability_adapter_2/HIP_DRIVE_PROBE.md:1) | fixed-root hip fixture 계획과 해석 한계 |
| [/home/ajou/yigyu/3/stability_adapter_2/run_hip_drive_probe.py:15](/home/ajou/yigyu/3/stability_adapter_2/run_hip_drive_probe.py:15) | 원본 hip 관절/형상 정의 추출 및 native 24조건 실행·raw 기록 |
| [/home/ajou/yigyu/3/stability_adapter_2/physics_presets.py:17](/home/ajou/yigyu/3/stability_adapter_2/physics_presets.py:17) | 하체만 damping0인 TGS/PGS 두 진단 preset; 기본 baseline 유지 |
| [/home/ajou/yigyu/3/stability_adapter_2/trials/lower_kd0_h0.json:1](/home/ajou/yigyu/3/stability_adapter_2/trials/lower_kd0_h0.json:1) | 기존 H0 초기각 및 절대 L_A 설정 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_hip_drive_probe.py:13](/home/ajou/yigyu/3/stability_adapter_2/plot_hip_drive_probe.py:13) | 24조건 raw 자료의 3-hinge −90° 시계열 |
| [/home/ajou/yigyu/3/stability_adapter_2/plot_lower_body_pd.py:9](/home/ajou/yigyu/3/stability_adapter_2/plot_lower_body_pd.py:9) | 원자료 행 수에 맞춘 footer; 기존 14조건 PNG 픽셀 재현 유지 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:458](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:458) | 09 hip fixture·10 damping-zero 그림/설명 누적 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:232](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md:232) | 후속 독립 진단 결과 인덱스 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/hip_drive_probe_v4/README.md:1) | 24조건 표·그래프·native getter 시점·실패 이력 |
| [/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/README.md:1](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_kd0_v1/README.md:1) | 두 native H0 trial 최대 오차/실패 분석 |

새 원자료는 hip_drive_probe_v1~v4(8-case 최초 결과·검사 실패 v2·24-case v3/v4)와 lower_kd0_v1 두 trial에 각각 보존했다. logs/XML/개별 case JSON/report/trace/states/contacts/leg_torques/source snapshot은 각 결과 README와 report의 원자료 인덱스를 따른다.

검증: native 포함 15 tests 통과, fixture24조건 실제 재실행 exact 재현, v3/v4 trace 동일, 실제 damping-zero2조건 재실행 exact 재현, 원본 보호87 metadata/과거49 SHA 불변. PNG는 실제 DOF 측정/JSON 요약을 그린 과학 그래프이며 native renderer가 아니다.

실제 humanoid 초기각/한계·기타 초기 목표·기본 controller는 유지했다. +5mm Z 실제 적용은 확인 대기 중이다. 이 단위는 안정성 성공이나 전체 목표 완료를 뜻하지 않는다.
